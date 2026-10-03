# -*- coding: utf-8 -*-
"""
Module: terminal_previewer.py
Project: TALOS v5.22.1
Description:
    In-terminal previewer for the TALOS Scientific Terminal Dashboard. Renders
    Markdown reports (LLM market intelligence, PRISMA syntheses) inside a styled
    Rich Panel, and renders syntax-highlighted source (BibTeX, JSON, Python)
    with line numbers. The previewer performs read-only file access and emits
    pure UTF-8 renderables; it never mutates the filesystem.

Dependencies:
    - pathlib.Path: file path resolution.
    - rich.console.Console, rich.panel.Panel: rendering primitives.
    - rich.markdown.Markdown, rich.syntax.Syntax: the two preview backends.
"""

from pathlib import Path
from typing import Optional, Union

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.syntax import Syntax


class TerminalPreviewer:
    """Preview Markdown and syntax-highlighted files in the terminal.

    Attributes:
        console (Console): The Rich console used for output.
    """

    def __init__(self, console: Optional[Console] = None) -> None:
        """Initialise the previewer with an optional console.

        Args:
            console (Optional[Console]): A Rich console; a fresh one is created
                when omitted.
        """
        self.console = console or Console()

    # ------------------------------------------------------------------
    # -- Markdown ------------------------------------------------------
    # ------------------------------------------------------------------

    def preview_markdown(self, file_path: Union[str, Path]) -> Panel:
        """Render a Markdown file inside a Panel and print it.

        Args:
            file_path: Path to a Markdown file.

        Returns:
            Panel: The rendered Markdown panel.
        """
        panel = self.render_markdown(file_path)
        self.console.print(panel)
        return panel

    def render_markdown(self, file_path: Union[str, Path]) -> Panel:
        """Build (without printing) a Markdown panel for the given file.

        Args:
            file_path: Path to a Markdown file.

        Returns:
            Panel: The Markdown content wrapped in a styled Panel.
        """
        path = Path(file_path)
        text = path.read_text(encoding="utf-8")
        return Panel(
            Markdown(text),
            title=f"[bold]{path.name}[/bold]",
            border_style="bright_cyan",
            padding=(1, 2),
        )

    # ------------------------------------------------------------------
    # -- Syntax --------------------------------------------------------
    # ------------------------------------------------------------------

    def preview_syntax(
        self,
        file_path: Union[str, Path],
        lexer: Optional[str] = None,
    ) -> Union[Panel, Syntax]:
        """Render a syntax-highlighted file and print it.

        Args:
            file_path: Path to the source file.
            lexer: Optional Pygments lexer name. Auto-detected when ``None``.

        Returns:
            The rendered Panel (when lexer explicit) or Syntax renderable.
        """
        renderable = self.render_syntax(file_path, lexer)
        self.console.print(renderable)
        return renderable

    def render_syntax(
        self,
        file_path: Union[str, Path],
        lexer: Optional[str] = None,
    ) -> Union[Panel, Syntax]:
        """Build (without printing) a syntax renderable for the given file.

        Args:
            file_path: Path to the source file.
            lexer: Optional Pygments lexer name. Auto-detected when ``None``.

        Returns:
            Panel (when lexer explicit) or Syntax (auto-detected).
        """
        path = Path(file_path)
        if lexer is None:
            return Syntax.from_path(str(path), line_numbers=True)
        code = path.read_text(encoding="utf-8")
        syntax = Syntax(code, lexer, line_numbers=True)
        return Panel(
            syntax,
            title=f"[bold]{path.name}[/bold]",
            border_style="green",
            padding=(0, 1),
        )
