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
Module: model_manager.py (v4.10.1)
Project: TALOS v4.10.1

Description:
    Interactive TUI for selecting and managing AI models across all providers.
    Supports Ollama (local) with quantization-aware model selection, plus
    cloud providers (Gemini, DeepSeek, Hugging Face).

    Features:
    - List installed + available Ollama models
    - Detect all quantization tags (Q8, Q4_K_M, Q2_K, etc.) via ollama show
    - Group tags by bit-depth (8-bit, 4-bit, 2-bit, 1-bit)
    - Auto-download missing models via ollama pull
    - Cloud model selection for Gemini, DeepSeek, Hugging Face
    - Save selections to .env
"""
import os
import subprocess
import sys
import json
import requests
import questionary
from dotenv import dotenv_values, set_key as _set_key
import time

# Ensure project root is in path so we can import core.hardware
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from core.hardware import (
    detect_vram_gb,
    get_installed_models,
    get_all_chat_models_sorted,
    get_embedding_models,
    get_ollama_library_models,
    get_bitnet_models,
    estimate_size_for_quant,
    extract_params_b,
    VRAM_HEADROOM,
    QUANT_SIZE_PER_BILLION,
    OLLAMA_LIBRARY_FALLBACK,
    pull_model as hw_pull_model,
)


def get_ollama_base():
    """Return the Ollama base URL from env or default."""
    return os.getenv("LOCAL_MODEL_BASE_URL", "http://localhost:11434").rstrip("/v1").rstrip("/")


def check_ollama_alive():
    """Check if Ollama server is reachable."""
    base = get_ollama_base()
    try:
        r = requests.get(f"{base}/api/tags", timeout=5)
        return r.status_code == 200
    except Exception:
        return False


def get_installed_models():
    """Return list of installed model names from Ollama."""
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

    Returns a list of dicts: {tag, size, estimated_vram_gb, bit_label}
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
        # Parse the output for tags and their sizes
        # Typical ollama show output format varies; try to find quantized tags
        in_tags = False
        for line in output.splitlines():
            line = line.strip()
            if "Tags:" in line:
                in_tags = True
                continue
            if in_tags and line and not line.startswith("---") and not line.startswith("License"):
                # Parse tag lines like: "q4_K_M    7.1 GB" or "q8_0    12.3 GB"
                parts = line.split()
                if len(parts) >= 2:
                    tag = parts[0]
                    # Check if second part looks like a size
                    try:
                        size_str = parts[1]
                        multiplier = 1.0
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

    Falls back to known quantization patterns if ollama show returns nothing.
    """
    base = model_base_name.split(":")[0] if ":" in model_base_name else model_base_name
    installed_full = get_installed_models()
    installed_base = {m.split(":")[0]: m for m in installed_full}

    # Try ollama show for structured tag listing
    detailed_tags = get_available_tags(base)

    if detailed_tags:
        return _categorize_tags(detailed_tags, base, installed_full)

    # Fallback: check if there are installed variants already
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

    # No variants found: provide common quantization options
    common_tags = ["q8_0", "q4_K_M", "q4_0", "q2_K", "q1_0"]
    for tag in common_tags:
        variants.append({
            "tag": tag,
            "size_gb": None,
            "full_name": f"{base}:{tag}",
        })

    return _categorize_tags(variants, base, installed_full)


def _categorize_tags(tags, base, installed_full):
    """Categorize tags into bit-depth groups and mark installed."""
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

        if "q8" in tag.lower() or "q_8" in tag.lower():
            result["8-bit (Q8)"].append(entry)
        elif "q6" in tag.lower():
            result["6-bit (Q6)"].append(entry)
        elif "q5" in tag.lower():
            result["4-bit (Q4)"].append(entry)  # Q5 grouped with Q4
        elif "q4" in tag.lower() or "q_4" in tag.lower():
            result["4-bit (Q4)"].append(entry)
        elif "q3" in tag.lower() or "q_3" in tag.lower():
            result["3-bit (Q3/Q2)"].append(entry)
        elif "q2" in tag.lower() or "q_2" in tag.lower():
            result["2-bit (Q2)"].append(entry)
        elif "q1" in tag.lower() or "q_1" in tag.lower():
            result["1-bit (Q1)"].append(entry)
        else:
            result["Other / No tag"].append(entry)

    # Remove empty categories
    return {k: v for k, v in result.items() if v}


