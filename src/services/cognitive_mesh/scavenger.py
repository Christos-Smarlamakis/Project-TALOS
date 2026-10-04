# -*- coding: utf-8 -*-
"""
Module: scavenger.py
Project: TALOS v5.23.0
Description:
    Autonomous Model Scavenger Agent for the Cognitive Mesh in-tree
    microservice. The agent forages three public catalogues -- the Hugging Face
    Hub API (top-100 text-generation models sorted by downloads), the OpenRouter
    models catalogue (full catalog ingestion with optional release-window
    filtering, per-token pricing, and context sizes), and the Ollama library
    (local tags plus a canonical remote-library catalogue) -- and reconciles
    every discovery against the active RTX 4070 (12 GB VRAM) budget through a
    hardened hardware-aware role classifier. Every discovered model is enriched
    with fuzzy cross-referenced MMLU-Pro / HumanEval / TTFT benchmarks. The
    result is a single MarketIntelligenceReport DTO consumed by the dual
    IntelligenceReporter (reporter.py) and the FastAPI mini-server (server.py).

    Key design decisions:
    - Every source query is best-effort and guarded; a network failure or
      malformed payload yields an empty result set rather than an exception,
      honouring the 100 percent air-gapped, never-crash guarantee.
    - The hardware-aware role classifier maps each model into one of three VRAM
      classes (LOCAL_OPTIMAL, CLOUD_COST_EFFECTIVE, FRONTIER_REASONING) and one
      of five scientific workload roles (Fast Screening, Kitchenham Rigor, Code
      Audit, Vector Embeddings, General Research) using token-boundary
      substring heuristics plus a parameter-count and price fallback.
    - Fuzzy benchmark enrichment cross-references each model identifier against
      the benchmark database in benchmarks.py so report columns are never empty
      for known families.
    - When every source fails, the agent degrades to the local benchmark cache
      (data/cache/llm_benchmarks.json) so a report is always produced offline.

Dependencies:
    - os, json, re, time, datetime: filesystem, parsing, and timestamps.
    - typing: type annotations (List, Dict, Optional, Any).
    - src.services.cognitive_mesh.dto: ScavengedModel / MarketIntelligenceReport.
    - src.services.cognitive_mesh.benchmarks (lazy): fuzzy benchmark enrichment.
"""

import json
import os
import re
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

# -- Resolve project root (same pattern as all src/*.py modules) --------------
_P = os.path.abspath(os.path.dirname(__file__))
while _P and not os.path.exists(os.path.join(_P, "talos.py")):
    _P = os.path.dirname(_P)
PROJECT_ROOT = _P
if _P:
    import sys
    sys.path.insert(0, _P)

from src.services.cognitive_mesh.dto import (  # noqa: E402
    AccessTier,
    MarketIntelligenceReport,
    ScavengedModel,
)
from src.services.cognitive_mesh.self_healing import (  # noqa: E402
    classify_model_access_tier,
)

# -- Canonical endpoint surface -----------------------------------------------
HF_API_URL = "https://huggingface.co/api/models"
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/models"
OLLAMA_TAGS_URL = "http://localhost:11434/api/tags"

# -- VRAM classification labels ------------------------------------------------
VRAM_LOCAL_OPTIMAL = "LOCAL_OPTIMAL"
VRAM_CLOUD_COST_EFFECTIVE = "CLOUD_COST_EFFECTIVE"
VRAM_FRONTIER_REASONING = "FRONTIER_REASONING"

# -- Scientific workload role labels ------------------------------------------
ROLE_FAST_SCREENING = "Fast Screening"
ROLE_KITCHENHAM_RIGOR = "Kitchenham Rigor"
ROLE_CODE_AUDIT = "Code Audit"
ROLE_VECTOR_EMBEDDINGS = "Vector Embeddings"
ROLE_GENERAL_RESEARCH = "General Research"

# -- Permissive open-weight license allowlist (lower-cased keys) ---------------
PERMISSIVE_LICENSES = {
    "apache-2.0",
    "apache 2.0",
    "mit",
    "llama",
    "llama2",
    "llama3",
    "llama3.1",
    "llama3.2",
    "llama3.3",
    "openrail",
    "openrail++",
    "openrail-m",
    "bigscience-openrail-m",
    "cc-by-4.0",
    "cc-by-sa-4.0",
    "gemma",
    "qwen",
}

