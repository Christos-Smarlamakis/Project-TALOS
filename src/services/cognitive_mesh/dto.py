# -*- coding: utf-8 -*-
"""
Module: dto.py
Project: TALOS v5.25.0
Description:
    Standalone Pydantic v2 data-transfer objects for the Cognitive Mesh in-tree
    microservice. This module is the single interchange surface consumed by the
    cognitive router (router.py), the provider registry (registry.py), the
    self-healing circuit breaker (self_healing.py), the benchmark client
    (benchmarks.py), the autonomous model scavenger (scavenger.py), and the
    dual intelligence reporter (reporter.py). Every schema is self-contained
    and imports only the Python standard library and Pydantic, so the whole
    package can be extracted verbatim into a standalone SYNAPSE (:8000)
    microservice shared by TALOS and MEMEX with zero dependency surgery.

    Key design decisions:
    - RoutingStrategy is a str-based Enum so it serializes directly in JSON
      payloads and remains comparable with provider-name string keys.
    - ProviderHealthState is a str-based Enum modelling the six-state
      self-healing circuit-breaker machine (HEALTHY, RATE_LIMITED, LATCHED,
      UNAUTHORIZED, UNREACHABLE, HALF_OPEN) introduced in v5.23.0.
    - AccessTier is a str-based Enum modelling the four explicit access tiers
      (LOCAL_NO_KEY, CLOUD_ZERO_CONFIG_FREE, CLOUD_FREE_TIER_WITH_KEY,
      CLOUD_PAID_API) used for zero-config failover routing.
    - RouterTaskRequest / RouterTaskResponse mirror the decoupled cognitive
      router contract (task type, strategy, messages, payload, telemetry).
    - ModelSpec / ProviderSpec / BenchmarkScorecard model the market-discovery,
      provider-status, and benchmark domains.
    - ScavengedModel / MarketIntelligenceReport model the autonomous foraging
      output and its summary statistics.
    - ProviderHealthReport / MeshDiagnosticReport model the ApiHealthProbeEngine
      probe result and the aggregate mesh diagnostic.
    - TaskComplexity / XAiDecisionRecord / SwarmSizingRecommendation model the
      v5.25.0 dynamic swarm-sizing and Explainable AI (XAI) audit domains.

Dependencies:
    - typing: type annotations (List, Dict, Optional, Any).
    - enum: definition of the RoutingStrategy enumeration.
    - pydantic (v2): BaseModel and Field for declarative validation.
"""

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class RoutingStrategy(str, Enum):
    """The five named cognitive routing strategies.

    Members are ``str`` subclasses so they serialize directly in Pydantic DTOs
    and remain comparable with provider-name string keys. ``LOCAL_FIRST_CLOUD_BACKUP``
    attempts the local Ollama tier first and dynamically fails over to the active
    cloud tier on failure or overload.
    """

    LOWEST_LATENCY = "lowest_latency"
    REASONING_RIGOR = "reasoning_rigor"
    LOWEST_COST = "lowest_cost"
    LOCAL_AIRGAPPED = "local_airgapped"
    LOCAL_FIRST_CLOUD_BACKUP = "local_first_cloud_backup"
    AUTO_SWARM_CASCADE = "auto_swarm_cascade"


class ProviderHealthState(str, Enum):
    """The six-state self-healing circuit-breaker health machine.

    Members subclass ``str`` so they serialize directly in JSON and remain
    comparable with provider-name string keys. The states model the full
    resilience lifecycle mandated by ISO/IEC 25010 Reliability:

    - ``HEALTHY``: Provider answered HTTP 200 and is fully routable.
    - ``RATE_LIMITED``: Provider returned HTTP 429; backoff window applied.
    - ``LATCHED``: Provider returned HTTP 402 (quota depleted); bypassed for
      the session unless explicitly probed.
    - ``UNAUTHORIZED``: Provider returned HTTP 401 (invalid credentials).
    - ``UNREACHABLE``: Timeout or 5xx (temporary network/upstream fault).
    - ``HALF_OPEN``: An expired backoff window permits a single probe attempt
      before the breaker re-closes or restores to HEALTHY.
    """

    HEALTHY = "HEALTHY"
    RATE_LIMITED = "RATE_LIMITED"
    LATCHED = "LATCHED"
    UNAUTHORIZED = "UNAUTHORIZED"
    UNREACHABLE = "UNREACHABLE"
    HALF_OPEN = "HALF_OPEN"


