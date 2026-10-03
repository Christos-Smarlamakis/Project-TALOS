# -*- coding: utf-8 -*-
"""
Module: quality_swarm.py
Project: TALOS v5.20.0
Description:
    Tier-2 Forensic Quality Swarm for the Two-Tier Hierarchical Swarm
    Architecture. Where the Tier-1 swarm (``swarm_evaluators.py``) performs
    thematic INCLUDE/EXCLUDE screening during PRISMA-ScR selection, this module
    performs the downstream forensic quality audit: four specialized skill
    auditors (``TheoryAuditor`` for Kitchenham Q1, ``BenchmarkAuditor`` for
    Q3-Q4, ``OpenScienceAuditor`` for Q5-Q6, and ``OperationalAuditor`` for
    Q2) each load a domain-specialized skill file compiled per profile and
    emit ternary scores plus targeted critiques.

    The ``SkillCompiler`` resolves the four canonical domain-agnostic templates
    under ``src/prisma/skills/templates/``, injects the active profile's
    ``research_topic``, ``inclusion_criteria``, and ``exclusion_criteria`` into
    the ``{{RESEARCH_DOMAIN}}`` / ``{{DOMAIN_CONSTRAINTS}}`` placeholders, and
    optionally refines the result with the hardware-advised heavy model. The
    ``SmartSectionSlicer`` extracts targeted text slices (Code Availability,
    Methodology, Experiments, Discussion/Limitations) to minimize the token
    footprint per auditor. The ``KitchenhamQualitySynthesizer`` dispatches the
    four auditors concurrently (bounded by ``threading.Semaphore(2)`` on the
    local GPU, ``max_workers=4`` on the Cloud Mesh), aggregates the six ternary
    scores into ``S_qual = (10/6) * sum(Q_i)``, computes the inter-auditor
    Fleiss agreement ``kappa_qual``, maps the 2D evidence quadrant, and
    synthesizes a unified forensic audit narrative.

Dependencies:
    - src.prisma.dspy_signatures.extract_json_payload: Robust JSON recovery.
    - src.prisma.quality_appraisal: KitchenhamRubric, map_evidence_quadrant,
        and the ternary snap-to-grid normalizer (rubric invariant reuse).
    - src.prisma.swarm_evaluators: calculate_cohens_kappa (Fleiss
        generalization) and keyword-hit helper (Tier-1 statistics reuse).
    - src.core.hardware_advisor (lazy): Hardware-aware heavy-model selection
        for the one-time skill compilation pass.
    - src.core.profile_manager (lazy): Active profile resolution.
    - pydantic: BaseModel/Field/field_validator for typed audit results.
"""

import json
import os
import re
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, Field, field_validator

from src.prisma.dspy_signatures import extract_json_payload
from src.prisma.quality_appraisal import (
    KitchenhamRubric,
    map_evidence_quadrant,
    _normalize_ternary,
)
from src.prisma.swarm_evaluators import calculate_cohens_kappa, _keyword_hits


# ---------------------------------------------------------------------------
# -- Project Root, Template Registry & Concurrency Budget --
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


# Canonical mapping of auditor keys to template and compiled-skill filenames.
# The templates are domain-agnostic; the compiled files are profile-bound.
SKILL_REGISTRY: Dict[str, Dict[str, str]] = {
    "theory": {
        "template": "theory_auditor.template.md",
        "compiled": "theory_auditor.md",
    },
    "empirical": {
        "template": "empirical_auditor.template.md",
        "compiled": "empirical_auditor.md",
    },
    "openscience": {
        "template": "openscience_auditor.template.md",
        "compiled": "openscience_auditor.md",
    },
    "operational": {
        "template": "operational_auditor.template.md",
        "compiled": "operational_auditor.md",
    },
}


def _templates_dir() -> str:
    """Return the absolute path of the domain-agnostic template directory.

    Returns:
        str: Absolute path to ``src/prisma/skills/templates``.
    """
    return os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "skills", "templates")


def _profile_skills_dir(profile_name: str) -> str:
    """Resolve the compiled-skills directory for a research profile.

    Args:
        profile_name (str): The profile workspace name.

    Returns:
        str: Absolute path to ``_profiles/<profile_name>/skills``.
    """
    return os.path.join(_resolve_project_root(), "_profiles",
                        profile_name, "skills")


def _default_profile_name() -> str:
    """Resolve the active profile name with a safe ``default`` fallback.

    Returns:
        str: The active profile name from the ProfileManager marker file.
    """
    try:
        from src.core.profile_manager import get_active_profile_name
        name = get_active_profile_name()
        if name:
            return str(name)
    except Exception:
        pass
    marker = os.path.join(_resolve_project_root(), "_profiles",
                          "active_profile.txt")
    try:
        if os.path.exists(marker):
            with open(marker, "r", encoding="utf-8") as fh:
                name = fh.read().strip()
                if name:
                    return name
    except OSError:
        pass
    return "default"


# Global semaphore bounding concurrent local-GPU auditor calls to two permits,
# mirroring the Constitution III requirement that inference workloads leave a
# 2GB VRAM headroom on the llama3.1:8b tier.
QUALITY_SWARM_SEMAPHORE = threading.Semaphore(2)


def resolve_quality_swarm_workers() -> Tuple[int, Optional[threading.Semaphore]]:
    """Resolve the auditor concurrency budget from the network strategy.

    Local-first strategies are bounded to two concurrent auditors behind the
    module-level VRAM semaphore. Cloud-first and strict-cloud strategies may
    run all four auditors concurrently over the Universal Cloud Mesh.

    Returns:
        tuple[int, Optional[threading.Semaphore]]: (max_workers, semaphore).
    """
    strategy = os.getenv("TALOS_NETWORK_STRATEGY", "strict_local").strip().lower()
    if strategy in ("cloud_first", "strict_cloud"):
        return 4, None
    return 2, QUALITY_SWARM_SEMAPHORE


