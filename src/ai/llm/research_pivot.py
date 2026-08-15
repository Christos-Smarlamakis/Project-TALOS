# -*- coding: utf-8 -*-
"""
Module: research_pivot.py (v1.0)
Project: TALOS v5.10.0
Description:
    Interactive Research Pivot Wizard for TALOS.  Guides the user through
    recalibrating the system when their research interests have shifted.

    The wizard does the following (each step is optional after the first):
      Step 1: Collect the NEW research direction from the user.
      Step 2: Run PYTHIA to regenerate search queries and evaluation prompts.
      Step 3: Optionally re-evaluate the entire database with the new criteria.
      Step 4: Optionally retrain the DRL agent with the updated scores.
      Step 5: Save everything back into the active profile.

    Usage:
        python scripts/research_pivot.py
        python scripts/research_pivot.py --auto  (non-interactive, skips confirmation)
"""
import os
import sys
_P = os.path.abspath(os.path.dirname(__file__))
while _P and not os.path.exists(os.path.join(_P, 'talos.py')):
    _P = os.path.dirname(_P)
if _P: sys.path.insert(0, _P)
import json
import shutil
import subprocess
import questionary
from questionary import Style

TALOS_QUESTIONARY_STYLE = Style([
    ('qmark', 'fg:#006699 bold'),
    ('question', 'bold fg:#e4e7ee'),
    ('answer', 'fg:#4a9eff bold'),
    ('pointer', 'fg:#4a9eff bold'),
    ('highlighted', 'fg:#4a9eff bold noinherit'),
    ('selected', 'fg:#28a745 bold'),
    ('separator', 'fg:#6b7280'),
    ('instruction', 'fg:#6b7280 italic'),
    ('text', 'fg:#c9cdd4'),
    ('disabled', 'fg:#6b7280 italic')
])

# -- v5.9.17: Enterprise logging & Universal Rich TUI --
from src.utils.logger import get_logger
from rich.console import Console
from rich.panel import Panel

logger = get_logger(__name__)
console = Console()

# ── Add project root to Python's import path ────────────────────────────────
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
PROFILES_DIR = os.path.join(PROJECT_ROOT, '_profiles')
ACTIVE_PROFILE_FILE = os.path.join(PROFILES_DIR, 'active_profile.txt')


def get_active_profile_name():
    """Return the name of the currently active profile, or 'default'."""
    if os.path.exists(ACTIVE_PROFILE_FILE):
        with open(ACTIVE_PROFILE_FILE, 'r', encoding='utf-8') as f:
            return f.read().strip()
    return "default"


def save_state_to_profile(profile_name):
    """
    Save root config.json and talos_research.db into the profile directory.

    Args:
        profile_name (str): Name of the profile to save to.
    """
    profile_path = os.path.join(PROFILES_DIR, profile_name)
    os.makedirs(profile_path, exist_ok=True)

    for fname in ['config.json', 'talos_research.db']:
        src = os.path.join(PROJECT_ROOT, fname)
        if os.path.exists(src):
            shutil.copy2(src, os.path.join(profile_path, fname))


def run_script(script_name, stdin_text="", args=None):
    """
    Execute a TALOS script as a subprocess and return (returncode, output).

    Args:
        script_name (str): Script filename (e.g., 'query_translator.py').
        stdin_text (str): Text to pipe via TALOS_GUI_STDIN env var.
        args (list, optional): Extra command-line arguments.

    Returns:
        tuple: (returncode, stdout + stderr text)
    """
    python_exe = sys.executable
    script_path = os.path.join(PROJECT_ROOT, 'scripts', script_name)
    cmd = [python_exe, script_path] + (args or [])
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["TALOS_GUI_STDIN"] = stdin_text
    env["TALOS_GUI_STDIN_CONFIRM"] = "y"
    try:
        r = subprocess.run(
            cmd, capture_output=True, text=True, timeout=1800,
            env=env, encoding="utf-8", errors="replace"
        )
        return r.returncode, r.stdout + "\n" + r.stderr
    except subprocess.TimeoutExpired:
        return -1, "Timeout (30 min)."
    except Exception as e:
        return -1, str(e)


