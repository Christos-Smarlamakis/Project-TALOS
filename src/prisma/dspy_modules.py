# -*- coding: utf-8 -*-
"""
Module: dspy_modules.py
Project: TALOS v5.14.2
Description:
    Modular pipeline classes implementing the four-phase PRISMA-ScR flow
    (Identification -> Screening -> Eligibility -> Included) on top of the typed
    declarative signatures in ``dspy_signatures``. ``PrismaPlanner`` synthesizes
    multi-database search protocols, ``PrismaEvaluator`` performs structured
    Chain-of-Thought title/abstract screening, ``PrismaEligibilityJudge``
    assesses full-record methodological suitability, and ``PrismaExecutor``
    orchestrates the end-to-end flow with live record counters and PRISMA 2020
    flowchart plus scoping-review report emission.

    Every LLM-backed step degrades gracefully: when the multi-tier ``AIManager``
    is unreachable (a fully air-gapped host with no local Ollama instance), each
    module falls back to deterministic, keyword-driven rules so the pipeline
    still completes and emits a reproducible report with clear warnings. The
    LLM interface used is ``AIManager.analyze_generic_text`` with robust JSON
    recovery, supporting both the local GPU tier (llama3.1:8b on port 11434) and
    the Universal Cloud Mesh.
Dependencies:
    - src.prisma.dspy_signatures: Typed declarative PRISMA-ScR signatures.
    - src.prisma.mermaid_generator: PRISMA 2020 Mermaid flowchart generation.
    - src.prisma.scoping_review_synthesizer: Markdown/LaTeX report synthesis.
    - src.core.ai_manager (lazy): Multi-provider LLM backend.
    - src.core.database_manager (lazy): Active-profile paper corpus.
"""

import json
import os
import re
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, List, Optional, Tuple

from src.prisma.dspy_signatures import (
    PrismaPlanSignature,
    PrismaScreeningSignature,
    PrismaEligibilitySignature,
    PrismaSynthesisSignature,
)
from src.prisma.mermaid_generator import generate_prisma_mermaid
from src.prisma.scoping_review_synthesizer import (
    synthesize_scoping_review,
    synthesize_scoping_review_latex,
)


# ---------------------------------------------------------------------------
# -- Project Root Resolution & Config Loading --
# ---------------------------------------------------------------------------

def _resolve_project_root() -> str:
    """Locate the TALOS repository root by walking up to ``talos.py``.

    Returns:
        str: Absolute path to the repository root.
    """
    current = os.path.dirname(os.path.abspath(__file__))
    while current and not os.path.exists(os.path.join(current, "talos.py")):
        parent = os.path.dirname(current)
        if parent == current:
            break
        current = parent
    return current


def _load_config() -> Dict[str, Any]:
    """Load ``config.json`` from the project root with template fallback.

    Returns:
        Dict[str, Any]: Configuration mapping, or an empty dict when absent.
    """
    root = _resolve_project_root()
    for name in ("config.json", "config.template.json"):
        path = os.path.join(root, name)
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as fh:
                    return json.load(fh)
            except (json.JSONDecodeError, OSError):
                continue
    return {}


# ---------------------------------------------------------------------------
# -- Prompt Templates (Structured JSON with Chain-of-Thought) --
# ---------------------------------------------------------------------------

_PLAN_PROMPT = (
    "You are a research librarian synthesizing a PRISMA-ScR search protocol. "
    "Given a research topic and domain scope, output a single JSON object with "
    "keys: search_facets (list of strings), boolean_strategy (string), "
    "methodological_inclusion_criteria (list of strings), exclusion_criteria "
    "(list of strings). Return ONLY valid JSON with no commentary."
)

_SCREEN_PROMPT = (
    "You are a systematic-review screener. Perform title/abstract screening. "
    "Think step by step, then output a single JSON object with keys: decision "
    "(one of INCLUDE, EXCLUDE, UNCERTAIN), relevance_score (float 0 to 10), "
    "exclusion_reason (string or null), methodology_tags (list of strings), "
    "chain_of_thought (string). Return ONLY valid JSON with no commentary."
)

_ELIGIBILITY_PROMPT = (
    "You are a scoping-review eligibility judge. Assess full-record "
    "methodological suitability. Output a single JSON object with keys: "
    "eligibility_decision (one of ELIGIBLE, INELIGIBLE), swarm_algorithm_type "
    "(string), learning_paradigm (string), network_architecture (string), "
    "justification (string). Return ONLY valid JSON with no commentary."
)

