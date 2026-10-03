# -*- coding: utf-8 -*-
"""
Module: quality_appraisal.py
Project: TALOS v5.19.0
Description:
    Standardized PRISMA Quality Appraisal engine implementing the Kitchenham et
    al. (2007) guidelines for systematic literature reviews in software
    engineering. This module formalizes a six-question, three-point categorical
    rubric ({0.0, 0.5, 1.0}) and decouples Semantic Relevance (``S_rel``, the
    existing four-layer ``overall_score``) from Methodological Quality
    (``S_qual``, computed here) onto a two-dimensional Evidence Decision Plane.

    v5.17.0 introduces the Two-Tier Hierarchical Swarm Architecture: the
    appraiser now supports an ``appraisal_mode`` parameter -- ``'single'``
    (fast single-prompt baseline) or ``'swarm'`` (Tier-2 Forensic Quality
    Swarm). In swarm mode, appraisal is delegated to
    ``KitchenhamQualitySynthesizer`` (``src/prisma/quality_swarm.py``), which
    dispatches four specialized skill auditors over targeted text slices and
    returns the merged rubric, the inter-auditor Fleiss ``kappa_qual``, and
    per-auditor forensic critiques. Profile skill files are auto-compiled by
    ``SkillCompiler`` before the batch when missing.

    v5.17.1 eliminates the silent-exit anti-pattern and adds a force
    re-appraisal engine: ``appraise_candidates_batch(force_reappraise=True)``
    re-audits every candidate regardless of prior ``quality_score``, while the
    default path renders an informative panel and re-displays the persisted 2D
    Evidence Quadrant distribution when no uncached candidates remain. The CLI
    and TUI expose this via the ``--force`` flag and an interactive re-appraisal
    confirmation prompt.

    ``PrismaQualityAppraiser`` evaluates a single paper or an entire candidate
    batch. Each appraisal prompts the multi-tier ``AIManager`` with a structured
    Kitchenham 2007 rubric, recovers the JSON answer defensively, validates it
    against ``KitchenhamRubric``, computes the normalized quality score
    ``S_qual = 10 / 6 * sum(Q_i)``, and maps the study onto one of four
    evidence quadrants (ELITE_FOUNDATIONAL, IDEA_MINE, METHODOLOGICAL_EXEMPLAR,
    METHODOLOGICAL_NOISE). Batch appraisal is throttled by a bounded
    ``threading.Semaphore(2)`` on local GPU and widened on the Cloud Mesh, in
    accordance with Constitution III VRAM containment.

Dependencies:
    - src.prisma.dspy_signatures.extract_json_payload: Robust JSON recovery.
    - src.core.ai_manager (lazy): Multi-provider LLM backend for appraisal.
    - src.core.database_manager (lazy): Active-profile SQLite persistence.
    - pydantic: BaseModel, Field, Literal, field_validator for typed rubrics.
    - rich: Table/Console for the quadrant distribution summary.
"""

import json
import os
import re
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field, field_validator, ValidationError

from src.prisma.dspy_signatures import extract_json_payload


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
# -- Ternary Rubric Normalization --
# ---------------------------------------------------------------------------

def _normalize_ternary(value: Any) -> float:
    """Coerce an arbitrary LLM output onto the strict {0.0, 0.5, 1.0} scale.

    Local models may emit ``0``/``1`` instead of ``0.0``/``1.0``, or a raw
    float that drifted from the categorical grid. This helper snaps any numeric
    input to the nearest valid ternary point so the rubric remains a strict
    three-point scale without brittle parse failures.

    Args:
        value (Any): Raw value recovered from the LLM JSON answer.

    Returns:
        float: One of ``0.0``, ``0.5``, or ``1.0``.
    """
    if value is None:
        return 0.0
    if isinstance(value, bool):
        return 1.0 if value else 0.0
    if isinstance(value, str):
        text = value.strip().lower()
        if text in ("1", "1.0", "yes", "true", "full", "fully"):
            return 1.0
        if text in ("0.5", "half", "partial", "partially"):
            return 0.5
        if text in ("0", "0.0", "no", "false", "none", "absent"):
            return 0.0
    try:
        num = float(value)
    except (TypeError, ValueError):
        return 0.0
    if num <= 0.25:
        return 0.0
    if num <= 0.75:
        return 0.5
    return 1.0


