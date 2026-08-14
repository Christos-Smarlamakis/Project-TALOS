# -*- coding: utf-8 -*-
"""
Module: verify_dependency_map.py (v1.0)
Project: TALOS v5.9.15
Description:
    AST-based dependency verification tool. Compares the documented
    dependency graph in PROJECT_MAP.md (Section 7) against actual
    Python imports found in the source code.

    Outputs:
    1. Console report (colored summary)
    2. data/reports/audits/dependency_audit.json (machine-readable for CI/CD)
    3. data/reports/audits/dependency_audit.html (colored HTML table)
    4. Exit code 0 if all documented imports exist, 1 otherwise

    Usage:
        python src/utils/verify_dependency_map.py           # verbose report
        python src/utils/verify_dependency_map.py --json    # JSON only
        python src/utils/verify_dependency_map.py --html    # HTML report
        python src/utils/verify_dependency_map.py --ci      # quiet, exit code only
"""
import os
import re
import ast
import sys
import json
from pathlib import Path
from datetime import datetime
from collections import defaultdict

# ── Configuration ────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
PROJECT_MAP = PROJECT_ROOT / "docs" / "PROJECT_MAP.md"
REPORTS_DIR = PROJECT_ROOT / "data" / "reports" / "audits"
SRC_DIR = PROJECT_ROOT / "src"

# Files to skip (not part of the dependency graph)
SKIP_FILES = {
    "__init__.py",
    "_bump.py", "_fix_ai.py", "_fix_now.py", "_fix2.py", "_fix3.py", "_fix4.py",
    "_git_status.ps1",
    "test_smoke.py",
}

# Mapping from import paths to documented names
IMPORT_TO_DOC_MAP = {
    # core modules
    "src.core.database_manager": "src.core.database_manager.DatabaseManager",
    "src.core.ai_manager": "src.core.ai_manager.AIManager",
    "src.core.hardware": "src.core.hardware",
    "src.core.profile_manager": "src.core.profile_manager",
    "src.core.notifier": "src.core.notifier",
    # utils
    "src.utils.api_health_check": "src.utils.api_health_check.run_diagnostics",
    # ingestion sources
    "src.ingestion.semantic_scholar_source": "src.ingestion.semantic_scholar_source.SemanticScholarSource",
    "src.ingestion.arxiv_source": "src.ingestion.*",
    "src.ingestion.elsevier_source": "src.ingestion.*",
    "src.ingestion.ieee_source": "src.ingestion.*",
    "src.ingestion.springer_source": "src.ingestion.*",
    "src.ingestion.openalex_source": "src.ingestion.*",
    "src.ingestion.dblp_source": "src.ingestion.*",
    "src.ingestion.core_source": "src.ingestion.*",
    "src.ingestion.crossref_source": "src.ingestion.*",
    "src.ingestion.openarchives_source": "src.ingestion.*",
    "src.ingestion.pubmed_source": "src.ingestion.*",
    "src.ingestion.scigov_source": "src.ingestion.*",
    "src.ingestion.osti_source": "src.ingestion.*",
    "src.ingestion.plos_source": "src.ingestion.*",
    # external libraries
    "sklearn": "sklearn",
    "sklearn.cluster": "sklearn",
    "sklearn.feature_extraction.text": "sklearn",
    "pyvis.network": "pyvis.network.Network",
    "sqlite3": "sqlite3",
    "python-docx": "python-docx",  # docx on import
    "docx": "python-docx",
    "google.genai": "google.genai",
    "requests": "requests",
    "shutil": "shutil",
    "flask": "Flask",
    "Flask": "Flask",
    "tabulator": "Tabulator.js",
}

