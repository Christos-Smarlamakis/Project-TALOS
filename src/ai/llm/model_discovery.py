# -*- coding: utf-8 -*-
"""
Module: model_discovery.py
Project: TALOS v5.10.14
Description:
    Dynamic Model Discovery Engine for the TALOS LLM router. This module
    discovers which inference models are currently active across the local
    (Ollama) tier and the optional cloud providers (NVIDIA NIM, Groq,
    OpenRouter, and Gemini), then computes normalized relative quality scores
    Q_p = raw_score(p) / max_k(raw_score(k)) over the active model set.

    The engine is fully air-gapped by design (Constitution II). A local JSON
    benchmark registry at data/model_benchmarks.json stores raw SWE-bench and
    MMLU-Pro scores, context window sizes, and pricing tiers for every known
    model. When the network is unavailable -- or a discovery request fails --
    the engine falls back to this registry so quality scoring always succeeds
    offline. The registry is created automatically on first use if absent.

    Key design decisions:
    - Local discovery queries the Ollama HTTP API (GET /api/tags) instead of
      the Python ollama client, so the module has no third-party import
      requirements beyond optional requests.
    - Cloud discovery queries OpenAI-compatible GET /v1/models endpoints plus
      the Gemini models.list endpoint, but only when online=True.
    - Q_p is deterministic and scale-invariant, matching the LLM Router
      Sub-Agent quality convention. The top active model receives Q_p = 1.0.
    - All network access is guarded by timeouts and try/except so failures
      degrade to the offline registry instead of raising.

Dependencies:
    - os, json, sys, time: Standard library utilities and project-root resolution.
    - requests (optional): HTTP calls for local/cloud discovery; guarded import.
    - config.settings: Canonical Ollama base URL.
    - src.integration.synapse_client (lazy): Optional model_discovered events.
"""

import json
import os
import sys
import time
import logging

# -- Resolve project root (same pattern as all src/*.py modules) --------------
_P = os.path.abspath(os.path.dirname(__file__))
while _P and not os.path.exists(os.path.join(_P, "talos.py")):
    _P = os.path.dirname(_P)
if _P:
    sys.path.insert(0, _P)

PROJECT_ROOT = _P

logger = logging.getLogger("talos.model_discovery")

# -- Optional requests import with graceful fallback --------------------------
try:
    import requests
    _REQUESTS_AVAILABLE = True
except ImportError:
    _REQUESTS_AVAILABLE = False
    logger.warning(
        "requests library not available. ModelDiscoveryEngine will operate "
        "from the offline registry only."
    )

# -- Canonical configuration constants ----------------------------------------
try:
    from config.settings import OLLAMA_BASE_URL
except ImportError:
    OLLAMA_BASE_URL = "http://127.0.0.1:11434"

# -- Default registry path (air-gapped benchmark cache) -----------------------
DEFAULT_REGISTRY_PATH = os.path.join(PROJECT_ROOT, "data", "model_benchmarks.json")

# -- Default benchmark registry content (created when the file is absent) -----
DEFAULT_BENCHMARK_MODELS = {
    "qwen2.5:14b": {"provider": "local", "swe_bench_score": 55.1, "mmlu_pro_score": 70.5, "context_window": 32768, "pricing_tier": "free"},
    "gemma3:12b": {"provider": "local", "swe_bench_score": 48.3, "mmlu_pro_score": 66.1, "context_window": 32768, "pricing_tier": "free"},
    "phi4:14b": {"provider": "local", "swe_bench_score": 52.6, "mmlu_pro_score": 69.2, "context_window": 16384, "pricing_tier": "free"},
    "llama3.3:70b": {"provider": "local", "swe_bench_score": 65.2, "mmlu_pro_score": 74.0, "context_window": 131072, "pricing_tier": "free"},
    "neutrino-8b": {"provider": "local", "swe_bench_score": 40.2, "mmlu_pro_score": 60.4, "context_window": 16384, "pricing_tier": "free"},
    "nemotron-70b": {"provider": "nvidia", "swe_bench_score": 70.4, "mmlu_pro_score": 78.0, "context_window": 131072, "pricing_tier": "cloud"},
    "llama-3.3-70b-versatile": {"provider": "groq", "swe_bench_score": 65.2, "mmlu_pro_score": 74.0, "context_window": 131072, "pricing_tier": "cloud"},
    "llama-3.3-70b": {"provider": "cerebras", "swe_bench_score": 65.2, "mmlu_pro_score": 74.0, "context_window": 131072, "pricing_tier": "cloud"},
    "gemini-2.5-pro": {"provider": "gemini", "swe_bench_score": 63.8, "mmlu_pro_score": 78.0, "context_window": 1048576, "pricing_tier": "cloud"},
    "deepseek-chat": {"provider": "deepseek", "swe_bench_score": 60.5, "mmlu_pro_score": 72.0, "context_window": 65536, "pricing_tier": "cloud"},
    "deepseek-v4-pro": {"provider": "deepseek", "swe_bench_score": 75.0, "mmlu_pro_score": 82.0, "context_window": 131072, "pricing_tier": "cloud"},
    "deepseek-v4-flash": {"provider": "deepseek", "swe_bench_score": 62.0, "mmlu_pro_score": 74.0, "context_window": 131072, "pricing_tier": "cloud"},
}

