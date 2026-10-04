# -*- coding: utf-8 -*-
"""
Module: test_codebase_documenter.py
Project: TALOS v5.25.0
Description:
    Hermetic unit tests for the codebase documentation subsystem. Verifies the
    AST analyzer extracts 112+ modules with class and function signatures, the
    architecture ledger persists decisions and a symbol table, and the relay
    orchestrator dry-run emits Markdown and HTML without any model dispatch.

Dependencies:
    - pytest: Test framework.
    - src.utils.codebase_documenter: the subsystem under test.
    - src.services.cognitive_mesh.xai_ledger: XAiDecisionLedger.
"""

import os

import pytest

from src.services.cognitive_mesh.xai_ledger import XAiDecisionLedger
from src.utils.codebase_documenter import (
    ArchitectureLedger,
    CodebaseAstAnalyzer,
    CodebaseDocGenerator,
    MultiLlmRelayOrchestrator,
)


class TestCodebaseAstAnalyzer:
    def test_discovers_112_plus_modules(self):
        analyzer = CodebaseAstAnalyzer()
        modules = analyzer.discover_modules()
        assert len(modules) >= 112

    def test_analyze_all_extracts_signatures(self):
        analyzer = CodebaseAstAnalyzer()
        analyses = analyzer.analyze_all()
        assert len(analyses) >= 112
        talos = analyses.get("talos.py")
        assert talos is not None
        assert len(talos.functions) > 0

    def test_dependency_graph_built(self):
        analyzer = CodebaseAstAnalyzer()
        analyses = analyzer.analyze_all()
        graph = analyzer.build_dependency_graph(analyses)
        assert isinstance(graph, dict)
        assert len(graph) >= 112


class TestArchitectureLedger:
    def test_record_and_retrieve_decision(self, tmp_path):
        ledger = ArchitectureLedger(os.path.join(str(tmp_path), "ledger.json"))
        ledger.record_decision("m.py", "documented", "because")
        assert len(ledger.decisions()) == 1

    def test_symbols_and_documented_tracking(self, tmp_path):
        ledger = ArchitectureLedger(os.path.join(str(tmp_path), "ledger.json"))
        ledger.mark_documented("a.py")
        ledger.register_symbols("a.py", ["Foo"], ["bar"])
        assert "a.py" in ledger.documented_modules()
        assert ledger.symbol_table()["a.py"]["classes"] == ["Foo"]
        assert ledger.get_undocumented(["a.py", "b.py"]) == ["b.py"]


class TestRelayOrchestratorDryRun:
    def test_dry_run_generates_docs(self, tmp_path):
        out = str(tmp_path)
        orch = MultiLlmRelayOrchestrator(
            generator=CodebaseDocGenerator(output_dir=out),
            xai_ledger=XAiDecisionLedger(os.path.join(out, "xai.jsonl")),
            architecture_ledger=ArchitectureLedger(os.path.join(out, "ledger.json")),
        )
        result = orch.run(mode="dry_run", dry_run=True, limit=3)
        assert result["modules"] == 3
        assert os.path.exists(result["markdown"])
        assert os.path.exists(result["html"])
        assert result["xai_records"] == 3