# ── Known third-party packages ────────────────────────────────────────────────
# These are external libraries used by TALOS. They are NOT project dependencies
# that need to be in the dependency graph (Section 7 tracks TALOS file-to-file
# relationships, not library imports).
EXTERNAL_PACKAGES = {
    # HTTP / API clients and network protocols
    "requests", "httpx", "urllib", "urllib.request", "socket", "smtplib", "email",
    # TALOS runtime dependencies (third-party)
    "dotenv", "tqdm", "questionary", "rich", "tabulate", "jinja2",
    "numpy", "pandas", "streamlit", "matplotlib", "seaborn", "wordcloud",
    "flask", "Flask", "pymed", "pyzotero", "elsapy", "pyvis",
    "sklearn", "sqlite3", "python-docx", "docx",
    "google", "google.generativeai", "google.genai", "google.genai.types",
    "duckduckgo_search", "ddgs", "openai", "networkx", "pickle",
    "fastapi", "uvicorn", "pydantic", "mcp",
    "arxiv", "semanticscholar", "tree_sitter", "rapidfuzz",
    "plotly", "dash", "psutil",
    "gymnasium", "torch", "pytest",
    # standard library
    "concurrent", "concurrent.futures", "logging", "warnings",
    "xml", "subprocess", "ast", "pathlib",
    "re", "typing", "collections", "datetime", "time", "os", "sys", "json",
    "io", "base64", "threading", "signal", "random", "platform",
    "stat", "tempfile", "shutil", "pickle",
    "argparse", "gc", "traceback", "uuid", "webbrowser",
    "math", "functools", "itertools", "contextlib", "enum",
    "dataclasses", "decimal", "fractions", "hashlib", "fnmatch",
    "glob", "inspect", "copy", "textwrap", "abc", "importlib", "pprint",
}

# ── Internal DDD packages ──────────────────────────────────────────────────────
# TALOS's own packages, documented at the package level in the map's module
# inventory (Section 2). Their child imports are not flagged as missing/stale.
INTERNAL_PACKAGES = {
    "src", "config", "talos", "vendor",
}

# ── Parent modules that, when documented, cover all child imports ─────────────
# If "src.core.hardware" is documented, then "src.core.hardware.detect_vram_gb"
# etc. are automatically covered.
COVERED_BY_PARENT = {
    # core submodules covered by parent doc
    "src.core.database_manager": "src.core.database_manager.DatabaseManager",
    "src.core.ai_manager": "src.core.ai_manager.AIManager",
    "src.core.hardware": "src.core.hardware",
    # ingestion sources covered by wildcard doc
    "src.ingestion": "src.ingestion.*",
    # flask submodules covered by "Flask" doc
    "flask": "Flask",
}


