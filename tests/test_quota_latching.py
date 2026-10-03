# -*- coding: utf-8 -*-
"""
Module: test_quota_latching.py
Project: TALOS v5.19.0
Description:
    Hermetic unit tests for the Cloud Provider Quota Latching mechanism in
    AIManager (src/core/ai_manager.py). Verifies that an HTTP 402/401 signal
    latches a provider offline and that subsequent fallback routing skips the
    latched provider with zero network attempts, dispatching directly to the
    next active provider (e.g. DeepSeek). No live network or SDK is required.

Dependencies:
    - pytest: Test framework.
    - unittest.mock: Patching provider execution methods.
"""
import pytest

from src.core.ai_manager import AIManager


def _make_manager():
    """Build a bare AIManager (skipping __init__) with minimal provider state."""
    mgr = AIManager.__new__(AIManager)
    mgr.exhausted_providers = set()
    mgr._quota_notice_emitted = set()
    mgr.providers = {
        "gemini": {"circuit_open": False, "consecutive_failures": 0},
        "deepseek": {"circuit_open": False, "consecutive_failures": 0},
    }
    mgr.FAILURE_THRESHOLD = 5
    mgr.last_provider_used = None
    return mgr


class TestQuotaSignalDetection:
    """Tests for the 402/401 exhaustion signal classifier."""

    def test_402_resource_exhausted(self):
        assert AIManager._is_quota_or_auth_exhausted(
            "Error code: 402 - RESOURCE_EXHAUSTED") is True

    def test_402_prepayment_credits_depleted(self):
        assert AIManager._is_quota_or_auth_exhausted(
            "402 prepayment credits depleted") is True

    def test_401_unauthorized(self):
        assert AIManager._is_quota_or_auth_exhausted(
            "401 Unauthorized - invalid API key") is True

    def test_rate_limit_429_is_not_quota_latch(self):
        assert AIManager._is_quota_or_auth_exhausted(
            "429 Too Many Requests") is False

    def test_quota_reason_codes(self):
        assert AIManager._quota_reason("401 Unauthorized") == "401"
        assert AIManager._quota_reason("402 RESOURCE_EXHAUSTED") == "402"
        assert AIManager._quota_reason("prepayment credits depleted") == "quota"


class TestQuotaLatching:
    """Tests for the session-level latch and zero-attempt skip behavior."""

    def test_latch_adds_provider_and_opens_circuit(self):
        mgr = _make_manager()
        mgr._latch_provider_exhausted("gemini", reason="402")

        assert "gemini" in mgr.exhausted_providers
        assert mgr.providers["gemini"]["circuit_open"] is True
        assert mgr.providers["gemini"]["consecutive_failures"] == mgr.FAILURE_THRESHOLD
        assert "gemini" in mgr._quota_notice_emitted

    def test_latch_is_idempotent(self):
        mgr = _make_manager()
        mgr._latch_provider_exhausted("gemini", reason="402")
        mgr._latch_provider_exhausted("gemini", reason="402")

        assert len(mgr._quota_notice_emitted) == 1
        assert mgr.exhausted_providers == {"gemini"}

    def test_402_routes_next_call_directly_to_deepseek(self, monkeypatch):
        """A latched Gemini is bypassed with zero attempts; DeepSeek serves."""
        mgr = _make_manager()
        mgr._latch_provider_exhausted("gemini", reason="402")

        monkeypatch.setattr(
            mgr, "_get_router_ordered_providers",
            lambda prompt, task: ["gemini", "deepseek"])
        monkeypatch.setattr(mgr, "_task_type", lambda model_type: "default")

        gemini_calls = {"count": 0}

        def fake_gemini(prompt, model_type, response_format):
            gemini_calls["count"] += 1
            return {"provider": "gemini"}

        def fake_deepseek(provider_name, prompt, model_type, response_format):
            return {"provider": "deepseek", "ok": True}

        monkeypatch.setattr(mgr, "_execute_gemini_request", fake_gemini)
        monkeypatch.setattr(mgr, "_execute_openai_compatible_request", fake_deepseek)

        result = mgr._execute_cloud_chain("prompt", "pro", "json")

        assert result == {"provider": "deepseek", "ok": True}
        assert gemini_calls["count"] == 0  # zero network attempts to Gemini
