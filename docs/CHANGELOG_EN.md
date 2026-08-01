# Changelog - Project TALOS

All notable changes to the TALOS project will be documented in this file. The project adheres to [Semantic Versioning](https://semver.org/).

## [v5.9.0] - 2026-08-01 -- Autonomous System Tester (RL-Driven, LLM-Judged)

### Added
- **Autonomous System Tester (RL-Driven Chaos Engineering)** (`src/ai/testing/autonomous_tester.py`, 390 lines): Non-Stationary Multi-Armed Bandit with Epsilon-Greedy (epsilon=0.2) and constant step-size Alpha (0.1). Stress-tests 4 TALOS system components (FastAPI Server, MCP Server, Daily Search, Citation Analyzer) via subprocess execution with 5-second timeout per cycle. If a target crashes, stderr is sent to the Fast Edge LLM (tier="fast") for a two-sentence diagnosis. Results visualized via Rich TUI (Spinners, red crash Panels, yellow AI Diagnosis Panels, green PASS confirmations, color-coded Q-Table). Q-table persisted as JSON at `data/tester_q_table.json`. Timestamped Markdown crash reports saved to `reports/autonomous_tester/CRASH_REPORT_{timestamp}.md`. Synapse event emitted on each test cycle via `synapse_client`. Reward signal: +50 for crash, -1 for pass. Standalone execution: `python src/ai/testing/autonomous_tester.py [cycles]`.
- **Autonomous System Tester REST API** (`src/api/tester_routes.py`, 200 lines): FastAPI APIRouter with prefix `/api/v1/tester`. `GET /api/v1/tester/status` returns current Q-table with per-arm Q-values and fragility classifications (STABLE/LOW/MODERATE/HIGH_FRAGILITY). `GET /api/v1/tester/reports` lists available Markdown crash reports sorted by timestamp descending. Pydantic v2 models: `ArmStatus`, `TesterStatus`, `CrashReportEntry`, `TesterReports`. File-system-based (read-only), restart-safe design.
- **TALOS Terminal CLI -- Option 6 (Autonomous System Tester)**: Integrated into `talos.py` 11-option menu under new "TESTING & CI/CD" section. Prompts user for cycle count (default 10). Calls `run_autonomous_tester()` directly via import.
- **Batch/POSIX Launcher Integration**: `run_talos.bat` option 8 and `run_talos.sh` option 8 launch `python src/ai/testing/autonomous_tester.py` with auto-environment activation.
- **Code Version Synchronicity Rule** (`.clinerules`): New CRITICAL rule mandating exact version string synchronization across 5 code files (`talos.py`, `run_talos.bat`, `run_talos.sh`, `config/settings.py`, `src/api/main_api.py`) during any version bump.

### Changed
- **FastAPI endpoint count**: 16 -> 18 (added `GET /api/v1/tester/status` and `GET /api/v1/tester/reports` via `app.include_router(tester_router)`).
- **`talos.py` menu restructured**: 10-option -> 11-option. New Section "TESTING & CI/CD" with Option 6 (Autonomous System Tester). Options 7-11 shifted: Baseline Standard (7), Baseline Academic (8), DRL Status (9), Docs Generator (10), Exit (11).
- **`run_talos.bat` and `run_talos.sh`**: 9-option -> 10-option. Autonomous System Tester as Option 8. Test Suite shifted to Option 9, Exit to Option 10.
- **Version strings synced across 5 code files and 15 documentation files** to v5.9.0.
- **Descriptive naming enforcement**: "PYTHIA" references replaced with "Query Translator" in talos.py menu text. "Argus" references removed in favor of "Autonomous Tester".
- **`test_multi_tier.py`**: `test_talos_version` assertion updated from "5.8.9" to "5.9.0".

### Verification
- All 7 changed `.py` files pass `python -m py_compile`.
- Zero emojis protocol enforced across all new code.

---

## [v5.8.9] - 2026-08-01 -- Full Ecosystem Deployment, Multi-Tier LLM, and TUI Mastery

### Added
- **Rich Terminal UI Dashboard**: Full Rich TUI refactoring in `talos.py`. Replaced all plain `print()` statements with `rich` library formatting (`Console`, `Panel`, `Table`, `Box`, `Text`). Dynamic status table at main menu header showing Conda environment, API port (8001), Synapse bus (8000), execution mode (Air-Gapped Local / Hybrid / Cloud), active LLM tiers (Fast Edge, Heavy Reasoning, Cloud Provider), and Active Research Focus (from config.json). 10-option menu restructured. `_build_info_panel()` and `_build_results_table()` helper functions for consistent Sci-Fi terminal aesthetics. Elite papers (score >= 7) highlighted in gold.
- **Active Research Focus Display** (v5.8.9): `_build_status_table()` reads `user_research_goal` from config.json, truncates at 65 chars, displays in bright green in the header status panel.
- **Interactive View & Pivot Research Focus** (v5.8.9): Option 4 refactored into interactive workflow. Shows raw research goal preview Panel, existing Boolean query preview (first 5 of N), and 3-action sub-menu: Pivot to New Goal (runs Query Translator in-place with config.json update), View All 14 Queries (Rich Table), or Return.
- **Model Manager CLI Integration**: `talos.py` menu option 1 calls `src.ai.llm.model_manager.main()` directly via import instead of subprocess launch, enabling in-process configuration.
- **Native MCP Server** (`src/mcp_server.py`, 269 lines): Official MCP (Model Context Protocol) Server using `MCPServer` from MCP SDK v2.0.0 with stdio transport. Four MCP tools: `talos_system_status`, `talos_semantic_search`, `talos_get_paper_details`, `talos_trigger_scrape`. All delegate to TALOS FastAPI backend via HTTP. Clean decoupled architecture with `TALOS_API_BASE` and `TALOS_MCP_TIMEOUT` configuration.
- **MCP Server Unit Test Suite** (`tests/test_mcp_server.py`, 334 lines, 27 tests): `TestMCPServerRegistration`, `TestTalosSystemStatus`, `TestTalosSemanticSearch`, `TestTalosGetPaperDetails`, `TestTalosTriggerScrape`, `TestConfiguration`. Full HTTP mocking.
- **SYNAPSE Event-Driven Protocol** (`src/integration/synapse_client.py`, 310 lines): `EventEmitter` class with thread-safe, non-blocking JSON event dispatch to the SYNAPSE bus at `http://localhost:8000/api/v1/events`. Valid event types: `paper_discovered`, `paper_evaluated`, `search_completed`, `gwo_optimized`, `agent_step`, `agent_episode_end`. Each event carries event_id (UUID4), timestamp (ISO 8601), event_type, source ("talos"), payload. Module-level convenience singleton: `synapse_emitter`.
- **SYNAPSE Webhook Receiver** (`src/api/synapse_routes.py`, 200 lines): FastAPI APIRouter exposing `POST /api/v1/synapse/webhook`. Pydantic v2 models for `trigger_search`, `trigger_evaluation`, `get_status`, `shutdown` commands. Command handler registry with `register_handler()`.
- **Timeline Documentation System**: `docs/TIMELINE_EN.md` and `docs/TIMELINE_GR.md` -- authoritative historical records of all TALOS development milestones. Phases 1-3 documented.
- **Multi-Tier LLM Routing Architecture**: `config/settings.py` (NEW, 113 lines) as canonical configuration hub. Defines `FAST_EDGE_MODEL` (fermionresearch/Neutrino-8B), `FAST_EDGE_BASE_URL` (http://127.0.0.1:11435/v1), `HEAVY_REASONING_MODEL` (qwen2.5:14b), `OLLAMA_BASE_URL` (http://127.0.0.1:11434). `src/core/ai_manager.py` v3.9: Added `tier` parameter ("fast"|"heavy"). Fast tier calls new `_execute_fast_tier_request()` via HTTP POST to FAST_EDGE_BASE_URL. Heavy tier uses standard provider chain. Supports three execution modes: local (air-gapped), hybrid (local + cloud fallback), cloud (cloud + local fallback). `DEFAULT_TIER` configurable via `TALOS_DEFAULT_TIER`.
- **Cross-Platform POSIX Launcher** (`run_talos.sh`, 525 lines): Full parity with run_talos.bat. Auto-detects virtualenv (.venv/ or venv/) or Conda environments. Background servers as detached POSIX daemons with Fermion auto-start support.
- **Automated Batch Runner** (`run_talos.bat` v5.8.9): Expanded from 3-option to 9-option structured menu across three sections: REST API & Frontend (Full Setup, FastAPI Server port 8001, MCP Server, Interim UI), CLI & Daemons (TUI, Autonomous Research, Live DRL Agent), Testing & System (Test Suite, Exit). Auto-Conda path detection scanning 5 common installation directories. Auto-start Fermion CPU daemon when FAST_EDGE_MODEL contains "Neutrino" or "local".
- **Expanded Test Suite**: 96 unit tests (up from 29). `test_smoke.py` moved from `tools/` to `tests/` with emoji-free [PASS]/[FAIL]/[SKIP] labels. `test_synapse.py` (21 tests), `test_multi_tier.py` (20 tests), `test_provisioner.py` (23 tests), `test_mcp_server.py` (27 tests).
- **Isolated Interim UI** (`src/utils/frontend_provisioner.py`, NEW): Downloads portable Cherry Studio based on OS into `cherry_ui_isolated/`. Auto-generates MCP config JSON. Public API: `get_os_name()`, `resolve_target_dir()`, `generate_mcp_config()`, `download_cherry_studio()`, `provision_full()`.
- **Dependency**: `rich` library added to `requirements.txt` for terminal UI beautification.

### Changed
- **Constitution v2.0** (`.clinerules`): Upgraded from 12-file rule to 8-Point Master Initialization Standard including: ZERO EMOJIS PROTOCOL (Point I), 100% AIR-GAPPED & LOCAL-FIRST (Point II), HARDWARE-AWARE VRAM CONTAINMENT (Point III), STRICT LINEAR EXECUTION & TIMELINE TRACKING (Point IV), VERIFICATION-FIRST WORKFLOW (Point V), MANDATORY 15-FILE DOCUMENTATION SYNCHRONICITY RULE (Point VI, supersedes prior 12-file rule), SYNAPSE INTEROPERABILITY PROTOCOL (Point VII), STRICT IN-CODE DOCUMENTATION STANDARDS (Point VIII).
- **15-File Documentation Synchronicity Rule**: Canonical set expanded from 12 to 15 files. Added Timeline documents (EN+GR) and updated all version references. The 15 files are: `.clinerules`, `README.md`, `ROADMAP.md`, `CHANGELOG_EN.md`, `CHANGELOG_GR.md`, `PROJECT_MAP.md`, `PROJECT_MAP_EN.md`, `TIMELINE_EN.md`, `TIMELINE_GR.md`, `API_HANDOVER_FOTIS.md`, `UX_UI_BLUEPRINT_FOTIS.md`, `IP_PROTECTION_STRATEGY.md`, `SYSTEM_CAPABILITIES_MASTER.md`, `SYSTEM_CAPABILITIES_MASTER.html`, `TECH_RADAR.md`.
- **Port Reallocation** (`src/api/main_api.py`): Port 8000 -> 8001. SYNAPSE event bus occupies port 8000. Host 0.0.0.0 -> 127.0.0.1 (local dev default). Endpoint count 15 -> 16 (added Synapse webhook).
- **Docker Modernization** (v5.8.9): `Dockerfile` base image `python:3.10-slim` -> `python:3.11-slim`. Exposed port 8001 (was 5000+8501). `HEALTHCHECK` at `/api/v1/health`. CMD changed to uvicorn on port 8001. Streamlit multi-start logic removed. `docker-compose.yml`: Service renamed to `talos_api`, container `talos_api_v5.8.9`. Port mapping `8001:8001`. Volumes changed to explicit `./data`, `./models`, `./logs`. `restart: unless-stopped`.
- **Environment & Configuration Templates** (`example.env`, `config.template.json`, `requirements.txt`): Full v5.8.9 key set. `config.template.json` added `ai_models` block. `requirements.txt` reorganized with explicit sections.
- **Project Maps Updated**: `PROJECT_MAP.md` and `PROJECT_MAP_EN.md` updated with Synapse Protocol, MCP Server, Multi-Tier LLM routing. File count 67 -> 69.
- **Version Strings** across all entry points: `config/settings.py` TALOS_VERSION -> "5.8.9", `src/api/main_api.py` app.version -> "5.8.9", `talos.py`, `run_talos.bat`, `run_talos.sh`, and all 15 documentation files synced.

### Fixed
- **TUI Status Panel Model Name Display** (v5.8.9): `_build_status_table()` now displays full raw configuration strings for all three active tiers instead of truncating via `split(":")`. Heavy Reasoning Tier shows "qwen2.5:14b" (was "14b"). Fast Edge Tier shows "fermionresearch/Neutrino-8B" (was "fermionresearch").
- **SQLite Column Count Mismatch**: `database_manager.py` `store_embeddings_batch()` had 23 values for 22 columns -- fixed parameter alignment.
- **Fast Tier Connection Refused Fallback**: `ai_manager.py` `_execute_fast_tier_request()` properly returns None on connection error, allowing provider chain fallback.
- **Model Dimension Mismatch Crash**: `drl_agent.py` `load()` now pre-checks saved state_dim/action_dim before `load_state_dict()`, recreates networks if dimensions differ.
- **Hour Normalization Inconsistency**: `talos_env.py` `/23.0` -> `/24.0` to match `talos_live_agent.py`.
- **8 Source Class Names Broken**: `live_agent_sources.py` auto-detects class names via module scanning instead of `.capitalize()` guessing.
- **Local Model Verification Hardcoded**: `ai_manager.py` `_ensure_local_model()` now reads `LOCAL_MODEL_NAME` and `LOCAL_EMBEDDING_MODEL` from `.env`.
- **Save Path Mismatch**: `drl_trainer.py` and `talos_live_agent.py` unified to `dddqn_trained.pth`.

### Removed
- **Streamlit Fully Deprecated** (confirmed in v5.8.9): `app.py` (1,175 lines), `.streamlit/` directory, `tools/_gui_runner.py` deleted. Streamlit removed from requirements.txt.
- **Tools Directory Cleanup**: Deleted `tools/start_talos.bat` (replaced by root `run_talos.bat`). Deleted `tools/_bump.py`, `tools/_git_status.ps1` (unused legacy scripts). `tools/` directory preserved (contains active `_bump_docs.py` and `_fix_changelogs.py`).
- **Stale Artifacts**: `talos.bat` (legacy launcher). `venv/` directory at project root. Stale data fix scripts (`_fix_ai.py` through `_fix4.py`). `dump.json` (stale data dump).

---

## [v5.6.0] - 2026-07-29 -- Streamlit Deprecation, Capabilities Docs, 12-File Sync Rule

### BREAKING -- Streamlit Fully Deprecated
- app.py (1,175 lines) deleted. .streamlit/ directory deleted. tools/_gui_runner.py deleted.
- streamlit removed from requirements.txt. Sole frontend: React 18 + Tailwind CSS + Shadcn UI.
- All markdown documentation purged of Streamlit references.

### Added
- docs/SYSTEM_CAPABILITIES_MASTER.md + .html: 9-section master capabilities reference (formal academic tone, no emojis)
- GET /api/v1/capabilities endpoint in src/api/main_api.py (15 endpoints total)
- docs/API_HANDOVER_FOTIS.md, docs/UX_UI_BLUEPRINT_FOTIS.md, docs/IP_PROTECTION_STRATEGY.md
- 12-File Documentation Sync Rule and Master Capabilities Rule in .clinerules

### Modified
- src/api/main_api.py v1.2 -> v1.3: version 5.5.2 -> 5.6.0, added from pathlib import Path, 14 -> 15 endpoints
- .clinerules v5.0.0 -> v5.6.0: Streamlit deprecated, React 18 sole frontend, 3 new CRITICAL rules
- README.md v5.5.2 -> v5.6.0: tagline updated, Streamlit purged, citation versions bumped
- ROADMAP.md v5.5.2 -> v5.6.0: new Section 8, summary table updated
- CHANGELOG_GR.md: v5.6.0 entry added in Greek

### Code Health Verified
- Database pathing: data/talos_research.db at project root -- confirmed correct
- API non-blocking: translate-query and recalculate-scores use inline helpers -- confirmed
- sys.exit monkey-patching: raises _ScrapeExit(RuntimeError) in main_api.py -- confirmed

## [v5.5.2] - 2026-07-22 -- 100% Ecosystem API Coverage (4 New Endpoints)

### Added
- **`src/api/main_api.py` v1.2 -- Four new "Deep Integration" endpoints for full ecosystem coverage:**
  - **`POST /api/v1/papers/{paper_id}/evaluate`** -- Triggers single-paper AI evaluation via BackgroundTasks.
  - **`POST /api/v1/ai/translate-query`** -- Synchronous natural-language -> boolean query translation.
  - **`GET /api/v1/analysis/authors`** -- Returns top authors from the local database via SQL aggregation.
  - **`POST /api/v1/db/recalculate-scores`** -- Bulk overall_score recalculation via BackgroundTasks.
- **New Pydantic models (4):** `TranslateQueryRequest`, `TranslateQueryResponse`, `AuthorSummary`, `EvaluatePaperRequest`
- **New helper:** `_flatten_json_for_translation()` -- inline duplicate of query_translator.flatten_json()
- **Total endpoints now: 14** (10 from v5.5.0/v5.5.1 + 4 new) -- **100% TALOS ecosystem coverage**.

## [v5.5.1] - 2026-07-22 -- Frontend DX Endpoints (GWO History + Architecture Graph)

### Added
- **`src/api/main_api.py` v1.1 -- Two new "Frontend DX" endpoints:**
  - **`GET /api/v1/optimize/gwo/history`** -- Returns GWO optimization history as `List[dict]` for direct Recharts consumption.
  - **`GET /api/v1/graph/view`** -- Serves the Alexandria Architecture Dependency Graph as HTML via FileResponse.
  - **StaticFiles mount** (`/static/templates`) added.
- **Total new code:** ~45 lines (2 endpoints + 1 mount + 2 import lines). Total endpoints: **10**.

## [v5.5.0] - 2026-07-22 -- FastAPI REST API Facade & Database Path Fix

### Added
- **`src/api/main_api.py` v1.0 (NEW, ~470 lines) -- FastAPI Facade Layer** with 8 REST endpoints: health, papers (paginated), paper detail, semantic search, scrape trigger, GWO trigger, task status, task list.
- **Pydantic models (10):** PaperSummary, PaperDetail, PaginatedPapers, SemanticSearchRequest, SemanticSearchResponse, ScrapeRequest, GWORunRequest, GWOResult, TaskStatus, SystemHealth.

### Changed
- **`src/core/database_manager.py` v5.4.2 -- Database path resolution fix (CRITICAL):** Project root resolution fixed from `src/` to correct project root. Priority order: explicit db_path > data/talos_research.db > active profile DB > create data/talos_research.db.

## [v5.4.1] - 2026-07-22 -- Root Directory Cleanup

### Changed
- Root directory cleaned up: `docs/` and `tools/` directories created. Internal documentation and dev scripts moved out of root.
- `.gitignore` v5.4.1: `!docs/PROJECT_MAP*.md` negate patterns added.
- README.md: Version updated to v5.4.1, all file paths updated.

## [v5.4.0] - 2026-07-22 -- src/ Package Layout (DDD Migration)

### BREAKING -- Project directory structure completely reorganized
All Python source files (~55) moved from old loose `core/`, `scripts/`, `sources/` layout into proper `src/` Domain-Driven Design package structure. Every import statement rewritten.

### New Directory Structure
```
src/
  core/ (5 files), ingestion/ (21 files), ai/drl/ (9 files), ai/optimizers/ (2 files),
  ai/embeddings/ (2 files), ai/llm/ (3 files), analysis/ (9 files), utils/ (8 files), api/ (1 file)
data/ (talos_research.db, dump.json, pdfs/)
```

### Changed
- **talos.py v5.4.1**: run_script() refactored with _SCRIPT_MAP dict. All from core.* -> from src.core.*.
- **app.py v5.4.1**: run() refactored with _SCRIPT_DIRS dict. All imports updated.
- **test_smoke.py v5.4.1**: Paths updated for new layout.
- **10 __init__.py files created** (one per package).
- **Old directories deleted**: core/, scripts/, sources/.
- **All sys.path hacks removed** -- project now uses proper package imports.

## [v5.3.7] - 2026-07-07 -- GWO v2.0 Hyperparameter Re-optimization

### Changed
- **core/drl_agent.py v2.3**: GWO-optimized LR=3.361e-05 (was 4.735e-05), GAMMA=0.6983 (was 0.575).
- **scripts/drl_trainer.py v1.4**: EPS_DECAY=0.9202 (was 0.9415).
- **70-iteration GWO run** with corrected fitness function producing valid hyperparameters.
- **models/dddqn_trained.pth** re-trained with new hyperparameters (554.6 KB).

## [v5.3.6 hotfix] - 2026-07-06 -- Grey Literature Miner Crash Fix (Batch 3)

### Fixed
- **core/ai_manager.py v3.8 -- Missing `analyze_generic_text()` (CRITICAL):** Implemented as thin wrapper around `_execute_request(model_type='pro', response_format='text')`.
- **scripts/grey_literature_miner.py v2.1**: DuckDuckGo import tries `ddgs` first, falls back to `duckduckgo_search`. Missing GEMINI_API_KEY no longer hard-exits.

## [v5.3.6] - 2026-07-06 -- The "TUI/CLI Hardening" Update (Batch 2 Audit Fixes)

### Fixed
- **talos.py v5.3.6 -- Dead menu option + Ctrl+C robustness**: Two options labeled "6." fixed; menu renumbered 1-10. safe_pause() helper added. safe_select() catches KeyboardInterrupt. Version string centralized in TALOS_VERSION constant.
- **scripts/drl_trainer.py v1.3 -- Graceful interrupt with partial save**: Ctrl+C mid-training saves partial model to models/dddqn_partial.pth.
- **scripts/talos_live_agent.py v3.2 -- argparse + startup guard**: argparse replaces ad-hoc sys.argv scanning.

## [v5.3.5] - 2026-07-06 -- The "DRL/GWO Scientific Integrity" Update (Batch 1 Audit Fixes)

### Fixed (5 CRITICAL bugs)
- **scripts/gwo_rl_optimizer.py v2.0 -- GWO fitness was pure noise**: calculate_fitness() previously used 100% random actions. Rewritten with training + evaluation phases. update_wolf_position() uses fresh r1,r2 per encircling term (canonical GWO).
- **core/talos_env.py v3.1 -- Time-limit termination bug**: step() now returns terminated=False, truncated=True at 200-step cutoff (Gymnasium semantics).
- **scripts/drl_trainer.py v1.2 -- Fatal NameError**: args.episodes references replaced with local episodes variable.
- **core/live_agent_orchestrator.py v1.1 -- State distribution mismatch**: LOW_SCORE_MAX 20 -> 10 to match training env normalization.
- **core/ai_manager.py v3.7 -- Provider attribution bug**: last_provider_used attribute tracks actual provider, eliminating false Gemini count increments.

## [v5.3.4] - 2026-07-05 -- The "Descriptive Module Names" Update

### Changed
- All mythological code names (APOLLO, CHIRON, ORPHEUS, PYTHIA, NAFSIKA, HERMES, ORACLE, ARGUS, ALEXANDRIA) replaced with descriptive titles in .clinerules, PROJECT_MAP.md, PROJECT_MAP_EN.md, app.py, README.md, ROADMAP.md.

## [v5.3.3] - 2026-07-05 -- The "Light-Only Theme & Universal Documentation" Update

### Changed
- app.py v5.3.3: Dark mode removed. Light-only theme via hardcoded CSS variables.
- templates/gui_theme.css v5.3.3: Dark/Light :root rules removed.
- templates/gui_strings.py v5.3.3: dark_toggle translation string removed.
- .clinerules v5.3.3: Progressive Documentation Rule extended to ALL file types.

## [v5.3.2] - 2026-07-05 -- The "Pluggable Network Architecture" Update

### Added
- **core/drl_networks.py v1.0 (NEW, ~100 lines)**: DuelingLSTM network extracted into dedicated module with common (input_dim, output_dim) interface for future architecture swapping.

### Changed
- core/drl_agent.py v2.2: network_class parameter for dependency injection. save() stores network class name in metadata. load() resolves class from metadata.

## [v5.3.1] - 2026-07-05 -- The "DRL Live Agent & Provider-Aware Orchestration" Update

### Added
- **core/live_agent_sources.py v1.0 (NEW, ~40 lines)**: Source discovery module with import_source_class() auto-detection and build_source_map() dense mapping.
- **core/live_agent_orchestrator.py v1.0 (NEW, ~420 lines)**: Provider-aware orchestration with cooldown mechanism, 21-dim state vector, 6 functions.
- **Tier-based Gemini configuration**: gemini_tier, provider_limits in config.json. 3 new query keys completing all 14 sources.
- **Cooldown mechanism v3.1**: 5-step lockout for negative-reward actions with random override.

### Fixed
- Sparse action mapping bug, model dimension mismatch crash, hour normalization inconsistency, 8 source class names broken, local model verification hardcoded, save path mismatch.

### Changed
- core/drl_agent.py v2.1: GWO-optimized hyperparameters applied. load() pre-checks dimensions. weights_only=True.
- core/talos_env.py v3.0: Provider-aware observation space. 21-dim state vector.
- scripts/talos_live_agent.py v3.1: Refactored from 530-line monolith to 110-line thin entry.

## [v5.3.0] - 2026-07-04 -- The "Multi-Language Documentation Builder" Update

### Added
- **scripts/generate_docs.py v2.0 (REWRITTEN, ~350 lines)**: Interactive, 18-language, 93+ file codebase documentation generator using local Ollama. 7 functions.

## [v5.2.1] - 2026-07-04 -- The "Academic Conference GUI & DRL Flagship" Update

### Added
- templates/gui_theme.css (NEW, 140 lines), templates/gui_strings.py (NEW, 124 lines).
- app.py Dual-Mode GUI (Simple + Advanced) with 8 pages.
- .clinerules: Added NO AUTO-GIT rule and Compile Check rule.

## [v5.2.0] - 2026-07-04 -- The "Onboarding & Dynamic Orchestration" Update

### Added
- app.py v5.2.0: Onboarding wizard (render_onboarding_wizard, _is_first_run), Research Pivot section.
- core/talos_env.py v2.0: Dynamic N-Source environment with _load_source_list, _load_source_limits.
- core/drl_agent.py v2.0: Dynamic agent adapting network dimensions at construction time.
- scripts/talos_service.py v2.0: Profile-aware daemon.
- scripts/talos_live_agent.py v2.0: Dynamic N-Source live agent with _import_source_class, _build_source_map.
- scripts/research_pivot.py v1.0 (NEW, ~180 lines): 5-step interactive wizard for research direction shifts.

##  [v5.2.0] - 2026-07-04 -- The Live Agent & PDF Downloader

### Added
- scripts/talos_live_agent.py v1.0 (330 lines): Live DRL inference engine with real-time state calculation.
- scripts/pdf_downloader.py v2.0: Multi-threaded batch download with ThreadPoolExecutor (15 workers).

## [v5.1.0] - 2026-07-04 -- DRL Dashboard & TUI/GUI Reorganization

### Added
- app.py -- DRL Agent Dashboard (new page) with GWO results, training status, reward chart.
- talos.py -- DRL Agent Status (Diagnostics -> Option 7), Compare Baselines (Analysis -> Option 10).

## [v5.0.1] - 2026-07-04 -- GWO JSON Export

### Added
- scripts/gwo_rl_optimizer.py: Saves best hyperparameters to models/gwo_best_params.json.

## [v5.0.0] - 2026-07-03 -- The "Hybrid Embeddings & Deep RL" Update

### Added (6 Phases, 14 new files, 22 modified files)
- **Phase 0**: Multi-Provider Hybrid Embeddings v2 (db_embedding_upgrade.py v2.0, database_manager.py v5.0 with get_papers_needing_embedding, get_all_embeddings, get_embedding_model_stats, semantic_search with model_filter; ai_manager.py v3.6 with generate_embeddings returning (vectors, model_name) tuple; embedding_generator.py v4.0 with --all seed-all mode)
- **Phase 1**: DRL Environment & Agent v1.0 (core/talos_env.py v1.0 with 6-dim observation, 4-action space; core/drl_agent.py v1.1 with DuelingLSTM + TalosDRLAgent + ReplayMemory; drl_trainer.py v1.0)
- **Phase 2**: Meta-Optimization & Offline Training (gwo_rl_optimizer.py v1.0 with Grey Wolf Optimizer; train_agent.py v1.0 with OfflineTalosEnv using real database scores)
- **Phase 4**: Autonomous Service & Notifications (core/notifier.py v1.0 with Telegram, Discord, Email; talos_service.py v1.1 with 24/7 service, daily reports, weekly digest; talos_service_api.py v1.0 on port 5002)
- **Baseline Report System** (generate_baseline_report.py v1.1 with 4 plots at 300/600 DPI, --academic flag for publication-quality output)
- **GPU Acceleration**: RTX 4070 CUDA 12.1 support, 10x training speed improvement

## [v4.11.0] - 2026-07-02 -- The "Project Map & Diagnostics" Update

### Added
- PROJECT_MAP.md: Complete project blueprint documenting all 55 files.
- .clinerules v5.0.0: Mandatory PROJECT_MAP.md reading rules for AI agents.
- templates/architecture_graph.html: Interactive Cytoscape.js dependency graph.
- scripts/verify_dependency_map.py: AST-based verification tool.

## [v4.10.1] - 2026-06-30 -- The "Model Management" Update

### Added
- scripts/model_manager.py (NEW, 608 lines): Interactive local + cloud model selection TUI.
- core/hardware.py: estimate_size_for_quant(), QUANT_SIZE_PER_BILLION table, VRAM_HEADROOM=0.70.
- Dynamic model discovery from Ollama library.

## [v4.10.0] - 2026-06-30 -- The "Zero-Config & Resilience" Update

### Added
- Tiered API Keys Management (GUI + TUI), API Health Check with tqdm, Smart Ollama Model Selector, PDF Downloader, System Health Check (78 checks).

## [v4.9.0] - 2026-06-29 -- The "Streamlit GUI & Quality" Update

### Added
- app.py: Complete 6-page Multi-Page Streamlit application.
- _gui_runner.py: Wrapper for subprocess execution of questionary-based scripts.
- test_smoke.py: 78 automated health checks.

## [v4.8.5] - 2026-06-29 -- The "Bug Hunt & Quality" Update

### Fixed
- 15+ bugs across all modules including elsevier_source NameError, grey_literature_miner logic, recalculate_scores missing operational_score, metadata_enricher 403 errors, recommender threshold raised to 7.0.

## [v4.8.4] - 2026-06-28 -- The "Multi-Provider & Web Search" Update

### Added
- Hugging Face Provider (free cloud inference), Live Web Search (DuckDuckGo), core/hardware.py detection module.

## [v4.8.3] - 2026-06-27 -- The "Secure Local AI & Privacy" Update

### Added
- Model pre-verification with auto-install, cloud fallback consent, bidirectional fallback.

## [v4.8.2] - 2026-06-27 -- The "Local AI & Resilience" Update

### Added
- Ollama local AI support, auto-install, local embeddings. Fixed 16 critical bugs.

## [v4.8.1] - 2026-05-08 -- The Dockerization & Portability Update

### Added
- Dockerfile, docker-compose.yml, start_talos.bat 1-click launcher.

## [v4.8.0] - 2026-03-20 -- The "Enrichment & Scientometrics" Update

### Added
- Scientometrics Suite (trend_analyzer.py), Data Enricher, 9 new database columns, profile-aware DatabaseManager.

## [v4.7.1] - 2025-11-30 -- The "HERMES" Performance Update

### Changed
- pdf_retriever.py rewritten with ThreadPoolExecutor for 10-15x speedup.

## [v4.7.0] - 2025-11-30 -- The PDF Retriever Update (Ethical Edition)

### Added
- pdf_retriever.py with Unpaywall API integration.

## [v4.6.0] - 2025-11-30 -- Grey Literature "Horizon Scanning"

### Added
- oracle_agent.py using Gemini 2.0 with Google Search Grounding.

## [v4.4.0] & [v4.5.0] - 2025-11-30 -- The "Open Access & Onboarding" Update

### Added
- PLOS source agent, Onboarding Wizard in talos.py.

## [v4.3.1] - 2025-11-30 -- The Batch Execution Fix

### Fixed
- sqlite3.ProgrammingError in bulk embedding updates via executemany.

## [v4.3.0] - 2025-11-28 -- The "Soft Shutdown" Update

### Added
- Dashboard Soft Shutdown button and /api/shutdown endpoint.

## [v4.2.0] - 2025-11-28 -- The Pythia Refinement & Architecture Hardening

### Changed
- AIManager v3.4: system_prompt_override for specialized agents. AIManager v3.3: Surgical JSON cleaning.

## [v4.1.0] - 2025-11-28 -- The Quad-Layer Architecture & Profile System

### Added
- 4-level evaluation framework (Strategic, Operational, Tactical, Playground). Profile Management System.

## [v4.0.0] - 2025-11-28 -- Automated Configuration ("Query Translator")

### Added
- scripts/query_translator.py: Natural language -> Boolean search queries via AI.

## [v3.2.0] - 2025-09-27 -- Operation "Genesis"

### Changed
- All source agents completely rewritten with standardized output format.

## [v3.0.0] - 2025-09-26 -- The Strategic Mentor (Knowledge Path Generator)

### Added
- scripts/knowledge_path_generator.py: Natural language dialogue, semantic search, K-Means clustering, narrative reports.

## [v2.21.0] - 2025-09-26 -- The Reliability Update

### Changed
- AIManager redesigned to be Model-Independent with native JSON mode and Circuit Breakers.

## [v2.20.0] - 2025-09-22 -- The Interactive Knowledge Graph

### Added
- Citation Analyzer: DOIs -> interactive HTML network graph via pyvis.

## [v2.19.0] - 2025-09-21 -- The Zotero Bridge & "Smart Sync" Update

### Added
- Zotero Connector with pyzotero for Web API synchronization.

## [v2.18.0] - 2025-09-21 -- The AI Resilience & Agent Expansion Update

### Added
- Centralized AIManager with automatic fallback (Circuit Breaker) from Gemini to DeepSeek.

## [v2.15.0] - 2025-09-19 -- The Interactive Dashboard

### Added
- scripts/interactive_dashboard.py: Flask + Tabulator.js web dashboard.

## [v1.0.0] - 2025-08-27 -- The Genesis

### Added
- Initial creation: arXiv querying, Gemini AI evaluation, Discord notifications via Webhook.