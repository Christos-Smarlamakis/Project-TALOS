# -*- coding: utf-8 -*-
"""
Module: test_model_scavenger.py
Project: TALOS v5.21.0
Description:
    Unit tests for the Autonomous Model Scavenger Agent
    (src/services/cognitive_mesh/scavenger.py). Verifies that mocked Hugging
    Face and OpenRouter payloads parse cleanly into MarketIntelligenceReport,
    that the hardware-aware role classifier assigns VRAM classes correctly, and
    that the offline fallback degrades gracefully to cached benchmarks.
"""

import time

from src.services.cognitive_mesh.dto import MarketIntelligenceReport, ScavengedModel
from src.services.cognitive_mesh.scavenger import ModelScavengerAgent


HF_PAYLOAD = [
    {
        "id": "meta-llama/Llama-3.1-8B-Instruct",
        "author": "meta-llama",
        "pipeline_tag": "text-generation",
        "tags": ["license:llama3.1"],
        "lastModified": "2024-07-23T00:00:00Z",
        "downloads": 100000,
    },
    {
        "id": "mistralai/Mistral-7B-v0.3",
        "author": "mistralai",
        "pipeline_tag": "text-generation",
        "tags": ["license:apache-2.0"],
        "lastModified": "2024-05-01T00:00:00Z",
    },
    {
        "id": "somevendor/proprietary-120b",
        "author": "somevendor",
        "pipeline_tag": "text-generation",
        "tags": ["license:proprietary"],
    },
]

OR_PAYLOAD = [
    {
        "id": "openai/gpt-6.1-sol",
        "name": "GPT-6.1 Sol",
        "created": int(time.time()) - 3600,
        "context_length": 1050000,
        "pricing": {"prompt": "0.000006", "completion": "0.000012"},
    },
]


class TestHuggingFaceParsing:
    def test_parses_permissive_models_only(self):
        agent = ModelScavengerAgent()
        models = agent._parse_huggingface_payload(HF_PAYLOAD)
        ids = {m.model for m in models}
        assert "meta-llama/Llama-3.1-8B-Instruct" in ids
        assert "mistralai/Mistral-7B-v0.3" in ids
        assert "somevendor/proprietary-120b" not in ids

    def test_extracts_parameter_count_from_id(self):
        agent = ModelScavengerAgent()
        models = agent._parse_huggingface_payload(HF_PAYLOAD)
        by_id = {m.model: m for m in models}
        assert by_id["meta-llama/Llama-3.1-8B-Instruct"].parameter_count_b == 8.0


class TestOpenRouterParsing:
    def test_parses_pricing_and_context(self):
        agent = ModelScavengerAgent()
        models = agent._parse_openrouter_payload(OR_PAYLOAD, window_days=30)
        assert len(models) == 1
        m = models[0]
        assert m.model == "openai/gpt-6.1-sol"
        assert m.context_window == 1050000
        assert m.pricing_prompt_per_1m_usd == 6.0
        assert m.pricing_completion_per_1m_usd == 12.0


class TestClassifier:
    def test_local_optimal_under_7b(self):
        agent = ModelScavengerAgent()
        m = ScavengedModel(model="x-3b", parameter_count_b=3.0, source="huggingface")
        assert agent._classify_vram(m) == "LOCAL_OPTIMAL"

    def test_ollama_quantized_14b_local(self):
        agent = ModelScavengerAgent()
        m = ScavengedModel(model="qwen2.5:14b", parameter_count_b=14.0, source="ollama")
        assert agent._classify_vram(m) == "LOCAL_OPTIMAL"

    def test_frontier_above_70b(self):
        agent = ModelScavengerAgent()
        m = ScavengedModel(model="x-100b", parameter_count_b=100.0, source="huggingface")
        assert agent._classify_vram(m) == "FRONTIER_REASONING"

    def test_cloud_mid_range(self):
        agent = ModelScavengerAgent()
        m = ScavengedModel(model="x-40b", parameter_count_b=40.0, source="huggingface")
        assert agent._classify_vram(m) == "CLOUD_COST_EFFECTIVE"


class TestOfflineFallback:
    def test_offline_fallback_produces_report(self, monkeypatch):
        agent = ModelScavengerAgent()

        def _http_get_json(self, url, params=None):
            return None

        monkeypatch.setattr(ModelScavengerAgent, "_http_get_json", _http_get_json)
        report = agent.scavenge_market(window_days=30)
        assert isinstance(report, MarketIntelligenceReport)
        assert report.total_models_scanned > 0
        assert report.offline_fallback is True
