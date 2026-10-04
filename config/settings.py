# -*- coding: utf-8 -*-
"""
Module: settings.py
Project: TALOS v5.24.0
Description:
    Canonical configuration hub for TALOS v5.24.0. Defines all environment-variable
    driven settings for multi-tier LLM routing, provider endpoints, cloud LLM
    configuration, system execution mode, and system-wide constants. This module
    is the single source of truth for configuration derived from .env and config.json.

    v5.24.0: Proactive Token-Bucket Rate Limiter provider RPM ceilings and
    Enterprise Database Vault defaults are consumed by the Cognitive Mesh and
    core subsystems (see src/services/cognitive_mesh/rate_limiter.py and
    src/core/database_vault.py).

    Key design decisions:
    - Reads from environment variables with sensible defaults for air-gapped operation.
    - Supports three-tier LLM architecture: "fast" (edge/lightweight, local,
      port 11434), "heavy" (reasoning/large, local, port 11434), and "cloud"
      (Universal Cloud Mesh, 8 providers).
    - v5.9.4: TALOS_EXECUTION_MODE is DEPRECATED and replaced by the 2D Execution
      Matrix: TALOS_NETWORK_STRATEGY (strict_local, local_first, cloud_first,
      strict_cloud) and TALOS_HARDWARE_STRATEGY (cpu_only, gpu_only, cpu_gpu_split).
    - v5.16.1: Fast tier uses Neutrino-8B at the unified local AI runtime (port 11434).
    - Heavy tier uses qwen2.5:14b at the standard Ollama endpoint (port 11434).
    - v5.16.2: Pluggable Provider Registry & Hardware-Aware Model Advisor --
      canonical provider base URLs and default models feed the modular
      registry (src/core/provider_registry.py), and the hardware advisor
    - v5.17.0: Two-Tier Hierarchical Swarm Architecture & Forensic Quality
      Engine -- Tier-2 quality swarm (src/prisma/quality_swarm.py) with
      profile-compiled auditor skills under _profiles/<name>/skills/.
      (src/core/hardware_advisor.py) consumes VRAM telemetry for budgeting.
    - v5.18.0: Ethical Academic PDF Harvester, Smart Section Slicing & SQLite
      FTS5 Engine -- src/ingestion/pdf_harvester/ cascades 12+ legal Open
      Access resolvers into data/fulltext_cache/, section_extractor caches
      Methodology/Experiments/Code/Limitations windows for the Tier-2 swarm,
      and src/search/fulltext_search.py indexes cached bodies with FTS5.
    - v5.18.1: Autonomous Chaos Hardening, Fault Isolation & Dead Code
      Decommissioning -- headless/non-interactive TTY hardening in
      src/analysis/citation_analyzer.py, a fault-tolerant optional-dependency
      import guard in src/ingestion/sources/pubmed_source.py, and the safe
      decommissioning of the legacy src/ingestion/pdf_downloader.py module.
    - v5.18.2: Net2Net DRL Checkpoint Repair, Win32 Close-to-Tray & Desktop
      Provisioner -- 18-source / 25-dim DDDQN tensor surgery confirmation,
      a Win32 close-to-tray window-procedure hook, a 1-click Desktop Shortcut
      provisioner, and an interactive autostart profile-target selector.
    - v5.18.3: DRL Dual-Checkpoint Net2Net Surgery & Daemon Profile Provisioning
      Engine -- genuine input tensor expansion on BOTH checkpoint locations
      (models/ and src/ai/models/), widening lstm1.weight_ih_l0 to [512, 25]
      and the advantage head to [19, 32] to permanently eliminate the
      RuntimeError: Expected 23, got 25; dynamic daemon banner/profile
      synchronization to the active profile (uav_mission_planning).
    - v5.18.4: Self-Healing Ingestion Gateway & Autostart Profile Provisioning
      -- an overarching src/ingestion/resilient_gateway.py wraps all 18 source
      adapters, fast-fails on 401/403/Quota errors without delayed retries, and
      mirrors IEEE/Elsevier/Springer through OpenAlex; daemon_autostart.py
      promotes profile selection to the first mandatory prompt.
    - v5.18.5: Hierarchical Evaluation Engine, Cognitive Router Quota Latching
      & Clean Ingestion Lifecycle -- centralizes the two-tier escalation
      pipeline (fast 8B sieve -> S_rel >= 6.0 -> heavy 14B/cloud deep
      scrutiny) in src/core/hierarchical_evaluator.py, latches cloud providers
      returning HTTP 402/401 directly into DeepSeek routing, and hardens the
      Science.gov (DNS isolation) and DBLP (query sanitization) adapters.
    - v5.20.0: Cognitive Meta-Router, SOTA LLM Dynamic Discovery & Enterprise
      Console Runbooks -- decoupled src/core/cognitive_router.py (4 strategies,
      circuit breaker, quota latching, Semaphore(2)), a 16-provider registry,
      src/core/model_benchmark_client.py + CLI --discover-llms, and the 6-zone
      docs/ARCHITECTURE_MAP.md.
    - v5.19.0: Two-Stage Rigor Decoupling Engine & Cognitive SOTA Role Matcher --
      upgrades src/core/hierarchical_evaluator.py to a true Stage-2 Dual-Audit
      (Faceted Deep Relevance Calibration S_rel_calibrated + Kitchenham 2007
      S_qual via PrismaQualityAppraiser) with 2D Evidence Quadrant mapping, and
      adds a four-role SOTA model matcher (src/core/hardware_advisor.py).
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

# Canonical fast edge inference URL (v5.16.1). The fast tier now routes
# directly to the verified universal local AI runtime on port 11434, retiring
# the phantom CPU edge port 11435.
FAST_EDGE_URL = os.getenv(
    "FAST_EDGE_URL",
    "http://127.0.0.1:11434/v1"
)

# Backward-compatible alias for FAST_EDGE_URL. Retained so existing diagnostics,
# tests, and documentation references keep resolving without breakage.
FAST_EDGE_BASE_URL = os.getenv("FAST_EDGE_BASE_URL", FAST_EDGE_URL)

# Heavy reasoning model: larger model for deep analysis, complex
# evaluations, and research synthesis tasks.
HEAVY_REASONING_MODEL = os.getenv(
    "HEAVY_REASONING_MODEL",
    "qwen2.5:14b"
)

# -- v5.18.5: Canonical local heavy-tier model alias consumed by the
# -- Hierarchical Evaluation Engine (src/core/hierarchical_evaluator.py).
# -- It is the same qwen2.5:14b GPU reasoning model as HEAVY_REASONING_MODEL,
# -- exposed under a semantic name so the escalation pipeline can reference
# -- the heavy tier without ambiguity.
LOCAL_HEAVY_MODEL = os.getenv("LOCAL_HEAVY_MODEL", HEAVY_REASONING_MODEL)

# -- v5.18.5: Science.gov is disabled by default. The federal endpoint is
# -- frequently absent (DNS failures) and produces dead DRL exploration
# -- actions; enable it explicitly by setting SCI_GOV_ENABLED=1 or the
# -- ``scigov_enabled`` config key.
SCI_GOV_ENABLED = os.getenv("SCI_GOV_ENABLED", "0")

# Standard Ollama base URL for the heavy reasoning tier.
# Default: localhost port 11434 (standard Ollama instance).
OLLAMA_BASE_URL = os.getenv(
    "OLLAMA_BASE_URL",
    "http://127.0.0.1:11434"
)

# -- Legacy local model configuration (used by ai_manager.py init) --
LOCAL_MODEL_BASE_URL = OLLAMA_BASE_URL + "/v1"

# -- Local GPU chat model (standard Ollama, port 11434) --
# llama3.1:8b is the preferred default: it is a verified-installed model with
# zero thinking/reasoning overhead, so local responses are fast and
# deterministic. Overridable via the LOCAL_GPU_MODEL or LOCAL_MODEL_NAME
# environment variable.
LOCAL_GPU_MODEL = os.getenv("LOCAL_GPU_MODEL", "llama3.1:8b")

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
DEEPSEEK_MODEL_CHAT = os.getenv("DEEPSEEK_MODEL_CHAT", "deepseek-v4-pro")
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

# -- SambaNova Cloud (v5.20.0) --
# SN40L RDUs provide ultra-fast Llama 3.1 70B / 405B inference through an
# OpenAI-compatible client.
SAMBANOVA_API_KEY = os.getenv("SAMBANOVA_API_KEY", "")
SAMBANOVA_BASE_URL = os.getenv("SAMBANOVA_BASE_URL", "https://api.sambanova.ai/v1")
SAMBANOVA_DEFAULT_MODEL = os.getenv("SAMBANOVA_DEFAULT_MODEL", "Meta-Llama-3.1-405B-Instruct")

# -- Together AI (v5.20.0) --
# High-throughput open-weights execution with strict JSON schema support.
TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY", "")
TOGETHER_BASE_URL = os.getenv("TOGETHER_BASE_URL", "https://api.together.xyz/v1")
TOGETHER_DEFAULT_MODEL = os.getenv("TOGETHER_DEFAULT_MODEL", "meta-llama/Llama-3.3-70B-Instruct-Turbo")

# -- Fireworks AI (v5.20.0) --
# Speculative-decoding optimized endpoints for high-frequency screening passes.
FIREWORKS_API_KEY = os.getenv("FIREWORKS_API_KEY", "")
FIREWORKS_BASE_URL = os.getenv("FIREWORKS_BASE_URL", "https://api.fireworks.ai/inference/v1")
FIREWORKS_DEFAULT_MODEL = os.getenv("FIREWORKS_DEFAULT_MODEL", "accounts/fireworks/models/llama-v3p1-70b-instruct")

# -- DeepInfra (v5.20.0) --
# Serverless endpoints for cost-effective batch abstract sieving.
DEEPINFRA_API_KEY = os.getenv("DEEPINFRA_API_KEY", "")
DEEPINFRA_BASE_URL = os.getenv("DEEPINFRA_BASE_URL", "https://api.deepinfra.com/v1/openai")
DEEPINFRA_DEFAULT_MODEL = os.getenv("DEEPINFRA_DEFAULT_MODEL", "meta-llama/Llama-3.3-70B-Instruct")

# -- Cohere (v5.20.0) --
# Command R / Command R+ for structured citation extraction and PRISMA grounding.
COHERE_API_KEY = os.getenv("COHERE_API_KEY", "")
COHERE_BASE_URL = os.getenv("COHERE_BASE_URL", "https://api.cohere.com/v2")
COHERE_DEFAULT_MODEL = os.getenv("COHERE_DEFAULT_MODEL", "command-r-plus")

# -- Perplexity (v5.20.0) --
# Sonar Reasoning / Sonar Pro for real-time claim verification and aerospace
# grey literature grounding.
PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY", "")
PERPLEXITY_BASE_URL = os.getenv("PERPLEXITY_BASE_URL", "https://api.perplexity.ai")
PERPLEXITY_DEFAULT_MODEL = os.getenv("PERPLEXITY_DEFAULT_MODEL", "sonar-pro")

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
#   "auto_dynamic" : v5.10.14 Autonomous Execution Matrix. Resolves at runtime
#                    to strict_local / local_first / cloud_first based on
#                    connectivity, VRAM, task type, and Privacy Guardrail
#                    consent. strict_local is NEVER overridden.
TALOS_NETWORK_STRATEGY = os.getenv("TALOS_NETWORK_STRATEGY", "strict_local")

# Hardware Strategy controls which local compute devices are used when
# inference is routed locally (via any network strategy that permits local).
#   "cpu_only"       : Force ALL local requests to the Fast Edge endpoint
#                      (FAST_EDGE_URL, port 11434). Even heavy-tier requests
#                      run on the fast model. No GPU utilization.
#   "gpu_only"       : Force ALL local requests to the standard Ollama
#                      endpoint (OLLAMA_BASE_URL, port 11434). Even fast-tier
#                      requests run on GPU.
#   "cpu_gpu_split"  : Default split. Both fast and heavy requests route to the
#                      unified local AI runtime (port 11434), respecting the
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
TALOS_VERSION = "5.24.0"

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