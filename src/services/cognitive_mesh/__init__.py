# -*- coding: utf-8 -*-
"""
Module: __init__.py
Project: TALOS v5.24.0
Description:
    Public API surface for the Cognitive Mesh in-tree extraction-ready
    microservice. Re-exports the cognitive meta-router, the self-healing
    circuit breaker, the sixteen-provider registry, the benchmark client, the
    autonomous model scavenger, the dual intelligence reporter, and the
    high-level client, plus every standalone Pydantic v2 DTO and enumeration.
    The package imports no SQLite WAL storage, PRISMA evaluation, or CLI
    modules, so it can be lifted verbatim into a standalone SYNAPSE (:8000)
    microservice shared by TALOS and MEMEX.

Dependencies:
    - src.services.cognitive_mesh.dto / registry / router / self_healing /
      benchmarks / scavenger / reporter / client: the microservice submodules.
"""

from src.services.cognitive_mesh.dto import (  # noqa: F401
    AccessTier,
    BenchmarkScorecard,
    MarketIntelligenceReport,
    MeshDiagnosticReport,
    ModelSpec,
    ProviderHealthReport,
    ProviderHealthState,
    ProviderSpec,
    RouterTaskRequest,
    RouterTaskResponse,
    RoutingStrategy,
    ScavengedModel,
)
from src.services.cognitive_mesh.registry import (  # noqa: F401
    LLMProvider,
    ProviderDescriptor,
    ProviderRegistry,
    get_available_providers,
    get_provider_registry,
)
from src.services.cognitive_mesh.router import (  # noqa: F401
    CognitiveMetaRouter,
    ProviderHttpError,
)
from src.services.cognitive_mesh.self_healing import (  # noqa: F401
    ApiHealthProbeEngine,
    SelfHealingCircuitBreaker,
    classify_access_tier,
    classify_model_access_tier,
)
from src.services.cognitive_mesh.benchmarks import (  # noqa: F401
    ModelBenchmarkClient,
    run_discover_llms,
)
from src.services.cognitive_mesh.scavenger import (  # noqa: F401
    ModelScavengerAgent,
    ModelScoutAgent,
)
from src.services.cognitive_mesh.reporter import IntelligenceReporter  # noqa: F401
from src.services.cognitive_mesh.client import CognitiveMeshClient  # noqa: F401
from src.services.cognitive_mesh.rate_limiter import (  # noqa: F401
    TokenBucketRateLimiter,
    get_rate_specs,
)
from src.services.cognitive_mesh.buffer_sync import BufferSyncEngine  # noqa: F401

__all__ = [
    "RoutingStrategy",
    "AccessTier",
    "ProviderHealthState",
    "RouterTaskRequest",
    "RouterTaskResponse",
    "ModelSpec",
    "ProviderSpec",
    "BenchmarkScorecard",
    "ScavengedModel",
    "MarketIntelligenceReport",
    "ProviderHealthReport",
    "MeshDiagnosticReport",
    "LLMProvider",
    "ProviderDescriptor",
    "ProviderRegistry",
    "get_provider_registry",
    "get_available_providers",
    "CognitiveMetaRouter",
    "ProviderHttpError",
    "SelfHealingCircuitBreaker",
    "ApiHealthProbeEngine",
    "classify_access_tier",
    "classify_model_access_tier",
    "ModelBenchmarkClient",
    "run_discover_llms",
    "ModelScoutAgent",
    "ModelScavengerAgent",
    "IntelligenceReporter",
    "CognitiveMeshClient",
    "TokenBucketRateLimiter",
    "get_rate_specs",
    "BufferSyncEngine",
]
