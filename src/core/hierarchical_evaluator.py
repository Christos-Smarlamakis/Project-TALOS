# -*- coding: utf-8 -*-
#  Project TALOS
#  Copyright (C) 2026 Christos Smarlamakis
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Affero General Public License as
#  published by the Free Software Foundation, either version 3 of the
#  License, or (at your option) any later version.
#
#  For commercial licensing, please contact the author.

"""
Module: hierarchical_evaluator.py
Project: TALOS v5.20.0
Description:
    Two-Stage Rigor Decoupling engine for TALOS. Replaces the fragmented
    multi-tier screening logic with a single deterministic pipeline that
    separates cheap semantic relevance screening from expensive
    methodological rigor appraisal:

      Stage 1 (Fast Relevance Sieve): a lightweight local fast-edge model
        (``llama3.1:8b``) scores the paper's preliminary semantic relevance
        ($S_{rel}^{prelim}$) cheaply. Papers that clearly miss the research
        framework are rejected immediately with zero heavy compute.

      Escalation Gate: when $S_{rel}^{prelim} >= escalation_threshold$
        (default 6.0), the paper is promoted to the Heavy Reasoning tier
        (local ``qwen2.5:14b`` GPU or a cloud reasoning model such as
        ``deepseek-reasoner``) which executes a Dual-Audit:

          1. Faceted Deep Relevance Calibration ($S_{rel}^{calibrated}$) --
             the heavy tier re-scores the paper, verifying the specific
             swarm algorithms (HMADRL, Dec-POMDP, QMIX) and GNN
             architectures (ST-GNN, ST-GAT) against the research framework.

          2. Kitchenham (2007) Quality Appraisal ($S_{qual}$) -- the six
             question rubric $Q_1..Q_6$ is audited via ``PrismaQualityAppraiser``,
             producing a validated ``KitchenhamRubric`` and a 2D Evidence
             Quadrant classification.

    Key design decisions:
    - The engine is decoupled from persistence: it returns structured verdict
      dictionaries; callers decide how to persist them.
    - Stage 1 always runs first (cheap, local); Stage 2 is dispatched only for
      the subset surviving the escalation gate, keeping GPU/cloud spend
      proportional to signal.
    - The 2D Evidence Quadrant (ELITE_FOUNDATIONAL, IDEA_MINE,
      METHODOLOGICAL_EXEMPLAR, METHODOLOGICAL_NOISE) is computed from the
      decoupled ($S_{rel}^{calibrated}$, $S_{qual}$) pair.
    - ``evaluate_batch`` bounds concurrency behind ``threading.Semaphore(2)``
      to protect the shared local GPU VRAM budget.

Dependencies:
    - threading: VRAM-guard semaphore for the concurrent batch pool.
    - concurrent.futures.ThreadPoolExecutor: worker pool for batch scoring.
    - config.settings: canonical local heavy/fast model identifiers.
    - src.core.ai_manager.AIManager: underlying multi-provider LLM executor.
    - src.prisma.quality_appraisal: Kitchenham 2007 appraisal + quadrant map
      (imported lazily to avoid a startup-time coupling).
"""
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List, Optional

try:
    from config.settings import (
        HEAVY_REASONING_MODEL,
        LOCAL_GPU_MODEL,
        LOCAL_HEAVY_MODEL,
    )
except ImportError:  # pragma: no cover - defensive fallback
    HEAVY_REASONING_MODEL = "qwen2.5:14b"
    LOCAL_GPU_MODEL = "llama3.1:8b"
    LOCAL_HEAVY_MODEL = "qwen2.5:14b"