_SYNTHESIS_PROMPT = (
    "You are a scoping-review synthesizer. Given a summary of included studies "
    "and a research topic, output a single JSON object with keys: "
    "thematic_taxonomy (object), methodological_distribution (object), "
    "identified_gaps (list of strings), synthesis_narrative (string). Return "
    "ONLY valid JSON with no commentary."
)

# -- Deterministic fallback keyword vocabularies (air-gapped grace path). --
_INCLUSION_KEYWORDS = [
    "reinforcement learning", "drl", "deep reinforcement", "multi-agent",
    "multiagent", "swarm", "uav", "unmanned", "drone", "metaheuristic",
    "grey wolf", "gwo", "hyper-heuristic", "hyperheuristic", "task allocation",
    "mission planning", "path planning", "graph neural", "st-gnn", "marll",
]
_EXCLUSION_KEYWORDS = [
    "survey of surveys", "retracted", "erratum", "corrigendum",
]


def _keyword_hits(text: str, keywords: List[str]) -> int:
    """Count how many keywords appear in a normalized text string.

    Args:
        text (str): Text to scan.
        keywords (List[str]): Lowercase keyword list.

    Returns:
        int: Number of distinct keywords matched.
    """
    if not text:
        return 0
    haystack = text.lower()
    return sum(1 for kw in keywords if kw and kw in haystack)


def _criteria_keywords(criteria: Optional[List[str]]) -> List[str]:
    """Extract lowercase keyword tokens from a list of criteria strings.

    Args:
        criteria (Optional[List[str]]): Criteria strings.

    Returns:
        List[str]: Lowercase keyword tokens.
    """
    tokens: List[str] = []
    for item in criteria or []:
        for token in re.split(r"[^a-zA-Z0-9]+", str(item).lower()):
            if len(token) > 2:
                tokens.append(token)
    return tokens


# ---------------------------------------------------------------------------
# -- PrismaPlanner: Search Protocol Synthesis --
# ---------------------------------------------------------------------------

class PrismaPlanner:
    """Synthesize multi-database search protocols and query facets.

    Uses the LLM backend to produce a declarative ``PrismaPlanSignature`` and
    falls back to a deterministic token-based facet builder when the LLM is
    unreachable.
    """

    def __init__(self, ai_manager: Optional[Any] = None) -> None:
        """Initialize the planner.

        Args:
            ai_manager (Optional[Any]): An ``AIManager`` instance or ``None``.
        """
        self.ai_manager = ai_manager

    def plan(self, research_topic: str, domain_scope: str = "") -> PrismaPlanSignature:
        """Synthesize a PRISMA-ScR search protocol.

        Args:
            research_topic (str): The research topic.
            domain_scope (str): Optional domain scope qualifier.

        Returns:
            PrismaPlanSignature: Validated search protocol signature.
        """
        if self.ai_manager is not None:
            prompt = (
                _PLAN_PROMPT
                + f"\n\nResearch topic: {research_topic}\n"
                + f"Domain scope: {domain_scope or '(unspecified)'}"
            )
            try:
                raw = self.ai_manager.analyze_generic_text(prompt)
                parsed = PrismaPlanSignature.parse_output(raw)
                if parsed is not None:
                    parsed.research_topic = research_topic
                    parsed.domain_scope = domain_scope
                    return parsed
            except Exception:
                pass
        return self._deterministic_plan(research_topic, domain_scope)

    def _deterministic_plan(self, research_topic: str, domain_scope: str) -> PrismaPlanSignature:
        """Build a deterministic facet plan from topic tokens (air-gapped path).

        Args:
            research_topic (str): The research topic.
            domain_scope (str): Optional domain scope qualifier.

        Returns:
            PrismaPlanSignature: Deterministically derived protocol.
        """
        tokens = [t for t in re.split(r"[^a-zA-Z0-9]+", research_topic.lower()) if len(t) > 2]
        facets = [research_topic]
        if domain_scope:
            facets.append(domain_scope)
        boolean_strategy = " AND ".join(f'("{t}")' for t in tokens) if tokens else research_topic
        return PrismaPlanSignature(
            research_topic=research_topic,
            domain_scope=domain_scope,
            search_facets=facets,
            boolean_strategy=boolean_strategy,
            methodological_inclusion_criteria=list(_INCLUSION_KEYWORDS),
            exclusion_criteria=list(_EXCLUSION_KEYWORDS),
        )


