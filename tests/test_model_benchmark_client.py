# -*- coding: utf-8 -*-
"""
Module: test_model_benchmark_client.py
Project: TALOS v5.20.0
Description:
    Hermetic unit tests for the ModelBenchmarkClient. Verifies the four-role
    top-model pairing, the local RTX 4070 budget reconciliation contract, and
    offline cache persistence. No live endpoints are contacted.

Dependencies:
    - pytest: Test framework.
    - src.core.model_benchmark_client: The module under test.
"""

from src.core.model_benchmark_client import ModelBenchmarkClient


class TestTopModelsByRole:
    def test_returns_all_four_roles(self):
        result = ModelBenchmarkClient().get_top_models_by_role()
        assert set(result.keys()) == {
            "fast_screening", "rigorous_audit", "code_audit", "vector_embeddings",
        }

    def test_each_role_has_model_and_provider(self):
        result = ModelBenchmarkClient().get_top_models_by_role()
        for info in result.values():
            assert info["model"]
            assert info["provider"]

    def test_fast_screening_prefers_low_ttft(self):
        result = ModelBenchmarkClient().get_top_models_by_role()
        assert result["fast_screening"]["ttft_ms"] <= result["rigorous_audit"]["ttft_ms"]


class TestLocalReconciliation:
    def test_reconcile_returns_mapping(self):
        local_map = ModelBenchmarkClient().reconcile_local_budget()
        assert isinstance(local_map, dict)


class TestOfflineCache:
    def test_refresh_offline_persists_cache(self, tmp_path):
        client = ModelBenchmarkClient(cache_path=str(tmp_path / "benchmarks.json"))
        summary = client.refresh(online=False)
        assert summary["record_count"] >= 9
        assert summary["mode"] == "air_gapped_seed"
        import os
        assert os.path.exists(client.cache_path)