# ---------------------------------------------------------------------------
# -- Skill Compiler (Domain-Agnostic Templates -> Profile-Bound Skills) --
# ---------------------------------------------------------------------------

class SkillCompiler:
    """One-time compiler of domain-specialized auditor skill files.

    Reads the four canonical domain-agnostic templates from
    ``src/prisma/skills/templates/``, injects the active profile's research
    domain and inclusion/exclusion constraints, and writes the compiled
    ``*.md`` skill files into ``_profiles/<profile_name>/skills/``. When an
    LLM backend is reachable, a hardware-advised heavy model (for example
    ``qwen2.5:14b`` locally or ``deepseek-reasoner`` / ``gemini-2.5-flash`` on
    the Cloud Mesh) refines each injected template into tailored audit prose;
    when offline, the deterministic placeholder injection is persisted as-is,
    preserving full air-gapped operability.

    Attributes:
        ai_manager (Optional[Any]): Optional pre-built ``AIManager`` backend.
        profile_name (Optional[str]): Explicit profile override.
    """

    def __init__(self, ai_manager: Optional[Any] = None,
                 profile_name: Optional[str] = None) -> None:
        """Initialize the compiler with optional pre-built dependencies.

        Args:
            ai_manager (Optional[Any]): Pre-built ``AIManager`` or ``None``.
            profile_name (Optional[str]): Explicit profile name override.
        """
        self.ai_manager = ai_manager
        self.profile_name = profile_name

    # -- Profile configuration loading -------------------------------------

    def _load_profile_config(self, profile_name: str) -> Dict[str, Any]:
        """Load the profile ``config.json`` with a root-level fallback.

        Args:
            profile_name (str): The profile workspace name.

        Returns:
            Dict[str, Any]: The configuration mapping, or an empty dict.
        """
        root = _resolve_project_root()
        candidates = [
            os.path.join(root, "_profiles", profile_name, "config.json"),
            os.path.join(root, "config.json"),
            os.path.join(root, "config.template.json"),
        ]
        for path in candidates:
            if os.path.exists(path):
                try:
                    with open(path, "r", encoding="utf-8") as fh:
                        return json.load(fh)
                except (json.JSONDecodeError, OSError):
                    continue
        return {}

    # -- Deterministic placeholder injection --------------------------------

    @staticmethod
    def _inject_placeholders(template_text: str,
                             config: Dict[str, Any]) -> str:
        """Inject the profile research domain and constraints into a template.

        Args:
            template_text (str): Raw template content with placeholders.
            config (Dict[str, Any]): The active profile configuration.

        Returns:
            str: The template with ``{{RESEARCH_DOMAIN}}`` and
                ``{{DOMAIN_CONSTRAINTS}}`` replaced by profile values.
        """
        domain = str(
            config.get("research_topic")
            or config.get("user_research_goal")
            or "the target research domain"
        ).strip()
        inclusion = str(config.get("inclusion_criteria") or "").strip()
        exclusion = str(config.get("exclusion_criteria") or "").strip()
        constraints_parts = []
        if inclusion:
            constraints_parts.append(f"Inclusion criteria: {inclusion}")
        if exclusion:
            constraints_parts.append(f"Exclusion criteria: {exclusion}")
        constraints = " ".join(constraints_parts) or (
            "the profile's declared inclusion and exclusion criteria"
        )
        return (template_text
                .replace("{{RESEARCH_DOMAIN}}", domain)
                .replace("{{DOMAIN_CONSTRAINTS}}", constraints))

    # -- Optional LLM refinement ---------------------------------------------

    def _select_compiler_model(self) -> str:
        """Select the hardware-advised heavy model for skill compilation.

        Returns:
            str: A human-readable model label for logging purposes.
        """
        strategy = os.getenv("TALOS_NETWORK_STRATEGY",
                             "strict_local").strip().lower()
        try:
            from src.core.hardware_advisor import HardwareModelAdvisor
            recommendations = HardwareModelAdvisor().get_recommendations()
            if strategy in ("cloud_first", "strict_cloud"):
                return str(recommendations.get("reasoning_cloud")
                           or "deepseek-reasoner")
            return str(recommendations.get("reasoning_local")
                       or "qwen2.5:14b")
        except Exception:
            return ("deepseek-reasoner"
                    if strategy in ("cloud_first", "strict_cloud")
                    else "qwen2.5:14b")

    def _polish_with_llm(self, skill_key: str, injected_text: str) -> str:
        """Refine an injected template into tailored prose via the heavy model.

        The refinement is strictly optional: any failure returns the
        deterministic injected text unchanged so compilation never fails in an
        air-gapped environment.

        Args:
            skill_key (str): The auditor key (theory/empirical/...).
            injected_text (str): Placeholder-injected template content.

        Returns:
            str: The refined skill document, or the injected text on failure.
        """
        if self.ai_manager is None:
            return injected_text
        model_label = self._select_compiler_model()
        prompt = (
            "You are a senior systematic-review methodologist. Rewrite the "
            "auditor skill document below into a tailored, domain-specialized "
            "audit checklist. Preserve the section structure, the ternary "
            "scoring anchors (0.0 / 0.5 / 1.0), and the REQUIRED OUTPUT "
            "FORMAT JSON schema EXACTLY as they are. Sharpen every criterion "
            "with concrete, verifiable checks for the declared research "
            "domain. Return ONLY the refined Markdown document.\n\n"
            f"--- SKILL DOCUMENT ({skill_key}, compiler model: {model_label}) ---\n"
            f"{injected_text}\n"
        )
        try:
            refined = self.ai_manager.analyze_generic_text(prompt)
        except Exception:
            return injected_text
        if not isinstance(refined, str):
            return injected_text
        refined = refined.strip()
        # -- Guard: the refined document must retain the JSON schema. --
        if len(refined) < 200 or '"q' not in refined:
            return injected_text
        return refined

    # -- Compilation entry point ---------------------------------------------

    def compiled_skills_exist(self, profile_name: Optional[str] = None) -> bool:
        """Check whether all four compiled skill files already exist.

        Args:
            profile_name (Optional[str]): Profile override; defaults to the
                active profile.

        Returns:
            bool: True when every compiled ``*.md`` skill file is present.
        """
        name = profile_name or self.profile_name or _default_profile_name()
        skills_dir = _profile_skills_dir(name)
        for entry in SKILL_REGISTRY.values():
            if not os.path.exists(os.path.join(skills_dir,
                                               entry["compiled"])):
                return False
        return True

    def compile_profile_skills(self, profile_name: Optional[str] = None,
                               force_recompile: bool = False) -> Path:
        """Compile the four domain-specialized skill files for a profile.

        When the compiled skills already exist and ``force_recompile`` is
        False, the method returns the directory path immediately without any
        I/O or inference (the zero-cost fast path). Otherwise each canonical
        template is read, injected with the profile's ``research_topic``,
        ``inclusion_criteria``, and ``exclusion_criteria``, optionally refined
        by the hardware-advised heavy model, and persisted under
        ``_profiles/<profile_name>/skills/``.

        Args:
            profile_name (Optional[str]): Profile override; defaults to the
                active profile.
            force_recompile (bool): When True, recompile even if the compiled
                skill files already exist.

        Returns:
            Path: The directory containing the four compiled skill files.

        Raises:
            FileNotFoundError: If the canonical template directory is missing.
        """
        name = profile_name or self.profile_name or _default_profile_name()
        skills_dir = _profile_skills_dir(name)

        # -- Zero-cost fast path: compiled skills already present. --
        if not force_recompile and self.compiled_skills_exist(name):
            return Path(skills_dir)

        templates_dir = _templates_dir()
        if not os.path.isdir(templates_dir):
            raise FileNotFoundError(
                f"Canonical skill template directory not found: {templates_dir}"
            )

        config = self._load_profile_config(name)
        os.makedirs(skills_dir, exist_ok=True)

        for skill_key, entry in SKILL_REGISTRY.items():
            template_path = os.path.join(templates_dir, entry["template"])
            with open(template_path, "r", encoding="utf-8") as fh:
                template_text = fh.read()
            injected = self._inject_placeholders(template_text, config)
            compiled = self._polish_with_llm(skill_key, injected)
            compiled_path = os.path.join(skills_dir, entry["compiled"])
            with open(compiled_path, "w", encoding="utf-8") as fh:
                fh.write(compiled)

        return Path(skills_dir)


