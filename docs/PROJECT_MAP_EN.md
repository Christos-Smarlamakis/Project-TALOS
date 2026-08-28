# PROJECT_MAP_EN.md -- Complete Project TALOS Map v5.10.16

> **Purpose:** This file is the "memory" of the project. It is mandatory reading for every new chat so the AI agent knows exactly what exists, where, and how it connects -- without re-reading all files.
>
> **Rule:** After ANY code change (new function, modified signature, new/deleted file), this file MUST be updated.
>
> **Last Updated:** 2026-08-28 (v5.10.16 -- Zero-Risk Performance Optimization & Academic LaTeX/BibTeX Engine)

---

## 1. Architecture Overview

```text
USER INTERFACES
  talos.py (Rich TUI -- 6-group hierarchical menu)  src/api/main_api.py (FastAPI -- 23 endpoints E01-E23)
  React 18 + Tailwind CSS + Shadcn UI           templates/dashboard.html (Flask, legacy)
  src/utils/tray_icon.py (system tray)          templates/live_foraging_visualizer.html (Three.js)

        | subprocess / direct import
        v

SRC PACKAGES
  src/core/          (5 files)  ai_manager, database_manager, hardware, notifier, profile_manager
  src/ai/drl/       (10 files)  drl_agent, drl_networks, talos_env, train_agent, live_agent_*
  src/ai/optimizers/ (3 files)  gwo_foraging_hyperparameter_tuner, gwo_live_dashboard, gwo_llm_router_reward_shaper
  src/ai/embeddings/ (2 files)  embedding_generator, db_embedding_upgrade
  src/ai/llm/        (4 files)  model_manager, query_translator, research_pivot, model_discovery
  src/ai/testing/    (1 file)   red_tester
  src/analysis/     (10 files)  citation_analyzer, author_profiler, recommender, knowledge_path, etc.
  src/ingestion/    (23 files)  16 source agents + 7 pipelines
  src/integration/   (3 files)  synapse_client, optica_client, visualizer_bridge
  src/utils/        (17 files)  db_stats, logger, tray_icon, model_provisioner, daemon_autostart, http_client, snapshot_manager, academic_export, etc.
  src/api/           (4 files)  main_api, synapse_routes, red_tester_routes, talos_service_api
  src/mcp_server.py             MCP stdio server (4 tools)

        | import
        v

GLOBAL HANDLERS (src/core)
  ai_manager.py (multi-provider LLM)     database_manager.py (SQLite + embeddings)
  hardware.py (GPU / VRAM detection)     notifier.py (alerts)     profile_manager.py (profiles)

        | HTTP requests
        v

EXTERNAL APIs & SERVICES
  Gemini  DeepSeek  HuggingFace  Ollama  Discord  Zotero  Unpaywall  ORCID
  Semantic Scholar  IEEE  Elsevier  Springer  Crossref  OpenAIRE  OpenReview
  SYNAPSE bus (port 8000)    OPTICA bridge (port 8002)
```

Data Flow:

```text
User > talos.py > run_script() > src/<package>/*.py > src/core/*.py
                                        > src/ingestion/*.py > External APIs
                                                |
                                        data/talos_research.db (SQLite)
                                                |
                                        config.json + .env
```

## 2. Core Modules (src/core)

| Module | Role |
|--------|------|
| `ai_manager.py` | Multi-provider LLM manager (Gemini, DeepSeek, HuggingFace, Ollama) with circuit breakers, JSON/text/embedding modes, and `last_provider_used` attribution |
| `database_manager.py` | SQLite persistence (20+ columns), 4-layer scoring (strategic/operational/tactical/playground), embeddings table, cosine semantic search, enrichment state machine |
| `hardware.py` | Single source of truth for GPU detection and VRAM queries; CPU fallback with graceful degradation |
| `notifier.py` | Telegram / Discord / Email alerting for high-score papers |
| `profile_manager.py` | Profile switching and retrieval (isolated config + DB per research topic) |

### 2.1 DRL Environment (`src/ai/drl/talos_env.py`, v3.2)

| Method | Signature | Description |
|--------|-----------|-------------|
| `_load_source_list` | `(config=None) -> list` | Read source list from config.json |
| `_build_obs` | `() -> np.ndarray` | 23-dim state: [hour/24, 16 source ratios, low/10, err/10, 4 provider ratios] |
| `step` | `(action) -> (obs, reward, terminated, truncated, info)` | Execute action (0..N-1 query source, N sleep) |
| `get_default_state_space` | `() -> int` | 23 |
| `get_default_action_space` | `() -> int` | 17 (16 sources + sleep) |

### 2.2 DRL Agent (`src/ai/drl/drl_agent.py`)

`TalosDRLAgent` -- DDDQN agent with pluggable networks (`drl_networks.py`), epsilon-greedy (eps=0.0 during live inference), and auto-reconstruction for new dimensions.

## 3. Entry Points

