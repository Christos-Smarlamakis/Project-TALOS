# -*- coding: utf-8 -*-
"""
Module: swarm_evaluators.py
Project: TALOS v5.20.0
Description:
    Multi-agent peer-review swarm and consensus engine for the PRISMA-ScR
    screening stage. This module introduces three specialized reviewer personas
    (``AlgorithmicReviewer`` for mathematical/DRL/GNN soundness,
    ``EmpiricalReviewer`` for simulation/benchmark/ablation rigor, and
    ``OperationalReviewer`` for swarm scalability/communication/NATO CJCSI
    operational constraints). Each persona emits a ``ReviewerVerdict`` carrying
    an INCLUDE / EXCLUDE / UNCERTAIN vote, a bounded 0.0-10.0 score, a 0.0-1.0
    confidence, and key critiques. A ``SwarmConsensusArbiter`` aggregates the
    three verdicts, computes the multi-rater inter-rater reliability metric
    (Cohen's Kappa via its Fleiss generalization), and resolves split decisions
    with a Chain-of-Thought adjudication step. The whole swarm degrades
    gracefully to deterministic keyword rules when no LLM backend is reachable
    (air-gapped operation), and is throttled by a global ``threading.Semaphore``
    VRAM guard so concurrent local-GPU inference stays within budget.
Dependencies:
    - threading: Global VRAM-bound semaphore for concurrent local inference.
    - dataclasses: ReviewerVerdict and ConsensusVerdict structured records.
    - collections.Counter: Vote tallies for the consensus arbiter.
    - pydantic: BaseModel/Field for the typed reviewer personas.
    - src.prisma.dspy_signatures.extract_json_payload: Robust JSON recovery.
"""

import os
import re
import threading
from collections import Counter
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from src.prisma.dspy_signatures import extract_json_payload


# ---------------------------------------------------------------------------
# -- VRAM Guard & Concurrency Budget --
# ---------------------------------------------------------------------------

# Global semaphore bounding the number of concurrent local-GPU inference calls
# for the multi-agent swarm. Two permits match the Constitution III requirement
# that inference workloads leave a 2GB VRAM headroom on the llama3.1:8b tier.
VRAM_SEMAPHORE = threading.Semaphore(2)


def resolve_swarm_workers() -> int:
    """Resolve the swarm concurrency width from the active network strategy.

    Local-first strategies are bounded to two concurrent reviewers to respect
    the VRAM semaphore. Cloud-first and strict-cloud strategies may run all
    three reviewers concurrently over the Universal Cloud Mesh.

    Returns:
        int: The maximum number of concurrent reviewer tasks (2 or 3).
    """
    strategy = os.getenv("TALOS_NETWORK_STRATEGY", "strict_local").strip().lower()
    if strategy in ("cloud_first", "strict_cloud"):
        return 3
    return 2


def _keyword_hits(text: Optional[str], keywords: List[str]) -> int:
    """Count how many focus keywords appear in a normalized text string.

    Args:
        text (Optional[str]): Text to scan (title plus abstract).
        keywords (List[str]): Lowercase keyword vocabulary.

    Returns:
        int: Number of distinct keywords matched.
    """
    if not text:
        return 0
    haystack = str(text).lower()
    return sum(1 for kw in keywords if kw and kw in haystack)


# ---------------------------------------------------------------------------
# -- Structured Verdict Records --
# ---------------------------------------------------------------------------

@dataclass
class ReviewerVerdict:
    """A single reviewer persona's structured judgement of one study.

    Attributes:
        agent_name (str): The persona identifier (e.g. "AlgorithmicReviewer").
        vote (str): One of INCLUDE, EXCLUDE, UNCERTAIN.
        score (float): Relevance score bounded to [0.0, 10.0].
        confidence (float): Self-reported confidence bounded to [0.0, 1.0].
        critiques (List[str]): Key critical observations from this reviewer.
    """

    agent_name: str
    vote: str
    score: float = 0.0
    confidence: float = 0.5
    critiques: List[str] = field(default_factory=list)


