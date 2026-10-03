# -*- coding: utf-8 -*-
"""
Module: harvester.py
Project: TALOS v5.18.2
Description:
    Ethical Academic PDF Harvester. Implements a fault-tolerant, fully local
    download pipeline that resolves a legal Open Access or preprint full-text
    URL via the cascading resolver and persists the PDF to the gitignored
    ``data/fulltext_cache/`` directory. Six layers of fault tolerance:

    1. ``%PDF-`` magic-bytes validation (first five bytes) rejects HTML error
       pages before they touch the filesystem.
    2. Atomic temporary-file writing: data lands in ``tmp_<id>.pdf`` and is
       atomically renamed to ``<id>.pdf`` only after a successful flush.
    3. SHA-256 integrity hashing, persisted alongside the path.
    4. A 20 second per-request timeout.
    5. A 50 MB maximum file-size cap enforced during streamed reads.
    6. Polite rate limiting (1.5 s inter-request delay) behind a lock.

    ``harvest_candidates`` queries the active profile SQLite database for papers
    whose ``overall_score >= min_relevance``, downloads them sequentially, and
    updates ``papers`` columns ``local_pdf_path``, ``pdf_sha256``, and
    ``pdf_status`` ('DOWNLOADED' | 'UNAVAILABLE' | 'FAILED').

    Key design decisions:
    - Air-gapped by design: no telemetry, no analytics, no network dependency
      beyond the explicit, user-triggered legal download.
    - Downloads run sequentially so the polite rate limit is strictly honoured.

Dependencies:
    - hashlib: SHA-256 integrity computation.
    - os / pathlib: cache directory resolution and atomic file handling.
    - threading / time: polite rate limiting with a monotonic clock.
    - requests: HTTP client with streaming for the size-capped download.
    - src.ingestion.pdf_harvester.resolvers: the legal OA URL cascade.
"""

import hashlib
import os
import threading
import time

import requests

from pathlib import Path
from typing import Any, Dict, List, Optional

from src.ingestion.pdf_harvester.resolvers import resolve_oa_url, ACADEMIC_USER_AGENT

# -- Canonical cache directory (relative to the repository root). -- #
FULLTEXT_CACHE_RELPATH = os.path.join("data", "fulltext_cache")

# -- PDF magic-bytes header (first five bytes of every valid PDF). -- #
PDF_MAGIC = b"%PDF-"

# -- Download guards: timeout, size cap, and polite delay. -- #
DOWNLOAD_TIMEOUT_SECONDS = 20
MAX_FILE_SIZE_MB = 50
RATE_LIMIT_DELAY_SECONDS = 1.5

# -- pdf_status state machine values persisted to the papers table. -- #
STATUS_DOWNLOADED = "DOWNLOADED"
STATUS_UNAVAILABLE = "UNAVAILABLE"
STATUS_FAILED = "FAILED"


def _resolve_project_root() -> str:
    """Return the absolute repository root (the directory holding talos.py)."""
    current = os.path.abspath(os.path.dirname(__file__))
    while current and not os.path.exists(os.path.join(current, "talos.py")):
        parent = os.path.dirname(current)
        if parent == current:
            break
        current = parent
    return current

