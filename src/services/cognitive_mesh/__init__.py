# -*- coding: utf-8 -*-
"""
Module: __init__.py
Project: TALOS v5.22.1
Description:
    Public API surface for the Cognitive Mesh in-tree extraction-ready
    microservice. Re-exports the cognitive meta-router, the sixteen-provider
    registry, the benchmark client, the autonomous model scavenger, the dual
    intelligence reporter, and the high-level client, plus every standalone
    Pydantic v2 DTO and enumeration. The package imports no SQLite WAL storage,
    PRISMA evaluation, or CLI modules, so it can be lifted verbatim into a
    standalone SYNAPSE (:8000) microservice shared by TALOS and MEMEX.

Dependencies:
    - src.services.cognitive_mesh.dto / registry / router / benchmarks /
      scavenger / reporter / client: the microservice submodules.
"""

from src.services.cognitive_mesh.dto import (  # noqa: F401
    BenchmarkScorecard,
    MarketIntelligenceReport,
    ModelSpec,
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

__all__ = [
    "RoutingStrategy",
    "RouterTaskRequest",
    "RouterTaskResponse",
    "ModelSpec",
    "ProviderSpec",
    "BenchmarkScorecard",
    "ScavengedModel",
    "MarketIntelligenceReport",
    "LLMProvider",
    "ProviderDescriptor",
    "ProviderRegistry",
    "get_provider_registry",
    "get_available_providers",
    "CognitiveMetaRouter",
    "ProviderHttpError",
    "ModelBenchmarkClient",
    "run_discover_llms",
    "ModelScoutAgent",
    "ModelScavengerAgent",
    "IntelligenceReporter",
    "CognitiveMeshClient",
]
