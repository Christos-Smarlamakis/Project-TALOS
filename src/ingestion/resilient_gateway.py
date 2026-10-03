# -*- coding: utf-8 -*-
"""
Module: resilient_gateway.py
Project: TALOS v5.18.4
Description:
    Overarching self-healing ingestion gateway that wraps every one of the 18
    academic source adapters. When a publisher source fast-fails with an
    authentication or quota error (HTTP 401/403, "Developer Inactive", or
    "Quota Exceeded"), the gateway immediately abandons the source without any
    additional delayed sleep retry loop and transparently mirrors the failed
    publisher through the OpenAlex catalog, normalizing recovered records into
    the canonical paper schema with the original source key preserved.

    Key design decisions:
    - The gateway is a single overarching layer; individual source files are
      never patched with fallback logic (strict modularity).
    - Source adapters swallow HTTP errors and print them to stdout rather than
      raising, so the gateway captures stdout and classifies both raised
      exceptions and printed error markers for fast-fail detection.
    - A fresh gateway instance is constructed per harvest worker so the
      per-call outcome (recovered / error / status) never races across threads.

Dependencies:
    - requests: OpenAlex mirror HTTP client.
    - src.utils.http_client.build_session: shared polite HTTP session (optional).
    - io, contextlib: stdout capture for in-process error classification.
"""
import io
from contextlib import redirect_stdout
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import requests

try:
    from src.utils.http_client import build_session
except ImportError:  # pragma: no cover - optional shared session
    build_session = None


# -- Canonical publisher -> full legal name mapping for the OpenAlex mirror. --
PUBLISHER_FALLBACK_MAP = {
    "ieee": "Institute of Electrical and Electronics Engineers",
    "elsevier": "Elsevier",
    "springer": "Springer Nature",
}

# -- OpenAlex works endpoint used by the publisher mirror. --
OPENALEX_WORKS_URL = "https://api.openalex.org/works"

# -- Error markers that indicate an authentication or quota fast-fail. --
_AUTH_ERROR_MARKERS = (
    "401", "403", "unauthorized", "forbidden", "developer inactive",
    "quota exceeded", "quota", "rate limit", "rate limited",
)

