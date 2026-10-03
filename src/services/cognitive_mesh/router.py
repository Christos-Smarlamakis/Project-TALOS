# -*- coding: utf-8 -*-
"""
Module: router.py
Project: TALOS v5.22.1
Description:
    Decoupled, extraction-ready Cognitive Meta-Router. This module selects an
    inference provider for a scientific task using one of four named routing
    strategies and protects the runtime with a session-scoped circuit breaker
    and quota-latching state machine. It is deliberately isolated from TALOS
    storage, PRISMA evaluation, and CLI concerns so that, in v6.0.0, the module
    can be lifted verbatim into a standalone SYNAPSE (:8000) microservice shared
    between TALOS and MEMEX with zero dependency surgery.

    The router exposes five strategies:
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

    Key design decisions:
    - Zero imports from SQLite WAL storage, PRISMA pipelines, or CLI scripts;
      all data interchange uses standalone Pydantic v2 DTOs and the decoupled
      provider registry (src/services/cognitive_mesh/registry.py).
    - HTTP 401 / 402 / 429 responses latch a provider offline for the current
      process session and transparently fail over to the next candidate in the
      same tier.
    - Local (Ollama) invocations are serialized behind a semaphore of width two
      to protect the RTX 4070 (12 GB VRAM) budget from OOM collisions.
    - Inference is performed through an injectable transport callable so the
      router is fully unit-testable without a live endpoint.

Dependencies:
    - threading, time, collections: concurrency arbiter, timing, and metric
      storage.
    - src.services.cognitive_mesh.dto: RoutingStrategy / RouterTaskRequest /
      RouterTaskResponse standalone Pydantic v2 DTOs.
    - src.services.cognitive_mesh.registry: decoupled provider catalogue
      (config-only).
"""

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
    RoutingStrategy,
    RouterTaskRequest,
    RouterTaskResponse,
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
    """

    def __init__(
        self,
        registry: Optional[ProviderRegistry] = None,
        transport: Optional[Callable[[str, str, RouterTaskRequest], Dict[str, Any]]] = None,
        local_semaphore_limit: int = 2,
        ema_alpha: float = 0.2,
    ) -> None:
        self._registry = registry if registry is not None else get_provider_registry()
        self._transport = transport
        self._local_semaphore = threading.Semaphore(local_semaphore_limit)
        self._ema_alpha = ema_alpha
        self._metrics: Dict[str, _ProviderMetrics] = defaultdict(_ProviderMetrics)

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
            return
        if http_status is not None and http_status >= 400:
            self._record_error(provider)
            return
        self._record_success(provider, latency_ms, prompt_tokens, completion_tokens)

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
        candidates = self._candidates_for_strategy(request.strategy, active)
        latched: List[str] = []
        last_error: Optional[Exception] = None

        for provider_name in candidates:
            if provider_name not in active:
                continue
            if self._is_latched(provider_name):
                latched.append(provider_name)
                continue
            try:
                result = self._invoke(provider_name, request)
                if latched:
                    result.fallback_occurred = True
                    result.latched_providers = list(latched)
                return result
            except ProviderHttpError as exc:
                if exc.status_code in LATCH_STATUSES:
                    self._latch(provider_name, exc.status_code)
                    latched.append(provider_name)
                else:
                    self._record_error(provider_name)
                last_error = exc
            except Exception as exc:  # pragma: no cover - defensive
                self._record_error(provider_name)
                last_error = exc

        return RouterTaskResponse(
            provider="",
            model="",
            content=None,
            strategy=request.strategy,
            fallback_occurred=bool(latched) or last_error is not None,
            latched_providers=latched,
        )

    def _invoke(self, provider_name: str, request: RouterTaskRequest) -> RouterTaskResponse:
        descriptor = self._registry.get(provider_name)
        model = descriptor.default_model if descriptor else provider_name
        is_local = provider_name == "ollama"

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





