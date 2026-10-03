# -*- coding: utf-8 -*-
"""
Module: cognitive_router.py
Project: TALOS v5.21.1
Description:
    Backward-compatible shim. The Cognitive Meta-Router has been migrated into
    the in-tree extraction-ready microservice namespace
    (src/services/cognitive_mesh/router.py) in v5.21.1. This module re-exports
    the canonical public API so every existing TALOS consumer and test
    continues to resolve ``from src.core.cognitive_router import ...`` without
    modification.

Dependencies:
    - src.services.cognitive_mesh.router: canonical CognitiveMetaRouter.
"""
from src.services.cognitive_mesh.router import (  # noqa: F401
    CognitiveMetaRouter,
    RoutingStrategy,
    RouterTaskRequest,
    RouterTaskResponse,
    ProviderHttpError,
    LATCH_STATUSES,
)
