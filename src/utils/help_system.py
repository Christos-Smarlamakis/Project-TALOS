# -*- coding: utf-8 -*-
"""
Module: help_system.py
Project: TALOS v5.16.0
Description:
    Dual-Surface User Assistance System. This module renders a rich, four-panel
    interactive command reference for the TALOS terminal UI and provides the
    interactive bridge to the FastAPI Web Manual. The four panels document the
    CLI fast-dispatch flags, the interactive navigation controls (TUI and the
    3D WebGL constellation HUD), the service port mapping, and the generated
    reports and storage artifacts. In non-interactive mode the function returns
    a Rich renderable Group so callers may print it directly; in interactive
    mode it prints the panels and then prompts the user to either open the Web
    Manual in a browser or return to the menu.

    Key design decisions:
    - Zero emojis and pure formal academic tone in every heading and cell.
    - Ports and directory paths are derived from config.settings so the manual
      never drifts from the canonical configuration surface.
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


def _panel_1_cli_flags() -> Panel:
    """Build Panel 1: categorized CLI fast-dispatch flags.

    Returns:
        Panel: A Rich Panel containing a categorized flag-reference Table.
    """
    table = Table(
        title="CLI Fast-Dispatch Flags",
        box=box.ROUNDED,
        border_style="bright_cyan",
        show_lines=True,
        header_style="bold bright_cyan",
        expand=False,
    )
    table.add_column("Category", style="bold cyan", no_wrap=True)
    table.add_column("Flag", style="bold white", no_wrap=True)
    table.add_column("Description", style="white")

    table.add_row("Research Setup", "--wizard",
                  "Launch the 4-step Research Setup Wizard "
                  "(src/utils/research_setup_wizard.py).")
    table.add_row("Ingestion", "--daily",
                  "Trigger the 18-source Daily Search ingestion pipeline "
                  "(src/ingestion/daily_search.py).")
    table.add_row("Universal Search Hub", "--snowball [seed]",
                  "Backward/forward citation snowballing (seed = DOI, DB ID, or title).")
    table.add_row("Universal Search Hub", "--vector-search [query]",
                  "Neural vector semantic search over local nomic-embed-text embeddings.")
    table.add_row("Universal Search Hub", "--code-search [query]",
                  "Reproducible code-first discovery (GitHub / PapersWithCode / benchmarks).")
    table.add_row("PRISMA Swarm", "--prisma [--swarm]",
                  "PRISMA-ScR declarative synthesis pipeline; --swarm enables the "
                  "3-agent peer-review consensus swarm.")
    table.add_row("Exports", "--export-bib [score] [--min-quality Q] [--quadrant Q]",
                  "Export curated papers to a BibTeX / LaTeX library with dual "
                  "relevance/quality filtering (data/exports/talos_library.bib).")
    table.add_row("Quality Appraisal", "--appraise-quality [--min-score 7.0]",
                  "Batch Kitchenham (2007) scientific quality appraisal of "
                  "candidate papers with 2D evidence-quadrant classification.")
    table.add_row("AI Strategy", "--strategy [mode]",
                  "Switch the AI execution strategy (strict_local, local_first, "
                  "cloud_first, strict_cloud, auto_dynamic).")
    table.add_row("Diagnostics", "--diagnostics | --doctor, -d",
                  "Run the 8-point ISO/IEC 25010 System Diagnostics Analyzer.")
    table.add_row("Diagnostics", "--stats",
                  "Run the Database Statistics health report (src/utils/db_stats.py).")
    table.add_row("Diagnostics", "--help, -h",
                  "Display this four-panel command reference manual.")

    return Panel(
        Align.left(table),
        title="[bold]Panel 1 -- CLI Fast-Dispatch Flags[/bold]",
        border_style=_PANEL_STYLES[0],
        box=box.ROUNDED,
        padding=(1, 2),
    )


def _panel_2_controls() -> Panel:
    """Build Panel 2: interactive controls and navigation semantics.

    Returns:
        Panel: A Rich Panel documenting TUI and 3D WebGL navigation controls.
    """
    body = Text()
    body.append("Terminal UI (TUI) Navigation\n", style="bold bright_blue")
    body.append("  Up / Down arrows     Move the selection highlight.\n")
    body.append("  Enter                Confirm the highlighted operation.\n")
    body.append("  Esc / Ctrl+C         Cancel safely -- the session returns to the "
                "menu without corrupting database or profile state.\n")
    body.append("\n")

    body.append("3D WebGL Constellation HUD (Visualizer Shortcuts)\n",
                style="bold bright_magenta")
    body.append("  C / L                Toggle the telemetry console overlay.\n")
    body.append("  R                    Reset the camera view.\n")
    body.append("  T                    Toggle the light/dark theme.\n")
    body.append("  F                    Toggle fullscreen.\n")
    body.append("  S                    Capture a PNG snapshot.\n")
    body.append("  Space                Pause / resume live playback.\n")
    body.append("  1 / 2 / 3            Set replay speed.\n")
    body.append("\n")

    body.append("3D WebGL Mouse Controls\n", style="bold bright_green")
    body.append("  Left-drag            Orbit / rotate the constellation.\n")
    body.append("  Right-drag           Pan the camera.\n")
    body.append("  Scroll wheel         Zoom in / out.\n")

    return Panel(
        body,
        title="[bold]Panel 2 -- Interactive Controls & Navigation[/bold]",
        border_style=_PANEL_STYLES[1],
        box=box.ROUNDED,
        padding=(1, 2),
    )


def _panel_3_ports() -> Panel:
    """Build Panel 3: port mapping and services architecture.

    Returns:
        Panel: A Rich Panel containing the service port mapping Table.
    """
    table = Table(
        title="Port Mapping & Services Architecture",
        box=box.ROUNDED,
        border_style="bright_magenta",
        show_lines=True,
        header_style="bold bright_magenta",
        expand=False,
    )
    table.add_column("Port", style="bold cyan", no_wrap=True)
    table.add_column("Service", style="bold white", no_wrap=True)
    table.add_column("Role", style="white")

    table.add_row(f"{TALOS_API_PORT}", "TALOS FastAPI",
                  "Headless REST API, interactive Web Manual (/help), and 3D "
                  "Knowledge Constellation Visualizer.")
    table.add_row("8000", "SYNAPSE Event Bus",
                  "Event-driven interoperability mesh for the ALEXANDRIA ecosystem.")
    table.add_row("8002", "OPTICA Bridge",
                  "Visualization offload microservice (cnsplots / PyVis).")
    table.add_row("11434", "Ollama GPU",
                  "Heavy reasoning tier (large local models on GPU).")
    table.add_row("11435", "Fast Edge CPU",
                  "Lightweight low-latency edge tier (dedicated local endpoint).")

    return Panel(
        Align.left(table),
        title="[bold]Panel 3 -- Port Mapping & Services Architecture[/bold]",
        border_style=_PANEL_STYLES[2],
        box=box.ROUNDED,
        padding=(1, 2),
    )


def _panel_4_artifacts() -> Panel:
    """Build Panel 4: generated reports and storage artifacts directory map.

    Returns:
        Panel: A Rich Panel containing the artifact directory map Table.
    """
    table = Table(
        title="Generated Reports & Storage Artifacts",
        box=box.ROUNDED,
        border_style="bright_green",
        show_lines=True,
        header_style="bold bright_green",
        expand=False,
    )
    table.add_column("Artifact", style="bold cyan", no_wrap=True)
    table.add_column("Path / Location", style="bold white", no_wrap=True)

    table.add_row("BibTeX / LaTeX library", "data/exports/talos_library.bib")
    table.add_row("Neural vector search reports", "data/reports/vector_search/")
    table.add_row("Code-first search reports", "data/reports/code_search/")
    table.add_row("Citation snowballing genealogy", "data/reports/snowball/")
    table.add_row("PRISMA-ScR LaTeX synthesis",
                  "src/prisma/scoping_review_synthesizer.py output")
    table.add_row("Active profile database", "data/talos_research.db (default)")
    table.add_row("Isolated profile databases", "_profiles/<profile>/talos_research.db")
    table.add_row("Quality appraisal fields",
                  "papers.quality_score / quality_rubric_json / evidence_quadrant")

    return Panel(
        Align.left(table),
        title="[bold]Panel 4 -- Generated Reports & Storage Artifacts[/bold]",
        border_style=_PANEL_STYLES[3],
        box=box.ROUNDED,
        padding=(1, 2),
    )


def _build_manual_group() -> Group:
    """Assemble the four panels into a single Rich renderable Group.

    Returns:
        Group: A Rich Group containing all four help panels.
    """
    return Group(
        _panel_1_cli_flags(),
        _panel_2_controls(),
        _panel_3_ports(),
        _panel_4_artifacts(),
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
    """Render the four-panel TALOS command reference manual.

    Args:
        interactive (bool): When False, return a Rich Group renderable for the
            caller to print (used by the --help CLI fast-dispatch path). When
            True, print the panels and prompt the user to either open the
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