def pull_model(full_name):
    """Pull a model from Ollama with real-time progress."""
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


# --- Cloud Model Selection ---

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


def _fits_label(fits, size_gb, vram_limit):
    """Return a fitness indicator label based on VRAM headroom."""
    if not size_gb or not vram_limit:
        return ""
    ratio = size_gb / vram_limit if vram_limit > 0 else 999
    if ratio <= 0.7:
        return " [FITS \u2713]"
    elif ratio <= 1.0:
        return " [TIGHT ~]"
    else:
        return " [TOO BIG \u2717]"


def select_ollama_model(env_path):
    """Interactive Ollama model selection with quantization support."""
    os.system('cls' if os.name == 'nt' else 'clear')
    print("\n" + "=" * 62)
    print("  Ollama Model Selection")
    print("=" * 62)

    if not check_ollama_alive():
        print("\n  [ERROR] Ollama server not reachable at", get_ollama_base())
        print("  Make sure Ollama is running (ollama serve).")
        input("\nPress Enter to return...")
        return

    # Detect VRAM
    vram_gb = detect_vram_gb()
    vram_limit = vram_gb * VRAM_HEADROOM if vram_gb else None
    if vram_gb:
        print(f"\n  GPU VRAM: {vram_gb:.1f}GB | Available for models: {vram_limit:.1f}GB (70% headroom)")
    else:
        print("\n  GPU VRAM: Not detected (no NVIDIA GPU or nvidia-smi missing)")

    installed = get_installed_models()
    values = dotenv_values(env_path)
    current_model = values.get("LOCAL_MODEL_NAME", "")

    print(f"  Currently configured: {current_model if current_model else 'None'}")

    # Build dynamic model list from core.hardware
    print("\n  Fetching available models from Ollama library...")
    all_models = get_all_chat_models_sorted(vram_gb)

    # Add library models that might be larger than VRAM limit (show them too, with warning)
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

    # Re-sort
    section_order = {"installed": 0, "library": 1, "bitnet": 2}
    all_models.sort(key=lambda m: (section_order.get(m.get("section", "library"), 99), m["size_gb"]))

    # Build choice list with VRAM indicators
    choices = []
    current_section = None
    for m in all_models:
        section = m.get("section", "library")
        if section != current_section:
            current_section = section
            section_labels = {"installed": "--- Installed ---", "library": "--- Available (Ollama Library) ---", "bitnet": "--- 1-Bit Models (Edge Devices) ---"}
            choices.append(questionary.Separator(f"  {section_labels.get(section, section)}"))

        label = m["name"]
        label += f" (~{m['size_gb']}GB)"
        label += _fits_label(m["fits"], m["size_gb"], vram_limit)
        if m.get("installed"):
            label += " [Installed]"
        if m.get("recommended"):
            label += " [Recommended]"
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
        return

    if selected == "Custom model name...":
        model_name = questionary.text("Enter model name (e.g., gemma3:12b):").ask()
        if not model_name or not model_name.strip():
            return
        model_name = model_name.strip()
    else:
        # Extract model name from label (before any annotation)
        model_name = selected.split(" (")[0].strip()

    base_name = model_name.split(":")[0]

    # Now show quantization options with VRAM estimates
    print(f"\n  Fetching quantization variants for {base_name}...")
    categories = get_quantized_variants(base_name)

    # Build flat list of quantized choices with VRAM estimates
    quant_choices = []
    for cat_name, variants in categories.items():
        quant_choices.append(questionary.Separator(f"  {cat_name}"))
        for v in variants:
            label = v["full_name"]
            # Calculate estimated VRAM for this quant
            tag = v.get("tag", "")
            est_size = estimate_size_for_quant(model_name, tag) if tag else v.get("size_gb")
            if est_size and est_size > 0 and est_size < 99:
                label += f" (est. ~{est_size}GB)"
                label += _fits_label(vram_limit and est_size <= vram_limit, est_size, vram_limit)
            elif v.get("size_gb"):
                label += f" (~{v['size_gb']}GB)"
                label += _fits_label(vram_limit and v["size_gb"] <= vram_limit, v["size_gb"], vram_limit)
            if v["installed"]:
                label += " [Installed]"
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
        return

    if selected_tag == "Use base tag (no quantization suffix)":
        final_model = model_name
    else:
        # Extract the full name from the label (before any annotation)
        clean = selected_tag.split(" (")[0].strip()
        final_model = clean if ":" in clean else model_name

    # Check if model with this tag is installed
    if final_model not in installed:
        # Show estimated VRAM impact
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
            success = pull_model(final_model)
            if not success:
                print("  Download failed. Model not changed.")
                input("\nPress Enter to continue...")
                return
        else:
            print("  Skipping download. Model not changed.")
            input("\nPress Enter to continue...")
            return

    # Save to .env
    _set_key(env_path, "LOCAL_MODEL_NAME", final_model)
    os.environ["LOCAL_MODEL_NAME"] = final_model
    print(f"\n  [LOCAL_MODEL_NAME] set to: {final_model}")
    print("  Restart TALOS or re-enter local mode for changes to take effect.")
    input("\nPress Enter to continue...")


