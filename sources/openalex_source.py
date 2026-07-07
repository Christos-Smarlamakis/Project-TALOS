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
Module: openalex_source.py
Project: TALOS v5.3.7

Description:
    Search agent for the OpenAlex API (https://openalex.org), a free and open
    catalog of ~250 million scholarly works. Fetches new papers matching the
    configured query within a date window using cursor-based pagination.
    Reconstructs abstracts from OpenAlex's inverted index format. Provides
    both batch fetching (``fetch_new_papers``) and single-title search
    (``search_papers``) for metadata enrichment workflows.

    Does not require an API key — uses the polite pool with email identification.
"""
import requests
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any


class OpenAlexSource:
    """Search agent for the OpenAlex API.

    Fetches scholarly works via the /works endpoint with configurable
    search queries, date filters, and result limits. Reconstructs abstracts
    from the inverted index format used by OpenAlex.

    Attributes:
        query (str): Search query from config.
        days_to_search (int): Lookback window in days.
        total_max_results (int): Maximum results to fetch.
        base_url (str): Base URL for the OpenAlex works API.
    """

    def __init__(self, config: Dict[str, Any]):
        """Initialize the OpenAlex agent from configuration.

        Args:
            config (dict): Application configuration dictionary.
        """
        self.query = config.get("openalex_query", "drone swarm intelligence")
        self.days_to_search = config.get("days_to_search_daily", 1)
        self.total_max_results = config.get("max_results_config", {}).get("openalex", 100)
        self.mailto = config.get("mailto", "user@example.com")
        self.base_url = "https://api.openalex.org/works"
        print("INFO: OpenAlexSource initialized.")

    def fetch_new_papers(self) -> List[Dict[str, Any]]:
        """Fetch recent papers from OpenAlex matching the configured query.

        Uses cursor-based pagination with date filtering.

        Returns:
            list of dict: Standardized paper dictionaries.
        """
        print(f"-> Searching OpenAlex...")
        all_papers = []
        page = 1
        per_page = 50

        cutoff_date = (datetime.now().date() - timedelta(days=self.days_to_search))
        date_filter = f"from_publication_date:{cutoff_date.strftime('%Y-%m-%d')}"

        while len(all_papers) < self.total_max_results:
            params = {
                "search": self.query,
                "per_page": per_page,
                "page": page,
                "sort": "publication_date:desc",
                "filter": date_filter,
                "mailto": self.mailto
            }
            try:
                response = requests.get(self.base_url, params=params, timeout=20)
                if response.status_code == 429:
                    print("   WARNING [OpenAlex]: Rate limit. Waiting 10 seconds...")
                    time.sleep(10)
                    continue

                response.raise_for_status()
                data = response.json()
                results_on_page = data.get('results', [])

                if not results_on_page:
                    break

                for work in results_on_page:
                    formatted_paper = self._format_paper(work)
                    if formatted_paper:
                        all_papers.append(formatted_paper)
                    if len(all_papers) >= self.total_max_results:
                        break

                if len(all_papers) >= self.total_max_results:
                    break

                if 'next_page' not in data.get('meta', {}) or not data.get('meta', {}).get('next_page'):
                    break

                page += 1
                time.sleep(0.2)

            except requests.exceptions.RequestException as e:
                print(f"   ERROR [OpenAlex]: Fetch failed: {e}")
                break

        print(f"   SUCCESS [OpenAlex]: Found {len(all_papers)} new papers.")
        return all_papers

    def search_papers(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search for papers by title (used for metadata enrichment).

        Args:
            query (str): Title or partial title to search for.
            limit (int): Maximum results to return.

        Returns:
            list of dict: Standardized paper dictionaries.
        """
        params = {"search": query, "per_page": limit, "sort": "relevance", "mailto": self.mailto}
        try:
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            results = []
            for work in data.get('results', []):
                paper = self._format_paper(work)
                if paper:
                    results.append(paper)
            return results
        except requests.exceptions.RequestException:
            return []

    def _reconstruct_abstract(self, inverted_index: Dict[str, List[int]]) -> str:
        """Reconstruct an abstract from OpenAlex's inverted index format.

        Args:
            inverted_index (dict): Mapping of words to position lists.

        Returns:
            str: Reconstructed abstract text, or a placeholder if empty.
        """
        if not inverted_index:
            return "No abstract available."

        word_positions = {}
        for word, positions in inverted_index.items():
            for pos in positions:
                word_positions[pos] = word

        abstract_list = [word_positions[i] for i in sorted(word_positions.keys())]
        return " ".join(abstract_list)

    def _format_paper(self, work: Dict[str, Any]) -> Dict[str, Any]:
        """Convert an OpenAlex work object to the standardized TALOS format.

        Args:
            work (dict): Raw work object from the OpenAlex API.

        Returns:
            dict: Standardized paper dictionary, or None if formatting fails.
        """
        try:
            authors_str = ", ".join([
                a.get("author", {}).get("display_name", "")
                for a in work.get("authorships", []) if a.get("author")
            ])

            doi_suffix = work.get("doi")
            doi = doi_suffix.replace("https://doi.org/", "") if doi_suffix else None
            url = doi_suffix or work.get("primary_location", {}).get("landing_page_url", "#")
            abstract = self._reconstruct_abstract(work.get('abstract_inverted_index'))

            return {
                "doi": doi,
                "url": url,
                "title": work.get("title", "N/A"),
                "authors_str": authors_str,
                "publication_year": work.get("publication_year"),
                "abstract": abstract,
                "source": "OpenAlex"
            }
        except Exception as e:
            print(f"   WARNING [OpenAlex]: Formatting failed: {e}")
            return None