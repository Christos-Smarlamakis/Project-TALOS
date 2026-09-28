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
Project: TALOS v5.15.1
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
      is 100% compatible with the 18 academic ingestion APIs.
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
    - Heuristic stopword filter (v5.12.2): the offline rule-based query
      generator strips English stopwords and punctuation noise via
      _extract_salient_terms so fallback boolean queries for IEEE Xplore,
      Scopus, and arXiv produce valid, executable Boolean syntax.
    - English-first cognitive mandate (v5.12.2): the LLM query/criteria
      generation prompt enforces a strict formal-English language mandate plus
      Boolean syntax constraints (no 'topic:' prefixes) and rigorous
      inclusion/exclusion criteria formatting.
    - 5-strategy execution matrix (v5.12.2): Step 2 now offers the full
      five-tier hierarchy (strict_local, local_first, cloud_first,
      strict_cloud, auto_dynamic) persisted to config.json under
      'ai_execution_strategy'.
    - Step 0 profile target gate (v5.12.4): a pre-flight selection step lets
      the researcher reconfigure the current active profile, switch to an
      existing isolated profile, or instantiate a fresh isolated workspace
      under _profiles/<name>/ before Steps 1-4 execute.

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
import re
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

# -- v5.12.2: English stopwords excluded from heuristic boolean query chains --
# -- Joining these words with AND yields invalid, zero-hit queries on IEEE --
# -- Xplore, Scopus, and arXiv. They are stripped by _extract_salient_terms. --
STOPWORDS = {
    "for", "with", "and", "to", "in", "on", "of", "by", "a", "an", "the",
    "at", "or", "is", "are", "using", "based", "into", "from", "that",
    "this", "these", "those", "their", "its", "via", "as", "be", "was",
    "were", "within", "towards", "toward", "between", "among", "through",
}

# -- v5.12.4: Step 0 profile target gate constants ----------------------------
PROFILES_DIRNAME = "_profiles"
ACTIVE_PROFILE_FILENAME = "active_profile.txt"
PROFILE_NAME_RE = re.compile(r"^[A-Za-z0-9_][A-Za-z0-9_-]*$")

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
    "rapid_30": {
        "label": "1. Rapid Reconnaissance: Last 30 Days (30 days) — Latest preprints & urgent breakthroughs",
        "days": 30,
    },
    "annual_365": {
        "label": "2. Annual Snapshot: Last 1 Year (365 days) — Recent SOTA algorithms & benchmarks",
        "days": 365,
    },
    "phd_1095": {
        "label": "3. Standard PhD Scoping Window: Last 3 Years (1,095 days) — Recommended for Chapter 2",
        "days": 1095,
    },
    "prisma_1825": {
        "label": "4. Comprehensive PRISMA-ScR: Last 5 Years (1,825 days) — Complete state-of-the-art coverage",
        "days": 1825,
    },
    "decadal_3650": {
        "label": "5. Decadal Archive: Last 10 Years (3,650 days) — Foundational & longitudinal analysis",
        "days": 3650,
    },
}

# -- AI execution strategy options ----------------------------------------------
EXECUTION_STRATEGIES = {
    "strict_local": {
        "label": "1. Strict Local (Only Local - 100% Air-Gapped / Offline via Ollama)",
        "network": "strict_local",
        "cloud_fallback": "0",
    },
    "local_first": {
        "label": "2. Local-First (Local GPU priority, Cloud Fallback on failure/OOM)",
        "network": "local_first",
        "cloud_fallback": "1",
    },
    "cloud_first": {
        "label": "3. Cloud-First (Cloud priority, Local Fallback on network failure)",
        "network": "cloud_first",
        "cloud_fallback": "1",
    },
    "strict_cloud": {
        "label": "4. Strict Cloud (Only Cloud - 0% GPU VRAM footprint, leaves GPU free for PhD training)",
        "network": "strict_cloud",
        "cloud_fallback": "1",
    },
    "auto_dynamic": {
        "label": "5. Autonomous 2D Matrix (auto_dynamic - adaptive real-time routing based on VRAM & task complexity)",
        "network": "auto_dynamic",
        "cloud_fallback": "1",
    },
}

