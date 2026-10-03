# -*- coding: utf-8 -*-
"""
Module: dto.py
Project: TALOS v5.21.0
Description:
    Standalone Pydantic v2 data-transfer objects for the Cognitive Mesh in-tree
    microservice. This module is the single interchange surface consumed by the
    cognitive router (router.py), the provider registry (registry.py), the
    benchmark client (benchmarks.py), the autonomous model scavenger
    (scavenger.py), and the dual intelligence reporter (reporter.py). Every
    schema is self-contained and imports only the Python standard library and
    Pydantic, so the whole package can be extracted verbatim into a standalone
    SYNAPSE (:8000) microservice shared by TALOS and MEMEX with zero dependency
    surgery.

    Key design decisions:
    - RoutingStrategy is a str-based Enum so it serializes directly in JSON
      payloads and remains comparable with provider-name string keys.
    - RouterTaskRequest / RouterTaskResponse mirror the decoupled cognitive
      router contract (task type, strategy, messages, payload, telemetry).
    - ModelSpec / ProviderSpec / BenchmarkScorecard model the market-discovery,
      provider-status, and benchmark domains.
    - ScavengedModel / MarketIntelligenceReport model the autonomous foraging
      output and its summary statistics.

Dependencies:
    - typing: type annotations (List, Dict, Optional, Any).
    - enum: definition of the RoutingStrategy enumeration.
    - pydantic (v2): BaseModel and Field for declarative validation.
"""

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class RoutingStrategy(str, Enum):
    """The four named cognitive routing strategies.

    Members are ``str`` subclasses so they serialize directly in Pydantic DTOs
    and remain comparable with provider-name string keys.
    """

    LOWEST_LATENCY = "lowest_latency"
    REASONING_RIGOR = "reasoning_rigor"
    LOWEST_COST = "lowest_cost"
    LOCAL_AIRGAPPED = "local_airgapped"


class RouterTaskRequest(BaseModel):
    """Standalone Pydantic v2 request DTO for a cognitive routing dispatch.

    Attributes:
        task_type (str): Semantic task label (e.g. ``fast_screening``,
            ``kitchenham_audit``, ``code_audit``, ``vector_embeddings``).
        strategy (RoutingStrategy): The requested routing strategy.
        messages (list[dict]): Chat-style messages for the target provider.
        payload (dict): Arbitrary task payload (prompt, schema, options).
        max_tokens (int): Upper bound on completion length.
        min_quality (float): Quality floor for LOWEST_COST (default 0.70).
        response_format (str): ``"text"`` or ``"json"``.
    """

    task_type: str = Field(default="general", description="Semantic task label.")
    strategy: RoutingStrategy = Field(
        default=RoutingStrategy.LOWEST_LATENCY,
        description="Requested routing strategy.",
    )
    messages: List[Dict[str, str]] = Field(default_factory=list)
    payload: Dict[str, Any] = Field(default_factory=dict)
    max_tokens: int = Field(default=512, ge=1)
    min_quality: float = Field(default=0.70, ge=0.0, le=1.0)
    response_format: str = Field(default="text")


class RouterTaskResponse(BaseModel):
    """Standalone Pydantic v2 response DTO for a cognitive routing dispatch.

    Attributes:
        provider (str): Selected provider name (empty on total failure).
        model (str): Selected model identifier.
        content (Any): Completion content (None when no transport is injected).
        latency_ms (float): Observed end-to-end latency in milliseconds.
        prompt_tokens (int): Prompt token count.
        completion_tokens (int): Completion token count.
        cost_estimate_usd (float): Estimated USD cost of the call.
        strategy (RoutingStrategy): The strategy that produced this dispatch.
        fallback_occurred (bool): True when a provider was latched/skipped.
        latched_providers (list[str]): Providers latched during this dispatch.
    """

    provider: str = ""
    model: str = ""
    content: Any = None
    latency_ms: float = 0.0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    cost_estimate_usd: float = 0.0
    strategy: RoutingStrategy = RoutingStrategy.LOWEST_LATENCY
    fallback_occurred: bool = False
    latched_providers: List[str] = Field(default_factory=list)


class ModelSpec(BaseModel):
    """Canonical model identity shared across routing, discovery, and reporting.

    Attributes:
        model (str): Model identifier (e.g. ``qwen2.5:14b``).
        provider (str): Serving provider or registry key.
        parameter_count_b (Optional[float]): Parameter count in billions.
        context_window (int): Maximum context window in tokens.
        license (str): Weight license identifier.
        release_date (Optional[str]): ISO 8601 release date.
        category (str): Latency/compute class label.
    """

    model: str = ""
    provider: str = ""
    parameter_count_b: Optional[float] = None
    context_window: int = 0
    license: str = ""
    release_date: Optional[str] = None
    category: str = ""


