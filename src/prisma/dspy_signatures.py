# -*- coding: utf-8 -*-
"""
Module: dspy_signatures.py
Project: TALOS v5.17.1
Description:
    Typed declarative schema structures for the PRISMA-ScR scoping review
    pipeline. These models mirror the Stanford DSPy ``dspy.Signature``
    philosophy -- a Signature is a declarative mapping of typed input fields to
    typed output fields that constrains what an LLM module must emit -- but they
    are implemented natively with Pydantic v2 so the pipeline remains fully
    functional in an air-gapped environment with no hard ``dspy-ai`` dependency.

    Four signatures are defined:
      - ``PrismaPlanSignature``:      research topic + domain scope -> search
        facets, boolean strategy, inclusion and exclusion criteria.
      - ``PrismaScreeningSignature``: title/abstract + criteria -> screening
        decision with relevance score, exclusion reason, methodology tags and
        an explicit chain-of-thought trace.
      - ``PrismaEligibilitySignature``: deep abstract/methodology assessment ->
        eligibility decision plus swarm algorithm type, learning paradigm and
        network architecture labels.
      - ``PrismaSynthesisSignature``:  included-studies summary + topic ->
        thematic taxonomy, methodological distribution, gaps and narrative.

    Every signature exposes a ``parse_output`` class method that recovers a
    validated instance from a potentially messy local-LLM response (handling
    Markdown code fences and chain-of-thought prose preceding the JSON object).
Dependencies:
    - json: Parsing recovered JSON payloads.
    - re: Fence stripping during payload extraction.
    - typing: Literal, Optional, List, Dict, Any annotations.
    - pydantic: BaseModel and Field for typed, validated signatures.
"""

import json
import re
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field, ValidationError


# ---------------------------------------------------------------------------
# -- JSON Payload Recovery --
# ---------------------------------------------------------------------------

def extract_json_payload(text: Optional[str]) -> Optional[Dict[str, Any]]:
    """Recover a JSON object from a potentially messy LLM response.

    Local models frequently wrap the requested JSON in Markdown code fences or
    prepend chain-of-thought prose. This helper strips fences and captures the
    first balanced ``{ ... }`` span, then attempts ``json.loads``. It is a
    defensive recovery function: it never raises, returning ``None`` when no
    parseable object exists so callers can fall back to deterministic rules.

    Args:
        text (Optional[str]): Raw LLM response text.

    Returns:
        Optional[Dict[str, Any]]: The parsed JSON object, or ``None``.
    """
    if not text:
        return None

    # -- Strip Markdown code fences (```json ... ``` or ``` ... ```). --
    cleaned = text
    fenced = re.search(r"```(?:json)?\s*(.*?)```", cleaned, flags=re.DOTALL)
    if fenced:
        cleaned = fenced.group(1)
    else:
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start != -1 and end != -1 and end > start:
            cleaned = cleaned[start:end + 1]

    try:
        return json.loads(cleaned)
    except (json.JSONDecodeError, TypeError):
        pass

    # -- Fallback: locate the first balanced object even without a clean fence. --
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(text[start:end + 1])
        except (json.JSONDecodeError, TypeError):
            return None
    return None


def _string_list(value: Any) -> List[str]:
    """Coerce a raw parsed value into a list of non-empty strings.

    Tolerates both JSON lists and comma/newline-separated strings so that a
    local model emitting ``"a, b, c"`` instead of ``["a", "b", "c"]`` still
    validates.

    Args:
        value (Any): Raw value recovered from JSON.

    Returns:
        List[str]: Normalized list of trimmed, non-empty strings.
    """
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]
    if isinstance(value, str):
        parts = re.split(r"[,\n;]", value)
        return [p.strip() for p in parts if p.strip()]
    return [str(value).strip()] if str(value).strip() else []


# ---------------------------------------------------------------------------
# -- Declarative Signature Base --
# ---------------------------------------------------------------------------

