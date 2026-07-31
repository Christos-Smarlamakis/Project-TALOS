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
Project: TALOS v5.8.0
Description:
    Interactive TUI for configuring all LLM tiers (Fast Edge CPU, Heavy Reasoning GPU,
    Cloud API) and setting the system execution mode (air-gapped local, hybrid, or
    full cloud). Supports Ollama model selection with quantization-aware sizing,
    plus cloud provider configuration for Gemini, DeepSeek, and Hugging Face.

    Key design decisions:
    - Multi-tier architecture: Fast Edge Tier (port 11435, CPU-optimized), Heavy
      Reasoning Tier (port 11434, GPU-optimized), Cloud API Tier (Gemini/DeepSeek/HF).
    - System Execution Mode selector writes TALOS_EXECUTION_MODE to .env.
    - All network-dependent operations check Ollama reachability first via
      check_ollama_alive() and degrade gracefully.
    - Zero-emojis protocol enforced: all status indicators use formal text badges.
    - Path resolution uses config/settings.py constants where available.

Dependencies:
    - os, sys, subprocess, time: Standard library utilities.
    - requests: HTTP calls to Ollama REST API.
    - questionary: Interactive terminal selection menus.
    - dotenv: Reading and writing .env key-value pairs.
    - src.core.hardware: GPU detection, model sizing, VRAM recommendations.
    - config.settings: Canonical environment variable keys and defaults.
"""
import os
import sys
import subprocess
import time
import requests
import questionary
from dotenv import dotenv_values, set_key as _set_key

# -- Project root resolution via pathlib (clean, no sys.path hacks) --
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
_ENV_PATH = str(_PROJECT_ROOT / ".env")

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
    GEMINI_FLASH_MODEL as DEFAULT_GEMINI_FLASH,
    GEMINI_PRO_MODEL as DEFAULT_GEMINI_PRO,
    DEEPSEEK_MODEL_CHAT as DEFAULT_DEEPSEEK_MODEL,
    HF_MODEL_NAME as DEFAULT_HF_MODEL,
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
    print(f"\n  Downloading {full_name} via ollama pull...")
    print(f"  (This may take several minutes depending on size)\n")
    try:
        result = subprocess.run(
            ["ollama", "pull", full_name],
            check=False
        )
        if result.returncode == 0:
            print(f"\n  [{full_name}] installed successfully.")
            return True
        else:
            print(f"\n  Failed to pull {full_name}. Exit code: {result.returncode}")
            return False
    except FileNotFoundError:
        print("\n  ERROR: ollama command not found. Is Ollama installed?")
        return False
    except Exception as e:
        print(f"\n  ERROR pulling model: {e}")
        return False


# ---------------------------------------------------------------------------
# -- Model Catalogues (cloud provider model lists) --
# ---------------------------------------------------------------------------

GEMINI_MODELS = [
    ("gemini-2.5-flash-lite", "Fast, lightweight (free tier)"),
    ("gemini-2.5-flash", "Fast, balanced"),
    ("gemini-2.5-pro", "Most capable, slower (free tier limited)"),
    ("gemini-2.0-flash", "Previous gen flash"),
    ("gemini-1.5-flash-latest", "Stable flash"),
    ("gemini-1.5-pro-latest", "Stable pro"),
]

DEEPSEEK_MODELS = [
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
# -- Internal: shared model browsing logic (used by Fast and Heavy tiers) --
# ---------------------------------------------------------------------------

def _browse_and_pick_ollama_model(vram_gb, vram_limit, env_path, current_model_key):
    """Shared interactive model browser for Ollama tiers.

    Displays installed models, library models, and BitNet models with VRAM
    fitness badges. Returns the selected fully qualified model name or None
    if the user cancels.

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

    print(f"  Currently configured: {current_model if current_model else 'None'}")

    # -- Build model list from core.hardware --
    print("\n  Fetching available models from Ollama library...")
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

    # Build choice list with VRAM indicators
    choices = []
    current_section = None
    for m in all_models:
        section = m.get("section", "library")
        if section != current_section:
            current_section = section
            section_labels = {
                "installed": "--- [INSTALLED] ---",
                "library": "--- Available (Ollama Library) ---",
                "bitnet": "--- 1-Bit Models (Edge Devices) ---",
            }
            choices.append(questionary.Separator(f"  {section_labels.get(section, section)}"))

        label = m["name"]
        label += f" (~{m['size_gb']}GB)"
        label += _fits_label(m["fits"], m["size_gb"], vram_limit)
        if m.get("installed"):
            label += " [INSTALLED]"
        if m.get("recommended"):
            label += " [RECOMMENDED]"
        choices.append(label)

    choices.append(questionary.Separator())
    choices.append("Custom model name...")
    choices.append("Cancel")

    selected = questionary.select(
        "Select a model:",
        choices=choices,
        use_indicator=True,
    ).ask()

    if not selected or selected == "Cancel":
        return None

    if selected == "Custom model name...":
        model_name = questionary.text("Enter model name (e.g., gemma3:12b):").ask()
        if not model_name or not model_name.strip():
            return None
        model_name = model_name.strip()
    else:
        model_name = selected.split(" (")[0].strip()

    return model_name


