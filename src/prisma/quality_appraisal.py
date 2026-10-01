# -*- coding: utf-8 -*-
"""
Module: quality_appraisal.py
Project: TALOS v5.16.0
Description:
    Standardized PRISMA Quality Appraisal engine implementing the Kitchenham et
    al. (2007) guidelines for systematic literature reviews in software
    engineering. This module formalizes a six-question, three-point categorical
    rubric ({0.0, 0.5, 1.0}) and decouples Semantic Relevance (``S_rel``, the
    existing four-layer ``overall_score``) from Methodological Quality
    (``S_qual``, computed here) onto a two-dimensional Evidence Decision Plane.

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
    """

    quality_score: float = Field(ge=0.0, le=10.0)
    rubric: KitchenhamRubric
    evidence_quadrant: QUADRANTS


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
    """

    def __init__(self, ai_manager: Optional[Any] = None,
                 db_manager: Optional[Any] = None) -> None:
        """Initialize the appraiser with optional pre-built dependencies.

        Args:
            ai_manager (Optional[Any]): Pre-built ``AIManager`` or ``None``.
            db_manager (Optional[Any]): Pre-built ``DatabaseManager`` or ``None``.
        """
        self.ai_manager = ai_manager
        self.db_manager = db_manager
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

    def appraise_candidates_batch(
        self,
        min_relevance: float = 7.0,
        active_profile: Optional[str] = None,
        render: bool = True,
    ) -> List[Dict[str, Any]]:
        """Appraise every uncached candidate paper in the active database.

        Queries the active-profile SQLite database for papers whose
        ``overall_score`` meets ``min_relevance`` and whose ``quality_score`` is
        still ``NULL``, then appraises them concurrently via ``ThreadPoolExecutor``
        with the VRAM-bounded concurrency budget. Each successful appraisal is
        persisted immediately through ``update_paper_quality``.

        Args:
            min_relevance (float): Minimum ``overall_score`` threshold (default 7.0).
            active_profile (Optional[str]): Optional explicit profile name.
            render (bool): When True, render the quadrant summary table.

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
            return []

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
                rubric_json = result.rubric.model_dump_json()
                db.update_paper_quality(
                    int(paper["id"]),
                    float(result.quality_score),
                    rubric_json,
                    str(result.evidence_quadrant),
                )
                return {
                    "paper_id": int(paper["id"]),
                    "title": paper.get("title") or "(untitled study)",
                    "relevance": float(paper.get("overall_score") or 0.0),
                    "quality_score": float(result.quality_score),
                    "evidence_quadrant": str(result.evidence_quadrant),
                }
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

        descriptions = {
            "ELITE_FOUNDATIONAL": "High relevance and high rigor (S_rel >= 7.0, S_qual >= 7.5).",
            "IDEA_MINE": "High relevance but weak rigor (S_rel >= 7.0, S_qual < 7.5).",
            "METHODOLOGICAL_EXEMPLAR": "Low relevance but strong rigor (S_rel < 7.0, S_qual >= 7.5).",
            "METHODOLOGICAL_NOISE": "Low relevance and low rigor (S_rel < 7.0, S_qual < 7.5).",
        }
        for quadrant, description in descriptions.items():
            table.add_row(quadrant, str(counts[quadrant]), description)

        self._console.print(table)
        return table

    def run(self, min_relevance: float = 7.0,
            active_profile: Optional[str] = None) -> List[Dict[str, Any]]:
        """Convenience wrapper that runs the batch appraisal and renders it.

        Args:
            min_relevance (float): Minimum ``overall_score`` threshold.
            active_profile (Optional[str]): Optional explicit profile name.

        Returns:
            List[Dict[str, Any]]: The appraisal summary dictionaries.
        """
        return self.appraise_candidates_batch(
            min_relevance=min_relevance,
            active_profile=active_profile,
            render=True,
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
    args = parser.parse_args(argv)

    appraiser = PrismaQualityAppraiser()
    results = appraiser.run(
        min_relevance=args.min_score,
        active_profile=args.profile,
    )
    if not results:
        print("No uncached candidate papers matched the appraisal threshold.")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
