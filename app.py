# -*- coding: utf-8 -*-
"""
Module: app.py (Streamlit Web GUI — Complete TALOS CLI Replacement)
Project: TALOS v4.10.1
Description:
    Complete Multi-Page Streamlit Web GUI replicating ALL functionality of
    the TALOS CLI. Every script is executed as a real subprocess.
    User input required by scripts is collected via Streamlit widgets
    and piped through stdin. Auto-confirms questionary.confirm() prompts.
    100% console-free.
"""

import streamlit as st
import sys
import os
import json
import time
import subprocess
from datetime import datetime
import pandas as pd
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.database_manager import DatabaseManager
from core.ai_manager import AIManager

# ═══════════════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="Project TALOS — Research Intelligence Platform",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ═══════════════════════════════════════════════════════════════════════════════
if "db" not in st.session_state:
    st.session_state.db = DatabaseManager()

if "config" not in st.session_state:
    cfg = os.path.join(os.path.dirname(__file__), "config.json")
    tpl = os.path.join(os.path.dirname(__file__), "config.template.json")
    try:
        with open(cfg, "r", encoding="utf-8") as f:
            st.session_state.config = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        with open(tpl, "r", encoding="utf-8") as f:
            st.session_state.config = json.load(f)

if "ai" not in st.session_state:
    st.session_state.ai = AIManager(st.session_state.config)

if "output" not in st.session_state:
    st.session_state.output = {}

# ═══════════════════════════════════════════════════════════════════════════════
def get_active_profile():
    d = os.path.join(os.path.dirname(__file__), "_profiles")
    f = os.path.join(d, "active_profile.txt")
    return open(f).read().strip() if os.path.exists(f) else "default"

def system_info():
    import platform
    return {"sys": platform.system(), "py": platform.python_version(),
            "prov": st.session_state.config.get("ai_provider_priority", ["gemini"])[0]}

def run(name, args=None, stdin_text="", confirm="y"):
    """Execute a TALOS script via _gui_runner.py wrapper (patches questionary).
    Input is passed via TALOS_GUI_STDIN env var (not stdin pipe — unreliable on Windows).
    """
    exe = sys.executable
    root = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(root, "scripts", name)
    if not os.path.exists(path):
        return -1, f"Script not found: {path}"
    wrapper = os.path.join(root, "_gui_runner.py")
    cmd = [exe, wrapper, path] + (args or [])
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["TALOS_GUI_STDIN"] = stdin_text
    env["TALOS_GUI_STDIN_CONFIRM"] = confirm
    try:
        r = subprocess.run(
            cmd, capture_output=True, text=True, timeout=600, env=env,
            encoding="utf-8", errors="replace"
        )
        return r.returncode, r.stdout + "\n" + r.stderr
    except subprocess.TimeoutExpired:
        return -1, "Timeout (10 min)."
    except Exception as e:
        return -1, str(e)

def show_output(key, label):
    """Display script output and parse any generated report file."""
    if key not in st.session_state.output:
        return
    output = st.session_state.output[key]
    with st.expander(f"📋 Console Output: {label}", expanded=True):
        st.code(output[:8000])
    # Try to find and display report file
    report_path = _extract_report_path(output)
    if report_path and os.path.exists(report_path):
        st.markdown("---")
        st.success(f"📄 Report saved: `{report_path}`")
        try:
            with open(report_path, "r", encoding="utf-8") as f:
                content = f.read()
            # For markdown files, render them
            if report_path.endswith(".md"):
                with st.container(border=True):
                    st.markdown(content[:10000])
            elif report_path.endswith(".html"):
                st.caption("🌐 HTML report — open in browser to view interactive content.")
                with st.container(border=True):
                    st.components.v1.html(content[:50000], height=600, scrolling=True)
            else:
                with st.container(border=True):
                    st.code(content[:5000])
        except Exception as e:
            st.caption(f"Could not read report: {e}")

def _extract_report_path(output):
    """Extract report file path from script output text."""
    import re
    # Pattern 1: "SUCCESS: Η αναφορά αποθηκεύτηκε με επιτυχία στο:\npath"
    m = re.search(r'(?:SUCCESS|INFO):.*αποθηκεύτηκε.*\n\s*(.+)', output)
    if m:
        return m.group(1).strip()
    # Pattern 2: "Report saved:\npath" or "Report Generated Successfully: path"
    m = re.search(r'(?:Report saved|Report Generated Successfully):\s*(.+)', output)
    if m:
        return m.group(1).strip()
    # Pattern 3: Any path-like string with reports/ in it
    m = re.search(r'(?:reports[\\/][^\s]+\.(?:md|html|txt))', output)
    if m:
        return m.group(0).strip()
    return None

def reload_config():
    cfg = os.path.join(os.path.dirname(__file__), "config.json")
    if os.path.exists(cfg):
        with open(cfg, "r", encoding="utf-8") as f:
            st.session_state.config = json.load(f)
        st.session_state.ai = AIManager(st.session_state.config)

def reload_db():
    st.session_state.db = DatabaseManager()

