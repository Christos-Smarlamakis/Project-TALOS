# Project TALOS -- Strategic Roadmap & Architecture Chronicle

This document serves as both the **development compass** and the **architectural narrative** of Project TALOS. It chronicles the evolution from a research aggregator to a fully autonomous, DRL-driven research intelligence platform -- and maps the path forward toward Project ALEXANDRIA.

> **Current Version:** v5.25.2 (Preserve All Information, Hierarchical 3-Tier AI Model Management & Interactive Candidate Selector) — Complete, 2026-10-04
> **Last Updated:** 2026-10-04

---

## 1. The Vision: From Aggregator to Autonomous Research Architect

Project TALOS was born from a simple question: **what if a literature review system could think for itself?**

The exponential growth of academic publishing (over 5 million papers per year) has broken the traditional Systematic Literature Review (SLR) workflow. A PhD researcher simply cannot manually monitor, evaluate, and synthesize the firehose of daily publications. TALOS answers this challenge by evolving through three generations:

1. **Gen 1 (v1-v4): The Aggregator** -- Searched 14 APIs, evaluated papers with AI, stored results in SQLite.
2. **Gen 2 (v5.0-v5.9): The Orchestrator** -- A Deep Reinforcement Learning agent that learns to select optimal APIs in real-time, backed by Multi-Tier LLM routing and Autonomous Red Testing.
3. **Gen 3 (v5.10-v6.0+): The Topological Ecosystem (Project ALEXANDRIA)** -- Automated PRISMA 2020 pipelines (PlanEval/DSPy), Bi-Level GWO AutoRL, Knowledge Graphs, and SYNAPSE Event Mesh interoperability.

---

## 2. v5.0.x -- The AI Core (COMPLETED)

The v5.0 series represents a **paradigm shift** -- TALOS ceased being a passive aggregator and became an **active, learning orchestrator**.

### 2.1 Phase 0: Multi-Provider Hybrid Embeddings
| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Ollama Embeddings** | `nomic-embed-text` (local) | Free, offline, zero-latency embeddings |
| **Gemini Embeddings** | `gemini-embedding-001` (cloud) | High-precision 768-dim vectors, `RETRIEVAL_DOCUMENT` task type |
| **Embeddings Table** | SQLite with B-tree indexes | Multi-model vector storage, backward-compatible |
| **Migration Script** | `db_embedding_upgrade.py` | Seamlessly migrated 3,849 legacy records to the new schema |
| **Google GenAI GA SDK** | `google.genai.Client` | Future-proof API |

### 2.2 Phase 1: Deep Reinforcement Learning Stack
| Component | File | Description |
|-----------|------|-------------|
| **Gymnasium Environment** | `src/ai/drl/talos_env.py` | Observation Space (6-dim): normalized hour, API usage ratios, streaks. Action Space (4): ArXiv, OpenAlex, Semantic Scholar, Sleep. |
| **DRL Agent** | `src/ai/drl/drl_agent.py` | 3-layer LSTM (128-64-32) with LayerNorm + Dueling heads (V + A). Double Dueling DQN, soft updates (t=1e-3), replay memory (10K). |
| **Training Loop** | `src/ai/drl/drl_trainer.py` | Interactive episode selection, profile-aware DB, real-time timing. |
| **GPU Acceleration** | RTX 4070, CUDA 12.1 | CuDNN optimization: `flatten_parameters()` before LSTM forward pass. **10x speedup** over CPU. |

---

## 3. v5.1.0 -- The Insights UI (COMPLETED)
- GWO optimization metrics display.
- Agent training status and reward progression visualization.
- Training details hardware table.

---

## 4. v5.2.x -- Onboarding & Dynamic Orchestration (COMPLETED)
- 4-step guided onboarding wizard.
- First-run auto-detection.
- Interactive research pivot workflow (`src/ai/llm/research_pivot.py`).
- Dynamic DRL stack supporting N sources dynamically.

---

## 5. v5.3.x -- DRL Scientific Integrity & UI Hardening (COMPLETED)
- **v5.3.1**: DRL Live Agent with provider-aware orchestration and 5-step cooldown lockout.
- **v5.3.2**: Pluggable network architecture (`src/ai/drl/drl_networks.py`).
- **v5.3.3**: Universal documentation rule, light-only UI theme.
- **v5.3.4**: Mythological names replaced with academic module titles.
- **v5.3.5**: GWO v2.0 real fitness evaluation (canonical Mirjalili 2014 algorithm).
- **v5.3.6**: Ctrl+C robustness and CLI hardening across all entry points.
- **v5.3.7**: Full 9.5-hour GWO hyperparameter optimization run (`LR=3.361e-05`, `GAMMA=0.6983`, `EPS_DECAY=0.9202`).

---

## 6. v5.4.x -- DDD Migration & Root Cleanup (COMPLETED)
- **v5.4.0**: Domain-Driven Design package layout, all source files relocated to `src/` hierarchy (`src/core`, `src/ingestion`, `src/ai`, `src/analysis`, `src/utils`, `src/api`).
- **v5.4.1**: Root directory cleanup, `docs/` and `tools/` structure.

---

