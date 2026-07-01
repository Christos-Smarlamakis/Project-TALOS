/* ═══════════════════════════════════════════════════════════════════════════
   TALOS Architecture Graph — Futuristic JS Engine
   Dependencies: Cytoscape.js (loaded from CDN in HTML)
   ═══════════════════════════════════════════════════════════════════════════ */

// ── Particle Background ──────────────────────────────────────────────────────
(function() {
    const canvas = document.getElementById('particles');
    const ctx = canvas.getContext('2d');
    let particles = [];
    const MAX = 120;

    function resize() {
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
    }
    window.addEventListener('resize', resize);
    resize();

    class Particle {
        constructor() {
            this.reset();
        }
        reset() {
            this.x = Math.random() * canvas.width;
            this.y = Math.random() * canvas.height;
            this.vx = (Math.random() - 0.5) * 0.4;
            this.vy = (Math.random() - 0.5) * 0.4;
            this.size = Math.random() * 1.5 + 0.3;
            this.opacity = Math.random() * 0.5 + 0.1;
        }
        update() {
            this.x += this.vx;
            this.y += this.vy;
            if (this.x < 0 || this.x > canvas.width || this.y < 0 || this.y > canvas.height) this.reset();
        }
        draw() {
            ctx.beginPath();
            ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
            ctx.fillStyle = `rgba(0, 229, 255, ${this.opacity})`;
            ctx.fill();
        }
    }

    for (let i = 0; i < MAX; i++) particles.push(new Particle());

    function animateParticles() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        particles.forEach(p => { p.update(); p.draw(); });
        // Draw connections between nearby particles
        for (let i = 0; i < particles.length; i++) {
            for (let j = i + 1; j < particles.length; j++) {
                const dx = particles[i].x - particles[j].x;
                const dy = particles[i].y - particles[j].y;
                const dist = Math.sqrt(dx * dx + dy * dy);
                if (dist < 120) {
                    ctx.beginPath();
                    ctx.moveTo(particles[i].x, particles[i].y);
                    ctx.lineTo(particles[j].x, particles[j].y);
                    ctx.strokeStyle = `rgba(0, 229, 255, ${0.04 * (1 - dist / 120)})`;
                    ctx.lineWidth = 0.5;
                    ctx.stroke();
                }
            }
        }
        requestAnimationFrame(animateParticles);
    }
    animateParticles();
})();

// ── Layer Color Palette ─────────────────────────────────────────────────────
const LAYER_COLORS = {
    entry:    { bg: '#ff4081', border: '#ff80ab', glow: '0 0 12px rgba(255,64,129,0.5)' },
    core:     { bg: '#ffd740', border: '#ffe57f', glow: '0 0 12px rgba(255,215,64,0.5)' },
    script:   { bg: '#448aff', border: '#82b1ff', glow: '0 0 12px rgba(68,138,255,0.5)' },
    source:   { bg: '#69f0ae', border: '#b9f6ca', glow: '0 0 12px rgba(105,240,174,0.5)' },
    external: { bg: '#b388ff', border: '#d1c4ff', glow: '0 0 12px rgba(179,136,255,0.5)' },
    config:   { bg: '#90a4ae', border: '#b0bec5', glow: '0 0 6px rgba(144,164,174,0.3)' },
    stdlib:   { bg: '#546e7a', border: '#78909c', glow: '0 0 4px rgba(84,110,122,0.2)' },
    thirdparty: { bg: '#26c6da', border: '#80deea', glow: '0 0 10px rgba(38,198,218,0.4)' },
};

// ── Initialize Cytoscape ─────────────────────────────────────────────────────
let cy;
let physicsOn = true;
let auditMode = false;
let auditColorsOn = true;

function initGraph(elements) {
    cy = cytoscape({
        container: document.getElementById('cy'),
        elements: elements,
        style: buildStyles(),
        layout: {
            name: 'cose',
            animate: false,
            nodeOverlap: 20,
            idealEdgeLength: (el) => el.data('weight') === 'heavy' ? 180 : 100,
            nodeRepulsion: 30000,
            gravity: 0.2,
            randomize: true,
            fit: true,
            padding: 60,
        },
    });
    setupInteractions();
    updateStats(elements);
    setTimeout(() => {
        const node = cy.getElementById('talos.py');
        if (node.length) cy.animate({ center: { eles: node }, zoom: 1.4 }, { duration: 800 });
    }, 600);
}

