# TALOS/ALEXANDRIA/ATHENA -- System Capabilities Master Reference v5.9.0

> **Document ID:** TALOS-SYS-CAP-001
> **Classification:** Public Reference
> **Scope:** TALOS Research Intelligence Platform (Headless FastAPI Backend + React Frontend)
> **Last Updated:** 29 July 2026

---

## Section 1: System Vision & Core Architecture

### 1.1 Foundational Principle

TALOS is an autonomous Research Intelligence Platform that ingests, evaluates, synthesizes, and visualizes scientific knowledge across 14 academic sources. It replaces manual systematic literature review workflows with an AI-driven, DRL-orchestrated pipeline that maintains a human-in-the-loop at every critical decision boundary.

### 1.2 Architectural Pillars

The system operates as a three-layer architecture:

| Layer | Component | Role |
|-------|-----------|------|
| **Frontend** | React 18 with Tailwind CSS and Shadcn UI | User-facing dashboard leveraging the REST API |
| **Backend** | `src/api/main_api.py` (14 endpoints) | Headless FastAPI facade exposing all core capabilities |
| **Persistence** | `src/core/database_manager.py` | SQLite + multi-model vector embeddings (Ollama + Gemini) |

### 1.3 Data Flow

```
User (React UI) --> FastAPI (:8000) --> src/core/*.py --> src/ingestion/*.py --> External APIs
                                                   ^
                                                   | --> src/ai/*.py --> DRL Agent + GWO + PYTHIA
                                                                  |
                                                   data/talos_research.db (SQLite + Embeddings)
                                                                  |
                                                   config.json + .env (Configuration + Secrets)
```

### 1.4 Operational Modes

- **Production:** Headless FastAPI listener on port 8000, React frontend consuming the API
- **Development:** `uvicorn src.api.main_api:app --reload --port 8000`
- **Background Services:** Scraping pipeline, GWO optimizer, DRL training -- all via FastAPI BackgroundTasks
- **CLI:** `talos.py` retains full terminal-mode access for maintenance and diagnostics

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

### 2.2 Source Agent Inventory

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
- **Zotero Connector** (`src/ingestion/zotero_connector.py`): Bi-directional sync with Zotero cloud library
- **Metadata Enricher** (`src/ingestion/metadata_enricher.py`): DOI resolution and metadata augmentation
- **Data Enricher** (`src/ingestion/data_enricher.py`): Unpaywall API integration for OA status and PDF links

---

## Section 3: Deep Reinforcement Learning & Optimization (DDDQN + GWO)

### 3.1 DRL Agent Architecture

The TALOS DRL Agent (`src/ai/drl/`) employs a **Double Dueling Deep Q-Network with 3-layer LSTM** trained on 3,849 real paper scores.

| Component | File | Purpose |
|-----------|------|---------|
| RL Environment | `src/ai/drl/talos_env.py` | Gymnasium-compliant N-source observation space with provider-aware state (1+N+2+4 dimensions) |
| Network Architectures | `src/ai/drl/drl_networks.py` | DuelingLSTM, DuelingMLP, and supporting value/advantage heads |
| Training Loop | `src/ai/drl/drl_trainer.py` | Epsilon-greedy training with prioritized experience replay |
| Live Orchestrator | `src/ai/drl/live_agent_orchestrator.py` | Main loop with cooldown mechanism, provider tracking, and reward calculation |
| Autonomous Service | `src/ai/drl/talos_service.py` | 24/7 background agent with Telegram/Discord/Email notifications |
| Live Agent Entry | `src/ai/drl/talos_live_agent.py` | CLI entry point for live API-fetching agent |
| Source Discovery | `src/ai/drl/live_agent_sources.py` | Dynamic source class import from config.json |

### 3.2 Action Space

- Actions 0..N-1: Query the corresponding academic source
- Action N: Sleep (cooldown/reset)
- Environment dynamically adjusts N based on configured sources

### 3.3 Reward Function

| Score Range | Reward |
|-------------|--------|
| score >= 8.0 | +20 (elite paper) |
| score >= 6.0 | +5 (good paper) |
| score < 6.0  | -10 (low-value paper) |

### 3.4 Grey Wolf Optimizer (GWO)