# -- Default cloud discovery endpoints (OpenAI-compatible + Gemini) -----------
DEFAULT_CLOUD_ENDPOINTS = [
    {"name": "nvidia", "url": "https://integrate.api.nvidia.com/v1/models"},
    {"name": "groq", "url": "https://api.groq.com/openai/v1/models"},
    {"name": "openrouter", "url": "https://openrouter.ai/api/v1/models"},
    {"name": "gemini", "url": "https://generativelanguage.googleapis.com/v1beta/models"},
]


class ModelDiscoveryEngine:
    """Dynamic discovery of active LLM models with air-gapped quality scoring.

    Attributes:
        registry_path (str): Absolute path to the local benchmark registry.
        ollama_url (str): Base URL of the local Ollama server.
        cloud_endpoints (list): Cloud provider model-list endpoint specs.
        timeout (float): HTTP request timeout in seconds.
        emit_events (bool): Whether to emit model_discovered Synapse events.
        online_default (bool): Default online flag for scoring calls (False).
    """

    def __init__(self, registry_path=None, ollama_url=None, cloud_endpoints=None,
                 timeout=4.0, emit_events=False):
        """Initialize the engine and guarantee the registry exists.

        Args:
            registry_path (str | None): Override for the registry path.
            ollama_url (str | None): Override for the Ollama base URL.
            cloud_endpoints (list | None): Override for cloud endpoints.
            timeout (float): HTTP request timeout in seconds.
            emit_events (bool): Emit model_discovered Synapse events.
        """
        self.registry_path = registry_path or DEFAULT_REGISTRY_PATH
        self.ollama_url = ollama_url or OLLAMA_BASE_URL
        self.cloud_endpoints = cloud_endpoints if cloud_endpoints is not None else DEFAULT_CLOUD_ENDPOINTS
        self.timeout = timeout
        self.emit_events = emit_events
        self.online_default = False
        self._ensure_registry()

    # ------------------------------------------------------------------
    # -- Registry management (air-gapped cache) -------------------------
    # ------------------------------------------------------------------

    def _ensure_registry(self):
        """Create the default benchmark registry if it does not exist."""
        if os.path.exists(self.registry_path):
            return
        try:
            os.makedirs(os.path.dirname(self.registry_path), exist_ok=True)
            payload = {
                "schema_version": "1.0",
                "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "source": "talos_default_registry",
                "models": DEFAULT_BENCHMARK_MODELS,
            }
            with open(self.registry_path, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2, ensure_ascii=False)
            logger.info("Created default model benchmark registry at %s", self.registry_path)
        except OSError as e:
            logger.warning("Could not create model benchmark registry: %s", e)

    def _load_registry(self):
        """Load the benchmark registry from disk.

        Returns:
            dict: Model name to benchmark metadata mapping. Falls back to the
                in-memory defaults when the file is missing or unreadable.
        """
        try:
            with open(self.registry_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data.get("models", {}) or {}
        except (OSError, ValueError) as e:
            logger.warning("Could not read model benchmark registry (%s). Using defaults.", e)
            return dict(DEFAULT_BENCHMARK_MODELS)

    # ------------------------------------------------------------------
    # -- Network helpers ------------------------------------------------
    # ------------------------------------------------------------------

    def _http_get_json(self, url, params=None):
        """Perform a GET request and return parsed JSON, or None on failure.

        Args:
            url (str): Target URL.
            params (dict | None): Optional query parameters.

        Returns:
            dict | list | None: Parsed JSON body, or None on any error.
        """
        if not _REQUESTS_AVAILABLE:
            return None
        try:
            response = requests.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.debug("Discovery request failed for %s: %s", url, e)
            return None

    # ------------------------------------------------------------------
    # -- Local discovery (Ollama) --------------------------------------
    # ------------------------------------------------------------------

    def _discover_local_models(self):
        """Query the local Ollama instance for installed models.

        Returns:
            list of dict: Discovered local models with name and provider fields.
        """
        data = self._http_get_json(self.ollama_url.rstrip("/") + "/api/tags")
        return self._parse_local_tags(data)

    @staticmethod
    def _parse_local_tags(data):
        """Parse an Ollama GET /api/tags JSON payload.

        Args:
            data (dict | None): Raw JSON from GET /api/tags.

        Returns:
            list of dict: Normalized model records (name, provider).
        """
        if not isinstance(data, dict):
            return []
        raw = data.get("models") or []
        models = []
        for entry in raw:
            entry = entry or {}
            name = entry.get("name") or entry.get("model")
            if name:
                models.append({"name": name, "provider": "local"})
        return models

    # ------------------------------------------------------------------
    # -- Cloud discovery (NVIDIA NIM, Groq, OpenRouter, Gemini) --------
    # ------------------------------------------------------------------

    def _discover_cloud_models(self):
        """Query configured cloud providers for dynamically available models.

        Returns:
            list of dict: Discovered cloud models (name, provider).
        """
        discovered = []
        for endpoint in self.cloud_endpoints:
            data = self._http_get_json(endpoint["url"])
            discovered.extend(self._parse_cloud_models(data, endpoint["name"]))
        return discovered

    @staticmethod
    def _parse_cloud_models(data, provider):
        """Parse a cloud provider model-list payload.

        Handles OpenAI-compatible responses (data list with id) and
        Gemini-style responses (models list with name).

        Args:
            data (dict | None): Raw JSON from a model-list endpoint.
            provider (str): Provider name to tag on each model.

        Returns:
            list of dict: Normalized model records (name, provider).
        """
        if not isinstance(data, dict):
            return []
        raw = data.get("data") or data.get("models") or []
        models = []
        for entry in raw or []:
            entry = entry or {}
            name = entry.get("id") or entry.get("name") or ""
            if name.startswith("models/"):
                name = name[len("models/"):]
            if name:
                models.append({"name": name, "provider": provider})
        return models

    # ------------------------------------------------------------------
    # -- Unified discovery ---------------------------------------------
    # ------------------------------------------------------------------

    def discover_active_models(self, online=True):
        """Discover all currently active models across local and cloud tiers.

        Args:
            online (bool): When True, also query cloud providers. When False,
                only the local Ollama tier is queried. Both modes fall back to
                the offline registry when live discovery yields nothing.

        Returns:
            dict: Structured report with keys mode, local_models,
                cloud_models, active_models, registry_models, and count.
        """
        registry = self._load_registry()

        local_models = self._discover_local_models()
        cloud_models = self._discover_cloud_models() if online else []

        live_models = local_models + cloud_models
        active_models = self._enrich_models(live_models, registry)

        if active_models:
            mode = "online" if cloud_models else "local"
        else:
            # -- Air-gapped fallback: use the registry directly -------------
            active_models = self._enrich_models(
                [{"name": name, "provider": meta.get("provider", "local")}
                 for name, meta in registry.items()],
                registry,
            )
            mode = "air_gapped_fallback"

        if self.emit_events:
            for model in active_models:
                self._emit_model_discovered(model)

        return {
            "mode": mode,
            "local_models": local_models,
            "cloud_models": cloud_models,
            "active_models": active_models,
            "registry_models": list(registry.keys()),
            "count": len(active_models),
        }

    @staticmethod
    def _enrich_models(models, registry):
        """Attach benchmark metadata from the registry to discovered models.

        Args:
            models (list of dict): Discovered models with name/provider fields.
            registry (dict): Model-name to benchmark-metadata mapping.

        Returns:
            list of dict: Enriched model records (name, provider, scores, etc.).
        """
        enriched = []
        for model in models:
            name = model["name"]
            meta = registry.get(name) or {}
            enriched.append({
                "name": name,
                "provider": model.get("provider") or meta.get("provider", "unknown"),
                "swe_bench_score": meta.get("swe_bench_score"),
                "mmlu_pro_score": meta.get("mmlu_pro_score"),
                "context_window": meta.get("context_window"),
                "pricing_tier": meta.get("pricing_tier", "unknown"),
            })
        return enriched

    # ------------------------------------------------------------------
    # -- Quality scoring ------------------------------------------------
    # ------------------------------------------------------------------

    def get_normalized_quality_scores(self, online=None):
        """Compute relative quality Q_p = raw_score(p) / max_k(raw_score(k)).

        The raw score for a model is its SWE-bench score, falling back to the
        MMLU-Pro score, and finally to zero when neither is present.

        Args:
            online (bool | None): Override for the online discovery flag. When
                None, the engine default (offline) is used.

        Returns:
            dict[str, float]: Active model name mapped to its normalized
                quality score in [0, 1]. The top model receives exactly 1.0.
                Empty dict when no models are active.
        """
        if online is None:
            online = self.online_default
        report = self.discover_active_models(online=online)
        return self._compute_quality_scores(report.get("active_models", []))

    @staticmethod
    def _compute_quality_scores(active):
        """Compute Q_p over a list of enriched active-model records.

        Args:
            active (list of dict): Enriched active model records.

        Returns:
            dict[str, float]: Model name to normalized quality score.
        """
        raw_scores = {}
        for model in active:
            raw = model.get("swe_bench_score") or model.get("mmlu_pro_score") or 0.0
            raw_scores[model["name"]] = float(raw)
        if not raw_scores:
            return {}
        max_score = max(raw_scores.values())
        if max_score <= 0.0:
            return {name: 0.0 for name in raw_scores}
        return {name: score / max_score for name, score in raw_scores.items()}

    def get_provider_quality_scores(self, online=None):
        """Aggregate normalized quality scores to the provider level.

        Each provider receives the maximum Q_p among its currently active
        models. This is the signal consumed by the LLM Router Sub-Agent.

        Args:
            online (bool | None): Override for the online discovery flag.

        Returns:
            dict[str, float]: Provider name mapped to its best normalized
                quality score.
        """
        if online is None:
            online = self.online_default
        report = self.discover_active_models(online=online)
        active = report.get("active_models", [])
        quality = self._compute_quality_scores(active)
        provider_best = {}
        for model in active:
            provider = model.get("provider", "unknown")
            score = quality.get(model["name"], 0.0)
            provider_best[provider] = max(provider_best.get(provider, 0.0), score)
        return provider_best

    # ------------------------------------------------------------------
    # -- Synapse event emission ----------------------------------------
    # ------------------------------------------------------------------

    def _emit_model_discovered(self, model):
        """Emit a non-blocking model_discovered Synapse event.

        Args:
            model (dict): Enriched model record.

        Returns:
            None: Emission is best-effort and never raises.
        """
        try:
            from src.integration.synapse_client import synapse_emitter
            synapse_emitter.emit("model_discovered", {
                "model_name": model.get("name"),
                "provider": model.get("provider"),
                "swe_bench_score": model.get("swe_bench_score"),
                "mmlu_pro_score": model.get("mmlu_pro_score"),
                "context_window": model.get("context_window"),
                "pricing_tier": model.get("pricing_tier"),
            })
        except Exception as e:
            logger.debug("model_discovered emission skipped: %s", e)


# -- Module-level convenience singleton ----------------------------------------
_model_discovery_singleton = None


def get_discovery_engine():
    """Return a shared ModelDiscoveryEngine singleton.

    Returns:
        ModelDiscoveryEngine: The shared discovery engine instance.
    """
    global _model_discovery_singleton
    if _model_discovery_singleton is None:
        _model_discovery_singleton = ModelDiscoveryEngine()
    return _model_discovery_singleton