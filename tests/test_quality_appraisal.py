# -*- coding: utf-8 -*-
"""
Module: test_quality_appraisal.py
Project: TALOS v5.16.0
Description:
    Unit tests for the PRISMA Quality Appraisal engine (Kitchenham 2007).
    The suite is hermetic -- no live Ollama or external API calls are made.
    It verifies the ternary rubric normalization, the normalized quality-score
    computation ``S_qual = (10/6) * sum(Q_i)``, the 2D evidence-quadrant
    mapping, and the single-paper appraisal path with a mocked LLM backend.

Dependencies:
    - pytest: Test framework.
    - src.prisma.quality_appraisal: The module under test.
"""

import pytest

from src.prisma.quality_appraisal import (
    KitchenhamRubric,
    QualityAppraisalResult,
    PrismaQualityAppraiser,
    map_evidence_quadrant,
    _normalize_ternary,
)


class TestTernaryNormalization:
    """Verify the strict three-point categorical normalization."""

    def test_integer_one_normalizes_to_one(self):
        assert _normalize_ternary(1) == 1.0

    def test_integer_zero_normalizes_to_zero(self):
        assert _normalize_ternary(0) == 0.0

    def test_half_normalizes_to_half(self):
        assert _normalize_ternary(0.5) == 0.5

    def test_drifted_float_snaps_to_nearest_point(self):
        assert _normalize_ternary(0.8) == 1.0
        assert _normalize_ternary(0.2) == 0.0

    def test_none_normalizes_to_zero(self):
        assert _normalize_ternary(None) == 0.0


class TestKitchenhamRubric:
    """Verify the rubric schema and quality-score computation."""

    def test_valid_rubric_parses(self):
        rubric = KitchenhamRubric(
            q1_aims_clarity=1,
            q2_context_realism=0.5,
            q3_baseline_rigor=1,
            q4_statistical_validity=0.5,
            q5_open_reproducibility=1,
            q6_limitations_negative_results=1,
        )
        assert rubric.question_sum == 5.0
        assert rubric.quality_score == pytest.approx(8.3333, abs=1e-3)

    def test_perfect_rubric_scores_ten(self):
        rubric = KitchenhamRubric(
            q1_aims_clarity=1.0,
            q2_context_realism=1.0,
            q3_baseline_rigor=1.0,
            q4_statistical_validity=1.0,
            q5_open_reproducibility=1.0,
            q6_limitations_negative_results=1.0,
        )
        assert rubric.quality_score == 10.0

    def test_zero_rubric_scores_zero(self):
        rubric = KitchenhamRubric()
        assert rubric.quality_score == 0.0

    def test_drifted_inputs_are_coerced(self):
        rubric = KitchenhamRubric(
            q1_aims_clarity="1",
            q2_context_realism=2,
            q3_baseline_rigor=0.8,
        )
        assert rubric.q1_aims_clarity == 1.0
        assert rubric.q2_context_realism == 1.0
        assert rubric.q3_baseline_rigor == 1.0


class TestQuadrantMapping:
    """Verify the 2D Evidence Decision Plane classification."""

    def test_elite_foundational(self):
        assert map_evidence_quadrant(9.0, 8.0) == "ELITE_FOUNDATIONAL"

    def test_idea_mine(self):
        assert map_evidence_quadrant(8.0, 6.0) == "IDEA_MINE"

    def test_methodological_exemplar(self):
        assert map_evidence_quadrant(5.0, 8.5) == "METHODOLOGICAL_EXEMPLAR"

    def test_methodological_noise(self):
        assert map_evidence_quadrant(5.0, 4.0) == "METHODOLOGICAL_NOISE"

    def test_boundary_thresholds(self):
        assert map_evidence_quadrant(7.0, 7.5) == "ELITE_FOUNDATIONAL"
        assert map_evidence_quadrant(6.999, 7.5) == "METHODOLOGICAL_EXEMPLAR"


class TestPrismaQualityAppraiser:
    """Verify the single-paper appraisal path with a mocked backend."""

    def _mock_ai_manager(self, raw_response):
        class _FakeAI:
            def analyze_generic_text(self, prompt):
                return raw_response
        return _FakeAI()

    def test_appraise_paper_computes_score_and_quadrant(self):
        raw = (
            '{"q1_aims_clarity": 1.0, "q2_context_realism": 1.0, '
            '"q3_baseline_rigor": 1.0, "q4_statistical_validity": 1.0, '
            '"q5_open_reproducibility": 1.0, '
            '"q6_limitations_negative_results": 1.0, '
            '"critique_rationale": "fully rigorous"}'
        )
        appraiser = PrismaQualityAppraiser(ai_manager=self._mock_ai_manager(raw))
        result = appraiser.appraise_paper(
            {"title": "A rigorous study", "abstract": "Abstract text."},
            relevance_score=9.0,
        )
        assert isinstance(result, QualityAppraisalResult)
        assert result.quality_score == 10.0
        assert result.evidence_quadrant == "ELITE_FOUNDATIONAL"

    def test_appraise_paper_returns_none_on_unparseable(self):
        appraiser = PrismaQualityAppraiser(ai_manager=self._mock_ai_manager("not json"))
        result = appraiser.appraise_paper(
            {"title": "Study", "abstract": "Abstract."},
            relevance_score=9.0,
        )
        assert result is None

    def test_appraise_paper_returns_none_when_backend_returns_none(self):
        class _NoneAI:
            def analyze_generic_text(self, prompt):
                return None
        appraiser = PrismaQualityAppraiser(ai_manager=_NoneAI())
        result = appraiser.appraise_paper(
            {"title": "Study", "abstract": "Abstract."},
            relevance_score=9.0,
        )
        assert result is None

