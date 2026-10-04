# -*- coding: utf-8 -*-
"""
Module: test_dynamic_swarm_sizer.py
Project: TALOS v5.25.0
Description:
    Hermetic unit tests for ``DynamicSwarmSizer`` and the ``AUTO_SWARM_CASCADE``
    routing strategy. Verifies the complexity score C maps to swarm cardinality
    K in {1, 2, 3, 5} and that the cascade executes decision-only with a
    controlled fake registry (no network, no database).

Dependencies:
    - pytest: Test framework.
    - src.services.cognitive_mesh.router: DynamicSwarmSizer, CognitiveMetaRouter.
    - src.services.cognitive_mesh.dto: RouterTaskRequest, RoutingStrategy,
      SwarmSizingRecommendation.
"""

import pytest

from src.services.cognitive_mesh.dto import (
    RouterTaskRequest,
    RoutingStrategy,
    SwarmSizingRecommendation,
)
from src.services.cognitive_mesh.router import (
    CognitiveMetaRouter,
    DynamicSwarmSizer,
)


class _FakeDescriptor:
    def __init__(self, name):
        self.name = name
        self.default_model = "{}_model".format(name)


class _FakeRegistry:
    def __init__(self, active_names):
        self._active = active_names

    def list_active(self):
        return [_FakeDescriptor(n) for n in self._active]

    def get(self, name):
        if name in self._active:
            return _FakeDescriptor(name)
        return None


class TestDynamicSwarmSizer:
    def test_parsing_maps_to_k1(self):
        sizer = DynamicSwarmSizer(registry=_FakeRegistry(["ollama"]))
        rec = sizer.recommend_swarm("parsing", {})
        assert rec.swarm_size == 1
        assert rec.complexity_band == "parsing"

    def test_summarization_maps_to_k2(self):
        sizer = DynamicSwarmSizer(registry=_FakeRegistry(["ollama"]))
        rec = sizer.recommend_swarm("summarization", {})
        assert rec.swarm_size == 2
        assert rec.complexity_band == "summarization"

    def test_consensus_maps_to_k3(self):
        sizer = DynamicSwarmSizer(registry=_FakeRegistry(["ollama"]))
        rec = sizer.recommend_swarm("consensus_verification", {})
        assert rec.swarm_size == 3
        assert rec.complexity_band == "consensus_verification"

    def test_deep_synthesis_maps_to_k5(self):
        sizer = DynamicSwarmSizer(registry=_FakeRegistry(["ollama"]))
        rec = sizer.recommend_swarm("deep_synthesis", {})
        assert rec.swarm_size == 5
        assert rec.complexity_band == "deep_synthesis"

    def test_complexity_within_unit_interval(self):
        sizer = DynamicSwarmSizer(registry=_FakeRegistry(["ollama"]))
        rec = sizer.recommend_swarm("documentation", {"text": "x" * 8000})
        assert 0.0 <= rec.complexity_score <= 1.0

    def test_recommendation_is_dto(self):
        sizer = DynamicSwarmSizer(registry=_FakeRegistry(["ollama", "groq", "deepseek"]))
        rec = sizer.recommend_swarm("documentation", {})
        assert isinstance(rec, SwarmSizingRecommendation)
        assert 1 <= len(rec.model_chain) <= 5


class TestAutoSwarmCascade:
    def test_auto_swarm_cascade_dispatch(self):
        router = CognitiveMetaRouter(registry=_FakeRegistry(["ollama"]))
        request = RouterTaskRequest(
            task_type="documentation",
            strategy=RoutingStrategy.AUTO_SWARM_CASCADE,
            payload={"text": "module docs"},
        )
        response = router.dispatch(request)
        assert response.strategy == RoutingStrategy.AUTO_SWARM_CASCADE
        assert response.provider == "ollama"

    def test_recommend_swarm_via_router(self):
        router = CognitiveMetaRouter(registry=_FakeRegistry(["ollama", "groq"]))
        rec = router.recommend_swarm("deep_synthesis", {})
        assert rec.swarm_size == 5