@dataclass
class ConsensusVerdict:
    """The aggregated result of the multi-agent consensus arbitration.

    Attributes:
        final_decision (str): INCLUDE, EXCLUDE, or UNCERTAIN.
        consensus_score (float): Confidence-weighted average reviewer score.
        kappa (float): Multi-rater Cohen's (Fleiss) kappa for the vote set.
        synthesis (str): Multi-perspective narrative reconciling the verdicts.
        votes (List[str]): The raw votes from each reviewer.
        verdicts (List[ReviewerVerdict]): The full structured verdicts.
        mean_confidence (float): Arithmetic mean of reviewer confidences.
    """

    final_decision: str
    consensus_score: float
    kappa: float
    synthesis: str
    votes: List[str] = field(default_factory=list)
    verdicts: List[ReviewerVerdict] = field(default_factory=list)
    mean_confidence: float = 0.0


# ---------------------------------------------------------------------------
# -- Inter-Rater Reliability (Cohen's Kappa) --
# ---------------------------------------------------------------------------

def calculate_cohens_kappa(votes: List[str]) -> float:
    """Compute the multi-rater inter-agent agreement metric for one study.

    For a single study rated by ``m`` reviewers this reduces to Fleiss' kappa
    (the multi-rater generalization of Cohen's kappa):

        kappa = (p_o - p_e) / (1 - p_e)

    where ``p_o`` is the observed pairwise agreement proportion and ``p_e`` is
    the agreement expected by chance under the observed marginal category
    distribution. Unanimous vote sets collapse to a degenerate denominator and
    are therefore reported as perfect agreement (1.0).

    Args:
        votes (List[str]): One vote per reviewer (INCLUDE / EXCLUDE / UNCERTAIN).

    Returns:
        float: The agreement coefficient in the range (-1.0, 1.0]. A value of
            1.0 indicates perfect agreement, 0.0 indicates chance-level
            agreement, and negative values indicate systematic disagreement.
    """
    if not votes:
        return 0.0

    normalized = [str(v).strip().upper() for v in votes if str(v).strip()]
    if not normalized:
        return 0.0

    categories = sorted(set(normalized))
    if len(categories) <= 1:
        # -- Degenerate denominator: perfect agreement by construction. --
        return 1.0

    m = len(normalized)
    if m < 2:
        return 1.0

    counts = Counter(normalized)

    # -- Observed agreement for a single subject over m raters. --
    p_o = (sum(c * c for c in counts.values()) - m) / float(m * (m - 1))

    # -- Chance-expected agreement under the observed marginals. --
    p_e = sum((counts.get(c, 0) / float(m)) ** 2 for c in categories)

    if abs(1.0 - p_e) < 1e-12:
        return 1.0 if p_o >= 1.0 - 1e-12 else 0.0

    return (p_o - p_e) / (1.0 - p_e)


def cohens_kappa_pairwise(votes_a: List[str], votes_b: List[str]) -> float:
    """Compute the classical pairwise Cohen's kappa between two aligned raters.

    This is the standard two-rater reliability coefficient over ``N`` aligned
    subjects. It is provided for completeness and for auditing the pairwise
    agreement matrix across the swarm.

    Args:
        votes_a (List[str]): First rater's votes across subjects.
        votes_b (List[str]): Second rater's votes across subjects (same length).

    Returns:
        float: Pairwise Cohen's kappa in (-1.0, 1.0]. Returns 0.0 on a length
            mismatch or when the pair has fewer than two categories.
    """
    if len(votes_a) != len(votes_b) or not votes_a:
        return 0.0

    a = [str(v).strip().upper() for v in votes_a]
    b = [str(v).strip().upper() for v in votes_b]
    categories = sorted(set(a) | set(b))
    if len(categories) <= 1:
        return 1.0

    n = len(a)
    p_o = sum(1 for x, y in zip(a, b) if x == y) / float(n)

    p_e = 0.0
    for cat in categories:
        p_a = a.count(cat) / float(n)
        p_b = b.count(cat) / float(n)
        p_e += p_a * p_b

    if abs(1.0 - p_e) < 1e-12:
        return 1.0 if p_o >= 1.0 - 1e-12 else 0.0

    return (p_o - p_e) / (1.0 - p_e)


# ---------------------------------------------------------------------------
# -- Reviewer Persona Prompts --
# ---------------------------------------------------------------------------

