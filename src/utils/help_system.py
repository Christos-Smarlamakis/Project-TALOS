# -*- coding: utf-8 -*-
"""
Module: help_system.py
Project: TALOS v5.21.1
Description:
    Enterprise Console Help System. Renders a structured, four-section CLI
    manual for the TALOS terminal UI and bridges to the interactive FastAPI Web
    Manual served at GET /help. The four sections are:
      - Section A: Standard Operating Procedures (SOP Runbooks) -- step-by-step
        workflows for PRISMA-ScR systematic review, neural vector and code-first
        retrieval, and autonomous mission planning.
      - Section B: Scientific Command Matrix -- a categorized cheatsheet of
        every CLI flag grouped into Ingestion, Evaluation, Search, PDF
        Harvesting, and System Management.
      - Section C: Operational Diagnostics & Self-Healing Guide -- recovery
        procedures for quota depletion, Ollama port conflicts, and model
        alignment.
      - Section D: Environment & Configuration Specs -- profile paths, hardware
        parameters, and port assignments (:8000, :8001, :8002, :11434).

    In non-interactive mode the renderer returns a Rich Group so callers may
    print it directly; in interactive mode it prints the sections and prompts
    the user to open the Web Manual or return to the menu.

    Key design decisions:
    - Zero emojis and pure formal academic tone in every heading and cell.
    - Ports and paths are derived from config.settings so the manual never
      drifts from the canonical configuration surface.
    - The interactive browser prompt optionally bootstraps the FastAPI backend
      (mirroring the capabilities viewer) so /help resolves even on a cold start.

Dependencies:
    - config.settings: canonical TALOS_VERSION and TALOS_API_PORT constants.
    - src.utils.ui_theme: the canonical TALOS_QUESTIONARY_STYLE prompt theme.
    - rich: Panel, Table, Text, Group, and Console rendering.
    - questionary: interactive action selection.
    - webbrowser, socket, subprocess, sys, os, time: interactive browser launch.
"""
import os
import socket
import subprocess
import sys
import time
import webbrowser

from rich.console import Console, Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich import box
from rich.align import Align

from config.settings import TALOS_VERSION, TALOS_API_PORT
from src.utils.ui_theme import TALOS_QUESTIONARY_STYLE

# -- Web Manual endpoint resolved from the canonical API port (default 8001). --
_HELP_WEB_URL = f"http://localhost:{TALOS_API_PORT}/help"

# -- Module-level Rich console used by the interactive renderer. --
_console = Console()

# -- Shared accent palette (matches the TALOS academic dark theme). --
_PANEL_STYLES = ("bright_cyan", "bright_blue", "bright_magenta", "bright_green")


