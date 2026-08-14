# -*- coding: utf-8 -*-
"""
Module: test_openaire_source.py
Project: TALOS v5.10.0
Description:
    Unit tests for the OpenAIRE source agent (src/ingestion/openaire.py).
    Covers optional bearer-token header construction, nested payload
    navigation, standardized paper formatting with grant/funding metadata
    enrichment, and paginated fetching with mocked HTTP responses.

    Key design decisions:
    - Hermetic: all requests.get calls are mocked; no live API traffic.
    - Follows the mock-first convention established in tests/test_multi_tier.py.

Dependencies:
    - unittest.mock: Patching requests.get and environment variables.
    - requests: Access to requests.exceptions for error-path simulation.
"""
import os

import requests
from unittest.mock import patch, MagicMock

from src.ingestion.openaire import OpenAIRESource


def _result(**overrides):
    """Build a minimal OpenAIRE researchProducts result payload."""
    result = {
        "title": ["A Sample Paper"],
        "creator": ["A. Author", "B. Author"],
        "description": ["A sample abstract."],
        "originalId": ["10.1234/abc", "internal-id"],
        "pid": ["https://doi.org/10.1234/abc"],
        "dateofacceptance": "2024-03-01",
    }
    result.update(overrides)
    return {"metadata": {"oaf:entity": {"oaf:result": result}}}


class TestInit:
    """Tests for OpenAIRESource.__init__ configuration handling."""

    def test_no_token_headers_empty(self):
        with patch.dict(os.environ, {}, clear=True):
            src = OpenAIRESource({})
        assert src.headers == {}

    def test_bearer_token_from_openaire_token(self):
        with patch.dict(os.environ, {"OPENAIRE_TOKEN": "tok123"}, clear=True):
            src = OpenAIRESource({})
        assert src.headers == {"Authorization": "Bearer tok123"}

    def test_bearer_token_from_openaire_api_key(self):
        with patch.dict(os.environ, {"OPENAIRE_API_KEY": "key456"}, clear=True):
            src = OpenAIRESource({})
        assert src.headers == {"Authorization": "Bearer key456"}

    def test_config_defaults(self):
        config = {"openaire_query": "swarm", "days_to_search_daily": 3,
                  "max_results_config": {"openaire": 42}}
        with patch.dict(os.environ, {}, clear=True):
            src = OpenAIRESource(config)
        assert src.query == "swarm"
        assert src.days_to_search == 3
        assert src.total_max_results == 42
        assert src.enabled is True


class TestHelpers:
    """Tests for the _first, _extract_result, and _extract_funding helpers."""

    def test_first_with_list(self):
        assert OpenAIRESource._first(["", "x", "y"]) == "x"

    def test_first_with_empty_list(self):
        assert OpenAIRESource._first([], "dflt") == "dflt"

    def test_first_with_scalar(self):
        assert OpenAIRESource._first("hello") == "hello"

    def test_first_with_none(self):
        assert OpenAIRESource._first(None, "dflt") == "dflt"

    def test_extract_result_nested(self):
        src = OpenAIRESource({"openaire_query": "q"})
        assert src._extract_result(_result())["title"] == ["A Sample Paper"]

    def test_extract_result_missing_returns_empty(self):
        src = OpenAIRESource({"openaire_query": "q"})
        assert src._extract_result({}) == {}

    def test_extract_funding_empty(self):
        src = OpenAIRESource({"openaire_query": "q"})
        assert src._extract_funding(None) == ""
        assert src._extract_funding({}) == ""

    def test_extract_funding_projects(self):
        src = OpenAIRESource({"openaire_query": "q"})
        projects = {"project": [{"code": "101", "acronym": "ABC", "funder": "EC"}]}
        summary = src._extract_funding(projects)
        assert "grant 101" in summary
        assert "ABC" in summary
        assert "funded by EC" in summary

    def test_extract_funding_single_dict(self):
        src = OpenAIRESource({"openaire_query": "q"})
        assert "grant 202" in src._extract_funding({"project": {"code": "202"}})


class TestFormatPaper:
    """Tests for the _format_paper standardized mapping."""

    def test_full_mapping_and_funding_enrichment(self):
        src = OpenAIRESource({"openaire_query": "q"})
        item = _result(projects={"project": [{"code": "101", "acronym": "ABC",
                                              "funder": "EC"}]})
        paper = src._format_paper(item)
        assert paper["source"] == "OpenAIRE"
        assert paper["title"] == "A Sample Paper"
        assert paper["authors_str"] == "A. Author, B. Author"
        assert paper["doi"] == "10.1234/abc"
        assert paper["url"] == "https://doi.org/10.1234/abc"
        assert paper["publication_year"] == 2024
        assert "[OpenAIRE funding:" in paper["abstract"]

    def test_doi_fallback_url(self):
        src = OpenAIRESource({"openaire_query": "q"})
        item = _result(pid=[])
        paper = src._format_paper(item)
        assert paper["url"] == "https://doi.org/10.1234/abc"

    def test_missing_title_returns_none(self):
        src = OpenAIRESource({"openaire_query": "q"})
        assert src._format_paper(_result(title=[])) is None


class TestFetchAndSearch:
    """Tests for paginated fetching with mocked HTTP responses."""

    @staticmethod
    def _mock_response(payload, status=200):
        resp = MagicMock()
        resp.status_code = status
        resp.json.return_value = payload
        resp.raise_for_status.return_value = None
        return resp

    def test_fetch_new_papers_success(self):
        src = OpenAIRESource({"openaire_query": "q", "days_to_search_daily": 7})
        payload = {"response": {"results": {"total": {"$": 1}, "result": [_result()]}}}
        with patch("requests.get", return_value=self._mock_response(payload)):
            papers = src.fetch_new_papers()
        assert len(papers) == 1
        assert papers[0]["source"] == "OpenAIRE"

    def test_fetch_new_papers_rate_limit_then_success(self):
        src = OpenAIRESource({"openaire_query": "q"})
        payload = {"response": {"results": {"total": {"$": 1}, "result": [_result()]}}}
        responses = [self._mock_response({}, status=429), self._mock_response(payload)]
        with patch("requests.get", side_effect=responses), \
                patch("time.sleep", return_value=None) as mock_sleep:
            papers = src.fetch_new_papers()
        assert len(papers) == 1
        mock_sleep.assert_called()

    def test_fetch_new_papers_request_error_returns_empty(self):
        src = OpenAIRESource({"openaire_query": "q"})
        with patch("requests.get",
                   side_effect=requests.exceptions.ConnectionError("boom")):
            assert src.fetch_new_papers() == []

    def test_search_papers_success(self):
        src = OpenAIRESource({"openaire_query": "q"})
        payload = {"response": {"results": {"result": [_result()]}}}
        with patch("requests.get", return_value=self._mock_response(payload)):
            assert len(src.search_papers("query", limit=3)) == 1

    def test_search_papers_request_error_returns_empty(self):
        src = OpenAIRESource({"openaire_query": "q"})
        with patch("requests.get",
                   side_effect=requests.exceptions.ConnectionError("boom")):
            assert src.search_papers("query") == []
