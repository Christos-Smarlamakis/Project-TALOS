# -*- coding: utf-8 -*-
"""
Module: test_hierarchical_evaluator.py
Project: TALOS v5.19.0
Description:
    Hermetic unit tests for the centralized HierarchicalEvaluationEngine
    (src/core/hierarchical_evaluator.py). Verifies the two-tier escalation
    contract: fast rejection below the escalation threshold, heavy-tier
    escalation at or above it, and input-order preservation in the concurrent
    batch pool. No live LLM, Ollama, or network access is required; the
    underlying AIManager is mocked.

Dependencies:
    - pytest: Test framework.
    - unittest.mock: Mocking the AIManager.evaluate_paper_json call.
"""
import pytest
from unittest.mock import MagicMock

from src.core.hierarchical_evaluator import HierarchicalEvaluationEngine


class TestHierarchicalEvaluationEngine:
    """Tests for the two-tier escalation pipeline."""

    def _engine(self, ai_manager, threshold=6.0):
        return HierarchicalEvaluationEngine(ai_manager, escalation_threshold=threshold)

    def test_fast_rejection_below_threshold(self):
        """A paper scoring below the threshold is rejected in the fast tier."""
        ai_manager = MagicMock()
        ai_manager.evaluate_paper_json.return_value = {
            "overall_score": 4.0,
            "scores": {"strategic": 4, "operational": 4, "tactical": 4, "playground": 4},
        }
        engine = self._engine(ai_manager)

        verdict = engine.evaluate_paper({"title": "Paper A", "abstract": "Abstract"})

        assert verdict["is_accepted"] is False
        assert verdict["escalated"] is False
        assert verdict["tier"] == "fast_local"
        assert verdict["overall_score"] == 4.0
        assert verdict["quality_score"] is None
        assert verdict["evidence_quadrant"] == "METHODOLOGICAL_NOISE"
        # -- Only the fast tier was consulted; the heavy tier was skipped. --
        ai_manager.evaluate_paper_json.assert_called_once()

    def test_escalation_at_or_above_threshold(self):
        """A paper scoring >= threshold escalates to the heavy reasoning tier."""
        ai_manager = MagicMock()
        ai_manager.evaluate_paper_json.side_effect = [
            {"overall_score": 7.5,
             "scores": {"strategic": 8, "operational": 7, "tactical": 8, "playground": 7}},
            {"overall_score": 8.0,
             "quality_score": 8.5,
             "reasoning": "Deep critique text",
             "contribution": "Core contribution"},
        ]
        engine = self._engine(ai_manager)

        verdict = engine.evaluate_paper({"title": "Paper B", "abstract": "Abstract"})

        assert verdict["is_accepted"] is True
        assert verdict["escalated"] is True
        assert verdict["tier"] == "heavy_reasoning"
        # -- S_rel_calibrated comes from the heavy tier's own overall_score. --
        assert verdict["overall_score"] == 8.0
        assert verdict["quality_score"] == 8.5
        assert verdict["evidence_quadrant"] == "ELITE_FOUNDATIONAL"
        assert verdict["key_contributions"] == "Core contribution"
        assert verdict["critique"] == "Deep critique text"
        assert ai_manager.evaluate_paper_json.call_count == 2

    def test_threshold_boundary_is_inclusive(self):
        """A score exactly equal to the threshold escalates (>= semantics)."""
        ai_manager = MagicMock()
        ai_manager.evaluate_paper_json.side_effect = [
            {"overall_score": 6.0},
            {"overall_score": 6.0, "quality_score": 6.0},
        ]
        engine = self._engine(ai_manager, threshold=6.0)

        verdict = engine.evaluate_paper({"title": "Paper C", "abstract": "Abstract"})

        assert verdict["escalated"] is True
        assert verdict["tier"] == "heavy_reasoning"

    def test_missing_fast_evaluation_rejects_safely(self):
        """A failed fast evaluation degrades to a safe rejection verdict."""
        ai_manager = MagicMock()
        ai_manager.evaluate_paper_json.return_value = None
        engine = self._engine(ai_manager)

        verdict = engine.evaluate_paper({"title": "Paper D", "abstract": "Abstract"})

        assert verdict["is_accepted"] is False
        assert verdict["escalated"] is False
        assert verdict["overall_score"] == 0.0
        assert verdict["tier"] == "fast_local"

    def test_batch_preserves_input_order(self):
        """The concurrent batch pool preserves input order in its output."""
        ai_manager = MagicMock()
        ai_manager.evaluate_paper_json.return_value = {
            "overall_score": 3.0,
            "scores": {"strategic": 3, "operational": 3, "tactical": 3, "playground": 3},
        }
        engine = self._engine(ai_manager)
        papers = [{"title": f"P{i}", "abstract": "A"} for i in range(5)]

        results = engine.evaluate_batch(papers)

        assert [r["paper"]["title"] for r in results] == ["P0", "P1", "P2", "P3", "P4"]