def _review_prompt(persona_name: str, role: str, focus: str) -> str:
    """Build a persona-specific screening prompt template.

    Args:
        persona_name (str): Persona identifier.
        role (str): Human-readable reviewer role.
        focus (str): The evaluation lens description.

    Returns:
        str: A structured-JSON prompt template.
    """
    return (
        f"You are {persona_name}, a specialized peer reviewer acting as a "
        f"{role} for a PRISMA-ScR systematic scoping review. {focus} "
        "Think step by step, then output a single JSON object with keys: "
        "vote (one of INCLUDE, EXCLUDE, UNCERTAIN), score (float 0 to 10), "
        "confidence (float 0 to 1), critiques (list of strings). Return ONLY "
        "valid JSON with no commentary."
    )


# ---------------------------------------------------------------------------
# -- Reviewer Persona Base --
# ---------------------------------------------------------------------------

class ReviewerPersona(BaseModel):
    """Typed base persona for a specialized multi-agent reviewer.

    Subclasses declare their ``name``, ``role``, ``focus_domain``, the
    ``system_prompt`` template, and the ``focus_keywords`` / ``concern_keywords``
    vocabularies used by the deterministic air-gapped fallback. The ``review``
    method attempts an LLM-backed structured assessment first and falls back to
    keyword heuristics when the backend is unreachable.
    """

    name: str = "Reviewer"
    role: str = "Peer Reviewer"
    focus_domain: str = "methodological soundness"
    system_prompt: str = ""
    focus_keywords: List[str] = Field(default_factory=list)
    concern_keywords: List[str] = Field(default_factory=list)

    def _build_prompt(
        self,
        title: str,
        abstract: str,
        inclusion_criteria: Optional[List[str]],
        exclusion_criteria: Optional[List[str]],
    ) -> str:
        """Assemble the full prompt for a single screening request."""
        return (
            self.system_prompt
            + f"\n\nTitle: {title}\nAbstract: {abstract}\n"
            + f"Inclusion criteria: {inclusion_criteria or []}\n"
            + f"Exclusion criteria: {exclusion_criteria or []}"
        )

    def _verdict_from_json(self, data: Dict[str, Any]) -> ReviewerVerdict:
        """Recover a ``ReviewerVerdict`` from parsed LLM JSON.

        Args:
            data (Dict[str, Any]): Parsed JSON payload.

        Returns:
            ReviewerVerdict: A bounded, validated verdict.
        """
        vote = str(data.get("vote", data.get("decision", "UNCERTAIN"))).strip().upper()
        if vote not in ("INCLUDE", "EXCLUDE", "UNCERTAIN"):
            vote = "UNCERTAIN"

        try:
            score = max(0.0, min(10.0, float(data.get("score", 0.0))))
        except (TypeError, ValueError):
            score = 0.0

        try:
            confidence = max(0.0, min(1.0, float(data.get("confidence", 0.5))))
        except (TypeError, ValueError):
            confidence = 0.5

        raw_critiques = data.get("critiques", data.get("critique", []))
        if isinstance(raw_critiques, str):
            critiques = [c.strip() for c in re.split(r"[\n;]", raw_critiques) if c.strip()]
        elif isinstance(raw_critiques, list):
            critiques = [str(c).strip() for c in raw_critiques if str(c).strip()]
        else:
            critiques = []

        return ReviewerVerdict(
            agent_name=self.name,
            vote=vote,
            score=score,
            confidence=confidence,
            critiques=critiques,
        )

    def _deterministic_review(self, title: str, abstract: str) -> ReviewerVerdict:
        """Apply persona keyword heuristics when the LLM is unavailable.

        Args:
            title (str): Study title.
            abstract (str): Study abstract.

        Returns:
            ReviewerVerdict: Heuristically derived verdict.
        """
        text = f"{title} {abstract}"
        positives = _keyword_hits(text, self.focus_keywords)
        concerns = _keyword_hits(text, self.concern_keywords)

        score = min(10.0, float(positives) * 2.0)
        critiques: List[str] = []
        if positives == 0:
            critiques.append(f"No {self.focus_domain} signal detected in the record.")
        if concerns:
            critiques.append(f"Detected {concerns} concern term(s) under the {self.name} lens.")

        if positives >= 2 and concerns == 0:
            vote = "INCLUDE"
        elif concerns >= 1 and positives == 0:
            vote = "EXCLUDE"
        else:
            vote = "UNCERTAIN"

        confidence = min(1.0, 0.4 + 0.1 * positives)

        return ReviewerVerdict(
            agent_name=self.name,
            vote=vote,
            score=score,
            confidence=confidence,
            critiques=critiques,
        )

    def review(
        self,
        title: str,
        abstract: str,
        inclusion_criteria: Optional[List[str]] = None,
        exclusion_criteria: Optional[List[str]] = None,
        ai_manager: Optional[Any] = None,
    ) -> ReviewerVerdict:
        """Evaluate a single study through this persona's specialized lens.

        Args:
            title (str): Study title.
            abstract (str): Study abstract.
            inclusion_criteria (Optional[List[str]]): Inclusion criteria.
            exclusion_criteria (Optional[List[str]]): Exclusion criteria.
            ai_manager (Optional[Any]): The multi-tier AIManager backend.

        Returns:
            ReviewerVerdict: The persona's structured judgement.
        """
        if ai_manager is not None:
            prompt = self._build_prompt(title, abstract, inclusion_criteria, exclusion_criteria)
            try:
                raw = ai_manager.analyze_generic_text(prompt)
                data = extract_json_payload(raw)
                if isinstance(data, dict):
                    return self._verdict_from_json(data)
            except Exception:
                pass
        return self._deterministic_review(title, abstract)


