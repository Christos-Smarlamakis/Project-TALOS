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
Module: talos.py (v5.2.1)
Project: TALOS v5.2.1
Description:
    Central CLI entry point with hierarchical menu system.
    v5.2.1 adds: Live DRL Agent, Autonomous Process (24/7), Research Pivot.
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

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'scripts')))
from scripts.profile_manager import (
    get_active_profile_name, save_current_state_to_profile, set_active_profile_name,
)

USE_LOCAL_MODEL = False

def safe_select(message, choices):
    try:
        return questionary.select(message, choices=choices, use_indicator=True, pointer="»").ask()
    except Exception:
        return questionary.select(message, choices=choices).unsafe_ask()

def run_script(script_name, python_exe, args=None, capture=False):
    project_root = os.path.dirname(os.path.abspath(__file__))
    script_path = os.path.join(project_root, 'scripts', script_name)
    command = [python_exe, script_path] + (args or [])
    print(f"\n--- Launching '{script_name}'... ---\n")
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
            print(f"\n--- '{script_name}' completed. ---")
            return result
        else:
            subprocess.run(command, check=True, env=env)
            print(f"\n--- '{script_name}' completed. ---")
            return True
    except KeyboardInterrupt:
        print(f"\n\n--- '{script_name}' cancelled. ---")
        return False
    except subprocess.CalledProcessError as e:
        if "interactive_dashboard.py" in script_name and e.returncode in [1, 2, -2, 3221225786]:
            print(f"\n--- Dashboard server terminated by user. ---")
            return True
        print(f"\n--- Error: {e} ---")
        return None
    except Exception as e:
        print(f"\n--- Error: {e} ---")
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
        if questionary.confirm("Start configuration now?", default=True).ask():
            run_script("query_translator.py", python_exe)
            set_active_profile_name("default")
            save_current_state_to_profile("default")
        print("\n--- Initial setup complete! ---\n")
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
    rdb = os.path.join(project_root, 'talos_research.db')
    tdb = pdb if os.path.exists(pdb) else rdb
    choice = safe_select("Database & Data:", choices=[
        "1. Statistics & Health", "2. Metadata Enrichment (APOLLO)", "3. Zotero Sync",
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
        "5. GWO Swarm Hunt (3D Visualization — Opens Streamlit GUI)",
        questionary.Separator(), "6. Baseline Report (Standard)",
        "7. Baseline Report (Academic — 600 DPI)", "8. DRL Agent Status",
        questionary.Separator(),
        "9. Generate Codebase Docs (18 Languages, LOCAL Only)",
        questionary.Separator(), "Back"
    ])
    if choice is None or "Back" in choice: return
    if choice.startswith("1."):
        tp = os.path.join(project_root, 'test_smoke.py')
        if os.path.exists(tp):
            r = subprocess.run([python_exe, tp], check=False, env=os.environ.copy())
            print("\nAll checks passed!" if r.returncode == 0 else f"\nCode {r.returncode}.")
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
        except: pass
        webbrowser.open(f"http://localhost:{port}/architecture_graph.html")
    elif choice.startswith("4."):
        if questionary.confirm("Start now? (may take 60s)", default=True).ask():
            run_script("architecture_intelligence_report.py", python_exe)
    elif choice.startswith("5."):
        # GWO Swarm Hunt — opens Streamlit GUI for 3D visualization
        import webbrowser
        print("\n" + "=" * 65)
        print("  GWO Swarm Hunt — 3D Interactive Visualization")
        print("=" * 65)
        print("\n  Opens Streamlit GUI with Plotly 3D scatter plot showing")
        print("  Grey Wolf Optimizer convergence across iterations.")
        print("  Use the DRL Agent Dashboard -> GWO Swarm Hunt section.")
        if questionary.confirm("Open Streamlit GUI now?", default=True).ask():
            print("\n  Starting Streamlit... Press Ctrl+C in this terminal when done.")
            subprocess.Popen([python_exe, "-m", "streamlit", "run",
                os.path.join(project_root, "app.py")],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(3)
            webbrowser.open("http://localhost:8501")
    elif choice.startswith("6."): run_script("generate_baseline_report.py", python_exe)
    elif choice.startswith("7."): run_script("generate_baseline_report.py", python_exe, args=["--academic"])
    elif choice.startswith("8."):
        mp = os.path.join(project_root, "models", "dddqn_trained.pth")
        gp = os.path.join(project_root, "models", "gwo_best_params.json")
        try:
            from rich.console import Console; from rich.table import Table; from rich.panel import Panel
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
        print("\n  Uses LOCAL Ollama — zero cloud cost, full privacy.")
        print("  Produces detailed Markdown docs for every code file you select.")
        if questionary.confirm("Launch documentation generator?", default=True).ask():
            run_script("generate_docs.py", python_exe)
    print(); input("Press Enter...")

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
                    # Rewrite env file preserving others
                    from dotenv import set_key
                    try:
                        set_key(env_path, k, nv.strip())
                        os.environ[k] = nv.strip()
                        print(f"\n  [{k}] updated.")
                    except Exception as e:
                        print(f"\n  Error: {e}")
        elif c.startswith("2"):
            tp = os.path.join(project_root, 'scripts', 'api_health_check.py')
            if os.path.exists(tp): subprocess.run([python_exe, tp], check=False)
        input("\nPress Enter...")

def profile_settings_menu(python_exe):
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        c = safe_select("Profile & Settings:", choices=[
            "1. Manage Profiles", "2. Research Goal (PYTHIA)", "3. AI Model Management",
            "4. API Keys Management", "5. API Diagnostics", "6. Research Pivot & Retrain",
            questionary.Separator(), "Back"
        ])
        if c is None or "Back" in c: return
        if c.startswith("1."): run_script("profile_manager.py", python_exe)
        elif c.startswith("2."): run_script("query_translator.py", python_exe)
        elif c.startswith("3."): run_script("model_manager.py", python_exe)
        elif c.startswith("4."): api_keys_menu(python_exe)
        elif c.startswith("5."):
            tp = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'scripts', 'api_health_check.py')
            if os.path.exists(tp): subprocess.run([python_exe, tp], check=False)
        elif c.startswith("6."): run_script("research_pivot.py", python_exe)
        input("\nPress Enter...")

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
    except: pass

