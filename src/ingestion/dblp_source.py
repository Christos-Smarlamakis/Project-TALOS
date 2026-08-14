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
Module: dblp_source.py
Project: TALOS v5.10.0

Description:
    Search agent for the DBLP Computer Science Bibliography API
    (https://dblp.org). Fetches papers matching the configured query with
    offset-based pagination. DBLP does not provide abstracts or strong
    date filters, so year-based filtering is done locally. Provides both
    batch fetching (``fetch_new_papers``) and single-title search
    (``search_papers``) for metadata enrichment workflows.

    Free to use — no API key required.
"""
import requests
import time
from datetime import datetime
from typing import List, Dict, Any


class DBLPSource:
    """Search agent for the DBLP API.

    Fetches computer science publications via the search/publ endpoint.
    Filters by year locally since DBLP lacks date-range query support.

    Attributes:
        query (str): Search query from config.
        days_to_search (int): Lookback window in days (converted to years).
        total_max_results (int): Maximum results to fetch.
        base_url (str): DBLP search API base URL.
    """

    def __init__(self, config: Dict[str, Any]):
        """Initialize the DBLP agent from configuration.

        Args:
            config (dict): Application configuration dictionary.
        """
        self.query = config.get("dblp_query", "swarm intelligence")
        self.days_to_search = config.get("days_to_search_daily", 1)
        self.total_max_results = config.get("max_results_config", {}).get("dblp", 100)
        self.base_url = "https://dblp.org/search/publ/api"
        print("INFO: DBLPSource initialized.")

    def fetch_new_papers(self) -> List[Dict[str, Any]]:
        """Fetch recent papers from DBLP matching the configured query.

        Returns:
            list of dict: Standardized paper dictionaries.
        """
        print(f"-> Searching DBLP...")
        all_papers = []
        offset = 0
        page_size = 100
        start_year = datetime.now().year - (self.days_to_search // 365) - 1

        while len(all_papers) < self.total_max_results:
            params = {
                "q": self.query,
                "h": page_size,
                "f": offset,
                "format": "json"
            }
            try:
                response = requests.get(self.base_url, params=params, timeout=20)
                response.raise_for_status()
                data = response.json()

                hits = data.get('result', {}).get('hits', {}).get('hit', [])
                if not hits:
                    break

                stop_searching = False
                for item in hits:
                    info = item.get('info', {})

                    year_str = info.get("year")
                    if year_str and int(year_str) < start_year:
                        stop_searching = True
                        continue

                    formatted_paper = self._format_paper(info)
                    if formatted_paper:
                        all_papers.append(formatted_paper)

                    if len(all_papers) >= self.total_max_results:
                        break

                if stop_searching or len(all_papers) >= self.total_max_results or len(hits) < page_size:
                    break

                offset += page_size
                time.sleep(1)

            except requests.exceptions.RequestException as e:
                print(f"   ERROR [DBLP]: Fetch failed: {e}")
                break

        print(f"   SUCCESS [DBLP]: Found {len(all_papers)} new papers.")
        return all_papers

    def search_papers(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search for papers by title (used for metadata enrichment).

        Args:
            query (str): Title or partial title to search for.
            limit (int): Maximum results to return.

        Returns:
            list of dict: Standardized paper dictionaries.
        """
        params = {"q": query, "h": limit, "format": "json"}
        try:
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            results = []
            for item in data.get('result', {}).get('hits', {}).get('hit', []):
                info = item.get('info', {})
                paper = self._format_paper(info)
                if paper:
                    results.append(paper)
            return results
        except requests.exceptions.RequestException:
            return []

    def _format_paper(self, info: Dict[str, Any]) -> Dict[str, Any]:
        """Convert a DBLP hit to the standardized TALOS format.

        Args:
            info (dict): Raw info object from a DBLP hit.

        Returns:
            dict: Standardized paper dictionary, or None if formatting fails.
        """
        try:
            authors_data = info.get('authors', {}).get('author', [])
            if isinstance(authors_data, list):
                authors_str = ", ".join([a.get('text', '') for a in authors_data])
            elif isinstance(authors_data, dict):
                authors_str = authors_data.get('text', '')
            else:
                authors_str = ""

            doi = info.get("doi")
            year_str = info.get("year")
            publication_year = int(year_str) if year_str and year_str.isdigit() else None

            url = info.get("ee") or (f"https://doi.org/{doi}" if doi else info.get("url", "#"))

            return {
                "doi": doi,
                "url": url,
                "title": info.get("title", "N/A"),
                "authors_str": authors_str,
                "publication_year": publication_year,
                "abstract": "DBLP does not provide abstracts via its API.",
                "source": "DBLP"
            }
        except Exception as e:
            print(f"   WARNING [DBLP]: Formatting failed: {e}")
            return None