# ---------------------------------------------------------------------------
# -- Kitchenham 2007 Rubric Schema --
# ---------------------------------------------------------------------------

class KitchenhamRubric(BaseModel):
    """Standardized six-question Kitchenham et al. (2007) quality rubric.

    Each categorical question is scored on the strict three-point scale
    {0.0, 0.5, 1.0}:

    - ``q1_aims_clarity``: research aims, formal problem formulation, scope.
    - ``q2_context_realism``: physical/environmental constraints (latency,
      aerodynamics, NATO operational bounds) explicitly modeled.
    - ``q3_baseline_rigor``: comparison against at least 2-3 modern
      state-of-the-art baselines under identical conditions.
    - ``q4_statistical_validity``: multiple random seeds (>= 5) with
      confidence intervals or standard deviations reported.
    - ``q5_open_reproducibility``: publicly accessible implementation via a
      verified code repository or open benchmark simulator.
    - ``q6_limitations_negative_results``: explicit analysis of failure cases,
      algorithmic boundaries, or scalability bottlenecks.

    Attributes:
        q1_aims_clarity (float): Ternary score for the aims-clarity question.
        q2_context_realism (float): Ternary score for the context question.
        q3_baseline_rigor (float): Ternary score for the baseline question.
        q4_statistical_validity (float): Ternary score for statistical validity.
        q5_open_reproducibility (float): Ternary score for reproducibility.
        q6_limitations_negative_results (float): Ternary score for limitations.
        critique_rationale (str): Concise Chain-of-Thought justification.
    """

    q1_aims_clarity: float = Field(
        default=0.0,
        description="0.0 (No), 0.5 (Partly), 1.0 (Yes). Are the research aims, formal problem formulation, and scope clearly stated?",
    )
    q2_context_realism: float = Field(
        default=0.0,
        description="0.0 (No), 0.5 (Partly), 1.0 (Yes). Are physical/environmental constraints (latency, aerodynamics, NATO bounds) explicitly modeled?",
    )
    q3_baseline_rigor: float = Field(
        default=0.0,
        description="0.0 (No), 0.5 (Partly), 1.0 (Yes). Is the method compared against at least 2-3 modern state-of-the-art baselines under identical conditions?",
    )
    q4_statistical_validity: float = Field(
        default=0.0,
        description="0.0 (No), 0.5 (Partly), 1.0 (Yes). Are experiments run over multiple random seeds (>= 5) with confidence intervals or standard deviations?",
    )
    q5_open_reproducibility: float = Field(
        default=0.0,
        description="0.0 (No), 0.5 (Partly), 1.0 (Yes). Is the implementation publicly accessible via a verified code repository or open benchmark simulator?",
    )
    q6_limitations_negative_results: float = Field(
        default=0.0,
        description="0.0 (No), 0.5 (Partly), 1.0 (Yes). Do the authors explicitly analyze failure cases, algorithmic boundaries, or scalability bottlenecks?",
    )
    critique_rationale: str = ""

    @field_validator(
        "q1_aims_clarity",
        "q2_context_realism",
        "q3_baseline_rigor",
        "q4_statistical_validity",
        "q5_open_reproducibility",
        "q6_limitations_negative_results",
        mode="before",
    )
    @classmethod
    def _coerce_ternary(cls, value: Any) -> float:
        """Normalize each question onto the strict ternary scale.

        Args:
            value (Any): Raw value recovered from the LLM JSON answer.

        Returns:
            float: One of ``0.0``, ``0.5``, or ``1.0``.
        """
        return _normalize_ternary(value)

    @property
    def question_sum(self) -> float:
        """Return the arithmetic sum of the six ternary questions.

        Returns:
            float: Sum in the inclusive range [0.0, 6.0].
        """
        return (
            self.q1_aims_clarity
            + self.q2_context_realism
            + self.q3_baseline_rigor
            + self.q4_statistical_validity
            + self.q5_open_reproducibility
            + self.q6_limitations_negative_results
        )

    @property
    def quality_score(self) -> float:
        """Return the normalized Kitchenham quality score ``S_qual``.

        The score is computed strictly as ``S_qual = (sum(Q_i) / 6.0) * 10.0``,
        yielding a value in the inclusive range [0.0, 10.0].

        Returns:
            float: The normalized methodological quality score.
        """
        return (self.question_sum / 6.0) * 10.0


