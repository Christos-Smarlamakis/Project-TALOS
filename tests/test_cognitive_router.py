# -*- coding: utf-8 -*-
"""
Module: test_cognitive_router.py
Project: TALOS v5.20.0
Description:
    Hermetic unit tests for the decoupled CognitiveMetaRouter. Verifies dynamic
    dispatch under LOWEST_LATENCY, REASONING_RIGOR, LOWEST_COST, and
    LOCAL_AIRGAPPED; confirms HTTP 401/402/429 quota latching triggers same-tier
    failover; and proves the module imports and executes with zero SQLite WAL or
    PRISMA dependencies. No live endpoints are contacted.

Dependencies:
    - pytest: Test framework.
    - src.core.cognitive_router: The module under test.
"""

import os

import pytest

from src.core.cognitive_router import (
    CognitiveMetaRouter,
    RoutingStrategy,
    ProviderHttpError,
    RouterTaskRequest,
)


class _FakeDescriptor:
    """Minimal stand-in for ProviderDescriptor."""

    def __init__(self, name, default_model=""):
        self.name = name
        self.default_model = default_model or name


class _FakeRegistry:
    """Minimal stand-in for ProviderRegistry with a controlled active set."""

    def __init__(self, active_names):
        self._active = list(active_names)

    def list_active(self):
        return [_FakeDescriptor(n) for n in self._active]

    def get(self, name):
        return _FakeDescriptor(name) if name in self._active else None


def _ok_transport(provider, model, request):
    return {"content": "ok:%s" % provider, "prompt_tokens": 10, "completion_tokens": 5}


class TestStrategyDispatch:
    """Verify each strategy dispatches to its expected provider."""

    def test_lowest_latency_prefers_lowest_ema_ttft(self):
        router = CognitiveMetaRouter(
            registry=_FakeRegistry(["groq", "cerebras", "sambanova", "ollama"]),
            transport=_ok_transport,
        )
        router.record_result("groq", latency_ms=100.0)
        router.record_result("cerebras", latency_ms=50.0)
        resp = router.dispatch("fast_screening", RoutingStrategy.LOWEST_LATENCY, {})
        assert resp.provider == "cerebras"

    def test_reasoning_rigor_prefers_deepseek(self):
        router = CognitiveMetaRouter(
            registry=_FakeRegistry(["deepseek", "anthropic", "sambanova"]),
            transport=_ok_transport,
        )
        resp = router.dispatch("kitchenham_audit", RoutingStrategy.REASONING_RIGOR, {})
        assert resp.provider == "deepseek"

    def test_lowest_cost_prefers_free_local_when_active(self):
        router = CognitiveMetaRouter(
            registry=_FakeRegistry(["deepseek", "mistral", "groq", "ollama"]),
            transport=_ok_transport,
        )
        resp = router.dispatch("fast_screening", RoutingStrategy.LOWEST_COST, {})
        assert resp.provider == "ollama"

    def test_lowest_cost_prefers_cheapest_cloud_when_local_inactive(self):
        router = CognitiveMetaRouter(
            registry=_FakeRegistry(["deepseek", "mistral", "groq"]),
            transport=_ok_transport,
        )
        resp = router.dispatch("fast_screening", RoutingStrategy.LOWEST_COST, {})
        assert resp.provider == "mistral"

    def test_local_airgapped_strictly_selects_ollama(self):
        router = CognitiveMetaRouter(
            registry=_FakeRegistry(["ollama", "groq", "deepseek"]),
            transport=_ok_transport,
        )
        resp = router.dispatch("fast_screening", RoutingStrategy.LOCAL_AIRGAPPED, {})
        assert resp.provider == "ollama"

    def test_dispatch_accepts_dto_form(self):
        router = CognitiveMetaRouter(
            registry=_FakeRegistry(["deepseek"]), transport=_ok_transport
        )
        request = RouterTaskRequest(
            task_type="kitchenham_audit", strategy=RoutingStrategy.REASONING_RIGOR
        )
        resp = router.dispatch(request)
        assert resp.provider == "deepseek"


class TestCircuitBreaker:
    """Verify 401/402/429 latching and same-tier failover."""

    @pytest.mark.parametrize("status", [401, 402, 429])
    def test_quota_latch_triggers_failover(self, status):
        calls = {"groq": 0, "cerebras": 0}

        def transport(provider, model, request):
            calls[provider] += 1
            if provider == "groq":
                raise ProviderHttpError("groq", status)
            return {"content": "ok", "prompt_tokens": 1, "completion_tokens": 1}

        router = CognitiveMetaRouter(
            registry=_FakeRegistry(["groq", "cerebras"]), transport=transport
        )
        resp = router.dispatch("fast_screening", RoutingStrategy.LOWEST_LATENCY, {})
        assert resp.provider == "cerebras"
        assert resp.fallback_occurred is True
        assert "groq" in resp.latched_providers
        assert router.get_metrics()["groq"]["latched"] is True
        assert calls["groq"] == 1
        assert calls["cerebras"] == 1

    def test_latched_provider_skipped_on_next_dispatch(self):
        router = CognitiveMetaRouter(
            registry=_FakeRegistry(["groq", "cerebras"]),
            transport=_ok_transport,
        )
        router.latch_provider("groq", 429)
        resp = router.dispatch("fast_screening", RoutingStrategy.LOWEST_LATENCY, {})
        assert resp.provider == "cerebras"
        assert "groq" in resp.latched_providers


class TestDecoupling:
    """Verify the router carries no SQLite WAL or PRISMA dependency."""

    def test_source_has_no_storage_or_prisma_imports(self):
        path = os.path.join(
            os.path.dirname(__file__), "..", "src", "core", "cognitive_router.py"
        )
        with open(path, "r", encoding="utf-8") as fh:
            source = fh.read()
        assert "database_manager" not in source
        assert "src.prisma" not in source

    def test_executes_without_storage_or_prisma(self):
        router = CognitiveMetaRouter(
            registry=_FakeRegistry(["groq", "cerebras"]), transport=_ok_transport
        )
        resp = router.dispatch("fast_screening", RoutingStrategy.LOWEST_LATENCY, {})
        assert resp.provider in ("groq", "cerebras")