# ---------------------------------------------------------------------------
# -- Smart Section Slicer (Token-Footprint Minimization) --
# ---------------------------------------------------------------------------

class SmartSectionSlicer:
    """Extract targeted text slices from a paper record for each auditor.

    Full papers are too large to dispatch verbatim to four concurrent
    auditors. This slicer detects canonical section boundaries with heading
    heuristics and returns only the slices relevant to each auditor's
    mandate, word-capped to roughly 300-500 words. When no section structure
    is detectable (abstract-only records), the slicer falls back to the
    title-plus-abstract prefix.
    """

    # -- Canonical section heading patterns (case-insensitive). --
    SECTION_PATTERNS: Dict[str, Tuple[str, ...]] = {
        "code_availability": (
            r"code availability", r"data availability",
            r"reproducibility", r"artifact", r"implementation details",
            r"software and data", r"open.source",
        ),
        "methodology": (
            r"method", r"approach", r"model", r"formulation",
            r"preliminaries", r"background", r"problem statement",
            r"proposed",
        ),
        "experiments": (
            r"experiment", r"result", r"evaluation", r"benchmark",
            r"ablation", r"performance", r"setup",
        ),
        "discussion_limitations": (
            r"discussion", r"limitation", r"conclusion",
            r"threats? to validity", r"future work", r"failure",
        ),
    }

    # -- Per-auditor slice targets. --
    AUDITOR_SECTIONS: Dict[str, Tuple[str, ...]] = {
        "theory": ("methodology", "discussion_limitations"),
        "empirical": ("experiments", "methodology"),
        "openscience": ("code_availability", "discussion_limitations"),
        "operational": ("methodology", "experiments"),
    }

    @staticmethod
    def _cap_words(text: str, max_words: int) -> str:
        """Cap a text block to at most ``max_words`` whitespace tokens.

        Args:
            text (str): The raw text block.
            max_words (int): Maximum number of words to retain.

        Returns:
            str: The word-capped text.
        """
        words = text.split()
        if len(words) <= max_words:
            return text.strip()
        return " ".join(words[:max_words]).strip() + " [...]"

    def _extract_sections(self, text: str) -> Dict[str, str]:
        """Split raw paper text into canonical sections by heading matches.

        Args:
            text (str): The full (or partial) paper text.

        Returns:
            Dict[str, str]: Mapping of section key to its extracted body.
        """
        sections: Dict[str, List[str]] = {key: [] for key in self.SECTION_PATTERNS}
        if not text:
            return {key: "" for key in sections}

        # -- Split on heading-like lines and attribute blocks by pattern. --
        lines = text.splitlines()
        current_key: Optional[str] = None
        for line in lines:
            stripped = line.strip().lower()
            heading_like = (
                stripped
                and len(stripped) < 90
                and not stripped.endswith(".")
                and re.match(r"^((\d+(\.\d+)*)\s+|[ivx]+\.\s+)?\S", stripped)
            )
            if heading_like:
                matched_key = None
                for key, patterns in self.SECTION_PATTERNS.items():
                    if any(re.search(p, stripped) for p in patterns):
                        matched_key = key
                        break
                if matched_key is not None:
                    current_key = matched_key
                    continue
            if current_key is not None:
                sections[current_key].append(line)

        return {key: "\n".join(block).strip() for key, block in sections.items()}

    # -- Cached PDF section windows (v5.18.0): the SmartSectionSlicer reads
    # real extracted section text whenever a local PDF has been harvested. -- #
    _CACHED_SECTION_FILES: Dict[str, str] = {
        "methodology": "methodology.txt",
        "experiments": "experiments.txt",
        "code_availability": "code_availability.txt",
        "discussion_limitations": "limitations.txt",
    }

    @staticmethod
    def _cached_section_dir(paper: Dict[str, Any]) -> Optional[str]:
        """Resolve the cached section directory for a paper, if present.

        Args:
            paper (Dict[str, Any]): Paper record with an ``id`` key.

        Returns:
            Optional[str]: Absolute cache directory, or None when absent.
        """
        pid = paper.get("id")
        if pid is None:
            return None
        project_root = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..")
        )
        cache_dir = os.path.join(project_root, "data", "fulltext_cache", str(pid))
        return cache_dir if os.path.isdir(cache_dir) else None

    def _load_cached_sections(self, paper: Dict[str, Any]) -> Dict[str, str]:
        """Load cached section text files for a paper into a keyed mapping.

        Args:
            paper (Dict[str, Any]): Paper record with an ``id`` key.

        Returns:
            Dict[str, str]: Mapping of section key to cached text (empty where
                no file exists).
        """
        cache_dir = self._cached_section_dir(paper)
        out: Dict[str, str] = {}
        if not cache_dir:
            return out
        for key, filename in self._CACHED_SECTION_FILES.items():
            path = os.path.join(cache_dir, filename)
            if os.path.exists(path):
                try:
                    with open(path, "r", encoding="utf-8") as handle:
                        out[key] = handle.read().strip()
                except OSError:
                    out[key] = ""
        return out

    def slice_for_auditor(self, auditor_key: str, paper: Dict[str, Any],
                          max_words: int = 400) -> str:
        """Return the targeted, word-capped text slice for one auditor.

        When the paper record carries a ``full_text`` field, the canonical
        sections targeted by the auditor are extracted and concatenated. When
        no sections are detectable (or only an abstract exists), the slice
        falls back to the title-plus-abstract prefix.

        Args:
            auditor_key (str): One of ``theory``, ``empirical``,
                ``openscience``, ``operational``.
            paper (Dict[str, Any]): Paper record with ``title``, ``abstract``,
                and optionally ``full_text``.
            max_words (int): Word cap for the returned slice (default 400).

        Returns:
            str: The targeted slice text, never empty when a title exists.
        """
        title = str(paper.get("title") or "(untitled study)").strip()
        abstract = str(paper.get("abstract") or "").strip()
        full_text = str(paper.get("full_text") or "").strip()

        fallback = f"Title: {title}\nAbstract: {abstract or '(no abstract)'}"
        if not full_text:
            # -- v5.18.0: read real cached PDF section text when a local PDF
            # was harvested by the Ethical Academic PDF Harvester. -- #
            cached = self._load_cached_sections(paper)
            if cached:
                cached_parts: List[str] = []
                for section_key in self.AUDITOR_SECTIONS.get(auditor_key, tuple()):
                    body = cached.get(section_key) or ""
                    if body:
                        cached_parts.append(f"[{section_key.upper()}]\n{body}")
                if cached_parts:
                    return self._cap_words("\n\n".join(cached_parts), max_words)
            return self._cap_words(fallback, max_words)

        sections = self._extract_sections(full_text)
        targets = self.AUDITOR_SECTIONS.get(auditor_key, tuple())
        parts: List[str] = []
        for section_key in targets:
            body = sections.get(section_key) or ""
            if body:
                parts.append(f"[{section_key.upper()}]\n{body}")

        if not parts:
            # -- No detectable structure: abstract-first prefix of full text. --
            merged = f"{fallback}\n\n{full_text}"
            return self._cap_words(merged, max_words)

        return self._cap_words("\n\n".join(parts), max_words)


