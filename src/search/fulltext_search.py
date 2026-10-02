# -*- coding: utf-8 -*-
"""
Module: fulltext_search.py
Project: TALOS v5.18.0
Description:
    SQLite FTS5 full-text search engine over locally cached paper bodies.
    ``FullTextSearchEngine`` creates and maintains the virtual table
    ``papers_fts(paper_id, title, fulltext_content)``, indexes extracted PDF
    text incrementally, and executes sub-millisecond FTS5 ``MATCH`` queries with
    snippet extraction and BM25 (Okapi) ranking.

    The engine is fully air-gapped: it reads extracted section text from the
    gitignored ``data/fulltext_cache/<id>/`` windows produced by
    ``src/ingestion/pdf_harvester/section_extractor.py`` and performs all
    matching inside the local SQLite process with zero external services.

    Results are returned as ranked dictionaries (paper_id, title, snippet, page,
    rank) and rendered in a styled Rich Table (``box.ROUNDED``) titled
    "SQLite FTS5 Full-Text Search Results".

    Key design decisions:
    - FTS5 uses the BM25 ranking function as its default relevance metric.
    - The ``snippet()`` auxiliary function highlights the exact matched sentence
      with ``<b>`` / ``</b>`` markers.
    - Query strings fall back to a quoted phrase search when FTS5 raises an
      operator-syntax error on raw input.

Dependencies:
    - os / pathlib: cache directory traversal.
    - sqlite3: FTS5 virtual table, MATCH queries, and snippet extraction.
    - rich: styled result table rendering.
"""

import os
import sqlite3

from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from rich.console import Console
    from rich.table import Table
    from rich import box
    RICH_AVAILABLE = True
except ImportError:  # pragma: no cover - rich not installed
    RICH_AVAILABLE = False

# -- Canonical cache directory (relative to the repository root). -- #
FULLTEXT_CACHE_RELPATH = os.path.join("data", "fulltext_cache")

# -- Approximate characters per rendered page (for page-number estimation). -- #
_CHARS_PER_PAGE = 3000


def _resolve_project_root() -> str:
    """Return the absolute repository root (the directory holding talos.py)."""
    current = os.path.abspath(os.path.dirname(__file__))
    while current and not os.path.exists(os.path.join(current, "talos.py")):
        parent = os.path.dirname(current)
        if parent == current:
            break
        current = parent
    return current

