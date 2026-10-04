# -*- coding: utf-8 -*-
"""
Module: test_xai_ledger.py
Project: TALOS v5.25.0
Description:
    Hermetic unit tests for ``XAiDecisionLedger``. Verifies append-only JSONL
    persistence, rationale generation, and audit-trail extraction with zero
    network I/O and zero database access.

Dependencies:
    - pytest: Test framework.
    - src.services.cognitive_mesh.xai_ledger: XAiDecisionLedger.
    - src.services.cognitive_mesh.dto: XAiDecisionRecord.
"""

import os

import pytest

from src.services.cognitive_mesh.dto import XAiDecisionRecord
from src.services.cognitive_mesh.xai_ledger import XAiDecisionLedger


@pytest.fixture
def ledger(tmp_path):
    return XAiDecisionLedger(os.path.join(str(tmp_path), "xai.jsonl"))


class TestXAiDecisionLedger:
    def test_append_persists_jsonl(self, ledger):
        record = XAiDecisionRecord(
            task_type="parsing", swarm_size=1, complexity_score=0.1
        )
        written = ledger.append(record)
        assert written["decision_id"]
        assert written["timestamp"]
        records = ledger.latest(10)
        assert len(records) == 1
        assert records[0]["task_type"] == "parsing"

    def test_latest_respects_limit(self, ledger):
        for i in range(5):
            ledger.append({"task_type": "task_{}".format(i), "swarm_size": 1})
        assert len(ledger.latest(3)) == 3
        assert len(ledger.latest(100)) == 5

    def test_append_accepts_plain_dict(self, ledger):
        ledger.append({"task_type": "summarization"})
        records = ledger.latest(1)
        assert records[0]["task_type"] == "summarization"
        assert "decision_id" in records[0]
        assert "timestamp" in records[0]

    def test_explain_generates_rationale(self, ledger):
        record = {
            "task_type": "deep_synthesis",
            "complexity_score": 0.9,
            "swarm_size": 5,
            "candidate_models": ["model_a", "model_b"],
            "pareto_rationale": "high reasoning depth",
        }
        text = ledger.explain(record)
        assert "deep_synthesis" in text
        assert "0.900" in text
        assert "5" in text
        assert "model_a" in text

    def test_explain_handles_empty_record(self, ledger):
        text = ledger.explain({})
        assert "general" in text
