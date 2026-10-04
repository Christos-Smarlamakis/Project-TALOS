# -*- coding: utf-8 -*-
"""
Module: router.py
Project: TALOS v5.25.0
Description:
    Decoupled, extraction-ready Cognitive Meta-Router. This module selects an
    inference provider for a scientific task using one of six named routing
    strategies and protects the runtime with a self-healing six-state circuit
    breaker (SelfHealingCircuitBreaker), a session-scoped quota-latching state
    machine, and dynamic zero-config failover to free-tier endpoints. It is
    deliberately isolated from TALOS
    storage, PRISMA evaluation, and CLI concerns so that, in v6.0.0, the module
    can be lifted verbatim into a standalone SYNAPSE (:8000) microservice shared
    between TALOS and MEMEX with zero dependency surgery.

    The router exposes six strategies:
      - LOWEST_LATENCY   : dispatch to the fastest active provider (Groq,
                           Cerebras, SambaNova, or local Ollama) ranked by an
                           exponential moving average of time-to-first-token.
      - REASONING_RIGOR  : dispatch to DeepSeek, Anthropic Claude, or SambaNova
                           Llama 405B for forensic scientific audits.
      - LOWEST_COST      : select the cheapest active provider whose quality
                           score meets the floor Q_min >= 0.70.
      - LOCAL_AIRGAPPED  : strictly local Ollama on port 11434, zero outbound
                           network egress, bounded by threading.Semaphore(2).
      - LOCAL_FIRST_CLOUD_BACKUP : attempt local Ollama first, then dynamically
                           fail over to the active cloud tier (v5.21.1).

      - AUTO_SWARM_CASCADE   : dynamically size the swarm (K = f(C)) via the
                            DynamicSwarmSizer and relay across the free-tier
                            frontier, logging every decision to the XAI ledger
                            (v5.25.0).


    Key design decisions:
    - Zero imports from SQLite WAL storage, PRISMA pipelines, or CLI scripts;
      all data interchange uses standalone Pydantic v2 DTOs and the decoupled
      provider registry (src/services/cognitive_mesh/registry.py).
    - HTTP 401 / 402 / 429 responses latch a provider offline for the current
      process session and transparently fail over to the next candidate in the
      same tier.
    - The SelfHealingCircuitBreaker adds a six-state machine with exponential
      backoff; when every primary candidate is latched, rate-limited, or
      unreachable, the router auto-fails over to the top available
      LOCAL_NO_KEY or CLOUD_ZERO_CONFIG_FREE candidate (v5.23.0).
    - Local (Ollama) invocations are serialized behind a semaphore of width two
      to protect the RTX 4070 (12 GB VRAM) budget from OOM collisions.
    - Inference is performed through an injectable transport callable so the
      router is fully unit-testable without a live endpoint.

Dependencies:
    - threading, time, collections: concurrency arbiter, timing, and metric
      storage.
    - src.services.cognitive_mesh.dto: RoutingStrategy / RouterTaskRequest /
      RouterTaskResponse / AccessTier standalone Pydantic v2 DTOs.
    - src.services.cognitive_mesh.registry: decoupled provider catalogue
      (config-only).
    - src.services.cognitive_mesh.self_healing: SelfHealingCircuitBreaker and
      classify_access_tier (six-state resilience + access-tier taxonomy).
"""

import json
import os
import threading
import time
from collections import defaultdict
from typing import Any, Callable, Dict, List, Optional

# -- Resolve project root (same pattern as all src/*.py modules) --------------
_P = os.path.abspath(os.path.dirname(__file__))
while _P and not os.path.exists(os.path.join(_P, "talos.py")):
    _P = os.path.dirname(_P)
if _P:
    import sys
    sys.path.insert(0, _P)

# -- Decoupled imports: config-only registry, never storage/PRISMA/CLI ---------
from src.services.cognitive_mesh.registry import (  # noqa: E402
    ProviderRegistry,
    get_provider_registry,
)

# -- HTTP statuses that trigger session-scoped quota latching ------------------
LATCH_STATUSES = (401, 402, 429)

