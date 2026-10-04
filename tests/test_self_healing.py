# -*- coding: utf-8 -*-
"""
Module: test_self_healing.py
Project: TALOS v5.23.0
Description:
    Hermetic unit tests for the Cognitive Mesh self-healing subsystem
    (src/services/cognitive_mesh/self_healing.py) introduced in v5.23.0. The
    suite verifies the six-state SelfHealingCircuitBreaker state machine, the
    exponential backoff timing window (T_backoff = min(T0 * 2^k, Tmax)), the
    session-scoped quota latching, the ApiHealthProbeEngine probe/timeout
    handling and diagnostic report generation, and the four-tier AccessTier
    classifier.

    Key design decisions:
    - All tests are hermetic: no live network, SQLite, or cloud endpoint is
      exercised. Probes are injected via the probe_fn callable.
    - Backoff-timing tests use a tiny initial backoff so they complete in
      milliseconds without waiting for the production 60-second default.

Dependencies:
    - pytest: test framework.
    - time: monotonic clock for backoff assertions.
    - src.services.cognitive_mesh.dto: AccessTier / ProviderHealthState.
    - src.services.cognitive_mesh.registry: ProviderDescriptor dataclass.
    - src.services.cognitive_mesh.self_healing: breaker, probe engine, and
      access-tier classifier under test.
"""

import time

import pytest

from src.services.cognitive_mesh.dto import AccessTier, ProviderHealthState
from src.services.cognitive_mesh.registry import ProviderDescriptor
from src.services.cognitive_mesh.self_healing import (
    ApiHealthProbeEngine,
    SelfHealingCircuitBreaker,
    classify_access_tier,
    classify_model_access_tier,
)


class _FakeRegistry:
    """Minimal registry stand-in exposing only the list_all() surface."""

    def __init__(self, descriptors):
        self._descriptors = descriptors

    def list_all(self):
        return list(self._descriptors)


def _descriptor(name, is_active=True, api_key_env=None,
                base_url="http://127.0.0.1:11434"):
    return ProviderDescriptor(
        name=name,
        base_url=base_url,
        api_key_env=api_key_env,
        default_model="",
        is_openai_compatible=True,
        is_active=is_active,
    )


# ------------------------------------------------------------------
# -- SelfHealingCircuitBreaker --------------------------------------
# ------------------------------------------------------------------

class TestSelfHealingCircuitBreaker:
    """Unit tests for the six-state circuit breaker state machine."""

    def test_healthy_by_default(self):
        breaker = SelfHealingCircuitBreaker()
        assert breaker.state("unknown") == ProviderHealthState.HEALTHY.value
        assert breaker.should_attempt("unknown") is True

    def test_http_200_records_success(self):
        breaker = SelfHealingCircuitBreaker()
        breaker.record_http_status("groq", 429)
        assert breaker.state("groq") == ProviderHealthState.RATE_LIMITED.value
        breaker.record_http_status("groq", 200)
        assert breaker.state("groq") == ProviderHealthState.HEALTHY.value
        assert breaker.error_count("groq") == 0

    def test_http_429_rate_limited_and_backoff_blocks(self):
        breaker = SelfHealingCircuitBreaker()
        breaker.record_http_status("groq", 429)
        assert breaker.state("groq") == ProviderHealthState.RATE_LIMITED.value
        assert breaker.should_attempt("groq") is False

    def test_http_402_latches_for_session(self):
        breaker = SelfHealingCircuitBreaker()
        breaker.record_http_status("anthropic", 402)
        assert breaker.state("anthropic") == ProviderHealthState.LATCHED.value
        assert breaker.should_attempt("anthropic") is False

    def test_http_401_unauthorized(self):
        breaker = SelfHealingCircuitBreaker()
        breaker.record_http_status("deepseek", 401)
        assert breaker.state("deepseek") == ProviderHealthState.UNAUTHORIZED.value
        assert breaker.should_attempt("deepseek") is False

    def test_timeout_unreachable(self):
        breaker = SelfHealingCircuitBreaker()
        breaker.record_timeout("nvidia")
        assert breaker.state("nvidia") == ProviderHealthState.UNREACHABLE.value
        assert breaker.should_attempt("nvidia") is False

    def test_half_open_after_backoff_expiry(self):
        breaker = SelfHealingCircuitBreaker(
            initial_backoff_seconds=0.05, max_backoff_seconds=0.5
        )
        breaker.record_timeout("nvidia")
        assert breaker.should_attempt("nvidia") is False
        time.sleep(0.08)
        assert breaker.should_attempt("nvidia") is True
        assert breaker.state("nvidia") == ProviderHealthState.HALF_OPEN.value
        breaker.record_success("nvidia")
        assert breaker.state("nvidia") == ProviderHealthState.HEALTHY.value

    def test_exponential_backoff_doubles(self):
        breaker = SelfHealingCircuitBreaker(
            initial_backoff_seconds=1.0, max_backoff_seconds=600.0
        )
        breaker.record_timeout("x")
        until1 = breaker.backoff_until("x")
        breaker.record_timeout("x")
        until2 = breaker.backoff_until("x")
        breaker.record_timeout("x")
        until3 = breaker.backoff_until("x")
        assert until1 is not None and until2 is not None and until3 is not None
        assert until3 > until2 > until1
        assert breaker.error_count("x") == 3

    def test_backoff_caps_at_max(self):
        breaker = SelfHealingCircuitBreaker(
            initial_backoff_seconds=1.0, max_backoff_seconds=2.0
        )
        for _ in range(12):
            breaker.record_timeout("x")
        until = breaker.backoff_until("x")
        assert until is not None
        assert until - time.monotonic() <= 2.0 + 0.05

    def test_force_probe_unlocks_latched(self):
        breaker = SelfHealingCircuitBreaker()
        breaker.record_http_status("anthropic", 402)
        assert breaker.should_attempt("anthropic") is False
        breaker.force_probe("anthropic")
        assert breaker.state("anthropic") == ProviderHealthState.HALF_OPEN.value
        assert breaker.should_attempt("anthropic") is True


