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
Module: crossref_source.py (v2.1 - Genesis + Search)
Project: TALOS v4.8.5

Description:
    Search agent for the Crossref API (https://api.crossref.org), a central
    registry of ~150 million scholarly works with persistent DOIs. Fetches
    new papers matching the configured query within a date window using
    offset-based pagination. Cleans HTML tags from abstracts. Provides both
    batch fetching (``fetch_new_papers``) and single-title search
    (``search_papers``) for metadata enrichment workflows.

    Does not require an API key — uses the polite pool with email identification.
"""
import requests
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any


class CrossrefSource:
    """Search agent for the Crossref API.

    Fetches scholarly works via the /works endpoint with configurable
    search queries, date filters, and result limits.

    Attributes:
        query (str): Bibliographic search query from config.
        days_to_search (int): Lookback window in days.
        total_max_results (int): Maximum results to fetch.
        base_url (str): Base URL for the Crossref works API.
    """

    def __init__(self, config: Dict[str, Any]):
        """Initialize the Crossref agent from configuration.

        Args:
            config (dict): Application configuration dictionary.
        """
        self.query = config.get("crossref_query", "swarm intelligence")
        self.days_to_search = config.get("days_to_search_daily", 1)
        self.total_max_results = config.get("max_results_config", {}).get("crossref", 100)
        self.mailto = config.get("mailto", "user@example.com")
        self.base_url = "https://api.crossref.org/works"
        print("INFO: CrossrefSource (v2.1 - Genesis + Search) initialized.")

    def fetch_new_papers(self) -> List[Dict[str, Any]]:
        """Fetch recent papers from Crossref matching the configured query.

        Uses offset-based pagination with date filtering.

        Returns:
            list of dict: Standardized paper dictionaries.
        """
        print(f"-> Searching Crossref...")
        all_papers = []
        offset = 0
        page_size = 100

        cutoff_date = (datetime.now().date() - timedelta(days=self.days_to_search))
        date_filter = f"from-pub-date:{cutoff_date.strftime('%Y-%m-%d')}"

        while len(all_papers) < self.total_max_results:
            params = {
                "query.bibliographic": self.query,
                "rows": page_size,
                "offset": offset,
                "sort": "published",
                "order": "desc",
                "filter": date_filter,
                "mailto": self.mailto
            }
            try:
                response = requests.get(self.base_url, params=params, timeout=20)
                if response.status_code == 429:
                    print("   WARNING [Crossref]: Rate limit. Waiting 5 seconds...")
                    time.sleep(5)
                    continue

                response.raise_for_status()
                data = response.json()
                items = data.get('message', {}).get('items', [])

                if not items:
                    break

                for item in items:
                    formatted_paper = self._format_paper(item)
                    if formatted_paper:
                        all_papers.append(formatted_paper)
                    if len(all_papers) >= self.total_max_results:
                        break

                if len(all_papers) >= self.total_max_results or len(items) < page_size:
                    break

                offset += page_size
                time.sleep(1)

            except requests.exceptions.RequestException as e:
                print(f"   ERROR [Crossref]: Fetch failed: {e}")
                break

        print(f"   SUCCESS [Crossref]: Found {len(all_papers)} new papers.")
        return all_papers

    def search_papers(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search for papers by title (used for metadata enrichment).

        Args:
            query (str): Title or partial title to search for.
            limit (int): Maximum results to return.

        Returns:
            list of dict: Standardized paper dictionaries.
        """
        params = {"query.bibliographic": query, "rows": limit, "mailto": self.mailto}
        try:
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            results = []
            for item in data.get('message', {}).get('items', []):
                paper = self._format_paper(item)
                if paper:
                    results.append(paper)
            return results
        except requests.exceptions.RequestException:
            return []

    def _format_paper(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Convert a Crossref work object to the standardized TALOS format.

        Args:
            item (dict): Raw work object from the Crossref API.

        Returns:
            dict: Standardized paper dictionary, or None if formatting fails.
        """
        try:
            title_list = item.get("title", ["N/A"])
            title = title_list[0] if title_list else "N/A"

            authors_list = item.get('author', [])
            authors_str = ", ".join([
                f"{a.get('given', '')} {a.get('family', '')}".strip()
                for a in authors_list
            ])

            abstract = item.get("abstract", "Crossref does not always provide an abstract.")
            abstract = abstract.replace('<jats:p>', '').replace('</jats:p>', '').replace('\n', ' ')

            doi = item.get("DOI")

            publication_year = None
            date_parts = item.get("published", {}).get("date-parts", [[None]])[0]
            if date_parts and date_parts[0] is not None:
                publication_year = int(date_parts[0])

            url = f"https://doi.org/{doi}" if doi else item.get("URL", "#")

            return {
                "doi": doi,
                "url": url,
                "title": title,
                "authors_str": authors_str,
                "publication_year": publication_year,
                "abstract": abstract,
                "source": "Crossref"
            }
        except Exception as e:
            print(f"   WARNING [Crossref]: Formatting failed: {e}")
            return None