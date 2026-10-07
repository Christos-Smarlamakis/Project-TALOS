# -*- coding: utf-8 -*-
"""
Module: submenu_renderer.py
Project: TALOS v5.25.3
Description:
    Universal 3-Tier Sub-Menu renderer for the TALOS Scientific Terminal
    Dashboard, implementing the ISO/IEC 25010 Usability layout. The renderer
    produces a strict three-tier stack:

      Tier 1 - Header Summary Panel: clean panel with title, subtitle, and an
               active domain description.
      Tier 2 - Body Grid (Strict Column-Major Numbering): a two-column Rich
               table where an ordered item list is split so that the left
               column holds ``[01]..[ceil(N/2)]`` top-to-bottom and the right
               column holds ``[ceil(N/2)+1]..[N]`` top-to-bottom, followed by a
               centered ``[00] Back`` footer row.
      Tier 3 - Contextual Navigation Footer: a compact one-line styled panel
               listing the input range, navigation keys, and context shortcuts.

    The renderer owns no domain logic; it is a pure renderable factory
    (Constitution III) plus a single type-safe input helper ``prompt_choice()``
    that replaces the legacy duplicate ``questionary.select`` lists across the
    entire system.

Dependencies:
    - rich.panel.Panel, rich.table.Table, rich.text.Text, rich.console.Group,
      rich.box, rich.prompt.Prompt, rich.align.Align, rich.console.Console:
      styled rendering and the type-safe single-line prompt.
"""

from typing import List, Optional, Tuple, Union

from rich import box
from rich.align import Align
from rich.console import Console, Group
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table
from rich.text import Text

console = Console()