function buildStyles() {
    const styles = [];
    // Layer styles
    for (const [layer, colors] of Object.entries(LAYER_COLORS)) {
        styles.push({
            selector: `node[layer="${layer}"]`,
            style: {
                'background-color': colors.bg,
                'border-color': colors.border,
                'border-width': 2,
            }
        });
    }
    // Node base
    styles.push({
        selector: 'node',
        style: {
            'label': 'data(label)',
            'color': '#e0e0f0',
            'font-size': '9px',
            'text-valign': 'center',
            'text-halign': 'center',
            'width': 20,
            'height': 20,
            'border-opacity': 1,
            'text-max-width': '140px',
            'text-wrap': 'wrap',
            'text-outline-color': '#0a0a14',
            'text-outline-width': 2,
        }
    });
    // Bigger nodes for entry/core
    styles.push({
        selector: 'node[layer="entry"], node[layer="core"]',
        style: { 'width': 32, 'height': 32, 'font-size': '11px', 'font-weight': 'bold' }
    });
    // Small nodes for stdlib/thirdparty
    styles.push({
        selector: 'node[layer="stdlib"], node[layer="thirdparty"]',
        style: { 'width': 14, 'height': 14, 'font-size': '7px' }
    });
    // External = rectangle
    styles.push({
        selector: 'node[layer="external"]',
        style: { 'shape': 'rectangle', 'width': 30, 'height': 20, 'font-size': '8px' }
    });
    // Config = diamond
    styles.push({
        selector: 'node[layer="config"]',
        style: { 'shape': 'diamond', 'width': 16, 'height': 16, 'font-size': '7px' }
    });
    // Edges
    styles.push({
        selector: 'edge',
        style: {
            'width': 1.2,
            'line-color': 'rgba(255,255,255,0.12)',
            'target-arrow-color': 'rgba(255,255,255,0.12)',
            'target-arrow-shape': 'triangle',
            'curve-style': 'bezier',
            'arrow-scale': 0.6,
            'opacity': 0.5,
        }
    });
    styles.push({
        selector: 'edge[label="subprocess"]',
        style: {
            'line-style': 'dashed', 'line-color': '#ff4081', 'target-arrow-color': '#ff4081',
            'opacity': 0.4, 'width': 1.5,
        }
    });
    styles.push({
        selector: 'edge[label="import"]',
        style: {
            'line-color': '#448aff', 'target-arrow-color': '#448aff', 'opacity': 0.5, 'width': 1.3,
        }
    });
    styles.push({
        selector: 'edge[label="HTTP"], edge[label="HTTP POST"], edge[label="genai"], edge[label="OpenAI client"], edge[label="pyzotero"], edge[label="reads"], edge[label="SQLite"], edge[label="reads keys"]',
        style: {
            'line-color': '#b388ff', 'target-arrow-color': '#b388ff', 'opacity': 0.5, 'width': 1.3,
        }
    });
    // Highlight
    styles.push({ selector: 'node.highlight', style: { 'border-color': '#ffffff', 'border-width': 4, 'z-index': 10 } });
    styles.push({ selector: 'node.dim', style: { 'opacity': 0.15, 'text-opacity': 0 } });
    styles.push({ selector: 'edge.dim', style: { 'opacity': 0.03 } });
    styles.push({ selector: 'edge.highlight', style: { 'line-color': '#00e5ff', 'target-arrow-color': '#00e5ff', 'width': 3, 'opacity': 1 } });
    return styles;
}

// ── Interactions ────────────────────────────────────────────────────────────
function setupInteractions() {
    const panel = document.getElementById('infoPanel');

    cy.on('tap', 'node', function(evt) {
        const node = evt.target;
        const desc = (node.data('desc') || 'No description').replace(/\\n/g, '<br>');
        const layer = node.data('layer') || '';
        const layerName = layer.charAt(0).toUpperCase() + layer.slice(1);
        const inDegree = node.connectedEdges('edge[target="' + node.id() + '"]').length;
        const outDegree = node.connectedEdges('edge[source="' + node.id() + '"]').length;

        // Collect connected dependencies
        let depsHtml = '';
        const connected = node.connectedEdges().add(node.connectedNodes());
        const depNodes = connected.nodes().filter(n => n.id() !== node.id());
        if (depNodes.length > 0) {
            depsHtml = '<div class="panel-deps"><div class="panel-deps-label">Connected Dependencies</div>';
            depNodes.forEach(n => {
                const edge = node.edgesWith(n);
                const label = edge.length > 0 ? edge[0].data('label') || '' : '';
                let tagClass = 'panel-dep-tag';
                if (label === 'import') tagClass += ' import';
                else if (label === 'subprocess') tagClass += ' subprocess';
                else if (label.includes('HTTP')) tagClass += ' http';
                depsHtml += `<span class="${tagClass}">${label ? label + ' → ' : ''}${n.data('label')}</span>`;
            });
            depsHtml += '</div>';
        }

        document.getElementById('panelTitle').textContent = node.data('label');
        document.getElementById('panelMeta').innerHTML = `<span>${layerName}</span><span>${outDegree} outgoing</span><span>${inDegree} incoming</span>`;
        document.getElementById('panelDesc').innerHTML = desc;
        document.getElementById('panelDeps').innerHTML = depsHtml;
        
        const sidePanel = document.getElementById('sidePanel');
        sidePanel.classList.add('visible');

        cy.elements().addClass('dim');
        node.removeClass('dim').addClass('highlight');
        connected.nodes().removeClass('dim').addClass('highlight');
        connected.edges().removeClass('dim').addClass('highlight');
    });

    cy.on('tap', function(evt) {
        if (evt.target === cy) {
            document.getElementById('sidePanel').classList.remove('visible');
            cy.elements().removeClass('dim highlight');
        }
    });

    // Search
    const searchBox = document.getElementById('searchBox');
    searchBox.addEventListener('input', function() {
        const query = this.value.toLowerCase();
        cy.elements().removeClass('dim highlight');
        if (!query) return;
        cy.nodes().forEach(n => {
            const label = (n.data('label') || '').toLowerCase();
            const desc = (n.data('desc') || '').toLowerCase();
            if (!label.includes(query) && !desc.includes(query)) n.addClass('dim');
        });
        cy.edges().forEach(e => {
            if (e.source().hasClass('dim') || e.target().hasClass('dim')) e.addClass('dim');
        });
    });
}

