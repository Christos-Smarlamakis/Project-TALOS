# -*- coding: utf-8 -*-
"""
Module: ai_strategy_selector.py
Project: TALOS v5.12.2
Description:
    Lightweight interactive and headless switcher for the TALOS 5-strategy AI
    execution matrix. It exposes the canonical strategy hierarchy
    (strict_local, local_first, cloud_first, strict_cloud, auto_dynamic) and
    persists the selection into config.json ('ai_execution_strategy') and .env
    (TALOS_NETWORK_STRATEGY / TALOS_ALLOW_CLOUD_FALLBACK).

    select_ai_execution_strategy() is shared by the TUI (talos.py main menu and
    Configuration & Profiles sub-menu) and the CLI fast-dispatch flag
    (python talos.py --strategy <mode>). With an explicit target it runs
    headlessly; without one it renders a Questionary prompt using the canonical
    TALOS_QUESTIONARY_STYLE theme.

    Design decision: persistence is delegated to
    research_setup_wizard._apply_execution_strategy() so the selector never
    diverges from the wizard's single source of truth for .env/config.json.

Dependencies:
    - questionary: interactive strategy selection prompt.
    - rich: confirmation panel and header rendering.
    - src.utils.ui_theme: TALOS_QUESTIONARY_STYLE prompt theme.
    - src.utils.research_setup_wizard: EXECUTION_STRATEGIES, _apply_execution_strategy,
      and _load_config (canonical persistence helpers).
"""
import sys

import questionary
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from src.utils.ui_theme import TALOS_QUESTIONARY_STYLE
from src.utils.research_setup_wizard import (
    EXECUTION_STRATEGIES,
    _apply_execution_strategy,
    _load_config,
)

console = Console()

# -- Canonical strategy keys (mirror research_setup_wizard.EXECUTION_STRATEGIES). --
VALID_STRATEGIES = list(EXECUTION_STRATEGIES.keys())


def _current_strategy():
    """Return the currently active ai_execution_strategy key, or None if unset.

    Returns:
        str or None: The active strategy key (e.g. 'strict_local'), or None.
    """
    try:
        config, _ = _load_config()
        return config.get("ai_execution_strategy")
    except Exception:
        return None


def _render_confirmation(strategy_key):
    """Print a clean Rich confirmation panel for the persisted strategy.

    Args:
        strategy_key (str): The canonical strategy key that was applied.
    """
    label = EXECUTION_STRATEGIES.get(strategy_key, {}).get("label", strategy_key)
    console.print(Panel(
        Text(f"AI Execution Strategy set to: {strategy_key}\n{label}",
             style="bold green"),
        title="[bold]STRATEGY UPDATED[/bold]",
        border_style="green",
    ))


def select_ai_execution_strategy(target_strategy=None):
    """Select and persist the AI execution strategy.

    Args:
        target_strategy (str, optional): Canonical strategy key supplied from
            the CLI. When provided it is validated and applied headlessly;
            otherwise an interactive Questionary prompt is rendered.

    Returns:
        bool: True when a strategy was applied, False when cancelled or invalid.
    """
    # -- Headless path: validate and apply an explicit target. --
    if target_strategy is not None:
        if target_strategy not in VALID_STRATEGIES:
            console.print(Panel(
                f"[yellow]Invalid strategy '{target_strategy}'. Valid options: "
                f"{', '.join(VALID_STRATEGIES)}.[/yellow]",
                title="[bold]INVALID STRATEGY[/bold]",
                border_style="yellow",
            ))
            return False
        _apply_execution_strategy(target_strategy)
        _render_confirmation(target_strategy)
        return True

    # -- Interactive path: show the current strategy and prompt for a new one. --
    current = _current_strategy()
    current_label = EXECUTION_STRATEGIES.get(current, {}).get(
        "label", "Not configured")
    console.print(Panel(
        Text(f"Current AI Execution Strategy: {current_label}",
             style="bold bright_cyan"),
        title="[bold]AI Execution Strategy Switcher[/bold]",
        border_style="#006699",
    ))

    choice = questionary.select(
        "Select AI execution strategy:",
        choices=[s["label"] for s in EXECUTION_STRATEGIES.values()],
        style=TALOS_QUESTIONARY_STYLE,
    ).ask()
    if choice is None:
        console.print("[dim]Strategy switch cancelled.[/dim]")
        return False

    for key, strategy in EXECUTION_STRATEGIES.items():
        if strategy["label"] == choice:
            _apply_execution_strategy(key)
            _render_confirmation(key)
            return True
    return False


if __name__ == "__main__":
    # Standalone entry point: python src/utils/ai_strategy_selector.py [--strategy <mode>]
    target = None
    argv = sys.argv[1:]
    for i, arg in enumerate(argv):
        if arg in ("--strategy", "--mode"):
            if i + 1 < len(argv) and not argv[i + 1].startswith("--"):
                target = argv[i + 1]
            break
    ok = select_ai_execution_strategy(target)
    sys.exit(0 if ok else 1)
