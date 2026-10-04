# -*- coding: utf-8 -*-
"""
Module: rate_limiter.py
Project: TALOS v5.24.0
Description:
    Proactive token-bucket rate limiter for the Cognitive Mesh microservice.
    Before any outbound inference request is dispatched to a cloud provider,
    the caller acquires a token through ``TokenBucketRateLimiter.acquire()``.
    Each provider is modelled as a classic token bucket with a refill rate
    ``r = RPM / 60`` (tokens per second) and a burst capacity ``B``. The
    limiter computes the exact smooth micro-sleep delay required to restore
    enough tokens, sleeping before dispatch so that HTTP 429 responses are
    eliminated proactively rather than reactively latched.

    Key design decisions:
    - Bucket state is per canonical provider name and guarded by a single
      ``threading.Lock``, so concurrent dispatches serialize safely with zero
      external queue dependency (Constitution II, air-gapped).
    - The sleep function and monotonic clock are injectable so the limiter is
      fully unit-testable without wall-clock waits or real network I/O.
    - Local Ollama carries an infinite rate spec (``r = inf``) and never
      sleeps; cloud providers use their documented RPM ceilings.
    - Imports only the Python standard library: zero references to SQLite WAL
      storage, PRISMA pipelines, or CLI scripts (Constitution III).

Dependencies:
    - threading: per-bucket state serialization under a single lock.
    - time: monotonic clock and default sleep implementation.
    - typing: type annotations for callable injection.
"""

import threading
import time
from typing import Callable, Dict, Optional

# -- Canonical per-provider rate ceilings (requests per minute) -----------------
# r = RPM / 60 tokens per second. Local Ollama is unbounded (air-gapped).
_PROVIDER_RPM: Dict[str, float] = {
    "groq": 30.0,
    "cerebras": 60.0,
    "gemini": 15.0,
    "sambanova": 20.0,
    "deepseek": 60.0,
    "openrouter": 20.0,
    "ollama": float("inf"),
}

# -- Fallback ceiling for any provider absent from the table above. ------------
_DEFAULT_RPM = 20.0


def get_rate_specs() -> Dict[str, float]:
    """Return the canonical provider rate ceilings as a read-only copy.

    Returns:
        dict: Provider name to requests-per-minute ceiling.
    """
    return dict(_PROVIDER_RPM)


class TokenBucketRateLimiter:
    """Proactive smooth micro-throttling token bucket for LLM providers.

    Each provider owns an independent bucket of capacity ``B = max(1.0, r)``
    where ``r = RPM / 60`` is the refill rate in tokens per second. The token
    count evolves as ``T(t) = min(B, T(t_last) + (t - t_last) * r)``. When a
    caller requests more tokens than are available, ``acquire`` computes the
    exact delay ``dt = deficit / r`` required to refill the shortfall and
    sleeps for that interval before returning.

    Attributes:
        sleep_fn (Callable[[float], None]): Injectable sleep callable.
        clock (Callable[[], float]): Injectable monotonic clock callable.
    """

    def __init__(
        self,
        sleep_fn: Optional[Callable[[float], None]] = None,
        clock: Optional[Callable[[], float]] = None,
    ) -> None:
        self._sleep_fn: Callable[[float], None] = sleep_fn or time.sleep
        self._clock: Callable[[], float] = clock or time.monotonic
        self._lock = threading.Lock()
        self._buckets: Dict[str, Dict[str, float]] = {}

    # ------------------------------------------------------------------
    # -- Public API ----------------------------------------------------
    # ------------------------------------------------------------------

    def acquire(self, provider_name: str, tokens: int = 1) -> float:
        """Acquire ``tokens`` for a provider, sleeping if the bucket is short.

        Args:
            provider_name (str): Canonical provider identifier.
            tokens (int): Number of tokens to consume (default one request).

        Returns:
            float: The micro-sleep delay in seconds actually applied (0.0 when
                no throttle was required).
        """
        key = self._normalize(provider_name)
        rpm = self._rpm(key)
        r = self._refill_rate(rpm)

        with self._lock:
            now = self._clock()
            bucket = self._ensure_bucket(key, r, now)

            if self._is_unbounded(r):
                # -- Infinite local rate: never throttle. --
                return 0.0

            self._refill(bucket, r, now)
            if bucket["tokens"] >= tokens:
                bucket["tokens"] -= tokens
                return 0.0

            # -- Exhausted: compute the exact smooth refill delay. --
            deficit = tokens - bucket["tokens"]
            bucket["tokens"] = 0.0
            delay = deficit / r

        if delay > 0.0:
            self._sleep_fn(delay)
        return delay

    def get_provider_status(self) -> Dict[str, Dict[str, float]]:
        """Return remaining tokens and fill percentage for every provider.

        Returns:
            dict: Provider name to ``{"remaining", "fill_pct", "rpm"}``.
        """
        snapshot: Dict[str, Dict[str, float]] = {}
        with self._lock:
            now = self._clock()
            for key, bucket in self._buckets.items():
                rpm = self._rpm(key)
                r = self._refill_rate(rpm)
                self._refill(bucket, r, now)
                remaining = bucket["tokens"]
                if self._is_unbounded(r):
                    fill = 100.0
                else:
                    fill = min(100.0, 100.0 * remaining / self._capacity(r))
                snapshot[key] = {
                    "remaining": remaining,
                    "fill_pct": round(fill, 2),
                    "rpm": rpm,
                }
        return snapshot

    # ------------------------------------------------------------------
    # -- Bucket mathematics --------------------------------------------
    # ------------------------------------------------------------------

    @staticmethod
    def _normalize(provider_name: str) -> str:
        return (provider_name or "").strip().lower()

    @staticmethod
    def _rpm(key: str) -> float:
        return _PROVIDER_RPM.get(key, _DEFAULT_RPM)

    @staticmethod
    def _refill_rate(rpm: float) -> float:
        return float("inf") if rpm == float("inf") else rpm / 60.0

    @staticmethod
    def _capacity(r: float) -> float:
        return float("inf") if r == float("inf") else max(1.0, r)

    @staticmethod
    def _is_unbounded(r: float) -> bool:
        return r == float("inf")

    def _ensure_bucket(self, key: str, r: float, now: float) -> Dict[str, float]:
        bucket = self._buckets.get(key)
        if bucket is None:
            bucket = {"tokens": self._capacity(r), "last": now}
            self._buckets[key] = bucket
        return bucket

    def _refill(self, bucket: Dict[str, float], r: float, now: float) -> None:
        """Advance the bucket to the current time using the refill rate."""
        if self._is_unbounded(r):
            bucket["tokens"] = float("inf")
            bucket["last"] = now
            return
        elapsed = max(0.0, now - bucket["last"])
        bucket["tokens"] = min(self._capacity(r), bucket["tokens"] + elapsed * r)
        bucket["last"] = now
