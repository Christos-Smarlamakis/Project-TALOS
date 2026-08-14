# -*- coding: utf-8 -*-
"""
Module: test_gwo_llm_router_reward_shaper.py
Project: TALOS v5.10.2
Description:
    Hermetic unit tests for the GWOLLMRouterRewardShaper bi-level optimizer.
    Covers simplex projection, the GWO outer loop, deterministic seeding, and
    JSON export of optimized reward weights, convergence trajectory, and the
    three Pareto profile configurations.

    Key design decisions:
    - All tests use small wolf/iteration/episode budgets and a fixed seed so
      they remain fast and deterministic without external LLM dependencies.
    - Export tests patch the models directory to a pytest tmp_path so the
      project's real models/ directory is never written during CI.

Dependencies:
    - pytest: Test framework for fixture-based tests.
    - numpy: Numeric assertions on projected weight vectors.
"""
import json
import os

import numpy as np
import pytest

from src.ai.optimizers.gwo_llm_router_reward_shaper import (
    GWOLLMRouterRewardShaper,
    WEIGHT_LABELS,
    DIMENSIONS,
    PARETO_PROFILES,
)


class TestSimplexProjection:
    """Tests for the simplex projection constraint."""

    def test_project_simplex_sums_to_one(self):
        """Verify the projection always yields weights summing to 1."""
        vector = np.array([0.9, 0.2, 0.4, 0.1])
        projected = GWOLLMRouterRewardShaper._project_simplex(vector)
        assert projected.shape == (4,)
        assert float(np.sum(projected)) == pytest.approx(1.0, abs=1e-9)
        assert np.all(projected >= 0.0)

    def test_project_simplex_handles_non_positive(self):
        """Verify a non-positive vector projects to a uniform distribution."""
        vector = np.array([-0.5, -0.2, -0.1, -0.3])
        projected = GWOLLMRouterRewardShaper._project_simplex(vector)
        assert float(np.sum(projected)) == pytest.approx(1.0, abs=1e-9)
        assert np.allclose(projected, 0.25, atol=1e-9)


class TestOptimizer:
    """Tests for the bi-level GWO optimization."""

    def test_optimize_returns_valid_weights(self):
        """Verify optimized weights obey the simplex constraint."""
        shaper = GWOLLMRouterRewardShaper(wolves=4, iterations=3,
                                          eval_episodes=5, seed=42)
        result = shaper.optimize()
        best = result["best_weights"]
        assert best.shape == (DIMENSIONS,)
        assert float(np.sum(best)) == pytest.approx(1.0, abs=1e-6)
        assert np.all(best >= 0.0)
        assert isinstance(result["best_reward"], float)
        assert len(shaper.trajectory) >= 1

    def test_optimize_is_deterministic_with_seed(self):
        """Verify a fixed seed reproduces the same best reward."""
        result_a = GWOLLMRouterRewardShaper(
            wolves=3, iterations=3, eval_episodes=4, seed=7).optimize()
        result_b = GWOLLMRouterRewardShaper(
            wolves=3, iterations=3, eval_episodes=4, seed=7).optimize()
        assert result_a["best_reward"] == pytest.approx(result_b["best_reward"])

    def test_export_writes_required_keys(self, tmp_path, monkeypatch):
        """Verify export writes a complete JSON artifact to the models directory."""
        shaper = GWOLLMRouterRewardShaper(wolves=3, iterations=2,
                                          eval_episodes=3, seed=11)
        result = shaper.optimize()
        monkeypatch.setattr(
            GWOLLMRouterRewardShaper,
            "_models_dir",
            staticmethod(lambda: str(tmp_path)),
        )
        output_path = shaper.export(result)
        assert os.path.exists(output_path)

        with open(output_path, "r", encoding="utf-8") as handle:
            payload = json.load(handle)

        assert payload["optimizer"] == "GWOLLMRouterRewardShaper"
        assert set(payload["best_weights"]) == set(WEIGHT_LABELS)
        assert payload["sum_check"] == pytest.approx(1.0, abs=1e-5)
        assert "convergence_trajectory" in payload
        assert set(payload["pareto_profiles"]) == set(PARETO_PROFILES)


class TestParetoProfiles:
    """Tests for the reference Pareto profile configurations."""

    def test_profiles_have_four_weights(self):
        """Verify each Pareto profile defines four weights summing to 1."""
        for name, profile in PARETO_PROFILES.items():
            assert set(profile) == set(WEIGHT_LABELS)
            assert sum(profile[label] for label in WEIGHT_LABELS) == pytest.approx(1.0, abs=1e-9)