class FullTextSearchEngine:
    """SQLite FTS5 full-text search over cached paper full-text bodies.

    Attributes:
        db_path (str): Absolute path to the active profile SQLite database.
    """

    def __init__(self, db_path: Optional[str] = None):
        """Initialize the engine and ensure the FTS5 virtual table exists.

        Args:
            db_path (str, optional): Override the SQLite database path. Defaults
                to the active profile database.
        """
        self.db_path = db_path or self._resolve_active_db_path()
        self._ensure_fts_table()

    @staticmethod
    def _resolve_active_db_path() -> str:
        """Resolve the active profile database path."""
        from src.core.database_manager import DatabaseManager
        return DatabaseManager().db_path

    def _connect(self) -> sqlite3.Connection:
        """Open a new SQLite connection with dict-like row access."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    # -- Schema ----------------------------------------------------------- #
    def _ensure_fts_table(self) -> None:
        """Create the ``papers_fts`` FTS5 virtual table if absent."""
        with self._connect() as conn:
            conn.execute(
                "CREATE VIRTUAL TABLE IF NOT EXISTS papers_fts USING FTS5("
                "paper_id UNINDEXED, title, fulltext_content)"
            )
            conn.commit()

    # -- Indexing --------------------------------------------------------- #
    def index_paper(self, paper_id: int, title: str,
                    fulltext_content: Optional[str]) -> None:
        """Index (or replace) a single paper row in the FTS5 table.

        Args:
            paper_id (int): The paper row id.
            title (str): Paper title.
            fulltext_content (Optional[str]): Extracted full-text body.
        """
        content = fulltext_content or ""
        with self._connect() as conn:
            conn.execute("DELETE FROM papers_fts WHERE paper_id = ?", (paper_id,))
            conn.execute(
                "INSERT INTO papers_fts(paper_id, title, fulltext_content) "
                "VALUES (?, ?, ?)",
                (paper_id, title, content),
            )
            conn.commit()

    def index_from_cache(self) -> int:
        """Index all cached extracted section windows for papers in the database.

        Returns:
            int: Number of papers indexed.
        """
        root = Path(_resolve_project_root())
        cache_dir = root / FULLTEXT_CACHE_RELPATH
        indexed = 0
        if not cache_dir.is_dir():
            return indexed

        title_map = self._paper_titles()
        for paper_dir in cache_dir.iterdir():
            if not paper_dir.is_dir():
                continue
            paper_id = paper_dir.name
            if not paper_id.isdigit():
                continue
            parts = []
            for filename in (
                "methodology.txt", "experiments.txt",
                "code_availability.txt", "limitations.txt",
            ):
                path = paper_dir / filename
                if path.exists():
                    try:
                        parts.append(path.read_text(encoding="utf-8"))
                    except OSError:
                        continue
            body = "\n\n".join(part for part in parts if part.strip())
            if not body:
                continue
            self.index_paper(int(paper_id), title_map.get(int(paper_id), ""), body)
            indexed += 1
        return indexed

    def _paper_titles(self) -> Dict[int, str]:
        """Return a mapping of paper id to title from the papers table."""
        with self._connect() as conn:
            rows = conn.execute("SELECT id, title FROM papers").fetchall()
        return {int(row["id"]): (row["title"] or "") for row in rows}

    # -- Search ----------------------------------------------------------- #
    def search_fulltext(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Execute an FTS5 MATCH query with snippet extraction and BM25 ranking.

        Args:
            query (str): Free-text query string.
            limit (int): Maximum number of results to return.

        Returns:
            List[Dict[str, Any]]: Ranked results with ``paper_id``, ``title``,
                ``snippet``, ``page``, and ``rank`` keys.
        """
        if not query or not query.strip():
            return []
        sql = (
            "SELECT paper_id, title, fulltext_content, "
            "snippet(papers_fts, 2, '<b>', '</b>', '...', 15) AS snippet, "
            "rank "
            "FROM papers_fts WHERE papers_fts MATCH ? "
            "ORDER BY rank LIMIT ?"
        )
        with self._connect() as conn:
            try:
                rows = conn.execute(sql, (query.strip(), limit)).fetchall()
            except sqlite3.OperationalError:
                # -- Fall back to a quoted phrase on operator-syntax errors. -- #
                phrase = '"' + query.strip().replace('"', '""') + '"'
                rows = conn.execute(sql, (phrase, limit)).fetchall()

        results: List[Dict[str, Any]] = []
        for row in rows:
            results.append({
                "paper_id": row["paper_id"],
                "title": row["title"] or "",
                "snippet": row["snippet"] or "",
                "page": self._estimate_page(row["fulltext_content"] or "",
                                           row["snippet"] or ""),
                "rank": row["rank"],
            })
        return results

    @staticmethod
    def _estimate_page(fulltext: str, snippet: str) -> int:
        """Estimate the 1-based page number of the first snippet match.

        Args:
            fulltext (str): The full indexed body.
            snippet (str): The highlighted FTS5 snippet.

        Returns:
            int: Approximate 1-based page number (3000 chars per page).
        """
        if not fulltext or not snippet:
            return 1
        plain = snippet.replace("<b>", "").replace("</b>", "")
        probe = plain[:40] if plain else ""
        if not probe:
            return 1
        idx = fulltext.find(probe)
        if idx < 0:
            return 1
        return max(1, (idx // _CHARS_PER_PAGE) + 1)

    # -- Presentation ----------------------------------------------------- #
    def render_results(self, results: List[Dict[str, Any]]) -> None:
        """Render ranked FTS5 results in a styled Rich Table.

        Args:
            results (List[Dict[str, Any]]): Output of ``search_fulltext``.
        """
        if not RICH_AVAILABLE:  # pragma: no cover
            for r in results:
                print(f"[{r['rank']}] ({r['paper_id']}) {r['title']} -> {r['snippet']}")
            return

        console = Console()
        table = Table(
            title="SQLite FTS5 Full-Text Search Results",
            box=box.ROUNDED,
            border_style="bright_cyan",
            show_lines=True,
            header_style="bold bright_cyan",
            expand=False,
        )
        table.add_column("#", style="bold cyan", no_wrap=True)
        table.add_column("Paper ID", style="bold white", no_wrap=True)
        table.add_column("Page", style="bold magenta", no_wrap=True)
        table.add_column("Title", style="white")
        table.add_column("Matched Snippet", style="green")

        for position, result in enumerate(results, start=1):
            table.add_row(
                str(position),
                str(result["paper_id"]),
                str(result["page"]),
                result["title"][:80],
                result["snippet"],
            )
        console.print(table)

    def run(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Search and render FTS5 results for CLI/TUI entry points.

        Args:
            query (str): Free-text query string.
            limit (int): Maximum number of results.

        Returns:
            List[Dict[str, Any]]: Ranked result dictionaries.
        """
        results = self.search_fulltext(query, limit=limit)
        if not results:
            console = Console() if RICH_AVAILABLE else None
            if console is not None:
                console.print("[yellow]No full-text matches found.[/yellow]")
            return results
        self.render_results(results)
        return results




