# PROJECT_MAP_EN.md -- Complete Project TALOS Map v5.24.0

> **Purpose:** This file is the "memory" of the project. It is mandatory reading for every new chat so the AI agent knows exactly what exists, where, and how it connects -- without re-reading all files.
>
> **Rule:** After ANY code change (new function, modified signature, new/deleted file), this file MUST be updated.
>
> **Last Updated:** 2026-10-04 (v5.24.0 -- Enterprise Data Vault, Proactive Token-Bucket Rate Limiter & Distributed JSONL Buffer Sync)

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
  src/core/          (8 files)  ai_manager, database_manager, database_vault, hardware, notifier, profile_manager, provider_registry, hardware_advisor
  src/services/      (12 files) cognitive_mesh/ (dto, registry, router, rate_limiter, benchmarks, buffer_sync, scavenger, reporter, server, client) -- extraction-ready for SYNAPSE
  src/ai/drl/       (10 files)  drl_agent, drl_networks, talos_env, train_agent, live_agent_*
  src/ai/optimizers/ (3 files)  gwo_foraging_hyperparameter_tuner, gwo_live_dashboard, gwo_llm_router_reward_shaper
  src/ai/embeddings/ (2 files)  embedding_generator, db_embedding_upgrade
  src/ai/llm/        (4 files)  model_manager, query_translator, research_pivot, model_discovery
  src/ai/testing/    (1 file)   red_tester
  src/analysis/     (10 files)  citation_analyzer, author_profiler, recommender, knowledge_path, etc.
  src/ingestion/    (25 files)  18 source agents + 7 pipelines
  src/integration/   (3 files)  synapse_client, optica_client, visualizer_bridge
  src/utils/        (21 files)  db_stats, logger, tray_icon, help_system, model_provisioner, daemon_autostart, http_client, snapshot_manager, academic_export, evaluation_history, research_setup_wizard, etc.
  src/api/           (4 files)  main_api, synapse_routes, red_tester_routes, talos_service_api
  src/prisma/        (8 files + skills/)  dspy_signatures, dspy_modules, swarm_evaluators (Tier-1), quality_swarm (Tier-2: SkillCompiler, SmartSectionSlicer, 4 auditors, KitchenhamQualitySynthesizer), mermaid_generator, scoping_review_synthesizer, quality_appraisal
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
| `ai_manager.py` | Multi-provider LLM manager (Gemini, DeepSeek, HuggingFace, Ollama) with circuit breakers, JSON/text/embedding modes, and `last_provider_used` attribution; v5.12.2 adds self-healing Ollama probe/spawn (`probe_local_ollama`), provider trimming (`STANDBY_NO_KEY`), on-demand .env key injection, google.genai GA SDK, thinking-model parser (`_strip_thinking_tags()` / `_extract_assistant_content()`), and `LOCAL_GPU_MODEL` baseline; v5.18.5 adds Cloud Provider Quota Latching (`exhausted_providers`) to fast-bypass 402/401 providers |
| `database_manager.py` | SQLite persistence (20+ columns), 4-layer scoring (strategic/operational/tactical/playground), embeddings table, cosine semantic search, enrichment state machine |
| `hardware.py` | Single source of truth for GPU detection and VRAM queries; CPU fallback with graceful degradation |
| `provider_registry.py` | Pluggable LLM provider registry (Open-Closed Principle): `ProviderDescriptor` + `ProviderRegistry` with `register`/`get`/`list_all`/`list_active` -- local Ollama + 9 cloud providers |
| `hardware_advisor.py` | Hardware-aware model advisor: `HardwareModelAdvisor` -- `get_hardware_profile()`, `calculate_vram_budget()` (4-bit), `get_recommendations()`, `scan_sota_models()` |
| `notifier.py` | Telegram / Discord / Email alerting for high-score papers |
| `profile_manager.py` | Profile switching and retrieval (isolated config + DB per research topic) |
| `hierarchical_evaluator.py` | Centralized Two-Stage Rigor Decoupling Engine (v5.19.0): `HierarchicalEvaluationEngine` with Stage 1 (fast 8B sieve → S_rel_prelim) + Stage 2 Dual-Audit (Faceted Relevance Calibration S_rel_calibrated + Kitchenham 2007 S_qual via `PrismaQualityAppraiser`) + 2D Evidence Quadrant mapping -- via `evaluate_paper()` / `evaluate_batch()` (ThreadPoolExecutor + `Semaphore(2)`) |

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
| `run_talos.bat` / `run_talos.sh` | Launcher scripts (TUI, API server, daemon, tests). v5.11.2: `run_talos.bat` adds `:AUTO_PREFLIGHT` (5-step onboarding wizard with silent Miniconda3 bootstrap), `:DISCOVER_CONDA` (multi-root + PATH discovery of `condabin\conda.bat`, back-fills `CONDA_ACTIVATE_PATH`), and a silent fast-path bypass gate (sub-1-second startup when Conda + `talosenv` + `.env` + core packages are already present) |
| `src/mcp_server.py` | MCP stdio server exposing 4 tools (system_status, semantic_search, paper_details, trigger_scrape) |

