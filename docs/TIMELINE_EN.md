# Project TALOS -- Historical Timeline (English)

> **Purpose:** This document serves as the authoritative chronological record of all development, research, and architectural milestones for Project TALOS. Every version bump, new feature, and breaking change is recorded here.
>
> **Rule:** After EVERY version bump, this file MUST be updated with the new milestone and its status.
>
> **Last Updated:** 2026-10-07 (v5.25.3 -- Universal 3-Tier Sub-Menu Harmonization, Fixed 120x34 Geometry & Actionable Model Hyperlinks)

---

## Phase 89: Universal 3-Tier Sub-Menu Harmonization, Fixed 120x34 Geometry & Actionable Model Hyperlinks (v5.25.3)

- [x] **Status:** COMPLETED (2026-10-07).

- [x] **Fixed 120x34 Console Geometry** -- `run_talos.bat` (`mode con: cols=120 lines=34`) + `talos.py` programmatic init pin the Windows console for a zero-scroll HUD/body/footer/prompt render.

- [x] **Dynamic Daemon Title** -- `talos_service.py` binds `SetConsoleTitleW` to `TALOS v{TALOS_VERSION} | Autonomous Research Service [{active_profile}]` (imported `TALOS_VERSION`, zero emojis), retiring the hardcoded `v5.22.1`.

- [x] **Phantom CPU Edge Server Retirement** -- the self-hosted `llama_cpp.server` (port 11435) and `CPU_SERVER_PORT` boot-batch launch are removed; local execution is bound strictly to 11434.

- [x] **Canonical Model Hyperlinks** -- `reporter.py` gains `_get_model_canonical_url()` (HF/OpenRouter/Ollama); HTML cards wrap titles in `<a class="model-title-link" target="_blank" rel="noopener noreferrer">` with `.card-badges` flex-wrap and full-width block titles; Markdown champion table uses `[model](url)`.

- [x] **Universal Sub-Menu Harmonization** -- daemon autostart + PRISMA appraisal-mode `questionary.select` lists converted to 3-tier `RichSubmenuRenderer` + `prompt_choice`; `_run_model_discovery()` title `(v5.25.3)` + compact names.

- [x] **Version sync** -- `config/settings.py` (`TALOS_VERSION = "5.25.3"`), `main_api.py`, `server.py`, `talos.py`, launchers, `docker-compose.yml` (`talos:5.25.3`), `CITATION.cff` (5.25.3, 2026-10-07), `tests/test_multi_tier.py`, and all 21 canonical docs to v5.25.3 (2026-10-07).

- [x] **Verification gates passed** -- compileall (0 errors), test_system_integrity, test_talos_version (5.25.3), test_console_dashboard/intelligence_reporter/resilient_gateway (35), port 11435 audit (0), verify_dependency_map --ci (0/0/0), bash -n, UTF-8 scan (0 U+FFFD), README [1]-[20] intact.

---

## Phase 88: Preserve All Information, Hierarchical 3-Tier AI Model Management & Interactive Candidate Selector (v5.25.2)

- [x] **Status:** COMPLETED (2026-10-04).

- [x] **Hierarchical 3-Tier AI Model Management Menu** -- `model_manager.py` (`main()`) rebuilt as a 3-tier Rich panel preserving the full live status snapshot (Ollama Status, Network/Hardware Strategy, Fast/Heavy/Embedding models, Gemini Flash/Pro, DeepSeek, Hugging Face) with six clean actions; duplicate `questionary.select` removed in favor of `RichSubmenuRenderer` + `prompt_choice`.

- [x] **Hierarchical Child Submenus** -- `select_cloud_models()` (10-provider registry), `select_execution_mode()` (Network + Hardware steps), and `select_embedding_model()` all render via `RichSubmenuRenderer`.

- [x] **Interactive Model Candidate Selector** -- `ai_strategy_selector.py` gains `_get_candidates_for_slot()`, `_render_candidate_table()`, `_prompt_candidate_selection()`; `configure_ai_strategy()` manual modes walk four role-slot steps (Screening local/cloud, Reasoning local/cloud) with VRAM/Cost/1k/TTFT/Rigor tables and ENTER-for-champion; AUTO_PILOT stays 1-click.

- [x] **Permanent Port 11435 Purge** -- unified local execution on 11434 with `threading.Semaphore(2)`; zero 11435 in active menus.

- [x] **Descriptive Naming & Markup Leak Fix** -- "Cognitive Mesh & FinOps" -> "AI Models, Strategy & Cost Control"; "FinOps Configurator" -> "Interactive AI Model Selector & Cost Optimizer"; `[dim]` leak in `_run_scavenge_models()` fixed to `console.print()`.

- [x] **Version sync** -- `config/settings.py` (`TALOS_VERSION = "5.25.2"`), `main_api.py`, `talos.py`, launchers, `docker-compose.yml` (`talos:5.25.2`), `CITATION.cff` (5.25.2, 2026-10-04), `tests/test_multi_tier.py`, and all 21 canonical docs to v5.25.2 (2026-10-04).

- [x] **Verification gates passed** -- compileall (0 errors), test_system_integrity, test_talos_version (5.25.2), test_console_dashboard (19), port 11435 audit (0), verify_dependency_map --ci (0/0/0), bash -n, UTF-8 scan (0 U+FFFD), README [1]-[20] intact.

---

## Phase 87: Segmented 3-Column Cockpit HUD, Visual Contrast Optimization & Zero-Scroll Bounding (v5.25.1)

- [x] **Status:** COMPLETED (2026-10-04).

- [x] **Segmented 3-Column Cockpit HUD** -- `hud_renderer.py` (`HudRenderer.build_hud`) rebuilt as a three-column Rich table (RESEARCH CORPUS | LOCAL EDGE & COMPUTE | COGNITIVE AI MESH) under a bright-cyan `TALOS TELEMETRY & SYSTEM COCKPIT (v5.25.1)` title; `_strategy_compact()` (LOCAL_FIRST / AIRGAPPED / CLOUD_BUDGET / AUTO_SWARM) and `_compact_gpu_name()`; zero truncation, zero ellipses.

- [x] **Responsive Layout Bounding** -- `layout_builder.py` header resized to exact content height and the four panels given `ratio=1` splits; full dashboard fits within 26-28 lines, zero scrollbars.

- [x] **HUD unit tests** -- `tests/test_console_dashboard.py` (3-column grid, bright-cyan title, zero truncation).

- [x] **Version sync** -- `config/settings.py` (`TALOS_VERSION = "5.25.1"`), `main_api.py`, `talos.py`, launchers, `docker-compose.yml` (`talos:5.25.1`), `CITATION.cff` (5.25.1, 2026-10-04), `tests/test_multi_tier.py`, and all 21 canonical docs to v5.25.1 (2026-10-04).

- [x] **Verification gates passed** -- compileall (0 errors), test_system_integrity, test_talos_version (5.25.1), test_console_dashboard (19), `--show-dashboard` (exit 0, 3-column HUD, unclipped), verify_dependency_map --ci (0/0/0), bash -n, UTF-8 scan (0 U+FFFD).

---

## Phase 86: Autonomous Multi-LLM Relay, XAI Decision Ledger & Dynamic Swarm Sizing (v5.25.0)

- [x] **Status:** COMPLETED (2026-10-04).

- [x] **XAI Decision Ledger** -- `xai_ledger.py` (`XAiDecisionLedger.append` / `latest` / `explain`) persisting append-only JSONL to `data/cache/xai_decision_log.jsonl`.

- [x] **Dynamic Swarm Sizer & AUTO mode** -- `router.py` (`DynamicSwarmSizer.recommend_swarm`, `RoutingStrategy.AUTO_SWARM_CASCADE`), complexity `C = 0.8 D + 0.15 T + 0.05 S`, `K in {1,2,3,5}`, free-tier frontier cascade.

- [x] **Field-station endpoints** -- `server.py` (`POST /mesh/swarm-recommend`, `GET /mesh/xai-trail`).

- [x] **Codebase documentation subsystem** -- `src/utils/codebase_documenter/` (`CodebaseAstAnalyzer`, `ArchitectureLedger`, `MultiLlmRelayOrchestrator`, `CodebaseDocGenerator`) producing `docs/CODEBASE_DOCUMENTATION_MASTER.md` and standalone `.html`.

- [x] **CLI & palette** -- `--document-codebase [--cascade|--local|--dry-run]`, `--show-xai-log [--limit N]`, `/doc-codebase`, `/xai`.

- [x] **Rule 11 & Rule 12** -- Academic Dual-Use Neutrality and Citation Integrity & Anti-Hallucination codified in `.clinerules`.

- [x] **Confidential Academic Dossier 13** -- `docs/internal/academic/13_MULTI_LLM_STATEFUL_RELAY_CODEBASE_DOCUMENTATION_ISO25010.md` (7 sections).

- [x] **Version sync** -- `config/settings.py` (`TALOS_VERSION = "5.25.0"`), `main_api.py`, `talos.py`, launchers, `docker-compose.yml` (`talos:5.25.0`), `CITATION.cff` (5.25.0, 2026-10-04), `tests/test_multi_tier.py`, and all 21 canonical docs to v5.25.0 (2026-10-04).

- [x] **Verification gates passed** -- compileall (0 errors), test_system_integrity, test_talos_version (5.25.0), test_xai_ledger + test_dynamic_swarm_sizer + test_codebase_documenter (19), `--document-codebase --dry-run` (exit 0), `--show-xai-log` (exit 0), neutrality audit, verify_dependency_map --ci (0/0/0), bash -n, UTF-8 scan (0 U+FFFD).

---

## Phase 85: Enterprise Data Vault, Proactive Token-Bucket Rate Limiter & Distributed JSONL Buffer Sync (v5.24.0)

- [x] **Status:** COMPLETED (2026-10-04).

- [x] **Proactive Token-Bucket Rate Limiter** -- `rate_limiter.py` (`TokenBucketRateLimiter.acquire` / `get_provider_status`), refill `r = RPM/60`, capacity `B`, smooth micro-sleep, Ollama `inf`; wired into `CognitiveMetaRouter`.

- [x] **Distributed JSONL Buffer Sync** -- `buffer_sync.py` (`BufferSyncEngine.ingest_jsonl_buffer` / `export_worker_buffer`) plus `POST /api/v1/cognitive/mesh/sync`.

- [x] **Enterprise Database Vault** -- `database_vault.py` (`verify_integrity` / `create_atomic_snapshot` VACUUM INTO / `restore_snapshot`) plus the startup sentinel in `DatabaseManager.__init__`.

- [x] **CLI & HUD** -- `--backup-db` / `--verify-db` / `--restore-backup` / `--sync-buffer`, `/backup` / `/verify` / `/sync`, HUD badges `Vault: INTEGRITY OK` and `Rate Limiter: ACTIVE`.

- [x] **Rule 9** -- the 8-Pillar ISO/IEC 25010 Software Product Quality Standard codified in `.clinerules`.

- [x] **Confidential Academic Dossier 12** -- `docs/internal/academic/12_ENTERPRISE_DATA_VAULT_PROACTIVE_RATE_LIMITING_ISO25010.md` (7 sections).

- [x] **Version sync** -- `config/settings.py` (`TALOS_VERSION = "5.24.0"`), `main_api.py`, `talos.py`, launchers, `docker-compose.yml` (`talos:5.24.0`), `CITATION.cff` (5.24.0, 2026-10-04), `tests/test_multi_tier.py`, and all 21 canonical docs to v5.24.0 (2026-10-04).

- [x] **Verification gates passed** -- compileall (0 errors), test_system_integrity, test_talos_version (5.24.0), test_rate_limiter + test_buffer_sync + test_database_vault (16), `--verify-db` / `--backup-db` (exit 0), verify_dependency_map --ci (0/0/0), bash -n, UTF-8 scan (0 U+FFFD).

---

## Phase 84: Universal 3-Tier Sub-Menu Architecture, Autonomous Self-Healing API Mesh & Access-Tier Engine (v5.23.0)

- [x] **Status:** COMPLETED (2026-10-04).

- [x] **Universal 3-Tier Sub-Menu Engine** -- `submenu_renderer.py` enforces the ISO/IEC 25010 three-tier layout (Header Summary Panel -> Column-Major two-column body grid with `[01]..[ceil(N/2)]` left / `[ceil(N/2)+1]..[N]` right -> Contextual Navigation Footer) plus a single type-safe `prompt_choice()`; eliminates every duplicate vertical `questionary` list across `talos.py` and `ai_strategy_selector.py`.

- [x] **Self-Healing Circuit Breaker** -- `src/services/cognitive_mesh/self_healing.py` implements the six-state `SelfHealingCircuitBreaker` (`HEALTHY`, `RATE_LIMITED`, `LATCHED`, `UNAUTHORIZED`, `UNREACHABLE`, `HALF_OPEN`) with exponential backoff `T_backoff = min(T0*2^k, Tmax)` (T0=60s, Tmax=600s).

- [x] **API Health Probe Engine** -- `ApiHealthProbeEngine.probe_all()` concurrently pings all 16 providers and emits a `MeshDiagnosticReport`; `--probe-apis` / `--diagnose-mesh` CLI flags and `/probe` palette shortcut surface live telemetry; the HUD renders `Mesh: 16 Providers (Active: X | Free: Y | Latched: Z)`.