def select_cloud_models(env_path):
    """Interactive cloud model selection (Gemini, DeepSeek, HF)."""
    os.system('cls' if os.name == 'nt' else 'clear')
    print("\n" + "=" * 62)
    print("  Cloud Model Configuration")
    print("=" * 62)

    values = dotenv_values(env_path)

    # --- Gemini ---
    if os.getenv("GEMINI_API_KEY") or values.get("GEMINI_API_KEY"):
        print("\n" + "-" * 62)
        print("  [Gemini Models]")
        current_gemini_flash = values.get("GEMINI_FLASH_MODEL", "gemini-2.5-flash-lite")
        current_gemini_pro = values.get("GEMINI_PRO_MODEL", "gemini-2.5-pro")
        print(f"  Flash (pre-screening): {current_gemini_flash}")
        print(f"  Pro   (deep analysis): {current_gemini_pro}")

        if questionary.confirm("Configure Gemini models?", default=False).ask():
            # Flash model
            flash_choices = [f"{m[0]} - {m[1]}" for m in GEMINI_MODELS]
            flash_sel = questionary.select(
                "Select Flash model (pre-screening):",
                choices=flash_choices + ["Cancel"],
            ).ask()
            if flash_sel and flash_sel != "Cancel":
                flash_model = flash_sel.split(" - ")[0]
                _set_key(env_path, "GEMINI_FLASH_MODEL", flash_model)
                os.environ["GEMINI_FLASH_MODEL"] = flash_model
                print(f"  Flash model set to: {flash_model}")

            # Pro model
            pro_sel = questionary.select(
                "Select Pro model (deep analysis):",
                choices=flash_choices + ["Cancel"],
            ).ask()
            if pro_sel and pro_sel != "Cancel":
                pro_model = pro_sel.split(" - ")[0]
                _set_key(env_path, "GEMINI_PRO_MODEL", pro_model)
                os.environ["GEMINI_PRO_MODEL"] = pro_model
                print(f"  Pro model set to: {pro_model}")

    # --- DeepSeek ---
    if os.getenv("DEEPSEEK_API_KEY") or values.get("DEEPSEEK_API_KEY"):
        print("\n" + "-" * 62)
        print("  [DeepSeek Models]")
        current_ds = values.get("DEEPSEEK_MODEL_CHAT", "deepseek-chat")
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
                print(f"  DeepSeek model set to: {ds_model}")

    # --- Hugging Face ---
    if os.getenv("HF_TOKEN") or values.get("HF_TOKEN"):
        print("\n" + "-" * 62)
        print("  [Hugging Face Models]")
        current_hf = os.getenv("HF_MODEL_NAME", values.get("HF_MODEL_NAME", "Not set"))
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
                print(f"  HF model set to: {hf_sel}")

    input("\nPress Enter to continue...")


