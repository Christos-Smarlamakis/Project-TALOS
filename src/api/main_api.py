# -*- coding: utf-8 -*-
"""
Module: main_api.py
Project: TALOS v5.9.18
Description:
    FastAPI facade layer exposing core TALOS functions (database queries,
    semantic search, scraping trigger, GWO optimization, Synapse webhook receiver,
    autonomous tester status/reports) as REST endpoints for the React 18 +
    Tailwind CSS + Shadcn UI frontend. All endpoints wrap existing synchronous
    core functions -- no logic is rewritten.

    Endpoints (18 total -- 100% ecosystem coverage + Synapse protocol + capabilities + tester):
    - GET  /api/v1/health              -> system health, DB stats, embedding coverage
    - GET  /api/v1/papers              -> paginated paper list
    - GET  /api/v1/papers/{paper_id}   -> full paper detail
    - POST /api/v1/papers/{paper_id}/evaluate -> single-paper AI evaluation (BgTasks)
    - POST /api/v1/search/semantic     -> natural-language semantic search
    - POST /api/v1/scrape/trigger      -> trigger daily scrape (BackgroundTasks)
    - POST /api/v1/optimize/gwo        -> trigger GWO hyperparameter optimization (BgTasks)
    - GET  /api/v1/optimize/gwo/history -> GWO optimization history for Recharts
    - GET  /api/v1/graph/view          -> serve architecture dependency graph HTML
    - POST /api/v1/ai/translate-query  -> natural-language -> boolean query translation
    - GET  /api/v1/analysis/authors    -> top authors from database (for BarChart)
    - POST /api/v1/db/recalculate-scores -> bulk overall_score recalculation (BgTasks)
    - GET  /api/v1/tasks/{task_id}     -> background task status
    - GET  /api/v1/tasks               -> list all background tasks
    - GET  /api/v1/capabilities        -> serve System Capabilities Master Reference HTML
    - POST /api/v1/synapse/webhook     -> SYNAPSE protocol inbound command receiver
    - GET  /api/v1/tester/status       -> Autonomous Red Tester Q-table status
    - GET  /api/v1/tester/reports      -> list crash report metadata

    Key design decisions:
    - Port 8001 (avoids conflict with SYNAPSE event bus on port 8000)
    - Synchronous endpoints (no async def) -- all core functions are blocking
    - BackgroundTasks (not Celery) for long-running scrape and GWO
    - Lazy singleton pattern for DatabaseManager and AIManager
    - sys.exit() monkey-patching to prevent scrape from killing the server
    - Pydantic v2 models with extra="ignore" for forward compatibility
    - Streamlit fully deprecated in v5.6.0; React 18 + Tailwind CSS + Shadcn UI is the sole frontend
    - Synapse Event-Driven Protocol integrated in v5.7.0 for ALEXANDRIA ecosystem interoperability
    - Autonomous Red Tester (RL-Driven Chaos Engineering) integrated in v5.9.1
    - LLM-Based Active Focus Summarization integrated in v5.9.1
    - 4-Way Execution Mode Matrix integrated in v5.9.1
    - 2D Execution Matrix (Network x Hardware Strategies) integrated in v5.9.4

Dependencies:
    - fastapi: REST framework, routing, background tasks, CORS middleware.
    - pydantic: Request/response model validation (v2).
    - src.core.database_manager: Database layer (SQLite + embeddings).
    - src.core.ai_manager: Multi-provider LLM interface.
    - src.api.synapse_routes: SYNAPSE webhook APIRouter for ecosystem eventing.
    - src.api.red_tester_routes: Autonomous Red Tester Q-table and reports endpoints.

    Usage:
        python -m uvicorn src.api.main_api:app --host 127.0.0.1 --port 8001
"""
import os
import sys

# -- Resolve project root (same pattern as all src/*.py modules) --------------
_P = os.path.abspath(os.path.dirname(__file__))
while _P and not os.path.exists(os.path.join(_P, 'talos.py')):
    _P = os.path.dirname(_P)
if _P:
    sys.path.insert(0, _P)

import json
import uuid
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

import numpy as np
from fastapi import FastAPI, HTTPException, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from src.core.database_manager import DatabaseManager
from src.core.ai_manager import AIManager
from src.api.synapse_routes import router as synapse_router
from src.api.red_tester_routes import router as red_tester_router

# -- Logging (v5.9.17: enterprise logger with Rich + rotating file handlers) --
from src.utils.logger import get_logger
logger = get_logger("api")