# ---------------------------------------------------------------------------
# -- PrismaEvaluator: Chain-of-Thought Screening --
# ---------------------------------------------------------------------------

class PrismaEvaluator:
    """Perform structured Chain-of-Thought title/abstract screening.

    Returns a ``PrismaScreeningSignature`` carrying the decision, a bounded
    relevance score, optional exclusion reason, methodology tags and the
    explicit chain-of-thought trace for auditability. When ``evaluation_mode``
    is ``'swarm'`` (v5.14.1), screening is delegated to the 3-agent peer-review
    swarm (Algorithmic / Empirical / Operational reviewers) with automated
    Cohen's Kappa inter-rater reliability and consensus arbitration.
    """

    def __init__(
        self,
        ai_manager: Optional[Any] = None,
        evaluation_mode: str = "single",
    ) -> None:
        """Initialize the evaluator.

        Args:
            ai_manager (Optional[Any]): An ``AIManager`` instance or ``None``.
            evaluation_mode (str): ``'single'`` (fast baseline) or ``'swarm'``
                (rigorous 3-agent consensus with Cohen's Kappa).
        """
        self.ai_manager = ai_manager
        self.evaluation_mode = evaluation_mode

    def screen(
        self,
        title: str,
        abstract: str,
        inclusion_criteria: Optional[List[str]] = None,
        exclusion_criteria: Optional[List[str]] = None,
    ) -> PrismaScreeningSignature:
        """Screen a single title/abstract pair.

        Args:
            title (str): Study title.
            abstract (str): Study abstract.
            inclusion_criteria (Optional[List[str]]): Inclusion criteria.
            exclusion_criteria (Optional[List[str]]): Exclusion criteria.

        Returns:
            PrismaScreeningSignature: Screening decision and metadata.
        """
        if self.evaluation_mode == "swarm":
            return self._screen_swarm(title, abstract, inclusion_criteria, exclusion_criteria)
        if self.ai_manager is not None:
            prompt = (
                _SCREEN_PROMPT
                + f"\n\nTitle: {title}\nAbstract: {abstract}\n"
                + f"Inclusion criteria: {inclusion_criteria or []}\n"
                + f"Exclusion criteria: {exclusion_criteria or []}"
            )
            try:
                raw = self.ai_manager.analyze_generic_text(prompt)
                parsed = PrismaScreeningSignature.parse_output(raw)
                if parsed is not None:
                    parsed.title = title
                    parsed.abstract = abstract
                    parsed.inclusion_criteria = list(inclusion_criteria or [])
                    parsed.exclusion_criteria = list(exclusion_criteria or [])
                    return parsed
            except Exception:
                pass
        return self._deterministic_screen(title, abstract, inclusion_criteria, exclusion_criteria)

    def _screen_swarm(
        self,
        title: str,
        abstract: str,
        inclusion_criteria: Optional[List[str]],
        exclusion_criteria: Optional[List[str]],
    ) -> PrismaScreeningSignature:
        """Screen a record via the 3-agent peer-review swarm consensus engine.

        Dispatches the Algorithmic, Empirical and Operational reviewer personas
        concurrently (bounded by the global VRAM semaphore and the network
        strategy worker budget) and aggregates their verdicts with the
        ``SwarmConsensusArbiter``, recording Cohen's Kappa and per-agent
        critiques in the returned signature metadata.

        Args:
            title (str): Study title.
            abstract (str): Study abstract.
            inclusion_criteria (Optional[List[str]]): Inclusion criteria.
            exclusion_criteria (Optional[List[str]]): Exclusion criteria.

        Returns:
            PrismaScreeningSignature: Consensus decision with swarm metadata.
        """
        from src.prisma.swarm_evaluators import (
            AlgorithmicReviewer,
            EmpiricalReviewer,
            OperationalReviewer,
            SwarmConsensusArbiter,
            VRAM_SEMAPHORE,
            resolve_swarm_workers,
        )

        reviewers = [
            AlgorithmicReviewer(),
            EmpiricalReviewer(),
            OperationalReviewer(),
        ]
        workers = resolve_swarm_workers()

        def _run(reviewer: Any) -> Any:
            with VRAM_SEMAPHORE:
                return reviewer.review(
                    title, abstract, inclusion_criteria, exclusion_criteria, self.ai_manager
                )

        if workers <= 1:
            verdicts = [_run(r) for r in reviewers]
        else:
            with ThreadPoolExecutor(max_workers=workers) as pool:
                verdicts = list(pool.map(_run, reviewers))

        arbiter = SwarmConsensusArbiter(self.ai_manager)
        consensus = arbiter.adjudicate(verdicts)

        agent_verdicts = [
            {
                "agent": v.agent_name,
                "vote": v.vote,
                "score": v.score,
                "confidence": v.confidence,
                "critiques": v.critiques,
            }
            for v in verdicts
        ]

        return PrismaScreeningSignature(
            title=title,
            abstract=abstract,
            inclusion_criteria=list(inclusion_criteria or []),
            exclusion_criteria=list(exclusion_criteria or []),
            decision=consensus.final_decision,
            relevance_score=consensus.consensus_score,
            exclusion_reason=(
                "Excluded by multi-agent swarm consensus."
                if consensus.final_decision == "EXCLUDE"
                else None
            ),
            methodology_tags=[v.agent_name for v in verdicts],
            chain_of_thought=consensus.synthesis,
            consensus_mode="swarm",
            swarm_kappa=consensus.kappa,
            agent_verdicts=agent_verdicts,
        )

    def _deterministic_screen(
        self,
        title: str,
        abstract: str,
        inclusion_criteria: Optional[List[str]],
        exclusion_criteria: Optional[List[str]],
    ) -> PrismaScreeningSignature:
        """Apply keyword heuristics when the LLM is unavailable.

        Args:
            title (str): Study title.
            abstract (str): Study abstract.
            inclusion_criteria (Optional[List[str]]): Inclusion criteria.
            exclusion_criteria (Optional[List[str]]): Exclusion criteria.

        Returns:
            PrismaScreeningSignature: Heuristically derived decision.
        """
        text = f"{title} {abstract}"
        inc_keywords = _criteria_keywords(inclusion_criteria) or list(_INCLUSION_KEYWORDS)
        exc_keywords = _criteria_keywords(exclusion_criteria) or list(_EXCLUSION_KEYWORDS)
        inc_hits = _keyword_hits(text, inc_keywords)
        exc_hits = _keyword_hits(text, exc_keywords)

        score = min(10.0, float(inc_hits) * 2.0)
        if exc_hits and inc_hits == 0:
            decision = "EXCLUDE"
            reason = "Matched exclusion criteria and no inclusion criteria."
        elif inc_hits >= 1:
            decision = "INCLUDE"
            reason = None
        else:
            decision = "UNCERTAIN"
            reason = "Insufficient signal in title/abstract for automated decision."
        return PrismaScreeningSignature(
            title=title,
            abstract=abstract,
            inclusion_criteria=list(inclusion_criteria or []),
            exclusion_criteria=list(exclusion_criteria or []),
            decision=decision,
            relevance_score=score,
            exclusion_reason=reason,
            methodology_tags=[],
            chain_of_thought=(
                f"Deterministic fallback: {inc_hits} inclusion keyword hits, "
                f"{exc_hits} exclusion keyword hits."
            ),
        )