# ---------------------------------------------------------------------------
# -- Evidence Quadrant Classification --
# ---------------------------------------------------------------------------

QUADRANTS = Literal[
    "ELITE_FOUNDATIONAL",
    "IDEA_MINE",
    "METHODOLOGICAL_EXEMPLAR",
    "METHODOLOGICAL_NOISE",
]


def map_evidence_quadrant(relevance_score: float, quality_score: float) -> str:
    """Map a (relevance, quality) pair onto the 2D Evidence Decision Plane.

    The plane is partitioned by two orthogonal thresholds: ``S_rel = 7.0`` on
    the semantic-relevance axis and ``S_qual = 7.5`` on the methodological
    quality axis.

    - ``ELITE_FOUNDATIONAL``: high relevance AND high rigor (S_rel >= 7.0 and
      S_qual >= 7.5) -- the foundation of the literature corpus.
    - ``IDEA_MINE``: high relevance but weak rigor (S_rel >= 7.0 and
      S_qual < 7.5) -- promising ideas requiring methodological scrutiny.
    - ``METHODOLOGICAL_EXEMPLAR``: low relevance but strong rigor (S_rel < 7.0
      and S_qual >= 7.5) -- rigorous methods reusable as transferable patterns.
    - ``METHODOLOGICAL_NOISE``: low relevance and low rigor (S_rel < 7.0 and
      S_qual < 7.5) -- unlikely to contribute to the synthesis.

    Args:
        relevance_score (float): Semantic relevance ``S_rel`` in [0.0, 10.0].
        quality_score (float): Methodological quality ``S_qual`` in [0.0, 10.0].

    Returns:
        str: One of the four quadrant identifiers.
    """
    if relevance_score >= 7.0 and quality_score >= 7.5:
        return "ELITE_FOUNDATIONAL"
    if relevance_score >= 7.0 and quality_score < 7.5:
        return "IDEA_MINE"
    if relevance_score < 7.0 and quality_score >= 7.5:
        return "METHODOLOGICAL_EXEMPLAR"
    return "METHODOLOGICAL_NOISE"


class QualityAppraisalResult(BaseModel):
    """Structured result of a single Kitchenham quality appraisal.

    Attributes:
        quality_score (float): Normalized ``S_qual`` in [0.0, 10.0].
        rubric (KitchenhamRubric): The validated six-question rubric.
        evidence_quadrant (QUADRANTS): The 2D decision-plane quadrant.
        appraisal_mode (str): ``'single'`` or ``'swarm'`` (v5.17.0).
        swarm_kappa (Optional[float]): Inter-auditor Fleiss agreement in
            swarm mode; ``None`` for the single-prompt baseline.
        auditor_critiques (Dict[str, str]): Per-auditor forensic critiques in
            swarm mode; empty for the single-prompt baseline.
    """

    quality_score: float = Field(ge=0.0, le=10.0)
    rubric: KitchenhamRubric
    evidence_quadrant: QUADRANTS
    appraisal_mode: str = "single"
    swarm_kappa: Optional[float] = None
    auditor_critiques: Dict[str, str] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# -- Batch Concurrency Budget (VRAM Guard) --
# ---------------------------------------------------------------------------

# Global semaphore bounding concurrent local-GPU appraisal calls to two permits,
# mirroring the Constitution III requirement that inference workloads leave a
# 2GB VRAM headroom on the llama3.1:8b tier.
VRAM_SEMAPHORE = threading.Semaphore(2)


def _resolve_batch_concurrency():
    """Resolve the batch appraisal concurrency budget.

    Local-first strategies are bounded to two workers behind the module-level
    ``VRAM_SEMAPHORE``. Cloud-first and strict-cloud strategies may run eight
    workers over the Universal Cloud Mesh with no local VRAM guard.

    Returns:
        tuple[int, Optional[threading.Semaphore]]: (max_workers, semaphore).
    """
    strategy = os.getenv("TALOS_NETWORK_STRATEGY", "strict_local").strip().lower()
    if strategy in ("cloud_first", "strict_cloud"):
        return 8, None
    return 2, VRAM_SEMAPHORE


# ---------------------------------------------------------------------------
# -- PRISMA Quality Appraiser --
# ---------------------------------------------------------------------------

