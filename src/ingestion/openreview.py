# -*- coding: utf-8 -*-
#  Project TALOS
#  Copyright (C) 2026 Christos Smarlamakis
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Affero General Public License as
#  published by the Free Software Foundation, either version 3 of the
#  License, or (at your option) any later version.
#
#  For commercial licensing, please contact the author.

"""
Module: openreview.py
Project: TALOS v5.10.0

Description:
    Search agent for the OpenReview API V2 (https://api2.openreview.net), the
    open peer-review platform used by leading machine-learning venues (NeurIPS,
    ICLR, ICML, ACL). Fetches forum notes matching the configured query within
    a date window using offset pagination. When optional OPENREVIEW_USERNAME and
    OPENREVIEW_PASSWORD credentials are present, an authenticated
    OpenReviewClient is instantiated; otherwise the source falls back gracefully
    to guest/public notes access. Peer-review decisions, ratings, and venue
    metadata are appended to the abstract field as a concise summary when
    available.

    Design decision: openreview-py is an OPTIONAL dependency. The import is
    guarded so that air-gapped or minimal installations without the client
    library degrade gracefully (self.enabled=False) rather than crashing.

Dependencies:
    - openreview: Official OpenReview API V2 client (openreview-py). Optional.
    - os: Environment variable access for optional credentials.
    - time: Rate-limiting delays between paginated requests.
    - datetime: Date-window calculation for recent-paper filtering.
"""
import os
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any

# -- Optional dependency guard (Constitution II: air-gapped, local-first) --
try:
    import openreview  # type: ignore
    OPENREVIEW_AVAILABLE = True
except ImportError:  # pragma: no cover - depends on optional package
    openreview = None  # type: ignore
    OPENREVIEW_AVAILABLE = False


