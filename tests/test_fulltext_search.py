# -*- coding: utf-8 -*-
"""
Module: test_fulltext_search.py
Project: TALOS v5.19.0
Description:
    Hermetic unit tests for the SQLite FTS5 full-text search engine. Verifies
    that the ``papers_fts`` virtual table is created, that ``index_paper``
    populates it, and that ``search_fulltext`` executes an FTS5 ``MATCH`` query
    with BM25 ranking and snippet highlighting. All tests operate on an isolated
    temporary SQLite database with zero external dependencies.

    Key design decisions:
    - A dedicated temporary database file isolates the FTS5 table from the live
      profile database.
    - The ``snippet()`` auxiliary function is asserted to return a highlighted
      match containing the queried term.

Dependencies:
    - os / tempfile: isolated database path.
    - sqlite3: minimal papers table fixture.
    - src.search.fulltext_search: the engine under test.
"""

import os
import sqlite3
import tempfile

import pytest

from src.search.fulltext_search import FullTextSearchEngine


@pytest.fixture
def engine(tmp_path):
    """Build a FullTextSearchEngine over an isolated temporary database."""
    db_path = str(tmp_path / "talos_test.db")
    conn = sqlite3.connect(db_path)
    conn.execute("CREATE TABLE papers (id INTEGER PRIMARY KEY, title TEXT)")
    conn.execute("INSERT INTO papers (id, title) VALUES (1, 'UAV Swarm Planning')")
    conn.commit()
    conn.close()
    return FullTextSearchEngine(db_path=db_path), db_path


class TestFTS5Engine:
    """Verify the FTS5 virtual table, indexing, and snippet query."""

    def test_virtual_table_created(self, engine):
        fts, db_path = engine
        conn = sqlite3.connect(db_path)
        row = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='papers_fts'"
        ).fetchone()
        conn.close()
        assert row is not None
        assert row[0] == "papers_fts"

    def test_index_and_search_returns_snippet(self, engine):
        fts, _ = engine
        fts.index_paper(
            1,
            "UAV Swarm Planning",
            "The methodology applies deep reinforcement learning for cooperative "
            "UAV mission planning under uncertainty.",
        )
        results = fts.search_fulltext("reinforcement learning", limit=5)
        assert len(results) == 1
        assert results[0]["paper_id"] == 1
        assert "reinforcement" in results[0]["snippet"]
        assert results[0]["page"] >= 1

    def test_search_no_match_returns_empty(self, engine):
        fts, _ = engine
        fts.index_paper(1, "UAV Swarm Planning", "A short abstract with no keywords.")
        results = fts.search_fulltext("zzzz_nonexistent_term_zzzz", limit=5)
        assert results == []

    def test_empty_query_returns_empty(self, engine):
        fts, _ = engine
        assert fts.search_fulltext("   ") == []
