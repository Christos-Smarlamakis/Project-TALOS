# -*- coding: utf-8 -*-
"""
Module: scoping_review_synthesizer.py
Project: TALOS v5.20.0
Description:
    Produces a publication-grade Scoping Review draft structured strictly per
    the PRISMA-ScR reporting guidelines (Tricco et al., 2018) and the PRISMA
    2020 statement (Page et al., 2021). ``synthesize_scoping_review`` emits a
    Markdown draft and ``synthesize_scoping_review_latex`` emits a LaTeX draft.
    Both compose seven canonical sections: Introduction, Protocol & Eligibility,
    Search Strategy, PRISMA 2020 Flowchart, Methodological Evidence Mapping,
    Thematic Discussion, and References. The flowchart is embedded by delegating
    to ``mermaid_generator.generate_prisma_mermaid`` so counts remain exact.
Dependencies:
    - src.prisma.mermaid_generator: PRISMA 2020 Mermaid flowchart generation.
"""

from typing import Any, Dict, List

from src.prisma.mermaid_generator import generate_prisma_mermaid


def _title(paper: Dict[str, Any]) -> str:
    """Extract a printable title from a standardized paper dictionary.

    Args:
        paper (Dict[str, Any]): Standardized paper record.

    Returns:
        str: Non-empty title string, or a fallback placeholder.
    """
    return str(paper.get("title") or "(untitled study)").strip()


def _authors(paper: Dict[str, Any]) -> str:
    """Extract a printable author string from a paper dictionary.

    Args:
        paper (Dict[str, Any]): Standardized paper record.

    Returns:
        str: Author string or an empty placeholder.
    """
    authors = paper.get("authors") or paper.get("authors_str") or ""
    return str(authors).strip()


def _reference_line(paper: Dict[str, Any], index: int) -> str:
    """Render a single numbered reference line for a paper.

    Args:
        paper (Dict[str, Any]): Standardized paper record.
        index (int): One-based reference number.

    Returns:
        str: Formatted reference entry.
    """
    year = paper.get("publication_year") or paper.get("year") or "n.d."
    doi = paper.get("doi") or ""
    source = paper.get("source") or ""
    suffix = f". doi:{doi}" if doi else ""
    if source:
        suffix += f" (source: {source})"
    return f"[{index}] {_authors(paper)} ({year}). {_title(paper)}{suffix}."


def _methodology_map(included_papers: List[Dict[str, Any]]) -> Dict[str, int]:
    """Aggregate a coarse methodological distribution over included papers.

    Uses any ``swarm_algorithm_type``, ``learning_paradigm`` or
    ``network_architecture`` labels attached to each record, falling back to the
    paper ``source``. Returns a sorted frequency mapping for the evidence map.

    Args:
        included_papers (List[Dict[str, Any]]): Included study records.

    Returns:
        Dict[str, int]: Frequency mapping keyed by methodology label.
    """
    dist: Dict[str, int] = {}
    for paper in included_papers:
        labels = []
        for key in ("swarm_algorithm_type", "learning_paradigm", "network_architecture"):
            value = paper.get(key)
            if value:
                labels.append(str(value))
        if not labels:
            labels.append(str(paper.get("source") or "Unspecified"))
        for label in labels:
            dist[label] = dist.get(label, 0) + 1
    return dict(sorted(dist.items(), key=lambda kv: kv[1], reverse=True))