class AccessTier(str, Enum):
    """The four explicit model/endpoint access tiers for zero-config failover.

    Members subclass ``str`` for direct JSON serialization and badge rendering.

    - ``LOCAL_NO_KEY``: Local runtime (Ollama); no key and no cloud egress.
    - ``CLOUD_ZERO_CONFIG_FREE``: Cloud endpoint usable with zero configuration
      and no API key (e.g. public inference endpoints).
    - ``CLOUD_FREE_TIER_WITH_KEY``: Cloud endpoint with a free tier gated by an
      API key.
    - ``CLOUD_PAID_API``: Paid cloud endpoint requiring a funded key.
    """

    LOCAL_NO_KEY = "LOCAL_NO_KEY"
    CLOUD_ZERO_CONFIG_FREE = "CLOUD_ZERO_CONFIG_FREE"
    CLOUD_FREE_TIER_WITH_KEY = "CLOUD_FREE_TIER_WITH_KEY"
    CLOUD_PAID_API = "CLOUD_PAID_API"


class TaskComplexity(str, Enum):
    """The four civilian task-complexity bands used by the dynamic swarm sizer.

    Members subclass ``str`` so they serialize directly in JSON and remain
    comparable with task-type string keys. The band is derived from the
    composite complexity score C in [0, 1] and drives the optimal swarm
    cardinality K in {1, 2, 3, 5} for autonomous multi-agent relays.

    - ``PARSING``: Deterministic extraction and normalization (K = 1).
    - ``SUMMARIZATION``: Single-pass compression and redaction (K = 2).
    - ``CONSENSUS_VERIFICATION``: Cross-model agreement audit (K = 3).
    - ``DEEP_SYNTHESIS``: Multi-perspective reasoning relay (K = 5).
    """

    PARSING = "parsing"
    SUMMARIZATION = "summarization"
    CONSENSUS_VERIFICATION = "consensus_verification"
    DEEP_SYNTHESIS = "deep_synthesis"


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
        access_tier (str): AccessTier classification (default
            CLOUD_PAID_API).
    """

    name: str = ""
    base_url: str = ""
    api_key_env: Optional[str] = None
    default_model: str = ""
    category: str = ""
    is_openai_compatible: bool = True
    is_active: bool = False
    access_tier: str = "CLOUD_PAID_API"


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
        downloads (int): Hugging Face download count (0 when unavailable).
        likes (int): Hugging Face like count (0 when unavailable).
        vram_class (str): LOCAL_OPTIMAL | CLOUD_COST_EFFECTIVE |
            FRONTIER_REASONING.
        recommended_role (str): Recommended scientific workload role.
        pricing_prompt_per_1m_usd (float): Prompt price per 1M tokens.
        pricing_completion_per_1m_usd (float): Completion price per 1M tokens.
        mmlu_pro (float): MMLU-Pro score (0..100).
        human_eval (float): HumanEval score (0..100).
        ttft_ms (float): Time-to-first-token in milliseconds.
        access_tier (str): AccessTier classification (LOCAL_NO_KEY,
            CLOUD_ZERO_CONFIG_FREE, CLOUD_FREE_TIER_WITH_KEY, or
            CLOUD_PAID_API).
    """

    model: str = ""
    developer: str = ""
    parameter_count_b: Optional[float] = None
    parameter_count_label: str = ""
    context_window: int = 0
    license: str = ""
    release_date: Optional[str] = None
    source: str = ""
    downloads: int = 0
    likes: int = 0
    vram_class: str = "LOCAL_OPTIMAL"
    recommended_role: str = ""
    pricing_prompt_per_1m_usd: float = 0.0
    pricing_completion_per_1m_usd: float = 0.0
    mmlu_pro: float = 0.0
    human_eval: float = 0.0
    ttft_ms: float = 0.0
    access_tier: str = "LOCAL_NO_KEY"


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
    local_no_key_count: int = 0
    cloud_zero_config_free_count: int = 0
    cloud_free_tier_with_key_count: int = 0
    cloud_paid_api_count: int = 0


