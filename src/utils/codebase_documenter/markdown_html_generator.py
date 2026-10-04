# -*- coding: utf-8 -*-
"""
Module: markdown_html_generator.py
Project: TALOS v5.25.0
Description:
    Compiles the AST analysis blueprints plus optional LLM-written prose into
    the master codebase documentation artefacts:
    ``docs/CODEBASE_DOCUMENTATION_MASTER.md`` and a fully self-contained
    ``docs/CODEBASE_DOCUMENTATION_MASTER.html``. The HTML embeds its own CSS and
    JavaScript, ships a client-side live search bar, and uses an academic dark
    theme with zero external CDN dependencies (100 percent air-gapped).

    Key design decisions:
    - Deterministic fallback: when no LLM prose is supplied for a module, the
      generator renders a structured section from the AST blueprint alone.
    - Zero third-party runtime: HTML is emitted by string templating only.
    - Strict UTF-8 writes so Greek and non-ASCII identifiers survive intact.

Dependencies:
    - os, json, datetime, html: filesystem and HTML escaping.
    - typing: type annotations.
"""

import html
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

_P = os.path.abspath(os.path.dirname(__file__))
while _P and not os.path.exists(os.path.join(_P, "talos.py")):
    _P = os.path.dirname(_P)

_DEFAULT_OUTPUT_DIR = os.path.join(
    _P or os.path.abspath(os.path.dirname(__file__)), "docs"
)


