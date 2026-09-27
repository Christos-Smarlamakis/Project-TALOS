# -*- coding: utf-8 -*-
"""
Module: test_research_setup_wizard.py
Project: TALOS v5.12.1
Description:
    Hermetic unit tests for the Research Setup Wizard. Verifies three contract
    areas without any live Ollama, Fast Edge, or FastAPI dependency:

    1. Sentinel detection and creation (data/.talos_onboarded).
    2. Cognitive validation and heuristic bypass fallback paths.
    3. Execution strategy and search-window selection persistence.

    Key design decisions:
    - All filesystem side effects are isolated into pytest tmp_path fixtures so
      the tests never touch the real config.json, .env, or data/ directory.
    - LLM-dependent paths are exercised only through the heuristic fallback or
      via monkeypatched mocks of _call_llm_text, keeping the suite deterministic.

Dependencies:
    - pytest: test framework and tmp_path/monkeypatch fixtures.
    - src.utils.research_setup_wizard: the module under test.
"""
import os
import json

import pytest

from src.utils import research_setup_wizard as wizard


class TestSentinel:
    """Sentinel detection and creation (data/.talos_onboarded)."""

    def test_sentinel_path_resolves_under_data(self, tmp_path):
        path = wizard._sentinel_path(str(tmp_path))
        assert path.endswith(os.path.join("data", ".talos_onboarded"))

    def test_sentinel_absent_initially(self, tmp_path):
        assert wizard._sentinel_exists(str(tmp_path)) is False

    def test_sentinel_created_and_detected(self, tmp_path):
        wizard._create_sentinel(str(tmp_path))
        assert wizard._sentinel_exists(str(tmp_path)) is True
        assert os.path.exists(wizard._sentinel_path(str(tmp_path)))


class TestCognitiveValidation:
    """Cognitive scope validation and heuristic bypass paths."""

    def test_too_brief_topic(self):
        result = wizard._analyze_scope_heuristic("drones")
        assert result["too_brief"] is True
        assert result["words"] < wizard.MIN_WORDS

    def test_sufficient_topic(self):
        result = wizard._analyze_scope_heuristic(
            "spatio-temporal attention for cooperative drone swarms")
        assert result["too_brief"] is False

    def test_empty_topic(self):
        result = wizard._analyze_scope_heuristic("")
        assert result["too_brief"] is True

    def test_subdomain_suggestions_returns_three(self):
        suggestions = wizard._suggest_subdomains_heuristic("drone swarms")
        assert len(suggestions) == 3

    def test_llm_scope_bypass_returns_none(self, monkeypatch):
        monkeypatch.setattr(wizard, "_call_llm_text", lambda *a, **k: None)
        assert wizard._analyze_scope_with_llm("drones") is None

    def test_llm_scope_sufficient_returns_no_subdomains(self, monkeypatch):
        monkeypatch.setattr(wizard, "_call_llm_text", lambda *a, **k: "SUFFICIENT")
        result = wizard._analyze_scope_with_llm("a valid topic")
        assert result is not None
        assert result["subdomains"] == []


class TestQueryGeneration:
    """Deterministic heuristic query/criteria generation."""

    def test_heuristic_generates_16_queries_and_criteria(self):
        config = {}
        wizard._generate_queries_heuristic(
            "spatio-temporal attention for drone swarms", config)
        for key in wizard.SOURCE_QUERY_KEYS:
            assert key in config and config[key]
        assert "inclusion_criteria" in config
        assert "exclusion_criteria" in config
        assert "AND" in config["ieee_query"]


class TestPersistence:
    """Execution strategy and search-window selection persistence."""

    def test_search_window_persisted(self, tmp_path):
        config = {}
        path = os.path.join(str(tmp_path), "config.json")
        assert wizard._write_search_window(config, path, "standard") is True
        with open(path, encoding="utf-8") as f:
            saved = json.load(f)
        assert saved["research_search_window"] == "standard"
        assert saved["days_to_search_historic"] == 1825
        assert saved["search_window_start_year"] == 2021
        assert saved["search_window_end_year"] == 2026

    def test_search_window_invalid_key(self, tmp_path):
        config = {}
        path = os.path.join(str(tmp_path), "config.json")
        assert wizard._write_search_window(config, path, "bogus") is False

    def test_execution_strategy_env_written(self, tmp_path):
        env_path = os.path.join(str(tmp_path), ".env")
        with open(env_path, "w", encoding="utf-8") as f:
            f.write("TALOS_NETWORK_STRATEGY=local_first\n")
        assert wizard._apply_execution_strategy("strict_local", str(tmp_path)) is True
        with open(env_path, encoding="utf-8") as f:
            content = f.read()
        assert "TALOS_NETWORK_STRATEGY=strict_local" in content
        assert "TALOS_ALLOW_CLOUD_FALLBACK=0" in content

    def test_execution_strategy_invalid_key(self, tmp_path):
        assert wizard._apply_execution_strategy("bogus", str(tmp_path)) is False

    def test_update_env_key_writes_without_quotes(self, tmp_path):
        env_path = os.path.join(str(tmp_path), ".env")
        with open(env_path, "w", encoding="utf-8") as f:
            f.write("")
        wizard._update_env_key(env_path, "TALOS_NETWORK_STRATEGY", "local_first")
        with open(env_path, encoding="utf-8") as f:
            content = f.read()
        assert "TALOS_NETWORK_STRATEGY=local_first" in content
        assert "='local_first'" not in content