The GWO (`src/ai/optimizers/gwo_rl_optimizer.py`) tunes three hyperparameters:

- **Learning Rate** (log scale): Controls DQN update magnitude
- **Gamma** (discount factor): Balances immediate vs. future rewards
- **Epsilon Decay**: Governs exploration-exploitation tradeoff

Each wolf trains a fresh DRL agent for \(N\) episodes per iteration. The pack converges toward the alpha wolf's position in 3D parameter space. A companion Dash dashboard (`gwo_live_dashboard.py`) renders the 3D swarm hunt in real-time at `localhost:8050`.

### 3.5 Model Artifacts

- `models/dddqn_trained.pth`: Trained DDDQN model weights (PyTorch)
- `models/dddqn_partial.pth`: Partial training checkpoint
- `models/talos_drl.pth`: Bundled agent state (network + optimizer)
- `models/gwo_best_params.json`: Converged hyperparameters
- `models/gwo_history.json`: Per-iteration wolf pack positions
- `models/gwo_progress.json`: Real-time progress file

---

## Section 4: Advanced Semantic & Graph Intelligence (ST-GAT)

### 4.1 Multi-Provider Hybrid Embeddings

TALOS implements a **dual-provider embedding architecture** stored in the `embeddings` table:

| Provider | Model | Dimensions | Cost | Latency |
|----------|-------|------------|------|---------|
| Ollama (local) | `nomic-embed-text` | 768 | Free | ~50ms |
| Gemini (cloud) | `gemini-embedding-001` | 768 | Paid | ~500ms |

### 4.2 Semantic Search Pipeline

1. **Embed the query** via `AIManager.generate_embeddings()` with fallback chain (Ollama -> Gemini)
2. **Compute cosine similarity** against all stored vectors filtered by model
3. **Rank and return** the top-k papers with full metadata
4. **Model filtering** ensures vectors from different providers are never compared

### 4.3 Architecture Graph Intelligence

The Architecture Dependency Graph (`templates/architecture_graph.html`) provides:

- Interactive D3.js force-directed visualization of the codebase
- Node coloring by module role (core, ingestion, analysis, AI, API, utils)
- Edge connections representing import dependencies
- Tooltip exposure of function signatures and module descriptions

### 4.4 Knowledge Path Generation

`src/analysis/knowledge_path_generator.py` constructs directed knowledge paths from seed papers through citation networks, identifying the evolution of ideas across publication years.

---

## Section 5: Multi-Agent & Autonomous Swarms (PYTHIA, Swarm Commander, HMADRL)

### 5.1 PYTHIA -- The AI Reasoning Engine

PYTHIA (`src/ai/llm/`) provides multi-model AI reasoning with circuit breaker resilience:

| Provider | Models | Role |
|----------|--------|------|
| Gemini | `gemini-2.5-pro`, `gemini-2.5-flash` | Primary deep analysis + pre-screening |
| DeepSeek | `deepseek-chat`, `deepseek-reasoner` | First fallback |
| HuggingFace | `Mixtral-8x7B`, `Llama-3.1-8B` | Free cloud fallback |
| Ollama (local) | `gemma3:12b` | Offline fallback, zero-cost |

### 5.2 Circuit Breaker Pattern

Each provider tracks consecutive failures. After **3 consecutive failures**, the circuit opens and that provider is skipped for subsequent requests. The circuit resets on the next successful request from any provider.

### 5.3 Query Translator (Research Architect)

`src/ai/llm/query_translator.py` transforms natural-language research goals into optimized boolean queries for all 14 sources simultaneously. It uses a dedicated system prompt override that instructs the LLM to act as a "Research Architect" rather than the default "PhD Advisor" role.

### 5.4 Research Pivot

`src/ai/llm/research_pivot.py` provides a guided wizard for changing research direction: reconfigures query translator parameters, re-evaluates the database against new criteria, and optionally retrains the DRL agent.

### 5.5 Autonomous Swarm Commander (Roadmap)

Planned HMADRL (Heterogeneous Multi-Agent DRL) architecture for coordinating multiple specialized agents (scraper, evaluator, summarizer, reviewer) in parallel research workflows.

---