class RichSubmenuRenderer:
    """Render a strict ISO/IEC 25010 three-tier Rich sub-menu.

    The renderer transforms an ordered list of menu items into a three-tier
    stack: a header panel, a two-column column-major body grid, and a
    contextual navigation footer. Every item receives a zero-padded numbered
    badge (``[01]`` .. ``[NN]``), optional status tags follow each label, and a
    centered ``[00] Back`` row is always appended.

    Attributes:
        title (str): Header panel title.
        subtitle (str): Optional descriptive subtitle.
        domain (str): Optional active domain description shown in the header.
        border_style (str): Rich border colour for the panels.
    """

    def __init__(self, title: str, subtitle: str = "",
                 border_style: str = "cyan", domain: str = "") -> None:
        self.title = title
        self.subtitle = subtitle
        self.border_style = border_style
        self.domain = domain

    # ------------------------------------------------------------------
    # -- Public API ----------------------------------------------------
    # ------------------------------------------------------------------

    def build(
        self,
        entries: List[Union[str, Tuple[str, Optional[str]]]],
        context_shortcuts: str = "",
        back_label: str = "Back / Return to Main Cockpit",
    ) -> Group:
        """Build and return the three-tier sub-menu renderable.

        Args:
            entries (list): Ordered menu items as ``(label, status)`` tuples.
                Category header strings are still accepted and rendered as
                full-width section separators.
            context_shortcuts (str): Shortcut summary for the navigation footer.
            back_label (str): Label for the ``[00]`` back row.

        Returns:
            Group: The three-tier renderable (header panel, body grid, footer).
        """
        header_panel = self._build_header()
        body_table = self._build_body(entries, back_label)
        footer_panel = self._build_footer(
            len(self._items(entries)), context_shortcuts
        )
        return Group(header_panel, body_table, footer_panel)

    def prompt_choice(
        self,
        valid_range: Tuple[int, int],
        default: str = "01",
    ) -> str:
        """Prompt for a type-safe single-line menu selection.

        The prompt accepts zero-padded or single-digit numbers within
        ``valid_range``, the Back navigation keys (``0``, ``00``, ``b``,
        ``back``), and the Quit keys (``q``, ``quit``, ``exit``).

        Args:
            valid_range (tuple[int, int]): Inclusive ``(lo, hi)`` selection range.
            default (str): Default selection string (e.g. ``"01"``).

        Returns:
            str: The normalized selection token (``"01".."NN"``, ``"00"`` for
                Back, or ``"q"`` for Quit).
        """
        lo, hi = valid_range
        prompt_text = f"Select operation [{lo:02d}-{hi:02d}] (default: {default})"
        while True:
            try:
                raw = (Prompt.ask(prompt_text, default=default) or "").strip()
            except (KeyboardInterrupt, EOFError):
                return "q"
            if not raw:
                raw = default
            key = raw.lower()
            if key in ("0", "00", "b", "back"):
                return "00"
            if key in ("q", "quit", "exit"):
                return "q"
            if key.isdigit():
                number = int(key)
                if 1 <= number <= hi:
                    return f"{number:02d}"
                if number == 0:
                    return "00"
            console.print(
                "[yellow]Invalid selection. Enter a number "
                f"{lo:02d}-{hi:02d}, 0/b for Back, or q to Quit.[/yellow]"
            )

    # ------------------------------------------------------------------
    # -- Tier builders -------------------------------------------------
    # ------------------------------------------------------------------

    def _build_header(self) -> Panel:
        """Build Tier 1: the header summary panel.

        Returns:
            Panel: The header panel with title, subtitle, and domain.
        """
        content = []
        if self.subtitle:
            content.append(Text(self.subtitle, style="dim"))
        if self.domain:
            content.append(Text(self.domain, style="bold bright_cyan"))
        return Panel(
            Group(*content) if content else Text(""),
            title="[bold]" + self.title + "[/bold]",
            border_style=self.border_style,
            box=box.ROUNDED,
            padding=(0, 1),
        )

    def _build_body(
        self,
        entries: List[Union[str, Tuple[str, Optional[str]]]],
        back_label: str,
    ) -> Table:
        """Build Tier 2: the two-column column-major body grid.

        Args:
            entries (list): Ordered menu entries.
            back_label (str): Label for the ``[00]`` back row.

        Returns:
            Table: The body table with strict column-major numbering.
        """
        items = self._items(entries)
        count = len(items)
        table = Table(show_header=False, box=box.SIMPLE,
                      border_style=self.border_style,
                      padding=(0, 2), expand=True)
        table.add_column(justify="left", no_wrap=True, ratio=1)
        table.add_column(justify="left", no_wrap=True, ratio=1)

        # -- Category headers are rendered as full-width separators first. --
        for entry in entries:
            if isinstance(entry, str):
                table.add_row(Text(entry, style="bold bright_cyan"), Text(""))

        if count == 0:
            back_cell = Text("[00] " + back_label, style="bold yellow")
            table.add_row(Align.center(back_cell), Text(""))
            return table

        left_count = (count + 1) // 2
        numbered = [
            (index + 1, label, status)
            for index, (label, status) in enumerate(items)
        ]
        left = numbered[:left_count]
        right = numbered[left_count:]

        for index in range(left_count):
            left_cell = self._cell(*left[index])
            right_cell = self._cell(*right[index]) if index < len(right) else Text("")
            table.add_row(left_cell, right_cell)

        # -- Centered [00] Back footer row. --
        back_cell = Text("[00] " + back_label, style="bold yellow")
        table.add_row(Align.center(back_cell), Text(""))
        return table

    def _build_footer(self, item_count: int, context_shortcuts: str) -> Panel:
        """Build Tier 3: the contextual one-line navigation footer.

        Args:
            item_count (int): The number of selectable items.
            context_shortcuts (str): Shortcut summary string.

        Returns:
            Panel: A compact one-line navigation footer.
        """
        shortcuts = (
            f"  |  Shortcuts: {context_shortcuts}" if context_shortcuts else ""
        )
        footer = (
            f"Input: 01-{item_count:02d}  |  Navigation: 00/b = Back, "
            f"q = Quit{shortcuts}"
        )
        return Panel(
            Text(footer, style="bold"),
            border_style="dim",
            box=box.ROUNDED,
            padding=(0, 1),
        )

    # ------------------------------------------------------------------
    # -- Helpers -------------------------------------------------------
    # ------------------------------------------------------------------

    @staticmethod
    def _items(
        entries: List[Union[str, Tuple[str, Optional[str]]]],
    ) -> List[Tuple[str, Optional[str]]]:
        """Extract the ordered item tuples, ignoring category header strings.

        Args:
            entries (list): Ordered menu entries.

        Returns:
            list: The ``(label, status)`` item tuples in order.
        """
        return [e for e in entries if not isinstance(e, str)]

    @staticmethod
    def _cell(number: int, label: str, status: Optional[str]) -> Text:
        """Build a single numbered body-grid cell.

        Args:
            number (int): The one-based item number.
            label (str): The item label.
            status (Optional[str]): The optional status tag.

        Returns:
            Text: The styled ``[NN] Label  STATUS`` cell.
        """
        cell = Text()
        cell.append("[{:02d}] ".format(number), style="bold cyan")
        cell.append(label or "", style="white")
        if status:
            cell.append("  " + status, style="dim yellow")
        return cell


def render_submenu(
    title: str,
    subtitle: str = "",
    entries: List[Union[str, Tuple[str, Optional[str]]]] = None,
    border_style: str = "cyan",
    domain: str = "",
    context_shortcuts: str = "",
) -> Group:
    """Build a three-tier Rich sub-menu in a single call.

    Args:
        title (str): Header panel title.
        subtitle (str): Optional descriptive subtitle.
        entries (list): Ordered menu items.
        border_style (str): Rich border colour.
        domain (str): Optional active domain description.
        context_shortcuts (str): Shortcut summary for the navigation footer.

    Returns:
        Group: The three-tier renderable.
    """
    return RichSubmenuRenderer(
        title, subtitle, border_style, domain
    ).build(entries or [], context_shortcuts=context_shortcuts)


__all__ = ["RichSubmenuRenderer", "render_submenu"]
