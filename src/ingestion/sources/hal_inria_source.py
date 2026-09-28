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
Module: hal_inria_source.py
Project: TALOS v5.14.2
Description:
    Search agent for the HAL open science repository public REST API
    (https://api.archives-ouvertes.fr/search/). Harvests CNRS, Inria, and ONERA
    robotics, multi-agent reinforcement learning, and French/EU PhD theses. The
    endpoint returns Solr-style JSON and requires no API key or authentication,
    preserving full air-gapped/local-first operation with graceful degradation
    when offline (Constitution II).

    Key design decisions:
    - Uses the ``fl`` (field list) parameter to minimize the response payload.
    - Normalizes each HAL document into the standardized TALOS paper dict:
      {doi, url, title, authors_str, publication_year, abstract, source}.
    - The abstract is appended with the document type and arXiv identifier when
      present, retaining grey-literature provenance through evaluation.

Dependencies:
    - requests: HTTP client for the HAL search endpoint.
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


class HalInriaSource:
    """Search agent for the HAL open science repository public REST API.

    Fetches CNRS / Inria / ONERA robotics, MARL, and PhD theses via the
    /search/ endpoint with configurable queries and result limits, emitting
    standardized paper dictionaries with HAL landing-page URLs and, when
    available, DOIs and keywords.

    Attributes:
        query (str): Search query from config.
        total_max_results (int): Maximum results to fetch.
        session: HTTP session (or raw requests module when unavailable).
        enabled (bool): Whether the source is operational.
    """

    BASE_URL = "https://api.archives-ouvertes.fr/search/"

    # -- Field list passed to HAL's Solr endpoint to keep payloads minimal. --
    FIELDS = (
        "title_s,authFullName_s,abstract_s,producedDate_s,publicationDate_s,"
        "doiId_s,uri_s,keyword_s,docType_s,arxivId_s"
    )

    def __init__(self, config: Dict[str, Any]):
        self.session = build_session() if build_session else requests
        self.query = config.get(
            "hal_inria_query",
            "multi-agent reinforcement learning swarm robotics",
        )
        self.total_max_results = config.get("max_results_config", {}).get("hal_inria", 50)
        self.enabled = True
        print("INFO: HalInriaSource initialized.")

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
        """Fetch CNRS / Inria / ONERA robotics papers from HAL.

        Uses cursor-less row-based pagination over the public search endpoint.

        Returns:
            list of dict: Standardized paper dictionaries.
        """
        print("-> Searching HAL / Inria...")
        all_papers = []
        rows = min(100, self.total_max_results)
        start = 0

        while len(all_papers) < self.total_max_results:
            params = {
                "q": self.query,
                "fl": self.FIELDS,
                "wt": "json",
                "rows": rows,
                "start": start,
            }
            try:
                response = self.session.get(self.BASE_URL, params=params, timeout=30)
                if response.status_code == 429:
                    print("   WARNING [HAL]: Rate limit. Waiting 10 seconds...")
                    time.sleep(10)
                    continue
                response.raise_for_status()
                data = response.json()
            except requests.exceptions.RequestException as e:
                print(f"   ERROR [HAL]: Fetch failed: {e}")
                break
            except ValueError as e:
                print(f"   ERROR [HAL]: Invalid JSON: {e}")
                break

            response_obj = data.get("response") or {}
            docs = response_obj.get("docs") or []
            if not docs:
                break

            for item in docs:
                formatted = self._format_paper(item)
                if formatted:
                    all_papers.append(formatted)
                if len(all_papers) >= self.total_max_results:
                    break

            start += rows
            time.sleep(0.5)

        print(f"   SUCCESS [HAL]: Found {len(all_papers)} new papers.")
        return all_papers

    def search_papers(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search HAL by a specific query (used for metadata enrichment).

        Args:
            query (str): Search query string.
            limit (int): Maximum results to return.

        Returns:
            list of dict: Standardized paper dictionaries.
        """
        params = {"q": query, "fl": self.FIELDS, "wt": "json", "rows": limit, "start": 0}
        try:
            response = self.session.get(self.BASE_URL, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()
        except requests.exceptions.RequestException:
            return []
        results = []
        for item in (data.get("response") or {}).get("docs") or []:
            paper = self._format_paper(item)
            if paper:
                results.append(paper)
        return results

    def _format_paper(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Convert a HAL document to the standardized TALOS format.

        Args:
            item (dict): A single HAL ``response.docs`` entry.

        Returns:
            dict: Standardized paper dictionary, or None on failure.
        """
        try:
            title = self._first(item.get("title_s"))
            if not title:
                return None

            authors_str = "; ".join(str(a) for a in self._as_list(item.get("authFullName_s")))
            abstract = self._first(item.get("abstract_s"), "No abstract available.")

            doc_type = self._first(item.get("docType_s"), "")
            arxiv_id = self._first(item.get("arxivId_s"), "")
            if doc_type or arxiv_id:
                extra = " ".join(str(p) for p in (doc_type, arxiv_id) if p)
                abstract = f"{abstract} [HAL: {extra}]"

            publication_year = None
            date_raw = self._first(item.get("publicationDate_s")) or self._first(item.get("producedDate_s"))
            if date_raw:
                try:
                    publication_year = int(str(date_raw)[:4])
                except (TypeError, ValueError):
                    publication_year = None

            doi = self._first(item.get("doiId_s"))
            url = self._first(item.get("uri_s"))
            if not url and doi:
                url = f"https://doi.org/{doi}"

            return {
                "doi": doi,
                "url": url or "#",
                "title": str(title),
                "authors_str": authors_str,
                "publication_year": publication_year,
                "abstract": str(abstract),
                "source": "HAL",
            }
        except Exception as e:
            print(f"   WARNING [HAL]: Formatting failed: {e}")
            return None

