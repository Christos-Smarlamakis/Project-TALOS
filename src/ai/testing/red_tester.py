# -*- coding: utf-8 -*-
"""
Module: red_tester.py
Project: TALOS v5.9.18
Description:
    Autonomous Red Tester (RL-Driven Chaos Engineering) that stress-tests TALOS
    system components using a Non-Stationary Multi-Armed Bandit (Epsilon-Greedy with
    constant step-size alpha). Two categories of test arms are discovered at runtime:
    (1) CLI arms -- every non-__init__.py Python module under src/ executed as a
    subprocess with --help -- and (2) API fuzzing arms -- malformed or edge-case HTTP
    requests against the local FastAPI on http://127.0.0.1:8001. If a target crashes
    (non-zero exit for CLI, HTTP 5xx or timeout for API), the stderr is sent to the
    Fast Edge LLM (tier="fast") for a human-readable two-sentence diagnosis. Results
    are visualized in the terminal using Rich (Spinners, Panels, Tables) and saved as
    timestamped Markdown crash reports under data/reports/red_tester/. A Synapse
    event is emitted on each test cycle.

    Key design decisions:
    - Non-stationary MAB: Epsilon=0.2 for exploration, alpha=0.1 for constant step-size
      Q-value updates. This ensures the bandit tracks shifting component fragility over
      time rather than converging to a stationary estimate.
    - Reward signal: +50 for a crash (the tester seeks crashes to surface), -1 for a
      successful pass (small penalty to discourage testing stable components).
    - Graceful rejection is a pass: API responses 400, 404, and 422 mean the endpoint
      validated the malformed input correctly and are treated as passes (reward -1).
    - Unhandled exceptions are crashes: API responses 500 or request timeouts are
      treated as crashes (reward +50), with the HTTP status and body fed to the LLM.
    - Q-table persisted as JSON at data/red_tester_q_table.json for continuity across runs.
    - Subprocess timeout of 5 seconds and API timeout of 3 seconds prevent hung tests
      from blocking the pipeline.
    - LLM Context Truncation: error output sent to the Fast Edge LLM is clipped to the
      last 2,000 characters to prevent context window overflow on massive stack traces.
    - LLM-as-a-Judge uses AIManager with tier="fast" for low-latency diagnosis.
    - Zero emojis protocol: all Rich output uses formal academic tone with color coding
      (green for pass, red for failure, yellow for AI diagnosis).

Dependencies:
    - json, os, subprocess, time, datetime: Core Python runtime for execution and I/O.
    - random: Epsilon-greedy action selection.
    - requests: HTTP client for API fuzzing arms (3-second timeout).
    - rich.console, rich.panel, rich.table, rich.status: Terminal UI beautification.
    - src.core.ai_manager: LLM-as-a-Judge diagnosis via fast edge tier.
    - src.integration.synapse_client: Synapse event emission.
"""
import json
import os
import random
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# -- Rich imports for the gorgeous terminal visualization --
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.status import Status
from rich.text import Text
from rich import box
from rich.align import Align

console = Console()

# -- v5.9.8: Clickable Terminal Hyperlinks --
def _make_clickable_path(path_str: str) -> str:
    """Convert a file path to a Rich terminal hyperlink for CTRL+CLICK navigation.

    Args:
        path_str: Absolute or relative file path.

    Returns:
        Rich [link=file:///...] formatted string with forward slashes.
    """
    abs_path = os.path.abspath(path_str).replace("\\", "/")
    return f"[link=file:///{abs_path}]{path_str}[/link]"

# -- Resolve project root (same pattern as all src/*.py modules) --
_PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
while _PROJECT_ROOT and not os.path.exists(os.path.join(_PROJECT_ROOT, 'talos.py')):
    _PROJECT_ROOT = os.path.dirname(_PROJECT_ROOT)

if _PROJECT_ROOT:
    sys.path.insert(0, _PROJECT_ROOT)

# -- Lazy imports for core modules (avoid import errors in air-gapped environments) --
_ai_manager = None
_synapse_emitter = None