# ---------------------------------------------------------------------------
# -- Typed Audit Result Models (Ternary Scores + Critiques) --
# ---------------------------------------------------------------------------

class TheoryAuditResult(BaseModel):
    """TheoryAuditor output for Kitchenham Q1 (aims/formulation/scope).

    Attributes:
        q1_aims_clarity (float): Ternary score in {0.0, 0.5, 1.0}.
        theory_critique (str): Forensic justification of the Q1 verdict.
    """

    q1_aims_clarity: float = Field(default=0.0)
    theory_critique: str = ""

    @field_validator("q1_aims_clarity", mode="before")
    @classmethod
    def _coerce(cls, value: Any) -> float:
        """Snap the raw score onto the strict ternary grid."""
        return _normalize_ternary(value)

    @property
    def mean_score(self) -> float:
        """Return the auditor's mean ternary score (single question)."""
        return float(self.q1_aims_clarity)


class OperationalAuditResult(BaseModel):
    """OperationalAuditor output for Kitchenham Q2 (context realism).

    Attributes:
        q2_context_realism (float): Ternary score in {0.0, 0.5, 1.0}.
        operational_critique (str): Forensic justification of the Q2 verdict.
    """

    q2_context_realism: float = Field(default=0.0)
    operational_critique: str = ""

    @field_validator("q2_context_realism", mode="before")
    @classmethod
    def _coerce(cls, value: Any) -> float:
        """Snap the raw score onto the strict ternary grid."""
        return _normalize_ternary(value)

    @property
    def mean_score(self) -> float:
        """Return the auditor's mean ternary score (single question)."""
        return float(self.q2_context_realism)


