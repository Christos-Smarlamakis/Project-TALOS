# -*- coding: utf-8 -*-
"""
Module: graphify_adapter.py
Project: TALOS v5.9.17
Description:
    Adapter module that wraps the vendored Graphify AST engine (located at
    vendor/graphify/) for use within the TALOS ecosystem. Provides a single
    public entry point, generate_ast_knowledge_graph(), which invokes
    Graphify as a subprocess via ``python -m graphify extract`` with the
    vendor directory dynamically added to PYTHONPATH. After successful
    extraction, it automatically executes ``graphify cluster-only`` to
    generate GRAPH_REPORT.md and community labels without requiring LLM
    calls (--no-label flag for 100% air-gapped operation). The generated
    ``graphify-out/`` directory is then moved from the target directory to
    ``data/reports/graphify_out/``.

    Key design decisions:
    - Uses subprocess invocation instead of fragile internal API imports --
      Graphify is designed as a CLI tool and its internal Python API is not
      a stable contract.
    - Vendor path is prepended to PYTHONPATH in a copied environment dict so
      the subprocess can resolve ``graphify`` as a package.
    - Graphify outputs to ``graphify-out/`` inside the target directory
      (e.g., ``src/graphify-out/`` when target is ``src/``). The adapter
      resolves the correct source path based on the target directory.
    - Auto-executes ``cluster-only`` after extraction to produce the
      clustering report and community labels without LLM calls.
    - All operations wrapped in try/except for graceful degradation.
    - Uses Rich console for TUI feedback and error panels.
    - Compliant with Section VIII docstring standards.

Dependencies:
    - sys, os, shutil, subprocess, pathlib: Process invocation and filesystem ops.
    - rich.console, rich.panel: TUI output for progress and error messages.
    - vendor/graphify: The vendored AST knowledge graph engine (invoked as subprocess).
"""
import os
import sys
import shutil
import subprocess
from pathlib import Path