# ---------------------------------------------------------------------------
# -- Specialized Reviewer Personas --
# ---------------------------------------------------------------------------

class AlgorithmicReviewer(ReviewerPersona):
    """Algorithmic rigor reviewer persona.

    Evaluates mathematical formulation, deep reinforcement learning algorithms
    (HMADRL, Dec-POMDPs, QMIX), graph neural networks (ST-GNNs / ST-GAT), and
    general theoretical soundness.
    """

    name: str = "AlgorithmicReviewer"
    role: str = "Algorithmic Rigor Reviewer"
    focus_domain: str = "mathematical formulation and DRL/GNN soundness"
    system_prompt: str = _review_prompt(
        "AlgorithmicReviewer",
        "Algorithmic Rigor Reviewer",
        "Evaluate the mathematical formulation, the correctness of any "
        "reinforcement learning algorithms (HMADRL, Dec-POMDPs, QMIX), the "
        "graph neural network architecture (ST-GNNs / ST-GAT), and the overall "
        "theoretical soundness of the work.",
    )
    focus_keywords: List[str] = Field(
        default_factory=lambda: [
            "reinforcement learning", "deep reinforcement", "drl", "hmadrl",
            "dec-pomdp", "qmix", "multi-agent", "multiagent", "graph neural",
            "st-gnn", "st-gat", "attention", "markov", "q-learning",
            "policy gradient", "actor-critic", "convergence", "theorem",
            "proof", "value function", "reward",
        ]
    )
    concern_keywords: List[str] = Field(
        default_factory=lambda: ["black box", "no theoretical", "heuristic only", "rule-based"]
    )


class EmpiricalReviewer(ReviewerPersona):
    """Empirical rigor reviewer persona.

    Evaluates simulation environments (Gazebo / AirSim / Isaac Gym), ablation
    studies, benchmark rigor, real flight tests, and quantitative metrics.
    """

    name: str = "EmpiricalReviewer"
    role: str = "Empirical Rigor Reviewer"
    focus_domain: str = "simulation, ablation, benchmark, and metric rigor"
    system_prompt: str = _review_prompt(
        "EmpiricalReviewer",
        "Empirical Rigor Reviewer",
        "Evaluate the simulation environment (Gazebo / AirSim / Isaac Gym), the "
        "presence and quality of ablation studies, benchmark rigor, any real "
        "flight or hardware tests, and the quantitative evaluation metrics.",
    )
    focus_keywords: List[str] = Field(
        default_factory=lambda: [
            "gazebo", "airsim", "isaac gym", "isaacgym", "simulation",
            "ablation", "benchmark", "real-world", "real world", "flight test",
            "experiment", "dataset", "rmse", "mae", "accuracy", "precision",
            "recall", "f1", "metric", "baseline", "pybullet",
        ]
    )
    concern_keywords: List[str] = Field(
        default_factory=lambda: ["no experiment", "no ablation", "no benchmark", "anecdotal"]
    )


