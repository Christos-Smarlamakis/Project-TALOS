# -*- coding: utf-8 -*-
"""
Module: generate_architecture_graph.py (v2.0)
Project: TALOS v5.10.0
Description:
    Auto-generates the architecture graph data file with ALL imports
    (including standard library and third-party packages).

    Outputs:
        templates/architecture_graph_data.json  — graph data for the HTML/JS viewer
        templates/architecture_graph.html       — HTML shell (if missing)

    Usage:
        python scripts/generate_architecture_graph.py
"""
import os
import ast
import json
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
OUTPUT_DATA = PROJECT_ROOT / "templates" / "architecture_graph_data.json"
SRC_DIR = PROJECT_ROOT / "src"

SKIP_FILES = {
    "__init__.py",
    "_bump.py", "_fix_ai.py", "_fix_now.py", "_fix2.py", "_fix3.py", "_fix4.py",
    "_git_status.ps1", "test_smoke.py",
}

# ── Standard library modules to recognize ────────────────────────────────────
STDLIB_MODULES = {
    "os", "sys", "json", "re", "time", "datetime", "pickle", "sqlite3",
    "stat", "tempfile", "shutil", "logging", "pathlib", "io", "base64",
    "threading", "signal", "random", "platform", "collections",
    "concurrent", "concurrent.futures", "subprocess", "xml", "xml.etree.ElementTree",
    "typing", "ast", "webbrowser", "importlib", "pprint", "hashlib", "fnmatch",
    "glob", "math", "struct", "sysconfig", "inspect", "copy", "textwrap",
    "abc", "enum", "dataclasses", "numbers", "decimal", "fractions",
}

# ── Layer assignments ────────────────────────────────────────────────────────
ENTRY_POINTS = {"talos.py", "app.py"}
CORE_MODULES = {"ai_manager.py", "database_manager.py", "hardware.py"}
CONFIG_ITEMS = {"config.json", ".env", "talos_research.db", "_gui_runner.py",
                "templates/dashboard.html"}

EXTERNAL_SERVICES = {
    "Gemini API": "Google Generative AI — Flash + Pro + Embedding",
    "DeepSeek API": "DeepSeek Cloud — OpenAI-compatible",
    "HuggingFace": "Free Cloud Inference — Router API",
    "Ollama (local)": "Local LLM — gemma3:12b + nomic-embed-text",
    "Discord Webhook": "Daily briefing push via Discord",
    "Zotero API": "Reference Manager Sync",
    "Unpaywall API": "Open Access PDF Discovery",
    "ORCID API": "Researcher Identity & Works",
}

THIRD_PARTY_MODULES = {
    "streamlit": "Streamlit Web GUI framework",
    "questionary": "Interactive CLI prompts",
    "requests": "HTTP client",
    "numpy": "Numerical computing",
    "pandas": "Data analysis library",
    "sklearn": "Machine learning (KMeans, TF-IDF)",
    "matplotlib": "Plotting library",
    "seaborn": "Statistical visualizations",
    "wordcloud": "Word cloud generation",
    "flask": "Web server (Dashboard)",
    "pyzotero": "Zotero API client",
    "elsapy": "Elsevier Scopus client",
    "pymed": "PubMed API client",
    "pyvis": "Network visualization",
    "docx": "Word document generation",
    "google": "Google genai SDK",
    "google.genai": "Google Generative AI SDK",
    "google.generativeai": "Google Gemini SDK",
    "openai": "OpenAI-compatible client",
    "tqdm": "Progress bars",
    "dotenv": "Environment variable loader",
    "duckduckgo_search": "Web search engine",
    "networkx": "Knowledge graph creation",
    "jinja2": "Template engine",
}