def _pick_quantization(model_name, vram_limit, installed_models):
    """Let the user choose a quantization tag for a given base model.

    Args:
        model_name: Model name, optionally with a tag.
        vram_limit: VRAM headroom-adjusted limit in GB (or None).
        installed_models: List of currently installed model names.

    Returns:
        str or None: The chosen fully qualified model name with tag, or None if cancelled.
    """
    base_name = model_name.split(":")[0]

    print(f"\n  Fetching quantization variants for {base_name}...")
    categories = get_quantized_variants(base_name)

    quant_choices = []
    for cat_name, variants in categories.items():
        quant_choices.append(questionary.Separator(f"  {cat_name}"))
        for v in variants:
            label = v["full_name"]
            tag = v.get("tag", "")
            est_size = estimate_size_for_quant(model_name, tag) if tag else v.get("size_gb")
            if est_size and est_size > 0 and est_size < 99:
                label += f" (est. ~{est_size}GB)"
                label += _fits_label(vram_limit and est_size <= vram_limit, est_size, vram_limit)
            elif v.get("size_gb"):
                label += f" (~{v['size_gb']}GB)"
                label += _fits_label(vram_limit and v["size_gb"] <= vram_limit, v["size_gb"], vram_limit)
            if v["installed"]:
                label += " [INSTALLED]"
            quant_choices.append(label)

    quant_choices.append(questionary.Separator())
    quant_choices.append("Use base tag (no quantization suffix)")
    quant_choices.append("Cancel")

    selected_tag = questionary.select(
        f"Select quantization for {base_name}:",
        choices=quant_choices,
        use_indicator=True,
    ).ask()

    if not selected_tag or selected_tag == "Cancel":
        return None

    if selected_tag == "Use base tag (no quantization suffix)":
        return model_name
    else:
        clean = selected_tag.split(" (")[0].strip()
        return clean if ":" in clean else model_name


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
    print(f"\n  {final_model}")
    if est_size and est_size < 99:
        print(f"  Estimated size: ~{est_size}GB")
    if vram_limit and est_size and est_size > vram_limit:
        print(f"  [WARNING] This model ({est_size}GB) exceeds available VRAM ({vram_limit:.1f}GB)")
    print(f"  Model is not installed.")
    do_pull = questionary.confirm(
        f"Download {final_model} now? (ollama pull)",
        default=True
    ).ask()
    if do_pull:
        return pull_model(final_model)
    else:
        print("  Skipping download. Model not changed.")
        input("\nPress Enter to continue...")
        return False


# ---------------------------------------------------------------------------
# -- Tier Configuration Functions --
# ---------------------------------------------------------------------------

