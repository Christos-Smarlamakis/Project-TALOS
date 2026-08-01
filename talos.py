# -*- coding: utf-8 -*-
#  Project TALOS
#  Copyright (C) 2026 Christos Smarlamakis
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Affero General Public License as
#  published by the Free Software Foundation, either version 3 of the
#  License, or (at your option) any later version.
#
#  For commercial licensing, please contact the author.
"""
Module: talos.py
Project: TALOS v5.9.0
Description:
    Main entry point for the TALOS TUI (Text User Interface). Provides a
    Rich-powered terminal dashboard with a dynamic status table showing
    Conda environment, API port, Synapse bus, execution mode, active
    LLM tiers, and the current active research focus from config.json.
    11-option menu with integrated Model Manager, CLI research tools,
    interactive View & Pivot Research Focus (Query Translator), system
    diagnostics, and the Autonomous System Tester (RL Chaos Fuzzer).

    v5.9.0: Autonomous System Tester (RL-Driven Chaos Engineering) integrated
    as menu option 8. Runs a Non-Stationary Epsilon-Greedy Multi-Armed Bandit
    that stress-tests TALOS components via subprocess, diagnoses crashes with
    LLM-as-a-Judge (Fast Edge tier), saves Markdown reports, and displays
    Rich Q-table (Component Fragility) with Spinners, Panels, and Tables.

    v5.8.9: Active Research Focus row in status table (reads
    user_research_goal from config.json, truncated at 65 chars). Option 4
    refactored into interactive View & Pivot Research Focus workflow with
    inline Query Translator execution, raw goal preview panel, and
    boolean query display.

    v5.8.5: Universal TUI Beautification -- all sub-menu launches, diagnostic
    outputs, and informational prompts wrapped in styled Rich Panels with
    color-coded borders. New _build_info_panel() and _build_results_table()
    helpers for consistent Sci-Fi terminal aesthetics. Elite paper scores
    (>=7) highlighted in gold. Query Translator and baseline reports
    display contextual descriptions before subprocess launch. Fixed model name
    display in status panel -- full raw configuration strings printed directly
    without split(":") truncation.

    v5.8.4: Full Rich TUI refactoring (Console, Panel, Table, Box, Text).
    Model Manager integrated as menu option 1 via direct import.
    Zero emojis protocol enforced across all Rich-formatted output.

Dependencies:
    - config.settings: Single source of truth for TALOS_VERSION.
    - src.core.profile_manager: Profile switching and retrieval.
    - src.ai.llm.model_manager: Multi-tier AI model management TUI.
    - src.ai.testing.autonomous_tester: RL-driven chaos engineering daemon.
    - rich: Terminal UI beautification (Console, Panel, Table, Box, Text).
    - questionary: Terminal UI interactive prompts.
    - python-dotenv: Environment variable loading.
"""
import questionary
import os
import subprocess
import sys
import time
import tempfile
import stat
from dotenv import load_dotenv
load_dotenv()

import shutil

from config.settings import TALOS_VERSION, TALOS_API_PORT, TALOS_EXECUTION_MODE
from config.settings import FAST_EDGE_MODEL, HEAVY_REASONING_MODEL
from config.settings import CLOUD_PROVIDER, GEMINI_FLASH_MODEL, DEEPSEEK_MODEL_CHAT
from config.settings import SYNAPSE_BUS_URL
from src.core.profile_manager import (
    get_active_profile_name, save_current_state_to_profile, set_active_profile_name,
)

# -- Rich imports for the gorgeous terminal dashboard --
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich import box
from rich.align import Align

console = Console()

USE_LOCAL_MODEL = False

# -- Script-name -> relative-path map (for run_script) -------------------------
# Maps the script filename to its package subdirectory under src/.
_SCRIPT_MAP = {
    # -- Ingestion --
    "daily_search.py":            "ingestion",
    "historic_search.py":         "ingestion",
    "grey_literature_miner.py":   "ingestion",
    "pdf_downloader.py":          "ingestion",
    "zotero_connector.py":        "ingestion",
    "metadata_enricher.py":       "ingestion",
    "data_enricher.py":           "ingestion",
    # -- DRL --
    "drl_trainer.py":             "ai/drl",
    "train_agent.py":             "ai/drl",
    "talos_live_agent.py":        "ai/drl",
    "talos_service.py":           "ai/drl",
    # -- Optimizers --
    "gwo_rl_optimizer.py":        "ai/optimizers",
    "gwo_live_dashboard.py":      "ai/optimizers",
    # -- Embeddings --
    "embedding_generator.py":     "ai/embeddings",
    "db_embedding_upgrade.py":    "ai/embeddings",
    # -- LLM --
    "query_translator.py":        "ai/llm",
    "model_manager.py":           "ai/llm",
    "research_pivot.py":          "ai/llm",
    # -- Analysis --
    "citation_analyzer.py":       "analysis",
    "author_profiler.py":         "analysis",
    "author_trajectory_analyzer.py": "analysis",
    "trend_analyzer.py":          "analysis",
    "architecture_intelligence_report.py": "analysis",
    "knowledge_path_generator.py": "analysis",
    "recommender.py":             "analysis",
    "generate_baseline_report.py": "analysis",
    "generate_architecture_graph.py": "analysis",
    # -- Utils --
    "db_stats.py":                "utils",
    "recalculate_scores.py":      "utils",
    "reevaluate_database.py":     "utils",
    "migrate_database_schema.py": "utils",
    "api_health_check.py":        "utils",
    "generate_docs.py":           "utils",
    "verify_dependency_map.py":   "utils",
    "interactive_dashboard.py":   "utils",
    # -- Core (profile manager is imported directly, but can also be run) --
    "profile_manager.py":         "core",
    # -- API --
    "talos_service_api.py":       "api",
}

def safe_select(message, choices):
    """Questionary select with graceful fallback.
    Returns None on Ctrl+C (all menus treat None as 'Back')."""
    try:
        return questionary.select(message, choices=choices, use_indicator=True, pointer=">").ask()
    except KeyboardInterrupt:
        return None
    except Exception:
        # Fancy select failed (e.g. limited console) -- plain fallback.
        try:
            return questionary.select(message, choices=choices).unsafe_ask()
        except KeyboardInterrupt:
            return None

