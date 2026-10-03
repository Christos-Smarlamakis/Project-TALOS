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
Module: historic_search.py (v5.19.0 - Unified Hierarchical Historical Harvester)
Project: TALOS v5.19.0

Description:
    The deep archive search orchestrator. Fetches papers from all 18 configured
    source agents spanning a multi-year window (configurable via
    ``days_to_search_historic``, default ~6 years), deduplicates by DOI/URL,
    and evaluates all new papers with the Flash model using Quad-Layer scoring.
    Designed for initial database population and periodic deep dives.
    Respects API call limits and rate delays to avoid quota exhaustion.
"""
import sys
import os, sys
_P = os.path.abspath(os.path.dirname(__file__))
while _P and not os.path.exists(os.path.join(_P, 'talos.py')):
    _P = os.path.dirname(_P)
if _P: sys.path.insert(0, _P)
import os
import time
import json
import requests
import threading
from dotenv import load_dotenv
import argparse
import re
import io
import hashlib
import logging
from contextlib import redirect_stdout
from concurrent.futures import ThreadPoolExecutor, as_completed

from src.ingestion.sources import SOURCE_REGISTRY, ALL_SOURCE_NAMES
from src.ingestion.resilient_gateway import ResilientIngestionGateway

from src.core.database_manager import DatabaseManager
from src.core.ai_manager import AIManager
from src.core.hierarchical_evaluator import HierarchicalEvaluationEngine
from src.ai.drl.llm_router_subagent import estimate_prompt_tokens
from src.integration.visualizer_bridge import push_visualizer_event
from rich.console import Console
from rich.panel import Panel
from rich import box
from rich.live import Live
from rich.table import Table


# -- Module-level logger (v5.13.0) used by the concurrent harvest workers. --
logger = logging.getLogger(__name__)


# -- v5.15.0: Canonical 18-source registry is unified in
# src/ingestion/sources/__init__.py and imported above. --


# -- v5.10.11: Live visualizer telemetry helpers (non-blocking HTTP POST) --
_VISUALIZER_EVENTS_URL = "http://127.0.0.1:8001/api/v1/visualizer/events"
_SOURCE_KEY_BY_CLASS = {cls: name for name, cls in SOURCE_REGISTRY}


def _source_key(source) -> str:
    """Resolve the canonical lowercase slug for an instantiated source agent."""
    return _SOURCE_KEY_BY_CLASS.get(type(source), type(source).__name__.lower())


def _source_query(source) -> str:
    """Return a human-readable query string for a source agent."""
    query = getattr(source, "query", None)
    if query:
        return str(query)
    terms = getattr(source, "search_terms", None)
    if isinstance(terms, (list, tuple)):
        return " OR ".join(str(t) for t in terms)
    return ""


def _emit_visualizer_event(event_type: str, payload: dict) -> None:
    """Fire-and-forget POST to the live visualizer events endpoint.

    Runs in a daemon thread so a slow or offline API server never blocks the
    ingestion pipeline. Failures are swallowed (best-effort telemetry).
    """
    def _post():
        try:
            requests.post(
                _VISUALIZER_EVENTS_URL,
                json={"event_type": event_type, "payload": payload},
                timeout=0.2,
            )
        except Exception:
            pass
    try:
        threading.Thread(target=_post, daemon=True).start()
    except Exception:
        pass


def _normalize_title(title):
    """Normalize a paper title into a canonical, punctuation-free string.

    Lowercases, collapses whitespace, and removes non-alphanumeric characters
    so equivalent titles from different providers hash identically.

    Args:
        title (str): The raw paper title.

    Returns:
        str: The normalized title (empty string for a missing title).
    """
    if not title:
        return ""
    text = " ".join(str(title).lower().split())
    return re.sub(r"[^a-z0-9 ]", "", text)


def _title_hash(title):
    """Return a stable SHA-1 hex digest for a normalized paper title.

    Args:
        title (str): The raw paper title.

    Returns:
        str: Hexadecimal digest used as the deduplication fallback key.
    """
    return hashlib.sha1(_normalize_title(title).encode("utf-8")).hexdigest()


def _deduplicate_papers(papers):
    """Deduplicate raw papers by DOI, falling back to a normalized title hash.

    Papers with a DOI are keyed by DOI; DOI-less papers are keyed by their
    normalized title hash so cross-source duplicates with no DOI still collapse
    to a single record. First-seen order is preserved.

    Args:
        papers (list of dict): Raw standardized paper dictionaries.

    Returns:
        list of dict: Unique papers preserving first-seen order.
    """
    unique = {}
    seen_titles = set()
    for paper in papers:
        doi = (paper.get("doi") or "").strip()
        if doi:
            if doi not in unique:
                unique[doi] = paper
            continue
        title = paper.get("title") or ""
        digest = _title_hash(title)
        if digest not in seen_titles:
            seen_titles.add(digest)
            unique["title:" + digest] = paper
    return list(unique.values())


def _harvest_single_source(source, source_key, query, criteria, date_limit):
    """Harvest one source agent in a dedicated worker thread.

    Routes the fetch through ``ResilientIngestionGateway`` so every one of the
    18 sources inherits self-healing: authentication / quota errors fast-fail
    without delayed retries and -- for IEEE, Elsevier, and Springer -- are
    transparently mirrored through OpenAlex. The gateway also captures stdout
    in-process so interleaved prints do not corrupt the Rich Live telemetry
    table.

    Args:
        source (object): Instantiated source agent exposing fetch_new_papers().
        source_key (str): Canonical lowercase slug for the source.
        query (str): Human-readable query string (telemetry only).
        criteria (str): Inclusion criteria from config (telemetry only).
        date_limit (int): Historical search window in days (telemetry only).

    Returns:
        dict: {'source', 'status', 'papers', 'error', 'elapsed'}.
    """
    started = time.time()
    _emit_visualizer_event("source_searching", {"source": source_key, "query": query})
    gateway = ResilientIngestionGateway()
    papers = gateway.harvest_source(
        source, query=query, criteria=criteria, date_limit=date_limit,
        source_key=source_key)
    elapsed = time.time() - started

    if gateway.last_recovered:
        _emit_visualizer_event("source_status", {
            "source": source_key, "status": "recovered", "count": len(papers),
        })
        return {
            "source": source_key, "status": "COMPLETED",
            "papers": papers, "error": None, "elapsed": elapsed,
        }
    if papers:
        _emit_visualizer_event("source_status", {
            "source": source_key, "status": "healthy", "count": len(papers),
        })
        return {
            "source": source_key, "status": "COMPLETED",
            "papers": papers, "error": None, "elapsed": elapsed,
        }
    if gateway.last_error:
        logger.error("Error fetching from %s: %s. Skipping source.",
                     type(source).__name__, gateway.last_error)
        _emit_visualizer_event("source_status", {
            "source": source_key, "status": "error", "message": gateway.last_error,
        })
        return {
            "source": source_key, "status": "FAILED",
            "papers": [], "error": gateway.last_error, "elapsed": elapsed,
        }
    logger.info("No new papers from %s", type(source).__name__)
    return {
        "source": source_key, "status": "COMPLETED",
        "papers": [], "error": None, "elapsed": elapsed,
    }


# -- v5.10.3: LLM Router Sub-Agent (two-stage provider selection) --
def route_evaluation_provider(ai_manager, content, task_type="default"):
    """Query the LLMRouterSubAgent for the optimal provider for an evaluation.

    Args:
        ai_manager (AIManager): AI manager exposing a ``router`` sub-agent.
        content (str): The title + abstract prompt text.
        task_type (str): Router task modifier key (``fast_screening`` or
            ``deep_research``).

    Returns:
        str | None: The selected provider name, or None when no router exists.
    """
    router = getattr(ai_manager, "router", None)
    if router is None:
        return None
    prompt_length = estimate_prompt_tokens(content)
    chosen = router.select_provider(prompt_length, task_type=task_type)
    print(f"  [ROUTER] {task_type}: prompt_length={prompt_length} -> provider={chosen}")
    return chosen


def build_sources(config, selected=None):
    """Build the ordered source list, filtered by name when requested.

    Args:
        config (dict): Configuration dictionary passed to each source agent.
        selected (list of str | None): Optional source names to run. When None,
            all 18 registered sources are returned.

    Returns:
        list: Instantiated source agents in canonical order.
    """
    if selected:
        requested = set(selected)
        unknown = requested - set(ALL_SOURCE_NAMES)
        if unknown:
            print(f"WARNING: Unknown source names ignored: {sorted(unknown)}")
        return [cls(config) for name, cls in SOURCE_REGISTRY if name in requested]
    return [cls(config) for name, cls in SOURCE_REGISTRY]


def load_configuration():
    """Load the project configuration from config.json.

    Returns:
        dict: Configuration dictionary.

    Raises:
        SystemExit: If config.json is missing or invalid.
    """
    print("PHASE 1: Loading configuration...")
    load_dotenv()
    project_root = _P if _P else os.getcwd()
    config_path = os.path.join(project_root, 'config.json')
    if not os.path.exists(config_path):
        config_path = os.path.join(project_root, 'config.template.json')
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
        print("SUCCESS: Configuration loaded.\n")
        return config
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"FATAL: Error loading config.json: {e}")
        sys.exit(1)


def main(sources=None):
    """Run the historical search pipeline: fetch all sources, deduplicate, evaluate, store.

    Args:
        sources (list of str | None): Optional source names to run. When None,
            all 18 registered sources are executed.
    """
    print("--- HISTORICAL SEARCH STARTED (v5.5 - Quad-Layer) ---")

    config = load_configuration()
    ai_manager = AIManager(config)
    db_manager = DatabaseManager()

    historic_config = config.copy()
    days_historic = config.get("days_to_search_historic", 2190)
    historic_config["days_to_search_daily"] = days_historic
    print(f"INFO: Search configured for the last {days_historic} days.\n")

    sources_to_search = build_sources(historic_config, selected=sources)

    import logging
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    logger = logging.getLogger(__name__)
    
    console = Console()

    # -- v5.13.0: Concurrent Multi-Threaded Historical Harvester. Each source
    # -- harvests in its own worker thread with per-thread stdout redirection so
    # -- a timeout or HTTP error in one provider never aborts the full run. --
    disabled_sources = [s for s in sources_to_search if not getattr(s, "enabled", True)]
    for source in disabled_sources:
        source_key = _source_key(source)
        logger.warning("Skipping %s -- disabled (no valid API key)", type(source).__name__)
        _emit_visualizer_event("source_status", {
            "source": source_key, "status": "error", "message": "disabled (no valid API key)",
        })

    enabled_sources = [s for s in sources_to_search if getattr(s, "enabled", True)]
    status = {}
    for source in enabled_sources:
        status[_source_key(source)] = {"status": "WAITING", "papers": 0, "elapsed": None}

    def _build_live_table():
        """Render the real-time Rich telemetry table for the historic harvest."""
        table = Table(
            title="Concurrent Historical Ingestion Mesh",
            box=box.ROUNDED,
            border_style="bright_cyan",
            header_style="bold bright_cyan",
        )
        table.add_column("Source Name", style="bold cyan")
        table.add_column("Status", style="bold")
        table.add_column("Papers Found", justify="right")
        table.add_column("Elapsed Time", justify="right")
        style_map = {
            "WAITING": "dim",
            "HARVESTING": "yellow",
            "COMPLETED": "green",
            "FAILED": "red",
        }
        for name, row in status.items():
            cell_style = style_map.get(row["status"], "white")
            elapsed = f"{row['elapsed']:.2f}s" if row["elapsed"] is not None else "--"
            table.add_row(
                name, f"[{cell_style}]{row['status']}[/{cell_style}]",
                str(row["papers"]), elapsed,
            )
        return table

    criteria = config.get("inclusion_criteria", "")
    all_historic_papers = []
    harvest_started = time.time()

    if enabled_sources:
        max_workers = min(18, len(enabled_sources))
        with Live(_build_live_table(), console=console, refresh_per_second=8) as live:
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_key = {}
                for source in enabled_sources:
                    source_key = _source_key(source)
                    status[source_key]["status"] = "HARVESTING"
                    future_to_key[executor.submit(
                        _harvest_single_source, source, source_key,
                        _source_query(source), criteria, days_historic,
                    )] = source_key
                for future in as_completed(future_to_key):
                    source_key = future_to_key[future]
                    result = future.result()
                    status[source_key]["status"] = result["status"]
                    status[source_key]["papers"] = len(result.get("papers") or [])
                    status[source_key]["elapsed"] = result.get("elapsed")
                    if result["status"] == "COMPLETED":
                        all_historic_papers.extend(result.get("papers") or [])
                    live.update(_build_live_table())
    harvest_elapsed = time.time() - harvest_started

    # -- v5.13.0: deduplicate by DOI + normalized title hash on the main thread.
    unique_papers = _deduplicate_papers(all_historic_papers)
    console.print(Panel(
        f"Total harvest time: [cyan]{harvest_elapsed:.2f}s[/cyan]\n"
        f"Raw papers collected: [cyan]{len(all_historic_papers)}[/cyan]\n"
        f"Unique deduplicated papers: [cyan]{len(unique_papers)}[/cyan]",
        title="[bold]Historical Ingestion Summary[/bold]",
        border_style="green",
    ))

    print(f"\nSUCCESS: Found {len(unique_papers)} potential unique papers across all sources.\n")

    papers_to_process = []
    for p in unique_papers:
        if p.get('doi'):
            if not db_manager.paper_exists_by_doi(p['doi']):
                papers_to_process.append(p)
        elif p.get('url'):
            if not db_manager.paper_exists_by_url(p['url']):
                papers_to_process.append(p)

    if not papers_to_process:
        print("INFO: Database appears to be already up to date. Terminating.")
        return

    print(f"INFO: Found {len(papers_to_process)} new, unique papers to add to the database.")

    API_CALL_LIMIT = config.get("api_call_limit_flash", 950)
    PRO_LIMIT = config.get("api_call_limit_pro", 95)
    REQUEST_DELAY = config.get("ai_request_delay", 5)
    min_score_for_deep_analysis = config.get("min_pre_screening_score", 6)
    api_calls_made = 0
    pro_calls_made = 0

    # -- v5.19.0: unified Two-Stage Rigor Decoupling engine. The legacy
    # -- flash-only scoring is replaced by the single deterministic
    # -- ``evaluate_paper()`` call (fast sieve + escalation gate + dual-audit). --
    evaluator = HierarchicalEvaluationEngine(
        ai_manager, escalation_threshold=min_score_for_deep_analysis)

    for i, paper in enumerate(papers_to_process):
        if api_calls_made >= API_CALL_LIMIT:
            print(f"\nWARNING: Reached the limit of {API_CALL_LIMIT} calls. Stopping for today.")
            break

        print(f"-> Processing paper {i+1}/{len(papers_to_process)}: '{paper['title'][:80]}...'")

        content_for_ai = f"Title: {paper['title']}\nAbstract: {paper.get('abstract', '')}"

        route_evaluation_provider(ai_manager, content_for_ai, task_type="fast_screening")

        # -- When the heavy-tier (pro) budget is exhausted, force a fast-only
        # -- verdict by raising the escalation threshold beyond reach. --
        if pro_calls_made >= PRO_LIMIT:
            verdict = evaluator.evaluate_paper(paper, escalation_threshold=11.0)
        else:
            verdict = evaluator.evaluate_paper(paper)
        api_calls_made += 1
        if verdict.get("escalated"):
            pro_calls_made += 1

        fast_eval = verdict.get("fast_evaluation")
        if not fast_eval:
            print(f"   WARNING: Hierarchical evaluation failed for {paper.get('doi')}. Skipping.")
            time.sleep(REQUEST_DELAY)
            continue

        paper_id = db_manager.add_paper(paper, fast_eval)
        overall = verdict.get("overall_score", 0.0)
        if paper_id:
            # -- v5.10.12 hotfix: centralized visualizer bridge (active push) --
            push_visualizer_event(
                "paper_evaluated",
                paper.get("source", "unknown"),
                overall,
                paper.get("title", "Unknown"),
            )
            print(f"   Score: {overall:.2f} (Saved) | Tier: {verdict.get('tier')}")
        else:
            print(f"   WARNING: Failed to save '{paper.get('title')}' to the database.")

        # -- v5.19.0: persist the decoupled Kitchenham quality appraisal. --
        if paper_id and verdict.get("escalated") and verdict.get("quality_score") is not None:
            db_manager.update_paper_quality(
                int(paper_id),
                float(verdict.get("quality_score")),
                verdict.get("quality_rubric_json") or "",
                verdict.get("evidence_quadrant") or "METHODOLOGICAL_NOISE",
            )

        time.sleep(REQUEST_DELAY)

    print("\n--- HISTORICAL SEARCH COMPLETE ---")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="TALOS Historical Search")
    parser.add_argument("--sources", nargs="+", default=None,
                        help="Space-separated source names to run (default: all 18).")
    args = parser.parse_args()
    main(sources=args.sources)