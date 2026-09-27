# -*- coding: utf-8 -*-
"""
Module: test_openreview_source.py
Project: TALOS v5.11.3
Description:
    Unit tests for the OpenReview source agent (src/ingestion/openreview_source.py).
    Covers configuration-driven initialization (authenticated, guest, and
    disabled), content-field extraction, standardized paper formatting with
    peer-review metadata enrichment, graceful degradation when the optional
    openreview-py client library is absent, and the v5.11.3 version-tolerant
    V2 note-query dispatch ladder (_query_notes).

    Key design decisions:
    - Hermetic: no live OpenReview API calls. The optional client and the
      OPENREVIEW_AVAILABLE flag are mocked.
    - Follows the mock-first convention established in tests/test_multi_tier.py.

Dependencies:
    - pytest: Test framework and fixtures.
    - unittest.mock: Patching the optional client and environment variables.
    - types: SimpleNamespace stubs for Note objects.
"""
import os
from types import SimpleNamespace

import pytest
from unittest.mock import patch, MagicMock

# -- v5.11.3: module-level import is required for patch.object() targeting. --
from src.ingestion import openreview_source
from src.ingestion.openreview_source import OpenReviewSource


class FakeField:
    """Stub for an OpenReview V2 content field object exposing a .value."""

    def __init__(self, value):
        self.value = value


def _make_note(title="A Title", authors=None, abstract="An abstract",
               decision=None, rating=None, recommendation=None, venue=None,
               doi=None, note_id="note123", forum="forum123",
               cdate=1700000000000):
    """Build a stub OpenReview Note with realistic content fields."""
    content = {
        "title": FakeField(title),
        "authors": authors if authors is not None else ["A. Author", "B. Author"],
        "abstract": FakeField(abstract),
    }
    if decision is not None:
        content["decision"] = FakeField(decision)
    if rating is not None:
        content["rating"] = FakeField(rating)
    if recommendation is not None:
        content["recommendation"] = FakeField(recommendation)
    if venue is not None:
        content["venue"] = FakeField(venue)
    if doi is not None:
        content["doi"] = FakeField(doi)
    return SimpleNamespace(content=content, id=note_id, forum=forum, cdate=cdate)


@pytest.fixture
def disabled_source():
    """An OpenReviewSource constructed in the no-library (disabled) state."""
    with patch.object(openreview_source, "OPENREVIEW_AVAILABLE", False):
        return openreview_source.OpenReviewSource({})


class TestInit:
    """Tests for OpenReviewSource.__init__ configuration handling."""

    def test_disabled_when_library_missing(self):
        with patch.object(openreview_source, "OPENREVIEW_AVAILABLE", False):
            src = openreview_source.OpenReviewSource({})
        assert src.enabled is False
        assert src.client is None

    def test_guest_client_without_credentials(self):
        with patch.object(openreview_source, "OPENREVIEW_AVAILABLE", True):
            mock_client_cls = MagicMock()
            with patch.object(openreview_source, "openreview") as mock_lib, \
                    patch.dict(os.environ, {}, clear=True):
                mock_lib.api.OpenReviewClient = mock_client_cls
                src = openreview_source.OpenReviewSource({})
        mock_client_cls.assert_called_once_with(
            baseurl=openreview_source.OpenReviewSource.BASE_URL
        )
        assert src.enabled is True

    def test_authenticated_client_with_credentials(self):
        env = {"OPENREVIEW_USERNAME": "u", "OPENREVIEW_PASSWORD": "p"}
        with patch.object(openreview_source, "OPENREVIEW_AVAILABLE", True):
            mock_client_cls = MagicMock()
            with patch.object(openreview_source, "openreview") as mock_lib, \
                    patch.dict(os.environ, env, clear=True):
                mock_lib.api.OpenReviewClient = mock_client_cls
                openreview_source.OpenReviewSource({})
        mock_client_cls.assert_called_once_with(
            baseurl=openreview_source.OpenReviewSource.BASE_URL,
            username="u", password="p",
        )