## 7. v5.5.x -- FastAPI REST Facade & Ecosystem Coverage (COMPLETED)
- **v5.5.0**: FastAPI REST facade with 8 core endpoints, database path resolution fix.
- **v5.5.1**: Frontend DX endpoints (GWO history for Recharts, architecture graph HTML).
- **v5.5.2**: 100% ecosystem API coverage (14 total endpoints, 16 Pydantic models).

---

## 8. v5.6.x -- Streamlit Deprecation & Headless Modernization (COMPLETED)
- **BREAKING**: Streamlit fully deprecated. Sole frontend: React 18 + Tailwind CSS + Shadcn UI.
- FastAPI upgraded to 15 endpoints (+`/api/v1/capabilities`).
- Created `docs/SYSTEM_CAPABILITIES_MASTER.md` and `.html`.
- Enforced 12-file documentation synchronicity rule.

---

## 9. v5.7.x -- Master Standard v2.0 & SYNAPSE Protocol (COMPLETED)
- Upgraded `.clinerules` to 8-Point Constitution v2.0 and 15-file sync rule.
- Scaffolded SYNAPSE Event-Driven Protocol (`src/integration/synapse_client.py`, `src/api/synapse_routes.py`).
- Port reallocation: TALOS FastAPI on port 8001, SYNAPSE bus on port 8000.
- Created `run_talos.bat` and `run_talos.sh` automated launchers.

---

## 10. v5.8.x -- Multi-Tier LLM Routing, Launchers & Enterprise TUI (COMPLETED)
- **v5.8.0 - v5.8.3**: Three-tier LLM routing (Fast Edge Neutrino-8B on port 11435, Heavy Reasoning Qwen2.5-14B on port 11434, Cloud Provider). Native MCP Server (`src/mcp_server.py`, 4 tools) for Cherry Studio. Isolated interim UI provisioner.
- **v5.8.4 - v5.8.9**: Rich TUI Dashboard in `talos.py`. Model Manager CLI integration. Auto-Conda detection and detached POSIX daemons in launchers. Expanded test suite (96+ unit tests). 15-file sync rule solidified.

---

## 11. v5.9.x -- Chaos Engineering, Universal Cloud Mesh & Hardening (COMPLETED)
- **v5.9.0 - v5.9.7**: Autonomous System Tester (`src/ai/testing/autonomous_tester.py`) with Non-Stationary Epsilon-Greedy MAB and LLM-as-a-Judge diagnostics. Scaled from 4 to 70+ dynamic test arms. Added `/api/v1/tester` REST endpoints.
- **v5.9.8 - v5.9.13**: Clickable terminal hyperlinks. Local-to-local fallback (CPU tier -> GPU Ollama before cloud). Vendored Graphify AST engine integration (`src/analysis/graphify_adapter.py`) with Academic Print Light Mode CSS injection.
- **v5.9.14 - v5.9.15**: Docker infrastructure overhaul (`host.docker.internal` local connectivity, `docs/DOCKER.md`). Fixed `pandas 3.0` DLL incompatibility. Silent fast boot (purged blocking startup model verification). Reconciled Section 7 dependency map.
- **v5.9.16**: Renamed tester to **Autonomous Red Tester** (`src/ai/testing/red_tester.py`). Implemented Deep API Fuzzing arms and LLM Context Window Truncation (2,000 chars limit).
- **v5.9.17**: Universal Rich TUI enforcement and Enterprise Logging (`src/utils/logger.py` with `RichHandler` and `RotatingFileHandler` to `data/logs/talos_system.log`).
- **v5.9.18**: **Universal Cloud Mesh** -- unified 8 OpenAI-compatible cloud providers (NVIDIA NIM 1M, Groq LPU, Cerebras, GitHub Models, Mistral AI, OpenRouter, DeepSeek, HuggingFace) alongside Google Gemini SDK. Model Manager Cloud TUI with `[ACTIVE]` vs `[UNCONFIGURED]` status indicators.

---

## 12. v5.10.x -- The Topological Space & Ingestion Expansion (CURRENT PHASE)

The v5.10.x series transitions Project TALOS from an aggregator to a fully adaptive, multi-agent cognitive architecture, paving the way for Project ALEXANDRIA.

