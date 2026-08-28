# -*- coding: utf-8 -*-
"""
Module: academic_export.py
Project: TALOS v5.10.16
Description:
    Zero-dependency academic export engine producing BibTeX (.bib) and
    publication-ready LaTeX (.tex) artifacts from the TALOS paper database.
    Generates citation-keyed BibTeX entries, longtable-formatted literature
    tables for Overleaf, and PRISMA candidate-set tables for systematic
    literature reviews. Pure standard library; fully air-gapped (Constitution II).

Dependencies:
    - os, sys, re, argparse: Standard library utilities.
    - src.core.database_manager.DatabaseManager: Elite paper retrieval.
"""

import os
import sys
import re
import argparse

# -- Resolve project root (same pattern as all src/*.py modules) --------------
_P = os.path.abspath(os.path.dirname(__file__))
while _P and not os.path.exists(os.path.join(_P, 'talos.py')):
    _P = os.path.dirname(_P)
if _P:
    sys.path.insert(0, _P)

from src.core.database_manager import DatabaseManager


# -- Character escaping helpers ------------------------------------------------

_BIBTEX_ESCAPE = {
    "&": "\\&",
    "%": "\\%",
    "$": "\\$",
    "#": "\\#",
    "_": "\\_",
    "{": "\\{",
    "}": "\\}",
}

_LATEX_ESCAPE = dict(_BIBTEX_ESCAPE)
_LATEX_ESCAPE.update({
    "~": "\\textasciitilde{}",
    "^": "\\textasciicircum{}",
    "\\": "\\textbackslash{}",
})


def _escape_latex(text):
    """Escape LaTeX reserved characters in a string."""
    if text is None:
        return ""
    return "".join(_LATEX_ESCAPE.get(ch, ch) for ch in str(text))


def _escape_bibtex(text):
    """Escape BibTeX reserved characters in a string."""
    if text is None:
        return ""
    return "".join(_BIBTEX_ESCAPE.get(ch, ch) for ch in str(text))


def _authors(paper):
    """Return the author string from either standardized key name."""
    return paper.get("authors_str") or paper.get("authors") or "Anonymous"


def _first_author_surname(authors_str):
    """Return the first author surname for citation-key generation."""
    if not authors_str:
        return "Anon"
    first = authors_str.split(",")[0].strip()
    parts = [p for p in first.split() if p]
    return parts[-1] if parts else "Anon"


def _make_citation_key(paper, used_keys):
    """Generate a unique AuthorYear[letter] citation key."""
    surname = re.sub(r"[^A-Za-z0-9]", "", _first_author_surname(_authors(paper)))
    if not surname:
        surname = "Anon"
    year = paper.get("publication_year") or paper.get("year") or "nd"
    base = f"{surname}{year}"
    key = base
    suffix = 0
    while key in used_keys:
        suffix += 1
        key = f"{base}{chr(96 + suffix)}"
    used_keys.add(key)
    return key


def _paper_entry_type(paper):
    """Classify a paper as @article or @inproceedings."""
    title = (paper.get("title") or "").lower()
    if any(token in title for token in ("conference", "proceedings", "symposium", "workshop")):
        return "inproceedings"
    return "article"


def export_bibtex(papers, output_path):
    """Write BibTeX entries for a list of papers.

    Args:
        papers (list of dict): Paper records.
        output_path (str): Target .bib file path.

    Returns:
        int: Number of entries written.
    """
    used_keys = set()
    entries = []
    for paper in papers:
        key = _make_citation_key(paper, used_keys)
        entry_type = _paper_entry_type(paper)
        fields = [
            ("title", _escape_bibtex(paper.get("title", "N/A"))),
            ("author", _escape_bibtex(_authors(paper))),
        ]
        if paper.get("publication_year"):
            fields.append(("year", str(paper.get("publication_year"))))
        if paper.get("doi"):
            fields.append(("doi", paper.get("doi")))
        if paper.get("url"):
            fields.append(("url", _escape_bibtex(paper.get("url"))))
        if paper.get("source"):
            fields.append(("note", f"Source: {_escape_bibtex(paper.get('source'))}"))
        body = ",\n".join(f"  {k} = {{{v}}}" for k, v in fields)
        entries.append(f"@{entry_type}{{{key},\n{body}\n}}")
    text = "\n\n".join(entries) + ("\n" if entries else "")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(text)
    return len(entries)