def _get_ai_manager():
    """Lazy-init singleton AIManager for LLM-as-a-Judge diagnosis."""
    global _ai_manager
    if _ai_manager is None:
        try:
            from src.core.ai_manager import AIManager
            _ai_manager = AIManager({})
        except Exception as e:
            console.print(f"[yellow][WARNING][/yellow] AIManager unavailable: {e}")
            _ai_manager = False  # Sentinel to avoid repeated attempts
    return _ai_manager if _ai_manager is not False else None


def _get_synapse_emitter():
    """Lazy-init Synapse EventEmitter for outbound events."""
    global _synapse_emitter
    if _synapse_emitter is None:
        try:
            from src.integration.synapse_client import synapse_emitter
            _synapse_emitter = synapse_emitter
        except Exception:
            _synapse_emitter = False
    return _synapse_emitter if _synapse_emitter is not False else None


# ---------------------------------------------------------------------------
# -- Configuration Constants --
# ---------------------------------------------------------------------------

# -- Target arms: dynamically discovered from src/ at runtime --
TARGET_ARMS: List[Tuple[str, str, object, object]] = []


def _discover_all_targets() -> List[Tuple[str, str, object, object]]:
    """Discover all test arms: CLI targets plus API fuzzing targets.

    CLI targets are all non-__init__.py files under src/ executed with --help.
    API fuzzing targets are malformed or edge-case HTTP requests against the
    local FastAPI (http://127.0.0.1:8001).

    Returns:
        List of (arm_type, display_name, target, args) tuples. arm_type is
        "cli" or "api". For CLI arms target is the relative .py path and args
        is the argument list. For API arms target is a request spec dict and
        args is None.
    """
    target_dirs = [
        "src/analysis",
        "src/ingestion",
        "src/ai",
        "src/utils",
        "src/core",
        "src/api",
    ]

    arms: List[Tuple[str, str, object, object]] = []
    for target_dir in target_dirs:
        dir_path = os.path.join(_PROJECT_ROOT, target_dir)
        if not os.path.isdir(dir_path):
            continue
        for root, dirs, files in os.walk(dir_path):
            for file in sorted(files):
                if file.endswith(".py") and file != "__init__.py":
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, _PROJECT_ROOT).replace("\\", "/")
                    module_part = rel_path.replace("/", ".").replace(".py", "")
                    display_name = f"{rel_path} ({module_part})"
                    arms.append(("cli", display_name, rel_path, ["--help"]))

    # -- API fuzzing arms: malformed or edge-case HTTP requests --
    arms.extend(_build_api_fuzzing_arms())

    return arms


def _build_api_fuzzing_arms() -> List[Tuple[str, str, object, object]]:
    """Build the API fuzzing arms targeting the local FastAPI.

    Each arm sends a malformed or edge-case request designed to probe the
    endpoint's input validation. Graceful rejections (400/404/422) are passes;
    HTTP 5xx responses and timeouts are crashes.

    Returns:
        List of ("api", display_name, request_spec, None) tuples. Each request
        spec is a dict with "method", "url", and optional "json"/"data"/"headers".
    """
    base = API_BASE_URL
    return [
        (
            "api",
            f"POST {base}/api/v1/synapse/webhook (malformed JSON)",
            {
                "method": "POST",
                "url": f"{base}/api/v1/synapse/webhook",
                "data": '{"command": "trigger_search", "params": ',
                "headers": {"Content-Type": "application/json"},
            },
            None,
        ),
        (
            "api",
            f"GET {base}/api/v1/papers/-999 (invalid negative ID)",
            {"method": "GET", "url": f"{base}/api/v1/papers/-999"},
            None,
        ),
        (
            "api",
            f"POST {base}/api/v1/search/semantic (empty query body)",
            {"method": "POST", "url": f"{base}/api/v1/search/semantic", "json": {}},
            None,
        ),
        (
            "api",
            f"POST {base}/api/v1/scrape/trigger (invalid source names)",
            {
                "method": "POST",
                "url": f"{base}/api/v1/scrape/trigger",
                "json": {"source_filter": ["nonexistent_source"]},
            },
            None,
        ),
    ]


