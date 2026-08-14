# -*- coding: utf-8 -*-
"""
Module: test_openreview_source.py
Project: TALOS v5.10.0
Description:
    Unit tests for the OpenReview source agent (src/ingestion/openreview.py).
    Covers configuration-driven initialization (authenticated, guest, and
    disabled), content-field extraction, standardized paper formatting with
    peer-review metadata enrichment, and graceful degradation when the
    optional openreview-py client library is absent.

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

from src.ingestion import openreview as openreview_source


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
                openreview_source.OpenReviewSource({})
        mock_client_cls.assert_called_once_with(
            baseurl=openreview_source.OpenReviewSource.BASE_URL
        )

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
