# -*- coding: utf-8 -*-
"""
Module: test_quality_swarm.py
Project: TALOS v5.17.0
Description:
    Hermetic unit tests for the Tier-2 Forensic Quality Swarm (v5.17.0).
    The suite makes no live Ollama or external API calls: the LLM backend is
    replaced by a deterministic fake, and the profile filesystem is redirected
    to a pytest ``tmp_path`` workspace. It verifies the ternary audit models,
    the SmartSectionSlicer token-minimization contract, the SkillCompiler
    placeholder injection and idempotent fast path, and the four-auditor
    KitchenhamQualitySynthesizer consensus (Q1-Q6, S_qual, kappa_qual,
    quadrant, narrative) end to end.

Dependencies:
    - pytest: Test framework and tmp_path/monkeypatch fixtures.
    - src.prisma.quality_swarm: The module under test.
"""

import json
import os

import pytest

import src.prisma.quality_swarm as qs
from src.prisma.quality_swarm import (
    BenchmarkAuditResult,
    KitchenhamQualitySynthesizer,
    OpenScienceAuditResult,
    OperationalAuditResult,
    SkillCompiler,
    SmartSectionSlicer,
    TheoryAuditResult,
    resolve_quality_swarm_workers,
)
from src.prisma.quality_appraisal import PrismaQualityAppraiser


# ---------------------------------------------------------------------------
# -- Fixtures --
# ---------------------------------------------------------------------------

@pytest.fixture()
def sandbox(monkeypatch, tmp_path):
    """Redirect the profile workspace and project root to a tmp directory."""
    (tmp_path / "talos.py").write_text("# marker\n", encoding="utf-8")
    profile_dir = tmp_path / "_profiles" / "demo"
    profile_dir.mkdir(parents=True)
    (profile_dir / "config.json").write_text(json.dumps({
        "research_topic": "Demonstration Research Domain",
        "inclusion_criteria": "Peer-reviewed demonstration studies.",
        "exclusion_criteria": "Non-empirical opinion pieces.",
    }), encoding="utf-8")
    monkeypatch.setattr(qs, "_resolve_project_root", lambda: str(tmp_path))
    monkeypatch.setattr(
        qs, "_profile_skills_dir",
        lambda name: str(tmp_path / "_profiles" / name / "skills"))
    monkeypatch.setenv("TALOS_NETWORK_STRATEGY", "strict_local")
    return tmp_path


class _FakeAI:
    """Deterministic LLM backend emitting per-auditor JSON verdicts."""

    def analyze_generic_text(self, prompt):
        if "TheoryAuditor" in prompt:
            return ('{"q1_aims_clarity": 1.0, '
                    '"theory_critique": "Formal aims and scope present."}')
        if "OperationalAuditor" in prompt:
            return ('{"q2_context_realism": 0.5, '
                    '"operational_critique": "Latency modeled; wind absent."}')
        if "BenchmarkAuditor" in prompt:
            return ('{"q3_baseline_rigor": 1.0, "q4_statistical_validity": 0.5, '
                    '"benchmark_critique": "Three baselines; only 3 seeds."}')
        return ('{"q5_open_reproducibility": 1.0, '
                '"q6_limitations_negative_results": 1.0, '
                '"openscience_critique": "Repository and limitations present."}')


MOCK_PAPER = {
    "title": "Formal Swarm Planning with Open Benchmarks",
    "abstract": (
        "We propose a formal problem statement. Compared against "
        "state-of-the-art baselines. Code is available at github."
    ),
}


# ---------------------------------------------------------------------------
# -- Ternary Audit Result Models --
# ---------------------------------------------------------------------------

