# -*- coding: utf-8 -*-
"""
Module: section_extractor.py
Project: TALOS v5.20.0
Description:
    Air-gapped PDF text extraction and smart section slicing for the Tier-2
    Quality Swarm. ``PDFSectionExtractor`` reads a locally cached PDF, extracts
    its full text with a lightweight local library (``pypdf``) and, when that is
    unavailable, falls back to a layout-aware printable-byte parser. The text is
    then split into four canonical evidence windows cached under
    ``data/fulltext_cache/<id>/``:

    - ``methodology.txt``        : Problem Formulation & Mathematical Modeling.
    - ``experiments.txt``        : Experiments, Baselines & Benchmark Results.
    - ``code_availability.txt``  : Footnotes, Repositories, Open Science.
    - ``limitations.txt``        : Discussion, Threats to Validity, Limitations.

    These cached windows are consumed by ``SmartSectionSlicer`` in
    ``src/prisma/quality_swarm.py`` so that forensic quality auditors read real
    extracted PDF section text whenever a local PDF exists.

    Key design decisions:
    - Extraction runs 100% locally with zero external telemetry or cloud calls.
    - Heading detection mirrors the ``SmartSectionSlicer`` heuristic so the two
      layers agree on section boundaries.
    - Every extraction is idempotent and fails soft.

Dependencies:
    - os / pathlib: cache directory resolution and file writing.
    - re: heading-pattern section detection.
    - pypdf (optional): primary text extraction; falls back to a regex parser.
"""

import os
import re

from pathlib import Path
from typing import Dict, List, Optional

# -- Guarded optional dependency: pypdf for local PDF text extraction. -- #
try:
    import pypdf
    PYPDF_AVAILABLE = True
except ImportError:  # pragma: no cover - pypdf not installed
    pypdf = None  # type: ignore[assignment]
    PYPDF_AVAILABLE = False

# -- Cache directory (relative to the repository root). -- #
FULLTEXT_CACHE_RELPATH = os.path.join("data", "fulltext_cache")

# -- Canonical section key -> cached filename mapping. -- #
SECTION_FILES: Dict[str, str] = {
    "methodology": "methodology.txt",
    "experiments": "experiments.txt",
    "code_availability": "code_availability.txt",
    "discussion_limitations": "limitations.txt",
}

# -- Heading patterns per section (mirrors SmartSectionSlicer.SECTION_PATTERNS). -- #
SECTION_PATTERNS: Dict[str, tuple] = {
    "methodology": (
        r"method", r"approach", r"model", r"formulation", r"preliminaries",
        r"background", r"problem statement", r"proposed", r"mathematical",
    ),
    "experiments": (
        r"experiment", r"result", r"evaluation", r"benchmark", r"ablation",
        r"performance", r"setup", r"baseline",
    ),
    "code_availability": (
        r"code availability", r"data availability", r"reproducibility",
        r"artifact", r"implementation details", r"open.source", r"software",
        r"repository", r"github",
    ),
    "discussion_limitations": (
        r"discussion", r"limitation", r"conclusion", r"threats? to validity",
        r"future work", r"failure",
    ),
}


def _resolve_project_root() -> str:
    """Return the absolute repository root (the directory holding talos.py)."""
    current = os.path.abspath(os.path.dirname(__file__))
    while current and not os.path.exists(os.path.join(current, "talos.py")):
        parent = os.path.dirname(current)
        if parent == current:
            break
        current = parent
    return current