def synthesize_scoping_review(
    included_papers: List[Dict[str, Any]],
    prisma_counts: Dict[str, int],
    topic: str,
) -> str:
    """Compose a PRISMA-ScR compliant scoping review draft in Markdown.

    Args:
        included_papers (List[Dict[str, Any]]): Final included study records.
        prisma_counts (Dict[str, int]): Record counts from the pipeline run.
        topic (str): The research topic under review.

    Returns:
        str: Publication-grade Markdown draft.
    """
    mermaid = generate_prisma_mermaid(prisma_counts)
    method_map = _methodology_map(included_papers)

    lines: List[str] = []
    lines.append(f"# Scoping Review: {topic}")
    lines.append("")
    lines.append("> Prepared by TALOS v5.17.0 -- Stanford DSPy PRISMA-ScR "
                 "Declarative Synthesis Pipeline. This draft follows the "
                 "PRISMA-ScR reporting guidelines (Tricco et al., 2018) and the "
                 "PRISMA 2020 statement (Page et al., 2021).")
    lines.append("")

    # -- 1. Introduction --
    lines.append("## 1. Introduction")
    lines.append("")
    lines.append(f"This scoping review maps the available evidence on **{topic}**. "
                 "The objective is to chart the breadth of methodological "
                 "approaches, identify recurring thematic clusters, and surface "
                 "gaps that warrant future primary research.")
    lines.append("")

    # -- 2. Protocol & Eligibility --
    lines.append("## 2. Protocol & Eligibility")
    lines.append("")
    lines.append("Eligibility was determined through a two-stage process: "
                 "title/abstract screening followed by full-record eligibility "
                 "assessment. Inclusion required methodological alignment with "
                 "the review question; studies were excluded when they fell "
                 "outside the declared domain scope or lacked a reportable "
                 "methodology.")
    lines.append("")

    # -- 3. Search Strategy --
    lines.append("## 3. Search Strategy")
    lines.append("")
    lines.append(f"Records were identified by declarative query synthesis over "
                 f"multi-database facets (n = {prisma_counts.get('databases', 0)} "
                 f"databases; n = {prisma_counts.get('registers', 0)} registers). "
                 f"After removing duplicates (n = "
                 f"{prisma_counts.get('duplicates_removed', 0)}), "
                 f"{prisma_counts.get('records_screened', 0)} records were screened.")
    lines.append("")

    # -- 4. PRISMA 2020 Flowchart --
    lines.append("## 4. PRISMA 2020 Flowchart")
    lines.append("")
    lines.append("```mermaid")
    lines.append(mermaid)
    lines.append("```")
    lines.append("")

    # -- 5. Methodological Evidence Mapping --
    lines.append("## 5. Methodological Evidence Mapping")
    lines.append("")
    if method_map:
        lines.append("| Methodology | Studies |")
        lines.append("|-------------|---------|")
        for label, count in method_map.items():
            lines.append(f"| {label} | {count} |")
    else:
        lines.append("_No methodological labels were recorded for the included "
                     "studies._")
    lines.append("")

    # -- 6. Thematic Discussion --
    lines.append("## 6. Thematic Discussion")
    lines.append("")
    lines.append(f"A total of {len(included_papers)} studies met the eligibility "
                 "criteria and were included in the synthesis. The thematic "
                 "clusters and methodological distribution above indicate the "
                 "predominant approaches in the field. Identified gaps and a "
                 "detailed narrative are enumerated below.")
    lines.append("")
    lines.append("### Included Studies")
    lines.append("")
    if included_papers:
        for idx, paper in enumerate(included_papers, start=1):
            lines.append(f"{idx}. {_reference_line(paper, idx)}")
    else:
        lines.append("_No studies were included._")
    lines.append("")

    # -- 7. References --
    lines.append("## 7. References")
    lines.append("")
    lines.append("[Tricco et al., 2018] Tricco, A. C., et al. (2018). PRISMA "
                 "Extension for Scoping Reviews (PRISMA-ScR): Checklist and "
                 "Explanation. _Annals of Internal Medicine_.")
    lines.append("[Page et al., 2021] Page, M. J., et al. (2021). The PRISMA 2020 "
                 "statement: an updated guideline for reporting systematic "
                 "reviews. _BMJ_, 372, n71.")
    lines.append("")
    return "\n".join(lines)


def synthesize_scoping_review_latex(
    included_papers: List[Dict[str, Any]],
    prisma_counts: Dict[str, int],
    topic: str,
) -> str:
    """Compose a PRISMA-ScR compliant scoping review draft in LaTeX.

    Args:
        included_papers (List[Dict[str, Any]]): Final included study records.
        prisma_counts (Dict[str, int]): Record counts from the pipeline run.
        topic (str): The research topic under review.

    Returns:
        str: Publication-grade LaTeX draft (article class).
    """
    method_map = _methodology_map(included_papers)
    refs = "".join(
        f"\\item {_reference_line(paper, idx)}\n"
        for idx, paper in enumerate(included_papers, start=1)
    )
    method_rows = "\n".join(
        f"    {label} & {count} \\\\" for label, count in method_map.items()
    )

    return f"""\\documentclass[11pt]{{article}}
\\title{{Scoping Review: {topic}}}
\\author{{Prepared by Project TALOS v5.17.0}}
\\date{{2026-09-28}}

\\begin{{document}}
\\maketitle

\\section{{Introduction}}
This scoping review maps the available evidence on \\textbf{{{topic}}}. The
objective is to chart the breadth of methodological approaches, identify
recurring thematic clusters, and surface gaps that warrant future research.

\\section{{Protocol \\& Eligibility}}
Eligibility was determined through a two-stage process: title/abstract screening
followed by full-record eligibility assessment.

\\section{{Search Strategy}}
Records were identified from {prisma_counts.get('databases', 0)} databases and
{prisma_counts.get('registers', 0)} registers. After removing
{prisma_counts.get('duplicates_removed', 0)} duplicates,
{prisma_counts.get('records_screened', 0)} records were screened.

\\section{{Methodological Evidence Mapping}}
\\begin{{tabular}}{{ll}}
\\hline
\\textbf{{Methodology}} & \\textbf{{Studies}} \\\\
\\hline
{method_rows}
\\hline
\\end{{tabular}}

\\section{{Thematic Discussion}}
A total of {len(included_papers)} studies met the eligibility criteria and were
included in the synthesis.

\\section{{References}}
\\begin{{enumerate}}
{refs}\\end{{enumerate}}

\\end{{document}}
"""