class OperationalReviewer(ReviewerPersona):
    """Swarm operational reviewer persona.

    Evaluates swarm scalability, communication topology and latency, physical
    collision avoidance, and NATO / CJCSI operational constraints.
    """

    name: str = "OperationalReviewer"
    role: str = "Swarm Operational Reviewer (NATO CJCSI)"
    focus_domain: str = "swarm scalability, communication, and operational safety"
    system_prompt: str = _review_prompt(
        "OperationalReviewer",
        "Swarm Operational Reviewer (NATO CJCSI)",
        "Evaluate swarm scalability, communication topology and latency, "
        "physical collision avoidance, and conformance to NATO / CJCSI "
        "operational constraints.",
    )
    focus_keywords: List[str] = Field(
        default_factory=lambda: [
            "scalability", "scalable", "latency", "communication", "topology",
            "collision", "collision avoidance", "nato", "cjcsi", "bandwidth",
            "robustness", "fault", "reliability", "throughput", "energy",
            "endurance", "safety", "interoperability", "sensor fusion",
        ]
    )
    concern_keywords: List[str] = Field(
        default_factory=lambda: ["single agent", "centralized only", "no communication", "no collision"]
    )


# ---------------------------------------------------------------------------
# -- Swarm Consensus Arbiter --
# ---------------------------------------------------------------------------