// ── Toolbar Functions ────────────────────────────────────────────────────────
function fitGraph() { cy.fit(undefined, 50); }

function togglePhysics() {
    const btn = document.getElementById('btn-physics');
    if (physicsOn) {
        cy.nodes().forEach(n => n.lock());
        btn.classList.remove('active'); btn.textContent = 'Physics: OFF';
    } else {
        cy.nodes().forEach(n => n.unlock());
        cy.layout({ name: 'cose', animate: true, randomize: false, fit: true }).run();
        btn.classList.add('active'); btn.textContent = 'Physics: ON';
    }
    physicsOn = !physicsOn;
}

function resetView() {
    cy.elements().removeClass('dim highlight');
    document.getElementById('searchBox').value = '';
    document.getElementById('layerFilter').value = 'all';
    filterByLayer();
}

function filterByLayer() {
    const layer = document.getElementById('layerFilter').value;
    if (layer === 'all') {
        cy.nodes().style('display', 'element');
        cy.edges().style('display', 'element');
    } else {
        cy.nodes().forEach(n => {
            n.style('display', n.data('layer') === layer ? 'element' : 'none');
        });
        cy.edges().forEach(e => {
            e.style('display',
                e.source().style('display') === 'element' && e.target().style('display') === 'element'
                ? 'element' : 'none');
        });
    }
    fitGraph();
}

function exportPNG() {
    const png = cy.png({ full: true, bg: getComputedStyle(document.body).getPropertyValue('--bg-primary').trim() || '#0d1b2a', scale: 2 });
    const a = document.createElement('a');
    a.href = png; a.download = 'talos_architecture_graph.png'; a.click();
}

function exportSVG() {
    const bgColor = getComputedStyle(document.body).getPropertyValue('--bg-primary').trim() || '#0d1b2a';
    if (typeof cy.svg === 'function') {
        try {
            let svg = cy.svg({ full: true, scale: 1 });
            // Inject background rect so SVG is not transparent
            const bgRect = `<rect width="100%" height="100%" fill="${bgColor}"/>`;
            svg = svg.replace(/<svg([^>]*)>/, `<svg$1>${bgRect}`);
            const dataUrl = 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(svg);
            const a = document.createElement('a');
            a.href = dataUrl;
            a.download = 'talos_architecture_graph.svg';
            document.body.appendChild(a);
            a.click();
            setTimeout(() => document.body.removeChild(a), 100);
            return;
        } catch(e) {
            console.warn('SVG generation failed, falling back to PNG:', e.message);
        }
    }
    // Fallback: wrap PNG in SVG container
    const png = cy.png({ full: true, bg: bgColor, scale: 2 });
    const svgWrap = `<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="100%" height="100%"><rect width="100%" height="100%" fill="${bgColor}"/><image width="100%" height="100%" xlink:href="${png}"/></svg>`;
    const dataUrl = 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(svgWrap);
    const a = document.createElement('a');
    a.href = dataUrl;
    a.download = 'talos_architecture_graph.svg';
    document.body.appendChild(a);
    a.click();
    setTimeout(() => document.body.removeChild(a), 100);
}

function toggleDarkMode() {
    document.body.classList.toggle('light');
}

function toggleFullscreen() {
    if (!document.fullscreenElement) {
        document.documentElement.requestFullscreen();
    } else {
        document.exitFullscreen();
    }
}

function zoomIn() { cy.zoom({ level: cy.zoom() * 1.3, renderedPosition: { x: window.innerWidth/2, y: window.innerHeight/2 } }); }
function zoomOut() { cy.zoom({ level: cy.zoom() / 1.3, renderedPosition: { x: window.innerWidth/2, y: window.innerHeight/2 } }); }

