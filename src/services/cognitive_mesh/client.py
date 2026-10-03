# -*- coding: utf-8 -*-
"""
Module: client.py
Project: TALOS v5.21.1
Description:
    High-level client facade for the Cognitive Mesh in-tree microservice. It
    provides a single entry point (CognitiveMeshClient) that is usable
    interchangeably in-process (direct CognitiveMetaRouter dispatch) and over
    HTTP (against the standalone FastAPI mini-server on port 8003). TALOS can
    therefore consume the mesh as a plain library while MEMEX consumes the
    identical request/response contract over the network, with zero divergence
    in the Pydantic v2 DTOs.

    Key design decisions:
    - In-process mode wraps a shared CognitiveMetaRouter instance for zero
      serialization overhead.
    - HTTP mode speaks the same DTOs (RouterTaskRequest / RouterTaskResponse)
      so both modes are contract-identical.
    - Every network call degrades gracefully to a neutral response rather than
      raising, honouring the air-gapped, never-crash guarantee.

Dependencies:
    - typing, os: annotations and project-root resolution.
    - requests (lazy): optional HTTP transport for cross-service consumption.
    - src.services.cognitive_mesh.dto: RouterTaskRequest / RouterTaskResponse /
      MarketIntelligenceReport.
    - src.services.cognitive_mesh.router: CognitiveMetaRouter.
"""

import os
from typing import Any, Dict, List, Optional

# -- Resolve project root (same pattern as all src/*.py modules) --------------
_P = os.path.abspath(os.path.dirname(__file__))
while _P and not os.path.exists(os.path.join(_P, "talos.py")):
    _P = os.path.dirname(_P)
if _P:
    import sys
    sys.path.insert(0, _P)

from src.services.cognitive_mesh.dto import (  # noqa: E402
    MarketIntelligenceReport,
    RouterTaskRequest,
    RouterTaskResponse,
)
from src.services.cognitive_mesh.router import CognitiveMetaRouter  # noqa: E402


class CognitiveMeshClient:
    """Unified facade for in-process and HTTP Cognitive Mesh consumption.

    Attributes:
        base_url (Optional[str]): HTTP base URL of a standalone mesh server
            (e.g. ``http://127.0.0.1:8003``). When ``None``, dispatch is
            performed in-process.
        router (CognitiveMetaRouter): The in-process router instance.
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        router: Optional[CognitiveMetaRouter] = None,
    ) -> None:
        self.base_url = base_url
        self._router = router if router is not None else CognitiveMetaRouter()

    # ------------------------------------------------------------------
    # -- Dispatch ------------------------------------------------------
    # ------------------------------------------------------------------

    def dispatch(self, request: RouterTaskRequest) -> RouterTaskResponse:
        """Dispatch a cognitive task in-process or over HTTP.

        Args:
            request (RouterTaskRequest): The routing request DTO.

        Returns:
            RouterTaskResponse: The dispatch result, including any fallback.
        """
        if self.base_url:
            return self._dispatch_http(request)
        return self._router.dispatch(request)

    def _dispatch_http(self, request: RouterTaskRequest) -> RouterTaskResponse:
        try:
            import requests  # noqa: F401
        except ImportError:
            return RouterTaskResponse(strategy=request.strategy)
        try:
            resp = requests.post(
                f"{self.base_url.rstrip('/')}/dispatch",
                json=request.model_dump(),
                timeout=10.0,
            )
            resp.raise_for_status()
            return RouterTaskResponse(**resp.json())
        except Exception:
            return RouterTaskResponse(strategy=request.strategy)

    # ------------------------------------------------------------------
    # -- Provider telemetry --------------------------------------------
    # ------------------------------------------------------------------

    def providers(self) -> List[Dict[str, Any]]:
        """Return the active provider set (in-process or over HTTP).

        Returns:
            list[dict]: Active provider descriptors as dictionaries.
        """
        if self.base_url:
            try:
                import requests  # noqa: F401
                resp = requests.get(
                    f"{self.base_url.rstrip('/')}/providers", timeout=5.0
                )
                resp.raise_for_status()
                return resp.json()
            except Exception:
                return []
        from src.services.cognitive_mesh.registry import get_provider_registry

        return [d.__dict__ for d in get_provider_registry().list_active()]

    # ------------------------------------------------------------------
    # -- Autonomous scavenging -----------------------------------------
    # ------------------------------------------------------------------

    def scavenge(self, window_days: int = 30) -> MarketIntelligenceReport:
        """Trigger an autonomous market scavenge.

        Args:
            window_days (int): Discovery window in days.

        Returns:
            MarketIntelligenceReport: The aggregate intelligence report.
        """
        if self.base_url:
            try:
                import requests  # noqa: F401
                resp = requests.post(
                    f"{self.base_url.rstrip('/')}/scavenge",
                    json={"window_days": window_days},
                    timeout=60.0,
                )
                resp.raise_for_status()
                return MarketIntelligenceReport(**resp.json())
            except Exception:
                return MarketIntelligenceReport(window_days=window_days)
        from src.services.cognitive_mesh.scavenger import ModelScavengerAgent

        return ModelScavengerAgent().scavenge_market(window_days=window_days)