FILE_DESCRIPTIONS = {
    "talos.py": "CLI Entry Point — Interactive menu, subprocess orchestrator",
    "app.py": "Streamlit Web GUI — Full CLI replacement, semantic search",
    "ai_manager.py": "AIManager — Multi-provider LLM (Gemini, DeepSeek, HF, Ollama) with circuit breaker",
    "database_manager.py": "DatabaseManager — SQLite + 4-layer scores + cosine similarity search",
    "hardware.py": "GPU detection — nvidia-smi, 30+ quantization formats, model recommendations",
    "daily_search.py": "Daily Search — 14 APIs, two-stage AI eval, Markdown + Discord",
    "historic_search.py": "Historical Deep Archive — Multi-year, database population",
    "grey_literature_miner.py": "Grey Literature — Gemini Search Grounding + DuckDuckGo",
    "knowledge_path_generator.py": "CHIRON — Semantic search + K-Means + AI narrative",
    "citation_analyzer.py": "ORPHEUS — Citation networks via S2 API + pyvis graph",
    "recommender.py": "Strategic Reading Report — TF-IDF clustering, HTML/DOCX/MD",
    "query_translator.py": "PYTHIA — Research goal → queries + prompts via AI",
    "model_manager.py": "Model Manager — Quantization-aware Ollama + cloud model config",
    "profile_manager.py": "Profile Manager — Switch/Create research profiles",
    "db_stats.py": "Database Statistics & Health",
    "metadata_enricher.py": "APOLLO — Multi-source metadata enrichment",
    "embedding_generator.py": "Embedding Generator — Batch vector generation",
    "data_enricher.py": "Data Enricher — Unpaywall OA links + IDs",
    "reevaluate_database.py": "AI Re-evaluation — Flash model batch processing",
    "recalculate_scores.py": "Score Recalculation — Bulk SQLite update",
    "trend_analyzer.py": "Scientometrics — Matplotlib/Seaborn reports",
    "pdf_downloader.py": "PDF Downloader — Unpaywall → OpenAlex → CORE",
    "zotero_connector.py": "Zotero Sync — 'Zotero is Ground Truth' strategy",
    "interactive_dashboard.py": "Flask Dashboard — Tabulator.js data table",
    "api_health_check.py": "API Diagnostics — Pings all configured APIs",
    "migrate_database_schema.py": "Schema Migration — Old analysis regex extraction",
    "author_profiler.py": "Unified Profiler — ORCID + OpenAlex + S2",
    "author_trajectory_analyzer.py": "Trajectory Analyzer — 5-year publication analysis",
    "verify_dependency_map.py": "Dependency Verification — AST-based map audit",
    "generate_architecture_graph.py": "Graph Generator — This script",
}

SOURCE_DESCRIPTIONS = {
    "arxiv_source.py": "arXiv API — Keyless, Atom XML, multi-query",
    "semantic_scholar_source.py": "S2 API — Search, refs, citations, exponential backoff",
    "openalex_source.py": "OpenAlex API — Keyless, ~250M works, inverted index",
    "elsevier_source.py": "Elsevier Scopus — API key + inst token, elsapy",
    "ieee_source.py": "IEEE Xplore — API key, exponential backoff",
    "springer_source.py": "Springer Nature — API key, exponential backoff",
    "core_source.py": "CORE API — Open access repository",
    "crossref_source.py": "Crossref API — DOI registry, search_papers()",
    "dblp_source.py": "DBLP API — Keyless, computer science focus",
    "pubmed_source.py": "PubMed API — Keyless, biomedical, pymed",
    "plos_source.py": "PLOS API — Keyless, open access publisher",
    "scigov_source.py": "Science.gov — Keyless, US government research",
    "osti_source.py": "OSTI.gov — Keyless, DOE research",
    "openarchives_source.py": "OpenArchives.gr — Greek academic repository",
}


def extract_imports(py_file):
    """Extract ALL import statements from a Python file using AST."""
    if not py_file.exists():
        return []
    try:
        with open(py_file, "r", encoding="utf-8") as f:
            source = f.read()
        tree = ast.parse(source, filename=str(py_file))
    except (SyntaxError, UnicodeDecodeError):
        return []

    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.startswith("src."):
                    imports.add(alias.name)
                else:
                    imports.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                if node.module.startswith("src."):
                    imports.add(node.module)
                else:
                    imports.add(node.module.split(".")[0])

    return sorted(imports)


def classify_module(module_name):
    """Classify a module into a layer."""
    if module_name in STDLIB_MODULES:
        return "stdlib"
    if module_name in THIRD_PARTY_MODULES:
        return "thirdparty"
    return None


def get_module_label(module_name, layer):
    """Get a display label and description for a module."""
    if layer == "stdlib":
        return module_name
    if layer == "thirdparty":
        return module_name
    return module_name


def scrape_all_imports():
    """Collect raw import data from all src/ and root files."""
    data = {}
    for py_file in sorted(SRC_DIR.rglob("*.py")):
        if py_file.name in SKIP_FILES or py_file.name == "__init__.py":
            continue
        data[py_file.name] = extract_imports(py_file)
    for py_file in sorted(PROJECT_ROOT.glob("*.py")):
        fname = py_file.name
        if fname.startswith("_") or fname in SKIP_FILES:
            continue
        data[fname] = extract_imports(py_file)
    return data


