# -*- coding: utf-8 -*-
"""
Module: __init__.py
Project: TALOS v5.15.5
Description:
    Package root for the Stanford DSPy PRISMA-ScR Declarative Synthesis Pipeline.
    Exposes the four typed declarative signatures (``dspy_signatures``), the
    modular pipeline classes (``dspy_modules``), the multi-agent peer-review
    swarm (``swarm_evaluators``), the PRISMA 2020 Mermaid flowchart generator
    (``mermaid_generator``), and the scoping review synthesizer
    (``scoping_review_synthesizer``). This package is fully air-gapped and
    local-first: the DSPy-style typed signatures are implemented natively with
    Pydantic v2, so no external ``dspy-ai`` package is required at runtime.
Dependencies:
    - src.prisma.dspy_signatures: Typed declarative PRISMA-ScR schema models.
    - src.prisma.dspy_modules: PrismaPlanner / PrismaEvaluator /
        PrismaEligibilityJudge / PrismaExecutor pipeline classes.
    - src.prisma.swarm_evaluators: Multi-agent peer-review swarm and consensus.
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
]
