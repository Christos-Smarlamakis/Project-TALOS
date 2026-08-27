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
Module: openaire.py
Project: TALOS v5.10.5

Description:
    Search agent for the OpenAIRE Research Graph API (v11.3.0,
    https://api.openaire.eu/search/researchProducts), a pan-European scholarly
    research graph aggregating publications, datasets, and software. Fetches
    research products matching the configured query within a date window using
    page-based pagination. Supports the optional Authorization Bearer token
    (OPENAIRE_TOKEN or OPENAIRE_API_KEY) and falls back to public
    unauthenticated requests when no token is present. Project grant/funding
    metadata, when present, is appended to the abstract field.

    Design decision: the bearer token is OPTIONAL. Unauthenticated requests are
    permitted by the public API, preserving air-gapped/local-first operation
    with graceful degradation (Constitution II).

Dependencies:
    - requests: HTTP client for the OpenAIRE search endpoint.
    - os: Environment variable access for the optional bearer token.
    - time: Rate-limiting delays between paginated requests.
    - datetime: Date-window calculation for recent-paper filtering.
"""
import os
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any
import requests


class OpenAIRESource:
    """Search agent for the OpenAIRE Research Graph API.

    Fetches research products via the /search/researchProducts endpoint with
    configurable search queries, date filters, and result limits. Appends
    project grant/funding metadata to the abstract field when present.

    Attributes:
        query (str): Search query from config.
        days_to_search (int): Lookback window in days.
        total_max_results (int): Maximum results to fetch.
        headers (dict): HTTP headers including the optional bearer token.
        base_url (str): Base URL for the OpenAIRE search API.
    """

    BASE_URL = "https://api.openaire.eu/search/researchProducts"

    # -- OpenAIRE's `keywords` parameter splits on whitespace and ANDs every
    # term. It does NOT support boolean OR/AND operators (those raise an HTTP
    # 409 SOLR parse error), so a long natural-language query requires every
    # term to co-occur in a single record and reliably matches zero records.
    # We therefore cap the number of ANDed terms sent to the API. --
    MAX_AND_TERMS = 3

    def __init__(self, config: Dict[str, Any]):
        """Initialize the OpenAIRE agent from configuration.

        Args:
            config (dict): Application configuration dictionary.
        """
        self.query = config.get("openaire_query", "artificial intelligence")
        self.days_to_search = config.get("days_to_search_daily", 1)
        self.total_max_results = config.get("max_results_config", {}).get("openaire", 50)
        self.enabled = True

        # -- Optional bearer token; otherwise public unauthenticated access. --
        token = os.getenv("OPENAIRE_TOKEN") or os.getenv("OPENAIRE_API_KEY") or ""
        self.headers = {"Authorization": f"Bearer {token}"} if token else {}
        print("INFO: OpenAIRESource initialized.")

    @staticmethod
    def _first(values, default=None):
        """Return the first non-empty value from a list-like field.

        Nested XML-to-JSON dictionary wrappers (``$``, ``#text``, ``value``)
        are unwrapped so a title such as ``[{"$": "Some Title"}]`` resolves to
        the plain string instead of the raw dictionary.

        Args:
            values: Raw field value (list, scalar, or None).
            default: Value returned when the field is empty.

        Returns:
            The first unwrapped value if it is a non-empty list, else the
            scalar/default.
        """
        def _unwrap(value):
            if isinstance(value, dict):
                return value.get("$", value.get("#text", value.get("value", str(value))))
            return value

        if isinstance(values, list):
            for value in values:
                if value not in (None, ""):
                    return _unwrap(value)
            return default
        return _unwrap(values) if values else default

    @staticmethod
    def _normalize_keywords(query: str) -> str:
        """Normalize a query for OpenAIRE's AND-only `keywords` parameter.

        OpenAIRE tokenizes `keywords` on whitespace and ANDs every term, and it
        does not support boolean OR/AND operators (they raise an HTTP 409 SOLR
        parse error). A long query therefore requires every term to co-occur in
        a single record, which reliably yields zero results. This helper caps
        the query to a small number of leading terms so that discovery queries
        remain broad enough to return results while staying on-topic.

        Args:
            query (str): Raw query string from config or a paper title.

        Returns:
            str: Whitespace-normalized query with at most MAX_AND_TERMS terms.
        """
        if not query:
            return ""
        return " ".join(query.split()[: OpenAIRESource.MAX_AND_TERMS])

    def _extract_result(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Navigate the nested OpenAIRE result payload to the oaf:result node.

        Args:
            item (dict): A single entry from results.result.

        Returns:
            dict: The inner oaf:result dictionary (empty if not found).
        """
        try:
            return item.get("metadata", {}).get("oaf:entity", {}).get("oaf:result", {})
        except AttributeError:
            return {}

    def fetch_new_papers(self) -> List[Dict[str, Any]]:
        """Fetch recent papers from OpenAIRE matching the configured query.

        Uses page-based pagination with a date filter derived from days_to_search.

        Returns:
            list of dict: Standardized paper dictionaries.
        """
        print("-> Searching OpenAIRE...")
        all_papers = []
        page = 1
        per_page = 100
        cutoff = (datetime.now().date() - timedelta(days=self.days_to_search)).strftime("%Y-%m-%d")

        while len(all_papers) < self.total_max_results:
            params = {
                "keywords": self._normalize_keywords(self.query),
                "fromDateAccepted": cutoff,
                "format": "json",
                "size": per_page,
                "page": page,
            }
            try:
                response = requests.get(self.BASE_URL, params=params, headers=self.headers, timeout=30)
                if response.status_code == 429:
                    print("   WARNING [OpenAIRE]: Rate limit. Waiting 10 seconds...")
                    time.sleep(10)
                    continue
                response.raise_for_status()
                data = response.json()
            except requests.exceptions.RequestException as e:
                print(f"   ERROR [OpenAIRE]: Fetch failed: {e}")
                break

            resp_obj = data.get("response") or {}
            results_obj = resp_obj.get("results") or {}
            result_list = results_obj.get("result") or []
            # -- OpenAIRE returns a single dict (not a list) for a lone result. --
            if isinstance(result_list, dict):
                result_list = [result_list]
            if not result_list:
                break

            for item in result_list:
                formatted = self._format_paper(item)
                if formatted:
                    all_papers.append(formatted)
                if len(all_papers) >= self.total_max_results:
                    break

            total = results_obj.get("total")
            if isinstance(total, dict):
                total = total.get("$", 0)
            try:
                total = int(total or 0)
            except (TypeError, ValueError):
                total = 0
            if len(all_papers) >= self.total_max_results or (total and page * per_page >= total):
                break

            page += 1
            time.sleep(0.5)

        print(f"   SUCCESS [OpenAIRE]: Found {len(all_papers)} new papers.")
        return all_papers

    def search_papers(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search for papers by title (used for metadata enrichment).

        Args:
            query (str): Title or partial title to search for.
            limit (int): Maximum results to return.

        Returns:
            list of dict: Standardized paper dictionaries.
        """
        params = {"keywords": self._normalize_keywords(query), "format": "json", "size": limit, "page": 1}
        try:
            response = requests.get(self.BASE_URL, params=params, headers=self.headers, timeout=15)
            response.raise_for_status()
            data = response.json()
            resp_obj = data.get("response") or {}
            results_obj = resp_obj.get("results") or {}
            result_list = results_obj.get("result") or []
            if isinstance(result_list, dict):
                result_list = [result_list]
            results = []
            for item in result_list:
                paper = self._format_paper(item)
                if paper:
                    results.append(paper)
            return results
        except requests.exceptions.RequestException:
            return []

    def _format_paper(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Convert an OpenAIRE research product to the standardized TALOS format.

        Args:
            item (dict): Raw entry from results.result.

        Returns:
            dict: Standardized paper dictionary, or None if formatting fails.
        """
        try:
            result = self._extract_result(item)
            if not result:
                return None

            title = self._first(result.get("title"))
            if not title:
                return None

            authors = result.get("creator", [])
            if isinstance(authors, list):
                authors_str = ", ".join(str(a) for a in authors)
            else:
                authors_str = str(authors) if authors else ""

            abstract = self._first(result.get("description"), "No abstract available.")

            # -- Extract DOI from originalId and URL from pid. --
            doi = None
            for identifier in (result.get("originalId") or []):
                if str(identifier).startswith("10."):
                    doi = str(identifier)
                    break
            url = self._first(result.get("pid"))
            if not url and doi:
                url = f"https://doi.org/{doi}"

            publication_year = None
            date_raw = self._first(result.get("dateofacceptance")) or self._first(result.get("publicationdate"))
            if date_raw:
                try:
                    publication_year = int(str(date_raw)[:4])
                except (TypeError, ValueError):
                    publication_year = None

            # -- Append project grant/funding metadata when present. --
            funding_summary = self._extract_funding(result.get("projects"))
            if funding_summary:
                abstract = f"{abstract} [OpenAIRE funding: {funding_summary}]"

            return {
                "doi": doi,
                "url": url or "#",
                "title": str(title),
                "authors_str": authors_str,
                "publication_year": publication_year,
                "abstract": str(abstract),
                "source": "OpenAIRE",
            }
        except Exception as e:
            print(f"   WARNING [OpenAIRE]: Formatting failed: {e}")
            return None

    def _extract_funding(self, projects: Any) -> str:
        """Build a concise grant/funding summary from the projects node.

        Args:
            projects: The raw 'projects' node from an OpenAIRE result.

        Returns:
            str: Semicolon-joined funding summary, or empty string.
        """
        if not projects or not isinstance(projects, dict):
            return ""
        project_list = projects.get("project", [])
        if isinstance(project_list, dict):
            project_list = [project_list]
        if not isinstance(project_list, list):
            return ""
        summaries = []
        for project in project_list:
            if not isinstance(project, dict):
                continue
            parts = []
            code = self._first(project.get("code"))
            acronym = self._first(project.get("acronym"))
            funder = self._first(project.get("funder"))
            if code:
                parts.append(f"grant {code}")
            if acronym:
                parts.append(str(acronym))
            if funder:
                parts.append(f"funded by {funder}")
            if parts:
                summaries.append(" ".join(parts))
        return "; ".join(summaries)
