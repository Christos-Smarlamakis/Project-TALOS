# -*- coding: utf-8 -*-
"""
Module: self_healing.py
Project: TALOS v5.23.0
Description:
    Autonomous self-healing circuit breaker and API health probe engine for the
    Cognitive Mesh in-tree microservice. The module implements the ISO/IEC
    25010 Reliability pillar: a six-state machine (HEALTHY, RATE_LIMITED,
    LATCHED, UNAUTHORIZED, UNREACHABLE, HALF_OPEN) that protects the router from
    degraded providers, together with an exponential-backoff timer
    (T_backoff = min(T0 * 2^k, Tmax)) that doubles the cooldown window on each
    consecutive failure up to a hard ceiling. A concurrent ApiHealthProbeEngine
    pings all sixteen registered providers with lightweight probe requests and
    emits a MeshDiagnosticReport for the CLI, HUD, and reporting surfaces.

    Key design decisions:
    - The breaker is transport-agnostic: it consumes HTTP status codes and
      timeout signals rather than performing network I/O itself, so it is fully
      unit-testable and reusable by both the router and the probe engine.
    - Access tiers are assigned deterministically by canonical provider name
      via classify_access_tier(); the four-tier taxonomy drives zero-config
      failover to LOCAL_NO_KEY / CLOUD_ZERO_CONFIG_FREE candidates.
    - The probe engine accepts an injectable probe callable so its state
      mapping is hermetic under test and air-gapped by default (a provider
      without a key is reported inactive without any network egress).
    - Zero imports from TALOS SQLite storage, PRISMA pipelines, or CLI logic:
      only the standard library, dto.py, and registry.py are imported, so the
      module can be lifted verbatim into a standalone SYNAPSE (:8000)
      microservice.

Dependencies:
    - os, socket, time, threading, concurrent.futures, datetime: environment
      lookup, reachability probes, timing, and concurrent probing.
    - typing: type annotations (Dict, List, Optional, Callable, Tuple, Any).
    - src.services.cognitive_mesh.dto: AccessTier / ProviderHealthState enums
      and ProviderHealthReport / MeshDiagnosticReport DTOs.
    - src.services.cognitive_mesh.registry: ProviderRegistry /
      ProviderDescriptor / get_provider_registry.
"""

import os
import socket
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional, Tuple

# -- Resolve project root (same pattern as all src/*.py modules) --------------
_P = os.path.abspath(os.path.dirname(__file__))
while _P and not os.path.exists(os.path.join(_P, "talos.py")):
    _P = os.path.dirname(_P)
if _P:
    import sys
    sys.path.insert(0, _P)

from src.services.cognitive_mesh.dto import (  # noqa: E402
    AccessTier,
    MeshDiagnosticReport,
    ProviderHealthReport,
    ProviderHealthState,
)
from src.services.cognitive_mesh.registry import (  # noqa: E402
    ProviderDescriptor,
    ProviderRegistry,
    get_provider_registry,
)

# -- Exponential backoff constants (seconds) ------------------------------------
DEFAULT_BACKOFF_SECONDS = 60.0
MAX_BACKOFF_SECONDS = 600.0

# -- Provider-name access-tier mapping ------------------------------------------
# LOCAL_NO_KEY: local runtime, zero key, zero cloud egress.
# CLOUD_ZERO_CONFIG_FREE: cloud endpoint usable without an API key.
# CLOUD_FREE_TIER_WITH_KEY: cloud endpoint with a free tier gated by a key.
# CLOUD_PAID_API: paid cloud endpoint requiring a funded key.
_PROVIDER_ACCESS_TIERS: Dict[str, str] = {
    "ollama": AccessTier.LOCAL_NO_KEY.value,
    "huggingface": AccessTier.CLOUD_ZERO_CONFIG_FREE.value,
    "groq": AccessTier.CLOUD_FREE_TIER_WITH_KEY.value,
    "gemini": AccessTier.CLOUD_FREE_TIER_WITH_KEY.value,
    "mistral": AccessTier.CLOUD_FREE_TIER_WITH_KEY.value,
    "cohere": AccessTier.CLOUD_FREE_TIER_WITH_KEY.value,
    "cerebras": AccessTier.CLOUD_FREE_TIER_WITH_KEY.value,
    "sambanova": AccessTier.CLOUD_FREE_TIER_WITH_KEY.value,
    "together": AccessTier.CLOUD_FREE_TIER_WITH_KEY.value,
    "nvidia": AccessTier.CLOUD_PAID_API.value,
    "deepseek": AccessTier.CLOUD_PAID_API.value,
    "openrouter": AccessTier.CLOUD_PAID_API.value,
    "anthropic": AccessTier.CLOUD_PAID_API.value,
    "fireworks": AccessTier.CLOUD_PAID_API.value,
    "deepinfra": AccessTier.CLOUD_PAID_API.value,
    "perplexity": AccessTier.CLOUD_PAID_API.value,
}