def build_elements(raw_imports):
    """Build the complete elements (nodes + edges) for Cytoscape."""
    elements = []
    added_nodes = set()
    all_layers = {
        "entry": list(ENTRY_POINTS),
        "core": [f"core/{f}" for f in CORE_MODULES],
        "script": [],
        "source": [],
        "external": list(EXTERNAL_SERVICES.keys()),
        "config": list(CONFIG_ITEMS),
        "stdlib": set(),
        "thirdparty": set(),
    }

    # Collect scripts and sources from the DDD src/ tree
    for py_file in sorted(SRC_DIR.rglob("*.py")):
        fname = py_file.name
        if fname in SKIP_FILES or fname == "__init__.py":
            continue
        if fname == "generate_architecture_graph.py":
            continue
        if fname.endswith("_source.py"):
            all_layers["source"].append(fname)
        elif fname in CORE_MODULES:
            continue  # core modules are handled separately
        else:
            all_layers["script"].append(fname)

    # ── Build nodes ──────────────────────────────────────────────────────
    def add_node(node_id, label, layer, desc=""):
        if node_id in added_nodes:
            return
        added_nodes.add(node_id)
        elements.append({
            "group": "nodes",
            "data": {"id": node_id, "label": label, "layer": layer, "desc": desc}
        })

    # TALOS files
    for fname in all_layers["entry"]:
        add_node(fname, fname, "entry", FILE_DESCRIPTIONS.get(fname, ""))
    for fname in all_layers["core"]:
        label = fname.replace("core/", "")
        add_node(label, label, "core", FILE_DESCRIPTIONS.get(label, ""))
    for fname in all_layers["script"]:
        add_node(fname, fname, "script", FILE_DESCRIPTIONS.get(fname, ""))
    for fname in all_layers["source"]:
        label = fname.replace("sources/", "")
        add_node(label, label, "source", SOURCE_DESCRIPTIONS.get(label, ""))
    for name in all_layers["external"]:
        add_node(name, name, "external", EXTERNAL_SERVICES.get(name, ""))
    for name in all_layers["config"]:
        add_node(name, name.replace("templates/", ""), "config", FILE_DESCRIPTIONS.get(name, ""))

    # Collect stdlib and third-party modules from ALL imports
    all_modules = set()
    for fname, imports in raw_imports.items():
        all_modules.update(imports)

    for mod in sorted(all_modules):
        tp = classify_module(mod)
        if tp:
            label = mod
            desc = THIRD_PARTY_MODULES.get(mod, "Standard library module" if tp == "stdlib" else "")
            add_node(mod, label, tp, desc)

    # ── Build edges ──────────────────────────────────────────────────────
    added_edges = set()

    def add_edge(src, tgt, label):
        key = (src, tgt, label)
        if key in added_edges:
            return
        # Resolve source: strip core/ and sources/ prefixes
        src_clean = src.replace("core/", "").replace("sources/", "")
        tgt_clean = tgt.replace("core/", "").replace("sources/", "")
        if src_clean not in added_nodes or tgt_clean not in added_nodes:
            return
        added_edges.add(key)
        elements.append({
            "group": "edges",
            "data": {"source": src_clean, "target": tgt_clean, "label": label}
        })

    # ── Entry → Core (known imports) ──
    add_edge("talos.py", "database_manager.py", "import")
    add_edge("talos.py", "hardware.py", "import")
    add_edge("talos.py", "profile_manager.py", "import")
    add_edge("talos.py", "config.json", "reads")
    add_edge("app.py", "database_manager.py", "import")
    add_edge("app.py", "ai_manager.py", "import")
    add_edge("app.py", "hardware.py", "import")
    add_edge("app.py", "semantic_scholar_source.py", "import")
    add_edge("app.py", "_gui_runner.py", "wraps via subprocess")
    add_edge("app.py", "templates/dashboard.html", "serves")

    # ── Entry → Scripts (subprocess) ──
    for script in all_layers["script"]:
        add_edge("talos.py", script, "subprocess")

    # ── ALL imports from every file ──
    for fname, imports in raw_imports.items():
        fname_clean = fname.replace("core/", "").replace("sources/", "")
        if fname_clean in ("talos.py", "app.py"):
            continue  # entry points handled above

        for imp in imports:
            # TALOS file import
            if imp.startswith(("core.", "scripts.", "sources.", "src.")):
                parts = imp.split(".")
                if len(parts) >= 2:
                    target = parts[-1] + ".py"
                    add_edge(fname_clean, target, "import")
                continue

            # External service mapping
            if "google" in imp:
                add_edge(fname_clean, "Gemini API", "genai")
            elif "openai" in imp:
                add_edge(fname_clean, "DeepSeek API", "OpenAI client")
            elif "pyzotero" in imp:
                add_edge(fname_clean, "Zotero API", "pyzotero")

            # Module import (stdlib or third-party)
            tp = classify_module(imp)
            if tp:
                add_edge(fname_clean, imp, "import")

    # ── Core → External (known) ──
    add_edge("ai_manager.py", "Gemini API", "genai")
    add_edge("ai_manager.py", "DeepSeek API", "OpenAI client")
    add_edge("ai_manager.py", "HuggingFace", "OpenAI client")
    add_edge("ai_manager.py", "Ollama (local)", "OpenAI + embed")
    add_edge("ai_manager.py", ".env", "reads keys")
    add_edge("ai_manager.py", "hardware.py", "import")
    add_edge("ai_manager.py", "config.json", "reads")
    add_edge("database_manager.py", "talos_research.db", "SQLite CRUD")

    # Core → stdlib/third-party
    for fname in all_layers["core"]:
        label_clean = fname.replace("core/", "")
        for imp in raw_imports.get(label_clean, []):
            tp = classify_module(imp)
            if tp:
                add_edge(label_clean, imp, "import")

    # ── Specific known edges ──
    add_edge("daily_search.py", "Discord Webhook", "HTTP POST")
    add_edge("zotero_connector.py", "Zotero API", "pyzotero")
    add_edge("data_enricher.py", "Unpaywall API", "HTTP")
    add_edge("pdf_downloader.py", "Unpaywall API", "HTTP")
    add_edge("author_profiler.py", "ORCID API", "HTTP")
    add_edge("author_trajectory_analyzer.py", "ORCID API", "HTTP")
    add_edge("author_trajectory_analyzer.py", "author_profiler.py", "import")
    add_edge("grey_literature_miner.py", "Gemini API", "Search Grounding")
    add_edge("trend_analyzer.py", "talos_research.db", "SQLite direct")
    add_edge("recommender.py", "talos_research.db", "SQLite direct")
    add_edge("interactive_dashboard.py", "templates/dashboard.html", "serves")
    add_edge("interactive_dashboard.py", "talos_research.db", "reads")
    add_edge("config.json", ".env", "complements")
    add_edge("profile_manager.py", "query_translator.py", "subprocess")
    add_edge("citation_analyzer.py", "semantic_scholar_source.py", "import")
    add_edge("metadata_enricher.py", "openalex_source.py", "import")
    add_edge("metadata_enricher.py", "crossref_source.py", "import")
    add_edge("metadata_enricher.py", "dblp_source.py", "import")
    add_edge("metadata_enricher.py", "semantic_scholar_source.py", "import")

    return elements