class ResilientIngestionGateway:
    """Overarching self-healing wrapper for all 18 academic source adapters.

    Attributes:
        last_error (str | None): Message of the most recent fast-fail error.
        last_recovered (bool): True when the last harvest recovered via mirror.
        last_status (str): "COMPLETED", "RECOVERED", or "FAILED".
    """

    def __init__(self, session=None):
        """Initialize the gateway with an optional shared HTTP session.

        Args:
            session (requests.Session, optional): Shared session for the mirror.
        """
        self.session = session or (build_session() if build_session else requests)
        self.last_error: Optional[str] = None
        self.last_recovered: bool = False
        self.last_status: str = "COMPLETED"

    # -- Public API ---------------------------------------------------------
    def harvest_source(
        self,
        source_instance,
        query: str = "",
        criteria=None,
        date_limit: Optional[int] = None,
        source_key: Optional[str] = None,
        days_to_search: Optional[int] = None,
        mailto: str = "user@example.com",
    ) -> List[Dict[str, Any]]:
        """Harvest one source with fast-fail detection and publisher mirroring.

        Invokes ``source_instance.fetch_new_papers()`` under stdout capture,
        classifies authentication / quota failures, and when the failed source
        is a mapped publisher, mirrors it through OpenAlex. The result is always
        a list of canonical paper dictionaries -- primary results, recovered
        mirror results, or an empty list -- never an unhandled exception.

        Args:
            source_instance (object): Source adapter exposing fetch_new_papers().
            query (str): Research query forwarded to the OpenAlex mirror.
            criteria (str | dict): Inclusion criteria (telemetry only).
            date_limit (int): Historical window in days (mirror lookback fallback).
            source_key (str): Canonical lowercase slug for the source.
            days_to_search (int): Mirror lookback window in days.
            mailto (str): Polite-pool email for the OpenAlex mirror.

        Returns:
            list of dict: Canonical paper dictionaries.
        """
        self.last_error = None
        self.last_recovered = False
        self.last_status = "COMPLETED"

        # -- Invoke the primary source under stdout capture so interleaved
        # -- prints never corrupt the Rich Live telemetry table and so the
        # -- gateway can classify printed auth/quota markers after the fact.
        buf = io.StringIO()
        papers: Optional[List[Dict[str, Any]]] = None
        try:
            with redirect_stdout(buf):
                papers = source_instance.fetch_new_papers() or []
        except Exception as exc:  # noqa: BLE001 - per-source isolation
            papers = None
            self.last_error = str(exc)

        # -- Fast-fail classification from a raised exception OR printed stdout.
        if self.last_error is None:
            self.last_error = self._detect_auth_error(buf.getvalue())

        # -- Publisher-level fallback mirroring (IEEE / Elsevier / Springer).
        if self.last_error is not None and source_key:
            slug = str(source_key).lower()
            publisher = PUBLISHER_FALLBACK_MAP.get(slug)
            if publisher:
                print(
                    f"   [RECOVERY] {source_key} API error "
                    f"({self.last_error}). Auto-healing via OpenAlex "
                    f"{publisher} mirror..."
                )
                mirror_window = days_to_search if days_to_search is not None else date_limit
                recovered = self._mirror_via_openalex(
                    query, publisher, source_key, mirror_window, mailto)
                if recovered:
                    self.last_recovered = True
                    self.last_status = "RECOVERED"
                    self.last_error = None
                    print(
                        f"   [RECOVERY] OpenAlex mirror recovered "
                        f"{len(recovered)} papers for source '{source_key}'.")
                    return recovered
                self.last_status = "FAILED"
                print(
                    f"   [WARN] OpenAlex mirror returned no records for "
                    f"'{source_key}'. Returning empty result.")
                return []
            self.last_status = "FAILED"
            print(
                f"   [WARN] {source_key} fast-failed "
                f"({self.last_error}) and no publisher mirror is mapped.")
            return []

        # -- Clean path: primary results or a genuinely empty harvest.
        if papers is None:
            papers = []
        if not papers:
            self.last_status = "FAILED" if self.last_error else "COMPLETED"
        else:
            self.last_error = None
            self.last_status = "COMPLETED"
        return papers

    # -- Error detection ----------------------------------------------------
    def _detect_auth_error(self, stdout_text: str) -> Optional[str]:
        """Scan captured stdout for authentication / quota error markers.

        Args:
            stdout_text (str): Captured source-agent stdout.

        Returns:
            str | None: The matched marker phrase, or None when clean.
        """
        if not stdout_text:
            return None
        lowered = stdout_text.lower()
        for marker in _AUTH_ERROR_MARKERS:
            if marker in lowered:
                return marker
        return None

    # -- OpenAlex mirror ----------------------------------------------------
    def _mirror_via_openalex(
        self,
        query: str,
        publisher: str,
        source_key: str,
        days_to_search: Optional[int],
        mailto: str,
    ) -> List[Dict[str, Any]]:
        """Query OpenAlex for a publisher and normalize to canonical schema.

        Args:
            query (str): Research query.
            publisher (str): Full publisher lineage name.
            source_key (str): Original source slug (preserved in ``source``).
            days_to_search (int): Mirror lookback window in days.
            mailto (str): Polite-pool email.

        Returns:
            list of dict: Normalized canonical paper dictionaries.
        """
        if not query:
            query = publisher
        filters = f'primary_location.source.publisher_lineage:"{publisher}"'
        if days_to_search:
            cutoff = datetime.now().date() - timedelta(days=int(days_to_search))
            filters = f'from_publication_date:{cutoff.strftime("%Y-%m-%d")},' + filters
        params = {
            "search": query,
            "per_page": 50,
            "sort": "publication_date:desc",
            "filter": filters,
            "mailto": mailto,
        }
        try:
            response = self.session.get(
                OPENALEX_WORKS_URL, params=params, timeout=20)
            response.raise_for_status()
            data = response.json()
        except requests.exceptions.RequestException as exc:
            self.last_error = f"OpenAlex mirror request failed: {exc}"
            return []

        recovered: List[Dict[str, Any]] = []
        for work in data.get("results", []):
            paper = self._normalize_openalex_work(work, source_key)
            if paper:
                recovered.append(paper)
        return recovered

    @staticmethod
    def _reconstruct_abstract(inverted_index: Optional[Dict[str, List[int]]]) -> str:
        """Reconstruct an abstract from OpenAlex's inverted index format.

        Args:
            inverted_index (dict): Mapping of words to position lists.

        Returns:
            str: Reconstructed abstract text, or a placeholder when empty.
        """
        if not inverted_index:
            return "No abstract available."
        positions: Dict[int, str] = {}
        for word, locs in inverted_index.items():
            for loc in locs:
                positions[loc] = word
        return " ".join(positions[i] for i in sorted(positions))

    @classmethod
    def _normalize_openalex_work(
        cls, work: Dict[str, Any], source_key: str
    ) -> Optional[Dict[str, Any]]:
        """Normalize one OpenAlex work to the canonical TALOS paper schema.

        Args:
            work (dict): Raw OpenAlex work object.
            source_key (str): Original source slug for the ``source`` field.

        Returns:
            dict | None: Canonical paper dictionary, or None on failure.
        """
        try:
            authors_str = ", ".join([
                a.get("author", {}).get("display_name", "")
                for a in work.get("authorships", []) if a.get("author")
            ])
            doi_suffix = work.get("doi")
            doi = doi_suffix.replace("https://doi.org/", "") if doi_suffix else None
            url = doi_suffix or work.get(
                "primary_location", {}).get("landing_page_url", "#")
            abstract = cls._reconstruct_abstract(
                work.get("abstract_inverted_index"))
            return {
                "doi": doi,
                "url": url,
                "title": work.get("title", "N/A"),
                "authors_str": authors_str,
                "publication_year": work.get("publication_year"),
                "abstract": abstract,
                "source": source_key,
            }
        except Exception:  # noqa: BLE001 - per-record isolation
            return None