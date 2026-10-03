# TALOS/ALEXANDRIA -- System Capabilities Master Reference v5.22.0

> **Document ID:** TALOS-SYS-CAP-001
> **Classification:** Public Reference
> **Scope:** TALOS Research Intelligence Platform (Headless FastAPI Backend + React Frontend + SYNAPSE Protocol + Graphify AST Intelligence)
> **Last Updated:** 2026-10-03
> **Version:** v5.22.0 -- Full-Spectrum Rich Terminal Dashboard 2.0 & Scientific Console Architecture

[![IEEE Computer Society WEIGD Fund 2026](https://img.shields.io/badge/IEEE_Computer_Society-WEIGD_Fund_Recipient_2026-006699?style=flat-square&logo=ieee&logoColor=white)](https://www.computer.org/volunteering/awards/scholarships/weigd-student-fund/weigd-recipients#summer-2026)

---

## Section 1: System Vision & Core Architecture

### 1.1 Foundational Principle

TALOS is an autonomous Research Intelligence Platform that ingests, evaluates, synthesizes, and visualizes scientific knowledge across 16 academic sources. It replaces manual systematic literature review workflows with an AI-driven, DRL-orchestrated pipeline that maintains a human-in-the-loop at every critical decision boundary. The system operates as a microservice within the broader ALEXANDRIA Ecosystem -- a distributed research intelligence mesh that communicates via the SYNAPSE Event-Driven Protocol. Starting in v5.9.10, TALOS also introspects its own codebase through a vendored Graphify AST Knowledge Graph engine, generating interactive dependency visualizations and architectural intelligence reports directly from source code.

### 1.2 Architectural Pillars

The system operates as a five-layer architecture:

| Layer | Component | Role |
|-------|-----------|------|
| **Frontend** | React 18 with Tailwind CSS and Shadcn UI | User-facing dashboard leveraging the REST API |
| **Backend** | `src/api/main_api.py` (25 endpoints) | Headless FastAPI facade exposing all core capabilities |
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
| TALOS_VERSION | "5.22.0" | `config/settings.py` |
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

## Section 6: REST API Reference (23 Endpoints)

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
| E20 | GET | `/api/v1/visualizer/live` | 3D Holographic Knowledge Constellation Visualizer HTML | `HTMLResponse` |
| E21 | GET | `/api/v1/visualizer/stream` | SSE event stream for live visualizer (15s heartbeat) | `StreamingResponse` |
| E22 | GET | `/api/v1/visualizer/demo-data` | Recent evaluated papers for offline conference replay | `List[dict]` |
| E23 | GET | `/api/v1/visualizer/state` | Consolidated AJAX polling snapshot (16-source health, latest evaluation, active query) | `dict` |

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
- **Desktop Control Hub System Tray (v5.10.13):** `src/utils/tray_icon.py` launches a pystray icon (navy/cyan "T") next to the Windows clock with a seven-item menu -- Open 3D Visualizer, Open Reports Folder, Open System Log, Open API Docs (Swagger), Trigger Instant Search Cycle, Show / Hide Console Window (Win32 `ShowWindow`), Terminate Daemon -- with self-healing auto-bootstrap (`_is_api_alive` / `_ensure_api_server`); initialized by `talos_service.py` on daemon startup.
- **New Console Window Daemon Launch (v5.10.12):** Option 11 spawns the 24/7 daemon via `subprocess.Popen(..., creationflags=subprocess.CREATE_NEW_CONSOLE)` so the TUI stays interactive.
- **Rich TrueColor DRL Telemetry (v5.10.12):** `live_agent_orchestrator.py` emits color-coded `[ACT]`, `[ROUTER]`, `[WARNING]`, `[RECOVERY]`, and `[EVAL]` badges with dynamic `[ELITE  +]` / `[ACCEPT v]` / `[REJECT X]` status.

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

## Section 13: Documentation Canon (16-File Sync)

### 13.1 The 16 Canonical Files

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
| 15 | `docs/internal/TECH_RADAR.md` | EN | Technology radar and stack choices (Confidential / Internal) |
| 16 | `docs/internal/TECH_RADAR_GR.md` | GR | Technology radar Greek master (Confidential / Internal) |

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
| `tests/test_system_integrity.py` | 474 integrity checks | Automated System Integrity Verification Suite (ISO/IEC 25010) |
| `tests/test_synapse.py` | 21 tests | EventEmitter + webhook route coverage |
| `tests/test_multi_tier.py` | 20 tests | Fast vs. heavy LLM routing logic, version assertion |
| `tests/test_provisioner.py` | 23 tests | Frontend provisioner OS detection and config generation |
| `tests/test_mcp_server.py` | 27 tests | MCP server tool registration and HTTP mocking |
| `tests/test_model_manager.py` | 29 tests | Ollama connectivity, VRAM fitness indicators, env key handling |
| **Total** | **198+ tests** | Full system coverage |

### 14.2 Verification Gates

1. `python -m py_compile <file>` (syntax)
2. `python src/utils/verify_dependency_map.py` (imports)
3. `python src/utils/db_stats.py` (database, if schema changed)
4. `python tests/test_system_integrity.py` (runtime health)

---

## Section 15: 3D WebGL / AJAX Visualizer & Recent Capabilities (v5.10.13)

### 15.0 3D WebGL / AJAX Knowledge Constellation Visualizer & Interactive Tools (v5.10.12)

- `templates/live_foraging_visualizer.html` -- vendored Three.js r128 (zero CDN) constellation:
  - 60 FPS animated energy laser beams (additive-blended `THREE.Line`) with traveling photon spheres (Cyan `#00ced1` / Gold `#f59e0b`).
  - Robust fuzzy source resolver `findNodeIndex(rawSource)` with `_source`/`source` suffix normalization.
  - Interactive click-to-fire via `THREE.Raycaster` on satellite nodes, updating the HUD.
  - SNAPSHOT (PNG via `canvas.toDataURL` -> `TALOS_3D_Constellation.png`), FULLSCREEN, THEME (dark / academic print), and HELP (keyboard shortcuts R/T/F/S/Space/1-3).
  - 1000ms pure-AJAX state poller (`GET /api/v1/visualizer/state?_t=`) with no-store headers: refreshes all 16 health auras and count badges, fires beams on new evaluation IDs.
- Backend: `GET /api/v1/visualizer/state` resolves the active profile DB via `get_active_profile_db_path()`; `POST /api/v1/visualizer/events` accepts a dict or list and updates `_sources_health_state`.
- SQLite optimizer: `src/utils/db_stats.py::optimize_database(db_path)` runs `PRAGMA integrity_check;` + `VACUUM;`.

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

### 15.14 Desktop Control Hub -- System Tray & Self-Healing Auto-Bootstrap (v5.10.13)

- `src/utils/tray_icon.py` expanded into a seven-item Desktop Control Hub: Open 3D Visualizer, Open Reports Folder (`data/reports`), Open System Log (`data/logs/talos_system.log`), Open API Docs (Swagger, `/docs`), Trigger Instant Search Cycle (`POST /api/v1/scrape/trigger`), Show / Hide Console Window (Win32 `ShowWindow`), Terminate Daemon.
- Tooltip title `"TALOS v5.10.13 | Research Intelligence Mesh"`; heavy imports (pystray, Pillow) remain lazy.
- **Self-Healing Auto-Bootstrap flow:** `_is_api_alive(port=8001)` probes `GET /api/v1/health` (0.6s timeout); `_ensure_api_server()` locates the project root and spawns `uvicorn src.api.main_api:app --host 127.0.0.1 --port 8001` with `subprocess.CREATE_NO_WINDOW` (Windows), polling until responsive (up to 3s).
- **Native OS Desktop Bridge:** `os.startfile` (Windows), `open` (macOS), `xdg-open` (Linux) for filesystem targets.

### 15.15 Hub-and-Spoke 3D Topology & Bi-directional 4-State Parabolic Telemetry (v5.10.13)

- Hub-and-spoke constellation: gold icosahedron core (hub) surrounded by 16 Fibonacci-distributed satellite source nodes (spokes) with core-to-node connection lines plus a neighbor mesh.
- Bi-directional 4-state beam bridge (`src/api/main_api.py` `_record_beam_event`): query_out -> standby (cyan) core->node beam; data_in/evaluation -> healthy (green) node->core beam; error -> red. Parabolic quadratic-bezier arcs rendered in `live_foraging_visualizer.html`.
- **Synthetic ID Engine:** `_live_eval_seq` / `_live_eval_state` mint strictly increasing ids so backlog re-evaluations (UPDATE with unchanged max DB id) still advance the HUD.

### 15.16 Database Persistence Architecture (v5.10.13)

- Single point of truth: `DatabaseManager.__init__(db_path=None)` now defaults to `get_active_profile_db_path()` resolving `_profiles/<active>/talos_research.db`.
- `get_active_profile_db_path()` reads `_profiles/active_profile.txt`, defaults to `"default"`, and creates the profile directory on demand.
- Removed legacy `data/talos_research.db` canonical-priority and `_resolve_profile_db` walk-up logic.

### 15.17 Professional Environment Configuration Canon (v5.10.13)

- `example.env` + `.env` reconstructed into six commented sections: Execution Matrix & Network Strategy, Local AI Model Tiers, Universal Cloud Mesh (9 providers), 16 Academic Ingestion APIs, Ecosystem Integrations, System Notifications.
- `.env` secrets preserved verbatim; guidance comments added above every variable.

### 15.18 Autonomous Execution Matrix & DeepSeek V4 Cognitive Integration (v5.10.14)

- **5th Network Strategy `auto_dynamic`:** `src/ai/llm/model_manager.py` `select_execution_mode()` now offers Option 5 -- autonomous strategy selection with Privacy Guardrails; `src/core/ai_manager.py` `_resolve_strategies(model_type)` collapses it at runtime.
- **Privacy Guardrail resolution policy (deterministic):** offline -> strict_local; online + non-deep task -> local_first; online + deep task + interactive consent -> cloud_first; refusal/offline -> strict_local; non-interactive -> local_first. Helpers: `_is_network_online()`, `_detect_vram_gb()`, `_resolve_auto_dynamic()`, `_prompt_auto_dynamic_consent()`, `_log_auto_matrix()`.
- **HARD CONSTRAINT:** `strict_local` short-circuits before any cloud/auto-dynamic logic -- air-gapped operation is never overridden.
- **DeepSeek V4 Cognitive Integration:** `_execute_openai_compatible_request()` injects `thinking={"type": "enabled"}` + `reasoning_effort="high"` for DeepSeek V4 models; default `DEEPSEEK_MODEL_CHAT` = `deepseek-v4-pro`.
- **DeepSeek V4 catalog:** `deepseek-v4-pro` (SWE-bench 75.0 / MMLU-Pro 82.0) and `deepseek-v4-flash` added to `model_manager.py` and `DEFAULT_BENCHMARK_MODELS`.

### 15.19 Universal TUI Feature Restoration & 100% Codebase Coverage (v5.10.15)

- **Unified 6-group hierarchical TUI:** `talos.py` `main_menu()` reorganized into six sections -- Configuration & Profiles, Research Search & Ingestion, Advanced Analysis & Visualizations, DRL Agents/Daemons & GWO Swarm, Database Maintenance & Data Tools, System Health/Diagnostics & CI/CD -- all using `TALOS_QUESTIONARY_STYLE`.
- **Dead sub-menu revival:** `profile_settings_menu()`, `database_data_menu()`, `system_health_menu()` reconnected; new `search_ingestion_menu()`, `analysis_visualization_menu()`, `drl_gwo_menu()`.
- **45/45 executable module coverage:** every orphaned module wired (Model Discovery, Model Provisioning, GWO LLM Router Reward Shaper, Red Tester, Daemon Autostart, OPTICA client).
- **GWO Swarm suite:** tuner, router reward shaper, and 3D live dashboard (Dash port 8050) unified.
- **Script map hardening:** `_resolve_script_path()` raises `FileNotFoundError` for unmapped scripts (no silent `scripts/` fallback).

### 15.20 Live Telemetry HUD Console, Win32 Close-to-Tray & Evaluation History Engine (v5.11.0)

- **Live Telemetry HUD Console:** `templates/live_foraging_visualizer.html` gains a bottom-right glassmorphism telemetry stream (rgba(15,23,42,0.85) + backdrop blur + cyan border) with a 40-line ring buffer, auto-scroll, color-coded `[ACT]`/`[ROUTER]`/`[DATA]`/`[RECOVERY]`/`[WARNING]`/`[ERROR]`/`[EVAL]` tags, `C`/`L` hotkey toggles, and automatic hide during PNG SNAPSHOT export.
- **Win32 Close-to-Tray Hook:** `src/utils/tray_icon.py` `enable_close_to_tray()` subclasses the console window procedure via `ctypes` (GetWindowLongPtrW / SetWindowLongPtrW / CallWindowProcW), intercepting `WM_CLOSE` and `WM_SYSCOMMAND`/`SC_CLOSE` to call `ShowWindow(SW_HIDE)` instead of terminating; a module-level WNDPROC reference prevents GC.
- **Full-Title & Authors Telemetry:** `live_agent_orchestrator.py` [EVAL] renders the complete title and normalized author list over a two-line Rich structure; `ai_manager.py` `_sanitize_connection_error()` returns the locale-independent English message "Connection refused: target host or port is offline."
- **Persistent Evaluation History:** `src/utils/evaluation_history.py` appends every evaluated paper to `data/history/daemon_evaluations.jsonl` (`record_evaluation()`, `read_evaluation_history()`, `verdict_for_score()`); `talos.py` `_show_evaluation_history(limit=30)` renders a Rich table.
- **Autonomous Linux Bootstrap:** `run_talos.sh` `detect_or_install_conda()` (PATH + standard-dir detection, x86_64/aarch64 silent Miniconda3) and `ensure_talosenv()` (Python 3.11 `talosenv`); menu options 2-9 execute inside `talosenv`.

### 15.21 TUI Sub-Menu Sanitization & Complete Hierarchy Audit (v5.11.1)

- **Questionary choice-list fix:** `profile_settings_menu()` in `talos.py` rewritten with explicit `questionary.Choice(title=..., value=...)` entries, a `__back__` sentinel, and strictly sequential 1-8 numbering.
- **Routing corrections:** "1. Manage Profiles" dispatches to `run_script("profile_manager.py", ...)`; "5. Model Discovery (Quality Scoring)" to the in-process `_run_model_discovery()` helper.
- **Unified sub-menu styling:** all seven sub-menus (`search_ingestion_menu`, `analysis_visualization_menu`, `drl_gwo_menu`, `database_data_menu`, `system_health_menu`, `author_tools_menu`, `api_keys_menu`) standardized with `[ Back / Return to Main Menu ]` labels and the canonical `TALOS_QUESTIONARY_STYLE` theme.

### 15.22 Zero-Click Windows Pre-Flight Onboarding Wizard (v5.11.2)

- **Progress-aware `:AUTO_PREFLIGHT` engine:** `run_talos.bat` gains a five-step guided setup wizard (`[Step 1/5]` through `[Step 5/5]`) with a reassuring header banner, per-step `[OK]` status ticks, and explicit time estimates, designed so non-technical researchers never face a blank or frozen console on a clean Windows PC.
- **Silent Miniconda3 bootstrap:** when no Conda runtime is detected, the wizard downloads Miniconda3 (~85 MB) via native `curl.exe -# -fS` (live progress bar) and installs it silently with `start /wait ... /InstallationType=JustMe /RegisterPython=0 /S /D=%USERPROFILE%\miniconda3`; fatal failures pause with a clear `[ERROR]` and exit code 1.
- **`:DISCOVER_CONDA` subroutine:** scans `%USERPROFILE%\miniconda3`, `%USERPROFILE%\anaconda3`, `C:\ProgramData\miniconda3`, `C:\ProgramData\anaconda3`, `%LOCALAPPDATA%\Continuum\anaconda3`, and PATH (`where conda`) for `condabin\conda.bat`; sets `CONDA_BAT`/`CONDA_ROOT` and back-fills the legacy `CONDA_ACTIVATE_PATH` so the existing `:ACTIVATE_CONDA` routine keeps working for all 10 menu options.
- **Silent fast-path bypass gate:** four suppressed startup checks (`CONDA_BAT` defined, `CONDA_ROOT` defined, `.env` present, `<root>\envs\talosenv\python.exe -c "import questionary, rich, fastapi"` succeeds) jump straight to `:MAIN_MENU` in under one second on subsequent launches; any failure falls through to the full wizard.
- **Automated provisioning steps:** Step 2 verifies/creates the `talosenv` Conda environment (Python 3.11); Step 3 initializes `.env` from `example.env`; Step 4 upgrades pip, installs `requirements.txt`, and runs `src/utils/frontend_provisioner.py` (one-time, 2-3 minutes); Step 5 performs the final integrity tick.
- **Batch hardening:** caret-escaped parentheses inside parenthesized code blocks, clean `call`/`goto :EOF` stack discipline, and strict CRLF line endings verified byte-level (zero lone LF).

### 15.23 Ecosystem Integrity, Deprecation Elimination & Dependency Alignment (v5.11.3)

**Part A -- Concurrency Hardening & Asynchronous Resilience (7 pre-demo fixes, formally sealed):**

- **Non-blocking SSE event loop:** `visualizer_sse_stream` (`src/api/main_api.py` L1340) offloads the blocking `_visualizer_event_queue.get` to a worker thread via `await asyncio.to_thread(_visualizer_event_queue.get, True, 1.0)`, so a connected `/api/v1/visualizer/stream` client no longer monopolizes the single uvicorn event loop (previously all other endpoints were starved to roughly 1 Hz in Live SSE mode).
- **Cached DatabaseManager singleton on visualizer polling:** `get_visualizer_demo_data` (L1382) and `get_visualizer_state` (L1551) consume the cached `_get_db()` singleton instead of per-request `DatabaseManager(db_path=...)` construction, eliminating per-poll DDL re-runs and full embeddings-table unpickling on every 1-1.5 s poll; both endpoints bind to the profile database active at server start.
- **Headless background workers:** `_run_scrape_background` (L749) and `_run_evaluate_background` (L972) inject `os.environ["TALOS_HEADLESS"] = "1"` at task entry; `AIManager._interactive_cloud_fallback()` (`src/core/ai_manager.py` L1229) short-circuits the interactive questionary consent prompt when the flag is set, guaranteeing no console-less BackgroundTasks thread can block on user input.
- **Scrape task concurrency lock:** module-level `_scrape_task_lock = threading.Lock()` (L185) serializes the process-global `sys.exit` monkey-patch/restore sequence (acquire L759, release inside `finally` L790); concurrent scrape triggers queue deterministically instead of racing the patch and permanently corrupting `sys.exit`.
- **Semantic search bounds clamping:** `DatabaseManager.semantic_search` (`src/core/database_manager.py` L342-344) clamps `top_k = min(top_k, len(self._embedding_ids))` and returns `[]` early for `top_k <= 0`, preventing `ValueError: kth out of bounds` from `np.argpartition` when the model-filtered embedding count is smaller than the requested top_k.
- **Visualizer payload guards:** `_record_beam_event` (L442-446) casts the `count` payload field inside `try/except (TypeError, ValueError)` defaulting to 0; malformed external POSTs to `/api/v1/visualizer/events` degrade gracefully instead of raising an unhandled HTTP 500.
- **GWO progress monitor resilience:** `_run_gwo_background._poll_progress` (L872) guards `gwo_history.json` reads with `except Exception: pass`, surviving mid-write truncation and structurally unexpected roots (e.g., a dict root causing `KeyError` on `history[-1]`) without killing the monitor thread.
**Part B -- Ecosystem Integrity & Dependency Alignment (5 fixes):**

- **OpenReview V2 note-query dispatch:** `OpenReviewSource._query_notes()` (`src/ingestion/openreview_source.py`) routes every note query through a version-tolerant ladder -- `search_notes(term=...)` when exposed by the V2 `OpenReviewClient`, `get_notes(content={"title": ...})` otherwise, and a bare `get_notes(limit=...)` retry on `TypeError` for mixed client versions; consumed by both `fetch_new_papers` (paginated, `sort="cdate:desc"`) and `search_papers`. Four hermetic tests in `tests/test_openreview_source.py` pin the dispatch contract.
- **Fast-Edge batch circuit breaker:** `AIManager._fast_edge_offline_memo` (`src/core/ai_manager.py`) is set on the first connection failure to the CPU edge endpoint (`FAST_EDGE_BASE_URL`, port 11435) and short-circuits every subsequent fast-tier call in the batch directly to the local GPU Ollama fallback (port 11434) with an `[INFO]` log line, eliminating repeated connection timeouts.
- **FastAPI lifespan lifecycle:** `src/api/main_api.py` uses an `@asynccontextmanager` `lifespan` coroutine (startup warm-up + readiness logs; explicit no-op shutdown) passed via `FastAPI(lifespan=...)`, fully eliminating the deprecated `@app.on_event` hooks and their DeprecationWarning.
- **Gemini warning suppression:** `_try_import_genai()` installs paired module-scoped and message-scoped `warnings.filterwarnings("ignore", category=FutureWarning, ...)` entries immediately before the lazy `google.generativeai` import, silencing the end-of-support notice without masking unrelated warnings.
- **GWO status multi-path check:** `talos.py:_show_drl_status` probes `models/gwo_foraging_hyperparameters.json`, `models/gwo_llm_router_reward_weights.json`, and the legacy `models/gwo_parameters.json`, rendering `Present` when any artifact exists or `Default Baseline Active (Run Opt 4.6 to tune)` guidance otherwise; detailed metrics render only for the foraging artifact with mid-write/schema guards.
- **Dependency map verifier repair:** `src/utils/verify_dependency_map.py` `parse_section_7` accepts both the English and Greek Section 7 headers (`Dependency Graph` / `Γράφος Εξαρτήσεων`) plus language-tagged code fences; the `EXTERNAL_PACKAGES` whitelist is expanded (`atexit`, `asyncio`, `queue`, `html`, `ctypes`, `win32com`, `win32com.client`, `PIL`, `Pillow`, `pystray`, `urllib3`); generated-report footers and all canonical docs are corrected from `scripts/` to `src/utils/` paths. `--ci` exits 0.

**Verification surface:** all 12 fixes (7 concurrency + 5 ecosystem integrity) audited in source at seal time; release gates: `python -m compileall src config tests talos.py`, `pytest tests/test_system_integrity.py` (zero `on_event` warnings), `pytest tests/test_multi_tier.py -k test_talos_version`, full multi-tier regression, `pytest tests/test_openreview_source.py`, `python src/utils/verify_dependency_map.py --ci` (exit 0), `bash -n run_talos.sh`, strict UTF-8 scan (zero U+FFFD replacement glyphs).

### 15.24 Research Setup Wizard, Local Cognitive Input Validation & Failsafe Onboarding (v5.12.0)

**Overview:** `src/utils/research_setup_wizard.py` implements a 4-step, English-first onboarding wizard that configures a fresh TALOS deployment while remaining fully air-gapped-safe.

- **Visual header & welcome panel:** a Rich `Panel` introduces the 4-step flow (Research Topic, AI Execution Strategy, Historical Search Window, First Flight Test) in professional academic English.
- **Runtime probing & auto-spawn** (`_ensure_local_ai_runtime()`): probes the Fast Edge endpoint (port 11435) and standard Ollama (port 11434) with a 0.8s socket timeout; on failure it silently spawns `ollama serve` (CREATE_NO_WINDOW on Windows) and performs a bounded 2-second poll. Returns `True` for Active LLM mode and `False` for Heuristic Bypass mode, logging `[INFO] Local AI servers offline. Engaging rule-based heuristic validation.` on fallback.
- **Step 1 -- Cognitive scope validation:** in Active LLM mode the Fast Edge model (Llama-3.1-8B / Neutrino-8B) analyses the topic with a hard 2-second timeout (`_analyze_scope_with_llm` via `ThreadPoolExecutor`), suggesting 2-3 sub-domains when the input is under 4 words; in Heuristic Bypass mode `_analyze_scope_heuristic` enforces a minimum 3-word threshold and `_suggest_subdomains_heuristic` returns deterministic examples. Query generation reuses `src.ai.llm.query_translator.flatten_json` (`_generate_queries_llm`) with a deterministic English fallback (`_generate_queries_heuristic`) producing 16 source queries plus `inclusion_criteria` / `exclusion_criteria`.
- **Step 2 -- Execution strategy:** `_apply_execution_strategy` writes `TALOS_NETWORK_STRATEGY` (`strict_local` / `local_first`) and `TALOS_ALLOW_CLOUD_FALLBACK` into `.env` via `dotenv.set_key(quote_mode="never")`.
- **Step 3 -- Search window:** `_write_search_window` persists `research_search_window`, `search_window_label`, `search_window_start_year` / `end_year`, and `days_to_search_historic` into `config.json` (Recent 730d / Standard 1825d / Retrospective 4015d).
- **Step 4 -- First flight:** `_run_first_flight` auto-bootstraps the FastAPI server (`_ensure_api_server`), triggers a 10-paper test search via `POST /api/v1/scrape/trigger`, and opens the 3D visualizer (`http://127.0.0.1:8001/api/v1/visualizer/live`).
- **First-run sentinel:** `_create_sentinel` writes `data/.talos_onboarded` only after successful completion; `talos.py:main_menu()` auto-invokes the wizard once when the sentinel is absent and fast-boots (<0.3s) when present. `profile_settings_menu()` exposes "2. Run Research Setup Wizard (Interactive Guide)".
- **ISO/IEC 25010 usability compliance:** deterministic degradation, no blocking prompts on console-less workers, bounded wait times, and English-first academic output meet the operability, fault tolerance, and accessibility sub-characteristics.

**Verification surface:** release gates include `python -m compileall src config tests talos.py`, `pytest tests/test_system_integrity.py`, `pytest tests/test_multi_tier.py -k test_talos_version` (v5.12.0), `pytest tests/test_research_setup_wizard.py`, `python src/utils/verify_dependency_map.py --ci` (exit 0), `bash -n run_talos.sh`, and a strict UTF-8 scan (zero U+FFFD glyphs).

### 15.25 Research Wizard Query Transparency & CLI Fast-Dispatch Engine (v5.12.1)

**Overview:** v5.12.1 adds two human-in-the-loop and operations conveniences: a query-transparency preview in the Research Setup Wizard, and a CLI fast-dispatch engine in `talos.py`.

- **Wizard query-transparency table** (`_render_query_preview()` in `src/utils/research_setup_wizard.py`): after Step 1 compiles the 16 academic queries, a rounded Rich Table (`box.ROUNDED`, title "Generated Academic Search Queries") previews the boolean query strings for the top primary sources (arXiv, IEEE Xplore, Scopus (Elsevier), OpenAlex, Semantic Scholar, Springer Link), followed by a Rich `Panel` summarizing the compiled `inclusion_criteria` / `exclusion_criteria`.
- **User confirmation gate** (`_step1_research_topic()`): a Questionary confirm ("Proceed with these compiled search parameters?", default `True`, `TALOS_QUESTIONARY_STYLE`) gates persistence to `config.json`; declining re-enters the research-scope prompt, while cancelling (Ctrl+C / None) aborts without writing anything.
- **CLI fast-dispatch engine** (`talos.py:_handle_cli_flags()` / `_cli_help_table()`): lightweight `sys.argv` parsing in `if __name__ == "__main__"` supports `--wizard` (launch `research_setup_wizard.py`), `--daily` (launch `daily_search.py`), `--stats` (launch `db_stats.py`), and `--help` / `-h` (render a Rich flag-reference table). Each flag dispatches through the existing `run_script()` helper and exits cleanly with code 0; no flags preserve the interactive `main_menu()` flow.

**Verification surface:** release gates include `python -m compileall src config tests talos.py`, `pytest tests/test_system_integrity.py`, `pytest tests/test_multi_tier.py -k test_talos_version` (v5.12.1), `python talos.py --help` (exit 0), `python src/utils/verify_dependency_map.py --ci` (exit 0), `bash -n run_talos.sh`, and a strict UTF-8 scan (zero U+FFFD glyphs).

### 15.26 Self-Healing AI Manager, 5-Tier Strategy Matrix & Research Wizard Integrity Engine (v5.12.2)

**Overview:** v5.12.2 hardens the AI manager for zero-touch local operation and cleans heuristic fallback queries for valid boolean execution. It adds a self-healing Ollama probe/spawn, lazy on-demand cloud credential injection, silent provider trimming, a google.genai GA SDK migration, and a heuristic stopword filter.

- **Self-healing Ollama probe & spawn** (`src/core/ai_manager.py:probe_local_ollama()` / `_ensure_local_ollama_runtime()`): a 0.8s `GET http://127.0.0.1:11434/api/tags` pre-flight; when offline it consults `auto_start_local_llm`, offers a `TALOS_QUESTIONARY_STYLE` confirm, spawns `ollama serve` detached (`CREATE_NEW_PROCESS_GROUP | DETACHED_PROCESS` on Windows), and polls up to 3.0s (0.5s interval) before graceful degradation.
- **Provider trimming** (`provider_status` map): cloud providers (Gemini, NVIDIA, Groq, Cerebras, GitHub Models, Mistral, DeepSeek, HuggingFace, OpenRouter) register only when their API key is present; missing keys are parked silently as `STANDBY_NO_KEY` without warning cascades or network attempts.
- **On-demand cloud key injection** (`_prompt_cloud_key()` / `_persist_env_key()` / `_register_cloud_provider_on_demand()` / `_ensure_cloud_credential_for_fallback()`): interactive masked `questionary.password` prompt, key validation, `os.environ` injection, clean `.env` append (gitignored, dedup-safe), and runtime provider registration.
- **Google GenAI GA SDK migration** (`_execute_gemini_request()`): prefers `google.genai` (`genai_types.GenerateContentConfig`) with legacy `google.generativeai` fallback, eliminating the end-of-support `FutureWarning`.
- **Heuristic stopword filter** (`src/utils/research_setup_wizard.py:_extract_salient_terms()`): strips English stopwords and punctuation noise, preserves hyphenated compounds, and caps boolean queries at 4-6 salient tokens for valid IEEE Xplore / Scopus / arXiv queries.
- **5-Tier AI execution strategy matrix** (`research_setup_wizard.py:EXECUTION_STRATEGIES` / `ai_strategy_selector.py`): the full five-tier hierarchy -- `strict_local` (100% air-gapped), `local_first` (local GPU priority, cloud fallback on OOM), `cloud_first` (cloud priority, local fallback on network failure), `strict_cloud` (0% GPU VRAM footprint to leave the workstation GPU free for concurrent PhD deep-learning runs such as ST-GNNs / HMADRL), and `auto_dynamic` (autonomous 2D router adapting to VRAM and task complexity) -- persisted to `config.json` (`ai_execution_strategy`) and `.env` (`TALOS_NETWORK_STRATEGY`), exposed via `--strategy [mode]` and the TUI switcher.
- **Day-based historical search window** (`_step3_search_window()` / `_prompt_custom_days()`): PRISMA-ScR day windows (30d, 365d, 1095d, 1825d, 3650d) plus custom positive-integer days, persisting `days_to_search_historic`.
- **Sentinel & cancellation integrity** (`_render_cancelled()`): graceful abort on any cancellation, zero `'N/A'` config writes, guarded `data/.talos_onboarded` sentinel.
- **Thinking/reasoning model parser** (`_strip_thinking_tags()` / `_extract_assistant_content()`): unwraps `reasoning_content`, `thinking`, and `<think>` tags across the Ollama/OpenAI endpoints.
- **English-first cognitive mandate** (`LANGUAGE_AND_SYNTAX_MANDATE`): enforces formal academic English in inclusion/exclusion criteria, disallowing hallucinated `topic:` prefixes.
- **Local GPU baseline** (`LOCAL_GPU_MODEL`): defaults to verified `llama3.1:8b`.

**Verification surface:** release gates include `python -m compileall src config tests talos.py`, `pytest tests/test_system_integrity.py`, `pytest tests/test_multi_tier.py -k test_talos_version` (v5.12.2), `pytest tests/test_research_setup_wizard.py` (28 tests), `python src/utils/verify_dependency_map.py --ci` (exit 0), `bash -n run_talos.sh`, and a strict UTF-8 scan (zero U+FFFD glyphs).


### 15.27 Research Pivot Modernization & Setup Wizard TUI Integration (v5.12.3)

**Overview:** v5.12.3 repairs the Research Pivot Wizard's broken subprocess paths and silent-failure reporting, eliminates the lingering mythological codenames, and promotes the Research Setup Wizard to the head of the Configuration & Profiles TUI menu.

- **Canonical subprocess path resolution** (`src/ai/llm/research_pivot.py:_resolve_script_path()` / `run_script()`): the broken `scripts/` subfolder and stale `src/ai/scripts/query_translator.py` path are replaced by a REPO_ROOT-anchored `_SCRIPT_MAP` resolving the Cognitive Query Compiler (`src/ai/llm/query_translator.py`), the database re-evaluation script (`src/utils/reevaluate_database.py` / `recalculate_scores.py`), and the DRL trainer (`src/ai/drl/train_agent.py`); every subprocess is launched with `sys.executable` (the active Conda interpreter).
- **Strict subprocess returncode verification**: the wizard captures `proc.returncode` and reports `YES` in the Pivot Summary only for returncode 0; any non-zero code surfaces as `FAILED (Code X)` with trailing output, eliminating the previous `YES` on exit code 2.
- **Rule 9 codename elimination**: lingering `PYTHIA` and `CHIRON` replaced with ISO/IEC 25010 functional terminology -- Cognitive Query Compiler and Citation Graph Analyzer -- across the Research Pivot Wizard and the Configuration & Profiles TUI menu.
- **Research Setup Wizard TUI promotion** (`talos.py:profile_settings_menu()`): the wizard is promoted to option 1 ("Research Setup Wizard (Full Onboarding & Reconfiguration)"), enabling re-running at any time to re-tune research scope, 16 search queries, criteria, search window, and AI execution strategy; remaining menu entries renumbered.

**Verification surface:** release gates include `python -m compileall src config tests talos.py`, `pytest tests/test_system_integrity.py`, `pytest tests/test_multi_tier.py -k test_talos_version` (v5.12.3), `pytest tests/test_research_setup_wizard.py` (28 tests), `python src/utils/verify_dependency_map.py --ci` (exit 0), `bash -n run_talos.sh`, and a strict UTF-8 scan (zero U+FFFD glyphs).


### 15.28 Concurrent Ingestion Mesh & Multi-Profile Research Onboarding (v5.12.4)

**Overview:** v5.12.4 introduces a pre-flight profile target gate to the Research Setup Wizard and replaces the sequential 16-source harvest loop with a concurrent ThreadPoolExecutor mesh, collapsing harvest latency from roughly 35-45 seconds to 3-4 seconds.

- **Step 0 Profile Target Selection** (`src/utils/research_setup_wizard.py:_step0_profile_selection()`): a three-way pre-flight gate (reconfigure the active profile in place, switch to an existing isolated profile, or create a fresh isolated `_profiles/<name>/` workspace) backed by `_list_profiles()` / `_get_active_profile()` / `_set_active_profile()` / `_seed_profile_config()` / `_load_profile_config_to_root()` / `_persist_active_config()`. The canonical `_profiles/active_profile.txt` marker drives `get_active_profile_db_path()` (the single-source-of-truth per-profile SQLite resolver), and the header panel renders `Target Profile: [<target_profile>]`.
- **Concurrent Academic Ingestion Mesh** (`src/ingestion/daily_search.py`): `ThreadPoolExecutor(max_workers=min(16, len(enabled_scrapers)))` isolates each provider in `_harvest_single_source(scraper_name, query, criteria, date_limit)` with per-thread stdout capture and a full exception guard; a timeout or HTTP error in one provider (e.g. Science.gov or OSTI) never aborts the batch. Results are gathered via `concurrent.futures.as_completed()` and aggregated on the main thread.
- **Real-time Rich Live telemetry**: a live table tracks WAITING / HARVESTING / COMPLETED / FAILED per source with Papers Found and Elapsed Time columns, followed by a final summary panel (total harvest time, raw count, deduplicated count).
- **DOI + normalized-title-hash deduplication** (`_deduplicate_papers()` / `_normalize_title()` / `_title_hash()`): main-thread dedup keyed by DOI with a SHA-1 normalized-title fallback collapses cross-source duplicates before database insertion.

**Verification surface:** release gates include `python -m compileall src config tests talos.py daily_search.py`, `pytest tests/test_system_integrity.py`, `pytest tests/test_multi_tier.py -k test_talos_version` (v5.12.4), `pytest tests/test_research_setup_wizard.py` (39 tests), `python src/utils/verify_dependency_map.py --ci` (exit 0), `bash -n run_talos.sh`, and a strict UTF-8 scan (zero U+FFFD glyphs).


### 15.29 Full-Stack Concurrent Multi-Threaded Engine & High-Throughput Harvester (v5.13.0)

**Overview:** v5.13.0 completes the end-to-end concurrency overhaul: it extends the concurrent ingestion mesh to historical harvesting and introduces a concurrent cognitive evaluation pool with dynamic VRAM-aware worker throttling, alongside batched SQLite WAL re-evaluation.

- **Concurrent Cognitive Evaluation Pool** (`src/core/ai_manager.py:batch_evaluate_papers()` / `_resolve_eval_concurrency()`): a multi-threaded batch evaluator scores an arbitrary list of papers through the structured JSON schema of `evaluate_paper_json()`. Worker concurrency is resolved from the 2D Execution Matrix via `_resolve_strategies()`: the Cloud Mesh (`cloud_first` / `strict_cloud`; DeepSeek, Gemini, Groq, and the OpenAI-compatible registry) runs `max_workers=8`, while local GPU (`strict_local` / `local_first`; Ollama) runs `max_workers=2` behind a bounded `threading.Semaphore(2)` to eliminate CUDA Out-Of-Memory risks. Results preserve input order as `(paper, evaluation_dict_or_None)` pairs.

- **Concurrent Historical Ingestion Mesh** (`src/ingestion/historic_search.py`): the sequential multi-year fetch loop is replaced with `ThreadPoolExecutor(max_workers=min(16, len(enabled_sources)))`; each source runs in `_harvest_single_source()` with per-thread `contextlib.redirect_stdout` capture and full exception guards, aggregated via `as_completed()` on the main thread and deduplicated by DOI + SHA-1 normalized-title hash.

- **Real-time Rich Live telemetry for historical harvesting**: a Rich Live table renders WAITING / HARVESTING / COMPLETED / FAILED per source with Papers Found and Elapsed Time columns, closing with a Historical Ingestion Summary panel.

- **Concurrent database re-evaluation** (`src/utils/reevaluate_database.py:_apply_evaluation_batch()`): the sequential loop now drives `batch_evaluate_papers()` and persists results with batched SQLite WAL commits (grouped UPDATE statements on a single WAL connection).

**Verification surface:** release gates include `python -m compileall src config tests talos.py daily_search.py`, `pytest tests/test_system_integrity.py`, `pytest tests/test_multi_tier.py -k test_talos_version` (v5.13.0), `pytest tests/test_research_setup_wizard.py`, `python src/utils/verify_dependency_map.py --ci` (exit 0), `bash -n run_talos.sh`, and a strict UTF-8 scan (zero U+FFFD glyphs).

### 15.30 System Diagnostics Analyzer & Operational Integrity Engine (v5.13.1)

**Overview:** v5.13.1 adds an ISO/IEC 25010 Diagnosability and Fault Tolerance layer: a self-contained System Diagnostics Analyzer that performs an 8-point pre-flight health check over the local, air-gapped runtime and renders a structured Rich health report with one-line remediation guidance for every failure.

- **System Diagnostics Analyzer** (`src/utils/system_diagnostics.py: SystemDiagnosticsEngine`): `run_diagnostics()` executes eight isolated, non-fatal probes in strict local-first order -- `check_python_environment()` (Python 3.11.x + `talosenv` conda environment), `check_database_integrity()` (`PRAGMA integrity_check` + WAL journal mode on the active profile database), `check_local_ai_runtime()` (0.8s HTTP GET to Ollama `/api/tags` verifying `LOCAL_GPU_MODEL`), `check_port_availability()` (conflict probe for ports 8001/8000/11434/11435), `check_filesystem_permissions()` (read/write probes on `data/`, `_profiles/`, `logs/`), `check_environment_credentials()` (`.env` structure validation with secret redaction), `check_daemon_status()` (`talos_service.py` process detection), and `check_network_endpoints()` (concurrent probe of 7 zero-key open repositories -- arXiv, OpenAlex, Crossref, DBLP, PubMed (NCBI), OSTI (DOE), PLOS -- with per-endpoint latency and a 1.5s timeout, guarded for air-gapped operation).
- **Rich health report** (`render_report()`): a `box.ROUNDED` Rich table titled "TALOS System Diagnostic Health Report" with Component / Target-Metric / Status (PASS green / WARN yellow / FAIL red) / Remediation Guidance columns; every failure carries a one-line copy-paste remediation.
- **CLI fast-dispatch** (`talos.py`): `--diagnostics` (canonical ISO flag) and `--doctor` / `-d` (DevOps alias) run `SystemDiagnosticsEngine().run_and_render()` headless and exit cleanly.
- **TUI Group 6 integration**: `system_health_menu()` gains Option 1 "System Health & Diagnostic Analyzer", with the remaining options renumbered 1-8 to 2-9.

**Verification surface:** release gates include `python -m compileall src config tests talos.py`, `pytest tests/test_system_integrity.py`, `pytest tests/test_multi_tier.py -k test_talos_version` (v5.13.1), `python talos.py --diagnostics` / `--doctor` (exit 0), `python src/utils/verify_dependency_map.py --ci` (exit 0), `bash -n run_talos.sh`, and a strict UTF-8 scan (zero U+FFFD glyphs).

### 15.31 Stanford DSPy PRISMA-ScR Pipeline & Declarative Synthesis Engine (v5.14.0)

**Overview:** v5.14.0 integrates the Stanford DSPy declarative programming paradigm into the PRISMA-ScR scoping review workflow, replacing brittle string prompts with typed declarative signatures and a four-phase linear pipeline, fully air-gapped and local-first.

- **Typed declarative signatures** (`src/prisma/dspy_signatures.py`): Pydantic-v2 schema models -- `PrismaPlanSignature` (topic/scope -> search facets, boolean strategy, methodological inclusion/exclusion criteria), `PrismaScreeningSignature` (title/abstract -> INCLUDE/EXCLUDE/UNCERTAIN decision + bounded relevance score + chain-of-thought), `PrismaEligibilitySignature` (deep assessment -> ELIGIBLE/INELIGIBLE + swarm algorithm type / learning paradigm / network architecture), `PrismaSynthesisSignature` (included-studies summary -> thematic taxonomy, methodological distribution, gaps, narrative), plus `extract_json_payload()` recovery.
- **PlanEval modules** (`src/prisma/dspy_modules.py`): `PrismaPlanner.plan()` (multi-database search protocol), `PrismaEvaluator.screen()` (Chain-of-Thought screening over `AIManager.analyze_generic_text`), `PrismaEligibilityJudge.assess()`, and `PrismaExecutor.run()` (4-phase flow with live counters N_identified / N_dedup / N_screened / N_excluded / N_eligible / N_included); deterministic keyword fallback for air-gapped hosts.
- **PRISMA 2020 Mermaid flowchart generator** (`src/prisma/mermaid_generator.py`): `generate_prisma_mermaid(counts)` emits an exact-count `flowchart TD`, with `mermaid_to_markdown()` / `mermaid_to_html()` export wrappers.
- **Scoping review synthesizer** (`src/prisma/scoping_review_synthesizer.py`): `synthesize_scoping_review()` (7-section Markdown) and `synthesize_scoping_review_latex()` (LaTeX article draft).
- **CLI/TUI surface**: `talos.py --prisma` fast-dispatch flag and the Group 3 Advanced Analysis menu option.
- **Rule 10 dossier**: `docs/internal/academic/01_STANFORD_DSPY_PRISMA_PIPELINE.md`.

**Verification surface:** release gates include `python -m compileall src config tests talos.py`, `pytest tests/test_system_integrity.py`, `pytest tests/test_multi_tier.py -k test_talos_version` (v5.14.0), `python talos.py --help` (lists `--prisma`), `python src/utils/verify_dependency_map.py --ci` (exit 0), `bash -n run_talos.sh`, and a strict UTF-8 scan (zero U+FFFD glyphs).

### 15.32 Multi-Agent Peer-Review Swarm & Consensus Engine (v5.14.1)

**Overview:** v5.14.1 augments the PRISMA-ScR screening stage with a multi-agent peer-review swarm and an automated inter-rater reliability engine, replacing the single-screener decision with three specialized reviewer personas and a statistically grounded Chain-of-Thought consensus arbiter, fully air-gapped and local-first.

- **Multi-agent review swarm** (`src/prisma/swarm_evaluators.py`): `AlgorithmicReviewer` (mathematical formulation, HMADRL / Dec-POMDPs / QMIX DRL, ST-GNNs / ST-GAT), `EmpiricalReviewer` (Gazebo / AirSim / Isaac Gym, ablations, benchmarks, metrics), and `OperationalReviewer` (scalability, communication topology and latency, collision avoidance, NATO / CJCSI) -- each emitting a typed `ReviewerVerdict` (vote, 0.0-10.0 score, 0.0-1.0 confidence, critiques).
- **Inter-rater reliability** (`calculate_cohens_kappa` / `cohens_kappa_pairwise`): Fleiss' multi-rater generalization of Cohen's Kappa `kappa = (p_o - p_e)/(1 - p_e)` over the three votes, plus a classical pairwise two-rater kappa for auditing.
- **Consensus arbiter** (`SwarmConsensusArbiter.adjudicate`): unanimous (3-0 / 0-3) short-circuits to an instant high-confidence decision; split (2-1 / 1-2 / 1-1-1) invokes Chain-of-Thought adjudication, falling back to a 2-1 majority (or UNCERTAIN on a tie); returns a `ConsensusVerdict` (final decision, confidence-weighted consensus score, Cohen's Kappa, multi-perspective synthesis narrative).
- **PRISMA pipeline integration** (`src/prisma/dspy_modules.py` + `dspy_signatures.py`): `PrismaEvaluator.evaluation_mode` (`'single'` / `'swarm'`); the swarm path dispatches the three personas via `ThreadPoolExecutor` bounded by `threading.Semaphore(2)` (2 local / 3 cloud workers) and records `consensus_mode`, `swarm_kappa`, and `agent_verdicts` on the screening signature; `PrismaExecutor.run()` logs mean Cohen's Kappa during Screening.
- **CLI/TUI surface**: `talos.py --prisma --swarm` fast-dispatch flag and the Group 3 "Select Screening Mode" prompt.
- **Rule 10 dossier**: `docs/internal/academic/02_MULTI_AGENT_CONSENSUS_SWARM.md`.

**Verification surface:** release gates include `python -m compileall src config tests talos.py`, `pytest tests/test_system_integrity.py`, `pytest tests/test_multi_tier.py -k test_talos_version` (v5.14.1), `python talos.py --help` (lists `--prisma [--swarm]`), the swarm evaluator unit exercise (3-agent review + Cohen's Kappa, exit 0), `python src/utils/verify_dependency_map.py --ci` (exit 0), `bash -n run_talos.sh`, and a strict UTF-8 scan (zero U+FFFD glyphs).

### 15.33 BibTeX Scientific Exporter, 18-Source Aerospace Ingestion & Feature Freeze (v5.14.2)

**Overview:** v5.14.2 introduces a local BibTeX/LaTeX scientific library exporter and expands the academic ingestion mesh from 16 to 18 sources by integrating two keyless grey literature repositories -- the NASA Technical Reports Server and the HAL open science repository (CNRS / Inria / ONERA) -- while persisting the PRISMA screening decision for reproducible systematic review, fully air-gapped and local-first.

- **BibTeX Scientific Exporter** (`src/utils/bibtex_exporter.py`): `BibTeXExporter` with `export_library(output_path, min_score, only_prisma_included, active_profile)`, `render_export_summary`, and `export_and_render`; generates standard-compliant `@article`/`@inproceedings` entries with `AuthorYearTitleKeyword` cite keys (e.g. `Smarlamakis2026Cooperative`), sanitizes all LaTeX reserved characters (&, %, $, #, _, {, }), and emits title, author, journal/booktitle, year, doi, url, abstract, keywords, and a `note` carrying the TALOS evaluation score; defaults to `data/exports/talos_library.bib`.
- **NASA NTRS Harvester** (`src/ingestion/nasa_ntrs_source.py`): `NasaNtrsSource.fetch_new_papers()` / `search_papers()` / `_format_paper()` over `https://ntrs.nasa.gov/api/citations/search` (pure JSON, no API key) for aerospace technical reports (NASA TM/TP/CR), flight control, avionics, and autonomous swarm research.
- **HAL/Inria Harvester** (`src/ingestion/hal_inria_source.py`): `HalInriaSource.fetch_new_papers()` / `search_papers()` / `_format_paper()` over `https://api.archives-ouvertes.fr/search/` (Solr-style JSON, no API key) for CNRS/Inria/ONERA robotics, multi-agent reinforcement learning, and French/EU PhD theses.
- **18-source registry**: `SOURCE_REGISTRY` in `daily_search.py` and `historic_search.py` gains `nasa_ntrs` and `hal_inria`; `max_workers=18`; `ALL_ACADEMIC_SOURCES` (checkbox TUI) and `_ALL_VISUALIZER_SOURCES` (API health map) expanded; `OPEN_ACADEMIC_ENDPOINTS` probes both endpoints.
- **Persisted PRISMA decision**: `papers.prisma_decision` nullable column (idempotent `ALTER TABLE` in `database_manager.create_table()`) enables the exporter's INCLUDE-only filter.
- **CLI/TUI surface**: `talos.py --export-bib [min_score]` fast-dispatch flag and the Group 5 Database Maintenance option 12.
- **Rule 10 dossier**: `docs/internal/academic/03_GREY_LITERATURE_AEROSPACE_EXPANSION.md`.

**Verification surface:** release gates include `python -m compileall src config tests talos.py` (0 errors), `pytest tests/test_system_integrity.py -q`, `pytest tests/test_multi_tier.py -k test_talos_version` (v5.14.2), `python talos.py --export-bib` (exit 0), source-factory mock tests (18 sources), `python src/utils/verify_dependency_map.py --ci` (exit 0), `bash -n run_talos.sh`, and a strict UTF-8 scan (zero U+FFFD glyphs).

### 15.34 Universal Scientific Search Hub & Neural Graph Discovery Engine (v5.15.0)

**Overview:** v5.15.0 modularizes the 18-source ingestion mesh into a dedicated `src/ingestion/sources/` subpackage behind a unified `SOURCE_REGISTRY`, and introduces the `src/search/` package with three graph-and-embedding discovery engines -- Citation Snowballing, Neural Vector Search, and Code-First Search -- fully local-first and air-gapped, exposed through new CLI flags and the Group 2 Universal Search Hub TUI menu.

- **Modular ingestion subpackage** (`src/ingestion/sources/`): `SOURCE_REGISTRY` mapping all 18 keys to their adapter classes, plus `ALL_SOURCE_NAMES`; `daily_search.py` / `historic_search.py` import the canonical registry from the subpackage.
- **Citation Snowballing Engine** (`src/search/citation_snowballing.py`): `CitationSnowballEngine.resolve_seed()` (DOI / DB ID / title), `backward_snowball()` / `forward_snowball()` (OpenAlex/Crossref/Semantic Scholar graph traversal, 2024-2026 forward window), `_filter_relevant()` (PrismaEvaluator / deterministic fallback), `_import_papers()`, and `generate_genealogy()`.
- **Neural Vector Search** (`src/search/neural_vector_search.py`): `NeuralVectorSearchEngine.embed()` / `cosine_similarity()` / `rank()` over the local `nomic-embed-text` model (port 11434), with a lexical fallback offline.
- **Code-First Search** (`src/search/code_first_search.py`): `CodeFirstSearchEngine._search_github_repos()` / `_search_paperswithcode()` / `_is_reproducible()` for GitHub / PapersWithCode / ROS2 / Gazebo / AirSim / Isaac Gym reproducibility signals.
- **CLI/TUI surface**: `--snowball [seed]`, `--vector-search [query]`, `--code-search [query]` fast-dispatch flags and a restructured Group 2 "Universal Search Hub" menu.
- **Rule 10 dossier**: `docs/internal/academic/04_NEURAL_GRAPH_SEARCH_PARADIGMS.md`.

**Verification surface:** release gates include `python -m compileall src config tests talos.py` (0 errors), `pytest tests/test_system_integrity.py -q`, `pytest tests/test_multi_tier.py -k test_talos_version` (5.15.0), `pytest tests/test_neural_vector_search.py -q` (mock `nomic-embed-text` embeddings, exit 0), ingestion modularization smoke test, `python src/utils/verify_dependency_map.py --ci` (exit 0), `bash -n run_talos.sh`, and a strict UTF-8 scan (zero U+FFFD glyphs).

### 15.35 Persistent Vector Cache & Accelerated Neural Embedding Engine (v5.15.1)

**Overview:** v5.15.1 introduces a persistent SQLite vector cache and an accelerated neural embedding engine that together cut semantic search latency from minutes to under 50ms while eliminating redundant re-embedding across runs, fully local-first and air-gapped.

- **Persistent vector cache** (`src/core/database_manager.py`): idempotent `paper_embeddings` table (BLOB-encoded float32 vectors, per-model index, `ON DELETE CASCADE` foreign key) plus `get_cached_embeddings(model_name)` (deserializes BLOBs into `paper_id -> float32` vectors) and `save_embeddings_batch(records)` (atomic `INSERT OR REPLACE` in WAL mode).
- **Incremental indexing + Rich progress** (`src/search/neural_vector_search.py`): `_index_uncached()` renders a live `rich.progress.Progress` bar (percentage, completed/total, ETA via `{task.time_remaining}`) for the uncached delta only, embedding concurrently via `ThreadPoolExecutor` (max 8 workers) and persisting in batches of 64.
- **Vectorized matrix cosine similarity** (`src/search/neural_vector_search.py`): `_matrix_rank()` assembles a single N x 768 document matrix and computes `S_C(q, D) = (q . D^T) / (||q|| ||D||)` in one NumPy vectorized pass.
- **Rich Table presentation** (`src/search/neural_vector_search.py`): `render_results()` renders top-K results in a `box.ROUNDED` table ("Neural Vector Semantic Search Results") with Rank, Similarity (%), Title, Year / Source, DOI / URL, and Key Abstract Match Snippet; JSON output preserved via `run(..., render=False)`.

**Verification surface:** release gates include `python -m compileall src config tests talos.py` (0 errors), `pytest tests/test_system_integrity.py -q`, `pytest tests/test_multi_tier.py -k test_talos_version` (5.15.1), `pytest tests/test_neural_vector_search.py -q` (mock `nomic-embed-text` embeddings, exit 0), persistent cache round-trip smoke test (`get_cached_embeddings` / `save_embeddings_batch`), `python src/utils/verify_dependency_map.py --ci` (exit 0), `bash -n run_talos.sh`, and a strict UTF-8 scan (zero U+FFFD glyphs).

### 15.36 Unified Reporting & Visual Telemetry across all 6 Discovery Modes (v5.15.2)

**Overview:** v5.15.2 harmonizes the UX and reporting surface of the Universal Search Hub by giving every discovery mode a dedicated styled Rich Table and a timestamped Markdown report, while eliminating raw JSON dumps from the TUI and CLI. All rendering and reporting operate 100% locally from the active SQLite database and in-memory result models (air-gapped safe).

- **Code-First Search reporting** (`src/search/code_first_search.py`): `render_results()` renders reproducible repositories in a `box.ROUNDED` table ("Reproducible Code-First Search Results") with Rank, Stars (`[bold yellow]N stars[/bold yellow]`, zero emoji), Repository Name, Paper Title & Description, Topics & Frameworks, and GitHub URL columns, plus supplementary PapersWithCode and matching-database tables; `export_search_report()` writes `data/reports/code_search/code_search_YYYYMMDD_HHMMSS.md` with clickable URLs; `run(..., render=True)` auto-invokes both.
- **Citation Snowballing reporting** (`src/search/citation_snowballing.py`): `render_genealogy()` renders the citation graph in a `box.ROUNDED` table ("Citation Snowballing Genealogy Graph") with Traversal (Backward/Forward), Depth, Title, Year / Source, DOI / URL, and Relevance Score columns; `export_snowball_report()` writes `data/reports/snowball/snowball_YYYYMMDD_HHMMSS.md` with Backward (Cited References) and Forward (Citing Recent Literature 2024-2026) tables and clickable links; `run(..., render=True)` auto-invokes both.
- **Neural Vector Search reporting** (`src/search/neural_vector_search.py`): pre-existing `render_results()` and `export_search_report()` (v5.15.1) now complete the unified trio across all three `src/search/` engines.
- **TUI/CLI consolidation** (`talos.py`): `--code-search` and `--snowball` fast-dispatch flags plus Group 2 menu options 3 (Snowballing) and 5 (Code-First) invoke `run()` directly; the dead `_render_search_result()` JSON-dump helper was removed.

**Verification surface:** release gates include `python -m compileall src config tests talos.py` (0 errors), `pytest tests/test_system_integrity.py -q`, `pytest tests/test_multi_tier.py -k test_talos_version` (5.15.2), `python talos.py --code-search "spatio temporal graph neural networks"` and `python talos.py --snowball "10.1109/TTE.2026.3665346"` smoke tests, `python src/utils/verify_dependency_map.py --ci` (exit 0), `bash -n run_talos.sh`, and a strict UTF-8 scan (zero U+FFFD glyphs).

### 15.37 Session-Level Circuit Breakers, Multi-Key Author Normalization, and Silent Daemon Lifecycle (v5.15.3)

**Overview:** v5.15.3 targets operational reliability in the 24/7 daemon: it removes the repetitive per-paper fallback log spam emitted during evaluations, hardens author extraction so no evaluation ever reports a false "Unknown Authors" when author data exists, and guarantees that standalone workstation execution stays 100% silent about the external SYNAPSE bus being offline. All three mechanisms are pure in-process state machines -- no new network dependencies, no schema changes, fully air-gapped safe.

- **Fast Tier Circuit Breaker state machine** (`src/core/ai_manager.py`): a process-lifetime latch `AIManager.fast_tier_offline` (default `False`, i.e. CLOSED). The first connection-refused/timeout on the CPU Edge endpoint (`FAST_EDGE_BASE_URL`, port 11435) transitions the latch to OPEN/LATCHED, emits a single one-time notice (`[INFO] Fast CPU tier (11435) offline. Latching direct local GPU routing for this session.`), and routes directly to local GPU Ollama (`LOCAL_GPU_MODEL` at port 11434). While LATCHED, every subsequent fast-tier request bypasses port 11435 at the top of `_execute_ollama_http()` with ZERO network attempts, ZERO timeout latency, and ZERO warning logs. The latch is never reset mid-process (re-armed only on a new `AIManager` instance); the legacy `_fast_edge_offline_memo` is retained as a synonym. Root cause addressed: the prior per-batch memo logged an `[INFO]` fallback line on every subsequent paper evaluation; the session latch eliminates that entire class of repetitive spam.
- **Author Resolution Normalizer** (`src/utils/evaluation_history.py:normalize_authors(paper)`): a single canonical resolver consumed by both `src/ai/drl/talos_service.py` and `src/ai/drl/live_agent_orchestrator.py`. It resolves author data across the standard key precedence `authors_str` -> `authors` -> `author`, handling (a) a flat string, (b) a list of dicts (`{"name": ...}`, `{"author": {"display_name": ...}}`, `{"full_name": ...}`, `{"text": ...}`), (c) a list of strings, and (d) a comma/semicolon-delimited string. It returns a clean comma-separated string and falls back to "Unknown Authors" only when no standard key holds data.
- **Clean Daemon Evaluation Telemetry** (`src/ai/drl/talos_service.py`): the daemon loop emits one uncluttered Rich block per real evaluation -- `[EVAL] <Full Title> | Authors: <Extracted Authors> | Score: <X.X>/10 | [<DECISION>] -> DB` -- gated on a resolved title so empty/simulated steps stay silent.
- **Silent Standalone SYNAPSE Buffering** (`src/integration/synapse_client.py`): a Standalone Quiet Mode state machine (`synapse_available`) latches the bus offline on the first connection-refused probe (port 8000) and buffers every subsequent event silently to a bounded in-memory ring buffer plus best-effort JSONL (`data/synapse_buffer.jsonl`), emitting a single one-time notice (`[INFO] SYNAPSE bus offline (port 8000). Operating in standalone quiet mode (local event buffering active).`) and zero per-paper warnings.

**Verification surface:** release gates include `python -m compileall src config tests talos.py` (0 errors), `pytest tests/test_system_integrity.py -q`, `pytest tests/test_multi_tier.py -k test_talos_version` (5.15.3), `pytest tests/test_session_circuit_breaker.py -q` (12 passed: 10 author-normalization + 2 circuit-breaker latching), `python src/utils/verify_dependency_map.py --ci` (exit 0), `bash -n run_talos.sh`, and a strict UTF-8 scan (zero U+FFFD glyphs).

### 15.38 DRL Action-Space Expansion, Net2Net Checkpoint Surgery, and 18-Source Autonomous Foraging (v5.15.4)

**Overview:** v5.15.4 expands the autonomous foraging action space from 16 to 18 academic sources and migrates the trained DDDQN checkpoint to the new geometry without retraining, preserving all pre-trained episodes of knowledge. The release has three pillars: (1) the Gymnasium environment (`talos_env.py`) grows `ALL_KNOWN_SOURCES` to 18 by registering NASA NTRS and HAL/Inria, scaling the action space from `Discrete(17)` to `Discrete(19)` and the observation space from 23 to 25 dimensions; (2) a Net2Net (Net2WiderNet) tensor-surgery utility (`scripts/migrate_d3qn_checkpoint.py`) widens the DuelingLSTM advantage head and LSTM input layer in place; and (3) the active profile configs explicitly enable all 18 sources so the daemon reports 18 configured and working sources on startup.

- **DRL action-space expansion** (`src/ai/drl/talos_env.py`): `ALL_KNOWN_SOURCES` grows from 16 to 18 by appending `nasa_ntrs` and `hal_inria`. The action space becomes `spaces.Discrete(len(sources) + 1) == Discrete(19)` (actions 0..17 query the 18 sources, action 18 is the sleep/cooldown action), and the observation space becomes `1 + 18 + 2 + 4 = 25` dimensions. `_load_source_list()` now guarantees the full canonical 18-source list is always present; the companion modules `drl_agent.py` (input_dim=25 / action_dim=19), `drl_networks.py`, `live_agent_sources.py`, and `live_agent_orchestrator.py` are re-baselined accordingly.

- **Net2Net checkpoint surgery** (`scripts/migrate_d3qn_checkpoint.py`): a one-shot Net2WiderNet migration of `models/dddqn_trained.pth` to the 18-source geometry. The mathematical formulation is the standard Net2Net widening: for the advantage head `A.weight` (`[old_A, hidden] -> [19, hidden]`) and `A.bias` (`[old_A] -> [19]`), surviving source rows are copied identically, the four newly introduced source heads (`openaire`, `openreview`, `nasa_ntrs`, `hal_inria`) are initialised with the mean of the top-5 existing source rows (ranked by L2 norm) plus a +0.05 optimistic exploratory bias, and the sleep row is re-indexed to position 18. For the LSTM input layer `lstm1.weight_ih_l0` (`[512, 21] -> [512, 25]`), columns are remapped by source name, the four new source columns are initialised with a column-mean prior, and the two streak columns plus four provider columns are shifted to their new trailing positions. Inspection revealed the legacy checkpoint held 14 sources (state_dim=21, action_dim=15), so the name-based migration expands 15 -> 19 actions and 21 -> 25 state dimensions and is robust to any legacy ordering. The result is verified by a strict `DuelingLSTM(25, 19).load_state_dict()` load with zero tensor-mismatch errors; a safety backup `models/dddqn_trained.pth.bak` is created on first run.

- **18-source profile synchronization** (`config.json`, `config.template.json`, `_profiles/default_drones/config.json`): `nasa_ntrs` and `hal_inria` are added to the `max_results_config` surfaces and query-key sets (new `nasa_ntrs_query` / `hal_inria_query`), so `talos_service.py` detects and reports 18 configured and working sources on daemon startup.

- **Scopus/Elsevier XML-JSON author normalization locked in** (`src/utils/evaluation_history.py`): `normalize_authors()` explicitly resolves the Scopus `$`-wrapped value nodes, the `@name` / `@surname` attribute pairs, and the `given_name` / `surname` fallback, with a clean 4-author + "et al." truncation.

**Verification surface:** release gates include `python -m compileall src config tests talos.py` (0 errors), `pytest tests/test_system_integrity.py -q`, `pytest tests/test_multi_tier.py -k test_talos_version` (5.15.4), a standalone DRL model strict-load check (`DuelingLSTM(25, 19)`), daemon source detection (Configured sources: 18, Working sources: 18), `python src/utils/verify_dependency_map.py --ci` (exit 0), `bash -n run_talos.sh`, and a strict UTF-8 scan (zero U+FFFD glyphs).

### 15.39 Dual-Surface User Assistance Architecture, Interactive Web Manual, and IEEE Theoretical Foundations (v5.15.5)

**Overview:** v5.15.5 introduces a Dual-Surface User Assistance Architecture: a rich four-panel console manual rendered by `src/utils/help_system.py` (reachable via `python talos.py --help` and TUI Option 7), and an interactive zero-CDN Web Manual served at `GET /help` (`http://localhost:8001/help`, with `GET /manual` issuing a 307 redirect). The release also formalizes the system's scientific pedigree by adding a strict IEEE-style Section 5 "Scientific References & Theoretical Foundations" to `README.md` (English and Greek).

- **Four-panel Rich console manual** (`src/utils/help_system.py`): `render_help_manual(interactive=False)` returns a `rich.console.Group` of four panels -- (1) CLI Fast-Dispatch Flags, (2) Interactive Controls & Navigation, (3) Port Mapping & Services Architecture, (4) Generated Reports & Storage Artifacts. `render_help_manual(interactive=True)` prints the panels and prompts the user with an interactive action (`[O] Open Interactive Web Manual in Browser (http://localhost:8001/help)` vs `Return to Menu`), auto-bootstrapping the FastAPI backend on a cold start before `webbrowser.open(...)`. Zero emojis across every heading and cell (ISO/IEC 25010 Context of Use compliance).

- **Interactive Web Manual** (`templates/help_manual.html` + `src/api/main_api.py`): a self-contained, zero-CDN, responsive page matching the academic dark theme, with a live search filter bar, click-to-copy buttons beside every CLI command (Clipboard API with `execCommand` fallback), structured cards (CLI Commands, Research Search Paradigms, Ports & Services, Directory Layout), and a dark/print-mode toggle. Endpoints `GET /help` (HTMLResponse) and `GET /manual` (307 redirect) raise the REST surface from 23 to 25 endpoints.

- **Formal IEEE Scientific References & Theoretical Foundations** (`README.md`): Section 5 (English) and the mirrored Greek "Επιστημονικές Αναφορές & Θεωρητικό Υπόβαθρο" present ten strictly-formatted IEEE citations ([1]-[10]) spanning Stanford DSPy, Net2Net, PRISMA 2020, PRISMA-ScR, Cohen's Kappa, Fleiss' Kappa, citation snowballing, Nomic Embed, Dueling DQN, and Double Q-Learning.

**Verification surface:** release gates include `python -m compileall src config tests talos.py` (0 errors), `pytest tests/test_system_integrity.py -q`, `pytest tests/test_multi_tier.py -k test_talos_version` (5.15.5), `python talos.py --help` (4-panel Rich manual, exit 0), `GET /help` (HTMLResponse 200) and `GET /manual` (307 redirect), `python src/utils/verify_dependency_map.py --ci` (exit 0), `bash -n run_talos.sh`, and a strict UTF-8 scan (zero U+FFFD glyphs).

### 15.40 PRISMA Quality Appraisal, Kitchenham's Standardized Rubric, and the 2D Decision Quadrant Plane (v5.16.0)

**Overview:** v5.16.0 introduces the PRISMA Quality Appraisal & Dual-Axis Scientific Rigor Engine, operationalizing the Kitchenham et al. (2007) guidelines for systematic literature reviews as a standardized, six-question, three-point categorical rubric. The engine formally decouples Semantic Relevance (S_rel, the existing four-layer `overall_score`) from Methodological Quality (S_qual, computed by the rubric) and projects every study onto a 2D Evidence Decision Plane with four quadrants.

- **Typed Kitchenham rubric** (`src/prisma/quality_appraisal.py`): `KitchenhamRubric` is a Pydantic-v2 model whose six fields (`q1_aims_clarity`, `q2_context_realism`, `q3_baseline_rigor`, `q4_statistical_validity`, `q5_open_reproducibility`, `q6_limitations_negative_results`) are typed as `Literal[0.0, 0.5, 1.0]` and normalized by a `field_validator` calling `_normalize_ternary`, which snaps drifted local-LLM outputs (e.g. `1`, `0.75`) back onto the strict ternary grid. `quality_score` is a property computing `S_qual = (sum(Q_i) / 6.0) * 10.0`.

- **2D Evidence Decision Plane** (`map_evidence_quadrant`): the plane is partitioned by orthogonal thresholds tau_rel = 7.0 and tau_qual = 7.5, yielding `ELITE_FOUNDATIONAL` (S_rel >= 7.0 and S_qual >= 7.5), `IDEA_MINE` (S_rel >= 7.0 and S_qual < 7.5), `METHODOLOGICAL_EXEMPLAR` (S_rel < 7.0 and S_qual >= 7.5), and `METHODOLOGICAL_NOISE` (S_rel < 7.0 and S_qual < 7.5).

- **Batch appraisal** (`PrismaQualityAppraiser`): `appraise_paper()` prompts the multi-tier `AIManager` with the structured rubric, recovers JSON via `extract_json_payload`, validates, computes S_qual, and maps the quadrant. `appraise_candidates_batch(min_relevance=7.0)` queries `overall_score >= ? AND quality_score IS NULL`, then runs a `ThreadPoolExecutor` bounded by `VRAM_SEMAPHORE = threading.Semaphore(2)` on local GPU (8 workers on the Cloud Mesh), persisting each result through `DatabaseManager.update_paper_quality`. `render_quadrant_summary()` emits a Rich quadrant-distribution table.

- **SQLite schema expansion** (`src/core/database_manager.py`): idempotent `ALTER TABLE` adds `quality_score REAL`, `quality_rubric_json TEXT`, and `evidence_quadrant TEXT`; `update_paper_quality()` writes all three columns in one WAL transaction.

- **BibTeX dual-filter export** (`src/utils/bibtex_exporter.py`): `export_library()` gains `min_quality` and `quadrant`, building `overall_score >= ? AND (quality_score >= ? OR quality_score IS NULL)` (plus an optional quadrant predicate). Each entry emits a `note` field (`TALOS Relevance: X.X/10, Scientific Quality: Y.Y/10 (Kitchenham 2007: High Rigor), Quadrant: Z`), with `_rigor_label()` mapping quality to High/Moderate/Low Rigor.

- **Integration surfaces**: CLI `--appraise-quality [--min-score 7.0]` in `talos.py:_handle_cli_flags()`; TUI Group 3 Option 15; Panel 1 and Panel 4 of `src/utils/help_system.py`; a new interactive card in `templates/help_manual.html`; Kitchenham IEEE citations [11]-[12] in `README.md` (EN and GR); and Rule 10 academic dossier 05 under `docs/internal/academic/`.

**Verification surface:** release gates include `python -m compileall src config tests talos.py` (0 errors), `pytest tests/test_quality_appraisal.py -q` (17 hermetic tests), `pytest tests/test_system_integrity.py -q`, `pytest tests/test_multi_tier.py -k test_talos_version` (5.16.0), `python talos.py --appraise-quality --min-score 7.0` (Rich quadrant table), BibTeX `min_quality=7.5` dual-filter export, `python talos.py --help` / `GET /help`, `python src/utils/verify_dependency_map.py --ci` (exit 0), `bash -n run_talos.sh`, and a strict UTF-8 scan (zero U+FFFD glyphs).

### 15.41 Unified Multi-Profile Architecture, Workspace State Synchronization, and Canonical Research Partitioning (v5.16.1)

**Overview:** v5.16.1 unifies the multi-profile workspace under a strict Single Source of Truth (SSOT) and migrates the active PhD corpus into a canonical research partition. The release establishes `src/core/profile_manager.py` as the sole authority for profile path resolution, eliminates every legacy relative-path bug that produced phantom databases and stale active-profile markers, consolidates the 5,472-paper corpus (114 elite with `overall_score > 7`, 325 quality-appraised) into the `uav_mission_planning` profile, and unifies local AI inference on port 11434 (retiring the phantom 11435 fast-edge warning path).

- **ProfileManager SSOT** (`src/core/profile_manager.py`): the canonical class is anchored to repo-root `_profiles/` via `Path(__file__).resolve().parents[2]` and exposes `get_profiles_dir()`, `get_active_profile_name()`, `set_active_profile(name)` (validate, scaffold, write `active_profile.txt`, synchronize config), `list_profiles()`, `create_profile(name, seed_config)`, `get_active_db_path()`, and `get_active_config_path()`. Module-level aliases preserve `talos.py` compatibility.

- **DatabaseManager delegation** (`src/core/database_manager.py`): `get_active_profile_db_path()` delegates to `ProfileManager.get_active_db_path()`, so the daemon, offline DRL environment, OPTICA bridge, and daily digest share one resolver.

- **Canonical workspace migration**: `_profiles/uav_mission_planning/` now holds the populated database and a `config.json` locking `research_topic: "Drone Mission Planning (Task Allocation-Path Planning) with DRL and ST-GAT"`; `active_profile.txt` and root `config.json` are synchronized accordingly. The TUI banner renders `Profile: [uav_mission_planning]` and `Active Research Focus: ...`.

- **Local AI runtime unification**: `FAST_EDGE_URL` defaults to `http://127.0.0.1:11434/v1` (with `FAST_EDGE_BASE_URL` as a backward-compatible alias); `src/core/ai_manager.py` routes the fast edge tier directly to the verified Ollama runtime; `system_diagnostics.py`, `help_system.py`, and `help_manual.html` document 11434 as the Universal Local AI Runtime (GPU/CPU), removing every phantom 11435 probe.

**Verification surface:** release gates include `python -m compileall src config tests talos.py` (0 errors), `pytest tests/test_system_integrity.py -q`, `pytest tests/test_multi_tier.py -k test_talos_version` (5.16.1), a `ProfileManager` get/set/switch/list smoke test, `python talos.py --diagnostics` (no 11435), `python src/utils/verify_dependency_map.py --ci` (exit 0), `bash -n run_talos.sh`, and a strict UTF-8 scan (zero U+FFFD glyphs).

### 15.42 Pluggable LLM Provider Registry, Hardware-Aware Parameter Budgeting, and SOTA Discovery (v5.16.2)

**Overview:** v5.16.2 introduces a modular, adapter-based provider registry and a hardware-aware model advisor, both designed to decouple provider and hardware concerns from the core evaluation loops while remaining 100% air-gapped and local-first. The release follows the Open-Closed Principle: adding a new inference backend is now a pure data operation, and VRAM-based model sizing is a deterministic, unit-testable function of detected hardware.

- **ProviderRegistry** (`src/core/provider_registry.py`): `ProviderDescriptor` (dataclass) records `name`, `base_url`, `api_key_env`, `default_model`, `category` (`local_gpu` / `local_cpu` / `cloud_reasoning` / `cloud_fast` / `cloud_heavy`), `is_openai_compatible`, and a dynamically evaluated `is_active`. `ProviderRegistry` pre-registers local Ollama plus nine cloud providers (NVIDIA NIM, DeepSeek, Gemini, Groq, Cerebras, Mistral, Hugging Face, OpenRouter, Anthropic) and exposes `register`, `get`, `list_all`, and `list_active`. `is_active` is re-evaluated at query time (key presence for cloud, TCP port probe for local Ollama). `AIManager` consumes it through additive `list_active_providers()` / `get_provider_descriptor()` helpers with zero changes to `OPENAI_COMPATIBLE_REGISTRY`, SDK initialization loops, or circuit breakers.

- **HardwareModelAdvisor** (`src/core/hardware_advisor.py`): `get_hardware_profile()` returns `{has_cuda, device_name, total_vram_gb, system_ram_gb, is_laptop_cpu}` by combining Torch CUDA introspection, the nvidia-smi `detect_vram_gb()` fallback, psutil system RAM, and a battery heuristic. `calculate_vram_budget()` applies the piecewise 4-bit-quantization formula (`VRAM >= 11.0 GB -> 14B`, `5.5 <= VRAM < 11.0 -> 8B`, `VRAM < 5.5 / CPU -> 3B`); `get_recommendations()` returns `{screening_local, reasoning_local, reasoning_cloud, fast_cloud}`.

- **SOTA radar** (`scan_sota_models(timeout=1.5)`): a static verified radar plus live Ollama tags and an OpenRouter probe, filtered by the detected budget to surface newer releases (Qwen 3/4, Llama 4). Offline it degrades to the static verified list and never raises.

- **Integration surfaces**: CLI `--hardware-advisor` / `--recommend-models` in `talos.py:_handle_cli_flags()`; TUI Configuration & Profiles Option 8; Panel 1 of `src/utils/help_system.py`.

**Verification surface:** release gates include `python -m compileall src config tests talos.py` (0 errors), `pytest tests/test_provider_registry.py tests/test_hardware_advisor.py -q` (18 hermetic tests), `pytest tests/test_system_integrity.py -q`, `pytest tests/test_multi_tier.py -k test_talos_version` (5.16.2), `python talos.py --recommend-models` (RTX 4070 -> 14B budget), `python src/utils/verify_dependency_map.py --ci` (exit 0), `bash -n run_talos.sh`, and a strict UTF-8 scan (zero U+FFFD glyphs).

### 15.43 Two-Tier Hierarchical Swarm Architecture, Forensic Quality Auditing, and Profile Skill Compilation (v5.17.0)

**Overview:** v5.17.0 introduces the Two-Tier Hierarchical Swarm Architecture, formally decoupling thematic screening from forensic quality auditing. Tier-1 (`swarm_evaluators.py`) remains the three-agent peer-review screening swarm answering "is this study on-topic?"; the new Tier-2 (`quality_swarm.py`) is a Forensic Quality Swarm of four specialized skill auditors answering "is this study methodologically trustworthy?", each scoring a disjoint block of the Kitchenham 2007 rubric over a targeted text slice. A `SkillCompiler` compiles four domain-agnostic master templates into profile-bound auditor skills, and a `KitchenhamQualitySynthesizer` merges the six ternary scores into the canonical `S_qual`, computes the inter-auditor Fleiss `kappa_qual`, maps the 2D evidence quadrant, and synthesizes a unified forensic narrative -- all bounded by the Constitution III VRAM semaphore.

- **Four specialized forensic auditors** (`src/prisma/quality_swarm.py`): `TheoryAuditor` (Q1: formal problem formulation, hypotheses, scope), `OperationalAuditor` (Q2: environmental realism, physical disturbances, communication latency, operational rules/safety bounds), `BenchmarkAuditor` (Q3-Q4: 2-3 modern SOTA baselines under identical conditions, >= 5 random seeds, confidence intervals, p-values, ablations), and `OpenScienceAuditor` (Q5-Q6: public code repository, open benchmark simulator, explicit limitations and failure boundaries). Each emits a typed Pydantic-v2 result with ternary scores snapped onto {0.0, 0.5, 1.0} and a named forensic critique.

- **Domain-agnostic templates & profile-compiled skills**: `src/prisma/skills/templates/` holds four invariant templates using only `{{RESEARCH_DOMAIN}}` / `{{DOMAIN_CONSTRAINTS}}` placeholders. `SkillCompiler.compile_profile_skills(profile_name, force_recompile)` injects the profile's `research_topic`, `inclusion_criteria`, and `exclusion_criteria`, optionally refines each skill with the hardware-advised heavy model (`HardwareModelAdvisor.get_recommendations()`: `qwen2.5:14b` local / `deepseek-reasoner` / `gemini-2.5-flash` cloud, with a length-and-schema guard), and persists `_profiles/<name>/skills/*.md` behind a zero-cost fast path.

- **SmartSectionSlicer**: heading-regex extraction of Code/Data Availability, Methodology, Experiments, and Discussion/Limitations with per-auditor target maps, ~300-500 word caps, and a title-plus-abstract fallback -- minimizing token overhead while quadrupling evidential focus.

- **KitchenhamQualitySynthesizer**: dispatches the four auditors concurrently (`threading.Semaphore(2)` local / `max_workers=4` cloud), auto-compiles missing skills, merges scores into `KitchenhamRubric` (invariant `S_qual = (10/6) * sum(Q_i)`), computes `kappa_qual` over banded LOW/MID/HIGH ratings (reusing `swarm_evaluators.calculate_cohens_kappa`), maps ELITE_FOUNDATIONAL / IDEA_MINE / METHODOLOGICAL_EXEMPLAR / METHODOLOGICAL_NOISE, and returns a `SwarmQualityVerdict`.

- **Appraiser swarm mode & persistence**: `PrismaQualityAppraiser(appraisal_mode='single'|'swarm')`; `QualityAppraisalResult` gains `appraisal_mode`, `swarm_kappa`, `auditor_critiques`; the extended payload persists into the existing `quality_score` / `quality_rubric_json` / `evidence_quadrant` SQLite columns with zero schema changes.

- **Integration surfaces**: CLI `--appraise-quality [--min-score 7.0] [--swarm]` and `--compile-skills [--force] [--profile name]`; TUI Group 3 Option 15 mode prompt; Panel 1 and web manual Card 6 documentation; Rule 10 dossier 06.

**Verification surface:** `python -m compileall src config tests talos.py` (0 errors), `pytest tests/test_quality_swarm.py -q` (17 hermetic), `pytest tests/test_quality_appraisal.py -q` (17 -- backward compatible), `pytest tests/test_system_integrity.py -q`, `pytest tests/test_multi_tier.py -k test_talos_version` (5.17.0), `python talos.py --compile-skills` (UAV profile), `python talos.py --help`, `python src/utils/verify_dependency_map.py --ci` (exit 0), `bash -n run_talos.sh`, and a strict UTF-8 scan (0 U+FFFD).

### 15.44 Quality Appraisal UX Transparency, Idempotent Quadrant Rendering, and Force Re-Appraisal Mechanics (v5.17.1)

**Overview:** v5.17.1 eliminates the silent-exit anti-pattern in the PRISMA Quality Appraisal engine. `PrismaQualityAppraiser.appraise_candidates_batch()` previously returned an empty list whenever every candidate paper already carried a `quality_score`, leaving CLI and TUI users with no feedback. The method now accepts `force_reappraise: bool = False` and routes through two deterministic paths: the default uncached-only path and an explicit force path that re-audits the entire candidate set.

- **Force re-appraisal mechanics**: when `force_reappraise=True`, the batch queries `overall_score >= min_relevance` with no `quality_score IS NULL` predicate, prints a yellow notice ("Force re-appraising all {n} candidate papers with {mode} mode..."), and runs the same `ThreadPoolExecutor` (bounded by `VRAM_SEMAPHORE = threading.Semaphore(2)` locally, 8 workers Cloud Mesh), overwriting `quality_score`, `quality_rubric_json`, and `evidence_quadrant` through `DatabaseManager.update_paper_quality()` in SQLite WAL.

- **Idempotent quadrant-distribution fallback**: when `force_reappraise=False` and zero uncached candidates remain, the engine invokes `_render_existing_quadrant_distribution()`, which re-reads the persisted `evidence_quadrant` / `overall_score` / `quality_score` columns, renders an informational Rich panel ("All {n} candidate papers ... have already been appraised. Displaying existing 2D Evidence Quadrant distribution."), and re-projects the distribution via `render_quadrant_summary()` -- no LLM calls, no re-computation, deterministic output.

- **CLI & TUI surfaces**: `--appraise-quality [--min-score 7.0] [--swarm] [--force]`; TUI Group 3 Option 15 queries `SELECT COUNT(*) ... quality_score IS NULL`, and when the corpus is fully appraised prompts "All candidate papers are already appraised. Force re-appraise with selected mode?" (default `No`), falling back to the quadrant table when declined.

- **Dual-Surface Help**: Panel 1 (`help_system.py`) and web manual Card 6 (`help_manual.html`) document `--appraise-quality [--swarm] [--force]` with a dedicated force re-appraisal command.

**Verification surface:** `python -m compileall src config tests talos.py` (0 errors), `pytest tests/test_quality_appraisal.py -q` (17 -- backward compatible), `pytest tests/test_quality_swarm.py -q` (17), `pytest tests/test_system_integrity.py -q`, `pytest tests/test_multi_tier.py -k test_talos_version` (5.17.1), `python talos.py --help`, `python src/utils/verify_dependency_map.py --ci` (exit 0), `bash -n run_talos.sh`, and a strict UTF-8 scan (0 U+FFFD).

---

### 15.45 Ethical Open Access PDF Harvesting, Smart Section Extraction, and SQLite FTS5 Full-Text Indexing (v5.18.0)

**Overview:** v5.18.0 introduces an ethical, fully air-gapped full-text acquisition and retrieval stack. `src/ingestion/pdf_harvester/` resolves legal Open Access and preprint full-text URLs through a cascading thirteen-source resolver and downloads PDFs under six layers of fault tolerance. `PDFSectionExtractor` slices each PDF into four evidentiary windows, and `FullTextSearchEngine` indexes those bodies with SQLite FTS5 for sub-millisecond BM25-ranked search.

- **Cascading resolver** (`src/ingestion/pdf_harvester/resolvers.py`): `resolve_oa_url(paper_dict)` walks (1) direct preprints (arXiv, IEEE TechRxiv `10.36227`, HAL/Inria, NASA NTRS), (2) publisher OA APIs (Elsevier ScienceDirect OA `ELSEVIER_API_KEY`, PLOS, PubMed Central), and (3) meta-resolvers (Unpaywall, OpenAlex `best_oa_location`, Semantic Scholar `openAccessPdf`, CORE, Crossref OA, SSRN), returning the first viable `(pdf_url, resolver_source)`.

- **Download pipeline** (`harvester.py:AcademicPDFHarvester`): `%PDF-` magic-bytes validation, atomic temporary-file writes (`tmp_<id>.pdf` -> `<id>.pdf`), SHA-256 integrity hashing, 20 s timeout, 50 MB cap, and 1.5 s polite delay under `TALOS-Academic-Research-Bot/5.18.0`. `harvest_candidates(min_relevance=7.0)` persists `papers.local_pdf_path`, `papers.pdf_sha256`, and `papers.pdf_status`.

- **Section extraction** (`section_extractor.py:PDFSectionExtractor`): local `pypdf` (printable-byte fallback) caches `methodology.txt`, `experiments.txt`, `code_availability.txt`, and `limitations.txt` under `data/fulltext_cache/<id>/`; `SmartSectionSlicer` consumes these windows.

- **FTS5 engine** (`src/search/fulltext_search.py:FullTextSearchEngine`): `papers_fts(paper_id, title, fulltext_content)` virtual table, `index_paper` / `index_from_cache`, `search_fulltext(query, limit=20)` with `snippet(papers_fts, 2, '<b>', '</b>', '...', 15)` and BM25 ranking, rendered in a `box.ROUNDED` Rich table.

- **CLI / TUI** (`talos.py`): `--download-pdfs [--min-score 7.0]`, `--fts "<query>"`, `--open-pdf [paper_id]`; Group 2 (Universal Search Hub) and Group 5 (Database & Data) menu options; Rule 10 dossier 07.

**Verification surface:** `python -m compileall src config tests talos.py` (0 errors), `pytest tests/test_pdf_harvester.py -q` (8 hermetic), `pytest tests/test_fulltext_search.py -q` (4 hermetic), `pytest tests/test_quality_swarm.py tests/test_quality_appraisal.py -q` (34), `pytest tests/test_system_integrity.py -q`, `pytest tests/test_multi_tier.py -k test_talos_version` (5.18.0), `python talos.py --help` (`--download-pdfs` / `--fts` / `--open-pdf`), dossier 07 (0 U+FFFD), `python src/utils/verify_dependency_map.py --ci` (exit 0), `bash -n run_talos.sh`, and a strict UTF-8 scan (0 U+FFFD).

### 15.46 Autonomous Chaos Hardening, Fault-Tolerant Ingestion Guards, and Headless TTY Resilience (v5.18.1)

**Overview:** v5.18.1 is a hardening release focused on eliminating two classes of unhandled runtime failures that the Autonomous Red Tester (RL-Driven Chaos Engineering) surfaced under headless, non-interactive execution. The release adds headless CLI and TTY guards to `src/analysis/citation_analyzer.py`, wraps the optional `pymed` ingestion dependency in a fault-isolation import guard, and decommissions the legacy `src/ingestion/pdf_downloader.py` module.

- **Headless CLI & TTY hardening** (`src/analysis/citation_analyzer.py`): `main()` short-circuits before any interactive prompt -- `--help`/`-h` prints a usage description and exits `0`; `not sys.stdin.isatty()` or `TALOS_HEADLESS` prints a `[INFO] Running in headless mode...` notice and exits `0`; and `questionary.select(...).ask()` is wrapped in a try/except for `EOFError`/`KeyboardInterrupt`/`Exception` so a non-interactive console buffer exits cleanly instead of raising `NoConsoleScreenBufferError`.

- **Fault-tolerant ingestion import** (`src/ingestion/sources/pubmed_source.py`): the optional `pymed` dependency is imported behind a `try/except ImportError` guard (`PYMED_AVAILABLE`), degrading `PubMedSource` to a disabled no-op source with a `[WARNING]` line, so the 18-source `__init__` registry never crashes with an unhandled `ModuleNotFoundError`.

- **Dead code decommissioning** -- the legacy `src/ingestion/pdf_downloader.py` (Unpaywall-based downloader, superseded by the v5.18.0 Ethical Academic PDF Harvester) is removed, reducing the module inventory from 103 to 102 Python modules.

- **Autonomous Red Tester audit** (`src/ai/testing/red_tester.py`): a 5-episode Non-Stationary Multi-Armed Bandit run across 95 discovered CLI/API arms confirmed zero unhandled crashes post-guard, with a clean Q-table update and stable `citation_analyzer.py` resilience.

**Verification surface:** `python -m compileall src config tests talos.py` (0 errors), `pytest tests/test_system_integrity.py -q`, `pytest tests/test_multi_tier.py -k test_talos_version` (5.18.1), `python src/analysis/citation_analyzer.py --help` (exit 0, no `NoConsoleScreenBufferError`), `python src/ai/testing/red_tester.py 5` (0 unhandled crashes), `python src/utils/verify_dependency_map.py --ci` (exit 0), `bash -n run_talos.sh`, and a strict UTF-8 scan (0 U+FFFD).

### 15.47 Net2Net Input Tensor Surgery, Win32 Close-to-Tray Hook, and Desktop Workspace Provisioning (v5.18.2)

**Overview:** v5.18.2 consolidates three operator-facing resilience and provisioning capabilities plus a Net2Net checkpoint repair. It seals the 18-source / 25-dimension DDDQN tensor surgery on `models/dddqn_trained.pth`, installs a Win32 close-to-tray window-procedure hook that minimizes the daemon console instead of terminating it, provisions a 1-click Desktop Shortcut launcher, and adds an interactive autostart profile-target selector.

- **Net2Net DRL checkpoint repair** (`scripts/migrate_d3qn_checkpoint.py`): an idempotent Net2WiderNet "replicate-then-specialise" expansion of `lstm1.weight_ih_l0` from `[512, 21]` to `[512, 25]` (hour column invariant; 14 legacy source columns remapped by name; four new source columns seeded with the column-mean prior; streak and provider columns shifted), plus advantage-head widening `A.weight` to `[19, 32]` / `A.bias` to `[19]` (preserved rows copied bit-for-bit, new rows seeded with the top-5 L2-norm mean + 0.05 exploratory bias). Metadata is updated (`state_dim=25`, `action_dim=19`, 18 `source_names`) and the PyTorch forward pass `TalosDRLAgent(25, 19).act(np.zeros((1, 25)))` now executes with zero shape errors.

- **Win32 close-to-tray window hook** (`src/utils/tray_icon.py`): `enable_close_to_tray()` subclasses the console WNDPROC via `SetWindowLongPtrW(GWLP_WNDPROC)` and intercepts `WM_CLOSE` (0x0010) and `WM_SYSCOMMAND`/`SC_CLOSE` (0xF060), hiding the console with `ShowWindow(hwnd, SW_HIDE)` and emitting a single de-duplicated `[TRAY]` notice. `talos_service.py` installs the hook immediately at startup, independently of the optional pystray companion.

- **1-click Desktop Shortcut provisioner** (`src/utils/desktop_shortcut.py`): `create_desktop_shortcut()` resolves the Windows Desktop (OneDrive-aware) and materialises `TALOS Research Hub.lnk` targeting `run_talos.bat` via a zero-dependency PowerShell `WScript.Shell` COM dispatch; wired through `talos.py --create-shortcut` and a Configuration & Profiles menu entry.

- **Autostart profile-target selector** (`src/utils/daemon_autostart.py` + `src/ai/drl/talos_service.py`): `select_daemon_profile()` queries `ProfileManager().list_profiles()` and embeds `--profile <name>` in the generated `talos_daemon_boot.bat` and Startup `.lnk`; `talos_service.py` accepts `--profile <name>` and activates the SSOT via `ProfileManager().set_active_profile()` before loading config/env/model.

**Verification surface:** `python -m compileall src config tests talos.py` (0 errors), `pytest tests/test_system_integrity.py -q`, `pytest tests/test_multi_tier.py -k test_talos_version` (5.18.2), `scripts/migrate_d3qn_checkpoint.py` (strict `DuelingLSTM(25, 19)` load), `TalosDRLAgent(25, 19).act(...)` forward pass (exit 0), `python talos.py --create-shortcut` (exit 0), `python src/utils/verify_dependency_map.py --ci` (exit 0), `bash -n run_talos.sh`, and a strict UTF-8 scan (0 U+FFFD).

### 15.48 Dual-Checkpoint Net2Net Input Surgery, Dynamic Daemon Profile Provisioning, and Zero-Mismatch Execution (v5.18.3)

**Overview:** v5.18.3 performs a genuine dual-checkpoint Net2Net input tensor surgery across BOTH canonical checkpoint locations (`models/dddqn_trained.pth` and `src/ai/models/dddqn_trained.pth`), permanently eliminating the PyTorch forward-pass shape mismatch `RuntimeError: Expected 23, got 25`, and formalises the interactive Questionary daemon-profile provisioning path with dynamic banner synchronisation to the active profile (`uav_mission_planning`).

- **Dual-checkpoint Net2Net input tensor surgery** (`scripts/migrate_d3qn_checkpoint.py`): the migration utility now iterates over both checkpoint paths in a single deterministic pass. For each checkpoint it backs up to `.pth.bak` (created once), inspects `lstm1.weight_ih_l0` (`[512, in_dim]`), and -- when `in_dim != 25` -- builds a `[512, 25]` tensor via name-based column remapping (hour column invariant; existing source columns copied bit-for-bit; newly introduced source columns seeded with the column-mean prior; streak and provider columns shifted). The advantage head `A.weight` is widened to `[19, 32]` / `A.bias` to `[19]` (surviving rows copied, new rows seeded with the top-5 L2-norm mean + 0.05 exploratory bias, Sleep re-indexed to 18), and metadata is updated (`state_dim=25`, `action_dim=19`, 18 `source_names`). The stale `src/ai/models/dddqn_trained.pth` (16 sources / 23 dims / 17 actions) is migrated 16 -> 18 sources / 23 -> 25 dims / 17 -> 19 actions, while the canonical `models/dddqn_trained.pth` is strict-loaded and skipped idempotently.

- **Dynamic daemon profile provisioning** (`src/utils/daemon_autostart.py` + `src/ai/drl/talos_service.py`): `select_daemon_profile()` is the canonical interactive Questionary target-profile selector (querying `ProfileManager().list_profiles()`, defaulting to the active profile `uav_mission_planning`), embedding `--profile <name>` into `talos_daemon_boot.bat` and the Startup `.lnk`. `talos_service.py` parses `--profile <name>` at the head of `main()`, invokes `ProfileManager().set_active_profile(name)` immediately, resolves `active_profile` from the SSOT, and prints a dynamic `Version: v5.18.3 | Profile: {active_profile} | Device: {device}` banner. Every search, evaluation, and database insertion operates exclusively inside `_profiles/{active_profile}/`.

- **Zero-mismatch execution**: `TalosDRLAgent(25, 19)` is constructed with the canonical 25-dim observation and 19-action space (both via dynamic default resolution from the 18-source config and via explicit construction), and `load()` + `act(np.zeros((1, 25)), eps=0.0)` execute with zero shape errors on BOTH checkpoints.

**Verification surface:** `python -m compileall src config tests talos.py scripts` (0 errors), `pytest tests/test_system_integrity.py -q`, `pytest tests/test_multi_tier.py -k test_talos_version` (5.18.3), dual-checkpoint `TalosDRLAgent(25, 19).act(np.zeros((1, 25)))` forward pass (exit 0), daemon `--profile uav_mission_planning` banner confirmation, `python src/utils/verify_dependency_map.py --ci` (exit 0), `bash -n run_talos.sh`, and a strict UTF-8 scan (0 U+FFFD).

### 15.49 Overarching Ingestion Gateway, Universal Publisher Mirroring, and Autostart Profile Target Provisioning (v5.18.4)

**Overview:** v5.18.4 introduces a top-level self-healing ingestion gateway (`src/ingestion/resilient_gateway.py`) that wraps all 18 academic source adapters as a single resilient layer, eliminating the futile 5s/10s sleep-retry loops that previously preceded a terminal 401/403/quota failure. The gateway classifies authentication and quota errors from either a raised exception or the source agent's captured stdout, then transparently mirrors failed publishers (IEEE, Elsevier, Springer) through OpenAlex via `primary_location.source.publisher_lineage` filtering, normalizing recovered records to the canonical paper schema with the original source key preserved. The release also promotes the daemon profile selector to the first mandatory prompt of the autostart provisioning flow.

- **ResilientIngestionGateway** (`src/ingestion/resilient_gateway.py`): `harvest_source(source_instance, query, criteria, date_limit, source_key, days_to_search, mailto)` invokes `fetch_new_papers()` under `redirect_stdout`, then runs `_detect_auth_error()` over a marker set (`401`, `403`, `unauthorized`, `forbidden`, `developer inactive`, `quota exceeded`, `quota`, `rate limit`). On a hit it fast-fails with zero additional retries and consults the canonical `PUBLISHER_FALLBACK_MAP`.

- **Universal publisher-mirroring fallback matrix**: `ieee -> "Institute of Electrical and Electronics Engineers"`, `elsevier -> "Elsevier"`, `springer -> "Springer Nature"`. `_mirror_via_openalex()` GETs `https://api.openalex.org/works` with `search=<query>` and `filter=primary_location.source.publisher_lineage:"<publisher>"`, reconstructs abstracts from the inverted index, and `_normalize_openalex_work()` emits the canonical schema with `source=<source_key>`. Per-call `last_recovered` / `last_error` / `last_status` state keeps the COMPLETED / FAILED / recovered telemetry intact.

- **Orchestrator integration**: `daily_search.py` and `historic_search.py` route `_harvest_single_source()` through the gateway, so all 18 sources inherit self-healing without any per-source patching.

- **Mandatory autostart profile selection** (`src/utils/daemon_autostart.py`): `main()` makes the Questionary profile list the first prompt (canonical `TALOS_QUESTIONARY_STYLE`), cancels cleanly on Ctrl+C, persists `daemon_profile` / `daemon_autostart` into `_profiles/<profile>/config.json`, and embeds `--profile <target>` in `talos_daemon_boot.bat` and the Startup shortcut.

**Verification surface:** `python -m compileall src config tests talos.py scripts` (0 errors), `pytest tests/test_system_integrity.py -q`, `pytest tests/test_multi_tier.py -k test_talos_version` (5.18.4), `pytest tests/test_resilient_gateway.py -q` (11 hermetic -- simulated 403 / "Developer Inactive" triggers the OpenAlex mirror cleanly), `python src/utils/verify_dependency_map.py --ci` (exit 0), `bash -n run_talos.sh`, and a strict UTF-8 scan (0 U+FFFD).

### 15.50 Hierarchical Multi-Tier Evaluation Architecture, Cognitive Router Quota Latching, and Clean Console Lifecycles (v5.18.5)

**Overview:** v5.18.5 centralizes the paper-evaluation workflow into a single deterministic escalation engine and hardens the LLM router against quota exhaustion. A new `HierarchicalEvaluationEngine` (`src/core/hierarchical_evaluator.py`) replaces the fragmented multi-tier if/else screening spread across `daily_search.py` and the daemon foraging loop, while `AIManager` learns to latch quota-exhausted cloud providers offline so the very next request routes directly to a credentialed provider (DeepSeek) with zero wasted network attempts. The release also standardizes the daemon console title and hardens two ingestion adapters against transient upstream failure modes.

- **HierarchicalEvaluationEngine** (`src/core/hierarchical_evaluator.py`): `evaluate_paper(paper, escalation_threshold=6.0)` runs the Fast Screening Sieve (`AIManager.evaluate_paper_json(model_type='flash')`) to produce $S_{rel}$, then branches at the Escalation Gate: $S_{rel} < 6.0$ returns a `tier='fast_local'` rejection, while $S_{rel} >= 6.0$ dispatches to the Heavy Reasoning tier (`model_type='pro'`, local `qwen2.5:14b` or cloud `deepseek-reasoner`) and computes a Kitchenham-inspired $S_{qual}$. `evaluate_batch()` uses a `ThreadPoolExecutor` bounded by `threading.Semaphore(2)` to protect shared GPU VRAM.

- **Cognitive LLM Router Quota Latching** (`src/core/ai_manager.py`): `exhausted_providers` set + `_latch_provider_exhausted()` latch any provider returning HTTP 402 (`RESOURCE_EXHAUSTED` / prepayment credits depleted) or 401 (`Unauthorized`) offline for the session, emitting a single notice. `_execute_cloud_chain` and `_execute_legacy_request` skip latched providers with zero network attempts.

- **Clean console lifecycle** (`src/ai/drl/talos_service.py`): `SetConsoleTitleW("TALOS v5.18.5 | Autonomous Research Service [{active_profile}]")` -- a pure-ASCII, emoji-free dynamic title.

- **Clean ingestion lifecycle**: `ScienceGovSource` isolates DNS failures (delegating to federal OSTI coverage, disabled by default via `scigov_enabled`); `DBLPSource._sanitize_dblp_query()` strips Boolean operators and `search_papers()`/`fetch_new_papers()` guard `response.json()` against `JSONDecodeError`.

**Verification surface:** `python -m compileall src config tests talos.py scripts` (0 errors), `pytest tests/test_system_integrity.py -q`, `pytest tests/test_multi_tier.py -k test_talos_version` (5.18.5), `pytest tests/test_hierarchical_evaluator.py tests/test_quota_latching.py tests/test_dblp_sanitizer.py tests/test_scigov_resilience.py -q` (24 hermetic), `python src/utils/verify_dependency_map.py --ci` (exit 0), `bash -n run_talos.sh`, and a strict UTF-8 scan (0 U+FFFD).

### 15.51 Two-Stage Rigor Decoupling Engine, Cognitive Router Quota Latching, and 4-Role SOTA Model Matching (v5.19.0)

**Overview:** v5.19.0 decouples cheap semantic relevance screening from expensive methodological rigor appraisal into a deterministic Two-Stage pipeline, upgrades paper evaluation with a Stage-2 Dual-Audit, and introduces a Cognitive SOTA 4-Role Model Matcher for hardware-aware model selection across local and cloud tiers.

- **Two-Stage Rigor Decoupling Engine** (`src/core/hierarchical_evaluator.py`): `HierarchicalEvaluationEngine.evaluate_paper()` runs Stage 1 (Fast Relevance Sieve via `evaluate_paper_json(model_type='flash')`) to produce $S_{rel}^{prelim}$, fast-rejecting papers below the `escalation_threshold=6.0` with `evidence_quadrant='METHODOLOGICAL_NOISE'` and zero heavy compute. Stage 2 executes a Dual-Audit on the heavy tier (`model_type='pro'` -> local `qwen2.5:14b` or cloud `deepseek-reasoner`): (1) Faceted Deep Relevance Calibration yields $S_{rel}^{calibrated}$ (verifying HMADRL / Dec-POMDP / QMIX swarm algorithms and ST-GNN / ST-GAT architectures); (2) Kitchenham 2007 Quality Appraisal yields $S_{qual}$ via `PrismaQualityAppraiser`. The 2D Evidence Quadrant (ELITE_FOUNDATIONAL / IDEA_MINE / METHODOLOGICAL_EXEMPLAR / METHODOLOGICAL_NOISE) is computed from the decoupled pair, and the deep verdict returns `overall_score=S_rel_calibrated`, `quality_score=S_qual`, `quality_rubric_json`, `evidence_quadrant`, and `critique`.

- **Cognitive Router Quota Latching** (`src/core/ai_manager.py`): the `exhausted_providers` set + `_latch_provider_exhausted()` latch any provider returning HTTP 402/401 offline for the session, emitting a single notice and routing subsequent calls directly to active providers (e.g. DeepSeek) with zero network attempts.

- **4-Role SOTA Model Matcher** (`src/core/hardware_advisor.py`): `get_role_based_matrix()` / `render_role_matrix()` / `apply_recommended_models()` categorize four scientific workloads (fast_screening / deep_reasoning_rigor / code_audit_slicing / vector_embeddings) across local GPU/CPU and Cloud Mesh, and persist the recommended stack into the active profile config.json via a 1-click `--apply-models` flag.

- **Clean console lifecycle** (`src/ai/drl/talos_service.py`): `SetConsoleTitleW("TALOS v5.19.0 | Autonomous Research Service [{active_profile}]")` -- a pure-ASCII, emoji-free dynamic title.

- **Clean ingestion + script unification**: `daily_search.py` and `historic_search.py` route evaluation through the engine and persist `quality_score` / `quality_rubric_json` / `evidence_quadrant` in SQLite WAL; `historic_search.py` is fully unified; Science.gov DNS isolation and DBLP query sanitization are retained.

**Verification surface:** `python -m compileall src config tests talos.py scripts` (0 errors), `pytest tests/test_system_integrity.py -q`, `pytest tests/test_multi_tier.py -k test_talos_version` (5.19.0), `pytest tests/test_hierarchical_evaluator.py tests/test_hardware_advisor.py tests/test_quality_appraisal.py tests/test_quota_latching.py tests/test_dblp_sanitizer.py tests/test_scigov_resilience.py -q` (53 hermetic), `python talos.py --recommend-models` (exit 0), `python src/utils/verify_dependency_map.py --ci` (exit 0), `bash -n run_talos.sh`, and a strict UTF-8 scan (0 U+FFFD).

---

### 15.52 Cognitive Meta-Router, Dynamic SOTA Model Scavenging, Enterprise Operational Runbooks, and Microservice Decoupling (v5.20.0)

**Overview:** v5.20.0 introduces a decoupled, extraction-ready Cognitive Meta-Router with four named routing strategies, expands the provider registry to sixteen inference engines, adds a dynamic SOTA model discovery client with a cached benchmark store, restructures the console help system into a four-section enterprise manual, and publishes a six-zone functional architecture map.

- **Decoupled Cognitive Meta-Router** (`src/core/cognitive_router.py`): `CognitiveMetaRouter.dispatch()` routes tasks under `LOWEST_LATENCY` (EMA TTFT over Groq / Cerebras / SambaNova / Ollama), `REASONING_RIGOR` (DeepSeek / Anthropic / SambaNova 405B), `LOWEST_COST` (cheapest provider meeting Q_min >= 0.70), and `LOCAL_AIRGAPPED` (Ollama :11434, zero egress, `Semaphore(2)`). Standalone Pydantic v2 DTOs (`RouterTaskRequest`, `RouterTaskResponse`, `RoutingStrategy`), zero SQLite WAL / PRISMA / CLI imports, and session-scoped 401/402/429 quota latching with same-tier failover.

- **16-provider registry** (`src/core/provider_registry.py`): SambaNova, Together, Fireworks, DeepInfra, Cohere, and Perplexity added; `LLMProvider` enum + `get_available_providers()` (graceful missing-key handling).

- **Dynamic SOTA discovery** (`src/core/model_benchmark_client.py`): `ModelBenchmarkClient` with `data/cache/llm_benchmarks.json` and `get_top_models_by_role()` for fast_screening / rigorous_audit / code_audit / vector_embeddings, reconciled against the RTX 4070 (12 GB) via `hardware_advisor`; CLI `--discover-llms`.

- **Enterprise Console Help** (`src/utils/help_system.py`): four sections -- A (SOP Runbooks), B (Scientific Command Matrix), C (Operational Diagnostics & Self-Healing), D (Environment & Configuration Specs, ports :8000/:8001/:8002/:11434).

- **Functional Architecture Map** (`docs/ARCHITECTURE_MAP.md` + `ARCHITECTURE_MAP_GR.md`): ISO/IEC 25010 six-zone decomposition with Zone 5 flagged extraction-ready for SYNAPSE (:8000) serving TALOS and MEMEX.

- **Academic Dossier 08** (`docs/internal/academic/08_COGNITIVE_META_ROUTING_DYNAMIC_DISCOVERY.md`): Rule 10 codified in `.clinerules`.

**Verification surface:** `python -m compileall src config tests talos.py` (0 errors), `pytest tests/test_system_integrity.py -q`, `pytest tests/test_multi_tier.py -k test_talos_version` (5.20.0), `pytest tests/test_provider_registry.py tests/test_cognitive_router.py tests/test_model_benchmark_client.py -q` (31 hermetic), `python talos.py --discover-llms` (exit 0), `python talos.py --help` (exit 0), `python src/utils/verify_dependency_map.py --ci` (exit 0), `bash -n run_talos.sh`, and a strict UTF-8 scan (0 U+FFFD).

### 15.53 In-Tree Cognitive Microservice Chassis, Autonomous Model Scavenging, and Dual Market Intelligence Reporting (v5.21.0)

**Overview:** v5.21.0 restructures the decoupled cognitive layer into an in-tree extraction-ready microservice chassis (`src/services/cognitive_mesh/`), adds an autonomous model scavenger foraging Hugging Face, OpenRouter, and Ollama, introduces a dual MD/HTML market-intelligence reporter, mounts a Cognitive Mesh FastAPI mini-server under `/api/v1/cognitive`, and archives Academic Dossier 09.

- **In-Tree Extraction-Ready Microservice** (`src/services/cognitive_mesh/`): eight submodules -- `dto.py` (standalone Pydantic v2 DTOs: `RoutingStrategy`, `RouterTaskRequest`, `RouterTaskResponse`, `ModelSpec`, `ProviderSpec`, `BenchmarkScorecard`, `ScavengedModel`, `MarketIntelligenceReport`), `registry.py` (16-provider registry), `router.py` (`CognitiveMetaRouter` with `Semaphore(2)` + quota latching), `benchmarks.py` (`ModelBenchmarkClient`), `scavenger.py` (`ModelScavengerAgent`), `reporter.py` (`IntelligenceReporter`), `server.py` (FastAPI mini-app, port 8003), and `client.py` (`CognitiveMeshClient`). Zero SQLite WAL / PRISMA / CLI imports.

- **Backward-compatible shims** (`src/core/cognitive_router.py`, `provider_registry.py`, `model_benchmark_client.py`): re-export the new namespace, preserving 100 percent of pre-v5.21.0 import paths.

- **Autonomous Model Scavenger Agent** (`scavenger.py`): forages Hugging Face (trending text-generation, permissive Apache-2.0/MIT/Llama licenses), OpenRouter (new-release delta within window + per-token pricing), and Ollama (quantized GGUF <= 14B); hardware-aware VRAM classifier (LOCAL_OPTIMAL <= 12 GB / CLOUD_COST_EFFECTIVE > 14B-70B / FRONTIER_REASONING > 70B) + 4-role assignment (Fast Screening / Kitchenham Rigor / Code Audit / Vector Embeddings); offline fallback to `data/cache/llm_benchmarks.json`.

- **Dual Intelligence Reporter** (`reporter.py`): `llm_market_intelligence_YYYYMMDD.md` + a 100 percent standalone zero-dependency Dark Theme HTML dashboard (embedded CSS/JS, filter buttons All Models / Local RTX 4070 <12GB / Cloud High-Throughput / Deep Reasoning, green/amber/blue VRAM badges).

- **Cognitive Mesh FastAPI mini-server** (`server.py`): `POST /dispatch`, `GET /providers`, `GET /benchmarks`, `POST /scavenge`, `GET /health`; mounted in `main_api.py` under `/api/v1/cognitive`; standalone `uvicorn src.services.cognitive_mesh.server:app --port 8003`.

- **CLI & TUI** -- `--scavenge-models [--days N] [--report-only]`; TUI Group 1 Option 10; Help Runbook A4.

- **Academic Dossier 09** (`docs/internal/academic/09_AUTONOMOUS_MODEL_SCAVENGING_MICROSERVICE_ARCHITECTURE.md`): seven mandatory sections (ISO/IEC 25010, Pareto discovery, microservice spec, dual reporting, PRISMA-ScR, SYNAPSE/MEMEX/OPTICA roadmap, IP notice).

**Verification surface:** `python -m compileall src config tests talos.py` (0 errors), `pytest tests/test_system_integrity.py -q`, `pytest tests/test_multi_tier.py -k test_talos_version` (5.21.0), `pytest tests/test_model_scavenger.py tests/test_intelligence_reporter.py tests/test_provider_registry.py tests/test_cognitive_router.py tests/test_model_benchmark_client.py -q` (43 hermetic), `python talos.py --scavenge-models --days 7 --report-only` (exit 0), `python talos.py --help` (Runbook A4), `python src/utils/verify_dependency_map.py --ci` (exit 0), `bash -n run_talos.sh`, and a strict UTF-8 scan (0 U+FFFD).

### 15.54 Decoupled Cognitive Mesh Hardening, Full-Catalog LLM Scavenger, Fuzzy Benchmarks & Auto-Pilot FinOps Configurator (v5.21.1)

**Overview:** v5.21.1 hardens the extraction-ready microservice with full-catalog scavenging (Hugging Face top-100 by downloads, OpenRouter 250+ without date truncation, canonical remote Ollama tags), fuzzy MMLU-Pro/HumanEval/TTFT benchmark cross-referencing, a hardened token-boundary role/VRAM classifier, an Executive Optimal Selection Matrix with FinOps cost estimation, a hybrid `LOCAL_FIRST_CLOUD_BACKUP` routing strategy, and an interactive Auto-Pilot FinOps configurator.

- **Hugging Face full-catalog harvester**: `sort=downloads&direction=-1&limit=100`; parses downloads / likes / author / params / license; `huggingface` always appended to `sources_queried`.

- **OpenRouter full-catalog ingestion**: `fetch_all` / `window_days <= 0` disables the release-date cutoff (250+ models); `window_days > 0` retains the delta.

- **Remote Ollama library catalogue**: 20 canonical remote tags (Qwen 2.5, Llama 3.1, DeepSeek-R1, Gemma 2/3, Mistral NeMo, Phi-4, CodeQwen); `>14B` drop removed.

- **Fuzzy benchmark cross-referencing** (`benchmarks.py`): `fuzzy_enrich_benchmarks()` (46-entry `FUZZY_BENCHMARK_PATTERNS` table) populates MMLU-Pro / HumanEval / TTFT across Claude, GPT, DeepSeek, Qwen, Llama, Mistral, Gemma.

- **Hardened heuristic classifier** (`scavenger.py`): unified `_classify_model()` decision tree (Vector Embeddings -> Code Audit -> Frontier Reasoning -> Fast Screening -> General Research) with token-boundary `_has_token()` (pro / mini / 7b false positives eliminated); frontier = sonnet/opus/r1/reasoner/pro/o1/o3/gpt-4/5/6/405b/nemotron-70b, price >= $3.00/1M, or >= 70B.

- **Executive Decision Matrix & FinOps** (`reporter.py`): `_select_champions()` (Local / Cloud / Frontier) + `_finops_cost()` per 1k papers; MD verdict tables + HTML champion cards + vanilla-JS search bar.

- **Hybrid routing** (`dto.py`, `router.py`): `RoutingStrategy.LOCAL_FIRST_CLOUD_BACKUP` (local-first, cloud failover via latching loop).

- **Auto-Pilot FinOps Configurator** (`ai_strategy_selector.py`, `talos.py`): `configure_ai_strategy()` + `apply_optimal_models()`; CLI `--configure-ai-strategy`, `--apply-optimal-models [--strategy ...]`, `--scavenge-models --all`; TUI Option 10.

**Verification surface:** `python -m compileall src config tests talos.py` (0 errors), `pytest tests/test_system_integrity.py -q`, `pytest tests/test_multi_tier.py -k test_talos_version` (5.21.1), `pytest tests/test_model_scavenger.py tests/test_intelligence_reporter.py tests/test_model_benchmark_client.py tests/test_cognitive_router.py -q` (45 hermetic), `python src/utils/verify_dependency_map.py --ci` (exit 0), `bash -n run_talos.sh`, strict UTF-8 scan (0 U+FFFD), decoupling grep (0 forbidden imports).

### 15.55 Full-Spectrum Rich Terminal Dashboard 2.0 & Scientific Console Architecture (v5.22.0)

**Overview:** v5.22.0 introduces the Scientific Terminal Dashboard (HMI), a full exploitation of the `rich` ecosystem that transforms the CLI into an interactive, multi-panel ISO/IEC 25010-conformant console. A modular renderer subsystem (`src/utils/console_dashboard/`) isolates all Rich rendering from `talos.py`, while a persistent telemetry HUD, a two-column / four-panel responsive grid, scientific tree viewers, a multi-metric progress monitor, terminal previewers, and a type-safe slash-command palette compose the new operator surface.

- **Modular console subsystem** (`src/utils/console_dashboard/`): `HudRenderer` (`hud_renderer.py`), `DashboardLayoutBuilder` (`layout_builder.py`), `ScientificTreeViewer` (`tree_views.py`), `MultiMetricProgress` / `create_scientific_progress` (`progress_monitors.py`), `TerminalPreviewer` (`terminal_previewer.py`).

- **Persistent telemetry HUD**: active profile, total / elite foundational / Kitchenham-appraised corpus, NVIDIA GPU name + VRAM (`nvidia-smi`), Ollama `:11434` probe, `TALOS_NETWORK_STRATEGY/TALOS_HARDWARE_STRATEGY`, scavenged-model count. Every probe is air-gapped and best-effort.

- **Two-column / four-panel responsive grid** (`rich.layout.Layout`): header HUD + Panels 1-4 (Cognitive Mesh & FinOps / Discovery & Harvesting / PRISMA Swarm & Full-Text / System-Export-Diagnostics) + footer command-palette legend; zero vertical scrolling at 105x32.

- **Scientific trees**: architecture (6 ISO/IEC 25010 zones), ATHENA research taxonomy (ST-GAT -> Dec-POMDP -> HMADRL -> CJCSI 3160.01A), and mesh health (18 APIs + 16 providers with live badges).

- **Command palette**: `rich.prompt.Prompt.ask()` + `_dispatch_slash_command()` (`/scavenge`, `/audit`, `/fts`, `/config`, `/tree`, `/view`, `/help`, `/quit`); CLI flags `--show-dashboard`, `--show-tree`, `--preview-report`.

**Verification surface:** `python -m compileall src config tests talos.py` (0 errors), `pytest tests/test_system_integrity.py -q`, `pytest tests/test_multi_tier.py -k test_talos_version` (5.22.0), `pytest tests/test_console_dashboard.py -q` (16 hermetic), `python talos.py --show-dashboard` / `--show-tree arch|phd|mesh` / `--preview-report` (exit 0), `python src/utils/verify_dependency_map.py --ci` (0/0/0), `bash -n run_talos.sh`, strict UTF-8 scan (0 U+FFFD).

---

> **Project TALOS** -- From Aggregator to Autonomous Research Architect.
> Built in Kalamata, Greece.
> (C) 2026 Christos Smarlamakis. All rights reserved.