class TestAuditResultModels:
    """Verify ternary coercion and mean-score semantics of audit models."""

    def test_theory_model_coerces_drifted_scores(self):
        result = TheoryAuditResult(q1_aims_clarity=0.8,
                                   theory_critique="ok")
        assert result.q1_aims_clarity == 1.0
        assert result.mean_score == 1.0

    def test_operational_model_defaults_to_zero(self):
        assert OperationalAuditResult().mean_score == 0.0

    def test_benchmark_model_averages_two_questions(self):
        result = BenchmarkAuditResult(q3_baseline_rigor=1,
                                      q4_statistical_validity="0.5")
        assert result.q4_statistical_validity == 0.5
        assert result.mean_score == pytest.approx(0.75)

    def test_openscience_model_averages_two_questions(self):
        result = OpenScienceAuditResult(q5_open_reproducibility=1,
                                        q6_limitations_negative_results=0)
        assert result.mean_score == pytest.approx(0.5)


# ---------------------------------------------------------------------------
# -- Smart Section Slicer --
# ---------------------------------------------------------------------------

class TestSmartSectionSlicer:
    """Verify targeted slicing and the word-cap contract."""

    FULL_TEXT = (
        "1. Introduction\nWe study planning.\n\n"
        "3. Methodology\nWe formalize the objective function formally.\n\n"
        "4. Experiments\nWe ran 5 random seeds with confidence intervals "
        "against three baselines.\n\n"
        "6. Limitations\nThe approach fails under extreme latency.\n\n"
        "Code Availability\nThe implementation is on GitHub.\n"
    )

    def test_abstract_fallback_without_full_text(self):
        slicer = SmartSectionSlicer()
        text = slicer.slice_for_auditor("theory", MOCK_PAPER)
        assert "Formal Swarm Planning" in text
        assert "github" in text.lower()

    def test_openscience_receives_code_and_limitations_slices(self):
        slicer = SmartSectionSlicer()
        text = slicer.slice_for_auditor("openscience",
                                        {"title": "T", "abstract": "A",
                                         "full_text": self.FULL_TEXT})
        assert "CODE_AVAILABILITY" in text
        assert "DISCUSSION_LIMITATIONS" in text
        assert "EXPERIMENTS" not in text

    def test_word_cap_is_enforced(self):
        slicer = SmartSectionSlicer()
        long_text = "word " * 5000
        text = slicer.slice_for_auditor(
            "theory", {"title": "T", "abstract": "A", "full_text": long_text},
            max_words=100)
        assert len(text.replace(" [...]", "").split()) <= 102


# ---------------------------------------------------------------------------
# -- Skill Compiler --
# ---------------------------------------------------------------------------

class TestSkillCompiler:
    """Verify domain injection, idempotent fast path, and force recompile."""

    def test_compilation_creates_four_domain_specialized_files(self, sandbox):
        path = SkillCompiler().compile_profile_skills("demo")
        files = sorted(os.listdir(path))
        assert files == ["empirical_auditor.md", "openscience_auditor.md",
                         "operational_auditor.md", "theory_auditor.md"]
        content = (path / "theory_auditor.md").read_text(encoding="utf-8")
        assert "Demonstration Research Domain" in content
        assert "Peer-reviewed demonstration studies." in content
        assert "{{RESEARCH_DOMAIN}}" not in content
        assert "{{DOMAIN_CONSTRAINTS}}" not in content

    def test_fast_path_returns_immediately_without_rewriting(self, sandbox):
        compiler = SkillCompiler()
        first = compiler.compile_profile_skills("demo")
        marker = first / "theory_auditor.md"
        marker.write_text("CUSTOM SENTINEL", encoding="utf-8")
        second = compiler.compile_profile_skills("demo")
        assert second == first
        assert marker.read_text(encoding="utf-8") == "CUSTOM SENTINEL"

    def test_force_recompile_overwrites_existing_skills(self, sandbox):
        compiler = SkillCompiler()
        first = compiler.compile_profile_skills("demo")
        marker = first / "theory_auditor.md"
        marker.write_text("CUSTOM SENTINEL", encoding="utf-8")
        compiler.compile_profile_skills("demo", force_recompile=True)
        assert "Demonstration Research Domain" in marker.read_text(
            encoding="utf-8")

    def test_compiled_skills_exist_gate(self, sandbox):
        compiler = SkillCompiler()
        assert compiler.compiled_skills_exist("demo") is False
        compiler.compile_profile_skills("demo")
        assert compiler.compiled_skills_exist("demo") is True


