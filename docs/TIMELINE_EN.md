# Project TALOS -- Historical Timeline (English)

> **Purpose:** This document serves as the authoritative chronological record of all development, research, and architectural milestones for Project TALOS. Every version bump, new feature, and breaking change is recorded here.
>
> **Rule:** After EVERY version bump, this file MUST be updated with the new milestone and its status.
>
> **Last Updated:** 2026-08-14 (v5.10.1 -- DRL Environment Scaling & Retraining: 17 Action Space)

---

## Phase 31: DRL Environment Scaling & Action Space Expansion (v5.10.1)

### Status: COMPLETED (2026-08-14)

- [x] **DRL environment scaling (`src/ai/drl/talos_env.py` v3.2)** -- state space scaled to 23 dimensions (1 hour + 16 source ratios + 2 streaks + 4 provider ratios) and action space scaled to 17 actions (16 sources + sleep).
- [x] **Canonical 16-source discovery** -- `_load_source_list()` guarantees `openreview` and `openaire` are present and falls back to the full 16-source `ALL_KNOWN_SOURCES` list.
- [x] **DDDQN retraining readiness** -- `drl_agent.py` (v2.1) auto-reconstructs networks for input_dim=23 / action_dim=17; GWO-optimized hyperparameters (LR=3.361e-05, GAMMA=0.6983, EPS_DECAY=0.9202) documented in `drl_trainer.py` (v1.4).
- [x] **Live orchestrator mapping** -- `live_agent_sources.py` (v1.1) and `live_agent_orchestrator.py` (v1.2) align source mapping and the 23-dim `calculate_state()`.
- [x] **DRL environment verification tests** -- `TestDRLEnvironment` in `tests/test_multi_tier.py` asserting `(23,)` observation shape and `Discrete(17)` action space.
- [x] **Sync all 6 code files and 15 documentation files to v5.10.1**.


## Phase 30: Academic Ingestion Expansion - OpenReview & OpenAIRE Integration (v5.10.0)

### Status: COMPLETED (2026-08-14)

- [x] **OpenReview source (`src/ingestion/openreview.py`)** -- `OpenReviewSource` agent for the OpenReview API V2 with authenticated/guest client fallback and peer-review decision/rating summary appended to abstracts.
- [x] **OpenAIRE source (`src/ingestion/openaire.py`)** -- `OpenAIRESource` agent for the OpenAIRE Research Graph API v11.3.0 with optional bearer token and grant/funding metadata appended to abstracts.
- [x] **16-source ingestion** -- `daily_search.py` and `historic_search.py` now run both new sources; `CORESource` restored to the daily pipeline (previously imported but uninstantiated).
- [x] **Config & Env Templates** -- `example.env` gained `OPENREVIEW_USERNAME`, `OPENREVIEW_PASSWORD`, `OPENAIRE_TOKEN`; `requirements.txt` gained `openreview-py`; `config.template.json`/`config.json` gained `openreview_query`, `openaire_query`, and `max_results_config` entries.
- [x] **Dependency map** -- `verify_dependency_map.py` `IMPORT_TO_DOC_MAP` registered the two new source modules.
- [x] **Unit tests** -- `tests/test_openreview_source.py` (13 tests) and `tests/test_openaire_source.py` (21 tests) added for hermetic, mock-first coverage of the new sources.
- [x] **Sync all 6 code files and 15 documentation files to v5.10.0** plus a global header sweep across 72 files in `src/`, `config/`, and `tests/` (Autonomous Red Tester subsystem included).


## Phase 29: Universal Cloud Mesh & Multi-Provider Redundancy Expansion (v5.9.18)

### Status: COMPLETED (2026-08-14)

- [x] **Universal Cloud Mesh (`config/settings.py`)** -- Added `NVIDIA_BASE_URL`, `GROQ_BASE_URL`, `CEREBRAS_BASE_URL`, `GITHUB_MODELS_BASE_URL`, `MISTRAL_BASE_URL`, `OPENROUTER_BASE_URL`, `HF_BASE_URL`, per-provider default models, API key getters, and the `TALOS_CLOUD_PROVIDERS` canonical list (9 providers).
- [x] **OpenAI-compatible provider registry (`src/core/ai_manager.py`)** -- Added `OPENAI_COMPATIBLE_REGISTRY` (8 redundancy providers), dictionary-driven `__init__` with graceful missing-key skipping, unified `_execute_openai_compatible_request()` with independent 5-failure circuit breakers, and registry-driven `_execute_cloud_chain()`.
- [x] **Model Manager Cloud Configuration TUI** -- `select_cloud_models()` renders a Rich table of all 9 providers (Provider Name, Env Key, Status, Default Model, Base URL) with per-provider key/model editing via `CLOUD_PROVIDER_CATALOG` and `get_cloud_provider_rows()`.
- [x] **Config & Env Templates** -- `example.env` gained 6 new provider keys; `config.template.json`/`config.json` `ai_provider_priority` updated to the 10-item local-first list; `failure_threshold` raised to 5.
- [x] **Unit Tests** -- `tests/test_multi_tier.py` (registry initialization, provider discovery, missing-key skip, cascade failover) and `tests/test_model_manager.py` (catalog table) expanded.
- [x] **Sync all 6 code files and 15 documentation files to v5.9.18** (full global header sweep across `src/`, `config/`, `tests/`)


## Phase 28: Universal Rich TUI, Enterprise Logging Upgrade & Global Header Sweep (v5.9.17)

### Status: COMPLETED (2026-08-14)

- [x] **Enterprise Logging (`src/utils/logger.py`)** -- `get_logger(name)` factory with `rich.logging.RichHandler` (emoji-free console) plus `logging.handlers.RotatingFileHandler` to `data/logs/talos_system.log` (10 MB, 5 backups, `%(asctime)s - %(name)s - %(levelname)s - %(message)s`).
- [x] **Universal Rich TUI & Logger Enforcement** -- audited `talos.py`, `model_manager.py`, `research_pivot.py`, `generate_docs.py`, `red_tester.py`: `print()` -> logger, Rich Console/Panel for menus/tables, `questionary` for prompts, removed legacy raw `input()`.
- [x] **Zero Emojis** -- stripped all emojis from `research_pivot.py`; translated inline Greek strings in `generate_docs.py` to English.
- [x] **Global Header Sweep** -- 78 files synced from `Project: TALOS v5.9.15/v5.9.16` to `v5.9.17`.
- [x] **Docker & Launcher Sweep** -- `Dockerfile`, `docker-compose.yml` (`talos:5.9.17`), `requirements.txt`, `docs/DOCKER.md`, `run_talos.bat`, `run_talos.sh`.
- [x] **Sync all 5 code files and 15 documentation files to v5.9.17**


