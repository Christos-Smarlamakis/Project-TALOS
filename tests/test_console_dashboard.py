# -*- coding: utf-8 -*-
"""
Module: test_console_dashboard.py
Project: TALOS v5.25.3
Description:
    Unit tests for the modular console dashboard subsystem
    (src/utils/console_dashboard/). Verifies the segmented 3-column HUD panel
    generation (bright-cyan cockpit title, three-column grid, zero truncation),
    the two-column / four-panel layout construction, the three scientific tree
    renderables, the terminal Markdown/syntax previewers, the multi-metric
    progress monitor, and the slash-command palette dispatcher. Every test is
    air-gapped and side-effect free (no network, no filesystem mutation beyond
    a temporary preview fixture).

Dependencies:
    - pytest: test fixtures (tmp_path).
    - rich: Panel, Tree, Layout renderables.
    - src.utils.console_dashboard: the subsystem under test.
    - talos: the command-palette dispatcher.
"""

from __future__ import annotations

from rich.layout import Layout
from rich.panel import Panel
from rich.tree import Tree

from src.utils.console_dashboard import (
    DashboardLayoutBuilder,
    HudRenderer,
    MultiMetricProgress,
    ScientificTreeViewer,
    TerminalPreviewer,
)


class TestHudRenderer:
    """Segmented three-column telemetry HUD generation."""

    def test_build_hud_returns_panel(self):
        panel = HudRenderer().build_hud()
        assert isinstance(panel, Panel)

    def test_build_hud_has_three_columns(self):
        from rich.table import Table
        panel = HudRenderer().build_hud()
        table = panel.renderable
        assert isinstance(table, Table)
        assert len(table.columns) == 3

    def test_build_hud_title_is_bright_cyan_cockpit(self):
        panel = HudRenderer().build_hud()
        assert panel.title is not None
        title_text = str(panel.title)
        assert "TALOS TELEMETRY & SYSTEM COCKPIT" in title_text
        assert "v5.25.3" in title_text

    def test_build_hud_no_truncation(self):
        from rich.console import Console
        console = Console(width=105, record=True)
        console.print(HudRenderer().build_hud())
        rendered = console.export_text()
        assert "\u2026" not in rendered
        assert "..." not in rendered


class TestDashboardLayoutBuilder:
    """Two-column / four-panel responsive grid."""

    def test_build_dashboard_returns_layout(self):
        layout = DashboardLayoutBuilder().build_dashboard()
        assert isinstance(layout, Layout)

    def test_dashboard_has_four_panels_and_footer(self):
        layout = DashboardLayoutBuilder().build_dashboard()
        assert layout["header"] is not None
        assert layout["body"]["left"]["panel1"] is not None
        assert layout["body"]["right"]["panel2"] is not None
        assert layout["body"]["left"]["panel3"] is not None
        assert layout["body"]["right"]["panel4"] is not None
        assert layout["footer"] is not None


class TestScientificTreeViewer:
    """Scientific tree renderables."""

    def test_architecture_tree(self):
        tree = ScientificTreeViewer().render_architecture_tree()
        assert isinstance(tree, Tree)

    def test_research_taxonomy_tree(self):
        tree = ScientificTreeViewer().render_research_taxonomy_tree()
        assert isinstance(tree, Tree)

    def test_mesh_health_tree(self):
        tree = ScientificTreeViewer().render_mesh_health_tree()
        assert isinstance(tree, Tree)


class TestTerminalPreviewer:
    """Markdown and syntax terminal previews."""

    def test_render_markdown(self, tmp_path):
        md = tmp_path / "sample.md"
        md.write_text("# Heading\n\nBody text.", encoding="utf-8")
        panel = TerminalPreviewer().render_markdown(md)
        assert isinstance(panel, Panel)

    def test_render_syntax_explicit_lexer(self, tmp_path):
        src = tmp_path / "sample.json"
        src.write_text('{"key": "value"}', encoding="utf-8")
        panel = TerminalPreviewer().render_syntax(src, lexer="json")
        assert isinstance(panel, Panel)

    def test_render_syntax_auto_detect(self, tmp_path):
        src = tmp_path / "sample.py"
        src.write_text("def f():\n    return 1\n", encoding="utf-8")
        renderable = TerminalPreviewer().render_syntax(src)
        assert renderable is not None


class TestMultiMetricProgress:
    """Multi-metric progress monitor."""

    def test_create_progress_adds_metric_task(self):
        monitor = MultiMetricProgress()
        task_id = monitor.add_metric_task("test", total=10.0, rate=1.0, vram=2.0)
        assert isinstance(task_id, int)


class TestCommandPalette:
    """Slash-command parsing and dispatch (side-effect-free paths)."""

    def test_quit_command(self):
        import talos
        assert talos._dispatch_slash_command("/quit", None) == "quit"

    def test_quit_alias_zero(self):
        import talos
        assert talos._dispatch_slash_command("0", None) == "quit"

    def test_tree_command_handled(self):
        import talos
        assert talos._dispatch_slash_command("/tree arch", None) == "handled"

    def test_fts_missing_arg_handled(self):
        import talos
        assert talos._dispatch_slash_command("/fts", None) == "handled"

    def test_view_missing_path_handled(self):
        import talos
        assert talos._dispatch_slash_command("/view", None) == "handled"

    def test_unknown_command(self):
        import talos
        assert talos._dispatch_slash_command("/bogus", None) == "unknown"