- [x] **Access-Tier Engine** -- the four-tier `AccessTier` taxonomy (`LOCAL_NO_KEY`, `CLOUD_ZERO_CONFIG_FREE`, `CLOUD_FREE_TIER_WITH_KEY`, `CLOUD_PAID_API`) classifies all models and endpoints; `CognitiveMetaRouter` auto-fails over to free-tier candidates; the reporter emits tier badges, filter buttons, and a zero-config free models section.

- [x] **Confidential Academic Dossier 11** -- `docs/internal/academic/11_SELF_HEALING_API_MESH_RESILIENCE_ISO25010.md` (7 sections).

- [x] **Version sync** -- `config/settings.py` (`TALOS_VERSION = "5.23.0"`), `main_api.py`, `server.py`, `talos.py`, launchers, `docker-compose.yml` (`talos:5.23.0`), `CITATION.cff` (5.23.0, 2026-10-04), `tests/test_multi_tier.py`, and all 21 canonical docs to v5.23.0 (2026-10-04).

- [x] **Verification gates passed** -- compileall (0 errors), test_system_integrity, test_talos_version (5.23.0), test_self_healing (21), cognitive-mesh suite (62), `--probe-apis` (exit 0), verify_dependency_map --ci (0/0/0), bash -n, UTF-8 scan (0 U+FFFD).

---

## Phase 83: Rich Sub-Menu Modernization, Daemon Profile Binding & Model Scout Terminology Formalization (v5.22.1)

- [x] **Status:** COMPLETED (2026-10-03).

- [x] **Orphan Database Merge** -- `merge_orphan_databases()` in `src/core/database_manager.py` consolidates the legacy `data/talos_research.db` and every non-active `_profiles/*/` database into `_profiles/uav_mission_planning/talos_research.db` with lowercased-DOI first and normalized-title SHA-256 deduplication; auto-runs once per process via `DatabaseManager.__init__`.

- [x] **Strict Daemon Profile Binding** -- `talos_service.py` and `live_agent_orchestrator.py` bind strictly to `get_active_profile_db_path()` and emit the `[DAEMON] Operating exclusively on profile: {active_profile}` banner.

- [x] **HUD & Cockpit Badges** -- `hud_renderer.py` renders `Models: 576 (74 Local | 188 Frontier)`; `layout_builder.py` adds the four dynamic tool-count panel badges.

- [x] **Rich Sub-Menu Engine** -- `submenu_renderer.py` (`RichSubmenuRenderer` / `render_submenu`) upgrades the five primary sub-menus to two-column Rich tables with `[01]`/`[02]` badges and `[00] Back`.

- [x] **Model Scout Formalization** -- `ModelScoutAgent` (primary) with `ModelScavengerAgent` alias; `--scout-models` CLI flag; `/scout` command-palette shortcut; "TALOS Model Scout Intelligence Report" titles.

- [x] **Version sync** -- `config/settings.py` (`TALOS_VERSION = "5.22.1"`), `main_api.py`, `talos.py`, launchers, `docker-compose.yml` (`talos:5.22.1`), `CITATION.cff` (5.22.1, 2026-10-03), `tests/test_multi_tier.py`, and all 21 canonical docs to v5.22.1 (2026-10-03).

- [x] **Verification gates passed** -- compileall (0 errors), test_system_integrity, test_talos_version (5.22.1), test_model_scavenger + test_intelligence_reporter + test_console_dashboard (42), `--scout-models --all --report-only` (exit 0), verify_dependency_map --ci (0/0/0), bash -n, UTF-8 scan (0 U+FFFD).

---

## Phase 82: Full-Spectrum Rich Terminal Dashboard 2.0 & Scientific Console Architecture (v5.22.0)

- [x] **Status:** COMPLETED (2026-10-03).

- [x] **Modular console dashboard subsystem** -- `src/utils/console_dashboard/` (6 files: `__init__`, `hud_renderer`, `layout_builder`, `tree_views`, `progress_monitors`, `terminal_previewer`); 100% of Rich rendering isolated from `talos.py` (Constitution III).

- [x] **Persistent telemetry HUD** -- `HudRenderer.build_hud()` (profile, total/elite/appraised corpus, NVIDIA GPU + VRAM, Ollama :11434 probe, network/hardware strategy, scavenged count).

- [x] **Two-column / four-panel responsive grid** -- `DashboardLayoutBuilder.build_dashboard()` (header HUD + Panels 1-4 + footer command-palette legend; zero vertical scrolling at 105x32).

- [x] **Scientific tree viewers** -- `ScientificTreeViewer` (architecture 6-zone, ATHENA taxonomy, 18-API/16-provider mesh health).

- [x] **Multi-metric progress monitor** -- `create_scientific_progress()` (Spinner / Bar(35) / progress / ETA / rate papers/s / GPU VRAM GB).

- [x] **Terminal previewers** -- `TerminalPreviewer.preview_markdown()` / `.preview_syntax()`.

- [x] **Type-safe command palette** -- `rich.prompt.Prompt.ask()` + `_dispatch_slash_command()` (`/scavenge`, `/audit`, `/fts`, `/config`, `/tree`, `/view`, `/help`, `/quit`); CLI `--show-dashboard`, `--show-tree`, `--preview-report`.

- [x] **Confidential Academic Dossier 10** -- `docs/internal/academic/10_TERMINAL_DASHBOARD_RICH_HMI_ISO25010.md` (7 sections).

- [x] **Version synced** -- `config/settings.py` (`TALOS_VERSION = "5.22.0"`), `main_api.py`, `talos.py`, launchers, `docker-compose.yml` (`talos:5.22.0`), `CITATION.cff` (5.22.0, 2026-10-03), `tests/test_multi_tier.py`, and all 21 canonical docs to v5.22.0 (2026-10-03).

- [x] **Verification gates passed** -- compileall, test_system_integrity, test_talos_version (5.22.0), test_console_dashboard (16), talos.py --show-dashboard/--show-tree/--preview-report, verify_dependency_map --ci (0/0/0), bash -n, UTF-8 scan (0 U+FFFD).

## Phase 81: Decoupled Cognitive Mesh Hardening, Full-Catalog Scavenger, Fuzzy Benchmarks & Auto-Pilot FinOps Configurator (v5.21.1)

- [x] **Status:** COMPLETED (2026-10-03).

- [x] **Hugging Face full-catalog harvester** -- `sort=downloads&direction=-1&limit=100`; parses downloads / likes / author / params / license; `huggingface` always appended to `sources_queried`.

- [x] **OpenRouter full-catalog ingestion** -- `fetch_all` / `window_days <= 0` disables the release-date cutoff (250+ models); `window_days > 0` retains the delta.

- [x] **Remote Ollama library catalogue** -- 20 canonical remote tags (Qwen 2.5, Llama 3.1, DeepSeek-R1, Gemma 2/3, Mistral NeMo, Phi-4, CodeQwen); the previous `>14B` drop removed.

- [x] **Fuzzy benchmark cross-referencing** -- `fuzzy_enrich_benchmarks()` (46-entry pattern table) populates MMLU-Pro / HumanEval / TTFT across Claude, GPT, DeepSeek, Qwen, Llama, Mistral, Gemma.

- [x] **Hardened heuristic classifier** -- unified `_classify_model()` decision tree with token-boundary `_has_token()` (pro / mini / 7b false positives eliminated); frontier = sonnet/opus/r1/reasoner/pro/o1/o3/gpt-4/5/6/405b/nemotron-70b, price >= $3.00/1M, or >= 70B.

- [x] **Executive Decision Matrix & FinOps** -- `_select_champions()` (Local / Cloud / Frontier) + `_finops_cost()` per 1k papers; MD verdict tables + HTML champion cards + vanilla-JS search bar.

- [x] **Hybrid routing** -- `RoutingStrategy.LOCAL_FIRST_CLOUD_BACKUP` (local-first, cloud failover via latching loop).

- [x] **Auto-Pilot FinOps Configurator** -- `configure_ai_strategy()` + `apply_optimal_models()`; CLI `--configure-ai-strategy`, `--apply-optimal-models [--strategy ...]`, `--scavenge-models --all`; TUI Option 10.

- [x] **Version sync** -- 5.21.1 across core files + docker-compose (`talos:5.21.1`) + CITATION.cff (5.21.1, 2026-10-03) + launchers + auxiliary modules + canonical docs (2026-10-03).

- [x] **Verification gates passed** -- compileall (0 errors), test_system_integrity, test_talos_version (5.21.1), 45 hermetic (scavenger + reporter + benchmark client + cognitive router incl. LOCAL_FIRST_CLOUD_BACKUP failover + fuzzy benchmarks), verify_dependency_map --ci (exit 0), bash -n, UTF-8 scan (0 U+FFFD), decoupling grep (0 forbidden imports).

## Phase 80: Cognitive Mesh In-Tree Microservice & Autonomous Model Scavenger Agent (v5.21.0)

- [x] **Status:** COMPLETED (2026-10-03).

- [x] **In-Tree Extraction-Ready Microservice** -- `src/services/cognitive_mesh/` (dto / registry / router / benchmarks / scavenger / reporter / server / client) engineered for frictionless standalone extraction to SYNAPSE (:8000); zero SQLite WAL / PRISMA / CLI imports.

- [x] **Autonomous Model Scavenger Agent** -- `scavenger.py` forages Hugging Face (trending text-generation, permissive licenses), OpenRouter (new-release delta + pricing), and Ollama (GGUF <= 14B); hardware-aware VRAM classifier (LOCAL_OPTIMAL / CLOUD_COST_EFFECTIVE / FRONTIER_REASONING) + 4-role assignment; offline fallback to `llm_benchmarks.json`.

- [x] **Dual Intelligence Reporter** -- `reporter.py` emits `llm_market_intelligence_YYYYMMDD.md` + a 100 percent standalone zero-dependency Dark Theme HTML dashboard (embedded CSS/JS, filter buttons, green/amber/blue VRAM badges).

- [x] **Cognitive Mesh FastAPI mini-server** -- `server.py` mounts `/api/v1/cognitive` in `main_api.py` (`/dispatch`, `/providers`, `/benchmarks`, `/scavenge`, `/health`) and runs standalone on port 8003.

- [x] **Backward-compatible shims** -- `src/core/cognitive_router.py`, `provider_registry.py`, `model_benchmark_client.py` re-export the new namespace (100 percent import compatibility).

- [x] **CLI & TUI** -- `--scavenge-models [--days N] [--report-only]`; TUI Group 1 Option 10; Help Runbook A4.

- [x] **Academic Dossier 09** -- `09_AUTONOMOUS_MODEL_SCAVENGING_MICROSERVICE_ARCHITECTURE.md` (7 sections).

- [x] **Version sync** -- 5.21.0 across core files + docker-compose (`talos:5.21.0`) + CITATION.cff (5.21.0, 2026-10-03) + launchers + auxiliary modules + canonical docs (2026-10-03).

- [x] **Verification gates passed** -- compileall (0 errors), test_system_integrity, test_talos_version (5.21.0), 43 hermetic (scavenger + reporter + provider registry + cognitive router + model benchmark), `--scavenge-models --days 7 --report-only` (exit 0), `--help` (Runbook A4), verify_dependency_map --ci (exit 0), bash -n, UTF-8 scan (0 U+FFFD).

## Phase 79: Cognitive Meta-Router, SOTA LLM Discovery Engine & Enterprise Console Runbooks (v5.20.0)

- [x] **Status:** COMPLETED (2026-10-03).

- [x] **Decoupled Cognitive Meta-Router** -- `src/core/cognitive_router.py` with 4 strategies (LOWEST_LATENCY / REASONING_RIGOR / LOWEST_COST / LOCAL_AIRGAPPED), Pydantic v2 DTOs, circuit breaker + 401/402/429 quota latching, Semaphore(2).

- [x] **16-provider registry** -- SambaNova, Together, Fireworks, DeepInfra, Cohere, Perplexity added; `LLMProvider` enum + `get_available_providers()`.

- [x] **Dynamic SOTA discovery** -- `src/core/model_benchmark_client.py` + `--discover-llms` (exit 0) + `data/cache/llm_benchmarks.json`.

- [x] **Enterprise Console Help** -- 4-section manual (SOP Runbooks / Command Matrix / Diagnostics / Environment).

- [x] **ARCHITECTURE_MAP** -- 6-zone ISO/IEC 25010 decomposition (EN + GR); Zone 5 extraction-ready.

- [x] **Academic Dossier 08** -- `08_COGNITIVE_META_ROUTING_DYNAMIC_DISCOVERY.md` (7 sections); Rule 10 codified in `.clinerules`.

- [x] **Version sync** -- 6 core files + docker-compose (`talos:5.20.0`) + CITATION.cff (5.20.0, 2026-10-03) + metadata + 19 canonical docs to v5.20.0 (2026-10-03).

- [x] **Verification gates passed** -- compileall (0 errors), test_system_integrity, test_talos_version (5.20.0), 31 hermetic (provider registry + cognitive router + model benchmark), `--discover-llms` (exit 0), `--help` (exit 0), verify_dependency_map --ci (exit 0), bash -n, UTF-8 scan (0 U+FFFD).

## Phase 78: Two-Stage Rigor Decoupling & Cognitive SOTA Role Matcher (v5.19.0)

- [x] **Status:** COMPLETED (2026-10-03).