## Phase 27: Autonomous Red Tester Upgrade - Rename, Deep API Fuzzing & Context Truncation (v5.9.16)

### Status: COMPLETED (2026-08-14)

- [x] **Rename `src/ai/testing/autonomous_tester.py` to `red_tester.py`** and `src/api/tester_routes.py` to `red_tester_routes.py` -- entry point `run_red_tester()`, router tag `red_tester`, endpoint prefix `/api/v1/tester` preserved for frontend compatibility.
- [x] **Migrate persistence artifacts** -- `data/tester_q_table.json` to `data/red_tester_q_table.json`, `data/reports/autonomous_tester/` to `data/reports/red_tester/`.
- [x] **Deep API Fuzzing** -- hybrid arm discovery (`_discover_all_targets()`) adds four API fuzzing arms against `http://127.0.0.1:8001` (malformed Synapse webhook JSON, negative paper ID, empty semantic query, invalid scrape source). Graceful rejections (400/404/422) are passes; HTTP 5xx and timeouts are crashes.
- [x] **LLM Context Truncation** -- `_protect_context_window()` clips crash stderr to the last 2,000 characters before Fast Edge LLM diagnosis.
- [x] **Sync all 5 code files and 15 documentation files to v5.9.16**

## Phase 26: RL & Daemon Hardening, Zero-Click Model Provisioning, Silent Fast Boot & Dependency Map Reconciliation (v5.9.15)

### Status: COMPLETED (2026-08-14)

- [x] **Full audit of DRL and daemon subsystems** -- Audited all 10 RL and daemon scripts across `src/ai/drl/`, `src/ai/optimizers/`, and `src/ai/testing/`. Confirmed hour normalization `/24.0`, Gymnasium time-limit truncation, soft updates, GWO canonical formulation, and MAB chaos fuzzer integrity.
- [x] **Reconcile Section 7 Dependency Graph in PROJECT_MAP files** -- Rebuilt Section 7 with the modern `src.*` DDD layout, clearing legacy drift warnings.
- [x] **Silent Fast Boot** -- Removed legacy startup model verification so `talos.py` boots directly into the Rich dashboard.
- [x] **Add Zero-Click local AI model provisioning to launchers** -- `run_talos.bat` and `run_talos.sh` pull Neutrino-8B and Qwen2.5:14b during setup.
- [x] **Create docs/TECH_RADAR_GR.md** -- Full pure Greek translation of the Tech Radar.
- [x] **Sync all 5 code files and 15 documentation files to v5.9.15**

## Phase 25: Docker Infrastructure Fix & Usage Reference (v5.9.14)

### Status: COMPLETED (2026-08-14)

- [x] **Fix stale Docker files and add detailed usage instructions** -- Corrected v5.8.2 headers in `Dockerfile`, `docker-compose.yml`, `.dockerignore`, and `example.env` to v5.9.14. Added a `config.json` bootstrap from `config.template.json`, the `_profiles/` volume, removed the deprecated Compose `version:` key, and defaulted local-model URLs to `host.docker.internal`. Added `docs/DOCKER.md` and corrected the README Docker instructions.

---

## Phase 24: Documentation & Version Sync (v5.9.14)

### Status: COMPLETED (2026-08-04)

- [x] **Sync version strings across all 4 code files and 15 documentation files to v5.9.14** -- `config/settings.py` TALOS_VERSION updated from 5.9.13 to 5.9.14. `talos.py` module docstring updated. `src/api/main_api.py` FastAPI version, description, and startup log message updated. `tests/test_multi_tier.py` assertion and docstring updated. Changelogs (EN, GR) receive v5.9.14 entries. Capabilities documents (MD, HTML) and batch/POSIX launchers already updated by user.
- [x] **Compile checks and pytest verification** -- All 4 changed `.py` files pass `python -m py_compile`. `test_talos_version` assertion passes.

---

## Phase 23: Academic Print Theme (Light Mode) Injection for AST Graphs (v5.9.13)

### Status: COMPLETED (2026-08-02)

- [x] **Implement HTML post-processing in graphify_adapter.py to inject Light/Dark toggle** -- Added `_inject_light_mode_toggle()` helper function that opens the generated `graph.html`, injects a full CSS block defining a `.light-mode` class override on `<body>` (white background, dark text, high-contrast nodes for academic print), and inserts a floating toggle button anchored to the top-right corner. Original dark mode is preserved as default; users toggle with a single click. All CSS uses `!important` to override Graphify's dynamically injected dark styles. Graceful degradation on I/O errors -- the pipeline never fails due to injection failure.
- [x] **Force-sync all 15 documentation files and 5 code files to v5.9.13**

---

## Phase 22: Graphify Output Path Resolution & Auto-Clustering Fix (v5.9.12)

### Status: COMPLETED (2026-08-02)

- [x] **Fix graphify-out path resolution in graphify_adapter.py** -- Graphify outputs ``graphify-out/`` inside the target directory (e.g., ``src/graphify-out/``) rather than the project root. The adapter now resolves the correct source path by joining ``target_dir`` with ``graphify-out``, with a backward-compatible fallback to the project root.
- [x] **Add auto-execution of cluster-only command for HTML/Markdown generation** -- After extraction succeeds, the adapter now automatically spawns a second subprocess running ``python -m graphify cluster-only <target_dir> --no-label``. The ``--no-label`` flag skips LLM community naming calls, preserving 100% air-gapped offline operation. This generates ``GRAPH_REPORT.md`` and assigns numeric community labels without requiring a separate manual command.
- [x] **Force-sync all 15 documentation files and 5 code files to v5.9.12**

---

## Phase 21: Vendored Dependencies Hotfix (v5.9.11)

### Status: COMPLETED (2026-08-02)

- [x] **Add tree-sitter-python and rapidfuzz to requirements.txt** -- Graphify AST engine subprocess failed with `ModuleNotFoundError: No module named 'rapidfuzz'` and missing `tree_sitter_python`. Both added under the "Graphify AST Knowledge Graph" section.
- [x] **Force-sync all 15 documentation files and 5 code files to v5.9.11**

---

## Phase 20: Vendored Graphify AST Integration & Rich Menu Reorganization (v5.9.10)

### Status: COMPLETED (2026-08-02)

- [x] **Add graphify dependencies (tree-sitter, networkx) to requirements.txt**
- [x] **Create src/analysis/graphify_adapter.py referencing vendor/graphify**
- [x] **Reorganize talos.py main menu into visual Rich groups**
- [x] **Force-sync all 15 documentation files and 5 code files to v5.9.10**

---

## Phase 19: Report Path Consolidation & Data Directory Isolation (v5.9.9)

### Status: COMPLETED (2026-08-02)