# -- MAB hyperparameters --
EPSILON = 0.2       # Exploration probability
ALPHA = 0.1         # Constant step-size for non-stationary Q-value updates
CRASH_REWARD = 50.0 # Reward when a target crashes (we want to find crashes)
PASS_PENALTY = -1.0 # Penalty when a target passes cleanly

# -- Subprocess configuration --
SUBPROCESS_TIMEOUT = 5  # Seconds before a test is considered hung

# -- API fuzzing configuration --
API_BASE_URL = "http://127.0.0.1:8001"  # Local FastAPI target for fuzzing arms
API_TIMEOUT = 3  # Seconds before an API fuzz request is considered hung
API_GRACEFUL_STATUS_CODES = {400, 404, 422}  # Validation rejections handled correctly

# -- LLM context protection --
CONTEXT_WINDOW_LIMIT = 2000  # Last N characters of error output sent to the Fast Edge LLM

# -- Persistence paths --
Q_TABLE_PATH = os.path.join(_PROJECT_ROOT, "data", "red_tester_q_table.json")
REPORTS_DIR = os.path.join(_PROJECT_ROOT, "data", "reports", "red_tester")

# -- AI diagnosis prompt template --
DIAGNOSIS_PROMPT = (
    "You are an expert software reliability engineer. A TALOS system component "
    "crashed during automated stress testing. Below is the stderr output from the "
    "crash. Provide a concise two-sentence diagnosis: (1) the likely root cause of "
    "the failure, and (2) a specific remediation recommendation.\n\n"
    "Component: {component_name}\n"
    "Command: {command}\n\n"
    "--- STDERR OUTPUT ---\n"
    "{stderr}\n"
    "--- END STDERR ---\n\n"
    "Diagnosis (exactly two sentences):"
)


# ---------------------------------------------------------------------------
# -- Q-Table Persistence --
# ---------------------------------------------------------------------------

def _load_q_table() -> Dict[int, float]:
    """Load the Q-table from data/red_tester_q_table.json.

    Returns:
        Dict mapping arm index (0..N-1) to estimated Q-value (float).
        Returns a zero-initialized table if the file does not exist.
    """
    if os.path.exists(Q_TABLE_PATH):
        try:
            with open(Q_TABLE_PATH, "r", encoding="utf-8") as f:
                raw = json.load(f)
            # Convert string keys back to int
            return {int(k): float(v) for k, v in raw.items()}
        except (json.JSONDecodeError, ValueError, KeyError):
            console.print("[yellow][WARNING][/yellow] Q-table file corrupted. Reinitializing.")
    # Initialize with zeros for all arms
    return {i: 0.0 for i in range(len(TARGET_ARMS))}


def _save_q_table(q_table: Dict[int, float]):
    """Persist the Q-table to data/red_tester_q_table.json.

    Args:
        q_table: Dict mapping arm index to estimated Q-value.
    """
    os.makedirs(os.path.dirname(Q_TABLE_PATH), exist_ok=True)
    serializable = {str(k): v for k, v in q_table.items()}
    with open(Q_TABLE_PATH, "w", encoding="utf-8") as f:
        json.dump(serializable, f, indent=2, ensure_ascii=False)


# ---------------------------------------------------------------------------
# -- LLM-as-a-Judge Diagnosis --
# ---------------------------------------------------------------------------

def _protect_context_window(text: str, max_chars: int = CONTEXT_WINDOW_LIMIT) -> str:
    """Clip diagnostic text to the tail to protect the LLM context window.

    Keeps only the last max_chars characters (the most relevant tail of a stack
    trace) and prepends a truncation marker when clipping occurred. This prevents
    context window overflow (OOM) on massive stack traces.

    Args:
        text: The raw error output.
        max_chars: Maximum number of characters to retain (default 2000).

    Returns:
        The protected text, possibly prefixed with a truncation marker.
    """
    if not text:
        return ""
    if len(text) <= max_chars:
        return text
    return f"[TRUNCATED {len(text) - max_chars} characters]\n...\n{text[-max_chars:]}"


