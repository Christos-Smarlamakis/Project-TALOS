# -*- coding: utf-8 -*-
"""
Module: layout_builder.py
Project: TALOS v5.22.1
Description:
    Builds the responsive two-column, four-panel terminal grid for the TALOS
    Scientific Terminal Dashboard using rich.layout.Layout. The layout is
    decomposed into a header HUD, a two-column body (left: Cognitive Mesh &
    FinOps over PRISMA Swarm & Full-Text; right: Discovery & Harvesting over
    System, Export & Diagnostics), and a footer command-palette bar. Panel
    bodies are static descriptive content; the interactive dispatcher in
    talos.py owns every state-changing route, keeping this module a pure
    renderable factory (Constitution III, strict modularity).

Dependencies:
    - rich.layout.Layout: the named-region grid primitive.
    - rich.panel.Panel, rich.text.Text, rich.align.Align: styling primitives.
"""

from typing import Optional

from rich.align import Align
from rich.layout import Layout
from rich.panel import Panel
from rich.text import Text


# -- v5.22.1: central tool-count badges (single source of truth). The four
# -- main-cockpit panels render these counts in their titles so the operator
# -- sees the tool surface at a glance. Edit here once to update all panels. --
_PANEL_TOOL_COUNTS = {
    "cognitive": 16,
    "discovery": 11,
    "prisma": 16,
    "drl_gwo": 10,
}