def parse_section_7(map_path):
    """Parse Section 7 (Dependency Graph) from PROJECT_MAP.md.

    Returns:
        dict: {filename: [documented_dependency, ...]}
    """
    if not map_path.exists():
        print(f"ERROR: {map_path} not found.")
        return {}

    with open(map_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Extract Section 7 content (between "## 7." and "## 8.")
    section_match = re.search(
        r"## 7\.\s*Dependency Graph.*?\n```\n(.*?)\n```",
        content, re.DOTALL
    )
    if not section_match:
        # Try alternative: just the code block after ## 7.
        section_match = re.search(
            r"## 7\.\s*Dependency Graph.*?\n\n```\n(.*?)\n```",
            content, re.DOTALL
        )
    if not section_match:
        print("WARNING: Could not extract Section 7 from PROJECT_MAP.md")
        return {}

    section_text = section_match.group(1)

    # Parse the tree structure
    # Format:
    #   filename
    #     ├── dependency
    #     └── subprocess → scripts/*.py
    documented = {}
    current_file = None

    for line in section_text.splitlines():
        line = line.strip()
        if not line:
            current_file = None
            continue

        # Check if this is a filename (no tree prefix)
        if not line.startswith(("├──", "└──", "│", " ")):
            # This is a filename at root level
            name = line
            # Remove trailing parenthetical notes like "(CHIRON)", "(ORPHEUS)", etc.
            name = re.sub(r'\s*\(.*?\)\s*$', '', name)
            # Handle combined entries like "daily_search.py / historic_search.py"
            if " / " in name:
                names = [n.strip() for n in name.split(" / ")]
                # Add dependencies to the first one, ignore the second for now
                current_file = names[0].strip()
            else:
                current_file = name.strip()
            documented[current_file] = []
            continue

        # This is a dependency line
        dep_line = line.lstrip("│ ├└───→ ")
        dep_line = re.sub(r'\s*\(.*?\)\s*', '', dep_line).strip()

        if current_file and dep_line:
            documented[current_file].append(dep_line)

    return documented


def extract_actual_imports(py_file, project_root):
    """Use AST to extract all imports from a Python file.

    Args:
        py_file (Path): Path to the .py file.
        project_root (Path): Project root for relative path calculation.

    Returns:
        list: List of documented-style dependency strings.
    """
    if not py_file.exists():
        return []

    try:
        with open(py_file, "r", encoding="utf-8") as f:
            source = f.read()
        tree = ast.parse(source, filename=str(py_file))
    except (SyntaxError, UnicodeDecodeError) as e:
        return [f"!SYNTAX_ERROR: {e}"]

    imports = []
    rel_path = str(py_file.relative_to(project_root)).replace("\\", "/")

    for node in ast.walk(tree):
        # import X
        if isinstance(node, ast.Import):
            for alias in node.names:
                module = alias.name
                doc_name = IMPORT_TO_DOC_MAP.get(module, module)
                imports.append(doc_name)

        # from X import Y
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                module = node.module
                for alias in node.names:
                    full = f"{module}.{alias.name}"
                    doc_name = IMPORT_TO_DOC_MAP.get(full, full)
                    # Also try the base module
                    base_doc = IMPORT_TO_DOC_MAP.get(module, module)
                    imports.append(doc_name)
                    if base_doc != doc_name:
                        imports.append(base_doc)

    # Also detect subprocess calls to other scripts
    try:
        subprocess_pattern = re.findall(
            r'subprocess\.run\s*\(\s*\[.*?[\'"]((?:src|scripts|core|sources)[^\'"]+\.py)[\'"]',
            source
        )
        for s in subprocess_pattern:
            name = s.replace("\\", "/").replace(".py", ".py")
            imports.append(f"subprocess → {name}")

        # Also detect _gui_runner wrapper calls from app.py
        run_pattern = re.findall(
            r'run\s*\(\s*[\'"]([^\'"]+\.py)[\'"]',
            source
        )
        for rp in run_pattern:
            imports.append(f"subprocess → scripts/{rp}")
    except Exception:
        pass

    return list(set(imports))  # deduplicate


def scan_all_files(project_root):
    """Scan all .py files in src/ and the project root and extract imports.

    Returns:
        dict: {basename: [actual_dependency, ...]}
    """
    actual = {}

    # Scan the DDD src/ package tree (core, ingestion, ai, analysis, utils, api)
    for py_file in sorted(SRC_DIR.rglob("*.py")):
        if py_file.name in SKIP_FILES or py_file.name == "__init__.py":
            continue
        rel = py_file.relative_to(project_root).as_posix()
        actual[rel] = extract_actual_imports(py_file, project_root)

    # Scan root .py files (talos.py)
    for py_file in sorted(project_root.glob("*.py")):
        fname = py_file.name
        if fname.startswith("_") or fname in SKIP_FILES:
            continue
        actual[fname] = extract_actual_imports(py_file, project_root)

    return actual


def normalize_dep(dep):
    """Normalize a dependency string for comparison."""
    dep = dep.strip()
    # Remove comments in parentheses
    dep = re.sub(r'\s*\(.*?\)\s*', '', dep)
    # Normalize subprocess entries
    dep = dep.replace("//", "/")
    # Handle wildcard entries
    dep = dep.replace("sources.*", "sources.*")
    return dep


def compare_dependencies(documented, actual):
    """Compare documented vs actual dependencies.

    Returns:
        list of dict: Each dict has {file, dependency, status, documented, actual}
    """
    results = []
    all_files = sorted(set(list(documented.keys()) + list(actual.keys())))

    for fname in all_files:
        doc_deps = {normalize_dep(d) for d in documented.get(fname, [])}
        act_deps = {normalize_dep(d) for d in actual.get(fname, [])}

        # Expand wildcard matches
        # sources.* matches any source import
        if "sources.*" in doc_deps:
            doc_deps.remove("sources.*")
            for act in list(act_deps):
                if act.startswith("sources.") and not act.startswith("sources.*"):
                    doc_deps.add(act)

        # Handle special case: daily_search.py is the canonical import for all sources
        # If any source dependency is documented for daily_search.py, count all source imports

        matched = doc_deps & act_deps
        stale = doc_deps - act_deps  # documented but not in actual code
        missing = act_deps - doc_deps  # in actual code but not documented

        for dep in sorted(matched):
            results.append({
                "file": fname,
                "dependency": dep,
                "status": "matched",
                "detail": ""
            })

        for dep in sorted(stale):
            # Skip internal DDD packages (covered at package level), external
            # libraries, subprocess entries, and non-import annotations.
            parts = dep.split(".")
            if parts[0] in INTERNAL_PACKAGES or parts[0] in EXTERNAL_PACKAGES:
                continue
            if dep.startswith("subprocess") or "/" in dep or "→" in dep:
                continue
            results.append({
                "file": fname,
                "dependency": dep,
                "status": "stale",
                "detail": "Documented but NOT found in actual code"
            })

        for dep in sorted(missing):
            # ── Filter 1: Skip external / standard library packages ──
            parts = dep.split(".")
            if parts[0] in EXTERNAL_PACKAGES:
                continue  # third-party library, not a TALOS file dependency

            # ── Filter 5 (v5.9.15): Skip internal DDD packages ──
            # TALOS's own packages are documented at the package level in the
            # map's module inventory (Section 2), not per-import in Section 7.
            if parts[0] in INTERNAL_PACKAGES:
                continue

            # ── Filter 2: Skip submodule paths whose parent is already documented ──
            # e.g. "core.hardware.detect_vram_gb" is covered if "core.hardware" is in doc_deps
            if len(parts) >= 2:
                parent = ".".join(parts[:2])  # e.g. "core.hardware"
                if parent in COVERED_BY_PARENT and COVERED_BY_PARENT[parent] in doc_deps:
                    continue
                # Also check if the grandparent is covered (e.g. "sources.elsevier_source.ElsClient")
                if len(parts) >= 3:
                    parent2 = ".".join(parts[:2])
                    if parent2 in COVERED_BY_PARENT and COVERED_BY_PARENT[parent2] in doc_deps:
                        continue

            # ── Filter 3: Deep sub-paths of third-party libs (docx.enum.text.WD_ALIGN_PARAGRAPH) ──
            if dep.count(".") > 2 and parts[0] not in ("core", "scripts", "sources"):
                continue

            # ── Filter 4: Syntax errors and internal noise ──
            if any(skip in dep.lower() for skip in ["!syntax", "__init__"]):
                continue
            if dep.startswith("subprocess"):
                continue

            results.append({
                "file": fname,
                "dependency": dep,
                "status": "missing",
                "detail": "Found in actual code but NOT documented"
            })

    return results


# ═══════════════════════════════════════════════════════════════════════════════
#  REPORT GENERATION (Console, HTML, Markdown, JSON)
# ═══════════════════════════════════════════════════════════════════════════════

AUDIT_INTRO_TEXT = """PROJECT_MAP.md is the master blueprint of TALOS — it documents
every file, its functions, and how files connect to each other.

This tool reads the actual Python source code and compares it
against what PROJECT_MAP.md claims. It detects three conditions:

  MATCHED   — The documentation matches the code. Correct.

  STALE     — Documented in the map but NOT found in the code.
              The map is outdated. These entries must be
              reviewed and either corrected or removed.

  MISSING   — Found in the code but NOT documented in the map.
              Code was added or changed but the map was not
              updated. These should be added to PROJECT_MAP.md."""

HOW_TO_FIX_TEXT = """1. Open PROJECT_MAP.md
2. For STALE items: Find the listed file's section and fix or
   remove the dependency/function entry.
3. For MISSING items: Add the new dependency/function to the
   appropriate file's section.
4. Re-run this tool to confirm the fixes."""


def generate_console_summary(results, label="Dependency Audit"):
    """Print a minimal console summary."""
    matched = len([r for r in results if r["status"] == "matched"])
    stale = len([r for r in results if r["status"] == "stale"])
    missing = len([r for r in results if r["status"] == "missing"])
    print(f"    {label}: {matched} matched, {stale} stale, {missing} missing")
    return stale + missing


def generate_html_report(results, output_path, title="Dependency Map Audit"):
    """Generate a complete HTML report with intro, summary, details, and how-to-fix."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    matched = len([r for r in results if r["status"] == "matched"])
    stale = len([r for r in results if r["status"] == "stale"])
    missing_count = len([r for r in results if r["status"] == "missing"])
    is_accurate = stale == 0 and missing_count == 0

    stale_list = [r for r in results if r["status"] == "stale"]
    missing_list = [r for r in results if r["status"] == "missing"]

    # Build stale rows
    stale_rows = ""
    for r in sorted(stale_list, key=lambda x: x["file"]):
        stale_rows += f"<tr class='status-stale'><td>STALE</td><td>{r['file']}</td><td>{r['dependency']}</td><td>{r.get('detail','')}</td></tr>"
    if not stale_rows:
        stale_rows = "<tr><td colspan='4' style='color:#2ecc71;text-align:center;'>No stale entries.</td></tr>"

    # Build missing rows
    missing_rows = ""
    for r in sorted(missing_list, key=lambda x: x["file"]):
        missing_rows += f"<tr class='status-missing'><td>MISSING</td><td>{r['file']}</td><td>{r['dependency']}</td><td>{r.get('detail','')}</td></tr>"
    if not missing_rows:
        missing_rows = "<tr><td colspan='4' style='color:#2ecc71;text-align:center;'>No missing entries.</td></tr>"

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>TALOS {title} — {datetime.now().strftime('%Y-%m-%d %H:%M')}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background: #0d1117; color: #c9d1d9; padding: 30px; max-width: 1100px; margin: auto;
        }}
        h1 {{ color: #e94560; margin-bottom: 5px; }}
        .subtitle {{ color: #8b949e; font-size: 0.85rem; margin-bottom: 20px; }}
        .intro-box {{
            background: #161b22; border: 1px solid #30363d; border-radius: 8px;
            padding: 20px; margin: 20px 0; line-height: 1.6; font-size: 0.9rem;
        }}
        .intro-box h2 {{ color: #e94560; font-size: 1rem; margin-bottom: 10px; }}
        .summary {{ display: flex; gap: 15px; margin: 20px 0; }}
        .summary-card {{
            background: #161b22; border: 1px solid #30363d; border-radius: 8px;
            padding: 16px 24px; text-align: center; flex: 1; min-width: 120px;
        }}
        .summary-card .count {{ font-size: 2rem; font-weight: bold; }}
        .summary-card .label {{ font-size: 0.8rem; color: #8b949e; }}
        .card-ok .count {{ color: #2ecc71; }} .card-stale .count {{ color: #e74c3c; }} .card-missing .count {{ color: #f39c12; }}
        .verdict {{
            padding: 16px; border-radius: 8px; margin: 20px 0; font-size: 1.1rem; text-align: center;
        }}
        .verdict.pass {{ background: #0d3320; border: 1px solid #2ecc71; color: #2ecc71; }}
        .verdict.fail {{ background: #3d1414; border: 1px solid #e74c3c; color: #e74c3c; }}
        .section-title {{ color: #e94560; font-size: 1rem; margin: 25px 0 10px 0; border-bottom: 1px solid #30363d; padding-bottom: 6px; }}
        table {{ width: 100%; border-collapse: collapse; margin: 10px 0; }}
        th {{ background: #161b22; padding: 10px; text-align: left; border-bottom: 2px solid #30363d; font-size: 0.85rem; }}
        td {{ padding: 8px 10px; border-bottom: 1px solid #21262d; font-size: 0.85rem; }}
        tr:hover {{ background: #161b22; }}
        .status-stale {{ border-left: 3px solid #e74c3c; background: rgba(231,76,60,0.06); }}
        .status-missing {{ border-left: 3px solid #f39c12; background: rgba(243,156,18,0.06); }}
        .how-to-fix {{
            background: #161b22; border: 1px solid #30363d; border-radius: 8px;
            padding: 20px; margin: 25px 0; line-height: 1.8; font-size: 0.9rem;
        }}
        .how-to-fix h2 {{ color: #e94560; font-size: 1rem; margin-bottom: 8px; }}
        .how-to-fix ol {{ padding-left: 20px; }}
        .how-to-fix li {{ margin: 4px 0; }}
        .footer {{ margin-top: 30px; color: #8b949e; font-size: 0.75rem; text-align: center; }}
    </style>
</head>
<body>
    <h1>🧠 TALOS {title}</h1>
    <p class="subtitle">Documented (PROJECT_MAP.md) vs Actual (AST Analysis of source code) · Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>

    <div class="verdict {'pass' if is_accurate else 'fail'}">
        {'✅ ALL CHECKS PASSED — Map is 100% accurate!' if is_accurate else '⚠️ DISCREPANCIES FOUND — Map needs updates.'}
    </div>

    <div class="summary">
        <div class="summary-card card-ok"><div class="count">{matched}</div><div class="label">Matched</div></div>
        <div class="summary-card card-stale"><div class="count">{stale}</div><div class="label">Stale (doc but not code)</div></div>
        <div class="summary-card card-missing"><div class="count">{missing_count}</div><div class="label">Missing (code but not doc)</div></div>
    </div>

    <div class="intro-box">
        <h2>What This Tool Does</h2>
        <p>{AUDIT_INTRO_TEXT.replace(chr(10), '<br>')}</p>
    </div>

    <h2 class="section-title">Stale Entries ({stale}) — Documented but NOT in actual code</h2>
    <table><thead><tr><th>Status</th><th>File</th><th>Dependency / Function</th><th>Detail</th></tr></thead><tbody>{stale_rows}</tbody></table>

    <h2 class="section-title">Missing Entries ({missing_count}) — In actual code but NOT documented</h2>
    <table><thead><tr><th>Status</th><th>File</th><th>Dependency / Function</th><th>Detail</th></tr></thead><tbody>{missing_rows}</tbody></table>

    <div class="how-to-fix">
        <h2>How to Fix</h2>
        <ol>{''.join(f'<li>{line}</li>' for line in HOW_TO_FIX_TEXT.splitlines() if line.strip())}</ol>
    </div>

    <div class="footer">Generated by scripts/verify_dependency_map.py — TALOS v5.0.0</div>
</body>
</html>"""

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    return output_path


def generate_markdown_report(results, output_path, title="Dependency Map Audit"):
    """Generate a complete Markdown report."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    matched = len([r for r in results if r["status"] == "matched"])
    stale = len([r for r in results if r["status"] == "stale"])
    missing_count = len([r for r in results if r["status"] == "missing"])
    is_accurate = stale == 0 and missing_count == 0

    stale_list = [r for r in results if r["status"] == "stale"]
    missing_list = [r for r in results if r["status"] == "missing"]

    lines = [
        f"# TALOS {title}",
        f"_Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}_",
        "",
        f"## Results",
        f"- **Matched:** {matched}",
        f"- **Stale (doc but not code):** {stale}",
        f"- **Missing (code but not doc):** {missing_count}",
        "",
        f"## Verdict",
        f"{'✅ ALL CHECKS PASSED — Map is 100% accurate!' if is_accurate else '⚠️ DISCREPANCIES FOUND — Map needs updates.'}",
        "",
        "---",
        "",
        "## What This Tool Does",
        "",
    ]
    for line in AUDIT_INTRO_TEXT.splitlines():
        if line.strip():
            lines.append(line.strip())
    lines.append("")

    if stale_list:
        lines.append(f"## Stale Entries ({stale}) — Documented but NOT in actual code")
        lines.append("")
        for r in sorted(stale_list, key=lambda x: x["file"]):
            lines.append(f"- `{r['file']}` → **{r['dependency']}**")
        lines.append("")

    if missing_list:
        lines.append(f"## Missing Entries ({missing_count}) — In actual code but NOT documented")
        lines.append("")
        for r in sorted(missing_list, key=lambda x: x["file"]):
            lines.append(f"- `{r['file']}` → **{r['dependency']}**")
        lines.append("")

    lines.append("## How to Fix")
    lines.append("")
    for line in HOW_TO_FIX_TEXT.splitlines():
        if line.strip():
            lines.append(line.strip())
    lines.append("")
    lines.append("---")
    lines.append(f"_Generated by scripts/verify_dependency_map.py — TALOS v5.0.0_")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    return output_path


def generate_json_report(results, output_path):
    """Generate a JSON report for CI/CD consumption."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    summary = {
        "generated_at": datetime.now().isoformat(),
        "project_version": "v5.0.0",
        "total_checks": len(results),
        "matched": len([r for r in results if r["status"] == "matched"]),
        "stale": len([r for r in results if r["status"] == "stale"]),
        "missing": len([r for r in results if r["status"] == "missing"]),
        "is_accurate": all(r["status"] == "matched" for r in results),
        "results": results,
    }
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    return output_path