class ProviderHealthReport(BaseModel):
    """Single provider health probe result produced by ApiHealthProbeEngine.

    Attributes:
        provider (str): Canonical provider identifier.
        state (str): ProviderHealthState value after the probe.
        latency_ms (float): Probe round-trip latency in milliseconds.
        http_status (Optional[int]): HTTP status (None on timeout/network fault).
        access_tier (str): AccessTier classification.
        error_count (int): Consecutive error counter in the breaker.
        backoff_until (Optional[float]): Monotonic timestamp when the backoff
            window expires (None when HEALTHY).
        is_active (bool): Registry availability flag at probe time.
    """

    provider: str = ""
    state: str = "HEALTHY"
    latency_ms: float = 0.0
    http_status: Optional[int] = None
    access_tier: str = "CLOUD_PAID_API"
    error_count: int = 0
    backoff_until: Optional[float] = None
    is_active: bool = False


class MeshDiagnosticReport(BaseModel):
    """Aggregate self-healing mesh diagnostic produced by ApiHealthProbeEngine.

    Attributes:
        generated_at (str): ISO 8601 generation timestamp.
        total_providers (int): Registered provider count.
        active_providers (int): Providers active in the registry.
        healthy (int): Providers in HEALTHY state.
        free (int): Providers with zero-config free access tier.
        latched (int): Providers in LATCHED state.
        probes (list[ProviderHealthReport]): Per-provider probe results.
    """

    generated_at: str = ""
    total_providers: int = 0
    active_providers: int = 0
    healthy: int = 0
    free: int = 0
    latched: int = 0
    probes: List[ProviderHealthReport] = Field(default_factory=list)


class XAiDecisionRecord(BaseModel):
    """Append-only Explainable AI (XAI) audit record for a routing decision.

    Persisted to ``data/cache/xai_decision_log.jsonl`` as one JSON object per
    line by ``XAiDecisionLedger``. Each record captures the full rationale
    behind a swarm-sizing or model-selection decision so that high-consequence
    operational outcomes remain auditable by external consumers (Robotic
    Operations Stations, MEMEX) with zero proprietary coupling.

    Attributes:
        timestamp (str): ISO 8601 wall-clock timestamp.
        decision_id (str): UUID4 decision identifier.
        task_type (str): Semantic task label.
        complexity_score (float): Composite complexity C in [0, 1].
        swarm_size (int): Optimal swarm cardinality K in {1, 2, 3, 5}.
        candidate_models (list[str]): Ordered model chain selected.
        pareto_rationale (str): Human-readable cost/latency/quality trade-off.
        safety_flags (dict): High-consequence operational safety verification
            flags (geofence_checked, consent_checked, airgapped).
        fallback_cascade (list[str]): Providers consulted before final choice.
    """

    timestamp: str = ""
    decision_id: str = ""
    task_type: str = "general"
    complexity_score: float = 0.0
    swarm_size: int = 1
    candidate_models: List[str] = Field(default_factory=list)
    pareto_rationale: str = ""
    safety_flags: Dict[str, bool] = Field(default_factory=dict)
    fallback_cascade: List[str] = Field(default_factory=list)


class SwarmSizingRecommendation(BaseModel):
    """Dynamic swarm-sizing recommendation produced by ``DynamicSwarmSizer``.

    Attributes:
        task_type (str): Semantic task label.
        complexity_score (float): Composite complexity C in [0, 1].
        complexity_band (str): TaskComplexity band derived from C.
        swarm_size (int): Optimal swarm cardinality K in {1, 2, 3, 5}.
        model_chain (list[dict]): Ordered candidate models with access tiers.
        access_tiers (list[str]): AccessTier classification per chain slot.
        rationale (str): Human-readable justification of the K selection.
        safety_category (str): Civilian operational safety category label.
    """

    task_type: str = "general"
    complexity_score: float = 0.0
    complexity_band: str = "parsing"
    swarm_size: int = 1
    model_chain: List[Dict[str, str]] = Field(default_factory=list)
    access_tiers: List[str] = Field(default_factory=list)
    rationale: str = ""
    safety_category: str = "standard"