class AcademicPDFHarvester:
    """Download legal Open Access / preprint PDFs for elite candidate papers.

    Attributes:
        cache_dir (Path): Absolute directory where PDFs are persisted.
        timeout (int): Per-request timeout in seconds.
        max_file_size_bytes (int): Maximum accepted PDF size in bytes.
        rate_limit_delay (float): Inter-request delay in seconds.
    """

    def __init__(self, cache_dir: Optional[str] = None,
                 timeout: int = DOWNLOAD_TIMEOUT_SECONDS,
                 max_file_size_mb: int = MAX_FILE_SIZE_MB,
                 rate_limit_delay: float = RATE_LIMIT_DELAY_SECONDS):
        """Initialize the harvester with configurable fault-tolerance guards.

        Args:
            cache_dir (str, optional): Override the cache directory. Defaults to
                ``<project_root>/data/fulltext_cache``.
            timeout (int): Per-request timeout in seconds.
            max_file_size_mb (int): Maximum accepted PDF size in megabytes.
            rate_limit_delay (float): Inter-request delay in seconds.
        """
        project_root = _resolve_project_root()
        if cache_dir:
            self.cache_dir = Path(cache_dir)
        else:
            self.cache_dir = Path(project_root) / FULLTEXT_CACHE_RELPATH
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self.timeout = timeout
        self.max_file_size_bytes = int(max_file_size_mb * 1024 * 1024)
        self.rate_limit_delay = rate_limit_delay

        # -- Thread-safe monotonic clock for polite rate limiting. -- #
        self._rate_lock = threading.Lock()
        self._last_request_time = 0.0

    # -- Integrity helpers ------------------------------------------------- #
    @staticmethod
    def validate_magic_bytes(data: bytes) -> bool:
        """Return True when ``data`` begins with the ``%PDF-`` magic header.

        Args:
            data (bytes): Raw downloaded payload.

        Returns:
            bool: True when the first five bytes are exactly ``%PDF-``.
        """
        if not isinstance(data, (bytes, bytearray)):
            return False
        return bytes(data[:5]) == PDF_MAGIC

    @staticmethod
    def compute_sha256(data: bytes) -> str:
        """Compute the lowercase SHA-256 hex digest of ``data``.

        Args:
            data (bytes): Raw payload.

        Returns:
            str: Lowercase hexadecimal SHA-256 digest.
        """
        return hashlib.sha256(data).hexdigest()

    # -- File-system helpers ---------------------------------------------- #
    def _atomic_write(self, pdf_id: str, data: bytes) -> Path:
        """Write ``data`` to ``tmp_<id>.pdf`` then atomically rename to ``<id>.pdf``.

        Args:
            pdf_id (str): The stable per-paper identifier (database id).
            data (bytes): The validated PDF payload.

        Returns:
            Path: The final (renamed) cache path.
        """
        tmp_path = self.cache_dir / f"tmp_{pdf_id}.pdf"
        final_path = self.cache_dir / f"{pdf_id}.pdf"
        with open(tmp_path, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_path, final_path)
        return final_path

    # -- Polite rate limiting --------------------------------------------- #
    def _polite_wait(self) -> None:
        """Enforce the inter-request delay behind a thread-safe lock."""
        with self._rate_lock:
            now = time.monotonic()
            elapsed = now - self._last_request_time
            remaining = self.rate_limit_delay - elapsed
            if remaining > 0:
                time.sleep(remaining)
            self._last_request_time = time.monotonic()

    # -- Download pipeline ------------------------------------------------ #
    def _fetch_pdf_bytes(self, url: str) -> Optional[bytes]:
        """Stream-download ``url`` and return validated-size bytes, or None.

        Args:
            url (str): The resolved PDF URL.

        Returns:
            Optional[bytes]: Raw payload within the size cap, or None on any
                network error, non-200 status, or size-cap violation.
        """
        try:
            with requests.get(
                url,
                headers={"User-Agent": ACADEMIC_USER_AGENT},
                stream=True,
                timeout=self.timeout,
                allow_redirects=True,
            ) as response:
                if response.status_code != 200:
                    return None
                content_length = response.headers.get("Content-Length")
                if content_length:
                    try:
                        if int(content_length) > self.max_file_size_bytes:
                            return None
                    except ValueError:
                        pass
                chunks: List[bytes] = []
                total = 0
                for chunk in response.iter_content(chunk_size=65536):
                    if not chunk:
                        continue
                    total += len(chunk)
                    if total > self.max_file_size_bytes:
                        return None
                    chunks.append(chunk)
                return b"".join(chunks)
        except requests.RequestException:
            return None

    def _download_pdf(self, url: str, pdf_id: str) -> Optional[str]:
        """Download, validate, atomically write, and hash a single PDF.

        Args:
            url (str): The resolved PDF URL.
            pdf_id (str): The stable per-paper identifier (database id).

        Returns:
            Optional[str]: The SHA-256 hex digest on success, or None when the
                payload fails magic-bytes validation or any download guard.
        """
        data = self._fetch_pdf_bytes(url)
        if not data or not self.validate_magic_bytes(data):
            return None
        self._atomic_write(pdf_id, data)
        return self.compute_sha256(data)

    # -- Database helpers ------------------------------------------------- #
    def _active_db_path(self, active_profile: Optional[str] = None) -> str:
        """Resolve the active profile database path.

        Args:
            active_profile (str, optional): Explicit profile name override.

        Returns:
            str: Absolute path to the SQLite database.
        """
        if active_profile:
            root = _resolve_project_root()
            return os.path.join(root, "_profiles", active_profile, "talos_research.db")
        from src.core.database_manager import DatabaseManager
        return DatabaseManager().db_path

    def _candidate_papers(self, db_path: str, min_relevance: float) -> List[Dict[str, Any]]:
        """Return papers with ``overall_score >= min_relevance`` not yet downloaded.

        Args:
            db_path (str): Absolute SQLite path.
            min_relevance (float): Minimum ``overall_score`` threshold.

        Returns:
            List[Dict[str, Any]]: Candidate paper records ordered by relevance.
        """
        import sqlite3
        query = (
            "SELECT id, doi, url, title, openalex_id, pmcid, pmid, overall_score "
            "FROM papers WHERE overall_score >= ? AND "
            "(pdf_status IS NULL OR pdf_status != ?) ORDER BY overall_score DESC"
        )
        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(query, (min_relevance, STATUS_DOWNLOADED)).fetchall()
        return [dict(row) for row in rows]

    def _update_paper_pdf(self, db_path: str, paper_id: int, local_pdf_path: str,
                          pdf_sha256: Optional[str], pdf_status: str) -> None:
        """Persist the PDF harvest result for one paper.

        Args:
            db_path (str): Absolute SQLite path.
            paper_id (int): The paper row id.
            local_pdf_path (str): Local cache path (or empty string).
            pdf_sha256 (Optional[str]): Integrity digest (or None).
            pdf_status (str): One of DOWNLOADED / UNAVAILABLE / FAILED.
        """
        import sqlite3
        with sqlite3.connect(db_path) as conn:
            conn.execute(
                "UPDATE papers SET local_pdf_path = ?, pdf_sha256 = ?, "
                "pdf_status = ? WHERE id = ?",
                (local_pdf_path, pdf_sha256, pdf_status, paper_id),
            )

    # -- Public entry point ----------------------------------------------- #
    def harvest_candidates(self, min_relevance: float = 7.0,
                           active_profile: Optional[str] = None) -> Dict[str, Any]:
        """Harvest Open Access PDFs for every elite candidate paper.

        Args:
            min_relevance (float): Minimum ``overall_score`` threshold (default 7.0).
            active_profile (str, optional): Explicit profile override.

        Returns:
            Dict[str, Any]: Summary counters: ``candidates``, ``downloaded``,
                ``unavailable``, ``failed``, and a ``results`` list of per-paper
                outcome records.
        """
        db_path = self._active_db_path(active_profile)
        candidates = self._candidate_papers(db_path, min_relevance)

        summary: Dict[str, Any] = {
            "candidates": len(candidates),
            "downloaded": 0,
            "unavailable": 0,
            "failed": 0,
            "results": [],
        }

        for paper in candidates:
            paper_id = paper.get("id")
            self._polite_wait()
            resolved = resolve_oa_url(paper)
            if not resolved:
                self._update_paper_pdf(db_path, paper_id, "", None, STATUS_UNAVAILABLE)
                summary["unavailable"] += 1
                summary["results"].append(
                    {"id": paper_id, "title": paper.get("title"), "status": STATUS_UNAVAILABLE}
                )
                continue

            pdf_url, source = resolved
            try:
                sha256 = self._download_pdf(pdf_url, str(paper_id))
            except Exception:
                sha256 = None

            if sha256:
                local_path = str(self.cache_dir / f"{paper_id}.pdf")
                self._update_paper_pdf(db_path, paper_id, local_path, sha256,
                                       STATUS_DOWNLOADED)
                summary["downloaded"] += 1
                summary["results"].append(
                    {"id": paper_id, "title": paper.get("title"), "status": STATUS_DOWNLOADED,
                     "source": source, "sha256": sha256}
                )
            else:
                self._update_paper_pdf(db_path, paper_id, "", None, STATUS_FAILED)
                summary["failed"] += 1
                summary["results"].append(
                    {"id": paper_id, "title": paper.get("title"), "status": STATUS_FAILED,
                     "source": source}
                )

        return summary



