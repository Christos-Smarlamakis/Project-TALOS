# -*- coding: utf-8 -*-
#  Project TALOS
#  Copyright (C) 2026 Christos Smarlamakis
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Affero General Public License as
#  published by the Free Software Foundation, either version 3 of the
#  License, or (at your option) any later version.
#
#  For commercial licensing, please contact the author.
"""
Module: model_manager.py
Project: TALOS v5.10.15
Description:
    Interactive TUI for configuring all LLM tiers (Fast Edge CPU, Heavy Reasoning GPU,
    Cloud API) and setting the 2D Execution Matrix (Network Strategy & Hardware Strategy).
    Supports Ollama model selection with quantization-aware sizing, plus the
    Universal Cloud Mesh provider registry (Gemini primary + 8-provider
    OpenAI-compatible redundancy cascade) for cloud configuration.

    Key design decisions:
    - Multi-tier architecture: Fast Edge Tier (port 11435, CPU-optimized), Heavy
      Reasoning Tier (port 11434, GPU-optimized), Cloud API Tier (Gemini/DeepSeek/HF).
    - v5.9.4: 2D Execution Matrix replaces the old TALOS_EXECUTION_MODE with
      TALOS_NETWORK_STRATEGY (strict_local, local_first, cloud_first, strict_cloud)
      and TALOS_HARDWARE_STRATEGY (cpu_only, gpu_only, cpu_gpu_split).
    - All network-dependent operations check Ollama reachability first via
      check_ollama_alive() and degrade gracefully.
    - Zero-emojis protocol enforced: all status indicators use formal text badges.
    - Rich library used for structured Panels, Tables, and user feedback.
    - Navigation safety locks: explicit Cancel/Back in all sub-menus.
    - Confirmation panel before any .env write operation.
    - Path resolution uses config/settings.py constants where available.

Dependencies:
    - os, sys, subprocess, time: Standard library utilities.
    - requests: HTTP calls to Ollama REST API.
    - questionary: Interactive terminal selection menus.
    - dotenv: Reading and writing .env key-value pairs.
    - rich: Terminal UI formatting (Console, Panel, Table, Box).
    - src.core.hardware: GPU detection, model sizing, VRAM recommendations.
    - config.settings: Canonical environment variable keys and defaults.
"""
import os
import sys
import subprocess
import time
import requests
import questionary
from src.utils.ui_theme import TALOS_QUESTIONARY_STYLE

from dotenv import dotenv_values, set_key as _set_key

# -- Rich TUI imports (v5.8.6) --
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box
from rich.text import Text

# -- Project root resolution via pathlib (clean, no sys.path hacks) --
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
_ENV_PATH = str(_PROJECT_ROOT / ".env")

# -- Rich Console instance for all TUI output --
console = Console()

# -- Import hardware utilities (project root is already in sys.path via talos.py launcher) --
from src.core.hardware import (
    detect_vram_gb,
    get_all_chat_models_sorted,
    get_ollama_library_models,
    get_bitnet_models,
    estimate_size_for_quant,
    VRAM_HEADROOM,
    pull_model as hw_pull_model,
)

# -- Cloud provider defaults from the canonical settings hub --
from config.settings import (
    TALOS_VERSION,
    GEMINI_FLASH_MODEL as DEFAULT_GEMINI_FLASH,
    GEMINI_PRO_MODEL as DEFAULT_GEMINI_PRO,
    DEEPSEEK_MODEL_CHAT as DEFAULT_DEEPSEEK_MODEL,
    DEEPSEEK_BASE_URL,
    HF_MODEL_NAME as DEFAULT_HF_MODEL,
    HF_BASE_URL,
    NVIDIA_DEFAULT_MODEL as DEFAULT_NVIDIA_MODEL,
    NVIDIA_BASE_URL,
    GROQ_DEFAULT_MODEL as DEFAULT_GROQ_MODEL,
    GROQ_BASE_URL,
    CEREBRAS_DEFAULT_MODEL as DEFAULT_CEREBRAS_MODEL,
    CEREBRAS_BASE_URL,
    GITHUB_MODELS_DEFAULT_MODEL as DEFAULT_GITHUB_MODEL,
    GITHUB_MODELS_BASE_URL,
    MISTRAL_DEFAULT_MODEL as DEFAULT_MISTRAL_MODEL,
    MISTRAL_BASE_URL,
    OPENROUTER_DEFAULT_MODEL as DEFAULT_OPENROUTER_MODEL,
    OPENROUTER_BASE_URL,
)


# ---------------------------------------------------------------------------
# -- Helper Functions --
# ---------------------------------------------------------------------------

def get_ollama_base():
    """Return the Ollama base URL from env or default."""
    return os.getenv("LOCAL_MODEL_BASE_URL", "http://localhost:11434").rstrip("/v1").rstrip("/")


def check_ollama_alive():
    """Check if Ollama server is reachable at its configured base URL.

    Returns:
        bool: True if the /api/tags endpoint responds with HTTP 200.
    """
    base = get_ollama_base()
    try:
        r = requests.get(f"{base}/api/tags", timeout=5)
        return r.status_code == 200
    except Exception:
        return False


def get_installed_models():
    """Return list of installed model names from Ollama.

    Returns:
        list[str]: Model names in "name:tag" format, or empty list on failure.
    """
    base = get_ollama_base()
    try:
        r = requests.get(f"{base}/api/tags", timeout=10)
        if r.status_code != 200:
            return []
        models = r.json().get("models", [])
        return [m["name"] for m in models]
    except Exception:
        return []