# -- Static well-known GGUF catalogue for the air-gapped Ollama fallback -------
# Each entry approximates the official Ollama library tags <= 14B parameters.
STATIC_OLLAMA_MODELS: List[Dict[str, Any]] = [
    {"id": "qwen2.5:14b", "params_b": 14.0, "role": ROLE_KITCHENHAM_RIGOR},
    {"id": "qwen2.5-coder:14b", "params_b": 14.0, "role": ROLE_CODE_AUDIT},
    {"id": "llama3.1:8b", "params_b": 8.0, "role": ROLE_FAST_SCREENING},
    {"id": "gemma2:9b", "params_b": 9.0, "role": ROLE_FAST_SCREENING},
    {"id": "mistral:7b", "params_b": 7.0, "role": ROLE_FAST_SCREENING},
    {"id": "phi3:14b", "params_b": 14.0, "role": ROLE_FAST_SCREENING},
    {"id": "nomic-embed-text", "params_b": 0.137, "role": ROLE_VECTOR_EMBEDDINGS},
]

# -- Canonical remote Ollama library catalogue (v5.21.1) ------------------------
# Popular remote models available through the Ollama library are appended to the
# locally installed set so the market report reflects the full Ollama ecosystem,
# including models far above the 14B local budget that must be served remotely.
REMOTE_OLLAMA_MODELS: List[Dict[str, Any]] = [
    {"id": "qwen2.5:7b", "params_b": 7.0},
    {"id": "qwen2.5:14b", "params_b": 14.0},
    {"id": "qwen2.5:32b", "params_b": 32.0},
    {"id": "qwen2.5:72b", "params_b": 72.0},
    {"id": "qwen2.5-coder:14b", "params_b": 14.0},
    {"id": "qwen2.5-coder:32b", "params_b": 32.0},
    {"id": "llama3.1:8b", "params_b": 8.0},
    {"id": "llama3.1:70b", "params_b": 70.0},
    {"id": "llama3.1:405b", "params_b": 405.0},
    {"id": "deepseek-r1:8b", "params_b": 8.0},
    {"id": "deepseek-r1:14b", "params_b": 14.0},
    {"id": "deepseek-r1:32b", "params_b": 32.0},
    {"id": "deepseek-r1:70b", "params_b": 70.0},
    {"id": "gemma2:9b", "params_b": 9.0},
    {"id": "gemma2:27b", "params_b": 27.0},
    {"id": "gemma3:12b", "params_b": 12.0},
    {"id": "gemma3:27b", "params_b": 27.0},
    {"id": "mistral-nemo:12b", "params_b": 12.0},
    {"id": "phi4:14b", "params_b": 14.0},
    {"id": "codeqwen:7b", "params_b": 7.0},
]

_PARAM_RE = re.compile(r"(\d+(?:\.\d+)?)\s*[bB]")

# -- Token-boundary classification keyword tables (v5.21.1) ---------------------
# Frontier architectures are matched on token boundaries to avoid false positives
# such as "pro" matching "proprietary" or "mini" matching "gemini".
_FRONTIER_TOKENS = ("sonnet", "opus", "r1", "reasoner", "pro", "o1", "o3")
_FRONTIER_SUBSTRINGS = ("gpt-4", "gpt-5", "gpt-6", "405b", "nemotron-70b")
_CODE_SUBSTRINGS = ("coder", "starcoder", "codellama", "deepseek-coder", "codeqwen", "code-")
_EMBED_SUBSTRINGS = ("embed", "bge-", "nomic-embed", "text-embedding")
_FAST_TOKENS = ("flash", "haiku", "mini", "3b", "7b", "8b", "9b", "12b", "14b")