# -- Approximate list prices (USD per 1M prompt / completion tokens) -----------
# Used by LOWEST_COST to select the cheapest provider meeting the quality floor.
_COST_USD_PER_1M: Dict[str, tuple] = {
    "ollama": (0.00, 0.00),
    "nvidia": (0.60, 2.40),
    "deepseek": (0.27, 1.10),
    "gemini": (0.15, 0.60),
    "groq": (0.59, 0.79),
    "cerebras": (0.60, 1.20),
    "mistral": (0.20, 0.60),
    "huggingface": (0.10, 0.40),
    "openrouter": (0.30, 1.20),
    "anthropic": (3.00, 15.00),
    "sambanova": (0.60, 2.40),
    "together": (0.88, 0.88),
    "fireworks": (0.90, 0.90),
    "deepinfra": (0.59, 0.79),
    "cohere": (0.15, 0.60),
    "perplexity": (1.00, 1.00),
}

# -- Static quality scores (0..1) approximating model capability --------------
_PROVIDER_QUALITY: Dict[str, float] = {
    "ollama": 0.72,
    "nvidia": 0.91,
    "deepseek": 0.95,
    "gemini": 0.93,
    "groq": 0.85,
    "cerebras": 0.84,
    "mistral": 0.80,
    "huggingface": 0.70,
    "openrouter": 0.82,
    "anthropic": 0.96,
    "sambanova": 0.90,
    "together": 0.86,
    "fireworks": 0.83,
    "deepinfra": 0.81,
    "cohere": 0.88,
    "perplexity": 0.89,
}


from src.services.cognitive_mesh.dto import (  # noqa: E402
    AccessTier,
    RoutingStrategy,
    RouterTaskRequest,
    RouterTaskResponse,
    SwarmSizingRecommendation,
    TaskComplexity,
    XAiDecisionRecord,
)
from src.services.cognitive_mesh.xai_ledger import XAiDecisionLedger  # noqa: E402
from src.services.cognitive_mesh.self_healing import (  # noqa: E402
    SelfHealingCircuitBreaker,
    classify_access_tier,
)
from src.services.cognitive_mesh.rate_limiter import (  # noqa: E402
    TokenBucketRateLimiter,
)


class ProviderHttpError(Exception):
    """Transport error carrying an HTTP status code.

    Attributes:
        provider (str): Provider that raised the error.
        status_code (int): HTTP status (401/402/429 trigger latching).
    """

    def __init__(self, provider: str, status_code: int, message: str = ""):
        super().__init__(message or f"{provider} returned HTTP {status_code}")
        self.provider = provider
        self.status_code = status_code


class _ProviderMetrics:
    """Per-provider runtime telemetry tracked by the router."""

    def __init__(self) -> None:
        self.ema_ttft_ms: Optional[float] = None
        self.throughput_tps: float = 0.0
        self.consecutive_errors: int = 0
        self.latched: bool = False
        self.latch_reason: Optional[int] = None