class BenchmarkAuditResult(BaseModel):
    """BenchmarkAuditor output for Kitchenham Q3 and Q4.

    Attributes:
        q3_baseline_rigor (float): Ternary score in {0.0, 0.5, 1.0}.
        q4_statistical_validity (float): Ternary score in {0.0, 0.5, 1.0}.
        benchmark_critique (str): Forensic justification of the Q3-Q4 verdicts.
    """

    q3_baseline_rigor: float = Field(default=0.0)
    q4_statistical_validity: float = Field(default=0.0)
    benchmark_critique: str = ""

    @field_validator("q3_baseline_rigor", "q4_statistical_validity",
                     mode="before")
    @classmethod
    def _coerce(cls, value: Any) -> float:
        """Snap the raw scores onto the strict ternary grid."""
        return _normalize_ternary(value)

    @property
    def mean_score(self) -> float:
        """Return the auditor's mean ternary score across Q3 and Q4."""
        return (float(self.q3_baseline_rigor)
                + float(self.q4_statistical_validity)) / 2.0


class OpenScienceAuditResult(BaseModel):
    """OpenScienceAuditor output for Kitchenham Q5 and Q6.

    Attributes:
        q5_open_reproducibility (float): Ternary score in {0.0, 0.5, 1.0}.
        q6_limitations_negative_results (float): Ternary score.
        openscience_critique (str): Forensic justification of Q5-Q6 verdicts.
    """

    q5_open_reproducibility: float = Field(default=0.0)
    q6_limitations_negative_results: float = Field(default=0.0)
    openscience_critique: str = ""

    @field_validator("q5_open_reproducibility",
                     "q6_limitations_negative_results", mode="before")
    @classmethod
    def _coerce(cls, value: Any) -> float:
        """Snap the raw scores onto the strict ternary grid."""
        return _normalize_ternary(value)

    @property
    def mean_score(self) -> float:
        """Return the auditor's mean ternary score across Q5 and Q6."""
        return (float(self.q5_open_reproducibility)
                + float(self.q6_limitations_negative_results)) / 2.0


# ---------------------------------------------------------------------------
# -- Skill Auditor Base --
# ---------------------------------------------------------------------------

class SkillAuditor:
    """Base class for the four forensic quality auditor personas.

    Each auditor loads its compiled, domain-specialized skill document from
    ``_profiles/<active>/skills/``, prompts the multi-tier ``AIManager`` with
    the skill plus a targeted text slice, recovers the JSON answer
    defensively, and validates it against its typed result model. When no
    backend is reachable, a deterministic keyword-heuristic fallback keeps the
    swarm fully operational in air-gapped environments (mirroring the Tier-1
    degradation contract of ``swarm_evaluators.py``).

    Attributes:
        name (str): Human-readable auditor identifier.
        skill_key (str): Registry key into ``SKILL_REGISTRY``.
        question_keys (Tuple[str, ...]): Kitchenham rubric fields owned.
        critique_field (str): JSON key carrying the auditor's critique.
        result_model (type): The Pydantic result model class.
        skill_text (str): The loaded compiled skill document.
        ai_manager (Optional[Any]): The multi-tier LLM backend.
    """

    name: str = "SkillAuditor"
    skill_key: str = ""
    question_keys: Tuple[str, ...] = ()
    critique_field: str = "critique"
    result_model: Any = BaseModel
    question_keywords: Dict[str, List[str]] = {}
    concern_keywords: List[str] = []

    def __init__(self, skill_text: str = "",
                 ai_manager: Optional[Any] = None) -> None:
        """Initialize the auditor with its skill document and backend.

        Args:
            skill_text (str): The compiled domain-specialized skill document.
            ai_manager (Optional[Any]): The multi-tier ``AIManager`` backend.
        """
        self.skill_text = skill_text
        self.ai_manager = ai_manager

    @classmethod
    def load_compiled_skill(cls, profile_name: Optional[str] = None) -> str:
        """Load the compiled skill document for the active profile.

        Falls back to the raw canonical template when the compiled file is
        absent, so the auditor remains functional even before compilation.

        Args:
            profile_name (Optional[str]): Profile override; defaults to the
                active profile.

        Returns:
            str: The skill document text (possibly empty on total failure).
        """
        entry = SKILL_REGISTRY.get(cls.skill_key, {})
        candidates = []
        if profile_name:
            candidates.append(os.path.join(
                _profile_skills_dir(profile_name), entry.get("compiled", "")))
        candidates.append(os.path.join(
            _templates_dir(), entry.get("template", "")))
        for path in candidates:
            try:
                if path and os.path.exists(path):
                    with open(path, "r", encoding="utf-8") as fh:
                        return fh.read()
            except OSError:
                continue
        return ""

    # -- Prompt assembly ------------------------------------------------------

    def _build_prompt(self, title: str, slice_text: str) -> str:
        """Assemble the full forensic audit prompt for one study.

        Args:
            title (str): Study title.
            slice_text (str): The targeted, word-capped text slice.

        Returns:
            str: The complete prompt sent to the LLM backend.
        """
        skill_block = self.skill_text.strip() or (
            f"You are {self.name}, a forensic quality auditor. Score each "
            "assigned Kitchenham quality question on the strict ternary "
            "scale {0.0, 0.5, 1.0}."
        )
        return (
            f"{skill_block}\n\n"
            "--- STUDY UNDER AUDIT ---\n"
            f"Title: {title}\n"
            f"{slice_text}\n\n"
            "Respond ONLY with a single valid JSON object using exactly the "
            "schema declared in the REQUIRED OUTPUT FORMAT section above."
        )

    # -- Result recovery -------------------------------------------------------

    def _result_from_json(self, data: Dict[str, Any]) -> BaseModel:
        """Recover a typed audit result from parsed LLM JSON.

        Args:
            data (Dict[str, Any]): Parsed JSON payload.

        Returns:
            BaseModel: The validated audit result model instance.
        """
        kwargs: Dict[str, Any] = {}
        for key in self.question_keys:
            kwargs[key] = data.get(key, 0.0)
        critique = data.get(self.critique_field, "")
        kwargs[self.critique_field] = str(critique).strip()
        return self.result_model(**kwargs)

    def _deterministic_audit(self, text: str) -> BaseModel:
        """Apply keyword heuristics when the LLM backend is unavailable.

        Each owned question is scored by its dedicated keyword vocabulary:
        two or more distinct hits yield 1.0, a single hit yields 0.5, and no
        hits yield 0.0. Concern terms cannot raise a score; they are noted in
        the critique for transparency.

        Args:
            text (str): The audited text (title plus slice).

        Returns:
            BaseModel: The heuristically derived audit result.
        """
        kwargs: Dict[str, Any] = {}
        notes: List[str] = []
        for key in self.question_keys:
            keywords = self.question_keywords.get(key, [])
            hits = _keyword_hits(text, keywords)
            if hits >= 2:
                kwargs[key] = 1.0
            elif hits == 1:
                kwargs[key] = 0.5
            else:
                kwargs[key] = 0.0
                notes.append(f"No {key} evidence signals detected.")
        concerns = _keyword_hits(text, self.concern_keywords)
        if concerns:
            notes.append(f"Detected {concerns} concern term(s).")
        notes.append("Deterministic keyword fallback (no LLM backend).")
        kwargs[self.critique_field] = " ".join(notes)
        return self.result_model(**kwargs)

    def audit(self, paper: Dict[str, Any], slice_text: str) -> BaseModel:
        """Audit a single study through this auditor's specialized skill.

        Args:
            paper (Dict[str, Any]): Paper record exposing ``title``.
            slice_text (str): The targeted, word-capped text slice.

        Returns:
            BaseModel: The validated audit result (LLM or deterministic).
        """
        title = str(paper.get("title") or "(untitled study)").strip()
        if self.ai_manager is not None:
            try:
                raw = self.ai_manager.analyze_generic_text(
                    self._build_prompt(title, slice_text))
                data = extract_json_payload(raw)
                if isinstance(data, dict):
                    return self._result_from_json(data)
            except Exception:
                pass
        return self._deterministic_audit(f"{title} {slice_text}")