- [x] **Two-Stage Rigor Decoupling Engine** -- `src/core/hierarchical_evaluator.py` upgrades `HierarchicalEvaluationEngine` into a true two-stage pipeline. Stage 1 (Fast Relevance Sieve) yields $S_{rel}^{prelim}$; papers below the escalation gate fast-reject with `evidence_quadrant='METHODOLOGICAL_NOISE'`. Stage 2 runs a Dual-Audit on the heavy tier: Faceted Deep Relevance Calibration ($S_{rel}^{calibrated}$ verifying HMADRL / Dec-POMDP / QMIX swarm + ST-GNN / ST-GAT architectures) and Kitchenham 2007 Quality Appraisal ($S_{qual}$ via `PrismaQualityAppraiser`), mapping each paper onto the 2D Evidence Quadrant and returning `quality_rubric_json` + `critique`.

- [x] **2D Evidence Quadrant real-time persistence** -- `daily_search.py` and `historic_search.py` persist `quality_score`, `quality_rubric_json`, and `evidence_quadrant` via `update_paper_quality()`; `historic_search.py` is fully unified onto the engine.

- [x] **Cognitive SOTA 4-Role Model Matcher** -- `hardware_advisor.py` gains `get_role_based_matrix()` (fast_screening / deep_reasoning_rigor / code_audit_slicing / vector_embeddings), `render_role_matrix()`, and `apply_recommended_models()`; `--apply-models` CLI + TUI Option 8 adoption.

- [x] **Clean console lifecycle** -- `talos_service.py` title bumped to `TALOS v5.19.0 | Autonomous Research Service [{active_profile}]`.

- [x] **Version synced** -- 6 code files + docker-compose.yml (`talos:5.19.0`) + CITATION.cff (5.19.0, 2026-10-03) + metadata + 19 canonical docs to v5.19.0 (2026-10-03).

- [x] **Verification gates passed** -- compileall (0 errors), test_system_integrity, test_talos_version (5.19.0), 53 hermetic tests, `--recommend-models` (exit 0), verify_dependency_map --ci (exit 0), bash -n, UTF-8 scan (0 U+FFFD).

## Phase 77: Hierarchical Evaluation Engine & LLM Router Quota Hardening (v5.18.5)

- [x] **Status:** COMPLETED (2026-10-03).

- [x] **Centralized Hierarchical Evaluation Engine** -- `src/core/hierarchical_evaluator.py` introduces `HierarchicalEvaluationEngine` with a deterministic two-tier escalation pipeline: a Fast 8B Screening Sieve (`evaluate_paper_json(model_type='flash')`) yields $S_{rel}$, and an Escalation Gate promotes papers scoring $S_{rel} >= 6.0$ to the Heavy 14B/cloud Reasoning tier (`model_type='pro'` + Kitchenham $S_{qual}$). `evaluate_batch()` runs a `ThreadPoolExecutor` behind `threading.Semaphore(2)` to protect GPU VRAM. `daily_search.py` and `live_agent_orchestrator.py` now route evaluation through the engine.

- [x] **Cognitive LLM Router Quota Latching** -- `AIManager` latches any cloud provider returning HTTP 402/401 into `exhausted_providers` for the session, skipping them with zero network attempts and routing the next call directly to DeepSeek. Single-notice emission via `_latch_provider_exhausted()`.

- [x] **Clean console lifecycle** -- `talos_service.py` sets the official emoji-free dynamic console title `TALOS v5.18.5 | Autonomous Research Service [{active_profile}]` via `SetConsoleTitleW`.

- [x] **Clean ingestion lifecycle** -- `scigov_source.py` isolates DNS failures (delegating to OSTI coverage, disabled by default) and `dblp_source.py` sanitizes Boolean queries + guards `response.json()` against `JSONDecodeError`.

- [x] **Version synced** -- 6 code files + docker-compose.yml (`talos:5.18.5`) + CITATION.cff (5.18.5, 2026-10-03) + metadata + 19 canonical docs to v5.18.5 (2026-10-03).

- [x] **Verification gates passed** -- compileall, test_system_integrity, test_talos_version (5.18.5), 24 new hermetic tests (hierarchical evaluator / quota latching / DBLP sanitizer / Science.gov DNS), verify_dependency_map --ci (exit 0), bash -n, UTF-8 scan (0 U+FFFD).

## Phase 76: Self-Healing Ingestion Gateway & Autostart Profile Selector (v5.18.4)

- [x] **Status:** COMPLETED (2026-10-03).

- [x] **Overarching Resilient Ingestion Gateway** -- `src/ingestion/resilient_gateway.py` introduces `ResilientIngestionGateway`, a top-level self-healing wrapper for all 18 academic source adapters. `harvest_source()` classifies 401/403/"Developer Inactive"/"Quota Exceeded" failures from raised exceptions or captured stdout, fast-fails without delayed sleep retries, and mirrors IEEE/Elsevier/Springer through OpenAlex (`primary_location.source.publisher_lineage`), normalizing results with `source=<source_key>` preserved. `daily_search.py` and `historic_search.py` route `_harvest_single_source()` through the gateway so every source inherits self-healing.

- [x] **Mandatory autostart profile selection** -- `daemon_autostart.py:main()` makes the Questionary profile selection the first mandatory prompt, cancels cleanly on Ctrl+C, persists `daemon_profile` / `daemon_autostart` into `_profiles/<profile>/config.json`, and embeds `--profile <target>` in `talos_daemon_boot.bat` and the Startup shortcut.

- [x] **Version synced** -- 6 code files + docker-compose.yml (`talos:5.18.4`) + CITATION.cff (5.18.4, 2026-10-03) + metadata + canonical docs to v5.18.4 (2026-10-03).

- [x] **Verification gates passed** -- compileall, test_system_integrity, test_talos_version (5.18.4), test_resilient_gateway (11 hermetic), verify_dependency_map --ci (exit 0), bash -n, UTF-8 scan (0 U+FFFD).

## Phase 75: DRL Dual-Checkpoint Net2Net Surgery & Daemon Profile Provisioning (v5.18.3)

- [x] **Status:** COMPLETED (2026-10-03).

- [x] **Genuine dual-checkpoint Net2Net input tensor surgery** -- `scripts/migrate_d3qn_checkpoint.py` now iterates over BOTH `models/dddqn_trained.pth` and `src/ai/models/dddqn_trained.pth`, expanding `lstm1.weight_ih_l0` to `[512, 25]` and the advantage head to `[19, 32]` / `[19]` (name-based remapping, column-mean prior seeding, Sleep action re-indexed to 18), permanently eliminating `RuntimeError: Expected 23, got 25`; the stale `src/ai/models/` copy migrated 16 -> 18 sources / 23 -> 25 dims / 17 -> 19 actions, while `models/` verified idempotently.

- [x] **Daemon profile provisioning** -- `daemon_autostart.py:select_daemon_profile()` (interactive Questionary selector, default active profile `uav_mission_planning`) embeds `--profile <name>` in the boot batch and Startup link; `talos_service.py --profile <name>` activates the SSOT and prints a dynamic `Version: v5.18.3 | Profile: {active_profile} | Device: {device}` banner.

- [x] **Version synced** -- 6 code files + docker-compose.yml (`talos:5.18.3`) + CITATION.cff (5.18.3, 2026-10-03) + metadata + 19 canonical docs to v5.18.3 (2026-10-03).

- [x] **Verification gates passed** -- compileall, test_system_integrity, test_talos_version (5.18.3), dual-checkpoint forward pass, daemon `--profile` banner, verify_dependency_map --ci (exit 0), bash -n, UTF-8 scan (0 U+FFFD).

## Phase 74: Net2Net DRL Checkpoint Repair, Win32 Close-to-Tray & Desktop Provisioner (v5.18.2)

- [x] **Status:** COMPLETED (2026-10-03).

- [x] **Net2Net DRL checkpoint repair sealed** -- `scripts/migrate_d3qn_checkpoint.py` is confirmed idempotent and the trained checkpoint `models/dddqn_trained.pth` is verified at the 18-source / 25-dim observation space (`lstm1.weight_ih_l0` [512, 25], `A.weight` [19, 32], `A.bias` [19], `state_dim=25`, `action_dim=19`), resolving the PyTorch forward-pass shape mismatch; `TalosDRLAgent(25, 19).act(np.zeros((1, 25)))` executes with zero errors.

- [x] **Win32 close-to-tray hook** -- `src/utils/tray_icon.py:enable_close_to_tray()` subclasses the console WNDPROC and intercepts WM_CLOSE / SC_CLOSE to `ShowWindow(SW_HIDE)` with a single de-duplicated `[TRAY]` notice; `talos_service.py` installs the hook immediately at startup.

- [x] **1-click Desktop Shortcut provisioner** -- `src/utils/desktop_shortcut.py:create_desktop_shortcut()` (PowerShell `WScript.Shell` COM, OneDrive-aware Desktop, `TALOS Research Hub.lnk`), wired via `talos.py --create-shortcut` and a Configuration & Profiles menu entry.

- [x] **Autostart profile-target selector** -- `daemon_autostart.py:select_daemon_profile()` + `talos_service.py --profile <name>` activate the operator-selected SSOT profile on boot.

- [x] **Version synced** -- 6 code files + docker-compose.yml (`talos:5.18.2`) + CITATION.cff (5.18.2, 2026-10-03) + metadata + 19 canonical docs to v5.18.2 (2026-10-03).

- [x] **Verification gates passed** -- compileall, test_system_integrity, test_talos_version (5.18.2), migrate_d3qn_checkpoint (strict load), TalosDRLAgent forward pass, talos.py --create-shortcut, verify_dependency_map --ci (exit 0), bash -n, UTF-8 scan (0 U+FFFD).

## Phase 72: Ethical Academic PDF Harvester & Full-Text FTS5 Engine (v5.18.0)

- [x] **Status:** COMPLETED (2026-10-02).

- [x] **Ethical Academic PDF Harvester** -- `src/ingestion/pdf_harvester/` introduces `resolve_oa_url` (a cascading 13-source legal Open Access resolver: arXiv, TechRxiv, HAL/Inria, NASA NTRS, Elsevier OA, PLOS, PubMed Central, Unpaywall, OpenAlex, Semantic Scholar, CORE, Crossref OA, SSRN), `AcademicPDFHarvester` (six-layer download pipeline: `%PDF-` magic-bytes validation, atomic writes, SHA-256, 20 s timeout, 50 MB cap, 1.5 s polite delay), and `PDFSectionExtractor` (air-gapped `pypdf` text extraction + smart section slicing).

- [x] **SQLite FTS5 full-text engine** -- `src/search/fulltext_search.py` builds the `papers_fts` virtual table, indexes cached bodies, and executes BM25-ranked `MATCH` queries with `snippet()` highlighting rendered in a `box.ROUNDED` Rich table.

- [x] **CLI & TUI** -- `--download-pdfs [--min-score]`, `--fts "<query>"`, and `--open-pdf [paper_id]` flags plus Group 2 and Group 5 menu options; `SmartSectionSlicer` reads cached PDF sections; `papers` schema gains `local_pdf_path` / `pdf_sha256` / `pdf_status`.

- [x] **Rule 10 dossier 07** -- `docs/internal/academic/07_ETHICAL_OPEN_ACCESS_PDF_HARVESTING_FTS.md` (7-section standard, EU Directive 2019/790 TDM framework).

- [x] **Version synced** -- 6 code files + docker-compose.yml (`talos:5.18.0`) + CITATION.cff (5.18.0, 2026-10-02) + metadata + 19 canonical docs to v5.18.0 (2026-10-02).

- [x] **Verification gates passed** -- compileall, `test_pdf_harvester.py` (8 passed), `test_fulltext_search.py` (4 passed), `test_quality_swarm.py`/`test_quality_appraisal.py` (34 passed), `test_system_integrity.py`, `test_talos_version` (5.18.0), `talos.py --help`, `verify_dependency_map.py --ci` (exit 0), `bash -n`, UTF-8 scan (0 U+FFFD).

## Phase 73: Autonomous Chaos Hardening & Fault Isolation (v5.18.1)

- [x] **Status:** COMPLETED (2026-10-03).

- [x] **Headless CLI & TTY hardening** -- `src/analysis/citation_analyzer.py` `main()` now handles `--help`/`-h`, detects non-TTY/`TALOS_HEADLESS` headless mode, and wraps `questionary.select().ask()` in a try/except for `EOFError`/`KeyboardInterrupt`/`Exception`, eliminating the `NoConsoleScreenBufferError` crash the Red Tester surfaced.

- [x] **Fault-tolerant ingestion imports** -- `src/ingestion/sources/pubmed_source.py` guards the optional `pymed` import behind `try/except ImportError` so the 18-source registry never crashes with `ModuleNotFoundError`.

- [x] **Dead code decommissioning** -- legacy `src/ingestion/pdf_downloader.py` removed (superseded by the v5.18.0 PDF Harvester); module inventory 103 -> 102.

- [x] **Autonomous Red Tester chaos audit** -- 5-episode Non-Stationary MAB run across 95 components with clean Q-table updates and zero unhandled crashes.

- [x] **Version synced** -- 6 code files + docker-compose.yml (`talos:5.18.1`) + CITATION.cff (5.18.1, 2026-10-03) + metadata + 19 canonical docs to v5.18.1 (2026-10-03).