class OpenReviewSource:
    """Search agent for the OpenReview API V2.

    Fetches forum notes via the OpenReviewClient with configurable search
    queries, date filters, and result limits. Appends peer-review decisions
    and ratings to the abstract field when present.

    Attributes:
        query (str): Search query from config.
        days_to_search (int): Lookback window in days.
        total_max_results (int): Maximum results to fetch.
        client: OpenReviewClient instance, or None if unavailable.
        enabled (bool): Whether the source can run (False if library missing).
    """

    BASE_URL = "https://api2.openreview.net"

    def __init__(self, config: Dict[str, Any]):
        """Initialize the OpenReview agent from configuration.

        Args:
            config (dict): Application configuration dictionary.
        """
        self.query = config.get("openreview_query", "artificial intelligence")
        self.days_to_search = config.get("days_to_search_daily", 1)
        self.total_max_results = config.get("max_results_config", {}).get("openreview", 50)
        self.enabled = OPENREVIEW_AVAILABLE

        if not OPENREVIEW_AVAILABLE:
            print("WARNING [OpenReview]: openreview-py is not installed. Source disabled.")
            self.client = None
            return

        # -- Optional authenticated client; fall back to guest access. --
        username = os.getenv("OPENREVIEW_USERNAME")
        password = os.getenv("OPENREVIEW_PASSWORD")
        try:
            if username and password:
                self.client = openreview.api.OpenReviewClient(
                    baseurl=self.BASE_URL, username=username, password=password
                )
            else:
                self.client = openreview.api.OpenReviewClient(baseurl=self.BASE_URL)
            print("INFO: OpenReviewSource initialized.")
        except Exception as e:
            print(f"WARNING [OpenReview]: Client init failed ({e}). Falling back to guest access.")
            try:
                self.client = openreview.api.OpenReviewClient(baseurl=self.BASE_URL)
            except Exception:
                self.client = None
                self.enabled = False

    def _get_content_value(self, note: Any, field: str, default=None):
        """Safely extract a scalar value from an OpenReview note content field.

        Args:
            note: The Note object from openreview-py.
            field (str): Field name within note.content.
            default: Value to return if the field is missing.

        Returns:
            The extracted value, or the default if unavailable.
        """
        try:
            content = getattr(note, "content", None)
            if not content:
                return default
            raw = content.get(field)
            if raw is None:
                return default
            # -- V2 Content objects expose .value; plain dicts do not. --
            if hasattr(raw, "value"):
                return raw.value
            if isinstance(raw, dict) and "value" in raw:
                return raw["value"]
            return raw
        except Exception:
            return default

    def fetch_new_papers(self) -> List[Dict[str, Any]]:
        """Fetch recent papers from OpenReview matching the configured query.

        Uses offset pagination with a date window derived from days_to_search.

        Returns:
            list of dict: Standardized paper dictionaries.
        """
        if not self.enabled or self.client is None:
            print("WARNING [OpenReview]: Source disabled. Returning no results.")
            return []

        print("-> Searching OpenReview...")
        all_papers = []
        offset = 0
        per_page = 100
        cutoff_ms = int((datetime.now() - timedelta(days=self.days_to_search)).timestamp() * 1000)

        while len(all_papers) < self.total_max_results:
            try:
                notes = self.client.get_notes(
                    term=self.query,
                    limit=per_page,
                    offset=offset,
                    sort="cdate:desc",
                )
            except Exception as e:
                print(f"   WARNING [OpenReview]: Fetch failed: {e}")
                break

            if not notes:
                break

            page_added = 0
            for note in notes:
                try:
                    cdate = int(getattr(note, "cdate", 0) or 0)
                except (TypeError, ValueError):
                    cdate = 0
                if cdate and cdate < cutoff_ms:
                    continue
                formatted = self._format_paper(note)
                if formatted:
                    all_papers.append(formatted)
                    page_added += 1
                if len(all_papers) >= self.total_max_results:
                    break

            if page_added == 0 and len(notes) > 0:
                # -- Entire page fell outside the date window; stop paginating. --
                break

            if len(notes) < per_page:
                break

            offset += per_page
            time.sleep(0.5)

        print(f"   SUCCESS [OpenReview]: Found {len(all_papers)} new papers.")
        return all_papers

    def search_papers(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search for papers by title (used for metadata enrichment).

        Args:
            query (str): Title or partial title to search for.
            limit (int): Maximum results to return.

        Returns:
            list of dict: Standardized paper dictionaries.
        """
        if not self.enabled or self.client is None:
            return []
        try:
            notes = self.client.get_notes(term=query, limit=limit)
            results = []
            for note in notes:
                paper = self._format_paper(note)
                if paper:
                    results.append(paper)
            return results
        except Exception:
            return []

    def _format_paper(self, note: Any) -> Dict[str, Any]:
        """Convert an OpenReview note object to the standardized TALOS format.

        Args:
            note: Raw Note object from the OpenReview API V2.

        Returns:
            dict: Standardized paper dictionary, or None if formatting fails.
        """
        try:
            title = self._get_content_value(note, "title", "N/A")
            if not title or title == "N/A":
                return None

            authors = self._get_content_value(note, "authors", [])
            if isinstance(authors, list):
                authors_str = ", ".join(str(a) for a in authors)
            else:
                authors_str = str(authors) if authors else ""

            abstract = self._get_content_value(note, "abstract", "No abstract available.")
            abstract = str(abstract)

            # -- Append peer-review decision/rating summary when present. --
            decision = self._get_content_value(note, "decision")
            rating = self._get_content_value(note, "rating")
            recommendation = self._get_content_value(note, "recommendation")
            venue = self._get_content_value(note, "venue")
            summary_parts = []
            if decision:
                summary_parts.append(f"Peer-review decision: {decision}")
            if recommendation:
                summary_parts.append(f"Recommendation: {recommendation}")
            if rating:
                summary_parts.append(f"Rating: {rating}")
            if venue:
                summary_parts.append(f"Venue: {venue}")
            if summary_parts:
                abstract = f"{abstract} [OpenReview meta: {'; '.join(summary_parts)}]"

            # -- Derive DOI, URL, and publication year. --
            doi = self._get_content_value(note, "doi")
            note_id = getattr(note, "id", None) or ""
            forum = getattr(note, "forum", None) or note_id
            url = f"https://openreview.net/forum?id={forum}"

            cdate = None
            try:
                cdate = int(getattr(note, "cdate", 0) or 0)
            except (TypeError, ValueError):
                cdate = None
            publication_year = None
            if cdate:
                publication_year = datetime.fromtimestamp(cdate / 1000).year

            return {
                "doi": doi,
                "url": url,
                "title": str(title),
                "authors_str": authors_str,
                "publication_year": publication_year,
                "abstract": abstract,
                "source": "OpenReview",
            }
        except Exception as e:
            print(f"   WARNING [OpenReview]: Formatting failed: {e}")
            return None