def select_fast_edge_model(env_path):
    """Configure the Fast Edge Tier model and endpoint.

    Prompts the user to select a lightweight model suitable for CPU-based
    pre-screening and quick evaluations. Writes FAST_EDGE_MODEL and
    FAST_EDGE_BASE_URL to .env.

    Args:
        env_path: Absolute path to the .env file.
    """
    os.system('cls' if os.name == 'nt' else 'clear')
    print("\n" + "=" * 62)
    print("  Fast Edge Tier Configuration (CPU / Port 11435)")
    print("=" * 62)

    if not check_ollama_alive():
        print("\n  [ERROR] Ollama server not reachable at", get_ollama_base())
        print("  Make sure Ollama is running (ollama serve).")
        input("\nPress Enter to return...")
        return

    vram_gb = detect_vram_gb()
    vram_limit = vram_gb * VRAM_HEADROOM if vram_gb else None
    if vram_gb:
        print(f"\n  GPU VRAM: {vram_gb:.1f}GB | Available for models: {vram_limit:.1f}GB (70% headroom)")
    else:
        print("\n  GPU VRAM: Not detected (no NVIDIA GPU or nvidia-smi missing)")

    print("\n  Fast Edge Tier uses a lightweight model for low-latency pre-screening.")
    print("  Recommended: fermionresearch/Neutrino-8B or similar small model.")

    values = dotenv_values(env_path)
    current_edge = values.get("FAST_EDGE_MODEL", "fermionresearch/Neutrino-8B")
    current_edge_url = values.get("FAST_EDGE_BASE_URL", "http://127.0.0.1:11435/v1")
    print(f"\n  Current Fast Edge Model: {current_edge}")
    print(f"  Current Fast Edge URL:   {current_edge_url}")

    # -- Configure endpoint URL --
    if questionary.confirm("Change Fast Edge endpoint URL?", default=False).ask():
        new_url = questionary.text(
            "Enter Fast Edge base URL:",
            default=current_edge_url
        ).ask()
        if new_url and new_url.strip():
            _set_key(env_path, "FAST_EDGE_BASE_URL", new_url.strip())
            os.environ["FAST_EDGE_BASE_URL"] = new_url.strip()
            print(f"  [FAST_EDGE_BASE_URL] set to: {new_url.strip()}")

    # -- Select model --
    model_name = _browse_and_pick_ollama_model(vram_gb, vram_limit, env_path, "FAST_EDGE_MODEL")
    if not model_name:
        return

    installed = get_installed_models()
    final_model = _pick_quantization(model_name, vram_limit, installed)
    if not final_model:
        return

    if not _install_if_needed(final_model, installed, vram_limit):
        return

    _set_key(env_path, "FAST_EDGE_MODEL", final_model)
    os.environ["FAST_EDGE_MODEL"] = final_model
    print(f"\n  [FAST_EDGE_MODEL] set to: {final_model}")
    print("  Restart TALOS or re-enter local mode for changes to take effect.")
    input("\nPress Enter to continue...")


