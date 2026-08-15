# -*- coding: utf-8 -*-
"""
Module: test_llm_router_subagent.py
Project: TALOS v5.10.4
Description:
    Hermetic unit tests for the LLMRouterSubAgent provider-selection delegate.
    Covers weight loading with Pareto fallback, signal estimation bounds,
    active-provider constraints, quality-driven selection, and determinism.

    Key design decisions:
    - Tests pass an explicit missing weights path so they never depend on a
      real ``models/gwo_llm_router_reward_weights.json`` artifact on disk.
    - All assertions are numeric or membership checks against the static
      ``PROVIDER_PROFILES`` table; no network or LLM calls are performed.

Dependencies:
    - pytest: Test framework for fixtures and approximate assertions.
    - json, os: Temporary weight artifact construction.
"""
import json
import os

import pytest

from src.ai.drl.llm_router_subagent import (
    LLMRouterSubAgent,
    WEIGHT_LABELS,
    DEFAULT_WEIGHTS,
    DEFAULT_PROFILE,
    PROVIDER_PROFILES,
    TASK_MODIFIERS,
    MAX_SWE_BENCH_SCORE,
    estimate_prompt_tokens,
    relative_quality,
)


class TestWeightLoading:
    """Tests for weight loading and normalization."""

    def test_load_weights_falls_back_to_default(self):
        """Verify a missing weights file falls back to the default profile."""
        agent = LLMRouterSubAgent(weights_path="__missing_weights__.json")
        assert agent.weights == pytest.approx(DEFAULT_WEIGHTS[DEFAULT_PROFILE])

    def test_load_weights_reads_json(self, tmp_path):
        """Verify optimized weights are read from a JSON artifact."""
        path = tmp_path / "weights.json"
        payload = {
            "best_weights": {
                "w_quality": 0.5, "w_latency": 0.2,
                "w_cost": 0.2, "w_penalty": 0.1,
            }
        }
        path.write_text(json.dumps(payload), encoding="utf-8")
        agent = LLMRouterSubAgent(weights_path=str(path))
        assert agent.weights["w_quality"] == pytest.approx(0.5)

    def test_normalize_sums_to_one(self):
        """Verify normalization projects onto the simplex."""
        normalized = LLMRouterSubAgent._normalize(
            {"w_quality": 3, "w_latency": 1, "w_cost": 1, "w_penalty": 1}
        )
        assert sum(normalized.values()) == pytest.approx(1.0, abs=1e-9)
        assert all(v >= 0.0 for v in normalized.values())


class TestSelectProvider:
    """Tests for provider selection."""

    def test_select_provider_returns_valid_provider(self):
        """Verify selection returns a known canonical provider."""
        agent = LLMRouterSubAgent(weights_path="__missing_weights__.json")
        provider = agent.select_provider(512, "fast_screening")
        assert provider in PROVIDER_PROFILES

    def test_select_provider_respects_active_providers(self):
        """Verify selection is constrained to the active provider list."""
        agent = LLMRouterSubAgent(weights_path="__missing_weights__.json")
        provider = agent.select_provider(
            512, "default", active_providers=["groq", "cerebras"]
        )
        assert provider in ("groq", "cerebras")

    def test_quality_weighting_prefers_quality_provider(self):
        """Verify a quality-only weight vector selects the top-benchmark provider."""
        agent = LLMRouterSubAgent(weights_path="__missing_weights__.json")
        agent.set_weights(
            {"w_quality": 1.0, "w_latency": 0.0, "w_cost": 0.0, "w_penalty": 0.0}
        )
        provider = agent.select_provider(512, "default")
        top = max(PROVIDER_PROFILES,
                  key=lambda p: PROVIDER_PROFILES[p]["swe_bench_score"])
        assert provider == top

    def test_select_provider_is_deterministic(self):
        """Verify identical inputs yield identical provider selections."""
        agent = LLMRouterSubAgent(weights_path="__missing_weights__.json")
        first = agent.select_provider(1024, "deep_research")
        second = agent.select_provider(1024, "deep_research")
        assert first == second


class TestSignals:
    """Tests for per-provider signal estimation."""

    def test_estimate_signals_returns_all_providers_in_bounds(self):
        """Verify signals cover all providers and stay within [0, 1]."""
        agent = LLMRouterSubAgent(weights_path="__missing_weights__.json")
        signals = agent.estimate_signals(512, "default")
        assert set(signals) == set(PROVIDER_PROFILES)
        for quality, latency, cost, penalty in signals.values():
            assert 0.0 <= quality <= 1.0
            assert 0.0 <= latency <= 1.0
            assert 0.0 <= cost <= 1.0
            assert 0.0 <= penalty <= 1.0


class TestForagingEvaluationTask:
    """Tests for the v5.10.3 foraging_evaluation routing task type."""

    def test_foraging_evaluation_task_modifier_exists(self):
        """Verify the foraging_evaluation task modifier is registered."""
        assert "foraging_evaluation" in TASK_MODIFIERS

    def test_select_provider_foraging_evaluation_returns_valid_provider(self):
        """Verify foraging_evaluation routing yields a canonical provider."""
        agent = LLMRouterSubAgent(weights_path="__missing_weights__.json")
        provider = agent.select_provider(1024, "foraging_evaluation")
        assert provider in PROVIDER_PROFILES


class TestEstimatePromptTokens:
    """Tests for the shared prompt-length estimator."""

    def test_empty_text_returns_one(self):
        """Verify empty input returns the minimum token count."""
        assert estimate_prompt_tokens("") == 1

    def test_returns_char_quarters(self):
        """Verify the four-characters-per-token heuristic."""
        assert estimate_prompt_tokens("a" * 400) == 100


class TestDynamicQualityNormalization:
    """Tests for dynamic relative min-max quality normalization."""

    def test_top_provider_quality_is_exactly_one(self):
        """Verify the provider with the top SWE-bench score receives Q=1.0."""
        agent = LLMRouterSubAgent(weights_path="__missing_weights__.json")
        top = max(PROVIDER_PROFILES,
                  key=lambda p: PROVIDER_PROFILES[p]["swe_bench_score"])
        quality, _, _, _ = agent.estimate_signals(0, "default")[top]
        assert quality == pytest.approx(1.0, abs=1e-9)

    def test_quality_equals_raw_over_max(self):
        """Verify every quality signal equals raw_score / max_score."""
        agent = LLMRouterSubAgent(weights_path="__missing_weights__.json")
        signals = agent.estimate_signals(0, "default")
        for name, profile in PROVIDER_PROFILES.items():
            expected = profile["swe_bench_score"] / MAX_SWE_BENCH_SCORE
            quality, _, _, _ = signals[name]
            assert quality == pytest.approx(expected, abs=1e-9)

    def test_relative_quality_formula(self):
        """Verify relative_quality() implements Q_p = raw / max."""
        assert relative_quality(MAX_SWE_BENCH_SCORE) == pytest.approx(1.0, abs=1e-9)
        assert relative_quality(MAX_SWE_BENCH_SCORE / 2.0) == pytest.approx(0.5, abs=1e-9)
        assert relative_quality(0.0) == pytest.approx(0.0, abs=1e-9)

    def test_all_quality_signals_within_unit_interval(self):
        """Verify all derived quality signals stay within [0, 1]."""
        agent = LLMRouterSubAgent(weights_path="__missing_weights__.json")
        signals = agent.estimate_signals(512, "default")
        for quality, _, _, _ in signals.values():
            assert 0.0 <= quality <= 1.0
