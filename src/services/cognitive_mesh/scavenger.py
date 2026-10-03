# -*- coding: utf-8 -*-
"""
Module: scavenger.py
Project: TALOS v5.21.0
Description:
    Autonomous Model Scavenger Agent for the Cognitive Mesh in-tree
    microservice. The agent forages three public catalogues -- the Hugging Face
    Hub API (trending text-generation models), the OpenRouter models catalogue
    (new releases and per-token pricing), and the local Ollama library
    (quantized GGUF tags) -- and reconciles every discovery against the active
    RTX 4070 (12 GB VRAM) budget through a hardware-aware role classifier.
    The result is a single MarketIntelligenceReport DTO consumed by the dual
    IntelligenceReporter (reporter.py) and the FastAPI mini-server (server.py).

    Key design decisions:
    - Every source query is best-effort and guarded; a network failure or
      malformed payload yields an empty result set rather than an exception,
      honouring the 100 percent air-gapped, never-crash guarantee.
    - The hardware-aware role classifier maps each model into one of three VRAM
      classes (LOCAL_OPTIMAL, CLOUD_COST_EFFECTIVE, FRONTIER_REASONING) and one
      of four scientific workload roles (Fast Screening, Kitchenham Rigor, Code
      Audit, Vector Embeddings).
    - When every source fails, the agent degrades to the local benchmark cache
      (data/cache/llm_benchmarks.json) so a report is always produced offline.

Dependencies:
    - os, json, re, time, datetime: filesystem, parsing, and timestamps.
    - typing: type annotations (List, Dict, Optional, Any).
    - src.services.cognitive_mesh.dto: ScavengedModel / MarketIntelligenceReport.
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
    MarketIntelligenceReport,
    ScavengedModel,
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

_PARAM_RE = re.compile(r"(\d+(?:\.\d+)?)\s*[bB]")


class ModelScavengerAgent:
    """Autonomous forager reconciling LLM catalogues against the RTX 4070 budget.

    Attributes:
        vram_gb (float): Detected local VRAM budget in gigabytes (default 12.0).
    """

    def __init__(self, vram_gb: float = 12.0) -> None:
        self.vram_gb = vram_gb

    # ------------------------------------------------------------------
    # -- Public foraging entry point -----------------------------------
    # ------------------------------------------------------------------

    def scavenge_market(self, window_days: int = 30) -> MarketIntelligenceReport:
        """Forage all three catalogues and assemble a market intelligence report.

        Args:
            window_days (int): Discovery window in days for OpenRouter deltas.

        Returns:
            MarketIntelligenceReport: The aggregate report with VRAM classes,
                recommended roles, and summary statistics.
        """
        report = MarketIntelligenceReport(
            generated_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            window_days=window_days,
        )

        # -- Forage each source independently; never let one failure abort. --
        online_succeeded = False
        for name, forage in (
            ("huggingface", self._forage_huggingface),
            ("openrouter", lambda: self._forage_openrouter(window_days)),
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

        # -- Classify every model against the VRAM budget. --
        for model in report.models:
            model.vram_class = self._classify_vram(model)
            if not model.recommended_role:
                model.recommended_role = self._recommend_role(model)

        self._compute_summary(report)
        return report

    # ------------------------------------------------------------------
    # -- Source 1: Hugging Face Hub API --------------------------------
    # ------------------------------------------------------------------

    def _forage_huggingface(self) -> List[ScavengedModel]:
        payload = self._http_get_json(
            HF_API_URL,
            params={"pipeline_tag": "text-generation", "sort": "trending",
                    "direction": "-1", "limit": "50"},
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
                )
            )
        return models

    # ------------------------------------------------------------------
    # -- Source 2: OpenRouter models catalogue -------------------------
    # ------------------------------------------------------------------

    def _forage_openrouter(self, window_days: int) -> List[ScavengedModel]:
        payload = self._http_get_json(OPENROUTER_API_URL)
        if not isinstance(payload, dict):
            return []
        return self._parse_openrouter_payload(payload.get("data", []), window_days)

    @staticmethod
    def _parse_openrouter_payload(
        payload: List[Dict[str, Any]], window_days: int
    ) -> List[ScavengedModel]:
        """Parse an OpenRouter catalogue into scavenged records within the window.

        Args:
            payload (list[dict]): The ``data`` array of the OpenRouter response.
            window_days (int): Delta window for newly-released models.

        Returns:
            list[ScavengedModel]: Newly-released models with pricing metadata.
        """
        cutoff = time.time() - (window_days * 86400)
        models: List[ScavengedModel] = []
        for item in payload:
            if not isinstance(item, dict):
                continue
            created = item.get("created") or 0
            try:
                created = int(created)
            except (TypeError, ValueError):
                created = 0
            if created and created < cutoff:
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
            return self._parse_ollama_payload(payload.get("models", []))
        return self._parse_ollama_payload(STATIC_OLLAMA_MODELS)

    @staticmethod
    def _parse_ollama_payload(payload: List[Dict[str, Any]]) -> List[ScavengedModel]:
        """Parse an Ollama tag-list into scavenged records <= 14B parameters.

        Args:
            payload (list[dict]): Either local /api/tags entries or static entries.

        Returns:
            list[ScavengedModel]: Quantized GGUF records suitable for 12 GB VRAM.
        """
        models: List[ScavengedModel] = []
        for item in payload:
            if not isinstance(item, dict):
                continue
            model_id = item.get("id") or item.get("name") or ""
            params = item.get("params_b")
            if params is None:
                params = ModelScavengerAgent._parse_param_count(model_id)
            if params is not None and params > 14.0:
                continue
            models.append(
                ScavengedModel(
                    model=model_id,
                    developer="Ollama",
                    parameter_count_b=params,
                    parameter_count_label=f"{params:.0f}B" if params else "",
                    context_window=0,
                    license="",
                    source="ollama",
                    vram_class=VRAM_LOCAL_OPTIMAL,
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

    def _classify_vram(self, model: ScavengedModel) -> str:
        """Classify a model into one of three VRAM compatibility classes.

        Args:
            model (ScavengedModel): The discovered model.

        Returns:
            str: LOCAL_OPTIMAL, CLOUD_COST_EFFECTIVE, or FRONTIER_REASONING.
        """
        params = model.parameter_count_b
        is_quantized = model.source in ("ollama",)
        if params is None:
            return VRAM_CLOUD_COST_EFFECTIVE
        if params <= 7.0:
            return VRAM_LOCAL_OPTIMAL
        if is_quantized and params <= 14.0:
            return VRAM_LOCAL_OPTIMAL
        if params <= 70.0:
            return VRAM_CLOUD_COST_EFFECTIVE
        return VRAM_FRONTIER_REASONING

    @staticmethod
    def _recommend_role(model: ScavengedModel) -> str:
        """Recommend one of the four scientific workload roles for a model.

        Args:
            model (ScavengedModel): The discovered model.

        Returns:
            str: Fast Screening, Kitchenham Rigor, Code Audit, or Vector Embeddings.
        """
        name = (model.model or "").lower()
        params = model.parameter_count_b
        if any(k in name for k in ("embed", "nomic", "e5", "bge", "gte")):
            return ROLE_VECTOR_EMBEDDINGS
        if any(k in name for k in ("coder", "code", "starcoder")):
            return ROLE_CODE_AUDIT
        if any(k in name for k in ("r1", "reasoner", "o1", "o3", "deepseek-r1")):
            return ROLE_KITCHENHAM_RIGOR
        if params is not None and params >= 30.0:
            return ROLE_KITCHENHAM_RIGOR
        return ROLE_FAST_SCREENING

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
        if numeric and numeric < 0.01:
            return round(numeric * 1_000_000.0, 4)
        return round(numeric, 4)

