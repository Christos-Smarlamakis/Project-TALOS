# -*- coding: utf-8 -*-
"""
Module: test_ai_strategy_candidates.py
Project: TALOS v5.25.3
Description:
    Hermetic unit tests for the interactive model candidate selector in
    src/utils/ai_strategy_selector.py (v5.25.3). Verifies the pure candidate
    discovery, VRAM estimation, rigor banding, and strategy-key mapping helpers
    that power the four step-by-step role-slot child menus in Option 10.

Dependencies:
    - pytest: test framework.
    - src.utils.ai_strategy_selector: the module under test.
"""

import pytest

from src.utils.ai_strategy_selector import (
    _get_candidates_for_slot,
    _strategy_key,
    _estimate_vram,
    _rigor_band,
)


class TestStrategyKey:
    """Strategy label to canonical ai_execution_strategy key mapping."""

    def test_local_first(self):
        assert _strategy_key("LOCAL_FIRST") == "local_first"

    def test_strict_local(self):
        assert _strategy_key("STRICT_LOCAL") == "strict_local"

    def test_cloud_budget(self):
        assert _strategy_key("CLOUD_BUDGET") == "cloud_first"

    def test_frontier(self):
        assert _strategy_key("FRONTIER") == "cloud_first"

    def test_unknown_falls_back_to_local_first(self):
        assert _strategy_key("UNKNOWN") == "local_first"


class TestVramEstimation:
    """VRAM estimation distinguishes local from cloud models."""

    def test_cloud_returns_none(self):
        assert _estimate_vram("claude-sonnet-4-5", "anthropic") is None

    def test_known_local_lookup(self):
        assert _estimate_vram("qwen2.5:14b", "ollama") == 9.0

    def test_heuristic_from_parameter_suffix(self):
        assert _estimate_vram("qwen3:30b", "ollama") == pytest.approx(19.5, abs=0.1)


class TestRigorBand:
    """Rigor banding from benchmark scores."""

    def test_frontier(self):
        assert _rigor_band(88.0, None) == "Frontier"

    def test_high(self):
        assert _rigor_band(78.0, None) == "High"

    def test_medium(self):
        assert _rigor_band(66.0, None) == "Medium"

    def test_low(self):
        assert _rigor_band(55.0, None) == "Low"

    def test_none(self):
        assert _rigor_band(None, None) == "-"


class TestCandidatesForSlot:
    """Candidate discovery across the four role slots."""

    REQUIRED_KEYS = {"name", "provider", "vram_gb", "cost_per_1k_usd", "ttft_ms", "rigor"}

    @pytest.mark.parametrize("slot", [
        "screening_local",
        "screening_cloud",
        "reasoning_local",
        "reasoning_cloud",
    ])
    def test_returns_list_of_enriched_dicts(self, slot):
        candidates = _get_candidates_for_slot(slot, "LOCAL_FIRST")
        assert isinstance(candidates, list)
        for c in candidates:
            assert self.REQUIRED_KEYS.issubset(c.keys())

    def test_local_slots_only_ollama(self):
        for slot in ("screening_local", "reasoning_local"):
            candidates = _get_candidates_for_slot(slot, "LOCAL_FIRST")
            for c in candidates:
                assert c["provider"] == "ollama"

    def test_cloud_slots_exclude_ollama(self):
        for slot in ("screening_cloud", "reasoning_cloud"):
            candidates = _get_candidates_for_slot(slot, "LOCAL_FIRST")
            for c in candidates:
                assert c["provider"] != "ollama"