def _diagnose_crash(component_name: str, command: str, stderr: str) -> Optional[str]:
    """Send crash stderr to the Fast Edge LLM for human-readable diagnosis.

    Args:
        component_name: Human-readable name of the crashed component.
        command: The exact subprocess command that was executed.
        stderr: Captured stderr output from the crashed subprocess.

    Returns:
        Two-sentence diagnosis string, or None if the AI manager is unavailable.
    """
    ai = _get_ai_manager()
    if ai is None:
        return None

    prompt = DIAGNOSIS_PROMPT.format(
        component_name=component_name,
        command=command,
        stderr=_protect_context_window(stderr),  # Keep last 2000 chars to protect the context window
    )

    try:
        result = ai._execute_request(
            prompt,
            model_type="pro",
            response_format="text",
            tier="fast",
            allow_prompt=False,
        )
        if result and isinstance(result, str):
            return result.strip()
    except Exception as e:
        console.print(f"[yellow][WARNING][/yellow] AI diagnosis failed: {e}")

    return None


# ---------------------------------------------------------------------------
# -- Arm Execution (CLI Subprocess + API Fuzzing) --
# ---------------------------------------------------------------------------

def _execute_arm(arm: Tuple[str, str, object, object]) -> Tuple[bool, str, str]:
    """Execute a single test arm and classify its outcome.

    Dispatches to the CLI subprocess executor or the API fuzzer based on the
    arm type.

    Args:
        arm: A (arm_type, display_name, target, args) tuple.

    Returns:
        Tuple of (crashed: bool, stdout: str, stderr: str). For API arms a crash
        is an HTTP 5xx or a timeout; graceful rejections (400/404/422) are passes.
    """
    arm_type, display_name, target, args = arm
    if arm_type == "cli":
        return _execute_cli_arm(display_name, target, args)
    if arm_type == "api":
        return _execute_api_arm(display_name, target)
    return True, "", f"Unknown arm type: {arm_type}"


def _execute_cli_arm(
    display_name: str,
    script_path: str,
    args: List[str],
) -> Tuple[bool, str, str]:
    """Execute a CLI target script as a subprocess with a timeout.

    Args:
        display_name: Human-readable component name.
        script_path: Relative path from project root to the target .py file.
        args: Additional command-line arguments (e.g., --help to trigger fast exit).

    Returns:
        Tuple of (crashed: bool, stdout: str, stderr: str).
        crashed is True if the subprocess returned non-zero exit code or timed out.
    """
    full_path = os.path.join(_PROJECT_ROOT, script_path)
    command = [sys.executable or "python", full_path] + args

    crashed = False
    stdout_str = ""
    stderr_str = ""

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            encoding='utf-8',
            errors='replace',
            timeout=SUBPROCESS_TIMEOUT,
            cwd=_PROJECT_ROOT,
            env={**os.environ, "PYTHONIOENCODING": "utf-8"},
        )
        stdout_str = result.stdout or ""
        stderr_str = result.stderr or ""
        if result.returncode != 0:
            crashed = True
    except subprocess.TimeoutExpired as e:
        crashed = True
        stdout_str = e.stdout.decode("utf-8", errors="replace") if e.stdout else ""
        stderr_str = e.stderr.decode("utf-8", errors="replace") if e.stderr else ""
        if not stderr_str:
            stderr_str = f"Process timed out after {SUBPROCESS_TIMEOUT} seconds."
    except Exception as e:
        crashed = True
        stderr_str = f"Subprocess execution exception: {e}"

    return crashed, stdout_str, stderr_str


