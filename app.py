# -*- coding: utf-8 -*-
"""
Module: app.py (Streamlit Web GUI v5.3.3 — Simple/Advanced Dual-Mode)
Project: TALOS v5.3.7
Description:
    Complete Multi-Page Streamlit Web GUI with TWO modes:
    - Simple Mode: 4 pages for non-technical users (students, researchers from any field)
    - Advanced Mode: 8 pages with full functionality (power users)

    Key design decisions:
    - Light-only theme with blue/teal academic palette (dark mode removed in v5.3.3)
    - Card-based home layout for visual clarity
    - Greek tooltips in Simple mode for accessibility
    - Wizard-style onboarding for new users
    - All advanced features hidden in Simple mode
"""
import streamlit as st
import sys
import os
import json
import time
import subprocess
from datetime import datetime
import shutil

import pandas as pd
import numpy as np

# ── Add project root to Python's import path ────────────────────────────────
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.database_manager import DatabaseManager
from core.ai_manager import AIManager
from dotenv import load_dotenv, set_key as _set_key

load_dotenv()

# ═══════════════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="Project TALOS — Research Intelligence",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ═══════════════════════════════════════════════════════════════════════════════
# SESSION STATE INIT
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

# UI state
if "advanced_mode" not in st.session_state:
    st.session_state.advanced_mode = False
if "lang" not in st.session_state:
    st.session_state.lang = "en"

# ── TRANSLATION SYSTEM ──────────────────────────────────────────────────────
# All UI strings loaded from templates/gui_strings.py
from templates.gui_strings import t

# ═══════════════════════════════════════════════════════════════════════════════
# THEME MANAGEMENT
# ═══════════════════════════════════════════════════════════════════════════════
# Theme is applied via CSS injection in render_css() — light-only academic palette.
# Dark mode was removed in v5.3.3 (not functioning correctly, not worth maintaining).

# ═══════════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
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
    """Execute a TALOS script via _gui_runner.py wrapper."""
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
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=600,
                          env=env, encoding="utf-8", errors="replace")
        return r.returncode, r.stdout + "\n" + r.stderr
    except subprocess.TimeoutExpired:
        return -1, "Timeout (10 min)."
    except Exception as e:
        return -1, str(e)

def show_output(key, label):
    """Display script output and parsed report files."""
    if key not in st.session_state.output:
        return
    output = st.session_state.output[key]
    with st.expander(f"📋 Console Output: {label}", expanded=False):
        st.code(output[:8000])

def reload_config():
    cfg = os.path.join(os.path.dirname(__file__), "config.json")
    if os.path.exists(cfg):
        with open(cfg, "r", encoding="utf-8") as f:
            st.session_state.config = json.load(f)
        st.session_state.ai = AIManager(st.session_state.config)

def reload_db():
    st.session_state.db = DatabaseManager()

# (old t() function removed — using STR dict above)