class DynamicSwarmSizer:
    """Dynamic swarm cardinality selector mapping task complexity to K.

    Computes a composite complexity score C in [0, 1] from the task's token
    volume, reasoning depth, and operational safety category, then maps C to
    the optimal swarm cardinality K in {1, 2, 3, 5} and selects an ordered
    model chain through the free-tier frontier cascade. Every recommendation
    is optionally persisted to the XAI decision ledger.

    Attributes:
        registry (ProviderRegistry): Provider catalogue (default: shared
            singleton). Injectable for hermetic tests.
        ledger (Optional[XAiDecisionLedger]): Injected XAI audit ledger.
    """

    _FREE_TIERS = (
        "LOCAL_NO_KEY",
        "CLOUD_ZERO_CONFIG_FREE",
        "CLOUD_FREE_TIER_WITH_KEY",
    )

    _TASK_DEPTH: Dict[str, float] = {
        "parsing": 0.1,
        "extraction": 0.1,
        "normalization": 0.1,
        "classification": 0.15,
        "summarization": 0.4,
        "redaction": 0.4,
        "translation": 0.4,
        "consensus": 0.65,
        "consensus_verification": 0.65,
        "verification": 0.65,
        "audit": 0.65,
        "kitchenham": 0.7,
        "appraisal": 0.7,
        "documentation": 0.95,
        "code_audit": 0.9,
        "synthesis": 0.95,
        "deep_synthesis": 0.95,
    }

    def __init__(
        self,
        registry: Optional[ProviderRegistry] = None,
        ledger: Optional[XAiDecisionLedger] = None,
    ) -> None:
        self._registry = registry if registry is not None else get_provider_registry()
        self._ledger = ledger

    def recommend_swarm(
        self,
        task_type: str,
        input_payload: Optional[Dict[str, Any]] = None,
    ) -> SwarmSizingRecommendation:
        """Recommend an optimal swarm cardinality and ordered model chain.

        Args:
            task_type (str): Semantic task label.
            input_payload (Optional[dict]): Task payload for complexity scoring.

        Returns:
            SwarmSizingRecommendation: The recommended K and model chain.
        """
        payload = input_payload or {}
        complexity = self._compute_complexity(task_type, payload)
        band = self._band_for_complexity(complexity)
        swarm_size = self._swarm_size_for_band(band)
        active = self._active_provider_names()
        model_chain = self._ordered_model_chain(active, swarm_size)
        access_tiers = [slot["access_tier"] for slot in model_chain]
        safety_category = str(payload.get("safety_category", "standard"))
        rationale = self._build_rationale(task_type, complexity, swarm_size, band)

        recommendation = SwarmSizingRecommendation(
            task_type=str(task_type),
            complexity_score=round(complexity, 4),
            complexity_band=band,
            swarm_size=swarm_size,
            model_chain=model_chain,
            access_tiers=access_tiers,
            rationale=rationale,
            safety_category=safety_category,
        )

        if self._ledger is not None:
            self._ledger.append(
                XAiDecisionRecord(
                    task_type=str(task_type),
                    complexity_score=recommendation.complexity_score,
                    swarm_size=swarm_size,
                    candidate_models=[slot["model"] for slot in model_chain],
                    pareto_rationale=rationale,
                    safety_flags=self._safety_flags(payload),
                    fallback_cascade=self._free_tier_frontier(active),
                )
            )
        return recommendation

    # ------------------------------------------------------------------
    # -- Complexity estimation -------------------------------------------
    # ------------------------------------------------------------------

    def _compute_complexity(
        self, task_type: str, payload: Dict[str, Any]
    ) -> float:
        depth = self._reasoning_depth(str(task_type))
        tokens = self._token_score(payload)
        safety = self._safety_score(payload)
        return min(1.0, max(0.0, 0.8 * depth + 0.15 * tokens + 0.05 * safety))

    @classmethod
    def _reasoning_depth(cls, task_type: str) -> float:
        key = task_type.lower()
        for label, score in cls._TASK_DEPTH.items():
            if label in key:
                return score
        return 0.5

    @staticmethod
    def _token_score(payload: Dict[str, Any]) -> float:
        text = payload.get("text") or payload.get("content") or ""
        if not text:
            text = json.dumps(payload, default=str)
        tokens = len(str(text)) / 4.0
        return min(1.0, tokens / 4000.0)

    @staticmethod
    def _safety_score(payload: Dict[str, Any]) -> float:
        category = str(payload.get("safety_category", "")).lower()
        if category in ("high_consequence", "high-consequence", "safety_critical"):
            return 1.0
        if "geofence" in str(payload).lower():
            return 0.6
        return 0.0

    @staticmethod
    def _band_for_complexity(complexity: float) -> str:
        if complexity < 0.25:
            return TaskComplexity.PARSING.value
        if complexity < 0.5:
            return TaskComplexity.SUMMARIZATION.value
        if complexity < 0.75:
            return TaskComplexity.CONSENSUS_VERIFICATION.value
        return TaskComplexity.DEEP_SYNTHESIS.value

    @staticmethod
    def _swarm_size_for_band(band: str) -> int:
        return {
            TaskComplexity.PARSING.value: 1,
            TaskComplexity.SUMMARIZATION.value: 2,
            TaskComplexity.CONSENSUS_VERIFICATION.value: 3,
            TaskComplexity.DEEP_SYNTHESIS.value: 5,
        }[band]

    @staticmethod
    def _build_rationale(
        task_type: str, complexity: float, swarm_size: int, band: str
    ) -> str:
        return (
            "Task '{}' scored complexity C={:.3f} (band '{}'); selected swarm "
            "cardinality K={} to balance latency, cost, and cross-model "
            "agreement."
        ).format(task_type, complexity, band, swarm_size)

    @staticmethod
    def _safety_flags(payload: Dict[str, Any]) -> Dict[str, bool]:
        text = str(payload).lower()
        return {
            "geofence_checked": "geofence" in text,
            "consent_checked": "consent" in text,
            "airgapped": bool(payload.get("airgapped", False)),
        }

    # ------------------------------------------------------------------
    # -- Model chain selection -------------------------------------------
    # ------------------------------------------------------------------

    def _active_provider_names(self) -> List[str]:
        try:
            return [d.name for d in self._registry.list_active()]
        except Exception:
            return []

    def _free_tier_frontier(self, active: List[str]) -> List[str]:
        ordered = [p for p in active if p == "ollama"]
        ordered += [
            p
            for p in active
            if p != "ollama" and classify_access_tier(p) in self._FREE_TIERS
        ]
        return ordered

    def _ordered_model_chain(
        self, active: List[str], k: int
    ) -> List[Dict[str, str]]:
        frontier = self._free_tier_frontier(active)
        chain: List[Dict[str, str]] = []
        seen: set = set()
        for provider in frontier:
            if len(chain) >= k:
                break
            if provider in seen:
                continue
            seen.add(provider)
            chain.append(self._chain_slot(provider))
        if len(chain) < k:
            remaining = sorted(
                [p for p in active if p not in seen],
                key=lambda p: _PROVIDER_QUALITY.get(p, 0.0),
                reverse=True,
            )
            for provider in remaining:
                if len(chain) >= k:
                    break
                if provider in seen:
                    continue
                seen.add(provider)
                chain.append(self._chain_slot(provider))
        return chain

    def _chain_slot(self, provider: str) -> Dict[str, str]:
        descriptor = self._registry.get(provider)
        model = descriptor.default_model if descriptor else provider
        return {
            "provider": provider,
            "model": model,
            "access_tier": classify_access_tier(provider),
        }


