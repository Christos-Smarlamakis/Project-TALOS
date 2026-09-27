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
Module: research_setup_wizard.py
Project: TALOS v5.12.1
Description:
    Structured, step-by-step research onboarding wizard for TALOS. Guides the
    researcher through four plain-English steps: (1) research topic capture
    with local cognitive scope validation, (2) AI execution strategy selection,
    (3) historical search window selection, and (4) an optional first-flight
    test that triggers a 10-paper search and opens the 3D Knowledge
    Constellation Visualizer.

    Key design decisions:
    - English-First Scientific Standard: every prompt, panel, and generated
      boolean query is produced in professional academic English so the output
      is 100% compatible with the 16 academic ingestion APIs.
    - Air-gapped failsafe: the wizard probes the local Ollama (port 11434) and
      Fast Edge (port 11435) runtimes, silently attempts to auto-spawn them,
      then performs a bounded 2-second wait. If no runtime is reachable, every
      cognitive step degrades to deterministic rule-based heuristics without
      blocking or crashing.
    - A sentinel file (data/.talos_onboarded) is written only after successful
      completion so the TUI can fast-boot on subsequent launches.
    - Query transparency (v5.12.1): after compilation, a rounded Rich table
      previews the boolean queries for the top primary sources alongside the
      inclusion/exclusion criteria, followed by a Questionary confirmation
      before the parameters are persisted to config.json.

Dependencies:
    - questionary: interactive prompts using the canonical TALOS theme.
    - rich: Panel, Table, and Console rendering for the academic header/summary.
    - dotenv: reading and safely updating the .env execution strategy keys.
    - src.utils.ui_theme: TALOS_QUESTIONARY_STYLE prompt theme.
    - src.utils.logger: enterprise Rich + rotating-file logger.
    - src.core.ai_manager: multi-provider LLM interface for scope validation and
      query generation (used only when a local runtime is reachable).
    - src.ai.llm.query_translator: flatten_json helper reused to normalize the
      LLM-generated query/criteria JSON into flat config.json keys.