def safe_pause(msg="Press Enter to return..."):
    """input() that swallows Ctrl+C so a stray interrupt at a pause prompt
    returns to the menu instead of killing the whole TUI."""
    try:
        input(msg)
    except (KeyboardInterrupt, EOFError):
        print()

def _resolve_script_path(script_name):
    """Resolve a script filename to its full path inside src/<subdir>/.
    Falls back to literal scripts/<name> if not in the map."""
    project_root = os.path.dirname(os.path.abspath(__file__))
    subdir = _SCRIPT_MAP.get(script_name)
    if subdir:
        return os.path.join(project_root, 'src', subdir, script_name)
    # Fallback: old-style (should not happen post-migration)
    return os.path.join(project_root, 'scripts', script_name)

def _build_info_panel(title, message, border_style="bright_blue"):
    """Build a styled Rich Panel for informational messages.

    Args:
        title: Panel title string.
        message: Body text (str or list of str).
        border_style: Rich border style color.

    Returns:
        A rich.panel.Panel ready for console.print().
    """
    if isinstance(message, str):
        body = Text(message, style="white")
    else:
        body = Text()
        for i, line in enumerate(message):
            body.append(line)
            if i < len(message) - 1:
                body.append("\n")
    return Panel(
        Align.center(body),
        title=f"[bold]{title}[/bold]",
        border_style=border_style,
        box=box.ROUNDED,
        padding=(1, 2),
    )


def _build_results_table(papers, title="Search Results"):
    """Build a styled Rich Table for paper search results.

    Columns: ID (cyan), Title (white/bold), Source (magenta),
             Year (yellow), Overall Score (emerald/bold).
    Elite papers (overall_score >= 7) are highlighted in gold.

    Args:
        papers: List of dicts with keys id, title, source,
                publication_year, overall_score.
        title: Table title string.

    Returns:
        A rich.table.Table ready for display.
    """
    table = Table(
        title=f"[bold bright_cyan]{title}[/bold bright_cyan]",
        box=box.ROUNDED,
        border_style="bright_blue",
        show_lines=True,
        header_style="bold bright_cyan",
    )
    table.add_column("ID", style="dim cyan", width=6, no_wrap=True)
    table.add_column("Title", style="white", width=50, overflow="fold")
    table.add_column("Source", style="magenta", width=16)
    table.add_column("Year", style="yellow", width=6, justify="right")
    table.add_column("Score", style="bold emerald", width=8, justify="right")

    for p in papers:
        score = p.get("overall_score", 0)
        try:
            score_f = float(score)
        except (TypeError, ValueError):
            score_f = 0.0
        score_str = f"{score_f:.1f}"
        # Highlight elite papers (score >= 7) in gold
        if score_f >= 7:
            score_style = "[bold gold1]"
            row_style = None
            score_str_display = f"{score_style}{score_str}[/bold gold1]"
        else:
            score_style = ""
            row_style = None
            score_str_display = score_str
        title_text = str(p.get("title", "N/A"))[:100]
        table.add_row(
            str(p.get("id", "?")),
            title_text,
            str(p.get("source", "N/A")),
            str(p.get("publication_year", "N/A")),
            score_str_display,
        )
    return table


def run_script(script_name, python_exe, args=None, capture=False):
    """Launch a TALOS script as a subprocess.

    The script is resolved from the _SCRIPT_MAP (src/<subdir>/<name>).
    All TALOS_* environment variables are forwarded to the child process.
    """
    script_path = _resolve_script_path(script_name)
    command = [python_exe, script_path] + (args or [])
    launch_panel = _build_info_panel(
        f"Launching: {script_name}",
        f"[dim]Command: {' '.join(command)}[/dim]",
        border_style="cyan",
    )
    console.print(launch_panel)
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    if USE_LOCAL_MODEL: env["TALOS_USE_LOCAL"] = "1"
    if os.environ.get("TALOS_MODELS_VERIFIED"): env["TALOS_MODELS_VERIFIED"] = "1"
    if os.environ.get("TALOS_ALLOW_CLOUD_FALLBACK"): env["TALOS_ALLOW_CLOUD_FALLBACK"] = "1"
    if os.environ.get("TALOS_ALLOW_LOCAL_FALLBACK"): env["TALOS_ALLOW_LOCAL_FALLBACK"] = "1"
    if os.environ.get("HF_MODEL_NAME"): env["HF_MODEL_NAME"] = os.environ["HF_MODEL_NAME"]
    try:
        if capture:
            result = subprocess.run(command, check=True, capture_output=True, text=True, encoding="utf-8", env=env)
            print(result.stdout)
            console.print(f"\n[dim green]--- '{script_name}' completed. ---[/dim green]")
            return result
        else:
            subprocess.run(command, check=True, env=env)
            console.print(f"\n[dim green]--- '{script_name}' completed. ---[/dim green]")
            return True
    except KeyboardInterrupt:
        console.print(f"\n[yellow]--- '{script_name}' cancelled by user. ---[/yellow]")
        return False
    except subprocess.CalledProcessError as e:
        if "interactive_dashboard.py" in script_name and e.returncode in [1, 2, -2, 3221225786]:
            console.print(f"\n[dim green]--- Dashboard server terminated by user. ---[/dim green]")
            return True
        console.print(f"\n[red]--- Error: {e} ---[/red]")
        return None
    except Exception as e:
        console.print(f"\n[red]--- Error: {e} ---[/red]")
        return None

def check_first_run(python_exe):
    config_path = "config.json"
    template_path = "config.template.json"
    if not os.path.exists(config_path):
        print("\nWelcome to Project TALOS!")
        if os.path.exists(template_path):
            shutil.copy(template_path, config_path)
            print("Created 'config.json' from the template.")
        else:
            print("ERROR: 'config.template.json' not found.")
            return
        if not os.path.exists("_profiles"): os.makedirs("_profiles")
        # .ask() returns None on Ctrl+C -- treat as "no" (skip config).
        answer = questionary.confirm("Start configuration now?", default=True).ask()
        if answer:
            run_script("query_translator.py", python_exe)
            set_active_profile_name("default")
            save_current_state_to_profile("default")
            print("\n--- Initial setup complete! ---\n")
        else:
            print("\n--- Setup skipped. You can configure later via Profile & Settings. ---\n")
        time.sleep(2)