- [x] **Verification gates passed** -- compileall, `test_system_integrity.py`, `test_talos_version` (5.18.1), `citation_analyzer.py --help` (exit 0), `red_tester.py 5`, `verify_dependency_map.py --ci` (exit 0), `bash -n`, UTF-8 scan (0 U+FFFD).

## Phase 71: PRISMA Quality Appraisal UX Transparency & Force Re-Appraisal (v5.17.1)

### Status: COMPLETED (2026-10-02)

- [x] **Silent-exit elimination** -- `src/prisma/quality_appraisal.py`: `appraise_candidates_batch()` no longer returns empty when every candidate already carries a `quality_score`. The default path renders an informative Rich panel and re-displays the persisted 2D Evidence Quadrant distribution (`_render_existing_quadrant_distribution`), guaranteeing idempotent, deterministic feedback.
- [x] **Force re-appraisal engine** -- new `force_reappraise: bool = False` parameter selects every candidate (`overall_score >= min_relevance`, ignoring prior `quality_score`), emits a yellow notice, and overwrites `quality_score` / `quality_rubric_json` / `evidence_quadrant` in SQLite WAL.
- [x] **CLI & TUI integration** -- `--appraise-quality [--min-score 7.0] [--swarm] [--force]`; TUI Group 3 Option 15 detects an already-appraised corpus and prompts before a deliberate re-audit, falling back to the quadrant table when declined.
- [x] **Dual-Surface Help sync** -- Panel 1 and web manual Card 6 document `--force` plus the UX-transparency fallback.
- [x] **Version synced** -- 6 core files + docker-compose.yml (`talos:5.17.1`) + CITATION.cff (5.17.1, 2026-10-02) + config.template.json + tray/visualizer/wizard/strategy/diagnostics/bibtex/help metadata + src/prisma/ and src/search/ docstrings + 19 canonical docs to v5.17.1 (2026-10-02).
- [x] **Verification gates passed** -- compileall (0 errors), test_quality_appraisal (17), test_quality_swarm (17), test_system_integrity, test_talos_version (5.17.1), `--help` documents `--force`, verify_dependency_map --ci (exit 0), bash -n, UTF-8 scan (0 U+FFFD).

## Phase 70: Two-Tier Hierarchical Swarm Architecture & Forensic Quality Engine (v5.17.0)

### Status: COMPLETED (2026-10-02)

- [x] **Two-Tier Hierarchical Swarm Architecture** -- `src/prisma/quality_swarm.py` (1,261 lines) formally decouples Tier-1 Thematic Screening (`swarm_evaluators.py`: three reviewer personas emitting INCLUDE/EXCLUDE/UNCERTAIN votes) from Tier-2 Forensic Quality Auditing (four specialized skill auditors scoring the Kitchenham 2007 rubric on admitted candidates). Tier-1 answers "is this study on-topic?"; Tier-2 answers "is this study methodologically trustworthy?".
- [x] **Four specialized forensic skill auditors** -- `TheoryAuditor` (Q1: formal problem formulation, hypotheses, scope), `OperationalAuditor` (Q2: environmental realism, physical disturbances, communication latency, operational rules/safety bounds), `BenchmarkAuditor` (Q3-Q4: 2-3 modern SOTA baselines, >= 5 seeds, confidence intervals, p-values, ablations), `OpenScienceAuditor` (Q5-Q6: public code repository, open benchmark simulator, explicit limitations). Each emits typed Pydantic-v2 results with ternary scores snapped onto the {0.0, 0.5, 1.0} grid plus a named forensic critique.
- [x] **Domain-Agnostic Core Templates & Profile-Compiled Skills** -- `src/prisma/skills/templates/` holds four invariant templates using only `{{RESEARCH_DOMAIN}}` / `{{DOMAIN_CONSTRAINTS}}` placeholders; `SkillCompiler.compile_profile_skills(profile_name, force_recompile)` injects the active profile's `research_topic` / `inclusion_criteria` / `exclusion_criteria`, optionally refines with the hardware-advised heavy model (`qwen2.5:14b` local, `deepseek-reasoner` / `gemini-2.5-flash` cloud), and writes `_profiles/<name>/skills/*.md` behind a zero-cost fast path.
- [x] **SmartSectionSlicer & consensus synthesis** -- heading-regex section extraction with per-auditor target maps, ~300-500 word caps, and abstract fallback; `KitchenhamQualitySynthesizer` dispatches the four auditors concurrently (Semaphore(2) local / 4 workers cloud), computes `S_qual = (10/6) * sum(Q_i)`, the inter-auditor Fleiss `kappa_qual` over banded ratings, the 2D quadrant, and the unified forensic narrative.
- [x] **Appraiser swarm mode & persistence** -- `PrismaQualityAppraiser(appraisal_mode='single'|'swarm')`; `QualityAppraisalResult` gains `appraisal_mode`, `swarm_kappa`, `auditor_critiques`; the extended payload persists into the existing `quality_score` / `quality_rubric_json` / `evidence_quadrant` SQLite columns (zero schema changes).
- [x] **CLI, TUI & dual help** -- `--appraise-quality [--min-score 7.0] [--swarm]` and `--compile-skills [--force]` flags; TUI Group 3 Option 15 mode prompt; Panel 1 + web manual Card 6 updated.
- [x] **Rule 10 dossier 06** -- `docs/internal/academic/06_TWO_TIER_HIERARCHICAL_SWARM_QUALITY.md` (7 sections, 1:1 code traceability, PhD/ICBE 2026 excerpts).
- [x] **Version synced** -- 6 core files + docker-compose.yml (`talos:5.17.0`) + CITATION.cff (5.17.0, 2026-10-02) + config.template.json + tray/visualizer/wizard/strategy/diagnostics/bibtex/help metadata + src/prisma/ and src/search/ docstrings + 19 canonical docs to v5.17.0 (2026-10-02).
- [x] **Verification gates passed** -- compileall (0 errors), test_quality_swarm (17 hermetic), test_quality_appraisal (17 -- backward compatible), test_system_integrity, test_talos_version (5.17.0), `--compile-skills` (UAV profile), `--help`, dossier 06 (0 U+FFFD), verify_dependency_map --ci (exit 0), bash -n, UTF-8 scan (0 U+FFFD).

## Phase 69: Pluggable Provider Registry & Hardware-Aware Model Advisor (v5.16.2)

### Status: COMPLETED (2026-10-02)

- [x] **Pluggable Provider Registry** -- `src/core/provider_registry.py` introduces `ProviderDescriptor` (dataclass) and `ProviderRegistry` implementing the Open-Closed Principle. The registry pre-registers local Ollama plus nine cloud providers (NVIDIA NIM, DeepSeek, Gemini, Groq, Cerebras, Mistral, Hugging Face, OpenRouter, Anthropic) and exposes `register` / `get` / `list_all` / `list_active`; `is_active` is dynamically evaluated from key presence (cloud) or port responsiveness (local Ollama).
- [x] **Hardware-Aware Model Advisor** -- `src/core/hardware_advisor.py` introduces `HardwareModelAdvisor` with `get_hardware_profile()` (`{has_cuda, device_name, total_vram_gb, system_ram_gb, is_laptop_cpu}`), `calculate_vram_budget()` (4-bit piecewise formula: >=11 GB -> 14B, 5.5-11 -> 8B, <5.5/CPU -> 3B), `get_recommendations()` (role-based stack), and `scan_sota_models()` (offline-graceful SOTA radar for Qwen 3/4 and Llama 4).
- [x] **Zero-regression AIManager decoupling** -- `AIManager` consumes the registry via `list_active_providers()` / `get_provider_descriptor()` without touching `OPENAI_COMPATIBLE_REGISTRY`, SDK init loops, circuit breakers, or public method contracts.
- [x] **CLI & TUI** -- `--hardware-advisor` / `--recommend-models` dispatch in `_handle_cli_flags()`; Configuration & Profiles Option 8; Panel 1 help-manual documentation.
- [x] **Version synced** -- 6 core files + docker-compose.yml (`talos:5.16.2`) + CITATION.cff (5.16.2, 2026-10-02) + tray/visualizer/wizard/strategy/diagnostics metadata + src/prisma/ and src/search/ docstrings + 19 canonical docs to v5.16.2 (2026-10-02).
- [x] **Verification gates passed** -- compileall, 18 new hermetic unit tests, test_system_integrity, test_talos_version (5.16.2), `--recommend-models` (RTX 4070 -> 14B budget), verify_dependency_map --ci (exit 0), bash -n, UTF-8 scan (0 U+FFFD).

## Phase 68: Unified Profile Architecture & Workspace Synchronization (v5.16.1)

### Status: COMPLETED (2026-10-02)

- [x] **ProfileManager as the single source of truth** -- `src/core/profile_manager.py` is refactored into a canonical `ProfileManager` class anchored to repo-root `_profiles/` (`Path(__file__).resolve().parents[2]`), exposing `get_profiles_dir()`, `get_active_profile_name()`, `set_active_profile()`, `list_profiles()`, `create_profile()`, `get_active_db_path()`, and `get_active_config_path()`, with backward-compatible module aliases for `talos.py`.
- [x] **DatabaseManager delegation** -- `get_active_profile_db_path()` delegates to `ProfileManager.get_active_db_path()`, collapsing every duplicate path resolver into one.
- [x] **Canonical PhD workspace migration** -- the 5,472-paper corpus (114 elite, 325 quality-appraised) is consolidated into `_profiles/uav_mission_planning/`; `active_profile.txt` points to it; root config locks `research_topic: "Drone Mission Planning (Task Allocation-Path Planning) with DRL and ST-GAT"`.
- [x] **Local AI runtime unification** -- `FAST_EDGE_URL` defaults to 11434, retiring the phantom 11435 fast-edge port; diagnostics/help/manual document 11434 as the Universal Local AI Runtime (GPU/CPU).
- [x] **TUI banner** -- the dashboard header renders `Profile: [uav_mission_planning]` and `Active Research Focus: ...`.
- [x] **Version synced** -- 6 core files + docker-compose.yml (`talos:5.16.1`) + CITATION.cff (5.16.1, 2026-10-02) + tray/visualizer/wizard/strategy/diagnostics metadata + src/prisma/ and src/search/ docstrings + 19 canonical docs to v5.16.1 (2026-10-02).
- [x] **Verification gates passed** -- compileall, test_system_integrity, test_talos_version (5.16.1), Profile SSOT, `--diagnostics` (no 11435), verify_dependency_map --ci (exit 0), bash -n, UTF-8 scan (0 U+FFFD).

## Phase 67: PRISMA Quality Appraisal & Dual-Axis Scientific Rigor Engine (v5.16.0)

### Status: COMPLETED (2026-10-01)

- [x] **Standardized Kitchenham (2007) quality rubric** -- `src/prisma/quality_appraisal.py` ships `KitchenhamRubric` (six three-point categorical questions), `QualityAppraisalResult`, and `PrismaQualityAppraiser`, with a `_normalize_ternary` snap-to-grid normalizer for local-LLM drift.
- [x] **Formal relevance/rigor decoupling** -- `S_qual = (sum(Q_i)/6.0)*10.0` is computed independently of the four-layer `overall_score`; `map_evidence_quadrant()` projects each study onto the 2D Evidence Decision Plane (ELITE_FOUNDATIONAL, IDEA_MINE, METHODOLOGICAL_EXEMPLAR, METHODOLOGICAL_NOISE).
- [x] **Batch quality appraisal** -- `--appraise-quality [--min-score 7.0]` (CLI) and TUI Group 3 Option 15 appraise uncached candidates concurrently via `ThreadPoolExecutor` (`Semaphore(2)` local / 8 Cloud Mesh) and render a Rich quadrant-distribution table.
- [x] **SQLite schema expansion** -- `quality_score REAL`, `quality_rubric_json TEXT`, `evidence_quadrant TEXT` columns added idempotently with a new `update_paper_quality()` helper.
- [x] **BibTeX dual-filter export** -- `export_library(min_quality, quadrant)` plus a `note` field carrying Relevance, Scientific Quality, and Quadrant.
- [x] **Kitchenham IEEE citations [11]-[12]** in `README.md` (EN and mirrored GR section).
- [x] **Rule 10 dossier 05** -- `docs/internal/academic/05_PRISMA_QUALITY_APPRAISAL_KITCHENHAM.md` (7 sections, dual-layer traceability).
- [x] **Version synced** -- 6 core files + docker-compose.yml (`talos:5.16.0`) + CITATION.cff (5.16.0, 2026-10-01) + tray/visualizer/wizard/strategy/diagnostics metadata + src/prisma/ and src/search/ docstrings + 19 canonical docs to v5.16.0 (2026-10-01).
- [x] **Verification gates passed** -- compileall, test_quality_appraisal (17 hermetic), test_system_integrity, test_talos_version (5.16.0), `--appraise-quality` CLI, BibTeX `min_quality=7.5`, `--help` / `GET /help`, README [11]/[12], dossier 0 U+FFFD, verify_dependency_map --ci (exit 0), bash -n, UTF-8 scan (0 U+FFFD).

## Phase 66: Dual-Surface Help System & IEEE Scientific Foundations (v5.15.5)

### Status: COMPLETED (2026-10-01)