- [x] **Redirect all reporting outputs in src/analysis/ and autonomous_tester.py to data/reports/**
- [x] **Move existing root reports/ contents to data/reports/ and purge root reports/ directory**
- [x] **Update tester_routes.py to read reports from data/reports/autonomous_tester/**
- [x] **Force-sync all 15 documentation files and 5 code files to v5.9.9**

---

## Phase 1: Architecture & APIs (v5.0 -- v5.6)

- [x] **v5.0.0 -- The AI Core** -- Multi-provider hybrid embeddings, DRL agent (DDDQN), GWO hyperparameter optimization, dynamic N-source environment, 4-layer scoring framework, circuit breaker pattern for AI providers.
- [x] **v5.1.0 -- The Insights UI** -- DRL dashboard with metric cards, agent training status, reward progression visualization, GPU-accelerated training (CuDNN).
- [x] **v5.2.0 -- The Live Agent** -- Onboarding wizard (4-step), research pivot workflow, dynamic DRL stack with 14 academic sources, PDF downloader with Unpaywall integration.
- [x] **v5.2.1 -- Academic Conference** -- Bilingual GUI redesign (English/Greek), CSS theme upgrade, academic conference presentation mode.
- [x] **v5.3.0 -- Auto-Docs** -- 18-language documentation generator, system capabilities reference, universal documentation builder.
- [x] **v5.3.1 -- DRL Live Agent** -- Provider-Aware Orchestration (Gemini/DeepSeek/HuggingFace/Local tracking), cooldown mechanism preventing deterministic loops.
- [x] **v5.3.2 -- Pluggable Networks** -- DRL network architecture extraction, DuelingLSTM as injectable component, future architecture extensibility.
- [x] **v5.3.3 -- Light-Only Theme** -- Dark mode removal, universal documentation rule, all file types covered by progressive documentation standard.
- [x] **v5.3.4 -- Descriptive Names** -- Mythological code names replaced with academic module titles (CHIRON -> Knowledge Path Generator, ORPHEUS -> Citation Network Analyzer, PYTHIA -> Query Translator, APOLLO -> Metadata Enricher).
- [x] **v5.3.5 -- DRL Scientific Integrity** -- GWO v2.0 with real fitness evaluation (not random noise), canonical Grey Wolf Optimizer algorithm (Mirjalili 2014), Batch 1 audit of training/evaluation distribution mismatch.
- [x] **v5.3.6 -- TUI/CLI Hardening** -- Ctrl+C robustness throughout CLI, dead menu option fix, safe_pause() and safe_select() guards, Batch 2 audit.
- [x] **v5.3.7 -- GWO Re-optimization** -- Full 9.5-hour training run, final hyperparameters: LR=3.361e-05, GAMMA=0.6983, EPS_DECAY=0.9202.
- [x] **v5.4.0 -- DDD Migration** -- Domain-Driven Design package layout, all 55 source files relocated to `src/` hierarchy (ai/, analysis/, api/, core/, ingestion/, utils/).
- [x] **v5.4.1 -- Root Cleanup** -- `docs/` and `tools/` directory creation, .gitignore negate patterns for permanent documentation files.
- [x] **v5.5.0 -- FastAPI REST Facade** -- 8 REST endpoints (health, papers, semantic search, scrape/GWO triggers, task status), database path fix to `data/talos_research.db`, 16 Pydantic v2 models.
- [x] **v5.5.1 -- Frontend Developer Experience** -- +2 endpoints: GWO history for Recharts <LineChart> and architecture dependency graph HTML via FileResponse.
- [x] **v5.5.2 -- 100% Ecosystem Coverage** -- +4 endpoints: single-paper AI evaluation, natural-language-to-boolean query translation, top authors aggregation, bulk score recalculation. Total: 14 endpoints.
- [x] **v5.6.0 -- Headless API & Documentation Enforcement** -- BREAKING: Streamlit fully deprecated. Deleted `app.py` (1,175 lines), `.streamlit/`, `tools/_gui_runner.py`. Removed `streamlit` from `requirements.txt`. Sole frontend is React 18 + Tailwind CSS + Shadcn UI. FastAPI upgraded to 15 endpoints (+`/api/v1/capabilities`). Created `docs/SYSTEM_CAPABILITIES_MASTER.md` and `.html` (9-section structured reference). Enforced 12-file documentation sync rule in `.clinerules`. Created `docs/API_HANDOVER_FOTIS.md`, `docs/UX_UI_BLUEPRINT_FOTIS.md`, `docs/IP_PROTECTION_STRATEGY.md`.

---

## Phase 2: Master Standard v2.0 Alignment (v5.7.2)

- [x] **v5.7.2 -- Constitution v2.0 Retrofit** -- Upgraded `.clinerules` from 12-file to 15-file documentation synchronization rule. Added Timeline documents as authoritative historical record (files #8 and #9 in the 15-file canon). Created `docs/TIMELINE_EN.md` (this file) and `docs/TIMELINE_GR.md`.
- [x] **SYNAPSE Event-Driven Protocol** -- Scaffolded `src/integration/synapse_client.py` (EventEmitter class) and `src/api/synapse_routes.py` (FastAPI APIRouter with `POST /api/v1/synapse/webhook`). Integrated Synapse router into `main_api.py`. Port reallocation: TALOS FastAPI now on port 8001 (was 8000), SYNAPSE bus on port 8000.
- [x] **Automated Batch Runner** -- Created `run_talos.bat` at project root with 3-option menu: (1) Full Setup with Conda environment and pip install, (2) Start FastAPI Server on port 8001, (3) Run Test Suite via `pytest -v`. Renamed legacy `tools/start_talos.bat` as archival reference.
- [ ] **Refactor all existing Python files to match the new strict Module-level Docstring standard** -- Apply Section VIII of the Constitution to every `.py` file in `src/`, `tools/`, and root. Each module must begin with the exact format: Module name, Project version, Description (2-4 sentences), Dependencies list.

---

## Phase 3: Multi-Tier Routing, Cross-Platform POSIX & Quality Assurance (v5.7.2)

- [x] **v5.7.2 -- Multi-Tier LLM Routing** -- Implemented `tier` parameter ("fast"|"heavy") in `AIManager._execute_request()`. Fast tier routes to Neutrino-8B via dedicated edge endpoint (127.0.0.1:11435); heavy tier uses standard Ollama (127.0.0.1:11434) with qwen2.5:14b. Environment variables: `FAST_EDGE_MODEL`, `FAST_EDGE_BASE_URL`, `HEAVY_REASONING_MODEL`, `OLLAMA_BASE_URL`. Created `config/settings.py` as canonical configuration hub.
- [x] **Isolated Interim UI Provisioner** -- Created `src/utils/frontend_provisioner.py`. Downloads portable Cherry Studio (CherryHQ/cherry-studio) based on OS into `cherry_ui_isolated/` (gitignored). Auto-generates MCP config JSON for Cherry Studio pointing to `src/mcp_server.py`.
- [x] **Cross-Platform POSIX Launcher** -- Created `run_talos.sh` mirroring `run_talos.bat` with 5 options: (1) Full Setup with virtualenv + pip install, (2) Start FastAPI Server on port 8001, (3) Start MCP Server, (4) Launch Interim UI (Cherry Studio), (5) Run Pytest Suite. `chmod +x` ready for Linux/macOS.
- [x] **Anti-Greeklish Audit** -- Scanned all `*_GR.md` files (PROJECT_MAP_GR, TIMELINE_GR, CHANGELOG_GR, README_GR, ROADMAP_GR, USER_GUIDE_GR). Replaced any transliterated Greeklish text with formal, academic Greek script using proper Unicode characters and accents. Technical terms preserved in English.
- [x] **Unit Tests (Pytest)** -- Created `tests/test_synapse.py` (EventEmitter + webhook route coverage), `tests/test_multi_tier.py` (fast vs. heavy LLM routing logic), `tests/test_provisioner.py` (frontend provisioner OS detection and config generation). All tests pass via `pytest -v`.
- [x] **15-File Documentation Sync** -- Updated version string to v5.7.2 in all 15 canonical documentation files. Documented all v5.7.2 additions in CHANGELOG_EN.md and CHANGELOG_GR.md. Synchronized PROJECT_MAP_EN.md and PROJECT_MAP.md with new modules and dependencies.

---

## Phase 4: Multi-Tier TUI Refactoring & Execution Modes (v5.8.9)

- [x] **v5.8.9 -- Comprehensive Model Manager Refactoring** -- Full audit and refactoring of `src/ai/llm/model_manager.py`. Removed legacy `sys.path` hacks (duplicate `import os, sys`, manual while-loop path climbing); standardized path resolution via `pathlib.Path` to `config/settings.py` and project root. Eliminated all Unicode emojis from banners, sub-menus, and status indicators -- replaced with formal ASCII text badges ([CONNECTED], [OFFLINE], [INSTALLED], [RECOMMENDED], [FITS], [TIGHT], [TOO BIG]). Restructured 5-option menu into 7-option menu supporting three-tier architecture.
- [x] **Implemented Multi-Tier Configuration Functions** -- `select_fast_edge_model()`: Configures FAST_EDGE_MODEL and FAST_EDGE_BASE_URL for CPU-optimized edge inference on port 11435. `select_heavy_model()`: Configures HEAVY_REASONING_MODEL and OLLAMA_BASE_URL for GPU-optimized reasoning on port 11434. Both reuse shared `_browse_and_pick_ollama_model()` and `_pick_quantization()` internal helpers extracted from the former monolithic `select_ollama_model()`. Added `_install_if_needed()` helper for consistent pull-before-save logic. `select_execution_mode()`: Sets TALOS_EXECUTION_MODE to "local" (air-gapped), "hybrid" (local+cloud fallback), or "cloud" (cloud priority), with backward-compatible TALOS_USE_LOCAL and TALOS_ALLOW_CLOUD_FALLBACK key updates.
- [x] **Updated `select_cloud_models()`** -- Now imports default model names from `config/settings.py` (canonical configuration hub) instead of hardcoded strings. Gemini/DeepSeek/HF configuration sections remain unchanged in behavior. Removed unused `time` and `json` imports from the module.
- [x] **Zero Emojis Protocol Enforced** -- All TUI output strings audited and sanitized. `_fits_label()` now returns pure ASCII text badges: `[FITS]`, `[TIGHT]`, `[TOO BIG]`. All section headers (`[CONNECTED]`, `[OFFLINE]`, `[INSTALLED]`, `[RECOMMENDED]`), status lines, and user prompts use formal academic language. No Unicode symbols in any print statement.
- [x] **Unit Test Suite Created** -- `tests/test_model_manager.py` with 29 test cases covering: `check_ollama_alive()` (3 tests), `_categorize_tags()` quantization grouping (11 tests), `_fits_label()` VRAM fitness indicators (6 tests), `.env` key update behavior (3 tests), `get_installed_models()` (2 tests), `get_available_tags()` (2 tests), and path resolution (2 tests). All 29 tests pass with `pytest -v`.
- [x] **Version Bump to v5.8.9** -- `config/settings.py`: Added `TALOS_EXECUTION_MODE` constant with "local"/"hybrid"/"cloud" semantics, `TALOS_VERSION` changed to "5.8.0". `src/api/main_api.py`: App version, description, and startup log updated to v5.8.9 with Multi-Tier LLM mention.
- [x] **15-File Documentation Sync** -- Updated version string to v5.8.9 in all 15 canonical documentation files. Documented v5.8.9 changes in CHANGELOG_EN.md and CHANGELOG_GR.md. Synchronized PROJECT_MAP_EN.md and PROJECT_MAP.md.

---

## Phase 5: Master Launchers, Standalone Daemons & Docker Modernization (v5.8.9 -- v5.8.9)

- [x] **v5.8.9 -- Workspace Sanitation** -- Removed `talos.bat` (legacy launcher). Verified `venv/` absent (uses `.venv` or Conda `talosenv`). `tools/` directory preserved with active scripts.
- [x] **Environment and Configuration Templates Updated** -- `example.env` with complete v5.8.9 key set. `config.template.json` with `ai_models` block. `requirements.txt` reorganized with explicit sections (httpx, mcp, pytest).
- [x] **Docker Infrastructure Modernized** -- `Dockerfile` upgraded to python:3.11-slim, port 8001, HEALTHCHECK at /api/v1/health. `docker-compose.yml` with container `talos_api_v5.8.9`, explicit volumes, `restart: unless-stopped`. `.dockerignore` expanded with venv/, .venv/, cherry_ui_isolated/, frontend_ui/, config.json, docs/, reports/, .pytest_cache/.
- [x] **15-File Documentation Sync (v5.8.9)** -- All version strings bumped to v5.8.9. All "Last Updated" dates set to 2026-08-01. New v5.8.9 entries added to CHANGELOG_EN.md, CHANGELOG_GR.md, TIMELINE_EN.md, TIMELINE_GR.md.

- [x] **v5.8.9 -- 9-Option Master Launchers** -- `run_talos.bat` and `run_talos.sh` expanded from 3-option to 9-option structured menu across three sections: REST API & FRONTEND (Full Setup, FastAPI, MCP Server, Cherry Studio), CLI & STANDALONE DAEMONS (TALOS Terminal CLI, Autonomous Research Daemon `talos_service.py`, Live DRL Agent `talos_live_agent.py --verbose`), TESTING & SYSTEM (Pytest, Exit). Full Setup now includes Frontend Provisioner as step 4/4.
- [x] **Expanded Test Suite (96 Unit Tests)** -- Moved `tools/test_smoke.py` to `tests/test_smoke.py` with emoji-free [PASS]/[FAIL]/[SKIP] labels, hardened `check()` for BaseException/SystemExit propagation, guarded `sys.exit()` behind `__name__`. Updated `tests/test_multi_tier.py` TALOS_VERSION assertion. Total test count: 96 passed, 0 failed.
- [x] **Tools Directory Purge** -- Deleted `tools/start_talos.bat` (replaced by root `run_talos.bat`), `tools/_bump.py`, `tools/_git_status.ps1`. Moved `tools/test_smoke.py` to `tests/`. `tools/_gui_runner.py` and `tools/_git_out.txt` already absent. `tools/` preserved (active `_bump_docs.py` and `_fix_changelogs.py`).
- [x] **16-File Documentation Sync (v5.8.9)** -- Updated version string to v5.8.9 in all 16 canonical documentation files. Documented v5.8.9 changes in CHANGELOG_EN.md and CHANGELOG_GR.md (formal Greek with accents). Updated TIMELINE_EN.md and TIMELINE_GR.md.

---

## Phase 6: Launcher Automation & Cross-Platform Zero-Touch Launch (v5.8.9)

- [x] **v5.8.9 -- Windows Auto-Conda Path Detection** -- `run_talos.bat` scans five common Miniconda/Anaconda installation directories for `Scripts\activate.bat`. Detected path stored in `CONDA_ACTIVATE_PATH` and used via a reusable `:ACTIVATE_CONDA` subroutine. Falls back to standard `conda` command if no activate.bat is found. Solves the common Windows failure mode where `conda` is not globally on PATH.
- [x] **v5.8.9 -- Windows Background Minimized Window Spawning** -- FastAPI (Option 2) and MCP server (Option 3) launch in separate minimized windows via `start "..." /min cmd /c`. Option 4 auto-starts the FastAPI backend chain: (1) launch FastAPI in background, (2) wait 2 seconds, (3) run the frontend provisioner. Main menu returns immediately.
- [x] **v5.8.9 -- POSIX Virtualenv/Conda Detection** -- `run_talos.sh` auto-detects Python environments in priority order: (1) local `.venv/bin/activate`, (2) local `venv/bin/activate`, (3) Conda `talosenv` via dynamic `conda info --base` resolution. Falls back to system Python with a clear warning.
- [x] **v5.8.9 -- POSIX Detached Background Daemons** -- FastAPI (Option 2) and MCP server (Option 3) launch as detached background processes with output redirected to `/dev/null`. Option 4 implements auto-start backend chain: (1) spawn uvicorn in background, (2) sleep 2 seconds, (3) run frontend provisioner. Full feature parity with Windows launcher.
- [x] **v5.8.9 -- Full cross-platform `run_talos.sh` rewrite** -- Complete POSIX launcher with 9-option menu, color-coded terminal output, `set -e` error handling, and per-option `detect_and_activate_env()` calls. Both launchers share identical menu structure and feature set.
- [x] **v5.8.9 -- Force-Sync All 15 Documentation Files** -- All version strings bumped to v5.8.9 across the 15 canonical documentation files. `.clinerules`, `config/settings.py`, `src/api/main_api.py` updated to "5.8.3".

---

## Phase 7: Rich TUI & Model Manager CLI Integration (v5.8.9)

- [x] **v5.8.9 -- Rich TUI Dashboard** -- Replaced all plain `print()` statements in `talos.py` with `rich` library formatting (`Console`, `Panel`, `Table`, `Box`, `Text`). Added dynamic status table at the top of the main menu showing Conda environment, API port (8001), Synapse bus (8000), active execution mode (Air-Gapped Local / Hybrid / Cloud), and active tiers (Fast Edge Neutrino-8B, Heavy Reasoning Qwen-14B, Cloud Provider Gemini/DeepSeek). Menu restructured to 10 options with Model Manager as dedicated option 1.
- [x] **v5.8.9 -- Model Manager CLI Integration** -- Integrated `src/ai/llm/model_manager.py` into `talos.py` main menu as option 1 ("Configure AI Models & Execution Modes"). Calls `model_manager.main()` directly via import instead of subprocess launch, enabling in-process configuration without spawning a child Python process.
- [x] **v5.8.9 -- Zero-Emojis Protocol Enforced Across TUI** -- All Rich-formatted output verified free of Unicode emojis. Professional dark slate/blue color scheme with `box.ROUNDED` panel borders. All status indicators use formal ASCII text.
- [x] **v5.8.9 -- Dependency Update** -- Added `rich` to `requirements.txt` for terminal UI beautification.
- [x] **v5.8.9 -- 15-File Documentation Sync** -- All version strings bumped to v5.8.9 across the 15 canonical documentation files. `config/settings.py`, `src/api/main_api.py` updated to "5.8.4".

---

## Phase 7b: Universal TUI Beautification & Pristine Release Sealing (v5.8.9)

- [x] **v5.8.9 -- TUI Model Name Display Fix** -- Fixed `_build_status_table()` in `talos.py` to display the full raw configuration string for all three active tiers instead of truncating via `split(":")`. The Heavy Reasoning Tier now shows "qwen2.5:14b" instead of "14b". The Fast Edge Tier shows "fermionresearch/Neutrino-8B" instead of "fermionresearch". The Cloud Provider shows the full provider name and model name as configured in `config/settings.py`.
- [x] **v5.8.9 -- Universal Sub-Menu Rich Panel Wrapping** -- All intermediate sub-menu launches (Options 2d-2e Live DRL Agent/Autonomous Process, 2l Compare Baselines, 3 Metadata Enrichment, 4 PYTHIA Query Translator, 6-7 Baseline Reports, 9 Docs Generator) now display contextual informational panels with color-coded borders (cyan/yellow/green/magenta) before subprocess launch. The `_build_info_panel()` helper constructs styled `rich.panel.Panel` objects with `box.ROUNDED` borders.
- [x] **v5.8.9 -- Rich Search Results Table** -- Added `_build_results_table()` helper for building styled paper search result tables with columns: ID (cyan), Title (white/bold, folded at 100 chars), Source (magenta), Year (yellow), Overall Score (emerald/bold). Elite papers (overall_score >= 7) highlighted in gold.
- [x] **v5.8.9 -- Sci-Fi Terminal Aesthetics** -- All `run_script()` output now uses `rich.console` for launch/completion/cancellation/error messages in styled colors (cyan/yellow/red/dim green). Replaced plain `print()` for script lifecycle messages with `console.print()` using Rich markup.
- [x] **v5.8.9 -- Pristine Release Sealing** -- All 15 canonical documentation files force-synced to v5.8.9. Version strings updated in `config/settings.py`, `src/api/main_api.py`, `tests/test_multi_tier.py`, `.clinerules`, and all 14 documentation files. Test assertion in `test_talos_version` expects "5.8.5".

---

## Phase 8: Enterprise TUI Refactoring, Safety Locks & Navigation Audit (v5.8.9)

## Phase 8b: Sub-script Path Audit & Config Resolution Fix (v5.8.9)

### Status: COMPLETED (2026-08-01)

- [x] **v5.8.9 -- Audited all `src/` sub-scripts for fragile config.json relative path resolution** -- 17 files identified with `os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'config.json'))` patterns that break when scripts are nested deeper than one level under project root.
- [x] **v5.8.9 -- Refactored config.json path resolution to use canonical `_P`-based project root detection** -- All 17 files now resolve the project root by walking upward from `__file__` until `talos.py` is found (`_P` variable defined at module top). Fallback to `config.template.json` if `config.json` is absent.
- [x] **v5.8.9 -- Files refactored** -- `src/analysis/`: citation_analyzer.py, author_profiler.py, architecture_intelligence_report.py, knowledge_path_generator.py. `src/ingestion/`: daily_search.py, historic_search.py, grey_literature_miner.py, pdf_downloader.py, zotero_connector.py, metadata_enricher.py, data_enricher.py. `src/utils/`: interactive_dashboard.py, reevaluate_database.py. `src/ai/`: embeddings/embedding_generator.py, llm/query_translator.py, drl/talos_env.py, drl/talos_live_agent.py.
- [x] **v5.8.9 -- Version bump** -- `config/settings.py` TALOS_VERSION = "5.8.7", `src/api/main_api.py` version and FastAPI metadata, `tests/test_multi_tier.py` test_talos_version assertion.
- [x] **v5.8.9 -- py_compile verification** -- All 17 changed files + main_api.py pass `python -m py_compile`.
- [x] **v5.8.9 -- 15-File Documentation Sync** -- All version strings bumped to v5.8.9 across 15 canonical files.


- [ ] **v5.8.9 -- Enterprise TUI Refactoring & Navigation Safety Locks** -- Complete visual refactoring of `src/ai/llm/model_manager.py` using the `rich` library across ALL sub-menus (Fast Tier, Heavy Tier, Cloud Config, Execution Mode, Embedding Selection, Quantization Selector). Implemented enterprise-grade navigation safety: explicit Cancel/Back choices in every sub-menu, and a `_confirm_setting_change()` helper with `rich.panel.Panel` confirmation summary before any `.env` write operation. Rich Tables for model selection with columns: Model Name, Est. Size, VRAM Headroom Status, Installation State. Quantization variants rendered in structured bit-depth groups. Execution Mode selector displays informational comparison panel. Cloud Configuration displays provider status and key presence in structured panels. Zero Emojis Protocol enforced across all new output.
- [ ] **v5.8.9 -- Sub-Menu Navigation Guardrails** -- Every sub-menu (Fast Edge, Heavy Reasoning, Cloud Config, Execution Mode, Embedding Selection) includes explicit `[Cancel / Return to Main Menu]` choice. Graceful return without changes or exceptions.
- [ ] **v5.8.9 -- Unit Test Expansion** -- Updated `tests/test_model_manager.py` with tests for `_confirm_setting_change()` helper, sub-menu cancellation flows, and rich table rendering. All tests pass via `pytest -v`.
- [ ] **v5.8.9 -- 15-File Documentation Sync** -- All version strings bumped to v5.8.9 across 15 canonical files. `config/settings.py`, `src/api/main_api.py`, `tests/test_multi_tier.py` updated.

---

## Phase 10: Autonomous System Tester (RL & LLM-Driven CI/CD) (v5.9.0)

- [x] **Create `src/ai/testing/autonomous_tester.py` with Non-Stationary MAB and LLM-as-a-Judge** -- Non-Stationary Epsilon-Greedy Multi-Armed Bandit (epsilon=0.2, alpha=0.1) stress-tests 4 system components (FastAPI Server, MCP Server, Daily Search, Citation Analyzer) via subprocess with 5-second timeout. Crash stderr sent to Fast Edge LLM (tier="fast") for two-sentence diagnosis. Rewards: +50 (crash), -1 (pass). Q-table persisted at `data/tester_q_table.json`. Crash reports in `reports/autonomous_tester/CRASH_REPORT_{timestamp}.md`.
- [x] **Implement Gorgeous Rich TUI Formatting** -- Rich Spinners, red crash Panels, yellow AI Diagnosis Panels, green PASS confirmations, color-coded Q-Table (Component Fragility: STABLE/LOW/MODERATE/HIGH_FRAGILITY). Synapse events emitted on each test cycle via `synapse_client`.
- [x] **Create `src/api/tester_routes.py` and integrate into `main_api.py`** -- FastAPI APIRouter with `GET /api/v1/tester/status` (Q-table with fragility classifications) and `GET /api/v1/tester/reports` (crash report listing). Pydantic v2 models. Endpoint count: 16 -> 18.
- [x] **Update `talos.py`, `run_talos.bat`, and `run_talos.sh`** -- Autonomous System Tester as menu option 6 (talos.py, new TESTING & CI/CD section) and option 8 (run_talos.bat/sh). Menu expanded: 10->11 options (talos.py), 9->10 options (launchers).
- [x] **Add 'Code Version Synchronicity Rule' to `.clinerules`** -- New CRITICAL rule mandating exact version synchronization across 5 code files (talos.py, run_talos.bat, run_talos.sh, config/settings.py, src/api/main_api.py) during any version bump.
- [x] **Force-Sync All 15 Documentation Files and 5 Code Files to v5.9.0**

## Phase 8c: Resilient Ingestion & Elsapy Safeguard (v5.8.9)

### Status: COMPLETED (2026-08-01)

- [x] **v5.8.9 -- Graceful Import Degradation for elsevier_source.py** -- Wrapped `from elsapy.elsclient import ElsClient`, `from elsapy.elssearch import ElsSearch`, and `from elsapy.elsdoc import AbsDoc` in a `try...except ImportError:` block. Module-level flag `ELSAPY_AVAILABLE` set to `False` if import fails. In `ElsevierSource.__init__()`, checks `ELSAPY_AVAILABLE` before proceeding; logs warning `"elsapy library is not installed. Skipping Elsevier source."` and sets `self.enabled = False` gracefully. Prevents `ModuleNotFoundError` from crashing the 14-source scraping pipeline.
- [x] **v5.8.9 -- Graceful Import Degradation for zotero_connector.py** -- Wrapped `from pyzotero import zotero` in a `try...except ImportError:` block. Module-level flag `PYZOTERO_AVAILABLE` set to `False` if import fails. In `main()`, checks `PYZOTERO_AVAILABLE` at entry; logs warning `"pyzotero library is not installed. Skipping Zotero Bridge."` and returns cleanly.
- [x] **v5.8.9 -- requirements.txt Verification** -- `elsapy` and `pyzotero` already present under the Academic APIs section (lines 23, 25).
- [x] **v5.8.9 -- Version Bump** -- `config/settings.py` TALOS_VERSION = "5.8.8", `src/api/main_api.py` app version and FastAPI metadata, `tests/test_multi_tier.py` test_talos_version assertion expects "5.8.8".
- [x] **v5.8.9 -- py_compile Verification** -- Both `elsevier_source.py` and `zotero_connector.py` pass `python -m py_compile`.
- [x] **v5.8.9 -- 15-File Documentation Sync** -- All version strings bumped to v5.8.9 across the 15 canonical documentation files. `.clinerules`, `config/settings.py`, `src/api/main_api.py`, `tests/test_multi_tier.py` updated.

---

## Phase 11: Ultimate TUI UX, LLM Focus Summarization & Advanced Execution Modes (v5.9.1)

- [x] **v5.9.1 -- LLM-Based Active Focus Summarization** -- After Query Translator generates boolean queries, a Fast Edge LLM call summarizes the research goal into a 6-10 word title saved as `active_focus_summary` in `config.json`. The TUI status table displays this clean summary in bold bright green instead of truncating the raw system prompt at 65 characters.
- [x] **v5.9.1 -- 4-Way Execution Mode Matrix** -- Refactored `model_manager.py` `select_execution_mode()` to offer 4 distinct routing combinations using a gorgeous Rich Table: (1) Pure Local (Fast: Local CPU | Heavy: Local GPU), (2) Edge-to-Cloud Hybrid (Fast: Local CPU | Heavy: Cloud API), (3) Cloud-to-Edge Hybrid (Fast: Cloud API | Heavy: Local GPU), (4) Pure Cloud (Fast: Cloud API | Heavy: Cloud API). New `.env` variables `TALOS_FAST_ROUTING` and `TALOS_HEAVY_ROUTING` allow independent per-tier routing configuration.
- [x] **v5.9.1 -- 100% Rich Sub-Menu Migration in model_manager.py** -- All remaining plain `print()` statements in `model_manager.py` sub-menus (Fast Edge Tier, Heavy Reasoning Tier, Cloud Config, Execution Mode, Embedding Selection) replaced with `rich.panel.Panel` and `rich.table.Table` components.
- [x] **v5.9.1 -- Force-Sync All 15 Documentation Files and 5 Code Files to v5.9.1**

---

## Phase 12: Dynamic Focus, Interactive Fallbacks & Capabilities Rewrite (v5.9.3)

### Status: COMPLETED (2026-08-01)

- [x] **v5.9.3 -- Purge Legacy Interactive Startup Prompts** -- Removed the legacy `questionary` prompts asking "Where to run AI calls? LOCAL/CLOUD" from `talos.py` `main_menu()`. TALOS now reads `TALOS_USE_LOCAL` from `.env` directly. Silent initialization with zero user interaction.
- [x] **v5.9.3 -- Dynamic Focus Summarization on Startup** -- New `_maybe_generate_focus_summary()` in `talos.py`. If `config.json` lacks `active_focus_summary` but has `user_research_goal` or any `*_query` keys, a Fast Edge LLM call generates a 6-10 word title, saves it, and displays it in the TUI header.
- [x] **v5.9.3 -- Interactive Runtime Cloud Fallback in AIManager** -- New `_interactive_cloud_fallback()` method. Catches `ConnectionError` in `_execute_fast_tier_request`. Uses `sys.stdin.isatty()` to check interactivity. If interactive, prompts with `questionary` to fallback to cloud. Non-interactive sessions fail gracefully.
- [x] **v5.9.3 -- Exhaustive Capabilities Sync Rule** -- Added to `.clinerules` as CRITICAL rule. Mandates that during every version bump, the AI must scan the codebase and rewrite `SYSTEM_CAPABILITIES_MASTER.md` and `.html` to cover 100% of all endpoints, agents, routing matrices, MCP tools, Synapse events, and RL components.
- [x] **v5.9.3 -- Exhaustive Capabilities Rewrite** -- Completely rewrote `docs/SYSTEM_CAPABILITIES_MASTER.md` and `.html` as ultra-detailed technical whitepapers covering: 18 REST API endpoints, MCP server tools, Synapse event types and payloads, DDDQN + GWO + Autonomous Tester Non-Stationary MAB, 4-Way Execution Mode Matrix, all 14 ingestion sources, all analysis modules, and system constants.
- [x] **v5.9.3 -- Force-Sync All 15 Documentation Files and 5 Code Files to v5.9.3** -- All version strings updated. Test assertion updated in `tests/test_multi_tier.py`. All 20 multi-tier tests pass.

---

## Phase 13: Conda Env Detection Hotfix (v5.9.3)

### Status: COMPLETED (2026-08-01)

- [x] **v5.9.3 -- Conda Environment Detection Hotfix** -- Updated `_build_status_table()` in `talos.py` to use `sys.prefix` fallback for Conda environment detection. When `CONDA_DEFAULT_ENV` is not set (common when running via VS Code or direct Python executable path), the script now extracts the environment name from `os.path.basename(sys.prefix)` if `"envs"` is in `sys.prefix`, or falls back to `sys.base_prefix != sys.prefix` / `hasattr(sys, "real_prefix")` for virtualenv detection. The status table no longer displays "N/A" when running in a properly activated Conda environment via a path-executed Python interpreter.
- [x] **v5.9.3 -- Force-Sync All 15 Documentation Files and 5 Code Files to v5.9.3** -- All version strings updated. Test assertion updated in `tests/test_multi_tier.py`.

---

## Phase 14: Advanced 2D Execution Matrix & Fallback Routing (v5.9.4)

### Status: COMPLETED (2026-08-01)

- [x] **v5.9.4 -- 2D Execution Matrix (Network x Hardware Strategies)** -- Replaced the legacy `TALOS_EXECUTION_MODE` with a richer 2D model. New `.env` variables: `TALOS_NETWORK_STRATEGY` (strict_local | local_first | cloud_first | strict_cloud) and `TALOS_HARDWARE_STRATEGY` (cpu_only | gpu_only | cpu_gpu_split). Network strategy controls air-gapped vs. cloud dependency and cross-environment fallback behavior. Hardware strategy controls CPU/GPU endpoint selection when running locally.
- [x] **v5.9.4 -- Refactored TUI Execution Mode Wizard in model_manager.py** -- `select_execution_mode()` rewritten as a 2-step `questionary.select` wizard. Step 1: Network Strategy with Rich table comparing 4 options. Step 2: Hardware Strategy with Rich table comparing 3 options. Summary confirmation panel with explicit Cancel/Back guardrails on both steps.
- [x] **v5.9.4 -- Overhauled AIManager Routing Logic** -- `_execute_request()` rewritten to use `_resolve_strategies()` for the 2D matrix. New methods: `_execute_local_strategy()` (hardware-aware: cpu_only/gpu_only/cpu_gpu_split), `_execute_ollama_http()` (unified local HTTP POST for CPU edge and GPU Ollama), `_execute_cloud_chain()` (cloud-only execution skipping local), `_execute_legacy_request()` (backward compat). Automatic cross-environment fallback: local_first catches ConnectionError and reroutes to cloud with [WARNING]; cloud_first reroutes to local on any cloud failure with [WARNING]. strict_local and strict_cloud never cross the boundary. Legacy `TALOS_FAST_ROUTING`/`TALOS_HEAVY_ROUTING` still respected as fallback.
- [x] **v5.9.4 -- Updated TUI Status Table in talos.py** -- `_build_status_table()` now displays the 2D Execution Matrix as "Network Strategy / Hardware Strategy" (e.g., "Strict Local / CPU+GPU Split") using human-readable labels from `config/settings.py` constants.
- [x] **v5.9.4 -- Force-Sync All 15 Documentation Files and 5 Code Files to v5.9.4** -- All version strings updated. Test assertion updated in `tests/test_multi_tier.py`.

---

## Phase 16: Data Directory Consolidation & Full-Repo Dynamic Target Discovery (v5.9.7)

### Status: COMPLETED (2026-08-01)

- [x] **Relocate REPORTS_DIR to data/reports/autonomous_tester/** -- Changed `REPORTS_DIR` from `reports/autonomous_tester/` (root) to `data/reports/autonomous_tester/` in `src/ai/testing/autonomous_tester.py` and `src/api/tester_routes.py`. All runtime-generated crash reports now reside under `data/`, ensuring a clean project root and proper Git exclusion via `.gitignore`.
- [x] **Implement _discover_all_python_targets()** -- Replaced the hardcoded 4-target TARGET_ARMS list with a dynamic file scanner that walks `src/analysis/`, `src/ingestion/`, `src/ai/`, `src/utils/`, `src/core/`, and `src/api/`, discovering all non-`__init__.py` Python files as test arms. Each arm is invoked with `--help` for fast subprocess exit. The autonomous tester now scales from 4 to 70+ arms covering the entire `src/` codebase.
- [x] **Q-Table reconciliation on launch** -- `run_autonomous_tester()` reconciles the persisted Q-table (if any) against the current arm count, preserving existing Q-values for arms that still exist and zero-initializing new arms.
- [x] **Force-Sync All 15 Documentation Files and 5 Code Files to v5.9.7**

## Phase 17: IEEE Computer Society WEIGD Fund Badging & v5.9.7 Release (2026-08-01)

### Status: COMPLETED (2026-08-01)

- [x] **Implement IEEE CS two-tone Rich color block badge in talos.py status header** -- Two-tone text badge using official IEEE brand colors (#006699 and #002855) displayed prominently at the top of the Rich terminal dashboard header panel.
- [x] **Add IEEE CS Shields.io badge to README.md and SYSTEM_CAPABILITIES_MASTER.md** -- Official Shields.io badge linking to IEEE Computer Society website with IEEE logo.
- [x] **Add styled CSS IEEE badge to SYSTEM_CAPABILITIES_MASTER.html** -- CSS pill badge with #006699 and #002855 background colors stating project support.
- [x] **Update CITATION.cff with IEEE Computer Society grant metadata** -- Funding section with grant type, title, and message recognizing the WEIGD Student Support Fund (2026).
- [x] **Force-sync all 15 documentation files and 5 code files to v5.9.7** -- Version strings updated in talos.py, run_talos.bat, run_talos.sh, config/settings.py, and src/api/main_api.py. All 15 canonical documentation files synchronized.

## Phase 18: Clickable Terminal Hyperlinks & Local-to-Local Fallback (v5.9.8)

### Status: COMPLETED (2026-08-02)

- [x] **Implement Rich [link=file:///...] hyperlinks in autonomous_tester.py and talos.py** -- `_make_clickable_path()` helper converts file paths to Rich terminal hyperlinks with forward slashes for CTRL+CLICK navigation. Crash report paths, Q-table paths, and reports directories are now clickable in the terminal.
- [x] **Fix AIManager fast-tier fallback to attempt local Ollama (11434) before cloud** -- When the fast edge CPU tier (port 11435) fails with a ConnectionError, `_execute_ollama_http()` now automatically falls back to the local GPU Ollama endpoint (port 11434) FIRST, preserving air-gapped operation. Only if both local endpoints fail does it attempt cloud fallback. Logs `[WARNING] Fast tier (11435) offline. Falling back to local Ollama (11434)...` and `[RECOVERY]` on successful GPU fallback.
- [x] **Force-sync all 15 documentation files and 5 code files to v5.9.8** -- Version strings updated in talos.py, run_talos.bat, run_talos.sh, config/settings.py, tests/test_multi_tier.py, and src/api/main_api.py.

---

## Phase 15: Distributed Ecosystem (Future -- v6.0.0+)

- [ ] **v6.0.0 -- PostgreSQL + pgvector Migration** -- Replace SQLite with PostgreSQL for concurrent access and production-grade vector similarity search.
- [ ] **v6.1.0 -- Local RAG Pipeline** -- Ollama + Chroma integration for chat-with-papers, PDF ingestion, and knowledge graph construction.
- [ ] **v6.2.0 -- Cross-Platform Frontend** -- Flutter desktop/mobile application (Windows, Linux, macOS, iOS, Android).
- [ ] **v6.3.0 -- Advanced Visualization** -- Three.js / Deck.gl for 3D clustering, citation network graphs, and timeline animations.
- [ ] **v6.4.0 -- Zero-Touch Deployment** -- PyInstaller standalone `.exe` build, Docker Swarm orchestration, Kubernetes Helm charts.

---

> **Project TALOS** -- From Aggregator to Autonomous Research Architect.
> Built in Kalamata, Greece.
> (C) 2026 Christos Smarlamakis. All rights reserved.
