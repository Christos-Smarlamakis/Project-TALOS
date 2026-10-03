# -*- coding: utf-8 -*-
"""
Module: ai_strategy_selector.py
Project: TALOS v5.20.0
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


def _recommendation_stack() -> dict:
    """Return the hardware-aware dual-slot champion model stack.

    Returns:
        dict: ``get_recommendations()`` payload, or an empty dict on failure.
    """
    try:
        from src.core.hardware_advisor import HardwareModelAdvisor
        return HardwareModelAdvisor().get_recommendations() or {}
    except Exception:
        return {}


def _active_provider_names() -> list:
    """Return the names of currently active providers (cloud keys + Ollama)."""
    try:
        from src.services.cognitive_mesh.registry import get_available_providers
        return [d.name for d in get_available_providers()]
    except Exception:
        return []


def _persist_stack(
    exec_strategy, screening_local, screening_cloud, reasoning_local, reasoning_cloud
) -> bool:
    """Persist the execution strategy and dual-slot model stack to the profile.

    Writes the active profile ``config.json`` atomically in pure UTF-8,
    updating ``ai_execution_strategy``, the ``ai_models`` block, and a new
    ``cognitive_slots`` block (screening_local / screening_cloud /
    reasoning_local / reasoning_cloud).

    Args:
        exec_strategy (str): Canonical ai_execution_strategy key.
        screening_local (str): Local fast-screening model.
        screening_cloud (str): Cloud fast-screening model.
        reasoning_local (str): Local deep-reasoning model.
        reasoning_cloud (str): Cloud deep-reasoning model.

    Returns:
        bool: True when the config was updated and persisted.
    """
    import json
    import os

    try:
        from src.core.profile_manager import ProfileManager
        config_path = ProfileManager().get_active_config_path()
    except Exception:
        return False
    if not config_path:
        return False

    try:
        with open(config_path, "r", encoding="utf-8") as fh:
            config = json.load(fh)
    except Exception:
        config = {}

    config["ai_execution_strategy"] = exec_strategy
    ai_models = config.setdefault("ai_models", {})
    ai_models.setdefault("fast_edge", {})["model"] = screening_local or screening_cloud
    ai_models.setdefault("heavy_reasoning", {})["model"] = reasoning_local or reasoning_cloud
    cloud = ai_models.setdefault("cloud_fallback", {})
    cloud["flash_model"] = screening_cloud
    cloud["pro_model"] = reasoning_cloud
    config["cognitive_slots"] = {
        "screening_local": screening_local,
        "screening_cloud": screening_cloud,
        "reasoning_local": reasoning_local,
        "reasoning_cloud": reasoning_cloud,
    }

    try:
        tmp_path = config_path + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as fh:
            json.dump(config, fh, indent=2, ensure_ascii=False)
        os.replace(tmp_path, config_path)
        return True
    except Exception:
        return False


def _render_apply_confirmation(strategy: str, ok: bool) -> None:
    """Render a Rich confirmation panel for a strategy/champion adoption."""
    style = "green" if ok else "red"
    label = "Applied successfully" if ok else "Failed to persist configuration"
    console.print(Panel(
        Text(f"Strategy: {strategy}\n{label}", style=f"bold {style}"),
        title="[bold]FINOps CONFIGURATION[/bold]",
        border_style=style,
    ))


def apply_optimal_models(strategy: str = "AUTO") -> bool:
    """Adopt champion hybrid models into the active profile headlessly.

    This powers ``python talos.py --apply-optimal-models --strategy ...``.

    Args:
        strategy (str): AUTO | LOCAL_FIRST | CLOUD_BUDGET | FRONTIER. AUTO
            inspects the RTX 4070 VRAM budget and active API keys to select
            LOCAL_FIRST_CLOUD_BACKUP when a cloud key is present, else
            STRICT_LOCAL_AIRGAPPED.

    Returns:
        bool: True when the config was updated and persisted.
    """
    strategy = (strategy or "AUTO").upper()
    recs = _recommendation_stack()
    screening_local = recs.get("screening_local", "qwen2.5:3b")
    screening_cloud = recs.get("screening_cloud", "gemini-2.5-flash")
    reasoning_local = recs.get("reasoning_local", "qwen2.5:14b")
    reasoning_cloud = recs.get("reasoning_cloud", "deepseek-reasoner")

    active = _active_provider_names()
    has_cloud = any(p in active for p in (
        "deepseek", "gemini", "anthropic", "groq", "openrouter", "mistral",
    ))

    if strategy == "LOCAL_FIRST":
        exec_strategy = "local_first"
    elif strategy == "CLOUD_BUDGET":
        exec_strategy = "cloud_first"
        screening_local = ""
        reasoning_local = ""
        screening_cloud = "gemini-2.5-flash"
        reasoning_cloud = "deepseek-chat"
    elif strategy == "FRONTIER":
        exec_strategy = "cloud_first"
        screening_local = ""
        reasoning_local = ""
        screening_cloud = "claude-sonnet-4-5"
        reasoning_cloud = "claude-sonnet-4-5"
    else:  # AUTO_PILOT
        exec_strategy = "local_first" if has_cloud else "strict_local"

    return _persist_stack(
        exec_strategy, screening_local, screening_cloud,
        reasoning_local, reasoning_cloud,
    )


def _render_impact_matrix(recs: dict) -> None:
    """Render the real-time trade-off impact matrix for the four role slots.

    Each slot shows its champion model, deployment class, approximate cost per
    1,000 papers, and a rigor index. The local VRAM budget is reported so users
    can immediately detect over-allocation against the RTX 4070 (12 GB) budget.

    Args:
        recs (dict): The ``get_recommendations()`` payload.
    """
    from rich.table import Table

    profile = recs.get("hardware_profile", {})
    vram_gb = profile.get("total_vram_gb") or 12.0

    table = Table(
        title="Role-Slot Impact Matrix (Cost / 1k papers, TTFT, VRAM, Rigor)",
        header_style="bold bright_cyan",
        border_style="cyan",
    )
    table.add_column("Slot", style="dim cyan")
    table.add_column("Champion Model", style="white")
    table.add_column("Deployment", style="yellow")
    table.add_column("Est. Cost /1k", justify="right")
    table.add_column("Rigor", justify="right")

    slots = [
        ("Screening (local)", recs.get("screening_local", "-"), "LOCAL", "Medium"),
        ("Screening (cloud)", recs.get("screening_cloud", "-"), "CLOUD", "High"),
        ("Reasoning (local)", recs.get("reasoning_local", "-"), "LOCAL", "High"),
        ("Reasoning (cloud)", recs.get("reasoning_cloud", "-"), "CLOUD", "Frontier"),
    ]
    for slot, model, deploy, rigor in slots:
        cost = "0.00" if deploy == "LOCAL" else "~1-6"
        table.add_row(slot, model, deploy, f"${cost}", rigor)

    console.print(table)
    console.print(
        f"[dim]Local VRAM budget: {vram_gb:.1f} GB. Local slots are bounded by "
        f"threading.Semaphore(2); models above the budget must route remotely. "
        f"Cloud slots incur token cost; local slots incur zero marginal cost.[/dim]"
    )


def configure_ai_strategy() -> bool:
    """Launch the Interactive Cognitive FinOps & Strategy Configurator.

    Screen 1 selects an execution mode ([0] AUTO_PILOT or [1-4] manual). Screen
    2 (manual modes) renders the role-slot impact matrix. Screen 3 persists the
    validated configuration to the active profile ``config.json``.

    Returns:
        bool: True when a configuration was persisted.
    """
    console.print(Panel(
        Text(
            "Interactive Cognitive FinOps & Strategy Configurator\n"
            "ISO/IEC 25010: operability, user-error protection, modularity.",
            style="bold bright_cyan",
        ),
        title="[bold]FINOps CONFIGURATOR[/bold]",
        border_style="#006699",
    ))

    # -- Screen 1: execution mode selection --
    choice = questionary.select(
        "Select execution mode:",
        choices=[
            "[0] AUTO_PILOT (Auto-Choose) -- 1-click optimal hybrid strategy",
            "[1] LOCAL_FIRST_CLOUD_BACKUP -- local Ollama with cloud failover",
            "[2] STRICT_LOCAL_AIRGAPPED -- zero outbound egress",
            "[3] CLOUD_COST_OPTIMIZED -- DeepSeek / Groq / Gemini Flash",
            "[4] CLOUD_FRONTIER_RIGOR -- Claude / GPT frontier reasoning",
        ],
        style=TALOS_QUESTIONARY_STYLE,
    ).ask()
    if choice is None:
        console.print("[dim]Configurator cancelled.[/dim]")
        return False

    if choice.startswith("[0]"):
        ok = apply_optimal_models("AUTO")
        _render_apply_confirmation("AUTO_PILOT", ok)
        return ok

    mode = {
        "[1]": "LOCAL_FIRST",
        "[2]": "STRICT_LOCAL",
        "[3]": "CLOUD_BUDGET",
        "[4]": "FRONTIER",
    }.get(choice[:3], "AUTO")

    # -- Screen 2: role-slot impact matrix (champion models pre-selected) --
    recs = _recommendation_stack()
    if recs:
        _render_impact_matrix(recs)

    # -- Screen 3: persist (1-click adoption) --
    ok = apply_optimal_models(mode)
    _render_apply_confirmation(mode, ok)
    return ok


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