def main_menu():
    python_exe = sys.executable or "python"
    project_root = os.path.dirname(os.path.abspath(__file__))
    print(f"INFO: Python from: {python_exe}")
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
        ap = get_active_profile_name()
        header = f"TALOS v5.3.0 | Profile: [{ap}]"
        try:
            from core.database_manager import DatabaseManager
            db = DatabaseManager(); s = db.get_database_statistics()
            prov = f"LOCAL ({os.getenv('LOCAL_MODEL_NAME','local')})" if USE_LOCAL_MODEL else "CLOUD (Gemini+DeepSeek)"
            vr = ""
            try:
                from core.hardware import detect_vram_gb
                v = detect_vram_gb()
                if v: vr = f" | VRAM: {v:.0f}GB"
            except: pass
            header = f"TALOS v5.3.0 | Profile: [{ap}] | {s['total_papers']} papers | {s['elite_papers']} elite | {prov}{vr}"
        except: pass

        choice = safe_select(header, choices=[
            questionary.Separator("  SEARCH & DISCOVERY"),
            "1. Daily Search (14 APIs)",
            "2. Historical Search (Deep Archive)",
            "3. Grey Literature / Web Horizon Scan",
            questionary.Separator("  AI-POWERED SEARCH (DRL)"),
            "4. Live DRL Agent (Real API Orchestration)",
            "5. Autonomous Research Process (24/7)",
            questionary.Separator("  ANALYSIS & INSIGHTS"),
            "6. Knowledge Path Generator (CHIRON)",
            "7. Citation Network Analyzer (ORPHEUS)",
            "8. Strategic Reading Report",
            "9. Author Analysis Tools",
            "10. Interactive Dashboard",
            "11. DRL Training (API Orchestrator)",
            "12. Compare Baselines (Pre/Post DRL)",
            questionary.Separator("  DATABASE & SETTINGS"),
            "13. Database & Data",
            "14. System Diagnostics",
            "15. Profile & Settings",
            questionary.Separator(), "Exit"
        ])
        if choice is None or choice == "Exit": break
        fm = "Press Enter to return..."

        if choice.startswith("1."): run_script("daily_search.py", python_exe)
        elif choice.startswith("2."):
            if questionary.confirm("This may take a long time. Sure?", default=False).ask():
                run_script("historic_search.py", python_exe)
        elif choice.startswith("3."): run_script("grey_literature_miner.py", python_exe)
        elif choice.startswith("4."):
            print("\n" + "=" * 65)
            print("  Live DRL Agent — Real API Orchestration")
            print("=" * 65)
            print("\n  The trained DRL agent selects the optimal API source in real-time.")
            if questionary.confirm("Start live agent? (Ctrl+C to stop)", default=True).ask():
                run_script("talos_live_agent.py", python_exe, args=["--verbose"])
        elif choice.startswith("5."):
            print("\n" + "=" * 65)
            print("  Autonomous Research Process — 24/7 + DRL")
            print("=" * 65)
            print("\n  Runs INDEFINITELY. Uses DRL agent to discover papers around the clock.")
            if questionary.confirm("Start autonomous process? (Ctrl+C to stop)", default=True).ask():
                run_script("talos_service.py", python_exe)
        elif choice.startswith("6."): run_script("knowledge_path_generator.py", python_exe)
        elif choice.startswith("7."): run_script("citation_analyzer.py", python_exe)
        elif choice.startswith("8."): run_script("recommender.py", python_exe)
        elif choice.startswith("9."): author_tools_menu(python_exe)
        elif choice.startswith("10."):
            run_script("interactive_dashboard.py", python_exe)
            fm = "Dashboard terminated. Press Enter..."
        elif choice.startswith("11."): run_script("drl_trainer.py", python_exe)
        elif choice.startswith("12."):
            print("\nCompare Baselines — Pre/Post DRL")
            if questionary.confirm("Generate new baseline and compare?", default=True).ask():
                run_script("generate_baseline_report.py", python_exe, args=["--academic"])
                rb = os.path.join(project_root, "reports", "general_status_report")
                if os.path.exists(rb):
                    folders = sorted([d for d in os.listdir(rb) if os.path.isdir(os.path.join(rb, d))], reverse=True)
                    if len(folders) >= 2:
                        print(f"\n  Latest:   {folders[0]}")
                        print(f"  Previous: {folders[1]}")
        elif choice.startswith("13."): database_data_menu(python_exe)
        elif choice.startswith("14."): system_health_menu(python_exe)
        elif choice.startswith("15."): profile_settings_menu(python_exe)
        if choice != "Exit": input(fm)
    print("\nTalos Command Center Closing...\n")

if __name__ == "__main__":
    try: main_menu()
    except KeyboardInterrupt: print("\n\nTalos Closing...\n")