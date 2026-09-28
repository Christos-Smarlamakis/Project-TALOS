# -*- coding: utf-8 -*-
"""
Module: mermaid_generator.py
Project: TALOS v5.15.0
Description:
    Generates a standard-compliant PRISMA 2020 flow diagram in pure Mermaid
    syntax (``flowchart TD``) for the TALOS declarative scoping review pipeline.
    The generator injects exact recorded record counts from the four-phase flow
    (Identification -> Screening -> Eligibility -> Included) so the resulting
    figure is fully reproducible and audit-ready. HTML and Markdown export
    wrappers are provided for direct embedding in reports and dashboards.

    The count keys accepted by ``generate_prisma_mermaid`` are:
        databases, registers, duplicates_removed, records_screened,
        records_excluded, reports_sought, reports_assessed,
        reports_excluded, studies_included, plus optional excluded_reasons.
Dependencies:
    - html: Escaping study titles/reasons embedded in node labels.
"""

import html
from typing import Dict, Optional


def _n(counts: Dict[str, int], key: str, default: int = 0) -> int:
    """Return an integer count, coercing ``None`` and missing keys to a default.

    Args:
        counts (Dict[str, int]): Record-count mapping.
        key (str): Key to read.
        default (int): Value to return when the key is absent or non-numeric.

    Returns:
        int: The resolved count.
    """
    try:
        value = counts.get(key, default)
        return int(value) if value is not None else default
    except (TypeError, ValueError):
        return default


def generate_prisma_mermaid(counts: Dict[str, int]) -> str:
    """Build a PRISMA 2020 ``flowchart TD`` Mermaid diagram with exact counts.

    The diagram follows the canonical PRISMA 2020 layout: a left column for
    Identification (databases + registers), a central Screening column, a right
    Eligibility column, and a final Included node. Every ``(n = ...)`` label is
    populated from ``counts`` so the figure reflects the actual pipeline run.

    Args:
        counts (Dict[str, int]): Record-count mapping (see module docstring).

    Returns:
        str: Pure Mermaid ``flowchart TD`` source.
    """
    databases = _n(counts, "databases", 0)
    registers = _n(counts, "registers", 0)
    dup = _n(counts, "duplicates_removed", 0)
    screened = _n(counts, "records_screened", 0)
    excluded = _n(counts, "records_excluded", 0)
    sought = _n(counts, "reports_sought", 0)
    assessed = _n(counts, "reports_assessed", 0)
    excluded2 = _n(counts, "reports_excluded", 0)
    included = _n(counts, "studies_included", 0)

    reasons = counts.get("excluded_reasons", {}) or {}
    reason_lines = ""
    if isinstance(reasons, dict) and reasons:
        reason_lines = "<br/>" + "<br/>".join(
            f"{html.escape(str(reason))} (n = {count})"
            for reason, count in reasons.items()
        )

    excluded_label = f"Records excluded<br/>(n = {excluded})"
    excluded2_label = f"Reports excluded<br/>(n = {excluded2})"
    if reason_lines:
        excluded2_label += reason_lines

    mermaid = "\n".join(
        line
        for line in [
            "flowchart TD",
            f'    A["Records identified from<br/>databases (n = {databases})"] --> C',
            f'    B["Records identified from<br/>registers (n = {registers})"] --> C',
            f'    C["Records after duplicates removed<br/>(n = {max(databases + registers - dup, 0)})"]',
            f'    C --> D["Records screened<br/>(n = {screened})"]',
            f'    D --> E["Records excluded<br/>(n = {excluded})"]',
            f'    D --> F["Reports sought for retrieval<br/>(n = {sought})"]',
            f'    F --> G["Reports assessed for eligibility<br/>(n = {assessed})"]',
            f'    G --> H["{excluded2_label}"]',
            f'    G --> I["Studies included in review<br/>(n = {included})"]',
        ]
    )
    return mermaid


def mermaid_to_markdown(mermaid: str, caption: Optional[str] = None) -> str:
    """Wrap a Mermaid diagram in a Markdown code fence.

    Args:
        mermaid (str): Mermaid source text.
        caption (Optional[str]): Optional figure caption placed above the fence.

    Returns:
        str: Markdown block suitable for the scoping review draft.
    """
    block = "```mermaid\n" + mermaid + "\n```"
    if caption:
        return f"{caption}\n\n{block}"
    return block


def mermaid_to_html(mermaid: str, title: str = "PRISMA 2020 Flowchart") -> str:
    """Wrap a Mermaid diagram in a minimal self-contained HTML document.

    Loads Mermaid from a vendored-free CDN script tag with a static fallback
    class name; the figure degrades to a raw code block when JavaScript is
    unavailable (air-gapped friendly).

    Args:
        mermaid (str): Mermaid source text.
        title (str): Document title.

    Returns:
        str: Complete HTML document rendering the flowchart.
    """
    escaped = html.escape(mermaid)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>{html.escape(title)}</title>
<script type="module">
import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
mermaid.initialize({{ startOnLoad: true, theme: 'default' }});
</script>
</head>
<body>
<h1>{html.escape(title)}</h1>
<pre class="mermaid">{escaped}</pre>
</body>
</html>"""