def export_latex_table(papers, output_path, caption="TALOS Elite Literature Set"):
    """Write a publication-ready longtable of papers for Overleaf.

    Args:
        papers (list of dict): Paper records.
        output_path (str): Target .tex file path.
        caption (str): Table caption.

    Returns:
        int: Number of data rows written.
    """
    header = (
        "\\begin{longtable}{p{6.5cm} p{3.5cm} l l l}\n"
        f"\\caption{{{_escape_latex(caption)}}}\\\\\n"
        "\\toprule\n"
        "Title & Authors & Year & Source & Score \\\\\n"
        "\\midrule\n"
        "\\endhead\n"
    )
    rows = []
    for paper in papers:
        title = _escape_latex(paper.get("title", "N/A"))
        authors = _escape_latex(_authors(paper))
        year = str(paper.get("publication_year") or paper.get("year") or "")
        source = _escape_latex(paper.get("source", ""))
        score = paper.get("overall_score")
        score_str = f"{float(score):.2f}" if score is not None else ""
        rows.append(f"{title} & {authors} & {year} & {source} & {score_str} \\\\")
    footer = "\\bottomrule\n\\end{longtable}\n"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(header + "\n".join(rows) + "\n" + footer)
    return len(rows)


def export_prisma_candidate_table(candidate_sets, output_path):
    """Write a PRISMA-style candidate/selection table.

    Args:
        candidate_sets (list of tuple): ``(stage_label, count)`` pairs.
        output_path (str): Target .tex file path.

    Returns:
        int: Number of stages written.
    """
    header = (
        "\\begin{table}[h!]\n"
        "\\centering\n"
        "\\begin{tabular}{l r}\n"
        "\\toprule\n"
        "PRISMA Stage & Count \\\\\n"
        "\\midrule\n"
    )
    rows = [f"{_escape_latex(str(label))} & {int(count)} \\\\" for label, count in candidate_sets]
    footer = "\\bottomrule\n\\end{tabular}\n\\end{table}\n"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(header + "\n".join(rows) + "\n" + footer)
    return len(rows)


def _load_elite_papers(min_score=7.0):
    """Load elite papers from the active profile database.

    Args:
        min_score (float): Minimum overall_score threshold.

    Returns:
        list of dict: Elite paper records, ordered by score descending.
    """
    db = DatabaseManager()
    rows = db.execute_query(
        "SELECT doi, url, title, authors, publication_year, source, overall_score "
        "FROM papers WHERE overall_score >= ? ORDER BY overall_score DESC",
        (min_score,),
        fetch_all=True,
    ) or []
    keys = ["doi", "url", "title", "authors_str", "publication_year", "source", "overall_score"]
    return [dict(zip(keys, row)) for row in rows]


def main(argv=None):
    """CLI entry point for the academic export engine."""
    parser = argparse.ArgumentParser(
        description="TALOS Academic Export Engine (BibTeX and LaTeX)."
    )
    parser.add_argument("--elite", action="store_true",
                        help="Export elite papers (overall_score >= 7). Default scope.")
    parser.add_argument("--bib", action="store_true",
                        help="Generate a BibTeX (.bib) file.")
    parser.add_argument("--tex", action="store_true",
                        help="Generate a LaTeX (.tex) longtable.")
    parser.add_argument("--output-dir",
                        default=os.path.join(_P, "data", "reports", "export"),
                        help="Output directory (default: data/reports/export/).")
    args = parser.parse_args(argv)

    if not args.bib and not args.tex:
        args.bib = True
        args.tex = True

    papers = _load_elite_papers()
    if not papers:
        print("[EXPORT] No elite papers found (overall_score >= 7).")
        return 0

    os.makedirs(args.output_dir, exist_ok=True)

    if args.bib:
        bib_path = os.path.join(args.output_dir, "talos_elite_papers.bib")
        count = export_bibtex(papers, bib_path)
        print(f"[EXPORT] BibTeX written: {bib_path} ({count} entries)")

    if args.tex:
        tex_path = os.path.join(args.output_dir, "talos_elite_papers.tex")
        count = export_latex_table(papers, tex_path)
        print(f"[EXPORT] LaTeX table written: {tex_path} ({count} rows)")

    return 0


if __name__ == "__main__":
    sys.exit(main())