# ═══════════════════════════════════════════════════════════════════════════════
#  FUNCTION DOCUMENTATION AUDIT (Sections 2-4 vs AST)
# ═══════════════════════════════════════════════════════════════════════════════

def parse_function_docs(map_path):
    """Parse Sections 2-4 of PROJECT_MAP.md to extract documented functions per file.

    Handles two formats:
    1. Tables (core + entry points): function names in backtick-wrapped cells
    2. Text lists (scripts): **Συναρτήσεις:** or **Κλάση:** followed by function names

    Returns:
        dict: {filepath: [function_names]}
    """
    if not map_path.exists():
        return {}

    with open(map_path, "r", encoding="utf-8") as f:
        content = f.read()

    documented = {}
    current_file = None
    in_section = False  # True when inside Sections 2-4

    for line in content.splitlines():
        # Detect section boundaries
        if line.startswith("## 2.") or line.startswith("## 3.") or line.startswith("## 4."):
            in_section = True
            continue
        if line.startswith("## 5.") or line.startswith("## Sources"):
            in_section = False
            current_file = None
            continue

        if not in_section:
            continue

        # ── Detect file name from headings ──
        # Patterns: "### 2.1 `core/ai_manager.py`", "#### `scripts/daily_search.py`"
        # Or "### 3.1 `talos.py`", "#### `scripts/daily_search.py`"
        heading_match = re.search(r'#{2,4}\s+.*?`([^`]+\.py)`', line)
        if heading_match:
            current_file = heading_match.group(1)
            # Normalize path: strip "scripts/" prefix to match scan_all_functions paths
            if current_file.startswith("scripts/"):
                current_file = current_file.replace("scripts/", "")
            if current_file not in documented:
                documented[current_file] = []
            continue

        if not current_file:
            continue

        # ── Pattern 1: Table row with function name ──
        # | `function_name` | `signature` | Description |
        table_match = re.findall(r'`([a-zA-Z_][\w]*)`\s*\|', line)
        for name in table_match:
            if name not in ("self", "config", "True", "False", "None") and len(name) > 1:
                documented[current_file].append(name)

        # ── Pattern 2: Text list — "**Συναρτήσεις:**" or "**Κλάση:**" ──
        func_list_match = re.search(r'\*\*(?:Συναρτήσεις|Κλάση):\*\*\s*(.*)', line)
        if func_list_match:
            names = re.findall(r'`([^`]+)`', func_list_match.group(1))
            documented[current_file].extend(names)

        # ── Pattern 3: Indented list items ──
        # - `__init__(config)`, `_get_user_goal()`, ...
        list_match = re.match(r'^\s*-\s+`([^`]+)`', line)
        if list_match:
            name = list_match.group(1)
            # Clean up: remove "self, " prefix and everything after "("
            name = re.sub(r'\(.*', '', name)
            name = name.replace("self, ", "").replace("self.", "")
            if name and len(name) > 1:
                documented[current_file].append(name)

    # Normalize: strip parameters and deduplicate
    for fname in documented:
        cleaned = set()
        for name in documented[fname]:
            # Strip everything from first '(' onwards (function parameters)
            name = re.sub(r'\(.*', '', name)
            name = name.strip("()").strip()
            # Skip noise entries
            if not name or len(name) <= 1:
                continue
            if name.startswith("-") or name.startswith("→"):
                continue
            # Skip common non-function words that appear in tables
            if name in ("self", "config", "True", "False", "None", "N/A",
                         "URL", "str", "int", "float", "bool", "list", "dict",
                         "tuple", "Dict", "List", "Any", "Union", "Tuple",
                         "Optional", "or", "and", "not", "in", "is"):
                continue
            # Skip entries that look like file paths or type hints
            if name.startswith("sources.") or name.startswith("core.") or name.startswith("scripts."):
                continue
            if ":" in name or "→" in name:
                continue
            cleaned.add(name)
        documented[fname] = sorted(cleaned)

    return documented