class PrismaQualityAppraiser:
    """Standardized Kitchenham (2007) quality appraisal engine.

    Evaluates a paper's methodological quality independently of its semantic
    relevance, then classifies the study onto the 2D Evidence Decision Plane.
    The class is fully air-gapped and local-first: when no ``AIManager`` backend
    is reachable, appraisal degrades to a deterministic zero-score rubric with
    an explicit warning instead of raising.

    Attributes:
        ai_manager (Optional[Any]): The multi-tier LLM backend, lazily built.
        db_manager (Optional[Any]): The active-profile database manager.
        appraisal_mode (str): ``'single'`` (fast baseline) or ``'swarm'``
            (Tier-2 Forensic Quality Swarm, v5.17.0).
    """

    def __init__(self, ai_manager: Optional[Any] = None,
                 db_manager: Optional[Any] = None,
                 appraisal_mode: str = "single") -> None:
        """Initialize the appraiser with optional pre-built dependencies.

        Args:
            ai_manager (Optional[Any]): Pre-built ``AIManager`` or ``None``.
            db_manager (Optional[Any]): Pre-built ``DatabaseManager`` or ``None``.
            appraisal_mode (str): ``'single'`` or ``'swarm'`` (default
                ``'single'``). Unknown values fall back to ``'single'``.
        """
        self.ai_manager = ai_manager
        self.db_manager = db_manager
        self.appraisal_mode = ("swarm" if str(appraisal_mode).strip().lower()
                               == "swarm" else "single")
        self._swarm_synthesizer = None
        self._active_profile: Optional[str] = None
        self._console = None

    def _ensure_ai_manager(self) -> Optional[Any]:
        """Lazily construct the multi-tier ``AIManager`` if not supplied.

        Returns:
            Optional[Any]: The AIManager instance, or ``None`` on failure.
        """
        if self.ai_manager is None:
            try:
                from src.core.ai_manager import AIManager
                self.ai_manager = AIManager(_load_config())
            except Exception:
                self.ai_manager = None
        return self.ai_manager

    def _ensure_db_manager(self) -> Optional[Any]:
        """Lazily construct the active-profile ``DatabaseManager`` if needed.

        Returns:
            Optional[Any]: The DatabaseManager instance, or ``None`` on failure.
        """
        if self.db_manager is None:
            try:
                from src.core.database_manager import DatabaseManager
                self.db_manager = DatabaseManager()
            except Exception:
                self.db_manager = None
        return self.db_manager

    @staticmethod
    def _build_prompt(paper: Dict[str, Any]) -> str:
        """Compose the structured Kitchenham 2007 appraisal prompt.

        Args:
            paper (Dict[str, Any]): Paper record exposing ``title`` and
                ``abstract`` keys.

        Returns:
            str: The complete appraisal prompt sent to the LLM backend.
        """
        title = str(paper.get("title") or "(untitled study)").strip()
        abstract = str(paper.get("abstract") or "").strip() or "(no abstract)"
        return (
            "You are a methodological quality appraiser performing a standardized "
            "quality appraisal following the Kitchenham et al. (2007) guidelines "
            "for systematic literature reviews in software engineering.\n\n"
            "Assess the study below against six standardized quality questions. "
            "For each question, assign exactly one of three categorical scores:\n"
            "  1.0 = the criterion is fully satisfied\n"
            "  0.5 = the criterion is partially satisfied\n"
            "  0.0 = the criterion is not satisfied or not reported\n\n"
            "Questions:\n"
            "Q1. Aims clarity: Are the research aims, formal problem formulation, "
            "and scope clearly stated?\n"
            "Q2. Context realism: Are physical/environmental constraints "
            "explicitly modeled (latency, aerodynamics, NATO bounds)?\n"
            "Q3. Baseline rigor: Is the method compared against at least 2-3 "
            "modern state-of-the-art baselines under identical conditions?\n"
            "Q4. Statistical validity: Are experiments conducted over multiple "
            "random seeds (>= 5), reporting confidence intervals or standard "
            "deviations?\n"
            "Q5. Open reproducibility: Is the implementation publicly accessible "
            "via a verified code repository or open benchmark simulator?\n"
            "Q6. Limitations and negative results: Do the authors explicitly "
            "analyze failure cases, algorithmic boundaries, or scalability "
            "bottlenecks?\n\n"
            "Respond ONLY with a valid JSON object using exactly this schema:\n"
            "{\n"
            '  "q1_aims_clarity": 0.0,\n'
            '  "q2_context_realism": 0.0,\n'
            '  "q3_baseline_rigor": 0.0,\n'
            '  "q4_statistical_validity": 0.0,\n'
            '  "q5_open_reproducibility": 0.0,\n'
            '  "q6_limitations_negative_results": 0.0,\n'
            '  "critique_rationale": "concise chain-of-thought justification per question"\n'
            "}\n\n"
            f"Study:\nTitle: {title}\nAbstract: {abstract}\n"
        )

    def appraise_paper(
        self,
        paper_dict: Dict[str, Any],
        relevance_score: float = 0.0,
    ) -> Optional[QualityAppraisalResult]:
        """Appraise a single paper and return its quality result.

        Prompts the LLM backend with the structured rubric, recovers the JSON
        answer, validates it, computes ``S_qual``, and maps the quadrant. When
        the backend is unreachable or the answer is unparseable, ``None`` is
        returned so the caller may skip persistence.

        Args:
            paper_dict (Dict[str, Any]): Paper record with ``title`` and
                ``abstract`` keys.
            relevance_score (float): Semantic relevance ``S_rel`` in [0.0, 10.0].

        Returns:
            Optional[QualityAppraisalResult]: The validated result, or ``None``.
        """
        # -- v5.17.0: Tier-2 Forensic Quality Swarm delegation. --
        if self.appraisal_mode == "swarm":
            return self._appraise_paper_swarm(paper_dict, relevance_score)
        ai = self._ensure_ai_manager()
        if ai is None:
            return None
        try:
            raw = ai.analyze_generic_text(self._build_prompt(paper_dict))
            payload = extract_json_payload(raw)
            if not payload:
                return None
            rubric = KitchenhamRubric(**payload)
            quality = rubric.quality_score
            quadrant = map_evidence_quadrant(
                float(relevance_score), float(quality)
            )
            return QualityAppraisalResult(
                quality_score=round(quality, 4),
                rubric=rubric,
                evidence_quadrant=quadrant,
            )
        except (ValidationError, TypeError, ValueError):
            return None

    def _appraise_paper_swarm(
        self,
        paper_dict: Dict[str, Any],
        relevance_score: float = 0.0,
    ) -> Optional[QualityAppraisalResult]:
        """Delegate one paper to the Tier-2 Forensic Quality Swarm.

        Lazily constructs the ``KitchenhamQualitySynthesizer``, runs the four
        specialized skill auditors concurrently, and adapts the swarm verdict
        onto the canonical ``QualityAppraisalResult`` contract so persistence
        and downstream consumers remain unchanged.

        Args:
            paper_dict (Dict[str, Any]): Paper record with ``title`` and
                ``abstract`` keys (plus optional ``full_text``).
            relevance_score (float): Semantic relevance ``S_rel``.

        Returns:
            Optional[QualityAppraisalResult]: The swarm appraisal result, or
                ``None`` when the swarm module is unavailable.
        """
        try:
            from src.prisma.quality_swarm import KitchenhamQualitySynthesizer
        except Exception:
            return None
        if self._swarm_synthesizer is None:
            self._swarm_synthesizer = KitchenhamQualitySynthesizer(
                ai_manager=self._ensure_ai_manager(),
                profile_name=self._active_profile,
            )
        try:
            verdict = self._swarm_synthesizer.synthesize(
                paper_dict,
                relevance_score=float(relevance_score),
                active_profile=self._active_profile,
            )
        except Exception:
            return None
        try:
            return QualityAppraisalResult(
                quality_score=float(verdict.quality_score),
                rubric=verdict.rubric,
                evidence_quadrant=verdict.evidence_quadrant,
                appraisal_mode="swarm",
                swarm_kappa=float(verdict.kappa_qual),
                auditor_critiques=dict(verdict.auditor_critiques),
            )
        except (ValidationError, TypeError, ValueError):
            return None

    def appraise_candidates_batch(
        self,
        min_relevance: float = 7.0,
        active_profile: Optional[str] = None,
        render: bool = True,
        force_reappraise: bool = False,
    ) -> List[Dict[str, Any]]:
        """Appraise candidate papers in the active database.

        Default (``force_reappraise=False``) behaviour selects only uncached
        candidates -- papers whose ``overall_score`` meets ``min_relevance`` and
        whose ``quality_score`` is still ``NULL``. When every candidate has
        already been appraised, the method does not silently exit: it renders an
        informative panel and re-displays the existing 2D Evidence Quadrant
        distribution, so the caller always receives actionable feedback.

        ``force_reappraise=True`` selects every candidate regardless of prior
        appraisal and overwrites ``quality_score``, ``quality_rubric_json``, and
        ``evidence_quadrant`` in SQLite WAL, enabling a deliberate re-audit.

        Args:
            min_relevance (float): Minimum ``overall_score`` threshold (default 7.0).
            active_profile (Optional[str]): Optional explicit profile name.
            render (bool): When True, render the quadrant summary table.
            force_reappraise (bool): When True, re-appraise every candidate
                (ignoring existing ``quality_score``). When False (default),
                appraise only uncached candidates and fall back to displaying
                the existing distribution when none remain.

        Returns:
            List[Dict[str, Any]]: One summary dict per successfully appraised
                paper, each carrying ``paper_id``, ``title``, ``relevance``,
                ``quality_score``, and ``evidence_quadrant``.
        """
        db = self._ensure_db_manager()
        if active_profile:
            from src.core.database_manager import DatabaseManager
            root = _resolve_project_root()
            db_path = os.path.join(root, "_profiles", active_profile, "talos_research.db")
            db = DatabaseManager(db_path=db_path)
        if db is None:
            return []

        # -- v5.17.0: track the active profile and auto-compile the
        # domain-specialized auditor skills before a swarm batch. --
        self._active_profile = active_profile
        if self.appraisal_mode == "swarm":
            try:
                from src.prisma.quality_swarm import SkillCompiler
                SkillCompiler(
                    ai_manager=self._ensure_ai_manager(),
                    profile_name=active_profile,
                ).compile_profile_skills(active_profile)
            except Exception:
                # -- Auditors degrade to canonical templates / keywords. --
                pass

        # -- v5.17.1: UX transparency & force re-appraisal. The default path
        # selects only uncached candidates; the force path re-selects every
        # candidate and overwrites the persisted quality columns in WAL. --
        if force_reappraise:
            rows = db.execute_query(
                "SELECT id, title, abstract, overall_score FROM papers "
                "WHERE overall_score >= ? "
                "ORDER BY overall_score DESC",
                (float(min_relevance),),
                fetch_all=True,
            ) or []
            papers = [
                {
                    "id": row[0],
                    "title": row[1],
                    "abstract": row[2],
                    "overall_score": row[3],
                }
                for row in rows
            ]
            if not papers:
                return []
            self._get_console().print(
                "[bold yellow]Notice:[/bold yellow] Force re-appraising all "
                f"{len(papers)} candidate papers with {self.appraisal_mode} mode..."
            )
        else:
            rows = db.execute_query(
                "SELECT id, title, abstract, overall_score FROM papers "
                "WHERE overall_score >= ? AND quality_score IS NULL "
                "ORDER BY overall_score DESC",
                (float(min_relevance),),
                fetch_all=True,
            ) or []
            papers = [
                {
                    "id": row[0],
                    "title": row[1],
                    "abstract": row[2],
                    "overall_score": row[3],
                }
                for row in rows
            ]
            if not papers:
                return self._render_existing_quadrant_distribution(
                    db, min_relevance, render
                )

        max_workers, semaphore = _resolve_batch_concurrency()
        max_workers = max(1, min(max_workers, len(papers)))
        results: List[Dict[str, Any]] = []

        def _appraise_one(paper: Dict[str, Any]):
            if semaphore is not None:
                with semaphore:
                    result = self.appraise_paper(
                        paper, relevance_score=float(paper.get("overall_score") or 0.0)
                    )
            else:
                result = self.appraise_paper(
                    paper, relevance_score=float(paper.get("overall_score") or 0.0)
                )
            if result is not None:
                # -- v5.17.0: persist the extended swarm payload (rubric plus
                # appraisal mode, inter-auditor kappa, and critiques). --
                payload = result.rubric.model_dump()
                payload["appraisal_mode"] = result.appraisal_mode
                if result.swarm_kappa is not None:
                    payload["swarm_kappa"] = float(result.swarm_kappa)
                if result.auditor_critiques:
                    payload["auditor_critiques"] = dict(result.auditor_critiques)
                rubric_json = json.dumps(payload, ensure_ascii=False)
                db.update_paper_quality(
                    int(paper["id"]),
                    float(result.quality_score),
                    rubric_json,
                    str(result.evidence_quadrant),
                )
                summary = {
                    "paper_id": int(paper["id"]),
                    "title": paper.get("title") or "(untitled study)",
                    "relevance": float(paper.get("overall_score") or 0.0),
                    "quality_score": float(result.quality_score),
                    "evidence_quadrant": str(result.evidence_quadrant),
                    "appraisal_mode": result.appraisal_mode,
                }
                if result.swarm_kappa is not None:
                    summary["swarm_kappa"] = float(result.swarm_kappa)
                return summary
            return None

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(_appraise_one, p) for p in papers]
            for future in as_completed(futures):
                try:
                    outcome = future.result()
                except Exception:
                    outcome = None
                if outcome is not None:
                    results.append(outcome)

        if render and results:
            self.render_quadrant_summary(results)
        return results

    def _get_console(self) -> Any:
        """Return a lazily-created Rich console for user-facing messages.

        Returns:
            Any: A ``rich.console.Console`` instance.
        """
        if self._console is None:
            from rich.console import Console
            self._console = Console()
        return self._console

    def _render_existing_quadrant_distribution(
        self,
        db: Any,
        min_relevance: float,
        render: bool = True,
    ) -> List[Dict[str, Any]]:
        """Render the persisted quadrant distribution when nothing is uncached.

        Invoked when ``force_reappraise=False`` and every candidate already
        carries a ``quality_score``. Instead of silently exiting, this renders an
        informative Rich panel and re-projects the persisted ``evidence_quadrant``
        values onto the 2D Evidence Decision Plane, guaranteeing idempotent,
        deterministic feedback for repeated appraisal invocations.

        Args:
            db (Any): The active-profile ``DatabaseManager``.
            min_relevance (float): Minimum ``overall_score`` threshold.
            render (bool): When True, render the quadrant summary table.

        Returns:
            List[Dict[str, Any]]: Summary dicts reconstructed from persisted
                quadrant values (``swarm_kappa`` is absent because it is not
                recoverable from the stored columns).
        """
        rows = db.execute_query(
            "SELECT id, evidence_quadrant, overall_score, quality_score "
            "FROM papers WHERE overall_score >= ? "
            "ORDER BY overall_score DESC",
            (float(min_relevance),),
            fetch_all=True,
        ) or []
        total_candidates = len(rows)
        summaries: List[Dict[str, Any]] = []
        for row in rows:
            summaries.append({
                "paper_id": int(row[0]),
                "evidence_quadrant": str(row[1] or "METHODOLOGICAL_NOISE"),
                "relevance": float(row[2] or 0.0),
                "quality_score": float(row[3] or 0.0),
            })

        from rich.panel import Panel

        info = (
            "[bold cyan]Information:[/bold cyan] All "
            f"{total_candidates} candidate papers "
            f"(overall_score >= {min_relevance}) have already been appraised. "
            "Displaying existing 2D Evidence Quadrant distribution."
        )
        self._get_console().print(
            Panel(info, border_style="cyan", title="[bold]Quality Appraisal[/bold]")
        )

        if render and summaries:
            self.render_quadrant_summary(summaries)
        return summaries

    def render_quadrant_summary(self, results: List[Dict[str, Any]]):
        """Render the 2D quadrant distribution as a Rich table.

        Args:
            results (List[Dict[str, Any]]): Appraisal summary dictionaries each
                carrying an ``evidence_quadrant`` key.

        Returns:
            Optional[rich.table.Table]: The rendered table, or ``None`` when
                Rich is unavailable.
        """
        try:
            from rich.console import Console
            from rich.table import Table
        except ImportError:
            return None

        if self._console is None:
            self._console = Console()

        counts = {q: 0 for q in (
            "ELITE_FOUNDATIONAL", "IDEA_MINE",
            "METHODOLOGICAL_EXEMPLAR", "METHODOLOGICAL_NOISE",
        )}
        for result in results:
            quadrant = result.get("evidence_quadrant", "METHODOLOGICAL_NOISE")
            if quadrant in counts:
                counts[quadrant] += 1

        table = Table(
            title="PRISMA Quality Appraisal -- 2D Evidence Quadrant Distribution",
            header_style="bold bright_cyan",
        )
        table.add_column("Quadrant", style="bold white", no_wrap=True)
        table.add_column("Studies", style="bold cyan", justify="right")
        table.add_column("Interpretation", style="white")

        # -- v5.17.0: report mean inter-auditor agreement in swarm mode. --
        kappas = [float(r["swarm_kappa"]) for r in results
                  if r.get("swarm_kappa") is not None]

        descriptions = {
            "ELITE_FOUNDATIONAL": "High relevance and high rigor (S_rel >= 7.0, S_qual >= 7.5).",
            "IDEA_MINE": "High relevance but weak rigor (S_rel >= 7.0, S_qual < 7.5).",
            "METHODOLOGICAL_EXEMPLAR": "Low relevance but strong rigor (S_rel < 7.0, S_qual >= 7.5).",
            "METHODOLOGICAL_NOISE": "Low relevance and low rigor (S_rel < 7.0, S_qual < 7.5).",
        }
        for quadrant, description in descriptions.items():
            table.add_row(quadrant, str(counts[quadrant]), description)

        self._console.print(table)
        if kappas:
            self._console.print(
                "[bright_cyan]Mean inter-auditor agreement "
                f"(Fleiss kappa_qual): {sum(kappas) / len(kappas):.3f} "
                f"across {len(kappas)} swarm-appraised studies.[/bright_cyan]"
            )
        return table

    def run(self, min_relevance: float = 7.0,
            active_profile: Optional[str] = None,
            force_reappraise: bool = False) -> List[Dict[str, Any]]:
        """Convenience wrapper that runs the batch appraisal and renders it.

        Args:
            min_relevance (float): Minimum ``overall_score`` threshold.
            active_profile (Optional[str]): Optional explicit profile name.
            force_reappraise (bool): When True, re-appraise every candidate
                regardless of prior ``quality_score`` (v5.17.1).

        Returns:
            List[Dict[str, Any]]: The appraisal summary dictionaries.
        """
        return self.appraise_candidates_batch(
            min_relevance=min_relevance,
            active_profile=active_profile,
            render=True,
            force_reappraise=force_reappraise,
        )


