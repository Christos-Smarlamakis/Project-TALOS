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
Module: scigov_source.py
Project: TALOS v5.20.0

Description:
    Search agent for the Science.gov federal science portal API v2. Fetches
    records matching the configured query and normalizes each hit into the
    standardized TALOS paper dictionary (doi, url, title, authors_str,
    publication_year, abstract, source).

    v5.18.5: Fault-tolerant DNS/connection isolation. The adapter catches
    ``requests.exceptions.RequestException``, ``requests.exceptions.ConnectionError``,
    and the underlying ``urllib3`` DNS ``NameResolutionError`` so that a
    failure to resolve ``api.science.gov`` logs a single informational notice
    and returns an empty list instead of raising an unhandled error. The
    source is disabled by default so the DRL agent avoids dead exploration
    actions against the frequently-absent endpoint; enable it explicitly via
    the ``scigov_enabled`` config key or the ``SCI_GOV_ENABLED`` env var.

Dependencies:
    - os: Environment-variable based enable/disable resolution.
    - requests: HTTP client for the Science.gov records endpoint.
    - src.utils.http_client: Shared session factory (optional, graceful import).
"""
import os
import requests

try:
    from src.utils.http_client import build_session
except ImportError:
    build_session = None

try:
    from urllib3.exceptions import NameResolutionError
except ImportError:
    NameResolutionError = None

from typing import List, Dict, Any

# -- Optional DNS exception tuple; empty when urllib3 is absent. --
_DNS_EXCEPTIONS = (NameResolutionError,) if NameResolutionError else ()


class ScienceGovSource:
    """Search agent for the Science.gov federal science portal API."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize the Science.gov agent from configuration.

        Args:
            config (dict): Application configuration dictionary.
        """
        self.session = build_session() if build_session else requests
        self.query = config.get("scigov_query", "unmanned systems")
        self.max_results = config.get("max_results_config", {}).get("scigov", 100)
        self.base_url = "https://api.science.gov/search/v2/records"
        # -- v5.18.5: disabled by default so the DRL agent avoids dead
        # -- exploration actions; opt in via config or environment. --
        self.enabled = bool(config.get("scigov_enabled", False)) or os.getenv(
            "SCI_GOV_ENABLED", "").lower() in ("1", "true", "yes")
        if self.enabled:
            print("INFO: ScienceGovSource initialized.")
        else:
            print("INFO: ScienceGovSource disabled by default (scigov_enabled=false).")

    @staticmethod
    def _is_dns_failure(exc: Exception) -> bool:
        """Detect whether an exception is a DNS resolution failure.

        Args:
            exc (Exception): The exception raised during the HTTP request.

        Returns:
            bool: True when the message indicates name resolution failure.
        """
        text = str(exc).lower()
        tokens = (
            "name or service not known",
            "getaddrinfo",
            "name_resolution",
            "failed to resolve",
            "nodename nor servname",
            "temporary failure in name resolution",
        )
        return any(token in text for token in tokens)

    def fetch_new_papers(self) -> List[Dict[str, Any]]:
        """Fetch records from the Science.gov API.

        The endpoint does not support a date filter, so results are sorted by
        published date where available. DNS and connection failures are
        isolated: the method logs a notice and returns an empty list rather
        than raising an unhandled error.

        Returns:
            list of dict: Standardized paper dictionaries (empty when disabled
                or when the API is unreachable).
        """
        if not self.enabled:
            return []

        print("-> Searching Science.gov...")
        params = {
            'q': self.query,
            'size': self.max_results,
            'sort': 'published_date:desc'
        }
        try:
            response = self.session.get(self.base_url, params=params, timeout=20)
            response.raise_for_status()
            data = response.json()

            papers = []
            for record in data.get('results', []):
                formatted_paper = self._format_paper(record)
                if formatted_paper:
                    papers.append(formatted_paper)

            print(f"   SUCCESS [Science.gov]: Found {len(papers)} papers.")
            return papers

        except _DNS_EXCEPTIONS:
            print("[INFO] Science.gov API unavailable. Delegating to federal OSTI coverage.")
            return []
        except requests.exceptions.ConnectionError as exc:
            if self._is_dns_failure(exc):
                print("[INFO] Science.gov API unavailable. Delegating to federal OSTI coverage.")
            else:
                print(f"   ERROR [Science.gov]: Connection failed: {exc}")
            return []
        except requests.exceptions.RequestException as exc:
            print(f"   ERROR [Science.gov]: Request failed: {exc}")
            return []

    def _format_paper(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Convert a Science.gov record to the standardized TALOS format.

        Args:
            record (dict): Raw record object from the Science.gov response.

        Returns:
            dict or None: Standardized paper dictionary, or None on failure.
        """
        try:
            authors_list = record.get('authors', [])
            authors_str = ", ".join(
                [author['name'] for author in authors_list if 'name' in author])

            doi = record.get("doi")
            url = f"https://doi.org/{doi}" if doi else record.get(
                "doiLink", record.get("link", "#"))

            publication_year = record.get("publication_year") or record.get("year")
            if publication_year and isinstance(publication_year, str) and publication_year.isdigit():
                publication_year = int(publication_year)
            elif not isinstance(publication_year, int):
                publication_year = None

            return {
                "doi": doi,
                "url": url,
                "title": record.get("title", "N/A"),
                "authors_str": authors_str if authors_str else "N/A",
                "publication_year": publication_year,
                "abstract": record.get("description", "No abstract available."),
                "source": "Science.gov"
            }
        except Exception as exc:
            print(f"   WARNING [Science.gov]: Failed to format a paper: {exc}")
            return None
