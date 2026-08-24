# -*- coding: utf-8 -*-
"""
Module: settings.py
Project: TALOS v5.10.10
Description:
    Canonical configuration hub for TALOS v5.10.10. Defines all environment-variable
    driven settings for multi-tier LLM routing, provider endpoints, cloud LLM
    configuration, system execution mode, and system-wide constants. This module
    is the single source of truth for configuration derived from .env and config.json.

    Key design decisions:
    - Reads from environment variables with sensible defaults for air-gapped operation.
    - Supports three-tier LLM architecture: "fast" (edge/lightweight, CPU, port 11435),
      "heavy" (reasoning/large, GPU, port 11434), and "cloud" (Universal Cloud
      Mesh, 8 providers).
    - v5.9.4: TALOS_EXECUTION_MODE is DEPRECATED and replaced by the 2D Execution
      Matrix: TALOS_NETWORK_STRATEGY (strict_local, local_first, cloud_first,
      strict_cloud) and TALOS_HARDWARE_STRATEGY (cpu_only, gpu_only, cpu_gpu_split).
    - Fast tier uses Neutrino-8B at a dedicated local endpoint (port 11435).
    - Heavy tier uses qwen2.5:14b at the standard Ollama endpoint (port 11434).
    - Cloud LLM providers (Gemini, NVIDIA NIM, Groq, Cerebras, GitHub Models,
      Mistral, OpenRouter, DeepSeek, HuggingFace) are configured via environment
      variables for optional redundancy/failover (v5.9.18 Universal Cloud Mesh).
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
# Supported values: "gemini", "nvidia", "groq", "cerebras", "github",
# "mistral", "openrouter", "deepseek", "huggingface".
CLOUD_PROVIDER = os.getenv("TALOS_CLOUD_PROVIDER", "gemini")

# -- Google Gemini --
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_FLASH_MODEL = os.getenv("GEMINI_FLASH_MODEL", "gemini-2.5-flash-lite")
GEMINI_PRO_MODEL = os.getenv("GEMINI_PRO_MODEL", "gemini-2.5-pro")

# -- DeepSeek --
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_MODEL_CHAT = os.getenv("DEEPSEEK_MODEL_CHAT", "deepseek-chat")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")

# -- HuggingFace Inference API (Universal Cloud Mesh, v5.9.18) --
HF_TOKEN = os.getenv("HF_TOKEN", "")
HF_BASE_URL = os.getenv("HF_BASE_URL", "https://router.huggingface.co/hf-inference/v1")
HF_MODEL_NAME = os.getenv("HF_MODEL_NAME", "meta-llama/Llama-3.3-70B-Instruct")

# -- NVIDIA NIM (Universal Cloud Mesh, v5.9.18) --
NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY", "")
NVIDIA_BASE_URL = os.getenv("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1")
NVIDIA_DEFAULT_MODEL = os.getenv("NVIDIA_DEFAULT_MODEL", "nvidia/nemotron-3-ultra")

# -- Groq (Universal Cloud Mesh, v5.9.18) --
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_BASE_URL = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1")
GROQ_DEFAULT_MODEL = os.getenv("GROQ_DEFAULT_MODEL", "llama-3.3-70b-versatile")

# -- Cerebras (Universal Cloud Mesh, v5.9.18) --
CEREBRAS_API_KEY = os.getenv("CEREBRAS_API_KEY", "")
CEREBRAS_BASE_URL = os.getenv("CEREBRAS_BASE_URL", "https://api.cerebras.ai/v1")
CEREBRAS_DEFAULT_MODEL = os.getenv("CEREBRAS_DEFAULT_MODEL", "llama-3.1-70b")

# -- GitHub Models (Universal Cloud Mesh, v5.9.18) --
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
GITHUB_MODELS_BASE_URL = os.getenv("GITHUB_MODELS_BASE_URL", "https://models.inference.ai.azure.com")
GITHUB_MODELS_DEFAULT_MODEL = os.getenv("GITHUB_MODELS_DEFAULT_MODEL", "gpt-4o-mini")

# -- Mistral (Universal Cloud Mesh, v5.9.18) --
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY", "")
MISTRAL_BASE_URL = os.getenv("MISTRAL_BASE_URL", "https://api.mistral.ai/v1")
MISTRAL_DEFAULT_MODEL = os.getenv("MISTRAL_DEFAULT_MODEL", "mistral-small-latest")

# -- OpenRouter (Universal Cloud Mesh, v5.9.18) --
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
OPENROUTER_DEFAULT_MODEL = os.getenv("OPENROUTER_DEFAULT_MODEL", "meta-llama/llama-3.3-70b-instruct:free")

# -- v5.9.18: Canonical cloud provider ordering for the Universal Cloud Mesh --
# This list is the authoritative enumeration of every cloud provider TALOS can
# route through. "gemini" uses the Google Generative AI SDK; all others use the
# OpenAI-compatible request path handled by AIManager.
TALOS_CLOUD_PROVIDERS = [
    "gemini", "nvidia", "groq", "cerebras", "github",
    "mistral", "openrouter", "deepseek", "huggingface"
]


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
TALOS_VERSION = "5.10.10"

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

# OPTICA Bridge base URL (v5.10.7). TALOS acts as an API client to the sister
# Project OPTICA microservice, which offloads heavy visualization workloads
# (cnsplots/PyVis graphics) to port 8002.
OPTICA_API_BASE = os.getenv(
    "OPTICA_API_BASE",
    "http://127.0.0.1:8002/api/v1"
)