def extract_actual_functions(py_file):
    """Use AST to extract all function and class definitions from a Python file.

    Args:
        py_file (Path): Path to the .py file.

    Returns:
        list: Function/class names defined in the file.
    """
    if not py_file.exists():
        return []

    try:
        with open(py_file, "r", encoding="utf-8") as f:
            source = f.read()
        tree = ast.parse(source, filename=str(py_file))
    except (SyntaxError, UnicodeDecodeError):
        return []

    names = []

    for node in ast.walk(tree):
        # Top-level function definitions
        if isinstance(node, ast.FunctionDef):
            names.append(node.name)
        # Class definitions
        elif isinstance(node, ast.ClassDef):
            names.append(node.name)
            # Also add class methods
            for child in ast.walk(node):
                if isinstance(child, ast.FunctionDef):
                    names.append(child.name)

    return sorted(set(names))


def scan_all_functions(project_root):
    """Scan all .py files and extract actual function/class definitions.

    Returns:
        dict: {filepath: [function_names]}
    """
    actual = {}

    for py_file in sorted(SCRIPTS_DIR.glob("*.py")):
        fname = py_file.name
        if fname in SKIP_FILES or fname == "verify_dependency_map.py":
            continue
        actual[fname] = extract_actual_functions(py_file)

    for py_file in sorted(CORE_DIR.glob("*.py")):
        fname = py_file.name
        if fname in SKIP_FILES:
            continue
        actual[f"core/{fname}"] = extract_actual_functions(py_file)

    for py_file in sorted(project_root.glob("*.py")):
        fname = py_file.name
        if fname.startswith("_") or fname in SKIP_FILES:
            continue
        actual[fname] = extract_actual_functions(py_file)

    return actual