def _execute_api_arm(
    display_name: str,
    request_spec: object,
) -> Tuple[bool, str, str]:
    """Send a malformed or edge-case HTTP request to the local FastAPI.

    Graceful rejections (400, 404, 422) mean the endpoint validated the bad input
    correctly and are treated as passes. HTTP 5xx responses and timeouts are
    treated as crashes, with the HTTP status and body included for LLM diagnosis.

    Args:
        display_name: Human-readable arm label.
        request_spec: Dict with "method", "url", and optional "json"/"data"/"headers".

    Returns:
        Tuple of (crashed: bool, stdout: str, stderr: str).
    """
    try:
        import requests
    except ImportError:
        return False, "", "requests library unavailable -- API fuzz arm skipped"

    spec = request_spec if isinstance(request_spec, dict) else {}
    method = spec.get("method", "GET")
    url = spec.get("url", "")
    kwargs = {}
    if "json" in spec:
        kwargs["json"] = spec["json"]
    if "data" in spec:
        kwargs["data"] = spec["data"]
    if "headers" in spec:
        kwargs["headers"] = spec["headers"]

    try:
        response = requests.request(method, url, timeout=API_TIMEOUT, **kwargs)
    except requests.exceptions.Timeout:
        # A hung endpoint is a real finding -- treat as a crash.
        stderr = f"API fuzz timeout: {method} {url} did not respond within {API_TIMEOUT} seconds."
        return True, "", stderr
    except requests.exceptions.ConnectionError:
        # The API is offline -- not a crash, avoid polluting the Q-table.
        return False, "", f"API unreachable (connection refused): {method} {url}"
    except Exception as e:
        # A fuzzer-side error, not an API defect.
        return False, "", f"API fuzz request exception: {e}"

    status = response.status_code
    text = (response.text or "")[:2000]
    stdout = f"{method} {url} -> HTTP {status}"

    if status >= 500:
        # Unhandled exception on the server side -- a crash worth surfacing.
        stderr = f"HTTP {status}: {text}"
        return True, stdout, stderr

    if status in API_GRACEFUL_STATUS_CODES:
        # Graceful rejection: the endpoint validated the bad input correctly.
        return False, stdout, f"Graceful rejection HTTP {status}: {text[:500]}"

    # Any other response (2xx, 3xx, other 4xx) did not crash the API.
    return False, stdout, f"HTTP {status}: {text[:500]}"


# ---------------------------------------------------------------------------
# -- Epsilon-Greedy Action Selection --
# ---------------------------------------------------------------------------

def _select_arm(q_table: Dict[int, float]) -> int:
    """Select an arm using epsilon-greedy strategy.

    With probability EPSILON, selects a random arm (exploration).
    Otherwise, selects the arm with the highest Q-value (exploitation).
    Ties are broken randomly among the best arms.

    Args:
        q_table: Current Q-value estimates per arm index.

    Returns:
        Selected arm index (0 to N-1).
    """
    n_arms = len(TARGET_ARMS)
    if random.random() < EPSILON:
        return random.randrange(n_arms)

    # -- Exploit: pick the arm with highest Q-value (break ties randomly) --
    max_q = max(q_table.values())
    best_arms = [i for i, q in q_table.items() if q == max_q]
    return random.choice(best_arms)


# ---------------------------------------------------------------------------
# -- Crash Report Generation --
# ---------------------------------------------------------------------------

