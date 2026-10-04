# -*- coding: utf-8 -*-
"""
Module: server.py
Project: TALOS v5.22.1
Description:
    FastAPI mini-application for the Cognitive Mesh in-tree microservice. It
    exposes the cognitive router dispatch, the sixteen-provider registry
    telemetry, the cached benchmark matrix, and the autonomous model scavenger
    over a small REST surface. The module exports ``cognitive_router_app`` (an
    APIRouter mounted by main_api.py under ``/api/v1/cognitive``) and a
    standalone ``app`` so the service can also run independently as
    ``uvicorn src.services.cognitive_mesh.server:app --port 8003``.

    Key design decisions:
    - The standalone ``app`` wraps the same ``cognitive_router_app`` router, so
      the in-tree and standalone deployments expose an identical contract.
    - The router is constructed without a transport by default, so dispatch is
      decision-only (fully hermetic) unless a transport is injected.
    - The health endpoint reports the RTX 4070 (12 GB VRAM) budget and active
      provider telemetry without importing any SQLite/PRISMA/CLI module.

Dependencies:
    - fastapi, pydantic: routing and request validation.
    - uvicorn (standalone block only): ASGI server for port 8003.
    - src.services.cognitive_mesh.dto / registry / router / benchmarks /
      scavenger: the microservice submodules.
"""

import os

# -- Resolve project root (same pattern as all src/*.py modules) --------------
_P = os.path.abspath(os.path.dirname(__file__))
while _P and not os.path.exists(os.path.join(_P, "talos.py")):
    _P = os.path.dirname(_P)
if _P:
    import sys
    sys.path.insert(0, _P)

from fastapi import APIRouter, FastAPI  # noqa: E402
from pydantic import BaseModel, Field  # noqa: E402

from src.services.cognitive_mesh.benchmarks import ModelBenchmarkClient  # noqa: E402
from src.services.cognitive_mesh.dto import (  # noqa: E402
    MarketIntelligenceReport,
    RouterTaskRequest,
    RouterTaskResponse,
)
from src.services.cognitive_mesh.registry import (  # noqa: E402
    get_available_providers,
    get_provider_registry,
)
from src.services.cognitive_mesh.router import CognitiveMetaRouter  # noqa: E402
from src.services.cognitive_mesh.scavenger import ModelScoutAgent  # noqa: E402

cognitive_router_app = APIRouter()

# -- Module-level router singleton (decision-only unless a transport is set) --
_router: CognitiveMetaRouter = None


def _get_router() -> CognitiveMetaRouter:
    global _router
    if _router is None:
        _router = CognitiveMetaRouter(registry=get_provider_registry())
    return _router


class ScavengeRequest(BaseModel):
    """Request body for the autonomous scavenge endpoint."""

    window_days: int = Field(default=30, ge=1, le=365)


@cognitive_router_app.post("/dispatch", response_model=RouterTaskResponse)
def dispatch(request: RouterTaskRequest) -> RouterTaskResponse:
    """Execute a cognitive routing dispatch under the requested strategy.

    Args:
        request (RouterTaskRequest): The routing request DTO.

    Returns:
        RouterTaskResponse: The dispatch result including any fallback.
    """
    return _get_router().dispatch(request)


@cognitive_router_app.get("/providers")
def providers() -> list:
    """Return the active status of all sixteen registered providers.

    Returns:
        list[dict]: Active provider descriptors as dictionaries.
    """
    return [d.__dict__ for d in get_available_providers()]


@cognitive_router_app.get("/benchmarks")
def benchmarks() -> dict:
    """Return the cached benchmark matrix (top models per scientific role).

    Returns:
        dict: The role-based matrix and cache path.
    """
    client = ModelBenchmarkClient()
    return {
        "top_models_by_role": client.get_top_models_by_role(),
        "cache_path": client.cache_path,
    }


@cognitive_router_app.post("/scavenge", response_model=MarketIntelligenceReport)
def scavenge(request: ScavengeRequest) -> MarketIntelligenceReport:
    """Trigger the autonomous model scavenger and return the intelligence report.

    Args:
        request (ScavengeRequest): Discovery window in days.

    Returns:
        MarketIntelligenceReport: The aggregate scavenging result.
    """
    return ModelScoutAgent().scavenge_market(window_days=request.window_days)


@cognitive_router_app.get("/health")
def health() -> dict:
    """Report service health with local GPU and active provider telemetry.

    Returns:
        dict: Status, local GPU budget, and active provider names.
    """
    active = get_available_providers()
    return {
        "status": "ok",
        "service": "cognitive_mesh",
        "version": "5.22.1",
        "local_gpu": {"name": "RTX 4070", "vram_gb": 12.0},
        "active_provider_count": len(active),
        "active_providers": [d.name for d in active],
    }


# -- Standalone FastAPI application (port 8003) -------------------------------
app = FastAPI(
    title="TALOS Cognitive Mesh Microservice",
    description=(
        "Extraction-ready in-tree cognitive microservice: meta-routing, "
        "provider registry, benchmark matrix, and autonomous model scavenging."
    ),
    version="5.23.0",
)
app.include_router(cognitive_router_app)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("src.services.cognitive_mesh.server:app", host="127.0.0.1", port=8003)