class ModelScoutAgent:
    """Autonomous Model Scout reconciling LLM catalogues against the RTX 4070 budget.

    This is the canonical (primary) class name for the autonomous model
    discovery agent (v5.22.1 terminology formalization). The historical name
    ``ModelScavengerAgent`` is retained as a module-level alias for 100 percent
    backward compatibility with existing callers and the test suite.

    Attributes:
        vram_gb (float): Detected local VRAM budget in gigabytes (default 12.0).
    """

    def __init__(self, vram_gb: float = 12.0) -> None:
        self.vram_gb = vram_gb

    # ------------------------------------------------------------------
    # -- Public foraging entry point -----------------------------------
    # ------------------------------------------------------------------

    def scavenge_market(
        self, window_days: int = 30, fetch_all: bool = False
    ) -> MarketIntelligenceReport:
        """Forage all three catalogues and assemble a market intelligence report.

        Args:
            window_days (int): Discovery window in days for OpenRouter deltas.
                A value of zero or a negative value disables date truncation.
            fetch_all (bool): When True (or when window_days <= 0), ingest the
                entire OpenRouter catalog without filtering by release date.

        Returns:
            MarketIntelligenceReport: The aggregate report with VRAM classes,
                recommended roles, fuzzy benchmarks, and summary statistics.
        """
        report = MarketIntelligenceReport(
            generated_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            window_days=window_days,
        )

        # -- Forage each source independently; never let one failure abort. --
        online_succeeded = False
        for name, forage in (
            ("huggingface", self._forage_huggingface),
            ("openrouter", lambda: self._forage_openrouter(window_days, fetch_all)),
            ("ollama", self._forage_ollama),
        ):
            try:
                models = forage()
            except Exception:
                models = []
                report.sources_failed.append(name)
                continue
            if models:
                report.sources_queried.append(name)
                report.models.extend(models)
                if name in ("huggingface", "openrouter"):
                    online_succeeded = True

        # -- Offline resilience: fall back to the local benchmark cache. --
        if not report.models:
            try:
                report.models = self._load_cached_benchmarks()
            except Exception:
                report.models = []
        if not online_succeeded:
            report.offline_fallback = True

        # -- Reconcile active provider telemetry. --
        report.active_providers = self._active_provider_count()

        # -- Classify every model and enrich fuzzy benchmark metrics. --
        for model in report.models:
            role, vram = self._classify_model(
                model.model,
                model.parameter_count_b,
                model.pricing_prompt_per_1m_usd,
                model.context_window,
                model.source,
            )
            model.vram_class = vram
            model.access_tier = classify_model_access_tier(model.source, model.developer)
            if not model.recommended_role:
                model.recommended_role = role
            self._apply_fuzzy_benchmarks(model)

        self._compute_summary(report)
        return report

    # ------------------------------------------------------------------
    # -- Source 1: Hugging Face Hub API --------------------------------
    # ------------------------------------------------------------------

    def _forage_huggingface(self) -> List[ScavengedModel]:
        payload = self._http_get_json(
            HF_API_URL,
            params={"pipeline_tag": "text-generation", "sort": "downloads",
                    "direction": "-1", "limit": "100"},
        )
        if not isinstance(payload, list):
            return []
        return self._parse_huggingface_payload(payload)

    @staticmethod
    def _parse_huggingface_payload(payload: List[Dict[str, Any]]) -> List[ScavengedModel]:
        """Parse a Hugging Face model-list payload into scavenged records.

        Args:
            payload (list[dict]): The JSON array returned by /api/models.

        Returns:
            list[ScavengedModel]: Permissive-license text-generation records.
        """
        models: List[ScavengedModel] = []
        for item in payload:
            if not isinstance(item, dict):
                continue
            pipeline = item.get("pipeline_tag")
            if pipeline and pipeline != "text-generation":
                continue
            license_name = ModelScavengerAgent._extract_license(item)
            if license_name and license_name not in PERMISSIVE_LICENSES:
                continue
            model_id = item.get("id") or item.get("modelId") or ""
            params = ModelScavengerAgent._parse_param_count(model_id)
            models.append(
                ScavengedModel(
                    model=model_id,
                    developer=item.get("author") or "",
                    parameter_count_b=params,
                    parameter_count_label=f"{params:.0f}B" if params else "",
                    context_window=int(item.get("context_length", 0) or 0),
                    license=license_name,
                    release_date=ModelScavengerAgent._iso_date(item),
                    source="huggingface",
                    downloads=int(item.get("downloads", 0) or 0),
                    likes=int(item.get("likes", 0) or 0),
                )
            )
        return models

    # ------------------------------------------------------------------
    # -- Source 2: OpenRouter models catalogue -------------------------
    # ------------------------------------------------------------------

    def _forage_openrouter(
        self, window_days: int, fetch_all: bool = False
    ) -> List[ScavengedModel]:
        payload = self._http_get_json(OPENROUTER_API_URL)
        if not isinstance(payload, dict):
            return []
        return self._parse_openrouter_payload(
            payload.get("data", []), window_days, fetch_all
        )

    @staticmethod
    def _parse_openrouter_payload(
        payload: List[Dict[str, Any]], window_days: int, fetch_all: bool = False
    ) -> List[ScavengedModel]:
        """Parse an OpenRouter catalogue into scavenged records.

        Args:
            payload (list[dict]): The ``data`` array of the OpenRouter response.
            window_days (int): Delta window for newly-released models. A value of
                zero or a negative value disables the cutoff entirely.
            fetch_all (bool): When True, ignore the release-window cutoff.

        Returns:
            list[ScavengedModel]: Models with pricing metadata.
        """
        apply_cutoff = (not fetch_all) and (window_days > 0)
        cutoff = time.time() - (window_days * 86400) if apply_cutoff else 0
        models: List[ScavengedModel] = []
        for item in payload:
            if not isinstance(item, dict):
                continue
            created = item.get("created") or 0
            try:
                created = int(created)
            except (TypeError, ValueError):
                created = 0
            if apply_cutoff and created and created < cutoff:
                continue
            pricing = item.get("pricing") or {}
            prompt_usd = ModelScavengerAgent._price_per_1m(pricing.get("prompt"))
            completion_usd = ModelScavengerAgent._price_per_1m(
                pricing.get("completion")
            )
            model_id = item.get("id") or item.get("name") or ""
            params = ModelScavengerAgent._parse_param_count(model_id)
            models.append(
                ScavengedModel(
                    model=model_id,
                    developer="OpenRouter",
                    parameter_count_b=params,
                    parameter_count_label=f"{params:.0f}B" if params else "",
                    context_window=int(item.get("context_length", 0) or 0),
                    license="",
                    release_date=(
                        datetime.fromtimestamp(created, tz=timezone.utc)
                        .strftime("%Y-%m-%d")
                        if created
                        else None
                    ),
                    source="openrouter",
                    pricing_prompt_per_1m_usd=prompt_usd,
                    pricing_completion_per_1m_usd=completion_usd,
                )
            )
        return models

    # ------------------------------------------------------------------
    # -- Source 3: Ollama library and quantization auditor -------------
    # ------------------------------------------------------------------

    def _forage_ollama(self) -> List[ScavengedModel]:
        payload = self._http_get_json(OLLAMA_TAGS_URL)
        if isinstance(payload, dict) and isinstance(payload.get("models"), list):
            local = self._parse_ollama_payload(payload.get("models", []))
        else:
            local = self._parse_ollama_payload(STATIC_OLLAMA_MODELS)
        # -- Append the canonical remote library catalogue (v5.21.1). --
        remote = self._parse_ollama_payload(REMOTE_OLLAMA_MODELS)
        merged: Dict[str, ScavengedModel] = {m.model: m for m in local}
        for model in remote:
            merged.setdefault(model.model, model)
        return list(merged.values())

    @staticmethod
    def _parse_ollama_payload(payload: List[Dict[str, Any]]) -> List[ScavengedModel]:
        """Parse an Ollama tag-list into scavenged records of any parameter size.

        Args:
            payload (list[dict]): Either local /api/tags entries, static entries,
                or the canonical remote library catalogue.

        Returns:
            list[ScavengedModel]: Quantized GGUF records; classification into
                LOCAL_OPTIMAL / CLOUD_COST_EFFECTIVE / FRONTIER_REASONING is
                deferred to the hardened classifier.
        """
        models: List[ScavengedModel] = []
        for item in payload:
            if not isinstance(item, dict):
                continue
            model_id = item.get("id") or item.get("name") or ""
            params = item.get("params_b")
            if params is None:
                params = ModelScavengerAgent._parse_param_count(model_id)
            models.append(
                ScavengedModel(
                    model=model_id,
                    developer="Ollama",
                    parameter_count_b=params,
                    parameter_count_label=f"{params:.0f}B" if params else "",
                    context_window=0,
                    license="",
                    source="ollama",
                    recommended_role=item.get("role", ""),
                )
            )
        return models

    # ------------------------------------------------------------------
    # -- Offline fallback ----------------------------------------------
    # ------------------------------------------------------------------

    def _load_cached_benchmarks(self) -> List[ScavengedModel]:
        cache_path = os.path.join(PROJECT_ROOT, "data", "cache", "llm_benchmarks.json")
        records: List[Dict[str, Any]] = []
        try:
            with open(cache_path, "r", encoding="utf-8") as fh:
                payload = json.load(fh)
            records = payload.get("records") or payload.get("models") or []
        except (OSError, ValueError):
            records = []
        if not records:
            try:
                from src.services.cognitive_mesh.benchmarks import DEFAULT_BENCHMARKS
                records = list(DEFAULT_BENCHMARKS)
            except Exception:
                records = []
        models: List[ScavengedModel] = []
        for record in records:
            if not isinstance(record, dict):
                continue
            model_id = record.get("model", "")
            params = ModelScavengerAgent._parse_param_count(model_id)
            models.append(
                ScavengedModel(
                    model=model_id,
                    developer=record.get("provider", ""),
                    parameter_count_b=params,
                    parameter_count_label=f"{params:.0f}B" if params else "",
                    context_window=int(record.get("context_window", 0) or 0),
                    license="",
                    source="benchmarks",
                    mmlu_pro=float(record.get("mmlu_pro", 0.0) or 0.0),
                    human_eval=float(record.get("human_eval", 0.0) or 0.0),
                    ttft_ms=float(record.get("ttft_ms", 0.0) or 0.0),
                )
            )
        return models

    # ------------------------------------------------------------------
    # -- Hardware-aware role classifier --------------------------------
    # ------------------------------------------------------------------

    @staticmethod
    def _has_token(name: str, token: str) -> bool:
        """Return True when ``token`` appears in ``name`` on a word boundary.

        A token is matched only when it is delimited by non-alphanumeric
        characters on both sides (or the start/end of the string). This prevents
        false positives such as ``pro`` matching ``proprietary``, ``mini``
        matching ``gemini``, or ``7b`` matching ``37b``/``70b``.

        Args:
            name (str): The lower-cased model identifier.
            token (str): The keyword token to search for.

        Returns:
            bool: True when the token is present on a word boundary.
        """
        pattern = r"(?<![a-z0-9])" + re.escape(token) + r"(?![a-z0-9])"
        return re.search(pattern, name) is not None

    @staticmethod
    def _classify_model(model_id, params, price, context, source=""):
        """Classify a model into a (recommended_role, vram_class) pair.

        Decision tree, evaluated strictly in priority order:

        1. Vector Embeddings: ``embed``/``bge-``/``nomic-embed``/``text-embedding``.
        2. Code Audit: ``coder``/``starcoder``/``codellama``/``deepseek-coder``/
           ``codeqwen``/``code-``.
        3. Frontier Reasoning / Kitchenham Rigor: ``sonnet``/``opus``/``r1``/
           ``reasoner``/``pro``/``o1``/``o3``/``gpt-4``/``gpt-5``/``gpt-6``/
           ``405b``/``nemotron-70b``, OR prompt price >= $3.00/1M, OR >= 70B params.
        4. Fast Screening: ``flash``/``haiku``/``mini``/``3b``/``7b``/``8b``/
           ``9b``/``12b``/``14b``, OR any model at or below 14B parameters.
        5. General Research: everything else (CLOUD_COST_EFFECTIVE).

        Args:
            model_id (str): Model identifier.
            params (Optional[float]): Parameter count in billions.
            price (Optional[float]): Prompt price per 1M tokens in USD.
            context (Any): Context window (reserved for future heuristics).
            source (str): Discovery source (used to detect local Ollama models).

        Returns:
            tuple[str, str]: The (recommended_role, vram_class) pair.
        """
        name = (model_id or "").lower()

        # -- 1. Vector Embeddings --
        if any(s in name for s in _EMBED_SUBSTRINGS):
            local = bool(source == "ollama") or (params is not None and params <= 14.0)
            return ROLE_VECTOR_EMBEDDINGS, (
                VRAM_LOCAL_OPTIMAL if local else VRAM_CLOUD_COST_EFFECTIVE
            )

        # -- 2. Code Audit --
        if any(s in name for s in _CODE_SUBSTRINGS):
            local = params is not None and params <= 14.0
            return ROLE_CODE_AUDIT, (
                VRAM_LOCAL_OPTIMAL if local else VRAM_CLOUD_COST_EFFECTIVE
            )

        # -- 3. Frontier Reasoning / Kitchenham Rigor --
        frontier = any(ModelScavengerAgent._has_token(name, t) for t in _FRONTIER_TOKENS)
        frontier = frontier or any(s in name for s in _FRONTIER_SUBSTRINGS)
        frontier = frontier or (price is not None and price >= 3.0)
        frontier = frontier or (params is not None and params >= 70.0)
        if frontier:
            return ROLE_KITCHENHAM_RIGOR, VRAM_FRONTIER_REASONING

        # -- 4. Fast Screening / Local Optimal --
        fast = any(ModelScavengerAgent._has_token(name, t) for t in _FAST_TOKENS)
        fast = fast or (params is not None and params <= 14.0)
        if fast:
            local = params is not None and params <= 14.0
            return ROLE_FAST_SCREENING, (
                VRAM_LOCAL_OPTIMAL if local else VRAM_CLOUD_COST_EFFECTIVE
            )

        # -- 5. General Cloud --
        return ROLE_GENERAL_RESEARCH, VRAM_CLOUD_COST_EFFECTIVE

    def _classify_vram(self, model: ScavengedModel) -> str:
        """Classify a model into one of three VRAM compatibility classes.

        Delegates to :meth:`_classify_model` for a single source of truth.

        Args:
            model (ScavengedModel): The discovered model.

        Returns:
            str: LOCAL_OPTIMAL, CLOUD_COST_EFFECTIVE, or FRONTIER_REASONING.
        """
        _, vram = self._classify_model(
            model.model,
            model.parameter_count_b,
            model.pricing_prompt_per_1m_usd,
            model.context_window,
            model.source,
        )
        return vram

    @staticmethod
    def _recommend_role(model: ScavengedModel) -> str:
        """Recommend one of the five scientific workload roles for a model.

        Delegates to :meth:`_classify_model` for a single source of truth.

        Args:
            model (ScavengedModel): The discovered model.

        Returns:
            str: Fast Screening, Kitchenham Rigor, Code Audit, Vector
                Embeddings, or General Research.
        """
        role, _ = ModelScavengerAgent._classify_model(
            model.model,
            model.parameter_count_b,
            model.pricing_prompt_per_1m_usd,
            model.context_window,
            model.source,
        )
        return role

    # ------------------------------------------------------------------
    # -- Fuzzy benchmark enrichment (v5.21.1) ---------------------------
    # ------------------------------------------------------------------

    @staticmethod
    def _apply_fuzzy_benchmarks(model: ScavengedModel) -> None:
        """Populate MMLU-Pro / HumanEval / TTFT from the fuzzy benchmark DB.

        The enrichment only fills metrics that are currently empty so that
        explicitly measured values are never overwritten.

        Args:
            model (ScavengedModel): The model record to enrich in place.
        """
        try:
            from src.services.cognitive_mesh.benchmarks import (
                fuzzy_enrich_benchmarks,
            )
            enriched = fuzzy_enrich_benchmarks(model.model, model.developer)
        except Exception:
            enriched = {}
        if not isinstance(enriched, dict):
            return
        if not model.mmlu_pro and enriched.get("mmlu_pro"):
            model.mmlu_pro = float(enriched["mmlu_pro"])
        if not model.human_eval and enriched.get("human_eval"):
            model.human_eval = float(enriched["human_eval"])
        if not model.ttft_ms and enriched.get("ttft_ms"):
            model.ttft_ms = float(enriched["ttft_ms"])

    # ------------------------------------------------------------------
    # -- Summary statistics --------------------------------------------
    # ------------------------------------------------------------------

    def _compute_summary(self, report: MarketIntelligenceReport) -> None:
        report.total_models_scanned = len(report.models)
        report.local_optimal_count = sum(
            1 for m in report.models if m.vram_class == VRAM_LOCAL_OPTIMAL
        )
        report.cloud_cost_effective_count = sum(
            1 for m in report.models if m.vram_class == VRAM_CLOUD_COST_EFFECTIVE
        )
        report.frontier_reasoning_count = sum(
            1 for m in report.models if m.vram_class == VRAM_FRONTIER_REASONING
        )
        report.local_no_key_count = sum(
            1 for m in report.models if m.access_tier == AccessTier.LOCAL_NO_KEY.value
        )
        report.cloud_zero_config_free_count = sum(
            1 for m in report.models
            if m.access_tier == AccessTier.CLOUD_ZERO_CONFIG_FREE.value
        )
        report.cloud_free_tier_with_key_count = sum(
            1 for m in report.models
            if m.access_tier == AccessTier.CLOUD_FREE_TIER_WITH_KEY.value
        )
        report.cloud_paid_api_count = sum(
            1 for m in report.models if m.access_tier == AccessTier.CLOUD_PAID_API.value
        )
        prices = [
            (m.pricing_prompt_per_1m_usd + m.pricing_completion_per_1m_usd)
            for m in report.models
            if (m.pricing_prompt_per_1m_usd or m.pricing_completion_per_1m_usd)
        ]
        report.average_price_per_1m_usd = (
            round(sum(prices) / len(prices), 4) if prices else 0.0
        )

    # ------------------------------------------------------------------
    # -- Transport and static parsing helpers --------------------------
    # ------------------------------------------------------------------

    @staticmethod
    def _http_get_json(url: str, params: Optional[Dict[str, str]] = None) -> Any:
        try:
            import requests
        except ImportError:
            return None
        try:
            resp = requests.get(url, params=params, timeout=8.0)
            if resp.status_code != 200:
                return None
            return resp.json()
        except Exception:
            return None

    def _active_provider_count(self) -> int:
        try:
            from src.services.cognitive_mesh.registry import get_provider_registry
            return len(get_provider_registry().list_active())
        except Exception:
            return 0

    @staticmethod
    def _parse_param_count(text: Optional[str]) -> Optional[float]:
        match = _PARAM_RE.search(text or "")
        if not match:
            return None
        try:
            return float(match.group(1))
        except ValueError:
            return None

    @staticmethod
    def _extract_license(item: Dict[str, Any]) -> str:
        license_val = item.get("license") or item.get("cardData", {}).get("license")
        if isinstance(license_val, dict):
            license_val = license_val.get("name", "")
        if license_val:
            return str(license_val).lower()
        for tag in item.get("tags") or []:
            if isinstance(tag, str) and tag.startswith("license:"):
                return tag.split(":", 1)[1].lower()
        return ""

    @staticmethod
    def _iso_date(item: Dict[str, Any]) -> Optional[str]:
        for key in ("lastModified", "createdAt", "last_modified"):
            value = item.get(key)
            if value:
                return str(value)[:10]
        return None

    @staticmethod
    def _price_per_1m(value: Any) -> float:
        try:
            numeric = float(value)
        except (TypeError, ValueError):
            return 0.0
        if numeric <= 0:
            return 0.0
        if numeric < 0.01:
            return round(numeric * 1_000_000.0, 4)
        return round(numeric, 4)


# -- v5.22.1: backward-compatible alias. The historical name is preserved so
# -- every pre-existing importer (talos.py, client.py, server.py, and the test
# -- suite) continues to work unchanged while ModelScoutAgent is the primary
# -- canonical class definition. --
ModelScavengerAgent = ModelScoutAgent