- [x] **Dual-Surface Help Architecture** -- `src/utils/help_system.py` renders a four-panel Rich console manual (CLI Fast-Dispatch Flags, Interactive Controls & Navigation, Port Mapping & Services Architecture, Generated Reports & Storage Artifacts), served via `talos.py --help` and TUI Option 7 with an interactive `[O] Open Interactive Web Manual` / `[Enter] Return to Menu` prompt (ISO/IEC 25010 Context of Use).
- [x] **Interactive Web Manual** -- `templates/help_manual.html` (self-contained, zero-CDN, responsive academic dark theme) served at `GET /help` with live search, click-to-copy, structured cards, and dark/print-mode toggle; `GET /manual` issues a 307 redirect. API endpoint count rises 23 -> 25.
- [x] **Formal IEEE Scientific References** -- `README.md` Section 5 (English) and the mirrored Greek "Επιστημονικές Αναφορές & Θεωρητικό Υπόβαθρο" present 10 strictly-formatted IEEE citations ([1]-[10]).
- [x] **TUI & CLI integration** -- `_cli_help_table()` delegates to `help_system.render_help_manual(interactive=False)`; the main menu gains Option 7 (Exit renumbered to 8).
- [x] **Version synced** -- 6 core files + docker-compose.yml (`talos:5.15.5`) + CITATION.cff (5.15.5, 2026-10-01) + tray/visualizer/wizard/diagnostics metadata + src/prisma/ and src/search/ docstrings + 19 canonical docs to v5.15.5 (2026-10-01).
- [x] **Verification gates passed** -- compileall, test_system_integrity, test_talos_version (5.15.5), `talos.py --help` (exit 0), `GET /help` (200) / `GET /manual` (307), verify_dependency_map --ci (exit 0), bash -n, UTF-8 scan (0 U+FFFD).

## Phase 65: DRL Action-Space Expansion & Net2Net Checkpoint Migration (v5.15.4)

### Status: COMPLETED (2026-10-01)

- [x] **DRL action-space expansion to 18 sources** -- `ALL_KNOWN_SOURCES` gains `nasa_ntrs` and `hal_inria`; Gymnasium action space `Discrete(17) -> Discrete(19)` (18 sources + sleep) and observation space 23 -> 25 dims; `_load_source_list()` guarantees the full 18-source list.
- [x] **Net2Net checkpoint surgery** -- `scripts/migrate_d3qn_checkpoint.py` widens the DuelingLSTM advantage head (15 -> 19) and LSTM input layer (21 -> 25) in `models/dddqn_trained.pth`, preserving all trained weights bit-for-bit and optimistically initialising the four new source heads; verified via strict `DuelingLSTM(25, 19).load_state_dict()` (zero mismatch); safety backup `models/dddqn_trained.pth.bak`.
- [x] **18-source profile sync** -- `nasa_ntrs`/`hal_inria` added to `max_results_config` + query keys across `config.json`, `config.template.json`, `_profiles/default_drones/config.json`.
- [x] **Scopus/Elsevier author normalization locked in** -- `normalize_authors()` handles `$`, `@name`/`@surname`, and `given_name`/`surname` with 4-author + et al. truncation.
- [x] **Version synced** -- 6 code files + docker-compose.yml (`talos:5.15.4`) + CITATION.cff (5.15.4, 2026-10-01) + tray/visualizer/wizard/diagnostics metadata + src/prisma/ and src/search/ docstrings + 19 canonical docs to v5.15.4 (2026-10-01).
- [x] **Verification gates passed** -- compileall, test_system_integrity, test_talos_version (5.15.4), DRL model strict load, daemon source detection (18/18), verify_dependency_map --ci (exit 0), bash -n, UTF-8 scan (0 U+FFFD).

## Phase 64: Session-Level Circuit Breaker & Author Extraction Hardening (v5.15.3)

### Status: COMPLETED (2026-09-29)

- [x] **Session-Level Circuit Breaker** -- `AIManager.fast_tier_offline` process-lifetime latch: the first CPU Edge (11435) connection failure latches the tier offline and emits a single one-time notice; every subsequent fast-tier call bypasses port 11435 with ZERO probes, ZERO timeout latency, and ZERO fallback spam, routing directly to local GPU (11434).
- [x] **Robust multi-key author normalization** -- `normalize_authors(paper)` resolves `authors_str` / `authors` (list-of-dicts, list-of-strings) / `author` across the 18-source mesh, eliminating "Unknown Authors" false positives; wired into the daemon (`talos_service.py`) and live orchestrator.
- [x] **Clean daemon [EVAL] telemetry** -- one uncluttered Rich block per real evaluation (`[EVAL] <title> | Authors: <authors> | Score: <X.X>/10 | [<DECISION>] -> DB`), gated on a resolved title.
- [x] **Silent Standalone SYNAPSE buffering** -- `SynapseClient.synapse_available` latches offline on first port-8000 probe and buffers events silently to memory + JSONL (`data/synapse_buffer.jsonl`) with zero per-paper warnings.
- [x] **Version synced** -- 6 code files + docker-compose.yml (`talos:5.15.3`) + CITATION.cff (5.15.3, 2026-09-29) + tray/visualizer/wizard/diagnostics metadata + src/prisma/ and src/search/ docstrings + 19 canonical docs to v5.15.3 (2026-09-29).
- [x] **Verification gates passed** -- compileall, test_system_integrity, test_talos_version (5.15.3), test_session_circuit_breaker (12 passed), verify_dependency_map --ci (exit 0), bash -n, UTF-8 scan (0 U+FFFD).

## Phase 63: Universal Search Hub UX & Reporting Harmonization (v5.15.2)

- [x] **Code-First Search reporting** -- `render_results()` (box.ROUNDED, Rank / Stars / Repository / Description / Topics / GitHub URL, zero emoji) + `export_search_report()` (timestamped `data/reports/code_search/code_search_*.md`); `run()` auto-invokes both.
- [x] **Citation Snowballing reporting** -- `render_genealogy()` (box.ROUNDED, Traversal / Depth / Title / Year-Source / DOI-URL / Relevance) + `export_snowball_report()` (timestamped `data/reports/snowball/snowball_*.md` with Backward + Forward 2024-2026 tables); `run()` auto-invokes both.
- [x] **TUI/CLI JSON dumps eliminated** -- `--code-search` / `--snowball` flags and Group 2 menu options 3/5 invoke `run()` directly; `_render_search_result()` removed.
- [x] **Version synced** -- 6 code files + docker-compose.yml + CITATION.cff + tray/visualizer/wizard/diagnostics metadata + src/prisma/ and src/search/ docstrings + 19 canonical docs to v5.15.2 (2026-09-28).
- [x] **Verification gates passed** -- compileall, test_system_integrity, test_talos_version (5.15.2), --code-search and --snowball smoke tests, verify_dependency_map --ci (exit 0), bash -n, UTF-8 scan (0 U+FFFD).

## Phase 62: Neural Vector Cache & Accelerated Embedding Engine (v5.15.1)

- [x] **Persistent vector cache** -- `paper_embeddings` SQLite table + `get_cached_embeddings` / `save_embeddings_batch` in `src/core/database_manager.py` (BLOB float32, per-model index, ON DELETE CASCADE).
- [x] **Incremental indexing + Rich progress** -- `_index_uncached` renders a live `rich.progress.Progress` bar (ETA + throughput) for the uncached delta; concurrent embedding via `ThreadPoolExecutor`, batched persistence (64).
- [x] **Vectorized matrix cosine similarity** -- `_matrix_rank` computes `S_C(q, D)` for all N papers in one NumPy pass (<50ms).
- [x] **Rich Table presentation** -- `render_results` renders Rank / Similarity (%) / Title / Year-Source / DOI-URL / snippet in `box.ROUNDED`; JSON preserved via `render=False`.
- [x] **Version synced** -- 6 code files + docker-compose.yml + CITATION.cff + tray/visualizer/wizard/diagnostics metadata + src/prisma/ docstrings + 19 canonical docs to v5.15.1 (2026-09-28).
- [x] **Verification gates passed** -- compileall, test_system_integrity, test_talos_version (5.15.1), test_neural_vector_search (mock embeddings), persistent cache smoke test, verify_dependency_map --ci (exit 0), bash -n, UTF-8 scan (0 U+FFFD).

## Phase 61: Universal Scientific Search Hub & Neural Graph Discovery (v5.15.0)

- [x] **Modular ingestion refactor** -- `src/ingestion/sources/` subpackage hosts all 18 adapters behind a unified `SOURCE_REGISTRY`; `daily_search.py` and `historic_search.py` import from it.
- [x] **Citation Snowballing Engine** -- `src/search/citation_snowballing.py` (backward/forward graph traversal, PRISMA relevance filter, genealogy graph, DB import).
- [x] **Neural Vector Search** -- `src/search/neural_vector_search.py` (local `nomic-embed-text`, cosine-similarity ranking, lexical fallback).
- [x] **Code-First Search** -- `src/search/code_first_search.py` (GitHub / PapersWithCode / benchmark reproducibility signals).
- [x] **CLI & TUI integration** -- `--snowball` / `--vector-search` / `--code-search` flags + Group 2 "Universal Search Hub" menu.
- [x] **Rule 10 dossier 04** -- `docs/internal/academic/04_NEURAL_GRAPH_SEARCH_PARADIGMS.md` (7-section, gitignored).
- [x] **Version synced** -- 6 core files + docker-compose.yml + CITATION.cff + tray/visualizer/wizard/diagnostics metadata + src/prisma/ docstrings + 19 canonical docs to v5.15.0 (2026-09-28).
- [x] **Verification gates passed** -- compileall, test_system_integrity, test_talos_version (5.15.0), test_neural_vector_search (mock embeddings), verify_dependency_map --ci (exit 0), bash -n, UTF-8 scan (0 U+FFFD).

## Phase 60: BibTeX Exporter, 18-Source Aerospace Ingestion & Feature Freeze (v5.14.2)

- [x] **BibTeX Scientific Exporter** -- `src/utils/bibtex_exporter.py` ships `BibTeXExporter` (cite keys `AuthorYearTitleKeyword`, LaTeX sanitization, `export_library`/`render_export_summary`, `--export-bib` CLI flag and Group 5 menu option).
- [x] **18-source ingestion** -- `nasa_ntrs_source.py` and `hal_inria_source.py` registered in `SOURCE_REGISTRY` (daily + historic), `max_workers=18`, checkbox TUI and API health map expanded to 18, diagnostics probes added.
- [x] **Persisted PRISMA decision** -- `papers.prisma_decision` column added for the exporter's INCLUDE filter.
- [x] **Rule 10 dossier 03** -- `docs/internal/academic/03_GREY_LITERATURE_AEROSPACE_EXPANSION.md` (7-section, gitignored).
- [x] **Version synced** -- 6 core files + docker-compose.yml + CITATION.cff + tray/visualizer/wizard metadata + src/prisma/ docstrings + 19 canonical docs to v5.14.2 (2026-09-28).
- [x] **Verification gates passed** -- compileall, test_system_integrity, test_talos_version (5.14.2), --export-bib (exit 0), source-factory mocks, verify_dependency_map --ci (exit 0), bash -n, UTF-8 scan (0 U+FFFD).

## Phase 59: Multi-Agent Peer-Review Swarm & Consensus Engine (v5.14.1)

### Status: COMPLETED (2026-09-28)

- [x] **Multi-agent peer-review swarm** -- `src/prisma/swarm_evaluators.py` (AlgorithmicReviewer / EmpiricalReviewer / OperationalReviewer specialized personas).
- [x] **Automated inter-rater reliability** -- `calculate_cohens_kappa()` (Fleiss' multi-rater generalization of Cohen's Kappa) + `cohens_kappa_pairwise()`.
- [x] **Chain-of-Thought consensus arbiter** -- `SwarmConsensusArbiter` (unanimous short-circuit, split adjudication, `ConsensusVerdict`).
- [x] **PRISMA pipeline integration** -- `PrismaEvaluator.evaluation_mode` (`'single'` / `'swarm'`) with VRAM-bounded `ThreadPoolExecutor` and `PrismaExecutor` consensus logging.
- [x] **CLI & TUI integration** -- `--prisma --swarm` flag + Group 3 screening-mode prompt.
- [x] **Rule 10 academic dossier** -- `docs/internal/academic/02_MULTI_AGENT_CONSENSUS_SWARM.md`.
- [x] **Version synced** -- 6 code files + Docker image + CITATION.cff + 19 documentation files to v5.14.1.
- [x] **Verification gates passed** -- compileall, test_system_integrity, test_talos_version (5.14.1), verify_dependency_map, bash -n, UTF-8 scan.

## Phase 58: Stanford DSPy PRISMA-ScR Pipeline (v5.14.0)

### Status: COMPLETED (2026-09-28)

- [x] **Declarative PRISMA-ScR signatures** -- `src/prisma/dspy_signatures.py` (Pydantic-v2 typed schema models mirroring the Stanford DSPy `dspy.Signature` paradigm).
- [x] **PlanEval pipeline modules** -- `src/prisma/dspy_modules.py` (PrismaPlanner / PrismaEvaluator / PrismaEligibilityJudge / PrismaExecutor with 4-phase linear flow and live record counters).
- [x] **PRISMA 2020 Mermaid flowchart generator** -- `src/prisma/mermaid_generator.py` (`generate_prisma_mermaid()` with exact counts).
- [x] **Scoping review synthesizer** -- `src/prisma/scoping_review_synthesizer.py` (Markdown + LaTeX drafts per PRISMA-ScR).
- [x] **CLI & TUI integration** -- `--prisma` fast-dispatch flag + Group 3 Advanced Analysis menu option.
- [x] **Rule 10 academic dossier** -- `docs/internal/academic/01_STANFORD_DSPY_PRISMA_PIPELINE.md` (7-section confidential dossier).
- [x] **Version synced** -- 6 code files + Docker image + CITATION.cff + 19 documentation files to v5.14.0.
- [x] **Roadmap re-aligned** -- CORTEX & n8n -> v5.15.0.
- [x] **Verification gates passed** -- compileall, test_system_integrity, test_talos_version (5.14.0), verify_dependency_map, bash -n, UTF-8 scan.