def _save_crash_report(
    display_name: str,
    command: str,
    stdout: str,
    stderr: str,
    diagnosis: Optional[str],
    q_table: Dict[int, float],
    arm_index: int,
) -> str:
    """Generate and save a Markdown crash report.

    Args:
        display_name: Human-readable component name.
        command: The command that was executed.
        stdout: Captured stdout.
        stderr: Captured stderr.
        diagnosis: AI-generated diagnosis or None.
        q_table: Current Q-table after update.
        arm_index: Index of the arm that crashed.

    Returns:
        Absolute path to the saved report file.
    """
    os.makedirs(REPORTS_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"CRASH_REPORT_{timestamp}.md"
    filepath = os.path.join(REPORTS_DIR, filename)

    diagnosis_text = diagnosis if diagnosis else "AI diagnosis unavailable (AIManager offline or request failed)."

    # -- Build Q-table summary for the report --
    q_table_lines = ""
    for i, (_, name, _, _) in enumerate(TARGET_ARMS):
        q_val = q_table.get(i, 0.0)
        marker = " <-- CRASHED" if i == arm_index else ""
        q_table_lines += f"| {name} | {q_val:+.2f}{marker} |\n"

    report_content = f"""# Autonomous Red Tester -- Crash Report

**Timestamp:** {datetime.now(timezone.utc).isoformat()}
**Component:** {display_name}
**Arm Index:** {arm_index}
**Command:** `{command}`

---

## AI Diagnosis (LLM-as-a-Judge, Fast Edge Tier)

{diagnosis_text}

---

## STDERR Output

```
{stderr[:5000] if stderr else "(empty)"}
```

---

## STDOUT Output

```
{stdout[:2000] if stdout else "(empty)"}
```

---

## Q-Table After Crash (Component Fragility Estimates)

| Component | Q-Value |
|---|---|
{q_table_lines}

---

*Report generated by TALOS v5.9.18 Autonomous Red Tester (RL-Driven Chaos Engineering)*
"""
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(report_content)

    return filepath


# ---------------------------------------------------------------------------
# -- Rich TUI Helpers --
# ---------------------------------------------------------------------------

def _build_q_table_panel(q_table: Dict[int, float]) -> Table:
    """Build a Rich Table displaying the current Q-table (Component Fragility).

    Higher Q-values indicate components more likely to crash -- these are
    the most fragile targets.

    Args:
        q_table: Current Q-value estimates per arm index.

    Returns:
        A rich.table.Table ready for console rendering.
    """
    table = Table(
        title="[bold bright_cyan]RL Q-Table (Component Fragility Estimates)[/bold bright_cyan]",
        box=box.ROUNDED,
        border_style="bright_blue",
        show_lines=True,
        header_style="bold bright_cyan",
    )
    table.add_column("#", style="dim cyan", width=4, justify="right")
    table.add_column("Component", style="white", width=50)
    table.add_column("Q-Value (Fragility)", style="bold", width=20, justify="right")
    table.add_column("Status", style="white", width=20)

    for i, (_, name, _, _) in enumerate(TARGET_ARMS):
        q_val = q_table.get(i, 0.0)
        # Color-code based on fragility
        if q_val >= 40:
            q_style = "[bold red]"
            status = "[red]HIGH FRAGILITY[/red]"
        elif q_val >= 10:
            q_style = "[bold yellow]"
            status = "[yellow]MODERATE[/yellow]"
        elif q_val > 0:
            q_style = "[dim yellow]"
            status = "[dim yellow]LOW[/dim yellow]"
        else:
            q_style = "[dim green]"
            status = "[green]STABLE[/green]"

        table.add_row(
            str(i + 1),
            name,
            f"{q_style}{q_val:+.2f}[/{q_style.split('[')[1].split(']')[0] if q_style != '[dim green]' else 'dim green'}]",
            status,
        )
    return table


# ---------------------------------------------------------------------------
# -- Main Test Cycle --
# ---------------------------------------------------------------------------

def _run_test_cycle(
    q_table: Dict[int, float],
    cycle: int,
    total_cycles: int,
) -> Dict[int, float]:
    """Execute a single test cycle: select arm, test target, update Q-table.

    Args:
        q_table: Current Q-value estimates (mutated in-place).
        cycle: Current cycle number (1-based, for display).
        total_cycles: Total number of cycles to run.

    Returns:
        Updated Q-table dict (same object reference).
    """
    n_arms = len(TARGET_ARMS)
    arm_index = _select_arm(q_table)
    arm = TARGET_ARMS[arm_index]
    arm_type, display_name, target, args = arm

    # -- Build the cycle header --
    console.print("")
    cycle_text = Text()
    cycle_text.append(f"Cycle {cycle}/{total_cycles}", style="bold bright_cyan")
    cycle_text.append(f"  |  Target: ", style="dim white")
    cycle_text.append(display_name, style="bold white")
    cycle_text.append(f"  |  Arm {arm_index + 1}/{n_arms}", style="dim cyan")
    console.print(Panel(
        Align.center(cycle_text),
        border_style="bright_blue",
        box=box.ROUNDED,
    ))

    # -- Build the command for display --
    if arm_type == "cli":
        command_str = f"{sys.executable or 'python'} {target} {' '.join(args)}"
        status_label = target
    else:
        spec = target if isinstance(target, dict) else {}
        command_str = f"{spec.get('method', 'GET')} {spec.get('url', '')}"
        status_label = command_str

    # -- Execute with Rich spinner --
    crashed = False
    stdout_str = ""
    stderr_str = ""
    with console.status(
        f"[bold bright_cyan][TESTING][/bold bright_cyan] Executing: {status_label}...",
        spinner="dots",
    ):
        crashed, stdout_str, stderr_str = _execute_arm(arm)

    # -- Compute reward and update Q-value --
    reward = CRASH_REWARD if crashed else PASS_PENALTY
    old_q = q_table[arm_index]
    new_q = old_q + ALPHA * (reward - old_q)
    q_table[arm_index] = new_q

    # -- Display result --
    if crashed:
        # -- Crash: render red Panel with traceback --
        crash_panel = Panel(
            Text(stderr_str[:2000] if stderr_str else "(no stderr captured)", style="red"),
            title="[bold red]CRASH DETECTED[/bold red]",
            border_style="red",
            box=box.ROUNDED,
            padding=(1, 2),
        )
        console.print(crash_panel)

        # -- AI Diagnosis --
        diagnosis = _diagnose_crash(display_name, command_str, stderr_str)
        if diagnosis:
            diag_panel = Panel(
                Text(diagnosis, style="yellow"),
                title="[bold yellow]AI DIAGNOSIS (Fast Edge LLM)[/bold yellow]",
                border_style="yellow",
                box=box.ROUNDED,
                padding=(1, 2),
            )
            console.print(diag_panel)
        else:
            console.print("[dim yellow]AI diagnosis unavailable.[/dim yellow]")

        # -- Save crash report --
        report_path = _save_crash_report(
            display_name, command_str, stdout_str, stderr_str,
            diagnosis, q_table, arm_index,
        )
        console.print(f"[dim green]Crash report saved: {_make_clickable_path(report_path)}[/dim green]")

        # -- Emit Synapse event --
        emitter = _get_synapse_emitter()
        if emitter:
            try:
                emitter.emit(
                    "agent_episode_end",
                    {
                        "component": display_name,
                        "arm_index": arm_index,
                        "crashed": True,
                        "reward": reward,
                        "q_value_before": old_q,
                        "q_value_after": new_q,
                        "diagnosis": diagnosis,
                        "cycle": cycle,
                    },
                )
            except Exception:
                pass  # Synapse emission is best-effort
    else:
        # -- Pass: green confirmation --
        console.print(f"[bold green][PASS][/bold green] {display_name} passed cleanly. Reward: {PASS_PENALTY:+.1f}")

    # -- Show Q-value change --
    console.print(
        f"[dim]Q-value: {old_q:+.2f} -> [bold]{new_q:+.2f}[/bold] "
        f"(alpha={ALPHA}, reward={reward:+.1f})[/dim]"
    )

    return q_table


# ---------------------------------------------------------------------------
# -- Standalone Entry Point --
# ---------------------------------------------------------------------------

def run_red_tester(cycles: int = 10):
    """Entry point for the Autonomous Red Tester.

    Runs the Non-Stationary MAB for the specified number of cycles, testing
    TALOS system components, diagnosing crashes with LLM-as-a-Judge, and
    displaying results via Rich TUI.

    Args:
        cycles: Number of test cycles to execute (default 10).
    """
    # -- Discover all Python targets dynamically --
    global TARGET_ARMS
    TARGET_ARMS = _discover_all_targets()
    if not TARGET_ARMS:
        console.print("[red][ERROR][/red] No test targets discovered. Aborting.")
        return

    # -- Load Q-table (reconciled to match discovered arm count) --
    q_table = _load_q_table()
    expected_keys = set(range(len(TARGET_ARMS)))
    if set(q_table.keys()) != expected_keys:
        reconciled = {}
        for i in range(len(TARGET_ARMS)):
            reconciled[i] = q_table.get(i, 0.0)
        q_table = reconciled

    # -- Header banner --
    console.print("")
    banner = Panel(
        Align.center(Text(
            "Autonomous Red Tester\n"
            "RL-Driven Chaos Engineering with LLM-as-a-Judge Diagnostics",
            style="bold bright_cyan",
        )),
        title="[bold]TALOS v5.9.18[/bold]",
        subtitle="[dim]Non-Stationary Epsilon-Greedy Multi-Armed Bandit[/dim]",
        border_style="bright_magenta",
        box=box.ROUNDED,
        padding=(1, 2),
    )
    console.print(banner)

    # -- Configuration summary --
    config_table = Table(show_header=False, box=None, padding=(0, 2))
    config_table.add_column("Param", style="dim cyan")
    config_table.add_column("Value", style="white")
    config_table.add_row("Arms", str(len(TARGET_ARMS)))
    config_table.add_row("Epsilon", str(EPSILON))
    config_table.add_row("Alpha (step-size)", str(ALPHA))
    config_table.add_row("Crash Reward", f"+{CRASH_REWARD:.0f}")
    config_table.add_row("Pass Penalty", f"{PASS_PENALTY:+.0f}")
    config_table.add_row("Timeout", f"{SUBPROCESS_TIMEOUT}s")
    config_table.add_row("Q-Table Path", Q_TABLE_PATH)
    config_table.add_row("Reports Dir", REPORTS_DIR)
    console.print(Panel(config_table, title="[bold]Configuration[/bold]", border_style="cyan", box=box.ROUNDED))
    console.print("")

    # -- Show initial Q-table --
    console.print(_build_q_table_panel(q_table))
    console.print("")

    # -- Run test cycles --
    console.print(f"[bold bright_cyan]Starting {cycles} test cycles...[/bold bright_cyan]")
    console.print("[dim]Use Ctrl+C to abort the test run early.[/dim]\n")

    for cycle in range(1, cycles + 1):
        try:
            q_table = _run_test_cycle(q_table, cycle, cycles)
        except KeyboardInterrupt:
            console.print("\n[yellow]Test run aborted by user.[/yellow]")
            break
        except Exception as e:
            console.print(f"[red]Unexpected error in cycle {cycle}: {e}[/red]")

    # -- Persist Q-table --
    _save_q_table(q_table)

    # -- Final Q-table display --
    console.print("")
    console.print(_build_q_table_panel(q_table))
    console.print("")

    # -- Summary --
    crashes_found = sum(1 for v in q_table.values() if v > 0)
    console.print(
        Panel(
            Text(
                f"Test run complete. Q-table saved to {_make_clickable_path(Q_TABLE_PATH)}.\n"
                f"Components with positive fragility: {crashes_found}/{len(TARGET_ARMS)}.\n"
                f"Crash reports: {_make_clickable_path(REPORTS_DIR)}",
                style="white",
            ),
            title="[bold green]Summary[/bold green]",
            border_style="green",
            box=box.ROUNDED,
        )
    )


# ---------------------------------------------------------------------------
# -- Main Guard for Standalone Execution --
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # -- Parse optional cycle count from command line --
    num_cycles = 10
    if len(sys.argv) > 1:
        try:
            num_cycles = int(sys.argv[1])
        except ValueError:
            console.print("[yellow]Invalid cycle count. Using default (10).[/yellow]")

    try:
        run_red_tester(cycles=num_cycles)
    except KeyboardInterrupt:
        console.print("\n[yellow]Autonomous Red Tester terminated by user.[/yellow]")
    except Exception as e:
        console.print(f"\n[red]Fatal error: {e}[/red]")
        sys.exit(1)