# -- FastAPI App & CORS -------------------------------------------------------
app = FastAPI(
    title="TALOS Research API",
description="Facade REST API for the TALOS autonomous research platform (v5.9.18 -- Universal Cloud Mesh & Multi-Provider Redundancy Expansion)",
version="5.9.18",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -- Include Synapse webhook router (v5.7.0) --
app.include_router(synapse_router)

# -- Include Autonomous Red Tester router (v5.9.1) --
app.include_router(red_tester_router)

# -- Mount templates/ as static files for architecture graph assets --
app.mount("/static/templates", StaticFiles(directory="templates"), name="static_templates")

# -- Singleton instances (lazy-init) ------------------------------------------
_db_manager: Optional[DatabaseManager] = None
_ai_manager: Optional[AIManager] = None
_config: Optional[dict] = None
_lock = threading.Lock()


def _get_project_root() -> str:
    """Return the absolute path to the project root (where talos.py lives)."""
    return _P


def _load_config() -> dict:
    """Load config.json from the project root. Cached after first call."""
    global _config
    if _config is not None:
        return _config
    config_path = os.path.join(_get_project_root(), "config.json")
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            _config = json.load(f)
        logger.info("Configuration loaded from %s", config_path)
        return _config
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.error("Failed to load config.json: %s", e)
        _config = {}
        return _config


def _get_db() -> DatabaseManager:
    """Lazy-init singleton DatabaseManager (profile-aware)."""
    global _db_manager
    if _db_manager is None:
        with _lock:
            if _db_manager is None:
                _db_manager = DatabaseManager()
                logger.info("DatabaseManager initialized (db: %s)", _db_manager.db_path)
    return _db_manager


def _get_ai() -> AIManager:
    """Lazy-init singleton AIManager from config."""
    global _ai_manager
    if _ai_manager is None:
        with _lock:
            if _ai_manager is None:
                _ai_manager = AIManager(_load_config())
                logger.info("AIManager initialized")
    return _ai_manager


# -- Background task store ----------------------------------------------------
_task_store: Dict[str, dict] = {}
_task_lock = threading.Lock()


def _create_task() -> str:
    """Create a new task entry and return its ID."""
    task_id = uuid.uuid4().hex[:8]
    with _task_lock:
        _task_store[task_id] = {
            "status": "running",
            "progress": "Starting...",
            "result": None,
            "error": None,
            "started_at": datetime.now().isoformat(),
            "completed_at": None,
        }
    return task_id


def _update_task(task_id: str, **kwargs):
    """Thread-safe update of a task entry."""
    with _task_lock:
        if task_id in _task_store:
            _task_store[task_id].update(kwargs)


# =============================================================================
# PYDANTIC MODELS
# =============================================================================

class PaperSummary(BaseModel):
    """Mirrors get_all_papers_for_dashboard() columns."""
    model_config = {"extra": "ignore"}
    id: int
    doi: Optional[str] = None
    url: Optional[str] = None
    title: Optional[str] = None
    authors: Optional[str] = None
    publication_year: Optional[int] = None
    abstract: Optional[str] = None
    source: Optional[str] = None
    strategic_score: int = 0
    operational_score: int = 0
    tactical_score: int = 0
    playground_score: int = 0
    overall_score: float = 0.0
    in_zotero: int = 0
    oa_pdf_url: Optional[str] = None


class PaperDetail(BaseModel):
    """Full row from get_single_paper_details() -- all columns."""
    model_config = {"extra": "ignore"}
    id: int
    doi: Optional[str] = None
    url: Optional[str] = None
    title: Optional[str] = None
    authors: Optional[str] = None
    publication_year: Optional[int] = None
    abstract: Optional[str] = None
    source: Optional[str] = None
    strategic_score: int = 0
    operational_score: int = 0
    tactical_score: int = 0
    playground_score: int = 0
    overall_score: float = 0.0
    evaluation_reasoning: Optional[str] = None
    evaluation_contribution: Optional[str] = None
    evaluation_utilization: Optional[str] = None
    suggested_tags: Optional[str] = None
    suggested_folder: Optional[str] = None
    suggested_discord_channel: Optional[str] = None
    in_zotero: int = 0
    embedding_model: Optional[str] = None
    processed_at: Optional[str] = None
    last_evaluated_at: Optional[str] = None
    oa_pdf_url: Optional[str] = None
    openalex_id: Optional[str] = None
    pmid: Optional[str] = None
    pmcid: Optional[str] = None
    oa_status: Optional[str] = None
    journal_issn: Optional[str] = None
    publisher: Optional[str] = None
    enrichment_status: int = 0


class PaginatedPapers(BaseModel):
    """Paginated response wrapper."""
    total: int
    page: int
    page_size: int
    papers: List[PaperSummary]


class SemanticSearchRequest(BaseModel):
    """Request body for semantic search."""
    query: str = Field(..., min_length=3, description="Natural language research query")
    top_k: int = Field(default=20, ge=1, le=200, description="Number of results to return")
    model_filter: Optional[str] = Field(
        default=None,
        description="Embedding model to use, e.g. 'ollama:nomic-embed-text' or 'gemini:gemini-embedding-001'",
    )


class SemanticSearchResponse(BaseModel):
    """Response from semantic search."""
    query: str
    model_used: Optional[str] = None
    results: List[PaperSummary]


class ScrapeRequest(BaseModel):
    """Optional source filter for scraping."""
    source_filter: Optional[List[str]] = Field(
        default=None,
        description="Specific sources to query (e.g. ['arxiv','ieee']). None = all 14 sources.",
    )


class GWORunRequest(BaseModel):
    """GWO hyperparameter optimization parameters."""
    wolves: int = Field(default=15, ge=5, le=100, description="Number of wolves (population size)")
    iterations: int = Field(default=50, ge=10, le=500, description="Maximum GWO iterations")
    rl_episodes: int = Field(default=30, ge=5, le=200, description="RL episodes per fitness evaluation")


class GWOResult(BaseModel):
    """Result from a completed GWO run."""
    learning_rate: float
    gamma: float
    epsilon_decay: float
    best_reward: float
    iterations: int
    gwo_time: float


class TaskStatus(BaseModel):
    """Status of a background task."""
    task_id: str
    status: str  # "running" | "completed" | "failed"
    progress: Optional[str] = None
    result: Optional[Any] = None
    error: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None


class SystemHealth(BaseModel):
    """System health check response."""
    status: str
    api_version: str
    db_stats: dict
    embedding_models: List[dict]
    timestamp: str


class TranslateQueryRequest(BaseModel):
    """Request body for natural-language-to-boolean query translation."""
    query: str = Field(..., min_length=10, description="Natural language research goal (e.g., 'I want to study drone swarm intelligence')")


class TranslateQueryResponse(BaseModel):
    """Response from query translation -- flattened dict of source keys -> boolean queries."""
    original_query: str
    boolean_query: dict


class AuthorSummary(BaseModel):
    """A single author with their publication count in the database."""
    author: str
    count: int


class EvaluatePaperRequest(BaseModel):
    """Optional model preference for single-paper evaluation."""
    model_type: str = Field(default="pro", description="AI model to use: 'pro' or 'flash'")


# =============================================================================
# ENDPOINTS
# =============================================================================

@app.on_event("startup")
def on_startup():
    """Pre-warm singletons and log readiness."""
    logger.info("TALOS FastAPI v5.9.18 starting up (Universal Cloud Mesh & Multi-Provider Redundancy Expansion, port 8001)...")
    _get_db()  # warm DatabaseManager
    logger.info("TALOS FastAPI ready on http://127.0.0.1:8001")
    logger.info("API docs: http://localhost:8001/docs")
    logger.info("Capabilities reference: http://localhost:8001/api/v1/capabilities")
    logger.info("Synapse webhook: http://localhost:8001/api/v1/synapse/webhook")


# -- GET /api/v1/health -------------------------------------------------------

@app.get("/api/v1/health", response_model=SystemHealth)
def health_check():
    """Return system health including database statistics and embedding model coverage."""
    try:
        db = _get_db()
        if not db._table_exists("papers"):
            db_stats = {"error": "no database", "total_papers": 0}
        else:
            db_stats = db.get_database_statistics()
        embedding_models = db.get_embedding_model_stats()
    except Exception as e:
        logger.error("Health check failed: %s", e)
        db_stats = {"error": str(e)}
        embedding_models = []

    return SystemHealth(
        status="running",
        api_version=app.version,
        db_stats=db_stats,
        embedding_models=embedding_models,
        timestamp=datetime.now().isoformat(),
    )


# -- GET /api/v1/papers (paginated) -------------------------------------------

@app.get("/api/v1/papers", response_model=PaginatedPapers)
def list_papers(
    page: int = Query(default=1, ge=1, description="Page number (1-based)"),
    page_size: int = Query(default=50, ge=1, le=500, description="Papers per page"),
):
    """Return a paginated list of all papers sorted by overall_score descending."""
    db = _get_db()
    all_papers = db.get_all_papers_for_dashboard()
    total = len(all_papers)

    start = (page - 1) * page_size
    end = start + page_size
    page_papers = all_papers[start:end]

    return PaginatedPapers(
        total=total,
        page=page,
        page_size=page_size,
        papers=page_papers,
    )


# -- GET /api/v1/papers/{paper_id} --------------------------------------------

@app.get("/api/v1/papers/{paper_id}", response_model=PaperDetail)
def get_paper(paper_id: int):
    """Return full detail for a single paper by its database ID."""
    db = _get_db()
    paper = db.get_single_paper_details(paper_id)
    if paper is None:
        raise HTTPException(status_code=404, detail=f"Paper {paper_id} not found")
    return paper


# -- POST /api/v1/search/semantic ---------------------------------------------

@app.post("/api/v1/search/semantic", response_model=SemanticSearchResponse)
def semantic_search(request: SemanticSearchRequest):
    """Perform semantic (vector) search against the paper database.

    Pipeline:
        1. Embed the user's query via AIManager (fallback chain)
        2. Compute cosine similarity against all stored embeddings
        3. Return the top_k matching papers with full metadata
    """
    try:
        ai = _get_ai()
        db = _get_db()

        # Step 1: Embed the query
        texts_to_embed = [f"Title: {request.query}\nAbstract: {request.query}"]
        result = ai.generate_embeddings(texts_to_embed)
        vectors, model_used = result if isinstance(result, tuple) else (result, None)

        if vectors is None or len(vectors) == 0:
            raise HTTPException(
                status_code=500,
                detail="Embedding generation failed -- all providers unavailable.",
            )

        # Step 2: Cosine similarity search
        query_vec = np.array(vectors[0])
        # If user didn't specify model_filter, use the model that generated the embedding
        effective_filter = request.model_filter or model_used
        paper_ids = db.semantic_search(query_vec, top_k=request.top_k, model_filter=effective_filter)

        if not paper_ids:
            return SemanticSearchResponse(query=request.query, model_used=model_used, results=[])

        # Step 3: Fetch full paper records
        papers = db.get_papers_by_ids(paper_ids)
        # Preserve semantic search order (get_papers_by_ids returns DB order)
        paper_map = {p["id"]: p for p in papers}
        ordered_papers = [paper_map[pid] for pid in paper_ids if pid in paper_map]

        return SemanticSearchResponse(
            query=request.query,
            model_used=model_used,
            results=ordered_papers,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Semantic search failed: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Semantic search error: {str(e)}")


# -- POST /api/v1/scrape/trigger ----------------------------------------------

def _run_scrape_background(task_id: str, source_filter: Optional[List[str]]):
    """Background task: run daily_search.main() without killing the server.

    Monkey-patches sys.exit to raise RuntimeError instead of terminating the
    process, since daily_search.main() calls sys.exit(1) on config load failure
    and other fatal errors.
    """
    try:
        _update_task(task_id, progress="Loading configuration...")

        # Import daily_search lazily (its main() instantiates 14 source agents)
        from src.ingestion.daily_search import main as daily_search_main

        # -- Monkey-patch sys.exit to prevent process death --
        _orig_exit = sys.exit

        class _ScrapeExit(RuntimeError):
            """Raised when daily_search calls sys.exit()."""
            pass

        def _safe_exit(code=0):
            raise _ScrapeExit(f"daily_search called sys.exit({code})")

        sys.exit = _safe_exit

        try:
            _update_task(task_id, progress="Fetching from 14 academic sources...")
            daily_search_main()
            _update_task(
                task_id,
                status="completed",
                progress="Scraping pipeline finished successfully.",
                completed_at=datetime.now().isoformat(),
            )
        except _ScrapeExit as e:
            _update_task(
                task_id,
                status="failed",
                progress="Scraping aborted.",
                error=str(e),
                completed_at=datetime.now().isoformat(),
            )
        finally:
            sys.exit = _orig_exit

    except Exception as e:
        logger.error("Background scrape [%s] failed: %s", task_id, e, exc_info=True)
        _update_task(
            task_id,
            status="failed",
            progress="Unexpected error during scraping.",
            error=str(e),
            completed_at=datetime.now().isoformat(),
        )


@app.post("/api/v1/scrape/trigger", response_model=TaskStatus, status_code=202)
def trigger_scrape(background_tasks: BackgroundTasks, request: ScrapeRequest = ScrapeRequest()):
    """Trigger a full daily search pipeline in the background.

    The pipeline fetches new papers from all 14 configured academic sources,
    deduplicates, runs two-stage AI evaluation (Flash pre-screening + Pro deep
    analysis), and generates a Markdown briefing report.

    Returns immediately with a task_id. Poll GET /api/v1/tasks/{task_id} for status.
    """
    task_id = _create_task()
    _update_task(task_id, progress="Queued for execution...")

    if request.source_filter:
        _update_task(
            task_id,
            progress=f"Queued (filtered to sources: {', '.join(request.source_filter)})",
        )

    background_tasks.add_task(_run_scrape_background, task_id, request.source_filter)

    with _task_lock:
        task_data = dict(_task_store[task_id])

    return TaskStatus(task_id=task_id, **task_data)


# -- POST /api/v1/optimize/gwo ------------------------------------------------

def _run_gwo_background(task_id: str, wolves: int, iterations: int, rl_episodes: int):
    """Background task: run GWO hyperparameter optimization.

    GWO trains a fresh DRL agent per wolf per iteration -- this is CPU-bound
    and takes minutes. Progress is monitored by reading gwo_history.json.
    """
    try:
        _update_task(task_id, progress="Initializing GWO optimizer...")

        # -- Import GWO lazily (imports TalosEnv, DRL agent) --
        import src.ai.optimizers.gwo_rl_optimizer as gwo_mod

        # Override RL episodes per the user's request
        gwo_mod.DEFAULT_RL_EPISODES = rl_episodes

        # -- Start a progress monitor thread --
        # GWO writes gwo_history.json incrementally; we poll it
        history_path = os.path.join(_get_project_root(), "models", "gwo_history.json")

        def _poll_progress():
            """Poll gwo_history.json every 2 seconds and update task progress."""
            last_iteration = 0
            while True:
                time.sleep(2)
                with _task_lock:
                    current = _task_store.get(task_id, {})
                    if current.get("status") != "running":
                        return
                try:
                    if os.path.exists(history_path):
                        with open(history_path, "r", encoding="utf-8") as f:
                            history = json.load(f)
                        if history:
                            current_iter = history[-1].get("iteration", 0)
                            if current_iter != last_iteration:
                                last_iteration = current_iter
                                _update_task(
                                    task_id,
                                    progress=f"GWO iteration {current_iter}/{iterations}",
                                )
                except (json.JSONDecodeError, OSError):
                    pass  # file may be mid-write

        monitor_thread = threading.Thread(target=_poll_progress, daemon=True)
        monitor_thread.start()

        try:
            _update_task(task_id, progress="Running GWO (this may take several minutes)...")
            result = gwo_mod.run_gwo(
                wolves_number=wolves,
                max_iterations=iterations,
                live=False,
            )
            _update_task(
                task_id,
                status="completed",
                progress=f"GWO complete after {result['iterations']} iterations",
                result=result,
                completed_at=datetime.now().isoformat(),
            )
        finally:
            # Stop the monitor thread (it exits when status != "running")
            pass

    except Exception as e:
        logger.error("Background GWO [%s] failed: %s", task_id, e, exc_info=True)
        _update_task(
            task_id,
            status="failed",
            progress="GWO optimization failed.",
            error=str(e),
            completed_at=datetime.now().isoformat(),
        )


@app.post("/api/v1/optimize/gwo", response_model=TaskStatus, status_code=202)
def trigger_gwo(background_tasks: BackgroundTasks, request: GWORunRequest = GWORunRequest()):
    """Trigger GWO hyperparameter optimization in the background.

    The Grey Wolf Optimizer tunes the DRL agent's learning rate, gamma, and
    epsilon decay by training a fresh agent per wolf per iteration. This is
    CPU-intensive and may take several minutes.

    Returns immediately with a task_id. Poll GET /api/v1/tasks/{task_id} for status.
    """
    task_id = _create_task()
    _update_task(
        task_id,
        progress=f"Queued (wolves={request.wolves}, iterations={request.iterations}, rl_episodes={request.rl_episodes})",
    )

    background_tasks.add_task(
        _run_gwo_background,
        task_id,
        request.wolves,
        request.iterations,
        request.rl_episodes,
    )

    with _task_lock:
        task_data = dict(_task_store[task_id])

    return TaskStatus(task_id=task_id, **task_data)


# -- GET /api/v1/tasks/{task_id} ----------------------------------------------

@app.get("/api/v1/tasks/{task_id}", response_model=TaskStatus)
def get_task_status(task_id: str):
    """Return the current status of a background task by its ID."""
    with _task_lock:
        task_data = _task_store.get(task_id)
    if task_data is None:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    return TaskStatus(task_id=task_id, **task_data)


# -- GET /api/v1/tasks --------------------------------------------------------

@app.get("/api/v1/tasks", response_model=List[TaskStatus])
def list_tasks():
    """Return all background tasks, newest first."""
    with _task_lock:
        tasks = [
            TaskStatus(task_id=tid, **data)
            for tid, data in sorted(
                _task_store.items(),
                key=lambda x: x[1].get("started_at", ""),
                reverse=True,
            )
        ]
    return tasks


# -- POST /api/v1/papers/{paper_id}/evaluate -----------------------------------

def _run_evaluate_background(task_id: str, paper_id: int, model_type: str):
    """Background task: evaluate a single paper with the LLM and update the DB."""
    try:
        _update_task(task_id, progress=f"Fetching paper {paper_id}...")
        db = _get_db()
        paper = db.get_single_paper_details(paper_id)
        if paper is None:
            _update_task(task_id, status="failed", error=f"Paper {paper_id} not found",
                         completed_at=datetime.now().isoformat())
            return

        title = paper.get("title") or "No title"
        abstract = paper.get("abstract") or "No abstract"
        text_to_evaluate = f"Title: {title}\nAbstract: {abstract}"

        _update_task(task_id, progress="Running AI evaluation...")
        ai = _get_ai()
        config = _load_config()
        # Use the pre-screening prompt if available, otherwise the PhD focus prompt
        eval_prompt = config.get("pre_screening_prompt") or config.get("phd_focus_system_prompt")
        result = ai.evaluate_paper_json(
            abstract=text_to_evaluate,
            model_type=model_type,
            system_prompt_override=eval_prompt,
        )

        if result is None:
            _update_task(task_id, status="failed", error="AI evaluation returned null -- all providers unavailable.",
                         completed_at=datetime.now().isoformat())
            return

        # Build evaluation_data dict matching what update_paper_evaluation expects
        evaluation_data = {
            "scores": {
                "strategic": result.get("strategic_score", 0),
                "operational": result.get("operational_score", 0),
                "tactical": result.get("tactical_score", 0),
                "playground": result.get("playground_score", 0),
            },
            "reasoning": result.get("evaluation_reasoning", ""),
            "contribution": result.get("evaluation_contribution", ""),
            "utilization": result.get("evaluation_utilization", ""),
            "tags": result.get("suggested_tags", ""),
            "folder": result.get("suggested_folder", ""),
            "discord_channel": result.get("suggested_discord_channel", ""),
        }
        db.update_paper_evaluation(paper_id, evaluation_data)

        _update_task(
            task_id,
            status="completed",
            progress=f"Paper {paper_id} evaluated successfully.",
            result=evaluation_data["scores"],
            completed_at=datetime.now().isoformat(),
        )
    except Exception as e:
        logger.error("Background evaluate [%s] failed: %s", task_id, e, exc_info=True)
        _update_task(task_id, status="failed", error=str(e), completed_at=datetime.now().isoformat())


@app.post("/api/v1/papers/{paper_id}/evaluate", response_model=TaskStatus, status_code=202)
def evaluate_paper_endpoint(paper_id: int, background_tasks: BackgroundTasks,
                            request: EvaluatePaperRequest = EvaluatePaperRequest()):
    """Trigger AI evaluation for a single paper in the background.

    Fetches the paper's title+abstract, sends them to the LLM for multi-axis
    scoring (strategic, operational, tactical, playground), and persists the
    results (scores, reasoning, tags) to the database.

    Returns immediately with a task_id. Poll GET /api/v1/tasks/{task_id} for status.
    """
    task_id = _create_task()
    _update_task(task_id, progress=f"Queued evaluation for paper {paper_id}...")
    background_tasks.add_task(_run_evaluate_background, task_id, paper_id, request.model_type)
    with _task_lock:
        task_data = dict(_task_store[task_id])
    return TaskStatus(task_id=task_id, **task_data)


# -- POST /api/v1/ai/translate-query -------------------------------------------

# -- Inline helpers from query_translator.py (avoid importing the interactive main) --

def _flatten_json_for_translation(y):
    """Recursively flatten a nested JSON dict, extracting known query/prompt keys."""
    out = {}
    known_keys = [
        'arxiv_query', 'ieee_query', 'semantic_scholar_query', 'springer_query',
        'openalex_query', 'dblp_query', 'elsevier_query', 'crossref_query',
        'openarchives_query', 'pubmed_query', 'osti_query', 'scigov_query', 'core_query',
        'phd_focus_system_prompt', 'pre_screening_prompt', 'trajectory_analyzer_prompt',
    ]
    def _flatten(x, name=''):
        if isinstance(x, dict):
            for a in x:
                _flatten(x[a], name + a + '_')
            return
        key = name[:-1] if name else ''
        for k in known_keys:
            if k == key or key.endswith('_' + k) or key.endswith(k):
                out[k] = x
                return
        out[key] = x
    _flatten(y)
    return out


@app.post("/api/v1/ai/translate-query", response_model=TranslateQueryResponse)
def translate_query(request: TranslateQueryRequest):
    """Translate a natural-language research goal into optimized boolean search queries.

    Uses the AIManager with the 'query_translator' system prompt override
    to act as a Research Architect. Returns a flattened dict mapping source keys
    (e.g., 'arxiv_query', 'ieee_query') to their boolean query strings.
    """
    config = _load_config()
    ai = _get_ai()

    # Build the meta-prompt (same logic as query_translator.py main function)
    meta_prompt = config.get(
        "query_translator_prompt",
        "Act as a Research Architect. Generate a flat JSON object with optimized search queries "
        "(keys like 'arxiv_query') and customized system prompts "
        "(keys like 'phd_focus_system_prompt') for the user's research goal. Do NOT nest the JSON.",
    )

    template_guidance = (
        f"\n**REFERENCE TEMPLATE FOR PROMPTS (Keep JSON structure, change content):**\n"
        f"{config.get('phd_focus_system_prompt', '')}\n\n"
        f"**USER RESEARCH GOAL:**\n{request.query}"
    )

    try:
        generated_config_raw = ai.evaluate_paper_json(
            abstract=template_guidance,
            model_type='pro',
            system_prompt_override=meta_prompt,
        )
    except Exception as e:
        logger.error("Query translation failed: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"AI translation error: {str(e)}")

    if not generated_config_raw:
        raise HTTPException(
            status_code=500,
            detail="AI did not return valid JSON. Try making your research goal more specific.",
        )

    flattened = _flatten_json_for_translation(generated_config_raw)
    return TranslateQueryResponse(original_query=request.query, boolean_query=flattened)


# -- GET /api/v1/analysis/authors ----------------------------------------------

@app.get("/api/v1/analysis/authors", response_model=List[AuthorSummary])
def list_top_authors(
    limit: int = Query(default=100, ge=1, le=500, description="Max authors to return"),
):
    """Return top authors ranked by publication count in the local database.

    Uses a direct SQL aggregation query on the papers table -- no external API calls.
    Ideal for Recharts <BarChart> consumption.
    """
    db = _get_db()
    try:
        import sqlite3
        with sqlite3.connect(db.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT authors, COUNT(*) as cnt FROM papers "
                "WHERE authors IS NOT NULL AND authors != '' "
                "GROUP BY authors ORDER BY cnt DESC LIMIT ?",
                (limit,),
            ).fetchall()
    except sqlite3.Error as e:
        logger.error("Author aggregation failed: %s", e)
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    return [AuthorSummary(author=row["authors"], count=row["cnt"]) for row in rows]


# -- POST /api/v1/db/recalculate-scores ----------------------------------------

def _run_recalculate_background(task_id: str):
    """Background task: recalculate overall_score for every paper in the database.

    Replicates the core logic of recalculate_scores.py without the interactive
    questionary prompt. Uses bulk execumany for performance.
    """
    import sqlite3 as _bg_sqlite3
    try:
        _update_task(task_id, progress="Connecting to database...")
        db = _get_db()

        _update_task(task_id, progress="Fetching all papers...")
        with _bg_sqlite3.connect(db.db_path) as conn:
            conn.row_factory = _bg_sqlite3.Row
            rows = conn.execute(
                "SELECT id, tactical_score, strategic_score, operational_score, playground_score FROM papers"
            ).fetchall()

        if not rows:
            _update_task(task_id, status="completed",
                         progress="Database is empty -- nothing to recalculate.",
                         completed_at=datetime.now().isoformat())
            return

        total = len(rows)
        _update_task(task_id, progress=f"Recalculating scores for {total} papers...")

        updates = []
        for i, row in enumerate(rows):
            scores_dict = {
                'strategic': row['strategic_score'],
                'operational': row['operational_score'],
                'tactical': row['tactical_score'],
                'playground': row['playground_score'],
            }
            new_overall = db._calculate_overall_score(scores_dict)
            updates.append((new_overall, row['id']))

            # Progress update every 500 rows
            if (i + 1) % 500 == 0:
                _update_task(task_id, progress=f"Recalculating... {i + 1}/{total}")

        _update_task(task_id, progress=f"Writing {len(updates)} updates to database...")
        with _bg_sqlite3.connect(db.db_path) as conn:
            conn.executemany("UPDATE papers SET overall_score = ? WHERE id = ?", updates)
            conn.commit()

        _update_task(
            task_id,
            status="completed",
            progress=f"Recalculation complete -- {total} papers updated.",
            result={"papers_updated": total},
            completed_at=datetime.now().isoformat(),
        )
    except Exception as e:
        logger.error("Background recalculate [%s] failed: %s", task_id, e, exc_info=True)
        _update_task(task_id, status="failed", error=str(e), completed_at=datetime.now().isoformat())


@app.post("/api/v1/db/recalculate-scores", response_model=TaskStatus, status_code=202)
def recalculate_scores_endpoint(background_tasks: BackgroundTasks):
    """Trigger a bulk recalculation of overall_score for all papers.

    Reads the four sub-scores (strategic, operational, tactical, playground)
    from each paper, applies the central weighted formula, and bulk-updates
    the database. This may take a few seconds for 5,000+ rows.

    Returns immediately with a task_id. Poll GET /api/v1/tasks/{task_id} for status.
    """
    task_id = _create_task()
    _update_task(task_id, progress="Queued score recalculation...")
    background_tasks.add_task(_run_recalculate_background, task_id)
    with _task_lock:
        task_data = dict(_task_store[task_id])
    return TaskStatus(task_id=task_id, **task_data)


# -- GET /api/v1/optimize/gwo/history -----------------------------------------

@app.get("/api/v1/optimize/gwo/history", response_model=List[dict])
def get_gwo_history():
    """Return GWO optimization history for direct Recharts <LineChart> consumption.

    Reads models/gwo_history.json first, falls back to models/gwo_progress.json.
    Returns the raw JSON array as List[dict]. Returns [] if neither file exists.
    """
    project_root = _get_project_root()
    # Try gwo_history.json first (detailed per-iteration data)
    history_paths = [
        os.path.join(project_root, "models", "gwo_history.json"),
        os.path.join(project_root, "models", "gwo_progress.json"),
    ]
    for path in history_paths:
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                logger.info("Served GWO history from %s (%d iterations)", path, len(data))
                return data
            except (json.JSONDecodeError, OSError) as e:
                logger.warning("Failed to read GWO history file %s: %s", path, e)
                continue
    return []


# -- GET /api/v1/graph/view ---------------------------------------------------

@app.get("/api/v1/graph/view")
def view_architecture_graph():
    """Serve the Alexandria Architecture Dependency Graph as an HTML page.

    Resolves templates/architecture_graph.html from the project root.
    Returns FileResponse so the browser renders it directly.
    Returns 404 if the file does not exist.
    """
    project_root = _get_project_root()
    graph_path = os.path.join(project_root, "templates", "architecture_graph.html")
    if not os.path.exists(graph_path):
        raise HTTPException(
            status_code=404,
            detail="architecture_graph.html not found in templates/ directory. "
                   "Please generate it first using the dependency graph tool.",
        )
    return FileResponse(graph_path, media_type="text/html")


# -- GET /api/v1/capabilities -------------------------------------------------

@app.get("/api/v1/capabilities", response_class=HTMLResponse, tags=["System"])
async def get_capabilities():
    """Serve the System Capabilities Master Reference as a standalone HTML page.

    Reads docs/SYSTEM_CAPABILITIES_MASTER.html from the project root.
    The document covers all 9 sections of the TALOS/ALEXANDRIA/ATHENA architecture
    and the complete 16-endpoint REST API reference.

    Returns 404 if the document has not been generated yet.
    """
    capabilities_path = Path("docs/SYSTEM_CAPABILITIES_MASTER.html")
    if capabilities_path.exists():
        return HTMLResponse(content=capabilities_path.read_text(encoding="utf-8"))
    raise HTTPException(status_code=404, detail="Capabilities document not found.")


# =============================================================================
# MAIN -- development server entry point
# =============================================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.api.main_api:app",
        host="127.0.0.1",
        port=8001,
        reload=False,
    )