# ---------------------------------------------------------------------------
# -- Kitchenham Quality Synthesizer --
# ---------------------------------------------------------------------------

class TestKitchenhamQualitySynthesizer:
    """Verify the four-auditor swarm consensus with a mocked backend."""

    def test_swarm_synthesis_computes_rubric_quadrant_and_kappa(self, sandbox):
        synthesizer = KitchenhamQualitySynthesizer(ai_manager=_FakeAI(),
                                                   profile_name="demo")
        verdict = synthesizer.synthesize(MOCK_PAPER, relevance_score=8.0)
        assert verdict.rubric.q1_aims_clarity == 1.0
        assert verdict.rubric.q2_context_realism == 0.5
        assert verdict.rubric.q3_baseline_rigor == 1.0
        assert verdict.rubric.q4_statistical_validity == 0.5
        assert verdict.rubric.q5_open_reproducibility == 1.0
        assert verdict.rubric.q6_limitations_negative_results == 1.0
        assert verdict.quality_score == pytest.approx(8.3333, abs=1e-3)
        assert verdict.evidence_quadrant == "ELITE_FOUNDATIONAL"
        assert -1.0 <= verdict.kappa_qual <= 1.0
        assert verdict.appraisal_mode == "swarm"
        assert len(verdict.auditor_critiques) == 4
        assert "S_qual" in verdict.synthesis
        assert "TheoryAuditor" in verdict.synthesis

    def test_unanimous_audits_yield_perfect_kappa(self, sandbox):
        class _PerfectAI:
            def analyze_generic_text(self, prompt):
                if "OperationalAuditor" in prompt:
                    return ('{"q2_context_realism": 1.0, '
                            '"operational_critique": "full"}')
                if "BenchmarkAuditor" in prompt:
                    return ('{"q3_baseline_rigor": 1.0, '
                            '"q4_statistical_validity": 1.0, '
                            '"benchmark_critique": "full"}')
                if "TheoryAuditor" in prompt:
                    return ('{"q1_aims_clarity": 1.0, '
                            '"theory_critique": "full"}')
                return ('{"q5_open_reproducibility": 1.0, '
                        '"q6_limitations_negative_results": 1.0, '
                        '"openscience_critique": "full"}')

        synthesizer = KitchenhamQualitySynthesizer(ai_manager=_PerfectAI(),
                                                   profile_name="demo")
        verdict = synthesizer.synthesize(MOCK_PAPER, relevance_score=9.0)
        assert verdict.quality_score == 10.0
        assert verdict.kappa_qual == pytest.approx(1.0)

    def test_swarm_degrades_deterministically_without_backend(self, sandbox):
        synthesizer = KitchenhamQualitySynthesizer(ai_manager=None,
                                                   profile_name="demo")
        synthesizer.ai_manager = None
        verdict = synthesizer.synthesize(MOCK_PAPER, relevance_score=8.0)
        assert 0.0 <= verdict.quality_score <= 10.0
        assert verdict.appraisal_mode == "swarm"

    def test_local_strategy_bounds_workers_to_two(self):
        workers, semaphore = resolve_quality_swarm_workers()
        assert workers == 2
        assert semaphore is not None


# ---------------------------------------------------------------------------
# -- Appraiser Swarm Integration --
# ---------------------------------------------------------------------------

class TestSwarmAppraiserIntegration:
    """Verify the swarm mode delegation inside PrismaQualityAppraiser."""

    def test_swarm_mode_returns_extended_result(self, sandbox):
        appraiser = PrismaQualityAppraiser(ai_manager=_FakeAI(),
                                           appraisal_mode="swarm")
        appraiser._active_profile = "demo"
        result = appraiser.appraise_paper(MOCK_PAPER, relevance_score=8.0)
        assert result is not None
        assert result.appraisal_mode == "swarm"
        assert result.swarm_kappa is not None
        assert result.quality_score == pytest.approx(8.3333, abs=1e-3)
        assert "theory_critique" in result.auditor_critiques

    def test_single_mode_remains_the_default(self):
        appraiser = PrismaQualityAppraiser()
        assert appraiser.appraisal_mode == "single"
