# -*- coding: utf-8 -*-
#  Project TALOS - Hardware Detection Module
#  Copyright (C) 2026 Christos Smarlamakis
"""
Module: hardware.py
Project: TALOS v4.8.5

Description:
    Auto-detects GPU VRAM via nvidia-smi and recommends the best local
    Ollama model for the available hardware. Contains a database of
    approximate 4-bit quantized model sizes for 20+ models and a
    recommendation lookup table based on VRAM tiers.

    Used by :class:`AIManager` during local model initialization to
    suggest an appropriate model if the user has not specified one.
"""
import subprocess

# Approx 4-bit quantized sizes in GB
MODEL_SIZES = {
    "gemma3:12b": 8, "gemma2:9b": 6, "gemma2:2b": 1.5,
    "llama3.2:3b": 2, "llama3.1:8b": 5, "llama3.3:70b": 43,
    "mistral:7b": 4.5, "mixtral:8x7b": 26, "command-r:35b": 22,
    "qwen2.5:14b": 10, "qwen2.5:7b": 5, "qwen2.5:3b": 2, "qwen2.5:0.5b": 0.4,
    "phi4:14b": 10, "phi3:3.8b": 2.5,
    "nomic-embed-text": 0.3,
}

# VRAM tier (GB) -> recommended model
RECOMMENDED = {
    24: "qwen2.5:14b", 16: "gemma3:12b", 12: "llama3.1:8b",
    8: "qwen2.5:7b", 6: "qwen2.5:3b", 4: "qwen2.5:0.5b", 0: "qwen2.5:0.5b",
}


def detect_vram_gb():
    """Auto-detect GPU VRAM via nvidia-smi.

    Returns:
        float or None: Total VRAM in GB, or None if detection fails.
    """
    try:
        r = subprocess.run(
            ["nvidia-smi", "--query-gpu=memory.total", "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=5)
        if r.returncode == 0:
            return int(r.stdout.strip().split("\n")[0]) / 1024
    except Exception:
        pass
    return None


def recommend_model(preferred="gemma3:12b"):
    """Recommend the best Ollama model for the available VRAM.

    If the user's preferred model fits within 85% of available VRAM,
    it is returned. Otherwise, the best model from the RECOMMENDED
    lookup table is chosen.

    Args:
        preferred (str): User's preferred model name (e.g., ``"gemma3:12b"``).

    Returns:
        tuple: ``(model_name, vram_gb)`` where model_name is the
        recommended model string and vram_gb is the detected VRAM.
    """
    vram = detect_vram_gb()
    if preferred and vram:
        size = MODEL_SIZES.get(preferred, 99)
        if size < vram * 0.85:
            return preferred, vram
        print(f"  >> {preferred} (~{size}GB) too large for {vram:.1f}GB VRAM.")
    if vram:
        for tier, model in sorted(RECOMMENDED.items(), reverse=True):
            if vram >= tier:
                print(f"  >> Recommended: {model} (~{MODEL_SIZES.get(model, '?')}GB)")
                return model, vram
    return RECOMMENDED[0], 0


def estimate_size(model_name):
    """Return the estimated 4-bit quantized size of a model in GB.

    Args:
        model_name (str): Model identifier (e.g., ``"gemma3:12b"``).

    Returns:
        float: Estimated size in GB, or 99 if unknown.
    """
    base = model_name.split(":")[0] if ":" in model_name else model_name
    tag = model_name.split(":")[1] if ":" in model_name else ""
    key = f"{base}:{tag}" if tag else base
    return MODEL_SIZES.get(key, 99)