# ------------------------------------------------------------------
# -- AccessTier classifier ------------------------------------------
# ------------------------------------------------------------------

class TestAccessTierClassifier:
    """Unit tests for the four-tier AccessTier taxonomy."""

    def test_ollama_local_no_key(self):
        assert classify_access_tier("ollama") == AccessTier.LOCAL_NO_KEY.value

    def test_huggingface_zero_config_free(self):
        assert (
            classify_access_tier("huggingface")
            == AccessTier.CLOUD_ZERO_CONFIG_FREE.value
        )

    def test_groq_free_tier_with_key(self):
        assert (
            classify_access_tier("groq")
            == AccessTier.CLOUD_FREE_TIER_WITH_KEY.value
        )

    def test_anthropic_paid(self):
        assert classify_access_tier("anthropic") == AccessTier.CLOUD_PAID_API.value

    def test_unknown_defaults_paid(self):
        assert (
            classify_access_tier("mystery-provider")
            == AccessTier.CLOUD_PAID_API.value
        )

    def test_model_access_tier_by_source(self):
        assert classify_model_access_tier("ollama") == AccessTier.LOCAL_NO_KEY.value
        assert (
            classify_model_access_tier("huggingface")
            == AccessTier.CLOUD_ZERO_CONFIG_FREE.value
        )
        assert (
            classify_model_access_tier("openrouter")
            == AccessTier.CLOUD_FREE_TIER_WITH_KEY.value
        )
        assert (
            classify_model_access_tier("benchmarks", provider="anthropic")
            == AccessTier.CLOUD_PAID_API.value
        )


# ------------------------------------------------------------------
# -- ApiHealthProbeEngine -------------------------------------------
# ------------------------------------------------------------------

class TestApiHealthProbeEngine:
    """Unit tests for the concurrent API health probe engine."""

    def test_probe_healthy_200(self):
        registry = _FakeRegistry([_descriptor("ollama")])
        probe_fn = lambda d: (200, 12.5)
        engine = ApiHealthProbeEngine(registry=registry, probe_fn=probe_fn)
        report = engine.probe_all()
        assert report.total_providers == 1
        assert report.healthy == 1
        assert report.probes[0].state == ProviderHealthState.HEALTHY.value
        assert report.probes[0].http_status == 200
        assert report.probes[0].latency_ms == 12.5

    def test_probe_429_rate_limited(self):
        registry = _FakeRegistry([_descriptor("groq", api_key_env="GROQ_API_KEY")])
        probe_fn = lambda d: (429, 3.0)
        engine = ApiHealthProbeEngine(registry=registry, probe_fn=probe_fn)
        report = engine.probe_all()
        assert report.probes[0].state == ProviderHealthState.RATE_LIMITED.value
        assert report.healthy == 0
        assert report.latched == 0

    def test_probe_timeout_unreachable(self):
        registry = _FakeRegistry(
            [_descriptor("nvidia", api_key_env="NVIDIA_API_KEY")]
        )
        probe_fn = lambda d: (None, 0.0)
        engine = ApiHealthProbeEngine(registry=registry, probe_fn=probe_fn)
        report = engine.probe_all()
        assert report.probes[0].state == ProviderHealthState.UNREACHABLE.value
        assert report.probes[0].http_status is None

    def test_inactive_provider_no_network(self):
        registry = _FakeRegistry(
            [_descriptor("anthropic", is_active=False, api_key_env="ANTHROPIC_API_KEY")]
        )
        called = {"hit": False}

        def probe_fn(d):
            called["hit"] = True
            return (200, 1.0)

        engine = ApiHealthProbeEngine(registry=registry, probe_fn=probe_fn)
        report = engine.probe_all()
        assert called["hit"] is False
        assert report.probes[0].is_active is False
        assert report.active_providers == 0

    def test_diagnostic_report_aggregation(self):
        registry = _FakeRegistry(
            [
                _descriptor("ollama"),
                _descriptor("groq", api_key_env="GROQ_API_KEY"),
                _descriptor("anthropic", api_key_env="ANTHROPIC_API_KEY"),
            ]
        )
        statuses = {"ollama": 200, "groq": 402, "anthropic": 429}

        def probe_fn(d):
            return statuses[d.name], 5.0

        engine = ApiHealthProbeEngine(registry=registry, probe_fn=probe_fn)
        report = engine.probe_all()
        assert report.total_providers == 3
        assert report.active_providers == 3
        assert report.healthy == 1
        assert report.latched == 1
        assert report.free == 1  # ollama is LOCAL_NO_KEY


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