class DspySignature(BaseModel):
    """Base class for typed declarative PRISMA-ScR signatures.

    Provides the shared ``parse_output`` protocol: given a raw LLM response
    string, recover and validate a concrete signature instance. Subclasses
    override ``_normalize`` to coerce loosely-typed local-model output into the
    strict declared field types before Pydantic validation.
    """

    model_config = {"extra": "ignore"}

    @classmethod
    def _normalize(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize raw parsed data before validation.

        Args:
            data (Dict[str, Any]): Parsed JSON payload.

        Returns:
            Dict[str, Any]: Normalized payload (identity by default).
        """
        return data

    @classmethod
    def parse_output(cls, text: Optional[str]) -> Optional["DspySignature"]:
        """Recover and validate a signature instance from raw LLM text.

        Args:
            text (Optional[str]): Raw LLM response text.

        Returns:
            Optional[DspySignature]: A validated instance, or ``None`` when the
                response is unparseable or fails validation.
        """
        data = extract_json_payload(text)
        if not isinstance(data, dict):
            return None
        try:
            return cls(**cls._normalize(data))
        except (ValidationError, TypeError):
            return None


# ---------------------------------------------------------------------------
# -- 1. PRISMA Plan Signature --
# ---------------------------------------------------------------------------

class PrismaPlanSignature(DspySignature):
    """Declarative signature synthesizing a multi-database search protocol.

    Input fields: ``research_topic`` and ``domain_scope``. Output fields:
    ``search_facets``, ``boolean_strategy``, ``methodological_inclusion_criteria``
    and ``exclusion_criteria``. This is the Identification-phase planner that
    produces a reproducible, PRISMA-ScR-compliant search strategy.
    """

    # -- Input fields --
    research_topic: str = ""
    domain_scope: str = ""

    # -- Output fields --
    search_facets: List[str] = Field(default_factory=list)
    boolean_strategy: str = ""
    methodological_inclusion_criteria: List[str] = Field(default_factory=list)
    exclusion_criteria: List[str] = Field(default_factory=list)

    @classmethod
    def _normalize(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "research_topic": data.get("research_topic", data.get("topic", "")),
            "domain_scope": data.get("domain_scope", data.get("scope", "")),
            "search_facets": _string_list(data.get("search_facets", data.get("facets", []))),
            "boolean_strategy": str(data.get("boolean_strategy", data.get("boolean_query", "")) or ""),
            "methodological_inclusion_criteria": _string_list(
                data.get("methodological_inclusion_criteria", data.get("inclusion_criteria", []))
            ),
            "exclusion_criteria": _string_list(data.get("exclusion_criteria", [])),
        }


# ---------------------------------------------------------------------------
# -- 2. PRISMA Screening Signature --
# ---------------------------------------------------------------------------

class PrismaScreeningSignature(DspySignature):
    """Declarative signature for title/abstract screening with chain-of-thought.

    Emits an ``INCLUDE`` / ``EXCLUDE`` / ``UNCERTAIN`` decision plus a bounded
    relevance score, an optional exclusion reason, methodology tags and the
    explicit ``chain_of_thought`` trace required for auditability.
    """

    # -- Input fields --
    title: str = ""
    abstract: str = ""
    inclusion_criteria: List[str] = Field(default_factory=list)
    exclusion_criteria: List[str] = Field(default_factory=list)

    # -- Output fields --
    decision: Literal["INCLUDE", "EXCLUDE", "UNCERTAIN"] = "UNCERTAIN"
    relevance_score: float = Field(default=0.0, ge=0.0, le=10.0)
    exclusion_reason: Optional[str] = None
    methodology_tags: List[str] = Field(default_factory=list)
    chain_of_thought: str = ""
    # -- v5.14.1: Multi-agent swarm consensus metadata. --
    consensus_mode: str = "single"
    swarm_kappa: Optional[float] = None
    agent_verdicts: List[Dict[str, Any]] = Field(default_factory=list)

    @classmethod
    def _normalize(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        decision = str(data.get("decision", "UNCERTAIN")).strip().upper()
        if decision not in ("INCLUDE", "EXCLUDE", "UNCERTAIN"):
            decision = "UNCERTAIN"
        score = data.get("relevance_score", 0.0)
        try:
            score = float(score)
        except (TypeError, ValueError):
            score = 0.0
        score = max(0.0, min(10.0, score))
        agent_verdicts = data.get("agent_verdicts", [])
        if not isinstance(agent_verdicts, list):
            agent_verdicts = []
        return {
            "title": data.get("title", ""),
            "abstract": data.get("abstract", ""),
            "decision": decision,
            "relevance_score": score,
            "exclusion_reason": data.get("exclusion_reason"),
            "methodology_tags": _string_list(data.get("methodology_tags", data.get("tags", []))),
            "chain_of_thought": str(data.get("chain_of_thought", "") or ""),
            "consensus_mode": str(data.get("consensus_mode", "single") or "single"),
            "swarm_kappa": data.get("swarm_kappa"),
            "agent_verdicts": agent_verdicts,
        }


# ---------------------------------------------------------------------------
# -- 3. PRISMA Eligibility Signature --
# ---------------------------------------------------------------------------

class PrismaEligibilitySignature(DspySignature):
    """Declarative signature for full-abstract/methodology eligibility.

    Assesses whether a screened-in study is methodologically eligible for the
    scoping review and labels its swarm algorithm type, learning paradigm and
    network architecture for the methodological evidence map.
    """

    # -- Input fields --
    title: str = ""
    abstract: str = ""
    methodology_tags: List[str] = Field(default_factory=list)
    deep_criteria: str = ""

    # -- Output fields --
    eligibility_decision: Literal["ELIGIBLE", "INELIGIBLE"] = "INELIGIBLE"
    swarm_algorithm_type: str = ""
    learning_paradigm: str = ""
    network_architecture: str = ""
    justification: str = ""

    @classmethod
    def _normalize(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        decision = str(data.get("eligibility_decision", "INELIGIBLE")).strip().upper()
        if decision not in ("ELIGIBLE", "INELIGIBLE"):
            decision = "INELIGIBLE"
        return {
            "title": data.get("title", ""),
            "abstract": data.get("abstract", ""),
            "methodology_tags": _string_list(data.get("methodology_tags", [])),
            "deep_criteria": str(data.get("deep_criteria", "") or ""),
            "eligibility_decision": decision,
            "swarm_algorithm_type": str(data.get("swarm_algorithm_type", "") or ""),
            "learning_paradigm": str(data.get("learning_paradigm", "") or ""),
            "network_architecture": str(data.get("network_architecture", "") or ""),
            "justification": str(data.get("justification", "") or ""),
        }


# ---------------------------------------------------------------------------
# -- 4. PRISMA Synthesis Signature --
# ---------------------------------------------------------------------------

class PrismaSynthesisSignature(DspySignature):
    """Declarative signature for thematic synthesis of included studies.

    Produces the thematic taxonomy, methodological distribution, identified
    research gaps and a narrative synthesis that feed the scoping review draft.
    """

    # -- Input fields --
    included_studies_summary: str = ""
    research_topic: str = ""

    # -- Output fields --
    thematic_taxonomy: Dict[str, Any] = Field(default_factory=dict)
    methodological_distribution: Dict[str, Any] = Field(default_factory=dict)
    identified_gaps: List[str] = Field(default_factory=list)
    synthesis_narrative: str = ""

    @classmethod
    def _normalize(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        taxonomy = data.get("thematic_taxonomy", {})
        distribution = data.get("methodological_distribution", {})
        return {
            "included_studies_summary": data.get("included_studies_summary", ""),
            "research_topic": data.get("research_topic", data.get("topic", "")),
            "thematic_taxonomy": taxonomy if isinstance(taxonomy, dict) else {},
            "methodological_distribution": distribution if isinstance(distribution, dict) else {},
            "identified_gaps": _string_list(data.get("identified_gaps", [])),
            "synthesis_narrative": str(data.get("synthesis_narrative", "") or ""),
        }