"""
import os
import sys
import json
import time
import socket
import subprocess
import webbrowser
from concurrent.futures import ThreadPoolExecutor

# -- Resolve project root (same pattern as every src/*.py module) -------------
_P = os.path.abspath(os.path.dirname(__file__))
while _P and not os.path.exists(os.path.join(_P, 'talos.py')):
    _P = os.path.dirname(_P)
if _P:
    sys.path.insert(0, _P)

import questionary
from dotenv import load_dotenv, set_key

from src.utils.ui_theme import TALOS_QUESTIONARY_STYLE
from src.utils.logger import get_logger
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.align import Align
from rich.table import Table
from rich import box

logger = get_logger("research_setup_wizard")
console = Console()

# -- Runtime probing constants -------------------------------------------------
OLLAMA_PORT = 11434          # Standard Ollama (GPU heavy tier)
EDGE_PORT = 11435            # Fast Edge CPU endpoint (Llama-3.1-8B / Neutrino)
PROBE_TIMEOUT = 0.8          # seconds per port probe
BOOTSTRAP_WAIT = 2.0         # seconds of bounded polling after spawn attempt
LLM_SCOPE_TIMEOUT = 2.0      # seconds for the Fast Edge scope validation
LLM_QUERY_TIMEOUT = 30.0     # seconds for full query/criteria generation

# -- Sentinel and fixed locations ----------------------------------------------
SENTINEL_FILENAME = ".talos_onboarded"
VISUALIZER_URL = "http://127.0.0.1:8001/api/v1/visualizer/live"
API_HEALTH_URL = "http://127.0.0.1:8001/api/v1/health"
API_PORT = 8001

# -- Cognitive validation threshold --------------------------------------------
MIN_WORDS = 3                # algorithmic minimum for a viable research topic

# -- The 16 ingestion source query keys written back to config.json -------------
SOURCE_QUERY_KEYS = [
    "arxiv_query", "ieee_query", "semantic_scholar_query", "springer_query",
    "openalex_query", "dblp_query", "elsevier_query", "crossref_query",
    "openarchives_query", "pubmed_query", "osti_query", "scigov_query",
    "core_query", "plos_query", "openreview_query", "openaire_query",
]

# -- Primary sources previewed in the Step 1 query-transparency table ----------
PRIMARY_SOURCE_LABELS = [
    ("arXiv", "arxiv_query"),
    ("IEEE Xplore", "ieee_query"),
    ("Scopus (Elsevier)", "elsevier_query"),
    ("OpenAlex", "openalex_query"),
    ("Semantic Scholar", "semantic_scholar_query"),
    ("Springer Link", "springer_query"),
]

# -- Historical search window options -------------------------------------------
SEARCH_WINDOWS = {
    "recent": {
        "label": "Recent Advances (2024 - 2026)",
        "start_year": 2024,
        "end_year": 2026,
        "days": 730,
    },
    "standard": {
        "label": "Standard Comprehensive Review (2021 - 2026) [Recommended]",
        "start_year": 2021,
        "end_year": 2026,
        "days": 1825,
    },
    "retrospective": {
        "label": "Full Decade Retrospective (2015 - 2026)",
        "start_year": 2015,
        "end_year": 2026,
        "days": 4015,
    },
}

# -- AI execution strategy options ----------------------------------------------
EXECUTION_STRATEGIES = {
    "strict_local": {
        "label": "1. Local & Completely Private (Air-Gapped / Offline via Ollama)",
        "network": "strict_local",
        "cloud_fallback": "0",
    },
    "local_first": {
        "label": "2. Hybrid Cloud with Free Providers (Google Gemini / Groq / DeepSeek)",
        "network": "local_first",
        "cloud_fallback": "1",
    },
}

# -- Deterministic heuristic fallbacks ------------------------------------------
DEFAULT_META_PROMPT = (
    "Act as a Research Architect. Generate a flat JSON object with optimized "
    "search queries (keys like 'arxiv_query') and inclusion/exclusion criteria "
    "for the user's research goal. Do NOT nest the JSON."
)

_ai_manager = None

# ---------------------------------------------------------------------------
# -- Project root & configuration helpers --
# ---------------------------------------------------------------------------

def _project_root():
    """Return the absolute project root directory (parent of talos.py)."""
    return _P or os.getcwd()


def _load_config(project_root=None):
    """Load config.json (falling back to config.template.json) as a dict.

    Args:
        project_root (str, optional): Project root override for testing.

    Returns:
        tuple: (config_dict, config_path) -- config_path is the active file.
    """
    root = project_root or _project_root()
    path = os.path.join(root, "config.json")
    if not os.path.exists(path):
        path = os.path.join(root, "config.template.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f), path


def _save_config(config, path):
    """Persist the config dict back to disk with UTF-8 and readable indentation.

    Args:
        config (dict): The full configuration dictionary.
        path (str): Destination config.json path.
    """
    with open(path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)


# ---------------------------------------------------------------------------
# -- Local AI runtime probing & auto-spawn --
# ---------------------------------------------------------------------------

def _port_reachable(host, port, timeout=PROBE_TIMEOUT):
    """Return True when a TCP connection to host:port succeeds within timeout.

    Args:
        host (str): Target host (127.0.0.1).
        port (int): Target port.
        timeout (float): Connection timeout in seconds.

    Returns:
        bool: True when the port accepts a connection, False otherwise.
    """
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except (OSError, socket.timeout, socket.gaierror):
        return False


def _spawn_local_ai():
    """Silently attempt to spawn the local Ollama runtime in the background.

    Uses creationflags=CREATE_NO_WINDOW on Windows so no console flashes.
    Any failure is swallowed -- the caller falls back to heuristics.
    """
    try:
        flags = 0
        if os.name == "nt":
            flags = subprocess.CREATE_NO_WINDOW
        subprocess.Popen(
            ["ollama", "serve"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=flags,
        )
        logger.info("Attempted silent Ollama spawn.")
    except Exception as exc:  # noqa: BLE001 - best-effort background spawn
        logger.info("Ollama spawn unavailable: %s", exc)


def _ensure_local_ai_runtime():
    """Probe and, if necessary, auto-spawn the local AI runtime.

    The probe order is: Fast Edge (11435) first, then standard Ollama (11434).
    When both are offline, a silent spawn is attempted and a bounded 2-second
    wait begins. The function returns True as soon as any local endpoint is
    reachable, otherwise it logs the heuristic-bypass notice and returns False.

    Returns:
        bool: True for Active LLM mode, False for Heuristic Bypass mode.
    """
    # -- Fast probe of both local endpoints --
    if _port_reachable("127.0.0.1", EDGE_PORT, PROBE_TIMEOUT):
        logger.info("Fast Edge runtime reachable on port %s.", EDGE_PORT)
        return True
    if _port_reachable("127.0.0.1", OLLAMA_PORT, PROBE_TIMEOUT):
        logger.info("Ollama runtime reachable on port %s.", OLLAMA_PORT)
        return True

    # -- Offline: attempt a silent background spawn --
    _spawn_local_ai()

    # -- Bounded wait (up to 2.0s) for the spawned runtime --
    deadline = time.monotonic() + BOOTSTRAP_WAIT
    while time.monotonic() < deadline:
        if _port_reachable("127.0.0.1", EDGE_PORT, PROBE_TIMEOUT):
            logger.info("Fast Edge runtime came online after spawn.")
            return True
        if _port_reachable("127.0.0.1", OLLAMA_PORT, PROBE_TIMEOUT):
            logger.info("Ollama runtime came online after spawn.")
            return True
        time.sleep(0.2)

    # -- Still offline: engage deterministic heuristic validation --
    logger.info("Local AI servers offline. Engaging rule-based heuristic validation.")
    return False

# ---------------------------------------------------------------------------
# -- Cognitive scope validation (LLM with heuristic bypass) --
# ---------------------------------------------------------------------------

def _get_ai_manager():
    """Return a cached AIManager, skipping local model verification."""
    global _ai_manager
    if _ai_manager is None:
        os.environ.setdefault("TALOS_MODELS_VERIFIED", "1")
        config, _ = _load_config()
        from src.core.ai_manager import AIManager
        _ai_manager = AIManager(config)
    return _ai_manager


def _call_llm_text(prompt, timeout):
    """Run a text-mode LLM request inside a thread with a hard timeout.

    Args:
        prompt (str): The prompt to send to the Fast Edge tier.
        timeout (float): Maximum seconds to wait.

    Returns:
        str or None: The model text response, or None on timeout/failure.
    """
    def _work():
        try:
            return _get_ai_manager()._execute_request(
                prompt=prompt,
                model_type="fast",
                response_format="text",
                tier="fast",
            )
        except Exception:  # noqa: BLE001 - LLM failure degrades to heuristic
            return None

    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(_work)
        try:
            return future.result(timeout=timeout)
        except Exception:  # noqa: BLE001 - timeout or worker failure
            return None


def _analyze_scope_heuristic(topic):
    """Deterministically assess whether a topic is cognitively viable.

    A topic is viable when it contains at least MIN_WORDS whitespace-delimited
    words. Shorter inputs return too_brief=True with guidance.

    Args:
        topic (str): The researcher's natural-language topic.

    Returns:
        dict: {"too_brief": bool, "words": int, "message": str}.
    """
    topic = (topic or "").strip()
    words = topic.split()
    if len(words) < MIN_WORDS:
        return {
            "too_brief": True,
            "words": len(words),
            "message": (
                "The research focus is too brief (fewer than "
                f"{MIN_WORDS} words). Please describe the domain, the methods, "
                "and the target application, for example: 'spatio-temporal "
                "attention for cooperative multi-agent path planning'."
            ),
        }
    return {"too_brief": False, "words": len(words), "message": ""}


def _suggest_subdomains_heuristic(topic):
    """Return 2-3 standard sub-domain suggestions for a too-brief topic.

    Args:
        topic (str): The current (short) research topic.

    Returns:
        list: A list of 2-3 suggested sub-domain phrasings.
    """
    stem = (topic or "").strip() or "the research domain"
    return [
        f"{stem} for multi-agent coordination",
        f"{stem} with deep reinforcement learning",
        f"{stem} under resource constraints",
    ]


def _analyze_scope_with_llm(topic):
    """Use the Fast Edge model to assess scope and suggest sub-domains.

    Args:
        topic (str): The researcher's natural-language topic.

    Returns:
        dict or None: {"subdomains": [str, ...], "message": str} on success,
        or None when the LLM is unreachable (triggers heuristic bypass).
    """
    prompt = (
        "You are a research scope validator. Assess the following research "
        "topic. If it is too brief (fewer than 4 words), return exactly 2 or 3 "
        "specific academic sub-domain suggestions separated by a newline. "
        "Otherwise return the single word 'SUFFICIENT'. Respond in English "
        "only, no extra commentary.\n\nTopic: " + topic
    )
    result = _call_llm_text(prompt, LLM_SCOPE_TIMEOUT)
    if not result or not isinstance(result, str):
        return None
    text = result.strip()
    if text.upper().startswith("SUFFICIENT"):
        return {"subdomains": [], "message": ""}
    suggestions = [
        line.strip(" -•\t")
        for line in text.splitlines()
        if line.strip()
    ][:3]
    return {
        "subdomains": suggestions,
        "message": (
            "The Fast Edge model suggests the following sub-domains to "
            "sharpen your focus: " + "; ".join(suggestions)
        ),
    }

# ---------------------------------------------------------------------------
# -- Query & criteria generation (LLM with heuristic fallback) --
# ---------------------------------------------------------------------------

def _generate_queries_heuristic(topic, config):
    """Deterministically build 16 English queries and criteria from the topic.

    Args:
        topic (str): The validated research topic.
        config (dict): The active config dict (mutated in place).

    Returns:
        None: The config dict is updated with *_query, inclusion_criteria,
        and exclusion_criteria keys.
    """
    clean = " ".join((topic or "").split())
    boolean = "(" + " AND ".join(clean.split()) + ")"
    for key in SOURCE_QUERY_KEYS:
        if key == "ieee_query":
            config[key] = boolean
        else:
            config[key] = clean
    config["inclusion_criteria"] = (
        "Peer-reviewed studies directly addressing: " + clean
    )
    config["exclusion_criteria"] = (
        "Studies outside the scope of the stated research focus; duplicate "
        "records; non-English full texts; opinion pieces without empirical "
        "results."
    )
    config["active_focus_summary"] = clean


def _generate_queries_llm(topic, config):
    """Use the Research Architect (query_translator) to generate queries.

    Reuses src.ai.llm.query_translator.flatten_json to normalize the model
    output into flat config keys. Returns True on success, False on failure.

    Args:
        topic (str): The validated research topic.
        config (dict): The active config dict (mutated in place).

    Returns:
        bool: True when generation succeeded, False when it must fall back.
    """
    try:
        from src.ai.llm.query_translator import flatten_json
        meta_prompt = config.get("query_translator_prompt", DEFAULT_META_PROMPT)
        guidance = (
            "\n\n**REFERENCE TEMPLATE FOR PROMPTS (Keep JSON structure, "
            "change content):**\n" + config.get("phd_focus_system_prompt", "") +
            "\n\n**USER RESEARCH GOAL:**\n" + topic +
            "\n\nAlso produce two additional string fields: "
            "'inclusion_criteria' and 'exclusion_criteria'."
        )

        def _work():
            ai = _get_ai_manager()
            return ai.evaluate_paper_json(
                abstract=guidance,
                model_type="pro",
                system_prompt_override=meta_prompt,
            )

        raw = None
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(_work)
            try:
                raw = future.result(timeout=LLM_QUERY_TIMEOUT)
            except Exception:  # noqa: BLE001 - timeout/worker failure
                raw = None

        if not raw or not isinstance(raw, dict):
            return False

        generated = flatten_json(raw)
        count = 0
        for key, value in generated.items():
            if key in SOURCE_QUERY_KEYS or "criteria" in key or "prompt" in key:
                config[key] = value
                count += 1
        return count > 0
    except Exception as exc:  # noqa: BLE001 - LLM generation is best-effort
        logger.info("Query generation via LLM failed: %s", exc)
        return False

# ---------------------------------------------------------------------------
# -- Execution strategy & search window persistence --
# ---------------------------------------------------------------------------

def _update_env_key(env_path, key, value):
    """Safely write a key=value pair into the .env file without quotes.

    Args:
        env_path (str): Absolute path to the .env file.
        key (str): Environment variable name.
        value (str): Raw (unquoted) value to write.
    """
    try:
        set_key(env_path, key, value, quote_mode="never")
        load_dotenv(env_path, override=True)
        logger.info(".env updated: %s=%s", key, value)
    except Exception as exc:  # noqa: BLE001 - .env update is best-effort
        logger.warning("Could not update .env %s: %s", key, exc)


def _apply_execution_strategy(strategy_key, project_root=None):
    """Persist the chosen execution strategy into the active .env.

    Args:
        strategy_key (str): One of 'strict_local' or 'local_first'.
        project_root (str, optional): Project root override for testing.

    Returns:
        bool: True on success, False when the strategy key is unknown.
    """
    strategy = EXECUTION_STRATEGIES.get(strategy_key)
    if not strategy:
        return False
    root = project_root or _project_root()
    env_path = os.path.join(root, ".env")
    _update_env_key(env_path, "TALOS_NETWORK_STRATEGY", strategy["network"])
    _update_env_key(env_path, "TALOS_ALLOW_CLOUD_FALLBACK", strategy["cloud_fallback"])
    return True


def _write_search_window(config, path, strategy_key):
    """Store the selected historical search window in the active config.json.

    Args:
        config (dict): The active config dict (mutated in place).
        path (str): Destination config.json path.
        strategy_key (str): One of the SEARCH_WINDOWS keys.

    Returns:
        bool: True on success, False when the strategy key is unknown.
    """
    window = SEARCH_WINDOWS.get(strategy_key)
    if not window:
        return False
    config["research_search_window"] = strategy_key
    config["search_window_label"] = window["label"]
    config["search_window_start_year"] = window["start_year"]
    config["search_window_end_year"] = window["end_year"]
    config["days_to_search_historic"] = window["days"]
    _save_config(config, path)
    return True


# ---------------------------------------------------------------------------
# -- Sentinel (first-run marker) --
# ---------------------------------------------------------------------------

def _sentinel_path(project_root=None):
    """Return the absolute path to the onboarding sentinel file."""
    root = project_root or _project_root()
    return os.path.join(root, "data", SENTINEL_FILENAME)


def _sentinel_exists(project_root=None):
    """Return True when the onboarding sentinel file already exists."""
    return os.path.exists(_sentinel_path(project_root))


def _create_sentinel(project_root=None):
    """Create the onboarding sentinel file (data/.talos_onboarded)."""
    path = _sentinel_path(project_root)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write("TALOS onboarding complete (v5.12.1)\n")
    logger.info("Onboarding sentinel created: %s", path)

# ---------------------------------------------------------------------------
# -- First-flight test & visualizer bootstrap --
# ---------------------------------------------------------------------------

def _api_is_alive():
    """Return True when the TALOS FastAPI backend responds on port 8001."""
    return _port_reachable("127.0.0.1", API_PORT, PROBE_TIMEOUT)


def _ensure_api_server():
    """Spawn the FastAPI backend if it is not already listening.

    On Windows the server launches in a hidden background window. This mirrors
    the self-healing behaviour of src/utils/tray_icon.py.
    """
    if _api_is_alive():
        return True
    try:
        root = _project_root()
        command = [
            sys.executable, "-m", "uvicorn",
            "src.api.main_api:app", "--host", "127.0.0.1",
            "--port", str(API_PORT),
        ]
        flags = 0
        if os.name == "nt":
            flags = subprocess.CREATE_NO_WINDOW
        subprocess.Popen(
            command,
            cwd=root,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=flags,
        )
        logger.info("Auto-bootstrapped FastAPI server on port %s.", API_PORT)
        deadline = time.monotonic() + BOOTSTRAP_WAIT
        while time.monotonic() < deadline:
            if _api_is_alive():
                return True
            time.sleep(0.2)
        return False
    except Exception as exc:  # noqa: BLE001 - server bootstrap is best-effort
        logger.warning("FastAPI bootstrap failed: %s", exc)
        return False


def _trigger_test_search():
    """Trigger a lightweight 10-paper test search via the scrape endpoint."""
    try:
        import urllib.request
        request = urllib.request.Request(
            "http://127.0.0.1:8001/api/v1/scrape/trigger",
            data=b"{}",
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=5.0) as response:
            return response.status < 300
    except Exception as exc:  # noqa: BLE001 - search trigger is best-effort
        logger.warning("Test search trigger unavailable: %s", exc)
        return False


def _run_first_flight():
    """Auto-bootstrap the API, trigger a test search, and open the visualizer.

    Returns:
        bool: True when the visualizer URL was opened, False otherwise.
    """
    if not _ensure_api_server():
        console.print("[yellow]FastAPI backend could not be started; skipping "
                      "visualizer launch.[/yellow]")
        return False
    _trigger_test_search()
    webbrowser.open(VISUALIZER_URL)
    return True


# ---------------------------------------------------------------------------
# -- Visual header --
# ---------------------------------------------------------------------------

def _render_header():
    """Render the styled Rich welcome header for the wizard."""
    body = Text()
    body.append("TALOS Research Setup Wizard\n", style="bold bright_cyan")
    body.append(
        "This guide configures your research parameters in 4 simple steps. "
        "All menus, queries, and reports operate in professional academic "
        "English for full compatibility with the 16 academic APIs.\n",
        style="white",
    )
    body.append(
        "1. Research Topic & Cognitive Validation\n"
        "2. AI Execution Strategy\n"
        "3. Historical Search Window\n"
        "4. First Flight Test & Visualizer\n",
        style="dim cyan",
    )
    console.print(Panel(
        Align.center(body),
        title="[bold]TALOS v5.12.1[/bold]",
        border_style="#006699",
        padding=(1, 2),
    ))

# ---------------------------------------------------------------------------
# -- Interactive step drivers --
# ---------------------------------------------------------------------------

def _render_query_preview(config):
    """Render the compiled search-query transparency table and criteria.

    Displays the boolean query strings for the top primary academic sources in
    a rounded Rich Table, followed by a summary of the inclusion and exclusion
    criteria, so the researcher can review the exact parameters before they are
    persisted to config.json.

    Args:
        config (dict): The active config dict already populated with *_query,
            inclusion_criteria, and exclusion_criteria keys.
    """
    table = Table(
        title="Generated Academic Search Queries",
        box=box.ROUNDED,
        border_style="bright_cyan",
        show_lines=True,
        header_style="bold bright_cyan",
    )
    table.add_column("Source", style="bold cyan", width=22, no_wrap=True)
    table.add_column("Boolean Query String", style="white", overflow="fold")
    for label, key in PRIMARY_SOURCE_LABELS:
        table.add_row(label, str(config.get(key) or ""))
    console.print(table)

    criteria_body = Text()
    criteria_body.append(
        "[dim]Inclusion Criteria:[/dim] " +
        str(config.get("inclusion_criteria") or "") + "\n"
    )
    criteria_body.append(
        "[dim]Exclusion Criteria:[/dim] " +
        str(config.get("exclusion_criteria") or "")
    )
    console.print(Panel(
        criteria_body,
        title="[bold]Compiled Criteria[/bold]",
        border_style="cyan",
        padding=(1, 2),
    ))


def _step1_research_topic(active_llm, config, config_path):
    """Step 1: capture and validate the research topic, then generate queries.

    Args:
        active_llm (bool): True when a local AI runtime is reachable.
        config (dict): Active config dict (mutated in place).
        config_path (str): Destination config.json path.

    Returns:
        str or None: The validated topic, or None when the user cancels.
    """
    console.print(Panel(
        "Describe your research focus in natural language. TALOS will compile "
        "it into 16 English academic search queries plus inclusion and "
        "exclusion criteria.",
        title="[bold]Step 1 of 4: Research Topic[/bold]",
        border_style="cyan",
    ))
    while True:
        # -- Capture and validate the research topic --
        while True:
            topic = questionary.text(
                "Research focus (English preferred):",
                style=TALOS_QUESTIONARY_STYLE,
            ).ask()
            if topic is None:
                return None
            assessment = _analyze_scope_heuristic(topic)
            if not assessment["too_brief"]:
                break

            suggestions = []
            if active_llm:
                llm = _analyze_scope_with_llm(topic)
                if llm and llm.get("subdomains"):
                    suggestions = llm["subdomains"]
                    console.print("[yellow]" + llm["message"] + "[/yellow]")
            if not suggestions:
                suggestions = _suggest_subdomains_heuristic(topic)
                console.print("[yellow]" + assessment["message"] + "[/yellow]")
                console.print("[dim]Example directions:[/dim]")
                for suggestion in suggestions:
                    console.print("  [cyan]-[/cyan] " + suggestion)
            console.print("[dim]Please re-enter a more detailed focus.[/dim]\n")

        # -- Compile the 16 academic queries plus inclusion/exclusion criteria --
        console.print("[bold bright_cyan]Generating search queries and criteria...[/bold bright_cyan]")
        generated = False
        if active_llm:
            generated = _generate_queries_llm(topic, config)
            if generated:
                console.print("[green]Queries generated by the local Research Architect.[/green]")
        if not generated:
            _generate_queries_heuristic(topic, config)
            console.print("[yellow]Rule-based heuristic queries applied (offline mode).[/yellow]")

        # -- v5.12.1: query-transparency preview + user confirmation --
        _render_query_preview(config)
        proceed = questionary.confirm(
            "Proceed with these compiled search parameters?",
            default=True,
            style=TALOS_QUESTIONARY_STYLE,
        ).ask()
        if proceed is None:
            return None
        if proceed:
            _save_config(config, config_path)
            return topic
        console.print("\n[dim]Review declined. Re-entering research scope.[/dim]\n")


def _step2_execution_strategy(project_root):
    """Step 2: select and persist the AI execution strategy.

    Args:
        project_root (str): Project root for .env resolution.

    Returns:
        str or None: The chosen strategy key, or None on cancel.
    """
    console.print(Panel(
        "Choose how TALOS should execute AI inference. The Local & Completely "
        "Private option is fully air-gapped; Hybrid Cloud adds free cloud "
        "providers as a fallback.",
        title="[bold]Step 2 of 4: AI Execution Strategy[/bold]",
        border_style="cyan",
    ))
    choice = questionary.select(
        "Select your AI execution strategy:",
        choices=[s["label"] for s in EXECUTION_STRATEGIES.values()],
        style=TALOS_QUESTIONARY_STYLE,
    ).ask()
    if choice is None:
        return None
    for key, strategy in EXECUTION_STRATEGIES.items():
        if strategy["label"] == choice:
            _apply_execution_strategy(key, project_root)
            return key
    return None


def _step3_search_window(config, config_path):
    """Step 3: select and persist the historical search window.

    Args:
        config (dict): Active config dict (mutated in place).
        config_path (str): Destination config.json path.

    Returns:
        str or None: The chosen window key, or None on cancel.
    """
    console.print(Panel(
        "Select the publication window for your literature search. The "
        "Standard Comprehensive Review is recommended for a balanced review.",
        title="[bold]Step 3 of 4: Historical Search Window[/bold]",
        border_style="cyan",
    ))
    choice = questionary.select(
        "Select your historical search window:",
        choices=[w["label"] for w in SEARCH_WINDOWS.values()],
        style=TALOS_QUESTIONARY_STYLE,
    ).ask()
    if choice is None:
        return None
    for key, window in SEARCH_WINDOWS.items():
        if window["label"] == choice:
            _write_search_window(config, config_path, key)
            return key
    return None


def _step4_first_flight():
    """Step 4: optionally run a test search and open the 3D visualizer.

    Returns:
        bool: True when the visualizer was launched, False otherwise.
    """
    console.print(Panel(
        "Optionally run a 10-paper test search and open the 3D Knowledge "
        "Constellation Visualizer to confirm end-to-end ingestion.",
        title="[bold]Step 4 of 4: First Flight Test[/bold]",
        border_style="cyan",
    ))
    run_test = questionary.confirm(
        "Run a 10-paper test search and open the 3D visualizer?",
        default=False,
        style=TALOS_QUESTIONARY_STYLE,
    ).ask()
    if run_test:
        return _run_first_flight()
    return False

def _render_summary(topic, strategy_key, window_key, first_flight):
    """Render the final academic summary panel."""
    strategy_label = EXECUTION_STRATEGIES.get(strategy_key, {}).get(
        "label", strategy_key or "N/A")
    window_label = SEARCH_WINDOWS.get(window_key, {}).get(
        "label", window_key or "N/A")
    body = Text()
    body.append("[dim]Research Topic:[/dim] " + (topic or "N/A") + "\n")
    body.append("[dim]Execution Strategy:[/dim] " + strategy_label + "\n")
    body.append("[dim]Search Window:[/dim] " + window_label + "\n")
    body.append("[dim]First Flight:[/dim] " +
                ("[green]LAUNCHED[/green]" if first_flight else "[yellow]SKIPPED[/yellow]") + "\n\n")
    body.append(
        "[dim]TALOS is now configured. Run a Daily Search or start the "
        "Autonomous Research Service to begin discovery.[/dim]",
        style="white",
    )
    console.print(Panel(
        Align.center(body),
        title="[bold]SETUP COMPLETE[/bold]",
        border_style="green",
        padding=(1, 2),
    ))


def main():
    """Orchestrate the 4-step research setup wizard end to end."""
    _render_header()
    project_root = _project_root()
    config, config_path = _load_config(project_root)

    active_llm = _ensure_local_ai_runtime()
    if active_llm:
        console.print("[green]Local AI runtime online -- Active LLM mode.[/green]\n")
    else:
        console.print("[yellow]Local AI offline -- Heuristic Bypass mode.[/yellow]\n")

    topic = _step1_research_topic(active_llm, config, config_path)
    if topic is None:
        console.print("[dim]Setup cancelled. No changes were persisted.[/dim]")
        return

    strategy_key = _step2_execution_strategy(project_root)
    window_key = _step3_search_window(config, config_path)
    first_flight = _step4_first_flight()

    _create_sentinel(project_root)
    _render_summary(topic, strategy_key, window_key, first_flight)


if __name__ == "__main__":
    # Top-level guard: a stray Ctrl+C exits cleanly without a traceback.
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n\n[dim]Setup cancelled by user.[/dim]\n")
        sys.exit(0)