class SwarmConsensusArbiter:
    """Aggregate individual reviewer verdicts into a consensus decision.

    Unanimous vote sets (3-0 or 0-3) yield an instant high-confidence decision.
    Split vote sets (2-1 or 1-2, or 1-1-1) invoke a Chain-of-Thought
    adjudication step (LLM-backed when available, majority/uncertain fallback
    otherwise) to reconcile the conflicting critiques. The result is a
    ``ConsensusVerdict`` carrying the final decision, a confidence-weighted
    consensus score, the multi-rater Cohen's Kappa, and a multi-perspective
    synthesis narrative.
    """

    def __init__(self, ai_manager: Optional[Any] = None) -> None:
        """Initialize the arbiter.

        Args:
            ai_manager (Optional[Any]): The multi-tier AIManager backend used for
                Chain-of-Thought adjudication of split votes.
        """
        self.ai_manager = ai_manager

    def adjudicate(self, verdicts: List[ReviewerVerdict]) -> ConsensusVerdict:
        """Aggregate a list of reviewer verdicts into a consensus decision.

        Args:
            verdicts (List[ReviewerVerdict]): One verdict per reviewer persona.

        Returns:
            ConsensusVerdict: The aggregated consensus result.
        """
        if not verdicts:
            return ConsensusVerdict(
                final_decision="UNCERTAIN",
                consensus_score=0.0,
                kappa=0.0,
                synthesis="No reviewer verdicts were produced.",
            )

        votes = [v.vote for v in verdicts]
        scores = [v.score for v in verdicts]
        confidences = [v.confidence for v in verdicts]

        kappa = calculate_cohens_kappa(votes)
        counts = Counter(votes)

        # -- Confidence-weighted consensus score (Borda-like aggregation). --
        total_conf = sum(confidences)
        if total_conf > 0:
            consensus_score = sum(s * c for s, c in zip(scores, confidences)) / total_conf
        else:
            consensus_score = sum(scores) / float(len(scores)) if scores else 0.0

        mean_confidence = sum(confidences) / float(len(confidences)) if confidences else 0.0

        if len(set(votes)) == 1:
            decision = votes[0]
            synthesis = self._unanimous_synthesis(decision, verdicts, consensus_score, kappa)
        else:
            decision = self._adjudicate_split(votes, verdicts, counts)
            synthesis = self._split_synthesis(decision, verdicts, counts, kappa)

        return ConsensusVerdict(
            final_decision=decision,
            consensus_score=round(consensus_score, 3),
            kappa=round(kappa, 4),
            synthesis=synthesis,
            votes=votes,
            verdicts=verdicts,
            mean_confidence=round(mean_confidence, 3),
        )

    def _unanimous_synthesis(
        self,
        decision: str,
        verdicts: List[ReviewerVerdict],
        consensus_score: float,
        kappa: float,
    ) -> str:
        """Synthesize the narrative for a unanimous decision."""
        agents = ", ".join(v.agent_name for v in verdicts)
        return (
            f"Unanimous {decision} decision across all three reviewers "
            f"({agents}) with perfect inter-rater agreement (Cohen's Kappa "
            f"{kappa:.4f}) and a consensus score of {consensus_score:.2f}. "
            "No adjudication was required."
        )

    def _split_synthesis(
        self,
        decision: str,
        verdicts: List[ReviewerVerdict],
        counts: Counter,
        kappa: float,
    ) -> str:
        """Synthesize the narrative for a split decision."""
        tally = ", ".join(f"{k}={v}" for k, v in counts.most_common())
        disagree = [v for v in verdicts if v.vote != decision]
        conflict = ""
        if disagree:
            conflict = (
                " The dissenting critiques were: "
                + " | ".join(f"{v.agent_name}: " + "; ".join(v.critiques) for v in disagree)
                + "."
            )
        return (
            f"Split vote ({tally}) resolved via Chain-of-Thought adjudication "
            f"to {decision} with inter-rater agreement (Cohen's Kappa {kappa:.4f})."
            f"{conflict}"
        )


    def _adjudicate_split(
        self,
        votes: List[str],
        verdicts: List[ReviewerVerdict],
        counts: Counter,
    ) -> str:
        """Resolve a split vote via Chain-of-Thought adjudication.

        Args:
            votes (List[str]): Raw reviewer votes.
            verdicts (List[ReviewerVerdict]): Structured verdicts.
            counts (Counter): Vote tallies.

        Returns:
            str: The final decision after adjudication.
        """
        majority, majority_count = counts.most_common(1)[0]

        # -- A 2-1 (or 1-2) split may be adjudicated by an LLM arbiter. --
        if majority_count >= 2 and self.ai_manager is not None:
            try:
                raw = self.ai_manager.analyze_generic_text(self._cot_prompt(verdicts))
                data = extract_json_payload(raw)
                if isinstance(data, dict):
                    decision = str(data.get("decision", "")).strip().upper()
                    if decision in ("INCLUDE", "EXCLUDE", "UNCERTAIN"):
                        return decision
            except Exception:
                pass
            return majority

        # -- 1-1-1 tie resolves to UNCERTAIN; otherwise majority wins. --
        if majority_count >= 2:
            return majority
        return "UNCERTAIN"

    def _cot_prompt(self, verdicts: List[ReviewerVerdict]) -> str:
        """Build a Chain-of-Thought adjudication prompt from split critiques.

        Args:
            verdicts (List[ReviewerVerdict]): The conflicting verdicts.

        Returns:
            str: A structured-JSON adjudication prompt.
        """
        lines = []
        for v in verdicts:
            critique = "; ".join(v.critiques) if v.critiques else "no critique"
            lines.append(
                f"- {v.agent_name}: {v.vote} (score {v.score:.1f}, "
                f"confidence {v.confidence:.2f}) -- {critique}"
            )
        block = "\n".join(lines)
        return (
            "You are the consensus arbiter of a 3-agent peer-review swarm. "
            "The reviewers disagree. Reason step by step over each critique, "
            "then output a single JSON object with key: decision (one of "
            "INCLUDE, EXCLUDE, UNCERTAIN). Return ONLY valid JSON.\n\n"
            f"Reviewer verdicts:\n{block}"
        )


__all__ = [
    "VRAM_SEMAPHORE",
    "resolve_swarm_workers",
    "ReviewerVerdict",
    "ConsensusVerdict",
    "calculate_cohens_kappa",
    "cohens_kappa_pairwise",
    "ReviewerPersona",
    "AlgorithmicReviewer",
    "EmpiricalReviewer",
    "OperationalReviewer",
    "SwarmConsensusArbiter",
]