# -- Providers whose tier is zero-config free (no key, no cost) -----------------
_ZERO_CONFIG_FREE_TIERS = frozenset(
    (AccessTier.LOCAL_NO_KEY.value, AccessTier.CLOUD_ZERO_CONFIG_FREE.value)
)


def classify_access_tier(provider_name: str) -> str:
    """Return the four-tier AccessTier value for a canonical provider name.

    Args:
        provider_name (str): Canonical provider identifier (e.g. ``ollama``,
            ``groq``, ``anthropic``). Unknown names default to CLOUD_PAID_API.

    Returns:
        str: The AccessTier value string.
    """
    return _PROVIDER_ACCESS_TIERS.get(
        (provider_name or "").lower(), AccessTier.CLOUD_PAID_API.value
    )


def classify_model_access_tier(source: str = "", provider: str = "") -> str:
    """Return the AccessTier value for a discovered model by source/provider.

    Args:
        source (str): Discovery source (huggingface/openrouter/ollama/benchmarks).
        provider (str): Serving provider fallback when the source is ambiguous.

    Returns:
        str: The AccessTier value string.
    """
    src = (source or "").lower()
    if src == "ollama":
        return AccessTier.LOCAL_NO_KEY.value
    if src == "huggingface":
        return AccessTier.CLOUD_ZERO_CONFIG_FREE.value
    if src == "openrouter":
        return AccessTier.CLOUD_FREE_TIER_WITH_KEY.value
    return classify_access_tier(provider)