# ═══════════════════════════════════════════════════════════════════════════════
st.markdown("""<style>
.main-header{background:linear-gradient(135deg,#1a1a2e,#16213e,#0f3460);padding:1.8rem 2rem;border-radius:12px;margin-bottom:1.2rem;border:1px solid rgba(255,255,255,.08)}
.main-header h1{color:#e94560;font-size:2.2rem;font-weight:700;margin:0}
.main-header p{color:#a0a0b0;font-size:1rem;margin:.4rem 0 0}
[data-testid="stMetricValue"]{font-size:1.8rem!important;font-weight:700!important}
.stButton>button{border-radius:8px;font-weight:600;transition:all .2s}
.stButton>button:hover{transform:translateY(-1px);box-shadow:0 4px 12px rgba(0,0,0,.2)}
</style>""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("""<div style="text-align:center;padding:1rem 0">
    <h2 style="color:#e94560;margin:0;font-size:1.5rem">🧠 TALOS v4.10.1</h2>
    <p style="color:#8b949e;font-size:.75rem;margin:.2rem 0 0">Research Intelligence Platform</p></div>""", unsafe_allow_html=True)
    st.markdown("---")

    page = st.radio("📍 Navigation", [
        "🏠 Home & Knowledge Base",
        "🔍 Search & Discovery",
        "🧪 Single Paper Evaluation",
        "📊 Analysis & Insights",
        "🛠️ Database Maintenance",
        "⚙️ Settings",
    ], label_visibility="collapsed")

    st.markdown("---")
    si = system_info()
    ap = get_active_profile()
    st.markdown(f"**Profile:** `{ap}`")
    st.markdown(f"**Provider:** {si['prov'].title()}")
    st.markdown(f"**Python:** {si['py']}")
    try:
        s = st.session_state.db.get_database_statistics()
        st.markdown("---")
        st.caption(f"📚 {s['total_papers']} papers · ⭐ {s['elite_papers']} elite · 📊 {s['avg_score']:.1f} avg")
    except Exception:
        pass

    st.markdown("---")
    st.markdown("### ☁️ AI Provider")
    if "provider_mode" not in st.session_state:
        st.session_state.provider_mode = "CLOUD (Gemini + DeepSeek)"
    if "allow_fallback" not in st.session_state:
        st.session_state.allow_fallback = True

    provider_choice = st.sidebar.radio(
        "Where to run AI calls?",
        ["CLOUD (Gemini + DeepSeek)", "LOCAL (Ollama / Gemma 3 12B)"],
        index=0 if "CLOUD" in st.session_state.provider_mode else 1,
        horizontal=True, key="provider_radio"
    )
    if provider_choice != st.session_state.provider_mode:
        st.session_state.provider_mode = provider_choice
        if "LOCAL" in provider_choice:
            st.session_state.config["ai_provider_priority"] = ["local", "gemini", "deepseek"]
            os.environ["TALOS_USE_LOCAL"] = "1"
        else:
            st.session_state.config["ai_provider_priority"] = ["gemini", "deepseek"]
            os.environ.pop("TALOS_USE_LOCAL", None)
        try:
            st.session_state.ai = AIManager(st.session_state.config)
            st.sidebar.success(f"✅ Switched to {provider_choice.split('(')[0].strip()}")
        except Exception as e:
            st.sidebar.warning(f"Error: {e}")

    fallback = st.sidebar.checkbox(
        "Allow cloud fallback" if "LOCAL" in st.session_state.provider_mode else "Allow local fallback",
        value=st.session_state.allow_fallback
    )
    if fallback != st.session_state.allow_fallback:
        st.session_state.allow_fallback = fallback
        if "LOCAL" in st.session_state.provider_mode:
            os.environ["TALOS_ALLOW_CLOUD_FALLBACK"] = "1" if fallback else "0"
        else:
            os.environ["TALOS_ALLOW_LOCAL_FALLBACK"] = "1" if fallback else "0"

    st.sidebar.caption(f"Priority: {' → '.join(st.session_state.config.get('ai_provider_priority', ['gemini']))}")

# ═══════════════════════════════════════════════════════════════════════════════
st.markdown("""<div class="main-header"><h1>🧠 Project TALOS</h1>
<p>AI-Powered Research Intelligence & Knowledge Discovery Platform — Full Web GUI</p></div>""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# 1. HOME & KNOWLEDGE BASE
# ═══════════════════════════════════════════════════════════════════════════════
if page == "🏠 Home & Knowledge Base":
    st.header("🏠 Home — Knowledge Base Overview")
    try:
        s = st.session_state.db.get_database_statistics()
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("📚 Papers", s["total_papers"])
        c2.metric("⭐ Elite (>7)", s["elite_papers"])
        c3.metric("📊 Avg Score", f"{s['avg_score']:.1f}")
        c4.metric("🔗 With DOI", s["total_papers"] - s["missing_doi"])
        c5.metric("🧠 Embedded", s["embedded_papers"])
    except Exception as e:
        st.warning(f"Database unavailable: {e}")

    st.markdown("---")
    dash_tab1, dash_tab2 = st.tabs(["📋 Full Paper Table", "📊 Analytics"])

    with dash_tab1:
        st.subheader("📋 Knowledge Base — All Papers")
        cf1, cf2, cf3, cf4, cf5, cf6 = st.columns(6)
        with cf1:
            if st.button("⭐ Core (≥7)", width="stretch", key="f_core"):
                st.session_state._filter = "core"
        with cf2:
            if st.button("🔴 Strategic ≥7", width="stretch", key="f_str"):
                st.session_state._filter = "strategic"
        with cf3:
            if st.button("🟣 Operational ≥7", width="stretch", key="f_opr"):
                st.session_state._filter = "operational"
        with cf4:
            if st.button("🔵 Tactical ≥7", width="stretch", key="f_tac"):
                st.session_state._filter = "tactical"
        with cf5:
            if st.button("🟡 Playground ≥7", width="stretch", key="f_ply"):
                st.session_state._filter = "playground"
        with cf6:
            if st.button("🗑️ Clear", width="stretch", key="f_clr"):
                st.session_state._filter = None

        sem_col1, sem_col2 = st.columns([3, 1])
        with sem_col1:
            sem_query = st.text_input("🔎 Semantic Search", placeholder="Search by meaning...", key="sem_q")
        with sem_col2:
            if st.button("🔍 Search", width="stretch", key="sem_btn") and sem_query:
                with st.spinner("Searching..."):
                    try:
                        vec = st.session_state.ai.generate_embeddings([sem_query])
                        if vec and vec[0]:
                            ids = st.session_state.db.semantic_search(np.array(vec[0]), top_k=50)
                            st.session_state._sem_ids = ids
                            st.success(f"Found {len(ids)} matches")
                    except Exception as e:
                        st.warning(f"Unavailable: {e}")

        try:
            papers = st.session_state.db.get_all_papers_for_dashboard()
            if papers:
                df = pd.DataFrame(papers)
                filt = st.session_state.get("_filter")
                if filt == "core":       df = df[df["overall_score"] >= 7]
                elif filt == "strategic": df = df[df["strategic_score"] >= 7]
                elif filt == "operational": df = df[df["operational_score"] >= 7]
                elif filt == "tactical": df = df[df["tactical_score"] >= 7]
                elif filt == "playground": df = df[df["playground_score"] >= 7]
                sem_ids = st.session_state.get("_sem_ids")
                if sem_ids and "id" in df.columns:
                    df = df[df["id"].isin(sem_ids)]

                dc = ["title","authors","source","publication_year","strategic_score","operational_score","tactical_score","playground_score","overall_score"]
                dc = [c for c in dc if c in df.columns]
                df2 = df[dc].head(100).copy()

                st.dataframe(df2, width="stretch", height=500,
                    column_config={
                        "strategic_score": st.column_config.ProgressColumn("🔴 Strategic", format="%d/10", min_value=0, max_value=10),
                        "operational_score": st.column_config.ProgressColumn("🟣 Operational", format="%d/10", min_value=0, max_value=10),
                        "tactical_score": st.column_config.ProgressColumn("🔵 Tactical", format="%d/10", min_value=0, max_value=10),
                        "playground_score": st.column_config.ProgressColumn("🟡 Playground", format="%d/10", min_value=0, max_value=10),
                        "overall_score": st.column_config.NumberColumn("⭐ Overall", format="%.1f"),
                    })
            else:
                st.info("📭 No papers yet. Run a Search to populate the database.")
        except Exception as e:
            st.warning(f"Could not load: {e}")

    with dash_tab2:
        cl, cr = st.columns(2)
        with cl:
            st.subheader("📈 Papers by Source")
            try:
                if s.get("by_source"):
                    sd = pd.DataFrame(s["by_source"], columns=["Source","Count"])
                    st.bar_chart(sd.set_index("Source"), width="stretch")
            except Exception: pass
        with cr:
            st.subheader("🏥 Database Health")
            try:
                hd = {"With DOIs": s["total_papers"]-s["missing_doi"], "Missing DOIs": s["missing_doi"],
                      "With Embeddings": s["embedded_papers"], "Enriched": s.get("enriched_papers",0),
                      "PDF Links": s.get("pdf_links",0)}
                st.dataframe(pd.DataFrame(list(hd.items()), columns=["Metric","Count"]), width="stretch", hide_index=True)
            except Exception: pass

# ═══════════════════════════════════════════════════════════════════════════════
# 2. SEARCH & DISCOVERY
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "🔍 Search & Discovery":
    st.header("🔍 Search & Discovery")
    t1, t2, t3 = st.tabs(["📰 Daily Search", "📚 Historical Archive", "🌐 Grey Literature"])

    with t1:
        st.subheader("📰 Daily Search — 14 Academic APIs")
        st.caption(f"Days: {st.session_state.config.get('days_to_search_daily',7)} · Min Score: {st.session_state.config.get('min_pre_screening_score',6)}")
        if st.button("🚀 Run Daily Search", type="primary", key="b1"):
            with st.spinner("Running daily search across 14 APIs..."):
                rc, out = run("daily_search.py")
                st.session_state.output["daily"] = out
            if rc == 0:
                st.success("✅ Daily Search complete!"); reload_db()
            else:
                st.warning(f"Completed (code {rc}).")
            show_output("daily", "daily_search.py")

    with t2:
        st.subheader("📚 Historical Search — Deep Archive")
        st.caption(f"Past {st.session_state.config.get('days_to_search_historic',365)} days.")
        if st.button("📜 Run Historical Search", type="primary", key="b2"):
            st.warning("⚠️ May take several minutes.")
            with st.spinner("Running historical search..."):
                # Historical search asks for confirm via questionary — auto-answer "y"
                rc, out = run("historic_search.py", stdin_text="y\n")
                st.session_state.output["historic"] = out
            if rc == 0:
                st.success("✅ Historical Search complete!"); reload_db()
            else:
                st.warning(f"Completed (code {rc}).")
            show_output("historic", "historic_search.py")

    with t3:
        st.subheader("🌐 Grey Literature / Web Horizon Scan")
        st.caption("Searches web sources, pre-prints, non-academic publications. Uses DuckDuckGo + Gemini Search Grounding.")
        grey_topic = st.text_input("Research topic to scan for:", placeholder="e.g. 'autonomous drone swarms open source'", key="grey_topic")
        if st.button("🌍 Run Horizon Scan", type="primary", key="b3"):
            if not grey_topic.strip():
                st.error("Please enter a research topic.")
            else:
                with st.spinner(f"Scanning for '{grey_topic}'..."):
                    # grey_literature_miner.py asks: topic → questionary.text()
                    rc, out = run("grey_literature_miner.py", stdin_text=grey_topic + "\n")
                    st.session_state.output["grey"] = out
                if rc == 0:
                    st.success("✅ Horizon scan complete!")
                else:
                    st.warning(f"Completed (code {rc}).")
                show_output("grey", "grey_literature_miner.py")

# ═══════════════════════════════════════════════════════════════════════════════
# 3. SINGLE PAPER EVALUATION
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "🧪 Single Paper Evaluation":
    st.header("🧪 Single Paper Evaluation — Quad-Layer Framework")
    
    # Framework explanation
    with st.expander("ℹ️ About the Quad-Layer Framework", expanded=False):
        st.markdown("""
| Layer | Measures | Weight |
|---|---|---|
| 🔴 **Strategic** | Long-term research alignment & impact potential | 30% |
| 🟣 **Operational** | Practical applicability & deployment readiness | 30% |
| 🔵 **Tactical** | Technical depth, methodology & implementation quality | 30% |
| 🟡 **Playground** | Novelty, creativity & exploratory research value | 10% |
""")

    # Input method tabs
    tab1, tab2, tab3 = st.tabs(["📝 Paste Abstract", "🔗 Fetch by DOI", "📄 Select from DB"])
    
    abstract = ""
    
    # Tab 1: Paste abstract
    with tab1:
        abstract = st.text_area("📝 Enter Paper Abstract", height=160, 
                                placeholder="Paste the paper abstract here (min. 50 characters)...", 
                                key="abs_paste")
        demo_col1, demo_col2 = st.columns([1, 3])
        with demo_col1:
            if st.button("📋 Load Demo", width="stretch", key="demo1"):
                st.session_state._demo_abs = (
                    "We present a novel framework for multi-agent reinforcement learning for autonomous "
                    "drone swarm operations in urban environments. Our approach combines hierarchical task "
                    "decomposition with emergent communication protocols, achieving 47% improvement in "
                    "mission completion rates. The system was validated across 1,200 simulated missions "
                    "spanning search-and-rescue, infrastructure inspection, and delivery scenarios.")
                st.rerun()
        demo_abs = st.session_state.get("_demo_abs", "")
        if demo_abs and not abstract:
            abstract = demo_abs
    
    # Tab 2: Fetch by DOI
    with tab2:
        doi_input = st.text_input("🔗 Enter DOI or Semantic Scholar URL:", 
                                   placeholder="e.g. '10.48550/arxiv.2506.12345' or 'https://doi.org/...'",
                                   key="doi_input")
        fetch_col1, fetch_col2 = st.columns([1, 3])
        with fetch_col1:
            fetch_doi = st.button("🔍 Fetch Paper", type="primary", width="stretch", key="btn_fetch_doi")
        if fetch_doi and doi_input:
            with st.spinner("Fetching paper details..."):
                # Try database first
                paper = st.session_state.db.get_single_paper_details_by_doi(doi_input) if hasattr(st.session_state.db, 'get_single_paper_details_by_doi') else None
                if not paper:
                    # Try Semantic Scholar
                    try:
                        from sources.semantic_scholar_source import SemanticScholarSource
                        s2 = SemanticScholarSource(st.session_state.config)
                        # Clean DOI
                        clean_doi = doi_input.strip()
                        if 'doi.org/' in clean_doi:
                            clean_doi = clean_doi.split('doi.org/')[-1]
                        paper_data = s2.get_paper_details(clean_doi)
                        if paper_data:
                            abstract = paper_data.get('abstract', '') or paper_data.get('title', '')
                            st.session_state._fetched_title = paper_data.get('title', '')
                            st.session_state._fetched_authors = paper_data.get('authors_str', '') or ', '.join([a.get('name', '') for a in paper_data.get('authors', [])]) if paper_data.get('authors') else ''
                            st.session_state._fetched_year = paper_data.get('publication_year', paper_data.get('year', ''))
                            st.success(f"✅ Found: **{paper_data.get('title', 'Unknown')[:100]}**")
                            st.caption(f"{st.session_state._fetched_authors} · {st.session_state._fetched_year}")
                    except Exception as e:
                        st.warning(f"Could not fetch from Semantic Scholar: {e}")
                else:
                    abstract = paper.get('abstract', '')
                    st.session_state._fetched_title = paper.get('title', '')
                    st.session_state._fetched_authors = paper.get('authors', '')
                    st.session_state._fetched_year = paper.get('publication_year', '')
                    st.success(f"✅ Found in database: **{paper.get('title', 'Unknown')[:100]}**")
                if abstract:
                    st.text_area("📄 Retrieved Abstract:", value=abstract, height=150, key="abs_fetched")
    
    # Tab 3: Select from DB
    with tab3:
        try:
            papers = st.session_state.db.get_all_papers_for_dashboard()
            if papers:
                df = pd.DataFrame(papers)
                paper_opts = {f"[{p['overall_score']:.1f}] {p['title'][:100]}": i for i, p in enumerate(papers)}
                selected = st.selectbox("Select a paper from your Knowledge Base:", [""] + list(paper_opts.keys()), key="db_select")
                if selected and paper_opts.get(selected) is not None:
                    idx = paper_opts[selected]
                    abstract = papers[idx].get('abstract', '')
                    st.text_area("📄 Abstract:", value=abstract[:3000] if abstract else "(No abstract available)", height=150, key="abs_db")
        except Exception as e:
            st.caption(f"Could not load papers: {e}")
    
    # Paper info display (if fetched)
    if st.session_state.get("_fetched_title"):
        st.markdown(f"**📄 {st.session_state._fetched_title}**")
        st.caption(f"{st.session_state._fetched_authors} · {st.session_state._fetched_year}")
    
    st.markdown("---")
    
    # Evaluate button
    if st.button("🔬 Analyze Paper", type="primary", width="stretch", key="btn_eval"):
        if not abstract or len(abstract.strip()) < 50:
            st.error("⚠️ Please provide an abstract (min. 50 characters). Use the Paste, DOI fetch, or DB tabs above.")
        else:
            with st.spinner("🧠 Evaluating with AI models..."):
                try:
                    sp = st.session_state.config.get("phd_focus_system_prompt")
                    result = st.session_state.ai.evaluate_paper_json(abstract, model_type="pro", system_prompt_override=sp)
                    if result:
                        st.session_state._eval = result
                        st.success("✅ Evaluation complete!")
                    else:
                        st.error("❌ All AI providers failed. Check API keys in .env file.")
                except Exception as e:
                    st.error(f"Error: {e}")

    # Display results
    if "_eval" in st.session_state and st.session_state._eval:
        r = st.session_state._eval
        sc = r.get("scores", {})
        st.markdown("---")
        st.subheader("📊 Quad-Layer Evaluation Results")
        
        # Score cards
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("🔴 Strategic", f"{sc.get('strategic',0)}/10", help="Long-term research alignment & impact")
        c2.metric("🟣 Operational", f"{sc.get('operational',0)}/10", help="Practical applicability & deployment readiness")
        c3.metric("🔵 Tactical", f"{sc.get('tactical',0)}/10", help="Technical depth & implementation quality")
        c4.metric("🟡 Playground", f"{sc.get('playground',0)}/10", help="Novelty, creativity & exploratory value")

        # Overall score
        ov = r.get("overall_score", 0)
        st.markdown(f"### 🎯 Overall Score: **{ov:.1f} / 10**")
        st.progress(min(ov/10, 1.0))

        # Score bars
        for layer, clr, lbl in [("strategic","#e74c3c","Strategic"),("operational","#9b59b6","Operational"),
                                 ("tactical","#3498db","Tactical"),("playground","#f1c40f","Playground")]:
            v = sc.get(layer, 0)
            st.markdown(
                f'<div style="display:flex;align-items:center;margin:6px 0">'
                f'<span style="width:110px;font-weight:600;color:{clr}">{lbl}</span>'
                f'<div style="flex:1;background:#2d2d2d;border-radius:6px;height:24px;margin:0 10px">'
                f'<div style="width:{v*10}%;background:{clr};border-radius:6px;height:24px;'
                f'display:flex;align-items:center;justify-content:center;color:white;font-weight:600;font-size:.8rem">'
                f'{v}/10</div></div></div>', unsafe_allow_html=True)

        # Detailed analysis
        with st.expander("📝 Detailed Analysis", expanded=True):
            for k, lab in [("reasoning","💭 Reasoning"),("contribution","🔬 Contribution"),("utilization","🔧 Utilization")]:
                if r.get(k): 
                    st.markdown(f"**{lab}:**")
                    st.write(r[k])
        
        # Tags
        if r.get("tags"):
            st.markdown("**🏷️ Tags:** " + " ".join(
                [f'<span style="background:#30363d;color:#e6edf3;padding:4px 10px;border-radius:12px;font-size:.8rem;margin:2px">{t}</span>' 
                 for t in r["tags"]]), unsafe_allow_html=True)
        
        # Folder / Channel suggestions
        if r.get("folder") or r.get("discord_channel"):
            st.caption(f"📁 Suggested folder: `{r.get('folder', 'N/A')}` | 📢 Discord channel: `{r.get('discord_channel', 'N/A')}`")

        with st.expander("🔧 Raw JSON Response"):
            st.json(r)

# ═══════════════════════════════════════════════════════════════════════════════
# 4. ANALYSIS & INSIGHTS
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "📊 Analysis & Insights":
    st.header("📊 Analysis & Insights")
    opt = st.selectbox("Analysis Tool", [
        "📖 Knowledge Path Generator (CHIRON)",
        "🔗 Citation Network Analyzer (ORPHEUS)",
        "📊 Strategic Reading Report (Recommender)",
        "👤 Author Analysis Tools",
        "🖥️ Interactive Dashboard (Legacy)",
    ])
    st.markdown("---")

    if "CHIRON" in opt:
        st.subheader("📖 CHIRON — Knowledge Path Generator")
        st.caption("Personalized reading path using semantic search + K-Means clustering.")
        chiron_goal = st.text_input("What do you want to learn in depth today?",
                                    placeholder="e.g. 'reinforcement learning for autonomous drone swarms'",
                                    key="chiron_goal")
        if st.button("🧭 Generate Knowledge Path", type="primary", key="bc"):
            if not chiron_goal.strip() or len(chiron_goal.strip()) < 10:
                st.error("Please describe your research goal (min. 10 characters).")
            else:
                with st.spinner("CHIRON is analyzing your knowledge base..."):
                    rc, out = run("knowledge_path_generator.py", stdin_text=chiron_goal + "\n")
                    st.session_state.output["chiron"] = out
                if rc == 0: st.success("✅ Knowledge path generated!")
                else: st.warning(f"Completed (code {rc}).")
                show_output("chiron", "knowledge_path_generator.py")

    elif "ORPHEUS" in opt:
        st.subheader("🔗 ORPHEUS — Citation Network Analyzer")
        st.caption("Analyzes citation networks around a target paper.")
        doi_input = ""
        try:
            core = st.session_state.db.get_recent_core_papers(limit=10, min_score=7.0)
            if core:
                opts = {f"[{p['overall_score']:.1f}] {p['title'][:80]}": p['doi'] for p in core if p.get('doi')}
                selected_title = st.selectbox("Select a Core Paper from DB:", [""] + list(opts.keys()))
                doi_input = opts.get(selected_title, "") if selected_title else ""
        except Exception:
            pass
        manual_doi = st.text_input("Or enter DOI manually:", value=doi_input)
        final_doi = manual_doi if manual_doi else doi_input

        if st.button("🔍 Analyze Citation Network", type="primary", key="bo"):
            if not final_doi:
                st.error("Please select a paper or enter a DOI.")
            else:
                # citation_analyzer asks: select method (1 or 2) → then DOI
                # We send: "1\nDOI\n" (option 1 = manual entry)
                stdin_input = f"1\n{final_doi}\n"
                with st.spinner("ORPHEUS is mapping citation networks..."):
                    rc, out = run("citation_analyzer.py", stdin_text=stdin_input)
                    st.session_state.output["orpheus"] = out
                if rc == 0: st.success("✅ Citation analysis complete!")
                else: st.warning(f"Completed (code {rc}).")
                show_output("orpheus", "citation_analyzer.py")

    elif "Reading" in opt:
        st.subheader("📊 Strategic Reading Report (Recommender)")
        st.caption("TF-IDF clustering + AI analysis for thematic reading recommendations.")
        if st.button("📋 Generate Reading Report", type="primary", key="br"):
            with st.spinner("Generating strategic reading report..."):
                rc, out = run("recommender.py")
                st.session_state.output["recommender"] = out
            if rc == 0: st.success("✅ Reading report generated!")
            else: st.warning(f"Completed (code {rc}).")
            show_output("recommender", "recommender.py")

    elif "Author" in opt:
        st.subheader("👤 Author Analysis Tools")
        at = st.radio("Tool:", ["Quick Profile", "Trajectory Analysis", "Full Report"], horizontal=True)
        author_input = st.text_input("👤 Author Name or ORCID iD", placeholder="e.g. 'Geoffrey Hinton'")
        if st.button("🔍 Analyze Author", type="primary", key="ba"):
            if not author_input:
                st.error("Enter a name or ORCID iD.")
            else:
                # author_profiler.py takes identifier as command-line arg
                with st.spinner(f"Analyzing '{author_input}'..."):
                    if "Quick" in at or "Full" in at:
                        rc, out = run("author_profiler.py", args=[author_input])
                        st.session_state.output["author"] = out
                    if "Trajectory" in at or "Full" in at:
                        rc2, out2 = run("author_trajectory_analyzer.py", args=[author_input])
                        st.session_state.output["traj"] = out2
                if rc == 0: st.success("✅ Author analysis complete!")
                else: st.warning(f"Completed (code {rc}).")
                show_output("author", "author_profiler.py")

    elif "Dashboard" in opt:
        st.subheader("🖥️ Interactive Dashboard (Legacy Flask)")
        st.caption("Launches the Flask/Tabulator.js dashboard on port 5000.")
        if st.button("🚀 Launch Dashboard", type="primary", key="bd"):
            st.info("Opens at http://localhost:5000")
            with st.spinner("Starting dashboard server..."):
                rc, out = run("interactive_dashboard.py")
                st.session_state.output["dash"] = out
            if rc in [0,1,2]: st.success("Dashboard server terminated.")
            else: st.warning(f"Code {rc}.")
            show_output("dash", "interactive_dashboard.py")

# ═══════════════════════════════════════════════════════════════════════════════
# 5. DATABASE MAINTENANCE
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "🛠️ Database Maintenance":
    st.header("🛠️ Database Maintenance")
    mo = st.selectbox("Task", [
        "📊 Statistics & Health", "📝 APOLLO Metadata Enrichment", "📚 Zotero Sync",
        "🧠 Embedding Generator", "🔄 AI Re-evaluation", "🔗 Data Enrichment (Unpaywall)",
        "📈 Scientometrics Report", "📥 PDF Downloader (Open Access)",
    ])
    st.markdown("---")

    MAP = {
        "Statistics": ("db_stats.py", "Database Statistics"),
        "APOLLO": ("metadata_enricher.py", "APOLLO Metadata Enrichment"),
        "Zotero": ("zotero_connector.py", "Zotero Sync"),
        "Embedding": ("embedding_generator.py", "Embedding Generator"),
        "Re-evaluation": ("reevaluate_database.py", "AI Re-evaluation"),
        "Data Enrichment": ("data_enricher.py", "Data Enrichment (Unpaywall)"),
        "Scientometrics": ("trend_analyzer.py", "Scientometrics Report"),
        "PDF": ("pdf_downloader.py", "PDF Downloader"),
    }
    for kw, (scr, lbl) in MAP.items():
        if kw in mo:
            st.subheader(f"📋 {lbl}")
            if st.button(f"▶️ Run {lbl}", type="primary", key=f"bm_{kw}"):
                # Scripts with questionary.confirm() need "y" via stdin
                stdin = "y\n" if kw in ("APOLLO", "Re-evaluation") else ""
                with st.spinner(f"Running {lbl}..."):
                    rc, out = run(scr, stdin_text=stdin)
                    st.session_state.output[kw] = out
                if rc == 0:
                    st.success(f"✅ {lbl} complete!")
                    if kw in ("Statistics", "APOLLO", "Zotero", "Embedding", "Re-evaluation", "Data Enrichment"):
                        reload_db()
                else: st.warning(f"Completed (code {rc}).")
                show_output(kw, scr)

# ═══════════════════════════════════════════════════════════════════════════════
# 6. SETTINGS (Unified: API Keys + Profiles + PYTHIA + Health Check)
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "⚙️ Settings":
    st.header("⚙️ Settings")
    
    tab_api, tab_profile, tab_health = st.tabs(["🔑 API Keys & Models", "📂 Profiles & PYTHIA", "🩺 Diagnostics"])
    
    # ── TAB 1: API Keys & Model Selection ──
    with tab_api:
        st.subheader("API Keys & Local Models")
        st.markdown("TALOS works with **100% free, keyless APIs**. Premium keys are strictly optional.")
        
        from dotenv import set_key as _set_key
        env_path = os.path.join(os.path.dirname(__file__), ".env")
        if not os.path.exists(env_path):
            open(env_path, "w", encoding="utf-8").close()
        
        def _save_env(key, value):
            _set_key(env_path, key, value.strip())
            os.environ[key] = value.strip()
        
        # ── Tier 1: Free & Keyless ──
        from core.hardware import (
            detect_vram_gb, get_all_chat_models_sorted, get_embedding_models, pull_model,
            MODEL_SIZES, estimate_size_for_quant, VRAM_HEADROOM, extract_params_b
        )
        vram = detect_vram_gb()
        chat_models = get_all_chat_models_sorted(vram)
        embedding_models = get_embedding_models()
        
        col_email, col_vram = st.columns(2)
        with col_email:
            mailto = st.text_input("📧 Contact Email", 
                                   value=os.getenv("MAILTO", st.session_state.config.get("mailto", "")),
                                   placeholder="your@email.com")
        with col_vram:
            if vram:
                vram_limit = vram * VRAM_HEADROOM
                st.metric("🖥️ GPU VRAM", f"{vram:.1f} GB", f"{vram_limit:.1f}GB usable (70%)")
            else:
                vram_limit = None
                st.info("GPU not detected")
        
        # Chat model selector with 3 sections
        st.markdown("#### 🧠 Chat Model")
        chat_options = []
        chat_index = 0
        current_chat = os.getenv("LOCAL_MODEL_NAME", "")
        
        installed = [m for m in chat_models if m.get("installed")]
        if installed:
            chat_options.append("─── 📥 Installed on this PC ───")
            for m in installed:
                fit_badge = ""
                if vram_limit and m['size_gb'] <= vram_limit:
                    fit_badge = " [FITS ✓]"
                elif vram_limit:
                    fit_badge = " [TOO BIG ✗]"
                label = f"   ✅ {m['name']} ({m['size_gb']}GB){fit_badge}"
                chat_options.append(label)
                if m["name"] == current_chat:
                    chat_index = len(chat_options) - 1
        
        library = [m for m in chat_models if not m.get("installed") and m.get("section") == "library"]
        if library:
            chat_options.append("─── 📡 Available via Ollama ───")
            for m in library:
                fit_badge = ""
                if vram_limit and m['size_gb'] <= vram_limit:
                    fit_badge = " [FITS ✓]"
                elif vram_limit:
                    fit_badge = " [TOO BIG ✗]"
                chat_options.append(f"   📥 {m['name']} ({m['size_gb']}GB){fit_badge}")
                if m["name"] == current_chat: chat_index = len(chat_options) - 1
                elif not current_chat and not installed and chat_index == 0: chat_index = len(chat_options) - 1
        
        bitnet = [m for m in chat_models if m.get("section") == "bitnet"]
        if bitnet:
            chat_options.append("─── ⚡ BitNet 1-bit (Edge/CPU) ───")
            for m in bitnet:
                desc = m.get("description", "")
                chat_options.append(f"   📥 {m['name']} ({m['size_gb']}GB)" + (f" — {desc}" if desc else ""))
        
        selected_chat_label = st.selectbox("Select chat model:", chat_options, index=chat_index if chat_options else 0, key="chat_model_select")
        if selected_chat_label.startswith("───"):
            st.warning("Please select an actual model, not a section header.")
            selected_chat = chat_models[0]["name"] if chat_models else ""
        else:
            selected_chat = selected_chat_label.strip().split(" ")[1]
        
        # Quantization selector
        quant_tag = ""
        if selected_chat:
            common_quants = ["q8_0", "q6_K", "q5_K_M", "q4_K_M", "q4_0", "q3_K_M", "q2_K", "q1_0"]
            quant_options = ["(base / default)"]
            for q in common_quants:
                est = estimate_size_for_quant(selected_chat, q)
                fit_badge = ""
                if vram_limit and est <= vram_limit:
                    fit_badge = " [FITS ✓]"
                elif vram_limit:
                    fit_badge = " [TOO BIG ✗]"
                if est and est < 99:
                    quant_options.append(f"{q} (est. ~{est}GB){fit_badge}")
                else:
                    quant_options.append(f"{q}")
            quant_sel = st.selectbox("Quantization (precision vs VRAM):", quant_options, key="quant_select")
            if quant_sel and quant_sel != "(base / default)":
                quant_tag = quant_sel.split(" ")[0]
                selected_chat = f"{selected_chat}:{quant_tag}" if ":" not in selected_chat                     else selected_chat.split(":")[0] + f":{quant_tag}"
        
        # Embedding model
        st.markdown("#### 🔤 Embedding Model")
        emb_options, emb_index = [], 0
        current_emb = os.getenv("LOCAL_EMBEDDING_MODEL", "nomic-embed-text")
        for i, m in enumerate(embedding_models):
            badge = "✅" if m["installed"] else "📥"
            emb_options.append(f"{badge} {m['name']} ({m['size_gb']}GB)")
            if m["name"] == current_emb: emb_index = i
        selected_emb_label = st.selectbox("Select embedding model:", emb_options, index=emb_index, key="emb_model_select")
        selected_emb = selected_emb_label.split(" ")[1]
        
        col_refresh, col_pull_chat, col_pull_emb = st.columns(3)
        with col_refresh:
            if st.button("🔄 Refresh", width="stretch", key="btn_refresh_models"): st.rerun()
        with col_pull_chat:
            if not any(m["installed"] for m in chat_models if m["name"] == selected_chat):
                if st.button(f"📥 Download {selected_chat}", width="stretch", key="btn_pull_chat"):
                    with st.spinner(f"Downloading {selected_chat}..."):
                        if pull_model(selected_chat): st.success(f"✅ {selected_chat} installed!"); st.rerun()
                        else: st.error("❌ Download failed.")
        with col_pull_emb:
            if not any(m["installed"] for m in embedding_models if m["name"] == selected_emb):
                if st.button(f"📥 Download {selected_emb}", width="stretch", key="btn_pull_emb"):
                    with st.spinner(f"Downloading {selected_emb}..."):
                        if pull_model(selected_emb): st.success(f"✅ {selected_emb} installed!"); st.rerun()
                        else: st.error("❌ Download failed.")
        
        # ── Cloud Model Configuration ──
        st.markdown("---")
        st.subheader("☁️ Cloud Model Configuration")
        st.caption("Select which cloud models to use when cloud fallback is enabled.")
        
        gemini_flash = st.selectbox("Gemini Flash (pre-screening):",
            ["gemini-2.5-flash-lite", "gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash-latest"],
            index=0, key="gemini_flash_select")
        gemini_pro = st.selectbox("Gemini Pro (deep analysis):",
            ["gemini-2.5-pro", "gemini-1.5-pro-latest"],
            index=0, key="gemini_pro_select")
        
        deepseek_model = st.selectbox("DeepSeek model:",
            ["deepseek-chat (general purpose)", "deepseek-reasoner (advanced reasoning)"],
            index=0, key="deepseek_model_select")
        deepseek_model = deepseek_model.split(" ")[0]
        
        hf_model_name = st.selectbox("HuggingFace model (free tier):",
            ["Qwen/Qwen2.5-7B-Instruct", "mistralai/Mistral-7B-Instruct-v0.3",
             "meta-llama/Llama-3.1-8B-Instruct", "microsoft/Phi-3-mini-4k-instruct",
             "google/gemma-2-2b-it", "mistralai/Mixtral-8x7B-Instruct-v0.1"],
            index=0, key="hf_model_select")
        
        # ── Premium AI APIs ──
        st.markdown("---")
        st.subheader("🔵 Premium AI APIs (Optional)")
        st.caption("Add these to unlock cloud AI providers.")
        col1, col2 = st.columns(2)
        with col1:
            gemini = st.text_input("🔑 GEMINI_API_KEY", value=os.getenv("GEMINI_API_KEY", ""), type="password")
            deepseek = st.text_input("🔑 DEEPSEEK_API_KEY", value=os.getenv("DEEPSEEK_API_KEY", ""), type="password")
        with col2:
            hf_token = st.text_input("🔑 HF_TOKEN (HuggingFace)", value=os.getenv("HF_TOKEN", ""), type="password")
            discord = st.text_input("🔗 DISCORD_WEBHOOK_URL", value=os.getenv("DISCORD_WEBHOOK_URL", ""), type="password")
        
        # ── Academic APIs ──
        st.markdown("---")
        st.subheader("📚 Academic APIs (Optional)")
        st.caption("Unlock additional research sources. All keyless sources work without these.")
        col1, col2 = st.columns(2)
        with col1:
            s2 = st.text_input("🔑 SEMANTIC_SCHOLAR_API_KEY", value=os.getenv("SEMANTIC_SCHOLAR_API_KEY", ""), type="password")
            s2_basic = st.text_input("🔑 S2 Basic Key", value=os.getenv("SEMANTIC_SCHOLAR_API_KEY_basic", ""), type="password")
            ieee = st.text_input("🔑 IEEE_API_KEY", value=os.getenv("IEEE_API_KEY", ""), type="password")
            springer = st.text_input("🔑 SPRINGER_API_KEY", value=os.getenv("SPRINGER_API_KEY", ""), type="password")
        with col2:
            elsevier = st.text_input("🔑 ELSEVIER_API_KEY", value=os.getenv("ELSEVIER_API_KEY", ""), type="password")
            elsevier_inst = st.text_input("🔑 ELSEVIER_INST_TOKEN", value=os.getenv("ELSEVIER_INST_TOKEN", ""), type="password")
            core = st.text_input("🔑 CORE_API_KEY", value=os.getenv("CORE_API_KEY", ""), type="password")
            openarchives = st.text_input("🔑 OPENARCHIVES_API_KEY", value=os.getenv("OPENARCHIVES_API_KEY", ""), type="password")
        
        # ── Integrations ──
        st.markdown("---")
        st.subheader("🔗 Integrations (Optional)")
        st.caption("Connect TALOS with external services.")
        col1, col2 = st.columns(2)
        with col1:
            zotero_id = st.text_input("📚 ZOTERO_USER_ID", value=os.getenv("ZOTERO_USER_ID", ""))
            zotero_key = st.text_input("📚 ZOTERO_API_KEY", value=os.getenv("ZOTERO_API_KEY", ""), type="password")
        with col2:
            orcid_id = st.text_input("🎓 ORCID_CLIENT_ID", value=os.getenv("ORCID_CLIENT_ID", ""))
            orcid_secret = st.text_input("🎓 ORCID_CLIENT_SECRET", value=os.getenv("ORCID_CLIENT_SECRET", ""), type="password")
        
        if st.button("💾 Save All Configuration", type="primary", key="btn_save_env"):
            try:
                _save_env("MAILTO", mailto)
                _save_env("LOCAL_MODEL_NAME", selected_chat)
                _save_env("LOCAL_EMBEDDING_MODEL", selected_emb)
                _save_env("GEMINI_FLASH_MODEL", gemini_flash)
                _save_env("GEMINI_PRO_MODEL", gemini_pro)
                _save_env("DEEPSEEK_MODEL_CHAT", deepseek_model)
                _save_env("HF_MODEL_NAME", hf_model_name)
                for k, v in [("GEMINI_API_KEY", gemini), ("DEEPSEEK_API_KEY", deepseek), ("HF_TOKEN", hf_token),
                             ("DISCORD_WEBHOOK_URL", discord), ("SEMANTIC_SCHOLAR_API_KEY", s2),
                             ("SEMANTIC_SCHOLAR_API_KEY_basic", s2_basic), ("IEEE_API_KEY", ieee),
                             ("ELSEVIER_API_KEY", elsevier), ("ELSEVIER_INST_TOKEN", elsevier_inst),
                             ("SPRINGER_API_KEY", springer), ("CORE_API_KEY", core),
                             ("OPENARCHIVES_API_KEY", openarchives), ("ZOTERO_USER_ID", zotero_id),
                             ("ZOTERO_API_KEY", zotero_key), ("ORCID_CLIENT_ID", orcid_id),
                             ("ORCID_CLIENT_SECRET", orcid_secret)]:
                    if v: _save_env(k, v)
                st.success("✅ All configuration saved to .env!")
            except Exception as e: st.error(str(e))
    
    # ── TAB 2: Profiles & PYTHIA ──
    with tab_profile:
        st.subheader("📂 Research Profiles")
        pd_ = os.path.join(os.path.dirname(__file__), "_profiles")
        ap = get_active_profile()
        st.info(f"**Active Profile:** `{ap}`")
        if os.path.exists(pd_):
            for p in [d for d in os.listdir(pd_) if os.path.isdir(os.path.join(pd_, d))]:
                st.markdown(f"- {'🟢' if p == ap else '⚪'} `{p}`")
        st.caption("💡 Profile management via CLI: `python talos.py` → Profile & Settings.")
        
        st.markdown("---")
        st.subheader("🔮 PYTHIA — Research Goal Configuration")
        st.caption("AI-powered configuration of search queries and evaluation prompts.")
        
        col_pythia1, col_pythia2 = st.columns([3, 1])
        with col_pythia1:
            research_goal = st.text_area("Describe your research goal:", 
                                          placeholder="e.g. 'I want to study autonomous drone swarm intelligence using multi-agent reinforcement learning and graph neural networks...'",
                                          height=80, key="settings_goal")
        with col_pythia2:
            st.write("")
            if st.button("🔮 Configure with PYTHIA", type="primary", width="stretch", key="btn_pythia"):
                if not research_goal.strip() or len(research_goal.strip()) < 20:
                    st.error("Please describe your research goal (min. 20 characters).")
                else:
                    with st.spinner("PYTHIA is optimizing your configuration..."):
                        rc, out = run("query_translator.py", stdin_text=research_goal + "\n")
                        st.session_state.output["pythia_settings"] = out
                    if rc == 0: 
                        st.success("✅ PYTHIA configuration complete!")
                        reload_config()
                    else: st.warning(f"Completed (code {rc}).")
                    show_output("pythia_settings", "PYTHIA Configuration")
        
        st.markdown("---")
        st.subheader("📊 Current Configuration Summary")
        cfg = st.session_state.config
        queries_count = sum(1 for k in cfg if k.endswith("_query"))
        st.markdown(f"- 📋 **{queries_count}** search queries configured")
        st.markdown(f"- 🧠 PhD focus prompt: **{'✅ Customized' if cfg.get('phd_focus_system_prompt', '').find('artificial intelligence') == -1 else '⚠️ Generic (not yet optimized)'}**")
        st.markdown(f"- 🖥️ Provider priority: `{' → '.join(cfg.get('ai_provider_priority', ['gemini']))}`")
    
    # ── TAB 3: Diagnostics ──
    with tab_health:
        st.subheader("🩺 System Diagnostics")
        
        if st.button("🩺 Run API Health Check", type="primary", key="btn_api_diag"):
            with st.spinner("Testing all APIs..."):
                try:
                    from scripts.api_health_check import run_diagnostics
                    results = run_diagnostics()
                    st.session_state._api_results = results
                    st.success("✅ Diagnostics complete!")
                except Exception as e: st.error(str(e))
        
        if "_api_results" in st.session_state:
            results = st.session_state._api_results
            for item in results:
                if isinstance(item, dict) and "category" in item:
                    st.markdown(f"**{item['category']}**")
                elif isinstance(item, tuple):
                    name, status, detail = item
                    if status == "available": st.success(f"✅ **{name}**: {detail}")
                    elif status == "keyless": st.info(f"🟢 **{name}**: {detail}")
                    elif status == "missing_key": st.warning(f"🟡 **{name}**: {detail}")
                    elif status == "invalid_key": st.error(f"🔴 **{name}**: {detail}")
                    else: st.warning(f"⚠️ **{name}**: {detail}")
        
        st.markdown("---")
        st.subheader("🩺 System Health Check")
        if st.button("🩺 Run Smoke Test", key="btn_health"):
            with st.spinner("Running health check..."):
                exe = sys.executable
                test_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_smoke.py")
                env = os.environ.copy()
                env["PYTHONIOENCODING"] = "utf-8"
                try:
                    r = subprocess.run([exe, test_path], capture_output=True, text=True, timeout=30, env=env, encoding="utf-8", errors="replace")
                    st.session_state.output["health"] = r.stdout + "\n" + r.stderr
                    if r.returncode == 0: st.success("🎉 All checks passed — Project is healthy!")
                    else: st.warning(f"Issues found (code {r.returncode}).")
                except Exception as e: st.error(str(e))
            show_output("health", "System Health Check")
        
        st.markdown("---")
        st.subheader("🖥️ System Information")
        si = system_info()
        c1, c2, c3 = st.columns(3)
        c1.metric("OS", si["sys"]); c2.metric("Python", si["py"]); c3.metric("Provider", si["prov"].title())

# ═══════════════════════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown(f"""<div style="text-align:center;padding:1rem;color:#8b949e;font-size:.85rem">
<strong>Project TALOS v4.10.1</strong> · © 2026 Christos Smarlamakis ·
Provider: {system_info()['prov'].title()} · Profile: <code>{get_active_profile()}</code> ·
{datetime.now().strftime('%Y-%m-%d %H:%M')}
</div>""", unsafe_allow_html=True)