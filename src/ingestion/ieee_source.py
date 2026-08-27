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
Module: ieee_source.py
Project: TALOS v5.10.0

Description:
    Search agent for the IEEE Xplore API. Fetches papers matching the configured
    query with year-based date filtering and offset-based pagination. Implements
    exponential backoff for rate limit handling (429/403 responses). Requires an
    API key via the ``IEEE_API_KEY`` environment variable. Gracefully disables
    itself if no key is configured.
"""
import requests
import os
import time
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any


class IEEEXploreSource:
    """Search agent for the IEEE Xplore API.

    Fetches papers with configurable queries, year filters, and result limits.
    Handles rate limiting with exponential backoff.

    Attributes:
        api_key (str or None): IEEE API key from environment.
        enabled (bool): False if no API key; agent skips gracefully.
        base_url (str): IEEE Xplore API base URL.
    """

    def __init__(self, config: Dict[str, Any]):
        """Initialize the IEEE agent.

        Args:
            config (dict): Application configuration.
        """
        self.api_key = os.getenv("IEEE_API_KEY")
        self.enabled = True
        if not self.api_key:
            print("WARNING: IEEE_API_KEY not found in .env file. Skipping source.")
            self.enabled = False
            return
        self.query = config.get("ieee_query", "robotics")
        self.days_to_search = config.get("days_to_search_daily", 1)
        self.total_max_results = config.get("max_results_config", {}).get("ieee", 100)
        self.base_url = "https://ieeexploreapi.ieee.org/api/v1/search/articles"
        print("INFO: IEEEXploreSource initialized.")

    def _make_request(self, params, max_retries=4, initial_backoff=5):
        """Make an API request with exponential backoff.

        Args:
            params (dict): Query parameters including apikey.
            max_retries (int): Maximum retry attempts.
            initial_backoff (float): Initial backoff in seconds.

        Returns:
            dict or None: Parsed JSON response.
        """
        for attempt in range(max_retries):
            try:
                response = requests.get(self.base_url, params=params, timeout=30)
                if response.status_code in [429, 403]:
                    if attempt == max_retries - 1: response.raise_for_status()
                    backoff = initial_backoff * (2 ** attempt) + random.uniform(0, 1)
                    print(f"   WARNING [IEEE]: API returned {response.status_code}. Retrying in {backoff:.2f}s...")
                    time.sleep(backoff)
                    continue
                response.raise_for_status()
                return response.json()
            except requests.exceptions.RequestException as e:
                print(f"   ERROR [IEEE]: API call failed after {attempt + 1} attempts. Error: {e}")
                # -- v5.10.12 hotfix: surface hidden API errors to the visualizer --
                try:
                    from src.integration.visualizer_bridge import push_visualizer_event
                    push_visualizer_event("error", "ieee", error_msg=str(e))
                except ImportError:
                    pass
                return None
        return None

    def fetch_new_papers(self) -> List[Dict[str, Any]]:
        """Fetch papers from IEEE Xplore.

        Returns:
            list of dict: Standardized paper dictionaries.
        """
        # ── Guard: skip if API key is missing ──────────────────────────────
        if not getattr(self, "enabled", True): return []

        print(f"-> Searching IEEE Xplore...")
        all_papers = []
        start_record = 1        # IEEE API uses 1-based indexing for pagination
        page_size = 200         # Maximum records per page
        start_year = datetime.now().year - (self.days_to_search // 365) - 1
        cutoff_date = datetime.now() - timedelta(days=self.days_to_search)

        # ── Paginate through results until we hit the limit or end ──────────
        while len(all_papers) < self.total_max_results:
            params = {
                "apikey": self.api_key, "format": "json", "max_records": page_size,
                "start_record": start_record, "sort_order": "desc", "sort_field": "publication_year",
                "querytext": self.query, "start_year": start_year
            }
            data = self._make_request(params)
            if not data or not data.get('articles'): break
            articles_on_page = data.get('articles', [])

            for article in articles_on_page:
                if len(all_papers) >= self.total_max_results: break

                pub_year_str = article.get("publication_year")
                if pub_year_str and pub_year_str.isdigit():
                    pub_year = int(pub_year_str)
                    if pub_year >= cutoff_date.year:
                        formatted = self._format_paper(article)
                        if formatted: all_papers.append(formatted)

            # ── Stop conditions: reached target OR no more pages ────────────
            if len(all_papers) >= self.total_max_results or len(articles_on_page) < page_size:
                break
            start_record += page_size  # Move to next page for next iteration

        print(f"   SUCCESS [IEEE]: Found {len(all_papers)} new papers.")
        return all_papers

    def _format_paper(self, article: Dict[str, Any]) -> Dict[str, Any]:
        """Convert an IEEE article to the standardized format.

        Args:
            article (dict): Raw IEEE API article.

        Returns:
            dict: Standardized paper dictionary.
        """
        try:
            authors_list = article.get('authors', {}).get('authors', [])
            authors_str = ", ".join([author.get('full_name', '') for author in authors_list])
            doi = article.get("doi")
            url = f"https://doi.org/{doi}" if doi else article.get("html_url", "#")
            year_str = article.get("publication_year")
            publication_year = int(year_str) if year_str and year_str.isdigit() else None
            return {
                "doi": doi, "url": url, "title": article.get("title", "N/A"),
                "authors_str": authors_str, "publication_year": publication_year,
                "abstract": article.get("abstract", "Abstract not provided by IEEE API.").replace("\n", " "),
                "source": "IEEE Xplore"
            }
        except Exception as e:
            print(f"   WARNING [IEEE]: Failed to format an article: {e}")
            return None