def get_available_tags(model_name):
    """Fetch all available quantization tags for a model via ollama show.

    Parses the output of 'ollama show <model>' to extract tag names and their
    reported sizes. Handles GB and MB units.

    Args:
        model_name: Model identifier, optionally with a tag suffix (e.g., 'qwen2.5:14b').

    Returns:
        list[dict]: Each dict has keys: tag, size_gb, full_name.
    """
    base_name = model_name.split(":")[0] if ":" in model_name else model_name
    try:
        result = subprocess.run(
            ["ollama", "show", base_name],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode != 0:
            return []
        output = result.stdout

        tags = []
        in_tags = False
        for line in output.splitlines():
            line = line.strip()
            if "Tags:" in line:
                in_tags = True
                continue
            if in_tags and line and not line.startswith("---") and not line.startswith("License"):
                parts = line.split()
                if len(parts) >= 2:
                    tag = parts[0]
                    try:
                        size_str = parts[1]
                        if "GB" in size_str.upper():
                            size_val = float(size_str.upper().replace("GB", "").strip())
                        elif "MB" in size_str.upper():
                            size_val = float(size_str.upper().replace("MB", "").strip()) / 1024
                        else:
                            size_val = float(size_str)
                        tags.append({
                            "tag": tag,
                            "size_gb": round(size_val, 1),
                            "full_name": f"{base_name}:{tag}",
                        })
                    except ValueError:
                        pass
            elif in_tags and (line.startswith("---") or line.startswith("License")):
                break

        return tags
    except Exception:
        return []


def get_quantized_variants(model_base_name):
    """Discover quantized variants of a model by calling ollama show.

    Falls back through three tiers:
    1. Structured tag listing from 'ollama show'.
    2. Already-installed variants matching the base name.
    3. Common quantization tags (q8_0, q4_K_M, q4_0, q2_K, q1_0) as a last resort.

    Args:
        model_base_name: Base model name without tag (e.g., 'qwen2.5').

    Returns:
        dict: Categories keyed by bit-depth label, each containing a list of variant dicts.
    """
    base = model_base_name.split(":")[0] if ":" in model_base_name else model_base_name
    installed_full = get_installed_models()

    # -- Tier 1: structured tags from ollama show --
    detailed_tags = get_available_tags(base)
    if detailed_tags:
        return _categorize_tags(detailed_tags, base, installed_full)

    # -- Tier 2: installed variants with matching base name --
    variants = []
    for full_name in installed_full:
        if full_name.startswith(base + ":"):
            tag = full_name.split(":", 1)[1]
            variants.append({
                "tag": tag,
                "size_gb": None,
                "full_name": full_name,
            })

    if variants:
        return _categorize_tags(variants, base, installed_full)

    # -- Tier 3: common quantization fallback --
    common_tags = ["q8_0", "q4_K_M", "q4_0", "q2_K", "q1_0"]
    for tag in common_tags:
        variants.append({
            "tag": tag,
            "size_gb": None,
            "full_name": f"{base}:{tag}",
        })

    return _categorize_tags(variants, base, installed_full)


def _categorize_tags(tags, base, installed_full):
    """Categorize quantization tags into bit-depth groups and mark installed status.

    Args:
        tags: List of dicts with keys tag, size_gb, full_name.
        base: Base model name.
        installed_full: List of fully qualified installed model names.

    Returns:
        dict: Only non-empty categories are included. Each category maps to a list
              of dicts with keys: full_name, tag, size_gb, installed.
    """
    result = {
        "8-bit (Q8)": [],
        "6-bit (Q6)": [],
        "4-bit (Q4)": [],
        "3-bit (Q3/Q2)": [],
        "2-bit (Q2)": [],
        "1-bit (Q1)": [],
        "Other / No tag": [],
    }

    for t in tags:
        tag = t.get("tag", "")
        full = t.get("full_name", f"{base}:{tag}" if tag else base)
        size = t.get("size_gb")
        is_installed = full in installed_full

        entry = {
            "full_name": full,
            "tag": tag,
            "size_gb": size,
            "installed": is_installed,
        }

        tag_lower = tag.lower()
        if "q8" in tag_lower or "q_8" in tag_lower:
            result["8-bit (Q8)"].append(entry)
        elif "q6" in tag_lower:
            result["6-bit (Q6)"].append(entry)
        elif "q5" in tag_lower:
            result["4-bit (Q4)"].append(entry)  # Q5 grouped with Q4
        elif "q4" in tag_lower or "q_4" in tag_lower:
            result["4-bit (Q4)"].append(entry)
        elif "q3" in tag_lower or "q_3" in tag_lower:
            result["3-bit (Q3/Q2)"].append(entry)
        elif "q2" in tag_lower or "q_2" in tag_lower:
            result["2-bit (Q2)"].append(entry)
        elif "q1" in tag_lower or "q_1" in tag_lower:
            result["1-bit (Q1)"].append(entry)
        else:
            result["Other / No tag"].append(entry)

    return {k: v for k, v in result.items() if v}


def pull_model(full_name):
    """Pull a model from Ollama with real-time progress.

    Args:
        full_name: Fully qualified model name (e.g., 'gemma3:12b').

    Returns:
        bool: True if the pull succeeded, False otherwise.
    """
    console.print(f"\n  [bold cyan]Downloading[/] [white]{full_name}[/] [dim]via ollama pull...[/]")
    console.print("  [dim](This may take several minutes depending on size)[/]\n")
    try:
        result = subprocess.run(
            ["ollama", "pull", full_name],
            check=False
        )
        if result.returncode == 0:
            console.print(f"\n  [bold green][[SUCCESS]][/] [white]{full_name}[/] installed successfully.")
            return True
        else:
            console.print(f"\n  [bold red][[FAILED]][/] Failed to pull {full_name}. Exit code: {result.returncode}")
            return False
    except FileNotFoundError:
        console.print("\n  [bold red][[ERROR]][/] ollama command not found. Is Ollama installed?")
        return False
    except Exception as e:
        console.print(f"\n  [bold red][[ERROR]][/] Pulling model: {e}")
        return False


# ---------------------------------------------------------------------------
# -- Model Catalogues (cloud provider model lists) --
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# -- Universal Model Provisioner integration (v5.10.5) --
# ---------------------------------------------------------------------------

def _provision_model(model_name):
    """Provision an uninstalled model via the appropriate delivery protocol.

    Ollama models use the interactive `pull_model()` with real-time progress.
    HuggingFace Hub and cloud models are delegated to the Universal Model
    Provisioner with Rich status feedback.

    Args:
        model_name (str): Fully qualified model name to provision.

    Returns:
        bool: True when the model became available, False otherwise.
    """
    try:
        from src.utils.model_provisioner import ModelProvisioner
    except ImportError:
        ModelProvisioner = None

    protocol = ModelProvisioner().detect_protocol(model_name) if ModelProvisioner else "ollama"
    if protocol == "ollama":
        return pull_model(model_name)

    with console.status(
        f"[bold cyan]Provisioning[/] [white]{model_name}[/] [dim]({protocol})[/] ...",
        spinner="dots",
    ):
        return ModelProvisioner().ensure_model_available(model_name, silent=True)


GEMINI_MODELS = [
    ("gemini-2.5-flash-lite", "Fast, lightweight (free tier)"),
    ("gemini-2.5-flash", "Fast, balanced"),
    ("gemini-2.5-pro", "Most capable, slower (free tier limited)"),
    ("gemini-2.0-flash", "Previous gen flash"),
    ("gemini-1.5-flash-latest", "Stable flash"),
    ("gemini-1.5-pro-latest", "Stable pro"),
]

DEEPSEEK_MODELS = [
    ("deepseek-v4-pro", "V4 Pro (cognitive integration, thinking enabled)"),
    ("deepseek-v4-flash", "V4 Flash (fast cognitive tier)"),
    ("deepseek-chat", "General purpose (cheapest)"),
    ("deepseek-reasoner", "Advanced reasoning (R1, more expensive)"),
]

HF_MODELS = [
    "mistralai/Mixtral-8x7B-Instruct-v0.1",
    "meta-llama/Llama-3.1-8B-Instruct",
    "Qwen/Qwen2.5-7B-Instruct",
    "mistralai/Mistral-7B-Instruct-v0.3",
    "microsoft/Phi-3-mini-4k-instruct",
    "google/gemma-2-2b-it",
]


# ---------------------------------------------------------------------------
# -- VRAM Fitness Indicator (Zero-Emojis -- text badges only) --
# ---------------------------------------------------------------------------

def _fits_label(fits, size_gb, vram_limit):
    """Return a formal text badge indicating whether a model fits in VRAM.

    Args:
        fits: Boolean indicating whether the model fits within headroom.
        size_gb: Model size in GB.
        vram_limit: Available VRAM after headroom deduction.

    Returns:
        str: One of ' [FITS]', ' [TIGHT]', ' [TOO BIG]', or empty string.
    """
    if not size_gb or not vram_limit:
        return ""
    ratio = size_gb / vram_limit if vram_limit > 0 else 999
    if ratio <= 0.7:
        return " [FITS]"
    elif ratio <= 1.0:
        return " [TIGHT]"
    else:
        return " [TOO BIG]"


# ---------------------------------------------------------------------------
# -- Confirmation Safety Lock (v5.8.6 -- NEW) --
# ---------------------------------------------------------------------------

def _confirm_setting_change(env_path, key_name, old_value, new_value):
    """Display a Rich confirmation panel before writing a .env key change.

    Constructs a styled Panel summarizing the pending change with the setting
    name, previous value, and proposed new value. Prompts the user for
    confirmation before applying the change.

    Args:
        env_path: Absolute path to the .env file (unused in panel, passed through
                  for caller context consistency).
        key_name: The .env key being modified (e.g., 'FAST_EDGE_MODEL').
        old_value: The current value (before the proposed change).
        new_value: The proposed new value.

    Returns:
        bool: True if the user confirmed the change, False otherwise.
    """
    # -- Build the confirmation table --
    table = Table(box=box.ROUNDED, show_header=True, header_style="bold white")
    table.add_column("Setting", style="cyan", no_wrap=True)
    table.add_column("Previous Value", style="dim yellow")
    table.add_column("Proposed Value", style="bold green")

    table.add_row(key_name, str(old_value) if old_value else "(empty)", str(new_value))

    # -- Wrap in a Panel --
    panel = Panel(
        table,
        title="[bold]Confirm Environment Change[/]",
        title_align="left",
        border_style="yellow",
        box=box.ROUNDED,
        padding=(1, 2),
    )
    console.print()
    console.print(panel)

    # -- Confirm with user --
    confirmed = questionary.confirm(
        "Apply this change to environment?",
        default=True,
        style=TALOS_QUESTIONARY_STYLE,
    ).ask()

    if confirmed:
        console.print(f"  [bold green][[CONFIRMED]][/] Change applied.")
    else:
        console.print(f"  [dim][[CANCELLED]][/] Change discarded.")

    return confirmed


# ---------------------------------------------------------------------------
# -- Internal: shared model browsing logic (used by Fast and Heavy tiers) --
# ---------------------------------------------------------------------------

def _browse_and_pick_ollama_model(vram_gb, vram_limit, env_path, current_model_key):
    """Shared interactive model browser for Ollama tiers.

    Displays installed models, library models, and BitNet models with VRAM
    fitness badges in a Rich Table. Returns the selected fully qualified
    model name or None if the user cancels.

    Args:
        vram_gb: Detected GPU VRAM in GB (or None).
        vram_limit: VRAM headroom-adjusted limit in GB (or None).
        env_path: Path to the .env file for reading current configuration.
        current_model_key: The .env key to display as "currently configured".

    Returns:
        str or None: Selected model name, or None if cancelled.
    """
    installed = get_installed_models()
    values = dotenv_values(env_path)
    current_model = values.get(current_model_key, "")

    console.print(f"  [dim]Currently configured:[/] [cyan]{current_model if current_model else 'None'}[/]")

    # -- Build model list from core.hardware --
    console.print("\n  [dim]Fetching available models from Ollama library...[/]")
    all_models = get_all_chat_models_sorted(vram_gb)

    # Add library models not already in the sorted list
    library_models = get_ollama_library_models(vram_gb if vram_gb else 99)
    library_names = {m["name"] for m in all_models}
    for m in library_models:
        if m["name"] not in library_names:
            fits = m["size_gb"] <= vram_limit if vram_limit else True
            all_models.append({
                "name": m["name"], "size_gb": m["size_gb"], "fits": fits,
                "installed": False, "recommended": False,
                "section": "library",
            })

    # Add BitNet models
    bitnet_models = get_bitnet_models(vram_gb)
    for m in bitnet_models:
        if m["name"] not in library_names:
            all_models.append({
                "name": m["name"], "size_gb": m["size_gb"], "fits": m["fits"],
                "installed": False, "recommended": False,
                "section": "bitnet", "hf_repo": m.get("hf_repo"),
                "description": m.get("description", ""),
            })

    # Sort by section priority then size
    section_order = {"installed": 0, "library": 1, "bitnet": 2}
    all_models.sort(key=lambda m: (section_order.get(m.get("section", "library"), 99), m["size_gb"]))

    # -- Build Rich Table for model display --
    table = Table(box=box.ROUNDED, show_header=True, header_style="bold white")
    table.add_column("#", style="dim", width=4)
    table.add_column("Model Name", style="cyan", no_wrap=True)
    table.add_column("Est. Size", style="yellow", justify="right")
    table.add_column("VRAM Status", style="white")
    table.add_column("State", style="white")

    section_labels = {
        "installed": "--- [INSTALLED] ---",
        "library": "--- Available (Ollama Library) ---",
        "bitnet": "--- 1-Bit Models (Edge Devices) ---",
    }

    choices_map = {}
    idx = 1
    current_section = None
    for m in all_models:
        section = m.get("section", "library")
        if section != current_section:
            current_section = section
            # Add a separator row
            table.add_section()
            table.add_row(
                "", Text(section_labels.get(section, section), style="bold magenta"),
                "", "", ""
            )

        vram_label = _fits_label(m["fits"], m["size_gb"], vram_limit)
        state_label = ""
        if m.get("installed"):
            state_label = "[INSTALLED]"
        if m.get("recommended"):
            state_label += " [RECOMMENDED]"

        # Determine VRAM status style
        vram_style = "white"
        if "[FITS]" in vram_label:
            vram_style = "green"
        elif "[TIGHT]" in vram_label:
            vram_style = "yellow"
        elif "[TOO BIG]" in vram_label:
            vram_style = "red"

        table.add_row(
            str(idx),
            m["name"],
            f"~{m['size_gb']}GB" if m.get("size_gb") else "?",
            Text(vram_label.strip(), style=vram_style) if vram_label else "-",
            state_label.strip() if state_label else "-",
        )
        choices_map[str(idx)] = m["name"]
        idx += 1

    console.print()
    console.print(table)

    # -- Build questionary choices --
    choices = []
    for k, name in choices_map.items():
        label = name
        # Find model info for badges
        model_info = next((m for m in all_models if m["name"] == name), None)
        if model_info:
            label += f" (~{model_info['size_gb']}GB)"
            label += _fits_label(model_info["fits"], model_info["size_gb"], vram_limit)
            if model_info.get("installed"):
                label += " [INSTALLED]"
            if model_info.get("recommended"):
                label += " [RECOMMENDED]"
        choices.append(questionary.Choice(title=label, value=name))

    choices.append(questionary.Separator())
    choices.append(questionary.Choice(title="Custom model name...", value="__custom__"))
    choices.append(questionary.Choice(title="[Cancel / Return to Main Menu]", value="__cancel__"))

    selected = questionary.select(
        "Select a model:",
        choices=choices,
        use_indicator=True,
        style=TALOS_QUESTIONARY_STYLE,
    ).ask()

    if selected == "__cancel__" or selected is None:
        console.print("  [dim][[CANCELLED]][/] Returning to main menu.")
        return None

    if selected == "__custom__":
        model_name = questionary.text("Enter model name (e.g., gemma3:12b):", style=TALOS_QUESTIONARY_STYLE).ask()
        if not model_name or not model_name.strip():
            console.print("  [dim][[CANCELLED]][/] No name entered.")
            return None
        model_name = model_name.strip()
        return model_name

    return selected


def _pick_quantization(model_name, vram_limit, installed_models):
    """Let the user choose a quantization tag for a given base model.

    Renders quantization variants in a Rich Table grouped by bit-depth
    before prompting for choice. Includes a Cancel option.

    Args:
        model_name: Model name, optionally with a tag.
        vram_limit: VRAM headroom-adjusted limit in GB (or None).
        installed_models: List of currently installed model names.

    Returns:
        str or None: The chosen fully qualified model name with tag, or None if cancelled.
    """
    base_name = model_name.split(":")[0]

    console.print(f"\n  [dim]Fetching quantization variants for [cyan]{base_name}[/]...[/]")
    categories = get_quantized_variants(base_name)

    # -- Build Rich Table for quantization display --
    table = Table(box=box.ROUNDED, show_header=True, header_style="bold white")
    table.add_column("#", style="dim", width=4)
    table.add_column("Variant", style="cyan", no_wrap=True)
    table.add_column("Est. Size", style="yellow", justify="right")
    table.add_column("VRAM Status", style="white")
    table.add_column("State", style="white")

    choices_map = {}
    idx = 1
    for cat_name, variants in categories.items():
        table.add_section()
        table.add_row("", Text(cat_name, style="bold magenta"), "", "", "")
        for v in variants:
            label = v["full_name"]
            tag = v.get("tag", "")
            est_size = estimate_size_for_quant(model_name, tag) if tag else v.get("size_gb")
            size_str = ""
            vram_label = ""
            if est_size and est_size > 0 and est_size < 99:
                size_str = f"~{est_size}GB"
                vram_label = _fits_label(vram_limit and est_size <= vram_limit, est_size, vram_limit)
            elif v.get("size_gb"):
                size_str = f"~{v['size_gb']}GB"
                vram_label = _fits_label(vram_limit and v["size_gb"] <= vram_limit, v["size_gb"], vram_limit)
            state_label = "[INSTALLED]" if v["installed"] else ""

            vram_style = "white"
            if "[FITS]" in vram_label:
                vram_style = "green"
            elif "[TIGHT]" in vram_label:
                vram_style = "yellow"
            elif "[TOO BIG]" in vram_label:
                vram_style = "red"

            table.add_row(
                str(idx),
                label,
                size_str if size_str else "-",
                Text(vram_label.strip(), style=vram_style) if vram_label else "-",
                state_label if state_label else "-",
            )
            choices_map[str(idx)] = v["full_name"]
            idx += 1

    console.print()
    console.print(table)

    # -- Build questionary choices --
    quant_choices = []
    for k, full in choices_map.items():
        # Find variant info for filtering
        variant_info = None
        for cat_variants in categories.values():
            for v in cat_variants:
                if v["full_name"] == full:
                    variant_info = v
                    break
            if variant_info:
                break

        display_label = full
        if variant_info:
            tag = variant_info.get("tag", "")
            est_size = estimate_size_for_quant(model_name, tag) if tag else variant_info.get("size_gb")
            if est_size and est_size > 0 and est_size < 99:
                display_label += f" (est. ~{est_size}GB)"
                display_label += _fits_label(vram_limit and est_size <= vram_limit, est_size, vram_limit)
            elif variant_info.get("size_gb"):
                display_label += f" (~{variant_info['size_gb']}GB)"
                display_label += _fits_label(vram_limit and variant_info["size_gb"] <= vram_limit, variant_info["size_gb"], vram_limit)
            if variant_info.get("installed"):
                display_label += " [INSTALLED]"
        quant_choices.append(questionary.Choice(title=display_label, value=full))

    quant_choices.append(questionary.Separator())
    quant_choices.append(questionary.Choice(title="Use base tag (no quantization suffix)", value="__base__"))
    quant_choices.append(questionary.Choice(title="[Cancel / Return to Main Menu]", value="__cancel__"))

    selected = questionary.select(
        f"Select quantization for [cyan]{base_name}[/]:",
        choices=quant_choices,
        use_indicator=True,
        style=TALOS_QUESTIONARY_STYLE,
    ).ask()

    if selected == "__cancel__" or selected is None:
        console.print("  [dim][[CANCELLED]][/] Returning to main menu.")
        return None

    if selected == "__base__":
        return model_name

    return selected if ":" in selected else model_name


def _install_if_needed(final_model, installed_models, vram_limit):
    """Check if a model is installed and offer to pull it if not.

    Args:
        final_model: Fully qualified model name to check.
        installed_models: List of installed model names.
        vram_limit: VRAM headroom-adjusted limit in GB (or None).

    Returns:
        bool: True if the model is installed (or was pulled successfully),
              False if the user declined or the pull failed.
    """
    if final_model in installed_models:
        return True

    tag = final_model.split(":", 1)[1] if ":" in final_model else ""
    est_size = estimate_size_for_quant(final_model, tag) if tag else estimate_size_for_quant(final_model)
    console.print(f"\n  [bold]{final_model}[/]")
    if est_size and est_size < 99:
        console.print(f"  [dim]Estimated size: ~{est_size}GB[/]")
    if vram_limit and est_size and est_size > vram_limit:
        console.print(f"  [bold yellow][[WARNING]][/] This model ({est_size}GB) exceeds available VRAM ({vram_limit:.1f}GB)")
    console.print("  [dim]Model is not installed.[/]")
    do_pull = questionary.confirm(
        f"Download {final_model} now? (ollama pull)",
        default=True,
        style=TALOS_QUESTIONARY_STYLE,
    ).ask()
    if do_pull:
        return _provision_model(final_model)
    else:
        console.print("  [dim]Skipping download. Model not changed.[/]")
        console.input("[dim]Press Enter to continue...[/]")
        return False


# ---------------------------------------------------------------------------
# -- Tier Configuration Functions --
# ---------------------------------------------------------------------------

def select_fast_edge_model(env_path):
    """Configure the Fast Edge Tier model and endpoint.

    Prompts the user to select a lightweight model suitable for CPU-based
    pre-screening and quick evaluations. Writes FAST_EDGE_MODEL and
    FAST_EDGE_BASE_URL to .env with confirmation safety locks.

    Implements explicit Cancel/Back navigation guardrails.

    Args:
        env_path: Absolute path to the .env file.
    """
    os.system('cls' if os.name == 'nt' else 'clear')
    panel = Panel(
        "[bold]Fast Edge Tier Configuration[/]\n[dim]CPU-Optimized | Port 11435 | Lightweight Pre-Screening[/]",
        border_style="cyan",
        box=box.ROUNDED,
        padding=(1, 2),
    )
    console.print(panel)

    if not check_ollama_alive():
        console.print(f"\n  [bold red][[ERROR]][/] Ollama server not reachable at [cyan]{get_ollama_base()}[/]")
        console.print("  [dim]Make sure Ollama is running (ollama serve).[/]")
        console.input("\n[dim]Press Enter to return...[/]")
        return

    vram_gb = detect_vram_gb()
    vram_limit = vram_gb * VRAM_HEADROOM if vram_gb else None
    if vram_gb:
        console.print(f"\n  [dim]GPU VRAM:[/] [green]{vram_gb:.1f}GB[/] [dim]| Available for models: [yellow]{vram_limit:.1f}GB[/] (70% headroom)[/]")
    else:
        console.print("\n  [dim]GPU VRAM: Not detected (no NVIDIA GPU or nvidia-smi missing)[/]")

    console.print("\n  [dim]Fast Edge Tier uses a lightweight model for low-latency pre-screening.[/]")
    console.print("  [dim]Recommended: fermionresearch/Neutrino-8B or similar small model.[/]")

    values = dotenv_values(env_path)
    current_edge = values.get("FAST_EDGE_MODEL", "fermionresearch/Neutrino-8B")
    current_edge_url = values.get("FAST_EDGE_BASE_URL", "http://127.0.0.1:11435/v1")
    console.print(f"\n  [dim]Current Fast Edge Model:[/] [cyan]{current_edge}[/]")
    console.print(f"  [dim]Current Fast Edge URL:  [/] [cyan]{current_edge_url}[/]")

    # -- Configure endpoint URL --
    if questionary.confirm("Change Fast Edge endpoint URL?", default=False, style=TALOS_QUESTIONARY_STYLE).ask():
        new_url = questionary.text(
            "Enter Fast Edge base URL:",
            default=current_edge_url,
            style=TALOS_QUESTIONARY_STYLE,
        ).ask()
        if new_url and new_url.strip():
            new_url_stripped = new_url.strip()
            # -- Confirmation safety lock --
            if _confirm_setting_change(env_path, "FAST_EDGE_BASE_URL", current_edge_url, new_url_stripped):
                _set_key(env_path, "FAST_EDGE_BASE_URL", new_url_stripped)
                os.environ["FAST_EDGE_BASE_URL"] = new_url_stripped
                console.print(f"  [bold green][[OK]][/] FAST_EDGE_BASE_URL set to: [cyan]{new_url_stripped}[/]")

    # -- Select model --
    model_name = _browse_and_pick_ollama_model(vram_gb, vram_limit, env_path, "FAST_EDGE_MODEL")
    if not model_name:
        console.input("\n[dim]Press Enter to return...[/]")
        return

    installed = get_installed_models()
    final_model = _pick_quantization(model_name, vram_limit, installed)
    if not final_model:
        console.input("\n[dim]Press Enter to return...[/]")
        return

    if not _install_if_needed(final_model, installed, vram_limit):
        console.input("\n[dim]Press Enter to return...[/]")
        return

    # -- Confirmation safety lock --
    if _confirm_setting_change(env_path, "FAST_EDGE_MODEL", current_edge, final_model):
        _set_key(env_path, "FAST_EDGE_MODEL", final_model)
        os.environ["FAST_EDGE_MODEL"] = final_model
        console.print(f"\n  [bold green][[OK]][/] FAST_EDGE_MODEL set to: [cyan]{final_model}[/]")
        console.print("  [dim]Restart TALOS or re-enter local mode for changes to take effect.[/]")

    console.input("\n[dim]Press Enter to continue...[/]")


def select_heavy_model(env_path):
    """Configure the Heavy Reasoning Tier model and endpoint.

    Prompts the user to select a large model for deep analysis and complex
    reasoning tasks. Writes HEAVY_REASONING_MODEL and OLLAMA_BASE_URL to .env
    with confirmation safety locks.

    Implements explicit Cancel/Back navigation guardrails.

    Args:
        env_path: Absolute path to the .env file.
    """
    os.system('cls' if os.name == 'nt' else 'clear')
    panel = Panel(
        "[bold]Heavy Reasoning Tier Configuration[/]\n[dim]GPU-Optimized | Port 11434 | Deep Analysis & Complex Reasoning[/]",
        border_style="magenta",
        box=box.ROUNDED,
        padding=(1, 2),
    )
    console.print(panel)

    if not check_ollama_alive():
        console.print(f"\n  [bold red][[ERROR]][/] Ollama server not reachable at [cyan]{get_ollama_base()}[/]")
        console.print("  [dim]Make sure Ollama is running (ollama serve).[/]")
        console.input("\n[dim]Press Enter to return...[/]")
        return

    vram_gb = detect_vram_gb()
    vram_limit = vram_gb * VRAM_HEADROOM if vram_gb else None
    if vram_gb:
        console.print(f"\n  [dim]GPU VRAM:[/] [green]{vram_gb:.1f}GB[/] [dim]| Available for models: [yellow]{vram_limit:.1f}GB[/] (70% headroom)[/]")
    else:
        console.print("\n  [dim]GPU VRAM: Not detected (no NVIDIA GPU or nvidia-smi missing)[/]")

    console.print("\n  [dim]Heavy Reasoning Tier uses a larger model for deep analysis tasks.[/]")
    console.print("  [dim]Recommended: qwen2.5:14b or similar 7-14B parameter model.[/]")

    values = dotenv_values(env_path)
    current_heavy = values.get("HEAVY_REASONING_MODEL", "qwen2.5:14b")
    current_heavy_url = values.get("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
    console.print(f"\n  [dim]Current Heavy Reasoning Model:[/] [cyan]{current_heavy}[/]")
    console.print(f"  [dim]Current Ollama URL:           [/] [cyan]{current_heavy_url}[/]")

    # -- Configure endpoint URL --
    if questionary.confirm("Change Heavy Reasoning endpoint URL?", default=False, style=TALOS_QUESTIONARY_STYLE).ask():
        new_url = questionary.text(
            "Enter Ollama base URL:",
            default=current_heavy_url,
            style=TALOS_QUESTIONARY_STYLE,
        ).ask()
        if new_url and new_url.strip():
            normalized = new_url.strip().rstrip("/")
            # -- Confirmation safety lock --
            if _confirm_setting_change(env_path, "OLLAMA_BASE_URL", current_heavy_url, normalized):
                _set_key(env_path, "OLLAMA_BASE_URL", normalized)
                os.environ["OLLAMA_BASE_URL"] = normalized
                # Also update LOCAL_MODEL_BASE_URL for backward compatibility
                local_url = normalized + "/v1"
                _set_key(env_path, "LOCAL_MODEL_BASE_URL", local_url)
                os.environ["LOCAL_MODEL_BASE_URL"] = local_url
                console.print(f"  [bold green][[OK]][/] OLLAMA_BASE_URL set to: [cyan]{normalized}[/]")

    # -- Select model --
    model_name = _browse_and_pick_ollama_model(vram_gb, vram_limit, env_path, "HEAVY_REASONING_MODEL")
    if not model_name:
        console.input("\n[dim]Press Enter to return...[/]")
        return

    installed = get_installed_models()
    final_model = _pick_quantization(model_name, vram_limit, installed)
    if not final_model:
        console.input("\n[dim]Press Enter to return...[/]")
        return

    if not _install_if_needed(final_model, installed, vram_limit):
        console.input("\n[dim]Press Enter to return...[/]")
        return

    # -- Confirmation safety lock --
    if _confirm_setting_change(env_path, "HEAVY_REASONING_MODEL", current_heavy, final_model):
        _set_key(env_path, "HEAVY_REASONING_MODEL", final_model)
        os.environ["HEAVY_REASONING_MODEL"] = final_model
        console.print(f"\n  [bold green][[OK]][/] HEAVY_REASONING_MODEL set to: [cyan]{final_model}[/]")
        console.print("  [dim]Restart TALOS or re-enter local mode for changes to take effect.[/]")

    console.input("\n[dim]Press Enter to continue...[/]")


# -- v5.9.18: Universal Cloud Mesh provider catalog (single source of truth) --
# Maps provider key -> (display name, env key, model env key, default model, base URL).
CLOUD_PROVIDER_CATALOG = [
    ("gemini", "Gemini", "GEMINI_API_KEY", "GEMINI_FLASH_MODEL", DEFAULT_GEMINI_FLASH, "n/a (Google GenAI SDK)"),
    ("nvidia", "NVIDIA NIM", "NVIDIA_API_KEY", "NVIDIA_DEFAULT_MODEL", DEFAULT_NVIDIA_MODEL, NVIDIA_BASE_URL),
    ("groq", "Groq", "GROQ_API_KEY", "GROQ_DEFAULT_MODEL", DEFAULT_GROQ_MODEL, GROQ_BASE_URL),
    ("cerebras", "Cerebras", "CEREBRAS_API_KEY", "CEREBRAS_DEFAULT_MODEL", DEFAULT_CEREBRAS_MODEL, CEREBRAS_BASE_URL),
    ("github", "GitHub Models", "GITHUB_TOKEN", "GITHUB_MODELS_DEFAULT_MODEL", DEFAULT_GITHUB_MODEL, GITHUB_MODELS_BASE_URL),
    ("mistral", "Mistral", "MISTRAL_API_KEY", "MISTRAL_DEFAULT_MODEL", DEFAULT_MISTRAL_MODEL, MISTRAL_BASE_URL),
    ("openrouter", "OpenRouter", "OPENROUTER_API_KEY", "OPENROUTER_DEFAULT_MODEL", DEFAULT_OPENROUTER_MODEL, OPENROUTER_BASE_URL),
    ("deepseek", "DeepSeek", "DEEPSEEK_API_KEY", "DEEPSEEK_MODEL_CHAT", DEFAULT_DEEPSEEK_MODEL, DEEPSEEK_BASE_URL),
    ("huggingface", "Hugging Face", "HF_TOKEN", "HF_MODEL_NAME", DEFAULT_HF_MODEL, HF_BASE_URL),
]


def get_cloud_provider_rows(values):
    """Build the cloud provider status rows for the Universal Cloud Mesh table.

    Args:
        values: dict-like mapping of .env values (dotenv_values result).

    Returns:
        list of dicts, each with keys: provider, display_name, env_key,
        model_env_key, status, model, base_url.
    """
    rows = []
    for key, display, env_key, model_env_key, default_model, base_url in CLOUD_PROVIDER_CATALOG:
        has_key = bool(os.getenv(env_key) or values.get(env_key))
        rows.append({
            "provider": key,
            "display_name": display,
            "env_key": env_key,
            "model_env_key": model_env_key,
            "status": "ACTIVE" if has_key else "UNCONFIGURED",
            "model": values.get(model_env_key, default_model),
            "base_url": base_url,
        })
    return rows


def select_cloud_models(env_path):
    """Interactive Universal Cloud Mesh configuration (v5.9.18).

    Renders a Rich table of all nine cloud providers (Gemini primary plus the
    8-provider OpenAI-compatible redundancy cascade) with columns: Provider Name,
    Env Key, Status ([ACTIVE] green vs [UNCONFIGURED] yellow), Default Model, and
    Base URL. Lets the user select any provider to view details, save its API key
    to .env, or modify its default model. Implements explicit Cancel/Back
    navigation guardrails.

    Args:
        env_path: Absolute path to the .env file.
    """
    os.system('cls' if os.name == 'nt' else 'clear')
    panel = Panel(
        "[bold]Cloud Configuration -- Universal Cloud Mesh[/]\n[dim]Gemini primary + 8-provider OpenAI-compatible redundancy cascade[/]",
        border_style="yellow",
        box=box.ROUNDED,
        padding=(1, 2),
    )
    console.print(panel)

    values = dotenv_values(env_path)

    # -- Provider registry table --
    rows = get_cloud_provider_rows(values)
    table = Table(
        box=box.ROUNDED,
        show_header=True,
        header_style="bold white",
        title="[bold bright_yellow]Cloud Provider Registry[/bold bright_yellow]",
        title_justify="center",
    )
    table.add_column("Provider Name", style="cyan")
    table.add_column("Env Key", style="white")
    table.add_column("Status", style="white")
    table.add_column("Default Model", style="green")
    table.add_column("Base URL", style="dim")

    for r in rows:
        status = "[bold green][ACTIVE][/]" if r["status"] == "ACTIVE" else "[bold yellow][UNCONFIGURED][/]"
        table.add_row(r["display_name"], r["env_key"], status, r["model"], r["base_url"])

    console.print()
    console.print(table)

    # -- Provider selection (any provider may be selected, configured or not) --
    choices = [questionary.Choice(title=r["display_name"], value=r["provider"]) for r in rows]
    choices.append(questionary.Separator())
    choices.append(questionary.Choice(title="[Cancel / Back]", value="__cancel__"))
    selected = questionary.select("Select a provider to view or configure:", choices=choices, style=TALOS_QUESTIONARY_STYLE).ask()

    if not selected or selected in ("__cancel__", "Cancel", "[Cancel / Back]"):
        console.input("\n[dim]Press Enter to return...[/]")
        return

    # -- Resolve the selected provider's metadata --
    meta = next((r for r in rows if r["provider"] == selected), None)
    if meta is None:
        console.input("\n[dim]Press Enter to return...[/]")
        return

    console.print(f"\n  [bold]{meta['display_name']}[/]")
    console.print(f"  [dim]Env Key:[/]      [cyan]{meta['env_key']}[/]")
    console.print(f"  [dim]Default Model:[/] [cyan]{meta['model']}[/]")
    console.print(f"  [dim]Base URL:[/]     [cyan]{meta['base_url']}[/]")

    # -- Configure / save API key --
    if questionary.confirm(f"Save API key for {meta['display_name']}?", default=False, style=TALOS_QUESTIONARY_STYLE).ask():
        current_key = os.getenv(meta["env_key"]) or values.get(meta["env_key"]) or ""
        new_key = questionary.text(f"Enter {meta['env_key']} value:", default=current_key or "", style=TALOS_QUESTIONARY_STYLE).ask()
        if new_key is not None and new_key.strip():
            _set_key(env_path, meta["env_key"], new_key.strip())
            os.environ[meta["env_key"]] = new_key.strip()
            console.print(f"  [bold green][[OK]][/] {meta['env_key']} saved.")
        else:
            console.print("  [dim][[CANCELLED]][/] No key entered.")

    # -- Modify default model --
    if questionary.confirm(f"Modify default model for {meta['display_name']}?", default=False, style=TALOS_QUESTIONARY_STYLE).ask():
        new_model = questionary.text("Enter model name:", default=meta["model"], style=TALOS_QUESTIONARY_STYLE).ask()
        if new_model and new_model.strip():
            _set_key(env_path, meta["model_env_key"], new_model.strip())
            os.environ[meta["model_env_key"]] = new_model.strip()
            console.print(f"  [bold green][[OK]][/] {meta['model_env_key']} set to: [cyan]{new_model.strip()}[/]")
        else:
            console.print("  [dim][[CANCELLED]][/] No model entered.")

    console.input("\n[dim]Press Enter to continue...[/]")


def select_execution_mode(env_path):
    """Configure the 2D Execution Matrix (Network Strategy & Hardware Strategy).

    v5.9.4: Replaces the old 4-Way Execution Mode Matrix with a richer 2D model.
    Step 1: Select Network Strategy (strict_local, local_first, cloud_first,
            strict_cloud). These determine air-gapped vs. cloud dependency and
            automatic cross-environment fallback behavior.
    Step 2: If the Network Strategy involves local compute (not strict_cloud),
            select a Hardware Strategy (cpu_only, gpu_only, cpu_gpu_split) that
            controls how requests are distributed across CPU and GPU endpoints.

    Sets TALOS_NETWORK_STRATEGY and TALOS_HARDWARE_STRATEGY in .env, plus
    backward-compatible legacy keys (TALOS_EXECUTION_MODE, TALOS_USE_LOCAL,
    TALOS_ALLOW_CLOUD_FALLBACK, TALOS_FAST_ROUTING, TALOS_HEAVY_ROUTING).

    Displays an informational Rich Panel before each step and a summary
    confirmation panel before writing.

    Args:
        env_path: Absolute path to the .env file.
    """
    os.system('cls' if os.name == 'nt' else 'clear')

    # -- Header panel --
    header_panel = Panel(
        "[bold]2D Execution Matrix Configuration[/]\n"
        "[dim]Network Strategy x Hardware Strategy -- Cross-Environment Fallback Routing[/]",
        border_style="blue",
        box=box.ROUNDED,
        padding=(1, 2),
    )
    console.print(header_panel)

    values = dotenv_values(env_path)
    current_network = values.get("TALOS_NETWORK_STRATEGY", "strict_local")
    current_hardware = values.get("TALOS_HARDWARE_STRATEGY", "cpu_gpu_split")

    console.print(f"\n  [dim]Current Network Strategy:[/]  [cyan]{current_network}[/]")
    console.print(f"  [dim]Current Hardware Strategy:[/] [cyan]{current_hardware}[/]")

    # -- Step 1: Network Strategy Selection --
    network_table = Table(
        box=box.ROUNDED,
        show_header=True,
        header_style="bold white",
        title="[bold bright_cyan]Step 1: Network Strategy[/bold bright_cyan]",
        title_justify="center",
    )
    network_table.add_column("#", style="dim", width=3, justify="right")
    network_table.add_column("Strategy", style="cyan", no_wrap=True, width=18)
    network_table.add_column("Description", style="white", width=40)
    network_table.add_column("Fallback Behavior", style="green", width=30)

    network_rows = [
        ("1", "Strict Local", "Air-Gapped. Zero internet dependency. Maximum privacy.",
         "None -- local only."),
        ("2", "Local-First", "Local tiers primary. Cloud as safety net.",
         "ConnectionError -> auto-reroute to Cloud."),
        ("3", "Cloud-First", "Cloud providers primary. Local as fallback.",
         "Auth/Rate/Timeout -> auto-reroute to Local."),
        ("4", "Strict Cloud", "Pure cloud. No local models required.",
         "None -- cloud only."),
        ("5", "Auto-Dynamic", "Autonomous strategy selection with Privacy Guardrails.",
         "Runtime resolve: offline/VRAM/task + consent gate."),
    ]
    for row in network_rows:
        network_table.add_row(*row)

    console.print()
    console.print(network_table)

    network_choices = [
        questionary.Choice(
            title="[1] Strict Local -- Air-Gapped (local only, never cloud)",
            value="strict_local"
        ),
        questionary.Choice(
            title="[2] Local-First -- Local primary, auto-fallback to Cloud on ConnectionError",
            value="local_first"
        ),
        questionary.Choice(
            title="[3] Cloud-First -- Cloud primary, auto-fallback to Local on auth/rate/timeout failure",
            value="cloud_first"
        ),
        questionary.Choice(
            title="[4] Strict Cloud -- Cloud only, no local models",
            value="strict_cloud"
        ),
        questionary.Choice(
            title="[5] Auto-Dynamic Orchestration -- Autonomous strategy selection with Privacy Guardrails",
            value="auto_dynamic"
        ),
        questionary.Separator(),
        questionary.Choice(title="[Cancel / Return to Main Menu]", value="__cancel__"),
    ]

    selected_network = questionary.select(
        "Select Network Strategy:",
        choices=network_choices,
        use_indicator=True,
        style=TALOS_QUESTIONARY_STYLE,
    ).ask()

    if selected_network == "__cancel__" or selected_network is None:
        console.print("  [dim][[CANCELLED]][/] Returning to main menu.")
        console.input("\n[dim]Press Enter to continue...[/]")
        return

    # -- Step 2: Hardware Strategy (only if network involves local compute) --
    selected_hardware = current_hardware  # default: keep current
    if selected_network != "strict_cloud":
        hardware_table = Table(
            box=box.ROUNDED,
            show_header=True,
            header_style="bold white",
            title="[bold bright_magenta]Step 2: Hardware Strategy[/bold bright_magenta]",
            title_justify="center",
        )
        hardware_table.add_column("#", style="dim", width=3, justify="right")
        hardware_table.add_column("Strategy", style="magenta", no_wrap=True, width=18)
        hardware_table.add_column("Description", style="white", width=40)
        hardware_table.add_column("Routing Rule", style="yellow", width=30)

        hardware_rows = [
            ("1", "CPU Only", "All local inference on CPU (FAST_EDGE_BASE_URL, port 11435).",
             "Fast and Heavy both -> CPU"),
            ("2", "GPU Only", "All local inference on GPU (OLLAMA_BASE_URL, port 11434).",
             "Fast and Heavy both -> GPU"),
            ("3", "CPU-GPU Split", "Fast tier -> CPU (port 11435), Heavy tier -> GPU (port 11434).",
             "Respects tier parameter."),
        ]
        for row in hardware_rows:
            hardware_table.add_row(*row)

        console.print()
        console.print(hardware_table)

        hardware_choices = [
            questionary.Choice(
                title="[1] CPU Only (Neutrino) -- All local requests on CPU endpoint",
                value="cpu_only"
            ),
            questionary.Choice(
                title="[2] GPU Only (Ollama) -- All local requests on GPU endpoint",
                value="gpu_only"
            ),
            questionary.Choice(
                title="[3] CPU+GPU Hybrid Split -- Fast on CPU, Heavy on GPU (default)",
                value="cpu_gpu_split"
            ),
            questionary.Separator(),
            questionary.Choice(title="[Cancel / Return to Main Menu]", value="__cancel__"),
        ]

        selected_hardware = questionary.select(
            "Select Hardware Strategy:",
            choices=hardware_choices,
            use_indicator=True,
            style=TALOS_QUESTIONARY_STYLE,
        ).ask()

        if selected_hardware == "__cancel__" or selected_hardware is None:
            console.print("  [dim][[CANCELLED]][/] Returning to main menu.")
            console.input("\n[dim]Press Enter to continue...[/]")
            return
    else:
        # Strict Cloud: hardware strategy is irrelevant, force cpu_gpu_split (default)
        selected_hardware = "cpu_gpu_split"

    # -- Network strategy label map --
    network_labels = {
        "strict_local": "Strict Local (Air-Gapped)",
        "local_first":  "Local-First (w/ Cloud Fallback)",
        "cloud_first":  "Cloud-First (w/ Local Fallback)",
        "strict_cloud": "Strict Cloud (Cloud-Only)",
        "auto_dynamic": "Auto-Dynamic (Privacy Guardrails)",
    }
    hardware_labels = {
        "cpu_only":      "CPU Only (Neutrino)",
        "gpu_only":      "GPU Only (Ollama)",
        "cpu_gpu_split": "CPU+GPU Hybrid Split",
    }

    # -- Build summary confirmation panel --
    summary_text = Text()
    summary_text.append("2D Execution Matrix -- Summary:\n\n", style="bold white underline")
    summary_text.append(f"  Network Strategy:  ", style="dim")
    summary_text.append(f"{network_labels.get(selected_network, selected_network)}\n", style="bold cyan")
    summary_text.append(f"                     ", style="dim")
    if selected_network == "strict_local":
        summary_text.append("[All inference local. Zero internet. Maximum privacy.]\n", style="dim green")
    elif selected_network == "local_first":
        summary_text.append("[Local primary. Auto-fallback to cloud on ConnectionError.]\n", style="dim green")
    elif selected_network == "cloud_first":
        summary_text.append("[Cloud primary. Auto-fallback to local on auth/rate/timeout.]\n", style="dim green")
    elif selected_network == "strict_cloud":
        summary_text.append("[Cloud-only. No local models needed. Internet required.]\n", style="dim green")
    elif selected_network == "auto_dynamic":
        summary_text.append("[Autonomous strategy selection. Cloud requires interactive consent.]\n", style="dim green")

    summary_text.append(f"\n  Hardware Strategy: ", style="dim")
    summary_text.append(f"{hardware_labels.get(selected_hardware, selected_hardware)}\n", style="bold magenta")
    summary_text.append(f"                     ", style="dim")
    if selected_hardware == "cpu_only":
        summary_text.append("[ALL local requests -> CPU (port 11435). No GPU.]\n", style="dim yellow")
    elif selected_hardware == "gpu_only":
        summary_text.append("[ALL local requests -> GPU (port 11434). No CPU edge.]\n", style="dim yellow")
    elif selected_hardware == "cpu_gpu_split":
        summary_text.append("[Fast -> CPU (11435), Heavy -> GPU (11434).]\n", style="dim yellow")

    summary_text.append(f"\n  Previous Network:  [dim]{network_labels.get(current_network, current_network)}[/dim]\n", style="")
    summary_text.append(f"  Previous Hardware: [dim]{hardware_labels.get(current_hardware, current_hardware)}[/dim]\n", style="")

    confirm_panel = Panel(
        summary_text,
        title="[bold]Confirm 2D Execution Matrix Configuration[/bold]",
        border_style="yellow",
        box=box.ROUNDED,
        padding=(1, 2),
    )
    console.print()
    console.print(confirm_panel)

    if not questionary.confirm("Apply this configuration?", default=True, style=TALOS_QUESTIONARY_STYLE).ask():
        console.print("  [dim][[CANCELLED]][/] No changes made.")
        console.input("\n[dim]Press Enter to continue...[/]")
        return

    # -- Write new env variables --
    _set_key(env_path, "TALOS_NETWORK_STRATEGY", selected_network)
    _set_key(env_path, "TALOS_HARDWARE_STRATEGY", selected_hardware)
    os.environ["TALOS_NETWORK_STRATEGY"] = selected_network
    os.environ["TALOS_HARDWARE_STRATEGY"] = selected_hardware

    # -- Backward-compatible keys --
    # Map network strategy to legacy per-tier routing for ai_manager.py v5.9.3 compat
    if selected_network == "strict_local":
        new_fast, new_heavy = "local", "local"
        mode_value = "local"
        _set_key(env_path, "TALOS_USE_LOCAL", "1")
        _set_key(env_path, "TALOS_ALLOW_CLOUD_FALLBACK", "0")
        os.environ["TALOS_USE_LOCAL"] = "1"
        os.environ["TALOS_ALLOW_CLOUD_FALLBACK"] = "0"
    elif selected_network == "local_first":
        new_fast, new_heavy = "local", "local"
        mode_value = "hybrid"
        _set_key(env_path, "TALOS_USE_LOCAL", "1")
        _set_key(env_path, "TALOS_ALLOW_CLOUD_FALLBACK", "1")
        os.environ["TALOS_USE_LOCAL"] = "1"
        os.environ["TALOS_ALLOW_CLOUD_FALLBACK"] = "1"
    elif selected_network == "cloud_first":
        new_fast, new_heavy = "cloud", "cloud"
        mode_value = "hybrid"
        _set_key(env_path, "TALOS_USE_LOCAL", "1")
        _set_key(env_path, "TALOS_ALLOW_CLOUD_FALLBACK", "1")
        os.environ["TALOS_USE_LOCAL"] = "1"
        os.environ["TALOS_ALLOW_CLOUD_FALLBACK"] = "1"
    elif selected_network == "auto_dynamic":
        new_fast, new_heavy = "local", "local"
        mode_value = "hybrid"
        _set_key(env_path, "TALOS_USE_LOCAL", "1")
        _set_key(env_path, "TALOS_ALLOW_CLOUD_FALLBACK", "1")
        os.environ["TALOS_USE_LOCAL"] = "1"
        os.environ["TALOS_ALLOW_CLOUD_FALLBACK"] = "1"
    else:  # strict_cloud
        new_fast, new_heavy = "cloud", "cloud"
        mode_value = "cloud"
        _set_key(env_path, "TALOS_USE_LOCAL", "0")
        _set_key(env_path, "TALOS_ALLOW_CLOUD_FALLBACK", "1")
        os.environ["TALOS_USE_LOCAL"] = "0"
        os.environ["TALOS_ALLOW_CLOUD_FALLBACK"] = "1"

    _set_key(env_path, "TALOS_FAST_ROUTING", new_fast)
    _set_key(env_path, "TALOS_HEAVY_ROUTING", new_heavy)
    _set_key(env_path, "TALOS_EXECUTION_MODE", mode_value)
    os.environ["TALOS_FAST_ROUTING"] = new_fast
    os.environ["TALOS_HEAVY_ROUTING"] = new_heavy
    os.environ["TALOS_EXECUTION_MODE"] = mode_value

    console.print(f"\n  [bold green][[OK]][/] 2D Execution Matrix updated:")
    console.print(f"  [dim]TALOS_NETWORK_STRATEGY:[/]  [bold cyan]{selected_network}[/] "
                  f"({network_labels.get(selected_network, selected_network)})")
    console.print(f"  [dim]TALOS_HARDWARE_STRATEGY:[/] [bold magenta]{selected_hardware}[/] "
                  f"({hardware_labels.get(selected_hardware, selected_hardware)})")
    console.print(f"  [dim]Legacy Compat:[/] TALOS_EXECUTION_MODE=[cyan]{mode_value}[/] "
                  f"FAST=[cyan]{new_fast}[/] HEAVY=[cyan]{new_heavy}[/]")
    console.print("  [dim]Restart TALOS for changes to take effect.[/]")
    console.input("\n[dim]Press Enter to continue...[/]")


def select_embedding_model(env_path):
    """Select the local embedding model for vector search.

    Offers a curated list of known-good embedding models, checks if they are
    installed, and offers to pull missing ones. Implements explicit Cancel/Back
    navigation guardrails and confirmation safety lock.

    Args:
        env_path: Absolute path to the .env file.
    """
    os.system('cls' if os.name == 'nt' else 'clear')
    panel = Panel(
        "[bold]Embedding Model Selection[/]\n[dim]Local Ollama models for vector search & semantic retrieval[/]",
        border_style="green",
        box=box.ROUNDED,
        padding=(1, 2),
    )
    console.print(panel)

    if not check_ollama_alive():
        console.print("\n  [bold red][[ERROR]][/] Ollama not reachable.")
        console.input("\n[dim]Press Enter to return...[/]")
        return

    values = dotenv_values(env_path)
    current_emb = values.get("LOCAL_EMBEDDING_MODEL", "")
    console.print(f"\n  [dim]Current embedding model:[/] [cyan]{current_emb if current_emb else 'Not set'}[/]")

    # Known good embedding models
    embedding_models = [
        "nomic-embed-text",
        "bge-m3",
        "mxbai-embed-large",
        "all-minilm",
        "snowflake-arctic-embed",
        "nomic-embed-text:latest",
    ]
    installed = get_installed_models()

    # -- Build Rich Table for embedding models --
    emb_table = Table(box=box.ROUNDED, show_header=True, header_style="bold white")
    emb_table.add_column("#", style="dim", width=4)
    emb_table.add_column("Model Name", style="cyan")
    emb_table.add_column("Installation State", style="white")

    choices_map = {}
    for idx, m in enumerate(embedding_models, start=1):
        state = "[green][INSTALLED][/]" if m in installed else "[dim][Available][/]"
        emb_table.add_row(str(idx), m, state)
        choices_map[str(idx)] = m

    console.print()
    console.print(emb_table)

    # -- Build questionary choices --
    choices = []
    for k, name in choices_map.items():
        prefix = "[INSTALLED] " if name in installed else "[Available] "
        choices.append(questionary.Choice(title=f"{prefix}{name}", value=name))
    choices.append(questionary.Choice(title="Custom...", value="__custom__"))
    choices.append(questionary.Separator())
    choices.append(questionary.Choice(title="[Cancel / Return to Main Menu]", value="__cancel__"))

    sel = questionary.select("Select embedding model:", choices=choices, style=TALOS_QUESTIONARY_STYLE).ask()
    if sel == "__cancel__" or sel is None:
        console.print("  [dim][[CANCELLED]][/] Returning to main menu.")
        console.input("\n[dim]Press Enter to continue...[/]")
        return

    if sel == "__custom__":
        model_name = questionary.text("Enter model name:", style=TALOS_QUESTIONARY_STYLE).ask()
        if not model_name or not model_name.strip():
            console.print("  [dim][[CANCELLED]][/] No model name entered.")
            console.input("\n[dim]Press Enter to continue...[/]")
            return
        model_name = model_name.strip()
    else:
        model_name = sel

    # Check and pull if needed
    if model_name not in installed:
        do_pull = questionary.confirm(f"Download {model_name}?", default=True, style=TALOS_QUESTIONARY_STYLE).ask()
        if do_pull:
            if not _provision_model(model_name):
                console.input("\n[dim]Press Enter to continue...[/]")
                return

    # -- Confirmation safety lock --
    if _confirm_setting_change(env_path, "LOCAL_EMBEDDING_MODEL", current_emb if current_emb else "(empty)", model_name):
        _set_key(env_path, "LOCAL_EMBEDDING_MODEL", model_name)
        os.environ["LOCAL_EMBEDDING_MODEL"] = model_name
        console.print(f"\n  [bold green][[OK]][/] LOCAL_EMBEDDING_MODEL set to: [cyan]{model_name}[/]")

    console.input("\n[dim]Press Enter to continue...[/]")


# ---------------------------------------------------------------------------
# -- Main TUI Entry Point --
# ---------------------------------------------------------------------------

def main():
    """Main TUI loop for multi-tier model management.

    Presents a 7-option menu for configuring:
    1. Fast Edge Tier (CPU, Port 11435)
    2. Heavy Reasoning Tier (GPU, Port 11434)
    3. Cloud API Tier (Gemini / DeepSeek / HF)
    4. System Execution Mode (Local / Hybrid / Cloud)
    5. Local Embedding Model
    6. Manual Ollama Pull
    7. Exit

    Ensures .env exists (copies from example.env if needed). All sub-menus
    handle cancellation (questionary.select -> Cancel) gracefully with
    explicit Cancel/Back navigation guardrails.
    """
    env_path = _ENV_PATH

    # -- Ensure .env exists --
    if not os.path.exists(env_path):
        example_path = str(_PROJECT_ROOT / "example.env")
        if os.path.exists(example_path):
            import shutil
            shutil.copy(example_path, env_path)
        else:
            open(env_path, 'w').close()

    while True:
        os.system('cls' if os.name == 'nt' else 'clear')

        # -- Main menu header panel --
        header_panel = Panel(
            f"[bold white]TALOS v{TALOS_VERSION}[/]\n[dim]Multi-Tier AI Model Management | 2D Execution Matrix | Safety Locks Active[/]",
            border_style="bright_blue",
            box=box.ROUNDED,
            padding=(1, 2),
        )
        console.print(header_panel)

        values = dotenv_values(env_path)
        ollama_status = "[green][CONNECTED][/]" if check_ollama_alive() else "[red][OFFLINE][/]"

        # -- Status table --
        status_table = Table(box=box.ROUNDED, show_header=False, pad_edge=False)
        status_table.add_column("Key", style="dim")
        status_table.add_column("Value", style="white")
        status_table.add_row("Ollama Status:", ollama_status)
        net_strat = values.get('TALOS_NETWORK_STRATEGY', 'strict_local')
        hw_strat = values.get('TALOS_HARDWARE_STRATEGY', 'cpu_gpu_split')
        net_labels = {"strict_local": "Strict Local", "local_first": "Local-First",
                      "cloud_first": "Cloud-First", "strict_cloud": "Strict Cloud"}
        hw_labels = {"cpu_only": "CPU Only", "gpu_only": "GPU Only",
                     "cpu_gpu_split": "CPU+GPU Split"}
        status_table.add_row("Network Strategy:", f"{net_strat} ({net_labels.get(net_strat, net_strat)})")
        status_table.add_row("Hardware Strategy:", f"{hw_strat} ({hw_labels.get(hw_strat, hw_strat)})")
        status_table.add_row("Legacy Mode:", values.get('TALOS_EXECUTION_MODE', 'local'))
        status_table.add_row("Fast Edge Model:", values.get('FAST_EDGE_MODEL', 'fermionresearch/Neutrino-8B'))
        status_table.add_row("Fast Edge URL:", values.get('FAST_EDGE_BASE_URL', 'http://127.0.0.1:11435/v1'))
        status_table.add_row("Heavy Reasoning:", values.get('HEAVY_REASONING_MODEL', 'qwen2.5:14b'))
        status_table.add_row("Ollama Base URL:", values.get('OLLAMA_BASE_URL', 'http://127.0.0.1:11434'))
        status_table.add_row("Embedding Model:", values.get('LOCAL_EMBEDDING_MODEL', 'Not set'))
        status_table.add_row("Gemini Flash:", values.get('GEMINI_FLASH_MODEL', DEFAULT_GEMINI_FLASH))
        status_table.add_row("Gemini Pro:", values.get('GEMINI_PRO_MODEL', DEFAULT_GEMINI_PRO))
        status_table.add_row("DeepSeek:", values.get('DEEPSEEK_MODEL_CHAT', DEFAULT_DEEPSEEK_MODEL))
        status_table.add_row("Hugging Face:", values.get('HF_MODEL_NAME', DEFAULT_HF_MODEL))

        console.print(status_table)

        # -- Menu options --
        console.print("\n" + "-" * 62)
        console.print("  [bold cyan][1][/] Configure Fast Edge Tier (CPU / Port 11435)")
        console.print("  [bold magenta][2][/] Configure Heavy Reasoning Tier (GPU / Port 11434)")
        console.print("  [bold yellow][3][/] Configure Cloud API Tier (Gemini / DeepSeek / HF)")
        console.print("  [bold blue][4][/] Select 2D Execution Matrix (Network x Hardware Strategies)")
        console.print("  [bold green][5][/] Select Local Embedding Model (Ollama)")
        console.print("  [bold white][6][/] Pull Ollama Model Manually")
        console.print("  [dim][7][/] Exit")

        choice = questionary.select(
            "Select action:",
            choices=[
                "1. Configure Fast Edge Tier (CPU / Port 11435)",
                "2. Configure Heavy Reasoning Tier (GPU / Port 11434)",
                "3. Configure Cloud API Tier (Gemini / DeepSeek / HF)",
                "4. Select 2D Execution Matrix (Network x Hardware Strategies)",
                "5. Select Local Embedding Model (Ollama)",
                "6. Pull Ollama Model Manually",
                "7. Exit",
            ],
            use_indicator=True,
            style=TALOS_QUESTIONARY_STYLE,
        ).ask()

        if not choice or choice.startswith("7"):
            console.print("\n  [dim]Exiting Model Manager. Configuration changes saved.[/]")
            break

        if choice.startswith("1"):
            select_fast_edge_model(env_path)
        elif choice.startswith("2"):
            select_heavy_model(env_path)
        elif choice.startswith("3"):
            select_cloud_models(env_path)
        elif choice.startswith("4"):
            select_execution_mode(env_path)
        elif choice.startswith("5"):
            select_embedding_model(env_path)
        elif choice.startswith("6"):
            model = questionary.text("Enter model to pull (e.g., gemma3:12b):", style=TALOS_QUESTIONARY_STYLE).ask()
            if model and model.strip():
                _provision_model(model.strip())
                console.input("\n[dim]Press Enter to continue...[/]")


if __name__ == "__main__":
    main()