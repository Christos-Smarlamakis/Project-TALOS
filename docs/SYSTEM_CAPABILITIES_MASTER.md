# TALOS/ALEXANDRIA/ATHENA -- System Capabilities Master Reference v5.9.9

> **Document ID:** TALOS-SYS-CAP-001
> **Classification:** Public Reference
> **Scope:** TALOS Research Intelligence Platform (Headless FastAPI Backend + React Frontend + SYNAPSE Protocol)
> **Last Updated:** 2026-08-02
> **Version:** v5.9.9 -- Report Path Consolidation & Data Directory Isolation

[![IEEE Computer Society WEIGD Fund 2026](https://img.shields.io/badge/IEEE_Computer_Society-WEIGD_Fund_Recipient_2026-006699?style=flat-square&logo=ieee&logoColor=white)](https://www.computer.org/)

---

## Section 1: System Vision & Core Architecture

### 1.1 Foundational Principle

TALOS is an autonomous Research Intelligence Platform that ingests, evaluates, synthesizes, and visualizes scientific knowledge across 14 academic sources. It replaces manual systematic literature review workflows with an AI-driven, DRL-orchestrated pipeline that maintains a human-in-the-loop at every critical decision boundary. The system operates as a microservice within the broader ALEXANDRIA Ecosystem -- a distributed research intelligence mesh that communicates via the SYNAPSE Event-Driven Protocol.

### 1.2 Architectural Pillars

The system operates as a five-layer architecture:

| Layer | Component | Role |
|-------|-----------|------|
| **Frontend** | React 18 with Tailwind CSS and Shadcn UI | User-facing dashboard leveraging the REST API |
| **Backend** | `src/api/main_api.py` (18 endpoints) | Headless FastAPI facade exposing all core capabilities |
| **AI Core** | `src/core/ai_manager.py` (4 providers + circuit breaker) | Multi-provider LLM orchestration with interactive cloud fallback |
| **Persistence** | `src/core/database_manager.py` | SQLite + multi-model vector embeddings (Ollama + Gemini) |
| **Integration** | `src/integration/synapse_client.py` + `src/mcp_server.py` | SYNAPSE Event Bus + MCP Tool Server for external tooling |

### 1.3 Data Flow

```
User (React UI) --> FastAPI (:8001) --> src/core/*.py --> src/ingestion/*.py --> External APIs
                         ^                                    |
                         |                                    v
                    SYNAPSE Bus (:8000)              data/talos_research.db
                         |                          (SQLite + Embeddings)
                    MCP Server (Cherry Studio)             ^
                                                           |
                    config.json + .env (Configuration + Secrets)
```

### 1.4 Operational Modes

- **Production:** Headless FastAPI listener on port 8001, React frontend consuming the API
- **Development:** `uvicorn src.api.main_api:app --reload --port 8001`
- **Background Services:** Scraping pipeline, GWO optimizer, DRL training -- all via FastAPI BackgroundTasks
- **CLI:** `talos.py` retains full terminal-mode access for maintenance and diagnostics
- **SYNAPSE Webhook:** `POST /api/v1/synapse/webhook` receives external commands from other ALEXANDRIA microservices
- **MCP Server:** `src/mcp_server.py` exposes tools (database query, semantic search, paper evaluation, GWO trigger, scrape trigger) to MCP-compatible clients like Cherry Studio

### 1.5 System Constants

| Constant | Value | Source File |
|----------|-------|-------------|
| TALOS_VERSION | "5.9.3" | `config/settings.py` |
| TALOS_API_PORT | 8001 | `config/settings.py` |
| SYNAPSE_BUS_URL | http://localhost:8000/api/v1/events | `config/settings.py` |
| FAST_EDGE_MODEL | fermionresearch/Neutrino-8B | `config/settings.py` |
| FAST_EDGE_BASE_URL | http://127.0.0.1:11435/v1 | `config/settings.py` |
| HEAVY_REASONING_MODEL | qwen2.5:14b | `config/settings.py` |
| OLLAMA_BASE_URL | http://127.0.0.1:11434 | `config/settings.py` |
| TALOS_EXECUTION_MODE | local | `config/settings.py` |
| TALOS_FAST_ROUTING | local | `config/settings.py` |
| TALOS_HEAVY_ROUTING | local | `config/settings.py` |
| DEFAULT_TIER | fast | `config/settings.py` |

---

## Section 2: Multi-Source Ingestion Engine

### 2.1 The "Genesis" Operation

TALOS ingests academic literature from **14 independent APIs**, each implemented as a standalone source agent under `src/ingestion/`. Every agent conforms to a standardized output format:

```json
{
  "doi": "string or null",
  "url": "string or null",
  "title": "string",
  "authors_str": "string",
  "publication_year": "integer or null",
  "abstract": "string or null",
  "source": "string"
}
```

### 2.2 Source Agent Inventory (14 APIs)

| Source | Module | Auth Model | Rate Limit Handling |
|--------|--------|-----------|---------------------|
| ArXiv | `src/ingestion/arxiv.py` | Public API | Exponential backoff |
| IEEE Xplore | `src/ingestion/ieee.py` | API key | Exponential backoff |
| Semantic Scholar | `src/ingestion/semantic_scholar.py` | Public API | 100 req/5min batch |
| Springer Nature | `src/ingestion/springer.py` | API key | Exponential backoff |
| OpenAlex | `src/ingestion/openalex.py` | Public API | Polite crawl delay |
| DBLP | `src/ingestion/dblp.py` | Public API | Basic rate limit |
| Elsevier/Scopus | `src/ingestion/elsevier.py` | API key + institutional token | Exponential backoff |
| CORE | `src/ingestion/core.py` | API key | Exponential backoff |
| CrossRef | `src/ingestion/crossref.py` | Public API | Polite crawl delay |
| OpenArchives | `src/ingestion/openarchives.py` | Public OAI-PMH | Polite crawl delay |
| PubMed | `src/ingestion/pubmed.py` | Public NCBI API | 3 req/sec |
| Sci.gov | `src/ingestion/scigov.py` | Public API | Basic rate limit |
| OSTI.gov | `src/ingestion/osti.py` | Public API | Basic rate limit |
| PLOS | `src/ingestion/plos.py` | Public API | Basic rate limit |

### 2.3 Ingestion Pipelines

- **Daily Search** (`src/ingestion/daily_search.py`): Concurrent 14-source fetch with deduplication and two-stage AI evaluation (Flash pre-screen, Pro deep analysis)
- **Historical Search** (`src/ingestion/historic_search.py`): Year-by-year backfill with epoch deduplication logic
- **Grey Literature Miner** (`src/ingestion/grey_literature_miner.py`): DuckDuckGo web search for preprints, technical reports, and white papers
- **PDF Downloader** (`src/ingestion/pdf_downloader.py`): ThreadPoolExecutor-batched Open Access PDF retrieval
- **Zotero Connector** (`src/ingestion/zotero_connector.py`): Bi-directional sync with Zotero cloud library (graceful pyzotero import degradation)
- **Metadata Enricher** (`src/ingestion/metadata_enricher.py`): DOI resolution and metadata augmentation via OpenAlex, Crossref, DBLP, Semantic Scholar fallback chain
- **Data Enricher** (`src/ingestion/data_enricher.py`): Unpaywall API integration for OA status and PDF links

---

## Section 3: AI Provider System & Multi-Tier LLM Routing

### 3.1 Provider Architecture (AIManager v3.7)

The AI Manager (`src/core/ai_manager.py`) implements a multi-provider architecture with automatic fallback and circuit breaker pattern across four independent providers:

| Provider | Type | SDK | Authentication | Use Case |
|----------|------|-----|----------------|----------|
| Gemini | Cloud | google-generativeai | GEMINI_API_KEY | Primary cloud text generation + embedding fallback |
| DeepSeek | Cloud | OpenAI-compatible API | DEEPSEEK_API_KEY | Fallback cloud provider |
| HuggingFace | Cloud (free) | OpenAI-compatible API | HF_TOKEN | Free cloud inference via router.huggingface.co |
| Local/Ollama | Local | OpenAI-compatible API | TALOS_USE_LOCAL=1 | Offline-first operation |

### 3.2 Circuit Breaker Pattern

- Failure threshold: 5 consecutive failures
- On threshold exceeded: circuit opens, provider skipped for rest of session
- On success: failure counter resets to 0
- Rate limit errors (HTTP 429) counted separately -- only trip circuit after multiple consecutive rate limits

### 3.3 Multi-Tier Routing Architecture (v5.7.1 + v5.9.1)

TALOS implements a three-tier LLM routing architecture with independent per-tier routing control:

| Tier | Default Model | Default Endpoint | Routing Env Var |
|------|---------------|------------------|-----------------|
| **Fast Edge** | fermionresearch/Neutrino-8B | http://127.0.0.1:11435/v1 | TALOS_FAST_ROUTING |
| **Heavy Reasoning** | qwen2.5:14b | http://127.0.0.1:11434 | TALOS_HEAVY_ROUTING |
| **Cloud Provider** | Gemini / DeepSeek / HF | API endpoints | TALOS_CLOUD_PROVIDER |

### 3.4 4-Way Execution Mode Matrix (v5.9.1)

The system supports four distinct routing combinations via the `model_manager.py` selector:

| Mode | Fast Tier Routing | Heavy Tier Routing | Use Case |
|------|-------------------|-------------------|----------|
| **1. Pure Local** | Local CPU (Neutrino-8B) | Local GPU (Qwen-14B) | Air-gapped operation |
| **2. Edge-to-Cloud Hybrid** | Local CPU (Neutrino-8B) | Cloud API (Gemini) | Fast screening + deep cloud analysis |
| **3. Cloud-to-Edge Hybrid** | Cloud API (Gemini) | Local GPU (Qwen-14B) | Cloud pre-screening + local deep analysis |
| **4. Pure Cloud** | Cloud API (Gemini) | Cloud API (Gemini) | Maximum throughput, no local compute |

### 3.5 Interactive Runtime Cloud Fallback (v5.9.3)

- On `ConnectionError` in `_execute_fast_tier_request`, the system checks `sys.stdin.isatty()`
- If interactive terminal: prompts via `questionary` -- "Local model connection failed. Switch to Cloud fallback?"
- If Yes: sets `TALOS_FAST_ROUTING=cloud` in `os.environ` for the session
- If No or non-interactive: fails gracefully with a log message
- Heavy tier also supports the same mechanism via `_interactive_cloud_fallback(tier="heavy")`

### 3.6 HYBRID Embedding Generation

- **Primary:** Ollama native `/api/embed` (nomic-embed-text, 768 dimensions)
- **Fallback:** Gemini `gemini-embedding-001` via `google-genai` SDK v2 (768 dimensions)
- **Deprecated:** HuggingFace embedding (removed due to DNS issues with api-inference endpoints)
- **Result:** Returns `(List[List[float]], model_name)` tuple for model-tagging in database

---

## Section 4: Deep Reinforcement Learning & Optimization (DDDQN + GWO)

### 4.1 DRL Agent Architecture

The TALOS DRL Agent (`src/ai/drl/`) employs a **Double Dueling Deep Q-Network with 3-layer LSTM** (DuelingLSTM architecture) trained on real paper evaluation scores.

| Component | Value |
|-----------|-------|
| Network Architecture | Double Dueling DQN with LSTM |
| State Space | 14-source environment (one-hot encoded) |
| Action Space | Selection of optimal API source |
| Reward Signal | Paper quality score (strategic + operational + tactical + playground) |
| Exploration | Epsilon-greedy with exponential decay |
| Persistence | `models/dddqn_trained.pth` |

### 4.2 GWO Hyperparameter Optimization

The Grey Wolf Optimizer (`src/ai/optimizers/gwo_rl_optimizer.py`) tunes the DRL agent's hyperparameters via a bio-inspired swarm intelligence algorithm (Mirjalili 2014).

| Parameter | Optimized Value | Range |
|-----------|----------------|-------|
| Learning Rate | 3.361e-05 | [1e-6, 1e-2] |
| Gamma (Discount) | 0.6983 | [0.5, 0.999] |
| Epsilon Decay | 0.9202 | [0.8, 0.999] |
| Best Fitness | From `models/gwo_best_params.json` | -- |
| Best Avg Reward | From `models/gwo_best_params.json` | -- |

- **GWO API:** `POST /api/v1/optimize/gwo` triggers optimization in background
- **GWO History:** `GET /api/v1/optimize/gwo/history` returns iteration-by-iteration data for Recharts
- **GWO Live Dashboard:** Dash-based 3D scatter plot at http://localhost:8050

### 4.3 Autonomous System Tester (RL-Driven Chaos Engineering) -- v5.9.0

The Autonomous System Tester (`src/ai/testing/autonomous_tester.py`) stress-tests TALOS components using a Non-Stationary Epsilon-Greedy Multi-Armed Bandit with LLM-as-a-Judge diagnostics.

| Component | Value |
|-----------|-------|
| Algorithm | Non-Stationary Epsilon-Greedy MAB |
| Epsilon | 0.2 |
| Learning Rate (Alpha) | 0.1 |
| Target Components | FastAPI Server, MCP Server, Daily Search, Citation Analyzer |
| Test Method | Subprocess launch with 5-second timeout |
| Rewards | +50 (crash detected), -1 (pass) |
| Diagnostics | Fast Edge LLM (tier="fast") provides 2-sentence crash analysis |
| Persistence | `data/tester_q_table.json` (Q-table) |
| Reports | `reports/autonomous_tester/CRASH_REPORT_{timestamp}.md` |
| Fragility Labels | STABLE, LOW, MODERATE, HIGH_FRAGILITY |
| Synapse Integration | Emits events on each test cycle |
| API Endpoints | `GET /api/v1/tester/status`, `GET /api/v1/tester/reports` |

---

## Section 5: SYNAPSE Event-Driven Protocol (v5.7.0)

### 5.1 Architecture

TALOS participates in the ALEXANDRIA Ecosystem via the SYNAPSE Event-Driven Protocol, implemented across two modules:

| Module | Role | Port |
|--------|------|------|
| `src/integration/synapse_client.py` | EventEmitter -- pushes JSON events OUT | Dest: localhost:8000 |
| `src/api/synapse_routes.py` | Webhook Receiver -- accepts commands IN | Listen: :8001/api/v1/synapse/webhook |

### 5.2 Outbound Event Types

| Event Type | Trigger | Payload |
|------------|---------|---------|
| `paper_discovered` | New paper found during scrape | DOI, title, source, score |
| `paper_evaluated` | AI evaluation complete | Paper ID, scores, reasoning |
| `search_completed` | Search pipeline finishes | Source count, total papers, duration |
| `gwo_optimized` | GWO run complete | Best params, best reward, iterations |
| `agent_step` | DRL agent takes an action | Episode, step, action, reward |
| `agent_episode_end` | DRL episode terminates | Episode, total reward, epsilon |

### 5.3 Event Schema (Mandatory Fields)

```json
{
  "event_id": "UUID4",
  "timestamp": "ISO 8601",
  "event_type": "paper_discovered | paper_evaluated | search_completed | gwo_optimized | agent_step | agent_episode_end",
  "source": "talos",
  "payload": {}
}
```

### 5.4 Inbound Commands (Webhook)

`POST /api/v1/synapse/webhook` accepts:

| Command | Parameters | Action |
|---------|-----------|--------|
| `trigger_search` | `{source_filter: [...]}` | Triggers daily search pipeline |
| `trigger_evaluation` | `{paper_id: int}` | Evaluates a specific paper |
| `get_status` | `{}` | Returns system health |
| `shutdown` | `{}` | Graceful process shutdown |

---

## Section 6: REST API Reference (18 Endpoints)

### 6.1 Endpoint Catalog

| ID | Method | Path | Description | Response Model |
|----|--------|------|-------------|---------------|
| E01 | GET | `/api/v1/health` | System health, DB stats, embedding coverage | `SystemHealth` |
| E02 | GET | `/api/v1/papers` | Paginated paper list | `PaginatedPapers` |
| E03 | GET | `/api/v1/papers/{paper_id}` | Full paper detail (all 28 columns) | `PaperDetail` |
| E04 | POST | `/api/v1/papers/{paper_id}/evaluate` | Single-paper AI evaluation (BgTasks) | `TaskStatus` |
| E05 | POST | `/api/v1/search/semantic` | Natural-language semantic (vector) search | `SemanticSearchResponse` |
| E06 | POST | `/api/v1/scrape/trigger` | Trigger daily scrape pipeline (BgTasks) | `TaskStatus` |
| E07 | POST | `/api/v1/optimize/gwo` | Trigger GWO hyperparameter optimization (BgTasks) | `TaskStatus` |
| E08 | GET | `/api/v1/optimize/gwo/history` | GWO optimization history for Recharts | `List[dict]` |
| E09 | GET | `/api/v1/graph/view` | Serve architecture dependency graph HTML | `FileResponse` |
| E10 | POST | `/api/v1/ai/translate-query` | Natural-language to boolean query translation | `TranslateQueryResponse` |
| E11 | GET | `/api/v1/analysis/authors` | Top authors from database (for BarChart) | `List[AuthorSummary]` |
| E12 | POST | `/api/v1/db/recalculate-scores` | Bulk overall_score recalculation (BgTasks) | `TaskStatus` |
| E13 | GET | `/api/v1/tasks/{task_id}` | Background task status | `TaskStatus` |
| E14 | GET | `/api/v1/tasks` | List all background tasks | `List[TaskStatus]` |
| E15 | GET | `/api/v1/capabilities` | Serve System Capabilities Master HTML | `HTMLResponse` |
| E16 | POST | `/api/v1/synapse/webhook` | SYNAPSE protocol inbound command receiver | `SynapseWebhookResponse` |
| E17 | GET | `/api/v1/tester/status` | Autonomous System Tester Q-table status | `TesterStatusResponse` |
| E18 | GET | `/api/v1/tester/reports` | List crash report metadata | `List[CrashReport]` |

### 6.2 Pydantic v2 Model Inventory

The API defines 16 Pydantic v2 models:

`PaperSummary`, `PaperDetail`, `PaginatedPapers`, `SemanticSearchRequest`, `SemanticSearchResponse`, `ScrapeRequest`, `GWORunRequest`, `GWOResult`, `TaskStatus`, `SystemHealth`, `TranslateQueryRequest`, `TranslateQueryResponse`, `AuthorSummary`, `EvaluatePaperRequest`, `TesterStatusResponse`, `CrashReport`

### 6.3 Background Task System

- **Task Store:** Thread-safe `_task_store` dict with locking
- **Task Lifecycle:** `queued -> running -> completed|failed`
- **Task ID:** 8-character hex UUID prefix
- **Polling:** `GET /api/v1/tasks/{task_id}` for individual status, `GET /api/v1/tasks` for all tasks
- **Long-Running Tasks:** Daily scrape (14 APIs), GWO optimization (minutes), Single-paper evaluation, Bulk score recalculation

---

## Section 7: MCP Server Tools

### 7.1 MCP Server Architecture

`src/mcp_server.py` implements a Model Context Protocol (MCP) server that exposes TALOS capabilities to MCP-compatible clients such as Cherry Studio, Claude Desktop, and other AI assistants.

### 7.2 MCP Tool Inventory

| Tool Name | Description | Parameters |
|-----------|-------------|------------|
| `talos_query_database` | Query the TALOS research database with SQL | `{query: str}` |
| `talos_semantic_search` | Perform semantic search across papers | `{query: str, top_k: int}` |
| `talos_evaluate_paper` | Evaluate a paper abstract with AI | `{abstract: str, model_type: str}` |
| `talos_trigger_gwo` | Trigger GWO hyperparameter optimization | `{wolves: int, iterations: int}` |
| `talos_trigger_scrape` | Trigger daily search pipeline | `{source_filter: list}` |
| `talos_get_health` | Get system health status | `{}` |
| `talos_list_papers` | List papers with pagination | `{page: int, page_size: int}` |
| `talos_translate_query` | Translate NL research goal to boolean queries | `{query: str}` |

### 7.3 MCP Server Configuration

- **Transport:** stdio (standard input/output)
- **Auto-Config:** Cherry Studio MCP config generated by `src/utils/frontend_provisioner.py`
- **Launch:** `python src/mcp_server.py` or via `run_talos.bat` Option 3

---

## Section 8: Analysis & Reporting Modules

### 8.1 Analysis Module Inventory

| Module | Path | Function |
|--------|------|----------|
| Citation Network Analyzer | `src/analysis/citation_analyzer.py` | Citation graph construction and analysis |
| Author Profiler | `src/analysis/author_profiler.py` | Author publication history and impact profiling |
| Author Trajectory Analyzer | `src/analysis/author_trajectory_analyzer.py` | Career trajectory analysis via ORCID |
| Trend Analyzer | `src/analysis/trend_analyzer.py` | Scientometrics and publication trend analysis |
| Architecture Intelligence Report | `src/analysis/architecture_intelligence_report.py` | System architecture health and dependency analysis |
| Knowledge Path Generator | `src/analysis/knowledge_path_generator.py` | Research path discovery and literature mapping |
| Recommender | `src/analysis/recommender.py` | Strategic reading recommendations |
| Baseline Report Generator | `src/analysis/generate_baseline_report.py` | Two-mode reports: Standard + Academic (600 DPI, serif fonts) |
| Architecture Graph Generator | `src/analysis/generate_architecture_graph.py` | D3.js interactive dependency graph |

### 8.2 Query Translator (PYTHIA)

`src/ai/llm/query_translator.py` translates natural-language research goals into 14 optimized boolean search queries. Uses AIManager with "Research Architect" persona. Output saved to `config.json` as `*_query` keys.

### 8.3 Model Manager

`src/ai/llm/model_manager.py` provides a Rich TUI for configuring:
- Fast Edge Tier model and endpoint
- Heavy Reasoning Tier model and endpoint
- Cloud Provider selection (Gemini/DeepSeek/HuggingFace)
- Execution Mode selection (4-Way Matrix)
- Embedding model selection
- VRAM-aware model size validation and fitness indicators

---

## Section 9: Database & Persistence

### 9.1 Database Schema

| Table | Purpose | Key Columns |
|-------|---------|-------------|
| `papers` | Primary paper storage | id, doi, title, abstract, authors, source, publication_year, strategic_score, operational_score, tactical_score, playground_score, overall_score, evaluation_reasoning, enrichment_status, oa_pdf_url |
| `embeddings` | Vector embeddings | paper_id, embedding (BLOB), model_name |
| `enrichment_log` | Enrichment tracking | paper_id, source, timestamp, status |

### 9.2 Scoring Framework (4-Layer Invariant)

| Layer | Weight | Description |
|-------|--------|-------------|
| Strategic | 30% | Long-term research alignment and field impact |
| Operational | 30% | Methodological rigor and reproducibility |
| Tactical | 30% | Immediate utility for current research goals |
| Playground | 10% | Creative/exploratory potential |

### 9.3 Semantic Search

- Cosine similarity computation against all stored embeddings
- Model-aware filtering: `model_filter` parameter restricts to specific embedding model
- Returns top_k results with full paper metadata

### 9.4 Profile System

- Isolated profiles under `_profiles/<name>/` with independent `config.json` and `talos_research.db`
- Profile switching via `src/core/profile_manager.py`

---

## Section 10: TUI & CLI Reference

### 10.1 Entry Points

| Entry Point | File | Type |
|-------------|------|------|
| TUI Dashboard | `talos.py` | Rich-powered interactive terminal (11 options) |
| Batch Launcher (Win) | `run_talos.bat` | 10-option batch menu |
| Batch Launcher (POSIX) | `run_talos.sh` | 10-option bash menu |

### 10.2 talos.py Features

- Dynamic status table: Conda environment, API port, Synapse bus, execution mode, active LLM tiers
- Active Research Focus row: displays LLM-generated 6-10 word summary from `active_focus_summary` in config.json
- Dynamic Focus Summarization: auto-generates summary via Fast Edge LLM on startup if missing
- Silent initialization: reads TALOS_USE_LOCAL from .env directly (no interactive prompts)
- 11-option menu with Model Manager integration, CLI research search, Autonomous System Tester, System diagnostics

### 10.3 run_talos.bat/sh Features

- Section 1: REST API & FRONTEND (Full Setup, FastAPI server, MCP server, Cherry Studio UI)
- Section 2: CLI & STANDALONE DAEMONS (TALOS CLI, Autonomous Research Daemon, Live DRL Agent)
- Section 3: TESTING & SYSTEM (Autonomous System Tester, Pytest suite, Exit)
- Auto-Conda path detection (Windows), virtualenv/Conda detection (POSIX)
- Background minimized/spawned server windows
- Fermion CPU accelerator auto-start for Neutrino-8B

---

## Section 11: Configuration & Environment

### 11.1 Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| TALOS_USE_LOCAL | (unset) | Enable local-only Ollama mode |
| TALOS_FAST_ROUTING | local | Fast tier routing: "local" or "cloud" |
| TALOS_HEAVY_ROUTING | local | Heavy tier routing: "local" or "cloud" |
| TALOS_EXECUTION_MODE | local | System-wide mode: "local", "hybrid", "cloud" |
| TALOS_CLOUD_PROVIDER | gemini | Default cloud provider |
| TALOS_ALLOW_CLOUD_FALLBACK | (unset) | Enable cloud fallback for local mode |
| TALOS_ALLOW_LOCAL_FALLBACK | (unset) | Enable local fallback for cloud mode |
| GEMINI_API_KEY | (unset) | Gemini API key |
| DEEPSEEK_API_KEY | (unset) | DeepSeek API key |
| HF_TOKEN | (unset) | HuggingFace API token |
| FAST_EDGE_MODEL | fermionresearch/Neutrino-8B | Fast edge model name |
| FAST_EDGE_BASE_URL | http://127.0.0.1:11435/v1 | Fast edge endpoint |
| HEAVY_REASONING_MODEL | qwen2.5:14b | Heavy reasoning model name |
| OLLAMA_BASE_URL | http://127.0.0.1:11434 | Standard Ollama endpoint |

### 11.2 config.json Keys

- `active_focus_summary`: 6-10 word LLM-generated research focus title (v5.9.3)
- `user_research_goal`: Raw natural-language research goal
- `phd_focus_system_prompt`: System prompt for AI evaluation persona
- `pre_screening_prompt`: Prompt for flash tier pre-screening
- `query_translator_prompt`: Meta-prompt for PYTHIA Query Translator
- `*_query` (14 keys): Boolean search queries for each academic source
- `ai_provider_priority`: Ordered list of provider names
- `failure_threshold`: Circuit breaker failure threshold

---

## Section 12: Documentation Canon (15-File Sync)

### 12.1 The 15 Canonical Files

| # | File | Language | Purpose |
|---|------|----------|---------|
| 1 | `.clinerules` | EN | Constitution v2.0 + AI agent instructions |
| 2 | `README.md` | EN | Project overview and quickstart |
| 3 | `docs/ROADMAP.md` | EN | Strategic roadmap and version history |
| 4 | `docs/CHANGELOG_EN.md` | EN | Detailed changelog (English) |
| 5 | `docs/CHANGELOG_GR.md` | GR | Detailed changelog (Greek) |
| 6 | `docs/PROJECT_MAP.md` | GR | Complete project map (Greek master) |
| 7 | `docs/PROJECT_MAP_EN.md` | EN | Complete project map (English) |
| 8 | `docs/TIMELINE_EN.md` | EN | Historical timeline (English) |
| 9 | `docs/TIMELINE_GR.md` | GR | Historical timeline (Greek) |
| 10 | `docs/internal/API_HANDOVER_FOTIS.md` | EN | API handover reference |
| 11 | `docs/internal/UX_UI_BLUEPRINT_FOTIS.md` | EN | UX/UI blueprint |
| 12 | `docs/internal/IP_PROTECTION_STRATEGY.md` | EN | IP protection strategy |
| 13 | `docs/SYSTEM_CAPABILITIES_MASTER.md` | EN | Capabilities reference (Markdown) |
| 14 | `docs/SYSTEM_CAPABILITIES_MASTER.html` | EN | Capabilities reference (HTML) |
| 15 | `docs/TECH_RADAR.md` | EN | Technology radar and stack choices |

### 12.2 Code Version Synchronicity (5 Files)

| # | File | Version String Location |
|---|------|------------------------|
| 1 | `talos.py` | Module docstring + printed banner |
| 2 | `run_talos.bat` | Window title, banner text, section headers |
| 3 | `run_talos.sh` | Script header comment, banner text, section headers |
| 4 | `config/settings.py` | `TALOS_VERSION` constant |
| 5 | `src/api/main_api.py` | `app.version` FastAPI metadata string |

---

## Section 13: v5.9.3 New Capabilities

### 13.1 Purged Legacy Prompts

- Removed interactive `questionary` prompts "Where to run AI calls? LOCAL/CLOUD" from `talos.py`
- TALOS now reads `TALOS_USE_LOCAL` from `.env` directly -- silent initialization

### 13.2 Dynamic Focus Summarization

- New function `_maybe_generate_focus_summary()` in `talos.py`
- Automatically generates 6-10 word research focus title via Fast Edge LLM on startup
- Saves to `active_focus_summary` in `config.json`
- Displayed in TUI header in bold bright green

### 13.3 Interactive Runtime Cloud Fallback

- New method `_interactive_cloud_fallback()` in `AIManager`
- Catches `ConnectionError` in Fast Edge tier requests
- Uses `sys.stdin.isatty()` for interactivity check
- Prompts with `questionary` for cloud fallback in interactive sessions
- Graceful degradation for non-interactive sessions

### 13.4 Exhaustive Capabilities Sync Rule

- New `CRITICAL` rule in `.clinerules` (Section VII in Constitution)
- Mandates complete rewrite of `SYSTEM_CAPABILITIES_MASTER.md` and `.html` during every version bump
- Covers 100% of endpoints, agents, routing matrices, MCP tools, Synapse events, and RL components

---

> **Project TALOS** -- From Aggregator to Autonomous Research Architect.
> Built in Kalamata, Greece.
> (C) 2026 Christos Smarlamakis. All rights reserved.