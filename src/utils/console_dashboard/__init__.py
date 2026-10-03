# -*- coding: utf-8 -*-
"""
Module: __init__.py
Project: TALOS v5.22.1
Description:
    Public entry point for the modular console dashboard subsystem that powers
    the TALOS Scientific Terminal Dashboard (HMI). Re-exports the five
    canonical renderers -- the persistent telemetry HUD, the two-column layout
    builder, the scientific tree viewer, the multi-metric progress monitor, and
    the terminal previewer -- so that ``talos.py`` and external consumers import
    from a single, stable namespace. Keeping the dashboard in this dedicated
    package (Constitution III, strict modularity) isolates all Rich rendering
    logic from the orchestration and routing concerns of the top-level entry
    point.

Dependencies:
    - hud_renderer: HudRenderer (persistent telemetry HUD panel).
    - layout_builder: DashboardLayoutBuilder (2-column / 4-panel grid).
    - tree_views: ScientificTreeViewer (architecture / taxonomy / mesh trees).
    - progress_monitors: MultiMetricProgress, create_scientific_progress.
    - terminal_previewer: TerminalPreviewer (Markdown and syntax previews).
"""

from .hud_renderer import HudRenderer
from .layout_builder import DashboardLayoutBuilder
from .submenu_renderer import RichSubmenuRenderer, render_submenu
from .tree_views import ScientificTreeViewer
from .progress_monitors import MultiMetricProgress, create_scientific_progress
from .terminal_previewer import TerminalPreviewer

__all__ = [
    "HudRenderer",
    "DashboardLayoutBuilder",
    "RichSubmenuRenderer",
    "render_submenu",
    "ScientificTreeViewer",
    "MultiMetricProgress",
    "create_scientific_progress",
    "TerminalPreviewer",
]