class PDFSectionExtractor:
    """Extract and cache targeted section text windows from local PDFs.

    Attributes:
        cache_dir (Path): Absolute directory holding per-paper section windows.
    """

    def __init__(self, cache_dir: Optional[str] = None):
        """Initialize the extractor with a configurable cache directory.

        Args:
            cache_dir (str, optional): Override the cache directory. Defaults to
                ``<project_root>/data/fulltext_cache``.
        """
        if cache_dir:
            self.cache_dir = Path(cache_dir)
        else:
            self.cache_dir = Path(_resolve_project_root()) / FULLTEXT_CACHE_RELPATH
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    # -- Text extraction -------------------------------------------------- #
    @staticmethod
    def _extract_text_pypdf(pdf_path: str) -> str:
        """Extract full text using ``pypdf`` when available.

        Args:
            pdf_path (str): Absolute path to the PDF.

        Returns:
            str: Concatenated page text, or empty string on failure.
        """
        try:
            if not PYPDF_AVAILABLE or pypdf is None:
                return ""
            reader = pypdf.PdfReader(pdf_path)
            pages = []
            for page in reader.pages:
                try:
                    pages.append(page.extract_text() or "")
                except Exception:
                    pages.append("")
            return "\n".join(pages).strip()
        except Exception:
            return ""

    @staticmethod
    def _extract_text_fallback(pdf_path: str) -> str:
        """Fallback printable-byte parser for PDFs without ``pypdf``.

        Args:
            pdf_path (str): Absolute path to the PDF.

        Returns:
            str: Best-effort printable text recovered from the raw bytes.
        """
        try:
            with open(pdf_path, "rb") as handle:
                raw = handle.read()
        except OSError:
            return ""
        cleaned = re.sub(rb"[^\x20-\x7e\n\t\r]+", b" ", raw)
        return cleaned.decode("ascii", errors="ignore").strip()

    def _extract_text(self, pdf_path: str) -> str:
        """Return the full text of a PDF, preferring ``pypdf`` over the fallback.

        Args:
            pdf_path (str): Absolute path to the PDF.

        Returns:
            str: Extracted text (may be empty for unreadable PDFs).
        """
        text = self._extract_text_pypdf(pdf_path)
        if not text:
            text = self._extract_text_fallback(pdf_path)
        return text.strip()

    # -- Section slicing -------------------------------------------------- #
    @staticmethod
    def _slice_sections(text: str) -> Dict[str, str]:
        """Split full text into canonical section windows by heading matches.

        Args:
            text (str): The full paper text.

        Returns:
            Dict[str, str]: Mapping of section key to its extracted body.
        """
        sections: Dict[str, List[str]] = {key: [] for key in SECTION_PATTERNS}
        if not text:
            return {key: "" for key in sections}

        current_key: Optional[str] = None
        for line in text.splitlines():
            stripped = line.strip().lower()
            heading_like = (
                stripped
                and len(stripped) < 90
                and not stripped.endswith(".")
                and re.match(r"^((\d+(\.\d+)*)\s+|[ivx]+\.\s+)?\S", stripped)
            )
            if heading_like:
                for key, patterns in SECTION_PATTERNS.items():
                    if any(re.search(p, stripped) for p in patterns):
                        current_key = key
                        break
                continue
            if current_key is not None:
                sections[current_key].append(line)

        return {key: "\n".join(block).strip() for key, block in sections.items()}

    # -- Public API ------------------------------------------------------- #
    def extract_sections(self, pdf_path: str, paper_id: str) -> Dict[str, str]:
        """Extract and persist the four canonical section windows for a PDF.

        Args:
            pdf_path (str): Absolute path to the local PDF.
            paper_id (str): Stable per-paper identifier (database id).

        Returns:
            Dict[str, str]: Mapping of section key to extracted text.
        """
        text = self._extract_text(pdf_path)
        sections = self._slice_sections(text)

        paper_dir = self.cache_dir / str(paper_id)
        paper_dir.mkdir(parents=True, exist_ok=True)

        for key, body in sections.items():
            filename = SECTION_FILES.get(key)
            if not filename:
                continue
            with open(paper_dir / filename, "w", encoding="utf-8") as handle:
                handle.write(body)

        return sections

    def load_sections(self, paper_id: str) -> Dict[str, str]:
        """Load previously cached section windows for a paper, if present.

        Args:
            paper_id (str): Stable per-paper identifier (database id).

        Returns:
            Dict[str, str]: Mapping of section key to cached text (empty where
                no file exists).
        """
        paper_dir = self.cache_dir / str(paper_id)
        out: Dict[str, str] = {}
        for key, filename in SECTION_FILES.items():
            path = paper_dir / filename
            if path.exists():
                try:
                    out[key] = path.read_text(encoding="utf-8").strip()
                except OSError:
                    out[key] = ""
            else:
                out[key] = ""
        return out