## Phase 45: Universal TUI Feature Restoration & 100% Codebase Coverage (v5.10.15)

### Status: COMPLETED (2026-08-28)

- [x] **Unified 6-group hierarchical TUI** -- `main_menu()` reorganized into six visually-grouped sections with `TALOS_QUESTIONARY_STYLE`.
- [x] **Revived dead sub-menus** -- `profile_settings_menu()`, `database_data_menu()`, `system_health_menu()` reconnected; new `search_ingestion_menu()`, `analysis_visualization_menu()`, `drl_gwo_menu()`.
- [x] **100% executable module coverage (45/45)** -- every orphaned module wired into the hierarchy.
- [x] **GWO Swarm suite** -- tuner, LLM router reward shaper, and 3D live dashboard unified.
- [x] **Script map hardening** -- `_resolve_script_path()` now raises `FileNotFoundError` on unmapped scripts.
- [x] **Version synced** -- 6 code files + Docker image + CITATION.cff to v5.10.15.
- [x] **Roadmap re-aligned** -- DSPy PRISMA -> v5.10.16; CORTEX & n8n -> v5.10.17.
- [x] **Verification gates passed** -- compileall, test_system_integrity, test_talos_version.

## Phase 44: Autonomous Matrix with Privacy Guardrails & DeepSeek V4 Integration (v5.10.14)

### Status: COMPLETED (2026-08-28)

- [x] **Auto-Dynamic Orchestration (Option 5)** -- `select_execution_mode()` gained `auto_dynamic` with full TUI table/choice/label/summary/env coverage.
- [x] **Privacy Guardrail Resolution Engine** -- `_resolve_strategies(model_type)` collapses `auto_dynamic` at runtime (`_is_network_online`, `_detect_vram_gb`, `_resolve_auto_dynamic`, `_prompt_auto_dynamic_consent`, `_log_auto_matrix`).
- [x] **HARD CONSTRAINT** -- `strict_local` short-circuits before any cloud/auto-dynamic logic.
- [x] **DeepSeek V4 Cognitive Integration** -- `_execute_openai_compatible_request()` injects `thinking` + `reasoning_effort` for DeepSeek V4 models.
- [x] **DeepSeek V4 catalog** -- `deepseek-v4-pro` (SWE-bench 75.0 / MMLU-Pro 82.0) and `deepseek-v4-flash` added to model manager and benchmark registry.
- [x] **Version synced** -- 6 code files + Docker image + CITATION.cff to v5.10.14.
- [x] **Roadmap re-aligned** -- DSPy PRISMA -> v5.10.15; CORTEX & n8n -> v5.10.16.
- [x] **Verification gates passed** -- compileall, test_system_integrity, test_talos_version.

## Phase 43: Desktop Control Hub, Self-Healing Infrastructure & Persistence Guarantee (v5.10.13)

### Status: COMPLETED (2026-08-28)

- [x] **Desktop Control Hub System Tray** -- `src/utils/tray_icon.py` expanded to a seven-item menu (Open 3D Visualizer, Open Reports Folder, Open System Log, Open API Docs (Swagger), Trigger Instant Search Cycle, Show / Hide Console Window, Terminate Daemon); tooltip `"TALOS v5.10.13 | Research Intelligence Mesh"`.
- [x] **Self-Healing Auto-Bootstrap** -- `_is_api_alive(port=8001)` health probe (0.6s timeout) plus `_ensure_api_server()` spawning a hidden `uvicorn src.api.main_api:app --host 127.0.0.1 --port 8001` (CREATE_NO_WINDOW) with up-to-3s polling.
- [x] **Native OS Desktop Bridge** -- cross-platform path openers for `data/reports` and `data/logs/talos_system.log`.
- [x] **Single Point of Truth Database Persistence** -- `DatabaseManager.__init__` defaults `db_path=None` to `get_active_profile_db_path()` (active profile database).
- [x] **Bi-directional 4-State Parabolic Telemetry & Synthetic ID Engine** -- documented the 4-state beam bridge and the synthetic latest-evaluation override (`_live_eval_seq` / `_live_eval_state`).
- [x] **OpenAIRE nested XML/JSON title parsing unwrap** -- `_first()` unwraps `$` / `#text` / `value` dictionary wrappers.
- [x] **Environment Canon Overhaul** -- `example.env` + `.env` reconstructed into six commented sections.
- [x] **Roadmap re-aligned** -- DSPy PRISMA shifted to v5.10.14; CORTEX & n8n Gateway shifted to v5.10.15.
- [x] **Version synced across 6 code files and the canonical documentation set** to v5.10.13.
- [x] **Verification gates passed** -- compileall, test_system_integrity, test_talos_version, db_stats.

## Phase 42: Autonomous Daemon Hardening, 3D Laser Telemetry & Tools (v5.10.12)

### Status: COMPLETED (2026-08-27)

- [x] **3D Animated Laser Beams & Photon Pulses** -- `activeBeams` array with additive-blended `THREE.Line` beams and traveling photon spheres at 60 FPS; sine-envelope opacity, node scale pulse, aura intensification, full disposal on completion.
- [x] **Interactive Visualizer Tools** -- raycaster click-to-fire, SNAPSHOT (PNG `TALOS_3D_Constellation.png`), FULLSCREEN, THEME, HELP modal with keyboard shortcuts (R/T/F/S/Space/1-3).
- [x] **1000ms Pure AJAX State Poller** -- cache-busted `/api/v1/visualizer/state` with no-store headers; refreshes 16 health auras/count badges and fires beams on new evaluation IDs.
- [x] **Active Profile DB Resolution** -- visualizer state resolves `get_active_profile_db_path()` on every request; `POST /api/v1/visualizer/events` updates `_sources_health_state`.
- [x] **SQLite Vacuum Optimizer** -- `src/utils/db_stats.py::optimize_database(db_path)` runs `PRAGMA integrity_check;` + `VACUUM;`.
- [x] **Roadmap re-aligned** -- DSPy PRISMA shifted to v5.10.13; CORTEX & n8n Gateway shifted to v5.10.14.
- [x] **Version synced across 6 code files and the canonical documentation set** to v5.10.12.
- [x] **Verification gates passed** -- compileall, test_system_integrity, test_talos_version.

## Phase 41: Vendored Three.js 3D Constellation Visualizer (v5.10.11)

### Status: COMPLETED (2026-08-24)

- [x] **Vendored Three.js** -- Production-grade Three.js r128 (UMD, MIT) bundle vendored at `static/js/three.min.js`; idempotent `app.mount("/static", StaticFiles(directory="static"))` added to `src/api/main_api.py`. Zero CDN calls.
- [x] **Three.js Visualizer Rebuild** -- `templates/live_foraging_visualizer.html` rebuilt with Three.js: gold icosahedron core, 16 Fibonacci-distributed satellite nodes, Health Aura Sprites (Green/Amber/Red/Cyan), core-to-node connection lines plus neighbor mesh, additive-blended energy laser beam fading over 1.2s.
- [x] **Academic Print Mode** -- THEME toggle switches renderer clear color to white (`0xffffff`) with navy high-contrast HUD for publication screenshots.
- [x] **Live Polling Bridge** -- 1.5-second `GET /api/v1/visualizer/demo-data` polling alongside SSE streaming; resilient fallback.
- [x] **Roadmap re-aligned** -- DSPy PRISMA shifted to v5.10.12; CORTEX & n8n Gateway shifted to v5.10.13.
- [x] **Version synced across 6 code files and 15 documentation files** to v5.10.11.
- [x] **Verification gates passed** -- compileall, test_system_integrity, test_talos_version.
## Phase 40: 3D Holographic Constellation Visualizer (v5.10.10)

### Status: COMPLETED (2026-08-24)

- [x] **3D WebGL 1.0 Visualizer** -- Single-file self-contained HTML (`templates/live_foraging_visualizer.html`) with embedded GLSL shaders, handwritten 3D matrix math library, zero CDN dependencies. Features: 16-satellite orbital constellation, rotating gold icosahedron core, animated energy pulse beams, octahedron lockout cages, ambient particle field, glassmorphism HUD overlay.
- [x] **FastAPI SSE Streaming** -- Three new endpoints: `GET /api/v1/visualizer/live` (HTML), `GET /api/v1/visualizer/stream` (Server-Sent Events with 15s heartbeat), `GET /api/v1/visualizer/demo-data` (50 most recent evaluations). In-memory `queue.Queue` broadcast with `broadcast_visualizer_event()` for thread-safe, non-blocking publication.
- [x] **Multi-Pipeline Event Hooking** -- `daily_search.py` emits `paper_evaluated` after Flash pre-screening and Pro deep analysis. `historic_search.py` emits `paper_evaluated` after Flash evaluation. All emissions are best-effort with graceful ImportError fallback.
- [x] **TUI Integration** -- `_menu_architecture_graphs()` gains "3. 3D Knowledge Constellation Visualizer (Browser)" with FastAPI reachability check, Rich info panel, and `webbrowser.open()` auto-launch.
- [x] **Dual-Mode Operation** -- Live SSE Stream (connects to `/api/v1/visualizer/stream`) and Conference Offline Replay (replays `/api/v1/visualizer/demo-data` with Play/Pause/1x-5x Speed/Timeline scrub).
- [x] **API endpoint count** increased from 19 to 22.
- [x] **Version synced across 6 code files and 15 documentation files** to v5.10.10.
- [x] **Verification gates passed** -- compileall, test_system_integrity, test_talos_version.
## Phase 39: Comprehensive TUI Feature Audit & Profile Management Restoration (v5.10.9)

### Status: COMPLETED (2026-08-23)

- [x] **Hierarchical TUI Refactoring** -- 16-option progressive-disclosure menu across six visual groups (Core Config & Profiles, Search & Ingestion, Advanced Analysis, RL & Daemons, System/DB/Diagnostics, Exit). Nine dedicated sub-menu handler functions added.
- [x] **Profile Management restored** -- `_manage_profiles()` delegates to `src.core.profile_manager` for profile switch/create/view/save operations. Active profile info displayed in Rich console with config and database health.
- [x] **All previously omitted tools restored** -- Daily Search, Historical Search, Grey Literature Miner, PDF Downloader, Citation Analyzer, Knowledge Path Generator, Recommender, Author Profiler, Trend Analyzer, GWO Foraging Tuner, GWO LLM Router Shaper, GWO Live Dashboard, Metadata Enrichment, Recalculate Scores, Re-evaluate Database, DB Health Stats, API Health Check.
- [x] **Profile Manager emoji cleanup** -- all emoji characters removed from print statements; replaced with plain-text markers.
- [x] **DSPy PRISMA shifted to v5.10.11**; CORTEX & n8n Gateway shifted to v5.10.12.
- [x] **Version synced across 6 code files and 15 documentation files** to v5.10.9.
- [x] **Verification gates passed** -- compileall, test_smoke, test_talos_version.
## Phase 38: Enterprise TUI Overhaul & Academic Aesthetics (v5.10.8)

### Status: COMPLETED (2026-08-22)

- [x] **Unified Questionary Theme** -- New canonical `src/utils/ui_theme.py` exporting `TALOS_QUESTIONARY_STYLE` with the Cyan/Teal & Bright White palette (bright-white separators, IEEE blue qmark, cyan/teal `noinherit` selection).
- [x] **Prompt-wide Styling** -- Every `questionary.select`/`checkbox`/`text`/`confirm` across 18 prompt-using modules now passes `style=TALOS_QUESTIONARY_STYLE`.
- [x] **Header Panel Border** -- Top-level Rich panel in `talos.py` now uses `border_style="#006699"`.
- [x] **DSPy PRISMA Postponed** -- shifted to v5.10.9; CORTEX & n8n Gateway shifted to v5.10.10.
- [x] **Version & Documentation Sync** -- v5.10.8 synced across 5 code files and 15 documentation files.

## Phase 37: OPTICA Bridge Integration (v5.10.7)

### Status: COMPLETED (2026-08-21)

- [x] **OPTICA REST Client** -- Added `src/integration/optica_client.py` (`OpticaClient`) so TALOS acts as an API client to Project OPTICA (port 8002), offloading cnsplots/PyVis graphics.
- [x] **Dynamic DB Path Resolution** -- `request_plot()` resolves the active profile database path via `get_active_profile_db_path()` and posts `{data_source, plot_type, journal_template, override_params}` to `{OPTICA_API_BASE}/plot/generate` with graceful connection-error handling.
- [x] **Configuration Expansion** -- `OPTICA_API_BASE` setting added to `config/settings.py`, `config.template.json`, and `example.env`.
- [x] **TUI Entry** -- "Data Visualizations (via OPTICA)" added to the Analysis & Insights menu group with plot-type and journal-template prompts.
- [x] **DSPy PRISMA Postponed** -- shifted to v5.10.8.
- [x] **Version & Documentation Sync** -- v5.10.7 synced across 5 code files and 15 documentation files.