function closePanel() {
    document.getElementById('sidePanel').classList.remove('visible');
    cy.elements().removeClass('dim highlight');
}

let minimapOn = false;
function toggleMinimap() {
    if (minimapOn) {
        cy.navigator({}).destroy();
        minimapOn = false;
    } else {
        cy.navigator({
            container: false,
            viewLiveFramerate: 0,
            thumbnailEventFramerate: 30,
            thumbnailLiveFramerate: false,
            dblClickDelay: 200,
            removeCustomContainer: false,
            rerenderDelay: 500,
        });
        minimapOn = true;
    }
}

function toggleLayerPill(pill) {
    const layer = pill.dataset.layer;
    const visible = pill.classList.toggle('on');
    if (visible) {
        cy.nodes(`[layer="${layer}"]`).style('display', 'element');
        cy.edges().style('display', 'element');
    } else {
        cy.nodes(`[layer="${layer}"]`).style('display', 'none');
        cy.edges().forEach(e => {
            if (e.source().style('display') === 'none' || e.target().style('display') === 'none') {
                e.style('display', 'none');
            }
        });
    }
    fitGraph();
}

// ── Stats ────────────────────────────────────────────────────────────────────
function updateStats(elements) {
    const nodes = elements.filter(e => e.group === 'nodes');
    const edges = elements.filter(e => e.group === 'edges');
    document.getElementById('statNodes').textContent = nodes.length;
    document.getElementById('statEdges').textContent = edges.length;
}

// ── Audit Mode ──────────────────────────────────────────────────────────────
function loadAudit() {
    const urlParams = new URLSearchParams(window.location.search);
    const auditPath = urlParams.get('audit');
    if (auditPath) fetchAuditData(auditPath);
}

async function fetchAuditData(path) {
    try {
        const resp = await fetch(path);
        if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
        const data = await resp.json();
        enableAuditMode(data);
    } catch (e) {
        console.warn('Audit: Could not load from', path, e.message);
        try {
            const resp2 = await fetch('../reports/audits/dependency_audit.json');
            if (resp2.ok) { enableAuditMode(await resp2.json()); return; }
        } catch (e2) {}
    }
}

function enableAuditMode(data) {
    auditMode = true;
    const bar = document.createElement('div');
    bar.className = 'audit-bar';
    bar.innerHTML = `
        <span style="color:#00e5ff;font-weight:bold;">Audit Results</span>
        <span class="audit-item matched"><span class="count">${data.matched||0}</span> Matched</span>
        <span class="audit-item stale"><span class="count">${data.stale||0}</span> Stale</span>
        <span class="audit-item missing"><span class="count">${data.missing||0}</span> Missing</span>
        <span class="audit-info">${data.generated_at ? data.generated_at.slice(0,16) : ''}</span>
    `;
    document.querySelector('.top-bar').insertAdjacentElement('afterend', bar);
    applyAuditColors(data);
}

function applyAuditColors(data) {
    if (!data || !data.results) return;
    cy.nodes().forEach(node => {
        const id = node.id();
        const stale = data.results.some(r => r.file === id && r.status === 'stale');
        const missing = data.results.some(r => r.file === id && r.status === 'missing');
        if (stale) node.style('border-color', '#ff5252');
        else if (missing) node.style('border-color', '#ffd740');
        else if (data.results.some(r => r.file === id && r.status === 'matched')) node.style('border-color', '#69f0ae');
    });
}

// ── Load graph data ──────────────────────────────────────────────────────────
async function loadGraphData() {
    // Try inline data first (embedded by generate_architecture_graph.py)
    const inlineData = document.getElementById('graph-data');
    if (inlineData) {
        try {
            const data = JSON.parse(inlineData.textContent);
            initGraph(data.elements);
            updateStats(data.elements);
            loadAudit();
            return;
        } catch (e) {
            console.warn('Failed to parse inline data:', e.message);
        }
    }
    // Fallback: try fetch (works when served via HTTP, not file://)
    try {
        const resp = await fetch('architecture_graph_data.json');
        if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
        const data = await resp.json();
        initGraph(data.elements);
        loadAudit();
    } catch (e) {
        console.error('Failed to load graph data:', e.message);
        document.getElementById('cy').innerHTML =
            '<div style="display:flex;align-items:center;justify-content:center;height:100%;color:#7a7a9e;font-size:1.2rem;">' +
            '<div style="text-align:center"><p style="font-size:3rem;margin-bottom:1rem">🧠</p>' +
            '<p>Graph data not found.</p>' +
            '<p style="font-size:0.8rem;margin-top:0.5rem">Run: python scripts/generate_architecture_graph.py</p></div></div>';
    }
}

// ── Bootstrap ────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', loadGraphData);