def compare_functions(documented, actual):
    """Compare documented vs actual function/class definitions.

    Returns:
        list of dict: Results with matched/stale/missing status.
    """
    results = []
    all_files = sorted(set(list(documented.keys()) + list(actual.keys())))

    for fname in all_files:
        doc_funcs = set(documented.get(fname, []))
        act_funcs = set(actual.get(fname, []))

        matched = doc_funcs & act_funcs
        stale = doc_funcs - act_funcs
        missing = act_funcs - doc_funcs

        # Filter noise: dunder methods, private helpers that are implied
        noise_patterns = {"__init__", "__str__", "__repr__", "__len__", "__call__",
                          "__getitem__", "__setitem__", "__iter__", "__next__",
                          "__enter__", "__exit__", "__contains__", "__eq__", "__hash__"}

        for dep in sorted(matched):
            results.append({
                "file": fname, "dependency": dep,
                "status": "matched", "detail": ""
            })

        for dep in sorted(stale):
            if dep in noise_patterns:
                continue
            results.append({
                "file": fname, "dependency": dep,
                "status": "stale",
                "detail": "Documented function not found in source code"
            })

        for dep in sorted(missing):
            if dep in noise_patterns:
                continue
            results.append({
                "file": fname, "dependency": dep,
                "status": "missing",
                "detail": "Function exists in code but not documented"
            })

    return results


