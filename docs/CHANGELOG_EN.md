# Changelog - Project TALOS

All notable changes to the TALOS project will be documented in this file. The project adheres to [Semantic Versioning](https://semver.org/).

## [v5.9.15] - 2026-08-14 -- RL & Daemon Hardening, Zero-Click Model Provisioning, Silent Fast Boot & Dependency Map Reconciliation

### Added
- **`docs/TECH_RADAR_GR.md`**: Complete Greek translation of the Technology Radar and Ecosystem Map, adhering to the pure Greek unicode protocol.
- **Zero-Click Local AI Model Provisioning in Launchers**: Added step [5/5] in `run_talos.bat` and `run_talos.sh` setup pipelines to automatically execute `fermion pull fermionresearch/Neutrino-8B` and `ollama pull qwen2.5:14b` during initial installation.
- **Silent Fast Boot**: Purged the legacy startup model verification (`_verify_local_models` in `talos.py`). The CLI now boots silently and instantly into the Rich dashboard; model inspection and installation are on-demand in Model Manager (Option 1).

### Changed
- **Section 7 Dependency Graph Reconciled** (`docs/PROJECT_MAP.md`, `docs/PROJECT_MAP_EN.md`): Rebuilt the architectural dependency graph using the modern `src.*` Domain-Driven Design package hierarchy, eliminating legacy drift warnings.
- **`verify_dependency_map.py` DDD Reconciliation**: Migrated `IMPORT_TO_DOC_MAP` and `COVERED_BY_PARENT` to `src.*` names and added internal-package classification so `--ci` reports zero missing drift.
- **DRL & Daemon Subsystem Hardened**: Full audit and verification across all 10 RL/Daemon modules (`talos_env.py`, `drl_agent.py`, `drl_networks.py`, `drl_trainer.py`, `live_agent_sources.py`, `live_agent_orchestrator.py`, `talos_live_agent.py`, `talos_service.py`, `gwo_rl_optimizer.py`, `autonomous_tester.py`).
- **Version strings synced across 5 code files and 15 documentation files** to v5.9.15.
- **`tests/test_multi_tier.py`**: `test_talos_version` assertion updated from "5.9.14" to "5.9.15".

### Verification
- `python -m compileall` passed on all Python files.
- Full test suite: 180 passed, 0 failed (`pytest -v`).
- `test_smoke.py`: 445 passed, 0 failed.
- Zero emojis protocol strictly enforced across all code and documentation.

## [v5.9.14] - 2026-08-02 -- Documentation Governance Restructuring

### Added
- **Three-Zone Documentation Architecture**: Created `docs/internal/` for proprietary team documents (API handovers, UX blueprints, IP strategies) and `docs/generated/` for high-volume automated documentation.
- **Gitignore Policies**: Added strict exclusion rules for `.clinerules`, `docs/internal/`, and `docs/generated/` to protect intellectual property and repository size, while keeping canonical public docs (`README`, `CHANGELOG`, `ROADMAP`) tracked.

### Changed
- **Documentation Generator**: Updated `src/utils/generate_docs.py` to output language-specific directories directly into `docs/generated/`.
- **15-File Sync Protocol**: Updated `.clinerules` path definitions to point to the new isolated directory structures.
- **Docker Infrastructure Fix & Usage Reference**: Corrected stale v5.8.2 headers in `Dockerfile`, `docker-compose.yml`, `.dockerignore`, and `example.env` to v5.9.14. Added a `config.json` bootstrap from `config.template.json`, added the `_profiles/` volume, removed the deprecated Compose `version:` key, and defaulted local-model URLs to `host.docker.internal`. Added a comprehensive `docs/DOCKER.md` usage reference and corrected the README Docker instructions.

## [v5.9.13] - 2026-08-02 -- Academic Print Theme (Light Mode) Injection

### Added
- **HTML Post-Processing**: Added `_inject_light_mode_toggle()` to `src/analysis/graphify_adapter.py`. Automatically parses the generated `graph.html` and injects a custom CSS block and UI button to toggle a high-contrast Academic Light Mode for print-ready manuscript screenshots.

## [v5.9.12] - 2026-08-02 -- Graphify Output Path Resolution & Auto-Clustering

### Fixed
- **AST Graph Path Resolution**: Fixed bug where `graphify_adapter.py` searched the project root for `graphify-out/` instead of the specified `target_dir` (e.g., `src/graphify-out/`), ensuring successful transfer to the `data/reports/` directory.

### Added
- **Auto-Clustering Execution**: The adapter now automatically spawns a secondary subprocess running `graphify cluster-only --no-label` upon successful AST extraction, ensuring the generation of `GRAPH_REPORT.md` and community labeling while maintaining offline integrity.

## [v5.9.11] - 2026-08-02 -- Vendored Dependencies Hotfix

### Added
- **AST Dependencies**: Explicitly added `tree-sitter-python` (language grammar) and `rapidfuzz` (entity resolution) to `requirements.txt` to prevent `ModuleNotFoundError` during the Graphify extraction pipeline on fresh deployments.

## [v5.9.10] - 2026-08-02 -- Vendored Graphify AST Integration & Rich Menu Reorganization

### Added
- **Vendored AST Engine**: Cloned the `graphify` repository into `vendor/graphify/` for 100% air-gapped, LLM-free codebase mapping via Abstract Syntax Trees (tree-sitter).
- **Graphify Adapter**: Created `src/analysis/graphify_adapter.py` to dynamically load the vendored package and output structural `graph.json` and `graph.html` artifacts.

### Changed
- **Rich TUI Reorganization**: Redesigned the main `talos.py` menu into 14 options strictly grouped via `rich` panels: [CORE & AI CONFIGURATION], [SEARCH & INGESTION], [ANALYSIS & TOPOLOGIES], [DAEMONS & CI/CD], and [DIAGNOSTICS & EXIT].

## [v5.9.9] - 2026-08-02 -- Report Path Consolidation & Data Directory Isolation

### Changed
- **Global Reports Migration**: Consolidated all 8 analysis scripts in `src/analysis/` to output exclusively to `data/reports/` instead of the project root. Migrated 124 historical reports.
- **Root Cleanup**: Deleted the root `reports/` directory, cementing `data/` as the sole locus for persistent runtime outputs, complying strictly with `.gitignore` policies.

## [v5.9.8] - 2026-08-02 -- Clickable Terminal Hyperlinks & Local-to-Local Fallback

### Added
- **Terminal Hyperlinks**: Introduced `_make_clickable_path()` across `talos.py` and `autonomous_tester.py` to format file outputs as `[link=file:///...]`, enabling direct CTRL+CLICK navigation in VS Code and Windows Terminal.

### Fixed
- **Local Fallback Chain**: Corrected `AIManager` logic where a failed Fast Edge tier (port 11435) would bypass the active local Heavy tier (port 11434). Connection errors now gracefully fallback to local Ollama before attempting cloud protocols.

## [v5.9.7] - 2026-08-01 -- IEEE Computer Society WEIGD Fund Badging

### Added
- **Institutional Recognition**: Embedded official IEEE Computer Society WEIGD Student Support Fund (2026) recognition across the ecosystem.
- **Visual Assets**: Deployed two-tone Rich terminal badges (`#006699` and `#002855`) in `talos.py`, Shields.io badges in Markdown files, and CSS pill badges in `SYSTEM_CAPABILITIES_MASTER.html`.
- **Citation Metadata**: Added grant metadata to `CITATION.cff`.

## [v5.9.6] - 2026-08-01 -- Dynamic Target Discovery

### Added
- **Full-Repo Fuzzing**: Upgraded `autonomous_tester.py` with `_discover_all_python_targets()`. The RL Bandit now dynamically scans the entire `src/` directory, scaling from 4 hardcoded arms to 70+ automated test targets.
- **Q-Table Reconciliation**: Persisted RL states in `data/tester_q_table.json` automatically reconcile with newly discovered files.

## [v5.9.5] - 2026-08-01 -- Silent Synapse Fallback & Non-Blocking CI/CD

### Fixed
- **Console Noise Reduction**: `synapse_client.py` now catches `ConnectionError` and uses `logger.warning()` instead of printing multi-line tracebacks when the port 8000 event bus is offline.
- **Non-Blocking Automation**: `AIManager` enforces `allow_prompt=False` when invoked by the autonomous tester, preventing interactive `(Y/n)` cloud fallback prompts from blocking background CI/CD cycles.

## [v5.9.4] - 2026-08-01 -- Advanced 2D Execution Matrix

### Added
- **2D Routing Strategy**: Implemented `TALOS_NETWORK_STRATEGY` (strict_local, local_first, cloud_first, strict_cloud) and `TALOS_HARDWARE_STRATEGY` (cpu_only, gpu_only, cpu_gpu_split).
- **Master Request Dispatcher**: Overhauled `src/core/ai_manager.py` to interpret the 2D matrix, allowing dynamic fallback chains (e.g., Cloud fails -> route to GPU -> GPU fails -> route to CPU).
- **Interactive Configuration Wizard**: TUI Model Manager now guides users through a two-step strategic selection panel.

## [v5.9.3] - 2026-08-01 -- Conda Environment Detection Hotfix

### Fixed
- **Environment Pathing**: Resolved an issue where `talos.py` displayed `Conda Environment: N/A` when launched directly via Python executables. Implemented robust `sys.prefix` and `sys.base_prefix` resolution.

## [v5.9.2] - 2026-08-01 -- Dynamic Focus Summarization & Interactive Cloud Fallback

### Added
- **LLM Context Summarization**: On startup, if no focus title exists, the Fast Edge LLM processes raw generated queries to automatically construct and display a 6-10 word active research focus title in the header.
- **Interactive Runtime Fallback**: If `AIManager` encounters a connection error to local models during an interactive terminal session, it prompts the user to switch to Cloud execution to prevent data loss.

### Removed
- **Legacy Startup Prompts**: Purged interactive initialization queries ("Local or Cloud?") to enable seamless zero-touch booting.

## [v5.9.1] - 2026-08-01 -- LLM-as-a-Judge Diagnostics

### Added
- **AI Crash Diagnostics**: Integrated `AIManager` into the autonomous tester. When a subprocess crashes, the `stderr` traceback is sent to the Fast Edge Tier (Neutrino-8B) to generate a 2-sentence human-readable debugging diagnosis.

## [v5.9.0] - 2026-08-01 -- Autonomous System Tester (RL Chaos Fuzzer)

### Added
- **RL-Driven Chaos Engineering**: Created `src/ai/testing/autonomous_tester.py`. Utilizes a Non-Stationary Epsilon-Greedy Multi-Armed Bandit algorithm to stress-test system components autonomously via background subprocesses.
- **Fragility Q-Table**: Persists learning weights to `data/tester_q_table.json`, actively prioritizing frequently crashing files.
- **REST API Routes**: Added `src/api/tester_routes.py` exposing `/api/v1/tester/status` and `/reports`.
- **System Launchers**: Option 8 integrated into `talos.py`, `run_talos.bat`, and `run_talos.sh` for automated CI/CD execution.

## [v5.8.9] - 2026-08-01 -- Full Ecosystem Deployment, Multi-Tier LLM, and TUI Dominance

### Added
- **Rich Terminal UI Dashboard**: Complete TUI rebuild in `talos.py` with the `rich` library. Dynamic status table with: Conda environment, API port (8001), Synapse bus (8000), execution mode, active LLM tiers, active research focus.
- **Active Research Focus Display**: `_build_status_table()` reads `user_research_goal` from config.json, truncates to 65 characters, displays in glowing green.
- **Interactive Research Focus View & Rotation**: Option 4 restructured into an interactive workflow with goal preview Panel, Boolean query preview, and a 3-action submenu.
- **Model Manager CLI**: `talos.py` option 1 calls `src.ai.llm.model_manager.main()` directly via import.
- **Native MCP Server**: 4 tools (system_status, semantic_search, paper_details, trigger_scrape) via stdio transport.
- **SYNAPSE Protocol**: Event-driven bus with thread-safe, non-blocking JSON event emission. 6 event types.
- **Multi-Tier LLM Routing Architecture**: Fast Edge (Neutrino-8B), Heavy Reasoning (qwen2.5:14b), Cloud. Three execution modes.
- **POSIX Launcher**: Full parity with run_talos.bat. Automatic environment detection.
- **Automated Batch Runner**: 9-option menu with Auto Conda Detection and Auto Fermion Start.
- **Expanded Test Suite**: 96 unit tests (from 29). `rich` library added.

### Changed
- **Constitution v2.0**: 8-Point Standard: Zero Emojis, 100% Air-Gapped & Local-First, Hardware-Aware VRAM, Strict Linear Execution, Verification-First, 15-File Sync, SYNAPSE Protocol, Code Documentation Standards.
- **Port Reallocation**: Port 8000 -> 8001 for TALOS API. Synapse bus occupies port 8000.
- **Docker Modernization**: python:3.10-slim -> python:3.11-slim. Exposed port 8001. Added HEALTHCHECK.

### Fixed
- **TUI Model Name Display**: Full raw strings instead of truncating via `split(":")`.
- **SQLite Column Mismatch**: 23 values for 22 columns -- fixed.
- **Fast Tier Connection Refused Fallback**: Correctly returns None on connection error.
- **Model Dimension Error**: `drl_agent.py load()` pre-checks dimensions before `load_state_dict()`.
- **Hour Normalization Inconsistency**: `/23.0` -> `/24.0`.
- **8 Broken Source Class Names**: Auto-detection via module scanning.
- **Hardcoded Local Model Verification**: Now reads `LOCAL_MODEL_NAME` from `.env`.
- **Save Path Mismatch**: Unified to `dddqn_trained.pth`.

### Removed
- **Streamlit Fully Deprecated**: `app.py`, `.streamlit/`, `tools/_gui_runner.py`.
- **Tools Folder Cleanup**: `tools/start_talos.bat`, `tools/_bump.py`, `tools/_git_status.ps1`.
- **Obsolete Files**: `talos.bat`, `venv/`, data fixup scripts, `dump.json`.

## [v5.8.8] - 2026-08-01 -- Resilient Ingestion & Elsapy Safeguard

### Added
- **API Dependencies**: Explicitly added `elsapy` and `pyzotero` to `requirements.txt`.

### Fixed
- **Graceful Import Degradation**: Wrapped `elsapy` and `pyzotero` imports in `try/except` blocks inside `elsevier_source.py` and `zotero_connector.py`. The 14-source scraping pipeline no longer crashes (`ModuleNotFoundError`) if specific vendor SDKs are missing, ensuring 100% resilient ingestion.

## [v5.8.7] - 2026-08-01 -- Sub-script Path Audit & Lazy SDK Imports

### Changed
- **Air-Gapped Resilience (Lazy Imports)**: Refactored `src/core/ai_manager.py` to import `google.generativeai` and `openai` lazily. The application boots and operates flawlessly on strictly local tiers without internet or cloud SDK installations.

### Fixed
- **Canonical Configuration Pathing**: Audited 17 standalone scripts across `src/analysis/`, `src/ingestion/`, `src/utils/`, and `src/ai/`. Replaced fragile relative paths (`../../config.json`) with a robust `_P`-based dynamic project root resolution, eliminating `FileNotFoundError` during CLI executions.

## [v5.8.6] - 2026-07-31 -- Enterprise TUI Safety Locks & Navigation Audit

### Added
- **Configuration Safety Locks**: Introduced `_confirm_setting_change()` to display a comparative `rich` panel (Previous Value vs. Proposed Value) requiring explicit user confirmation before writing to `.env`.
- **Navigation Guardrails**: Added explicit `[Cancel / Return to Main Menu]` Sentinel options to all TUI sub-menus preventing user entrapment.

## [v5.8.5] - 2026-07-31 -- Universal TUI Beautification

### Fixed
- **Model Name Parsing**: Resolved a bug in `_build_status_table()` where `split(":")[-1]` caused the Heavy Reasoning Model to display as `"14b"` instead of the full `"qwen2.5:14b"`.

### Changed
- **Sub-menu Aesthetics**: All interactive CLI options, search results, and diagnostic outputs are now wrapped in perfectly formatted `rich.panel.Panel` and `rich.table.Table` objects with zero emojis.

## [v5.8.4] - 2026-07-31 -- Rich TUI Dashboard & Model Manager Integration

### Added
- **Rich Library Integration**: Added `rich` to dependencies. Transformed the basic ASCII CLI into a high-tech, dark-mode Starship Command Dashboard.
- **Unified Menu**: The `model_manager.py` TUI was directly imported and integrated into `talos.py` as Option 1, expanding the main menu to a structured 10-option layout.

## [v5.8.3] - 2026-07-31 -- Zero-Touch Launch Chain Automation

### Added
- **Conda Auto-Detection**: `run_talos.bat` and `run_talos.sh` automatically scan common system paths to locate and activate the Conda/virtualenv silently.
- **Asynchronous Background Spawning**: Master launchers now use `start /min` (Windows) and `&` (POSIX) to spawn the FastAPI and MCP servers silently in the background, allowing seamless "Zero-Touch" UI invocation.

## [v5.8.2] - 2026-07-31 -- Docker Modernization & Workspace Sanitation

### Changed
- **Containerization Upgrade**: Upgraded `Dockerfile` to `python:3.11-slim` targeting port 8001 with native `/api/v1/health` checks.
- **Docker Compose**: Configured `docker-compose.yml` to utilize `host.docker.internal:host-gateway` for seamless access to local Ollama and Neutrino ports. Included persistent volumes for `data/`, `models/`, and `logs/`.

### Removed
- **Legacy Files**: Purged old `talos.bat` and redundant `venv/` artifacts to enforce a pristine project root.

## [v5.8.1] - 2026-07-31 -- Cross-Platform Provisioner Architecture

### Fixed
- **Hardware-Aware Provisioning**: Rewrote `frontend_provisioner.py` with strict architecture parsing (`x64` vs `arm64`) and OS detection (`Windows`, `Darwin`, `Linux`), preventing incorrect cross-platform downloads (e.g., downloading Mac binaries on Windows). Fallbacks stabilized to known v1.9.12 assets.

## [v5.8.0] - 2026-07-31 -- Multi-Tier Execution Modes & 95-Test Suite

### Added
- **Execution Modes**: TUI now supports `Local Air-Gapped`, `Hybrid`, and `Full Cloud` modes.
- **QA Expansion**: Test suite expanded to 95 automated pytest assertions covering the new multi-tier configurations.

## [v5.7.2] - 2026-07-30 -- Pragmatic "Core 5" QA Suite & Anti-Greeklish Audit

### Added
- **Core Verification**: Established the "Core 5" Pytest suite (`test_api_endpoints.py`, `test_database.py`, `test_llm_routing.py`, `test_synapse.py`, `test_smoke.py`).

### Fixed
- **Zero-Greeklish Enforcement**: All `*_GR.md` documents audited to guarantee pure formal academic Greek with proper Unicode accents.

## [v5.7.1] - 2026-07-30 -- Multi-Tier LLM Architecture & Isolated UI Provisioning

### Added
- **Multi-Tier Routing**: Introduced `tier="fast"` (targeting the ultra-compressed Neutrino-8B running on CPU) and `tier="heavy"` (targeting GPU-based local models), optimizing token throughput and VRAM conservation.
- **Interim UI Provisioner**: Created a utility to fetch the Cherry Studio portable release into an isolated, git-ignored `cherry_ui_isolated/` directory, generating its MCP configuration automatically.

## [v5.7.0] - 2026-07-30 -- SYNAPSE Event Bus & Constitution v2.0

### Added
- **Project SYNAPSE Integration**: Developed `src/integration/synapse_client.py` and `synapse_routes.py` enabling JSON-based asynchronous event publishing on port 8000.
- **Constitution v2.0**: Upgraded `.clinerules` to the 8-Point Master Standard (enforcing Linear Execution and the Timeline Tracking system).

### Changed
- **Port Reallocation**: Shifted TALOS FastAPI backend from port 8000 to `8001` to prevent collisions with the central event bus.

## [v5.6.0] - 2026-07-29 -- Streamlit Deprecation & Master Capabilities Documentation

### Added
- **Master Capabilities Record**: Introduced `SYSTEM_CAPABILITIES_MASTER.md` and dynamically served it via FastAPI at `GET /api/v1/capabilities`.
- **12-File Sync Rule**: Hardcoded the mandate to synchronize core architecture documents on every bump.

### Removed
- **Legacy GUI**: Completely eradicated `app.py` and `.streamlit/` as TALOS transitioned to a pure headless backend for React.

## [v5.5.2] - 2026-07-28 -- 100% FastAPI Coverage & DX Routes

### Added
- **Deep Integration Endpoints**: Exposed internal AI tools (`/evaluate`, `/translate-query`, `/authors`, `/recalculate-scores`) as REST endpoints.
- **Developer Experience (DX)**: Added utility endpoints serving `graph.html` and GWO historical metrics directly to the React frontend.

## [v5.5.1] - 2026-07-28 -- Frontend DX Endpoints (GWO History + Architecture Graph)

### Added
- **`GET /api/v1/optimize/gwo/history`** -- Returns GWO optimization history as `List[dict]` for direct consumption by Recharts `<LineChart>`.
- **`GET /api/v1/graph/view`** -- Serves the Alexandria Architecture Dependency Graph as HTML page via `FileResponse`.

## [v5.5.0] - 2026-07-28 -- FastAPI REST API Façade & Database Path Fix

### Added
- **`src/api/main_api.py` v1.0** -- FastAPI Façade Layer with 8 REST endpoints wrapping existing core functions without logic duplication.

### Fixed
- **`src/core/database_manager.py` v5.4.2 -- Database path resolution (CRITICAL)**: Corrected project root resolution, connecting to the populated `data/talos_research.db` instead of empty database.

## [v5.4.1] - 2026-07-28 -- Root Directory Cleanup & Technical Debt Eradication

### Changed
- **Workspace Hygiene**: Relocated miscellaneous development scripts to `tools/` and proprietary planning files to `docs/`. Refined `.gitignore` to protect environment secrets.

## [v5.4.0] - 2026-07-27 -- Domain-Driven Design (DDD) Migration

### Changed
- **Structural Overhaul**: Massive architectural migration of 55+ loose scripts from the root and `scripts/` directories into a formal, production-ready `src/` layout (`api/`, `core/`, `ai/`, `ingestion/`, `analysis/`, `utils/`).

## [v5.3.7] - 2026-07-07 -- GWO v2.0 Hyperparameter Re-Optimization

### Changed
- **`core/drl_agent.py` v2.3**: Updated GWO-optimized hyperparameters: `LR=3.361e-05`, `GAMMA=0.6983`.
- **`scripts/drl_trainer.py` v1.4**: Updated GWO-optimized epsilon decay: `EPS_DECAY=0.9202`.

## [v5.3.6 hotfix] - 2026-07-06 -- Grey Literature Miner Crash Fix (Batch 3)

### Fixed
- **`core/ai_manager.py` v3.8 -- Missing `analyze_generic_text()` (CRITICAL)**: The method was documented in PROJECT_MAP.md and called in TWO places from `grey_literature_miner.py` but had never been implemented.
- **`scripts/grey_literature_miner.py` v2.1**: Adaptive DuckDuckGo import.

## [v5.3.6] - 2026-07-06 -- TUI/CLI Hardening Update (Batch 2 Audit Fixes)

### Fixed
- **`talos.py` v5.3.6**: Fixed duplicate menu option "6.", added `safe_pause()`. `safe_select()` handles KeyboardInterrupt.
- **`scripts/drl_trainer.py` v1.3**: Graceful interrupt with partial model save on Ctrl+C.
- **`scripts/talos_live_agent.py` v3.2**: argparse replaces ad-hoc `sys.argv` scanning.

## [v5.3.5] - 2026-07-06 -- DRL/GWO Scientific Integrity Update (Batch 1)

### Fixed (5 CRITICAL bugs)
- **`scripts/gwo_rl_optimizer.py` v2.0**: `calculate_fitness()` rewritten with training + greedy evaluation phases.
- **`core/talos_env.py` v3.1**: `step()` returns `terminated=False, truncated=True` at 200-step cutoff.
- **`scripts/drl_trainer.py` v1.2**: Fixed fatal `NameError` on `args.episodes` in interactive mode.
- **`core/live_agent_orchestrator.py` v1.1**: `LOW_SCORE_MAX` 20 -> 10.
- **`core/ai_manager.py` v3.7**: `last_provider_used` tracks actual provider.

## [v5.3.4] - 2026-07-05 -- Descriptive Module Names Update

### Changed
- Replaced all mythological code names (APOLLO, CHIRON, ORPHEUS, PYTHIA, etc.) with descriptive academic titles throughout the codebase and documentation.

## [v5.3.3] - 2026-07-05 -- Light-Only Theme & Universal Documentation Update

### Changed
- **`app.py` v5.3.3**: Removed broken dark theme. Hardcoded light-only academic blue/teal palette.
- **`.clinerules` v5.3.3**: Universal progressive documentation rule covering ALL file types.

## [v5.3.2] - 2026-07-05 -- Pluggable Network Architecture Update

### Added
- **`core/drl_networks.py` v1.0**: Dedicated neural network module with `DuelingLSTM` class. Designed for future architecture swapping (Transformer, xLSTM) without touching the agent core.

## [v5.3.1] - 2026-07-05 -- DRL Live Agent & Provider-Aware Orchestration

### Added
- **`core/live_agent_sources.py` v1.0**: Dynamic source discovery with auto-detection of broken class names.
- **`core/live_agent_orchestrator.py` v1.0**: Core orchestration loop with cooldown mechanism, provider-aware state.

## [v5.3.0] - 2026-07-04 -- Multi-Language Documentation Builder

### Added
- **`scripts/generate_docs.py` v2.0**: Completely rewritten — documents the ENTIRE codebase (93+ files) in 18 languages using local Ollama instance only.

## [v5.2.1] - 2026-07-04 -- Academic Conference GUI & DRL Flagship

### Added
- **`templates/gui_theme.css`**: Professional CSS theme with glassmorphism, animations, custom scrollbar.
- **`templates/gui_strings.py`**: Translation dictionary (100+ EN/GR keys) with dynamic `t()`.

## [v5.2.0] - 2026-07-04 -- Onboarding & Dynamic Orchestration

### Added
- **`app.py` v5.2.0**: Onboarding wizard with 4-step guided setup. Research Pivot workflow.
- **`core/talos_env.py` v2.0**: Dynamic N-Source environment supporting all 14 academic APIs dynamically.
- **`core/drl_agent.py` v2.0**: Dynamic agent with metadata-aware save/load.
- **`scripts/research_pivot.py` v1.0**: Automated research direction change workflow.

## [v5.2.0] - 2026-07-04 -- The Live Agent & PDF Downloader

### Added
- **`scripts/talos_live_agent.py` v1.0**: Live DRL inference engine connecting trained agent to real APIs.
- **`scripts/pdf_downloader.py` v2.0**: Multi-threaded batch download with ThreadPoolExecutor, ~10x speedup.

## [v5.1.0] - 2026-07-04 -- DRL Dashboard & TUI/GUI Reorganization

### Added
- **`app.py` -- DRL Agent Dashboard**: Streamlit page showing GWO optimization results, agent training status, reward progression chart.
- **`talos.py` -- DRL Agent Status**: Panel with trained model status + GWO hyperparameters.

## [v5.0.1] - 2026-07-04 -- JSON Export from GWO

### Added
- **`scripts/gwo_rl_optimizer.py`**: Saves best hyperparameters to `models/gwo_best_params.json` after optimization completion.

## [v5.0.0] - 2026-07-03 -- Hybrid Embeddings & Deep RL

### Added (6 Phases, 14 new files, 22 modified)
- **Phase 0**: Multi-Provider Hybrid Embeddings v2 (Ollama + Gemini).
- **Phase 1**: DRL Environment & Agent v1.0 (Gymnasium + Double Dueling DQN with LSTM).
- **Phase 2**: Meta-Optimization & Offline Training (Grey Wolf Optimizer + offline training with real database scores).
- **Phase 4**: Autonomous Service & Notifications (Telegram, Discord, Email).
- **Baseline Report System**: Automated snapshot generator with 4 plots in 300/600 DPI.
- **GPU Acceleration**: RTX 4070 CUDA 12.1, 10x faster training.

## [v4.11.0] - 2026-07-02 -- Project Map & Diagnostics Update

### Added
- **PROJECT_MAP.md**: Complete project map documenting all 55 files, functions, dependencies, database schema.
- **`.clinerules` v5.0.0**: Mandatory PROJECT_MAP.md reading for AI agents.
- **`templates/architecture_graph.html`**: Interactive Cytoscape.js dependency graph with 102 nodes, 318 edges.
- **`scripts/verify_dependency_map.py`**: AST-based verification tool for dependency and function documentation audits.

## [v4.10.1] - 2026-06-30 -- Model Management Update

### Added
- **`scripts/model_manager.py`**: Specialized Model Management TUI with quantization-aware model selection, dynamic discovery from Ollama library, VRAM-fit indicators.
- **`core/hardware.py`**: Quantization size estimation with 30+ quantization types.

## [v4.10.0] - 2026-06-30 -- Zero-Config & Resilience Update

### Added
- **Tiered API Keys Management**: GUI + TUI with 4 sections (Free & Keyless, Premium AI, Academic APIs, Integrations).
- **API Health Check v1.1**: 25 API checks with real-time tqdm progress bar.
- **Smart Ollama Model Selector**: 3-section dropdown (Installed, Ollama Library, BitNet 1-bit).
- **PDF Downloader**: Unpaywall / OpenAlex keyless fallback.
- **System Health Check**: 78 automated checks integrated into GUI and TUI.

## [v4.9.0] - 2026-06-29 -- Streamlit GUI & Quality Update

### Added
- **Streamlit Web GUI (`app.py`)**: Complete replacement of CLI menu with 6-page professional Streamlit interface.
- **Smoke Test Suite (`test_smoke.py`)**: 78 automated checks (syntax, imports, database, AI Manager).

## [v4.8.5] - 2026-06-29 -- Bug Hunt & Quality Update

### Fixed
- 15+ bugs across all modules including elsevier_source, grey_literature_miner, recalculate_scores, metadata_enricher.
- Multi-source metadata enrichment fallback chain (OpenAlex -> Crossref -> DBLP -> Semantic Scholar).
- Recommender threshold raised from 4.0 to 7.0.

## [v4.8.4] - 2026-06-28 -- Multi-Provider & Web Search Update

### Added
- **Hugging Face Provider**: Free cloud inference via OpenAI-compatible unified API.
- **Live Web Search**: DuckDuckGo integration for grey literature mining.
- **`core/hardware.py`**: GPU VRAM detection and smart model recommendation.

## [v4.8.3] - 2026-06-27 -- Secure Local AI & Privacy Update

### Added
- **Model Pre-Verification**: Automatic check and installation of all models on startup.
- **Privacy Guard**: User consent required before any cloud fallback.
- **Bidirectional Fallback**: Local -> Cloud and Cloud -> Local with explicit user approval.

## [v4.8.2] - 2026-06-27 -- Local AI & Resilience Update

### Added
- **Local AI (Ollama) Support**: Full offline operation capability with no cloud dependencies.
- **16 Critical Bug Fixes**: Including db_stats KeyError, source agent crash without API keys, silent paper loss without DOI.

## [v4.8.1] - 2026-05-08 -- Dockerization & Portability Update

### Added
- **Docker Support**: Dockerfile based on python:3.10-slim, docker-compose.yml.
- **1-Click Launcher (Windows)**: start_talos.bat with automated venv creation and dependency installation.

## [v4.8.0] - 2025-12-20 -- Enrichment & Scientometrics Update

### Added
- **Scientometrics Suite (trend_analyzer.py)**: HTML reports with statistical analysis and visualizations (Research Timeline, Quality Landscape, Open Access Landscape, WordCloud, Top Authors).
- **Data Enricher**: Unpaywall API integration for external identifier bridging.
- **9 New Database Columns**: Including oa_pdf_url, openalex_id, pmid, pmcid, oa_status.

## [v4.7.1] - 2025-11-30 -- Performance Update

### Changed
- **pdf_retriever.py**: Rewritten with ThreadPoolExecutor (10-15x faster).

## [v4.7.0] - 2025-11-30 -- PDF Retriever (Ethical Edition)

### Added
- **pdf_retriever.py**: Scans database for DOI-bearing articles, queries Unpaywall API for legal Open Access PDFs.

## [v4.6.0] - 2025-11-30 -- Grey Literature "Horizon Scanning"

### Added
- **oracle_agent.py**: Gemini 2.0 with Google Search Grounding for grey literature discovery.

## [v4.4.0] & [v4.5.0] - 2025-11-30 -- Open Access & Onboarding Update

### Added
- **PLOS Agent**: Public Library of Science API integration.
- **Onboarding Wizard**: Automatic detection of new installations, guided setup.

## [v4.3.1] - 2025-11-30 -- Batch Execution Fix

### Fixed
- **sqlite3.ProgrammingError**: Fixed incorrect number of bindings in batch embedding updates.

## [v4.3.0] - 2025-11-28 -- Soft Shutdown Update

### Added
- **Dashboard Soft Shutdown**: Exit button in dashboard UI returning cleanly to menu.
- **/api/shutdown Endpoint**: Graceful Flask server termination.

## [v4.2.0] - 2025-11-28 -- Pythia Refinement & Architecture Hardening

### Changed
- **AIManager v3.4**: System prompt override capability.
- **AIManager v3.3**: Surgical JSON cleaning mechanism.
- **ArxivSource v3.8**: Config-driven architecture with dynamic query reading.

## [v4.1.0] - 2025-11-28 -- Quad-Layer Architecture & Profile System

### Added
- **Quad-Layer Evaluation Framework**: Extended from 3 to 4 layers (Strategic, Operational, Tactical, Playground).
- **Profile Management System**: Multiple isolated research profiles with independent config and database.

## [v4.0.0] - 2025-11-28 -- Automated Configuration ("Query Translator")

### Added
- **scripts/query_translator.py**: Natural language research goals -> optimized Boolean search queries for 10+ APIs via AI.

## [v3.2.2] - 2025-11-27 -- API Rate Limit Optimization

### Changed
- **Dynamic Rate Limiting**: Added `ai_request_delay` parameter to config.json (default 5 seconds).

## [v3.2.1] - 2025-09-27 -- The "Metrics" Update

### Added
- **scripts/db_stats.py**: Quick database statistics report tool.
- **get_database_statistics**: New method in DatabaseManager.

## [v3.2.0] - 2025-09-27 -- Operation "Genesis"

### Changed
- **Complete Upgrade of All Source Agents**: Standardized output format with guaranteed critical fields (doi, publication_year, authors_str).
- **Improved ElsevierSource Resilience**: Smart enrichment strategy with targeted second API call for missing abstracts.

## [v3.1.1] - 2025-09-27 -- Stability & UX Finalization

### Added
- **Project "APOLLO" (metadata_enricher.py)**: Smart maintenance tool scanning database for incomplete records.
- **Smart Author Identification**: ORCID iD detection, enriched disambiguation with institutional affiliation.

### Fixed
- Terminal compatibility (NoConsoleScreenBufferError), TypeError in author_profiler, FileNotFoundError.

## [v3.0.0] - 2025-09-26 -- Strategic Mentor (Knowledge Path Generator)

### Added
- **scripts/knowledge_path_generator.py**: Natural language dialogue, deep semantic search, K-Means clustering for structured knowledge paths.

## [v2.21.0] - 2025-09-26 -- Reliability Update

### Changed
- **AIManager v3.1**: Redesigned as Model-Independent with native JSON mode and provider-specific Circuit Breakers.
- **BREAKING - JSON Architecture**: All prompts restructured to require strict JSON output.

## [v2.20.1] - 2025-09-24 -- "Smart Target" Selector for Citation Analyzer

### Added
- **Interactive Target Selection**: Two ways to select target paper (manual DOI entry or smart database selection of top-10 recent core papers).

## [v2.20.0] - 2025-09-22 -- Interactive Knowledge Graph ("ORPHEUS")

### Added
- **Citation Analyzer**: DOI -> interactive HTML network graph via pyvis with full interactivity.

## [v2.19.1] - 2025-09-21 -- Trajectory Analyzer Upgrade with AIManager

### Changed
- **AIManager Integration**: Trajectory Analyzer rewritten to use centralized AIManager instead of direct Gemini API calls.

## [v2.19.0] - 2025-09-21 -- Zotero Bridge & "Smart Sync" Update

### Added
- **Zotero Connector**: pyzotero-based Web API synchronization with Pro model upgrade.

## [v2.18.1] - 2025-09-21 -- "Circuit Breaker" Smart Fallback

### Added
- **Circuit Breaker Implementation**: State-aware AIManager with consecutive failure counter, automatic fallback bypass.

## [v2.18.0] - 2025-09-21 -- AI Resilience & Agent Expansion Update

### Added
- **Centralized AI Manager**: Single point of AI execution with automatic Gemini -> DeepSeek fallback.
- **Smart Store-First Strategy**: Pre-screening with Flash model, deep analysis only for elite papers.

## [v2.17.0] - 2025-09-20 -- "Smart Store-First" Strategy & Agent Expansion

### Added
- **PubMed Agent**: Biomedical database integration via pymed.
- **OSTI.gov Agent**: US Department of Energy technical reports access.

## [v2.16.0] - 2025-09-20 -- Health & Government Intel Update

### Added
- **PubMed Agent**: Foundational biomedical research access for bio-inspired algorithms.
- **Science.gov Agent**: US government agency publications access.

## [v2.15.3] - 2025-09-20 -- Semantic Brain (Semantic Search Integration)

### Added
- **Semantic Embeddings Infrastructure**: BLOB column for vector storage, embedding_generator.py for batch creation.
- **Semantic Search Back-end**: Cosine similarity computation with natural language query support.

## [v2.15.2] - 2025-09-19 -- "Article DNA" Visualization

### Added
- **Article DNA Visualization**: Dynamic Tabulator column with color-coded sparkline bar charts for multi-axis scores.

## [v2.15.1] - 2025-09-19 -- Dashboard Refinement ("NAFSIKA")

### Added
- **Smart Filter Buttons**: Predefined filter buttons (Core Papers, Tactical Focus, etc.).
- **Modal Info Card**: Full article details in popup modal via /api/paper/<id> endpoint.

## [v2.15.0] - 2025-09-19 -- Interactive Dashboard ("NAFSIKA")

### Added
- **Interactive Dashboard (interactive_dashboard.py)**: Flask + Tabulator.js web dashboard with real-time database interaction.
- **Persistent "In Zotero" State**: Database column for permanent checkbox state storage.

## [v2.14.0] - 2025-09-17 -- Multi-Axis Evaluation & Interactive Dashboard

### Added
- **Multi-Axis Scoring**: Three independent axes (Tactical, Strategic, Simulation) with weighted overall_score.
- **Interactive Report Dashboard**: DataTables.js integration for dynamic sorting, filtering, and pagination.

## [v2.13.0] - 2025-09-16 -- Scopus Integration & Query Optimization

### Added
- **Full ElsevierSource Activation**: Two-factor authentication (APIKey + Institutional Token) with modern pagination.
- **Strategic Query Optimization**: Boolean logic combining multiple interest pillars per API syntax.

## [v2.12.0] - 2025-09-16 -- Smart Recalibrator & Agent Activation

### Added
- **Smart Recalibrator (reevaluate_database.py)**: Intelligent database re-evaluation with prioritization and batching.
- **OpenArchivesSource Activation**: Greek national aggregator integration with specialized queries.

## [v2.11.1] - 2025-08-31 -- Critical Unicode Fix

### Fixed
- **UnicodeDecodeError**: Upgraded run_script in talos.py for bulletproof encoding with forced UTF-8 environment.

## [v2.11.0] - 2025-08-31 -- Strategic Dossier Update

### Added
- **Author Trajectory Analyzer**: Holistic strategic analysis of researcher's recent work portfolio.
- **Unified "Profiler -> Analyzer" Workflow**: Chained execution with automatic ORCID iD extraction.

## [v2.10.0] - 2025-08-31 -- Unified Profiler Update

### Added
- **Unified Author Profiler**: Three-source strategy (ORCID for identity, OpenAlex for linking, Semantic Scholar for metrics).

## [v2.9.2] - 2025-08-30 -- Transparency & Filtering Optimization

### Changed
- **Full Transparency**: Detailed filtering steps printed for main_search.py.
- **VIP Pass for Titles**: Smart quality control allowing keyword-matched articles without abstracts.

## [v2.9.1] - 2025-08-30 -- Score Storage Bug Fix

### Fixed
- **Structural Restructuring**: extract_relevance_score moved exclusively to database-writing scripts.

## [v2.8.0] - 2025-08-30 -- "Two-Stage Sentinel" Update

### Added
- **Pre-Screening**: Fast initial evaluation using Flash-Lite model.
- **Store-First Strategy**: All pre-screened articles immediately stored.
- **Elite Deep Analysis**: Only high-scoring articles receive Pro model analysis.

## [v2.7.2] - 2025-08-29 -- HTML Layout Perfection

### Fixed
- **recommender.py**: Added `table-layout: fixed;` CSS property for proper column width enforcement.

## [v2.7.1] - 2025-08-29 -- HTML Layout Optimization

### Changed
- **recommender.py**: Specific column widths set for balanced, readable table display.

## [v2.7.0] - 2025-08-29 -- Elegant & Concise Reports

### Changed
- **Markdown Export Redesign**: Structured, condensed format with headings and callouts.
- **DOCX Export Redesign**: Elegant portrait document with headings and paragraphs instead of tables.

## [v2.6.1] - 2025-08-29 -- DOCX Export Fix

### Fixed
- **XML Sanitization**: Removed incompatible characters for proper Word document saving.

## [v2.6.0] - 2025-08-29 -- The Scribe Update

### Added
- **Microsoft Word (.docx) Export**: Full report export to formatted Word document.
- **Markdown (.md) Export**: Report export ready for Obsidian import.

## [v2.5.1] - 2025-08-29 -- HTML Encoding Fix

### Fixed
- **recommender.py**: Added `<meta charset="UTF-8">` for proper Greek character display.

## [v2.5.0] - 2025-08-28 -- The Keystone Update

### Added
- **Crossref API Integration**: Access to central metadata database covering all major publishers.

## [v2.4.0] - 2025-08-28 -- The Profiler Update

### Added
- **Author Profiler (author_profiler.py)**: Scopus Author Profile API integration for researcher metrics.

## [v2.3.0] - 2025-08-28 -- The Elsevier Integration

### Added
- **Elsevier Scopus Integration**: elsapy-based Scopus Search API agent.

## [v2.2.0] - 2025-08-28 -- Automatic Cluster Naming

### Added
- **TF-IDF Keyword Extraction**: Automatic extraction of top 4 representative keywords per cluster as dynamic titles.

## [v2.1.0] - 2025-08-28 -- Smart "Reading Path"

### Added
- **Strategic Recommender Upgrade**: Elite filtering for foundational papers, dedicated "State-of-the-Art" category.

## [v2.0.0] - 2025-08-27 -- The Pantheon Update

### Added
- **DBLP Integration**: High-quality Computer Science bibliography database.
- **CORE Integration**: Aggregator containing millions of open-access articles.

## [v1.11.0] - 2025-08-28 -- Perfection & Stabilization

### Added
- **Smart Launcher**: Automatic Python executable detection via sys.executable.
- **Bulletproof Score Extraction**: Multiple regex strategies for score parsing.

## [v1.10.0] - 2025-08-28 -- OpenAlex Integration

### Added
- **OpenAlex Agent**: Full pagination support, inverted index abstract reconstruction.

## [v1.9.0] - 2025-08-28 -- Semantic Scholar Upgrade

### Changed
- **Direct API Calls**: Replaced semanticscholar library with direct requests for absolute control.

## [v1.8.0] - 2025-08-28 -- Springer Upgrade

### Changed
- **Pagination Addition**: Springer agent rewritten for 100-result pagination with rate limit handling.

## [v1.7.1] - 2025-08-27 -- Flexible Parameterization

### Changed
- **Flexible days_to_search**: Separate parameters for daily and historic search.
- **Enhanced arxiv_query**: Combined category and full-text search.

## [v1.7.0] - 2025-08-27 -- Limits Optimization & Flash-Lite Adoption

### Changed
- **Per-Source Limits**: Individual result limits configurable via max_results_config.
- **gemini-2.5-flash-lite**: Adopted for historic search leveraging 1000+ requests/day free tier.

## [v1.6.0] - 2025-08-27 -- Critical Bug Fix

### Fixed
- **Score Storage**: extract_relevance_score moved from recommender to database-writing scripts.

## [v1.5.0] - 2025-08-27 -- Encyclopedic Documentation

### Added
- **CHANGELOG.md**: Project history documentation file.
- **Comprehensive README.md**: Complete rewrite as hyper-detailed encyclopedic manual.

## [v1.4.0] - 2025-08-27 -- Reports & Strategy

### Added
- **Strategic Reading Path**: Recommender upgrade with foundational-then-specialized article suggestions.
- **Report Export**: CSV and HTML report export to reports/ directory.

## [v1.3.0] - 2025-08-27 -- The Control Center

### Added
- **Project Named "TALOS"**: Official project name adopted.
- **talos.py**: Central interactive terminal menu as launcher for all functionality.
- **Gemini Model Auto-Selection**: Config-based model selection (Pro/Flash) for daily vs historic search.

## [v1.2.0] - 2025-08-27 -- The Memory

### Added
- **SQLite Database Integration**: Local database (research_bot.db) with duplicate avoidance.

## [v1.1.0] - 2025-08-27 -- The Polyphony

### Added
- **Multi-Source Support**: Object-oriented rewrite with dedicated source agents (ArXiv, Semantic Scholar, IEEE, Springer).
- **Deduplication**: Logic for removing duplicate articles across multiple sources.

## [v1.0.0] - 2025-08-27 -- The Genesis

### Added
- **Initial Creation**: Simple script querying arXiv, evaluating abstracts via Gemini AI, sending Discord notifications via Webhook.