# ---------------------------------------------------------------------------
# -- Specialized Forensic Auditor Personas --
# ---------------------------------------------------------------------------

class TheoryAuditor(SkillAuditor):
    """Forensic auditor for Kitchenham Q1 (formal problem formulation).

    Loads ``theory_auditor.md`` and evaluates whether the research aims, the
    mathematical or structural problem formulation, the hypotheses, and the
    problem scope are explicitly and consistently stated.
    """

    name: str = "TheoryAuditor"
    skill_key: str = "theory"
    question_keys: Tuple[str, ...] = ("q1_aims_clarity",)
    critique_field: str = "theory_critique"
    result_model: Any = TheoryAuditResult
    question_keywords: Dict[str, List[str]] = {
        "q1_aims_clarity": [
            "aim", "objective", "we propose", "formulation",
            "problem statement", "hypothesis", "research question",
            "theorem", "proof", "definition", "objective function",
            "we formalize", "scope",
        ],
    }
    concern_keywords: List[str] = [
        "no clear aim", "vague", "ill-defined", "informal only",
    ]


class OperationalAuditor(SkillAuditor):
    """Forensic auditor for Kitchenham Q2 (operational context realism).

    Loads ``operational_auditor.md`` and evaluates whether environmental
    realism, physical disturbances, communication latency, and operational
    rules or safety bounds are explicitly modeled.
    """

    name: str = "OperationalAuditor"
    skill_key: str = "operational"
    question_keys: Tuple[str, ...] = ("q2_context_realism",)
    critique_field: str = "operational_critique"
    result_model: Any = OperationalAuditResult
    question_keywords: Dict[str, List[str]] = {
        "q2_context_realism": [
            "latency", "bandwidth", "communication", "disturbance",
            "noise", "wind", "aerodynamic", "collision", "safety",
            "constraint", "real-world", "hardware", "field test",
            "nato", "cjcsi", "robust", "dropout", "interference",
        ],
    }
    concern_keywords: List[str] = [
        "idealized", "no noise", "perfect communication", "simulation only",
    ]


class BenchmarkAuditor(SkillAuditor):
    """Forensic auditor for Kitchenham Q3 and Q4 (empirical rigor).

    Loads ``empirical_auditor.md`` and evaluates comparative baseline rigor
    (2-3 modern SOTA baselines under identical conditions) and statistical
    validity (>= 5 random seeds, confidence intervals, p-values, ablations).
    """

    name: str = "BenchmarkAuditor"
    skill_key: str = "empirical"
    question_keys: Tuple[str, ...] = (
        "q3_baseline_rigor", "q4_statistical_validity")
    critique_field: str = "benchmark_critique"
    result_model: Any = BenchmarkAuditResult
    question_keywords: Dict[str, List[str]] = {
        "q3_baseline_rigor": [
            "baseline", "state-of-the-art", "sota", "compared against",
            "comparison with", "benchmark", "outperform",
        ],
        "q4_statistical_validity": [
            "random seed", "seeds", "confidence interval",
            "standard deviation", "p-value", "p <", "ablation",
            "significance", "variance", "std",
        ],
    }
    concern_keywords: List[str] = [
        "single run", "no baseline", "anecdotal", "cherry-picked",
    ]


class OpenScienceAuditor(SkillAuditor):
    """Forensic auditor for Kitchenham Q5 and Q6 (open science).

    Loads ``openscience_auditor.md`` and evaluates open reproducibility
    (public code repository, open benchmark simulator or dataset) and the
    explicit reporting of limitations and failure boundaries.
    """

    name: str = "OpenScienceAuditor"
    skill_key: str = "openscience"
    question_keys: Tuple[str, ...] = (
        "q5_open_reproducibility", "q6_limitations_negative_results")
    critique_field: str = "openscience_critique"
    result_model: Any = OpenScienceAuditResult
    question_keywords: Dict[str, List[str]] = {
        "q5_open_reproducibility": [
            "github", "gitlab", "code is available", "available at",
            "repository", "open source", "open-source", "dataset",
            "zenodo", "benchmark simulator", "reproducibility",
        ],
        "q6_limitations_negative_results": [
            "limitation", "threats to validity", "failure",
            "bottleneck", "future work", "scalability issue",
            "negative result", "boundary",
        ],
    }
    concern_keywords: List[str] = [
        "available upon request", "proprietary", "closed source",
    ]