class ProviderSpec(BaseModel):
    """Provider identity and runtime status DTO (Pydantic mirror of the registry).

    Attributes:
        name (str): Canonical provider identifier.
        base_url (str): Root HTTP endpoint.
        api_key_env (Optional[str]): Environment variable holding the API key.
        default_model (str): Default model identifier.
        category (str): Latency/compute class label.
        is_openai_compatible (bool): Whether the provider speaks the
            OpenAI-compatible ``/v1/chat/completions`` protocol.
        is_active (bool): Runtime availability flag.
    """

    name: str = ""
    base_url: str = ""
    api_key_env: Optional[str] = None
    default_model: str = ""
    category: str = ""
    is_openai_compatible: bool = True
    is_active: bool = False


class BenchmarkScorecard(BaseModel):
    """Benchmark metrics for a single model.

    Attributes:
        model (str): Model identifier.
        provider (str): Serving provider.
        roles (list[str]): Scientific workload roles this model can serve.
        mmlu_pro (float): MMLU-Pro accuracy score (0..100).
        human_eval (float): HumanEval pass@1 score (0..100).
        cost_per_1m_usd (float): Blended cost per 1M tokens in USD.
        ttft_ms (float): Time-to-first-token in milliseconds.
        throughput_tps (float): Sustained tokens per second.
    """

    model: str = ""
    provider: str = ""
    roles: List[str] = Field(default_factory=list)
    mmlu_pro: float = 0.0
    human_eval: float = 0.0
    cost_per_1m_usd: float = 0.0
    ttft_ms: float = 0.0
    throughput_tps: float = 0.0


class ScavengedModel(BaseModel):
    """A single discovered model with market and hardware metadata.

    Attributes:
        model (str): Model identifier.
        developer (str): Releasing organization.
        parameter_count_b (Optional[float]): Parameter count in billions.
        parameter_count_label (str): Human-readable parameter count (e.g. "14B").
        context_window (int): Maximum context window in tokens.
        license (str): Weight license identifier.
        release_date (Optional[str]): ISO 8601 release date.
        source (str): Discovery source (huggingface/openrouter/ollama/benchmarks).
        vram_class (str): LOCAL_OPTIMAL | CLOUD_COST_EFFECTIVE |
            FRONTIER_REASONING.
        recommended_role (str): Recommended scientific workload role.
        pricing_prompt_per_1m_usd (float): Prompt price per 1M tokens.
        pricing_completion_per_1m_usd (float): Completion price per 1M tokens.
        mmlu_pro (float): MMLU-Pro score (0..100).
        human_eval (float): HumanEval score (0..100).
        ttft_ms (float): Time-to-first-token in milliseconds.
    """

    model: str = ""
    developer: str = ""
    parameter_count_b: Optional[float] = None
    parameter_count_label: str = ""
    context_window: int = 0
    license: str = ""
    release_date: Optional[str] = None
    source: str = ""
    vram_class: str = "LOCAL_OPTIMAL"
    recommended_role: str = ""
    pricing_prompt_per_1m_usd: float = 0.0
    pricing_completion_per_1m_usd: float = 0.0
    mmlu_pro: float = 0.0
    human_eval: float = 0.0
    ttft_ms: float = 0.0


class MarketIntelligenceReport(BaseModel):
    """Aggregate autonomous scavenging report.

    Attributes:
        generated_at (str): ISO 8601 generation timestamp.
        window_days (int): Discovery window in days.
        sources_queried (list[str]): Sources successfully queried.
        sources_failed (list[str]): Sources that failed (offline resilience).
        models (list[ScavengedModel]): Discovered model records.
        total_models_scanned (int): Total records scanned.
        active_providers (int): Active provider count from the registry.
        average_price_per_1m_usd (float): Mean blended price per 1M tokens.
        local_optimal_count (int): Models classified LOCAL_OPTIMAL.
        cloud_cost_effective_count (int): Models classified CLOUD_COST_EFFECTIVE.
        frontier_reasoning_count (int): Models classified FRONTIER_REASONING.
        offline_fallback (bool): True when degraded to cached benchmarks.
    """

    generated_at: str = ""
    window_days: int = 30
    sources_queried: List[str] = Field(default_factory=list)
    sources_failed: List[str] = Field(default_factory=list)
    models: List[ScavengedModel] = Field(default_factory=list)
    total_models_scanned: int = 0
    active_providers: int = 0
    average_price_per_1m_usd: float = 0.0
    local_optimal_count: int = 0
    cloud_cost_effective_count: int = 0
    frontier_reasoning_count: int = 0
    offline_fallback: bool = False