# ---------------------------------------------------------------------------
# -- Standalone CLI Entrypoint --
# ---------------------------------------------------------------------------

def main(argv: Optional[List[str]] = None) -> int:
    """Standalone entrypoint for batch Kitchenham quality appraisal.

    Args:
        argv (Optional[List[str]]): Command-line arguments following the script.

    Returns:
        int: Process exit code (0 on success).
    """
    import argparse

    parser = argparse.ArgumentParser(
        description="TALOS PRISMA Quality Appraisal (Kitchenham 2007) batch engine."
    )
    parser.add_argument("--min-score", type=float, default=7.0,
                        help="Minimum overall_score threshold (default: 7.0).")
    parser.add_argument("--profile", default=None,
                        help="Optional explicit profile name.")
    parser.add_argument("--swarm", action="store_true",
                        help="Forensic mode: run the Tier-2 four-auditor "
                             "quality swarm instead of the fast single "
                             "screener (v5.17.0).")
    parser.add_argument("--compile-skills", action="store_true",
                        help="Compile the domain-specialized auditor skills "
                             "for the profile and exit (v5.17.0).")
    parser.add_argument("--force", action="store_true",
                        help="Force re-appraisal of already-appraised "
                             "candidates, or force skill recompilation with "
                             "--compile-skills.")
    args = parser.parse_args(argv)

    if args.compile_skills:
        from src.prisma.quality_swarm import SkillCompiler
        path = SkillCompiler().compile_profile_skills(
            profile_name=args.profile,
            force_recompile=bool(args.force),
        )
        print(f"[OK] Profile auditor skills compiled under: {path}")
        return 0

    mode = "swarm" if args.swarm else "single"
    appraiser = PrismaQualityAppraiser(appraisal_mode=mode)
    results = appraiser.run(
        min_relevance=args.min_score,
        active_profile=args.profile,
        force_reappraise=bool(args.force),
    )
    if not results:
        print("No uncached candidate papers matched the appraisal threshold.")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