class SelfHealingCircuitBreaker:
    """Six-state self-healing circuit breaker with exponential backoff.

    The breaker tracks a per-provider state machine and a monotonically
    increasing cooldown window so that a transiently failing provider is
    excluded from routing until its backoff expires, after which a single
    half-open probe is permitted before the breaker either restores the
    provider to HEALTHY or re-closes it.

    State transitions:
      - HTTP 200        -> HEALTHY (resets error count and backoff).
      - HTTP 429        -> RATE_LIMITED (sets a backoff window).
      - HTTP 402        -> LATCHED (quota depleted; bypassed unless probed).
      - HTTP 401        -> UNAUTHORIZED (invalid credentials).
      - Timeout / 5xx   -> UNREACHABLE (temporary network fault).

    Attributes:
        initial_backoff_seconds (float): T0 in ``T_backoff = min(T0*2^k, Tmax)``.
        max_backoff_seconds (float): Tmax ceiling for the backoff window.
    """

    def __init__(
        self,
        initial_backoff_seconds: float = DEFAULT_BACKOFF_SECONDS,
        max_backoff_seconds: float = MAX_BACKOFF_SECONDS,
    ) -> None:
        self.initial_backoff_seconds = initial_backoff_seconds
        self.max_backoff_seconds = max_backoff_seconds
        self._states: Dict[str, str] = {}
        self._error_counts: Dict[str, int] = {}
        self._backoff_until: Dict[str, float] = {}
        self._lock = threading.Lock()

    # ------------------------------------------------------------------
    # -- Query API -----------------------------------------------------
    # ------------------------------------------------------------------

    def state(self, provider: str) -> str:
        """Return the current ProviderHealthState value for a provider.

        Args:
            provider (str): Canonical provider identifier.

        Returns:
            str: The current health state (defaults to HEALTHY).
        """
        with self._lock:
            return self._states.get(provider, ProviderHealthState.HEALTHY.value)

    def error_count(self, provider: str) -> int:
        """Return the consecutive-error counter for a provider.

        Args:
            provider (str): Canonical provider identifier.

        Returns:
            int: The number of consecutive errors recorded.
        """
        with self._lock:
            return self._error_counts.get(provider, 0)

    def backoff_until(self, provider: str) -> Optional[float]:
        """Return the monotonic timestamp when the backoff window expires.

        Args:
            provider (str): Canonical provider identifier.

        Returns:
            Optional[float]: The backoff expiry timestamp, or None when absent.
        """
        with self._lock:
            return self._backoff_until.get(provider)

    def should_attempt(self, provider: str) -> bool:
        """Return whether the provider may be attempted for routing.

        Expired backoff windows automatically transition the provider to
        HALF_OPEN, permitting exactly one probe attempt before the breaker
        re-closes or restores to HEALTHY.

        Args:
            provider (str): Canonical provider identifier.

        Returns:
            bool: True when the provider is routable (HEALTHY/HALF_OPEN),
                False when latched, unauthorized, or still cooling down.
        """
        with self._lock:
            state = self._states.get(provider, ProviderHealthState.HEALTHY.value)
            if state == ProviderHealthState.LATCHED.value:
                return False
            if state == ProviderHealthState.UNAUTHORIZED.value:
                return False
            if state in (
                ProviderHealthState.HEALTHY.value,
                ProviderHealthState.HALF_OPEN.value,
            ):
                return True
            # RATE_LIMITED / UNREACHABLE: honour the backoff window.
            until = self._backoff_until.get(provider, 0.0)
            if time.monotonic() >= until:
                self._states[provider] = ProviderHealthState.HALF_OPEN.value
                return True
            return False

    # ------------------------------------------------------------------
    # -- Mutation API --------------------------------------------------
    # ------------------------------------------------------------------

    def record_success(self, provider: str) -> None:
        """Restore a provider to HEALTHY, clearing its error state.

        Args:
            provider (str): Canonical provider identifier.
        """
        with self._lock:
            self._states[provider] = ProviderHealthState.HEALTHY.value
            self._error_counts[provider] = 0
            self._backoff_until.pop(provider, None)

    def record_http_status(self, provider: str, status: int) -> None:
        """Record an HTTP status and drive the state machine accordingly.

        Args:
            provider (str): Canonical provider identifier.
            status (int): The HTTP status code observed (200/401/402/429/5xx).
        """
        if status == 200:
            self.record_success(provider)
        elif status == 429:
            self._set_backoff(provider, ProviderHealthState.RATE_LIMITED.value)
        elif status == 402:
            with self._lock:
                self._states[provider] = ProviderHealthState.LATCHED.value
        elif status == 401:
            with self._lock:
                self._states[provider] = ProviderHealthState.UNAUTHORIZED.value
        elif status >= 500:
            self._set_backoff(provider, ProviderHealthState.UNREACHABLE.value)
        # -- 3xx / other 4xx are treated as soft failures (no state change). --

    def record_timeout(self, provider: str) -> None:
        """Record a network timeout, transitioning the provider to UNREACHABLE.

        Args:
            provider (str): Canonical provider identifier.
        """
        self._set_backoff(provider, ProviderHealthState.UNREACHABLE.value)

    def record_unreachable(self, provider: str) -> None:
        """Record a 5xx/transport fault, transitioning to UNREACHABLE.

        Alias of record_timeout for readability at call sites.

        Args:
            provider (str): Canonical provider identifier.
        """
        self.record_timeout(provider)

    def force_probe(self, provider: str) -> None:
        """Reset a provider to HALF_OPEN to permit an explicit probe attempt.

        Used by the probe engine to bypass a LATCHED/backoff state and verify
        whether a provider has recovered.

        Args:
            provider (str): Canonical provider identifier.
        """
        with self._lock:
            self._states[provider] = ProviderHealthState.HALF_OPEN.value
            self._backoff_until.pop(provider, None)

    # ------------------------------------------------------------------
    # -- Internal helpers ----------------------------------------------
    # ------------------------------------------------------------------

    def _set_backoff(self, provider: str, state: str) -> None:
        """Apply an exponentially increasing backoff window to a provider.

        The window follows ``T_backoff = min(T0 * 2^k, Tmax)`` where ``k`` is
        the number of prior consecutive errors.

        Args:
            provider (str): Canonical provider identifier.
            state (str): The target ProviderHealthState value.
        """
        with self._lock:
            errors = self._error_counts.get(provider, 0)
            backoff = min(
                self.initial_backoff_seconds * (2 ** errors),
                self.max_backoff_seconds,
            )
            self._error_counts[provider] = errors + 1
            self._backoff_until[provider] = time.monotonic() + backoff
            self._states[provider] = state