| Sub-Version | Codename | Focus | Status |
|:------------|:---------|:------|:-------|
| **v5.10.0** | Ingestion Expansion | Added OpenReview (Source #15, ICLR/NeurIPS peer reviews via `openreview-py`) and OpenAIRE (Source #16, EU Horizon open access). Expanded `daily_search` and `historic_search` to 16 sources. Added 34 unit tests. | Complete |
| **v5.10.1** | DRL Environment Scaling | Scaled Gymnasium environment (`talos_env.py`) to **23 State Dimensions** and **17 Action Dimensions** (16 sources + Sleep). Dynamic DuelingLSTM network auto-reconstruction. | Complete |
| **v5.10.2** | LLM Router & GWO Shaper | Created `LLMRouterSubAgent` (`src/ai/drl/llm_router_subagent.py`) implementing Contextual Bandit decision policy. Created `GWOLLMRouterRewardShaper` (`src/ai/optimizers/gwo_llm_router_reward_shaper.py`) for Bi-Level multi-objective reward weight optimization. Renamed hyperparameter tuner to `gwo_foraging_hyperparameter_tuner.py`. Implemented Interactive 16-Source Checkbox TUI in `talos.py`. | Complete |
| **v5.10.3** | Hierarchical DRL | Integrated `LLMRouterSubAgent` directly into 24/7 research daemon (`talos_service.py`), live foraging orchestrator (`live_agent_orchestrator.py`), and search pipelines. Implemented dynamic SWE-bench relative quality normalization ($Q_p = \text{Score}_p / \max_k \text{Score}_k$). | Complete |
| **v5.10.4** | Model Discovery & SYNAPSE | Created `ModelDiscoveryEngine` (`src/ai/llm/model_discovery.py`) with local `data/model_benchmarks.json` cache and live API model scanning. Exposed 19th REST endpoint `GET /api/v1/synapse/status`. | Complete |
| **v5.10.5** | Dynamic Provisioner | Created `ModelProvisioner` (`src/utils/model_provisioner.py`) with 3-tier path resolution (custom vault `FAST_EDGE_MODEL_PATH`, in-tree `models/`, auto-download) and JIT auto-pull for Ollama and HuggingFace Hub with self-healing fallback. 296 Pytest tests passing. | Complete |
| **v5.10.6** | Daemon OS Autostart & Orchestrator | Added `src/utils/daemon_autostart.py` (Windows Startup shortcut), interactive daemon pre-flight in `talos.py`, and `daemon_target_sources` injection into `talos_live_agent.py`. | Complete |
| **v5.10.7** | OPTICA Bridge Integration | Added `src/integration/optica_client.py` (`OpticaClient`) REST client to offload cnsplots/PyVis graphics to Project OPTICA (port 8002); new "Data Visualizations (via OPTICA)" TUI menu option. | Complete |
| **v5.10.8** | Enterprise TUI Overhaul & Academic Aesthetics | Unified questionary prompt style (Cyan/Teal #00ced1 selection colors, bright-white separators, IEEE blue #4a9eff question mark) canonicalized in `src/utils/ui_theme.py` and applied to every CLI prompt. | Complete |
| **v5.10.9** | Comprehensive TUI Feature Audit & Profile Management Restoration | Hierarchical 16-option TUI across 6 visual groups, 9 dedicated sub-menus, Profile Management restored, Grey Literature Miner, Knowledge Path, Citation Analyzer, GWO Suite, DB Maintenance tools all surfaced in the TUI. | Complete |
| **v5.10.10** | 3D Holographic Knowledge Constellation | Real-time WebGL 1.0 3D visualizer streaming foraging events across all pipelines (DRL, Daily 16 APIs, Historic Archive). Dual-mode: Live SSE + Conference Offline Replay. FastAPI SSE endpoint, 22 REST API endpoints. | Complete |
| **v5.10.11** | Vendored Three.js 3D Knowledge Constellation | Production-grade Three.js visualizer locally vendored in `static/js/three.min.js` (r128 UMD). Health Aura Sprites, Academic Print Theme, 1.5s Live Polling Bridge, `/static` FastAPI mount, Fibonacci-sphere 16-node constellation. Supersedes the v5.10.10 raw WebGL prototype. | Complete |
| **v5.10.12** | Autonomous Daemon Hardening, 3D Laser Telemetry & Interactive Visualizer Tools | 60 FPS animated laser beams with traveling photon pulses, raycaster click-to-fire, PNG snapshot/fullscreen/help tools, 1000ms pure-AJAX state polling, active-profile DB resolution, and SQLite VACUUM optimizer. 23 FastAPI endpoints. | Complete |
| **v5.11.0** | Live Telemetry HUD Console, Win32 Close-to-Tray & Linux Bootstrap | Bottom-right glassmorphism telemetry HUD console, native Win32 close-to-tray hook, full title/authors [EVAL] telemetry with English error sanitization, persistent JSONL evaluation history + TUI viewer, zero-touch Miniconda/talosenv Linux bootstrap. | Complete |
| **v5.11.1** | TUI Sub-Menu Sanitization & Complete Hierarchy Audit | Questionary choice-list corruption fix in `profile_settings_menu()`, sequential 1-8 renumbering, unified `[ Back / Return to Main Menu ]` labels across all sub-menus. | Complete |
| **v5.11.2** | Zero-Click Windows Pre-Flight Onboarding Wizard & Cross-Platform Packaging | Progress-aware 5-step `:AUTO_PREFLIGHT` setup wizard in `run_talos.bat` with time estimates and `[OK]` ticks, silent Miniconda3 bootstrap via native `curl.exe`, new `:DISCOVER_CONDA` multi-root discovery, and a silent fast-path bypass gate for sub-1-second daily launches. | Complete |
| **v5.11.3** | Ecosystem Integrity, Deprecation Elimination & Dependency Alignment | OpenReview V2 `search_notes` dispatch ladder (`_query_notes`), Fast-Edge (11435) batch circuit breaker (`_fast_edge_offline_memo`), FastAPI `lifespan` migration, Gemini FutureWarning suppression, multi-path GWO artifact status check, and dependency-map verifier repair (dual-language Section 7, whitelist expansion); also formally seals the 7 pre-demo concurrency hardening fixes. | Complete |
| **v5.12.0** | Research Setup Wizard & Cognitive Onboarding | `src/utils/research_setup_wizard.py` -- 4-step English-first onboarding, local AI auto-spawn with failsafe heuristic bypass (2s Fast Edge scope validation), first-run sentinel automation, and ISO/IEC 25010 usability compliance. | Complete |
| **v5.12.1** | Research Wizard Query Transparency & CLI Fast-Dispatch Engine | Step 1 query-preview table (top primary sources + inclusion/exclusion criteria) with a Questionary confirmation gate; `talos.py` CLI fast-dispatch flags (`--wizard`/`--daily`/`--stats`/`--help`). | Complete |
| **v5.12.2** | Self-Healing AI Manager, 5-Tier Strategy Matrix & Research Wizard Integrity Engine | Self-healing Ollama probe/spawn, 5-tier execution strategy matrix (`strict_local`/`local_first`/`cloud_first`/`strict_cloud`/`auto_dynamic`), day-based historical search window, cancellation integrity, thinking-model parser, English-first cognitive mandate. | Complete |
| **v5.12.3** | Research Pivot Modernization & Setup Wizard TUI Integration | `research_pivot.py` canonical REPO_ROOT-anchored subprocess paths with strict returncode verification, Rule 9 codename elimination (Cognitive Query Compiler / Citation Graph Analyzer), and Research Setup Wizard promoted to option 1 in the Configuration & Profiles TUI menu. | Complete |
| **v5.12.4** | Concurrent Ingestion Mesh & Multi-Profile Research Onboarding | Step 0 profile target gate (`_step0_profile_selection()`: reconfigure active / switch existing / create fresh isolated profile) and `ThreadPoolExecutor(max_workers=16)` concurrent 16-source harvest with Rich Live telemetry and DOI + normalized-title-hash deduplication (~35-45s to ~3-4s). | Complete |
| **v5.13.0** | Full-Stack Concurrent Multi-Threaded Engine & High-Throughput Harvester | ThreadPoolExecutor 16-source ingestion mesh (daily + historic), concurrent cognitive evaluation pool (8 cloud / 2 VRAM-guarded local workers), batched SQLite WAL re-evaluation, and Rich Live concurrency telemetry. | Complete |
| **v5.13.1** | System Diagnostics Analyzer & Operational Integrity Engine | 8-point pre-flight health check (Python env, SQLite integrity/WAL, local AI runtime, port availability, filesystem permissions, .env structure, daemon status, optional network endpoints) with a Rich health report + one-line remediation; CLI --diagnostics/--doctor and TUI Group 6 option. | Complete |
| **v5.14.0** | Stanford DSPy PRISMA-ScR Pipeline & Declarative Synthesis Engine | Typed declarative PRISMA-ScR signatures (`src/prisma/dspy_signatures.py`), PlanEval modules (Planner/Evaluator/EligibilityJudge/Executor), PRISMA 2020 Mermaid flowchart generator, scoping review synthesizer, and Rule 10 academic dossier. | Complete |
| **v5.14.1** | Multi-Agent Peer-Review Swarm & Consensus Engine | 3-agent specialized review swarm (`src/prisma/swarm_evaluators.py`), automated Cohen's Kappa inter-rater reliability, Chain-of-Thought consensus arbiter, PRISMA pipeline swarm screening mode, and Rule 10 academic dossier. | Complete |
| **v5.14.2** | BibTeX Scientific Exporter, 18-Source Aerospace Ingestion & Feature Freeze | `BibTeXExporter` (`src/utils/bibtex_exporter.py`) with `AuthorYearTitleKeyword` cite keys and LaTeX sanitization; NASA NTRS (`nasa_ntrs_source.py`) and HAL/Inria (`hal_inria_source.py`) keyless REST harvesters raising ingestion to 18 sources; persisted `prisma_decision` column; Rule 10 dossier 03. Final Feature Freeze. | Complete |
| **v5.15.0** | Universal Scientific Search Hub & Neural Graph Discovery Engine | Modular `src/ingestion/sources/` subpackage (18 adapters, unified `SOURCE_REGISTRY`), `CitationSnowballEngine` (`src/search/citation_snowballing.py`), `NeuralVectorSearchEngine` (`src/search/neural_vector_search.py`, local `nomic-embed-text`), `CodeFirstSearchEngine` (`src/search/code_first_search.py`), CLI `--snowball`/`--vector-search`/`--code-search` + Group 2 Universal Search Hub, Rule 10 dossier 04. | Complete |
| **v5.15.3** | Session Circuit Breaker, Robust Author Extraction & Daemon Lifecycle Hardening | Session-level `fast_tier_offline` circuit breaker latching the CPU edge (11435) offline after first failure (zero re-probes / fallback spam), multi-key `normalize_authors()` resolver eliminating "Unknown Authors" false positives, clean single-line `[EVAL]` daemon telemetry, and silent standalone SYNAPSE buffering (`synapse_available` + JSONL). | Complete |
| **v5.16.1** | Unified Profile Architecture & Workspace Synchronization Engine | `ProfileManager` as the strict single source of truth (repo-root `_profiles/` anchoring), canonical `uav_mission_planning` PhD workspace migration (5,472 papers / 114 elite / 325 quality-appraised), and local AI runtime unification on port 11434 (retiring phantom 11435). | Complete |
| **v5.16.2** | Pluggable Provider Registry & Hardware-Aware Model Advisor | Modular adapter-based `ProviderRegistry` (`src/core/provider_registry.py`) implementing the Open-Closed Principle (local Ollama + nine cloud providers, `register`/`get`/`list_all`/`list_active`), hardware-aware `HardwareModelAdvisor` (`src/core/hardware_advisor.py`) with 4-bit VRAM parameter budgeting and role-based recommendations, offline-graceful SOTA discovery radar (Qwen 3/4, Llama 4), zero-regression `AIManager` decoupling, and CLI `--hardware-advisor`/`--recommend-models` + TUI Option 8. | Complete |
| **v5.16.0** | PRISMA Quality Appraisal & Dual-Axis Scientific Rigor Engine (Kitchenham 2007) | Standardized six-question, three-point Kitchenham quality rubric (`src/prisma/quality_appraisal.py`), decoupling of Semantic Relevance (S_rel) from Methodological Quality (S_qual), 2D Evidence Decision Plane quadrants, batch appraisal (`--appraise-quality`), SQLite schema expansion (`quality_score`/`quality_rubric_json`/`evidence_quadrant`), BibTeX dual-filter export, Rule 10 dossier 05. | Complete |
| **v5.17.0** | Two-Tier Hierarchical Swarm Architecture & Forensic Quality Engine | Tier-2 Forensic Quality Swarm (`src/prisma/quality_swarm.py`): four specialized skill auditors (Theory Q1 / Operational Q2 / Benchmark Q3-Q4 / OpenScience Q5-Q6) loading profile-compiled, domain-agnostic template skills; `SkillCompiler`, `SmartSectionSlicer`, and `KitchenhamQualitySynthesizer` with `S_qual` and inter-auditor Fleiss `kappa_qual`; appraiser `appraisal_mode` ('single'/'swarm'); CLI `--appraise-quality [--swarm]` / `--compile-skills`; Rule 10 dossier 06. | Complete |
| **v5.18.0** | Ethical Academic PDF Harvester, Smart Section Slicing & SQLite FTS5 Engine | Cascading 13-source legal Open Access resolver (`src/ingestion/pdf_harvester/resolvers.py`), six-layer download pipeline (`harvester.py`: `%PDF-` magic bytes, atomic writes, SHA-256, timeout, size cap, polite rate limit), air-gapped `PDFSectionExtractor`, SQLite FTS5 `FullTextSearchEngine` (`src/search/fulltext_search.py`), CLI `--download-pdfs` / `--fts` / `--open-pdf`, `SmartSectionSlicer` cached-section integration, Rule 10 dossier 07. | Complete |
| **v5.18.5** | Hierarchical Evaluation Engine, Cognitive LLM Router & Clean Ingestion Lifecycle | Centralized `HierarchicalEvaluationEngine` (`src/core/hierarchical_evaluator.py`) with 2-tier escalation (fast 8B sieve -> S_rel >= 6.0 -> heavy 14B/cloud deep scrutiny); Cognitive LLM Router Quota Latching (`AIManager.exhausted_providers`, 402/401 fast-fail to DeepSeek with zero attempts); emoji-free dynamic console title (`SetConsoleTitleW`); Science.gov DNS isolation + disabled-by-default; DBLP Boolean query sanitization + JSON resilience. | Complete |
| **v5.18.4** | Self-Healing Ingestion Gateway & Autostart Profile Provisioning | Overarching `ResilientIngestionGateway` (`src/ingestion/resilient_gateway.py`) wrapping all 18 sources with fast-fail 401/403/quota circuit breaking and OpenAlex publisher mirroring for IEEE/Elsevier/Springer (`primary_location.source.publisher_lineage`); mandatory Questionary profile selection as Step 1 in `daemon_autostart.py:main()` with `daemon_profile` persistence into `_profiles/<profile>/config.json` and `--profile <target>` boot-batch embedding. | Complete |
| **v5.18.3** | DRL Dual-Checkpoint Net2Net Surgery & Daemon Profile Provisioning Engine | Genuine dual-checkpoint Net2Net input tensor surgery (`migrate_d3qn_checkpoint.py` iterating both `models/` and `src/ai/models/`, expanding `lstm1.weight_ih_l0` to `[512, 25]` and `A.weight` to `[19, 32]`, eliminating `RuntimeError: Expected 23, got 25`), and interactive Questionary daemon profile provisioning (`daemon_autostart.py` + `talos_service.py --profile`) with dynamic banner sync to `uav_mission_planning`. | Complete |
| **v5.18.2** | Net2Net DRL Checkpoint Repair, Win32 Close-to-Tray Hook & Desktop Provisioner | Net2Net 18-source / 25-dim DDDQN checkpoint repair (`migrate_d3qn_checkpoint.py`, idempotent, forward pass verified), Win32 close-to-tray window-procedure hook (`tray_icon.py`, SW_HIDE + `[TRAY]` notice), 1-click Desktop Shortcut provisioner (`desktop_shortcut.py`), and interactive autostart profile-target selector (`daemon_autostart.py` + `talos_service.py --profile`). | Complete |
| **v5.18.1** | Autonomous Chaos Hardening, Fault Isolation & Dead Code Decommissioning | Headless/non-interactive TTY hardening (`src/analysis/citation_analyzer.py`), fault-tolerant optional-dependency import guard (`pymed` in `pubmed_source.py`), decommissioning of legacy `pdf_downloader.py` (module inventory 103 -> 102), and an Autonomous Red Tester chaos audit (5 episodes, 95 components, zero unhandled crashes). | Complete |
| **v5.19.0** | Two-Stage Rigor Decoupling & Cognitive SOTA Role Matcher | Two-stage rigor-decoupling `HierarchicalEvaluationEngine` (Stage-1 fast sieve -> Stage-2 Dual-Audit: Faceted Relevance Calibration S_rel_calibrated + Kitchenham 2007 S_qual via PrismaQualityAppraiser) with 2D Evidence Quadrant real-time persistence; 4-role SOTA model matcher (`get_role_based_matrix` / `render_role_matrix` / `apply_recommended_models`); `historic_search` engine unification; `--apply-models` CLI. | Complete |
| **v5.20.0** | Cognitive Meta-Router, SOTA LLM Discovery & Enterprise Console Runbooks | Decoupled `CognitiveMetaRouter` (`src/core/cognitive_router.py`, 4 strategies + circuit breaker + Semaphore(2)), 16-provider registry, `model_benchmark_client` + `--discover-llms`, 4-section enterprise help, `ARCHITECTURE_MAP` (6 zones), Rule 10 Dossier 08. | Complete |
| **v5.21.0** | Cognitive Mesh In-Tree Microservice & Autonomous LLM Scavenger Agent | Extraction-ready `src/services/cognitive_mesh/` (dto/registry/router/benchmarks/scavenger/reporter/server/client) with backward-compatible `src/core/` shims; `ModelScavengerAgent` foraging Hugging Face/OpenRouter/Ollama with hardware-aware VRAM classifier; dual MD/HTML `IntelligenceReporter`; Cognitive Mesh FastAPI mini-server mounted under `/api/v1/cognitive`; `--scavenge-models` CLI + TUI Option 10; Dossier 09. | Complete |
| **v5.21.1** | Decoupled Cognitive Mesh Hardening, Full-Catalog LLM Scavenger, Fuzzy Benchmarks & Auto-Pilot FinOps Configurator | HF full-catalog (top-100 by downloads), OpenRouter full-catalog (`--all`), remote Ollama catalogue, `fuzzy_enrich_benchmarks()` (46-entry pattern table), hardened token-boundary `_classify_model()` classifier, Executive Decision Matrix & FinOps, `LOCAL_FIRST_CLOUD_BACKUP` routing, Auto-Pilot FinOps Configurator (`--configure-ai-strategy`, `--apply-optimal-models`). | Complete |
| **v6.0.0+** | ALEXANDRIA-VII (CORTEX Prime, Standalone Cognitive Microservice & SYNAPSE Event Bus) | Extract the `src/services/cognitive_mesh/` microservice into a standalone SYNAPSE (:8000) service shared between TALOS and MEMEX; Tauri Desktop App, PostgreSQL+pgvector, 3D Knowledge Graphs. | Future |

---

## 13. v6.0.0+ -- Project ALEXANDRIA: The Distributed Ecosystem (FUTURE)

Project ALEXANDRIA marks the full desktop and distributed release of the platform:

| Component | Technology | Description |
|-----------|-----------|-------------|
| **Desktop Application** | Tauri / Electron | 100% standalone offline `.exe` desktop application wrapping React 18 + Shadcn UI |
| **Database Layer** | PostgreSQL + pgvector | High-concurrency vector database replacing local SQLite for multi-user labs |
| **Semantic Knowledge Graphs** | Graphify AST + Leiden | Multi-document topological concept extraction and interactive 3D graph visualization |
| **Offline Deep MoE Reasoning** | Kimi K3 C-Engine | 2.78-Trillion parameter MoE inference running on CPU in 8.24GB RAM for deep offline paper synthesis |
| **Hardware Nexus** | AMD AI Halo (128GB UMA) | High-throughput local research workstation serving as the central compute node for TALOS, ALEXANDRIA, and ATHENA |

---

## 14. Summary Version Table

| Version | Codename | Primary Focus | Status |
|:--------|:---------|:--------------|:-------|
| **v1.0 - v4.11** | The Aggregator | 14-source scraping, Gemini AI evaluation, SQLite storage | Complete |
| **v5.0.0** | The AI Core | Hybrid Embeddings, DDDQN Agent, GWO Hyperparameter Optimizer | Complete |
| **v5.1.0** | The Insights UI | DRL Terminal & Browser Dashboard, GPU Acceleration | Complete |
| **v5.2.0** | The Live Agent | 14-source Dynamic DRL live agent, Onboarding Wizard | Complete |
| **v5.3.x** | Scientific Integrity | GWO v2.0 canonical math, DuelingLSTM extraction, CLI hardening | Complete |
| **v5.4.x** | DDD Migration | Domain-Driven Design package layout (`src/` hierarchy) | Complete |
| **v5.5.x** | REST API Facade | Headless FastAPI backend (14 endpoints, 16 Pydantic models) | Complete |
| **v5.6.0** | Headless Standard | Streamlit fully deprecated, React 18 sole frontend, 15 endpoints | Complete |
| **v5.7.2** | Constitution v2.0 | SYNAPSE Event Bus (:8000), FastAPI port 8001, 15-file sync rule | Complete |
| **v5.8.x** | Multi-Tier TUI | 3-Tier LLM routing, Native MCP Server, Rich TUI Dashboard | Complete |
| **v5.9.x** | Red Team & Mesh | Autonomous Red Tester (Deep Fuzzing), Universal Cloud Mesh (9 Providers), Enterprise Logger | Complete |
| **v5.10.0** | Ingestion Expansion | 16 Academic Sources (+OpenReview, +OpenAIRE), 225 Pytest tests | Complete |
| **v5.10.1** | DRL 17-Actions | 23 State Dimensions, 17 Action Dimensions, Environment Scaling | Complete |
| **v5.10.2** | Sub-Agent & Shaper | `LLMRouterSubAgent` Contextual Bandit, Bi-Level GWO Reward Shaper, 16-Source Checkbox TUI | Complete |
| **v5.10.3** | HMADRL Orchestrator | Hierarchical DRL coupling in Daemon, Live Agent, Search pipelines, Dynamic SWE-bench $Q_p$ | Complete |
| **v5.10.4** | Model Discovery | `ModelDiscoveryEngine`, local JSON cache, 19th REST endpoint (`GET /api/v1/synapse/status`) | Complete |
| **v5.10.5** | Dynamic Provisioner | `ModelProvisioner`, 3-tier path resolution (`FAST_EDGE_MODEL_PATH`), JIT auto-pull, 296 tests | Complete |
| **v5.10.6** | Daemon OS Autostart & Orchestrator | Windows Startup shortcut, daemon pre-flight, source injection | Complete |
| **v5.10.7** | OPTICA Bridge Integration | `OpticaClient` REST client offloading cnsplots/PyVis to OPTICA (8002), TUI plot menu | Complete |
| **v5.10.8** | Enterprise TUI Overhaul & Academic Aesthetics | Unified Cyan/Teal questionary style applied to every CLI prompt | Complete |
| **v5.10.9** | TUI Feature Audit & Profile Management | Hierarchical 16-option TUI, 9 sub-menus, Profile Management restored | Complete |
| **v5.10.10** | Knowledge Constellation Viz | Real-time 3D WebGL visualizer, SSE streaming, 22 endpoints, offline replay | Complete |
| **v5.10.11** | Vendored Three.js Constellation | Three.js r128 vendored, Health Aura Sprites, Print Theme, 1.5s polling bridge | Complete |
| **v5.10.12** | Daemon Hardening, 3D Laser Telemetry & Tools | 60 FPS laser beams, photon pulses, snapshot/fullscreen/help, 1000ms AJAX polling, SQLite VACUUM | Complete |
| **v5.10.13** | Desktop Control Hub, Self-Healing Infrastructure, Active Profile Persistence & Environment Canon Overhaul | System tray control hub, self-healing API auto-bootstrap, active-profile DB persistence, 6-section .env canon | Complete |
| **v5.10.14** | Autonomous Execution Matrix with Privacy Guardrails & DeepSeek V4 Cognitive Integration | auto_dynamic 5th network strategy, Rich privacy consent gate, DeepSeek V4 Pro thinking | Complete |
| **v5.10.15** | Universal TUI Feature Restoration & 100% Codebase Coverage | Unified 6-group hierarchical TUI, 45/45 module coverage, dead sub-menu revival, GWO Swarm suite | Complete |
| **v5.10.16** | Zero-Risk Performance Optimization & Academic LaTeX/BibTeX Engine | SQLite WAL + PRAGMA tuning, safe online snapshotting, HTTP session pooling, deterministic LRU caching, BibTeX/LaTeX exporter | Complete |
| **v5.11.0** | Live Telemetry HUD Console, Win32 Close-to-Tray & Linux Bootstrap | HUD telemetry console, close-to-tray hook, full-title/authors telemetry, JSONL evaluation history, zero-touch Linux bootstrap | Complete |
| **v5.11.1** | TUI Sub-Menu Sanitization & Complete Hierarchy Audit | Questionary choice-list corruption fix, sequential 1-8 renumbering, unified sub-menu back labels | Complete |
| **v5.11.2** | Zero-Click Windows Pre-Flight Onboarding Wizard | 5-step progress-aware setup wizard, silent Miniconda3 bootstrap, `:DISCOVER_CONDA` discovery, sub-1-second fast-path bypass | Complete |
| **v5.11.3** | Ecosystem Integrity & Dependency Alignment | OpenReview V2 fix, 11435 batch circuit breaker, FastAPI lifespan, warning suppression, GWO status check, verifier repair; 7 concurrency fixes sealed | Complete |
| **v5.12.0** | Research Setup Wizard & Cognitive Onboarding | 4-step English-first wizard, local AI auto-spawn with heuristic bypass, first-run sentinel, ISO/IEC 25010 usability | Complete |
| **v5.12.1** | Research Wizard Query Transparency & CLI Fast-Dispatch Engine | Step 1 query-preview table + confirmation gate; CLI fast-dispatch flags (--wizard/--daily/--stats/--help) | Complete |
| **v5.12.2** | Self-Healing AI Manager, 5-Tier Strategy Matrix & Research Wizard Integrity Engine | Self-healing Ollama probe/spawn, 5-tier execution strategy matrix, day-based search windows, cancellation integrity, thinking-model parser, English-first mandate, LOCAL_GPU_MODEL baseline | Complete |
| **v5.12.3** | Research Pivot Modernization & Setup Wizard TUI Integration | research_pivot.py canonical paths + returncode verification, Rule 9 codename elimination, Research Setup Wizard promoted to TUI option 1 | Complete |
| **v5.12.4** | Concurrent Ingestion Mesh & Multi-Profile Research Onboarding | Step 0 profile target gate + ThreadPoolExecutor(16) concurrent harvest, Rich Live telemetry, DOI + title-hash dedup (~35-45s to ~3-4s) | Complete |
| **v5.13.0** | Full-Stack Concurrent Multi-Threaded Engine & High-Throughput Harvester | ThreadPoolExecutor 16-source mesh, concurrent eval pool (8/2), WAL re-evaluation, Rich Live telemetry | Complete |
| **v5.13.1** | System Diagnostics Analyzer & Operational Integrity Engine | 8-point pre-flight health check + Rich health report + one-line remediation; CLI --diagnostics/--doctor; TUI Group 6 option | Complete |
| **v5.14.0** | Stanford DSPy PRISMA-ScR Pipeline & Declarative Synthesis Engine | Typed signatures, PlanEval modules, Mermaid 2020 flowchart, scoping review synthesizer, Rule 10 dossier | Complete |
| **v5.14.1** | Multi-Agent Peer-Review Swarm & Consensus Engine | 3-agent review swarm, Cohen's Kappa, CoT consensus arbiter, swarm screening mode, Rule 10 dossier | Complete |
| **v5.14.2** | BibTeX Scientific Exporter, 18-Source Aerospace Ingestion & Feature Freeze | BibTeX exporter, NASA NTRS + HAL/Inria (18 sources), prisma_decision, Rule 10 dossier 03 | Complete |
| **v5.15.0** | Universal Scientific Search Hub & Neural Graph Discovery Engine | Modular ingestion sources subpackage, citation snowballing, neural vector search (nomic-embed-text), code-first search, CLI + TUI | Complete |
| **v5.15.3** | Session Circuit Breaker, Robust Author Extraction & Daemon Lifecycle Hardening | Session circuit breaker, author normalizer, clean [EVAL] telemetry, silent standalone SYNAPSE buffering | Complete |
| **v5.16.1** | Unified Profile Architecture & Workspace Synchronization Engine | ProfileManager SSOT, uav_mission_planning migration, port 11434 unification | Complete |
| **v5.16.2** | Pluggable Provider Registry & Hardware-Aware Model Advisor | ProviderRegistry (OCP), HardwareModelAdvisor (VRAM budget), SOTA radar, --recommend-models, TUI Option 8 | Complete |
| **v5.16.0** | PRISMA Quality Appraisal & Dual-Axis Scientific Rigor Engine (Kitchenham 2007) | Six-question Kitchenham rubric, S_rel / S_qual decoupling, 2D quadrants, --appraise-quality, SQLite quality columns, BibTeX dual-filter, Rule 10 dossier 05 | Complete |
| **v5.17.0** | Two-Tier Hierarchical Swarm Architecture & Forensic Quality Engine | Tier-2 four-auditor quality swarm, SkillCompiler, SmartSectionSlicer, S_qual + Fleiss kappa, --swarm / --compile-skills, Rule 10 dossier 06 | Complete |
| **v5.18.0** | Ethical Academic PDF Harvester, Smart Section Slicing & SQLite FTS5 Engine | 13-source OA cascade, magic-bytes/SHA-256/atomic-write download, section_extractor, FTS5 engine, --download-pdfs/--fts/--open-pdf, Rule 10 dossier 07 | Complete |
| **v5.19.0** | Two-Stage Rigor Decoupling & Cognitive SOTA Role Matcher | Stage-2 Dual-Audit (S_rel_calibrated + Kitchenham S_qual), 2D Evidence Quadrant persistence, 4-role SOTA matcher, --apply-models | Complete |
| **v5.20.0** | Cognitive Meta-Router, SOTA LLM Discovery & Enterprise Console Runbooks | Decoupled CognitiveMetaRouter (4 strategies), 16 providers, --discover-llms, enterprise help, ARCHITECTURE_MAP, Dossier 08 | Complete |
| **v5.21.0** | Cognitive Mesh In-Tree Microservice & Autonomous LLM Scavenger Agent | Extraction-ready cognitive mesh, ModelScavengerAgent, dual MD/HTML reporter, Cognitive Mesh FastAPI mini-server, --scavenge-models, Dossier 09 | Complete |
| **v5.21.1** | Decoupled Cognitive Mesh Hardening, Full-Catalog LLM Scavenger, Fuzzy Benchmarks & Auto-Pilot FinOps Configurator | HF + OpenRouter full-catalog, fuzzy benchmarks, hardened classifier, Executive Decision Matrix & FinOps, hybrid routing, Auto-Pilot configurator | Complete |
| **v5.20.0** | CORTEX & n8n Gateway | Discord bot, n8n workflow templates, ecosystem integration | Upcoming |
| **v6.0.0+** | Project ALEXANDRIA | Tauri Desktop App, PostgreSQL+pgvector, 3D Knowledge Graphs, Kimi K3 C-Engine | Future |

---

> **Project TALOS** -- From Aggregator to Autonomous Research Architect.
> Built in Greece.
> (C) 2026 Christos Smarlamakis