# -*- coding: utf-8 -*-
"""
Module: test_session_circuit_breaker.py
Project: TALOS v5.15.3
Description:
    Hermetic unit tests for the v5.15.3 reliability hardening:

    1. The Session-Level Circuit Breaker in ``AIManager``: once the CPU edge
       endpoint (port 11435) fails with a connection error, the
       ``fast_tier_offline`` latch is set for the process lifetime and every
       subsequent fast-tier request bypasses port 11435 with ZERO network
       attempts.

    2. The multi-key author normalizer ``normalize_authors``: verifies that
       every author representation produced across the 18-source ingestion
       mesh resolves to a clean comma-separated string instead of the false
       "Unknown Authors" fallback.

    All tests are hermetic -- no live Ollama, no SYNAPSE bus, no network.

Dependencies:
    - pytest: Test framework.
    - unittest.mock: Patching HTTP requests and session objects.
"""
import os
import pytest
from unittest.mock import patch, MagicMock

import requests

from src.utils.evaluation_history import normalize_authors


# ------------------------------------------------------------------
# -- Author Normalization Tests (verification gate 4) --
# ------------------------------------------------------------------

class TestAuthorNormalization:
    """Verify multi-key author resolution eliminates "Unknown Authors" fallbacks."""

    def test_flat_authors_str(self):
        assert normalize_authors({"authors_str": "Alice, Bob"}) == "Alice, Bob"

    def test_list_of_dicts_name_key(self):
        paper = {"authors": [{"name": "Alice"}, {"name": "Bob"}]}
        assert normalize_authors(paper) == "Alice, Bob"

    def test_list_of_strings(self):
        paper = {"authors": ["Alice", "Bob"]}
        assert normalize_authors(paper) == "Alice, Bob"

    def test_openalex_nested_author_display_name(self):
        paper = {"authors": [{"author": {"display_name": "Alice Smith"}}]}
        assert normalize_authors(paper) == "Alice Smith"

    def test_full_name_key(self):
        paper = {"authors": [{"full_name": "Alice Smith"}, {"full_name": "Bob Jones"}]}
        assert normalize_authors(paper) == "Alice Smith, Bob Jones"

    def test_singular_author_key(self):
        paper = {"author": "Alice, Bob"}
        assert normalize_authors(paper) == "Alice, Bob"

    def test_semicolon_delimited_string(self):
        paper = {"authors": "Alice; Bob; Carol"}
        assert normalize_authors(paper) == "Alice, Bob, Carol"

    def test_missing_authors_falls_back(self):
        assert normalize_authors({}) == "Unknown Authors"

    def test_non_dict_falls_back(self):
        assert normalize_authors(None) == "Unknown Authors"

    def test_empty_list_falls_back(self):
        assert normalize_authors({"authors": []}) == "Unknown Authors"


# ------------------------------------------------------------------
# -- Session Circuit Breaker Latching Tests (verification gate 5) --
# ------------------------------------------------------------------

class TestSessionCircuitBreaker:
    """Verify the fast tier latches offline after one failure with zero re-probes."""

    @pytest.fixture
    def aimanager(self):
        """Create an AIManager with model verification and router init patched."""
        config = {
            "ai_provider_priority": ["local"],
            "pre_screening_model": "gemini-2.5-flash-lite",
            "model_for_daily_search": "gemini-2.5-pro",
            "pre_screening_prompt": "Evaluate this paper.",
            "failure_threshold": 4,
        }
        with patch.dict(os.environ, {
            "TALOS_USE_LOCAL": "1",
            "LOCAL_MODEL_NAME": "gemma3:12b",
            "TALOS_MODELS_VERIFIED": "1",
        }, clear=False):
            ai_module = __import__('src.core.ai_manager', fromlist=['AIManager'])
            with patch.object(
                ai_module.AIManager, '_ensure_local_model', return_value=None
            ), patch.object(
                ai_module.AIManager, '_init_router', return_value=MagicMock()
            ):
                return ai_module.AIManager(config)

    @staticmethod
    def _gpu_response():
        """Build a mock 200 response for the GPU Ollama endpoint."""
        resp = MagicMock()
        resp.status_code = 200
        resp.json.return_value = {
            "choices": [{"message": {"content": "Evaluated."}}]
        }
        resp.text = ""
        return resp

    def test_latches_offline_after_first_connection_failure(self, aimanager):
        """After one 11435 failure, fast_tier_offline is latched True."""
        calls = []

        def fake_post(url, *args, **kwargs):
            calls.append(url)
            if "11435" in url:
                raise requests.exceptions.ConnectionError("Connection refused")
            return self._gpu_response()

        assert aimanager.fast_tier_offline is False
        with patch.object(aimanager._local_session, "post", side_effect=fake_post):
            result = aimanager._execute_ollama_http(
                "Test prompt", response_format="text", use_edge=True
            )
        assert result == "Evaluated."
        assert aimanager.fast_tier_offline is True
        # First call: one probe to 11435 (failure) + one GPU fallback to 11434.
        assert sum(1 for u in calls if "11435" in u) == 1

    def test_zero_reprobe_after_latch(self, aimanager):
        """Once latched, subsequent fast-tier calls never touch 11435."""
        calls = []

        def fake_post(url, *args, **kwargs):
            calls.append(url)
            if "11435" in url:
                raise requests.exceptions.ConnectionError("Connection refused")
            return self._gpu_response()

        with patch.object(aimanager._local_session, "post", side_effect=fake_post):
            # First call: latches offline.
            aimanager._execute_ollama_http(
                "Prompt 1", response_format="text", use_edge=True
            )
            calls.clear()
            # Subsequent calls: must bypass 11435 entirely.
            aimanager._execute_ollama_http(
                "Prompt 2", response_format="text", use_edge=True
            )
            aimanager._execute_ollama_http(
                "Prompt 3", response_format="text", use_edge=True
            )

        assert aimanager.fast_tier_offline is True
        assert sum(1 for u in calls if "11435" in u) == 0
        # All subsequent calls route directly to GPU (11434).
        assert all("11434" in u for u in calls)