def author_tools_menu(python_exe):
    os.system('cls' if os.name == 'nt' else 'clear')
    choice = safe_select("Author Analysis Tools:", choices=[
        "1. Quick Profile (Profiler)", "2. Trajectory Analysis",
        "3. Full Report (Profiler -> Trajectory)", questionary.Separator(), "Back"
    ])
    if choice is None or "Back" in choice: return
    if choice.startswith("1.") or choice.startswith("2."):
        aid = questionary.text("Enter author name or ORCID iD:").ask()
        scr = "author_profiler.py" if "1." in choice else "author_trajectory_analyzer.py"
        if aid: run_script(scr, python_exe, args=[aid.strip()])
    elif choice.startswith("3."):
        an = questionary.text("Enter author name:").ask()
        if an:
            result = run_script("author_profiler.py", python_exe, args=an.strip().split(), capture=True)
            if result and result.stdout:
                sel = next((l.split(":", 1)[1].strip() for l in result.stdout.splitlines() if l.startswith("SELECTED_ORCID_ID:")), None)
                if sel: run_script("author_trajectory_analyzer.py", python_exe, args=[sel])

def database_data_menu(python_exe):
    os.system('cls' if os.name == 'nt' else 'clear')
    project_root = os.path.dirname(os.path.abspath(__file__))
    ap = get_active_profile_name()
    pdb = os.path.join(project_root, '_profiles', ap, 'talos_research.db')
    rdb = os.path.join(project_root, 'data', 'talos_research.db')   # moved to data/
    tdb = pdb if os.path.exists(pdb) else rdb
    choice = safe_select("Database & Data:", choices=[
        "1. Statistics & Health", "2. Metadata Enrichment", "3. Zotero Sync",
        "4. Generate/Update Embeddings", "5. AI Re-evaluation", "6. Data Enrichment (Unpaywall)",
        "7. Scientometrics Report", "8. PDF Downloader", questionary.Separator(), "Back"
    ])
    if choice is None or "Back" in choice: return
    if choice.startswith("1."): run_script("db_stats.py", python_exe)
    elif choice.startswith("2."): run_script("metadata_enricher.py", python_exe)
    elif choice.startswith("3."): run_script("zotero_connector.py", python_exe)
    elif choice.startswith("4."): run_script("embedding_generator.py", python_exe)
    elif choice.startswith("5."): run_script("reevaluate_database.py", python_exe)
    elif choice.startswith("6."): run_script("data_enricher.py", python_exe)
    elif choice.startswith("7."): run_script("trend_analyzer.py", python_exe, args=[tdb])
    elif choice.startswith("8."): run_script("pdf_downloader.py", python_exe)