def embed_data_in_html(elements, html_path, stats):
    """Embed graph data directly into the HTML file for file:// compatibility."""
    with open(html_path, "r", encoding="utf-8") as f:
        html = f.read()

    # Remove any existing inline data blocks (from previous generations)
    import re as _re
    html = _re.sub(r'<script id="graph-data" type="application/json">.*?</script>\s*', '', html, flags=_re.DOTALL)

    data_json = json.dumps({"elements": elements, "stats": stats}, indent=2, ensure_ascii=False)

    # Find the closing </body> tag and inject the data script before it
    data_script = f'\n<script id="graph-data" type="application/json">\n{data_json}\n</script>\n'
    html = html.replace("</body>", data_script + "</body>")

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)


def main():
    print("TALOS Architecture Graph Generator v2.1")
    print(f"  Project root: {PROJECT_ROOT}")
    print()

    # Scrape all imports
    raw_imports = scrape_all_imports()
    print(f"  Files scanned: {len(raw_imports)}")

    # Build elements
    elements = build_elements(raw_imports)
    nodes = [e for e in elements if e["group"] == "nodes"]
    edges = [e for e in elements if e["group"] == "edges"]

    # Count per layer
    layers = {}
    for n in nodes:
        layer = n["data"]["layer"]
        layers[layer] = layers.get(layer, 0) + 1

    print(f"  Nodes: {len(nodes)} ({', '.join(f'{k}:{v}' for k,v in sorted(layers.items()))})")
    print(f"  Edges: {len(edges)}")

    stats = {"nodes": len(nodes), "edges": len(edges), "layers": layers}

    # Write JSON data file (for programmatic consumers)
    output = {
        "generated_at": datetime.now().isoformat(),
        "project_version": "v4.11.0",
        "stats": stats,
        "elements": elements,
    }
    with open(OUTPUT_DATA, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    # Embed data directly into HTML for file:// compatibility
    html_path = PROJECT_ROOT / "templates" / "architecture_graph.html"
    embed_data_in_html(elements, html_path, stats)

    print(f"\n  Data saved: {OUTPUT_DATA}")
    print(f"  HTML updated: {html_path}")
    print(f"  Open in browser: file:///{str(html_path).replace(os.sep, '/')}")
    print("\n  Done.")


if __name__ == "__main__":
    main()