class DashboardLayoutBuilder:
    """Construct the 4-panel Scientific Terminal Dashboard layout.

    The builder owns only presentation: it assembles a named Layout tree whose
    four body panels describe the four cognitive zones of the HMI, delegating
    the header to a ``HudRenderer`` and the footer to a command-palette legend.
    It never executes domain logic.

    Attributes:
        hud_panel (Optional[Panel]): The cached HUD panel to place in the header.
    """

    def __init__(self, hud_panel: Optional[Panel] = None) -> None:
        """Initialise the builder with an optional pre-built HUD panel.

        Args:
            hud_panel (Optional[Panel]): A HUD panel; when omitted a placeholder
                header is used.
        """
        self.hud_panel: Optional[Panel] = hud_panel

    # ------------------------------------------------------------------
    # -- Public API ----------------------------------------------------
    # ------------------------------------------------------------------

    def build_dashboard(self, hud_panel: Optional[Panel] = None) -> Layout:
        """Assemble and return the full named-region dashboard layout.

        Args:
            hud_panel (Optional[Panel]): Overrides the cached HUD panel.

        Returns:
            Layout: The complete layout tree with every region populated.
        """
        header = hud_panel or self.hud_panel or self._placeholder_header()

        layout = Layout(name="root")
        layout.split(
            Layout(name="header", size=7),
            Layout(name="body"),
            Layout(name="footer", size=4),
        )

        layout["body"].split_row(
            Layout(name="left", ratio=1),
            Layout(name="right", ratio=1),
        )
        layout["left"].split(
            Layout(name="panel1"),
            Layout(name="panel3"),
        )
        layout["right"].split(
            Layout(name="panel2"),
            Layout(name="panel4"),
        )

        layout["header"].update(header)
        layout["panel1"].update(self._panel_cognitive())
        layout["panel2"].update(self._panel_discovery())
        layout["panel3"].update(self._panel_prisma())
        layout["panel4"].update(self._panel_system())
        layout["footer"].update(self._footer())
        return layout

    # ------------------------------------------------------------------
    # -- Panel factories ----------------------------------------------
    # ------------------------------------------------------------------

    def _placeholder_header(self) -> Panel:
        """Return a minimal header used when no HUD panel is supplied.

        Returns:
            Panel: A placeholder header panel.
        """
        return Panel(
            Align.center(
                Text(
                    "TALOS v5.22.1 -- Scientific Terminal Dashboard",
                    style="bold bright_cyan",
                )
            ),
            border_style="#006699",
        )

    def _panel(self, title: str, body: str, border_style: str) -> Panel:
        """Return a styled panel from a title and a newline-joined body.

        Args:
            title (str): Panel title.
            body (str): Panel body text (Rich markup allowed).
            border_style (str): Border colour style string.

        Returns:
            Panel: The styled panel.
        """
        return Panel(body, title=title, border_style=border_style, padding=(0, 1))

    def _panel_cognitive(self) -> Panel:
        """Panel 1 -- Cognitive Mesh & FinOps.

        Returns:
            Panel: The Cognitive Mesh & FinOps panel.
        """
        body = (
            "[bold bright_cyan]Cognitive Mesh & FinOps[/bold bright_cyan]\n"
            "[dim]AI Strategy Configurator (Auto-Pilot FinOps)[/dim]\n"
            "[dim]Model Scout (full multi-source catalog)[/dim]\n"
            "[dim]Discover Top LLMs & Live Benchmarks[/dim]\n"
            "[dim]Hardware SOTA Advisor[/dim]"
        )
        return self._panel(
            "[1] Cognitive Mesh & FinOps ({} Tools)".format(_PANEL_TOOL_COUNTS["cognitive"]),
            body, "cyan",
        )

    def _panel_discovery(self) -> Panel:
        """Panel 2 -- Discovery & Harvesting Mesh.

        Returns:
            Panel: The Discovery & Harvesting Mesh panel.
        """
        body = (
            "[bold bright_cyan]Discovery & Harvesting Mesh[/bold bright_cyan]\n"
            "[dim]Daily Ingestion (18 APIs)[/dim]\n"
            "[dim]Historical Deep-Days Harvest[/dim]\n"
            "[dim]Forward/Backward Citation Snowballing[/dim]\n"
            "[dim]Neural Vector & Code-First Retrieval[/dim]"
        )
        return self._panel(
            "[2] Discovery & Harvesting Mesh ({} Tools)".format(_PANEL_TOOL_COUNTS["discovery"]),
            body, "bright_blue",
        )

    def _panel_prisma(self) -> Panel:
        """Panel 3 -- Advanced Analysis & PRISMA.

        Returns:
            Panel: The Advanced Analysis & PRISMA panel.
        """
        body = (
            "[bold bright_cyan]Advanced Analysis & PRISMA[/bold bright_cyan]\n"
            "[dim]Knowledge Constellation & Graphify[/dim]\n"
            "[dim]PRISMA-ScR Declarative Synthesis[/dim]\n"
            "[dim]Two-Tier Kitchenham Quality Appraisal[/dim]\n"
            "[dim]BibTeX / LaTeX Academic Export[/dim]"
        )
        return self._panel(
            "[3] Advanced Analysis & PRISMA ({} Tools)".format(_PANEL_TOOL_COUNTS["prisma"]),
            body, "bright_magenta",
        )

    def _panel_system(self) -> Panel:
        """Panel 4 -- DRL Agents & GWO Swarm.

        Returns:
            Panel: The DRL Agents & GWO Swarm panel.
        """
        body = (
            "[bold bright_cyan]DRL Agents & GWO Swarm[/bold bright_cyan]\n"
            "[dim]24/7 Autonomous Daemon[/dim]\n"
            "[dim]Live DRL Agent (API Fetching)[/dim]\n"
            "[dim]Train DRL Agent / Offline Training[/dim]\n"
            "[dim]GWO Hyperparameter & Router Swarm[/dim]"
        )
        return self._panel(
            "[4] DRL Agents & GWO Swarm ({} Tools)".format(_PANEL_TOOL_COUNTS["drl_gwo"]),
            body, "green",
        )

    def _footer(self) -> Panel:
        """Return the footer command-palette legend.

        Returns:
            Panel: The footer prompt bar.
        """
        body = (
            "[bold bright_cyan]Command Palette[/bold bright_cyan]  "
            "[dim]/scavenge|/scout  /audit  /fts <q>  /config  /tree <arch|phd|mesh>  "
            "/probe  /view <path>  /help  /quit[/dim]"
        )
        return Panel(body, title="[bold]Console HMI[/bold]", border_style="yellow", padding=(0, 1))
