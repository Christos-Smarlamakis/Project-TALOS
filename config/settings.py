# -*- coding: utf-8 -*-
"""
Module: settings.py
Project: TALOS v5.8.4
Description:
    Canonical configuration hub for TALOS v5.8.3. Defines all environment-variable
    driven settings for multi-tier LLM routing, provider endpoints, cloud LLM
    configuration, system execution mode, and system-wide constants. This module
    is the single source of truth for configuration derived from .env and config.json.

    Key design decisions:
    - Reads from environment variables with sensible defaults for air-gapped operation.
    - Supports three-tier LLM architecture: "fast" (edge/lightweight, CPU, port 11435),
      "heavy" (reasoning/large, GPU, port 11434), and "cloud" (Gemini/DeepSeek/HF).
    - TALOS_EXECUTION_MODE controls system-wide routing: "local" (air-gapped),
      "hybrid" (local primary, cloud fallback), or "cloud" (cloud primary, local fallback).
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

# -- System Execution Mode --
# Controls how TALOS routes inference requests across tiers.
#   "local"  : Air-gapped. All inference via local Ollama tiers only.
#   "hybrid" : Local tiers as primary, cloud providers as fallback.
#   "cloud"  : Cloud providers as primary, local tiers as fallback.
TALOS_EXECUTION_MODE = os.getenv("TALOS_EXECUTION_MODE", "local")

# Project version string -- updated with each release.
TALOS_VERSION = "5.8.4"

# TALOS FastAPI port (port 8000 is reserved for SYNAPSE event bus).
TALOS_API_PORT = int(os.getenv("TALOS_API_PORT", "8001"))

# SYNAPSE event bus URL for outbound events.
SYNAPSE_BUS_URL = os.getenv(
    "SYNAPSE_BUS_URL",
    "http://localhost:8000/api/v1/events"
)