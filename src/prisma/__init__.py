# -*- coding: utf-8 -*-
"""
Module: __init__.py
Project: TALOS v5.18.4
Description:
    Package root for the Stanford DSPy PRISMA-ScR Declarative Synthesis Pipeline.
    Exposes the four typed declarative signatures (``dspy_signatures``), the
    modular pipeline classes (``dspy_modules``), the Tier-1 multi-agent
    peer-review screening swarm (``swarm_evaluators``), the Tier-2 Forensic
    Quality Swarm with its profile skill compiler (``quality_swarm``, v5.17.0),
    the Kitchenham quality appraisal engine (``quality_appraisal``), the
    PRISMA 2020 Mermaid flowchart generator (``mermaid_generator``), and the
    scoping review synthesizer (``scoping_review_synthesizer``). This package
    is fully air-gapped and local-first: the DSPy-style typed signatures are
    implemented natively with Pydantic v2, so no external ``dspy-ai`` package
    is required at runtime.
Dependencies:
    - src.prisma.dspy_signatures: Typed declarative PRISMA-ScR schema models.
    - src.prisma.dspy_modules: PrismaPlanner / PrismaEvaluator /
        PrismaEligibilityJudge / PrismaExecutor pipeline classes.
    - src.prisma.swarm_evaluators: Tier-1 multi-agent screening swarm.
    - src.prisma.quality_swarm: Tier-2 forensic quality swarm, SmartSectionSlicer,
        SkillCompiler, and KitchenhamQualitySynthesizer.
    - src.prisma.quality_appraisal: Kitchenham rubric and 2D quadrant engine.
    - src.prisma.mermaid_generator: PRISMA 2020 flowchart generator.
    - src.prisma.scoping_review_synthesizer: Markdown and LaTeX report synthesizer.
"""

from src.prisma.dspy_signatures import (
    PrismaPlanSignature,
    PrismaScreeningSignature,
    PrismaEligibilitySignature,
    PrismaSynthesisSignature,
    extract_json_payload,
)
from src.prisma.dspy_modules import (
    PrismaPlanner,
    PrismaEvaluator,
    PrismaEligibilityJudge,
    PrismaExecutor,
)
from src.prisma.swarm_evaluators import (
    AlgorithmicReviewer,
    EmpiricalReviewer,
    OperationalReviewer,
    ReviewerVerdict,
    ConsensusVerdict,
    SwarmConsensusArbiter,
    calculate_cohens_kappa,
    cohens_kappa_pairwise,
)
from src.prisma.mermaid_generator import (
    generate_prisma_mermaid,
    mermaid_to_markdown,
    mermaid_to_html,
)
from src.prisma.scoping_review_synthesizer import (
    synthesize_scoping_review,
    synthesize_scoping_review_latex,
)
from src.prisma.quality_appraisal import (
    KitchenhamRubric,
    QualityAppraisalResult,
    PrismaQualityAppraiser,
    map_evidence_quadrant,
)
from src.prisma.quality_swarm import (
    SkillCompiler,
    SmartSectionSlicer,
    SkillAuditor,
    TheoryAuditor,
    OperationalAuditor,
    BenchmarkAuditor,
    OpenScienceAuditor,
    TheoryAuditResult,
    OperationalAuditResult,
    BenchmarkAuditResult,
    OpenScienceAuditResult,
    SwarmQualityVerdict,
    KitchenhamQualitySynthesizer,
    resolve_quality_swarm_workers,
)

__all__ = [
    "PrismaPlanSignature",
    "PrismaScreeningSignature",
    "PrismaEligibilitySignature",
    "PrismaSynthesisSignature",
    "extract_json_payload",
    "PrismaPlanner",
    "PrismaEvaluator",
    "PrismaEligibilityJudge",
    "PrismaExecutor",
    "AlgorithmicReviewer",
    "EmpiricalReviewer",
    "OperationalReviewer",
    "ReviewerVerdict",
    "ConsensusVerdict",
    "SwarmConsensusArbiter",
    "calculate_cohens_kappa",
    "cohens_kappa_pairwise",
    "generate_prisma_mermaid",
    "mermaid_to_markdown",
    "mermaid_to_html",
    "synthesize_scoping_review",
    "synthesize_scoping_review_latex",
    "KitchenhamRubric",
    "QualityAppraisalResult",
    "PrismaQualityAppraiser",
    "map_evidence_quadrant",
    "SkillCompiler",
    "SmartSectionSlicer",
    "SkillAuditor",
    "TheoryAuditor",
    "OperationalAuditor",
    "BenchmarkAuditor",
    "OpenScienceAuditor",
    "TheoryAuditResult",
    "OperationalAuditResult",
    "BenchmarkAuditResult",
    "OpenScienceAuditResult",
    "SwarmQualityVerdict",
    "KitchenhamQualitySynthesizer",
    "resolve_quality_swarm_workers",
]