# ═══════════════════════════════════════════════════════════════════════════════
# CSS STYLING
# ═══════════════════════════════════════════════════════════════════════════════
def render_css():
    """Load the external CSS theme and inject light-only CSS variables."""
    css_path = os.path.join(os.path.dirname(__file__), "templates", "gui_theme.css")
    try:
        with open(css_path, "r", encoding="utf-8") as f:
            css_content = f.read()
    except Exception:
        css_content = "/* gui_theme.css not found */"

    # ── Light-only CSS variables (dark mode removed in v5.3.3) ──
    # Blue/Teal palette — scientific, eye-friendly
    bg = "#ffffff"
    card_bg = "#f0f4f8"
    border = "#c8d6e5"
    text = "#1a2a3a"
    accent = "#1a73e8"
    muted = "#5a6a7a"
    sbar = "linear-gradient(180deg, #f0f4f8, #ffffff)"
    # Header variables — different from main bg for visual distinction
    hdr_bg = "linear-gradient(135deg, #e8f0fe 0%, #d2e3fc 50%, #c6dafb 100%)"
    hdr_text = "#1a2a3a"
    hdr_accent = "#1a73e8"
    hdr_sub = "rgba(0,0,0,.55)"

    st.markdown(f"""<style>
    :root {{
        --bg: {bg}; --card-bg: {card_bg}; --border: {border};
        --text: {text}; --accent: {accent}; --muted: {muted};
        --sidebar-bg: {sbar};
        --header-bg: {hdr_bg}; --header-text: {hdr_text};
        --header-accent: {hdr_accent}; --header-sub: {hdr_sub};
    }}
    {css_content}
    </style>""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ═══════════════════════════════════════════════════════════════════════════════
def render_sidebar():
    with st.sidebar:
        st.markdown(f"""<div style="text-align:center;padding:.5rem 0">
        <h2 style="color:#4a9eff;margin:0;font-size:1.4rem">🧠 TALOS</h2>
        <p style="color:var(--muted);font-size:.7rem;margin:.2rem 0 0">{t('sidebar_title')} v5.3.4</p>
        </div>""", unsafe_allow_html=True)
        st.markdown("---")

        # ── Language toggle ──
        new_lang = st.selectbox("🌐 Language / Γλώσσα", ["English (EN)", "Ελληνικά (GR)"],
                               index=0 if st.session_state.lang == "en" else 1, key="lang_select")
        if "EN" in new_lang and st.session_state.lang != "en":
            st.session_state.lang = "en"; st.rerun()
        elif "GR" in new_lang and st.session_state.lang != "gr":
            st.session_state.lang = "gr"; st.rerun()

        # ── Mode badge ──
        mode_label = "Advanced" if st.session_state.advanced_mode else "Simple"
        st.markdown(f'<div class="mode-badge">{mode_label}</div>', unsafe_allow_html=True)

        # ── Navigation ──
        if st.session_state.advanced_mode:
            page = st.radio(t("nav_advanced"), [
                t("home"), t("search_disc"), t("paper_eval"), t("analysis"),
                t("db_data"), t("diagnostics"), t("drl_dash"), t("profile"),
            ], label_visibility="collapsed")
        else:
            page = st.selectbox(t("simple_prompt"), [
                t("simple_home_label"), t("simple_search_label"),
                t("simple_library_label"), t("simple_eval_label"),
                t("simple_agent_label"),
            ])

        st.markdown("---")

        # ── Mode toggle ──
        new_adv = st.toggle("🔧 Advanced Mode", value=st.session_state.advanced_mode, key="tog_adv",
                           help="Enable full feature set for power users")
        if new_adv != st.session_state.advanced_mode:
            st.session_state.advanced_mode = new_adv
            st.rerun()

        # ── DB Stats ──
        try:
            s = st.session_state.db.get_database_statistics()
            st.markdown("---")
            st.caption(f"📚 {s['total_papers']} papers · ⭐ {s['elite_papers']} elite")
        except Exception:
            pass

        # ── Profile ──
        ap = get_active_profile()
        si = system_info()
        st.markdown(f'<div class="sidebar-footer">Profile: <b>{ap}</b><br>{si["prov"].title()} · Python {si["py"]}</div>',
                   unsafe_allow_html=True)
        return page


# ═══════════════════════════════════════════════════════════════════════════════
# SIMPLE MODE PAGES
# ═══════════════════════════════════════════════════════════════════════════════

def simple_home():
    """Home page for Simple Mode — big cards with guided actions."""
    st.markdown(f'<div class="main-header"><h1>{t("sh_hero_title")}</h1>'
                f'<p>{t("sh_hero_subtitle")}</p></div>', unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f'<div class="card"><h3>{t("sh_card_search_title")}</h3>'
                    f'<p>{t("sh_card_search_desc")}</p></div>', unsafe_allow_html=True)
        st.button(t("sh_search_button"), type="primary", width="stretch", key="s_home_search")
    with c2:
        st.markdown(f'<div class="card"><h3>{t("sh_card_library_title")}</h3>'
                    f'<p>{t("sh_card_library_desc")}</p></div>', unsafe_allow_html=True)
        st.button("▶ " + t("sh_card_library_title"), width="stretch", key="s_home_library")
    with c3:
        st.markdown(f'<div class="card"><h3>{t("sh_card_eval_title")}</h3>'
                    f'<p>{t("sh_card_eval_desc")}</p></div>', unsafe_allow_html=True)
        st.button("▶ " + t("sh_card_eval_title"), width="stretch", key="s_home_eval")

    st.markdown("---")
    try:
        s = st.session_state.db.get_database_statistics()
        c1, c2, c3 = st.columns(3)
        c1.metric(t("sh_home_papers"), s["total_papers"])
        c2.metric(t("sh_home_elite"), s["elite_papers"])
        c3.metric(t("sh_home_avg"), f"{s['avg_score']:.1f}")
    except Exception:
        st.info(t("sh_home_empty"))


def simple_search():
    """Simple search — one text input, runs daily_search.py."""
    st.header(t("sh_search_title"))
    st.caption(t("sh_search_desc"))

    topic = st.text_input(t("sh_search_placeholder"), placeholder="e.g. 'artificial intelligence in drones'",
                         key="simple_topic")
    if st.button(t("sh_search_button"), type="primary", width="stretch", key="btn_simple_search"):
        if not topic.strip() or len(topic.strip()) < 15:
            st.error(t("sh_search_error"))
        else:
            with st.spinner(t("sh_search_running").replace("{topic}", topic)):
                rc1, _ = run("query_translator.py", stdin_text=topic + "\n")
                rc2, out = run("daily_search.py")
                st.session_state.output["simple_search"] = out
            if rc2 == 0:
                st.success(t("sh_search_success"))
                reload_db()
            else:
                st.warning(t("sh_search_partial"))
            show_output("simple_search", "daily_search.py")


def simple_library():
    """Simple library — search by meaning + browse top papers."""
    st.header(t("sh_library_title"))
    st.caption(t("sh_library_desc"))

    sem_query = st.text_input(t("sh_library_sem_label"),
                              placeholder="e.g. 'deep reinforcement learning for robotics'",
                              key="simple_sem_q")
    if sem_query and st.button(t("sh_library_sem_btn"), key="simple_sem_btn"):
        with st.spinner("Searching..."):
            try:
                import requests as _req
                r = _req.post("http://localhost:11434/api/embed",
                             json={"model": "nomic-embed-text", "input": [sem_query]}, timeout=10)
                if r.status_code == 200:
                    vectors = r.json().get("embeddings")
                    if vectors:
                        ids = st.session_state.db.semantic_search(np.array(vectors[0]), top_k=50)
                        st.session_state._sem_ids = ids
                        st.success(t("sh_library_sem_found").replace("{n}", str(len(ids))))
            except Exception as e:
                st.warning(t("sh_library_sem_unavail").replace("{e}", str(e)))

    try:
        papers = st.session_state.db.get_all_papers_for_dashboard()
        if papers:
            df = pd.DataFrame(papers)
            if "_sem_ids" in st.session_state and st.session_state._sem_ids:
                df = df[df["id"].isin(st.session_state._sem_ids)]
            df = df.sort_values("overall_score", ascending=False).head(20)
            display_cols = ["title", "source", "publication_year", "overall_score"]
            display_cols = [c for c in display_cols if c in df.columns]
            st.dataframe(df[display_cols], width="stretch", height=400,
                        column_config={
                            "title": st.column_config.TextColumn(t("sh_library_title")),
                            "source": st.column_config.TextColumn("Source"),
                            "publication_year": st.column_config.NumberColumn("Year"),
                            "overall_score": st.column_config.NumberColumn("Score", format="%.1f"),
                        })
        else:
            st.info(t("sh_library_empty"))
    except Exception as e:
        st.warning(t("sh_library_load_error").replace("{e}", str(e)))


def simple_agent():
    """Simple Agent — one-button DRL agent."""
    st.header(t("sh_agent_title"))
    st.caption(t("sh_agent_desc"))

    model_path = os.path.join(os.path.dirname(__file__), "models", "dddqn_trained.pth")
    if os.path.exists(model_path):
        size_kb = os.path.getsize(model_path) / 1024
        st.success(t("sh_agent_ready").replace("{size:.1f}", f"{size_kb:.1f}"))
        if st.button(t("sh_agent_btn"), type="primary", width="stretch", key="btn_simple_agent"):
            with st.spinner(t("sh_agent_running")):
                rc, out = run("talos_live_agent.py", args=["--verbose"])
                st.session_state.output["simple_agent"] = out
            if rc in [0, 1, 2]: st.success(t("sh_agent_done"))
            else: st.warning(f"Completed (code {rc}).")
            show_output("simple_agent", "Live DRL Agent")
    else:
        st.warning(t("sh_agent_untrained"))
        st.code("python scripts/train_agent.py --episodes 500", language="bash")


def simple_evaluate():
    """Simple paper evaluation."""
    st.header(t("sh_eval_title"))
    st.caption(t("sh_eval_desc"))

    abstract = st.text_area(t("sh_eval_label"), height=200,
                           placeholder="Paste the paper abstract here...",
                           key="simple_abs")

    if st.button(t("sh_eval_btn"), type="primary", width="stretch", key="btn_simple_eval"):
        if not abstract or len(abstract.strip()) < 50:
            st.error(t("sh_eval_error"))
        else:
            with st.spinner(t("sh_eval_spinner")):
                try:
                    result = st.session_state.ai.evaluate_paper_json(abstract, model_type="pro")
                    if result:
                        sc = result.get("scores", {})
                        ov = result.get("overall_score", 0)
                        c1, c2, c3, c4 = st.columns(4)
                        c1.metric(t("sh_eval_strategic"), f"{sc.get('strategic',0)}/10")
                        c2.metric(t("sh_eval_operational"), f"{sc.get('operational',0)}/10")
                        c3.metric(t("sh_eval_tactical"), f"{sc.get('tactical',0)}/10")
                        c4.metric(t("sh_eval_playground"), f"{sc.get('playground',0)}/10")
                        st.markdown(f"### {t('sh_eval_overall')}: **{ov:.1f} / 10**")
                        st.progress(min(ov / 10, 1.0))
                        if result.get("reasoning"):
                            st.markdown(f"**{t('sh_eval_reasoning')}:** {result['reasoning']}")
                        if result.get("tags"):
                            st.markdown("**{t('sh_eval_tags')}:** " + " . ".join(result["tags"]))
                    else:
                        st.error(t("sh_eval_fail"))
                except Exception as e:
                    st.error(f"Error: {e}")


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN PAGE HANDLER
# ═══════════════════════════════════════════════════════════════════════════════

def handle_advanced_page(page):
    """Handle routing for Advanced Mode pages."""
    if page == t("home"):
        advanced_home()
    elif page == t("search_disc"):
        advanced_search()
    elif page == t("paper_eval"):
        advanced_evaluate()
    elif page == t("analysis"):
        advanced_analysis()
    elif page == t("db_data"):
        advanced_database()
    elif page == t("diagnostics"):
        advanced_diagnostics()
    elif page == t("drl_dash"):
        advanced_drl_dashboard()
    elif page == t("profile"):
        advanced_settings()


def advanced_home():
    """Advanced Home — full dashboard with filters and semantic search."""
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

    # ── Filter buttons ──
    filter_cols = st.columns(7)
    filters = {"All": None, "Core ≥7": 7.0, "Strategic ≥7": 7.0, "Operational ≥7": 7.0,
               "Tactical ≥7": 7.0, "Playground ≥7": 7.0, "Elite ≥8": 8.0}
    active_filter = "All"
    for i, (label, thresh) in enumerate(filters.items()):
        with filter_cols[i % 7]:
            if st.button(label, key=f"hf_{label}", width="stretch"):
                st.session_state._home_filter = (label, thresh)

    if "_home_filter" not in st.session_state:
        st.session_state._home_filter = ("All", None)
    active_filter, active_thresh = st.session_state._home_filter

    # ── Semantic search ──
    with st.expander("🔍 Semantic Search (search by meaning)", expanded=False):
        sem_q = st.text_input("Search papers by meaning:", key="adv_sem_q")
        if sem_q and st.button("🔍 Search", key="adv_sem_btn"):
            with st.spinner("Searching..."):
                try:
                    import requests as _req
                    r = _req.post("http://localhost:11434/api/embed",
                                 json={"model": "nomic-embed-text", "input": [sem_q]}, timeout=10)
                    if r.status_code == 200:
                        vectors = r.json().get("embeddings")
                        if vectors:
                            ids = st.session_state.db.semantic_search(np.array(vectors[0]), top_k=200)
                            st.session_state._sem_ids = ids
                            st.success(f"Found {len(ids)} semantically similar papers!")
                except Exception as e:
                    st.warning(f"Semantic search unavailable: {e}")

    # ── Papers table ──
    try:
        papers = st.session_state.db.get_all_papers_for_dashboard()
        if papers:
            df = pd.DataFrame(papers)
            # Apply semantic filter
            if "_sem_ids" in st.session_state and st.session_state._sem_ids:
                df = df[df["id"].isin(st.session_state._sem_ids)]
            # Apply numeric filter
            if active_thresh is not None:
                if active_filter == "Core ≥7":
                    df = df[df["overall_score"] >= 7.0]
                elif active_filter == "Strategic ≥7":
                    df = df[df.get("strategic_score", df["overall_score"]) >= active_thresh]
                elif active_filter == "Operational ≥7":
                    df = df[df.get("operational_score", df["overall_score"]) >= active_thresh]
                elif active_filter == "Tactical ≥7":
                    df = df[df.get("tactical_score", df["overall_score"]) >= active_thresh]
                elif active_filter == "Playground ≥7":
                    df = df[df.get("playground_score", df["overall_score"]) >= active_thresh]
                elif active_filter == "Elite ≥8":
                    df = df[df["overall_score"] >= 8.0]
            df = df.sort_values("overall_score", ascending=False).head(200)
            display_cols = ["title", "source", "publication_year", "overall_score"]
            if "authors" in df.columns: display_cols.insert(1, "authors")
            display_cols = [c for c in display_cols if c in df.columns]
            st.caption(f"Showing {len(df)} papers (filter: {active_filter})")
            st.dataframe(df[display_cols], width="stretch", height=600,
                        column_config={
                            "overall_score": st.column_config.NumberColumn("⭐ Overall", format="%.1f"),
                            "title": st.column_config.TextColumn("Title", width="large"),
                        })
        else:
            st.info("📭 No papers yet. Run a Search to populate the database.")
    except Exception as e:
        st.warning(f"Could not load: {e}")


def advanced_search():
    """Advanced Search — AI Search (flagship) + daily/historic/process/grey lit."""
    st.header("🔍 Search & Discovery")
    t1, t2, t3, t4, t5 = st.tabs([
        t("ai_search_title"), "📰 Daily Search (14 APIs)", "📚 Historical Archive",
        t("ai_process_title"), "🌐 Grey Literature",
    ])
    # ── Tab 1: AI-Powered Search (FLAGSHIP) ──
    with t1:
        st.subheader(t("ai_search_title"))
        st.caption(t("ai_search_desc"))
        live_col1, live_col2 = st.columns(2)
        with live_col1:
            if st.button("🧠 Start AI-Powered Live Agent", type="primary", width="stretch", key="btn_ai_search"):
                with st.spinner("DRL agent orchestrating APIs in real-time..."):
                    rc, out = run("talos_live_agent.py", args=["--verbose"])
                    st.session_state.output["ai_search"] = out
                if rc in [0, 1, 2]: st.success("✅ AI search complete!")
                else: st.warning(f"Completed (code {rc}).")
                show_output("ai_search", "DRL Live Agent")
        with live_col2:
            if st.button("📊 Open DRL Dashboard", width="stretch", key="btn_open_drl"):
                st.switch_page("pages/7_🧠_DRL_Agent_Dashboard.py") if False else None
    # ── Tab 2: Daily Search ──
    with t2:
        st.subheader("📰 Daily Search — 14 Academic APIs")
        if st.button("🚀 Run Daily Search", type="primary", key="b1"):
            with st.spinner("Running..."):
                rc, out = run("daily_search.py")
                st.session_state.output["daily"] = out
            if rc == 0: st.success("✅ Complete!"); reload_db()
            else: st.warning(f"Code {rc}.")
            show_output("daily", "daily_search.py")
    # ── Tab 3: Historical Search ──
    with t3:
        st.subheader("📚 Historical Search")
        if st.button("📜 Run Historical Search", type="primary", key="b2"):
            with st.spinner("Running..."):
                rc, out = run("historic_search.py", stdin_text="y\n")
                st.session_state.output["historic"] = out
            if rc == 0: st.success("✅ Complete!"); reload_db()
            else: st.warning(f"Code {rc}.")
    # ── Tab 4: Autonomous Process (24/7 + DRL) ──
    with t4:
        st.subheader(t("ai_process_title"))
        st.caption(t("ai_process_desc"))
        st.warning(t("process_stop"))
        report_mode = st.radio(t("process_reporting"), [
            t("process_silent"), t("process_normal"), t("process_verbose"),
        ], index=0, horizontal=True)
        if st.button("🤖 " + t("process_start"), type="primary", key="btn_process"):
            mode_flag = "1" if t("process_silent") in report_mode else ("2" if t("process_normal") in report_mode else "3")
            with st.spinner("Process starting..."):
                rc, out = run("talos_service.py")
                st.session_state.output["process"] = out
            if rc in [0, 1, 2]: st.success("✅ Process stopped.")
            else: st.warning(f"Completed (code {rc}).")
            show_output("process", "Autonomous Process")
    # ── Tab 5: Grey Literature ──
    with t5:
        st.subheader("🌐 Grey Literature")
        topic = st.text_input("Research topic:", key="grey_topic")
        if st.button("🌍 Run Horizon Scan", type="primary", key="b3"):
            if not topic.strip():
                st.error("Please enter a topic.")
            else:
                with st.spinner(f"Scanning '{topic}'..."):
                    rc, out = run("grey_literature_miner.py", stdin_text=topic + "\n")
                    st.session_state.output["grey"] = out
                if rc == 0: st.success("✅ Complete!")
                else: st.warning(f"Code {rc}.")


def advanced_evaluate():
    """Advanced Evaluation — DOI fetch + DB selection."""
    st.header("🧪 Single Paper Evaluation")
    abstract = st.text_area("📝 Enter Paper Abstract", height=160, key="adv_abs")
    if st.button("🔬 Analyze Paper", type="primary", width="stretch", key="btn_adv_eval"):
        if not abstract or len(abstract.strip()) < 50:
            st.error("⚠️ Please provide an abstract (min. 50 characters).")
        else:
            with st.spinner("Evaluating..."):
                try:
                    result = st.session_state.ai.evaluate_paper_json(abstract, model_type="pro")
                    if result:
                        sc = result.get("scores", {})
                        ov = result.get("overall_score", 0)
                        c1, c2, c3, c4 = st.columns(4)
                        c1.metric("🔴 Strategic", f"{sc.get('strategic',0)}/10")
                        c2.metric("🟣 Operational", f"{sc.get('operational',0)}/10")
                        c3.metric("🔵 Tactical", f"{sc.get('tactical',0)}/10")
                        c4.metric("🟡 Playground", f"{sc.get('playground',0)}/10")
                        st.markdown(f"### 🎯 Overall Score: **{ov:.1f} / 10**")
                        st.progress(min(ov / 10, 1.0))
                    else:
                        st.error("❌ All AI providers failed.")
                except Exception as e:
                    st.error(f"Error: {e}")


def advanced_analysis():
    """Advanced Analysis — tool dropdown."""
    st.header("📊 Analysis & Insights")
    opt = st.selectbox("Analysis Tool", [
        "📖 Knowledge Path Generator",
        "🔗 Citation Network Analyzer",
        "📊 Strategic Reading Report (Recommender)",
        "👤 Author Analysis Tools",
        "🖥️ Interactive Dashboard (Legacy)",
        "📊 Baseline Report (Standard)",
        "🎓 Baseline Report (Academic)",
        "🤖 Autonomous Research Service (24/7)",
        "📡 Service API (Port 5002)",
        "🧠 Live DRL Agent (Real APIs)",
    ])
    st.markdown("---")
    if "Knowledge Path" in opt:
        goal = st.text_input("Research goal:", key="chiron_goal")
        if st.button("🧭 Generate", type="primary", key="bc") and goal:
            with st.spinner("..."):
                rc, out = run("knowledge_path_generator.py", stdin_text=goal + "\n")
                st.session_state.output["chiron"] = out
            if rc == 0: st.success("✅ Knowledge path generated!")
    elif "Citation Network" in opt:
        doi = st.text_input("DOI:", key="orpheus_doi")
        if st.button("🔍 Analyze", type="primary", key="bo") and doi:
            with st.spinner("..."):
                rc, out = run("citation_analyzer.py", stdin_text=f"1\n{doi}\n")
                st.session_state.output["orpheus"] = out
            if rc == 0: st.success("✅ Citation analysis complete!")
    elif "Reading" in opt:
        if st.button("📋 Generate Report", type="primary", key="br"):
            with st.spinner("..."):
                rc, out = run("recommender.py")
                st.session_state.output["recommender"] = out
            if rc == 0: st.success("✅ Report generated!")
    elif "Baseline" in opt:
        is_acad = "Academic" in opt
        label = "Academic (600 DPI)" if is_acad else "Standard (300 DPI)"
        args = ["--academic"] if is_acad else []
        if st.button(f"🎓 Generate {label} Report", type="primary", key=f"btn_bl_{'acad' if is_acad else 'std'}"):
            with st.spinner(f"Generating {label}..."):
                rc, out = run("generate_baseline_report.py", args=args)
                st.session_state.output["baseline"] = out
            if rc == 0: st.success(f"✅ {label} report generated!")
    elif "Autonomous" in opt:
        st.warning("⚠️ This service runs INDEFINITELY.")
        if st.button("🚀 Start", type="primary", key="btn_service"):
            with st.spinner("..."):
                rc, out = run("talos_service.py")
                st.session_state.output["service"] = out
            if rc in [0, 1, 2]: st.success("✅ Service terminated.")
    elif "Service API" in opt:
        if st.button("📡 Start API", type="primary", key="btn_api"):
            with st.spinner("..."):
                rc, out = run("talos_service_api.py")
                st.session_state.output["service_api"] = out
            if rc in [0, 1, 2]: st.success("✅ API server terminated.")
    elif "Live DRL" in opt:
        st.warning("⚠️ This makes REAL API calls.")
        if st.button("🧠 Start Live Agent", type="primary", key="btn_live"):
            with st.spinner("..."):
                rc, out = run("talos_live_agent.py", args=["--verbose"])
                st.session_state.output["live_agent"] = out
            if rc in [0, 1, 2]: st.success("✅ Live agent terminated.")


def advanced_database():
    """Advanced Database — maintenance tools."""
    st.header("🛠️ Database & Data")
    mo = st.selectbox("Task", [
        "📊 Statistics & Health", "📝 Metadata Enrichment", "📚 Zotero Sync",
        "🧠 Embedding Generator", "🔄 AI Re-evaluation", "🔗 Data Enrichment (Unpaywall)",
        "📈 Scientometrics Report", "📥 PDF Downloader (Open Access)",
    ])
    MAP = {
        "Statistics": "db_stats.py", "metadata": "metadata_enricher.py",
        "Zotero": "zotero_connector.py", "Embedding": "embedding_generator.py",
        "Re-evaluation": "reevaluate_database.py", "Data Enrichment": "data_enricher.py",
        "Scientometrics": "trend_analyzer.py", "PDF": "pdf_downloader.py",
    }
    for kw, scr in MAP.items():
        if kw in mo:
            if st.button(f"▶️ Run", type="primary", key=f"bm_{kw}"):
                with st.spinner("..."):
                    rc, out = run(scr)
                    st.session_state.output[kw] = out
                if rc == 0:
                    st.success("✅ Complete!")
                    if kw in ("Statistics", "Embedding"): reload_db()
                else: st.warning(f"Code {rc}.")


def advanced_diagnostics():
    """Advanced Diagnostics — integrity check + audit."""
    st.header("🩺 System Diagnostics")
    if st.button("Run Code Integrity Check", type="primary", key="btn_integrity"):
        test_path = os.path.join(os.path.dirname(__file__), "test_smoke.py")
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        try:
            r = subprocess.run([sys.executable, test_path], capture_output=True, text=True,
                              timeout=30, env=env, encoding="utf-8", errors="replace")
            st.session_state.output["integrity"] = r.stdout + "\n" + r.stderr
            if r.returncode == 0: st.success("All checks passed!")
            else: st.warning(f"Issues found (code {r.returncode}).")
        except Exception as e:
            st.error(str(e))
        show_output("integrity", "Code Integrity Check")

    if st.button("Run Documentation Audit", type="primary", key="btn_doc_audit"):
        with st.spinner("Scanning..."):
            rc, out = run("verify_dependency_map.py", args=["--all"])
            st.session_state.output["doc_audit"] = out
        if rc == 0: st.success("Audit complete. Map is 100% accurate.")
        else: st.warning("Discrepancies found.")

    st.markdown("---")
    if st.button("Open Architecture Graph", type="primary", key="btn_arch_graph"):
        import webbrowser, socket
        port = 8765
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.5)
            if sock.connect_ex(('127.0.0.1', port)) != 0:
                server_dir = os.path.join(os.path.dirname(__file__), "templates")
                subprocess.Popen(
                    [sys.executable, "-m", "http.server", str(port), "--bind", "127.0.0.1", "--directory", server_dir],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                )
            sock.close()
        except: pass
        webbrowser.open(f"http://localhost:{port}/architecture_graph.html")
        st.success("Architecture graph opened in browser!")

    if st.button("Generate Architecture Intelligence Report", type="primary", key="btn_arch_report"):
        with st.spinner("Generating..."):
            rc, out = run("architecture_intelligence_report.py")
            st.session_state.output["arch_report"] = out
        if rc == 0: st.success("✅ Report generated (EN + GR)!")
        else: st.warning(f"Completed (code {rc}).")


def advanced_drl_dashboard():
    """DRL Dashboard — 4 tabs: GWO Live, Training, Status, 3D Swarm Hunt."""
    st.header("🧠 DRL Agent Dashboard")

    tab1, tab2, tab3, tab4 = st.tabs([
        "♮ Run GWO (Live)", "♮ DRL Training", "📊 Model & Results", "♮ Swarm Hunt 3D"
    ])

    models_dir = os.path.join(os.path.dirname(__file__), "models")

    # ══════════════════════════════════════════════════════════════════════
    # TAB 1: Run GWO — Live Optimization from GUI
    # ══════════════════════════════════════════════════════════════════════
    with tab1:
        st.subheader("Grey Wolf Optimizer — Live")
        st.caption(
            "Run hyperparameter optimization directly from the GUI. "
            "The chart updates in real-time as the wolf pack converges."
        )

        col1, col2, col3 = st.columns(3)
        with col1:
            wolves_num = st.number_input("Wolves", 5, 1000, 15, key="gwo_wolves")
        with col2:
            iters_num = st.number_input("Iterations", 5, 1000, 50, key="gwo_iters")

        progress_path = os.path.join(models_dir, "gwo_progress.json")

        # ── Start / Stop / Live Dashboard buttons ────────────────────────
        btn_col1, btn_col2, btn_col3 = st.columns(3)

        with btn_col1:
            if st.button("♮ Start GWO", type="primary", key="btn_gwo_start", use_container_width=True):
                if os.path.exists(progress_path):
                    os.remove(progress_path)
                st.session_state._gwo_running = True
                st.session_state._gwo_process = subprocess.Popen(
                    [sys.executable, os.path.join(os.path.dirname(__file__), "scripts", "gwo_rl_optimizer.py"),
                     "--wolves", str(wolves_num), "--iters", str(iters_num), "--live"],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                )
                st.rerun()

        with btn_col2:
            if st.session_state.get("_gwo_running"):
                if st.button("Stop GWO", key="btn_gwo_stop", use_container_width=True):
                    process = st.session_state.get("_gwo_process")
                    if process:
                        process.terminate()
                    st.session_state._gwo_running = False
                    st.warning("Optimization stopped.")
                    st.rerun()

        with btn_col3:
            if st.button("Open Live Dashboard", key="btn_gwo_dash", use_container_width=True,
                        help="Opens the Dash live 3D visualization in a new browser tab"):
                import webbrowser
                # Check if dash is already running by trying to connect
                dash_running = False
                try:
                    import socket
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    s.settimeout(0.5)
                    if s.connect_ex(('127.0.0.1', 8050)) == 0:
                        dash_running = True
                    s.close()
                except:
                    pass

                if not dash_running:
                    # Start Dash server
                    subprocess.Popen(
                        [sys.executable, os.path.join(os.path.dirname(__file__), "scripts", "gwo_live_dashboard.py")],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                    )
                    time.sleep(2)
                webbrowser.open("http://localhost:8050")

        # ── Status indicator when GWO is running ───────────────────────
        if st.session_state.get("_gwo_running"):
            if os.path.exists(progress_path):
                try:
                    with open(progress_path, "r") as f:
                        progress = json.load(f)
                    status = progress.get("status", "running")
                    iteration = progress.get("iteration", 0)
                    max_iters = progress.get("max_iterations", iters_num)
                    best_reward = progress.get("best_reward", 0)

                    if status == "complete":
                        st.success(f"Optimization Complete! {iteration} iterations, best reward: {best_reward:.1f}")
                        st.session_state._gwo_running = False
                        st.balloons()
                    else:
                        pct = min(iteration / max(max_iters, 1), 1.0)
                        st.progress(pct, f"Iteration {iteration} / {max_iters}")
                        c1, c2 = st.columns(2)
                        c1.metric("Best Reward", f"{best_reward:.1f}")
                        c2.metric("Iteration", f"{iteration}/{max_iters}")
                        st.info("Open the Live Dashboard to see the 3D swarm visualization.")
                except Exception:
                    st.info("GWO is starting up... (first iteration takes ~30-60 seconds)")
            else:
                st.info("GWO is starting up... (first iteration takes ~30-60 seconds)")
        else:
            st.info("Press 'Start GWO' to begin, then 'Open Live Dashboard' to see the 3D visualization.")


    # ══════════════════════════════════════════════════════════════════════
    # TAB 2: DRL Training
    # ══════════════════════════════════════════════════════════════════════
    with tab2:
        st.subheader("DRL Agent Training")
        st.caption("Train the LSTM-DDDQN agent with GWO-optimized hyperparameters.")

        episodes = st.slider("Training Episodes", 50, 2000, 700, 50, key="train_episodes")
        if st.button("♮ Start Training", type="primary", key="btn_train_start"):
            with st.spinner(f"Training for {episodes} episodes..."):
                rc, out = run("drl_trainer.py", args=[f"--episodes", str(episodes)])
                st.session_state.output["drl_train"] = out
            if rc == 0:
                st.success(f"Training Complete! {episodes} episodes.")
            else:
                st.warning(f"Training finished with code {rc}.")
            show_output("drl_train", "drl_trainer.py")

    # ══════════════════════════════════════════════════════════════════════
    # TAB 3: Model & Results
    # ══════════════════════════════════════════════════════════════════════
    with tab3:
        st.subheader("Model & Optimization Results")

        gwo_path = os.path.join(models_dir, "gwo_best_params.json")
        if os.path.exists(gwo_path):
            try:
                with open(gwo_path, "r") as f:
                    gwo = json.load(f)
                st.markdown("#### GWO-Optimized Hyperparameters")
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("LR", f"{gwo['learning_rate']:.6e}")
                c2.metric("Gamma", f"{gwo['gamma']:.4f}")
                c3.metric("Eps Decay", f"{gwo['epsilon_decay']:.6f}")
                c4.metric("Best Fitness", f"{gwo['best_fitness']:.1f}",
                         delta=f"Reward: {gwo['best_avg_reward']:.1f}")
                st.caption(f"Optimized in {gwo.get('iterations','?')} iterations, {gwo.get('gwo_time_seconds','?')}s")
            except Exception as e:
                st.warning(f"Could not read GWO params: {e}")
        else:
            st.info("No GWO results yet. Run the optimizer in Tab 1.")

        st.markdown("---")

        model_path = os.path.join(models_dir, "dddqn_trained.pth")
        if os.path.exists(model_path):
            size_kb = os.path.getsize(model_path) / 1024
            st.success(f"Trained model: {size_kb:.1f} KB")
            try:
                import torch
                d = torch.load(model_path, map_location="cpu", weights_only=True)
                c1, c2, c3 = st.columns(3)
                c1.metric("State Dim", d.get("state_dim", "?"))
                c2.metric("Action Dim", d.get("action_dim", "?"))
                c3.metric("Network", d.get("network_class", "DuelingLSTM"))
            except Exception:
                pass
        else:
            st.warning("No trained model yet. Run training in Tab 2.")


    # ══════════════════════════════════════════════════════════════════════
    # TAB 4: GWO Swarm Hunt — Interactive 3D Replay
    # ══════════════════════════════════════════════════════════════════════
    with tab4:
        st.subheader("GWO Swarm Hunt — 3D Convergence Replay")
        st.caption(
            "Replay the optimization history. Alpha (★) is the best wolf. "
            "Drag the slider to see how the pack converged."
        )

        history_path = os.path.join(models_dir, "gwo_history.json")
        if os.path.exists(history_path):
            try:
                with open(history_path, "r") as f:
                    gwo_history = json.load(f)
            except Exception:
                st.warning("Could not parse history file.")
                gwo_history = []

            if gwo_history:
                import plotly.graph_objects as go

                max_iter = len(gwo_history) - 1
                iter_idx = st.slider("Iteration", 0, max_iter, 0, key="gwo_iter_slider")

                entry = gwo_history[iter_idx]
                wolves_data = entry["wolves"]

                roles = {"alpha": [], "beta": [], "delta": [], "omega": []}
                for w in wolves_data:
                    roles[w["role"]].append(w)

                fig = go.Figure()

                if roles["omega"]:
                    fig.add_trace(go.Scatter3d(
                        x=[w["lr"] for w in roles["omega"]],
                        y=[w["gamma"] for w in roles["omega"]],
                        z=[w["eps_d"] for w in roles["omega"]],
                        mode='markers',
                        marker=dict(size=5, color=[w["fitness"] for w in roles["omega"]],
                                   colorscale='Viridis', showscale=True,
                                   colorbar=dict(title="Fitness", x=1.02), opacity=0.7),
                        name=f'Omega ({len(roles["omega"])})',
                        hovertemplate='LR: %{x:.2e}<br>Gamma: %{y:.3f}<br>Eps Decay: %{z:.4f}<extra></extra>',
                    ))

                for role, color, size, label in [
                    ("delta", "gold", 10, "Delta"),
                    ("beta", "darkorange", 12, "Beta"),
                    ("alpha", "crimson", 16, "ALPHA"),
                ]:
                    if roles[role]:
                        w = roles[role][0]
                        fig.add_trace(go.Scatter3d(
                            x=[w["lr"]], y=[w["gamma"]], z=[w["eps_d"]],
                            mode='markers+text',
                            marker=dict(size=size, color=color, symbol='diamond',
                                       line=dict(color='black', width=1)),
                            text=[label], textposition='top center',
                            textfont=dict(size=size-2, color=color),
                            name=f'{label} (fitness={w["fitness"]:.1f})',
                            hovertemplate=f'{label}<br>LR: %{{x:.2e}}<br>Gamma: %{{y:.3f}}<br>Eps Decay: %{{z:.4f}}<extra></extra>',
                        ))

                fig.update_layout(
                    title=f"GWO Swarm Hunt — Iteration {iter_idx} / {max_iter}",
                    scene=dict(
                        xaxis=dict(title="Learning Rate", type="log", gridcolor='rgba(128,128,128,0.2)'),
                        yaxis=dict(title="Gamma", range=[0.48, 1.0], gridcolor='rgba(128,128,128,0.2)'),
                        zaxis=dict(title="Epsilon Decay", range=[0.88, 1.0], gridcolor='rgba(128,128,128,0.2)'),
                        bgcolor='rgba(0,0,0,0)',
                    ),
                    legend=dict(x=0.01, y=0.99, bgcolor='rgba(0,0,0,0.3)'),
                    margin=dict(l=0, r=0, b=0, t=50), height=600,
                    paper_bgcolor='rgba(0,0,0,0)', font=dict(color='#e0e0e0'),
                )
                st.plotly_chart(fig, use_container_width=True, key=f"gwo_plot_{iter_idx}")

                c1, c2, c3 = st.columns(3)
                c1.metric("Alpha Fitness", f"{entry.get('alpha_fitness', 0):.1f}")
                c2.metric("Beta Fitness", f"{entry.get('beta_fitness', 0):.1f}")
                c3.metric("Delta Fitness", f"{entry.get('delta_fitness', 0):.1f}")
        else:
            st.info("No GWO history file found. Run the optimizer first in Tab 1.")


def advanced_settings():
    """Advanced Settings — API keys + models + profiles + VRAM-aware model management."""
    st.header("⊙ Profile & Settings")
    from core.hardware import detect_vram_gb, estimate_size_for_quant, get_all_chat_models_sorted, get_embedding_models, pull_model

    # ── Provider Selection ────────────────────────────────────────────────
    provider = st.radio(t("model_provider"), [t("model_local"), t("model_cloud")], horizontal=True,
                       index=0 if "TALOS_USE_LOCAL" in os.environ else 1, key="settings_provider")
    is_local = t("model_local") in provider

    env_path = os.path.join(os.path.dirname(__file__), ".env")
    vram_gb = detect_vram_gb()

    c1, c2 = st.columns(2)
    with c1: st.metric(t("model_vram"), f"{vram_gb:.1f} GB" if vram_gb else "N/A")
    with c2:
        if vram_gb:
            usable = vram_gb * 0.70
            st.caption(f"{usable:.1f} GB usable (70% headroom)")

    if is_local:
        # ═══ LOCAL MODE ═══════════════════════════════════════════════════
        all_models = get_all_chat_models_sorted(vram_gb) if vram_gb else []
        installed = [m for m in all_models if m.get("installed")][:10]
        library = [m for m in all_models if not m.get("installed") and not m.get("bitnet")][:15]
        bitnet = [m for m in all_models if m.get("bitnet")]

        # ── Chat Model ────────────────────────────────────────────────────
        st.subheader(t("model_chat"))
        section = st.selectbox(t("model_select"), [
            t("model_installed"), t("model_library"), t("model_bitnet"),
        ])
        models = installed if t("model_installed") in section else (library if t("model_library") in section else bitnet)
        model_names = []
        for m in models:
            name = m.get("full_name", m.get("name", ""))
            size_gb = estimate_size_for_quant(name, m.get("quant"))
            badge = t("model_fits") if size_gb <= (vram_gb or 0) * 0.70 else (t("model_tight") if size_gb <= (vram_gb or 0) else t("model_toobig"))
            label = f"{name} ({size_gb:.1f}GB) [{badge}]" if vram_gb else name
            model_names.append(label)
        if model_names:
            sel = st.selectbox(t("model_chat"), model_names, key="model_sel")
            if st.button(t("model_save"), key="btn_save_local"):
                full = sel.split(" (")[0] if " (" in sel else sel
                try:
                    from dotenv import set_key
                    set_key(env_path, "LOCAL_MODEL_NAME", full)
                    os.environ["LOCAL_MODEL_NAME"] = full
                    st.success(f"Saved: {full}")
                except Exception as e:
                    st.error(str(e))
        else:
            st.info("No models available. Check Ollama connection.")

    else:
        # ═══ CLOUD MODE ═══════════════════════════════════════════════════
        st.subheader("Cloud AI Models")
        flash_opts = ["gemini-2.0-flash", "gemini-2.5-flash", "gemini-1.5-flash"]
        pro_opts = ["gemini-2.5-pro", "gemini-2.0-pro", "gemini-1.5-pro"]
        ds_opts = ["deepseek-chat", "deepseek-reasoner"]
        hf_opts = ["mistralai/Mixtral-8x7B-Instruct-v0.1", "meta-llama/Llama-3.1-8B-Instruct",
                  "Qwen/Qwen2.5-7B-Instruct", "mistralai/Mistral-7B-Instruct-v0.3",
                  "microsoft/Phi-3-mini-4k-instruct", "google/gemma-2-2b-it"]

        gf = st.selectbox(t("model_gemini_flash"), flash_opts, index=0)
        gp = st.selectbox(t("model_gemini_pro"), pro_opts, index=0)
        ds = st.selectbox(t("model_deepseek"), ds_opts, index=0)
        hf = st.selectbox(t("model_hf"), hf_opts, index=0)
        if st.button(t("model_save"), key="btn_save_cloud"):
            try:
                from dotenv import set_key
                set_key(env_path, "GEMINI_FLASH_MODEL", gf)
                set_key(env_path, "GEMINI_PRO_MODEL", gp)
                set_key(env_path, "DEEPSEEK_MODEL_CHAT", ds)
                set_key(env_path, "HF_MODEL_NAME", hf)
                os.environ["GEMINI_FLASH_MODEL"] = gf
                os.environ["GEMINI_PRO_MODEL"] = gp
                os.environ["DEEPSEEK_MODEL_CHAT"] = ds
                os.environ["HF_MODEL_NAME"] = hf
                st.success("Cloud models saved!")
            except Exception as e:
                st.error(str(e))

    # ── Embedding Model ────────────────────────────────────────────────────
    st.markdown("---")
    st.subheader(t("model_embed"))
    emb_models = get_embedding_models() if is_local else [
        {"name": "gemini-embedding-001 (cloud)", "description": "768-dim, paid"},
    ]
    emb_names = [m.get("name", "text-embedding-004") for m in emb_models]
    emb_sel = st.selectbox(t("model_embed"), emb_names, key="emb_sel")
    if st.button(f"Save Embedding: {emb_sel}", key="btn_save_emb"):
        try:
            from dotenv import set_key
            set_key(env_path, "LOCAL_EMBEDDING_MODEL", emb_sel)
            os.environ["LOCAL_EMBEDDING_MODEL"] = emb_sel
            st.success(f"Embedding model saved: {emb_sel}")
        except Exception as e:
            st.error(str(e))

    # ── Research Pivot ──────────────────────────────────────────────────────
    st.markdown("---")
    st.subheader("🔄 Research Pivot (Change Research Direction)")
    st.caption("If your research interests have shifted, use this to reconfigure the Query Translator, "
              "re-evaluate the database, and re-train the DRL agent.")
    if st.button("🔄 Start Research Pivot", type="primary", key="btn_pivot"):
        with st.spinner("Running Research Pivot wizard..."):
            rc, out = run("research_pivot.py")
            st.session_state.output["pivot"] = out
        if rc == 0: st.success("✅ Research Pivot complete!"); reload_config()
        else: st.warning(f"Completed (code {rc}).")
        show_output("pivot", "research_pivot.py")


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN RENDER
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    render_css()
    page = render_sidebar()

    if page is None:
        return

    # ── Simple Mode Routing ──
    if not st.session_state.advanced_mode:
        if t("simple_home_label") in page:
            simple_home()
        elif t("simple_search_label") in page:
            simple_search()
        elif t("simple_library_label") in page:
            simple_library()
        elif t("simple_eval_label") in page:
            simple_evaluate()
        elif t("simple_agent_label") in page:
            simple_agent()
    else:
        # ── Advanced Mode Routing ──
        st.markdown("""<div style="text-align:center;padding:1rem 0">
        <h2 style="color:#4a9eff;margin:0;font-size:1.5rem">🧠 Project TALOS</h2>
        <p style="color:var(--muted);font-size:.85rem">Research Intelligence Platform v5.3.0</p>
        </div>""", unsafe_allow_html=True)
        handle_advanced_page(page)

    # ── Footer ──
    st.markdown("---")
    st.markdown(f"""<div style="text-align:center;color:#8b949e;font-size:.75rem;padding:0 0 1rem 0">
    TALOS v5.3.4 · © 2026 Christos Smarlamakis · {datetime.now().strftime('%Y-%m-%d %H:%M')}
    </div>""", unsafe_allow_html=True)


if __name__ == "__main__":
    main()