# ---------------------------------------------------------------------------
# -- Swarm Quality Verdict & Consensus Synthesizer --
# ---------------------------------------------------------------------------

@dataclass
class SwarmQualityVerdict:
    """Aggregated result of the four-auditor forensic quality swarm.

    Attributes:
        quality_score (float): Normalized ``S_qual`` in [0.0, 10.0].
        rubric (KitchenhamRubric): The merged six-question rubric.
        evidence_quadrant (str): The 2D decision-plane quadrant.
        kappa_qual (float): Inter-auditor Fleiss agreement coefficient.
        auditor_critiques (Dict[str, str]): Per-auditor forensic critiques.
        synthesis (str): The unified forensic audit narrative.
        appraisal_mode (str): Always ``"swarm"`` for this verdict type.
    """

    quality_score: float
    rubric: KitchenhamRubric
    evidence_quadrant: str
    kappa_qual: float
    auditor_critiques: Dict[str, str] = field(default_factory=dict)
    synthesis: str = ""
    appraisal_mode: str = "swarm"


class KitchenhamQualitySynthesizer:
    """Concurrent dispatcher and consensus synthesizer of the Tier-2 swarm.

    Dispatches the four specialized auditors against targeted text slices,
    merges their six ternary scores into the canonical ``KitchenhamRubric``,
    computes ``S_qual = (10/6) * sum(Q_i)``, derives the inter-auditor Fleiss
    agreement ``kappa_qual`` over banded auditor ratings, maps the 2D evidence
    quadrant, and synthesizes a unified forensic audit narrative.

    Attributes:
        ai_manager (Optional[Any]): The multi-tier LLM backend, lazily built.
        profile_name (Optional[str]): Explicit profile override.
        slicer (SmartSectionSlicer): The targeted section slicer.
    """

    # -- Auditor band thresholds for the kappa computation. --
    BAND_HIGH = 0.75
    BAND_MID = 0.375

    def __init__(self, ai_manager: Optional[Any] = None,
                 profile_name: Optional[str] = None) -> None:
        """Initialize the synthesizer with optional pre-built dependencies.

        Args:
            ai_manager (Optional[Any]): Pre-built ``AIManager`` or ``None``.
            profile_name (Optional[str]): Explicit profile name override.
        """
        self.ai_manager = ai_manager
        self.profile_name = profile_name
        self.slicer = SmartSectionSlicer()

    def _ensure_ai_manager(self) -> Optional[Any]:
        """Lazily construct the multi-tier ``AIManager`` if not supplied.

        Returns:
            Optional[Any]: The AIManager instance, or ``None`` on failure.
        """
        if self.ai_manager is None:
            try:
                from src.core.ai_manager import AIManager
                self.ai_manager = AIManager()
            except Exception:
                self.ai_manager = None
        return self.ai_manager

    def _build_auditors(self, profile_name: str) -> Dict[str, SkillAuditor]:
        """Instantiate the four auditors with their compiled skill documents.

        Args:
            profile_name (str): The profile whose compiled skills are loaded.

        Returns:
            Dict[str, SkillAuditor]: Mapping of auditor key to instance.
        """
        ai = self._ensure_ai_manager()
        auditors: Dict[str, SkillAuditor] = {}
        for cls in (TheoryAuditor, OperationalAuditor,
                    BenchmarkAuditor, OpenScienceAuditor):
            skill_text = cls.load_compiled_skill(profile_name)
            auditors[cls.skill_key] = cls(skill_text=skill_text,
                                          ai_manager=ai)
        return auditors

    # -- Inter-auditor agreement -----------------------------------------------

    @classmethod
    def _score_band(cls, mean_score: float) -> str:
        """Band an auditor's mean ternary score for the kappa computation.

        Args:
            mean_score (float): The auditor's mean ternary score in [0, 1].

        Returns:
            str: One of ``HIGH``, ``MID``, or ``LOW``.
        """
        if mean_score >= cls.BAND_HIGH:
            return "HIGH"
        if mean_score >= cls.BAND_MID:
            return "MID"
        return "LOW"

    @classmethod
    def compute_kappa_qual(cls, audits: Dict[str, BaseModel]) -> float:
        """Compute the inter-auditor Fleiss agreement coefficient.

        Each auditor's mean ternary score is banded into a categorical rating
        (LOW / MID / HIGH) and the multi-rater Fleiss generalization of
        Cohen's kappa is applied over the four-rater band set, reusing the
        Tier-1 implementation for statistical consistency.

        Args:
            audits (Dict[str, BaseModel]): Mapping of auditor key to result.

        Returns:
            float: The agreement coefficient in the range (-1.0, 1.0].
        """
        bands = [cls._score_band(float(getattr(result, "mean_score", 0.0)))
                 for result in audits.values()]
        return float(calculate_cohens_kappa(bands))

    # -- Forensic narrative synthesis -------------------------------------------

    @staticmethod
    def _synthesize_narrative(audits: Dict[str, BaseModel],
                              rubric: KitchenhamRubric,
                              quadrant: str,
                              kappa: float) -> str:
        """Compose the unified forensic audit narrative from the critiques.

        Args:
            audits (Dict[str, BaseModel]): Mapping of auditor key to result.
            rubric (KitchenhamRubric): The merged six-question rubric.
            quadrant (str): The resolved evidence quadrant.
            kappa (float): The inter-auditor agreement coefficient.

        Returns:
            str: The multi-perspective forensic narrative.
        """
        labels = {
            "theory": "TheoryAuditor (Q1)",
            "operational": "OperationalAuditor (Q2)",
            "empirical": "BenchmarkAuditor (Q3-Q4)",
            "openscience": "OpenScienceAuditor (Q5-Q6)",
        }
        lines = [
            "Two-Tier Forensic Quality Audit -- Consensus Synthesis",
            f"S_qual = {rubric.quality_score:.2f}/10 "
            f"(sum Q_i = {rubric.question_sum:.1f}/6) | "
            f"Quadrant: {quadrant} | Inter-auditor kappa: {kappa:.3f}",
        ]
        critique_fields = {
            "theory": "theory_critique",
            "operational": "operational_critique",
            "empirical": "benchmark_critique",
            "openscience": "openscience_critique",
        }
        for key, label in labels.items():
            result = audits.get(key)
            critique = ""
            if result is not None:
                critique = str(
                    getattr(result, critique_fields.get(key, ""), "") or "")
            lines.append(f"[{label}] {critique or 'No critique recorded.'}")
        return "\n".join(lines)

    # -- Concurrent dispatch & consensus ----------------------------------------

    def synthesize(self, paper: Dict[str, Any],
                   relevance_score: float = 0.0,
                   active_profile: Optional[str] = None
                   ) -> SwarmQualityVerdict:
        """Run the four-auditor forensic swarm on one paper and synthesize.

        The compiled profile skills are compiled on demand when missing, the
        four auditors are dispatched concurrently behind the VRAM-bounded
        semaphore (2 workers locally, 4 on the Cloud Mesh), and the six
        ternary scores are merged into the canonical Kitchenham rubric.

        Args:
            paper (Dict[str, Any]): Paper record with ``title``, ``abstract``,
                and optionally ``full_text``.
            relevance_score (float): Semantic relevance ``S_rel`` in [0, 10].
            active_profile (Optional[str]): Explicit profile name override.

        Returns:
            SwarmQualityVerdict: The aggregated forensic verdict.
        """
        profile_name = (active_profile or self.profile_name
                        or _default_profile_name())

        # -- Auto-compile profile skills when missing (one-time cost). --
        compiler = SkillCompiler(ai_manager=self.ai_manager,
                                 profile_name=profile_name)
        try:
            compiler.compile_profile_skills(profile_name)
        except Exception:
            # -- Auditors fall back to raw canonical templates. --
            pass

        auditors = self._build_auditors(profile_name)
        max_workers, semaphore = resolve_quality_swarm_workers()
        max_workers = max(1, min(max_workers, len(auditors)))

        slices = {
            key: self.slicer.slice_for_auditor(key, paper)
            for key in auditors
        }

        audits: Dict[str, BaseModel] = {}

        def _run_one(key: str, auditor: SkillAuditor) -> Tuple[str, BaseModel]:
            if semaphore is not None:
                with semaphore:
                    return key, auditor.audit(paper, slices[key])
            return key, auditor.audit(paper, slices[key])

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(_run_one, key, auditor)
                       for key, auditor in auditors.items()]
            for future in as_completed(futures):
                try:
                    key, result = future.result()
                except Exception:
                    continue
                audits[key] = result

        # -- Guarantee complete coverage: deterministic zeros for failures. --
        for cls in (TheoryAuditor, OperationalAuditor,
                    BenchmarkAuditor, OpenScienceAuditor):
            if cls.skill_key not in audits:
                audits[cls.skill_key] = cls.result_model(
                    **{cls.critique_field:
                       "Auditor execution failed; zero-score fallback."})

        theory = audits["theory"]
        operational = audits["operational"]
        benchmark = audits["empirical"]
        openscience = audits["openscience"]

        rubric = KitchenhamRubric(
            q1_aims_clarity=theory.q1_aims_clarity,
            q2_context_realism=operational.q2_context_realism,
            q3_baseline_rigor=benchmark.q3_baseline_rigor,
            q4_statistical_validity=benchmark.q4_statistical_validity,
            q5_open_reproducibility=openscience.q5_open_reproducibility,
            q6_limitations_negative_results=(
                openscience.q6_limitations_negative_results),
        )
        quality = rubric.quality_score
        quadrant = map_evidence_quadrant(float(relevance_score),
                                         float(quality))
        kappa = self.compute_kappa_qual(audits)

        critiques = {
            "theory_critique": str(theory.theory_critique),
            "operational_critique": str(operational.operational_critique),
            "benchmark_critique": str(benchmark.benchmark_critique),
            "openscience_critique": str(openscience.openscience_critique),
        }
        synthesis = self._synthesize_narrative(audits, rubric, quadrant, kappa)

        return SwarmQualityVerdict(
            quality_score=round(float(quality), 4),
            rubric=rubric,
            evidence_quadrant=quadrant,
            kappa_qual=round(float(kappa), 4),
            auditor_critiques=critiques,
            synthesis=synthesis,
        )