def _section_a_sop_runbooks() -> Panel:
    """Build Section A: Standard Operating Procedures (SOP Runbooks).

    Returns:
        Panel: A Rich Panel with three guided step-by-step workflows.
    """
    body = Text()
    body.append("Runbook A1 -- PRISMA-ScR Systematic Review Workflow\n",
                style="bold bright_cyan")
    body.append("  1. Deep harvest      : python talos.py --daily  "
                "(18-source ingestion)\n")
    body.append("  2. Swarm appraisal   : python talos.py --appraise-quality "
                "--swarm --min-score 7.0\n")
    body.append("  3. Full-text download: python talos.py --download-pdfs "
                "--min-score 7.0\n")
    body.append("  4. LaTeX synthesis   : python talos.py --prisma --swarm\n")
    body.append("\n")

    body.append("Runbook A2 -- Neural Vector & Code-First Retrieval Workflow\n",
                style="bold bright_blue")
    body.append("  1. Code mining        : python talos.py --code-search \"<query>\"\n")
    body.append("  2. Vector embedding   : python talos.py --vector-search \"<query>\"\n")
    body.append("  3. FTS5 verification  : python talos.py --fts \"<phrase>\"\n")
    body.append("\n")

    body.append("Runbook A3 -- Autonomous Mission Planning Execution\n",
                style="bold bright_magenta")
    body.append("  1. Provision profile and compile auditor skills:\n")
    body.append("     python talos.py --compile-skills\n")
    body.append("  2. Launch the PAIR-DRL agent evaluation under CJCSI 3160.01A\n")
    body.append("     constraints via Group 4 (DRL Agents, Daemons & GWO Swarm).\n")
    body.append("  3. Review the 3D Knowledge Constellation HUD and export the\n")
    body.append("     synthesized mission-planning report.\n")
    body.append("\n")

    body.append("Runbook A4 -- Autonomous Model Scout & Market Intelligence\n",
                style="bold bright_green")
    body.append("  1. Forage the full multi-source catalog (150+ models):\n")
    body.append("     python talos.py --scout-models --all\n")
    body.append("     (alias: --scavenge-models --all)\n")
    body.append("  2. Limit discovery to a recent window:\n")
    body.append("     python talos.py --scout-models --days 30\n")
    body.append("  3. Generate reports without the console summary:\n")
    body.append("     python talos.py --scout-models --all --report-only\n")
    body.append("  4. Configure the hybrid FinOps strategy (auto-pilot):\n")
    body.append("     python talos.py --configure-ai-strategy\n")
    body.append("  5. Adopt champion models with one click:\n")
    body.append("     python talos.py --apply-optimal-models --strategy AUTO\n")
    body.append("  6. Open the standalone Dark Theme dashboard under:\n")
    body.append("     data/reports/llm_intelligence/llm_market_intelligence_YYYYMMDD.html\n")

    return Panel(
        body,
        title="[bold]Section A -- Standard Operating Procedures (SOP Runbooks)[/bold]",
        border_style=_PANEL_STYLES[0],
        box=box.ROUNDED,
        padding=(1, 2),
    )


def _section_b_command_matrix() -> Panel:
    """Build Section B: the categorized Scientific Command Matrix.

    Returns:
        Panel: A Rich Panel containing a five-category flag-reference Table.
    """
    table = Table(
        title="Scientific Command Matrix",
        box=box.ROUNDED,
        border_style="bright_blue",
        show_lines=True,
        header_style="bold bright_blue",
        expand=False,
    )
    table.add_column("Category", style="bold cyan", no_wrap=True)
    table.add_column("Flag", style="bold white", no_wrap=True)
    table.add_column("Description", style="white")

    table.add_row("Ingestion", "--daily", "18-source daily search ingestion pipeline.")
    table.add_row("Ingestion", "--wizard", "4-step research setup wizard.")
    table.add_row("Evaluation", "--appraise-quality [--swarm] [--force]",
                  "Kitchenham (2007) quality appraisal with Tier-2 swarm.")
    table.add_row("Evaluation", "--prisma [--swarm]",
                  "PRISMA-ScR declarative synthesis pipeline.")
    table.add_row("Evaluation", "--compile-skills [--force]",
                  "Compile the four domain-specialized auditor skills.")
    table.add_row("Evaluation", "--export-bib [score]",
                  "Export the curated library to BibTeX / LaTeX.")
    table.add_row("Search", "--snowball [seed]", "Citation snowballing.")
    table.add_row("Search", "--vector-search [query]",
                  "Neural vector semantic search.")
    table.add_row("Search", "--code-search [query]", "Code-first discovery.")
    table.add_row("Search", "--fts \"[query]\"", "SQLite FTS5 full-text search.")
    table.add_row("PDF Harvesting", "--download-pdfs [--min-score 7.0]",
                  "Harvest legal Open Access full-text PDFs.")
    table.add_row("PDF Harvesting", "--open-pdf [paper_id]",
                  "Open a downloaded local PDF.")
    table.add_row("System Management", "--strategy [mode]",
                  "Switch the AI execution strategy.")
    table.add_row("System Management", "--hardware-advisor | --recommend-models",
                  "VRAM budget + 4-role SOTA model matcher.")
    table.add_row("System Management", "--apply-models",
                  "Persist the recommended model stack.")
    table.add_row("System Management", "--discover-llms",
                  "Live SOTA benchmark discovery matrix.")
    table.add_row("System Management", "--scout-models [--all] [--days N] [--report-only]",
                  "Autonomous Model Scout + dual MD/HTML intelligence reports "
                  "(alias: --scavenge-models).")
    table.add_row("System Management", "--configure-ai-strategy",
                  "Interactive Cognitive FinOps & Strategy Configurator (auto-pilot).")
    table.add_row("System Management", "--apply-optimal-models [--strategy ...]",
                  "1-click champion hybrid model adoption into the active profile.")
    table.add_row("System Management", "--diagnostics | --doctor",
                  "8-point ISO/IEC 25010 diagnostics analyzer.")
    table.add_row("System Management", "--stats", "Database statistics report.")
    table.add_row("System Management", "--probe-apis | --diagnose-mesh",
                  "Self-healing API mesh health probe (16 providers, latency, "
                  "HTTP status, access tier).")
    table.add_row("System Management", "--help, -h",
                  "Display this enterprise manual.")

    return Panel(
        Align.left(table),
        title="[bold]Section B -- Scientific Command Matrix[/bold]",
        border_style=_PANEL_STYLES[1],
        box=box.ROUNDED,
        padding=(1, 2),
    )