def main():
    """
    Run the Research Pivot Wizard.

    Guides the user step-by-step through recalibrating TALOS after a
    research focus shift.  Each step is confirmed before execution.
    """
    profile = get_active_profile_name()
    auto_mode = "--auto" in sys.argv or "--yes" in sys.argv

    # -- Rich header panel (emoji-free academic styling) --
    header = Panel(
        "[bold bright_cyan]TALOS Research Pivot Wizard[/bold bright_cyan]\n"
        f"[dim]Active Profile:[/dim] [cyan]{profile}[/cyan]\n"
        f"[dim]Mode:[/dim] {'[yellow]AUTO (non-interactive)[/yellow]' if auto_mode else '[green]INTERACTIVE[/green]'}\n"
        "[dim]This wizard recalibrates TALOS after a research focus shift.[/dim]",
        title="[bold]RESEARCH PIVOT[/bold]",
        border_style="bright_magenta",
    )
    console.print(header)

    # -- STEP 1: Collect new research direction --
    if auto_mode:
        # In auto mode, try to read from TALOS_GUI_STDIN env var
        new_direction = os.environ.get("TALOS_GUI_STDIN", "").strip()
        if not new_direction:
            logger.error("--auto mode requires TALOS_GUI_STDIN env var or piped input.")
            return
        logger.info("Research direction: %s...", new_direction[:80])
    else:
        new_direction = questionary.text(
            "Describe your NEW research direction (what has changed?):",
            validate=lambda t: True if len(t.strip()) > 20
            else "Please provide at least 20 characters.",
            style=TALOS_QUESTIONARY_STYLE,
        ).ask()

        if not new_direction:
            logger.warning("Pivot cancelled -- no research direction provided.")
            return

    # -- STEP 2: Run PYTHIA to regenerate queries and prompts --
    run_pythia = True
    if not auto_mode:
        run_pythia = questionary.confirm(
            "Step 2/4: Run PYTHIA to regenerate search queries and prompts?",
            default=True,
            style=TALOS_QUESTIONARY_STYLE,
        ).ask()

    if run_pythia:
        logger.info("Running PYTHIA with the new research direction...")
        rc, out = run_script("query_translator.py", stdin_text=new_direction + "\n")
        if rc == 0:
            logger.info("PYTHIA completed -- queries and prompts regenerated.")
            # Save immediately to the profile
            save_state_to_profile(profile)
            logger.info("Profile '%s' saved with new configuration.", profile)
        else:
            logger.warning("PYTHIA completed with code %s. Check output.", rc)
            if out.strip():
                # Show last 10 lines of output
                for line in out.strip().split("\n")[-10:]:
                    logger.info("    %s", line)
    else:
        logger.info("Skipped PYTHIA.")

    # -- STEP 3: Optionally re-evaluate the database --
    run_reeval = False
    if not auto_mode:
        run_reeval = questionary.confirm(
            "Step 3/4: Re-evaluate the database with the new criteria?\n"
            "   (This re-scores all papers using the updated prompts.)",
            default=True,
            style=TALOS_QUESTIONARY_STYLE,
        ).ask()

    if run_reeval:
        logger.info("Running database re-evaluation...")
        logger.info("(This may take a while depending on database size.)")
        rc, out = run_script("reevaluate_database.py", stdin_text="y\n")
        if rc == 0:
            logger.info("Database re-evaluation complete.")
        else:
            logger.warning("Re-evaluation completed with code %s.", rc)
    else:
        logger.info("Skipped database re-evaluation.")

    # -- STEP 4: Optionally retrain the DRL agent --
    run_retrain = False
    if not auto_mode:
        run_retrain = questionary.confirm(
            "Step 4/4: Retrain the DRL agent with updated scores?\n"
            "   (Runs 500 episodes of DDQN training -- ~2-5 minutes on GPU.)",
            default=False,
            style=TALOS_QUESTIONARY_STYLE,
        ).ask()

    if run_retrain:
        episodes = 500
        if not auto_mode:
            ep_input = questionary.text(
                "How many training episodes?",
                default="500",
                validate=lambda t: t.isdigit() and int(t) > 0,
                style=TALOS_QUESTIONARY_STYLE,
            ).ask()
            if ep_input:
                episodes = int(ep_input)

        logger.info("Training DRL agent for %s episodes...", episodes)
        rc, out = run_script("train_agent.py", args=[f"--episodes={episodes}"])
        if rc == 0:
            logger.info("Agent retraining complete.")

            # Show summary from output
            for line in out.strip().split("\n"):
                if any(kw in line for kw in ["Best episode", "Average reward", "Model saved"]):
                    logger.info("    %s", line.strip())
        else:
            logger.warning("Training completed with code %s.", rc)
    else:
        logger.info("Skipped agent retraining.")

    # -- STEP 5: Final save --
    save_state_to_profile(profile)
    logger.info("Profile '%s' saved.", profile)

    # -- Summary panel (emoji-free academic styling) --
    summary = Panel(
        "[bold bright_cyan]Research Pivot Complete[/bold bright_cyan]\n"
        f"[dim]Profile:[/dim] {profile}\n"
        f"[dim]PYTHIA regenerated:[/dim] {'[green]YES[/green]' if run_pythia else '[yellow]SKIPPED[/yellow]'}\n"
        f"[dim]Database re-evaluated:[/dim] {'[green]YES[/green]' if run_reeval else '[yellow]SKIPPED[/yellow]'}\n"
        f"[dim]Agent retrained:[/dim] {'[green]YES[/green]' if run_retrain else '[yellow]SKIPPED[/yellow]'}\n\n"
        "[dim]Next steps:[/dim]\n"
        "  - Run a Daily Search to find new papers with your new queries.\n"
        "  - Start the Autonomous Research Service (daemon) for 24/7 monitoring.\n"
        "  - Use CHIRON to generate a new knowledge path.",
        title="[bold]PIVOT SUMMARY[/bold]",
        border_style="green",
    )
    console.print(summary)
if __name__ == "__main__":
    main()