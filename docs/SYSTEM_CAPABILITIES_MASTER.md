# TALOS/ALEXANDRIA/ATHENA -- System Capabilities Master Reference v5.10.10

> **Document ID:** TALOS-SYS-CAP-001
> **Classification:** Public Reference
> **Scope:** TALOS Research Intelligence Platform (Headless FastAPI Backend + React Frontend + SYNAPSE Protocol + Graphify AST Intelligence)
> **Last Updated:** 2026-08-22
> **Version:** v5.10.10 -- Enterprise TUI Overhaul & Academic Aesthetics

[![IEEE Computer Society WEIGD Fund 2026](https://img.shields.io/badge/IEEE_Computer_Society-WEIGD_Fund_Recipient_2026-006699?style=flat-square&logo=ieee&logoColor=white)](https://www.computer.org/)

---

## Section 1: System Vision & Core Architecture

### 1.1 Foundational Principle

TALOS is an autonomous Research Intelligence Platform that ingests, evaluates, synthesizes, and visualizes scientific knowledge across 16 academic sources. It replaces manual systematic literature review workflows with an AI-driven, DRL-orchestrated pipeline that maintains a human-in-the-loop at every critical decision boundary. The system operates as a microservice within the broader ALEXANDRIA Ecosystem -- a distributed research intelligence mesh that communicates via the SYNAPSE Event-Driven Protocol. Starting in v5.9.10, TALOS also introspects its own codebase through a vendored Graphify AST Knowledge Graph engine, generating interactive dependency visualizations and architectural intelligence reports directly from source code.

### 1.2 Architectural Pillars

The system operates as a five-layer architecture:

| Layer | Component | Role |
|-------|-----------|------|
| **Frontend** | React 18 with Tailwind CSS and Shadcn UI | User-facing dashboard leveraging the REST API |
| **Backend** | `src/api/main_api.py` (19 endpoints) | Headless FastAPI facade exposing all core capabilities |
| **AI Core** | `src/core/ai_manager.py` (9 providers -- Universal Cloud Mesh + circuit breaker + 2D matrix) | Multi-provider LLM orchestration with hardware-aware routing and interactive cloud fallback |
| **Persistence** | `src/core/database_manager.py` | SQLite + multi-model vector embeddings (Ollama + Gemini) |
| **Integration** | `src/integration/synapse_client.py` + `src/mcp_server.py` + `src/analysis/graphify_adapter.py` | SYNAPSE Event Bus + MCP Tool Server + AST Knowledge Graph Intelligence |

### 1.3 Data Flow

```
User (React UI) --> FastAPI (:8001) --> src/core/*.py --> src/ingestion/*.py --> External APIs
                          ^                                    |
                          |                                    v
                     SYNAPSE Bus (:8000)              data/talos_research.db
                          |                          (SQLite + Embeddings)
                     MCP Server (Cherry Studio)             ^
                          |                                 |
              vendor/graphify/ --> AST KG --> data/reports/graphify_out/
                          |                                 |
                     config.json + .env (Configuration + Secrets)
```

### 1.4 Operational Modes

- **Production:** Headless FastAPI listener on port 8001, React frontend consuming the API
- **Development:** `uvicorn src.api.main_api:app --reload --port 8001`
- **Background Services:** Scraping pipeline, GWO optimizer, DRL training, Autonomous Red Tester -- all via FastAPI BackgroundTasks
- **CLI:** `talos.py` (Rich-powered TUI, 11 options) retains full terminal-mode access for maintenance, diagnostics, and Graphify AST generation
- **SYNAPSE Webhook:** `POST /api/v1/synapse/webhook` receives external commands from other ALEXANDRIA microservices
- **MCP Server:** `src/mcp_server.py` exposes 4 tools (system_status, semantic_search, paper_details, trigger_scrape) to MCP-compatible clients like Cherry Studio
- **Graphify AST Pipeline:** `src/analysis/graphify_adapter.py` generates interactive D3.js AST knowledge graphs from the TALOS codebase via vendored Graphify engine, with academic print theme toggle

### 1.5 System Constants

| Constant | Value | Source File |
|----------|-------|-------------|
| TALOS_VERSION | "5.10.5" | `config/settings.py` |
| TALOS_API_PORT | 8001 | `config/settings.py` |
| SYNAPSE_BUS_URL | http://localhost:8000/api/v1/events | `config/settings.py` |
| FAST_EDGE_MODEL | fermionresearch/Neutrino-8B | `config/settings.py` |
| FAST_EDGE_BASE_URL | http://127.0.0.1:11435/v1 | `config/settings.py` |
| HEAVY_REASONING_MODEL | qwen2.5:14b | `config/settings.py` |
| OLLAMA_BASE_URL | http://127.0.0.1:11434 | `config/settings.py` |
| TALOS_NETWORK_STRATEGY | strict_local | `config/settings.py` |
| TALOS_HARDWARE_STRATEGY | cpu_gpu_split | `config/settings.py` |
| TALOS_FAST_ROUTING | local | `config/settings.py` |
| TALOS_HEAVY_ROUTING | local | `config/settings.py` |
| DEFAULT_TIER | fast | `config/settings.py` |
| TALOS_CLOUD_PROVIDER | gemini | `config/settings.py` |

---

## Section 2: Multi-Source Ingestion Engine

### 2.1 The "Genesis" Operation

TALOS ingests academic literature from **16 independent APIs**, each implemented as a standalone source agent under `src/ingestion/`. Every agent conforms to a standardized output format:

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

### 2.2 Source Agent Inventory (16 APIs)

| Source | Module | Auth Model | Rate Limit Handling |
|--------|--------|-----------|---------------------|
| ArXiv | `src/ingestion/arxiv.py` | Public API | Exponential backoff |
| IEEE Xplore | `src/ingestion/ieee.py` | API key | Exponential backoff |
| Semantic Scholar | `src/ingestion/semantic_scholar.py` | Public API | 100 req/5min batch |
| Springer Nature | `src/ingestion/springer.py` | API key | Exponential backoff |
| OpenAlex | `src/ingestion/openalex.py` | Public API | Polite crawl delay |
| DBLP | `src/ingestion/dblp.py` | Public API | Basic rate limit |
| Elsevier/Scopus | `src/ingestion/elsevier.py` | API key + institutional token (elsapy, graceful import degradation) | Exponential backoff |
| CORE | `src/ingestion/core.py` | API key | Exponential backoff |
| CrossRef | `src/ingestion/crossref.py` | Public API | Polite crawl delay |
| OpenArchives | `src/ingestion/openarchives.py` | Public OAI-PMH | Polite crawl delay |
| PubMed | `src/ingestion/pubmed.py` | Public NCBI API | 3 req/sec |
| Sci.gov | `src/ingestion/scigov.py` | Public API | Basic rate limit |
| OSTI.gov | `src/ingestion/osti.py` | Public API | Basic rate limit |
| PLOS | `src/ingestion/plos.py` | Public API | Basic rate limit |
| OpenReview | `src/ingestion/openreview.py` | Public API (optional credentials) | Rate limit + backoff |
| OpenAIRE | `src/ingestion/openaire.py` | Public API (optional bearer token) | Rate limit + backoff |

### 2.3 Ingestion Pipelines

- **Daily Search** (`src/ingestion/daily_search.py`): Concurrent 16-source fetch with deduplication and two-stage AI evaluation (Flash pre-screen, Pro deep analysis)
- **Historical Search** (`src/ingestion/historic_search.py`): Year-by-year backfill with epoch deduplication logic
- **Grey Literature Miner** (`src/ingestion/grey_literature_miner.py`): DuckDuckGo web search for preprints, technical reports, and white papers
- **PDF Downloader** (`src/ingestion/pdf_downloader.py`): ThreadPoolExecutor-batched Open Access PDF retrieval (15 workers)
- **Zotero Connector** (`src/ingestion/zotero_connector.py`): Bi-directional sync with Zotero cloud library (graceful pyzotero import degradation)
- **Metadata Enricher** (`src/ingestion/metadata_enricher.py`): DOI resolution and metadata augmentation via OpenAlex, Crossref, DBLP, Semantic Scholar fallback chain
- **Data Enricher** (`src/ingestion/data_enricher.py`): Unpaywall API integration for OA status and PDF links

---

## Section 3: AI Provider System & Multi-Tier LLM Routing

### 3.1 Provider Architecture (AIManager v3.9+)

The AI Manager (`src/core/ai_manager.py`) implements a nine-provider Universal Cloud Mesh (v5.9.18) with automatic fallback and independent per-provider circuit breakers. Gemini remains the primary non-OpenAI-compatible path via the Google Generative AI SDK, while eight OpenAI-compatible redundancy providers are driven by a unified dictionary registry (`OPENAI_COMPATIBLE_REGISTRY`) and a single request handler (`_execute_openai_compatible_request`):

| Provider | Type | SDK | Authentication | Use Case |
|----------|------|-----|----------------|----------|
| Gemini | Cloud | google-genai SDK | GEMINI_API_KEY | Primary cloud text generation + embedding fallback |
| NVIDIA NIM | Cloud | OpenAI-compatible | NVIDIA_API_KEY | `nvidia/nemotron-3-ultra` (integrate.api.nvidia.com/v1) |
| Groq | Cloud | OpenAI-compatible | GROQ_API_KEY | `llama-3.3-70b-versatile` (api.groq.com) |
| Cerebras | Cloud | OpenAI-compatible | CEREBRAS_API_KEY | `llama-3.1-70b` (api.cerebras.ai) |
| GitHub Models | Cloud | OpenAI-compatible | GITHUB_TOKEN | `gpt-4o-mini` (models.inference.ai.azure.com) |
| Mistral | Cloud | OpenAI-compatible | MISTRAL_API_KEY | `mistral-small-latest` (api.mistral.ai) |
| OpenRouter | Cloud | OpenAI-compatible | OPENROUTER_API_KEY | `meta-llama/llama-3.3-70b-instruct:free` (openrouter.ai) |
| DeepSeek | Cloud | OpenAI-compatible | DEEPSEEK_API_KEY | `deepseek-chat` (api.deepseek.com) |
| HuggingFace | Cloud | OpenAI-compatible | HF_TOKEN | `meta-llama/Llama-3.3-70B-Instruct` (router.huggingface.co) |
| Local/Ollama | Local | OpenAI-compatible | TALOS_USE_LOCAL=1 | Offline-first operation |

The failover cascade iterates `ai_provider_priority` (default: `["local", "nvidia", "groq", "cerebras", "github", "gemini", "deepseek", "mistral", "openrouter", "huggingface"]`), skipping unconfigured providers and open circuits. `last_provider_used` records the exact provider that served each successful request.

### 3.2 Circuit Breaker Pattern

- Failure threshold: 5 consecutive failures
- On threshold exceeded: circuit opens, provider skipped for rest of session
- On success: failure counter resets to 0
- Rate limit errors (HTTP 429) counted separately -- only trip circuit after multiple consecutive rate limits

### 3.3 Multi-Tier LLM Routing Architecture (v5.7.1 + v5.9.1)

TALOS implements a three-tier LLM routing architecture with independent per-tier routing control:

| Tier | Default Model | Default Endpoint | Routing Env Var |
|------|---------------|------------------|-----------------|
| **Fast Edge** | fermionresearch/Neutrino-8B | http://127.0.0.1:11435/v1 | TALOS_FAST_ROUTING |
| **Heavy Reasoning** | qwen2.5:14b | http://127.0.0.1:11434 | TALOS_HEAVY_ROUTING |
| **Cloud Provider** | Universal Cloud Mesh (9 providers) | API endpoints | TALOS_CLOUD_PROVIDER |

### 3.4 Local-to-Local Fallback (v5.9.8)

When the Fast Edge CPU tier (port 11435) fails with a `ConnectionError`, the system automatically falls back to the local GPU Ollama endpoint (port 11434) **first**, preserving air-gapped operation. Only if both local endpoints fail does it attempt cloud fallback (when network strategy permits).

### 3.5 2D Execution Matrix (Network x Hardware Strategies) -- v5.9.4

The legacy `TALOS_EXECUTION_MODE` is superseded by a richer 2D model controlling network dependency and hardware device independently:

#### Network Strategy (TALOS_NETWORK_STRATEGY)

| Strategy | Local Inference | Cloud Inference | Cross-Environment Fallback |
|----------|----------------|-----------------|---------------------------|
| **strict_local** | Required | Forbidden | Never |
| **local_first** | Primary | Fallback | Local -> Cloud on ConnectionError |
| **cloud_first** | Fallback | Primary | Cloud -> Local on any cloud failure |
| **strict_cloud** | Forbidden | Required | Never |

#### Hardware Strategy (TALOS_HARDWARE_STRATEGY)

| Strategy | Fast Tier Endpoint | Heavy Tier Endpoint | 
|----------|--------------------|---------------------|
| **cpu_only** | Port 11435 (CPU) | Port 11435 (CPU) -- GPU endpoint unused |
| **gpu_only** | Port 11434 (GPU) | Port 11434 (GPU) -- CPU endpoint unused |
| **cpu_gpu_split** | Port 11435 (CPU, Neutrino-8B) | Port 11434 (GPU, Qwen-14B) |

### 3.6 4-Way Execution Mode Matrix (v5.9.1)

For backward compatibility, the system also supports four distinct routing combinations via the Model Manager TUI:

| Mode | Fast Tier Routing | Heavy Tier Routing | Use Case |
|------|-------------------|-------------------|----------|
| **1. Pure Local** | Local CPU (Neutrino-8B) | Local GPU (Qwen-14B) | Air-gapped operation |
| **2. Edge-to-Cloud Hybrid** | Local CPU (Neutrino-8B) | Cloud API (Gemini) | Fast screening + deep cloud analysis |
| **3. Cloud-to-Edge Hybrid** | Cloud API (Gemini) | Local GPU (Qwen-14B) | Cloud pre-screening + local deep analysis |
| **4. Pure Cloud** | Cloud API (Gemini) | Cloud API (Gemini) | Maximum throughput, no local compute |

### 3.7 Interactive Runtime Cloud Fallback (v5.9.3)

- On `ConnectionError` in Fast Edge tier requests, the system checks `sys.stdin.isatty()`
- If interactive terminal: prompts via `questionary` -- "Local model connection failed. Switch to Cloud fallback?"
- If Yes: sets `TALOS_FAST_ROUTING=cloud` in `os.environ` for the session
- If No or non-interactive: fails gracefully with a log message
- Heavy tier also supports the same mechanism

### 3.8 HYBRID Embedding Generation

- **Primary:** Ollama native `/api/embed` (nomic-embed-text, 768 dimensions)
- **Fallback:** Gemini `gemini-embedding-001` via `google-genai` SDK v2 (768 dimensions)
- **Deprecated:** HuggingFace embedding (removed due to DNS issues with api-inference endpoints)
- **Result:** Returns `(List[List[float]], model_name)` tuple for model-tagging in database

---

### 3.4 Dynamic Model Discovery Engine (v5.10.4)

`src/ai/llm/model_discovery.py` (`ModelDiscoveryEngine`) discovers active LLM models across Ollama (GET /api/tags) and cloud providers (NVIDIA NIM, Groq, OpenRouter, Gemini GET /v1/models), with an air-gapped fallback to `data/model_benchmarks.json`. It computes `Q_p = raw / max(raw)` normalized quality scores and `get_provider_quality_scores()` for the router. `LLMRouterSubAgent.refresh_quality_scores()` / `load_quality_scores()` consume these dynamic signals.

### 3.5 Universal Dynamic Model Provisioner (v5.10.5)

`src/utils/model_provisioner.py` (`ModelProvisioner`) guarantees a model is available before routing. Deterministic `detect_protocol()` (cloud prefixes, Ollama colon, HuggingFace Hub slash) and a 3-tier `resolve_local_model_path()` (`FAST_EDGE_MODEL_PATH`, in-tree `models/<sanitized_name>`, network). `ensure_model_available()` performs JIT `ollama pull` / `huggingface_hub.snapshot_download` with a self-healing fallback that logs `[WARNING] Auto-provisioning failed ... Reverting to baseline model.` and returns `False` without crashing. Integrated into the SETUP routine and the Model Manager TUI.

## Section 4: Deep Reinforcement Learning & Optimization (DDDQN + GWO)

### 4.1 DRL Agent Architecture

The TALOS DRL Agent (`src/ai/drl/`) employs a **Double Dueling Deep Q-Network with 3-layer LSTM** (DuelingLSTM architecture) trained on real paper evaluation scores.

| Component | Value |
|-----------|-------|
| Network Architecture | DuelingLSTM (3-layer LSTM 128->64->32 + LayerNorm + dueling V/A heads) |
| State Space | Provider-aware: 1 + 16 sources + 2 streaks + 4 providers = 23 dimensions |
| Action Space | 16 sources + 1 sleep = 17 actions (indices 0..15 = sources, 16 = sleep) |
| Reward Signal | Paper quality score mapped via brackets: +20 (score >= 8.0), +5 (score >= 6.0), -10 (score < 6.0) |
| Exploration | Epsilon-greedy with exponential decay |
| GWO-Optimized Hyperparameters | LR=3.361e-05, GAMMA=0.6983, EPS_DECAY=0.9202 |
| Cooldown Mechanism | 5-step lockout for negative-reward actions with random override on sleep |
| Persistence | `models/dddqn_trained.pth`, `models/dddqn_partial.pth`, `models/talos_drl.pth` |

### 4.2 DRL Module Inventory

| Module | Purpose |
|--------|---------|
| `src/ai/drl/talos_env.py` (v3.2) | Gymnasium-compliant 16-source environment with 23-dim provider-aware observation space and 17-action space |
| `src/ai/drl/drl_networks.py` (v1.0) | Pluggable network architectures: DuelingLSTM with common (input_dim, output_dim) interface |
| `src/ai/drl/drl_agent.py` (v2.1) | Double Dueling DQN with `network_class` dependency injection and auto-reconstruction for 23/17 dimensions |
| `src/ai/drl/drl_trainer.py` (v1.4) | Epsilon-greedy training with Ctrl+C graceful partial save |
| `src/ai/drl/live_agent_sources.py` (v1.1) | Dynamic source discovery via module scanning (16 sources) |
| `src/ai/drl/live_agent_orchestrator.py` (v1.2) | Main loop with cooldown, provider tracking, reward calculation, 23-dim state |
| `src/ai/drl/talos_live_agent.py` (v3.2) | CLI entry for live API-fetching DRL agent with argparse |
| `src/ai/drl/talos_service.py` (v2.0) | 24/7 autonomous research daemon with Telegram/Discord/Email notifications |

### 4.3 GWO Hyperparameter Optimization

The Grey Wolf Optimizer (`src/ai/optimizers/gwo_foraging_hyperparameter_tuner.py` v2.1) tunes the DRL agent's hyperparameters via a bio-inspired swarm intelligence algorithm (Mirjalili 2014). Each wolf trains a fresh DRL agent; the pack converges toward the alpha wolf's position in 3D parameter space.

| Parameter | Optimized Value | Range |
|-----------|----------------|-------|
| Learning Rate | 3.361e-05 | [1e-6, 1e-2] |
| Gamma (Discount) | 0.6983 | [0.5, 0.999] |
| Epsilon Decay | 0.9202 | [0.8, 0.999] |

- **GWO API:** `POST /api/v1/optimize/gwo` triggers optimization in background
- **GWO History:** `GET /api/v1/optimize/gwo/history` returns iteration-by-iteration data for Recharts
- **GWO Live Dashboard:** Dash-based 3D scatter plot at http://localhost:8050
- **Model Artifacts:** `models/gwo_foraging_hyperparameters.json`, `models/gwo_history.json`, `models/gwo_progress.json`, `models/gwo_llm_router_reward_weights.json`

### 4.4 Autonomous Red Tester (RL-Driven Chaos Engineering) -- v5.9.0 / v5.9.7 / v5.9.16

The Autonomous Red Tester (`src/ai/testing/red_tester.py`) stress-tests TALOS components using a Non-Stationary Epsilon-Greedy Multi-Armed Bandit with LLM-as-a-Judge diagnostics. In v5.9.16 it was renamed from `autonomous_tester.py` and upgraded with Deep API Fuzzing and LLM Context Truncation.

| Component | Value |
|-----------|-------|
| Algorithm | Non-Stationary Epsilon-Greedy MAB |
| Epsilon | 0.2 |
| Learning Rate (Alpha) | 0.1 |
| Target Discovery | Hybrid discovery (`_discover_all_targets()`) -- 70+ CLI arms across `src/` plus 4 API fuzzing arms |
| Test Method | CLI: subprocess launch with `--help`; API: `requests` with 3-second timeout |
| Timeout | 5 seconds (CLI) / 3 seconds (API) per target cycle |
| Rewards | +50 (crash detected), -1 (pass) |
| Deep API Fuzzing | 4 arms against `http://127.0.0.1:8001`: malformed Synapse webhook JSON, negative paper ID, empty semantic query, invalid scrape source (v5.9.16) |
| Graceful Rejection | API 400/404/422 handled correctly = pass (reward -1) |
| Unhandled Exception | API HTTP 5xx or timeout = crash (reward +50, status/body fed to LLM) |
| Diagnostics | Fast Edge LLM (tier="fast") provides 2-sentence crash analysis |
| LLM Context Truncation | `_protect_context_window()` clips error output to the last 2000 chars before LLM (v5.9.16) |
| Persistence | `data/red_tester_q_table.json` (Q-table with reconciliation on launch) |
| Reports | `data/reports/red_tester/CRASH_REPORT_{timestamp}.md` |
| Fragility Labels | STABLE, LOW, MODERATE, HIGH_FRAGILITY |
| Rich TUI | Spinners, red crash Panels, yellow AI Diagnosis Panels, green PASS confirmations, color-coded Q-Table |
| Clickable Paths | Rich `[link=file:///...]` terminal hyperlinks for crash reports (v5.9.8) |
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
| `model_discovered` | Model Discovery Engine finds an active model | Model name, provider, scores |
| `router_decision` | LLM Router selects a provider | Provider, task type, prompt length, score |

### 5.3 Event Schema (Mandatory Fields)

```json
{
  "event_id": "UUID4",
  "timestamp": "ISO 8601",
  "event_type": "paper_discovered | paper_evaluated | search_completed | gwo_optimized | agent_step | agent_episode_end | model_discovered | router_decision",
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

`GET /api/v1/synapse/status` reports bus reachability, queue health (emission counters), supported event types, and subscriber status.

---

## Section 6: REST API Reference (19 Endpoints)

### 6.1 Endpoint Catalog

| ID | Method | Path | Description | Response Model |
|----|--------|------|-------------|---------------|
| E01 | GET | `/api/v1/health` | System health, DB stats, embedding coverage | `SystemHealth` |
| E02 | GET | `/api/v1/papers` | Paginated paper list (sorted by overall_score) | `PaginatedPapers` |
| E03 | GET | `/api/v1/papers/{paper_id}` | Full paper detail (all 28+ columns) | `PaperDetail` |
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
| E17 | GET | `/api/v1/tester/status` | Autonomous Red Tester Q-table status (70+ arms) | `TesterStatusResponse` |
| E18 | GET | `/api/v1/tester/reports` | List crash report metadata from data/reports/ | `List[CrashReport]` |
| E19 | GET | `/api/v1/synapse/status` | SYNAPSE bus reachability, queue health, event types | `dict` |

### 6.2 Pydantic v2 Model Inventory

The API defines 16 Pydantic v2 models:

`PaperSummary`, `PaperDetail`, `PaginatedPapers`, `SemanticSearchRequest`, `SemanticSearchResponse`, `ScrapeRequest`, `GWORunRequest`, `GWOResult`, `TaskStatus`, `SystemHealth`, `TranslateQueryRequest`, `TranslateQueryResponse`, `AuthorSummary`, `EvaluatePaperRequest`, `TesterStatusResponse`, `CrashReport`

### 6.3 Background Task System

- **Task Store:** Thread-safe `_task_store` dict with locking
- **Task Lifecycle:** `queued -> running -> completed|failed`
- **Task ID:** 8-character hex UUID prefix
- **Polling:** `GET /api/v1/tasks/{task_id}` for individual status, `GET /api/v1/tasks` for all tasks
- **Long-Running Tasks:** Daily scrape (16 APIs), GWO optimization (minutes), Single-paper evaluation, Bulk score recalculation

### 6.4 Interactive Documentation

Auto-generated OpenAPI docs available at:
- `http://localhost:8001/docs` (Swagger UI)
- `http://localhost:8001/redoc` (ReDoc)

---

## Section 7: MCP Server Tools

### 7.1 MCP Server Architecture

`src/mcp_server.py` (384 lines, v5.8.3) implements a Model Context Protocol (MCP) server using the official `MCPServer` from MCP SDK v2.0.0 with stdio transport. All tools delegate to the TALOS FastAPI backend via HTTP at the configurable `TALOS_API_BASE` (default: `http://127.0.0.1:8001/api/v1`). This decoupled architecture ensures clean separation of concerns -- the MCP server is a thin translation layer between MCP tool calls and the REST API.

### 7.2 MCP Tool Inventory (4 Tools)

| Tool Name | Description | Parameters | Maps to Endpoint |
|-----------|-------------|------------|------------------|
| `talos_system_status` | Query system health, DB stats, and embedding model availability | `{}` | `GET /health` |
| `talos_semantic_search` | Vector-based semantic search across all papers | `{query: str, top_k: int}` | `POST /search/semantic` |
| `talos_get_paper_details` | Retrieve complete paper record with AI evaluation, classification, enrichment | `{paper_id: int}` | `GET /papers/{paper_id}` |
| `talos_trigger_scrape` | Launch background academic scraping pipeline | `{sources: Optional[List[str]]}` | `POST /scrape/trigger` |

### 7.3 MCP Server Configuration

- **Transport:** stdio (standard input/output)
- **Auto-Config:** Cherry Studio MCP config generated by `src/utils/frontend_provisioner.py`
- **Launch:** `python src/mcp_server.py` or via `run_talos.bat` Option 3
- **Timeout:** `TALOS_MCP_TIMEOUT` env var (default: 30 seconds)
- **Error Handling:** All tools return descriptive error strings rather than raising exceptions, ensuring LLM-friendly responses

---

## Section 8: Analysis & Reporting Modules

### 8.1 Analysis Module Inventory

| Module | Path | Function |
|--------|------|----------|
| Citation Network Analyzer | `src/analysis/citation_analyzer.py` | Citation graph construction and analysis with pyvis interactive visualization |
| Author Profiler | `src/analysis/author_profiler.py` | Author publication history and impact profiling |
| Author Trajectory Analyzer | `src/analysis/author_trajectory_analyzer.py` | Career trajectory analysis via ORCID |
| Trend Analyzer | `src/analysis/trend_analyzer.py` | Scientometrics and publication trend analysis |
| Architecture Intelligence Report | `src/analysis/architecture_intelligence_report.py` | System architecture health, dual-language (EN+GR) NATO CDE-compatible reports |
| Knowledge Path Generator | `src/analysis/knowledge_path_generator.py` | Research path discovery and literature mapping with K-Means clustering |
| Recommender | `src/analysis/recommender.py` | Strategic reading recommendations (reads SQLite directly) |
| Baseline Report Generator | `src/analysis/generate_baseline_report.py` | Two-mode reports: Standard + Academic (600 DPI, serif fonts, publication-ready) |
| Architecture Graph Generator | `src/analysis/generate_architecture_graph.py` | D3.js interactive dependency graph of codebase imports |

### 8.2 Graphify AST Knowledge Graph (NEW -- v5.9.10 to v5.9.13)

`src/analysis/graphify_adapter.py` (606 lines) wraps a vendored Graphify AST engine at `vendor/graphify/` to generate interactive D3.js knowledge graphs directly from TALOS source code.

| Phase | Version | Capability |
|-------|---------|-----------|
| v5.9.10 | Vendored Integration | Added `generate_ast_knowledge_graph()` function invoking Graphify as subprocess with `python -m graphify extract src/ --code-only` |
| v5.9.11 | Dependency Hotfix | Added `tree-sitter-python` and `rapidfuzz` to requirements.txt for AST parsing and entity resolution |
| v5.9.12 | Path Resolution + Auto-Clustering | Fixed graphify-out path resolution (output path varies by target directory); auto-executes `graphify cluster-only` with `--no-label` flag to generate `GRAPH_REPORT.md` and community labels without LLM calls, preserving 100% air-gapped operation |
| v5.9.13 | Academic Print Theme | `_inject_light_mode_toggle()` injects a CSS light-mode toggle into generated `graph.html`, enabling both dark (default) and light (academic print) themes with a single click. Original dark mode preserved; all CSS overrides use `!important` for reliability. Graceful degradation on I/O errors |

**Graphify Pipeline Output:**
- `data/reports/graphify_out/graph.html` -- Interactive D3.js force-directed AST dependency graph
- `data/reports/graphify_out/GRAPH_REPORT.md` -- Auto-generated clustering report with community labels
- `data/reports/graphify_out/` -- Full Graphify output directory with node/edge JSON

**Integration:** Launchable from `talos.py` Rich TUI menu under Analysis & Insights section

### 8.3 Query Translator (PYTHIA)

`src/ai/llm/query_translator.py` translates natural-language research goals into 14 optimized boolean search queries. Uses AIManager with "Research Architect" persona. Output saved to `config.json` as `*_query` keys.

### 8.4 Model Manager

`src/ai/llm/model_manager.py` (100% Rich TUI) provides a 7-option menu for configuring:
- Fast Edge Tier model and endpoint (CPU, port 11435)
- Heavy Reasoning Tier model and endpoint (GPU, port 11434)
- Cloud Provider selection (Gemini/DeepSeek/HuggingFace)
- 2D Execution Matrix wizard: 2-step selection (Network Strategy + Hardware Strategy) with summary confirmation panels
- Embedding model selection
- VRAM-aware model size validation and fitness indicators (`[FITS]`, `[TIGHT]`, `[TOO BIG]`)
- Explicit Cancel/Back navigation guardrails in all sub-menus
- `_confirm_setting_change()` helper with Rich Panel confirmation before any `.env` write

### 8.5 Research Pivot

`src/ai/llm/research_pivot.py` provides a 5-step guided wizard for changing research direction: reconfigures query translator parameters, re-evaluates the database against new criteria, and optionally retrains the DRL agent.

---

## Section 9: Database & Persistence

### 9.1 Database Schema

| Table | Purpose | Key Columns |
|-------|---------|-------------|
| `papers` | Primary paper storage | id, doi, title, abstract, authors, source, publication_year, strategic_score, operational_score, tactical_score, playground_score, overall_score, evaluation_reasoning, evaluation_contribution, evaluation_utilization, suggested_tags, suggested_folder, suggested_discord_channel, enrichment_status, oa_pdf_url, embedding_model |
| `embeddings` | Vector embeddings | paper_id, embedding (BLOB), model_name |
| `enrichment_log` | Enrichment tracking | paper_id, source, timestamp, status |

### 9.2 Scoring Framework (4-Layer Invariant)

| Layer | Weight | Description |
|-------|--------|-------------|
| Strategic | 30% | Long-term research alignment and field impact |
| Operational | 30% | Methodological rigor and reproducibility |
| Tactical | 30% | Immediate utility for current research goals |
| Playground | 10% | Creative/exploratory potential |

**Overall Score Formula:** `Overall = 0.30 * S + 0.30 * O + 0.30 * T + 0.10 * P`

### 9.3 Semantic Search

- Cosine similarity computation against all stored embeddings
- Model-aware filtering: `model_filter` parameter restricts to specific embedding model
- Returns top_k results with full paper metadata
- Supported embedding models: `nomic-embed-text` (Ollama, 768d), `gemini-embedding-001` (Gemini, 768d)

### 9.4 Enrichment State Machine

| Status | Value | Meaning |
|--------|-------|---------|
| Pending | 0 | Paper has not yet been enriched |
| Enriched | 1 | Metadata + OA PDF successfully resolved |
| Failed | 2 | Enrichment attempted but failed |

### 9.5 XAI Reasoning Outputs

For each evaluated paper, the AI generates:
- `evaluation_reasoning`: Narrative explanation of the scores
- `evaluation_contribution`: The paper's contribution to the field
- `evaluation_utilization`: How the paper's findings can be applied
- `suggested_tags`: Auto-generated keyword tags
- `suggested_folder`: Recommended organizational folder
- `suggested_discord_channel`: Relevant notification channel

### 9.6 Profile System

- Isolated profiles under `_profiles/<name>/` with independent `config.json` and `talos_research.db`
- Profile switching via `src/core/profile_manager.py`

---

## Section 10: TUI & CLI Reference

### 10.1 Entry Points

| Entry Point | File | Type |
|-------------|------|------|
| TUI Dashboard | `talos.py` | Rich-powered interactive terminal (11 options) |
| Batch Launcher (Win) | `run_talos.bat` | 10-option batch menu with auto-Conda detection |
| Batch Launcher (POSIX) | `run_talos.sh` | 10-option bash menu with virtualenv/Conda detection |

### 10.2 talos.py Rich TUI Features (v5.8.9+)

- **Dynamic Status Table:** Conda/virtualenv environment, API port (8001), Synapse bus (8000), 2D Execution Matrix (Network Strategy / Hardware Strategy with human-readable labels), active LLM tiers (full raw model names)
- **IEEE CS Badge:** Two-tone Rich color block (#006699 / #002855) in header panel
- **Active Research Focus:** LLM-generated 6-10 word summary from `active_focus_summary` in config.json, displayed in bold bright green
- **Dynamic Focus Summarization:** Auto-generates summary via Fast Edge LLM on startup if missing (v5.9.3)
- **Silent Initialization:** Reads TALOS_USE_LOCAL from .env directly (no interactive prompts)
- **11-Option Menu** (organized in visual Rich groups):
  - MODEL CONFIGURATION (Option 1: Model Manager)
  - RESEARCH OPERATIONS (Options 2-4: CLI Research Search, Daily Search Pipeline, View & Pivot Research Focus)
  - ANALYSIS & INSIGHTS (Options 5-7: Graphify AST Knowledge Graph, Autonomous Red Tester, Baseline Reports)
  - SYSTEM DIAGNOSTICS (Options 8-10: DRL Agent Status, Architecture Graph, Docs Generator)
  - EXIT (Option 11)
- **Rich Panels:** All sub-menu launches display contextual informational panels with color-coded borders
- **Elite Papers:** Overall score >= 7 highlighted in gold in search results tables
- **Clickable Hyperlinks:** Crash report paths, Q-table paths, and report directories are clickable Rich `[link=file:///...]` terminal hyperlinks (v5.9.8)
- **Ctrl+C Safety:** `safe_pause()` and `safe_select()` helpers for graceful interrupt handling

### 10.3 run_talos.bat / run_talos.sh Features

- **Section 1: REST API & FRONTEND** (Full Setup, FastAPI server on port 8001, MCP server, Cherry Studio UI)
- **Section 2: CLI & STANDALONE DAEMONS** (TALOS TUI, Autonomous Research Daemon 24/7, Live DRL Agent)
- **Section 3: TESTING & SYSTEM** (Autonomous Red Tester, Pytest suite, Exit)
- **Auto-Conda Path Detection** (Windows): scans 5 common Miniconda/Anaconda directories
- **Auto-virtualenv/Conda Detection** (POSIX): `.venv/` -> `venv/` -> Conda `talosenv` -> system Python
- **Background Minimized/Spawned Server Windows** (Windows)
- **Detached Background Daemons** (POSIX, output to /dev/null)
- **Fermion CPU Accelerator Auto-Start** for Neutrino-8B

### 10.4 Enterprise Logging & Universal Rich TUI (v5.9.17)

- **`src/utils/logger.py`** -- single `get_logger(name)` factory with two handlers:
  - `rich.logging.RichHandler` for emoji-free, colorized console output.
  - `logging.handlers.RotatingFileHandler` writing `data/logs/talos_system.log` (10 MB per file, 5 backups) with formatter `%(asctime)s - %(name)s - %(levelname)s - %(message)s`.
- **`data/logs/`** directory auto-created; the root `talos` logger is configured idempotently (no duplicate handlers) and disables propagation.
- **Universal Rich TUI enforcement** -- `talos.py`, `model_manager.py`, `research_pivot.py`, `generate_docs.py`, `red_tester.py` audited: status/diagnostics via logger, Rich Console/Panel for menus and tables, `questionary` for prompts, no raw `input()`, zero emojis.


---

### 10.5 Universal Cloud Mesh & Multi-Provider Redundancy Expansion (v5.9.18)

- **`config/settings.py`** -- expanded the cloud tier to a nine-provider mesh: Gemini (Google GenAI SDK) plus 8 OpenAI-compatible redundancy providers (NVIDIA NIM, Groq, Cerebras, GitHub Models, Mistral, OpenRouter, DeepSeek, HuggingFace). Added `TALOS_CLOUD_PROVIDERS` canonical list.
- **`src/core/ai_manager.py`** -- `OPENAI_COMPATIBLE_REGISTRY` (dictionary-driven init), unified `_execute_openai_compatible_request()`, independent 5-failure circuit breakers, registry-driven `_execute_cloud_chain()`.
- **`src/ai/llm/model_manager.py`** -- Cloud Configuration TUI renders a Rich table of all 9 providers (Provider Name, Env Key, Status, Default Model, Base URL) via `CLOUD_PROVIDER_CATALOG` and `get_cloud_provider_rows()`.
- **`config.json` / `config.template.json` / `example.env`** -- `ai_provider_priority` updated to `["local", "nvidia", "groq", "cerebras", "github", "gemini", "deepseek", "mistral", "openrouter", "huggingface"]`; 6 new API-key template entries; `failure_threshold` = 5.


### 10.6 Academic Ingestion Expansion -- OpenReview & OpenAIRE Integration (v5.10.0)

- **`src/ingestion/openreview.py`** -- new `OpenReviewSource` agent for the OpenReview API V2 with authenticated/guest `OpenReviewClient` fallback; peer-review decisions, ratings, recommendations, and venue metadata appended to abstracts.
- **`src/ingestion/openaire.py`** -- new `OpenAIRESource` agent for the OpenAIRE Research Graph API v11.3.0 with optional bearer token; project grant/funding metadata appended to abstracts.
- **16-source ingestion** -- `daily_search.py` and `historic_search.py` now run both new sources (plus `CORESource` restored to the daily pipeline); `requirements.txt` gains `openreview-py`; `example.env` gains `OPENREVIEW_USERNAME`, `OPENREVIEW_PASSWORD`, `OPENAIRE_TOKEN`; config gains `openreview_query`/`openaire_query` and `max_results_config` entries.


---

## Section 11: Configuration & Environment

### 11.1 Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| TALOS_NETWORK_STRATEGY | strict_local | Network dependency: strict_local, local_first, cloud_first, strict_cloud |
| TALOS_HARDWARE_STRATEGY | cpu_gpu_split | Hardware routing: cpu_only, gpu_only, cpu_gpu_split |
| TALOS_FAST_ROUTING | local | Fast tier routing: "local" or "cloud" |
| TALOS_HEAVY_ROUTING | local | Heavy tier routing: "local" or "cloud" |
| TALOS_CLOUD_PROVIDER | gemini | Default cloud provider |
| TALOS_ALLOW_CLOUD_FALLBACK | (unset) | Enable cloud fallback for local mode (legacy) |
| TALOS_ALLOW_LOCAL_FALLBACK | (unset) | Enable local fallback for cloud mode (legacy) |
| FAST_EDGE_MODEL | fermionresearch/Neutrino-8B | Fast edge model name |
| FAST_EDGE_BASE_URL | http://127.0.0.1:11435/v1 | Fast edge endpoint |
| HEAVY_REASONING_MODEL | qwen2.5:14b | Heavy reasoning model name |
| OLLAMA_BASE_URL | http://127.0.0.1:11434 | Standard Ollama GPU endpoint |
| GEMINI_API_KEY | (unset) | Gemini API key |
| DEEPSEEK_API_KEY | (unset) | DeepSeek API key |
| HF_TOKEN | (unset) | HuggingFace API token |
| LOCAL_MODEL_NAME | gemma3:12b | Fallback local chat model |
| LOCAL_EMBEDDING_MODEL | nomic-embed-text | Local embedding model |
| TALOS_DEFAULT_TIER | fast | Default tier for requests |

### 11.2 config.json Keys

- `active_focus_summary`: 6-10 word LLM-generated research focus title (v5.9.3)
- `user_research_goal`: Raw natural-language research goal
- `phd_focus_system_prompt`: System prompt for AI evaluation persona
- `pre_screening_prompt`: Prompt for flash tier pre-screening
- `query_translator_prompt`: Meta-prompt for PYTHIA Query Translator
- `*_query` (16 keys): Boolean search queries for each academic source
- `ai_provider_priority`: Ordered list of provider names
- `failure_threshold`: Circuit breaker failure threshold
- `provider_limits`: Per-provider rate limits (rpm, rpd, tpm)
- `gemini_tier`: Gemini API tier (free, tier1, tier2)

---

## Section 12: Deployment & Infrastructure

### 12.1 Deployment Options

| Mode | Components | Command |
|------|-----------|---------|
| Development | FastAPI with reload | `uvicorn src.api.main_api:app --reload --port 8001` |
| Production | FastAPI on port 8001 | `uvicorn src.api.main_api:app --host 127.0.0.1 --port 8001` |
| Docker | Headless FastAPI container (host Ollama via host-gateway) | `docker compose up -d --build` |
| Kubernetes | Cluster with Ollama sidecar | `kubectl apply -f k8s/` |

### 12.2 Hardware Requirements

| Tier | GPU | VRAM | Capability |
|------|-----|------|-----------|
| Minimum | CPU only | N/A | Ingestion + evaluation (cloud LLMs only) |
| Recommended | RTX 3060+ | 12 GB | Local nomic-embed-text + light chat models |
| Optimal | RTX 4070+ | 16 GB | Full local DRL training + embedding generation + dual-tier (CPU+GPU split) |

### 12.3 Docker Support

- `Dockerfile`: Single-stage `python:3.11-slim` image (matches the dev environment, Python 3.11) with a `config.json` bootstrap from `config.template.json`
- `docker-compose.yml`: FastAPI service on port 8001 with persistent volumes (`data/`, `models/`, `logs/`, `_profiles/`) and host Ollama access via `host.docker.internal`
- `restart: unless-stopped` for production resilience
- `HEALTHCHECK` at `/api/v1/health`
- Full usage reference: `docs/DOCKER.md`

---

## Section 13: Documentation Canon (15-File Sync)

### 13.1 The 15 Canonical Files

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
| 13 | `docs/SYSTEM_CAPABILITIES_MASTER.md` | EN | Capabilities reference (Markdown) -- this file |
| 14 | `docs/SYSTEM_CAPABILITIES_MASTER.html` | EN | Capabilities reference (HTML) |
| 15 | `docs/TECH_RADAR.md` | EN | Technology radar and stack choices |

### 13.2 Code Version Synchronicity (5 Files)

| # | File | Version String Location |
|---|------|------------------------|
| 1 | `talos.py` | Module docstring + printed banner |
| 2 | `run_talos.bat` | Window title, banner text, section headers |
| 3 | `run_talos.sh` | Script header comment, banner text, section headers |
| 4 | `config/settings.py` | `TALOS_VERSION` constant |
| 5 | `src/api/main_api.py` | `app.version` FastAPI metadata string |

---

## Section 14: Test Suite

### 14.1 Test Inventory

| Test File | Tests | Coverage |
|-----------|-------|----------|
| `tests/test_smoke.py` | 78 health checks | System health, database, configuration |
| `tests/test_synapse.py` | 21 tests | EventEmitter + webhook route coverage |
| `tests/test_multi_tier.py` | 20 tests | Fast vs. heavy LLM routing logic, version assertion |
| `tests/test_provisioner.py` | 23 tests | Frontend provisioner OS detection and config generation |
| `tests/test_mcp_server.py` | 27 tests | MCP server tool registration and HTTP mocking |
| `tests/test_model_manager.py` | 29 tests | Ollama connectivity, VRAM fitness indicators, env key handling |
| **Total** | **198+ tests** | Full system coverage |

### 14.2 Verification Gates

1. `python -m py_compile <file>` (syntax)
2. `python scripts/verify_dependency_map.py` (imports)
3. `python scripts/db_stats.py` (database, if schema changed)
4. `python tests/test_smoke.py` (runtime health)

---

## Section 15: v5.9.10 to v5.9.13 New Capabilities

### 15.1 Vendored Graphify AST Integration (v5.9.10 to v5.9.13)

- `src/analysis/graphify_adapter.py` -- adapter wrapping vendored `vendor/graphify/` AST engine
- Generates interactive D3.js knowledge graphs from TALOS source code via subprocess invocation
- Auto-executes `cluster-only` command with `--no-label` flag (100% air-gapped, no LLM keys required)
- Outputs to `data/reports/graphify_out/` (graph.html, GRAPH_REPORT.md, JSON artifacts)
- Academic Print Theme: `_inject_light_mode_toggle()` injects CSS light-mode toggle into generated graph.html (v5.9.13)
- Path resolution with backward-compatible fallback for varying Graphify output locations (v5.9.12)
- Dependencies: `tree-sitter-python`, `rapidfuzz`, `tree-sitter`, `networkx`

### 15.2 Rich Menu Reorganization (v5.9.10)

- talos.py 11-option menu organized into visual Rich groups with Panel separators
- Graphify AST Knowledge Graph option under Analysis & Insights section

### 15.3 Data Directory Isolation (v5.9.9)

- All runtime-generated reports consolidated under `data/reports/`
- Root `reports/` directory deleted -- clean project root
- 8 analysis scripts + autonomous tester + tester routes updated

### 15.4 Clickable Terminal Hyperlinks (v5.9.8)

- `_make_clickable_path()` helper converts file paths to Rich `[link=file:///...]` terminal hyperlinks
- Crash report paths, Q-table paths, and reports directories are CTRL+CLICK navigable

### 15.5 Fast-Tier Local-to-Local Fallback (v5.9.8)

- When fast edge CPU tier (port 11435) fails, automatically falls back to local GPU Ollama (port 11434) FIRST
- Preserves air-gapped operation before attempting cloud fallback

### 15.6 Dynamic Target Discovery (v5.9.7)

- Autonomous Red Tester scales from 4 hardcoded targets to 70+ dynamically discovered arms
- Q-table reconciliation on launch preserves existing Q-values

### 15.7 2D Execution Matrix (v5.9.4)

- Network Strategy (4 modes) x Hardware Strategy (3 modes) = 12 combinations
- Backward-compatible with legacy TALOS_EXECUTION_MODE
- Cross-environment automatic fallback with transparent routing

### 15.8 LLM Router Sub-Agent, Bi-Level GWO Reward Shaping & Interactive 16-Source Checkbox TUI (v5.10.2)

- `src/ai/drl/llm_router_subagent.py` -- `LLMRouterSubAgent` selects the optimal active provider from `models/gwo_llm_router_reward_weights.json` weights (Pareto fallback), scoring quality/latency/cost/rate-limit signals; `AIManager` delegates cloud/legacy provider selection to it via `_get_router_ordered_providers`.
- **Relative min-max quality normalization** -- each `PROVIDER_PROFILES` entry stores a raw SWE-bench Verified score (`swe_bench_score`); the quality signal is derived dynamically as `Q_p = Score(p) / max_k Score(k)`, so the top-benchmark provider receives exactly `Q_p = 1.0` and every other provider scales proportionally.
- `src/ai/optimizers/gwo_llm_router_reward_shaper.py` -- `GWOLLMRouterRewardShaper` bi-level multi-objective optimizer: canonical GWO outer loop over a simplex-projected 4D weight vector `[w_quality, w_latency, w_cost, w_penalty]` plus an inner LLM Router evaluation under `R = w_quality*QualityScore - w_latency*LatencyRatio - w_cost*CostRatio - w_penalty*RateLimitPenalty`. Exports `models/gwo_llm_router_reward_weights.json` with convergence trajectory and three Pareto profiles (Deep Research, Fast Screening, Air-Gapped Local).
- `gwo_rl_optimizer.py` renamed to `gwo_foraging_hyperparameter_tuner.py` (class `GWOForagingHyperparameterTuner`); best-parameters export renamed to `models/gwo_foraging_hyperparameters.json`.
- `talos.py` Options 3a/3b now prompt a `questionary.checkbox()` over all 16 academic sources (all pre-selected) passed to the search scripts via `--sources`.
- `daily_search.py` / `historic_search.py` gain a canonical `SOURCE_REGISTRY`, `ALL_SOURCE_NAMES`, and `build_sources()` helper with `--sources` argparse filtering.

### 15.9 Hierarchical DRL Orchestration - Daemon & Foraging Sub-Agent Integration (v5.10.3)

- `LLMRouterSubAgent` is now invoked directly by the live DRL foraging orchestrator (`live_agent_orchestrator.py` v1.3), the 24/7 autonomous daemon (`talos_service.py` v2.1), and the daily/historic search pipelines for optimal provider selection before each paper evaluation.
- New `foraging_evaluation` task modifier in `TASK_MODIFIERS` (`prompt_scale=1.0`, `quality_bias=0.02`) plus a shared `estimate_prompt_tokens()` helper (four-characters-per-token heuristic).
- Daemon logs `[DAEMON/ROUTER]` routing decisions to `data/logs/talos_system.log`; orchestrator logs `[ROUTER]` choices to the live-agent console and module logger.
- Search pipelines route Fast Edge pre-screening (`fast_screening`) and Heavy Reasoning deep analysis (`deep_research`) through `route_evaluation_provider()`.
- New hermetic tests in `tests/test_multi_tier.py` (`TestLLMRouterSubAgentPipelineIntegration`) and `tests/test_llm_router_subagent.py` verify that orchestrator, daemon, and search pipelines invoke `LLMRouterSubAgent.select_provider()`.

### 15.10 Dynamic Model Discovery Engine & SYNAPSE Protocol Interoperability (v5.10.4)

- `src/ai/llm/model_discovery.py` (`ModelDiscoveryEngine`) with air-gapped `data/model_benchmarks.json` registry and `Q_p = raw / max(raw)` quality scoring.
- `LLMRouterSubAgent.refresh_quality_scores()` / `load_quality_scores()` and non-blocking `router_decision` Synapse emission.
- `GET /api/v1/synapse/status` endpoint, `model_discovered` / `router_decision` event types, and emission statistics.
- `tests/test_model_discovery.py` (15 hermetic tests).

---

### 15.11 Universal Dynamic Model Provisioner & Self-Healing Redundancy Engine (v5.10.5)

- `src/utils/model_provisioner.py` (`ModelProvisioner`) with deterministic protocol detection and 3-tier local path resolution (`FAST_EDGE_MODEL_PATH`, in-tree `models/<sanitized_name>`, network).
- JIT auto-pull for Ollama (`ollama pull`) and HuggingFace Hub (`huggingface_hub.snapshot_download`) with self-healing fallback (`[WARNING] Auto-provisioning failed ... Reverting to baseline model.`).
- `run_talos.bat` / `run_talos.sh` step [5/5] execute the provisioner; `model_manager.py` `_provision_model()` routes uninstalled models through it.
- `tests/test_model_provisioner.py` (22 hermetic tests).

### 15.12 Daemon OS Autostart & Orchestrator (v5.10.6)

- `src/utils/daemon_autostart.py` (`generate_boot_batch()`, `install_windows_autostart()`) generates `talos_daemon_boot.bat` and registers a Windows Startup-folder `.lnk` (pywin32, `shell32.dll,43` icon, minimized window).
- Interactive daemon pre-flight in `talos.py` ("Configure Daemon & OS Autostart"): network strategy, target sources, optional autostart hook.
- `daemon_target_sources` in `config.json` injected into `talos_live_agent.py --sources`.
- `talos_live_agent.py` gains `--sources` (`nargs="+"`) source filtering.

### 15.13 OPTICA Bridge Integration (v5.10.7)

- `src/integration/optica_client.py` (`OpticaClient`) -- REST client to Project OPTICA (port 8002) offloading heavy cnsplots/PyVis graphics.
- `request_plot(plot_type, journal_template)` resolves the active profile DB path via `get_active_profile_db_path()` and POSTs `{data_source, plot_type, journal_template, override_params}` to `{OPTICA_API_BASE}/plot/generate` with graceful connection-error handling.
- `config/settings.py` `OPTICA_API_BASE` (default `http://127.0.0.1:8002/api/v1`); mirrored in `config.template.json` and `example.env`.
- TUI "Data Visualizations (via OPTICA)" menu option (Analysis & Insights group): plot type (`opex_dashboard` / `semantic_topology`) and journal template (`nature` / `science` / `cell`).

---

> **Project TALOS** -- From Aggregator to Autonomous Research Architect.
> Built in Kalamata, Greece.
> (C) 2026 Christos Smarlamakis. All rights reserved.