def _section_c_diagnostics() -> Panel:
    """Build Section C: Operational Diagnostics & Self-Healing Guide.

    Returns:
        Panel: A Rich Panel with recovery procedures for common failure modes.
    """
    body = Text()
    body.append("C1 -- Quota Depletion Recovery\n", style="bold bright_cyan")
    body.append("  - The Cognitive Meta-Router latches a provider offline on HTTP\n")
    body.append("    401 / 402 / 429 and fails over to the next provider in the tier.\n")
    body.append("  - Rotate the API key in the .env file, then restart the session to\n")
    body.append("    clear the session-scoped latches.\n")
    body.append("  - Verify the active provider set: python talos.py --discover-llms\n\n")

    body.append("C2 -- Ollama Port Conflict Recovery\n", style="bold bright_blue")
    body.append("  - Ollama binds :11434; TALOS FastAPI uses :8001 and SYNAPSE uses :8000,\n")
    body.append("    so the three services never collide.\n")
    body.append("  - On Windows, identify the holder: netstat -ano | findstr :11434\n")
    body.append("  - Restart Ollama, then re-probe: python talos.py --diagnostics\n\n")

    body.append("C3 -- Model Alignment Recovery\n", style="bold bright_magenta")
    body.append("  - Reconcile the local GPU budget (RTX 4070, 12 GB VRAM):\n")
    body.append("      python talos.py --recommend-models\n")
    body.append("  - Adopt the recommended 4-role stack: python talos.py --apply-models\n")
    body.append("  - Re-provision any missing model via the Model Provisioning CLI.\n")

    return Panel(
        body,
        title="[bold]Section C -- Operational Diagnostics & Self-Healing Guide[/bold]",
        border_style=_PANEL_STYLES[2],
        box=box.ROUNDED,
        padding=(1, 2),
    )


def _section_d_environment() -> Panel:
    """Build Section D: Environment & Configuration Specs.

    Returns:
        Panel: A Rich Panel combining the port map with profile and hardware
            specifications.
    """
    ports = Table(
        title="Port Assignments",
        box=box.ROUNDED,
        border_style="bright_green",
        show_lines=True,
        header_style="bold bright_green",
        expand=False,
    )
    ports.add_column("Port", style="bold cyan", no_wrap=True)
    ports.add_column("Service", style="bold white", no_wrap=True)
    ports.add_column("Role", style="white")
    ports.add_row("8000", "SYNAPSE Event Bus",
                  "ALEXANDRIA ecosystem interoperability mesh.")
    ports.add_row(f"{TALOS_API_PORT}", "TALOS FastAPI",
                  "REST API, Web Manual (/help), visualizer.")
    ports.add_row("8002", "OPTICA Bridge", "Visualization offload microservice.")
    ports.add_row("11434", "Ollama Runtime", "Local GPU/CPU inference (RTX 4070).")

    specs = Text()
    specs.append("\nProfile Paths\n", style="bold bright_green")
    specs.append("  Active profile config : _profiles/<name>/config.json\n")
    specs.append("  Isolated databases    : _profiles/<name>/talos_research.db\n")
    specs.append("  Default database      : data/talos_research.db\n\n")
    specs.append("Hardware Parameters\n", style="bold bright_green")
    specs.append("  GPU budget            : RTX 4070 (12 GB VRAM), 80% training / "
                "2 GB inference headroom\n")
    specs.append("  Local concurrency cap : threading.Semaphore(2)\n")
    specs.append("  Local models          : qwen2.5:14b, llama3.1:8b, nomic-embed-text\n")

    return Panel(
        Group(Align.left(ports), specs),
        title="[bold]Section D -- Environment & Configuration Specs[/bold]",
        border_style=_PANEL_STYLES[3],
        box=box.ROUNDED,
        padding=(1, 2),
    )