# ---------------------------------------------------------------------------
# -- PrismaEligibilityJudge: Full-Record Eligibility --
# ---------------------------------------------------------------------------

class PrismaEligibilityJudge:
    """Assess full abstract/methodology suitability for inclusion.

    Returns a ``PrismaEligibilitySignature`` that labels the swarm algorithm
    type, learning paradigm and network architecture, enabling the
    methodological evidence map in the scoping review report.
    """

    def __init__(self, ai_manager: Optional[Any] = None) -> None:
        """Initialize the judge.

        Args:
            ai_manager (Optional[Any]): An ``AIManager`` instance or ``None``.
        """
        self.ai_manager = ai_manager

    def assess(
        self,
        title: str,
        abstract: str,
        methodology_tags: Optional[List[str]] = None,
        deep_criteria: str = "",
    ) -> PrismaEligibilitySignature:
        """Assess a single screened-in record for methodological eligibility.

        Args:
            title (str): Study title.
            abstract (str): Study abstract.
            methodology_tags (Optional[List[str]]): Tags from screening.
            deep_criteria (str): Deep eligibility criteria text.

        Returns:
            PrismaEligibilitySignature: Eligibility decision and labels.
        """
        if self.ai_manager is not None:
            prompt = (
                _ELIGIBILITY_PROMPT
                + f"\n\nTitle: {title}\nAbstract: {abstract}\n"
                + f"Methodology tags: {methodology_tags or []}\n"
                + f"Deep criteria: {deep_criteria or '(unspecified)'}"
            )
            try:
                raw = self.ai_manager.analyze_generic_text(prompt)
                parsed = PrismaEligibilitySignature.parse_output(raw)
                if parsed is not None:
                    parsed.title = title
                    parsed.abstract = abstract
                    parsed.methodology_tags = list(methodology_tags or [])
                    parsed.deep_criteria = deep_criteria
                    return parsed
            except Exception:
                pass
        return self._deterministic_assess(title, abstract, methodology_tags, deep_criteria)

    def _deterministic_assess(
        self,
        title: str,
        abstract: str,
        methodology_tags: Optional[List[str]],
        deep_criteria: str,
    ) -> PrismaEligibilitySignature:
        """Apply a conservative heuristic when the LLM is unavailable.

        A record is deemed eligible when it has a non-empty abstract (a
        reportable methodology exists); it is labelled by scanning the text for
        known paradigm and architecture keywords.

        Args:
            title (str): Study title.
            abstract (str): Study abstract.
            methodology_tags (Optional[List[str]]): Screening tags.
            deep_criteria (str): Deep eligibility criteria text.

        Returns:
            PrismaEligibilitySignature: Heuristically derived decision.
        """
        text = f"{title} {abstract}".lower()
        has_abstract = bool(abstract and abstract.strip())
        eligible = has_abstract

        algorithm = ""
        for label, kw in (
            ("Grey Wolf Optimizer", "grey wolf"),
            ("Particle Swarm", "particle swarm"),
            ("Genetic Algorithm", "genetic algorithm"),
            ("Ant Colony", "ant colony"),
        ):
            if kw in text:
                algorithm = label
                break

        paradigm = ""
        for label, kw in (
            ("Deep Reinforcement Learning", "reinforcement learning"),
            ("Supervised Learning", "supervised"),
            ("Unsupervised Learning", "unsupervised"),
            ("Heuristic/Metaheuristic", "metaheuristic"),
        ):
            if kw in text:
                paradigm = label
                break

        architecture = ""
        for label, kw in (
            ("Graph Neural Network", "graph neural"),
            ("Transformer", "transformer"),
            ("Convolutional Neural Network", "convolutional"),
            ("Multi-Agent Network", "multi-agent"),
        ):
            if kw in text:
                architecture = label
                break

        return PrismaEligibilitySignature(
            title=title,
            abstract=abstract,
            methodology_tags=list(methodology_tags or []),
            deep_criteria=deep_criteria,
            eligibility_decision="ELIGIBLE" if eligible else "INELIGIBLE",
            swarm_algorithm_type=algorithm,
            learning_paradigm=paradigm,
            network_architecture=architecture,
            justification=(
                "Deterministic fallback: eligibility based on abstract presence "
                "and keyword-labelled methodology."
            ),
        )