class CodebaseDocGenerator:
    """Compile codebase blueprints into Markdown and standalone HTML.

    Attributes:
        output_dir (str): Directory that receives the generated artefacts.
        version (str): Version string stamped into the documents.
    """

    def __init__(
        self, output_dir: Optional[str] = None, version: str = "5.25.0"
    ) -> None:
        self.output_dir = output_dir or _DEFAULT_OUTPUT_DIR
        self.version = version

    # ------------------------------------------------------------------
    # -- Public API -----------------------------------------------------
    # ------------------------------------------------------------------

    def generate(
        self,
        records: List[Dict[str, Any]],
        llm_contents: Optional[Dict[str, str]] = None,
        graph: Optional[Dict[str, List[str]]] = None,
    ) -> Dict[str, str]:
        """Generate the master Markdown and standalone HTML documents.

        Args:
            records (list[dict]): Serializable per-module blueprints.
            llm_contents (Optional[dict]): Module path to LLM-written prose.
            graph (Optional[dict]): Module path to dependency paths.

        Returns:
            dict: ``{"markdown": path, "html": path, "modules": count}``.
        """
        llm_contents = llm_contents or {}
        graph = graph or {}
        os.makedirs(self.output_dir, exist_ok=True)

        markdown_text = self._build_markdown(records, llm_contents, graph)
        html_text = self._build_html(records, llm_contents, graph)

        md_path = os.path.join(self.output_dir, "CODEBASE_DOCUMENTATION_MASTER.md")
        html_path = os.path.join(self.output_dir, "CODEBASE_DOCUMENTATION_MASTER.html")

        with open(md_path, "w", encoding="utf-8") as fh:
            fh.write(markdown_text)
        with open(html_path, "w", encoding="utf-8") as fh:
            fh.write(html_text)

        return {
            "markdown": md_path,
            "html": html_path,
            "modules": len(records),
        }

    # ------------------------------------------------------------------
    # -- Markdown ---------------------------------------------------------
    # ------------------------------------------------------------------

    def _build_markdown(
        self,
        records: List[Dict[str, Any]],
        llm_contents: Dict[str, str],
        graph: Dict[str, List[str]],
    ) -> str:
        stats = self._stats(records, graph)
        lines = [
            "# TALOS Codebase Documentation Master",
            "",
            "| Attribute | Value |",
            "| --- | --- |",
            "| Version | {} |".format(self.version),
            "| Generated | {} |".format(_iso_now()),
            "| Modules documented | {} |".format(stats["modules"]),
            "| Classes | {} |".format(stats["classes"]),
            "| Functions | {} |".format(stats["functions"]),
            "| Dependency edges | {} |".format(stats["edges"]),
            "",
            "## Table of Contents",
            "",
        ]
        for record in records:
            path = record.get("path", "")
            lines.append("- [{}](#{})".format(path, _anchor(path)))

        lines += ["", "---", ""]
        for record in records:
            lines += self._markdown_section(record, llm_contents, graph)
        return "\n".join(lines) + "\n"

    def _markdown_section(
        self,
        record: Dict[str, Any],
        llm_contents: Dict[str, str],
        graph: Dict[str, List[str]],
    ) -> List[str]:
        path = record.get("path", "")
        lines = ["## Module: {}".format(path), ""]
        summary = record.get("docstring") or "(no module docstring)"
        lines.append("**Summary:** {}".format(summary.strip().splitlines()[0]))
        lines.append("")

        prose = llm_contents.get(path)
        if prose:
            lines.append(prose.strip())
            lines.append("")

        classes = record.get("classes", [])
        if classes:
            lines.append("### Classes")
            lines.append("")
            for cls in classes:
                lines.append(
                    "- `{}` (line {})".format(cls.get("name"), cls.get("line_number"))
                )
                if cls.get("docstring"):
                    lines.append("  - {}".format(cls["docstring"]))
                for method in cls.get("methods", []):
                    lines.append(
                        "  - `{}({})` (line {})".format(
                            method.get("name"),
                            method.get("args"),
                            method.get("line_number"),
                        )
                    )
            lines.append("")

        functions = record.get("functions", [])
        if functions:
            lines.append("### Functions")
            lines.append("")
            for func in functions:
                lines.append(
                    "- `{}({})` (line {})".format(
                        func.get("name"), func.get("args"), func.get("line_number")
                    )
                )
            lines.append("")

        deps = graph.get(path, [])
        if deps:
            lines.append("### Dependencies")
            lines.append("")
            for dep in deps:
                lines.append("- {}".format(dep))
            lines.append("")

        lines.append("---")
        lines.append("")
        return lines

    @staticmethod
    def _stats(
        records: List[Dict[str, Any]], graph: Dict[str, List[str]]
    ) -> Dict[str, int]:
        classes = sum(len(r.get("classes", [])) for r in records)
        functions = sum(len(r.get("functions", [])) for r in records)
        edges = sum(len(v) for v in graph.values())
        return {
            "modules": len(records),
            "classes": classes,
            "functions": functions,
            "edges": edges,
        }

    # ------------------------------------------------------------------
    # -- Standalone HTML ---------------------------------------------------
    # ------------------------------------------------------------------

    def _build_html(
        self,
        records: List[Dict[str, Any]],
        llm_contents: Dict[str, str],
        graph: Dict[str, List[str]],
    ) -> str:
        stats = self._stats(records, graph)
        cards = "\n".join(
            self._render_module_card(r, llm_contents, graph) for r in records
        )
        body = (
            '<header class="hero"><h1>TALOS Codebase Documentation Master</h1>'
            '<p class="meta">Version {} &middot; Generated {} &middot; '
            '{} modules &middot; {} classes &middot; {} functions &middot; '
            '{} dependency edges</p></header>'
        ).format(
            self.version,
            _iso_now(),
            stats["modules"],
            stats["classes"],
            stats["functions"],
            stats["edges"],
        )
        return _html_page(body + cards)

    def _render_module_card(
        self,
        record: Dict[str, Any],
        llm_contents: Dict[str, str],
        graph: Dict[str, List[str]],
    ) -> str:
        path = record.get("path", "")
        summary = _escape(
            (record.get("docstring") or "(no module docstring)")
            .strip()
            .splitlines()[0]
        )
        parts = ['<section class="card" data-search="{}">'.format(_escape(path))]
        parts.append("<h2>{}</h2>".format(_escape(path)))
        parts.append('<p class="summary">{}</p>'.format(summary))

        prose = llm_contents.get(path)
        if prose:
            parts.append(
                '<div class="prose">{}</div>'.format(_escape(prose.strip()))
            )

        classes = record.get("classes", [])
        if classes:
            parts.append("<h3>Classes</h3><ul>")
            for cls in classes:
                label = _escape(cls.get("name", ""))
                parts.append('<li><code>{}</code> (line {})'.format(
                    label, cls.get("line_number")
                ))
                if cls.get("docstring"):
                    parts.append(" &mdash; {}".format(_escape(cls["docstring"])))
                for method in cls.get("methods", []):
                    parts.append(
                        '<ul><li><code>{}({})</code> (line {})</li></ul>'.format(
                            _escape(method.get("name", "")),
                            _escape(method.get("args", "")),
                            method.get("line_number"),
                        )
                    )
                parts.append("</li>")
            parts.append("</ul>")

        functions = record.get("functions", [])
        if functions:
            parts.append("<h3>Functions</h3><ul>")
            for func in functions:
                parts.append(
                    "<li><code>{}({})</code> (line {})</li>".format(
                        _escape(func.get("name", "")),
                        _escape(func.get("args", "")),
                        func.get("line_number"),
                    )
                )
            parts.append("</ul>")

        deps = graph.get(path, [])
        if deps:
            parts.append("<h3>Dependencies</h3><ul>")
            for dep in deps:
                parts.append("<li>{}</li>".format(_escape(dep)))
            parts.append("</ul>")

        parts.append("</section>")
        return "\n".join(parts)