## Section 6: Automated Literature Review & XAI (Quad-Layer Scoring, NATO CDE Procedural Hooks)

### 6.1 Quad-Layer Evaluation Framework

Every paper ingested by TALOS is scored across four orthogonal dimensions:

| Layer | Weight | Focus | Example Criteria |
|-------|--------|-------|------------------|
| **Strategic** | 30% | Theoretical framework, high-level decision making | Novelty, field impact, paradigm shift |
| **Operational** | 30% | Resource allocation, coordination mechanisms | Task allocation, auctions, consensus |
| **Tactical** | 30% | Algorithmic implementation, neural policies | DRL architectures, training methodology |
| **Playground** | 10% | Simulation environments, datasets, benchmarks | Gymnasium envs, real-world datasets |

Overall Score Formula:

\[
\text{Overall} = 0.30 \times S + 0.30 \times O + 0.30 \times T + 0.10 \times P
\]

### 6.2 Two-Stage AI Evaluation

1. **Pre-Screening (Flash model):** Rapid triage of all new papers using the `pre_screening_prompt`
2. **Deep Analysis (Pro model):** Thorough evaluation of papers passing pre-screening using the `phd_focus_system_prompt`

### 6.3 Enrichment State Machine

| Status | Value | Meaning |
|--------|-------|---------|
| Pending | 0 | Paper has not yet been enriched |
| Enriched | 1 | Metadata + OA PDF successfully resolved |
| Failed | 2 | Enrichment attempted but failed |

### 6.4 XAI Reasoning Outputs

For each evaluated paper, the AI generates:

- `evaluation_reasoning`: Narrative explanation of the scores
- `evaluation_contribution`: The paper's contribution to the field
- `evaluation_utilization`: How the paper's findings can be applied
- `suggested_tags`: Auto-generated keyword tags
- `suggested_folder`: Recommended organizational folder
- `suggested_discord_channel`: Relevant notification channel

### 6.5 NATO CDE Procedural Hooks

The Architecture Intelligence Report (`src/analysis/architecture_intelligence_report.py`) generates dual-language (EN + GR) reports compatible with NATO CDE (Concept Development & Experimentation) procedural documentation standards.

---

## Section 7: Edge-Cloud & Deployment Ecosystem

### 7.1 Deployment Options

| Mode | Components | Command |
|------|-----------|---------|
| Development | FastAPI with reload | `uvicorn src.api.main_api:app --reload` |
| Production | FastAPI on port 8000 | `uvicorn src.api.main_api:app --host 0.0.0.0 --port 8000` |
| Docker | Containerized with GPU passthrough | `docker-compose up --build` |
| Kubernetes | Cluster with Ollama sidecar | `kubectl apply -f k8s/` |

### 7.2 Hardware Requirements

| Tier | GPU | VRAM | Capability |
|------|-----|------|------------|
| Minimum | CPU only | N/A | Ingestion + evaluation (cloud LLMs only) |
| Recommended | RTX 3060+ | 12 GB | Local nomic-embed-text + light chat models |
| Optimal | RTX 4070+ | 16 GB | Full local DRL training + embedding generation |

### 7.3 Environment Configuration

- **`.env`**: API keys for all providers (Gemini, DeepSeek, HuggingFace, Discord, Telegram, Zotero, Unpaywall, ORCID)
- **`config.json`**: Query strings, system prompts, source configuration
- **`config.template.json`**: Reference template with placeholder values
- **Profiles**: `_profiles/<name>/` directories with isolated config.json + talos_research.db per research topic

### 7.4 Docker Support

- `Dockerfile`: Multi-stage Python 3.11 build with CUDA 12.1 support
- `docker-compose.yml`: FastAPI + Ollama services with shared volumes for models and data

---

## Section 8: Dashboards & User Interfaces

### 8.1 React 18 Frontend (Primary)

The production user interface is a **React 18 Single Page Application** built with:

- **Tailwind CSS**: Utility-first CSS framework for responsive design
- **Shadcn UI**: Headless component primitives for accessible, composable UI
- **Recharts**: Composable charting library for data visualization

The React frontend consumes the FastAPI REST API at port 8000 and provides:

