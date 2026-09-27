# -*- coding: utf-8 -*-
"""
Module: test_research_setup_wizard.py
Project: TALOS v5.12.2
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

    def test_heuristic_boolean_excludes_stopwords(self):
        config = {}
        wizard._generate_queries_heuristic(
            "spatio-temporal attention for drone swarms", config)
        assert config["ieee_query"] == "(spatio-temporal AND attention AND drone AND swarms)"

    def test_extract_salient_terms_strips_stopwords(self):
        terms = wizard._extract_salient_terms(
            "a framework for the cooperative drone swarms")
        assert terms == ["framework", "cooperative", "drone", "swarms"]

    def test_extract_salient_terms_preserves_hyphenated_compound(self):
        terms = wizard._extract_salient_terms("spatio-temporal modeling")
        assert terms[0] == "spatio-temporal"

    def test_llm_guidance_includes_language_mandate(self, monkeypatch):
        captured = {}

        def fake_evaluate(self, **kwargs):
            captured.update(kwargs)
            return {
                "arxiv_query": "drone swarms",
                "inclusion_criteria": "peer-reviewed studies",
                "exclusion_criteria": "non-empirical work",
            }

        mock_ai = type("MockAI", (), {"evaluate_paper_json": fake_evaluate})()
        monkeypatch.setattr(wizard, "_get_ai_manager", lambda: mock_ai)
        config = {"query_translator_prompt": "Act as Research Architect.",
                  "phd_focus_system_prompt": "core framework"}
        assert wizard._generate_queries_llm("drone swarms", config) is True
        guidance = captured.get("abstract", "")
        assert "LANGUAGE MANDATE" in guidance
        assert "SYNTAX CONSTRAINTS" in guidance
        assert "CRITERIA SPECIFICATION" in guidance
        assert "topic:" in guidance


class TestPersistence:
    """Execution strategy and search-window selection persistence."""

    def test_search_window_persisted(self, tmp_path):
        config = {}
        path = os.path.join(str(tmp_path), "config.json")
        assert wizard._write_search_window(config, path, "prisma_1825") is True
        with open(path, encoding="utf-8") as f:
            saved = json.load(f)
        assert saved["research_search_window"] == "prisma_1825"
        assert saved["days_to_search_historic"] == 1825
        assert saved["search_window_label"]

    def test_search_window_invalid_key(self, tmp_path):
        config = {}
        path = os.path.join(str(tmp_path), "config.json")
        assert wizard._write_search_window(config, path, "bogus") is False

    def test_search_windows_have_five_presets(self):
        assert set(wizard.SEARCH_WINDOWS.keys()) == {
            "rapid_30", "annual_365", "phd_1095", "prisma_1825", "decadal_3650"}
        assert wizard.SEARCH_WINDOWS["rapid_30"]["days"] == 30
        assert wizard.SEARCH_WINDOWS["annual_365"]["days"] == 365
        assert wizard.SEARCH_WINDOWS["phd_1095"]["days"] == 1095
        assert wizard.SEARCH_WINDOWS["prisma_1825"]["days"] == 1825
        assert wizard.SEARCH_WINDOWS["decadal_3650"]["days"] == 3650

    def test_search_window_custom_days(self, tmp_path):
        config = {}
        path = os.path.join(str(tmp_path), "config.json")
        assert wizard._write_search_window(config, path, "custom", 730) is True
        with open(path, encoding="utf-8") as f:
            saved = json.load(f)
        assert saved["research_search_window"] == "custom"
        assert saved["days_to_search_historic"] == 730
        assert "730" in saved["search_window_label"]

    def test_search_window_custom_invalid_days(self, tmp_path):
        config = {}
        path = os.path.join(str(tmp_path), "config.json")
        assert wizard._write_search_window(config, path, "custom", 0) is False
        assert wizard._write_search_window(config, path, "custom", None) is False
        assert wizard._write_search_window(config, path, "custom", -5) is False

    def test_prompt_custom_days_parses_integer(self, monkeypatch):
        class FakeQuestion:
            def ask(self):
                return "730"
        monkeypatch.setattr(wizard.questionary, "text", lambda *a, **k: FakeQuestion())
        assert wizard._prompt_custom_days() == 730

    def test_prompt_custom_days_rejects_non_integer(self, monkeypatch):
        answers = iter(["abc", "0", "-3", "1825"])
        class FakeQuestion:
            def ask(self):
                return next(answers)
        monkeypatch.setattr(wizard.questionary, "text", lambda *a, **k: FakeQuestion())
        assert wizard._prompt_custom_days() == 1825

    def test_prompt_custom_days_cancel(self, monkeypatch):
        class FakeQuestion:
            def ask(self):
                return None
        monkeypatch.setattr(wizard.questionary, "text", lambda *a, **k: FakeQuestion())
        assert wizard._prompt_custom_days() is None

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

    def test_execution_strategies_has_five_entries(self):
        keys = set(wizard.EXECUTION_STRATEGIES.keys())
        assert keys == {"strict_local", "local_first", "cloud_first",
                        "strict_cloud", "auto_dynamic"}
        for key, strategy in wizard.EXECUTION_STRATEGIES.items():
            assert strategy["network"] == key

    def test_execution_strategy_persists_to_config(self, tmp_path):
        config_path = os.path.join(str(tmp_path), "config.json")
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump({}, f)
        assert wizard._apply_execution_strategy("cloud_first", str(tmp_path)) is True
        with open(config_path, encoding="utf-8") as f:
            saved = json.load(f)
        assert saved["ai_execution_strategy"] == "cloud_first"

    def test_execution_strategy_all_five_persist_network(self, tmp_path):
        env_path = os.path.join(str(tmp_path), ".env")
        for key in ("strict_local", "local_first", "cloud_first",
                    "strict_cloud", "auto_dynamic"):
            with open(env_path, "w", encoding="utf-8") as f:
                f.write("")
            assert wizard._apply_execution_strategy(key, str(tmp_path)) is True
            with open(env_path, encoding="utf-8") as f:
                content = f.read()
            assert f"TALOS_NETWORK_STRATEGY={key}" in content

    def test_update_env_key_writes_without_quotes(self, tmp_path):
        env_path = os.path.join(str(tmp_path), ".env")
        with open(env_path, "w", encoding="utf-8") as f:
            f.write("")
        wizard._update_env_key(env_path, "TALOS_NETWORK_STRATEGY", "local_first")
        with open(env_path, encoding="utf-8") as f:
            content = f.read()
        assert "TALOS_NETWORK_STRATEGY=local_first" in content
        assert "='local_first'" not in content
