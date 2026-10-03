# -*- coding: utf-8 -*-
"""
Module: test_model_scavenger.py
Project: TALOS v5.21.1
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

    def test_parses_downloads_and_likes(self):
        agent = ModelScavengerAgent()
        payload = [{
            "id": "meta-llama/Llama-3.1-8B-Instruct",
            "author": "meta-llama",
            "pipeline_tag": "text-generation",
            "tags": ["license:llama3.1"],
            "downloads": 12345,
            "likes": 678,
        }]
        models = agent._parse_huggingface_payload(payload)
        assert models[0].downloads == 12345
        assert models[0].likes == 678


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

    def test_full_catalog_keeps_old_models(self):
        agent = ModelScavengerAgent()
        old = [{
            "id": "openai/gpt-4o",
            "name": "GPT-4o",
            "created": 1600000000,  # an old release timestamp
            "context_length": 128000,
            "pricing": {"prompt": "0.0000025", "completion": "0.00001"},
        }]
        models = agent._parse_openrouter_payload(old, window_days=0)
        assert len(models) == 1

    def test_window_filter_drops_old_models(self):
        agent = ModelScavengerAgent()
        old = [{
            "id": "openai/gpt-4o",
            "name": "GPT-4o",
            "created": 1600000000,
            "context_length": 128000,
            "pricing": {"prompt": "0.0000025", "completion": "0.00001"},
        }]
        models = agent._parse_openrouter_payload(old, window_days=30)
        assert len(models) == 0


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

    def test_claude_sonnet_is_frontier_rigor(self):
        agent = ModelScavengerAgent()
        role, vram = agent._classify_model("claude-3-5-sonnet", None, 0.0, None)
        assert vram == "FRONTIER_REASONING"
        assert role == "Kitchenham Rigor"

    def test_gpt4_is_frontier_rigor(self):
        agent = ModelScavengerAgent()
        role, vram = agent._classify_model("gpt-4o", None, 0.0, None)
        assert vram == "FRONTIER_REASONING"
        assert role == "Kitchenham Rigor"

    def test_deepseek_r1_is_frontier_rigor(self):
        agent = ModelScavengerAgent()
        role, vram = agent._classify_model("deepseek-r1", None, 0.0, None)
        assert vram == "FRONTIER_REASONING"
        assert role == "Kitchenham Rigor"

    def test_under_14b_is_local_optimal(self):
        agent = ModelScavengerAgent()
        _, vram = agent._classify_model("qwen2.5:14b", 14.0, 0.0, None)
        assert vram == "LOCAL_OPTIMAL"

    def test_coder_model_is_code_audit(self):
        agent = ModelScavengerAgent()
        role, vram = agent._classify_model("qwen2.5-coder:14b", 14.0, 0.0, None)
        assert role == "Code Audit"
        assert vram == "LOCAL_OPTIMAL"

    def test_embedding_model_is_vector_embeddings(self):
        agent = ModelScavengerAgent()
        role, _ = agent._classify_model("nomic-embed-text", 0.137, 0.0, None, "ollama")
        assert role == "Vector Embeddings"

    def test_token_boundary_prevents_mini_false_positive(self):
        agent = ModelScavengerAgent()
        assert agent._has_token("gemini-2.5", "mini") is False
        assert agent._has_token("gpt-4o-mini", "mini") is True
        assert agent._has_token("proprietary", "pro") is False
        assert agent._has_token("gemini-2.5-pro", "pro") is True


class TestFuzzyBenchmarks:
    def test_enriches_claude_sonnet(self):
        from src.services.cognitive_mesh.benchmarks import fuzzy_enrich_benchmarks
        bm = fuzzy_enrich_benchmarks("claude-3-5-sonnet")
        assert bm["mmlu_pro"] == 88.0
        assert bm["human_eval"] == 93.0

    def test_enriches_deepseek_r1(self):
        from src.services.cognitive_mesh.benchmarks import fuzzy_enrich_benchmarks
        bm = fuzzy_enrich_benchmarks("deepseek-r1:14b")
        assert bm["mmlu_pro"] == 84.0
        assert bm["ttft_ms"] == 600

    def test_unknown_model_returns_empty(self):
        from src.services.cognitive_mesh.benchmarks import fuzzy_enrich_benchmarks
        assert fuzzy_enrich_benchmarks("totally-unknown-model") == {}

    def test_scavenger_applies_fuzzy_benchmarks(self):
        agent = ModelScavengerAgent()
        m = ScavengedModel(model="qwen2.5:14b", parameter_count_b=14.0, source="ollama")
        agent._apply_fuzzy_benchmarks(m)
        assert m.mmlu_pro == 70.5
        assert m.ttft_ms == 350


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