def select_heavy_model(env_path):
    """Configure the Heavy Reasoning Tier model and endpoint.

    Prompts the user to select a large model for deep analysis and complex
    reasoning tasks. Writes HEAVY_REASONING_MODEL and OLLAMA_BASE_URL to .env.

    Args:
        env_path: Absolute path to the .env file.
    """
    os.system('cls' if os.name == 'nt' else 'clear')
    print("\n" + "=" * 62)
    print("  Heavy Reasoning Tier Configuration (GPU / Port 11434)")
    print("=" * 62)

    if not check_ollama_alive():
        print("\n  [ERROR] Ollama server not reachable at", get_ollama_base())
        print("  Make sure Ollama is running (ollama serve).")
        input("\nPress Enter to return...")
        return

    vram_gb = detect_vram_gb()
    vram_limit = vram_gb * VRAM_HEADROOM if vram_gb else None
    if vram_gb:
        print(f"\n  GPU VRAM: {vram_gb:.1f}GB | Available for models: {vram_limit:.1f}GB (70% headroom)")
    else:
        print("\n  GPU VRAM: Not detected (no NVIDIA GPU or nvidia-smi missing)")

    print("\n  Heavy Reasoning Tier uses a larger model for deep analysis tasks.")
    print("  Recommended: qwen2.5:14b or similar 7-14B parameter model.")

    values = dotenv_values(env_path)
    current_heavy = values.get("HEAVY_REASONING_MODEL", "qwen2.5:14b")
    current_heavy_url = values.get("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
    print(f"\n  Current Heavy Reasoning Model: {current_heavy}")
    print(f"  Current Ollama URL:            {current_heavy_url}")

    # -- Configure endpoint URL --
    if questionary.confirm("Change Heavy Reasoning endpoint URL?", default=False).ask():
        new_url = questionary.text(
            "Enter Ollama base URL:",
            default=current_heavy_url
        ).ask()
        if new_url and new_url.strip():
            normalized = new_url.strip().rstrip("/")
            _set_key(env_path, "OLLAMA_BASE_URL", normalized)
            os.environ["OLLAMA_BASE_URL"] = normalized
            # Also update LOCAL_MODEL_BASE_URL for backward compatibility
            _set_key(env_path, "LOCAL_MODEL_BASE_URL", normalized + "/v1")
            os.environ["LOCAL_MODEL_BASE_URL"] = normalized + "/v1"
            print(f"  [OLLAMA_BASE_URL] set to: {normalized}")

    # -- Select model --
    model_name = _browse_and_pick_ollama_model(vram_gb, vram_limit, env_path, "HEAVY_REASONING_MODEL")
    if not model_name:
        return

    installed = get_installed_models()
    final_model = _pick_quantization(model_name, vram_limit, installed)
    if not final_model:
        return

    if not _install_if_needed(final_model, installed, vram_limit):
        return

    _set_key(env_path, "HEAVY_REASONING_MODEL", final_model)
    os.environ["HEAVY_REASONING_MODEL"] = final_model
    print(f"\n  [HEAVY_REASONING_MODEL] set to: {final_model}")
    print("  Restart TALOS or re-enter local mode for changes to take effect.")
    input("\nPress Enter to continue...")


def select_cloud_models(env_path):
    """Interactive cloud model selection (Gemini, DeepSeek, Hugging Face).

    Reads current configuration from .env and config/settings.py defaults.
    Offers to configure each provider only if its API key is present.

    Args:
        env_path: Absolute path to the .env file.
    """
    os.system('cls' if os.name == 'nt' else 'clear')
    print("\n" + "=" * 62)
    print("  Cloud API Tier Configuration (Gemini / DeepSeek / HF)")
    print("=" * 62)

    values = dotenv_values(env_path)

    # -- Gemini --
    if os.getenv("GEMINI_API_KEY") or values.get("GEMINI_API_KEY"):
        print("\n" + "-" * 62)
        print("  [Gemini Models]")
        current_gemini_flash = values.get("GEMINI_FLASH_MODEL", DEFAULT_GEMINI_FLASH)
        current_gemini_pro = values.get("GEMINI_PRO_MODEL", DEFAULT_GEMINI_PRO)
        print(f"  Flash (pre-screening): {current_gemini_flash}")
        print(f"  Pro   (deep analysis): {current_gemini_pro}")

        if questionary.confirm("Configure Gemini models?", default=False).ask():
            flash_choices = [f"{m[0]} - {m[1]}" for m in GEMINI_MODELS]
            flash_sel = questionary.select(
                "Select Flash model (pre-screening):",
                choices=flash_choices + ["Cancel"],
            ).ask()
            if flash_sel and flash_sel != "Cancel":
                flash_model = flash_sel.split(" - ")[0]
                _set_key(env_path, "GEMINI_FLASH_MODEL", flash_model)
                os.environ["GEMINI_FLASH_MODEL"] = flash_model
                print(f"  [GEMINI_FLASH_MODEL] set to: {flash_model}")

            pro_sel = questionary.select(
                "Select Pro model (deep analysis):",
                choices=flash_choices + ["Cancel"],
            ).ask()
            if pro_sel and pro_sel != "Cancel":
                pro_model = pro_sel.split(" - ")[0]
                _set_key(env_path, "GEMINI_PRO_MODEL", pro_model)
                os.environ["GEMINI_PRO_MODEL"] = pro_model
                print(f"  [GEMINI_PRO_MODEL] set to: {pro_model}")

    # -- DeepSeek --
    if os.getenv("DEEPSEEK_API_KEY") or values.get("DEEPSEEK_API_KEY"):
        print("\n" + "-" * 62)
        print("  [DeepSeek Models]")
        current_ds = values.get("DEEPSEEK_MODEL_CHAT", DEFAULT_DEEPSEEK_MODEL)
        print(f"  Current: {current_ds}")

        if questionary.confirm("Configure DeepSeek model?", default=False).ask():
            ds_choices = [f"{m[0]} - {m[1]}" for m in DEEPSEEK_MODELS]
            ds_sel = questionary.select(
                "Select DeepSeek model:",
                choices=ds_choices + ["Cancel"],
            ).ask()
            if ds_sel and ds_sel != "Cancel":
                ds_model = ds_sel.split(" - ")[0]
                _set_key(env_path, "DEEPSEEK_MODEL_CHAT", ds_model)
                os.environ["DEEPSEEK_MODEL_CHAT"] = ds_model
                print(f"  [DEEPSEEK_MODEL_CHAT] set to: {ds_model}")

    # -- Hugging Face --
    if os.getenv("HF_TOKEN") or values.get("HF_TOKEN"):
        print("\n" + "-" * 62)
        print("  [Hugging Face Models]")
        current_hf = values.get("HF_MODEL_NAME", DEFAULT_HF_MODEL)
        print(f"  Current: {current_hf}")

        if questionary.confirm("Configure Hugging Face model?", default=False).ask():
            hf_sel = questionary.select(
                "Select HF model (free tier):",
                choices=HF_MODELS + ["Custom...", "Cancel"],
            ).ask()
            if hf_sel and hf_sel != "Cancel":
                if hf_sel == "Custom...":
                    custom = questionary.text("Enter HF model ID:").ask()
                    if custom and custom.strip():
                        hf_sel = custom.strip()
                    else:
                        return
                _set_key(env_path, "HF_MODEL_NAME", hf_sel)
                os.environ["HF_MODEL_NAME"] = hf_sel
                print(f"  [HF_MODEL_NAME] set to: {hf_sel}")

    input("\nPress Enter to continue...")


def select_execution_mode(env_path):
    """Configure the system execution mode.

    Sets TALOS_EXECUTION_MODE in .env to one of:
      - "local"   : Air-gapped. All inference via local Ollama tiers only.
      - "hybrid"  : Local tiers as primary, cloud providers as fallback.
      - "cloud"   : Cloud providers as primary, local as fallback.

    Args:
        env_path: Absolute path to the .env file.
    """
    os.system('cls' if os.name == 'nt' else 'clear')
    print("\n" + "=" * 62)
    print("  System Execution Mode Selector")
    print("=" * 62)

    values = dotenv_values(env_path)
    current_mode = values.get("TALOS_EXECUTION_MODE", "local")
    print(f"\n  Current Execution Mode: {current_mode}")

    print("\n  Execution modes:")
    print("    local   - Air-gapped. All inference via local Ollama tiers only.")
    print("              No cloud APIs are called. Works fully offline.")
    print("    hybrid  - Local tiers as primary, cloud providers as fallback.")
    print("              Uses cloud only when local models are unavailable or fail.")
    print("    cloud   - Cloud providers as primary, local tiers as fallback.")
    print("              Uses cloud APIs for all inference when keys are available.\n")

    mode_map = {
        "local (Air-Gapped)": "local",
        "hybrid (Local + Cloud Fallback)": "hybrid",
        "cloud (Cloud Priority)": "cloud",
    }
    choices = list(mode_map.keys()) + ["Cancel"]

    selected = questionary.select(
        "Select execution mode:",
        choices=choices,
        use_indicator=True,
    ).ask()

    if not selected or selected == "Cancel":
        return

    mode_value = mode_map[selected]
    _set_key(env_path, "TALOS_EXECUTION_MODE", mode_value)
    os.environ["TALOS_EXECUTION_MODE"] = mode_value

    # -- Update TALOS_USE_LOCAL and TALOS_ALLOW_CLOUD_FALLBACK for backward compat --
    if mode_value == "local":
        _set_key(env_path, "TALOS_USE_LOCAL", "1")
        _set_key(env_path, "TALOS_ALLOW_CLOUD_FALLBACK", "0")
        os.environ["TALOS_USE_LOCAL"] = "1"
        os.environ["TALOS_ALLOW_CLOUD_FALLBACK"] = "0"
    elif mode_value == "hybrid":
        _set_key(env_path, "TALOS_USE_LOCAL", "1")
        _set_key(env_path, "TALOS_ALLOW_CLOUD_FALLBACK", "1")
        os.environ["TALOS_USE_LOCAL"] = "1"
        os.environ["TALOS_ALLOW_CLOUD_FALLBACK"] = "1"
    elif mode_value == "cloud":
        _set_key(env_path, "TALOS_USE_LOCAL", "0")
        _set_key(env_path, "TALOS_ALLOW_CLOUD_FALLBACK", "1")
        os.environ["TALOS_USE_LOCAL"] = "0"
        os.environ["TALOS_ALLOW_CLOUD_FALLBACK"] = "1"

    print(f"\n  [TALOS_EXECUTION_MODE] set to: {mode_value}")
    print(f"  [TALOS_USE_LOCAL] set to: {os.environ.get('TALOS_USE_LOCAL', '')}")
    print(f"  [TALOS_ALLOW_CLOUD_FALLBACK] set to: {os.environ.get('TALOS_ALLOW_CLOUD_FALLBACK', '')}")
    print("  Restart TALOS for changes to take effect.")
    input("\nPress Enter to continue...")


def select_embedding_model(env_path):
    """Select the local embedding model for vector search.

    Offers a curated list of known-good embedding models, checks if they are
    installed, and offers to pull missing ones.

    Args:
        env_path: Absolute path to the .env file.
    """
    os.system('cls' if os.name == 'nt' else 'clear')
    print("\n" + "=" * 62)
    print("  Embedding Model Selection (Ollama)")
    print("=" * 62)

    if not check_ollama_alive():
        print("\n  [ERROR] Ollama not reachable.")
        input("\nPress Enter to return...")
        return

    values = dotenv_values(env_path)
    current_emb = values.get("LOCAL_EMBEDDING_MODEL", "")
    print(f"\n  Current embedding model: {current_emb if current_emb else 'Not set'}")

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

    choices = []
    for m in embedding_models:
        prefix = "[INSTALLED] " if m in installed else "[Available] "
        choices.append(f"{prefix}{m}")
    choices.append("Custom...")
    choices.append("Cancel")

    sel = questionary.select("Select embedding model:", choices=choices).ask()
    if not sel or sel == "Cancel":
        return

    model_name = sel.replace("[INSTALLED] ", "").replace("[Available] ", "").strip()
    if sel.startswith("Custom..."):
        model_name = questionary.text("Enter model name:").ask()
        if not model_name or not model_name.strip():
            return
        model_name = model_name.strip()

    # Check and pull if needed
    if model_name not in installed:
        do_pull = questionary.confirm(f"Download {model_name}?", default=True).ask()
        if do_pull:
            if not pull_model(model_name):
                input("\nPress Enter to continue...")
                return

    _set_key(env_path, "LOCAL_EMBEDDING_MODEL", model_name)
    os.environ["LOCAL_EMBEDDING_MODEL"] = model_name
    print(f"\n  [LOCAL_EMBEDDING_MODEL] set to: {model_name}")
    input("\nPress Enter to continue...")


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
    handle cancellation (questionary.select -> Cancel) gracefully.
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
        print("\n" + "=" * 62)
        print("  TALOS v5.8.0 -- Multi-Tier AI Model Management")
        print("=" * 62)

        values = dotenv_values(env_path)
        ollama_status = "[CONNECTED]" if check_ollama_alive() else "[OFFLINE]"

        print(f"\n  Ollama Status:         {ollama_status}")
        print(f"  Execution Mode:        {values.get('TALOS_EXECUTION_MODE', 'local')}")
        print(f"  Fast Edge Model:       {values.get('FAST_EDGE_MODEL', 'fermionresearch/Neutrino-8B')}")
        print(f"  Fast Edge URL:         {values.get('FAST_EDGE_BASE_URL', 'http://127.0.0.1:11435/v1')}")
        print(f"  Heavy Reasoning Model: {values.get('HEAVY_REASONING_MODEL', 'qwen2.5:14b')}")
        print(f"  Ollama Base URL:       {values.get('OLLAMA_BASE_URL', 'http://127.0.0.1:11434')}")
        print(f"  Embedding Model:       {values.get('LOCAL_EMBEDDING_MODEL', 'Not set')}")
        print(f"  Gemini Flash:          {values.get('GEMINI_FLASH_MODEL', DEFAULT_GEMINI_FLASH)}")
        print(f"  Gemini Pro:            {values.get('GEMINI_PRO_MODEL', DEFAULT_GEMINI_PRO)}")
        print(f"  DeepSeek:              {values.get('DEEPSEEK_MODEL_CHAT', DEFAULT_DEEPSEEK_MODEL)}")
        print(f"  Hugging Face:          {values.get('HF_MODEL_NAME', DEFAULT_HF_MODEL)}")

        print("\n" + "-" * 62)
        print("  [1] Configure Fast Edge Tier (CPU / Port 11435)")
        print("  [2] Configure Heavy Reasoning Tier (GPU / Port 11434)")
        print("  [3] Configure Cloud API Tier (Gemini / DeepSeek / HF)")
        print("  [4] Select System Execution Mode (Air-Gapped Local / Hybrid / Full Cloud)")
        print("  [5] Select Local Embedding Model (Ollama)")
        print("  [6] Pull Ollama Model Manually")
        print("  [7] Exit")

        choice = questionary.select(
            "Select action:",
            choices=[
                "1. Configure Fast Edge Tier (CPU / Port 11435)",
                "2. Configure Heavy Reasoning Tier (GPU / Port 11434)",
                "3. Configure Cloud API Tier (Gemini / DeepSeek / HF)",
                "4. Select System Execution Mode (Air-Gapped Local / Hybrid / Full Cloud)",
                "5. Select Local Embedding Model (Ollama)",
                "6. Pull Ollama Model Manually",
                "7. Exit",
            ],
            use_indicator=True,
        ).ask()

        if not choice or choice.startswith("7"):
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
            model = questionary.text("Enter model to pull (e.g., gemma3:12b):").ask()
            if model and model.strip():
                pull_model(model.strip())
                input("\nPress Enter to continue...")


if __name__ == "__main__":
    main()