class ApiHealthProbeEngine:
    """Concurrent lightweight health probe over all sixteen providers.

    The engine pings every registered provider descriptor using either an
    injected probe callable (for hermetic testing) or a default reachability
    probe (TCP connect for cloud, socket connect for local Ollama). Each probe
    result is folded into the shared SelfHealingCircuitBreaker and aggregated
    into a MeshDiagnosticReport.

    Attributes:
        registry (ProviderRegistry): The provider catalogue.
        breaker (SelfHealingCircuitBreaker): The shared state machine.
        timeout (float): Per-probe timeout in seconds.
        max_workers (int): Thread-pool width for concurrent probing.
        probe_fn (Optional[Callable]): Injected probe returning
            ``(http_status_or_None, latency_ms)``.
    """

    def __init__(
        self,
        registry: Optional[ProviderRegistry] = None,
        breaker: Optional[SelfHealingCircuitBreaker] = None,
        timeout: float = 2.0,
        max_workers: int = 16,
        probe_fn: Optional[
            Callable[[ProviderDescriptor], Tuple[Optional[int], float]]
        ] = None,
    ) -> None:
        self._registry = registry if registry is not None else get_provider_registry()
        self._breaker = breaker if breaker is not None else SelfHealingCircuitBreaker()
        self._timeout = timeout
        self._max_workers = max_workers
        self._probe_fn = probe_fn

    # ------------------------------------------------------------------
    # -- Public API ----------------------------------------------------
    # ------------------------------------------------------------------

    def probe_all(self) -> MeshDiagnosticReport:
        """Probe all registered providers and return a diagnostic report.

        Returns:
            MeshDiagnosticReport: Aggregate mesh health with per-provider rows.
        """
        descriptors = self._list_all()
        probes: List[ProviderHealthReport] = []
        if self._max_workers <= 1 or len(descriptors) <= 1:
            probes = [self._probe_one(d) for d in descriptors]
        else:
            with ThreadPoolExecutor(max_workers=self._max_workers) as pool:
                futures = {pool.submit(self._probe_one, d): d for d in descriptors}
                for future in as_completed(futures):
                    try:
                        probes.append(future.result())
                    except Exception:  # pragma: no cover - defensive
                        descriptor = futures[future]
                        probes.append(self._inert_report(descriptor))

        probes.sort(key=lambda p: p.provider)
        active = sum(1 for p in probes if p.is_active)
        healthy = sum(
            1 for p in probes if p.state == ProviderHealthState.HEALTHY.value
        )
        latched = sum(
            1 for p in probes if p.state == ProviderHealthState.LATCHED.value
        )
        free = sum(1 for p in probes if p.access_tier in _ZERO_CONFIG_FREE_TIERS)
        return MeshDiagnosticReport(
            generated_at=datetime.now(timezone.utc).isoformat(),
            total_providers=len(probes),
            active_providers=active,
            healthy=healthy,
            free=free,
            latched=latched,
            probes=probes,
        )

    # ------------------------------------------------------------------
    # -- Probe internals ------------------------------------------------
    # ------------------------------------------------------------------

    def _list_all(self) -> List[ProviderDescriptor]:
        """Return all registered descriptors, degrading to an empty list.

        Returns:
            list[ProviderDescriptor]: The registered provider descriptors.
        """
        try:
            return self._registry.list_all()
        except Exception:
            return []

    def _probe_one(self, descriptor: ProviderDescriptor) -> ProviderHealthReport:
        """Probe a single provider and fold the result into the breaker.

        Args:
            descriptor (ProviderDescriptor): The provider to probe.

        Returns:
            ProviderHealthReport: The per-provider probe result.
        """
        provider = descriptor.name
        tier = classify_access_tier(provider)

        if not descriptor.is_active and descriptor.api_key_env is not None:
            # -- Inactive cloud provider (no key): no network egress. --
            return self._build_report(descriptor, tier, None, 0.0)

        # -- Force a half-open probe so latched/backoff states are re-verified. --
        self._breaker.force_probe(provider)

        status, latency = self._run_probe(descriptor)
        if status is None:
            self._breaker.record_timeout(provider)
        else:
            self._breaker.record_http_status(provider, status)
        return self._build_report(descriptor, tier, status, latency)

    def _run_probe(self, descriptor: ProviderDescriptor) -> Tuple[Optional[int], float]:
        """Execute the injected or default probe for a descriptor.

        Args:
            descriptor (ProviderDescriptor): The provider to probe.

        Returns:
            tuple[Optional[int], float]: ``(http_status_or_None, latency_ms)``.
        """
        if self._probe_fn is not None:
            return self._probe_fn(descriptor)
        start = time.perf_counter()
        try:
            reachable = self._tcp_reachable(descriptor.base_url, self._timeout)
            latency = (time.perf_counter() - start) * 1000.0
            return (200 if reachable else None), latency
        except Exception:
            latency = (time.perf_counter() - start) * 1000.0
            return None, latency

    def _build_report(
        self,
        descriptor: ProviderDescriptor,
        tier: str,
        status: Optional[int],
        latency: float,
    ) -> ProviderHealthReport:
        """Assemble a ProviderHealthReport from a probe outcome.

        Args:
            descriptor (ProviderDescriptor): The provider descriptor.
            tier (str): The AccessTier value.
            status (Optional[int]): The observed HTTP status (None on timeout).
            latency (float): Probe latency in milliseconds.

        Returns:
            ProviderHealthReport: The per-provider report row.
        """
        provider = descriptor.name
        return ProviderHealthReport(
            provider=provider,
            state=self._breaker.state(provider),
            latency_ms=round(latency, 2),
            http_status=status,
            access_tier=tier,
            error_count=self._breaker.error_count(provider),
            backoff_until=self._breaker.backoff_until(provider),
            is_active=descriptor.is_active,
        )

    @staticmethod
    def _inert_report(descriptor: ProviderDescriptor) -> ProviderHealthReport:
        """Build a neutral report for a provider whose probe raised.

        Args:
            descriptor (ProviderDescriptor): The provider descriptor.

        Returns:
            ProviderHealthReport: A HEALTHY, inactive report row.
        """
        return ProviderHealthReport(
            provider=descriptor.name,
            state=ProviderHealthState.HEALTHY.value,
            access_tier=classify_access_tier(descriptor.name),
            is_active=descriptor.is_active,
        )

    @staticmethod
    def _tcp_reachable(base_url: str, timeout: float) -> bool:
        """Determine TCP reachability of a host:port extracted from a URL.

        Args:
            base_url (str): A URL of the form ``http://host:port[/path]``.
            timeout (float): Socket connect timeout in seconds.

        Returns:
            bool: True when the TCP handshake succeeds.
        """
        try:
            host = "127.0.0.1"
            port = 11434
            stripped = (base_url or "").split("://", 1)[-1]
            netloc = stripped.split("/", 1)[0]
            if ":" in netloc:
                host, port_s = netloc.rsplit(":", 1)
                if port_s.isdigit():
                    port = int(port_s)
            with socket.create_connection((host, port), timeout=timeout):
                return True
        except Exception:
            return False
        return False


__all__ = [
    "SelfHealingCircuitBreaker",
    "ApiHealthProbeEngine",
    "classify_access_tier",
    "classify_model_access_tier",
    "DEFAULT_BACKOFF_SECONDS",
    "MAX_BACKOFF_SECONDS",
]
