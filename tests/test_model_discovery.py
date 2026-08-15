# -*- coding: utf-8 -*-
"""
Module: test_model_discovery.py
Project: TALOS v5.10.4
Description:
    Hermetic unit tests for the Dynamic Model Discovery Engine
    (src/ai/llm/model_discovery.py) and the SYNAPSE status endpoint
    (src/api/synapse_routes.py). Tests cover local Ollama tag parsing, cloud
    model-list parsing, offline registry fallback, dynamic relative quality
    score calculation, provider-level aggregation, and the GET /status endpoint.

    Key design decisions:
    - No network access: live discovery calls are short-circuited or mocked.
    - A temporary registry file is used for hermetic registry tests.
    - The SYNAPSE status endpoint is exercised through a minimal FastAPI app.

Dependencies:
    - pytest: Test framework for fixture-based testing.
    - unittest.mock: Mocking HTTP discovery calls.
    - fastapi.testclient.TestClient: Simulated HTTP requests.
"""
import json
import os
import pytest
from unittest.mock import MagicMock

from src.ai.llm.model_discovery import (
    ModelDiscoveryEngine,
    DEFAULT_BENCHMARK_MODELS,
)


@pytest.fixture
def tmp_registry(tmp_path):
    """Create a temporary benchmark registry with a known model set."""
    registry_path = tmp_path / "model_benchmarks.json"
    models = {
        "alpha": {"provider": "local", "swe_bench_score": 40.0, "mmlu_pro_score": 50.0, "context_window": 8192, "pricing_tier": "free"},
        "beta": {"provider": "nvidia", "swe_bench_score": 80.0, "mmlu_pro_score": 90.0, "context_window": 131072, "pricing_tier": "cloud"},
        "gamma": {"provider": "groq", "swe_bench_score": 20.0, "mmlu_pro_score": 30.0, "context_window": 65536, "pricing_tier": "cloud"},
    }
    payload = {"schema_version": "1.0", "models": models}
    registry_path.write_text(json.dumps(payload), encoding="utf-8")
    return str(registry_path)


def make_engine(registry_path):
    """Build an engine against a registry with live discovery short-circuited."""
    engine = ModelDiscoveryEngine(registry_path=registry_path, emit_events=False)
    engine._discover_local_models = MagicMock(return_value=[])
    engine._discover_cloud_models = MagicMock(return_value=[])
    return engine


class TestLocalDiscovery:
    """Tests for the Ollama /api/tags payload parser."""

    def test_parse_local_tags_standard(self):
        data = {"models": [{"name": "qwen2.5:14b"}, {"name": "gemma3:12b"}]}
        result = ModelDiscoveryEngine._parse_local_tags(data)
        assert result == [
            {"name": "qwen2.5:14b", "provider": "local"},
            {"name": "gemma3:12b", "provider": "local"},
        ]

    def test_parse_local_tags_empty(self):
        assert ModelDiscoveryEngine._parse_local_tags(None) == []
        assert ModelDiscoveryEngine._parse_local_tags({"models": []}) == []

    def test_parse_local_tags_uses_model_key(self):
        data = {"models": [{"model": "phi4:14b"}]}
        result = ModelDiscoveryEngine._parse_local_tags(data)
        assert result == [{"name": "phi4:14b", "provider": "local"}]


class TestCloudDiscovery:
    """Tests for the cloud model-list payload parser."""

    def test_parse_cloud_models_openai_style(self):
        data = {"object": "list", "data": [{"id": "nemotron-70b"}, {"id": "llama-3.3-70b"}]}
        result = ModelDiscoveryEngine._parse_cloud_models(data, "nvidia")
        assert result == [
            {"name": "nemotron-70b", "provider": "nvidia"},
            {"name": "llama-3.3-70b", "provider": "nvidia"},
        ]

    def test_parse_cloud_models_gemini_style(self):
        data = {"models": [{"name": "models/gemini-2.5-pro"}]}
        result = ModelDiscoveryEngine._parse_cloud_models(data, "gemini")
        assert result == [{"name": "gemini-2.5-pro", "provider": "gemini"}]

    def test_parse_cloud_models_empty(self):
        assert ModelDiscoveryEngine._parse_cloud_models(None, "groq") == []
        assert ModelDiscoveryEngine._parse_cloud_models({}, "groq") == []