class CognitiveMetaRouter:
    """Decoupled multi-strategy cognitive meta-router with circuit breaking.

    Attributes:
        registry (ProviderRegistry): Provider catalogue (default: shared
            singleton). Injectable for hermetic tests.
        transport (Optional[Callable]): Optional callable of the form
            ``transport(provider_name, model, request) -> dict``. When omitted
            the router performs decision-only dispatch (no network I/O).
        local_semaphore (threading.Semaphore): Concurrency arbiter for local
            GPU calls (default width two).
        ema_alpha (float): Smoothing factor for time-to-first-token EMA.
        breaker (Optional[SelfHealingCircuitBreaker]): Injected six-state
            breaker (default: a fresh instance).
        swarm_sizer (Optional[DynamicSwarmSizer]): Injected swarm sizer
            (default: lazily created with the shared ledger).
        ledger (Optional[XAiDecisionLedger]): Injected XAI audit ledger.
    """

    def __init__(
        self,
        registry: Optional[ProviderRegistry] = None,
        transport: Optional[Callable[[str, str, RouterTaskRequest], Dict[str, Any]]] = None,
        local_semaphore_limit: int = 2,
        ema_alpha: float = 0.2,
        breaker: Optional[SelfHealingCircuitBreaker] = None,
        rate_limiter: Optional[TokenBucketRateLimiter] = None,
        swarm_sizer: Optional[DynamicSwarmSizer] = None,
        ledger: Optional[XAiDecisionLedger] = None,
    ) -> None:
        self._registry = registry if registry is not None else get_provider_registry()
        self._transport = transport
        self._local_semaphore = threading.Semaphore(local_semaphore_limit)
        self._ema_alpha = ema_alpha
        self._metrics: Dict[str, _ProviderMetrics] = defaultdict(_ProviderMetrics)
        self._breaker = breaker if breaker is not None else SelfHealingCircuitBreaker()
        self._rate_limiter = (
            rate_limiter if rate_limiter is not None else TokenBucketRateLimiter()
        )
        self._swarm_sizer = swarm_sizer
        self._ledger = ledger

    # ------------------------------------------------------------------
    # -- Public dispatch API -------------------------------------------
    # ------------------------------------------------------------------

    def dispatch(
        self,
        task_type: Any,
        strategy: Optional[RoutingStrategy] = None,
        payload: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> RouterTaskResponse:
        """Route a task under the requested strategy with circuit breaking.

        Accepts either the DTO form ``dispatch(RouterTaskRequest(...))`` or the
        positional form ``dispatch(task_type, strategy, payload)``.

        Args:
            task_type (Any): A ``RouterTaskRequest`` or a semantic task string.
            strategy (Optional[RoutingStrategy]): Routing strategy (positional).
            payload (Optional[dict]): Task payload (positional form).
            **kwargs: Additional ``RouterTaskRequest`` fields (positional form).

        Returns:
            RouterTaskResponse: The dispatch result, including any fallback.
        """
        if isinstance(task_type, RouterTaskRequest):
            request = task_type
        else:
            request = RouterTaskRequest(
                task_type=str(task_type),
                strategy=strategy or RoutingStrategy.LOWEST_LATENCY,
                payload=payload or {},
                **kwargs,
            )
        return self._execute(request)

    def recommend_swarm(
        self,
        task_type: str,
        input_payload: Optional[Dict[str, Any]] = None,
    ) -> SwarmSizingRecommendation:
        """Recommend an optimal swarm cardinality and ordered model chain.

        Delegates to the injected (or lazily created) ``DynamicSwarmSizer`` and
        logs the resulting decision to the XAI ledger when one is configured.

        Args:
            task_type (str): Semantic task label.
            input_payload (Optional[dict]): Task payload for complexity scoring.

        Returns:
            SwarmSizingRecommendation: The recommended K and model chain.
        """
        return self._get_swarm_sizer().recommend_swarm(task_type, input_payload)

    def _get_swarm_sizer(self) -> "DynamicSwarmSizer":
        """Return the swarm sizer, creating it lazily with the shared ledger."""
        if self._swarm_sizer is None:
            self._swarm_sizer = DynamicSwarmSizer(self._registry, self._ledger)
        return self._swarm_sizer

    def record_result(
        self,
        provider: str,
        *,
        latency_ms: float,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        http_status: Optional[int] = None,
    ) -> None:
        """Record an external call outcome to update metrics and latching.

        Intended for callers that perform their own HTTP transport and report
        results back to the router for telemetry and circuit-breaking.

        Args:
            provider (str): Provider name.
            latency_ms (float): End-to-end latency in milliseconds.
            prompt_tokens (int): Prompt tokens consumed.
            completion_tokens (int): Completion tokens produced.
            http_status (Optional[int]): HTTP status, if the call failed.
        """
        if http_status in LATCH_STATUSES:
            self._latch(provider, http_status)
            self._breaker.record_http_status(provider, http_status)
            return
        if http_status is not None and http_status >= 400:
            self._record_error(provider)
            self._breaker.record_http_status(provider, http_status)
            return
        self._record_success(provider, latency_ms, prompt_tokens, completion_tokens)
        self._breaker.record_success(provider)

    def latch_provider(self, provider: str, reason: int = 429) -> None:
        """Manually latch a provider offline for the current session.

        Args:
            provider (str): Provider name.
            reason (int): Latch reason status code.
        """
        self._latch(provider, reason)

    def release_provider(self, provider: str) -> None:
        """Unlatch a provider, returning it to the candidate pool.

        Args:
            provider (str): Provider name.
        """
        metrics = self._metrics[provider]
        metrics.latched = False
        metrics.latch_reason = None

    def get_metrics(self) -> Dict[str, Dict[str, Any]]:
        """Return a snapshot of runtime provider telemetry.

        Returns:
            dict: Provider name to metric dictionary.
        """
        snapshot: Dict[str, Dict[str, Any]] = {}
        for name, metrics in self._metrics.items():
            snapshot[name] = {
                "ema_ttft_ms": metrics.ema_ttft_ms,
                "throughput_tps": metrics.throughput_tps,
                "consecutive_errors": metrics.consecutive_errors,
                "latched": metrics.latched,
                "latch_reason": metrics.latch_reason,
            }
        return snapshot

    # ------------------------------------------------------------------
    # -- Core execution pipeline ---------------------------------------
    # ------------------------------------------------------------------

    def _execute(self, request: RouterTaskRequest) -> RouterTaskResponse:
        active = self._active_provider_names()
        if request.strategy == RoutingStrategy.AUTO_SWARM_CASCADE:
            recommendation = self.recommend_swarm(request.task_type, request.payload)
            candidates = [slot["provider"] for slot in recommendation.model_chain]
        else:
            candidates = self._candidates_for_strategy(request.strategy, active)
        latched: List[str] = []
        last_error: Optional[Exception] = None

        def _attempt(provider_name: str) -> Optional[RouterTaskResponse]:
            """Invoke one provider, folding outcomes into the breaker."""
            try:
                result = self._invoke(provider_name, request)
                if latched:
                    result.fallback_occurred = True
                    result.latched_providers = list(latched)
                return result
            except ProviderHttpError as exc:
                self._breaker.record_http_status(provider_name, exc.status_code)
                if exc.status_code in LATCH_STATUSES:
                    self._latch(provider_name, exc.status_code)
                    latched.append(provider_name)
                else:
                    self._record_error(provider_name)
                last_error = exc
            except Exception as exc:  # pragma: no cover - defensive
                self._breaker.record_timeout(provider_name)
                self._record_error(provider_name)
                last_error = exc
            return None

        for provider_name in candidates:
            if provider_name not in active:
                continue
            if self._is_latched(provider_name):
                latched.append(provider_name)
                continue
            if not self._breaker.should_attempt(provider_name):
                latched.append(provider_name)
                continue
            result = _attempt(provider_name)
            if result is not None:
                return result

        # -- v5.23.0: dynamic zero-config failover to free-tier candidates. --
        for provider_name in self._zero_config_free_failover(active):
            if provider_name in candidates:
                continue
            if self._is_latched(provider_name):
                continue
            if not self._breaker.should_attempt(provider_name):
                continue
            result = _attempt(provider_name)
            if result is not None:
                return result

        return RouterTaskResponse(
            provider="",
            model="",
            content=None,
            strategy=request.strategy,
            fallback_occurred=bool(latched) or last_error is not None,
            latched_providers=latched,
        )

    def _zero_config_free_failover(self, active: List[str]) -> List[str]:
        """Return free-tier candidates for dynamic zero-config failover.

        Providers whose access tier is LOCAL_NO_KEY or CLOUD_ZERO_CONFIG_FREE
        are preferred fallback targets when paid endpoints are latched or
        rate-limited. Local Ollama is always ranked first for air-gapped
        operation.

        Args:
            active (list[str]): Currently active provider names.

        Returns:
            list[str]: Free-tier provider names in failover priority order.
        """
        free = [
            p for p in active
            if classify_access_tier(p) in (
                AccessTier.LOCAL_NO_KEY.value,
                AccessTier.CLOUD_ZERO_CONFIG_FREE.value,
            )
        ]
        ordered = [p for p in free if p == "ollama"] + [p for p in free if p != "ollama"]
        return ordered

    def _invoke(self, provider_name: str, request: RouterTaskRequest) -> RouterTaskResponse:
        descriptor = self._registry.get(provider_name)
        model = descriptor.default_model if descriptor else provider_name
        is_local = provider_name == "ollama"

        # -- v5.24.0: proactive token-bucket throttle before outbound dispatch. --
        # Decision-only dispatch (no transport) skips the throttle so hermetic
        # unit tests never incur real wall-clock sleeps.
        if self._transport is not None:
            self._rate_limiter.acquire(provider_name, tokens=1)

        start = time.perf_counter()
        if is_local:
            acquired = self._local_semaphore.acquire(timeout=10.0)
            if not acquired:
                raise RuntimeError("local concurrency budget exhausted")
            try:
                result = self._transport_call(provider_name, model, request)
            finally:
                self._local_semaphore.release()
        else:
            result = self._transport_call(provider_name, model, request)

        latency_ms = (time.perf_counter() - start) * 1000.0
        prompt_tokens = int(result.get("prompt_tokens", 0) or 0)
        completion_tokens = int(result.get("completion_tokens", 0) or 0)
        self._record_success(provider_name, latency_ms, prompt_tokens, completion_tokens)
        self._breaker.record_success(provider_name)

        return RouterTaskResponse(
            provider=provider_name,
            model=model,
            content=result.get("content"),
            latency_ms=latency_ms,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            cost_estimate_usd=self._estimate_cost(
                provider_name, prompt_tokens, completion_tokens
            ),
            strategy=request.strategy,
            fallback_occurred=False,
        )

    def _transport_call(
        self, provider_name: str, model: str, request: RouterTaskRequest
    ) -> Dict[str, Any]:
        if self._transport is None:
            return {"content": None, "prompt_tokens": 0, "completion_tokens": 0}
        result = self._transport(provider_name, model, request)
        if not isinstance(result, dict):
            result = {"content": result}
        status = result.get("status_code")
        if status in LATCH_STATUSES:
            raise ProviderHttpError(provider_name, status)
        return result

    # ------------------------------------------------------------------
    # -- Strategy candidate selection ----------------------------------
    # ------------------------------------------------------------------

    def _candidates_for_strategy(
        self, strategy: RoutingStrategy, active: List[str]
    ) -> List[str]:
        if strategy == RoutingStrategy.LOCAL_AIRGAPPED:
            return ["ollama"]
        if strategy == RoutingStrategy.LOCAL_FIRST_CLOUD_BACKUP:
            fallback = [p for p in active if p != "ollama"]
            return ["ollama"] + fallback
        if strategy == RoutingStrategy.REASONING_RIGOR:
            return ["deepseek", "anthropic", "sambanova"]
        if strategy == RoutingStrategy.LOWEST_LATENCY:
            base = ["groq", "cerebras", "sambanova", "ollama"]
            return sorted(base, key=lambda p: self._ema_ttft(p))
        if strategy == RoutingStrategy.LOWEST_COST:
            qualified = [p for p in active if self._quality(p) >= 0.70]
            return sorted(qualified, key=lambda p: self._combined_cost(p))
        return list(active)

    # ------------------------------------------------------------------
    # -- Metrics and latching helpers ----------------------------------
    # ------------------------------------------------------------------

    def _ema_ttft(self, provider: str) -> float:
        value = self._metrics[provider].ema_ttft_ms
        return value if value is not None else float("inf")

    def _quality(self, provider: str) -> float:
        return _PROVIDER_QUALITY.get(provider, 0.0)

    def _combined_cost(self, provider: str) -> float:
        prompt_price, completion_price = _COST_USD_PER_1M.get(provider, (1.0, 1.0))
        return prompt_price + completion_price

    def _estimate_cost(
        self, provider: str, prompt_tokens: int, completion_tokens: int
    ) -> float:
        prompt_price, completion_price = _COST_USD_PER_1M.get(provider, (1.0, 1.0))
        cost = (prompt_tokens / 1_000_000.0) * prompt_price
        cost += (completion_tokens / 1_000_000.0) * completion_price
        return round(cost, 8)

    def _record_success(
        self, provider: str, latency_ms: float, prompt_tokens: int, completion_tokens: int
    ) -> None:
        metrics = self._metrics[provider]
        if metrics.ema_ttft_ms is None:
            metrics.ema_ttft_ms = latency_ms
        else:
            metrics.ema_ttft_ms = (
                self._ema_alpha * latency_ms
                + (1.0 - self._ema_alpha) * metrics.ema_ttft_ms
            )
        if latency_ms > 0:
            metrics.throughput_tps = completion_tokens / (latency_ms / 1000.0)
        metrics.consecutive_errors = 0

    def _record_error(self, provider: str) -> None:
        self._metrics[provider].consecutive_errors += 1

    def _latch(self, provider: str, reason: int) -> None:
        metrics = self._metrics[provider]
        metrics.latched = True
        metrics.latch_reason = reason

    def _is_latched(self, provider: str) -> bool:
        return self._metrics[provider].latched

    def _active_provider_names(self) -> List[str]:
        try:
            return [d.name for d in self._registry.list_active()]
        except Exception:
            return []





