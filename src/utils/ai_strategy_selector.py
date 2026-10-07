# -*- coding: utf-8 -*-
"""
Module: ai_strategy_selector.py
Project: TALOS v5.25.3
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
    from src.utils.console_dashboard import RichSubmenuRenderer
    renderer = RichSubmenuRenderer(
        "AI Execution Strategy Switcher",
        f"Current AI Execution Strategy: {current_label}",
        border_style="#006699",
        domain="AI Models, Strategy & Cost Control Domain",
    )
    labels = [s["label"] for s in EXECUTION_STRATEGIES.values()]
    console.print(renderer.build(entries=[(label, None) for label in labels]))
    choice = renderer.prompt_choice((1, len(labels)), default="01")
    if choice in ("00", "q"):
        console.print("[dim]Strategy switch cancelled.[/dim]")
        return False

    keys = list(EXECUTION_STRATEGIES.keys())
    key = keys[int(choice) - 1]
    _apply_execution_strategy(key)
    _render_confirmation(key)
    return True


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


# ---------------------------------------------------------------------------
# -- Interactive Model Candidate Selector (v5.25.3) --
# ---------------------------------------------------------------------------

_VRAM_LOOKUP = {
    "qwen2.5:14b": 9.0,
    "qwen2.5-coder:14b": 9.0,
    "qwen2.5:3b": 2.5,
    "qwen2.5:7b": 5.0,
    "llama3.1:8b": 5.5,
    "llama3.1:70b": 40.0,
    "llama-3.3-70b-versatile": 40.0,
    "nomic-embed-text": 0.3,
    "fermionresearch/Neutrino-8B": 5.5,
}


def _estimate_vram(model_name, provider):
    """Estimate the VRAM footprint of a model in GB (local) or None (cloud).

    Args:
        model_name (str): Model identifier.
        provider (str): Provider key ('ollama' for local, otherwise cloud).

    Returns:
        float or None: Estimated VRAM in GB, or None for cloud models.
    """
    if provider != "ollama":
        return None
    if model_name in _VRAM_LOOKUP:
        return _VRAM_LOOKUP[model_name]
    import re as _re
    match = _re.search(r"(\d+(?:\.\d+)?)b", (model_name or "").lower())
    if match:
        params_b = float(match.group(1))
        return round(params_b * 0.65, 1)
    return None


def _rigor_band(mmlu_pro, human_eval):
    """Map benchmark scores to a descriptive rigor band.

    Args:
        mmlu_pro (float): MMLU-Pro score (or None).
        human_eval (float): HumanEval score (or None).

    Returns:
        str: One of 'Frontier', 'High', 'Medium', 'Low', or '-'.
    """
    score = mmlu_pro if mmlu_pro is not None else human_eval
    if score is None:
        return "-"
    if score >= 85:
        return "Frontier"
    if score >= 75:
        return "High"
    if score >= 60:
        return "Medium"
    return "Low"


def _load_benchmark_records():
    """Load candidate model records from the air-gapped benchmark cache.

    Returns:
        list[dict]: Benchmark records with model, provider, roles, and metrics.
    """
    import json
    import os

    project_root = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )
    path = os.path.join(project_root, "data", "cache", "llm_benchmarks.json")
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        return data.get("records", [])
    except Exception:
        return []


def _get_candidates_for_slot(slot_name, strategy):
    """Return enriched candidate models for a role slot.

    Queries ``data/cache/llm_benchmarks.json`` and enriches each record with
    VRAM, cost-per-1k, TTFT, and rigor metrics for a candidate table.

    Args:
        slot_name (str): One of 'screening_local', 'screening_cloud',
            'reasoning_local', 'reasoning_cloud'.
        strategy (str): The selected execution mode (used to bias ordering).

    Returns:
        list[dict]: Candidate dicts with keys name, provider, vram_gb,
            cost_per_1k_usd, ttft_ms, rigor.
    """
    records = _load_benchmark_records()
    role = "fast_screening" if slot_name.startswith("screening") else "rigorous_audit"
    deployment = "ollama" if slot_name.endswith("_local") else "cloud"

    candidates = []
    for r in records:
        provider = (r.get("provider") or "").lower()
        roles = r.get("roles") or []
        if role not in roles:
            continue
        is_local = provider == "ollama"
        if deployment == "ollama" and not is_local:
            continue
        if deployment == "cloud" and is_local:
            continue
        cost_1m = r.get("cost_per_1m_usd")
        candidates.append({
            "name": r.get("model", "?"),
            "provider": provider,
            "vram_gb": _estimate_vram(r.get("model"), provider),
            "cost_per_1k_usd": round(cost_1m / 1000, 4) if cost_1m is not None else None,
            "ttft_ms": r.get("ttft_ms"),
            "rigor": _rigor_band(r.get("mmlu_pro"), r.get("human_eval")),
        })

    if strategy in ("CLOUD_BUDGET", "LOCAL_FIRST"):
        candidates.sort(key=lambda c: (c["cost_per_1k_usd"] is None, c["cost_per_1k_usd"] or 0))
    elif strategy == "FRONTIER":
        order = {"Frontier": 0, "High": 1, "Medium": 2, "Low": 3, "-": 4}
        candidates.sort(key=lambda c: order.get(c["rigor"], 4))

    return candidates


def _render_candidate_table(candidates, slot_name):
    """Render a Rich candidate table with VRAM, Cost/1k, TTFT, and Rigor.

    Args:
        candidates (list[dict]): Candidate model dicts.
        slot_name (str): The role slot label.
    """
    from rich.table import Table

    table = Table(
        title=f"Candidate Models -- {slot_name}",
        header_style="bold bright_cyan",
        border_style="cyan",
    )
    table.add_column("#", style="dim", width=3, justify="right")
    table.add_column("Model", style="white")
    table.add_column("Provider", style="cyan")
    table.add_column("VRAM", justify="right", style="yellow")
    table.add_column("Cost/1k", justify="right", style="magenta")
    table.add_column("TTFT", justify="right", style="green")
    table.add_column("Rigor", justify="right", style="bold")

    for idx, c in enumerate(candidates, start=1):
        vram = f"{c['vram_gb']}GB" if c["vram_gb"] is not None else "N/A"
        cost = f"${c['cost_per_1k_usd']:.4f}" if c["cost_per_1k_usd"] is not None else "$0.0000"
        ttft = f"{c['ttft_ms']}ms" if c["ttft_ms"] is not None else "-"
        table.add_row(str(idx), c["name"], c["provider"], vram, cost, ttft, c["rigor"])

    console.print(table)


def _prompt_candidate_selection(candidates, slot_name, champion):
    """Prompt the user to pick a candidate by number or accept the champion.

    Args:
        candidates (list[dict]): Candidate model dicts.
        slot_name (str): The role slot label.
        champion (str): Default champion model name (ENTER accepts it).

    Returns:
        str: The selected model name (or champion when ENTER pressed).
    """
    from rich.prompt import Prompt

    if not candidates:
        console.print(f"[yellow]No candidates for {slot_name}. Using champion.[/yellow]")
        return champion

    _render_candidate_table(candidates, slot_name)

    default_idx = None
    for idx, c in enumerate(candidates, start=1):
        if c["name"] == champion:
            default_idx = idx
            break
    default_token = str(default_idx) if default_idx else "1"

    console.print(
        f"[dim]Champion default: [bold]{champion}[/bold] "
        f"(press ENTER to accept).[/dim]"
    )
    while True:
        try:
            raw = (Prompt.ask(
                f"Pick model [01-{len(candidates):02d}] "
                f"(ENTER = champion: {default_token})",
                default=default_token,
            ) or "").strip()
        except (KeyboardInterrupt, EOFError):
            return champion
        if not raw:
            raw = default_token
        if raw.isdigit():
            num = int(raw)
            if 1 <= num <= len(candidates):
                return candidates[num - 1]["name"]
        console.print("[yellow]Invalid selection. Enter a number or press ENTER.[/yellow]")


def _strategy_key(mode):
    """Map an execution mode label to its canonical ai_execution_strategy key.

    Args:
        mode (str): One of LOCAL_FIRST, STRICT_LOCAL, CLOUD_BUDGET, FRONTIER.

    Returns:
        str: The canonical ai_execution_strategy key.
    """
    return {
        "LOCAL_FIRST": "local_first",
        "STRICT_LOCAL": "strict_local",
        "CLOUD_BUDGET": "cloud_first",
        "FRONTIER": "cloud_first",
    }.get(mode, "local_first")


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
        title="[bold]AI MODEL & COST OPTIMIZATION[/bold]",
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
    """Launch the Interactive AI Model Selector & Cost Optimizer.

    Screen 1 selects an execution mode ([1] AUTO_PILOT or [2-5] manual). For
    manual modes, four sequential child steps render candidate tables for the
    Screening (local), Screening (cloud), Reasoning (local), and Reasoning
    (cloud) slots -- each with VRAM, Cost/1k, TTFT, and Rigor -- letting the
    user pick by number or press ENTER for the champion default. A final step
    renders the customized matrix and persists to the active profile.

    Returns:
        bool: True when a configuration was persisted.
    """
    console.print(Panel(
        Text(
            "Interactive AI Model Selector & Cost Optimizer\n"
            "ISO/IEC 25010: operability, user-error protection, modularity.",
            style="bold bright_cyan",
        ),
        title="[bold]AI MODEL SELECTOR & COST OPTIMIZER[/bold]",
        border_style="#006699",
    ))

    # -- Screen 1: execution mode selection --
    from src.utils.console_dashboard import RichSubmenuRenderer
    mode_labels = [
        "AUTO_PILOT (Auto-Choose) -- 1-click optimal hybrid strategy",
        "LOCAL_FIRST_CLOUD_BACKUP -- local Ollama with cloud failover",
        "STRICT_LOCAL_AIRGAPPED -- zero outbound egress",
        "CLOUD_COST_OPTIMIZED -- DeepSeek / Groq / Gemini Flash",
        "CLOUD_FRONTIER_RIGOR -- Claude / GPT frontier reasoning",
    ]
    renderer = RichSubmenuRenderer(
        "Select Execution Mode",
        "ISO/IEC 25010: operability, user-error protection, modularity.",
        border_style="#006699",
        domain="AI Models, Strategy & Cost Control Domain",
    )
    console.print(renderer.build(entries=[(label, None) for label in mode_labels]))
    choice = renderer.prompt_choice((1, 5), default="01")
    if choice in ("00", "q"):
        console.print("[dim]Configurator cancelled.[/dim]")
        return False

    num = int(choice)
    if num == 1:
        # -- AUTO_PILOT: instant 1-click champion adoption. --
        ok = apply_optimal_models("AUTO")
        _render_apply_confirmation("AUTO_PILOT", ok)
        return ok

    mode = {
        2: "LOCAL_FIRST",
        3: "STRICT_LOCAL",
        4: "CLOUD_BUDGET",
        5: "FRONTIER",
    }[num]

    # -- Screen 2: step-by-step role-slot customization (4 child steps). --
    recs = _recommendation_stack()
    champions = {
        "screening_local": recs.get("screening_local", "qwen2.5:3b"),
        "screening_cloud": recs.get("screening_cloud", "gemini-2.5-flash"),
        "reasoning_local": recs.get("reasoning_local", "qwen2.5:14b"),
        "reasoning_cloud": recs.get("reasoning_cloud", "deepseek-reasoner"),
    }
    slot_labels = {
        "screening_local": "Screening (local)",
        "screening_cloud": "Screening (cloud)",
        "reasoning_local": "Reasoning (local)",
        "reasoning_cloud": "Reasoning (cloud)",
    }

    selected = {}
    for slot in ("screening_local", "screening_cloud", "reasoning_local", "reasoning_cloud"):
        candidates = _get_candidates_for_slot(slot, mode)
        champion = champions[slot]
        # -- Prepend the champion when it is absent from the candidate list. --
        if champion and all(c["name"] != champion for c in candidates):
            candidates.insert(0, {
                "name": champion,
                "provider": "ollama" if slot.endswith("_local") else "cloud",
                "vram_gb": _estimate_vram(champion, "ollama" if slot.endswith("_local") else "cloud"),
                "cost_per_1k_usd": 0.0 if slot.endswith("_local") else None,
                "ttft_ms": None,
                "rigor": "Champion",
            })
        selected[slot] = _prompt_candidate_selection(candidates, slot_labels[slot], champion)

    # -- Screen 3: render the customized matrix and persist. --
    custom_stack = {
        "screening_local": selected["screening_local"],
        "screening_cloud": selected["screening_cloud"],
        "reasoning_local": selected["reasoning_local"],
        "reasoning_cloud": selected["reasoning_cloud"],
        "hardware_profile": recs.get("hardware_profile", {}),
    }
    _render_impact_matrix(custom_stack)

    ok = _persist_stack(
        _strategy_key(mode),
        selected["screening_local"],
        selected["screening_cloud"],
        selected["reasoning_local"],
        selected["reasoning_cloud"],
    )
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