# ---------------------------------------------------------------------------
# -- PrismaExecutor: End-to-End Orchestrator --
# ---------------------------------------------------------------------------

class PrismaExecutor:
    """Orchestrate the 4-phase PRISMA-ScR flow end-to-end.

    The flow is strictly linear (Constitution IV): Identification -> Screening
    -> Eligibility -> Included. Live record counters are maintained in
    ``self.counts`` and updated after each phase. The executor composes the
    ``PrismaPlanner``, ``PrismaEvaluator`` and ``PrismaEligibilityJudge`` and
    finally emits a PRISMA 2020 Mermaid flowchart plus Markdown and LaTeX
    scoping review drafts.
    """

    def __init__(
        self,
        ai_manager: Optional[Any] = None,
        db_manager: Optional[Any] = None,
        evaluation_mode: str = "single",
    ) -> None:
        """Initialize the executor.

        Args:
            ai_manager (Optional[Any]): Optional pre-built ``AIManager``.
            db_manager (Optional[Any]): Optional pre-built ``DatabaseManager``.
            evaluation_mode (str): Default screening mode: ``'single'`` (fast)
                or ``'swarm'`` (3-agent consensus with Cohen's Kappa).
        """
        self._ai_manager = ai_manager
        self._db_manager = db_manager
        self._evaluation_mode = evaluation_mode
        self.planner: Optional[PrismaPlanner] = None
        self.evaluator: Optional[PrismaEvaluator] = None
        self.judge: Optional[PrismaEligibilityJudge] = None
        self.counts: Dict[str, int] = {}
        self.plan: Optional[PrismaPlanSignature] = None
        self.included_papers: List[Dict[str, Any]] = []
        self.mermaid: str = ""
        self.markdown_report: str = ""
        self.latex_report: str = ""
        self.swarm_stats: Dict[str, Any] = {}

    def _ensure_ai_manager(self) -> Optional[Any]:
        """Lazily construct the multi-tier ``AIManager`` if not supplied.

        Returns:
            Optional[Any]: The AIManager instance, or ``None`` if construction
                fails (the executor then uses deterministic fallbacks).
        """
        if self._ai_manager is None:
            try:
                from src.core.ai_manager import AIManager
                self._ai_manager = AIManager(_load_config())
            except Exception:
                self._ai_manager = None
        return self._ai_manager

    def _ensure_components(self) -> None:
        """Instantiate planner, evaluator and judge over the resolved backend."""
        ai = self._ensure_ai_manager()
        self.planner = PrismaPlanner(ai)
        self.evaluator = PrismaEvaluator(ai, evaluation_mode=self._evaluation_mode)
        self.judge = PrismaEligibilityJudge(ai)

    def _collect_papers(
        self,
        papers: Optional[List[Dict[str, Any]]],
        limit: Optional[int],
    ) -> List[Dict[str, Any]]:
        """Gather the identification corpus from a supplied list or the DB.

        Args:
            papers (Optional[List[Dict[str, Any]]]): Explicit paper list.
            limit (Optional[int]): Maximum records to process.

        Returns:
            List[Dict[str, Any]]: The identification corpus.
        """
        if papers:
            corpus = list(papers)
        else:
            try:
                from src.core.database_manager import DatabaseManager
                db = self._db_manager or DatabaseManager()
                corpus = db.get_all_papers_for_dashboard()
            except Exception:
                corpus = []
        if limit is not None and limit > 0:
            corpus = corpus[:limit]
        return corpus

    @staticmethod
    def _deduplicate(papers: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], int]:
        """Remove duplicate records keyed by DOI then normalized title.

        Args:
            papers (List[Dict[str, Any]]): Records to deduplicate.

        Returns:
            Tuple[List[Dict[str, Any]], int]: (deduplicated list, removed count).
        """
        seen = set()
        unique = []
        removed = 0
        for paper in papers:
            key = str(paper.get("doi") or "").strip().lower()
            if not key:
                key = re.sub(r"[^a-z0-9]+", " ", str(paper.get("title") or "").lower()).strip()
            if not key:
                key = f"id:{paper.get('id')}"
            if key in seen:
                removed += 1
            else:
                seen.add(key)
                unique.append(paper)
        return unique, removed

    def run(
        self,
        research_topic: str = "reinforcement learning swarm mission planning",
        domain_scope: str = "swarm robotics and deep reinforcement learning",
        papers: Optional[List[Dict[str, Any]]] = None,
        max_papers: Optional[int] = None,
        deep_criteria: str = "",
        evaluation_mode: Optional[str] = None,
        render: bool = False,
    ) -> Dict[str, Any]:
        """Execute the full 4-phase PRISMA-ScR pipeline.

        Args:
            research_topic (str): Research topic under review.
            domain_scope (str): Domain scope qualifier.
            papers (Optional[List[Dict[str, Any]]]): Explicit paper corpus.
            max_papers (Optional[int]): Maximum records to process.
            deep_criteria (str): Deep eligibility criteria text.
            evaluation_mode (Optional[str]): ``'single'`` or ``'swarm'``;
                overrides the executor's default screening mode.
            render (bool): When True, render live counters to the console.

        Returns:
            Dict[str, Any]: Result carrying the plan, counts, included studies,
                Mermaid diagram and Markdown/LaTeX drafts.
        """
        if evaluation_mode is not None:
            self._evaluation_mode = evaluation_mode

        self._ensure_components()
        assert self.planner is not None
        assert self.evaluator is not None
        assert self.judge is not None

        # -- Phase 1: Identification (plan + corpus + deduplication). --
        self.plan = self.planner.plan(research_topic, domain_scope)
        corpus = self._collect_papers(papers, max_papers)
        n_identified = len(corpus)
        sources = {str(p.get("source") or "unspecified") for p in corpus}
        n_databases = len(sources) if sources else 1
        deduped, n_dup = self._deduplicate(corpus)

        inclusion_criteria = self.plan.methodological_inclusion_criteria
        exclusion_criteria = self.plan.exclusion_criteria

        # -- Phase 2: Screening. --
        excluded_reasons: Dict[str, int] = {}
        candidates: List[Dict[str, Any]] = []
        swarm_kappas: List[float] = []
        for paper in deduped:
            result = self.evaluator.screen(
                str(paper.get("title") or ""),
                str(paper.get("abstract") or ""),
                inclusion_criteria,
                exclusion_criteria,
            )
            if getattr(result, "consensus_mode", "single") == "swarm" and result.swarm_kappa is not None:
                swarm_kappas.append(float(result.swarm_kappa))
            if result.decision == "EXCLUDE":
                reason = str(result.exclusion_reason or "Excluded at screening")
                excluded_reasons[reason] = excluded_reasons.get(reason, 0) + 1
            else:
                record = dict(paper)
                record["screening"] = result.model_dump()
                record["methodology_tags"] = list(result.methodology_tags)
                candidates.append(record)

        n_screened = len(deduped)
        n_excluded_screening = n_screened - len(candidates)
        n_sought = len(candidates)

        # -- Log swarm consensus statistics from the screening phase. --
        if self._evaluation_mode == "swarm" and swarm_kappas:
            mean_kappa = sum(swarm_kappas) / float(len(swarm_kappas))
            self.swarm_stats = {
                "records_consensus": len(swarm_kappas),
                "mean_kappa": mean_kappa,
                "kappas": swarm_kappas,
            }
            print(
                f"Swarm consensus screening: {len(swarm_kappas)} records, "
                f"mean Cohen's Kappa = {mean_kappa:.4f}"
            )

        # -- Phase 3: Eligibility. --
        included: List[Dict[str, Any]] = []
        for record in candidates:
            verdict = self.judge.assess(
                str(record.get("title") or ""),
                str(record.get("abstract") or ""),
                list(record.get("methodology_tags") or []),
                deep_criteria,
            )
            if verdict.eligibility_decision == "ELIGIBLE":
                final = dict(record)
                final["swarm_algorithm_type"] = verdict.swarm_algorithm_type
                final["learning_paradigm"] = verdict.learning_paradigm
                final["network_architecture"] = verdict.network_architecture
                final["justification"] = verdict.justification
                included.append(final)
            else:
                reason = str(verdict.justification or "Ineligible at eligibility stage")
                excluded_reasons[reason] = excluded_reasons.get(reason, 0) + 1

        n_assessed = len(candidates)
        n_excluded_eligibility = n_assessed - len(included)
        n_included = len(included)

        # -- Phase 4: Included + artifact emission. --
        counts = {
            "databases": n_databases,
            "registers": 0,
            "duplicates_removed": n_dup,
            "records_screened": n_screened,
            "records_excluded": n_excluded_screening,
            "reports_sought": n_sought,
            "reports_assessed": n_assessed,
            "reports_excluded": n_excluded_eligibility,
            "studies_included": n_included,
            "excluded_reasons": excluded_reasons,
        }
        self.counts = counts
        self.included_papers = included
        self.mermaid = generate_prisma_mermaid(counts)
        self.markdown_report = synthesize_scoping_review(included, counts, research_topic)
        self.latex_report = synthesize_scoping_review_latex(included, counts, research_topic)

        if render:
            self._render_counters()

        return {
            "topic": research_topic,
            "plan": self.plan.model_dump(),
            "counts": counts,
            "included_papers": included,
            "mermaid": self.mermaid,
            "markdown_report": self.markdown_report,
            "latex_report": self.latex_report,
            "swarm_stats": self.swarm_stats,
        }

    # -- Rendering & Interactive Entrypoints --

    def _render_counters(self) -> None:
        """Render the live record counters as a Rich table (or plain text)."""
        counts = self.counts or {}
        try:
            from rich.console import Console
            from rich.table import Table
        except ImportError:
            self._print_counters_plain(counts)
            return

        console = Console()
        table = Table(title="PRISMA-ScR Record Counters", header_style="bold cyan",
                      border_style="cyan")
        table.add_column("Stage", style="bold")
        table.add_column("Metric", style="white")
        table.add_column("Count", justify="right", style="bold yellow")
        rows = [
            ("Identification", "Databases", counts.get("databases", 0)),
            ("Identification", "Registers", counts.get("registers", 0)),
            ("Identification", "Duplicates removed", counts.get("duplicates_removed", 0)),
            ("Screening", "Records screened", counts.get("records_screened", 0)),
            ("Screening", "Records excluded", counts.get("records_excluded", 0)),
            ("Eligibility", "Reports sought", counts.get("reports_sought", 0)),
            ("Eligibility", "Reports assessed", counts.get("reports_assessed", 0)),
            ("Eligibility", "Reports excluded", counts.get("reports_excluded", 0)),
            ("Included", "Studies included", counts.get("studies_included", 0)),
        ]
        for stage, metric, value in rows:
            table.add_row(stage, metric, str(value))
        console.print(table)

    @staticmethod
    def _print_counters_plain(counts: Dict[str, int]) -> None:
        """Fallback plain-text counter rendering without Rich."""
        print("\nPRISMA-ScR Record Counters")
        for label, key in (
            ("Databases", "databases"),
            ("Registers", "registers"),
            ("Duplicates removed", "duplicates_removed"),
            ("Records screened", "records_screened"),
            ("Records excluded", "records_excluded"),
            ("Reports sought", "reports_sought"),
            ("Reports assessed", "reports_assessed"),
            ("Reports excluded", "reports_excluded"),
            ("Studies included", "studies_included"),
        ):
            print(f"  {label}: {counts.get(key, 0)}")

    def _write_report(self, markdown: str, topic: str) -> str:
        """Persist the Markdown draft under ``data/reports`` and return the path.

        Args:
            markdown (str): Markdown scoping review draft.
            topic (str): Research topic (used only for the header context).

        Returns:
            str: Absolute path of the written report file.
        """
        root = _resolve_project_root()
        reports_dir = os.path.join(root, "data", "reports")
        os.makedirs(reports_dir, exist_ok=True)
        safe_topic = re.sub(r"[^a-zA-Z0-9]+", "_", topic).strip("_").lower() or "review"
        path = os.path.join(reports_dir, f"prisma_scoping_review_{safe_topic}.md")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(markdown)
        return path

    def run_interactive(self) -> Dict[str, Any]:
        """Run the pipeline interactively, prompting for topic and scope."""
        try:
            from rich.prompt import Prompt

            def ask(message: str, default: str) -> str:
                return Prompt.ask(message, default=default)
        except ImportError:
            def ask(message: str, default: str) -> str:
                value = input(f"{message} [{default}]: ")
                return value or default

        topic = ask("Research topic", "reinforcement learning swarm mission planning")
        scope = ask("Domain scope", "swarm robotics and deep reinforcement learning")
        raw_limit = ask("Maximum records to process (0 = all)", "50")
        try:
            max_papers = int(raw_limit) if int(raw_limit) > 0 else None
        except (TypeError, ValueError):
            max_papers = 50

        default_mode = "2" if self._evaluation_mode == "swarm" else "1"
        mode_choice = ask(
            "Screening mode (1 = Fast Single Screener, 2 = Rigorous Multi-Agent Review Swarm)",
            default_mode,
        )
        evaluation_mode = "swarm" if mode_choice.strip() == "2" else "single"

        result = self.run(
            research_topic=topic,
            domain_scope=scope,
            max_papers=max_papers,
            evaluation_mode=evaluation_mode,
            render=True,
        )

        path = self._write_report(result["markdown_report"], topic)
        try:
            from rich.console import Console
            console = Console()
            console.print(f"[green]Scoping review draft written to:[/green] {path}")
            console.print("[dim]Mermaid PRISMA 2020 flowchart:[/dim]")
            console.print(result["mermaid"])
        except ImportError:
            print(f"Scoping review draft written to: {path}")
            print("\nMermaid PRISMA 2020 flowchart:\n")
            print(result["mermaid"])
        return result


# ---------------------------------------------------------------------------
# -- Standalone CLI Entrypoint --
# ---------------------------------------------------------------------------

def main() -> None:
    """Standalone entrypoint for the PRISMA-ScR pipeline CLI."""
    PrismaExecutor().run_interactive()


if __name__ == "__main__":
    main()
