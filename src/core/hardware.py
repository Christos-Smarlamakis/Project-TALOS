# -*- coding: utf-8 -*-
#  Project TALOS - Hardware Detection Module
#  Copyright (C) 2026 Christos Smarlamakis
"""
Module: hardware.py
Project: TALOS v5.9.15

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
        if size < vram * VRAM_HEADROOM:
            return preferred, vram
        print(f"  >> {preferred} (~{size}GB) too large for {vram:.1f}GB VRAM.")
    if vram:
        for tier, model in sorted(RECOMMENDED.items(), reverse=True):
            if vram >= tier:
                print(f"  >> Recommended: {model} (~{MODEL_SIZES.get(model, '?')}GB)")
                return model, vram
    return RECOMMENDED[0], 0


# ═══════════════════════════════════════════════════════════════════════════════
#  QUANTIZATION SIZE ESTIMATION
# ═══════════════════════════════════════════════════════════════════════════════
# Per-quantization GB per 1B parameters (empirical averages across model families)
QUANT_SIZE_PER_BILLION = {
    "q8_0": 1.00,     # 8-bit: ~1.0 GB per 1B params
    "q8": 1.00,
    "q6_K": 0.75,     # 6-bit: ~0.75 GB per 1B params
    "q6": 0.75,
    "q5_K_M": 0.60,   # 5-bit: ~0.60 GB per 1B params
    "q5_K_S": 0.58,
    "q5_0": 0.55,
    "q5_1": 0.56,
    "q5": 0.58,
    "q4_K_M": 0.55,   # 4-bit: ~0.55 GB per 1B params
    "q4_K_S": 0.52,
    "q4_0": 0.50,
    "q4_1": 0.52,
    "q4": 0.55,
    "iq4_nl": 0.48,   # IQ4 (importance-aware 4-bit): ~0.48 GB per 1B
    "iq4_xs": 0.42,
    "q3_K_L": 0.38,   # 3-bit: ~0.38 GB per 1B params
    "q3_K_M": 0.35,
    "q3_K_S": 0.32,
    "q3": 0.35,
    "iq3_m": 0.32,    # IQ3 (importance-aware 3-bit): ~0.32 GB per 1B
    "iq3_s": 0.28,
    "iq3_xs": 0.26,
    "q2_K": 0.28,     # 2-bit: ~0.28 GB per 1B params
    "q2": 0.28,
    "iq2_m": 0.26,    # IQ2 (importance-aware 2-bit): ~0.26 GB per 1B
    "iq2_s": 0.24,
    "iq2_xs": 0.22,
    "iq2_xxs": 0.20,
    "q1_0": 0.20,     # 1-bit: ~0.20 GB per 1B params
    "q1": 0.20,
    "iq1_m": 0.18,
    "iq1_s": 0.16,
}
# VRAM headroom multiplier (30% reserved for OS + other tasks)
VRAM_HEADROOM = 0.70


def extract_params_b(model_name):
    """Extract parameter count in billions from a model name.
    
    Args:
        model_name (str): e.g. 'gemma4:12b', 'llama3.3:70b', 'mistral:7b'
    
    Returns:
        float or None: Parameter count in billions, or None if unparseable.
    """
    import re
    name = model_name.lower()
    for pattern in [r'(\d+\.?\d*)b\b', r'(\d+\.?\d*)-b\b', r':(\d+\.?\d*)b\b']:
        match = re.search(pattern, name)
        if match:
            return float(match.group(1))
    return None


def estimate_size_for_quant(model_name, quant_tag=None):
    """Estimate model size in GB for a given quantization level.
    
    Uses the formula: size_gb = params_billions * QUANT_SIZE_PER_BILLION[quant].
    Falls back to MODEL_SIZES lookup if quantization unknown.
    
    Args:
        model_name (str): Model name (e.g. 'gemma4:12b', 'llama3.3:70b')
        quant_tag (str, optional): Quant tag (e.g. 'q4_K_M', 'q2_K'). 
                                   If None, assumes 4-bit (default).
    
    Returns:
        float: Estimated size in GB. Returns 99 if estimation impossible.
    """
    params = extract_params_b(model_name)
    if params is None:
        # Fall back to MODEL_SIZES
        base = model_name.split(":")[0] if ":" in model_name else model_name
        return MODEL_SIZES.get(base, OLLAMA_LIBRARY_FALLBACK.get(base, 99))
    
    if quant_tag:
        # Normalize: strip prefix like 'q4_K_M' -> main key
        quant_key = quant_tag.lower().replace("_", "")
        for known_key, gb_per_billion in sorted(QUANT_SIZE_PER_BILLION.items(), 
                                                  key=lambda x: -len(x[0])):
            if quant_key.startswith(known_key.replace("_", "")):
                return round(params * gb_per_billion, 1)
    
    # Default: assume Q4_K_M (~0.55 GB per 1B)
    return round(params * 0.55, 1)


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


def get_installed_models():
    """Query Ollama API for locally installed models.

    Returns:
        list of str: Names of installed models (e.g., ['gemma3:12b', 'nomic-embed-text']).
        Returns empty list if Ollama is not reachable.
    """
    import requests
    try:
        resp = requests.get("http://localhost:11434/api/tags", timeout=5)
        if resp.status_code == 200:
            return [m['name'] for m in resp.json().get('models', [])]
    except Exception:
        pass
    return []


def get_all_chat_models_sorted(vram_gb=None):
    """Get all chat models sorted by VRAM fit.
    
    Returns list of dicts: {name, size_gb, fits, installed, recommended}
    Excludes embedding models (nomic-embed-text).
    
    Args:
        vram_gb (float, optional): Available VRAM. If None, auto-detects.
    """
    if vram_gb is None:
        vram_gb = detect_vram_gb() or 99
    installed = get_installed_models()
    recommended_name = RECOMMENDED.get(0, "qwen2.5:0.5b")
    if vram_gb and vram_gb < 99:
        for tier, model in sorted(RECOMMENDED.items(), reverse=True):
            if vram_gb >= tier:
                recommended_name = model
                break
    
    models = []
    for name, size in MODEL_SIZES.items():
        # Skip embedding models
        if "embed" in name.lower():
            continue
        fits = size <= vram_gb * VRAM_HEADROOM if vram_gb else True
        models.append({
            "name": name,
            "size_gb": size,
            "fits": fits,
            "installed": name in installed,
            "recommended": name == recommended_name,
        })
    
    # Sort: recommended first, then by size ascending (smaller = more likely to fit)
    models.sort(key=lambda m: (not m["recommended"], m["size_gb"]))
    return models


def get_embedding_models():
    """Get available embedding models.
    
    Returns list of dicts: {name, size_gb, installed}
    """
    installed = get_installed_models()
    embedding_models = []
    for name, size in MODEL_SIZES.items():
        if "embed" in name.lower():
            embedding_models.append({
                "name": name,
                "size_gb": size,
                "installed": name in installed,
            })
    return embedding_models if embedding_models else [{"name": "nomic-embed-text", "size_gb": 0.3, "installed": "nomic-embed-text" in installed}]


# ═══════════════════════════════════════════════════════════════════════════════
# 1-BIT QUANTIZED MODELS (BitNet b1.58) — ~0.2 GB per 1B parameters
# These are GGUF models from Hugging Face that can be imported into Ollama.
# ═══════════════════════════════════════════════════════════════════════════════
BITNET_MODELS = [
    {"name": "BitNet-b1.58-3B", "size_gb": 0.6, "hf_repo": "1bitLLM/BitNet-b1.58-3B-GGUF", "description": "3B params, 1.58-bit"},
    {"name": "BitNet-b1.58-7B", "size_gb": 1.5, "hf_repo": "1bitLLM/BitNet-b1.58-7B-GGUF", "description": "7B params, 1.58-bit"},
    {"name": "BitNet-b1.58-13B", "size_gb": 2.5, "hf_repo": "1bitLLM/BitNet-b1.58-13B-GGUF", "description": "13B params, 1.58-bit"},
    {"name": "BitLlama-1.58-3B", "size_gb": 0.6, "hf_repo": "hf-llm-bitnet/bitllama-3b-1.58-GGUF", "description": "Llama-3B, 1.58-bit"},
    {"name": "BitLlama-1.58-8B", "size_gb": 1.6, "hf_repo": "hf-llm-bitnet/bitllama-8b-1.58-GGUF", "description": "Llama-8B, 1.58-bit"},
    {"name": "TriLite-1.58B", "size_gb": 0.35, "hf_repo": "microsoft/TriLite-GGUF", "description": "1.58B params, ternary"},
    {"name": "BitDelta-1.58-7B", "size_gb": 1.5, "hf_repo": "microsoft/BitDelta-GGUF", "description": "7B delta, 1-bit"},
]

# Well-known Ollama library models (fetched dynamically as fallback)
OLLAMA_LIBRARY_FALLBACK = {
    "llama3.2:3b": 2, "llama3.2:1b": 0.8, "llama3.1:8b": 5, "llama3.1:70b": 43,
    "gemma3:12b": 8, "gemma3:4b": 3, "gemma2:9b": 6, "gemma2:2b": 1.5,
    "mistral:7b": 4.5, "mixtral:8x7b": 26, "qwen2.5:14b": 10, "qwen2.5:7b": 5,
    "qwen2.5:3b": 2, "qwen2.5:0.5b": 0.4, "phi4:14b": 10, "phi3:3.8b": 2.5,
    "command-r:35b": 22, "deepseek-r1:7b": 4.5, "deepseek-r1:14b": 9,
    "deepseek-coder-v2:16b": 10, "codellama:7b": 4, "codellama:13b": 8,
    "nomic-embed-text": 0.3, "mxbai-embed-large": 0.7,
}


def get_ollama_library_models(vram_gb=None):
    """
    Fetch popular models from Ollama library (dynamically from internet).
    Falls back to hardcoded OLLAMA_LIBRARY_FALLBACK if API unreachable.
    
    Returns list of dicts: {name, size_gb, fits}
    """
    import requests
    if vram_gb is None:
        vram_gb = detect_vram_gb() or 99
    
    models = []
    
    # Try fetching from Ollama API
    try:
        resp = requests.get("https://ollama.com/api/tags", timeout=8)
        if resp.status_code == 200:
            data = resp.json()
            for m in data.get("models", [])[:60]:
                name = m.get("name", "")
                # Estimate size from parameter count in name (e.g., "7b" ≈ 4GB at 4-bit)
                size = MODEL_SIZES.get(name, 99)
                if size == 99:
                    # Try to estimate from name
                    for param_str in ["70b", "35b", "14b", "12b", "8b", "7b", "3b", "2b", "1b", "0.5b"]:
                        if param_str in name.lower():
                            params = float(param_str.replace("b", ""))
                            size = params * 0.7
                            break
                if size <= vram_gb * VRAM_HEADROOM:
                    models.append({"name": name, "size_gb": round(size, 1), "fits": True})
    except Exception:
        pass
    
    # Fallback: use hardcoded library if API failed or returned few results
    if len(models) < 5:
        for name, size in OLLAMA_LIBRARY_FALLBACK.items():
            if "embed" in name.lower():
                continue
            if name not in [m["name"] for m in models]:
                fits = size <= vram_gb * VRAM_HEADROOM if vram_gb else True
                models.append({"name": name, "size_gb": size, "fits": fits})
    
    return models


def get_bitnet_models(vram_gb=None):
    """
    Get 1-bit quantized models suitable for edge devices.
    These models use ~0.2 GB per 1B parameters (1.58-bit quantization).
    
    Returns list of dicts: {name, size_gb, fits, hf_repo, description}
    """
    if vram_gb is None:
        vram_gb = detect_vram_gb() or 99
    
    models = []
    for m in BITNET_MODELS:
        fits = m["size_gb"] <= vram_gb * VRAM_HEADROOM if vram_gb else True
        models.append({
            "name": m["name"],
            "size_gb": m["size_gb"],
            "fits": fits,
            "hf_repo": m["hf_repo"],
            "description": m["description"],
            "section": "bitnet",
        })
    return models


def get_all_chat_models_sorted(vram_gb=None):
    """Get all chat models sorted by VRAM fit, organized in 3 sections:
    1. Currently installed (via Ollama)
    2. Ollama library (available from internet)
    3. BitNet 1-bit quantized models (for edge devices)
    
    Returns list of dicts: {name, size_gb, fits, installed, recommended, section}
    """
    if vram_gb is None:
        vram_gb = detect_vram_gb() or 99
    installed = get_installed_models()
    recommended_name = RECOMMENDED.get(0, "qwen2.5:0.5b")
    if vram_gb and vram_gb < 99:
        for tier, model in sorted(RECOMMENDED.items(), reverse=True):
            if vram_gb >= tier:
                recommended_name = model
                break
    
    # Global model list
    models = []
    
    # ── Section 1: Installed models ──
    for name in installed:
        if "embed" in name.lower():
            continue
        size = MODEL_SIZES.get(name, estimate_size(name))
        fits = size <= vram_gb * VRAM_HEADROOM if vram_gb else True
        models.append({
            "name": name, "size_gb": size, "fits": fits,
            "installed": True, "recommended": name == recommended_name,
            "section": "installed",
        })
    
    # ── Section 2: Ollama library (not installed) ──
    library = get_ollama_library_models(vram_gb)
    for m in library:
        if m["name"] in [x["name"] for x in models]:
            continue
        size = m["size_gb"]
        if size > vram_gb * VRAM_HEADROOM:
            continue
        models.append({
            "name": m["name"], "size_gb": size, "fits": True,
            "installed": False, "recommended": False,
            "section": "library",
        })
    
    # ── Section 3: BitNet 1-bit models ──
    bitnet = get_bitnet_models(vram_gb)
    for m in bitnet:
        if m["name"] in [x["name"] for x in models]:
            continue
        models.append({
            "name": m["name"], "size_gb": m["size_gb"], "fits": m["fits"],
            "installed": False, "recommended": False,
            "section": "bitnet", "hf_repo": m.get("hf_repo"),
            "description": m.get("description", ""),
        })
    
    # Sort: installed first, then library, then bitnet. Within each, by size ascending
    section_order = {"installed": 0, "library": 1, "bitnet": 2}
    models.sort(key=lambda m: (section_order.get(m.get("section", "library"), 99), m["size_gb"]))
    return models


def pull_model(model_name):
    """Pull a model via Ollama CLI. Returns True on success."""
    import subprocess as sp
    try:
        r = sp.run(["ollama", "pull", model_name], capture_output=True, text=True, timeout=600)
        return r.returncode == 0
    except Exception:
        return False