## 4. Packages & Scripts Inventory

| Package | Files | Key modules |
|---------|-------|-------------|
| `src/ai/drl/` | 10 | `talos_service.py` (24/7 daemon), `talos_live_agent.py`, `live_agent_orchestrator.py`, `llm_router_subagent.py`, `train_agent.py`, `drl_trainer.py` |
| `src/ai/optimizers/` | 3 | GWO foraging tuner, live dashboard, reward shaper |
| `src/ai/embeddings/` | 2 | `embedding_generator.py`, `db_embedding_upgrade.py` |
| `src/ai/llm/` | 4 | `model_manager.py`, `query_translator.py`, `research_pivot.py`, `model_discovery.py` |
| `src/analysis/` | 10 | `citation_analyzer.py`, `author_profiler.py`, `recommender.py`, `knowledge_path_generator.py`, `trend_analyzer.py`, `graphify_adapter.py`, `generate_baseline_report.py`, etc. |
| `src/ingestion/` | 24 | 18 source agents + `daily_search.py`, `historic_search.py`, `grey_literature_miner.py`, `zotero_connector.py`, `metadata_enricher.py`, `data_enricher.py` |
| `src/utils/` | 18 | `db_stats.py`, `logger.py`, `tray_icon.py`, `help_system.py`, `model_provisioner.py`, `daemon_autostart.py`, `ui_theme.py`, `api_health_check.py`, `http_client.py`, `snapshot_manager.py`, `academic_export.py`, etc. |
| `src/prisma/` | 8 | `dspy_signatures.py` (typed declarative Pydantic-v2 signatures), `dspy_modules.py` (PlanEval: Planner/Evaluator/EligibilityJudge/Executor), `swarm_evaluators.py` (Tier-1 3-agent peer-review swarm + Cohen's Kappa + consensus arbiter), `quality_swarm.py` (Tier-2 Forensic Quality Swarm: `SkillCompiler`, `SmartSectionSlicer`, `TheoryAuditor`/`OperationalAuditor`/`BenchmarkAuditor`/`OpenScienceAuditor`, `KitchenhamQualitySynthesizer`, `SwarmQualityVerdict`), `mermaid_generator.py`, `scoping_review_synthesizer.py`, `quality_appraisal.py` (Kitchenham 2007 rubric + 2D quadrants), plus `skills/` package with 4 domain-agnostic templates |

## 5. Sources (18 APIs)

arxiv, ieee, semantic_scholar, springer, openalex, dblp, elsevier, core, crossref, openarchives, pubmed, scigov, osti, plos, openreview, openaire, nasa_ntrs, hal_inria

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

**v5.16.1:** `src/core/profile_manager.py` is the strict single source of truth. The `ProfileManager` class (anchored to repo-root `_profiles/`) exposes `get_profiles_dir()`, `get_active_profile_name()`, `set_active_profile()`, `list_profiles()`, `create_profile()`, `get_active_db_path()`, and `get_active_config_path()`. `database_manager.get_active_profile_db_path()` and the wizard/TUI helpers delegate to it.

## 7. Dependency Graph

```text
talos.py
  +-- src/utils/ui_theme.py, logger.py
  +-- src/core/profile_manager.py
  +-- src/core/hardware_advisor.py
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
  +-- src/ingestion/resilient_gateway.py

src/ingestion/resilient_gateway.py
  +-- src/utils/http_client.py

src/ingestion/sources/*.py
  +-- src/utils/http_client.py

src/search/citation_snowballing.py
  +-- src/prisma/dspy_modules.py
  +-- src/core/ai_manager.py
  +-- src/core/database_manager.py

src/search/neural_vector_search.py
  +-- config/settings.py
  +-- src/core/database_manager.py

src/search/code_first_search.py
  +-- src/core/database_manager.py

src/utils/research_setup_wizard.py
  +-- src/utils/ui_theme.py, logger.py
  +-- src/core/ai_manager.py
  +-- src/ai/llm/query_translator.py

src/utils/system_diagnostics.py
  +-- src/core/database_manager.py
  +-- config/settings.py

src/utils/help_system.py
  +-- config/settings.py
  +-- src/utils/ui_theme.py
  +-- rich, questionary, webbrowser

src/utils/desktop_shortcut.py
  +-- os, subprocess (stdlib); rich (lazy)

src/utils/daemon_autostart.py
  +-- src/core/profile_manager.py (lazy); win32com.client, questionary (lazy)

src/prisma/dspy_modules.py
  +-- src/prisma/dspy_signatures.py
  +-- src/prisma/swarm_evaluators.py
  +-- src/prisma/mermaid_generator.py
  +-- src/prisma/scoping_review_synthesizer.py

src/prisma/swarm_evaluators.py
  +-- src/prisma/dspy_signatures.py

src/prisma/quality_appraisal.py
  +-- src/prisma/dspy_signatures.py
  +-- src/prisma/quality_swarm.py (lazy, swarm mode)
  +-- src/core/ai_manager.py
  +-- src/core/database_manager.py

src/prisma/quality_swarm.py
  +-- src/prisma/dspy_signatures.py
  +-- src/prisma/quality_appraisal.py
  +-- src/prisma/swarm_evaluators.py
  +-- src/core/hardware_advisor.py (lazy)
  +-- src/core/profile_manager.py (lazy)
  +-- src/core/ai_manager.py (lazy)

scripts/migrate_d3qn_checkpoint.py
  +-- torch
  +-- src/ai/drl/drl_networks.py (DuelingLSTM)

src/core/provider_registry.py
  +-- config/settings.py

src/core/hardware_advisor.py
  +-- src/core/hardware.py
  +-- config/settings.py

src/core/ai_manager.py
  +-- src/core/provider_registry.py

src/core/hierarchical_evaluator.py
  +-- config/settings.py
  +-- src/core/ai_manager.py (lazy)
```

## 8. Module Descriptions (recent additions highlighted)

| Module | Path | Description |
|--------|------|-------------|
| **Universal TUI (v5.10.15)** | `talos.py` | Unified 6-group hierarchical menu -- 45/45 executable modules, dead sub-menu revival, GWO Swarm suite |
| **Desktop Control Hub (v5.10.13)** | `src/utils/tray_icon.py` | `launch_tray_icon_async()` -- 7-item pystray menu (3D Visualizer, Reports Folder, System Log, Swagger, Instant Search, Console, Terminate) with `_is_api_alive()` / `_ensure_api_server()` self-healing |
| **DatabaseManager Persistence (v5.10.13)** | `src/core/database_manager.py` | Default `db_path=None` -> `get_active_profile_db_path()` (active profile DB `_profiles/<active>/talos_research.db`) |
| **Profile Manager SSOT (v5.16.1)** | `src/core/profile_manager.py` | Canonical `ProfileManager` class (repo-root `_profiles/`), exposing `get_profiles_dir()` / `get_active_profile_name()` / `set_active_profile()` / `list_profiles()` / `create_profile()` / `get_active_db_path()` / `get_active_config_path()`; canonical `uav_mission_planning` workspace |
| **Pluggable Provider Registry (v5.16.2)** | `src/core/provider_registry.py` | `ProviderDescriptor` (dataclass) + `ProviderRegistry` with `register` / `get` / `list_all` / `list_active` -- 10 providers (Ollama + NVIDIA NIM, DeepSeek, Gemini, Groq, Cerebras, Mistral, Hugging Face, OpenRouter, Anthropic); dynamic `is_active` evaluation |
| **Hardware-Aware Model Advisor (v5.16.2)** | `src/core/hardware_advisor.py` | `HardwareModelAdvisor` -- `get_hardware_profile()` (`{has_cuda, device_name, total_vram_gb, system_ram_gb, is_laptop_cpu}`), `calculate_vram_budget()` (4-bit piecewise), `get_recommendations()`, `scan_sota_models()` (SOTA radar) |
| **Ethical Academic PDF Harvester, Smart Section Slicing & SQLite FTS5 Engine (v5.18.0)** | `src/ingestion/pdf_harvester/`, `src/search/fulltext_search.py`, `src/core/database_manager.py` | `resolve_oa_url()` (13-source legal OA cascade: arXiv, TechRxiv, HAL/Inria, NASA NTRS, Elsevier OA, PLOS, PMC, Unpaywall, OpenAlex, Semantic Scholar, CORE, Crossref OA, SSRN); `AcademicPDFHarvester.harvest_candidates()` (`%PDF-` magic bytes, atomic writes, SHA-256, polite rate limit); `PDFSectionExtractor.extract_sections()` (methodology/experiments/code_availability/limitations windows); `FullTextSearchEngine.search_fulltext()` (FTS5 `papers_fts` + BM25 + snippet); `SmartSectionSlicer` cached-section integration; CLI `--download-pdfs` / `--fts` / `--open-pdf`; `papers` schema `local_pdf_path` / `pdf_sha256` / `pdf_status` |
| **Two-Tier Forensic Quality Swarm (v5.17.0)** | `src/prisma/quality_swarm.py` | Tier-2 swarm: `SkillCompiler.compile_profile_skills()` (domain-agnostic templates -> `_profiles/<name>/skills/*.md`), `SmartSectionSlicer.slice_for_auditor()`, four specialized auditors (`TheoryAuditor` Q1 / `OperationalAuditor` Q2 / `BenchmarkAuditor` Q3-Q4 / `OpenScienceAuditor` Q5-Q6), `KitchenhamQualitySynthesizer.synthesize()` (`S_qual` + Fleiss `kappa_qual` + quadrant + narrative), and `SwarmQualityVerdict` |
| **3D Visualizer (v5.10.12)** | `templates/live_foraging_visualizer.html` | Three.js constellation with 60 FPS laser beams, photon pulses, raycaster, snapshot |
| **OPTICA Bridge (v5.10.7)** | `src/integration/optica_client.py` | REST client to Project OPTICA (port 8002) offloading heavy graphics |
| **Daemon OS Autostart (v5.10.6)** | `src/utils/daemon_autostart.py` | Windows Startup shortcut + boot batch generator |
| **Universal Model Provisioner (v5.10.5)** | `src/utils/model_provisioner.py` | 3-tier local path resolution + self-healing fallback |
| **Enterprise Logger** | `src/utils/logger.py` | `get_logger(name)` -- RichHandler console + RotatingFileHandler |
| **MCP Server** | `src/mcp_server.py` | 4-tool stdio server delegating to FastAPI |
| **SYNAPSE Emitter** | `src/integration/synapse_client.py` | EventEmitter pushing JSON events to port 8000 |
| **Visualizer Bridge (v5.10.12)** | `src/integration/visualizer_bridge.py` | `push_visualizer_event()` -- centralized HTTP push bridge to the 3D Visualizer (port 8001) |

| **Evaluation History (v5.11.0)** | `src/utils/evaluation_history.py` | `record_evaluation()` / `read_evaluation_history()` / `verdict_for_score()` -- append-only JSONL recorder at `data/history/daemon_evaluations.jsonl`; `_show_evaluation_history(limit=30)` Rich TUI viewer in `talos.py` |
| **Live Telemetry HUD Console (v5.11.0)** | `templates/live_foraging_visualizer.html` | bottom-right glassmorphism stream (40-line ring buffer, auto-scroll, `C`/`L` hotkeys, snapshot auto-hide) driven by `appendConsoleLog()` |
| **Win32 Close-to-Tray Hook (v5.11.0)** | `src/utils/tray_icon.py` | `enable_close_to_tray()` subclasses the console WndProc (WM_CLOSE / SC_CLOSE to SW_HIDE) so closing minimizes to tray |
| **Research Setup Wizard (v5.12.0)** | `src/utils/research_setup_wizard.py` | `_ensure_local_ai_runtime()` (probe/spawn ports 11434+11435 with 2s bounded wait), `_analyze_scope_heuristic()` / `_analyze_scope_with_llm()`, `_generate_queries_llm()` / `_generate_queries_heuristic()`, `_apply_execution_strategy()`, `_write_search_window()`, `_create_sentinel()`, `_render_query_preview()` (query-transparency table + confirmation gate, v5.12.1), `_extract_salient_terms()` (heuristic stopword cleaner, v5.12.2), `_prompt_custom_days()` / `_step3_search_window()` (day-based window), `_render_cancelled()` (cancellation integrity), `LANGUAGE_AND_SYNTAX_MANDATE` (English-first mandate), 5-tier `EXECUTION_STRATEGIES` + `ai_strategy_selector.py` (strategy switcher) -- Step 0 profile gate (_step0_profile_selection + _list_profiles/_get_active_profile/_set_active_profile/_seed_profile_config/_persist_active_config, v5.12.4) + 4-step English-first onboarding with failsafe heuristic bypass |
| **Research Pivot Wizard (v5.12.3)** | `src/ai/llm/research_pivot.py` | `_resolve_script_path()` / `run_script()` -- REPO_ROOT-anchored canonical path resolution via `_SCRIPT_MAP` (Cognitive Query Compiler, database re-evaluation, DRL trainer) executed with `sys.executable`; strict `proc.returncode` verification (YES only for code 0, otherwise `FAILED (Code X)`); Rule 9 codename elimination (PYTHIA/CHIRON) |
| **Concurrent Ingestion Mesh (v5.12.4)** | `src/ingestion/daily_search.py` | `_harvest_single_source()` (per-thread source isolation with stdout capture + full exception guard), `_deduplicate_papers()` (DOI + SHA-1 normalized-title hash), `_normalize_title()` / `_title_hash()`, `ThreadPoolExecutor(max_workers=min(18, len(enabled_scrapers)))` with `as_completed()` + Rich Live telemetry table (WAITING/HARVESTING/COMPLETED/FAILED) and ingestion summary panel (~35-45s to ~3-4s) |

| **Full-Stack Concurrent Multi-Threaded Engine (v5.13.0)** | `src/core/ai_manager.py`, `src/ingestion/historic_search.py`, `src/utils/reevaluate_database.py` | `batch_evaluate_papers()` / `_resolve_eval_concurrency()` (8 cloud / 2 local workers + `threading.Semaphore(2)` VRAM guard), `historic_search.py` `ThreadPoolExecutor(max_workers=min(18, len(enabled_sources)))` mesh + `_harvest_single_source()` + Rich Live telemetry, `reevaluate_database.py:_apply_evaluation_batch()` (batched SQLite WAL commits) |
| **System Diagnostics Analyzer (v5.13.1)** | `src/utils/system_diagnostics.py` | `SystemDiagnosticsEngine` -- 8-point pre-flight health check (Python environment, SQLite integrity, local AI runtime, port availability, filesystem permissions, environment credentials, daemon status, network endpoints) with `run_diagnostics()` / `render_report()` (Rich health table + one-line remediation); CLI `--diagnostics`/`--doctor`/`-d` and TUI Group 6 option 1 |
| **Stanford DSPy PRISMA-ScR Pipeline (v5.14.0)** | `src/prisma/dspy_signatures.py`, `dspy_modules.py`, `mermaid_generator.py`, `scoping_review_synthesizer.py` | Declarative Pydantic-v2 signatures (`PrismaPlanSignature`, `PrismaScreeningSignature`, `PrismaEligibilitySignature`, `PrismaSynthesisSignature`) + `extract_json_payload()`; `PrismaPlanner.plan()` (protocol synthesis), `PrismaEvaluator.screen()` (Chain-of-Thought screening), `PrismaEligibilityJudge.assess()`, `PrismaExecutor.run()` (4-phase flow + live counters); `generate_prisma_mermaid()` (PRISMA 2020), `synthesize_scoping_review()` / `synthesize_scoping_review_latex()`; CLI `--prisma` + TUI Group 3 |
| **Multi-Agent Peer-Review Swarm & Consensus Engine (v5.14.1)** | `src/prisma/swarm_evaluators.py`, `dspy_modules.py`, `dspy_signatures.py` | `AlgorithmicReviewer` / `EmpiricalReviewer` / `OperationalReviewer` (specialized personas) + `ReviewerVerdict` / `ConsensusVerdict`; `calculate_cohens_kappa()` (Fleiss generalization of Cohen's Kappa) + `cohens_kappa_pairwise()`; `SwarmConsensusArbiter.adjudicate()` (unanimous short-circuit + Chain-of-Thought adjudication); `PrismaEvaluator.evaluation_mode='swarm'` with VRAM `threading.Semaphore(2)`; CLI `--prisma --swarm` + TUI Group 3 screening-mode prompt |
| **BibTeX Scientific Exporter, 18-Source Aerospace Ingestion & Feature Freeze (v5.14.2)** | `src/utils/bibtex_exporter.py`, `src/ingestion/nasa_ntrs_source.py`, `src/ingestion/hal_inria_source.py` | `BibTeXExporter.export_library()` / `render_export_summary()` (`AuthorYearTitleKeyword` cite keys, LaTeX sanitization, `--export-bib`); `NasaNtrsSource` (keyless NASA NTRS REST JSON); `HalInriaSource` (keyless HAL/Inria REST JSON); `papers.prisma_decision` column in `database_manager.create_table()`; CLI `--export-bib` + TUI Group 5 option 12 |
| **Universal Scientific Search Hub & Neural Graph Discovery Engine (v5.15.0)** | `src/ingestion/sources/`, `src/search/citation_snowballing.py`, `src/search/neural_vector_search.py`, `src/search/code_first_search.py` | Unified `SOURCE_REGISTRY` (18 adapters); `CitationSnowballEngine` (backward/forward graph traversal, PRISMA filter, genealogy graph); `NeuralVectorSearchEngine` (local `nomic-embed-text`, cosine similarity); `CodeFirstSearchEngine` (reproducibility signals); CLI `--snowball`/`--vector-search`/`--code-search` + TUI Group 2 |
| **Persistent Vector Cache & Accelerated Neural Embedding Engine (v5.15.1)** | `src/core/database_manager.py`, `src/search/neural_vector_search.py` | Idempotent `paper_embeddings` table + `get_cached_embeddings()` / `save_embeddings_batch()`; `NeuralVectorSearchEngine._index_uncached()` (live `rich.progress.Progress` + `ThreadPoolExecutor` + batch-64 persistence), `_matrix_rank()` (vectorized NumPy matrix cosine similarity, <50ms), `render_results()` (styled Rich Table) |
| **Universal Search Hub UX & Reporting Harmonization (v5.15.2)** | `src/search/code_first_search.py`, `src/search/citation_snowballing.py`, `talos.py` | `CodeFirstSearchEngine.render_results()` / `export_search_report()` (`data/reports/code_search/`); `CitationSnowballEngine.render_genealogy()` / `export_snowball_report()` (`data/reports/snowball/`); raw JSON dumps eliminated (`_render_search_result` removed) |
| **Session Circuit Breaker, Robust Author Extraction & Daemon Lifecycle Hardening (v5.15.3)** | `src/core/ai_manager.py`, `src/utils/evaluation_history.py`, `src/ai/drl/talos_service.py`, `src/ai/drl/live_agent_orchestrator.py`, `src/integration/synapse_client.py` | `AIManager.fast_tier_offline` (latches CPU Edge 11435 offline after first failure, zero re-probes/logs); `normalize_authors(paper)` (resolves `authors_str`/`authors`/`author`); clean `[EVAL]` daemon telemetry; silent SYNAPSE buffering (`synapse_available` + JSONL) |
| **DRL Action-Space Expansion to 18 Sources & Net2Net Checkpoint Migration (v5.15.4)** | `src/ai/drl/talos_env.py`, `scripts/migrate_d3qn_checkpoint.py`, `config.json`, `config.template.json`, `_profiles/default_drones/config.json` | `ALL_KNOWN_SOURCES` 16 -> 18 (adds `nasa_ntrs`, `hal_inria`); action space `Discrete(17) -> Discrete(19)`, observation 23 -> 25 dims; Net2Net surgery (`migrate_d3qn_checkpoint.py`) widens the DuelingLSTM advantage head (15 -> 19) + LSTM input (21 -> 25) preserving all trained weights; 18-source profile/daemon sync; Scopus `$`/`@name`/`@surname` author normalization locked in |
| **Dual-Surface Interactive Help System & Scientific Foundations Canon (v5.15.5)** | `src/utils/help_system.py`, `templates/help_manual.html`, `src/api/main_api.py`, `README.md` | `render_help_manual()` 4-panel Rich manual (`--help` + TUI Option 7); `GET /help` + `GET /manual` (307 redirect) serve the zero-CDN `help_manual.html` (live search, click-to-copy, dark/print-mode toggle); README Section 5 IEEE references [1]-[10] (EN + GR) |
| **PRISMA Quality Appraisal & Dual-Axis Scientific Rigor Engine (v5.16.0)** | `src/prisma/quality_appraisal.py`, `src/core/database_manager.py`, `src/utils/bibtex_exporter.py` | `KitchenhamRubric` / `QualityAppraisalResult` / `PrismaQualityAppraiser`; `map_evidence_quadrant()` (2D quadrants, tau_rel=7.0 / tau_qual=7.5); `appraise_paper()` / `appraise_candidates_batch(force_reappraise)` (ThreadPoolExecutor + `Semaphore(2)`); `update_paper_quality()` (`quality_score`/`quality_rubric_json`/`evidence_quadrant`); `export_library(min_quality, quadrant)` (BibTeX dual-filter + `note` field); CLI `--appraise-quality [--force]` + TUI Group 3 Option 15 (force re-appraisal prompt, v5.17.1) |
| **Pluggable Provider Registry & Hardware-Aware Model Advisor (v5.16.2)** | `src/core/provider_registry.py`, `src/core/hardware_advisor.py`, `src/core/ai_manager.py`, `talos.py`, `src/utils/help_system.py` | `ProviderRegistry` (Open-Closed Principle, 10 providers); `HardwareModelAdvisor` (hardware profile, 4-bit VRAM budget, role-based stack, SOTA radar); `AIManager.list_active_providers()` / `get_provider_descriptor()` (zero regression); CLI `--hardware-advisor` / `--recommend-models` + TUI Option 8 |

| **Two-Stage Rigor Decoupling & Cognitive SOTA Role Matcher (v5.19.0)** | `src/core/hierarchical_evaluator.py`, `src/core/hardware_advisor.py`, `src/ingestion/historic_search.py`, `talos.py` | `HierarchicalEvaluationEngine` Stage-2 Dual-Audit (Faceted Relevance Calibration S_rel_calibrated + Kitchenham S_qual via `PrismaQualityAppraiser`) + 2D Evidence Quadrant; `get_role_based_matrix()` / `render_role_matrix()` / `apply_recommended_models()` (4-role SOTA); `historic_search` engine unification; CLI `--apply-models` |
| **Hierarchical Evaluation Engine, Cognitive LLM Router & Clean Ingestion Lifecycle (v5.18.5)** | `src/core/hierarchical_evaluator.py`, `src/core/ai_manager.py`, `src/ingestion/daily_search.py`, `src/ai/drl/live_agent_orchestrator.py`, `src/ingestion/sources/scigov_source.py`, `src/ingestion/sources/dblp_source.py` | `HierarchicalEvaluationEngine.evaluate_paper()` / `evaluate_batch()` (fast 8B sieve → gate S_rel >= 6.0 → heavy 14B/cloud reasoning + Kitchenham S_qual) · `AIManager.exhausted_providers` + `_latch_provider_exhausted()` (zero-attempt bypass of 402/401 providers) · `SetConsoleTitleW` dynamic console title (zero emojis) · `ScienceGovSource` (DNS isolation + disabled-by-default) · `DBLPSource._sanitize_dblp_query()` (Boolean cleanup + JSONDecodeError guard) |
| **Self-Healing Ingestion Gateway & Autostart Profile Selector (v5.18.4)** | `src/ingestion/resilient_gateway.py`, `src/ingestion/daily_search.py`, `src/ingestion/historic_search.py`, `src/utils/daemon_autostart.py` | `ResilientIngestionGateway` (fast-fail 401/403/Quota, OpenAlex mirroring for IEEE/Elsevier/Springer, `source=<source_key>`) · `main()` Questionary profile selector (Step 1) + `daemon_profile` persistence into `_profiles/<profile>/config.json` |
| **Dual-Checkpoint Net2Net Surgery & Daemon Profile Provisioning (v5.18.3)** | `scripts/migrate_d3qn_checkpoint.py`, `src/utils/daemon_autostart.py`, `src/ai/drl/talos_service.py` | Genuine Net2Net input tensor surgery on BOTH checkpoints (`models/` + `src/ai/models/`, `lstm1.weight_ih_l0` [512, 25], `A.weight` [19, 32], eliminating `RuntimeError: Expected 23, got 25`); `select_daemon_profile()` (Questionary) + `--profile <name>` with dynamic banner synced to `uav_mission_planning` |
| **Net2Net Checkpoint Repair, Win32 Close-to-Tray, Desktop Shortcut & Autostart Profile Selector (v5.18.2)** | `scripts/migrate_d3qn_checkpoint.py`, `src/utils/tray_icon.py`, `src/utils/desktop_shortcut.py`, `src/utils/daemon_autostart.py`, `src/ai/drl/talos_service.py`, `talos.py` | Idempotent Net2Net migration confirmation/seal (18 sources / 25 dims, zero-error forward pass); `enable_close_to_tray()` (WNDPROC, SW_HIDE + `[TRAY]` notice); `create_desktop_shortcut()` (`TALOS Research Hub.lnk` via `WScript.Shell` COM); `select_daemon_profile()` + `--profile <name>` |

## 9. Auxiliary Files

| File/Dir | Role |
|----------|------|
| `docs/` | Permanent documentation (CHANGELOG, ROADMAP, TIMELINE, PROJECT_MAP, SYSTEM_CAPABILITIES, ENVIRONMENT_SETUP_GUIDE EN/GR) |
| `docs/ENVIRONMENT_SETUP_GUIDE.md` | Canonical English environment & credentials setup guide (`.env` vs `settings.py` decoupling, local Ollama, cloud mesh, academic APIs, network/port matrix) |
| `docs/ENVIRONMENT_SETUP_GUIDE_GR.md` | Canonical Greek environment & credentials setup guide (pure Greek script) |
| `docs/internal/` | Proprietary / confidential documents (API_HANDOVER, UX_UI_BLUEPRINT, IP_PROTECTION, TECH_RADAR EN/GR -- confidential strategy map) |
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
12. The SSE generator in `visualizer_sse_stream` must never call blocking `queue.Queue.get()` directly on the event loop -- always offload via `asyncio.to_thread` (pre-demo hardening patch)
13. `get_visualizer_state` / `get_visualizer_demo_data` use the cached `_get_db()` singleton -- after switching the active profile, restart uvicorn so the singleton rebinds to the new profile database
14. Background tasks (`_run_scrape_background`, `_run_evaluate_background`) set `TALOS_HEADLESS=1` at entry -- any new background task invoking AIManager must do the same, otherwise an interactive prompt may block a console-less worker thread
15. The `sys.exit` monkey-patch in `_run_scrape_background` is serialized by the module-level `_scrape_task_lock` -- never patch process-global symbols without this lock
16. `DatabaseManager.semantic_search` clamps `top_k` to the loaded embedding count (`min(top_k, len(self._embedding_ids))`) -- keep the clamp when modifying
17. The OpenReview V2 client rejects `get_notes(term=...)` with `TypeError` -- all note queries must route exclusively through `OpenReviewSource._query_notes()` (search_notes -> content query -> TypeError fallback)
18. `AIManager.fast_tier_offline` (session-level latch, v5.15.3) short-circuits a known-offline Fast Edge endpoint (11435) for the remainder of the process lifetime with zero logs -- the legacy `_fast_edge_offline_memo` is retained as a synonym; it resets only on a new AIManager instance, never manually inside a loop
19. FastAPI startup runs through the `lifespan` context manager in `main_api.py` -- never reintroduce `@app.on_event` handlers (deprecated, emits DeprecationWarning)
20. `SynapseClient.synapse_available` (v5.15.3) latches the SYNAPSE bus (port 8000) offline after the first connection refusal -- events are buffered silently to memory + `data/synapse_buffer.jsonl`; `normalize_authors()` prevents false "Unknown Authors"

---

> **Last Updated:** 2026-10-04 (v5.24.0 -- Enterprise Data Vault, Proactive Token-Bucket Rate Limiter & Distributed JSONL Buffer Sync)
> **Project Version:** v5.24.0
> **Total .py modules under src/:** 115 (core 8 + services 12 + ai/drl 10 + ai/optimizers 3 + ai/embeddings 2 + ai/llm 4 + ai/testing 1 + analysis 10 + ingestion 6 + ingestion/sources 18 + search 3 + integration 3 + utils 23 + api 4 + prisma 8 + mcp_server 1)