def system_health_menu(python_exe):
    os.system('cls' if os.name == 'nt' else 'clear')
    project_root = os.path.dirname(os.path.abspath(__file__))
    choice = safe_select("System Diagnostics:", choices=[
        "1. Code Integrity Check", "2. Documentation Audit",
        "3. Open Architecture Graph", "4. Architecture Intelligence Report",
        "5. GWO Live Dashboard (Dash -- Real-Time 3D Swarm)",
        questionary.Separator(), "6. Baseline Report (Standard)",
        "7. Baseline Report (Academic -- 600 DPI)", "8. DRL Agent Status",
        questionary.Separator(),
        "9. Generate Codebase Docs (18 Languages, LOCAL Only)",
        questionary.Separator(), "Back"
    ])
    if choice is None or "Back" in choice: return
    if choice.startswith("1."):
        tp = os.path.join(project_root, 'tests', 'test_smoke.py')
        if not os.path.exists(tp):
            tp = os.path.join(project_root, 'test_smoke.py')  # legacy fallback
        if os.path.exists(tp):
            r = subprocess.run([python_exe, tp], check=False, env=os.environ.copy())
            print("\nAll checks passed!" if r.returncode == 0 else f"\nCode {r.returncode}.")
        else:
            print("\nSmoke test not found at tests/test_smoke.py")
    elif choice.startswith("2."):
        run_script("verify_dependency_map.py", python_exe, args=["--all"])
    elif choice.startswith("3."):
        import webbrowser, socket
        port = 8765
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM); s.settimeout(0.5)
            if s.connect_ex(('127.0.0.1', port)) != 0:
                sd = os.path.join(project_root, "templates")
                subprocess.Popen([python_exe, "-m", "http.server", str(port), "--bind", "127.0.0.1", "--directory", sd], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            s.close()
        except Exception: pass
        webbrowser.open(f"http://localhost:{port}/architecture_graph.html")
    elif choice.startswith("4."):
        if questionary.confirm("Start now? (may take 60s)", default=True).ask():
            run_script("architecture_intelligence_report.py", python_exe)
    elif choice.startswith("5."):
        import webbrowser, socket
        print("\n" + "=" * 65)
        print("  GWO Live Dashboard -- Real-Time 3D Swarm Hunt")
        print("=" * 65)
        print("\n  Starts a Dash server at http://localhost:8050")
        print("  Shows live 3D scatter plot of GWO wolf pack convergence.")
        print("  Auto-refreshes every 3 seconds.")
        dash_running = False
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(0.5)
            if s.connect_ex(('127.0.0.1', 8050)) == 0:
                dash_running = True
            s.close()
        except Exception:
            pass
        if not dash_running:
            print("\n  Starting Dash server...")
            script_path = _resolve_script_path("gwo_live_dashboard.py")
            subprocess.Popen(
                [python_exe, script_path],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
            time.sleep(2)
        webbrowser.open("http://localhost:8050")
        print("\n  Dashboard opened in browser.")
        print("  NOTE: Run GWO first from another terminal with --live flag.")
        print("  python src/ai/optimizers/gwo_rl_optimizer.py --live")
    elif choice.startswith("6."): run_script("generate_baseline_report.py", python_exe)
    elif choice.startswith("7."): run_script("generate_baseline_report.py", python_exe, args=["--academic"])
    elif choice.startswith("8."):
        mp = os.path.join(project_root, "models", "dddqn_trained.pth")
        gp = os.path.join(project_root, "models", "gwo_best_params.json")
        try:
            c = Console(); t = Table(show_header=False, box=None)
            t.add_column("K"); t.add_column("V")
            if os.path.exists(mp): t.add_row("Model", f"[green]Present ({os.path.getsize(mp)/1024:.0f}KB)")
            else: t.add_row("Model", "[red]Not found")
            if os.path.exists(gp):
                import json
                with open(gp) as f: p = json.load(f)
                t.add_row("LR", f"[yellow]{p['learning_rate']:.6e}")
                t.add_row("Gamma", f"[yellow]{p['gamma']:.4f}")
                t.add_row("Epsilon Decay", f"[yellow]{p['epsilon_decay']:.6f}")
                t.add_row("Best Fitness", f"[magenta]{p['best_fitness']:.1f}")
                t.add_row("Best Reward", f"[green]{p['best_avg_reward']:.1f}")
            else: t.add_row("GWO", "[red]Not found")
            c.print(Panel(t, title="[bold]DRL Agent Status", border_style="cyan"))
        except ImportError:
            print("\n=== DRL Agent Status ===")
            if os.path.exists(mp): print(f"  Model: {mp} ({os.path.getsize(mp)/1024:.0f}KB)")
            else: print("  No trained model")
            if os.path.exists(gp):
                import json
                with open(gp) as f: p = json.load(f)
                print(f"  LR={p['learning_rate']:.6e} GAMMA={p['gamma']:.4f} EPS={p['epsilon_decay']:.6f} Fitness={p['best_fitness']:.1f}")
    elif choice.startswith("9."):
        print("\n" + "=" * 65)
        print("  Codebase Documentation Generator (18 Languages)")
        print("=" * 65)
        print("\n  Uses LOCAL Ollama -- zero cloud cost, full privacy.")
        print("  Produces detailed Markdown docs for every code file you select.")
        if questionary.confirm("Launch documentation generator?", default=True).ask():
            run_script("generate_docs.py", python_exe)
    print(); safe_pause("Press Enter...")

def api_keys_menu(python_exe):
    from dotenv import dotenv_values
    project_root = os.path.dirname(os.path.abspath(__file__))
    env_path = os.path.join(project_root, '.env')
    if not os.path.exists(env_path):
        ep = os.path.join(project_root, 'example.env')
        if os.path.exists(ep): shutil.copy(ep, env_path)
        else: open(env_path, 'w').close()
    ALL_KEYS = [
        ("Contact", [("MAILTO", "Contact Email")]),
        ("Premium AI", [("GEMINI_API_KEY", "Gemini"), ("DEEPSEEK_API_KEY", "DeepSeek"), ("HF_TOKEN", "HuggingFace")]),
        ("Academic", [("SEMANTIC_SCHOLAR_API_KEY", "Semantic Scholar"), ("IEEE_API_KEY", "IEEE"),
         ("ELSEVIER_API_KEY", "Scopus"), ("SPRINGER_API_KEY", "Springer"), ("CORE_API_KEY", "CORE"), ("OPENARCHIVES_API_KEY", "OpenArchives")]),
        ("Integrations", [("DISCORD_WEBHOOK_URL", "Discord"), ("ZOTERO_USER_ID", "Zotero ID"), ("ZOTERO_API_KEY", "Zotero Key"),
         ("ORCID_CLIENT_ID", "ORCID ID"), ("ORCID_CLIENT_SECRET", "ORCID Secret")]),
        ("Local", [("LOCAL_MODEL_NAME", "Chat Model"), ("LOCAL_EMBEDDING_MODEL", "Embedding Model")]),
    ]
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        print("\n  API Keys Management\n")
        vals = dotenv_values(env_path)
        for cat, keys in ALL_KEYS:
            print(f"  [{cat}]")
            for k, d in keys:
                v = vals.get(k, ""); s = "[SET]" if v.strip() else "[NOT SET]"
                print(f"    {k:<28} | {s:<8} | {d}")
        print("\n  [1] Edit key  [2] API Diagnostics  [3] Back")
        c = safe_select("Action:", ["1. Edit a key", "2. API Diagnostics", "3. Back"])
        if c is None or c.startswith("3"): return
        if c.startswith("1"):
            flat = []
            for cat, keys in ALL_KEYS:
                flat.append(f"--- {cat} ---")
                for k, d in keys:
                    v = vals.get(k, ""); s = "[SET]" if v.strip() else "[NOT SET]"
                    flat.append(f"{k}  {s}")
            flat.append("Cancel")
            sel = safe_select("Key:", choices=flat)
            if sel and not sel.startswith("---") and sel != "Cancel":
                k = sel.split()[0]; cv = vals.get(k, "")
                nv = questionary.text(f"New value for {k}:", default=cv).ask()
                if nv is not None:
                    from dotenv import set_key
                    try:
                        set_key(env_path, k, nv.strip())
                        os.environ[k] = nv.strip()
                        print(f"\n  [{k}] updated.")
                    except Exception as e:
                        print(f"\n  Error: {e}")
        elif c.startswith("2"):
            tp = _resolve_script_path("api_health_check.py")
            if os.path.exists(tp): subprocess.run([python_exe, tp], check=False)
        safe_pause("\nPress Enter...")

def profile_settings_menu(python_exe):
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        c = safe_select("Profile & Settings:", choices=[
            "1. Manage Profiles", "2. Research Goal (Query Translator)", "3. AI Model Management",
            "4. API Keys Management", "5. API Diagnostics", "6. Research Pivot & Retrain",
            questionary.Separator(), "Back"
        ])
        if c is None or "Back" in c: return
        if c.startswith("1."): run_script("profile_manager.py", python_exe)
        elif c.startswith("2."): run_script("query_translator.py", python_exe)
        elif c.startswith("3."): run_script("model_manager.py", python_exe)
        elif c.startswith("4."): api_keys_menu(python_exe)
        elif c.startswith("5."):
            tp = _resolve_script_path("api_health_check.py")
            if os.path.exists(tp): subprocess.run([python_exe, tp], check=False)
        elif c.startswith("6."): run_script("research_pivot.py", python_exe)
        safe_pause("\nPress Enter...")

def _verify_local_models():
    import requests
    print("\n[Verifying local models...]")
    try:
        r = requests.get("http://localhost:11434/api/tags", timeout=5)
        if r.status_code != 200: return
        models = [m['name'] for m in r.json().get('models', [])]
        for m in ["gemma3:12b", "nomic-embed-text"]:
            if m not in models:
                print(f"  >> Pulling {m}...")
                subprocess.run(["ollama", "pull", m], check=True)
            else: print(f"  >> {m} installed.")
        os.environ["TALOS_MODELS_VERIFIED"] = "1"
    except Exception: pass


# ---------------------------------------------------------------------------
# -- Rich TUI: Dynamic Status Table Builder --
# ---------------------------------------------------------------------------

def _build_status_table():
    """Build and return a Rich Table with live system status information.

    Reads configuration from environment variables and config/settings.py
    to display:
      - Conda Environment / API Port / Synapse Bus
      - Active Execution Mode (Air-Gapped Local / Hybrid / Cloud)
      - Active Tiers: Fast Edge, Heavy Reasoning, Cloud Provider
      - Active Research Focus (from config.json user_research_goal)
    """
    # -- Detect Conda environment name --
    conda_env = os.environ.get("CONDA_DEFAULT_ENV", "N/A")

    # -- Execution mode human-readable label --
    mode = os.environ.get("TALOS_EXECUTION_MODE", TALOS_EXECUTION_MODE)
    mode_labels = {
        "local":  "Air-Gapped Local",
        "hybrid": "Hybrid (Local + Cloud Fallback)",
        "cloud":  "Cloud Priority",
    }
    mode_display = mode_labels.get(mode, mode)

    # -- Fast Edge model: use raw configuration string directly --
    fast_edge = os.environ.get("FAST_EDGE_MODEL", FAST_EDGE_MODEL)

    # -- Heavy Reasoning model: use raw configuration string directly --
    heavy_model = os.environ.get("HEAVY_REASONING_MODEL", HEAVY_REASONING_MODEL)

    # -- Cloud provider: display raw provider name + raw model name --
    cloud_prov = os.environ.get("TALOS_CLOUD_PROVIDER", CLOUD_PROVIDER)
    if cloud_prov == "gemini":
        gemini_model = os.environ.get("GEMINI_FLASH_MODEL", GEMINI_FLASH_MODEL)
        cloud_display = f"Gemini ({gemini_model})"
    elif cloud_prov == "deepseek":
        deepseek_model = os.environ.get("DEEPSEEK_MODEL_CHAT", DEEPSEEK_MODEL_CHAT)
        cloud_display = f"DeepSeek ({deepseek_model})"
    else:
        cloud_display = str(cloud_prov) if cloud_prov else "None"

    # -- Synapse bus URL shorthand --
    synapse_short = "localhost:8000" if "8000" in SYNAPSE_BUS_URL else SYNAPSE_BUS_URL

    # -- Build the table --
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Key", style="dim cyan", no_wrap=True)
    table.add_column("Value", style="white")

    table.add_row("Conda Environment", f"[bold bright_cyan]{conda_env}[/bold bright_cyan]")
    table.add_row("API Port", f"[bold green]{TALOS_API_PORT}[/bold green]")
    table.add_row("Synapse Bus", f"[dim green]{synapse_short}[/dim green]")
    table.add_row("", "")
    table.add_row("Execution Mode", f"[bold yellow]{mode_display}[/bold yellow]")
    table.add_row("", "")
    table.add_row("Fast Edge Tier", f"[bright_cyan]{fast_edge}[/bright_cyan]")
    table.add_row("Heavy Reasoning Tier", f"[bright_magenta]{heavy_model}[/bright_magenta]")
    table.add_row("Cloud Provider", f"[bright_blue]{cloud_display}[/bright_blue]")
    table.add_row("", "")
    # -- Active Research Focus (from config.json) --
    focus_display = "[dim]Not configured[/dim]"
    try:
        import json as _json
        with open("config.json", "r", encoding="utf-8") as _f:
            _cfg = _json.load(_f)
        goal = _cfg.get("user_research_goal") or _cfg.get("phd_focus_system_prompt", "")
        if goal.strip():
            if len(goal) > 65:
                goal = goal[:65].rstrip() + "..."
            focus_display = f"[bright_green]{goal}[/bright_green]"
    except Exception:
        pass
    table.add_row("Active Research Focus", focus_display)

    return table


# ---------------------------------------------------------------------------
# -- Interactive View & Pivot Research Focus (v5.8.9) --
# ---------------------------------------------------------------------------

def _view_and_pivot_research_focus(python_exe, project_root):
    """Display current research goal and offer interactive pivot workflow.

    Shows a cyan-bordered Panel with the raw research goal text from
    config.json plus a preview of existing boolean queries (if any).
    The user may then either pivot to a new goal (running Query Translator
    in-place), view all 14 generated queries, or return to the main menu.

    Args:
        python_exe: Path to the Python executable.
        project_root: Absolute path to the project root directory.
    """
    os.system('cls' if os.name == 'nt' else 'clear')

    # -- Read current goal and queries from config.json --
    current_goal = ""
    queries = {}
    try:
        import json as _json
        with open("config.json", "r", encoding="utf-8") as _f:
            _cfg = _json.load(_f)
        current_goal = _cfg.get("user_research_goal") or _cfg.get("phd_focus_system_prompt", "")
        # Collect any keys ending in _query as boolean queries
        for k, v in _cfg.items():
            if k.endswith("_query") and isinstance(v, str) and v.strip():
                queries[k] = v
    except Exception:
        current_goal = "[Error reading config.json]"

    # -- Build the goal preview panel --
    goal_body = Text()
    if current_goal.strip():
        goal_body.append("Current Research Goal:\n\n", style="bold white")
        goal_body.append(current_goal.strip(), style="bright_green")
    else:
        goal_body.append("No research goal configured.", style="dim yellow")

    goal_panel = Panel(
        goal_body,
        title="[bold]Active Research Focus[/bold]",
        border_style="cyan",
        box=box.ROUNDED,
        padding=(1, 2),
    )
    console.print(goal_panel)
    console.print("")

    # -- Show query preview if queries exist --
    if queries:
        query_text = Text()
        query_text.append(f"Boolean Queries Defined: {len(queries)} of 14\n\n", style="bold bright_cyan")
        for i, (k, v) in enumerate(sorted(queries.items())):
            short_name = k.replace("_query", "")
            short_val = v[:80] + ("..." if len(v) > 80 else "")
            query_text.append(f"[dim]{short_name}:[/dim] {short_val}\n")
            if i >= 4:  # Show first 5, then ...
                remaining = len(queries) - i - 1
                if remaining > 0:
                    query_text.append(f"\n[dim]... and {remaining} more. Select 'View All Queries' below to see full list.[/dim]")
                break
        query_panel = Panel(
            query_text,
            title="[bold]Query Preview[/bold]",
            border_style="bright_blue",
            box=box.ROUNDED,
            padding=(1, 2),
        )
        console.print(query_panel)
        console.print("")

    # -- Interactive menu --
    pivot_choice = safe_select("View & Pivot Research Focus:", choices=[
        "1. Pivot to New Research Goal (Run Query Translator)",
        "2. View All 14 Generated Boolean Queries",
        "3. Return to Main Menu",
    ])

    if pivot_choice is None or "3." in pivot_choice:
        return

    if "1." in pivot_choice:
        # -- Prompt for new goal --
        new_goal = questionary.text(
            "Enter your new research goal (natural language):",
            default=current_goal.strip() if current_goal.strip() else ""
        ).ask()
        if new_goal is None or not new_goal.strip():
            console.print("\n[yellow]Pivot cancelled -- no goal provided.[/yellow]")
            safe_pause()
            return

        # -- Update config.json with the new goal --
        try:
            import json as _json
            with open("config.json", "r", encoding="utf-8") as _f:
                _cfg = _json.load(_f)
            _cfg["user_research_goal"] = new_goal.strip()
            # Clear old queries so PYTHIA regenerates them fresh
            for k in list(_cfg.keys()):
                if k.endswith("_query"):
                    _cfg[k] = ""
            with open("config.json", "w", encoding="utf-8") as _f:
                _json.dump(_cfg, _f, indent=2, ensure_ascii=False)
            console.print("\n[green][SUCCESS][/green] Research goal updated. Launching PYTHIA Query Translator...\n")
        except Exception as e:
            console.print(f"\n[red]Error updating config.json: {e}[/red]")
            safe_pause()
            return

        # -- Run Query Translator in-process (same as run_script but with
        #    confirmation first) --
        info = _build_info_panel(
            "PYTHIA -- Query Translator",
            "Translates your natural-language research goal into optimized\n"
            "boolean search queries for all 14 academic APIs.\n"
            "[dim]Uses the AI Manager with Research Architect persona.[/dim]",
            border_style="bright_magenta",
        )
        console.print(info)
        if questionary.confirm("Proceed with Query Translation?", default=True).ask():
            run_script("query_translator.py", python_exe)
            # -- Show success panel --
            success = _build_info_panel(
                "Research Focus Pivot Complete",
                f"New goal set and queries regenerated.\n"
                f"[bright_green]{new_goal.strip()[:100]}[/bright_green]",
                border_style="green",
            )
            console.print(success)
        safe_pause()

    elif "2." in pivot_choice:
        # -- View all generated boolean queries --
        os.system('cls' if os.name == 'nt' else 'clear')
        try:
            import json as _json
            with open("config.json", "r", encoding="utf-8") as _f:
                _cfg = _json.load(_f)
            q_table = Table(
                title="[bold bright_cyan]All Generated Boolean Queries[/bold bright_cyan]",
                box=box.ROUNDED,
                border_style="cyan",
                show_lines=True,
                header_style="bold bright_cyan",
            )
            q_table.add_column("#", style="dim cyan", width=4, justify="right")
            q_table.add_column("API Source", style="bright_magenta", width=20)
            q_table.add_column("Boolean Query", style="white", width=60, overflow="fold")
            count = 0
            for k in sorted(_cfg.keys()):
                if k.endswith("_query"):
                    count += 1
                    v = _cfg[k]
                    q_table.add_row(str(count), k.replace("_query", ""), v if v else "[dim](empty)[/dim]")
            if count == 0:
                q_table.add_row("", "[dim yellow]No queries defined.[/dim yellow]", "")
            console.print(q_table)
        except Exception as e:
            console.print(f"[red]Error reading config.json: {e}[/red]")
        safe_pause()


def main_menu():
    python_exe = sys.executable or "python"
    project_root = os.path.dirname(os.path.abspath(__file__))
    check_first_run(python_exe)
    time.sleep(1)
    global USE_LOCAL_MODEL
    if not USE_LOCAL_MODEL:
        c = safe_select("Where to run AI calls?", choices=["LOCAL (Ollama)", "CLOUD (Gemini+DeepSeek)"])
        USE_LOCAL_MODEL = (c and "LOCAL" in c)
        if USE_LOCAL_MODEL:
            _verify_local_models()
            fb = safe_select("Allow cloud fallback?", choices=["NO", "YES"])
            if fb and "YES" in fb: os.environ["TALOS_ALLOW_CLOUD_FALLBACK"] = "1"
        else:
            fb = safe_select("Allow local fallback?", choices=["NO", "YES"])
            if fb and "YES" in fb: os.environ["TALOS_ALLOW_LOCAL_FALLBACK"] = "1"
            if os.getenv("HF_TOKEN"):
                m = safe_select("HF model:", choices=["Mixtral-8x7B", "Llama-3.1-8B", "Qwen2.5-7B", "Mistral-7B", "Phi-3-mini", "Gemma-2-2b"])
                if m: os.environ["HF_MODEL_NAME"] = m

    while True:
        os.system('cls' if os.name == 'nt' else 'clear')

        # -- Build the Rich dashboard header --
        ap = get_active_profile_name()

        # -- Title banner --
        title_text = Text()
        title_text.append("TALOS", style="bold bright_cyan")
        title_text.append(f" v{TALOS_VERSION}", style="bold cyan")
        title_text.append(f"  |  Profile: [{ap}]", style="dim white")

        # -- Database stats line --
        db_line = ""
        try:
            from src.core.database_manager import DatabaseManager
            db = DatabaseManager(); s = db.get_database_statistics()
            db_line = f"Papers: {s['total_papers']}  |  Elite: {s['elite_papers']}"
        except Exception:
            pass

        # -- VRAM line --
        vram_line = ""
        try:
            from src.core.hardware import detect_vram_gb
            v = detect_vram_gb()
            if v: vram_line = f"VRAM: {v:.0f} GB"
        except Exception:
            pass

        # Status panel
        status_table = _build_status_table()

        # -- Assemble the full header panel --
        header_content = Table(show_header=False, box=None, padding=(0, 0))
        header_content.add_column(justify="center")
        header_content.add_row(title_text)
        if db_line or vram_line:
            stats_parts = []
            if db_line: stats_parts.append(db_line)
            if vram_line: stats_parts.append(vram_line)
            header_content.add_row(Text(" | ".join(stats_parts), style="dim white"))
        header_content.add_row("")
        header_content.add_row(status_table)

        header_panel = Panel(
            Align.center(header_content),
            border_style="bright_blue",
            box=box.ROUNDED,
            padding=(1, 2),
        )

        console.print(header_panel)

        # -- Menu choices (11 options) --
        choice = safe_select("Select operation:", choices=[
            questionary.Separator("  CORE CONFIGURATION"),
            " 1. Configure AI Models & Execution Modes (Model Manager)",
            questionary.Separator("  SEARCH & DISCOVERY"),
            " 2. CLI Research Search (Interactive)",
            questionary.Separator("  ENRICHMENT & ANALYSIS"),
            " 3. Metadata Enrichment",
            " 4. View & Pivot Research Focus (Query Translator)",
            questionary.Separator("  MODEL MANAGEMENT"),
            " 5. Model Manager (Legacy/Direct)",
            questionary.Separator("  TESTING & CI/CD"),
            " 6. Autonomous System Tester (RL Chaos Fuzzer)",
            questionary.Separator("  SYSTEM DIAGNOSTICS"),
            " 7. Baseline Report (Standard)",
            " 8. Baseline Report (Academic -- 600 DPI)",
            " 9. DRL Agent Status",
            "10. Codebase Docs Generator (18 Languages)",
            questionary.Separator(),
            "11. Exit",
        ])
        if choice is None or "Exit" in choice: break
        fm = "Press Enter to return..."

        # -- Route menu choices --
        if "1." in choice:
            # -- Model Manager: import and run main() in-process --
            console.print("\n[bold bright_cyan]Launching AI Model Manager...[/bold bright_cyan]\n")
            try:
                from src.ai.llm.model_manager import main as mm_main
                mm_main()
            except Exception as e:
                console.print(f"[red]Error launching Model Manager: {e}[/red]")
                safe_pause("\nPress Enter...")
        elif "2." in choice:
            # -- CLI Research Search: open the full legacy search menu --
            choice2 = safe_select("CLI Research Search:", choices=[
                questionary.Separator("  SEARCH & DISCOVERY"),
                "2a. Daily Search (14 APIs)",
                "2b. Historical Search (Deep Archive)",
                "2c. Grey Literature / Web Horizon Scan",
                questionary.Separator("  AI-POWERED SEARCH (DRL)"),
                "2d. Live DRL Agent (Real API Orchestration)",
                "2e. Autonomous Research Process (24/7)",
                questionary.Separator("  ANALYSIS & INSIGHTS"),
                "2f. Knowledge Path Generator",
                "2g. Citation Network Analyzer",
                "2h. Strategic Reading Report",
                "2i. Author Analysis Tools",
                "2j. Interactive Dashboard",
                "2k. DRL Training (API Orchestrator)",
                "2l. Compare Baselines (Pre/Post DRL)",
                questionary.Separator(), "Back"
            ])
            if choice2 is None or "Back" in choice2: continue
            if "2a" in choice2: run_script("daily_search.py", python_exe)
            elif "2b" in choice2:
                if questionary.confirm("This may take a long time. Sure?", default=False).ask():
                    run_script("historic_search.py", python_exe)
            elif "2c" in choice2: run_script("grey_literature_miner.py", python_exe)
            elif "2d" in choice2:
                info = _build_info_panel(
                    "Live DRL Agent -- Real API Orchestration",
                    "The trained DRL agent selects the optimal API source in real-time\n"
                    "using the 14-source academic API environment.",
                    border_style="cyan",
                )
                console.print(info)
                if questionary.confirm("Start live agent? (Ctrl+C to stop)", default=True).ask():
                    run_script("talos_live_agent.py", python_exe, args=["--verbose"])
            elif "2e" in choice2:
                info = _build_info_panel(
                    "Autonomous Research Process -- 24/7 + DRL",
                    "Runs INDEFINITELY. Uses the DRL agent to discover papers\n"
                    "around the clock with periodic AI evaluation and reporting.",
                    border_style="yellow",
                )
                console.print(info)
                if questionary.confirm("Start autonomous process? (Ctrl+C to stop)", default=True).ask():
                    run_script("talos_service.py", python_exe)
            elif "2f" in choice2: run_script("knowledge_path_generator.py", python_exe)
            elif "2g" in choice2: run_script("citation_analyzer.py", python_exe)
            elif "2h" in choice2: run_script("recommender.py", python_exe)
            elif "2i" in choice2: author_tools_menu(python_exe)
            elif "2j" in choice2:
                run_script("interactive_dashboard.py", python_exe)
                fm = "Dashboard terminated. Press Enter..."
            elif "2k" in choice2: run_script("drl_trainer.py", python_exe)
            elif "2l" in choice2:
                info = _build_info_panel(
                    "Compare Baselines -- Pre/Post DRL",
                    "Generates a new academic baseline report and compares it\n"
                    "against the previous one (Delta analysis).",
                    border_style="yellow",
                )
                console.print(info)
                if questionary.confirm("Generate new baseline and compare?", default=True).ask():
                    run_script("generate_baseline_report.py", python_exe, args=["--academic"])
                    rb = os.path.join(project_root, "reports", "general_status_report")
                    if os.path.exists(rb):
                        folders = sorted([d for d in os.listdir(rb) if os.path.isdir(os.path.join(rb, d))], reverse=True)
                        if len(folders) >= 2:
                            comp = _build_info_panel(
                                "Baseline Comparison",
                                [f"[cyan]Latest:[/cyan]   {folders[0]}",
                                 f"[cyan]Previous:[/cyan] {folders[1]}"],
                                border_style="green",
                            )
                            console.print(comp)
        elif "3." in choice:
            info = _build_info_panel(
                "Metadata Enrichment",
                "Enriches paper records with metadata from OpenAlex,\n"
                "Crossref, DBLP, and Semantic Scholar (multi-source fallback chain).",
                border_style="cyan",
            )
            console.print(info)
            run_script("metadata_enricher.py", python_exe)
        elif "4." in choice:
            # -- View & Pivot Research Focus (interactive workflow) --
            _view_and_pivot_research_focus(python_exe, project_root)
        elif "5." in choice:
            run_script("model_manager.py", python_exe)
        elif "6." in choice:
            # -- Autonomous System Tester (RL Chaos Fuzzer) --
            info = _build_info_panel(
                "Autonomous System Tester (RL-Driven Chaos Engineering)",
                "Stress-tests TALOS system components using a Non-Stationary\n"
                "Epsilon-Greedy Multi-Armed Bandit. Diagnoses crashes with\n"
                "LLM-as-a-Judge (Fast Edge tier) and saves Markdown reports.\n"
                "[dim]Displays Rich Q-table (Component Fragility) with Spinners,\n"
                "Panels, and Tables. Emits Synapse events on each test cycle.[/dim]",
                border_style="bright_magenta",
            )
            console.print(info)
            cycles_str = questionary.text(
                "Number of test cycles (default 10):",
                default="10"
            ).ask()
            if cycles_str is not None:
                try:
                    cycles = int(cycles_str.strip()) if cycles_str.strip() else 10
                except ValueError:
                    cycles = 10
                    console.print("[yellow]Invalid input. Using default (10).[/yellow]")
                try:
                    from src.ai.testing.autonomous_tester import run_autonomous_tester
                    run_autonomous_tester(cycles=cycles)
                except Exception as e:
                    console.print(f"[red]Error running Autonomous Tester: {e}[/red]")
        elif "7." in choice:
            info = _build_info_panel(
                "Baseline Report (Standard)",
                "Generates a standard baseline report with score distribution,\n"
                "quad-layer averages, source distribution, and embedding coverage.",
                border_style="green",
            )
            console.print(info)
            run_script("generate_baseline_report.py", python_exe)
        elif "8." in choice:
            info = _build_info_panel(
                "Baseline Report (Academic -- 600 DPI)",
                "Generates a publication-quality academic baseline report\n"
                "with serif fonts, 600 DPI plots, and muted color palette\n"
                "suitable for IEEE/Springer journals.",
                border_style="yellow",
            )
            console.print(info)
            run_script("generate_baseline_report.py", python_exe, args=["--academic"])
        elif "9." in choice:
            # -- DRL Status: rich-powered display --
            mp = os.path.join(project_root, "models", "dddqn_trained.pth")
            gp = os.path.join(project_root, "models", "gwo_best_params.json")
            t = Table(show_header=False, box=box.SIMPLE, border_style="cyan")
            t.add_column("Parameter", style="dim cyan")
            t.add_column("Value", style="white")
            if os.path.exists(mp):
                t.add_row("DRL Model", f"[green]Present ({os.path.getsize(mp)/1024:.0f} KB)")
            else:
                t.add_row("DRL Model", "[red]Not found")
            if os.path.exists(gp):
                import json
                with open(gp) as f: p = json.load(f)
                t.add_row("Learning Rate", f"[yellow]{p['learning_rate']:.6e}")
                t.add_row("Gamma", f"[yellow]{p['gamma']:.4f}")
                t.add_row("Epsilon Decay", f"[yellow]{p['epsilon_decay']:.6f}")
                t.add_row("Best Fitness", f"[magenta]{p['best_fitness']:.1f}")
                t.add_row("Best Reward", f"[green]{p['best_avg_reward']:.1f}")
            else:
                t.add_row("GWO Params", "[red]Not found")
            drl_panel = Panel(
                t,
                title="[bold]DRL Agent Status[/bold]",
                border_style="cyan",
                box=box.ROUNDED,
            )
            console.print(drl_panel)
        elif "10." in choice:
            info = _build_info_panel(
                "Codebase Documentation Generator (18 Languages)",
                "Uses LOCAL Ollama -- zero cloud cost, full privacy.\n"
                "Produces detailed Markdown docs for every code file selected.\n"
                "[dim]Supports: English, Greek, Chinese, Hindi, Spanish, Arabic, and 12 more.[/dim]",
                border_style="bright_blue",
            )
            console.print(info)
            if questionary.confirm("Launch documentation generator?", default=True).ask():
                run_script("generate_docs.py", python_exe)

        if choice and "Exit" not in choice:
            safe_pause(fm)

    # -- Exit sequence --
    console.print("\n[dim]TALOS Command Center Closing...[/dim]\n")

if __name__ == "__main__":
    # Top-level guard: any stray Ctrl+C exits cleanly with code 0
    # (no traceback dumped to the user).
    try:
        main_menu()
    except KeyboardInterrupt:
        print("\n\nTALOS Closing...\n")
        sys.exit(0)