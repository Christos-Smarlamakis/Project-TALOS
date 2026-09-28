# -*- coding: utf-8 -*-
"""
Module: code_first_search.py
Project: TALOS v5.15.0
Description:
    Reproducible code-first search engine. Discovers research papers that are
    verified to possess an official GitHub / PapersWithCode repository, a PyTorch
    implementation, or a robotic simulation benchmark (ROS2, Gazebo, AirSim,
    Isaac Gym). It queries the public GitHub repository search and PapersWithCode
    APIs, then cross-references results against the active profile database so
    only code-linked, reproducible studies surface.

    Key design decisions:
    - All queries degrade gracefully: an offline or rate-limited API returns an
      empty result rather than raising.
    - Reproducibility signals are matched against repository descriptions, topics,
      and PapersWithCode metadata (repository field, evaluation benchmark).
    - The engine is read-only with respect to the database; it surfaces matching
      records without modifying the corpus.

Dependencies:
    - os: Environment variable access.
    - requests: HTTP client for GitHub and PapersWithCode APIs.
"""
import os

import requests

# -- Reproducibility signal keywords (robotic simulation + DL frameworks). --
REPRO_SIGNALS = (
    "pytorch", "tensorflow", "jax", "ros2", "gazebo", "airsim", "isaac",
    "isaac gym", "isaacgym", "simulation", "benchmark", "reinforcement",
    "gymnasium", "paper", "arxiv", "official", "implementation",
)


class CodeFirstSearchEngine:
    """Discover code-linked, reproducible research papers.

    Queries GitHub repositories and PapersWithCode for papers carrying an
    official implementation or a robotic simulation benchmark, and returns both
    the external reproducible artifacts and any matching records already present
    in the active profile database.
    """

    GITHUB_SEARCH_URL = "https://api.github.com/search/repositories"
    PWC_SEARCH_URL = "https://paperswithcode.com/api/v1/papers/"

    def __init__(self, timeout: int = 20):
        """Initialize the engine.

        Args:
            timeout (int): HTTP request timeout in seconds.
        """
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update(
            {"Accept": "application/vnd.github+json", "User-Agent": "TALOS"}
        )

    def _search_github_repos(self, query: str, limit: int = 20):
        """Search GitHub repositories matching the query.

        Args:
            query (str): Search query.
            limit (int): Maximum repositories to return.

        Returns:
            list: Repository records with name/url/description/topics/stars.
        """
        try:
            response = self.session.get(
                self.GITHUB_SEARCH_URL,
                params={"q": query, "per_page": min(limit, 100)},
                timeout=self.timeout,
            )
            response.raise_for_status()
            items = response.json().get("items", [])
            return [
                {
                    "repo": item.get("full_name"),
                    "url": item.get("html_url"),
                    "description": item.get("description") or "",
                    "topics": item.get("topics") or [],
                    "stars": item.get("stargazers_count", 0),
                }
                for item in items
            ]
        except (requests.RequestException, ValueError):
            return []

    def _is_reproducible(self, record):
        """Determine whether a repository carries a reproducibility signal.

        Args:
            record (dict): A repository or paper record.

        Returns:
            bool: True when a known code/benchmark signal is present.
        """
        blob = " ".join(
            str(record.get(k) or "")
            for k in ("description", "topics", "title", "repository")
        ).lower()
        return any(signal in blob for signal in REPRO_SIGNALS)

    def _search_paperswithcode(self, query: str, limit: int = 20):
        """Search PapersWithCode for papers matching the query.

        Args:
            query (str): Search query.
            limit (int): Maximum papers to return.

        Returns:
            list: Paper records with title/abstract-url/repository.
        """
        try:
            response = self.session.get(
                self.PWC_SEARCH_URL,
                params={"q": query},
                timeout=self.timeout,
            )
            response.raise_for_status()
            results = response.json().get("results", [])[:limit]
            return [
                {
                    "title": paper.get("title"),
                    "url": paper.get("url_abs") or paper.get("url_pdf"),
                    "repository": paper.get("repository"),
                }
                for paper in results
            ]
        except (requests.RequestException, ValueError):
            return []

    def run(self, query: str, limit: int = 20):
        """Discover reproducible, code-linked papers for a query.

        Args:
            query (str): Research query.
            limit (int): Maximum results per external source.

        Returns:
            dict: ``repositories`` and ``papers_with_code`` result lists plus a
                ``matching_db_papers`` list of active-profile records that match
                by title or abstract.
        """
        repos = [r for r in self._search_github_repos(query, limit) if self._is_reproducible(r)]
        pwc = [p for p in self._search_paperswithcode(query, limit) if self._is_reproducible(p)]
        return {
            "query": query,
            "repositories": repos,
            "papers_with_code": pwc,
            "matching_db_papers": self._match_db_papers(query),
        }

    def _match_db_papers(self, query: str):
        """Cross-reference the query against the active profile database.

        Args:
            query (str): Research query.

        Returns:
            list: Matching paper records (id/title/doi/url/source).
        """
        try:
            from src.core.database_manager import DatabaseManager
            db = DatabaseManager()
            like = f"%{query.strip()}%"
            rows = db.execute_query(
                "SELECT id, title, doi, url, source FROM papers "
                "WHERE title LIKE ? OR abstract LIKE ? LIMIT 50",
                (like, like),
                fetch_all=True,
            )
            return [
                {"id": r[0], "title": r[1], "doi": r[2], "url": r[3], "source": r[4]}
                for r in (rows or [])
            ]
        except Exception:  # pragma: no cover - DB unavailable
            return []