# ---------------------------------------------------------------------------
# -- Standalone CLI Entrypoint --
# ---------------------------------------------------------------------------

def main(argv: Optional[List[str]] = None) -> int:
    """Standalone entrypoint for skill compilation and swarm self-checks.

    Args:
        argv (Optional[List[str]]): Command-line arguments following the
            script.

    Returns:
        int: Process exit code (0 on success).
    """
    import argparse

    parser = argparse.ArgumentParser(
        description="TALOS Tier-2 Forensic Quality Swarm (v5.17.0): profile "
                    "skill compilation and consensus synthesis utilities."
    )
    parser.add_argument("--compile-skills", action="store_true",
                        help="Compile the four domain-specialized skill files "
                             "for the active (or --profile) research profile.")
    parser.add_argument("--force", action="store_true",
                        help="Force recompilation of existing skill files.")
    parser.add_argument("--profile", default=None,
                        help="Optional explicit profile name.")
    args = parser.parse_args(argv)

    if args.compile_skills:
        path = SkillCompiler().compile_profile_skills(
            profile_name=args.profile,
            force_recompile=bool(args.force),
        )
        print(f"[OK] Profile skills compiled under: {path}")
        return 0

    print("No action requested. Use --compile-skills to compile profile "
          "auditor skills.")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
