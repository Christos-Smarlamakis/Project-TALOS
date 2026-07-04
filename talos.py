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
Module: talos.py (v4.11.0 - The Project Map & Diagnostics Update)
Project: TALOS v4.11.0

Description:
    The central entry point and interactive CLI for Project TALOS.
    Provides a hierarchical menu system for all research operations:

    - Onboarding Wizard for first-time users (auto-creates config.json + launches PYTHIA)
    - Search & Discovery (daily search, historical deep archive, grey literature mining)
    - Analysis & Insights (knowledge paths, citation networks, reading reports, author tools)
    - Database Maintenance (stats, enrichment, embeddings, re-evaluation, scientometrics)
    - Profile Management (switch/create/configure research profiles)

    All subprocesses are launched via :func:`run_script` with consistent
    environment variable propagation for provider and fallback settings.
"""
import questionary
import os
import subprocess
import sys
import time
import tempfile
import stat
from dotenv import load_dotenv
load_dotenv()  # Load HF_TOKEN and other env vars before first use

import shutil

# Add scripts directory to path for profile_manager imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'scripts')))
from scripts.profile_manager import (
    get_active_profile_name,
    save_current_state_to_profile,
    set_active_profile_name,
)

USE_LOCAL_MODEL = False


def safe_select(message, choices):
    """Display a questionary select prompt with a fallback for limited terminals.

    Args:
        message (str): The prompt message to display.
        choices (list): List of choice strings or questionary.Choice objects.

    Returns:
        str or None: The selected choice value, or None if cancelled.
    """
    try:
        return questionary.select(message, choices=choices, use_indicator=True, pointer="»").ask()
    except Exception:
        print("\nWARNING: Advanced terminal UI failed. Falling back to simple mode.")
        return questionary.select(message, choices=choices).unsafe_ask()


def run_script(script_name: str, python_exe: str, args: list = None, capture: bool = False):
    """Launch a TALOS script as a subprocess with consistent environment configuration.

    Propagates all provider and fallback environment variables to child processes.
    Handles dashboard termination gracefully (non-zero exit codes are expected).

    Args:
        script_name (str): Name of the script file in the 'scripts/' directory.
        python_exe (str): Path to the Python executable to use.
        args (list, optional): Additional command-line arguments for the script.
        capture (bool): If True, capture and return stdout from the subprocess.

    Returns:
        subprocess.CompletedProcess or bool or None:
            - CompletedProcess if capture=True
            - True if script completed successfully
            - None if script failed
    """
    project_root = os.path.dirname(os.path.abspath(__file__))
    script_path = os.path.join(project_root, 'scripts', script_name)
    command = [python_exe, script_path] + (args or [])

    print(f"\n--- Launching '{script_name}'... ---\n")
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"

    if USE_LOCAL_MODEL:
        env["TALOS_USE_LOCAL"] = "1"
    if os.environ.get("TALOS_MODELS_VERIFIED"):
        env["TALOS_MODELS_VERIFIED"] = "1"
    if os.environ.get("TALOS_ALLOW_CLOUD_FALLBACK"):
        env["TALOS_ALLOW_CLOUD_FALLBACK"] = "1"
    if os.environ.get("TALOS_ALLOW_LOCAL_FALLBACK"):
        env["TALOS_ALLOW_LOCAL_FALLBACK"] = "1"
    if os.environ.get("HF_MODEL_NAME"):
        env["HF_MODEL_NAME"] = os.environ["HF_MODEL_NAME"]

    try:
        if capture:
            result = subprocess.run(command, check=True, capture_output=True, text=True, encoding="utf-8", env=env)
            print(result.stdout)
            print(f"\n--- '{script_name}' completed. ---")
            return result
        else:
            try:
                subprocess.run(command, check=True, env=env)
                print(f"\n--- '{script_name}' completed. ---")
                return True
            except subprocess.CalledProcessError as e:
                # Dashboard uses signal-based shutdown - non-zero exit is normal
                if "interactive_dashboard.py" in script_name and e.returncode in [1, 2, -2, 3221225786]:
                    print(f"\n--- Dashboard server terminated by user. ---")
                    return True
                else:
                    raise e

    except KeyboardInterrupt:
        print(f"\n\n--- '{script_name}' cancelled by user. Returning to menu... ---")
        return False
    except (subprocess.CalledProcessError, FileNotFoundError, Exception) as e:
        print(f"\n--- Error running '{script_name}': {e} ---")
        return None


def check_first_run(python_exe):
    """Detect first-time usage and run the Onboarding Wizard.

    If config.json is missing, copies the template and optionally launches
    PYTHIA (query_translator.py) to configure the initial research profile.

    Args:
        python_exe (str): Path to the Python executable.
    """
    config_path = "config.json"
    template_path = "config.template.json"

    if not os.path.exists(config_path):
        print("\nWelcome to Project TALOS!")
        print("   It appears this is your first time running the system.")
        print("   I will create an initial profile for you.\n")

        if os.path.exists(template_path):
            shutil.copy(template_path, config_path)
            print("Created 'config.json' from the template.")
        else:
            print("ERROR: 'config.template.json' not found.")
            return

        if not os.path.exists("_profiles"):
            os.makedirs("_profiles")

        print("\nLet's configure your research goal with AI assistance (Project PYTHIA).")
        if questionary.confirm("Start configuration now?", default=True).ask():
            run_script("query_translator.py", python_exe)

            print("\nSaving new profile as 'default'...")
            set_active_profile_name("default")
            save_current_state_to_profile("default")

        print("\n--- Initial setup complete! ---\n")
        time.sleep(2)


# --- SUB-MENUS ---

def author_tools_menu(python_exe: str):
    """Sub-menu for author analysis tools (Profiler, Trajectory, Full Report).

    Args:
        python_exe (str): Path to the Python executable.
    """
    os.system('cls' if os.name == 'nt' else 'clear')
    choice = safe_select(
        "Author Analysis Tools:",
        choices=[
            "1. Quick Profile (Profiler)",
            "2. Trajectory Analysis",
            "3. Full Report (Profiler -> Trajectory)",
            questionary.Separator(),
            "Back to Main Menu"
        ]
    )
    if choice is None or choice.startswith("Back"): return

    if choice.startswith("1."):
        author_identifier = questionary.text("Enter author name or ORCID iD:").ask()
        if author_identifier: run_script("author_profiler.py", python_exe, args=[author_identifier.strip()])

    elif choice.startswith("2."):
        author_identifier = questionary.text("Enter author name or ORCID iD:").ask()
        if author_identifier: run_script("author_trajectory_analyzer.py", python_exe, args=[author_identifier.strip()])

    elif choice.startswith("3."):
        author_name = questionary.text("Enter author name:").ask()
        if author_name:
            print("\n--- [STEP 1/2] Identifying researcher... ---")
            profiler_result = run_script("author_profiler.py", python_exe, args=author_name.strip().split(), capture=True)
            if profiler_result and profiler_result.stdout:
                selected_id = next((line.split(":", 1)[1].strip() for line in profiler_result.stdout.splitlines() if line.startswith("SELECTED_ORCID_ID:")), None)
                if selected_id:
                    print(f"\n--- [STEP 2/2] Launching Trajectory Analyzer... ---")
                    run_script("author_trajectory_analyzer.py", python_exe, args=[selected_id])
                else:
                    print("\n--- No ORCID iD selected. Aborting. ---")


def database_data_menu(python_exe: str):
    """Sub-menu for database operations and data management.

    Args:
        python_exe (str): Path to the Python executable.
    """
    os.system('cls' if os.name == 'nt' else 'clear')

    project_root = os.path.dirname(os.path.abspath(__file__))
    active_profile = get_active_profile_name()
    profile_db_path = os.path.join(project_root, '_profiles', active_profile, 'talos_research.db')
    root_db_path = os.path.join(project_root, 'talos_research.db')
    target_db = profile_db_path if os.path.exists(profile_db_path) else root_db_path

    choice = safe_select(
        "Database & Data:",
        choices=[
            "1. Statistics & Health (Metrics)",
            "2. Metadata Enrichment (APOLLO)",
            "3. Zotero Sync",
            "4. Generate/Update Embeddings (Semantic Brain)",
            "5. AI Re-evaluation (Smart Recalibration)",
            "6. Data Enrichment (Unpaywall/IDs)",
            "7. Scientometrics Report",
            "8. PDF Downloader (Open Access)",
            questionary.Separator(),
            "Back to Main Menu"
        ]
    )
    if choice is None or choice.startswith("Back"): return

    if choice.startswith("1."): run_script("db_stats.py", python_exe)
    elif choice.startswith("2."): run_script("metadata_enricher.py", python_exe)
    elif choice.startswith("3."): run_script("zotero_connector.py", python_exe)
    elif choice.startswith("4."): run_script("embedding_generator.py", python_exe)
    elif choice.startswith("5."): run_script("reevaluate_database.py", python_exe)
    elif choice.startswith("6."): run_script("data_enricher.py", python_exe)
    elif choice.startswith("7."): run_script("trend_analyzer.py", python_exe, args=[target_db])
    elif choice.startswith("8."): run_script("pdf_downloader.py", python_exe)


def system_health_menu(python_exe: str):
    """Sub-menu for system health checks and project audits.

    Args:
        python_exe (str): Path to the Python executable.
    """
    os.system('cls' if os.name == 'nt' else 'clear')

    project_root = os.path.dirname(os.path.abspath(__file__))

    choice = safe_select(
        "System Diagnostics:",
        choices=[
            "1. Code Integrity Check",
            "2. Documentation Audit (Map vs Code)",
            "3. Open Architecture Graph",
            "4. Architecture Intelligence Report (AI Analysis)",
            questionary.Separator(),
            "5. Generate Baseline Report (Standard)",
            "6. Generate Baseline Report (Academic — 600 DPI)",
            "7. DRL Agent Status (Training Health)",
            questionary.Separator(),
            "Back to Main Menu"
        ]
    )
    if choice is None or choice.startswith("Back"): return

    if choice.startswith("1."):
        print("\nSystem Health Check...\n")
        test_path = os.path.join(project_root, 'test_smoke.py')
        if os.path.exists(test_path):
            result = subprocess.run([python_exe, test_path], check=False, env=os.environ.copy())
            if result.returncode == 0:
                print("\nAll checks passed — Project is healthy!")
            else:
                print(f"\nHealth check completed with code {result.returncode}.")
        else:
            print("test_smoke.py not found.")
    elif choice.startswith("2."):
        print("\nRunning Dependency Map Audit...\n")
        print("Compares documented dependencies and functions (PROJECT_MAP.md)")
        print("against actual Python source code.\n")
        run_script("verify_dependency_map.py", python_exe, args=["--all"])
        print("\nReports saved:")
        print("  reports/audits/dependency_audit.html")
        print("  reports/audits/dependency_audit.md")
        print("  reports/audits/dependency_audit.json")
    elif choice.startswith("3."):
        import webbrowser
        import socket
        # Start local HTTP server if needed (allows CDN scripts like cytoscape-svg to load)
        port = 8765
        server_running = False
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.5)
            server_running = sock.connect_ex(('127.0.0.1', port)) == 0
            sock.close()
        except Exception:
            pass
        
        if not server_running:
            print(f"\nStarting local HTTP server on port {port}...")
            server_dir = os.path.join(project_root, "templates")
            subprocess.Popen(
                [python_exe, "-m", "http.server", str(port), "--bind", "127.0.0.1", "--directory", server_dir],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
            print("Server started.")
        
        audit_json = os.path.join(project_root, "reports", "audits", "dependency_audit.json")
        url = f"http://localhost:{port}/architecture_graph.html"
        if os.path.exists(audit_json):
            url += "?audit=../reports/audits/dependency_audit.json"
        print(f"\nOpening {url}")
        webbrowser.open(url)
        print("Graph opened in your default browser.")

    elif choice.startswith("4."):
        print("\nGenerating Architecture Intelligence Report...\n")
        print("This will analyze PROJECT_MAP.md, the dependency audit,")
        print("and the architecture graph to produce a comprehensive")
        print("intelligence report in English and Greek.\n")
        print("⚠️  Requires a working AI provider (Gemini Pro or DeepSeek).")
        if not questionary.confirm("Start now? (may take up to 60 seconds)", default=True).ask():
            return
        run_script("architecture_intelligence_report.py", python_exe)
        print("\nReports saved:")
        print("  reports/architecture_intelligence_report_en.md")
        print("  reports/architecture_intelligence_report_gr.md")
    elif choice.startswith("5."):
        run_script("generate_baseline_report.py", python_exe)
    elif choice.startswith("6."):
        run_script("generate_baseline_report.py", python_exe, args=["--academic"])
    elif choice.startswith("7."):
        models_dir = os.path.join(project_root, "models")
        model_path = os.path.join(models_dir, "dddqn_trained.pth")
        gwo_path = os.path.join(models_dir, "gwo_best_params.json")
        # Try rich formatting, fall back to plain text
        try:
            from rich.console import Console
            from rich.table import Table
            from rich.panel import Panel
            from rich.text import Text
            console = Console()
            console.print()
            table = Table(show_header=False, box=None, padding=(0, 2))
            table.add_column("Key", style="bold cyan", no_wrap=True)
            table.add_column("Value", style="white")
            # ── Check trained model ──
            if os.path.exists(model_path):
                size_kb = os.path.getsize(model_path) / 1024
                table.add_row("Trained Model", f"[green]✅ Present[/green] ({size_kb:.1f} KB)")
            else:
                table.add_row("Trained Model", "[red]❌ Not found[/red] — run DRL Training first")
            table.add_section()
            # ── Check GWO params ──
            if os.path.exists(gwo_path):
                import json
                with open(gwo_path, "r") as f:
                    params = json.load(f)
                table.add_row("GWO Params", "[green]✅ Present[/green]")
                table.add_row("Learning Rate", f"[bold yellow]{params['learning_rate']:.6e}[/bold yellow]")
                table.add_row("Gamma", f"[bold yellow]{params['gamma']:.4f}[/bold yellow]")
                table.add_row("Epsilon Decay", f"[bold yellow]{params['epsilon_decay']:.6f}[/bold yellow]")
                table.add_row("Best Fitness", f"[bold magenta]{params['best_fitness']:.1f}[/bold magenta]")
                table.add_row("Best Avg Reward", f"[bold green]{params['best_avg_reward']:.1f}[/bold green]")
                table.add_row("Iterations", str(params['iterations']))
                table.add_row("Time", f"{params['gwo_time_seconds']}s")
            else:
                table.add_row("GWO Params", "[red]❌ Not found[/red] — run GWO optimizer first")
            console.print(Panel(table, title="[bold]🧠 DRL Agent Status[/bold]", border_style="cyan", padding=(1, 2)))
        except ImportError:
            # Fallback: plain text output
            print("\n" + "=" * 50)
            print("  DRL Agent Status")
            print("=" * 50)
            if os.path.exists(model_path):
                size_kb = os.path.getsize(model_path) / 1024
                print(f"  ✅ Trained model:  {model_path} ({size_kb:.1f} KB)")
            else:
                print(f"  ❌ No trained model found (run DRL Training first)")
            if os.path.exists(gwo_path):
                import json
                with open(gwo_path, "r") as f:
                    params = json.load(f)
                print(f"  ✅ GWO Best Params: {gwo_path}")
                print(f"     LR={params['learning_rate']:.6e}  GAMMA={params['gamma']:.4f}  EPS_DECAY={params['epsilon_decay']:.6f}")
                print(f"     Best fitness={params['best_fitness']:.1f}  Reward={params['best_avg_reward']:.1f}")
                print(f"     Iterations={params['iterations']}  Time={params['gwo_time_seconds']}s")
            else:
                print(f"  ❌ No GWO params found (run GWO optimizer first)")
        print("=" * 50)

    print()
    input("Press Enter to continue...")


def api_keys_menu(python_exe: str):
    """Sub-menu for viewing and editing API keys in the .env file.

    Displays all configured keys with masked values and [SET]/[NOT SET] status.
    Allows interactive editing of individual keys using dotenv.

    Args:
        python_exe (str): Path to the Python executable.
    """
    from dotenv import set_key as _set_key, dotenv_values

    project_root = os.path.dirname(os.path.abspath(__file__))
    env_path = os.path.join(project_root, '.env')

    # Ensure .env exists
    if not os.path.exists(env_path):
        example_path = os.path.join(project_root, 'example.env')
        if os.path.exists(example_path):
            import shutil
            shutil.copy(example_path, env_path)
        else:
            open(env_path, 'w').close()

    # Define all known keys with categories
    ALL_KEYS = [
        ("Contact", [("MAILTO", "Contact Email (for polite API pools)")]),
        ("Premium AI", [
            ("GEMINI_API_KEY", "Google Gemini API Key"),
            ("DEEPSEEK_API_KEY", "DeepSeek API Key"),
            ("HF_TOKEN", "Hugging Face Token"),
        ]),
        ("Academic APIs", [
            ("SEMANTIC_SCHOLAR_API_KEY", "Semantic Scholar API Key"),
            ("SEMANTIC_SCHOLAR_API_KEY_basic", "Semantic Scholar Basic Key"),
            ("IEEE_API_KEY", "IEEE Xplore API Key"),
            ("ELSEVIER_API_KEY", "Elsevier Scopus API Key"),
            ("ELSEVIER_INST_TOKEN", "Elsevier Institutional Token"),
            ("SPRINGER_API_KEY", "Springer Nature API Key"),
            ("CORE_API_KEY", "CORE API Key"),
            ("OPENARCHIVES_API_KEY", "OpenArchives.gr API Key"),
        ]),
        ("Integrations", [
            ("DISCORD_WEBHOOK_URL", "Discord Webhook URL"),
            ("ZOTERO_USER_ID", "Zotero User ID"),
            ("ZOTERO_API_KEY", "Zotero API Key"),
            ("ORCID_CLIENT_ID", "ORCID Client ID"),
            ("ORCID_CLIENT_SECRET", "ORCID Client Secret"),
        ]),
        ("Local Models", [
            ("LOCAL_MODEL_NAME", "Ollama Chat Model"),
            ("LOCAL_EMBEDDING_MODEL", "Ollama Embedding Model"),
        ]),
    ]

    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        print("\n" + "=" * 62)
        print("  API Keys Management")
        print("=" * 62)

        values = dotenv_values(env_path)

        for category, keys in ALL_KEYS:
            print(f"\n  [{category}]")
            for key, desc in keys:
                val = values.get(key, "")
                status = "[SET]" if val.strip() else "[NOT SET]"
                masked = val[:4] + "****" if len(val) > 4 else val
                print(f"    {key:<28} | {status:<8} | {desc}")

        print("\n" + "-" * 62)
        print("  [1] Edit a key")
        print("  [2] Run API Diagnostics")
        print("  [3] Back")

        choice = safe_select(
            "Select action:",
            choices=["1. Edit a key", "2. Run API Diagnostics", "3. Back"]
        )
        if choice is None or choice.startswith("3"):
            return

        if choice.startswith("1"):
            # Build a flat list of choices
            flat = []
            for cat, keys in ALL_KEYS:
                flat.append(f"--- {cat} ---")
                for key, desc in keys:
                    val = values.get(key, "")
                    status = "[SET]" if val.strip() else "[NOT SET]"
                    flat.append(f"{key}  {status}")
            flat.append("Cancel")

            selected = safe_select("Select key to edit:", choices=flat)
            if selected and not selected.startswith("---") and selected != "Cancel":
                key_to_edit = selected.split()[0]
                current_val = values.get(key_to_edit, "")
                print(f"\nEditing: {key_to_edit}")
                print(f"Current value: {current_val[:4] + '****' if len(current_val) > 4 else current_val}")
                new_val = questionary.text("New value (leave empty to clear):", default=current_val).ask()
                if new_val is not None:
                    # Update using dotenv
                    vals = dotenv_values(env_path)
                    vals[key_to_edit] = new_val.strip()
                    # Rewrite the env file
                    env_lines = []
                    read_vals = dotenv_values(env_path)
                    read_vals[key_to_edit] = new_val.strip()
                    # Read original file to preserve comments
                    if os.path.exists(env_path):
                        with open(env_path, 'r', encoding='utf-8') as f:
                            original_lines = f.readlines()
                    else:
                        original_lines = []
                    # Check if key already exists in file
                    found = False
                    new_lines = []
                    for line in original_lines:
                        if line.strip().startswith(key_to_edit + " ") or line.strip().startswith(key_to_edit + "="):
                            new_lines.append(f"{key_to_edit} = \"{new_val.strip()}\"\n")
                            found = True
                        else:
                            new_lines.append(line)
                    if not found:
                        new_lines.append(f"\n{key_to_edit} = \"{new_val.strip()}\"\n")
                    written = False
                    for attempt in range(3):
                        try:
                            # Attempt 1 & 3: direct write
                            # Attempt 2: chmod to add write permission first
                            if attempt == 1:
                                try:
                                    os.chmod(env_path, os.stat(env_path).st_mode | stat.S_IWRITE)
                                except Exception:
                                    pass
                            with open(env_path, 'w', encoding='utf-8') as f:
                                f.writelines(new_lines)
                            written = True
                            break
                        except PermissionError:
                            if attempt == 2:
                                # Last resort: write to temp file and atomically replace
                                try:
                                    tmp_fd, tmp_path = tempfile.mkstemp(
                                        dir=os.path.dirname(env_path),
                                        prefix='.env_tmp_',
                                        text=True
                                    )
                                    with os.fdopen(tmp_fd, 'w', encoding='utf-8') as tmp_f:
                                        tmp_f.writelines(new_lines)
                                    os.replace(tmp_path, env_path)
                                    written = True
                                    break
                                except Exception:
                                    if os.path.exists(tmp_path):
                                        try:
                                            os.unlink(tmp_path)
                                        except Exception:
                                            pass
                    if not written:
                        print(f"\n  [ERROR] Could not write to {env_path} (Permission denied).")
                        print(f"  Your changes were NOT saved. Please check file permissions.")
                        print(f"  Try: right-click the .env file -> Properties -> uncheck 'Read-only'.")
                    else:
                        os.environ[key_to_edit] = new_val.strip()
                        print(f"\n  [{key_to_edit}] updated.")

        elif choice.startswith("2"):
            print("\nRunning API Diagnostics...\n")
            test_path = os.path.join(project_root, 'scripts', 'api_health_check.py')
            if os.path.exists(test_path):
                result = subprocess.run([python_exe, test_path], check=False, env=os.environ.copy())
                if result.returncode == 0:
                    print("\n  All checks passed.")
                else:
                    print(f"\n  Health check completed with code {result.returncode}.")
            else:
                print("  api_health_check.py not found.")
        
        input("\nPress Enter to continue...")


def profile_settings_menu(python_exe: str):
    """Sub-menu for profile management and research goal configuration.

    Args:
        python_exe (str): Path to the Python executable.
    """
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        choice = safe_select(
            "Profile & Settings:",
            choices=[
                "1. Manage Profiles (Switch/Create)",
                "2. Configure Research Goal (PYTHIA)",
                "3. AI Model Management (Local & Cloud)",
                "4. API Keys Management",
                "5. API Diagnostics",
                questionary.Separator(),
                "Back to Main Menu"
            ]
        )
        if choice is None or choice.startswith("Back"):
            return
        if choice.startswith("1"):
            run_script("profile_manager.py", python_exe)
        elif choice.startswith("2"):
            run_script("query_translator.py", python_exe)
        elif choice.startswith("3"):
            run_script("model_manager.py", python_exe)
        elif choice.startswith("4"):
            api_keys_menu(python_exe)
        elif choice.startswith("5"):
            print("\nRunning API Diagnostics...\n")
            project_root = os.path.dirname(os.path.abspath(__file__))
            test_path = os.path.join(project_root, 'scripts', 'api_health_check.py')
            if os.path.exists(test_path):
                result = subprocess.run([python_exe, test_path], check=False, env=os.environ.copy())
                if result.returncode == 0:
                    print("\n  All checks passed.")
                else:
                    print(f"\n  Completed with code {result.returncode}.")
            else:
                print("  api_health_check.py not found.")
            input("\nPress Enter to continue...")


def _verify_local_models():
    """Verify and auto-install required local models for Ollama.

    Checks that gemma3:12b and nomic-embed-text are available.
    Missing models are pulled automatically via 'ollama pull'.
    Sets TALOS_MODELS_VERIFIED=1 on success.
    """
    import requests
    print("\n[Verifying local models...]")
    base = "http://localhost:11434"
    try:
        resp = requests.get(f"{base}/api/tags", timeout=5)
        if resp.status_code != 200:
            print("WARNING: Ollama not reachable.")
            return
        models = [m['name'] for m in resp.json().get('models', [])]
        for model in ["gemma3:12b", "nomic-embed-text"]:
            if model not in models:
                print(f"  >> Pulling {model}...")
                subprocess.run(["ollama", "pull", model], check=True)
            else:
                print(f"  >> {model} already installed.")
        os.environ["TALOS_MODELS_VERIFIED"] = "1"
        print("[All local models ready.]")
    except Exception as e:
        print(f"WARNING: Model verification failed: {e}")


# --- MAIN MENU ---

def main_menu():
    """Display the main interactive menu and dispatch to sub-menus and scripts.

    Handles first-run onboarding, AI provider selection, and the main
    event loop with hierarchical sub-menus for all TALOS operations.
    """
    python_exe = sys.executable or "python"
    project_root = os.path.dirname(os.path.abspath(__file__))
    print(f"INFO: Using Python from: {python_exe}")

    check_first_run(python_exe)

    time.sleep(1)

    # --- AI Provider Selection ---
    global USE_LOCAL_MODEL
    if not USE_LOCAL_MODEL:
        choice = safe_select(
            "Where to run AI calls?",
            choices=[
                "LOCAL  (Ollama / Gemma 3 12B)",
                "CLOUD  (Gemini + DeepSeek)"
            ]
        )
        USE_LOCAL_MODEL = (choice and "LOCAL" in choice)
        if USE_LOCAL_MODEL:
            print("Local mode enabled.")
            _verify_local_models()

            fallback = safe_select("Allow cloud fallback if local fails?",
                choices=["NO - Keep data offline", "YES - Allow cloud as backup"])
            if fallback and "YES" in fallback:
                os.environ["TALOS_ALLOW_CLOUD_FALLBACK"] = "1"
                print("Cloud fallback ALLOWED.")
            else:
                print("Cloud fallback BLOCKED.")
        else:
            fallback = safe_select("Allow local fallback if cloud fails?",
                choices=["NO - Cloud only", "YES - Allow local as backup"])
            if fallback and "YES" in fallback:
                os.environ["TALOS_ALLOW_LOCAL_FALLBACK"] = "1"
                print("Local fallback ALLOWED.")
            if os.getenv("HF_TOKEN"):
                hf_models = [
                    "mistralai/Mixtral-8x7B-Instruct-v0.1",
                    "meta-llama/Llama-3.1-8B-Instruct",
                    "Qwen/Qwen2.5-7B-Instruct",
                    "mistralai/Mistral-7B-Instruct-v0.3",
                    "microsoft/Phi-3-mini-4k-instruct",
                    "google/gemma-2-2b-it"
                ]
                m = safe_select("Select HF model (free):", choices=hf_models)
                if m: os.environ["HF_MODEL_NAME"] = m

    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        active_profile = get_active_profile_name()

        # --- Build dynamic header with DB stats ---
        header = f"TALOS v4.11.0 | Profile: [{active_profile}]"
        try:
            from core.database_manager import DatabaseManager
            db = DatabaseManager()
            stats = db.get_database_statistics()
            if USE_LOCAL_MODEL:
                local_model = os.getenv("LOCAL_MODEL_NAME", "local")
                provider = f"LOCAL ({local_model})"
            else:
                provider = "CLOUD (Gemini+DeepSeek)"
            vram_str = ""
            try:
                from core.hardware import detect_vram_gb
                vram = detect_vram_gb()
                if vram:
                    vram_str = f" | VRAM: {vram:.0f}GB"
            except Exception:
                pass
            header = f"TALOS v4.11.0 | Profile: [{active_profile}] | {stats['total_papers']} papers | {stats['elite_papers']} elite | {provider}{vram_str}"
        except Exception:
            pass

        choice = safe_select(
            header,
            choices=[
                questionary.Separator("  SEARCH & DISCOVERY"),
                "1. Daily Search (New Papers)",
                "2. Historical Search (Deep Archive)",
                "3. Grey Literature / Web Horizon Scan",
                questionary.Separator("  ANALYSIS & INSIGHTS"),
                "4. Knowledge Path Generator (CHIRON)",
                "5. Citation Network Analyzer (ORPHEUS)",
                "6. Strategic Reading Report",
            "7. Author Analysis Tools",
            "8. Interactive Dashboard",
            "9. DRL Training (API Orchestrator)",
            "10. Compare Baselines (Pre/Post DRL)",
            questionary.Separator("  DATABASE & SETTINGS"),
            "11. Database & Data",
            "12. System Diagnostics",
            "13. Profile & Settings",
                questionary.Separator(),
                "Exit"
            ]
        )

        if choice is None or choice == "Exit": break

        final_message = "Press Enter to return to the menu..."

        if choice.startswith("1."): run_script("daily_search.py", python_exe)
        elif choice.startswith("2."):
            if questionary.confirm("This process may take a long time. Are you sure?", default=False).ask():
                run_script("historic_search.py", python_exe)
        elif choice.startswith("3."): run_script("grey_literature_miner.py", python_exe)
        elif choice.startswith("4."): run_script("knowledge_path_generator.py", python_exe)
        elif choice.startswith("5."): run_script("citation_analyzer.py", python_exe)
        elif choice.startswith("6."): run_script("recommender.py", python_exe)
        elif choice.startswith("7."): author_tools_menu(python_exe)
        elif choice.startswith("8."):
            run_script("interactive_dashboard.py", python_exe)
            final_message = "Dashboard server terminated. Press Enter to return to the menu..."
        elif choice.startswith("9."): run_script("drl_trainer.py", python_exe)
        elif choice.startswith("10."):
            print("\n" + "=" * 65)
            print("  Compare Baselines — Pre/Post DRL Agent")
            print("=" * 65)
            print("\n  This will generate a NEW baseline report and compare")
            print("  it against the previous one (if it exists).")
            print("\n  Reports are read from: reports/general_status_report/")
            print()
            if questionary.confirm("Generate new baseline and compare?", default=True).ask():
                # Run a fresh baseline report
                run_script("generate_baseline_report.py", python_exe, args=["--academic"])
                # Try to find two most recent report folders
                report_base = os.path.join(project_root, "reports", "general_status_report")
                if os.path.exists(report_base):
                    folders = sorted([d for d in os.listdir(report_base) if os.path.isdir(os.path.join(report_base, d))], reverse=True)
                    if len(folders) >= 2:
                        latest = folders[0]
                        previous = folders[1]
                        print(f"\n  📊 Latest report:   reports/general_status_report/{latest}/")
                        print(f"  📊 Previous report: reports/general_status_report/{previous}/")
                        # Try to read metrics from both reports
                        import json as _json
                        def _read_metrics(folder_name):
                            rpt_path = os.path.join(report_base, folder_name, "report.md")
                            if not os.path.exists(rpt_path): return None
                            with open(rpt_path, "r", encoding="utf-8") as f:
                                text = f.read()
                            import re
                            total = re.search(r"Total Papers\s*\|\s*([\d,]+)", text)
                            elite = re.search(r"Elite Papers.*\|\s*([\d,]+)", text)
                            avg   = re.search(r"Average Score\s*\|\s*([\d.]+)", text)
                            return {
                                "total": int(total.group(1).replace(",","")) if total else 0,
                                "elite": int(elite.group(1).replace(",","")) if elite else 0,
                                "avg": float(avg.group(1)) if avg else 0.0,
                            }
                        m1 = _read_metrics(latest)
                        m2 = _read_metrics(previous)
                        if m1 and m2:
                            print("\n  📈 Comparison:")
                            print(f"    Total Papers:  {m2['total']:,} → {m1['total']:,}  (Δ = {m1['total']-m2['total']:+,})")
                            print(f"    Elite Papers:  {m2['elite']:,} → {m1['elite']:,}  (Δ = {m1['elite']-m2['elite']:+,})")
                            print(f"    Avg Score:     {m2['avg']:.2f} → {m1['avg']:.2f}  (Δ = {m1['avg']-m2['avg']:+.2f})")
                        else:
                            print("\n  ⚠️  Could not read metrics from both reports.")
                    else:
                        print(f"\n  ⚠️  Only {len(folders)} report(s) found. Need 2 for comparison.")
                        print(f"  Run a baseline report first, then deploy the DRL agent and run again.")
                else:
                    print(f"\n  ⚠️  No baseline reports found.")
                    print(f"  Use 'Generate Baseline Report' from System Diagnostics first.")
            print("=" * 65)
        elif choice.startswith("11."):
            print("\n" + "=" * 65)
            print("  Live DRL Agent — Real API Orchestration")
            print("=" * 65)
            print("\n  ⚠️  This makes REAL API calls to ArXiv, OpenAlex, and Semantic Scholar.")
            print("  The trained DRL agent selects the optimal source in real-time.")
            if questionary.confirm("Start live agent? (runs until Ctrl+C)", default=True).ask():
                run_script("talos_live_agent.py", python_exe, args=["--verbose"])
        elif choice.startswith("12."): database_data_menu(python_exe)
        elif choice.startswith("13."): system_health_menu(python_exe)
        elif choice.startswith("14."): profile_settings_menu(python_exe)

        if choice != "Exit": input(final_message)

    print("\nTalos Command Center Closing...\nBye Bye...\n")


if __name__ == "__main__":
    try:
        main_menu()
    except KeyboardInterrupt:
        print("\n\nTalos Command Center Closing...\nBye Bye...")