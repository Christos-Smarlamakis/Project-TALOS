# -*- coding: utf-8 -*-
"""
Module: submenu_renderer.py
Project: TALOS v5.22.1
Description:
    Unified Rich sub-menu renderer for the TALOS Scientific Terminal Dashboard.
    Upgrades the primary sub-menus (Universal Search Hub, Configuration &
    Profiles, Advanced Analysis & Visualizations, DRL Agents & GWO Swarm, and
    PRISMA Swarm & PDF Tools) from plain monochrome questionary lists into
    structured two-column Rich tables/panels matching the Main Cockpit
    aesthetic. The renderer is a pure renderable factory (Constitution III):
    it owns no domain logic and never prompts for input.

Dependencies:
    - rich.panel.Panel, rich.table.Table, rich.text.Text, rich.console.Group,
      rich.box: styled rendering primitives.
"""
from typing import List, Optional, Tuple, Union

from rich import box
from rich.console import Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text


class RichSubmenuRenderer:
    """Render a structured two-column Rich sub-menu panel.

    The renderer transforms an ordered list of menu entries into a compact
    two-column Rich Table wrapped in a rounded Panel. Category header strings
    break the columns into labelled groups, every item receives a zero-padded
    numbered badge (``[01]``, ``[02]``, ...), optional status tags follow each
    label, and a ``[00] Back`` row is always appended so the user can return to
    the main cockpit.

    Attributes:
        title (str): Panel title.
        subtitle (str): Optional descriptive subtitle shown under the title.
        border_style (str): Rich border colour for the panel.
    """

    def __init__(self, title: str, subtitle: str = "",
                 border_style: str = "cyan") -> None:
        self.title = title
        self.subtitle = subtitle
        self.border_style = border_style

    # ------------------------------------------------------------------
    # -- Public API ----------------------------------------------------
    # ------------------------------------------------------------------

    def build(self, entries: List[Union[str, Tuple[str, Optional[str]]]]) -> Panel:
        """Build and return the two-column sub-menu panel.

        Args:
            entries (list): Ordered menu entries. Each element is either a
                category header string, or a 2-tuple ``(label, status)`` where
                ``status`` is an optional tag (may be ``None``).

        Returns:
            Panel: The styled Rich panel containing the two-column table.
        """
        table = Table(show_header=False, box=None, padding=(0, 1), expand=False)
        table.add_column(justify="left", no_wrap=True)
        table.add_column(justify="left", no_wrap=True)

        pending: List[Text] = []
        counter = 0

        def flush() -> None:
            """Emit buffered item cells into the table, two per row."""
            while pending:
                left = pending.pop(0)
                right = pending.pop(0) if pending else Text("")
                table.add_row(left, right)

        for entry in entries:
            if isinstance(entry, str):
                # -- Category header: full-width separator row. --
                flush()
                table.add_row(Text(entry, style="bold bright_cyan"), Text(""))
                continue
            label, status = entry
            counter += 1
            cell = Text()
            cell.append("[{:02d}] ".format(counter), style="bold cyan")
            cell.append(label or "", style="white")
            if status:
                cell.append("  " + status, style="dim yellow")
            pending.append(cell)

        flush()
        # -- Always append the Back navigation row. --
        table.add_row(Text("[00] Back", style="bold yellow"), Text(""))

        content = []
        if self.subtitle:
            content.append(Text(self.subtitle, style="dim"))
        content.append(table)

        return Panel(
            Group(*content),
            title="[bold]" + self.title + "[/bold]",
            border_style=self.border_style,
            box=box.ROUNDED,
            padding=(0, 1),
        )


def render_submenu(title: str, subtitle: str = "",
                   entries: List[Union[str, Tuple[str, Optional[str]]]] = None,
                   border_style: str = "cyan") -> Panel:
    """Build a two-column Rich sub-menu panel in a single call.

    Args:
        title (str): Panel title.
        subtitle (str): Optional descriptive subtitle.
        entries (list): Ordered menu entries (header strings and (label, status)
            tuples).
        border_style (str): Rich border colour.

    Returns:
        Panel: The styled Rich panel.
    """
    return RichSubmenuRenderer(title, subtitle, border_style).build(entries or [])


__all__ = ["RichSubmenuRenderer", "render_submenu"]
