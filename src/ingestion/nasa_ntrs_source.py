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
Module: nasa_ntrs_source.py
Project: TALOS v5.14.2
Description:
    Search agent for the NASA Technical Reports Server (NTRS) public REST API
    (https://ntrs.nasa.gov/api/citations/search). Harvests aerospace technical
    reports (NASA TM, TP, CR), flight control, avionics, and autonomous swarm
    research with direct PDF links. The endpoint is pure JSON and requires no
    API key or authentication, preserving full air-gapped/local-first operation
    with graceful degradation when offline (Constitution II).

    Key design decisions:
    - Uses GET with ``q``, ``page.size`` and ``page.from`` query parameters.
    - Normalizes each NTRS citation into the standardized TALOS paper dict:
      {doi, url, title, authors_str, publication_year, abstract, source}.
    - The abstract is appended with the NASA report number and center when
      present, so the technical-report provenance survives into evaluation.

Dependencies:
    - requests: HTTP client for the NTRS search endpoint.
    - time: Rate-limiting delays between paginated requests.
    - typing: Type annotations.
"""
import time
from typing import List, Dict, Any
import requests

try:
    from src.utils.http_client import build_session
except ImportError:
    build_session = None


class NasaNtrsSource:
    """Search agent for the NASA NTRS public REST API.

    Fetches aerospace technical reports via the /api/citations/search endpoint
    with configurable queries and result limits, and emits standardized paper
    dictionaries carrying the NTRS landing-page URL and, when available, the
    DOI and report number.

    Attributes:
        query (str): Search query from config.
        total_max_results (int): Maximum results to fetch.
        session: HTTP session (or raw requests module when unavailable).
        enabled (bool): Whether the source is operational.
    """

    BASE_URL = "https://ntrs.nasa.gov/api/citations/search"

    def __init__(self, config: Dict[str, Any]):
        self.session = build_session() if build_session else requests
        self.query = config.get(
            "nasa_ntrs_query",
            "unmanned aerial vehicle swarm autonomous flight control",
        )
        self.total_max_results = config.get("max_results_config", {}).get("nasa_ntrs", 50)
        self.enabled = True
        print("INFO: NasaNtrsSource initialized.")

    @staticmethod
    def _first(values, default=None):
        """Return the first non-empty value from a list-like or scalar field.

        Args:
            values: Raw field value (list, scalar, or None).
            default: Value returned when the field is empty.

        Returns:
            The first non-empty scalar, or the default.
        """
        if isinstance(values, list):
            for value in values:
                if value not in (None, ""):
                    return value
            return default
        return values if values else default

    @staticmethod
    def _as_list(value):
        """Coerce a scalar or list value into a list.

        Args:
            value: Raw scalar or list.

        Returns:
            list: The value as a list (empty list for None).
        """
        if value is None:
            return []
        if isinstance(value, list):
            return value
        return [value]

    def fetch_new_papers(self) -> List[Dict[str, Any]]:
        """Fetch aerospace technical reports from NASA NTRS.

        Uses page-based pagination over the public search endpoint and returns
        standardized paper dictionaries.

        Returns:
            list of dict: Standardized paper dictionaries.
        """
        print("-> Searching NASA NTRS...")
        all_papers = []
        page_size = min(100, self.total_max_results)
        offset = 0

        while len(all_papers) < self.total_max_results:
            params = {
                "q": self.query,
                "page.size": page_size,
                "page.from": offset,
            }
            try:
                response = self.session.get(self.BASE_URL, params=params, timeout=30)
                if response.status_code == 429:
                    print("   WARNING [NASA NTRS]: Rate limit. Waiting 10 seconds...")
                    time.sleep(10)
                    continue
                response.raise_for_status()
                data = response.json()
            except requests.exceptions.RequestException as e:
                print(f"   ERROR [NASA NTRS]: Fetch failed: {e}")
                break
            except ValueError as e:
                print(f"   ERROR [NASA NTRS]: Invalid JSON: {e}")
                break

            results = data.get("results") or []
            if not results:
                break

            for item in results:
                formatted = self._format_paper(item)
                if formatted:
                    all_papers.append(formatted)
                if len(all_papers) >= self.total_max_results:
                    break

            offset += page_size
            time.sleep(0.5)

        print(f"   SUCCESS [NASA NTRS]: Found {len(all_papers)} new papers.")
        return all_papers

    def search_papers(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search NTRS by a specific query (used for metadata enrichment).

        Args:
            query (str): Search query string.
            limit (int): Maximum results to return.

        Returns:
            list of dict: Standardized paper dictionaries.
        """
        params = {"q": query, "page.size": limit, "page.from": 0}
        try:
            response = self.session.get(self.BASE_URL, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()
        except requests.exceptions.RequestException:
            return []
        results = []
        for item in data.get("results") or []:
            paper = self._format_paper(item)
            if paper:
                results.append(paper)
        return results

    def _format_paper(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Convert an NTRS citation to the standardized TALOS format.

        Args:
            item (dict): A single NTRS ``results`` entry.

        Returns:
            dict: Standardized paper dictionary, or None on failure.
        """
        try:
            title = self._first(item.get("title"))
            if not title:
                return None

            # -- Authors may live at the top level or under publications. --
            authors_str = ""
            publications = self._as_list(item.get("publications"))
            if publications and isinstance(publications[0], dict):
                author_list = self._as_list(publications[0].get("authorNames"))
                authors_str = "; ".join(str(a) for a in author_list)
            if not authors_str:
                author_list = self._as_list(item.get("authorNames"))
                authors_str = "; ".join(str(a) for a in author_list)

            abstract = self._first(item.get("abstract"), "No abstract available.")
            report_numbers = self._as_list(item.get("reportNumbers"))
            report_number = report_numbers[0] if report_numbers else ""
            center = self._first(item.get("center"), "")
            if report_number or center:
                extra = " ".join(str(p) for p in (report_number, center) if p)
                abstract = f"{abstract} [NASA NTRS: {extra}]"

            publication_year = None
            date_raw = self._first(item.get("submittedDate")) or self._first(item.get("publicationDate"))
            if date_raw:
                try:
                    publication_year = int(str(date_raw)[:4])
                except (TypeError, ValueError):
                    publication_year = None

            citation_id = item.get("id")
            url = f"https://ntrs.nasa.gov/citations/{citation_id}" if citation_id else "#"

            doi = None
            for citation in self._as_list(item.get("citations")):
                if isinstance(citation, dict):
                    doi = self._first(citation.get("doi"))
                    if doi:
                        break

            return {
                "doi": doi,
                "url": url,
                "title": str(title),
                "authors_str": authors_str,
                "publication_year": publication_year,
                "abstract": str(abstract),
                "source": "NASA NTRS",
            }
        except Exception as e:
            print(f"   WARNING [NASA NTRS]: Formatting failed: {e}")
            return None