| Entry | Description |
|-------|-------------|
| `talos.py` | Rich-powered TUI (15-option menu across five visual groups) |
| `src/api/main_api.py` | Headless FastAPI facade (23 endpoints E01-E23, port 8001) with Synapse webhook + Red Tester routers |
| `run_talos.bat` / `run_talos.sh` | Launcher scripts (TUI, API server, daemon, tests) |
| `src/mcp_server.py` | MCP stdio server exposing 4 tools (system_status, semantic_search, paper_details, trigger_scrape) |

## 4. Packages & Scripts Inventory

| Package | Files | Key modules |
|---------|-------|-------------|
| `src/ai/drl/` | 10 | `talos_service.py` (24/7 daemon), `talos_live_agent.py`, `live_agent_orchestrator.py`, `llm_router_subagent.py`, `train_agent.py`, `drl_trainer.py` |
| `src/ai/optimizers/` | 3 | GWO foraging tuner, live dashboard, reward shaper |
| `src/ai/embeddings/` | 2 | `embedding_generator.py`, `db_embedding_upgrade.py` |
| `src/ai/llm/` | 4 | `model_manager.py`, `query_translator.py`, `research_pivot.py`, `model_discovery.py` |
| `src/analysis/` | 10 | `citation_analyzer.py`, `author_profiler.py`, `recommender.py`, `knowledge_path_generator.py`, `trend_analyzer.py`, `graphify_adapter.py`, `generate_baseline_report.py`, etc. |
| `src/ingestion/` | 23 | 16 source agents + `daily_search.py`, `historic_search.py`, `grey_literature_miner.py`, `pdf_downloader.py`, `zotero_connector.py`, `metadata_enricher.py`, `data_enricher.py` |
| `src/utils/` | 17 | `db_stats.py`, `logger.py`, `tray_icon.py`, `model_provisioner.py`, `daemon_autostart.py`, `ui_theme.py`, `api_health_check.py`, `http_client.py`, `snapshot_manager.py`, `academic_export.py`, etc. |

## 5. Sources (16 APIs)

arxiv, ieee, semantic_scholar, springer, openalex, dblp, elsevier, core, crossref, openarchives, pubmed, scigov, osti, plos, openreview, openaire

Standardized output: `{doi, url, title, authors_str, publication_year, abstract, source}`

## 6. Configuration & Data Flow

### 6.1 config.json Schema (top-level keys)

Models & routing: `model_for_daily_search`, `pre_screening_model`, `grey_research_model`, `deepseek_model_chat`, `ai_provider_priority`, `gemini_tier`, `provider_limits`, `failure_threshold`

Thresholds & limits: `min_pre_screening_score`, `reevaluation_days_window`, `api_call_limit_flash`, `api_call_limit_pro`, `ai_request_delay`, `days_to_search_daily`, `days_to_search_historic`, `max_results_config`

Queries: `arxiv_query`, `ieee_query`, `springer_query`, `openalex_query`, `dblp_query`, `elsevier_query`, `crossref_query`, `openarchives_query`, `pubmed_query`, `osti_query`, `plos_query`, `semantic_scholar_query`, `core_query`, `scigov_query`, `openreview_query`, `openaire_query`

Prompts: `phd_focus_system_prompt`, `pre_screening_prompt`, `trajectory_analyzer_prompt`, `orpheus_references_prompt_instruction`, `orpheus_citations_prompt_instruction`, `chiron_synthesizer_prompt`, `query_translator_prompt`

Daemon: `daemon_target_sources`, `daemon_reporting_mode`, `active_focus_summary`, `mailto`

### 6.2 .env Keys (example.env)

LLM & runtime: `FAST_EDGE_MODEL`, `FAST_EDGE_BASE_URL`, `HEAVY_REASONING_MODEL`, `OLLAMA_BASE_URL`, `TALOS_CLOUD_PROVIDER`, `TALOS_EXECUTION_MODE`, `TALOS_API_PORT`, `SYNAPSE_BUS_URL`, `OPTICA_API_BASE`

Provider keys: `GEMINI_API_KEY`, `DEEPSEEK_API_KEY`, `HF_TOKEN`, `NVIDIA_API_KEY`, `GROQ_API_KEY`, `CEREBRAS_API_KEY`, `GITHUB_TOKEN`, `MISTRAL_API_KEY`, `OPENROUTER_API_KEY`

Source keys: `ZOTERO_API_KEY`, `SEMANTIC_SCHOLAR_API_KEY`, `IEEE_API_KEY`, `SPRINGER_API_KEY`, `ELSEVIER_API_KEY`, `CORE_API_KEY`, `OPENARCHIVES_API_KEY`, `OPENREVIEW_USERNAME/PASSWORD`, `OPENAIRE_TOKEN`, `ORCID_CLIENT_ID/SECRET`

Alerts: `DISCORD_WEBHOOK_URL`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `SMTP_*`, `MAILTO`

### 6.3 Environment Variables (Runtime)

`TALOS_USE_LOCAL`, `TALOS_MODELS_VERIFIED`, `TALOS_ALLOW_CLOUD_FALLBACK`, `TALOS_ALLOW_LOCAL_FALLBACK`, `TALOS_NETWORK_STRATEGY`, `TALOS_HARDWARE_STRATEGY`, `HF_MODEL_NAME`

### 6.4 Profile System