def main():
    """Main verification workflow."""
    ci_mode = "--ci" in sys.argv
    json_only = "--json" in sys.argv
    html_only = "--html" in sys.argv
    fn_mode = "--functions" in sys.argv
    all_mode = "--all" in sys.argv

    if not ci_mode:
        print("TALOS Dependency Map Verifier v2.0")
        print(f"  PROJECT_MAP.md: {PROJECT_MAP}")
        print()

    has_errors = False

    # ── MODE: Dependencies (default) or --all ──
    if not fn_mode:
        documented = parse_section_7(PROJECT_MAP)
        actual = scan_all_files(PROJECT_ROOT)
        results = compare_dependencies(documented, actual)

        json_path = REPORTS_DIR / "dependency_audit.json"
        html_path = REPORTS_DIR / "dependency_audit.html"
        md_path = REPORTS_DIR / "dependency_audit.md"

        if json_only:
            generate_json_report(results, json_path)
        elif html_only:
            generate_html_report(results, html_path, "Dependency Map Audit")
        else:
            generate_console_summary(results, "Dependency Audit")
            generate_html_report(results, html_path, "Dependency Map Audit")
            generate_markdown_report(results, md_path, "Dependency Map Audit")
            generate_json_report(results, json_path)
            if not ci_mode:
                print(f"    Reports: {html_path.name} | {md_path.name} | {json_path.name}")

        has_errors = any(r["status"] in ("stale", "missing") for r in results)

    # ── MODE: Functions (--functions or --all) ──
    if fn_mode or all_mode:
        doc_funcs = parse_function_docs(PROJECT_MAP)
        act_funcs = scan_all_functions(PROJECT_ROOT)
        fn_results = compare_functions(doc_funcs, act_funcs)

        fn_json = REPORTS_DIR / "function_audit.json"
        fn_html = REPORTS_DIR / "function_audit.html"
        fn_md = REPORTS_DIR / "function_audit.md"

        if json_only:
            generate_json_report(fn_results, fn_json)
        elif html_only:
            generate_html_report(fn_results, fn_html, "Function Documentation Audit")
        else:
            generate_console_summary(fn_results, "Function Audit")
            generate_html_report(fn_results, fn_html, "Function Documentation Audit")
            generate_markdown_report(fn_results, fn_md, "Function Documentation Audit")
            generate_json_report(fn_results, fn_json)
            if not ci_mode:
                print(f"    Reports: {fn_html.name} | {fn_md.name} | {fn_json.name}")

        has_errors = has_errors or any(r["status"] in ("stale", "missing") for r in fn_results)

    if not ci_mode:
        print(f"\n  Done.")

    # Exit code: 0 if all good, 1 if issues found
    if ci_mode:
        sys.exit(1 if has_errors else 0)


if __name__ == "__main__":
    main()