# -- Deterministic heuristic fallbacks ------------------------------------------
DEFAULT_META_PROMPT = (
    "Act as a Research Architect. Generate a flat JSON object with optimized "
    "search queries (keys like 'arxiv_query') and inclusion/exclusion criteria "
    "for the user's research goal. Do NOT nest the JSON."
)

# -- v5.12.2: strict English-first cognitive generation mandate ----------------
# Appended to the LLM query/criteria generation prompt so the compiled queries
# and criteria are always formal academic English with valid, executable
# Boolean syntax (no 'topic:' prefixes, no locale leakage).
LANGUAGE_AND_SYNTAX_MANDATE = (
    "\n\n**LANGUAGE MANDATE:** Output ALL criteria (inclusion_criteria, "
    "exclusion_criteria) and all search queries strictly in formal academic "
    "English. NEVER use Greek or any other language, regardless of user locale.\n\n"
    "**SYNTAX CONSTRAINTS:**\n"
    "- Do NOT invent or use non-standard prefixes such as 'topic:'.\n"
    "- For arXiv: Use standard title/abstract keywords or pure search terms "
    "without fake tags.\n"
    "- For IEEE Xplore: Use standard Boolean syntax with double quotes for exact "
    "phrases (e.g. (\"cooperative mission planning\" AND \"UAV swarms\")). Do NOT "
    "output 'topic:'.\n"
    "- For Scopus, OpenAlex, Semantic Scholar, Springer Link: Output standard "
    "Boolean keyword queries.\n\n"
    "**CRITERIA SPECIFICATION:**\n"
    "- inclusion_criteria: Clear, rigorous academic sentence in English defining "
    "peer-reviewed scope, primary methodologies, and domain context.\n"
    "- exclusion_criteria: Clear, rigorous academic sentence in English defining "
    "out-of-scope fields, non-empirical work, pre-prints without validation, or "
    "duplicate studies."
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
# -- v5.12.4: Step 0 profile target gate helpers --
# ---------------------------------------------------------------------------

def _profiles_dir(project_root=None):
    """Return the absolute canonical _profiles directory for a project root.

    Anchored to the repository root (the directory containing talos.py) so the
    wizard operates on the same profile namespace as the database manager's
    get_active_profile_db_path() resolver.

    Args:
        project_root (str, optional): Project root override for testing.

    Returns:
        str: Absolute path to the _profiles directory.
    """
    root = project_root or _project_root()
    return os.path.join(root, PROFILES_DIRNAME)


def _active_profile_file(project_root=None):
    """Return the absolute path to the active-profile marker file.

    Args:
        project_root (str, optional): Project root override for testing.

    Returns:
        str: Absolute path to _profiles/active_profile.txt.
    """
    return os.path.join(_profiles_dir(project_root), ACTIVE_PROFILE_FILENAME)


def _list_profiles(project_root=None):
    """List the names of every existing research profile.

    Only directory entries under _profiles are considered profiles; the
    active_profile.txt marker and any stray files are ignored.

    Args:
        project_root (str, optional): Project root override for testing.

    Returns:
        list[str]: Sorted profile directory names (may be empty).
    """
    profiles_dir = _profiles_dir(project_root)
    if not os.path.isdir(profiles_dir):
        return []
    names = []
    for entry in os.listdir(profiles_dir):
        if os.path.isdir(os.path.join(profiles_dir, entry)):
            names.append(entry)
    return sorted(names)


def _get_active_profile(project_root=None):
    """Return the currently active profile name, defaulting to 'default'.

    Creates the _profiles directory and the marker file on first run so the
    return value is always a concrete, usable profile name.

    Args:
        project_root (str, optional): Project root override for testing.

    Returns:
        str: The active profile name (never empty).
    """
    profiles_dir = _profiles_dir(project_root)
    os.makedirs(profiles_dir, exist_ok=True)
    marker = _active_profile_file(project_root)
    if os.path.exists(marker):
        try:
            with open(marker, "r", encoding="utf-8") as f:
                name = f.read().strip()
            if name:
                return name
        except OSError:
            pass
    _set_active_profile(project_root, "default")
    return "default"


def _set_active_profile(project_root, name):
    """Persist the given profile name as the active profile.

    Args:
        project_root (str): Project root (directory containing talos.py).
        name (str): The profile name to activate.
    """
    profiles_dir = _profiles_dir(project_root)
    os.makedirs(profiles_dir, exist_ok=True)
    with open(_active_profile_file(project_root), "w", encoding="utf-8") as f:
        f.write(name)


def _validate_profile_name(name):
    """Validate a proposed profile name for filesystem safety.

    Accepts alphanumeric names optionally containing underscores or hyphens
    after the first character. Spaces and path separators are rejected.

    Args:
        name (str): The raw proposed profile name.

    Returns:
        bool: True when the name is a safe single path component.
    """
    return bool(name) and bool(PROFILE_NAME_RE.match((name or "").strip()))


def _seed_profile_config(project_root, name):
    """Seed a new profile directory with an isolated config.json.

    Copies the current root config.json (falling back to config.template.json)
    into _profiles/<name>/config.json. No database file is copied: a fresh
    talos_research.db is created lazily by DatabaseManager on first use.

    Args:
        project_root (str): Project root (directory containing talos.py).
        name (str): The profile name to seed.

    Returns:
        str: Absolute path to the seeded profile config.json.
    """
    profile_dir = os.path.join(_profiles_dir(project_root), name)
    os.makedirs(profile_dir, exist_ok=True)
    src = os.path.join(project_root, "config.json")
    if not os.path.exists(src):
        src = os.path.join(project_root, "config.template.json")
    dst = os.path.join(profile_dir, "config.json")
    if os.path.exists(src):
        with open(src, "r", encoding="utf-8") as f_in:
            data = f_in.read()
    else:
        data = json.dumps({})
    with open(dst, "w", encoding="utf-8") as f_out:
        f_out.write(data)
    return dst


def _load_profile_config_to_root(project_root, name):
    """Activate a profile by copying its config.json into the root workspace.

    This mirrors the profile manager's swap model: the root config.json is the
    active working copy consumed by the wizard and daily_search.py, while the
    per-profile config lives under _profiles/<name>/config.json.

    Args:
        project_root (str): Project root (directory containing talos.py).
        name (str): The profile name to activate.
    """
    src = os.path.join(_profiles_dir(project_root), name, "config.json")
    dst = os.path.join(project_root, "config.json")
    if os.path.exists(src):
        with open(src, "r", encoding="utf-8") as f_in:
            data = f_in.read()
        with open(dst, "w", encoding="utf-8") as f_out:
            f_out.write(data)


def _persist_active_config(project_root, name):
    """Persist the root config.json back into the active profile directory.

    Called after successful onboarding so the isolated workspace retains the
    researcher's final query, criteria, and strategy configuration.

    Args:
        project_root (str): Project root (directory containing talos.py).
        name (str): The active profile name to persist to.
    """
    src = os.path.join(project_root, "config.json")
    if not os.path.exists(src):
        return
    profile_dir = os.path.join(_profiles_dir(project_root), name)
    os.makedirs(profile_dir, exist_ok=True)
    with open(src, "r", encoding="utf-8") as f_in:
        data = f_in.read()
    with open(os.path.join(profile_dir, "config.json"), "w", encoding="utf-8") as f_out:
        f_out.write(data)


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

def _extract_salient_terms(topic, max_terms=6):
    """Extract up to max_terms salient tokens/phrases from a research topic.

    Strips stopwords and punctuation noise (unbalanced parentheses, stray
    hyphens), preserves hyphenated compound terms (e.g. ``spatio-temporal``),
    deduplicates in original order, and caps the result so fallback boolean
    queries remain executable and return records instead of zero hits.

    Args:
        topic (str): The raw research topic text.
        max_terms (int): Maximum number of salient terms to return (4-6).

    Returns:
        list[str]: The salient terms in original order.
    """
    if not topic:
        return []
    text = " ".join((topic or "").split())
    tokens = re.findall(r"[A-Za-z0-9]+(?:-[A-Za-z0-9]+)*", text)
    salient = []
    seen = set()
    for token in tokens:
        lower = token.lower()
        if lower in STOPWORDS:
            continue
        if len(token) < 2:
            continue
        if lower not in seen:
            seen.add(lower)
            salient.append(token)
        if len(salient) >= max_terms:
            break
    return salient


def _generate_queries_heuristic(topic, config):
    """Deterministically build 16 English queries and criteria from the topic.

    v5.12.2: the boolean query chains only salient (non-stopword) tokens via
    _extract_salient_terms so IEEE Xplore, Scopus, and arXiv fallback queries
    produce valid, executable Boolean syntax that returns records rather than
    zero hits from stopword-laden AND chains.

    Args:
        topic (str): The validated research topic.
        config (dict): The active config dict (mutated in place).

    Returns:
        None: The config dict is updated with *_query, inclusion_criteria,
        and exclusion_criteria keys.
    """
    clean = " ".join((topic or "").split())
    salient = _extract_salient_terms(topic)
    # -- v5.12.2: heuristic stopword cleaner -- when salient terms survive the
    # -- filter they drive the queries; otherwise we fall back to the raw topic
    # -- so an all-stopword input still produces a non-empty, runnable query. --
    boolean = "(" + " AND ".join(salient) + ")" if salient else "(" + clean + ")"
    plain = " ".join(salient) if salient else clean
    for key in SOURCE_QUERY_KEYS:
        if key == "ieee_query":
            config[key] = boolean
        else:
            config[key] = plain
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
            "'inclusion_criteria' and 'exclusion_criteria'." +
            LANGUAGE_AND_SYNTAX_MANDATE
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
    """Persist the chosen execution strategy into .env and config.json.

    Writes the canonical strategy string to config.json under
    'ai_execution_strategy' and maps it onto the .env keys
    TALOS_NETWORK_STRATEGY and TALOS_ALLOW_CLOUD_FALLBACK.

    Args:
        strategy_key (str): One of the five EXECUTION_STRATEGIES keys.
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

    # -- v5.12.2: persist the canonical strategy key into config.json. --
    # -- Wrapped defensively so isolated test fixtures (no config.json) --
    # -- still exercise the .env path without erroring. --
    try:
        config, config_path = _load_config(root)
        config["ai_execution_strategy"] = strategy_key
        _save_config(config, config_path)
    except Exception:
        pass

    return True


def _write_search_window(config, path, strategy_key, days=None):
    """Store the selected historical search window in the active config.json.

    For preset windows the day count is read from SEARCH_WINDOWS; for a custom
    window an explicit ``days`` value is required and validated.

    Args:
        config (dict): The active config dict (mutated in place).
        path (str): Destination config.json path.
        strategy_key (str): One of the SEARCH_WINDOWS keys, or 'custom'.
        days (int, optional): Explicit day count for the custom window.

    Returns:
        bool: True on success, False when the key is unknown or days is invalid.
    """
    if strategy_key == "custom":
        if not isinstance(days, int) or days <= 0:
            return False
        label = f"Custom Days Window ({days} days)"
    else:
        window = SEARCH_WINDOWS.get(strategy_key)
        if not window:
            return False
        days = window["days"]
        label = window["label"]
    config["research_search_window"] = strategy_key
    config["search_window_label"] = label
    config["days_to_search_historic"] = days
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
        f.write("TALOS onboarding complete (v5.15.1)\n")
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
# -- v5.12.4: Step 0 profile target gate --
# ---------------------------------------------------------------------------

def _step0_profile_selection(project_root):
    """Step 0: select the target research profile before any configuration.

    Offers three mutually exclusive paths:
      1. Reconfigure the current active profile in place (no delay).
      2. Switch to an existing isolated profile and load its config.
      3. Create a brand-new isolated profile under _profiles/<name>/.

    Args:
        project_root (str): Project root (directory containing talos.py).

    Returns:
        str or None: The target profile name, or None when the user cancels.
    """
    current = _get_active_profile(project_root)
    existing = _list_profiles(project_root)

    console.print(Panel(
        "TALOS isolates every research effort into its own profile. Each profile "
        "owns a dedicated config.json and a fresh talos_research.db so parallel "
        "research tracks never contaminate one another.",
        title="[bold]Step 0 of 4: Profile Target Selection[/bold]",
        border_style="#006699",
    ))

    choice = questionary.select(
        "Select target profile for this research setup:",
        choices=[
            "1. Current Active Profile: [" + current + "] (Reconfigure existing workspace)",
            "2. Switch to an existing profile...",
            "3. Create a NEW isolated profile (e.g. 'uav_mission_planning', 'phd_chapter2')",
        ],
        style=TALOS_QUESTIONARY_STYLE,
    ).ask()
    if choice is None:
        return None

    # -- Option 1: keep the current active profile, proceed immediately. --
    if choice.startswith("1."):
        return current

    # -- Option 2: switch to an existing isolated profile. --
    if choice.startswith("2."):
        if not existing:
            console.print("[yellow]No existing profiles found. Create one with "
                          "option 3, or stay on the current profile.[/yellow]")
            return _step0_profile_selection(project_root)
        selected = questionary.select(
            "Select an existing profile to activate:",
            choices=existing,
            style=TALOS_QUESTIONARY_STYLE,
        ).ask()
        if selected is None:
            return None
        _set_active_profile(project_root, selected)
        _load_profile_config_to_root(project_root, selected)
        console.print(f"[green]Switched to profile: {selected}[/green]")
        return selected

    # -- Option 3: create a new isolated profile. --
    while True:
        raw = questionary.text(
            "Enter a name for the new isolated profile (letters, digits, "
            "underscores; e.g. 'uav_mission_planning'):",
            style=TALOS_QUESTIONARY_STYLE,
        ).ask()
        if raw is None:
            return None
        name = (raw or "").strip().replace(" ", "_")
        if not _validate_profile_name(name):
            console.print("[yellow]Invalid profile name. Use only letters, "
                          "digits, underscores, or hyphens (no spaces).[/yellow]")
            continue
        if name in _list_profiles(project_root):
            console.print(f"[yellow]Profile '{name}' already exists. Choose "
                          "another name.[/yellow]")
            continue
        _seed_profile_config(project_root, name)
        _set_active_profile(project_root, name)
        _load_profile_config_to_root(project_root, name)
        console.print(f"[green]Created and activated new profile: {name}[/green]")
        return name


# ---------------------------------------------------------------------------
# -- Visual header --
# ---------------------------------------------------------------------------

def _render_header(target_profile=None):
    """Render the styled Rich welcome header for the wizard.

    Args:
        target_profile (str, optional): The target profile name to display.
    """
    body = Text()
    body.append("TALOS Research Setup Wizard\n", style="bold bright_cyan")
    body.append(
        "This guide configures your research parameters in 4 simple steps. "
        "All menus, queries, and reports operate in professional academic "
        "English for full compatibility with the 18 academic APIs.\n",
        style="white",
    )
    body.append(
        "0. Profile Target Selection\n"
        "1. Research Topic & Cognitive Validation\n"
        "2. AI Execution Strategy\n"
        "3. Historical Search Window\n"
        "4. First Flight Test & Visualizer\n",
        style="dim cyan",
    )
    if target_profile:
        body.append("\nTarget Profile: ", style="dim")
        body.append(f"[{target_profile}]", style="bold green")
    console.print(Panel(
        Align.center(body),
        title="[bold]TALOS v5.15.1[/bold]",
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

        # -- Compile the 18 academic queries plus inclusion/exclusion criteria --
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
        "Select how TALOS routes AI inference between your local GPU (Ollama) "
        "and the external cloud mesh. Strict Local is 100% air-gapped with zero "
        "cloud egress; Strict Cloud leaves the GPU VRAM footprint at 0% for "
        "concurrent PhD training; Local-First and Cloud-First set the primary "
        "tier with automatic fallback; the Autonomous 2D Matrix adapts routing "
        "in real time from detected VRAM and task complexity.",
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


def _prompt_custom_days():
    """Prompt for and validate a custom search-window day count.

    Returns:
        int or None: The validated positive day count, or None on cancel.
    """
    while True:
        raw = questionary.text(
            "Enter the number of days back to search from today "
            "(e.g. 730 for 2 years, 1825 for 5 years):",
            style=TALOS_QUESTIONARY_STYLE,
        ).ask()
        if raw is None:
            return None
        raw = (raw or "").strip()
        if raw.isdigit() and int(raw) > 0:
            return int(raw)
        console.print("[yellow]Please enter a positive whole number of days.[/yellow]")


def _step3_search_window(config, config_path):
    """Step 3: select and persist the historical search window (in days).

    Args:
        config (dict): Active config dict (mutated in place).
        config_path (str): Destination config.json path.

    Returns:
        str or None: The chosen window key, or None on cancel.
    """
    console.print(Panel(
        "Select the publication window for your literature search. Each option "
        "is measured in days back from today; shorter windows surface the "
        "latest preprints while longer windows capture foundational work.",
        title="[bold]Step 3 of 4: Historical Search Window[/bold]",
        border_style="cyan",
    ))
    choices = [w["label"] for w in SEARCH_WINDOWS.values()]
    choices.append("6. Custom Days Window — Enter an explicit number of days")
    choice = questionary.select(
        "Select your historical publication search window (measured in days from today):",
        choices=choices,
        style=TALOS_QUESTIONARY_STYLE,
    ).ask()
    if choice is None:
        return None

    # -- Custom days window: prompt and validate a positive integer. --
    if "Custom Days Window" in (choice or ""):
        days = _prompt_custom_days()
        if days is None:
            return None
        _write_search_window(config, config_path, "custom", days)
        return "custom"

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
    if run_test is None:
        return None
    if run_test:
        return _run_first_flight()
    return False

def _render_summary(topic, strategy_key, window_key, first_flight, config=None):
    """Render the final academic summary panel."""
    strategy_label = EXECUTION_STRATEGIES.get(strategy_key, {}).get(
        "label", strategy_key or "N/A")
    window_label = None
    if config:
        window_label = config.get("search_window_label")
    if not window_label:
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


def _render_cancelled():
    """Print the clean cancellation panel and exit without persisting anything.

    Called whenever the user cancels (None or KeyboardInterrupt) in any step,
    so no config.json writes, 'N/A' placeholders, or sentinel creation occur.
    """
    console.print(Panel(
        "[yellow]Setup cancelled by user. Configuration was not altered.[/yellow]",
        title="[bold]CANCELLED[/bold]",
        border_style="yellow",
    ))
    sys.exit(0)


def main():
    """Orchestrate the research setup wizard (Step 0 gate + Steps 1-4)."""
    project_root = _project_root()

    # -- v5.12.4: Step 0 profile target gate runs before any configuration. --
    target_profile = _step0_profile_selection(project_root)
    if target_profile is None:
        _render_cancelled()

    _render_header(target_profile)
    config, config_path = _load_config(project_root)

    active_llm = _ensure_local_ai_runtime()
    if active_llm:
        console.print("[green]Local AI runtime online -- Active LLM mode.[/green]\n")
    else:
        console.print("[yellow]Local AI offline -- Heuristic Bypass mode.[/yellow]\n")

    # -- Cancellation integrity: any step returning None aborts the whole flow
    # -- before any config.json writes, 'N/A' placeholders, or sentinel file. --
    topic = _step1_research_topic(active_llm, config, config_path)
    if topic is None:
        _render_cancelled()

    strategy_key = _step2_execution_strategy(project_root)
    if strategy_key is None:
        _render_cancelled()

    window_key = _step3_search_window(config, config_path)
    if window_key is None:
        _render_cancelled()

    first_flight = _step4_first_flight()
    if first_flight is None:
        _render_cancelled()

    _create_sentinel(project_root)
    _persist_active_config(project_root, target_profile)
    _render_summary(topic, strategy_key, window_key, first_flight, config)


if __name__ == "__main__":
    # Top-level guard: a stray Ctrl+C exits cleanly without a traceback.
    try:
        main()
    except KeyboardInterrupt:
        _render_cancelled()








