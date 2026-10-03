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
Module: bibtex_exporter.py
Project: TALOS v5.21.1
Description:
    Automated BibTeX / LaTeX scientific library exporter for TALOS. Reads the
    active-profile SQLite research database (``talos_research.db``) and emits a
    standard-compliant ``.bib`` library containing every curated paper above a
    configurable overall-score threshold, or every PRISMA-included study. The
    exporter is 100 percent local and air-gapped (Constitution II): it never
    performs network I/O and requires no API keys.

    Key design decisions:
    - Cite keys follow the ``AuthorYearTitleKeyword`` convention (for example
      ``Smarlamakis2026Cooperative``) and are deduplicated with a letter suffix.
    - Every LaTeX special character is sanitized so the output compiles under
      pdflatex / bibtex without escaping errors.
    - The output path defaults to ``data/exports/talos_library.bib``, resolved
      relative to the project root, and the target directory is created if
      missing.

Dependencies:
    - os, sys, re, argparse: Standard library utilities and CLI dispatch.
    - src.core.database_manager.DatabaseManager: Active-profile paper retrieval.
    - rich: Console and Panel for the confirmation summary.
"""
import os
import sys
import re
import argparse

# -- Resolve project root (same bootstrap pattern as all src/*.py modules). --
_P = os.path.abspath(os.path.dirname(__file__))
while _P and not os.path.exists(os.path.join(_P, "talos.py")):
    _P = os.path.dirname(_P)
if _P:
    sys.path.insert(0, _P)

from src.core.database_manager import DatabaseManager  # noqa: E402
from rich.console import Console  # noqa: E402
from rich.panel import Panel  # noqa: E402


# -- LaTeX reserved-character sanitization map ------------------------------
_BIBTEX_ESCAPE = {
    "&": "\\&",
    "%": "\\%",
    "$": "\\$",
    "#": "\\#",
    "_": "\\_",
    "{": "\\{",
    "}": "\\}",
    "~": "\\textasciitilde{}",
    "^": "\\textasciicircum{}",
    "\\": "\\textbackslash{}",
}


def _escape_bibtex(text):
    """Escape BibTeX/LaTeX reserved characters in a string.

    Args:
        text: Raw field value (str, numeric, or None).

    Returns:
        str: Sanitized string safe for direct inclusion in a BibTeX field.
    """
    if text is None:
        return ""
    return "".join(_BIBTEX_ESCAPE.get(ch, ch) for ch in str(text))


def _clean_key_token(text):
    """Strip a string down to alphanumeric characters for cite-key building.

    Args:
        text: Raw string token (str or None).

    Returns:
        str: Alphanumeric-only token, or an empty string when empty/None.
    """
    if not text:
        return ""
    return re.sub(r"[^A-Za-z0-9]", "", str(text))


class BibTeXExporter:
    """Automated BibTeX / LaTeX scientific library exporter.

    Connects to the active-profile SQLite database and produces a
    standard-compliant ``.bib`` file from curated papers.

    Attributes:
        console (rich.console.Console): Rich console for summary rendering.
        project_root (str): Absolute path to the TALOS project root.
        default_output (str): Default ``.bib`` output path under data/exports/.
    """

    # -- Columns read from the papers table for every exported record. --
    COLUMNS = (
        "doi", "url", "title", "authors", "publication_year", "abstract",
        "source", "overall_score", "suggested_tags", "publisher",
        "journal_issn", "prisma_decision", "quality_score", "evidence_quadrant",
    )

    def __init__(self):
        self.console = Console()
        self.project_root = _P
        self.default_output = os.path.join(_P, "data", "exports", "talos_library.bib")

    # ------------------------------------------------------------------
    # -- Citation-key generation --
    # ------------------------------------------------------------------

    @staticmethod
    def _first_author_surname(authors_str):
        """Return the first author surname from an author string.

        Args:
            authors_str (str): Author field (``Last, First; Last, First``).

        Returns:
            str: First author surname, or ``Anon`` when unavailable.
        """
        if not authors_str:
            return "Anon"
        first = str(authors_str).split(";")[0].split(",")[0].strip()
        parts = [p for p in first.split() if p]
        return parts[-1] if parts else "Anon"

    @staticmethod
    def _first_title_keyword(title):
        """Return the first significant word of a title for cite keys.

        Args:
            title (str): Raw paper title.

        Returns:
            str: Leading significant title word, or ``Paper`` when unavailable.
        """
        if not title:
            return "Paper"
        for token in str(title).split():
            cleaned = _clean_key_token(token)
            if len(cleaned) >= 4:
                return cleaned.capitalize()
        cleaned = _clean_key_token(str(title)) or "Paper"
        return cleaned[:20].capitalize()

    def _build_cite_key(self, paper, used_keys):
        """Generate a unique ``AuthorYearTitleKeyword`` citation key.

        Args:
            paper (dict): Paper record with authors/publication_year/title.
            used_keys (set): Already-assigned keys for collision resolution.

        Returns:
            str: Unique, sanitized citation key.
        """
        surname = _clean_key_token(self._first_author_surname(paper.get("authors")))
        surname = surname.capitalize() if surname else "Anon"
        year = paper.get("publication_year") or "nd"
        keyword = self._first_title_keyword(paper.get("title"))
        base = f"{surname}{year}{keyword}"
        key = base
        suffix = 0
        while key in used_keys:
            suffix += 1
            key = f"{base}{chr(96 + suffix)}"
        used_keys.add(key)
        return key

    # ------------------------------------------------------------------
    # -- Entry-type classification --
    # ------------------------------------------------------------------

    @staticmethod
    def _entry_type(paper):
        """Classify a paper as @article or @inproceedings.

        Args:
            paper (dict): Paper record with title/source fields.

        Returns:
            str: ``article`` or ``inproceedings``.
        """
        haystack = " ".join(
            str(paper.get(field) or "") for field in ("title", "source", "publisher")
        ).lower()
        for token in ("conference", "proceedings", "symposium", "workshop"):
            if token in haystack:
                return "inproceedings"
        return "article"

    @staticmethod
    def _venue(paper):
        """Resolve the best-available venue string for a paper.

        Args:
            paper (dict): Paper record.

        Returns:
            str: Venue (publisher, journal ISSN, or source), or empty string.
        """
        return str(
            paper.get("publisher")
            or paper.get("journal_issn")
            or paper.get("source")
            or ""
        )

    # ------------------------------------------------------------------
    # -- Single-entry formatting --
    # ------------------------------------------------------------------

    @staticmethod
    def _rigor_label(quality_score):
        """Map a Kitchenham quality score onto a short rigor label.

        Args:
            quality_score (float or None): Normalized ``S_qual`` in [0.0, 10.0].

        Returns:
            str: One of ``High Rigor``, ``Moderate Rigor``, or ``Low Rigor``.
        """
        if quality_score is None:
            return "Unassessed"
        value = float(quality_score)
        if value >= 7.5:
            return "High Rigor"
        if value >= 5.0:
            return "Moderate Rigor"
        return "Low Rigor"

    def _format_entry(self, paper, used_keys):
        """Render a single paper record as a BibTeX entry block.

        Args:
            paper (dict): Paper record.
            used_keys (set): Already-assigned citation keys.

        Returns:
            str: Formatted BibTeX entry, or empty string if the paper has no title.
        """
        title = paper.get("title")
        if not title:
            return ""
        cite_key = self._build_cite_key(paper, used_keys)
        entry_type = self._entry_type(paper)
        venue_field = "booktitle" if entry_type == "inproceedings" else "journal"
        venue = self._venue(paper)

        score = paper.get("overall_score")
        quality = paper.get("quality_score")
        quadrant = paper.get("evidence_quadrant")
        note_parts = []
        if score is not None:
            note_parts.append(f"TALOS Relevance: {float(score):.1f}/10")
        if quality is not None:
            rigor = self._rigor_label(quality)
            note_parts.append(
                f"Scientific Quality: {float(quality):.1f}/10 "
                f"(Kitchenham 2007: {rigor})"
            )
            if quadrant:
                note_parts.append(f"Quadrant: {quadrant}")
        note = "; ".join(note_parts)

        lines = [f"@{entry_type}{{{cite_key},"]
        lines.append(f"  title = {{{_escape_bibtex(title)}}},")
        lines.append(f"  author = {{{_escape_bibtex(paper.get('authors') or 'Anonymous')}}},")
        if venue:
            lines.append(f"  {venue_field} = {{{_escape_bibtex(venue)}}},")
        if paper.get("publication_year"):
            lines.append(f"  year = {{{_escape_bibtex(paper.get('publication_year'))}}},")
        if paper.get("doi"):
            lines.append(f"  doi = {{{_escape_bibtex(paper.get('doi'))}}},")
        if paper.get("url"):
            lines.append(f"  url = {{{_escape_bibtex(paper.get('url'))}}},")
        if paper.get("abstract"):
            lines.append(f"  abstract = {{{_escape_bibtex(paper.get('abstract'))}}},")
        if paper.get("suggested_tags"):
            lines.append(f"  keywords = {{{_escape_bibtex(paper.get('suggested_tags'))}}},")
        if note:
            lines.append(f"  note = {{{_escape_bibtex(note)}}},")
        # -- Remove the trailing comma from the final field and close. --
        lines[-1] = lines[-1].rstrip(",")
        lines.append("}")
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # -- Library export --
    # ------------------------------------------------------------------

    def export_library(self, output_path=None, min_score=7.0, only_prisma_included=False,
                       active_profile=None, min_quality=0.0, quadrant=None):
        """Export curated papers to a BibTeX (.bib) library file.

        Args:
            output_path (str or None): Target .bib path. Defaults to
                ``data/exports/talos_library.bib``.
            min_score (float): Minimum ``overall_score`` threshold.
            only_prisma_included (bool): When True, export only papers whose
                ``prisma_decision`` equals ``INCLUDE`` instead of score-filtering.
            active_profile (str or None): Optional profile name. When None, the
                DatabaseManager resolves the active profile automatically.
            min_quality (float): Minimum Kitchenham ``quality_score`` threshold.
                Papers with a ``NULL`` quality score are always retained so
                unappraised studies are not silently dropped (dual filter).
            quadrant (str or None): Optional ``evidence_quadrant`` restriction.
                When set, only papers in that quadrant are exported.

        Returns:
            tuple[str, int]: (output_file_path, exported_count).
        """
        # -- Resolve the target output path and ensure the directory exists. --
        output = output_path or self.default_output
        os.makedirs(os.path.dirname(output) or ".", exist_ok=True)

        # -- Connect to the active-profile (or explicitly named) database. --
        db_path = None
        if active_profile:
            db_path = os.path.join(self.project_root, "_profiles", active_profile, "talos_research.db")
        db = DatabaseManager(db_path=db_path)

        # -- Build the selection query (dual relevance/quality filter). --
        column_sql = ", ".join(self.COLUMNS)
        if only_prisma_included:
            rows = db.execute_query(
                f"SELECT {column_sql} FROM papers WHERE prisma_decision = 'INCLUDE' "
                "ORDER BY overall_score DESC",
                fetch_all=True,
            ) or []
        else:
            conditions = [
                "overall_score >= ?",
                "(quality_score >= ? OR quality_score IS NULL)",
            ]
            params = [float(min_score), float(min_quality)]
            if quadrant:
                conditions.append("evidence_quadrant = ?")
                params.append(quadrant)
            where_clause = " AND ".join(conditions)
            rows = db.execute_query(
                f"SELECT {column_sql} FROM papers WHERE {where_clause} "
                "ORDER BY overall_score DESC",
                tuple(params),
                fetch_all=True,
            ) or []

        papers = [dict(zip(self.COLUMNS, row)) for row in rows]

        used_keys = set()
        entries = [self._format_entry(paper, used_keys) for paper in papers]
        entries = [e for e in entries if e]

        with open(output, "w", encoding="utf-8") as handle:
            handle.write("% TALOS curated literature library\n")
            handle.write("% Generated by Project TALOS v5.21.1 (BibTeX Scientific Exporter)\n\n")
            handle.write("\n\n".join(entries))
            if entries:
                handle.write("\n")

        return output, len(entries)

    # ------------------------------------------------------------------
    # -- Rendering --
    # ------------------------------------------------------------------

    def render_export_summary(self, filepath, count):
        """Render a Rich confirmation panel for the export result.

        Args:
            filepath (str): The written .bib output path.
            count (int): Number of exported entries.

        Returns:
            rich.panel.Panel: The rendered panel (also printed to the console).
        """
        panel = Panel(
            f"[bold]BibTeX export complete.[/bold]\n"
            f"Exported [bold cyan]{count}[/bold cyan] entries to:\n"
            f"[green]{filepath}[/green]",
            title="TALOS BibTeX Scientific Exporter",
            border_style="bright_cyan",
        )
        self.console.print(panel)
        return panel

    def export_and_render(self, output_path=None, min_score=7.0, only_prisma_included=False,
                          active_profile=None, min_quality=0.0, quadrant=None):
        """Export the library and render the confirmation panel in one call.

        Args:
            output_path (str or None): Target .bib path.
            min_score (float): Minimum overall_score threshold.
            only_prisma_included (bool): Export PRISMA-included studies only.
            active_profile (str or None): Optional explicit profile name.
            min_quality (float): Minimum Kitchenham quality_score threshold.
            quadrant (str or None): Optional evidence_quadrant restriction.

        Returns:
            tuple[str, int]: (output_file_path, exported_count).
        """
        filepath, count = self.export_library(
            output_path=output_path,
            min_score=min_score,
            only_prisma_included=only_prisma_included,
            active_profile=active_profile,
            min_quality=min_quality,
            quadrant=quadrant,
        )
        self.render_export_summary(filepath, count)
        return filepath, count


def main(argv=None):
    """Standalone CLI entry point for the BibTeX exporter.

    Args:
        argv (list[str] or None): Command-line arguments following the script.

    Returns:
        int: Process exit code (0 on success).
    """
    parser = argparse.ArgumentParser(
        description="TALOS BibTeX Scientific Exporter (data/exports/talos_library.bib)."
    )
    parser.add_argument("--min-score", type=float, default=7.0,
                        help="Minimum overall_score threshold (default: 7.0).")
    parser.add_argument("--prisma-only", action="store_true",
                        help="Export only PRISMA-included studies (prisma_decision == INCLUDE).")
    parser.add_argument("--output", default=None,
                        help="Target .bib path (default: data/exports/talos_library.bib).")
    parser.add_argument("--profile", default=None,
                        help="Optional explicit profile name.")
    parser.add_argument("--min-quality", type=float, default=0.0,
                        help="Minimum Kitchenham quality_score threshold (default: 0.0).")
    parser.add_argument("--quadrant", default=None,
                        help="Optional evidence_quadrant filter "
                             "(ELITE_FOUNDATIONAL, IDEA_MINE, METHODOLOGICAL_EXEMPLAR, METHODOLOGICAL_NOISE).")
    args = parser.parse_args(argv)

    exporter = BibTeXExporter()
    exporter.export_and_render(
        output_path=args.output,
        min_score=args.min_score,
        only_prisma_included=args.prisma_only,
        active_profile=args.profile,
        min_quality=args.min_quality,
        quadrant=args.quadrant,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())