def generate_ast_knowledge_graph(target_dir: str = None) -> dict:
    """Run the Graphify AST pipeline against a target directory via subprocess.

    Resolves the absolute path to ``vendor/graphify``, prepends it to
    PYTHONPATH in a copy of the current environment, then invokes::

        python -m graphify extract src/ --code-only

    with ``cwd`` set to the project root. This performs pure-local AST
    extraction (no LLM key required), builds a knowledge graph, runs
    clustering, and writes all artifacts to ``graphify-out/`` in the cwd.
    On success, the ``graphify-out/`` directory is moved to
    ``data/reports/graphify_out/``.

    Args:
        target_dir: Absolute or relative path to the directory to analyze.
                    Defaults to ``src/`` relative to the project root.

    Returns:
        A dict with keys:
            - success (bool): Whether the pipeline completed.
            - output_dir (str): Path to the output directory.
            - files (list[str]): List of generated output files.
            - error (str or None): Error message if success is False.
            - stats (dict or None): Pipeline statistics (node count,
              edge count, file count) if successful.
    """
    from rich.console import Console
    from rich.panel import Panel
    console = Console()

    # -- Resolve project root --
    _p = os.path.abspath(os.path.dirname(__file__))
    while _p and not os.path.exists(os.path.join(_p, 'talos.py')):
        _p = os.path.dirname(_p)
    project_root = _p if _p else os.getcwd()

    if target_dir is None:
        target_dir = os.path.join(project_root, 'src')
    target_dir = os.path.abspath(target_dir)
    if not os.path.isdir(target_dir):
        return {
            'success': False,
            'output_dir': None,
            'files': [],
            'error': f"Target directory does not exist: {target_dir}",
            'stats': None,
        }

    output_dir = os.path.join(project_root, 'data', 'reports', 'graphify_out')

    result = {
        'success': False,
        'output_dir': output_dir,
        'files': [],
        'error': None,
        'stats': None,
    }

    # -- Resolve vendor/graphify absolute path --
    vendor_graphify = os.path.join(project_root, 'vendor', 'graphify')
    if not os.path.isdir(vendor_graphify):
        result['error'] = (
            f"Vendor directory not found at {vendor_graphify}. "
            "Clone the graphify repository into vendor/graphify/."
        )
        console.print(Panel(
            result['error'],
            title="[bold red]Error[/bold red]",
            border_style="red",
        ))
        return result

    # -- Compute target_dir relative to project_root for subprocess arg --
    # Graphify extract accepts a path argument; we use the target dir name.
    try:
        target_rel = os.path.relpath(target_dir, project_root)
    except ValueError:
        # On Windows, relpath can raise ValueError if paths are on different
        # drives. Fall back to the absolute path.
        target_rel = target_dir

    # -- Build environment with vendor/graphify on PYTHONPATH --
    env = os.environ.copy()
    existing_pythonpath = env.get('PYTHONPATH', '')
    if existing_pythonpath:
        env['PYTHONPATH'] = vendor_graphify + os.pathsep + existing_pythonpath
    else:
        env['PYTHONPATH'] = vendor_graphify

    # -- Build the subprocess command --
    # graphify extract <path> --code-only performs AST extraction, builds
    # the graph, runs clustering, and writes outputs to graphify-out/.
    # We explicitly do NOT pass --no-viz so graph.html is generated.
    cmd = [
        sys.executable,
        "-m", "graphify",
        "extract",
        target_rel,
        "--code-only",
    ]

    console.print(
        f"\n[bold bright_cyan]Graphify AST Knowledge Graph Pipeline[/bold bright_cyan]"
    )
    console.print(f"[dim]Target: {target_dir}[/dim]")
    console.print(f"[dim]Output: {output_dir}[/dim]")
    console.print(f"[dim]Command: {' '.join(cmd)}[/dim]\n")

    # -- Execute subprocess --
    console.print("[cyan]Running Graphify extraction...[/cyan]")
    try:
        proc = subprocess.run(
            cmd,
            env=env,
            cwd=project_root,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        result['error'] = (
            f"Python executable not found at {sys.executable}. "
            "Ensure Python is installed and available on PATH."
        )
        console.print(Panel(
            result['error'],
            title="[bold red]Error[/bold red]",
            border_style="red",
        ))
        return result
    except Exception as e:
        result['error'] = f"Unexpected error invoking graphify subprocess: {e}"
        console.print(Panel(
            result['error'],
            title="[bold red]Error[/bold red]",
            border_style="red",
        ))
        return result

    # -- Print subprocess stdout for visibility --
    if proc.stdout:
        for line in proc.stdout.splitlines():
            stripped = line.strip()
            if stripped:
                console.print(f"  [dim]{stripped}[/dim]")

    # -- Handle subprocess failure --
    if proc.returncode != 0:
        error_detail = proc.stderr.strip() if proc.stderr else "(no stderr output)"
        result['error'] = (
            f"Graphify subprocess exited with code {proc.returncode}.\n\n"
            f"STDERR:\n{error_detail}"
        )

        # -- Produce a rich error panel with actionable diagnostics --
        diagnostic_lines = [
            f"[bold]Exit Code:[/bold] {proc.returncode}",
            "",
            "[bold]STDERR Output:[/bold]",
            error_detail if error_detail else "(none)",
        ]

        # -- Check for common failure modes --
        stderr_lower = (proc.stderr or '').lower()
        stdout_lower = (proc.stdout or '').lower()

        if 'tree-sitter' in stderr_lower or 'tree-sitter' in stdout_lower:
            diagnostic_lines.append("")
            diagnostic_lines.append(
                "[bold yellow]Diagnosis:[/bold yellow] The tree-sitter library "
                "or a language grammar is missing. Install it with:"
            )
            diagnostic_lines.append(
                "  [dim]pip install tree-sitter[/dim]"
            )
        elif 'no module named' in stderr_lower:
            diagnostic_lines.append("")
            diagnostic_lines.append(
                "[bold yellow]Diagnosis:[/bold yellow] A required Python module "
                "is missing. Check that all graphify dependencies are installed."
            )
            diagnostic_lines.append(
                "  [dim]pip install -r vendor/graphify/requirements.txt[/dim] "
                "or install via the graphify pyproject.toml"
            )
        elif 'permission' in stderr_lower:
            diagnostic_lines.append("")
            diagnostic_lines.append(
                "[bold yellow]Diagnosis:[/bold yellow] Permission denied. "
                "Check file permissions on the target directory and "
                "graphify-out/."
            )

        console.print(Panel(
            "\n".join(diagnostic_lines),
            title="[bold red]Graphify Subprocess Failed[/bold red]",
            border_style="red",
        ))
        return result

    # -- Execute cluster-only subprocess for report generation --
    # Graphify's extract command produces the graph and clustering data.
    # The cluster-only command generates GRAPH_REPORT.md and names
    # communities. We use --no-label to avoid LLM calls, preserving
    # 100% air-gapped operation.
    console.print("[cyan]Running Graphify cluster-only (report generation)...[/cyan]")
    cluster_cmd = [
        sys.executable,
        "-m", "graphify",
        "cluster-only",
        target_rel,
        "--no-label",
    ]
    try:
        cluster_proc = subprocess.run(
            cluster_cmd,
            env=env,
            cwd=project_root,
            capture_output=True,
            text=True,
        )
    except Exception as e:
        result['error'] = f"Unexpected error invoking graphify cluster-only subprocess: {e}"
        console.print(Panel(
            result['error'],
            title="[bold red]Error[/bold red]",
            border_style="red",
        ))
        return result

    if cluster_proc.stdout:
        for line in cluster_proc.stdout.splitlines():
            stripped = line.strip()
            if stripped:
                console.print(f"  [dim]{stripped}[/dim]")

    if cluster_proc.returncode != 0:
        error_detail = cluster_proc.stderr.strip() if cluster_proc.stderr else "(no stderr output)"
        console.print(Panel(
            f"Graphify cluster-only exited with code {cluster_proc.returncode}.\n\n"
            f"STDERR:\n{error_detail}",
            title="[bold yellow]Warning[/bold yellow]",
            border_style="yellow",
        ))
        # Non-fatal: continue with move even if cluster-only fails.
        # The graph and HTML may still be valid from extraction.

    # -- Move graphify-out/ to data/reports/graphify_out/ --
    # Graphify creates graphify-out/ inside the target directory
    # (e.g., src/graphify-out/ when target_rel is "src").
    graphify_out_src = os.path.join(target_dir, 'graphify-out')
    if not os.path.isdir(graphify_out_src):
        # Fallback: also check project root for backward compatibility
        fallback_src = os.path.join(project_root, 'graphify-out')
        if os.path.isdir(fallback_src):
            graphify_out_src = fallback_src
        else:
            result['error'] = (
                "Graphify subprocess completed successfully but the expected "
                f"output directory was not found at '{os.path.join(target_dir, 'graphify-out')}' "
                f"or '{os.path.join(project_root, 'graphify-out')}'. "
                "The extraction may have produced no output."
            )
            console.print(Panel(
                result['error'],
                title="[bold yellow]Warning[/bold yellow]",
                border_style="yellow",
            ))
            return result


    # -- Remove existing output directory if present --
    if os.path.isdir(output_dir):
        try:
            shutil.rmtree(output_dir)
        except Exception as e:
            result['error'] = (
                f"Failed to remove existing output directory "
                f"'{output_dir}': {e}"
            )
            console.print(Panel(
                result['error'],
                title="[bold red]Error[/bold red]",
                border_style="red",
            ))
            return result

    # -- Move graphify-out/ to the reports directory --
    try:
        shutil.move(graphify_out_src, output_dir)
    except Exception as e:
        result['error'] = (
            f"Failed to move '{graphify_out_src}' to "
            f"'{output_dir}': {e}"
        )
        console.print(Panel(
            result['error'],
            title="[bold red]Error[/bold red]",
            border_style="red",
        ))
        return result

    console.print(
        f"  [green]Moved graphify-out/ -> {output_dir}[/green]"
    )

    # -- Inject Academic Print Mode (Light/Dark Toggle) into graph.html --
    _inject_light_mode_toggle(output_dir)

    # -- Collect generated files --
    generated_files = []
    try:
        for root, dirs, files in os.walk(output_dir):
            for fname in files:
                full = os.path.join(root, fname)
                generated_files.append(full)
    except Exception:
        pass

    result['files'] = generated_files

    # -- Attempt to read stats from graph.json --
    node_count = 0
    edge_count = 0
    graph_json_path = os.path.join(output_dir, 'graph.json')
    if os.path.isfile(graph_json_path):
        try:
            import json
            with open(graph_json_path, 'r', encoding='utf-8') as f:
                graph_data = json.load(f)
            node_count = len(graph_data.get('nodes', []))
            edge_count = len(graph_data.get('edges', []))
        except Exception:
            pass

    result['stats'] = {
        'node_count': node_count,
        'edge_count': edge_count,
        'files_analyzed': 0,  # Not easily countable from subprocess stdout
        'output_files': len(generated_files),
        'target_dir': target_dir,
    }
    result['success'] = True

    # -- Final summary --
    console.print(
        f"\n[bold green][SUCCESS][/bold green] Graphify pipeline complete."
    )
    console.print(f"[dim]Output directory: {output_dir}[/dim]")
    if node_count or edge_count:
        console.print(
            f"[dim]Graph: {node_count} nodes, {edge_count} edges[/dim]"
        )
    for f in generated_files:
        console.print(f"  [dim cyan]- {os.path.basename(f)}[/dim cyan]")

    return result


def _inject_light_mode_toggle(output_dir: str) -> None:
    """Post-process graph.html to inject an Academic Print Mode (Light/Dark) toggle.

    Opens ``graph.html`` in the output directory, injects a custom CSS block
    defining a ``.light-mode`` class on ``<body>`` that overrides dark backgrounds
    with white-background / dark-text academic print styling, and inserts a
    floating toggle button anchored to the top-right corner of the viewport.
    The original dark mode styling is preserved as the default; users can
    switch to light mode at any time via the button.

    This function is called automatically after the graphify-out/ directory
    is moved into ``data/reports/graphify_out/``. If ``graph.html`` does not
    exist or any I/O error occurs, the function logs a warning via Rich and
    returns gracefully without failing the pipeline.

    Args:
        output_dir: Absolute path to the directory containing ``graph.html``
                    (typically ``data/reports/graphify_out/``).
    """
    graph_html_path = os.path.join(output_dir, 'graph.html')
    if not os.path.isfile(graph_html_path):
        # graph.html was not generated -- this is non-fatal.
        return

    try:
        with open(graph_html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
    except Exception:
        # Graceful degradation: if we cannot read, skip injection.
        return

    # -- Academic Print Mode CSS block --
    # This block defines the .light-mode class overrides for a print-ready
    # white-background, dark-text, high-contrast academic theme.  All rules
    # use !important to ensure they win over the dynamically injected dark
    # styles produced by Graphify's internal JS visualization.
    light_mode_css = """
<style id="talos-light-mode-style">
/* TALOS v5.9.17 -- Academic Print Mode (Light Theme) Override */
/* Injected automatically by graphify_adapter.py post-processing step.  */

body.light-mode {
    background: #ffffff !important;
    color: #111827 !important;
}

body.light-mode .sidebar,
body.light-mode #sidebar,
body.light-mode [class*="sidebar"] {
    background: #f8f9fa !important;
    border-left: 1px solid #d1d5db !important;
    color: #111827 !important;
}

body.light-mode .node-info,
body.light-mode .node-details,
body.light-mode [class*="node-info"],
body.light-mode [class*="node-details"] {
    color: #111827 !important;
    background: #f3f4f6 !important;
}

body.light-mode .panel,
body.light-mode [class*="panel"] {
    background: #f3f4f6 !important;
    color: #111827 !important;
    border-color: #d1d5db !important;
}

body.light-mode a,
body.light-mode .link {
    color: #1d4ed8 !important;
}

body.light-mode h1, body.light-mode h2, body.light-mode h3,
body.light-mode h4, body.light-mode h5, body.light-mode h6 {
    color: #0f172a !important;
}

body.light-mode svg text {
    fill: #111827 !important;
}

body.light-mode svg .node text,
body.light-mode svg .label {
    fill: #111827 !important;
    stroke: none !important;
}

body.light-mode svg .edge,
body.light-mode svg .link,
body.light-mode svg line {
    stroke: #6b7280 !important;
}

body.light-mode .graph-container,
body.light-mode #graph,
body.light-mode [class*="graph"] {
    background: #ffffff !important;
}

body.light-mode .header,
body.light-mode #header,
body.light-mode .title-bar {
    background: #e5e7eb !important;
    color: #0f172a !important;
    border-bottom: 1px solid #d1d5db !important;
}

/* Toggle button styling */
#talos-theme-toggle {
    position: fixed;
    top: 12px;
    right: 12px;
    z-index: 99999;
    padding: 8px 16px;
    border-radius: 6px;
    border: 1px solid #6b7280;
    background: #1f2937;
    color: #f9fafb;
    font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
    font-size: 13px;
    font-weight: 600;
    cursor: pointer;
    box-shadow: 0 2px 8px rgba(0,0,0,0.25);
    transition: background 0.2s ease, color 0.2s ease;
    user-select: none;
}

#talos-theme-toggle:hover {
    background: #374151;
}

body.light-mode #talos-theme-toggle {
    background: #e5e7eb;
    color: #111827;
    border-color: #9ca3af;
}

body.light-mode #talos-theme-toggle:hover {
    background: #d1d5db;
}
</style>"""

    # -- Floating toggle button HTML --
    toggle_button_html = """
<button id="talos-theme-toggle" onclick="document.body.classList.toggle('light-mode');" title="Toggle Academic Print Mode (Light/Dark)">
    Toggle Academic Light Mode
</button>"""

    # -- Inject CSS before </head> --
    if '</head>' in html_content:
        html_content = html_content.replace('</head>', light_mode_css + '\n</head>')
    else:
        # Fallback: prepend to <body> if no </head> tag found
        html_content = light_mode_css + '\n' + html_content

    # -- Inject button right after <body> opening tag --
    if '<body' in html_content:
        # Find the > that closes the <body ...> tag
        body_open_end = html_content.find('>', html_content.find('<body'))
        if body_open_end != -1:
            html_content = (
                html_content[:body_open_end + 1]
                + toggle_button_html
                + html_content[body_open_end + 1:]
            )
    else:
        # Fallback: prepend button at very top of HTML
        html_content = toggle_button_html + '\n' + html_content

    # -- Write back the modified HTML --
    try:
        with open(graph_html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
    except Exception:
        # Graceful degradation -- if we cannot write, skip without failing.
        return

    # -- Log success via Rich console --
    try:
        from rich.console import Console
        console = Console()
        console.print(
            "  [dim cyan]Injected Academic Print Mode (Light/Dark) toggle into graph.html[/dim cyan]"
        )
    except Exception:
        pass


# -- Standalone execution support --
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(
        description="TALOS Graphify AST Knowledge Graph Adapter"
    )
    parser.add_argument(
        'target_dir',
        nargs='?',
        default=None,
        help='Directory to analyze (default: project src/)',
    )
    args = parser.parse_args()
    generate_ast_knowledge_graph(args.target_dir)