def _build_manual_group() -> Group:
    """Assemble the four enterprise sections into a single Rich Group.

    Returns:
        Group: A Rich Group containing Sections A through D.
    """
    return Group(
        _section_a_sop_runbooks(),
        _section_b_command_matrix(),
        _section_c_diagnostics(),
        _section_d_environment(),
    )


def _open_web_manual() -> None:
    """Probe the FastAPI backend and open the interactive Web Manual.

    If the API backend is not already listening, this helper bootstraps a
    detached uvicorn process (mirroring the capabilities viewer) so the /help
    endpoint resolves on a cold start, then opens the URL in the default
    browser.
    """
    host, port = "127.0.0.1", TALOS_API_PORT
    listening = False
    try:
        with socket.create_connection((host, port), timeout=0.25):
            listening = True
    except OSError:
        listening = False

    if not listening:
        project_root = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..")
        )
        try:
            subprocess.Popen(
                [sys.executable, "-m", "uvicorn", "src.api.main_api:app",
                 "--host", host, "--port", str(port)],
                cwd=project_root,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except OSError:
            _console.print(
                f"[yellow]FastAPI bootstrap failed; ensure the server is running "
                f"on port {port} before opening {_HELP_WEB_URL}.[/yellow]"
            )
            return
        deadline = time.monotonic() + 3.0
        while time.monotonic() < deadline:
            try:
                with socket.create_connection((host, port), timeout=0.25):
                    listening = True
                    break
            except OSError:
                time.sleep(0.15)

    if not listening:
        _console.print(
            f"[yellow]FastAPI is not reachable on port {port}. Start it first, "
            f"then open {_HELP_WEB_URL}.[/yellow]"
        )
        return

    webbrowser.open(_HELP_WEB_URL)
    _console.print(f"[green]Opened the interactive Web Manual: {_HELP_WEB_URL}[/green]")


def render_help_manual(interactive: bool = False):
    """Render the four-section enterprise command reference manual.

    Args:
        interactive (bool): When False, return a Rich Group renderable for the
            caller to print (used by the --help CLI fast-dispatch path). When
            True, print the sections and prompt the user to either open the
            interactive Web Manual in a browser or return to the menu.

    Returns:
        Group or None: A Rich Group renderable when ``interactive`` is False;
        otherwise None after the interactive prompt completes.
    """
    manual_group = _build_manual_group()

    if not interactive:
        return manual_group

    _console.print(manual_group)

    # -- Interactive follow-up action (ISO/IEC 25010 Context of Use) --
    try:
        import questionary
    except ImportError:  # pragma: no cover - questionary is a hard dependency
        questionary = None

    if questionary is None:
        _console.print(
            "[dim]Interactive prompt unavailable. Open the Web Manual manually: "
            f"{_HELP_WEB_URL}[/dim]"
        )
        return None

    try:
        choice = questionary.select(
            "Help manual actions:",
            choices=[
                "Open Interactive Web Manual in Browser "
                f"({_HELP_WEB_URL})",
                "Return to Menu",
            ],
            style=TALOS_QUESTIONARY_STYLE,
            instruction="Use arrow keys to navigate, Enter to select, Esc/Ctrl+C to cancel.",
        ).ask()
    except (KeyboardInterrupt, EOFError):
        choice = None

    if choice is not None and "Open Interactive Web Manual" in choice:
        _open_web_manual()

    return None