def select_embedding_model(env_path):
    """Select the local embedding model for vector search."""
    os.system('cls' if os.name == 'nt' else 'clear')
    print("\n" + "=" * 62)
    print("  Embedding Model Selection")
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
        prefix = "[Installed] " if m in installed else "[Available] "
        choices.append(f"{prefix}{m}")
    choices.append("Custom...")
    choices.append("Cancel")

    sel = questionary.select("Select embedding model:", choices=choices).ask()
    if not sel or sel == "Cancel":
        return

    model_name = sel.replace("[Installed] ", "").replace("[Available] ", "").strip()
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


# --- Main Entry Point ---

def main():
    """Main TUI loop for model management."""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    env_path = os.path.join(project_root, '.env')

    # Ensure .env exists
    if not os.path.exists(env_path):
        example_path = os.path.join(project_root, 'example.env')
        if os.path.exists(example_path):
            import shutil
            shutil.copy(example_path, env_path)
        else:
            open(env_path, 'w').close()

    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        print("\n" + "=" * 62)
        print("  AI Model Management (v4.10.1)")
        print("=" * 62)

        values = dotenv_values(env_path)
        ollama_status = "Connected" if check_ollama_alive() else "Offline"

        print(f"\n  [Ollama Status] {ollama_status}")
        print(f"  [Local Chat Model]   {values.get('LOCAL_MODEL_NAME', 'Not set')}")
        print(f"  [Local Embedding]    {values.get('LOCAL_EMBEDDING_MODEL', 'Not set')}")
        print(f"  [Gemini Flash]       {values.get('GEMINI_FLASH_MODEL', 'gemini-2.5-flash-lite')}")
        print(f"  [Gemini Pro]         {values.get('GEMINI_PRO_MODEL', 'gemini-2.5-pro')}")
        print(f"  [DeepSeek]           {values.get('DEEPSEEK_MODEL_CHAT', 'deepseek-chat')}")
        print(f"  [Hugging Face]       {os.getenv('HF_MODEL_NAME', values.get('HF_MODEL_NAME', 'Not set'))}")

        print("\n" + "-" * 62)
        print("  [1] Select Local Chat Model (Ollama)")
        print("  [2] Select Local Embedding Model (Ollama)")
        print("  [3] Configure Cloud Models (Gemini / DeepSeek / HF)")
        print("  [4] Pull a Model Manually (ollama pull)")
        print("  [5] Back")

        choice = questionary.select(
            "Select action:",
            choices=[
                "1. Select Local Chat Model (Ollama)",
                "2. Select Local Embedding Model (Ollama)",
                "3. Configure Cloud Models (Gemini / DeepSeek / HF)",
                "4. Pull a Model Manually (ollama pull)",
                "5. Back",
            ],
            use_indicator=True,
        ).ask()

        if not choice or choice.startswith("5"):
            break

        if choice.startswith("1"):
            select_ollama_model(env_path)
        elif choice.startswith("2"):
            select_embedding_model(env_path)
        elif choice.startswith("3"):
            select_cloud_models(env_path)
        elif choice.startswith("4"):
            model = questionary.text("Enter model to pull (e.g., gemma3:12b):").ask()
            if model and model.strip():
                pull_model(model.strip())
                input("\nPress Enter to continue...")


if __name__ == "__main__":
    main()