## Phase 36: Daemon OS Autostart Orchestrator (v5.10.6)

- [x] **Windows OS Autostart Generator** -- Added `src/utils/daemon_autostart.py` with `install_windows_autostart()` producing `talos_daemon_boot.bat` and a Startup-folder `.lnk` (pywin32, `shell32.dll,43` icon, minimized window).
- [x] **Interactive Daemon Pre-Flight** -- `talos.py` gains a "Configure Daemon & OS Autostart" option prompting network strategy, target sources, and autostart hook.
- [x] **Daemon Source Injection** -- `_run_live_search()` reads `daemon_target_sources` from `config.json` and forwards them to `talos_live_agent.py --sources`.
- [x] **Version & Documentation Sync** -- v5.10.6 synced across 5 code files and 15 documentation files.

## Phase 35: Universal Dynamic Model Provisioner & Self-Healing Redundancy Engine (v5.10.5)

### Status: COMPLETED (2026-08-15)

- [x] **Universal Dynamic Model Provisioner** -- `src/utils/model_provisioner.py` `ModelProvisioner` with deterministic protocol detection (Ollama colon / HuggingFace slash / cloud prefixes), 3-tier local path resolution (`FAST_EDGE_MODEL_PATH` then in-tree `models/<sanitized_name>` then network), and `ensure_model_available()` for JIT Ollama pull and HuggingFace Hub snapshot download with self-healing fallback.
- [x] **SETUP integration** -- `run_talos.bat` / `run_talos.sh` step [5/5] now executes the provisioner for out-of-the-box fast edge + heavy model provisioning.
- [x] **Model Manager integration** -- `_provision_model()` routes uninstalled Ollama/HuggingFace selections through the provisioner with Rich status feedback.
- [x] **Hermetic tests** -- `tests/test_model_provisioner.py` (22 tests).
- [x] **Sync all 6 code files and 15 documentation files to v5.10.5**.

## Phase 34: Dynamic Model Discovery Engine & SYNAPSE Protocol Interoperability (v5.10.4)

### Status: COMPLETED (2026-08-15)

- [x] **Dynamic Model Discovery Engine** -- `src/ai/llm/model_discovery.py` `ModelDiscoveryEngine` discovers active models across Ollama (GET /api/tags) and cloud providers (NVIDIA NIM, Groq, OpenRouter, Gemini), falling back to the air-gapped `data/model_benchmarks.json` registry; computes `Q_p = raw / max(raw)` normalized quality scores.
- [x] **LLM Router integration** -- `refresh_quality_scores()` / `load_quality_scores()` overrides plus a non-blocking `router_decision` Synapse emission in `select_provider()`.
- [x] **SYNAPSE readiness** -- new `model_discovered` / `router_decision` event types, emission statistics, and `GET /api/v1/synapse/status` endpoint; `daily_search.py` / `ai_manager.py` emit non-blocking `router_decision` events.
- [x] **Hermetic tests** -- `tests/test_model_discovery.py` (15 tests).
- [x] **Sync all 6 code files and 15+ documentation files to v5.10.4**.

## Phase 33: Hierarchical DRL Orchestration - Daemon & Foraging Sub-Agent Integration (v5.10.3)

### Status: COMPLETED (2026-08-14)

- [x] **Live DRL foraging orchestrator integration** -- `evaluate_paper()` in `src/ai/drl/live_agent_orchestrator.py` (v1.3) consults `LLMRouterSubAgent.select_provider()` with task type `foraging_evaluation` before evaluation, logging the routing choice to console and module logger.
- [x] **Autonomous research daemon integration** -- `src/ai/drl/talos_service.py` (v2.1) routes all background paper evaluations through `route_daemon_evaluation()`, logging `[DAEMON/ROUTER]` decisions to `data/logs/talos_system.log`.
- [x] **Search pipeline integration** -- `daily_search.py` and `historic_search.py` query the router via `route_evaluation_provider()` for Fast Edge (`fast_screening`) and Heavy Reasoning (`deep_research`) provider selection.
- [x] **Router enhancements** -- `foraging_evaluation` task modifier and shared `estimate_prompt_tokens()` helper added to `llm_router_subagent.py`.
- [x] **Unit tests** -- new `TestLLMRouterSubAgentPipelineIntegration` and router/estimator tests verify that orchestrator, daemon, and search pipelines invoke `select_provider()`.
- [x] **Sync all 6 code files and 15 documentation files to v5.10.3**.


## Phase 32: LLM Router Sub-Agent, Bi-Level GWO Reward Shaping & Interactive 16-Source Checkbox TUI (v5.10.2)

### Status: COMPLETED (2026-08-14)

- [x] **LLM Router Sub-Agent (`src/ai/drl/llm_router_subagent.py`)** -- `LLMRouterSubAgent` selects the optimal active provider from `models/gwo_llm_router_reward_weights.json` weights (Pareto fallback), scoring quality/latency/cost/rate-limit signals; `AIManager` delegates cloud/legacy provider selection to it.
- [x] **GWO LLM Router Reward Shaper (`src/ai/optimizers/gwo_llm_router_reward_shaper.py`)** -- `GWOLLMRouterRewardShaper` class for Bi-Level Multi-Objective Reward Optimization via canonical GWO; simplex-projected 4D weight vector, inner router evaluation under `R = w_q*Quality - w_l*Latency - w_c*Cost - w_p*Penalty`; exports `models/gwo_llm_router_reward_weights.json`.
- [x] **GWO tuner rename** -- `gwo_rl_optimizer.py` to `gwo_foraging_hyperparameter_tuner.py`; added `GWOForagingHyperparameterTuner` facade; export renamed to `models/gwo_foraging_hyperparameters.json`.
- [x] **Interactive 16-Source Checkbox TUI** -- `questionary.checkbox()` in `talos.py` Options 3a/3b over all 16 sources (pre-selected), passed via `--sources`.
- [x] **Source filtering** -- `SOURCE_REGISTRY` + `build_sources()` + `--sources` argparse in `daily_search.py` / `historic_search.py`.
- [x] **Hermetic tests** -- `tests/test_gwo_llm_router_reward_shaper.py` (6 tests).
- [x] **Sync all 6 code files and 15 documentation files to v5.10.2**.


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

## Phase 46: Zero-Risk Performance Optimization & Academic LaTeX/BibTeX Engine (v5.10.16)

- [x] **SQLite WAL mode + PRAGMA connection factory** in `DatabaseManager` (`busy_timeout=5000`, `cache_size=-64000`, `synchronous=NORMAL`, `temp_store=MEMORY`).
- [x] **Safe online snapshotting** (`snapshot_manager.py`) before VACUUM, re-scoring, and re-evaluation.
- [x] **HTTP session pooling** (`http_client.py`) across 13 ingestion sources and local Ollama/Fast-edge inference.
- [x] **Deterministic LRU caching** on pure routing/provisioning helpers.
- [x] **Zero-dependency academic exporter** (`academic_export.py`) for BibTeX (.bib) and LaTeX (.tex) artifacts.
- [x] **Version synced** across 6 code files, docker-compose.yml, CITATION.cff, and 15+ documentation files to v5.10.16.

## Phase 47: Live Telemetry HUD, Win32 Close-to-Tray & Linux Bootstrap (v5.11.0)

### Status: COMPLETED (2026-09-23)

- [x] **Live Telemetry HUD Console** -- bottom-right glassmorphism stream in `templates/live_foraging_visualizer.html` (40-line ring buffer, auto-scroll, `C`/`L` hotkeys, snapshot auto-hide).
- [x] **Win32 Close-to-Tray Hook** -- `enable_close_to_tray()` subclasses the console WndProc (WM_CLOSE / SC_CLOSE to SW_HIDE) in `src/utils/tray_icon.py`.
- [x] **Full-Title & Authors Telemetry** -- [EVAL] renders full title + normalized authors over a two-line Rich structure; `_sanitize_connection_error()` yields clean English socket errors.
- [x] **Persistent Evaluation History** -- `src/utils/evaluation_history.py` JSONL recorder + `_show_evaluation_history(limit=30)` Rich TUI viewer in `talos.py`.
- [x] **Autonomous Linux Bootstrap** -- `run_talos.sh` `detect_or_install_conda()` + `ensure_talosenv()` for Ubuntu/Debian/Linux Mint.
- [x] **Version synced** -- 6 code files + docker-compose.yml + CITATION.cff + 15 canonical docs to v5.11.0 (2026-09-23).
- [x] **Verification gates passed** -- compileall, test_system_integrity, test_talos_version, bash -n.

## Phase 48: TUI Sub-Menu Sanitization & Complete Hierarchy Audit (v5.11.1)

### Status: COMPLETED (2026-09-24)

- [x] **Questionary choice-list fix** -- `profile_settings_menu()` in `talos.py` rewritten with `questionary.Choice(title=..., value=...)` entries, a `__back__` sentinel, and strictly sequential 1-8 numbering.
- [x] **Routing corrections** -- "1. Manage Profiles" -> `run_script("profile_manager.py", ...)`; "5. Model Discovery (Quality Scoring)" -> in-process `_run_model_discovery()`.
- [x] **Unified sub-menu styling** -- every sub-menu standardized with `[ Back / Return to Main Menu ]` labels and `TALOS_QUESTIONARY_STYLE`.
- [x] **Version synced** -- 6 code files + docker-compose.yml + CITATION.cff + 19 canonical docs to v5.11.1 (2026-09-24).
- [x] **Verification gates passed** -- compileall, test_system_integrity, test_talos_version, bash -n.

## Phase 49: Zero-Click Windows Onboarding & Pre-Flight Engine (v5.11.2)

### Status: COMPLETED (2026-09-26)

- [x] **Progress-aware pre-flight wizard** -- new `:AUTO_PREFLIGHT` routine in `run_talos.bat` with numbered `[Step 1/5]`-`[Step 5/5]` guidance, `[OK]` status ticks, and explicit time estimates for first-time users.
- [x] **Silent Miniconda3 bootstrap** -- automatic ~85 MB download via native `curl.exe -# -fS` and silent `/S` install to `%USERPROFILE%\miniconda3` when no Conda runtime is detected.
- [x] **`:DISCOVER_CONDA` subroutine** -- multi-root + PATH discovery of `condabin\conda.bat` with backwards-compatible back-fill of `CONDA_ACTIVATE_PATH` for all existing menu options.
- [x] **Silent fast-path bypass gate** -- four suppressed startup checks (Conda, talosenv, .env, core package probe) skip the wizard entirely; daily launches reach the main menu in under one second.
- [x] **Batch hardening** -- caret-escaped parentheses inside code blocks, clean `call`/`goto :EOF` stack discipline, strict CRLF verified byte-level (zero lone LF).
- [x] **Version synced** -- 6 code files + docker-compose.yml + CITATION.cff + 19 canonical docs to v5.11.2 (2026-09-26).
- [x] **Verification gates passed** -- compileall, test_system_integrity, test_talos_version, bash -n, label/jump audit, UTF-8 integrity scan.

## Phase 50: Ecosystem Integrity & Dependency Alignment (v5.11.3)

### Status: COMPLETED (2026-09-26)