`_profiles/<name>/` holds an isolated `config.json` and `talos_research.db` per research topic. `active_profile.txt` tracks the active profile.

## 7. Dependency Graph

```text
talos.py
  +-- src/utils/ui_theme.py, logger.py
  +-- src/core/profile_manager.py
  +-- src/core/ai_manager.py
  +-- src/api/main_api.py (subprocess uvicorn)
  +-- src/ai/drl/talos_service.py (subprocess CREATE_NEW_CONSOLE)

src/ai/drl/talos_service.py
  +-- src/core/notifier.py
  +-- src/core/database_manager.py
  +-- src/ai/drl/drl_agent.py, talos_env.py, train_agent.py
  +-- src/ai/drl/live_agent_orchestrator.py
  +-- src/ai/drl/llm_router_subagent.py
  +-- src/utils/tray_icon.py (optional)
  +-- src/integration/visualizer_bridge.py

src/ai/drl/live_agent_orchestrator.py
  +-- src/integration/visualizer_bridge.py

src/ingestion/*.py
  +-- src/core/database_manager.py
  +-- src/integration/synapse_client.py
  +-- src/integration/visualizer_bridge.py
```

## 8. Module Descriptions (recent additions highlighted)

| Module | Path | Description |
|--------|------|-------------|
| **Universal TUI (v5.10.15)** | `talos.py` | Unified 6-group hierarchical menu -- 45/45 executable modules, dead sub-menu revival, GWO Swarm suite |
| **Desktop Control Hub (v5.10.13)** | `src/utils/tray_icon.py` | `launch_tray_icon_async()` -- 7-item pystray menu (3D Visualizer, Reports Folder, System Log, Swagger, Instant Search, Console, Terminate) with `_is_api_alive()` / `_ensure_api_server()` self-healing |
| **DatabaseManager Persistence (v5.10.13)** | `src/core/database_manager.py` | Default `db_path=None` -> `get_active_profile_db_path()` (active profile DB `_profiles/<active>/talos_research.db`) |
| **3D Visualizer (v5.10.12)** | `templates/live_foraging_visualizer.html` | Three.js constellation with 60 FPS laser beams, photon pulses, raycaster, snapshot |
| **OPTICA Bridge (v5.10.7)** | `src/integration/optica_client.py` | REST client to Project OPTICA (port 8002) offloading heavy graphics |
| **Daemon OS Autostart (v5.10.6)** | `src/utils/daemon_autostart.py` | Windows Startup shortcut + boot batch generator |
| **Universal Model Provisioner (v5.10.5)** | `src/utils/model_provisioner.py` | 3-tier local path resolution + self-healing fallback |
| **Enterprise Logger** | `src/utils/logger.py` | `get_logger(name)` -- RichHandler console + RotatingFileHandler |
| **MCP Server** | `src/mcp_server.py` | 4-tool stdio server delegating to FastAPI |
| **SYNAPSE Emitter** | `src/integration/synapse_client.py` | EventEmitter pushing JSON events to port 8000 |
| **Visualizer Bridge (v5.10.12)** | `src/integration/visualizer_bridge.py` | `push_visualizer_event()` -- centralized HTTP push bridge to the 3D Visualizer (port 8001) |

## 9. Auxiliary Files

| File/Dir | Role |
|----------|------|
| `docs/` | Permanent documentation (CHANGELOG, ROADMAP, TIMELINE, PROJECT_MAP, SYSTEM_CAPABILITIES, TECH_RADAR) |
| `docs/internal/` | Proprietary documents (API_HANDOVER, UX_UI_BLUEPRINT, IP_PROTECTION) |
| `tools/` | Dev & utility scripts |
| `Dockerfile`, `docker-compose.yml` | Containerization |
| `README.md`, `CITATION.cff`, `LICENSE` | Metadata |
| `data/reports/` | All generated reports (v5.9.9 consolidation) |

## 10. Known Gotchas & Conventions

1. Greek comments break editor text matching
2. `.env` values without quotes -- load_dotenv does not strip quotes
3. `daily_search.py` and `historic_search.py` must stay in sync for dedup logic
4. 4-layer framework (strategic/operational/tactical/playground) is INVARIANT
5. `recommender.py` reads SQLite directly, not via DatabaseManager
6. Circuit breaker at 5+ failures
7. Database path resolves to `data/talos_research.db` (no ghost DBs in `src/`)
8. API endpoints must never trigger interactive `questionary.confirm()`
9. TALOS FastAPI runs on port 8001 (Synapse on 8000, OPTICA on 8002)
10. The daemon spawns in a new console window (CREATE_NEW_CONSOLE) on Windows
11. `src/utils/tray_icon.py` uses lazy imports so it degrades gracefully without pystray

---

> **Last Updated:** 2026-08-28 (v5.10.16 -- Zero-Risk Performance Optimization & Academic LaTeX/BibTeX Engine)
> **Project Version:** v5.10.16
> **Total .py modules under src/:** 83 (core 5 + ai/drl 10 + ai/optimizers 3 + ai/embeddings 2 + ai/llm 4 + ai/testing 1 + analysis 10 + ingestion 23 + integration 3 + utils 17 + api 4 + mcp_server 1)