def _html_page(body: str) -> str:
    """Wrap rendered body content in a self-contained dark-theme HTML page.

    The page embeds its own CSS and JavaScript (live search filter) and loads
    zero external resources, satisfying the 100 percent air-gapped requirement.

    Args:
        body (str): The rendered hero header and module cards.

    Returns:
        str: A complete standalone HTML document.
    """
    return """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>TALOS Codebase Documentation Master</title>
<style>
:root {
  --bg: #0d1117;
  --panel: #161b22;
  --border: #30363d;
  --text: #e6edf3;
  --muted: #8b949e;
  --accent: #58a6ff;
  --code: #f0883e;
}
* { box-sizing: border-box; }
body {
  margin: 0; background: var(--bg); color: var(--text);
  font-family: -apple-system, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  line-height: 1.55;
}
.hero { padding: 2rem 1.5rem 1.5rem; border-bottom: 1px solid var(--border); }
.hero h1 { margin: 0 0 .5rem; font-size: 1.8rem; color: var(--accent); }
.hero .meta { margin: 0; color: var(--muted); font-size: .9rem; }
.searchbar {
  position: sticky; top: 0; padding: 1rem 1.5rem;
  background: var(--bg); border-bottom: 1px solid var(--border);
}
.searchbar input {
  width: 100%; padding: .65rem .9rem; border-radius: 6px;
  border: 1px solid var(--border); background: var(--panel);
  color: var(--text); font-size: 1rem;
}
.card {
  margin: 1.25rem 1.5rem; padding: 1.25rem 1.5rem;
  background: var(--panel); border: 1px solid var(--border);
  border-radius: 8px;
}
.card h2 { margin: 0 0 .35rem; font-size: 1.15rem; color: var(--accent); }
.card h3 { margin: 1rem 0 .4rem; font-size: .95rem; color: var(--muted); }
.card ul { margin: .2rem 0; padding-left: 1.4rem; }
.card .summary { color: var(--muted); margin: 0; }
.card .prose { margin-top: .8rem; white-space: pre-wrap; }
code { color: var(--code); font-family: "SFMono-Regular", Consolas, monospace; }
.hidden { display: none; }
</style>
</head>
<body>
<div class="searchbar">
  <input id="search" type="search" placeholder="Search modules, classes, or functions...">
</div>
<div id="content">
""" + body + """
</div>
<script>
(function () {
  var input = document.getElementById("search");
  var cards = Array.prototype.slice.call(document.querySelectorAll(".card"));
  input.addEventListener("input", function () {
    var q = input.value.trim().toLowerCase();
    cards.forEach(function (card) {
      var hay = card.getAttribute("data-search") + " " + card.textContent;
      card.classList.toggle("hidden", q !== "" && hay.toLowerCase().indexOf(q) === -1);
    });
  });
})();
</script>
</body>
</html>
"""


def _iso_now() -> str:
    """Return the current UTC wall-clock time as an ISO 8601 string."""
    return datetime.now(timezone.utc).astimezone().isoformat()


def _anchor(path: str) -> str:
    """Derive a Markdown anchor from a module path.

    Args:
        path (str): Project-relative module path.

    Returns:
        str: Lower-cased, space-normalized anchor.
    """
    return path.lower().replace("/", "-").replace("_", "-").replace(".", "-")


def _escape(text: str) -> str:
    """Escape text for safe inclusion in HTML.

    Args:
        text (str): The raw text to escape.

    Returns:
        str: HTML-escaped text.
    """
    return html.escape(str(text), quote=False)