- [x] **Seven-fix source audit (7/7 verified)** -- non-blocking SSE via `await asyncio.to_thread(_visualizer_event_queue.get, True, 1.0)` (`main_api.py`); cached `_get_db()` singleton on visualizer polling; `TALOS_HEADLESS=1` injected in `_run_scrape_background`/`_run_evaluate_background`; `_scrape_task_lock = threading.Lock()` serializing the `sys.exit` monkey-patch; `semantic_search` top_k clamp (database_manager.py); `_record_beam_event` payload guards; GWO monitor `except Exception` resilience.
- [x] **OpenReview V2 dispatch** -- new `OpenReviewSource._query_notes()` helper: `search_notes(term=)` preferred, `get_notes(content={"title": ...})` fallback, bare `get_notes(limit=)` retry on `TypeError`; 4 new hermetic tests in `tests/test_openreview_source.py`.
- [x] **Fast-Edge batch circuit breaker** -- `AIManager._fast_edge_offline_memo` skips a known-offline port-11435 endpoint for the remainder of the batch with instant GPU (11434) fallback and an `[INFO]` log line.
- [x] **Deprecation elimination** -- FastAPI `lifespan` context manager replaces `@app.on_event("startup")` (zero `on_event` warnings); paired module/message FutureWarning filters silence the `google.generativeai` end-of-support notice.
- [x] **GWO status multi-path check** -- `_show_drl_status` probes foraging/router/legacy GWO artifacts with `Present` vs `Default Baseline Active` messaging.
- [x] **Dependency verifier repair** -- dual-language Section 7 header regex (English + Greek master) + language-tagged fence support (```text) + whitelist expansion; stale `scripts/` paths corrected to `src/utils/`; `--ci` exit 0 restored.
- [x] **Release codification** -- the pre-demo stability hardening (formerly a same-version v5.11.2 patch) is formally sealed under v5.11.3 together with the 5 ecosystem-integrity fixes, with full changelog canon, timeline phase, and capabilities whitepaper section.
- [x] **Version synced** -- 6 code files + docker-compose.yml + CITATION.cff + tray/visualizer/evaluation-history metadata + 19 canonical docs to v5.11.3 (2026-09-26).
- [x] **Verification gates passed** -- compileall, test_system_integrity (zero on_event warnings), test_talos_version, test_openreview_source, verify_dependency_map --ci (exit 0), full multi-tier regression, bash -n, UTF-8 integrity scan (zero U+FFFD glyphs).

---

## Phase 51: Research Setup Wizard & Failsafe Onboarding (v5.12.0)

### Status: COMPLETED (2026-09-27)

- [x] **Research Setup Wizard** -- `src/utils/research_setup_wizard.py` delivers a 4-step, English-first onboarding flow (topic + cognitive validation, execution strategy, search window, first-flight visualizer).
- [x] **Local AI auto-spawn with heuristic bypass** -- probes ports 11434/11435 (0.8s), silent `ollama serve` spawn, bounded 2s wait, deterministic rule-based fallback when offline.
- [x] **2-second scope validation timeout** -- Fast Edge (Llama-3.1-8B / Neutrino-8B) cognitive validation with a hard timeout and sub-domain suggestion fallback.
- [x] **First-run sentinel automation** -- `data/.talos_onboarded` written on completion; `talos.py:main_menu()` auto-invokes the wizard once and fast-boots (<0.3s) thereafter.
- [x] **TUI integration** -- `profile_settings_menu()` option 2 routes to the wizard; `_SCRIPT_MAP` registers it under `utils`.
- [x] **Hermetic tests** -- `tests/test_research_setup_wizard.py` covers sentinel, heuristic validation, and strategy/window persistence.
- [x] **Version synced** -- 6 code files + docker-compose.yml + CITATION.cff + tray/visualizer/evaluation-history metadata + 19 canonical docs to v5.12.0 (2026-09-27).
- [x] **Verification gates passed** -- compileall, test_system_integrity, test_talos_version, test_research_setup_wizard, verify_dependency_map --ci (exit 0), bash -n, UTF-8 integrity scan (zero U+FFFD glyphs).

---

## Phase 52: Research Wizard Query Transparency & CLI Fast-Dispatch (v5.12.1)

### Status: COMPLETED (2026-09-27)

- [x] **Wizard query-transparency table** -- `_render_query_preview()` renders a rounded Rich Table (title "Generated Academic Search Queries") previewing the compiled boolean queries for the top primary sources (arXiv, IEEE Xplore, Scopus (Elsevier), OpenAlex, Semantic Scholar, Springer Link) plus the inclusion/exclusion criteria.
- [x] **User confirmation gate** -- a Questionary confirm ("Proceed with these compiled search parameters?", default True) precedes config.json persistence; declining re-enters the scope prompt, cancelling aborts cleanly.
- [x] **CLI fast-dispatch flags** -- `talos.py` gains `--wizard`, `--daily`, `--stats`, and `--help`/`-h` via `_handle_cli_flags()` / `_cli_help_table()`, each dispatching through `run_script()` and exiting 0.
- [x] **Version synced** -- 6 code files + docker-compose.yml + CITATION.cff + tray/visualizer/evaluation-history/wizard metadata + 19 canonical docs to v5.12.1 (2026-09-27).
- [x] **Verification gates passed** -- compileall, test_system_integrity, test_talos_version, `talos.py --help` (exit 0), verify_dependency_map --ci (exit 0), bash -n, UTF-8 integrity scan (zero U+FFFD glyphs).

---

## Phase 53: Self-Healing AI Manager, 5-Strategy Matrix & Wizard Integrity (v5.12.2)

### Status: COMPLETED (2026-09-27)

- [x] **Self-healing Ollama probe & spawn** -- `probe_local_ollama()` issues a 0.8s `GET /api/tags` pre-flight; `_ensure_local_ollama_runtime()` consults `auto_start_local_llm`, offers a `TALOS_QUESTIONARY_STYLE` confirm, spawns `ollama serve` detached, and polls up to 3.0s before graceful degradation.
- [x] **Provider trimming** -- cloud providers are registered only when their key is present; missing keys are parked silently as `STANDBY_NO_KEY` in a new `provider_status` map (no warning cascades, no network attempts).
- [x] **On-demand cloud key injection** -- `_prompt_cloud_key()` / `_persist_env_key()` / `_register_cloud_provider_on_demand()` securely prompt, validate, persist to `.env`, and register a provider at runtime.
- [x] **Google GenAI GA SDK migration** -- `_execute_gemini_request()` prefers `google.genai` (`GenerateContentConfig`), falling back to legacy `google.generativeai` only when the GA SDK is absent.
- [x] **Heuristic query stopword cleaner** -- `_extract_salient_terms()` strips English stopwords and punctuation noise from fallback boolean queries, capping at 4-6 salient tokens for valid IEEE Xplore / Scopus / arXiv queries.
- [x] **5-Tier execution strategy matrix** -- `EXECUTION_STRATEGIES` + `ai_strategy_selector.py` expose `strict_local` / `local_first` / `cloud_first` / `strict_cloud` (0% GPU VRAM footprint) / `auto_dynamic`, persisted to config.json + .env and exposed via `--strategy [mode]` plus the TUI switcher.
- [x] **Day-based historical search window** -- Step 3 presets (30/365/1095/1825/3650 days) plus custom positive-integer days via `_prompt_custom_days()`, persisting `days_to_search_historic`.
- [x] **Sentinel & cancellation integrity** -- `_render_cancelled()` aborts on any cancellation, eliminates 'N/A' config writes, and guards the `data/.talos_onboarded` sentinel.
- [x] **Thinking/reasoning parser resilience** -- `_strip_thinking_tags()` / `_extract_assistant_content()` unwrap `reasoning_content`, `thinking`, and `<think>` tags.
- [x] **English-first cognitive mandate** -- `LANGUAGE_AND_SYNTAX_MANDATE` enforces academic English and disallows `topic:` prefixes.
- [x] **Local GPU baseline** -- `LOCAL_GPU_MODEL` defaults to verified `llama3.1:8b`.
- [x] **Version synced** -- 6 code files + docker-compose.yml + CITATION.cff + tray/visualizer/evaluation-history/wizard metadata + 19 canonical docs to v5.12.2 (2026-09-27).
- [x] **Verification gates passed** -- compileall, test_system_integrity, test_talos_version, test_research_setup_wizard (28 tests), verify_dependency_map --ci (exit 0), bash -n, UTF-8 integrity scan (zero U+FFFD glyphs).

## Phase 54: Research Pivot Modernization & Wizard Menu Integration (v5.12.3)

### Status: COMPLETED (2026-09-27)

- [x] **Research Pivot canonical path resolution** -- `research_pivot.py` drops the broken `scripts/` subfolder and the stale `src/ai/scripts/query_translator.py` path; a REPO_ROOT-anchored `_SCRIPT_MAP` resolves the Cognitive Query Compiler (`src/ai/llm/query_translator.py`), the re-evaluation script (`src/utils/reevaluate_database.py` / `recalculate_scores.py`), and the DRL trainer (`src/ai/drl/train_agent.py`), all launched with `sys.executable`.
- [x] **Strict subprocess returncode verification** -- the wizard captures `proc.returncode` and reports `YES` only for returncode 0; non-zero codes surface as `FAILED (Code X)` with trailing output, eliminating the previous `YES` on exit code 2.
- [x] **Rule 9 codename elimination** -- lingering `PYTHIA` / `CHIRON` replaced with ISO/IEC 25010 functional terminology (Cognitive Query Compiler / Citation Graph Analyzer) across the Research Pivot Wizard and the Configuration & Profiles TUI menu.
- [x] **Research Setup Wizard TUI promotion** -- `profile_settings_menu()` promotes the wizard to option 1 ("Full Onboarding & Reconfiguration") and renumbers the remaining entries, enabling re-running at any time to re-tune scope, 16 queries, criteria, search window, and AI execution strategy.
- [x] **Version synced** -- 6 code files + docker-compose.yml + CITATION.cff + tray/visualizer/evaluation-history/wizard metadata + 19 canonical docs to v5.12.3 (2026-09-27).
- [x] **Verification gates passed** -- compileall, test_system_integrity, test_talos_version, test_research_setup_wizard (28 tests), verify_dependency_map --ci (exit 0), bash -n, UTF-8 integrity scan (zero U+FFFD glyphs).

## Phase 55: Concurrent Ingestion Mesh & Multi-Profile Research Onboarding (v5.12.4)

### Status: COMPLETED (2026-09-28)

- [x] **Step 0 Profile Target Selection** -- `research_setup_wizard.py:_step0_profile_selection()` gates the wizard with a three-way choice (reconfigure active profile, switch to an existing profile, or create a fresh isolated `_profiles/<name>/` workspace); the header now renders `Target Profile: [<target_profile>]` and the canonical `_profiles/active_profile.txt` marker drives `get_active_profile_db_path()`.
- [x] **Concurrent Academic Ingestion Mesh** -- `daily_search.py` replaces the sequential 16-source loop with `ThreadPoolExecutor(max_workers=min(16, len(enabled_scrapers)))`; each provider runs in `_harvest_single_source()` with strict per-thread exception isolation so a timeout in Science.gov or OSTI never aborts the run.
- [x] **Rich Live concurrency telemetry** -- a live table tracks WAITING / HARVESTING / COMPLETED / FAILED per source with papers-found and elapsed-time columns, closing with a total-time / raw / deduplicated summary panel.
- [x] **DOI + normalized-title-hash deduplication** -- `_deduplicate_papers()` collapses cross-source duplicates on the main thread before DB insertion.
- [x] **Harvest latency reduction** -- from ~35-45s down to ~3-4s.
- [x] **Environment Setup Guides** -- `docs/ENVIRONMENT_SETUP_GUIDE.md` / `_GR.md` documented as the official setup references.
- [x] **Version synced** -- 6 code files + docker-compose.yml + CITATION.cff + tray/visualizer/evaluation-history/wizard metadata + 19 canonical docs to v5.12.4 (2026-09-28).
- [x] **Verification gates passed** -- compileall, test_system_integrity, test_talos_version, test_research_setup_wizard (39 tests), verify_dependency_map --ci (exit 0), bash -n, UTF-8 integrity scan (zero U+FFFD glyphs).

## Phase 57: System Diagnostics Analyzer & Operational Integrity Engine (v5.13.1)

### Status: COMPLETED (2026-09-28)

- [x] **System Diagnostics Analyzer** -- `src/utils/system_diagnostics.py` ships `SystemDiagnosticsEngine` (ISO/IEC 25010 Diagnosability) with an 8-point pre-flight health check (Python env, SQLite integrity/WAL, local AI runtime, port availability, filesystem permissions, .env structure, daemon status, optional network endpoints) and a `box.ROUNDED` Rich health report with one-line remediation guidance.
- [x] **CLI fast-dispatch** -- `--diagnostics` (canonical) and `--doctor`/`-d` (alias) run the analyzer headless and exit 0.
- [x] **TUI Group 6 integration** -- `system_health_menu()` gains Option 1 "System Health & Diagnostic Analyzer"; options renumbered 1-8 to 2-9.
- [x] **Version synced** -- 6 code files + docker-compose.yml + CITATION.cff + tray/visualizer/evaluation-history/wizard metadata + 19 canonical docs to v5.13.1 (2026-09-28).
- [x] **Verification gates passed** -- compileall, test_system_integrity, test_talos_version, --diagnostics/--doctor CLI runs, verify_dependency_map --ci (exit 0), bash -n, UTF-8 integrity scan (zero U+FFFD glyphs).

## Phase 56: Full-Stack Concurrent Multi-Threaded Engine & High-Throughput Harvester (v5.13.0)

### Status: COMPLETED (2026-09-28)

- [x] **Concurrent Cognitive Evaluation Pool** -- `ai_manager.py:batch_evaluate_papers()` / `_resolve_eval_concurrency()` score a batch of papers concurrently; the Cloud Mesh runs 8 workers while local GPU runs 2 workers behind a `threading.Semaphore(2)` VRAM guard, preserving the structured JSON evaluation schema.
- [x] **Concurrent Historical Ingestion Mesh** -- `historic_search.py` adopts the `ThreadPoolExecutor(max_workers=min(16, len(enabled_sources)))` model with `_harvest_single_source()` per-thread stdout redirection, `as_completed()` aggregation, and DOI + SHA-1 title-hash deduplication.
- [x] **Rich Live concurrency telemetry** -- historical harvesting gains a live WAITING / HARVESTING / COMPLETED / FAILED table and a Historical Ingestion Summary panel.
- [x] **Concurrent database re-evaluation** -- `reevaluate_database.py:_apply_evaluation_batch()` drives the concurrent pool and persists results with batched SQLite WAL commits.
- [x] **Latency/throughput gains** -- 8x-10x literature-harvest latency reduction and 5x-8x LLM scoring acceleration.
- [x] **Version synced** -- 6 code files + docker-compose.yml + CITATION.cff + tray/visualizer/evaluation-history/wizard metadata + 19 canonical docs to v5.13.0 (2026-09-28).
- [x] **Verification gates passed** -- compileall, test_system_integrity, test_talos_version, test_research_setup_wizard, verify_dependency_map --ci (exit 0), bash -n, UTF-8 integrity scan (zero U+FFFD glyphs).



---

> **Project TALOS** -- From Aggregator to Autonomous Research Architect.
> Built in Kalamata, Greece.
> (C) 2026 Christos Smarlamakis. All rights reserved.
