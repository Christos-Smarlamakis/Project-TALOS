# -*- coding: utf-8 -*-
"""
Module: test_buffer_sync.py
Project: TALOS v5.24.0
Description:
    Unit tests for the distributed JSONL buffer sync engine
    (src/services/cognitive_mesh/buffer_sync.py). Verifies JSONL parsing,
    model deduplication, cache merging, and offline buffer export using an
    isolated temporary cache so the real benchmark store is never touched.

Dependencies:
    - pytest, json, pathlib: test framework and file fixtures.
    - src.services.cognitive_mesh.buffer_sync: BufferSyncEngine.
"""

import json
from pathlib import Path

import pytest

from src.services.cognitive_mesh.buffer_sync import BufferSyncEngine


def _write_jsonl(path, records):
    with open(path, "w", encoding="utf-8") as fh:
        for record in records:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")


class TestBufferSyncEngine:
    def test_ingest_parses_and_deduplicates(self, tmp_path):
        engine = BufferSyncEngine(cache_path=str(tmp_path / "cache.json"))
        buf = tmp_path / "hermes_buffer.jsonl"
        _write_jsonl(
            buf,
            [
                {"model": "model-a", "provider": "groq", "mmlu_pro": 66.0},
                {"model": "model-b", "provider": "deepseek", "mmlu_pro": 84.0},
                {"model": "model-a", "provider": "groq", "mmlu_pro": 70.0},
            ],
        )
        result = engine.ingest_jsonl_buffer(buf)
        assert result["parsed"] == 3
        assert result["deduplicated"] == 2
        assert result["skipped"] == 1
        assert result["merged"] == 2

    def test_ingest_missing_file_returns_zero(self, tmp_path):
        engine = BufferSyncEngine(cache_path=str(tmp_path / "cache.json"))
        result = engine.ingest_jsonl_buffer(tmp_path / "missing.jsonl")
        assert result["parsed"] == 0
        assert result["merged"] == 0

    def test_export_worker_buffer_writes_jsonl(self, tmp_path):
        engine = BufferSyncEngine(cache_path=str(tmp_path / "cache.json"))
        out = engine.export_worker_buffer(
            [{"model": "m1"}, {"model": "m2"}], tmp_path / "out.jsonl"
        )
        assert out.exists()
        lines = [l for l in out.read_text(encoding="utf-8").splitlines() if l]
        assert len(lines) == 2
        assert json.loads(lines[0])["model"] == "m1"

    def test_merge_persists_to_cache(self, tmp_path):
        engine = BufferSyncEngine(cache_path=str(tmp_path / "cache.json"))
        buf = tmp_path / "hermes_buffer.jsonl"
        _write_jsonl(
            buf,
            [{"model": "model-x", "provider": "ollama", "roles": ["code_audit"]}],
        )
        result = engine.ingest_jsonl_buffer(buf)
        assert result["merged"] == 1
        cache = Path(engine.cache_path)
        assert cache.exists()
        payload = json.loads(cache.read_text(encoding="utf-8"))
        records = payload.get("records") or payload.get("models")
        assert any(r.get("model") == "model-x" for r in records)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
