# -*- coding: utf-8 -*-
"""
Module: test_pdf_harvester.py
Project: TALOS v5.18.0
Description:
    Hermetic unit tests for the Ethical Academic PDF Harvester. Verifies the
    four integrity guards (``%PDF-`` magic-bytes validation, SHA-256 hashing,
    atomic temporary-file writing, and size/status handling) without any live
    network access. ``requests.get`` is patched with a deterministic fake so the
    download pipeline is exercised end-to-end in isolation.

    Key design decisions:
    - Uses ``pytest`` ``tmp_path`` for isolated cache directories.
    - Patching targets ``src.ingestion.pdf_harvester.harvester.requests.get``
      so no external HTTP request is ever attempted.
    - Every assertion is deterministic and does not depend on ``pypdf``.

Dependencies:
    - pytest: test framework.
    - unittest.mock: request patching.
"""

import hashlib
import os

import pytest

from unittest.mock import patch

from src.ingestion.pdf_harvester.harvester import AcademicPDFHarvester


class _FakeResponse:
    """Minimal requests.Response stand-in supporting the context-manager API."""

    def __init__(self, content, status=200, headers=None):
        self._content = content
        self.status_code = status
        self.headers = headers or {}

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def iter_content(self, chunk_size):
        for offset in range(0, len(self._content), chunk_size):
            yield self._content[offset:offset + chunk_size]


class TestMagicBytesValidation:
    """Verify the %PDF- magic-bytes guard."""

    def test_valid_pdf_header_accepted(self):
        assert AcademicPDFHarvester.validate_magic_bytes(b"%PDF-1.7 ...") is True

    def test_html_payload_rejected(self):
        assert AcademicPDFHarvester.validate_magic_bytes(b"<html><body>error</body></html>") is False

    def test_empty_payload_rejected(self):
        assert AcademicPDFHarvester.validate_magic_bytes(b"") is False


class TestSha256:
    """Verify deterministic SHA-256 integrity hashing."""

    def test_sha256_matches_hashlib(self):
        payload = b"%PDF-1.4 binary payload"
        expected = hashlib.sha256(payload).hexdigest()
        assert AcademicPDFHarvester.compute_sha256(payload) == expected


class TestAtomicWrite:
    """Verify atomic temporary-file writing with no leftover tmp file."""

    def test_atomic_write_creates_final_only(self, tmp_path):
        harvester = AcademicPDFHarvester(cache_dir=str(tmp_path))
        path = harvester._atomic_write("7", b"%PDF-1.4 data")
        assert path == tmp_path / "7.pdf"
        assert (tmp_path / "7.pdf").exists()
        assert not (tmp_path / "tmp_7.pdf").exists()


class TestDownloadPipeline:
    """Verify the full download path with a mocked HTTP client."""

    def _harvester(self, tmp_path):
        return AcademicPDFHarvester(cache_dir=str(tmp_path), rate_limit_delay=0)

    def test_valid_pdf_downloaded_and_hashed(self, tmp_path):
        harvester = self._harvester(tmp_path)
        pdf_bytes = b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\n%%EOF\n"
        with patch("src.ingestion.pdf_harvester.harvester.requests.get",
                   return_value=_FakeResponse(pdf_bytes, status=200,
                                              headers={"Content-Length": str(len(pdf_bytes))})):
            sha256 = harvester._download_pdf("http://example.com/paper.pdf", "1")
        assert sha256 == hashlib.sha256(pdf_bytes).hexdigest()
        assert (tmp_path / "1.pdf").exists()

    def test_html_payload_rejected_by_magic_bytes(self, tmp_path):
        harvester = self._harvester(tmp_path)
        html = b"<html><head><title>Login</title></head><body>Access denied</body></html>"
        with patch("src.ingestion.pdf_harvester.harvester.requests.get",
                   return_value=_FakeResponse(html, status=200)):
            sha256 = harvester._download_pdf("http://example.com/blocked", "2")
        assert sha256 is None
        assert not (tmp_path / "2.pdf").exists()

    def test_non_200_status_returns_none(self, tmp_path):
        harvester = self._harvester(tmp_path)
        with patch("src.ingestion.pdf_harvester.harvester.requests.get",
                   return_value=_FakeResponse(b"", status=404)):
            sha256 = harvester._download_pdf("http://example.com/missing", "3")
        assert sha256 is None
