# -*- coding: utf-8 -*-
"""
Module: test_dblp_sanitizer.py
Project: TALOS v5.19.0
Description:
    Hermetic unit tests for the DBLP query sanitizer and JSON resilience in
    src/ingestion/sources/dblp_source.py. Verifies that complex Boolean
    queries are reduced to a clean 6-8 term keyword string and that invalid or
    HTML responses degrade to an empty list without raising JSONDecodeError.

Dependencies:
    - pytest: Test framework.
"""
import pytest

from src.ingestion.sources.dblp_source import DBLPSource


class TestDblpSanitizer:
    """Tests for _sanitize_dblp_query."""

    def test_strips_boolean_operators_parentheses_and_quotes(self):
        query = ('cooperative mission planning AND UAV swarms AND '
                 '(deep multi agent reinforcement learning OR spatio '
                 'temporal graph neural networks WITH attention mechanisms)')
        result = DBLPSource._sanitize_dblp_query(query)

        lowered = result.lower()
        assert "and" not in lowered
        assert "or" not in lowered
        assert "with" not in lowered
        assert "not" not in lowered
        assert "(" not in result
        assert ")" not in result
        assert '"' not in result

    def test_caps_at_eight_terms(self):
        query = "one two three four five six seven eight nine ten eleven"
        result = DBLPSource._sanitize_dblp_query(query)
        assert len(result.split()) <= 8

    def test_preserves_salient_terms(self):
        query = "cooperative mission planning UAV swarms deep learning"
        result = DBLPSource._sanitize_dblp_query(query)
        for term in ("cooperative", "mission", "planning", "UAV", "swarms"):
            assert term in result

    def test_empty_and_none_queries(self):
        assert DBLPSource._sanitize_dblp_query("") == ""
        assert DBLPSource._sanitize_dblp_query(None) == ""


class TestDblpJsonResilience:
    """Tests for graceful degradation on non-JSON responses."""

    class _FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            raise ValueError("Expecting value: line 1 column 1 (char 0)")

    class _FakeSession:
        def get(self, *args, **kwargs):
            return TestDblpJsonResilience._FakeResponse()

    def test_search_papers_returns_empty_on_invalid_json(self):
        source = DBLPSource.__new__(DBLPSource)
        source.session = self._FakeSession()
        source.base_url = "https://dblp.org/search/publ/api"

        result = source.search_papers("complex (Boolean) AND query")

        assert result == []