class TestGetContentValue:
    """Tests for the _get_content_value field extraction helper."""

    def test_content_object_with_value(self, disabled_source):
        note = SimpleNamespace(content={"title": FakeField("Hello")})
        assert disabled_source._get_content_value(note, "title") == "Hello"

    def test_plain_dict_value(self, disabled_source):
        note = SimpleNamespace(content={"title": {"value": "World"}})
        assert disabled_source._get_content_value(note, "title") == "World"

    def test_plain_scalar_value(self, disabled_source):
        note = SimpleNamespace(content={"year": 2024})
        assert disabled_source._get_content_value(note, "year") == 2024

    def test_missing_field_returns_default(self, disabled_source):
        note = SimpleNamespace(content={})
        assert disabled_source._get_content_value(note, "nope", "fallback") == "fallback"

    def test_no_content_attribute_returns_default(self, disabled_source):
        note = SimpleNamespace()
        assert disabled_source._get_content_value(note, "title", "dflt") == "dflt"


class TestFormatPaper:
    """Tests for the _format_paper standardized mapping."""

    def test_full_mapping_and_meta_enrichment(self, disabled_source):
        note = _make_note(decision="Accept", rating="8: clear accept",
                          venue="NeurIPS 2024", doi="10.5555/example")
        paper = disabled_source._format_paper(note)
        assert paper["source"] == "OpenReview"
        assert paper["title"] == "A Title"
        assert paper["authors_str"] == "A. Author, B. Author"
        assert paper["doi"] == "10.5555/example"
        assert paper["url"] == "https://openreview.net/forum?id=forum123"
        assert paper["publication_year"] == 2023
        assert "Peer-review decision: Accept" in paper["abstract"]
        assert "Rating: 8: clear accept" in paper["abstract"]
        assert "Venue: NeurIPS 2024" in paper["abstract"]

    def test_missing_title_returns_none(self, disabled_source):
        assert disabled_source._format_paper(_make_note(title=None)) is None


class TestFetchAndSearch:
    """Tests for graceful degradation of fetch/search paths."""

    def test_fetch_new_papers_returns_empty_when_disabled(self, disabled_source):
        assert disabled_source.fetch_new_papers() == []

    def test_search_papers_returns_empty_when_disabled(self, disabled_source):
        assert disabled_source.search_papers("query") == []

    def test_search_papers_returns_empty_on_client_error(self, disabled_source):
        disabled_source.enabled = True
        disabled_source.client = MagicMock()
        disabled_source.client.get_notes.side_effect = RuntimeError("boom")
        assert disabled_source.search_papers("query") == []


class TestQueryNotesDispatch:
    """Tests for the v5.11.3 version-tolerant V2 note-query dispatch ladder."""

    def test_search_notes_preferred_when_available(self, disabled_source):
        """Clients exposing search_notes use the dedicated V2 search endpoint."""
        disabled_source.enabled = True
        disabled_source.client = MagicMock()
        disabled_source.client.search_notes.return_value = [_make_note()]
        results = disabled_source.search_papers("query")
        disabled_source.client.search_notes.assert_called_once_with(
            term="query", limit=5
        )
        assert len(results) == 1
        assert results[0]["title"] == "A Title"

    def test_content_query_when_search_notes_missing(self, disabled_source):
        """Clients without search_notes fall back to a content-field query."""
        disabled_source.enabled = True
        client = MagicMock(spec=["get_notes"])
        client.get_notes.return_value = [_make_note()]
        disabled_source.client = client
        results = disabled_source.search_papers("query")
        client.get_notes.assert_called_once_with(
            content={"title": "query"}, limit=5
        )
        assert len(results) == 1

    def test_typeerror_falls_back_to_bare_get_notes(self, disabled_source):
        """A TypeError from mixed client versions retries with limit only."""
        disabled_source.enabled = True
        disabled_source.client = MagicMock()
        disabled_source.client.search_notes.side_effect = TypeError(
            "unexpected keyword argument 'term'"
        )
        disabled_source.client.get_notes.return_value = [
            _make_note(title="Fallback Paper")
        ]
        results = disabled_source.search_papers("query")
        disabled_source.client.get_notes.assert_called_once_with(limit=5)
        assert [p["title"] for p in results] == ["Fallback Paper"]

    def test_fetch_uses_dispatch_with_pagination_kwargs(self, disabled_source):
        """fetch_new_papers passes offset and sort through the dispatcher."""
        disabled_source.enabled = True
        disabled_source.client = MagicMock()
        disabled_source.client.search_notes.return_value = []
        assert disabled_source.fetch_new_papers() == []
        disabled_source.client.search_notes.assert_called_once_with(
            term=disabled_source.query, limit=100, offset=0, sort="cdate:desc"
        )