class HierarchicalEvaluationEngine:
    """Two-tier paper evaluation engine with an escalation gate.

    Attributes:
        ai_manager: The configured ``AIManager`` used to execute LLM scoring.
        escalation_threshold (float): The $S_{rel}$ threshold at or above
            which a paper is escalated to the heavy reasoning tier.
        fast_model (str): Identifier of the fast screening model.
        heavy_model (str): Identifier of the heavy reasoning model.
    """

    def __init__(self, ai_manager: Any, escalation_threshold: float = 6.0):
        """Initialize the engine with an AI manager and threshold.

        Args:
            ai_manager: A configured ``AIManager`` instance.
            escalation_threshold (float): $S_{rel}$ escalation threshold.
        """
        self.ai_manager = ai_manager
        self.escalation_threshold = float(escalation_threshold)
        self.fast_model = LOCAL_GPU_MODEL
        self.heavy_model = LOCAL_HEAVY_MODEL or HEAVY_REASONING_MODEL

    # ------------------------------------------------------------------
    # -- Score extraction helpers --
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_relevance(evaluation: Optional[Dict[str, Any]]) -> float:
        """Extract the semantic relevance score $S_{rel}$ from an evaluation.

        The structured evaluation schema emits ``overall_score`` as the
        weighted four-layer relevance. When that key is absent, the method
        falls back to the arithmetic mean of the four layer scores, and
        finally to ``0.0`` when the evaluation is unusable.

        Args:
            evaluation (dict or None): Structured JSON evaluation.

        Returns:
            float: The relevance score in the range [0.0, 10.0].
        """
        if not evaluation:
            return 0.0
        overall = evaluation.get("overall_score")
        if isinstance(overall, (int, float)):
            return float(overall)
        scores = evaluation.get("scores") or {}
        if isinstance(scores, dict):
            numeric = [v for v in scores.values() if isinstance(v, (int, float))]
            if numeric:
                return float(sum(numeric) / len(numeric))
        return 0.0

    @staticmethod
    def _extract_quality(evaluation: Optional[Dict[str, Any]],
                         fallback_relevance: float = 0.0) -> float:
        """Extract the Kitchenham-inspired methodological quality $S_{qual}$.

        Prefers an explicit ``quality_score`` / ``s_qual`` key emitted by the
        deep tier. When absent, the deep tier's own ``overall_score`` is used
        as a proxy, falling back to the fast-tier relevance score.

        Args:
            evaluation (dict or None): Deep-tier structured evaluation.
            fallback_relevance (float): Fallback score when quality is absent.

        Returns:
            float: The quality score in the range [0.0, 10.0].
        """
        if not evaluation:
            return fallback_relevance
        for key in ("quality_score", "s_qual", "quality"):
            value = evaluation.get(key)
            if isinstance(value, (int, float)):
                return float(value)
        return HierarchicalEvaluationEngine._extract_relevance(evaluation)

    @staticmethod
    def _paper_content(paper: Dict[str, Any]) -> str:
        """Build the title + abstract prompt body for a standardized paper.

        Args:
            paper (dict): Standardized paper dictionary.

        Returns:
            str: Combined title/abstract text for LLM scoring.
        """
        title = paper.get("title", "")
        abstract = paper.get("abstract", "")
        return f"Title: {title}\nAbstract: {abstract}"

    @staticmethod
    def _calibrate_relevance(deep_evaluation: Optional[Dict[str, Any]],
                             fallback: float) -> float:
        """Extract the faceted calibrated relevance $S_{rel}^{calibrated}$.

        The heavy reasoning tier re-scores the paper against the research
        framework's specific swarm algorithms (HMADRL, Dec-POMDP, QMIX) and
        GNN architectures (ST-GNN, ST-GAT), calibrating the preliminary
        fast-tier relevance. Falls back to the fast-tier score when the deep
        tier is unavailable.

        Args:
            deep_evaluation (dict or None): Heavy-tier structured evaluation.
            fallback (float): Preliminary $S_{rel}$ from the fast sieve.

        Returns:
            float: The calibrated relevance score in [0.0, 10.0].
        """
        if not deep_evaluation:
            return fallback
        calibrated = HierarchicalEvaluationEngine._extract_relevance(deep_evaluation)
        return calibrated if calibrated > 0.0 else fallback

    def _appraise_quality(self, paper: Dict[str, Any],
                          s_rel_calibrated: float) -> Optional[tuple]:
        """Run the Kitchenham (2007) quality appraisal via PrismaQualityAppraiser.

        Audits the six questions $Q_1..Q_6$ and returns the decoupled
        methodological quality $S_{qual}$, the validated rubric JSON, the 2D
        Evidence Quadrant, and the critique rationale.

        Args:
            paper (dict): Standardized paper dictionary.
            s_rel_calibrated (float): Calibrated relevance for quadrant mapping.

        Returns:
            Optional[tuple]: ``(s_qual, rubric_json, quadrant, critique)`` or
                ``None`` when the appraisal backend is unreachable.
        """
        try:
            from src.prisma.quality_appraisal import PrismaQualityAppraiser
        except Exception:
            return None
        try:
            appraiser = PrismaQualityAppraiser(
                ai_manager=self.ai_manager, appraisal_mode="single")
            result = appraiser.appraise_paper(
                paper, relevance_score=float(s_rel_calibrated))
        except Exception:
            return None
        if result is None:
            return None
        rubric_json = result.rubric.model_dump_json()
        critique = getattr(result.rubric, "critique_rationale", "") or ""
        return (
            float(result.quality_score),
            rubric_json,
            str(result.evidence_quadrant),
            critique,
        )

    @staticmethod
    def _map_quadrant(relevance: float, quality: float) -> str:
        """Map a (relevance, quality) pair onto the 2D Evidence Quadrant.

        Lazily imports the canonical ``map_evidence_quadrant`` from the PRISMA
        quality module, falling back to the static threshold rules when the
        module is unavailable.

        Args:
            relevance (float): Calibrated relevance $S_{rel}^{calibrated}$.
            quality (float): Methodological quality $S_{qual}$.

        Returns:
            str: One of the four quadrant identifiers.
        """
        try:
            from src.prisma.quality_appraisal import map_evidence_quadrant
            return map_evidence_quadrant(float(relevance), float(quality))
        except Exception:
            if relevance >= 7.0 and quality >= 7.5:
                return "ELITE_FOUNDATIONAL"
            if relevance >= 7.0:
                return "IDEA_MINE"
            if quality >= 7.5:
                return "METHODOLOGICAL_EXEMPLAR"
            return "METHODOLOGICAL_NOISE"

    # ------------------------------------------------------------------
    # -- Core evaluation methods --
    # ------------------------------------------------------------------

    def evaluate_paper(self, paper: Dict[str, Any],
                       escalation_threshold: Optional[float] = None) -> Dict[str, Any]:
        """Evaluate a single paper through the Two-Stage Rigor Decoupling pipeline.

        Stage 1 (Fast Relevance Sieve): the paper's title and abstract are
        scored by the fast edge model via ``AIManager.evaluate_paper_json``
        with ``model_type='flash'``, yielding the preliminary relevance
        $S_{rel}^{prelim}$.

        Escalation Gate:
            - $S_{rel}^{prelim} < threshold$: return a fast rejection verdict
              (``is_accepted=False``, ``escalated=False``,
              ``evidence_quadrant='METHODOLOGICAL_NOISE'``,
              ``tier='fast_local'``) with ``overall_score = S_rel_prelim``.
            - $S_{rel}^{prelim} >= threshold$: dispatch the Dual-Audit on the
              heavy tier (``model_type='pro'``):
                1. Faceted Deep Relevance Calibration -> $S_{rel}^{calibrated}$.
                2. Kitchenham (2007) Quality Appraisal -> $S_{qual}$ + rubric +
                   2D Evidence Quadrant.
              Return a deep verdict (``is_accepted = S_rel_calibrated >= 6.0``,
              ``escalated=True``, ``tier='heavy_reasoning'``).

        Args:
            paper (dict): Standardized paper dictionary with ``title`` and
                optionally ``abstract``.
            escalation_threshold (float, optional): Per-call override of the
                instance threshold.

        Returns:
            dict: A structured verdict dictionary (see method docstring).
        """
        threshold = (self.escalation_threshold if escalation_threshold is None
                     else float(escalation_threshold))
        content = self._paper_content(paper)

        # -- Tier 1: Fast Screening Sieve (local, cheap) --
        fast_evaluation = self.ai_manager.evaluate_paper_json(content, model_type="flash")
        s_rel = self._extract_relevance(fast_evaluation)

        # -- Escalation Gate --
        if s_rel < threshold:
            return {
                "paper": paper,
                "is_accepted": False,
                "escalated": False,
                "overall_score": s_rel,
                "quality_score": None,
                "quality_rubric_json": None,
                "evidence_quadrant": "METHODOLOGICAL_NOISE",
                "critique": None,
                "tier": "fast_local",
                "fast_evaluation": fast_evaluation,
                "deep_evaluation": None,
                "key_contributions": None,
            }

        # -- Stage 2: Heavy Reasoning Dual-Audit (local qwen2.5:14b or cloud) --
        deep_evaluation = self.ai_manager.evaluate_paper_json(content, model_type="pro")
        s_rel_calibrated = self._calibrate_relevance(deep_evaluation, fallback=s_rel)

        # -- Dual-Audit leg 2: Kitchenham 2007 quality appraisal --
        quality = self._appraise_quality(paper, s_rel_calibrated)
        if quality is not None:
            s_qual, rubric_json, quadrant, critique = quality
        else:
            s_qual = self._extract_quality(deep_evaluation,
                                           fallback_relevance=s_rel_calibrated)
            quadrant = self._map_quadrant(s_rel_calibrated, s_qual)
            rubric_json = None
            critique = ((deep_evaluation or {}).get("reasoning")
                        or (deep_evaluation or {}).get("critique"))

        return {
            "paper": paper,
            "is_accepted": s_rel_calibrated >= 6.0,
            "escalated": True,
            "overall_score": s_rel_calibrated,
            "quality_score": s_qual,
            "quality_rubric_json": rubric_json,
            "evidence_quadrant": quadrant,
            "critique": critique,
            "tier": "heavy_reasoning",
            "fast_evaluation": fast_evaluation,
            "deep_evaluation": deep_evaluation,
            "key_contributions": (deep_evaluation or {}).get("contribution"),
        }

    def evaluate_batch(self, papers: List[Dict[str, Any]],
                       threshold: Optional[float] = None) -> List[Dict[str, Any]]:
        """Evaluate a batch of papers concurrently through the escalation pipeline.

        Concurrency is managed with a ``ThreadPoolExecutor`` and a bounded
        ``threading.Semaphore(2)`` so that the shared local GPU VRAM budget is
        never exhausted, while preserving the original input order in the
        returned verdict list.

        Args:
            papers (list of dict): Standardized paper dictionaries.
            threshold (float, optional): Per-batch escalation threshold.

        Returns:
            list of dict: Ordered verdict dictionaries preserving input order.
        """
        if not papers:
            return []

        semaphore = threading.Semaphore(2)

        def _evaluate_one(paper: Dict[str, Any]) -> Dict[str, Any]:
            with semaphore:
                return self.evaluate_paper(paper, escalation_threshold=threshold)

        workers = max(1, min(2, len(papers)))
        results: List[Dict[str, Any]] = [{} for _ in papers]
        with ThreadPoolExecutor(max_workers=workers) as executor:
            future_to_index = {
                executor.submit(_evaluate_one, paper): index
                for index, paper in enumerate(papers)
            }
            for future in as_completed(future_to_index):
                index = future_to_index[future]
                try:
                    results[index] = future.result()
                except Exception as exc:  # pragma: no cover - defensive isolation
                    results[index] = {
                        "paper": papers[index],
                        "is_accepted": False,
                        "escalated": False,
                        "overall_score": 0.0,
                        "quality_score": None,
                        "quality_rubric_json": None,
                        "evidence_quadrant": "METHODOLOGICAL_NOISE",
                        "critique": None,
                        "tier": "fast_local",
                        "fast_evaluation": None,
                        "deep_evaluation": None,
                        "key_contributions": None,
                        "error": str(exc),
                    }
        return results
