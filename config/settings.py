# -*- coding: utf-8 -*-
"""
Module: settings.py
Project: TALOS v5.9.13
Description:
    Canonical configuration hub for TALOS v5.9.8. Defines all environment-variable
    driven settings for multi-tier LLM routing, provider endpoints, cloud LLM
    configuration, system execution mode, and system-wide constants. This module
    is the single source of truth for configuration derived from .env and config.json.

    Key design decisions:
    - Reads from environment variables with sensible defaults for air-gapped operation.
    - Supports three-tier LLM architecture: "fast" (edge/lightweight, CPU, port 11435),
      "heavy" (reasoning/large, GPU, port 11434), and "cloud" (Gemini/DeepSeek/HF).
    - v5.9.4: TALOS_EXECUTION_MODE is DEPRECATED and replaced by the 2D Execution
      Matrix: TALOS_NETWORK_STRATEGY (strict_local, local_first, cloud_first,
      strict_cloud) and TALOS_HARDWARE_STRATEGY (cpu_only, gpu_only, cpu_gpu_split).
    - Fast tier uses Neutrino-8B at a dedicated local endpoint (port 11435).
    - Heavy tier uses qwen2.5:14b at the standard Ollama endpoint (port 11434).
    - Cloud LLM providers (Gemini, DeepSeek, HuggingFace) are configured via
      environment variables for optional fallback/promotion.
    - All values can be overridden via .env for flexibility.

Dependencies:
    - os: Environment variable access.
"""
import os


# ------------------------------------------------------------------
# -- Multi-Tier LLM Routing Configuration --
# ------------------------------------------------------------------

# Fast edge model: lightweight, low-latency inference for pre-screening
# and quick evaluations. Runs on a separate Ollama instance or compatible
# OpenAI-compatible endpoint.
FAST_EDGE_MODEL = os.getenv(
    "FAST_EDGE_MODEL",
    "fermionresearch/Neutrino-8B"
)

# Base URL for the fast edge inference endpoint.
# Default: localhost port 11435 (dedicated edge Ollama instance).
FAST_EDGE_BASE_URL = os.getenv(
    "FAST_EDGE_BASE_URL",
    "http://127.0.0.1:11435/v1"
)

# Heavy reasoning model: larger model for deep analysis, complex
# evaluations, and research synthesis tasks.
HEAVY_REASONING_MODEL = os.getenv(
    "HEAVY_REASONING_MODEL",
    "qwen2.5:14b"
)

# Standard Ollama base URL for the heavy reasoning tier.
# Default: localhost port 11434 (standard Ollama instance).
OLLAMA_BASE_URL = os.getenv(
    "OLLAMA_BASE_URL",
    "http://127.0.0.1:11434"
)

# -- Legacy local model configuration (used by ai_manager.py init) --
LOCAL_MODEL_BASE_URL = OLLAMA_BASE_URL + "/v1"

# -- Default tier for requests when not explicitly specified --
DEFAULT_TIER = os.getenv("TALOS_DEFAULT_TIER", "fast")


# ------------------------------------------------------------------
# -- Cloud LLM Provider Configuration --
# ------------------------------------------------------------------

# Default cloud provider when not running entirely local.
# Supported values: "gemini", "deepseek", "huggingface".
CLOUD_PROVIDER = os.getenv("TALOS_CLOUD_PROVIDER", "gemini")

# -- Google Gemini --
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_FLASH_MODEL = os.getenv("GEMINI_FLASH_MODEL", "gemini-2.5-flash-lite")
GEMINI_PRO_MODEL = os.getenv("GEMINI_PRO_MODEL", "gemini-2.5-pro")

# -- DeepSeek --
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_MODEL_CHAT = os.getenv("DEEPSEEK_MODEL_CHAT", "deepseek-chat")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")

# -- HuggingFace Inference API --
HF_TOKEN = os.getenv("HF_TOKEN", "")
HF_MODEL_NAME = os.getenv("HF_MODEL_NAME", "mistralai/Mixtral-8x7B-Instruct-v0.1")


# ------------------------------------------------------------------
# -- System Constants --
# ------------------------------------------------------------------

# -- v5.9.4: 2D Execution Matrix (Network Strategy & Hardware Strategy) --
# Network Strategy controls whether inference is local-only, cloud-only, or
# mixed with transparent automatic fallback.
#   "strict_local" : Air-gapped. All inference via local Ollama tiers only.
#                    Cloud providers are NEVER called even if configured.
#   "local_first"  : Local tiers as primary. If a local request throws a
#                    ConnectionError, automatically fallback to cloud.
#   "cloud_first"  : Cloud providers as primary. If cloud fails (auth error,
#                    rate limit, timeout), automatically fallback to local.
#   "strict_cloud" : Pure cloud. Local tiers are NEVER called. Requires valid
#                    cloud API keys (Gemini, DeepSeek, or HuggingFace).
TALOS_NETWORK_STRATEGY = os.getenv("TALOS_NETWORK_STRATEGY", "strict_local")

# Hardware Strategy controls which local compute devices are used when
# inference is routed locally (via any network strategy that permits local).
#   "cpu_only"       : Force ALL local requests to the Fast Edge CPU endpoint
#                      (FAST_EDGE_BASE_URL, port 11435). Even heavy-tier
#                      requests run on CPU. No GPU utilization.
#   "gpu_only"       : Force ALL local requests to the standard Ollama GPU
#                      endpoint (OLLAMA_BASE_URL, port 11434). Even fast-tier
#                      requests run on GPU.
#   "cpu_gpu_split"  : Default split: fast requests on CPU (port 11435),
#                      heavy requests on GPU (port 11434). Respects the
#                      tier parameter of each request.
TALOS_HARDWARE_STRATEGY = os.getenv("TALOS_HARDWARE_STRATEGY", "cpu_gpu_split")

# -- DEPRECATED (v5.9.4): TALOS_EXECUTION_MODE --
# Replaced by TALOS_NETWORK_STRATEGY and TALOS_HARDWARE_STRATEGY.
# Retained for backward compatibility; maps to the new strategies:
#   "local"  -> network="strict_local",  hardware="cpu_gpu_split"
#   "hybrid" -> network="local_first",   hardware="cpu_gpu_split"
#   "cloud"  -> network="cloud_first",   hardware="cpu_gpu_split"
# If TALOS_NETWORK_STRATEGY is explicitly set, this legacy key is ignored.
TALOS_EXECUTION_MODE = os.getenv("TALOS_EXECUTION_MODE", "local")

# Project version string -- updated with each release.
TALOS_VERSION = "5.9.13"

# -- v5.9.1: Per-Tier Routing Configuration --
# Controls where each tier routes its inference requests.
#   "local"  : Route to local Ollama instance (CPU for fast, GPU for heavy).
#   "cloud"  : Route to cloud API provider (Gemini/DeepSeek/HF).
TALOS_FAST_ROUTING = os.getenv("TALOS_FAST_ROUTING", "local")
TALOS_HEAVY_ROUTING = os.getenv("TALOS_HEAVY_ROUTING", "local")

# TALOS FastAPI port (port 8000 is reserved for SYNAPSE event bus).
TALOS_API_PORT = int(os.getenv("TALOS_API_PORT", "8001"))

# SYNAPSE event bus URL for outbound events.
SYNAPSE_BUS_URL = os.getenv(
    "SYNAPSE_BUS_URL",
    "http://localhost:8000/api/v1/events"
)