class TestOfflineFallback:
    """Tests for the air-gapped registry fallback behavior."""

    def test_registry_created_when_absent(self, tmp_path):
        registry_path = str(tmp_path / "new_registry.json")
        engine = ModelDiscoveryEngine(registry_path=registry_path, emit_events=False)
        assert os.path.exists(registry_path)
        loaded = engine._load_registry()
        assert set(loaded.keys()) == set(DEFAULT_BENCHMARK_MODELS.keys())

    def test_discover_falls_back_to_registry_offline(self, tmp_registry):
        engine = make_engine(tmp_registry)
        report = engine.discover_active_models(online=False)
        assert report["mode"] == "air_gapped_fallback"
        assert report["count"] == 3
        names = {m["name"] for m in report["active_models"]}
        assert names == {"alpha", "beta", "gamma"}

    def test_enrich_attaches_registry_metadata(self, tmp_registry):
        engine = make_engine(tmp_registry)
        registry = engine._load_registry()
        enriched = engine._enrich_models([{"name": "alpha", "provider": "local"}], registry)
        assert enriched[0]["swe_bench_score"] == 40.0
        assert enriched[0]["pricing_tier"] == "free"


class TestQualityScoring:
    """Tests for the dynamic relative quality calculation Q_p."""

    def test_compute_quality_scores_top_is_one(self):
        active = [
            {"name": "a", "swe_bench_score": 40.0},
            {"name": "b", "swe_bench_score": 80.0},
            {"name": "c", "swe_bench_score": 20.0},
        ]
        scores = ModelDiscoveryEngine._compute_quality_scores(active)
        assert scores["b"] == pytest.approx(1.0)
        assert scores["a"] == pytest.approx(0.5)
        assert scores["c"] == pytest.approx(0.25)

    def test_compute_quality_scores_empty(self):
        assert ModelDiscoveryEngine._compute_quality_scores([]) == {}

    def test_compute_quality_scores_zero_floor(self):
        active = [{"name": "a", "swe_bench_score": 0.0}]
        assert ModelDiscoveryEngine._compute_quality_scores(active) == {"a": 0.0}

    def test_get_normalized_quality_scores_dynamic(self, tmp_registry):
        engine = make_engine(tmp_registry)
        scores = engine.get_normalized_quality_scores()
        assert scores["beta"] == pytest.approx(1.0)
        assert scores["alpha"] == pytest.approx(0.5)
        assert scores["gamma"] == pytest.approx(0.25)

    def test_provider_quality_aggregation(self, tmp_registry):
        engine = make_engine(tmp_registry)
        provider_scores = engine.get_provider_quality_scores()
        assert provider_scores["nvidia"] == pytest.approx(1.0)
        assert provider_scores["local"] == pytest.approx(0.5)
        assert provider_scores["groq"] == pytest.approx(0.25)


class TestSynapseStatusEndpoint:
    """Tests for the GET /api/v1/synapse/status endpoint."""

    @pytest.fixture
    def client(self):
        """Create a FastAPI TestClient with the synapse router mounted."""
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from src.api.synapse_routes import router

        app = FastAPI()
        app.include_router(router)
        return TestClient(app)

    def test_status_endpoint_returns_structure(self, client):
        response = client.get("/api/v1/synapse/status")
        assert response.status_code == 200
        data = response.json()
        assert data["source"] == "talos"
        assert data["bus"] in ("reachable", "unreachable")
        assert isinstance(data["supported_event_types"], list)
        assert "model_discovered" in data["supported_event_types"]
        assert "router_decision" in data["supported_event_types"]
        assert set(data["queue_health"].keys()) == {"total", "success", "failure"}
        assert "subscribers" in data
        assert "timestamp" in data