- Interactive paper library with semantic search, filtering, and pagination
- DRL agent dashboard with live status and training controls
- GWO optimization history visualizations (LineChart, 3D Scatter)
- Author publication statistics (BarChart)
- Architecture dependency graph embedding
- Background task monitoring and management

### 8.2 Flask Dashboard (Legacy/Embedded)

`templates/dashboard.html` serves a Tabulator.js-based interactive table at port 5000 for direct database browsing. This remains available as a lightweight alternative when the React frontend is not deployed.

### 8.3 CLI Interface

`talos.py` retains a full-featured text-based interface via `questionary` prompts:

- Search & Discovery operations
- Paper evaluation
- Analysis & insights generation
- Database maintenance (statistics, enrichment, embedding generation)
- Diagnostics (code integrity check, dependency map verification)
- DRL training and GWO optimization
- Profile management

### 8.4 Architecture Graph

`templates/architecture_graph.html` is an interactive D3.js force-directed graph served both via the API (`/api/v1/graph/view`) and as a standalone HTML document. Node colors encode module roles, edges show import dependencies, and tooltips expose function-level detail.

---

## Section 9: Complete REST API Reference (14 Endpoints)

### 9.1 Base URL

```
http://localhost:8000/api/v1
```

### 9.2 Interactive Documentation

Auto-generated OpenAPI docs at:

```
http://localhost:8000/docs          (Swagger UI)
http://localhost:8000/redoc         (ReDoc)
```

### 9.3 Endpoint Catalog

| # | Method | Path | Description | Response |
|---|--------|------|-------------|----------|
| 1 | `GET` | `/health` | System health, DB stats, embedding coverage | `SystemHealth` |
| 2 | `GET` | `/papers` | Paginated paper list (sorted by overall_score) | `PaginatedPapers` |
| 3 | `GET` | `/papers/{paper_id}` | Full paper detail with all 25 fields | `PaperDetail` |
| 4 | `POST` | `/papers/{paper_id}/evaluate` | Single-paper AI evaluation (BackgroundTasks) | `TaskStatus` (202) |
| 5 | `POST` | `/search/semantic` | Natural-language semantic vector search | `SemanticSearchResponse` |
| 6 | `POST` | `/scrape/trigger` | Trigger daily scrape pipeline (BackgroundTasks) | `TaskStatus` (202) |
| 7 | `POST` | `/optimize/gwo` | Trigger GWO hyperparameter optimization (BackgroundTasks) | `TaskStatus` (202) |
| 8 | `GET` | `/optimize/gwo/history` | GWO optimization history for Recharts | `List[dict]` |
| 9 | `GET` | `/graph/view` | Serve architecture dependency graph HTML | `HTML` (FileResponse) |
| 10 | `POST` | `/ai/translate-query` | Natural-language to boolean query translation | `TranslateQueryResponse` |
| 11 | `GET` | `/analysis/authors` | Top authors ranked by publication count | `List[AuthorSummary]` |
| 12 | `POST` | `/db/recalculate-scores` | Bulk overall_score recalculation (BackgroundTasks) | `TaskStatus` (202) |
| 13 | `GET` | `/tasks/{task_id}` | Background task status | `TaskStatus` |
| 14 | `GET` | `/tasks` | List all background tasks (newest first) | `List[TaskStatus]` |

### 9.4 Additional System Endpoint

| # | Method | Path | Description | Response |
|---|--------|------|-------------|----------|
| 15 | `GET` | `/capabilities` | Serve the System Capabilities Master Reference | `HTMLResponse` |

### 9.5 Authentication

Endpoints are currently unauthenticated (development mode). Production deployment should add JWT-based authentication via FastAPI middleware.

### 9.6 Rate Limiting

Background task endpoints (`/scrape/trigger`, `/optimize/gwo`, `/db/recalculate-scores`, `/papers/{id}/evaluate`) are designed for single-concurrent-task operation. Starting a new task while one is running does not queue -- it creates an independent task. Future versions will implement a proper job queue with concurrent task limits.

### 9.7 CORS Configuration

CORS is configured with `allow_origins=["*"]` for development. Production must restrict this to the React frontend origin.

---

*End of System Capabilities Master Reference -- TALOS v5.9.0*
