# TALOS Codebase Documentation Master

| Attribute | Value |
| --- | --- |
| Version | 5.25.0 |
| Generated | 2026-10-04T13:55:36.107162+03:00 |
| Modules documented | 147 |
| Classes | 150 |
| Functions | 586 |
| Dependency edges | 322 |

## Table of Contents

- [config/settings.py](#config-settings-py)
- [src/ai/drl/drl_agent.py](#src-ai-drl-drl-agent-py)
- [src/ai/drl/drl_networks.py](#src-ai-drl-drl-networks-py)
- [src/ai/drl/drl_trainer.py](#src-ai-drl-drl-trainer-py)
- [src/ai/drl/live_agent_orchestrator.py](#src-ai-drl-live-agent-orchestrator-py)
- [src/ai/drl/live_agent_sources.py](#src-ai-drl-live-agent-sources-py)
- [src/ai/drl/llm_router_subagent.py](#src-ai-drl-llm-router-subagent-py)
- [src/ai/drl/talos_env.py](#src-ai-drl-talos-env-py)
- [src/ai/drl/talos_live_agent.py](#src-ai-drl-talos-live-agent-py)
- [src/ai/drl/talos_service.py](#src-ai-drl-talos-service-py)
- [src/ai/drl/train_agent.py](#src-ai-drl-train-agent-py)
- [src/ai/embeddings/db_embedding_upgrade.py](#src-ai-embeddings-db-embedding-upgrade-py)
- [src/ai/embeddings/embedding_generator.py](#src-ai-embeddings-embedding-generator-py)
- [src/ai/llm/model_discovery.py](#src-ai-llm-model-discovery-py)
- [src/ai/llm/model_manager.py](#src-ai-llm-model-manager-py)
- [src/ai/llm/query_translator.py](#src-ai-llm-query-translator-py)
- [src/ai/llm/research_pivot.py](#src-ai-llm-research-pivot-py)
- [src/ai/optimizers/gwo_foraging_hyperparameter_tuner.py](#src-ai-optimizers-gwo-foraging-hyperparameter-tuner-py)
- [src/ai/optimizers/gwo_live_dashboard.py](#src-ai-optimizers-gwo-live-dashboard-py)
- [src/ai/optimizers/gwo_llm_router_reward_shaper.py](#src-ai-optimizers-gwo-llm-router-reward-shaper-py)
- [src/ai/testing/__init__.py](#src-ai-testing---init---py)
- [src/ai/testing/red_tester.py](#src-ai-testing-red-tester-py)
- [src/analysis/architecture_intelligence_report.py](#src-analysis-architecture-intelligence-report-py)
- [src/analysis/author_profiler.py](#src-analysis-author-profiler-py)
- [src/analysis/author_trajectory_analyzer.py](#src-analysis-author-trajectory-analyzer-py)
- [src/analysis/citation_analyzer.py](#src-analysis-citation-analyzer-py)
- [src/analysis/generate_architecture_graph.py](#src-analysis-generate-architecture-graph-py)
- [src/analysis/generate_baseline_report.py](#src-analysis-generate-baseline-report-py)
- [src/analysis/graphify_adapter.py](#src-analysis-graphify-adapter-py)
- [src/analysis/knowledge_path_generator.py](#src-analysis-knowledge-path-generator-py)
- [src/analysis/recommender.py](#src-analysis-recommender-py)
- [src/analysis/trend_analyzer.py](#src-analysis-trend-analyzer-py)
- [src/api/main_api.py](#src-api-main-api-py)
- [src/api/red_tester_routes.py](#src-api-red-tester-routes-py)
- [src/api/synapse_routes.py](#src-api-synapse-routes-py)
- [src/api/talos_service_api.py](#src-api-talos-service-api-py)
- [src/core/ai_manager.py](#src-core-ai-manager-py)
- [src/core/cognitive_router.py](#src-core-cognitive-router-py)
- [src/core/database_manager.py](#src-core-database-manager-py)
- [src/core/database_vault.py](#src-core-database-vault-py)
- [src/core/hardware.py](#src-core-hardware-py)
- [src/core/hardware_advisor.py](#src-core-hardware-advisor-py)
- [src/core/hierarchical_evaluator.py](#src-core-hierarchical-evaluator-py)
- [src/core/model_benchmark_client.py](#src-core-model-benchmark-client-py)
- [src/core/notifier.py](#src-core-notifier-py)
- [src/core/profile_manager.py](#src-core-profile-manager-py)
- [src/core/provider_registry.py](#src-core-provider-registry-py)
- [src/ingestion/daily_search.py](#src-ingestion-daily-search-py)
- [src/ingestion/data_enricher.py](#src-ingestion-data-enricher-py)
- [src/ingestion/grey_literature_miner.py](#src-ingestion-grey-literature-miner-py)
- [src/ingestion/historic_search.py](#src-ingestion-historic-search-py)
- [src/ingestion/metadata_enricher.py](#src-ingestion-metadata-enricher-py)
- [src/ingestion/pdf_harvester/__init__.py](#src-ingestion-pdf-harvester---init---py)
- [src/ingestion/pdf_harvester/harvester.py](#src-ingestion-pdf-harvester-harvester-py)
- [src/ingestion/pdf_harvester/resolvers.py](#src-ingestion-pdf-harvester-resolvers-py)
- [src/ingestion/pdf_harvester/section_extractor.py](#src-ingestion-pdf-harvester-section-extractor-py)
- [src/ingestion/resilient_gateway.py](#src-ingestion-resilient-gateway-py)
- [src/ingestion/sources/__init__.py](#src-ingestion-sources---init---py)
- [src/ingestion/sources/arxiv_source.py](#src-ingestion-sources-arxiv-source-py)
- [src/ingestion/sources/core_source.py](#src-ingestion-sources-core-source-py)
- [src/ingestion/sources/crossref_source.py](#src-ingestion-sources-crossref-source-py)
- [src/ingestion/sources/dblp_source.py](#src-ingestion-sources-dblp-source-py)
- [src/ingestion/sources/elsevier_source.py](#src-ingestion-sources-elsevier-source-py)
- [src/ingestion/sources/hal_inria_source.py](#src-ingestion-sources-hal-inria-source-py)
- [src/ingestion/sources/ieee_source.py](#src-ingestion-sources-ieee-source-py)
- [src/ingestion/sources/nasa_ntrs_source.py](#src-ingestion-sources-nasa-ntrs-source-py)
- [src/ingestion/sources/openaire_source.py](#src-ingestion-sources-openaire-source-py)
- [src/ingestion/sources/openalex_source.py](#src-ingestion-sources-openalex-source-py)
- [src/ingestion/sources/openarchives_source.py](#src-ingestion-sources-openarchives-source-py)
- [src/ingestion/sources/openreview_source.py](#src-ingestion-sources-openreview-source-py)
- [src/ingestion/sources/osti_source.py](#src-ingestion-sources-osti-source-py)
- [src/ingestion/sources/plos_source.py](#src-ingestion-sources-plos-source-py)
- [src/ingestion/sources/pubmed_source.py](#src-ingestion-sources-pubmed-source-py)
- [src/ingestion/sources/scigov_source.py](#src-ingestion-sources-scigov-source-py)
- [src/ingestion/sources/semantic_scholar_source.py](#src-ingestion-sources-semantic-scholar-source-py)
- [src/ingestion/sources/springer_source.py](#src-ingestion-sources-springer-source-py)
- [src/ingestion/zotero_connector.py](#src-ingestion-zotero-connector-py)
- [src/integration/__init__.py](#src-integration---init---py)
- [src/integration/optica_client.py](#src-integration-optica-client-py)
- [src/integration/synapse_client.py](#src-integration-synapse-client-py)
- [src/integration/visualizer_bridge.py](#src-integration-visualizer-bridge-py)
- [src/mcp_server.py](#src-mcp-server-py)
- [src/prisma/__init__.py](#src-prisma---init---py)
- [src/prisma/dspy_modules.py](#src-prisma-dspy-modules-py)
- [src/prisma/dspy_signatures.py](#src-prisma-dspy-signatures-py)
- [src/prisma/mermaid_generator.py](#src-prisma-mermaid-generator-py)
- [src/prisma/quality_appraisal.py](#src-prisma-quality-appraisal-py)
- [src/prisma/quality_swarm.py](#src-prisma-quality-swarm-py)
- [src/prisma/scoping_review_synthesizer.py](#src-prisma-scoping-review-synthesizer-py)
- [src/prisma/skills/__init__.py](#src-prisma-skills---init---py)
- [src/prisma/swarm_evaluators.py](#src-prisma-swarm-evaluators-py)
- [src/search/__init__.py](#src-search---init---py)
- [src/search/citation_snowballing.py](#src-search-citation-snowballing-py)
- [src/search/code_first_search.py](#src-search-code-first-search-py)
- [src/search/fulltext_search.py](#src-search-fulltext-search-py)
- [src/search/neural_vector_search.py](#src-search-neural-vector-search-py)
- [src/services/__init__.py](#src-services---init---py)
- [src/services/cognitive_mesh/__init__.py](#src-services-cognitive-mesh---init---py)
- [src/services/cognitive_mesh/benchmarks.py](#src-services-cognitive-mesh-benchmarks-py)
- [src/services/cognitive_mesh/buffer_sync.py](#src-services-cognitive-mesh-buffer-sync-py)
- [src/services/cognitive_mesh/client.py](#src-services-cognitive-mesh-client-py)
- [src/services/cognitive_mesh/dto.py](#src-services-cognitive-mesh-dto-py)
- [src/services/cognitive_mesh/rate_limiter.py](#src-services-cognitive-mesh-rate-limiter-py)
- [src/services/cognitive_mesh/registry.py](#src-services-cognitive-mesh-registry-py)
- [src/services/cognitive_mesh/reporter.py](#src-services-cognitive-mesh-reporter-py)
- [src/services/cognitive_mesh/router.py](#src-services-cognitive-mesh-router-py)
- [src/services/cognitive_mesh/scavenger.py](#src-services-cognitive-mesh-scavenger-py)
- [src/services/cognitive_mesh/self_healing.py](#src-services-cognitive-mesh-self-healing-py)
- [src/services/cognitive_mesh/server.py](#src-services-cognitive-mesh-server-py)
- [src/services/cognitive_mesh/xai_ledger.py](#src-services-cognitive-mesh-xai-ledger-py)
- [src/utils/academic_export.py](#src-utils-academic-export-py)
- [src/utils/ai_strategy_selector.py](#src-utils-ai-strategy-selector-py)
- [src/utils/api_health_check.py](#src-utils-api-health-check-py)
- [src/utils/bibtex_exporter.py](#src-utils-bibtex-exporter-py)
- [src/utils/codebase_documenter/__init__.py](#src-utils-codebase-documenter---init---py)
- [src/utils/codebase_documenter/architecture_ledger.py](#src-utils-codebase-documenter-architecture-ledger-py)
- [src/utils/codebase_documenter/ast_analyzer.py](#src-utils-codebase-documenter-ast-analyzer-py)
- [src/utils/codebase_documenter/markdown_html_generator.py](#src-utils-codebase-documenter-markdown-html-generator-py)
- [src/utils/codebase_documenter/relay_orchestrator.py](#src-utils-codebase-documenter-relay-orchestrator-py)
- [src/utils/console_dashboard/__init__.py](#src-utils-console-dashboard---init---py)
- [src/utils/console_dashboard/hud_renderer.py](#src-utils-console-dashboard-hud-renderer-py)
- [src/utils/console_dashboard/layout_builder.py](#src-utils-console-dashboard-layout-builder-py)
- [src/utils/console_dashboard/progress_monitors.py](#src-utils-console-dashboard-progress-monitors-py)
- [src/utils/console_dashboard/submenu_renderer.py](#src-utils-console-dashboard-submenu-renderer-py)
- [src/utils/console_dashboard/terminal_previewer.py](#src-utils-console-dashboard-terminal-previewer-py)
- [src/utils/console_dashboard/tree_views.py](#src-utils-console-dashboard-tree-views-py)
- [src/utils/daemon_autostart.py](#src-utils-daemon-autostart-py)
- [src/utils/db_stats.py](#src-utils-db-stats-py)
- [src/utils/desktop_shortcut.py](#src-utils-desktop-shortcut-py)
- [src/utils/evaluation_history.py](#src-utils-evaluation-history-py)
- [src/utils/frontend_provisioner.py](#src-utils-frontend-provisioner-py)
- [src/utils/generate_docs.py](#src-utils-generate-docs-py)
- [src/utils/help_system.py](#src-utils-help-system-py)
- [src/utils/http_client.py](#src-utils-http-client-py)
- [src/utils/interactive_dashboard.py](#src-utils-interactive-dashboard-py)
- [src/utils/logger.py](#src-utils-logger-py)
- [src/utils/migrate_database_schema.py](#src-utils-migrate-database-schema-py)
- [src/utils/model_provisioner.py](#src-utils-model-provisioner-py)
- [src/utils/recalculate_scores.py](#src-utils-recalculate-scores-py)
- [src/utils/reevaluate_database.py](#src-utils-reevaluate-database-py)
- [src/utils/research_setup_wizard.py](#src-utils-research-setup-wizard-py)
- [src/utils/snapshot_manager.py](#src-utils-snapshot-manager-py)
- [src/utils/system_diagnostics.py](#src-utils-system-diagnostics-py)
- [src/utils/tray_icon.py](#src-utils-tray-icon-py)
- [src/utils/ui_theme.py](#src-utils-ui-theme-py)
- [src/utils/verify_dependency_map.py](#src-utils-verify-dependency-map-py)
- [talos.py](#talos-py)

---

## Module: config/settings.py

**Summary:** Module: settings.py

---

## Module: src/ai/drl/drl_agent.py

**Summary:** Module: drl_agent.py (v2.2 — 18-Source Scaling)

### Classes

- `ReplayMemory` (line 75)
  - Experience replay buffer for the DDQN agent.
  - `__init__(self, capacity)` (line 88)
  - `store(self, transition)` (line 97)
  - `sample(self, batch_size)` (line 106)
  - `__len__(self)` (line 118)
- `TalosDRLAgent` (line 124)
  - Double Dueling DQN agent for TALOS API source selection.
  - `__init__(self, state_dim, action_dim, network_class)` (line 150)
  - `reset_hidden_states(self)` (line 203)
  - `act(self, state, eps)` (line 216)
  - `learn(self)` (line 251)
  - `_soft_update(local_model, target_model, tau)` (line 309)
  - `save(self, path)` (line 327)
  - `load(self, path)` (line 345)

### Dependencies

- src/ai/drl/drl_networks.py
- src/ai/drl/talos_env.py

---

## Module: src/ai/drl/drl_networks.py

**Summary:** Module: drl_networks.py (v1.1)

### Classes

- `DuelingLSTM` (line 30)
  - Dueling LSTM network for the TALOS DRL agent.
  - `__init__(self, input_dim, output_dim)` (line 54)
  - `forward(self, state)` (line 84)

---

## Module: src/ai/drl/drl_trainer.py

**Summary:** Module: drl_trainer.py (v1.4 — DRL Environment Scaling)

### Functions

- `main()` (line 48)

### Dependencies

- src/ai/drl/drl_agent.py
- src/ai/drl/talos_env.py
- src/utils/ui_theme.py

---

## Module: src/ai/drl/live_agent_orchestrator.py

**Summary:** Module: live_agent_orchestrator.py (v1.4 — 18-Source Scaling)

### Functions

- `_get_provider_limits(config)` (line 66)
- `calculate_state(normalized_hour, source_call_counts, source_limits, provider_call_counts, provider_limits, low_score_streak, error_streak, source_names)` (line 100)
- `execute_live_fetch(action, action_map, config)` (line 151)
- `_estimate_prompt_tokens(text)` (line 223)
- `evaluate_paper(paper, ai_manager, provider_call_counts)` (line 239)
- `calculate_reward(score)` (line 335)
- `run_live_loop(agent, action_map, working_source_names, config, ai_manager, verbose, episodes)` (line 353)

### Dependencies

- src/core/hierarchical_evaluator.py
- src/core/profile_manager.py
- src/integration/visualizer_bridge.py
- src/utils/evaluation_history.py

---

## Module: src/ai/drl/live_agent_sources.py

**Summary:** Module: live_agent_sources.py (v1.2)

### Functions

- `import_source_class(source_name)` (line 22)
- `build_source_map(source_names)` (line 71)

---

## Module: src/ai/drl/llm_router_subagent.py

**Summary:** Module: llm_router_subagent.py

### Classes

- `LLMRouterSubAgent` (line 174)
  - Selects the optimal active provider for an LLM inference request.
  - `__init__(self, weights_path)` (line 183)
  - `_normalize(weights_dict)` (line 198)
  - `load_weights(path)` (line 218)
  - `set_weights(self, weights)` (line 242)
  - `estimate_signals(self, prompt_length, task_type)` (line 252)
  - `score_provider(self, signals)` (line 286)
  - `load_quality_scores(self, quality_map)` (line 303)
  - `refresh_quality_scores(self, engine, online)` (line 316)
  - `_emit_router_decision(self, provider, task_type, prompt_length, score)` (line 345)
  - `select_provider(self, prompt_length, task_type, active_providers)` (line 369)

### Functions

- `relative_quality(raw_score)` (line 124)
- `estimate_prompt_tokens(text)` (line 157)

### Dependencies

- src/ai/llm/model_discovery.py
- src/integration/synapse_client.py

---

## Module: src/ai/drl/talos_env.py

**Summary:** Module: talos_env.py (v3.3 — 18-source / 25-dim scaling)

### Classes

- `TalosEnv` (line 159)
  - Gymnasium environment for TALOS API source selection (N sources + sleep).
  - `__init__(self, source_names, source_limits, config)` (line 180)
  - `arxiv_limit(self)` (line 244)
  - `openalex_limit(self)` (line 249)
  - `s2_limit(self)` (line 254)
  - `_get_limit(self, name)` (line 258)
  - `reset(self, seed, options)` (line 266)
  - `step(self, action)` (line 304)
  - `_build_obs(self)` (line 401)
  - `_simulate_score(self)` (line 433)
  - `_score_to_reward(score)` (line 455)

### Functions

- `_load_source_list(config)` (line 66)
- `_try_load_config()` (line 114)
- `_load_source_limits(source_names, config)` (line 134)
- `get_default_state_space()` (line 482)
- `get_default_action_space()` (line 496)

---

## Module: src/ai/drl/talos_live_agent.py

**Summary:** Module: talos_live_agent.py (v3.2 — Batch 2 TUI hardening)

### Functions

- `_parse_args()` (line 47)
- `main()` (line 61)

### Dependencies

- src/ai/drl/drl_agent.py
- src/ai/drl/live_agent_orchestrator.py
- src/ai/drl/live_agent_sources.py
- src/ai/drl/talos_env.py
- src/core/ai_manager.py

---

## Module: src/ai/drl/talos_service.py

**Summary:** Module: talos_service.py (v2.1 — Profile-Aware, Dynamic N Sources)

### Functions

- `_handle_signal(signum, frame)` (line 84)
- `_spawn_fermion_cpu_server(strategy)` (line 134)
- `_terminate_fermion_cpu_server()` (line 174)
- `build_paper_alert(paper_data, source)` (line 195)
- `_is_fresh_paper(paper_meta)` (line 224)
- `should_send_daily_digest(last_sent_date)` (line 282)
- `send_daily_digest(notifier)` (line 305)
- `_save_daily_report(today_discoveries)` (line 327)
- `_get_daemon_router()` (line 359)
- `_log_router_decision(source_name, provider, prompt_length)` (line 376)
- `route_daemon_evaluation(source_name, prompt_length)` (line 402)
- `_load_daemon_target_sources()` (line 421)
- `_run_live_search()` (line 441)
- `_run_daemon_iteration(env, agent, notifier, sleep_action, verbose, epsilon, last_live_search, last_digest_date, papers_discovered, high_score_count)` (line 481)
- `main()` (line 689)

### Dependencies

- config/settings.py
- src/ai/drl/drl_agent.py
- src/ai/drl/llm_router_subagent.py
- src/ai/drl/train_agent.py
- src/core/database_manager.py
- src/core/notifier.py
- src/core/profile_manager.py
- src/integration/visualizer_bridge.py
- src/utils/evaluation_history.py
- src/utils/logger.py
- src/utils/tray_icon.py

---

## Module: src/ai/drl/train_agent.py

**Summary:** Module: train_agent.py (v1.0)

### Classes

- `OfflineTalosEnv` (line 52)
  - Extension of TalosEnv that uses REAL paper scores from the database.
  - `__init__(self, *args, **kwargs)` (line 65)
  - `_load_papers_from_db()` (line 80)
  - `_simulate_score(self)` (line 124)

### Functions

- `main()` (line 145)

### Dependencies

- src/ai/drl/drl_agent.py
- src/ai/drl/talos_env.py
- src/core/database_manager.py

---

## Module: src/ai/embeddings/db_embedding_upgrade.py

**Summary:** Module: db_embedding_upgrade.py (v2.0)

### Functions

- `get_db_path()` (line 35)
- `upgrade_database(db_path)` (line 55)
- `main()` (line 157)

---

## Module: src/ai/embeddings/embedding_generator.py

**Summary:** Module: embedding_generator.py (v4.0 — Multi-Model Seed All)

### Functions

- `load_configuration()` (line 36)
- `generate_for_model(ai_manager, db_manager, model_name, provider_name)` (line 49)
- `main()` (line 106)

### Dependencies

- src/core/ai_manager.py
- src/core/database_manager.py

---

## Module: src/ai/llm/model_discovery.py

**Summary:** Module: model_discovery.py

### Classes

- `ModelDiscoveryEngine` (line 99)
  - Dynamic discovery of active LLM models with air-gapped quality scoring.
  - `__init__(self, registry_path, ollama_url, cloud_endpoints, timeout, emit_events)` (line 111)
  - `_ensure_registry(self)` (line 134)
  - `_load_registry(self)` (line 152)
  - `_http_get_json(self, url, params)` (line 171)
  - `_discover_local_models(self)` (line 195)
  - `_parse_local_tags(data)` (line 205)
  - `_discover_cloud_models(self)` (line 229)
  - `_parse_cloud_models(data, provider)` (line 242)
  - `discover_active_models(self, online)` (line 272)
  - `_enrich_models(models, registry)` (line 317)
  - `get_normalized_quality_scores(self, online)` (line 345)
  - `_compute_quality_scores(active)` (line 366)
  - `get_provider_quality_scores(self, online)` (line 386)
  - `_emit_model_discovered(self, model)` (line 415)

### Functions

- `get_discovery_engine()` (line 442)

### Dependencies

- config/settings.py
- src/integration/synapse_client.py

---

## Module: src/ai/llm/model_manager.py

**Summary:** Module: model_manager.py

### Functions

- `get_ollama_base()` (line 109)
- `check_ollama_alive()` (line 114)
- `get_installed_models()` (line 128)
- `get_available_tags(model_name)` (line 145)
- `get_quantized_variants(model_base_name)` (line 201)
- `_categorize_tags(tags, base, installed_full)` (line 249)
- `pull_model(full_name)` (line 305)
- `_provision_model(model_name)` (line 343)
- `_fits_label(fits, size_gb, vram_limit)` (line 402)
- `_confirm_setting_change(env_path, key_name, old_value, new_value)` (line 428)
- `_browse_and_pick_ollama_model(vram_gb, vram_limit, env_path, current_model_key)` (line 484)
- `_pick_quantization(model_name, vram_limit, installed_models)` (line 635)
- `_install_if_needed(final_model, installed_models, vram_limit)` (line 750)
- `select_fast_edge_model(env_path)` (line 790)
- `select_heavy_model(env_path)` (line 874)
- `get_cloud_provider_rows(values)` (line 977)
- `select_cloud_models(env_path)` (line 1002)
- `select_execution_mode(env_path)` (line 1093)
- `select_embedding_model(env_path)` (line 1383)
- `main()` (line 1483)

### Dependencies

- config/settings.py
- src/core/hardware.py
- src/utils/model_provisioner.py
- src/utils/ui_theme.py

---

## Module: src/ai/llm/query_translator.py

**Summary:** Module: query_translator.py (v2.3 - Final with Override)

### Functions

- `load_config()` (line 36)
- `save_config(config, path)` (line 44)
- `flatten_json(y)` (line 49)
- `main()` (line 88)

### Dependencies

- src/core/ai_manager.py
- src/utils/ui_theme.py

---

## Module: src/ai/llm/research_pivot.py

**Summary:** Module: research_pivot.py

### Functions

- `get_active_profile_name()` (line 62)
- `save_state_to_profile(profile_name)` (line 70)
- `_resolve_script_path(script_name)` (line 86)
- `run_script(script_name, stdin_text, args)` (line 103)
- `main()` (line 138)

### Dependencies

- src/utils/logger.py
- src/utils/ui_theme.py

---

## Module: src/ai/optimizers/gwo_foraging_hyperparameter_tuner.py

**Summary:** Module: gwo_foraging_hyperparameter_tuner.py (v2.1 — GWOForagingHyperparameterTuner)

### Classes

- `GWOForagingHyperparameterTuner` (line 276)
  - Class-based facade for the GWO DRL hyperparameter tuner.
  - `__init__(self, wolves, iterations, rl_episodes, live)` (line 291)
  - `optimize(self)` (line 306)

### Functions

- `_build_history_entry(iteration, wolves, best_wolves, wolves_number, fitness_values)` (line 59)
- `decode_wolf(wolf_position)` (line 82)
- `calculate_fitness(wolf_position)` (line 89)
- `find_best_three_wolves(wolves_positions)` (line 139)
- `update_wolf_position(wolf_pos, dim, best_wolves, a_factor)` (line 152)
- `_write_live_progress(iteration, max_iters, best_reward, best_fitness, a_factor, status)` (line 174)
- `run_gwo(wolves_number, max_iterations, live)` (line 187)
- `main()` (line 321)

### Dependencies

- src/ai/drl/drl_agent.py
- src/ai/drl/talos_env.py

---

## Module: src/ai/optimizers/gwo_live_dashboard.py

**Summary:** Module: gwo_live_dashboard.py (v1.0 — Dash Live GWO Visualizer)

### Functions

- `update_dashboard(n_intervals)` (line 73)

---

## Module: src/ai/optimizers/gwo_llm_router_reward_shaper.py

**Summary:** Module: gwo_llm_router_reward_shaper.py

### Classes

- `GWOLLMRouterRewardShaper` (line 90)
  - Bi-Level GWO optimizer for the LLM Router reward weights.
  - `__init__(self, wolves, iterations, eval_episodes, seed)` (line 107)
  - `_project_simplex(vector)` (line 128)
  - `_evaluate_router(self, weights)` (line 146)
  - `_fitness(self, weights)` (line 187)
  - `_update_position(self, wolf, dim, alpha, beta, delta, a_factor)` (line 198)
  - `optimize(self)` (line 241)
  - `_models_dir()` (line 309)
  - `export(self, result)` (line 320)
  - `run(self)` (line 370)

### Functions

- `main()` (line 406)

### Dependencies

- src/ai/drl/llm_router_subagent.py

---

## Module: src/ai/testing/__init__.py

**Summary:** Module: __init__.py

### Dependencies

- src/ai/testing/red_tester.py

---

## Module: src/ai/testing/red_tester.py

**Summary:** Module: red_tester.py

### Functions

- `_make_clickable_path(path_str)` (line 67)
- `_safe_str(output)` (line 79)
- `_get_ai_manager()` (line 112)
- `_get_synapse_emitter()` (line 125)
- `_discover_all_targets()` (line 145)
- `_build_api_fuzzing_arms()` (line 187)
- `_load_q_table()` (line 276)
- `_save_q_table(q_table)` (line 295)
- `_protect_context_window(text, max_chars)` (line 311)
- `_diagnose_crash(component_name, command, stderr)` (line 332)
- `_execute_arm(arm)` (line 373)
- `_execute_cli_arm(display_name, script_path, args)` (line 394)
- `_execute_api_arm(display_name, request_spec)` (line 444)
- `_select_arm(q_table)` (line 511)
- `_save_crash_report(display_name, command, stdout, stderr, diagnosis, q_table, arm_index)` (line 538)
- `_build_q_table_panel(q_table)` (line 626)
- `_run_test_cycle(q_table, cycle, total_cycles)` (line 679)
- `run_red_tester(cycles)` (line 806)

### Dependencies

- src/core/ai_manager.py
- src/integration/synapse_client.py

---

## Module: src/analysis/architecture_intelligence_report.py

**Summary:** Module: architecture_intelligence_report.py (v1.0)

### Functions

- `load_config()` (line 47)
- `collect_data()` (line 58)
- `build_prompt(data, language)` (line 105)
- `generate_report(data, language, config)` (line 171)
- `main()` (line 201)

### Dependencies

- src/core/ai_manager.py

---

## Module: src/analysis/author_profiler.py

**Summary:** Module: author_profiler.py (v3.9 - Intelligent Input & Final)

### Classes

- `UnifiedProfiler` (line 44)
  - `__init__(self, mailto_email)` (line 45)
  - `_is_orcid(self, identifier)` (line 57)
  - `_query_api(self, url, source_name, headers, params)` (line 61)
  - `_query_orcid_search(self, author_name)` (line 71)
  - `_query_openalex(self, orcid_id)` (line 77)
  - `_get_doi_from_work(self, work_summary)` (line 81)
  - `run(self, identifier)` (line 89)
  - `display_unified_dossier(self, name, orcid_id, oa_data, ss_data, works)` (line 155)
  - `export_to_markdown(self, search_term, name, orcid_id, oa_data, ss_data, works)` (line 187)

### Dependencies

- src/utils/ui_theme.py

---

## Module: src/analysis/author_trajectory_analyzer.py

**Summary:** Module: author_trajectory_analyzer.py (v3.2 - Unified Input)

### Classes

- `TrajectoryAnalyzer` (line 42)
  - `__init__(self, config)` (line 43)
  - `_query_api(self, url, source_name, headers)` (line 52)
  - `get_author_data(self, orcid_id)` (line 61)
  - `analyze_trajectory(self, author_name, works)` (line 70)
  - `_is_orcid(self, identifier)` (line 91)
  - `run(self, identifier)` (line 95)

### Dependencies

- src/analysis/author_profiler.py
- src/core/ai_manager.py

---

## Module: src/analysis/citation_analyzer.py

**Summary:** Module: citation_analyzer.py (v2.1 - Robust Interactive Selection)

### Functions

- `get_paper_identifier(user_input)` (line 44)
- `analyze_paper_list(ai_manager, papers, analysis_type, config)` (line 51)
- `create_interactive_citation_graph(target_paper, references, citations, output_path)` (line 73)
- `get_target_paper_from_user(db_manager)` (line 117)
- `main()` (line 178)

### Dependencies

- src/core/ai_manager.py
- src/core/database_manager.py
- src/ingestion/sources/semantic_scholar_source.py
- src/utils/ui_theme.py

---

## Module: src/analysis/generate_architecture_graph.py

**Summary:** Module: generate_architecture_graph.py (v2.0)

### Functions

- `extract_imports(py_file)` (line 138)
- `classify_module(module_name)` (line 167)
- `get_module_label(module_name, layer)` (line 176)
- `scrape_all_imports()` (line 185)
- `build_elements(raw_imports)` (line 200)
- `embed_data_in_html(elements, html_path, stats)` (line 371)
- `main()` (line 390)

---

## Module: src/analysis/generate_baseline_report.py

**Summary:** Module: generate_baseline_report.py (v1.1 — Academic Style)

### Functions

- `apply_academic_style()` (line 75)
- `resolve_db_path()` (line 106)
- `load_dataframe(db_path)` (line 129)
- `load_embedding_stats(db_path)` (line 151)
- `compute_metrics(df)` (line 183)
- `plot_score_distribution(df, outdir, academic)` (line 220)
- `plot_layer_averages(df, outdir, academic)` (line 266)
- `plot_source_distribution(df, outdir, academic)` (line 305)
- `plot_embedding_distribution(embedding_stats, outdir, academic)` (line 351)
- `generate_markdown(metrics, embedding_stats, plot_paths, outdir, timestamp)` (line 394)
- `generate_html(metrics, embedding_stats, plot_paths, outdir, timestamp)` (line 478)
- `main()` (line 578)

---

## Module: src/analysis/graphify_adapter.py

**Summary:** Module: graphify_adapter.py

### Functions

- `generate_ast_knowledge_graph(target_dir)` (line 44)
- `_inject_light_mode_toggle(output_dir)` (line 403)

---

## Module: src/analysis/knowledge_path_generator.py

**Summary:** Module: knowledge_path_generator.py (v1.9 - Final Bugfix)

### Classes

- `KnowledgePathGenerator` (line 41)
  - The KnowledgePathGenerator class is responsible for generating a structured knowledge path based on a user's learning goal.
  - `__init__(self, config)` (line 60)
  - `_get_user_goal(self)` (line 73)
  - `_find_relevant_papers(self, goal_text, top_k)` (line 87)
  - `_extract_keywords_for_filename(self, goal_text)` (line 101)
  - `_get_top_keywords_for_cluster(self, vectorizer, kmeans_model, cluster_id, top_n)` (line 112)
  - `_structure_knowledge(self, df, num_clusters, min_score)` (line 119)
  - `_synthesize_narrative(self, structured_knowledge, user_goal)` (line 148)
  - `_save_report(self, topic_keywords, narrative_report)` (line 176)
  - `run(self)` (line 198)

### Dependencies

- src/core/ai_manager.py
- src/core/database_manager.py
- src/utils/ui_theme.py

---

## Module: src/analysis/recommender.py

**Summary:** Module: recommender.py (v4.1 - Structured Reports Update)

### Classes

- `ReadingRecommender` (line 50)
  - Αναλύει τα άρθρα της βάσης δεδομένων του TALOS, εφαρμόζει μηχανική μάθηση
  - `__init__(self, db_name)` (line 56)
  - `load_papers_from_db(self)` (line 64)
  - `get_top_keywords_for_cluster(self, vectorizer, kmeans_model, cluster_id, top_n)` (line 81)
  - `_clean_abstract(self, text)` (line 88)
  - `run_analysis_and_reporting(self, num_clusters, min_score)` (line 97)
  - `_print_structured_report(self, foundational, hot, clusters)` (line 149)
  - `_paper_to_dict(self, row)` (line 171)
  - `export_structured_reports(self, foundational, hot, clusters, all_papers)` (line 192)
  - `_export_structured_html(self, found, hot, clusters, top50, timestamp)` (line 211)
  - `_export_structured_docx(self, found, hot, clusters, top50, timestamp)` (line 350)
  - `_export_structured_markdown(self, found, hot, clusters, top50, timestamp)` (line 401)

---

## Module: src/analysis/trend_analyzer.py

**Summary:** Module: trend_analyzer.py (v1.0 - Scientometrics Module)

### Classes

- `TrendAnalyzer` (line 50)
  - `__init__(self, db_path)` (line 51)
  - `load_data(self)` (line 56)
  - `fig_to_base64(self, fig)` (line 82)
  - `generate_plots(self, df)` (line 91)
  - `generate_html_report(self, plots, count)` (line 172)

### Functions

- `main()` (line 296)

---

## Module: src/api/main_api.py

**Summary:** Module: main_api.py

### Classes

- `PaperSummary` (line 498)
  - Mirrors get_all_papers_for_dashboard() columns.
- `PaperDetail` (line 518)
  - Full row from get_single_paper_details() -- all columns.
- `PaginatedPapers` (line 554)
  - Paginated response wrapper.
- `SemanticSearchRequest` (line 562)
  - Request body for semantic search.
- `SemanticSearchResponse` (line 572)
  - Response from semantic search.
- `ScrapeRequest` (line 579)
  - Optional source filter for scraping.
- `GWORunRequest` (line 587)
  - GWO hyperparameter optimization parameters.
- `GWOResult` (line 594)
  - Result from a completed GWO run.
- `TaskStatus` (line 604)
  - Status of a background task.
- `SystemHealth` (line 615)
  - System health check response.
- `TranslateQueryRequest` (line 624)
  - Request body for natural-language-to-boolean query translation.
- `TranslateQueryResponse` (line 629)
  - Response from query translation -- flattened dict of source keys -> boolean queries.
- `AuthorSummary` (line 635)
  - A single author with their publication count in the database.
- `EvaluatePaperRequest` (line 641)
  - Optional model preference for single-paper evaluation.

### Functions

- `lifespan(app)` (line 105)
- `_get_project_root()` (line 174)
- `_load_config()` (line 179)
- `_get_db()` (line 196)
- `_get_ai()` (line 207)
- `_create_task()` (line 226)
- `_update_task(task_id, **kwargs)` (line 241)
- `broadcast_visualizer_event(event_type, payload)` (line 258)
- `_source_has_key(slug)` (line 319)
- `_record_source_status(payload)` (line 336)
- `_record_beam_event(event_type, payload)` (line 375)
- `health_check()` (line 653)
- `list_papers(page, page_size)` (line 679)
- `get_paper(paper_id)` (line 703)
- `semantic_search(request)` (line 715)
- `_run_scrape_background(task_id, source_filter)` (line 768)
- `trigger_scrape(background_tasks, request)` (line 832)
- `_run_gwo_background(task_id, wolves, iterations, rl_episodes)` (line 860)
- `trigger_gwo(background_tasks, request)` (line 936)
- `get_task_status(task_id)` (line 968)
- `list_tasks()` (line 980)
- `_run_evaluate_background(task_id, paper_id, model_type)` (line 996)
- `evaluate_paper_endpoint(paper_id, background_tasks, request)` (line 1060)
- `_flatten_json_for_translation(y)` (line 1082)
- `translate_query(request)` (line 1107)
- `list_top_authors(limit)` (line 1154)
- `_run_recalculate_background(task_id)` (line 1182)
- `recalculate_scores_endpoint(background_tasks)` (line 1242)
- `get_gwo_history()` (line 1262)
- `view_architecture_graph()` (line 1290)
- `get_capabilities()` (line 1311)
- `serve_help_manual()` (line 1329)
- `redirect_manual_to_help()` (line 1350)
- `serve_visualizer()` (line 1358)
- `visualizer_sse_stream()` (line 1380)
- `get_visualizer_demo_data(limit)` (line 1423)
- `get_visualizer_sources_health()` (line 1466)
- `_score_to_reward(score)` (line 1503)
- `_infer_active_provider()` (line 1522)
- `_clean_paper_title(title)` (line 1543)
- `get_visualizer_state()` (line 1584)
- `post_visualizer_events(request)` (line 1698)

### Dependencies

- src/ai/optimizers/gwo_foraging_hyperparameter_tuner.py
- src/api/red_tester_routes.py
- src/api/synapse_routes.py
- src/core/ai_manager.py
- src/core/database_manager.py
- src/ingestion/daily_search.py
- src/services/cognitive_mesh/server.py
- src/utils/logger.py

---

## Module: src/api/red_tester_routes.py

**Summary:** Module: red_tester_routes.py

### Classes

- `ArmStatus` (line 94)
  - Q-value status for a single test arm (system component).
- `TesterStatus` (line 103)
  - Full status response for the Autonomous Red Tester.
- `CrashReportEntry` (line 112)
  - Metadata for a single crash report file.
- `TesterReports` (line 121)
  - List of available crash reports.

### Functions

- `_discover_target_arms()` (line 52)
- `_classify_fragility(q_value)` (line 133)
- `_load_q_table()` (line 152)
- `get_tester_status()` (line 174)
- `get_tester_reports()` (line 205)

---

## Module: src/api/synapse_routes.py

**Summary:** Module: synapse_routes.py

### Classes

- `SynapseWebhookRequest` (line 59)
  - Inbound SYNAPSE command envelope.
- `SynapseWebhookResponse` (line 81)
  - Acknowledgment response for a received SYNAPSE command.

### Functions

- `register_handler(command, handler)` (line 112)
- `_handle_get_status(params)` (line 137)
- `_handle_shutdown(params)` (line 142)
- `synapse_webhook(request)` (line 158)
- `_check_bus_reachability(bus_url, timeout)` (line 243)
- `synapse_status()` (line 266)

### Dependencies

- src/integration/synapse_client.py

---

## Module: src/api/talos_service_api.py

**Summary:** Module: talos_service_api.py (v1.0)

### Functions

- `_get_today_folder()` (line 46)
- `api_status()` (line 53)
- `api_report()` (line 104)

---

## Module: src/core/ai_manager.py

**Summary:** Module: ai_manager.py (v4.1 - Self-Healing AI Manager, Universal Cloud Mesh & Auto-Dynamic Privacy Guardrails)

### Classes

- `AIManager` (line 408)
  - Manages all LLM and embedding interactions with multi-provider fallback
  - `__init__(self, config)` (line 426)
  - `_ensure_local_ollama_runtime(self)` (line 536)
  - `_persist_env_key(self, key, value)` (line 585)
  - `_register_cloud_provider_on_demand(self, provider_name)` (line 618)
  - `_prompt_cloud_key(self, provider_name)` (line 672)
  - `_ensure_cloud_credential(self, provider_name)` (line 711)
  - `_ensure_cloud_credential_for_fallback(self)` (line 731)
  - `_init_router(self)` (line 748)
  - `_task_type(model_type)` (line 763)
  - `_emit_router_decision_synapse(self, provider, task_type, prompt_length)` (line 778)
  - `_get_router_ordered_providers(self, prompt, task_type)` (line 799)
  - `list_active_providers(self)` (line 833)
  - `get_provider_descriptor(self, name)` (line 846)
  - `_clean_json_string(self, text)` (line 860)
  - `evaluate_paper_json(self, abstract, model_type, system_prompt_override)` (line 885)
  - `_resolve_eval_concurrency(self)` (line 907)
  - `batch_evaluate_papers(self, papers, criteria, max_workers, model_type)` (line 931)
  - `analyze_generic_text(self, full_prompt)` (line 991)
  - `generate_embeddings(self, texts)` (line 1004)
  - `_execute_huggingface_embedding(self, texts, hf_token)` (line 1088)
  - `_resolve_strategies(self, model_type)` (line 1151)
  - `_is_network_online(host, port, timeout)` (line 1205)
  - `_detect_vram_gb()` (line 1227)
  - `_resolve_auto_dynamic(self, model_type, hardware)` (line 1239)
  - `_prompt_auto_dynamic_consent(self, vram_gb)` (line 1276)
  - `_log_auto_matrix(self, task_type, resolved_strategy, reason)` (line 1330)
  - `_execute_request(self, prompt, model_type, response_format, tier, allow_prompt)` (line 1353)
  - `_execute_local_strategy(self, prompt, response_format, tier, hardware_strategy, allow_prompt)` (line 1448)
  - `_execute_ollama_http(self, prompt, response_format, use_edge, allow_prompt)` (line 1478)
  - `_execute_cloud_chain(self, prompt, model_type, response_format)` (line 1590)
  - `_execute_legacy_request(self, prompt, model_type, response_format, tier, allow_prompt)` (line 1635)
  - `_execute_fast_tier_request(self, prompt, response_format)` (line 1692)
  - `_execute_gemini_request(self, prompt, model_type, response_format)` (line 1712)
  - `_execute_deepseek_request(self, prompt, response_format)` (line 1748)
  - `_execute_openai_compatible_request(self, provider_name, prompt, model_type, response_format)` (line 1762)
  - `_execute_openai_compatible(self, prompt, response_format, provider_name)` (line 1833)
  - `_interactive_cloud_fallback(self, error, tier, allow_prompt)` (line 1853)
  - `_latch_provider_exhausted(self, provider_name, reason)` (line 1918)
  - `_is_quota_or_auth_exhausted(message)` (line 1942)
  - `_quota_reason(message)` (line 1961)
  - `_handle_failure(self, provider_name)` (line 1977)
  - `_ensure_local_model(self)` (line 1995)

### Functions

- `_try_import_openai()` (line 130)
- `_try_import_genai()` (line 149)
- `_resolve_project_root()` (line 206)
- `probe_local_ollama(port, timeout)` (line 221)
- `_spawn_local_ollama()` (line 242)
- `_is_interactive_tty()` (line 262)
- `_strip_thinking_tags(text)` (line 278)
- `_extract_assistant_content(message)` (line 306)
- `_sanitize_connection_error(exc)` (line 392)

### Dependencies

- config/settings.py
- src/ai/drl/llm_router_subagent.py
- src/core/hardware.py
- src/core/provider_registry.py
- src/integration/synapse_client.py
- src/utils/http_client.py
- src/utils/ui_theme.py

---

## Module: src/core/cognitive_router.py

**Summary:** Module: cognitive_router.py

### Dependencies

- src/services/cognitive_mesh/router.py

---

## Module: src/core/database_manager.py

**Summary:** Module: database_manager.py (v5.0 - Multi-Provider Hybrid Embeddings)

### Classes

- `DatabaseManager` (line 276)
  - `__init__(self, db_path, db_name)` (line 277)
  - `_resolve_profile_db(project_root)` (line 302)
  - `_table_exists(self, table_name)` (line 316)
  - `_apply_pragmas(self, conn)` (line 321)
  - `_connect(self)` (line 339)
  - `execute_query(self, query, params, commit, fetch_one, fetch_all)` (line 350)
  - `execute_many(self, query, params_list, commit)` (line 362)
  - `create_table(self)` (line 373)
  - `paper_exists_by_doi(self, doi)` (line 444)
  - `paper_exists_by_url(self, url)` (line 447)
  - `get_paper_id_by_doi(self, doi)` (line 450)
  - `get_paper_id_by_url(self, url)` (line 454)
  - `_calculate_overall_score(self, scores)` (line 459)
  - `add_paper(self, paper_data, evaluation_data, in_zotero)` (line 463)
  - `update_paper_evaluation(self, paper_id, evaluation_data)` (line 487)
  - `update_paper_quality(self, paper_id, quality_score, rubric_json, quadrant)` (line 505)
  - `get_papers_not_recently_evaluated(self, days_window, limit)` (line 531)
  - `get_all_papers_for_dashboard(self)` (line 536)
  - `get_single_paper_details(self, paper_id)` (line 542)
  - `update_zotero_status_by_id(self, paper_id, status)` (line 548)
  - `get_papers_needing_embedding(self, model)` (line 552)
  - `store_embeddings_batch(self, updates)` (line 566)
  - `get_all_embeddings(self, model_filter)` (line 569)
  - `get_cached_embeddings(self, model_name)` (line 584)
  - `save_embeddings_batch(self, records)` (line 619)
  - `get_papers_by_ids(self, ids)` (line 649)
  - `get_recent_core_papers(self, limit, min_score)` (line 657)
  - `get_recent_elite_papers(self, hours, min_score)` (line 662)
  - `get_embedding_model_stats(self)` (line 672)
  - `_load_embeddings_into_memory(self, model_filter)` (line 682)
  - `reload_embeddings_for_model(self, model_filter)` (line 697)
  - `semantic_search(self, query_vector, top_k, model_filter)` (line 702)
  - `get_all_papers_as_dataframe(self)` (line 724)
  - `get_database_statistics(self)` (line 733)
  - `get_papers_for_enrichment(self)` (line 752)
  - `update_papers_enrichment_batch(self, update_list)` (line 761)

### Functions

- `get_active_profile_db_path()` (line 21)
- `_run_vault_verify_once()` (line 52)
- `_paper_columns(conn)` (line 96)
- `_has_papers_table(conn)` (line 111)
- `_normalized_title(title)` (line 126)
- `_dedup_keys(row)` (line 140)
- `merge_orphan_databases(target_profile_name)` (line 166)
- `_run_orphan_merge_once()` (line 254)

### Dependencies

- src/core/database_vault.py
- src/core/profile_manager.py

---

## Module: src/core/database_vault.py

**Summary:** Module: database_vault.py

### Classes

- `DatabaseVault` (line 41)
  - Automated SQLite integrity vault with atomic snapshot rotation.
  - `__init__(self, backup_dir, max_retention_days, db_path)` (line 49)
  - `verify_integrity(self, db_path)` (line 63)
  - `quick_status(self)` (line 111)
  - `create_atomic_snapshot(self, backup_dir, max_retention_days)` (line 137)
  - `_rotate(self, backup_dir, max_retention_days)` (line 178)
  - `restore_snapshot(self, snapshot_path)` (line 192)
  - `_resolve_db(self, db_path)` (line 225)

### Dependencies

- src/core/database_manager.py

---

## Module: src/core/hardware.py

**Summary:** Module: hardware.py

### Functions

- `detect_vram_gb()` (line 36)
- `recommend_model(preferred)` (line 53)
- `extract_params_b(model_name)` (line 124)
- `estimate_size_for_quant(model_name, quant_tag)` (line 142)
- `estimate_size(model_name)` (line 174)
- `get_installed_models()` (line 189)
- `get_all_chat_models_sorted(vram_gb)` (line 206)
- `get_embedding_models()` (line 244)
- `get_ollama_library_models(vram_gb)` (line 287)
- `get_bitnet_models(vram_gb)` (line 333)
- `get_all_chat_models_sorted(vram_gb)` (line 357)
- `pull_model(model_name)` (line 422)

---

## Module: src/core/hardware_advisor.py

**Summary:** Module: hardware_advisor.py

### Classes

- `HardwareModelAdvisor` (line 77)
  - Compute a VRAM-based parameter budget and a tailored model stack.
  - `get_hardware_profile(self)` (line 91)
  - `_detect_laptop_cpu()` (line 147)
  - `_detect_gpu_name()` (line 172)
  - `calculate_vram_budget(vram_gb)` (line 198)
  - `get_recommendations(self)` (line 222)
  - `scan_sota_models(self, timeout)` (line 258)
  - `_scan_ollama_tags(timeout)` (line 305)
  - `_scan_openrouter_models(self, timeout)` (line 329)
  - `render_recommendations(self)` (line 371)
  - `get_role_based_matrix(self)` (line 462)
  - `render_role_matrix(self)` (line 528)
  - `apply_recommended_models(self)` (line 572)

### Functions

- `get_hardware_advisor()` (line 633)

### Dependencies

- config/settings.py
- src/core/hardware.py
- src/core/profile_manager.py

---

## Module: src/core/hierarchical_evaluator.py

**Summary:** Module: hierarchical_evaluator.py

### Classes

- `HierarchicalEvaluationEngine` (line 77)
  - Two-tier paper evaluation engine with an escalation gate.
  - `__init__(self, ai_manager, escalation_threshold)` (line 88)
  - `_extract_relevance(evaluation)` (line 105)
  - `_extract_quality(evaluation, fallback_relevance)` (line 132)
  - `_paper_content(paper)` (line 156)
  - `_calibrate_relevance(deep_evaluation, fallback)` (line 170)
  - `_appraise_quality(self, paper, s_rel_calibrated)` (line 192)
  - `_map_quadrant(relevance, quality)` (line 231)
  - `evaluate_paper(self, paper, escalation_threshold)` (line 261)
  - `evaluate_batch(self, papers, threshold)` (line 348)

### Dependencies

- config/settings.py
- src/prisma/quality_appraisal.py

---

## Module: src/core/model_benchmark_client.py

**Summary:** Module: model_benchmark_client.py

### Dependencies

- src/services/cognitive_mesh/benchmarks.py

---

## Module: src/core/notifier.py

**Summary:** Module: notifier.py (v1.0)

### Classes

- `TalosNotifier` (line 64)
  - Multi-channel notification sender for the TALOS autonomous daemon.
  - `__init__(self)` (line 79)
  - `telegram_send(self, paper, score, action_taken)` (line 112)
  - `discord_send(self, paper, score, action_taken)` (line 181)
  - `email_send(self, subject, body)` (line 240)
  - `email_paper_alert(self, paper, score, action_taken)` (line 281)
  - `email_daily_digest(self, papers)` (line 340)

### Functions

- `_paper_value(paper, key, default)` (line 41)

### Dependencies

- config/settings.py

---

## Module: src/core/profile_manager.py

**Summary:** Module: profile_manager.py

### Classes

- `ProfileManager` (line 78)
  - Canonical multi-profile workspace manager (single source of truth).
  - `__init__(self, root)` (line 87)
  - `get_profiles_dir(self)` (line 99)
  - `get_active_profile_name(self)` (line 108)
  - `list_profiles(self)` (line 124)
  - `_root_config_path(self)` (line 134)
  - `_load_profile_config_to_root(self, name)` (line 141)
  - `_persist_root_config_to_profile(self, name)` (line 147)
  - `set_active_profile(self, name)` (line 156)
  - `create_profile(self, name, seed_config)` (line 180)
  - `get_active_db_path(self)` (line 214)
  - `get_active_config_path(self)` (line 225)

### Functions

- `_validate_profile_name(name)` (line 73)
- `ensure_profiles_dir()` (line 243)
- `get_active_profile_name()` (line 248)
- `set_active_profile_name(name)` (line 253)
- `save_current_state_to_profile(profile_name)` (line 258)
- `load_profile_to_root(profile_name)` (line 263)
- `run_pythia_script()` (line 268)
- `create_new_profile()` (line 287)
- `switch_profile()` (line 308)
- `configure_current_profile()` (line 335)
- `main()` (line 348)

### Dependencies

- src/utils/ui_theme.py

---

## Module: src/core/provider_registry.py

**Summary:** Module: provider_registry.py

### Dependencies

- src/services/cognitive_mesh/registry.py

---

## Module: src/ingestion/daily_search.py

**Summary:** Module: daily_search.py (Quad-Layer & Rate Limit Safe)

### Functions

- `_source_key(source)` (line 79)
- `_source_query(source)` (line 84)
- `_normalize_title(title)` (line 95)
- `_title_hash(title)` (line 113)
- `_deduplicate_papers(papers)` (line 125)
- `_harvest_single_source(source, source_key, query, criteria, date_limit)` (line 154)
- `_emit_visualizer_event(event_type, payload)` (line 215)
- `_emit_router_decision_synapse(provider, task_type, prompt_length)` (line 237)
- `route_evaluation_provider(ai_manager, content, task_type)` (line 258)
- `build_sources(config, selected)` (line 280)
- `generate_markdown_report(report_data)` (line 300)
- `post_report_to_discord(config, markdown_content, filename)` (line 336)
- `load_configuration()` (line 359)
- `main(sources)` (line 381)

### Dependencies

- src/ai/drl/llm_router_subagent.py
- src/core/ai_manager.py
- src/core/database_manager.py
- src/core/hierarchical_evaluator.py
- src/ingestion/resilient_gateway.py
- src/integration/synapse_client.py
- src/integration/visualizer_bridge.py

---

## Module: src/ingestion/data_enricher.py

**Summary:** Module: data_enricher.py (v4.8.1 — Graceful Degradation)

### Functions

- `get_enrichment_data(doi)` (line 87)
- `process_paper(paper_data)` (line 112)
- `force_reset_status(db_path)` (line 189)
- `main()` (line 209)

### Dependencies

- src/core/database_manager.py

---

## Module: src/ingestion/grey_literature_miner.py

**Summary:** Module: grey_literature_miner.py (v2.1 — Batch 3 hotfix)

### Functions

- `load_config()` (line 47)
- `save_report(topic, content)` (line 60)
- `run_miner()` (line 86)

### Dependencies

- src/core/ai_manager.py
- src/utils/ui_theme.py

---

## Module: src/ingestion/historic_search.py

**Summary:** Module: historic_search.py (v5.19.0 - Unified Hierarchical Historical Harvester)

### Functions

- `_source_key(source)` (line 72)
- `_source_query(source)` (line 77)
- `_emit_visualizer_event(event_type, payload)` (line 88)
- `_normalize_title(title)` (line 109)
- `_title_hash(title)` (line 127)
- `_deduplicate_papers(papers)` (line 139)
- `_harvest_single_source(source, source_key, query, criteria, date_limit)` (line 168)
- `route_evaluation_provider(ai_manager, content, task_type)` (line 230)
- `build_sources(config, selected)` (line 251)
- `load_configuration()` (line 271)
- `main(sources)` (line 296)

### Dependencies

- src/ai/drl/llm_router_subagent.py
- src/core/ai_manager.py
- src/core/database_manager.py
- src/core/hierarchical_evaluator.py
- src/ingestion/resilient_gateway.py
- src/integration/visualizer_bridge.py

---

## Module: src/ingestion/metadata_enricher.py

**Summary:** Module: metadata_enricher.py (v2.0 - Multi-Source Fallback)

### Classes

- `MetadataEnricher` (line 48)
  - Η κλάση που ενορχηστρώνει τη διαδικασία εμπλουτισμού των μεταδεδομένων.
  - `__init__(self, config)` (line 53)
  - `find_papers_to_enrich(self)` (line 74)
  - `update_paper_metadata(self, paper_id, new_data)` (line 87)
  - `_search_with_fallback(self, query)` (line 113)
  - `run(self)` (line 136)

### Functions

- `load_configuration()` (line 199)

### Dependencies

- src/core/database_manager.py
- src/ingestion/sources/crossref_source.py
- src/ingestion/sources/dblp_source.py
- src/ingestion/sources/openalex_source.py
- src/ingestion/sources/semantic_scholar_source.py
- src/utils/ui_theme.py

---

## Module: src/ingestion/pdf_harvester/__init__.py

**Summary:** Module: __init__.py (src/ingestion/pdf_harvester)

### Dependencies

- src/ingestion/pdf_harvester/harvester.py
- src/ingestion/pdf_harvester/resolvers.py
- src/ingestion/pdf_harvester/section_extractor.py

---

## Module: src/ingestion/pdf_harvester/harvester.py

**Summary:** Module: harvester.py

### Classes

- `AcademicPDFHarvester` (line 77)
  - Download legal Open Access / preprint PDFs for elite candidate papers.
  - `__init__(self, cache_dir, timeout, max_file_size_mb, rate_limit_delay)` (line 87)
  - `validate_magic_bytes(data)` (line 117)
  - `compute_sha256(data)` (line 131)
  - `_atomic_write(self, pdf_id, data)` (line 143)
  - `_polite_wait(self)` (line 163)
  - `_fetch_pdf_bytes(self, url)` (line 174)
  - `_download_pdf(self, url, pdf_id)` (line 214)
  - `_active_db_path(self, active_profile)` (line 232)
  - `_candidate_papers(self, db_path, min_relevance)` (line 247)
  - `_update_paper_pdf(self, db_path, paper_id, local_pdf_path, pdf_sha256, pdf_status)` (line 268)
  - `harvest_candidates(self, min_relevance, active_profile)` (line 288)

### Functions

- `_resolve_project_root()` (line 67)

### Dependencies

- src/core/database_manager.py
- src/ingestion/pdf_harvester/resolvers.py

---

## Module: src/ingestion/pdf_harvester/resolvers.py

**Summary:** Module: resolvers.py

### Functions

- `_headers()` (line 59)
- `_http_get_json(url, params, timeout)` (line 64)
- `_doi(paper)` (line 86)
- `_url(paper)` (line 94)
- `_resolve_arxiv(paper)` (line 103)
- `_resolve_techrxiv(paper)` (line 127)
- `_resolve_hal_inria(paper)` (line 142)
- `_resolve_nasa_ntrs(paper)` (line 160)
- `_resolve_elsevier_oa(paper)` (line 196)
- `_resolve_plos(paper)` (line 231)
- `_resolve_pmc(paper)` (line 246)
- `_resolve_unpaywall(paper)` (line 269)
- `_resolve_openalex(paper)` (line 293)
- `_resolve_semantic_scholar(paper)` (line 323)
- `_resolve_core(paper)` (line 348)
- `_resolve_crossref_oa(paper)` (line 374)
- `_resolve_ssrn(paper)` (line 398)
- `resolve_oa_url(paper_dict)` (line 436)

---

## Module: src/ingestion/pdf_harvester/section_extractor.py

**Summary:** Module: section_extractor.py

### Classes

- `PDFSectionExtractor` (line 91)
  - Extract and cache targeted section text windows from local PDFs.
  - `__init__(self, cache_dir)` (line 98)
  - `_extract_text_pypdf(pdf_path)` (line 113)
  - `_extract_text_fallback(pdf_path)` (line 137)
  - `_extract_text(self, pdf_path)` (line 154)
  - `_slice_sections(text)` (line 170)
  - `extract_sections(self, pdf_path, paper_id)` (line 204)
  - `load_sections(self, paper_id)` (line 229)

### Functions

- `_resolve_project_root()` (line 81)

---

## Module: src/ingestion/resilient_gateway.py

**Summary:** Module: resilient_gateway.py

### Classes

- `ResilientIngestionGateway` (line 57)
  - Overarching self-healing wrapper for all 18 academic source adapters.
  - `__init__(self, session)` (line 66)
  - `harvest_source(self, source_instance, query, criteria, date_limit, source_key, days_to_search, mailto)` (line 78)
  - `_detect_auth_error(self, stdout_text)` (line 171)
  - `_mirror_via_openalex(self, query, publisher, source_key, days_to_search, mailto)` (line 189)
  - `_reconstruct_abstract(inverted_index)` (line 239)
  - `_normalize_openalex_work(cls, work, source_key)` (line 257)

### Dependencies

- src/utils/http_client.py

---

## Module: src/ingestion/sources/__init__.py

**Summary:** Module: __init__.py

### Dependencies

- src/ingestion/sources/arxiv_source.py
- src/ingestion/sources/core_source.py
- src/ingestion/sources/crossref_source.py
- src/ingestion/sources/dblp_source.py
- src/ingestion/sources/elsevier_source.py
- src/ingestion/sources/hal_inria_source.py
- src/ingestion/sources/ieee_source.py
- src/ingestion/sources/nasa_ntrs_source.py
- src/ingestion/sources/openaire_source.py
- src/ingestion/sources/openalex_source.py
- src/ingestion/sources/openarchives_source.py
- src/ingestion/sources/openreview_source.py
- src/ingestion/sources/osti_source.py
- src/ingestion/sources/plos_source.py
- src/ingestion/sources/pubmed_source.py
- src/ingestion/sources/scigov_source.py
- src/ingestion/sources/semantic_scholar_source.py
- src/ingestion/sources/springer_source.py

---

## Module: src/ingestion/sources/arxiv_source.py

**Summary:** Module: arxiv_source.py

### Classes

- `ArxivSource` (line 36)
  - Search agent for the arXiv API.
  - `__init__(self, config)` (line 50)
  - `fetch_new_papers(self)` (line 70)
  - `_format_paper(self, entry, ns, published_date)` (line 124)

### Dependencies

- src/utils/http_client.py

---

## Module: src/ingestion/sources/core_source.py

**Summary:** Module: core_source.py

### Classes

- `CORESource` (line 35)
  - Search agent for the CORE API.
  - `__init__(self, config)` (line 43)
  - `fetch_new_papers(self)` (line 60)
  - `_format_paper(self, item)` (line 109)

### Dependencies

- src/utils/http_client.py

---

## Module: src/ingestion/sources/crossref_source.py

**Summary:** Module: crossref_source.py

### Classes

- `CrossrefSource` (line 38)
  - Search agent for the Crossref API.
  - `__init__(self, config)` (line 51)
  - `fetch_new_papers(self)` (line 65)
  - `search_papers(self, query, limit)` (line 125)
  - `_format_paper(self, item)` (line 149)

### Dependencies

- src/utils/http_client.py

---

## Module: src/ingestion/sources/dblp_source.py

**Summary:** Module: dblp_source.py

### Classes

- `DBLPSource` (line 47)
  - Search agent for the DBLP API.
  - `__init__(self, config)` (line 60)
  - `_sanitize_dblp_query(query)` (line 74)
  - `fetch_new_papers(self)` (line 96)
  - `search_papers(self, query, limit)` (line 158)
  - `_format_paper(self, info)` (line 186)

### Dependencies

- src/utils/http_client.py

---

## Module: src/ingestion/sources/elsevier_source.py

**Summary:** Module: elsevier_source.py

### Classes

- `ElsevierSource` (line 42)
  - Search agent for the Elsevier Scopus API.
  - `__init__(self, config)` (line 54)
  - `fetch_new_papers(self)` (line 79)
  - `_fetch_abstract(self, scopus_id)` (line 111)
  - `_format_paper(self, result)` (line 129)

---

## Module: src/ingestion/sources/hal_inria_source.py

**Summary:** Module: hal_inria_source.py

### Classes

- `HalInriaSource` (line 45)
  - Search agent for the HAL open science repository public REST API.
  - `__init__(self, config)` (line 68)
  - `_first(values, default)` (line 79)
  - `_as_list(value)` (line 97)
  - `fetch_new_papers(self)` (line 112)
  - `search_papers(self, query, limit)` (line 166)
  - `_format_paper(self, item)` (line 190)

### Dependencies

- src/utils/http_client.py

---

## Module: src/ingestion/sources/ieee_source.py

**Summary:** Module: ieee_source.py

### Classes

- `IEEEXploreSource` (line 37)
  - Search agent for the IEEE Xplore API.
  - `__init__(self, config)` (line 49)
  - `_make_request(self, params, max_retries, initial_backoff)` (line 68)
  - `fetch_new_papers(self)` (line 101)
  - `_format_paper(self, article)` (line 146)

### Dependencies

- src/integration/visualizer_bridge.py
- src/utils/http_client.py

---

## Module: src/ingestion/sources/nasa_ntrs_source.py

**Summary:** Module: nasa_ntrs_source.py

### Classes

- `NasaNtrsSource` (line 45)
  - Search agent for the NASA NTRS public REST API.
  - `__init__(self, config)` (line 62)
  - `_first(values, default)` (line 73)
  - `_as_list(value)` (line 91)
  - `fetch_new_papers(self)` (line 106)
  - `search_papers(self, query, limit)` (line 158)
  - `_format_paper(self, item)` (line 182)

### Dependencies

- src/utils/http_client.py

---

## Module: src/ingestion/sources/openaire_source.py

**Summary:** Module: openaire.py

### Classes

- `OpenAIRESource` (line 48)
  - Search agent for the OpenAIRE Research Graph API.
  - `__init__(self, config)` (line 72)
  - `_first(values, default)` (line 90)
  - `_normalize_keywords(query)` (line 118)
  - `_extract_result(self, item)` (line 138)
  - `fetch_new_papers(self)` (line 152)
  - `search_papers(self, query, limit)` (line 218)
  - `_format_paper(self, item)` (line 247)
  - `_extract_funding(self, projects)` (line 309)

### Dependencies

- src/utils/http_client.py

---

## Module: src/ingestion/sources/openalex_source.py

**Summary:** Module: openalex_source.py

### Classes

- `OpenAlexSource` (line 38)
  - Search agent for the OpenAlex API.
  - `__init__(self, config)` (line 52)
  - `fetch_new_papers(self)` (line 66)
  - `search_papers(self, query, limit)` (line 128)
  - `_reconstruct_abstract(self, inverted_index)` (line 152)
  - `_format_paper(self, work)` (line 172)

### Dependencies

- src/utils/http_client.py

---

## Module: src/ingestion/sources/openarchives_source.py

**Summary:** Module: openarchives_source.py

### Classes

- `OpenArchivesSource` (line 33)
  - Search agent for OpenArchives.gr.
  - `__init__(self, config)` (line 35)
  - `fetch_new_papers(self)` (line 50)
  - `_format_paper(self, item)` (line 75)

### Dependencies

- src/utils/http_client.py

---

## Module: src/ingestion/sources/openreview_source.py

**Summary:** Module: openreview_source.py

### Classes

- `OpenReviewSource` (line 59)
  - Search agent for the OpenReview API V2.
  - `__init__(self, config)` (line 76)
  - `_get_content_value(self, note, field, default)` (line 114)
  - `_query_notes(self, term, limit, offset, sort)` (line 141)
  - `fetch_new_papers(self)` (line 182)
  - `search_papers(self, query, limit)` (line 241)
  - `_format_paper(self, note)` (line 265)

---

## Module: src/ingestion/sources/osti_source.py

**Summary:** Module: osti_source.py

### Classes

- `OSTISource` (line 31)
  - Search agent for OSTI.gov.
  - `__init__(self, config)` (line 33)
  - `fetch_new_papers(self)` (line 41)
  - `_format_paper(self, record)` (line 60)

### Dependencies

- src/utils/http_client.py

---

## Module: src/ingestion/sources/plos_source.py

**Summary:** Module: plos_source.py

### Classes

- `PLOSSource` (line 33)
  - Search agent for the PLOS API (Open Access).
  - `__init__(self, config)` (line 35)
  - `fetch_new_papers(self)` (line 43)
  - `_format_paper(self, doc)` (line 78)

### Dependencies

- src/utils/http_client.py

---

## Module: src/ingestion/sources/pubmed_source.py

**Summary:** Module: pubmed_source.py 

### Classes

- `PubMedSource` (line 35)
  - Search agent for PubMed.
  - `__init__(self, config)` (line 37)
  - `fetch_new_papers(self)` (line 51)
  - `_format_paper(self, article)` (line 70)

---

## Module: src/ingestion/sources/scigov_source.py

**Summary:** Module: scigov_source.py

### Classes

- `ScienceGovSource` (line 55)
  - Search agent for the Science.gov federal science portal API.
  - `__init__(self, config)` (line 58)
  - `_is_dns_failure(exc)` (line 78)
  - `fetch_new_papers(self)` (line 98)
  - `_format_paper(self, record)` (line 146)

### Dependencies

- src/utils/http_client.py

---

## Module: src/ingestion/sources/semantic_scholar_source.py

**Summary:** Module: semantic_scholar_source.py

### Classes

- `SemanticScholarSource` (line 36)
  - Search agent for the Semantic Scholar API.
  - `__init__(self, config)` (line 49)
  - `_make_request(self, endpoint, params, max_retries, initial_backoff)` (line 63)
  - `_format_paper(self, paper)` (line 98)
  - `search_papers(self, query, limit)` (line 115)
  - `fetch_new_papers(self)` (line 131)
  - `get_paper_details(self, paper_id, fields)` (line 165)
  - `_get_paginated_paper_list(self, url, limit)` (line 177)
  - `get_paper_references(self, paper_id, limit)` (line 202)
  - `get_paper_citations(self, paper_id, limit)` (line 215)

### Dependencies

- src/integration/visualizer_bridge.py
- src/utils/http_client.py

---

## Module: src/ingestion/sources/springer_source.py

**Summary:** Module: springer_source.py

### Classes

- `SpringerNatureSource` (line 35)
  - Search agent for the Springer Nature API.
  - `__init__(self, config)` (line 44)
  - `_make_request(self, params, max_retries, initial_backoff)` (line 63)
  - `fetch_new_papers(self)` (line 89)
  - `_format_paper(self, article)` (line 117)

### Dependencies

- src/utils/http_client.py

---

## Module: src/ingestion/zotero_connector.py

**Summary:** Module: zotero_connector.py (v2.1 - Graceful Import Degradation)

### Functions

- `main()` (line 52)

### Dependencies

- src/core/ai_manager.py
- src/core/database_manager.py

---

## Module: src/integration/__init__.py

**Summary:** Module: __init__.py

---

## Module: src/integration/optica_client.py

**Summary:** Module: optica_client.py

### Classes

- `OpticaClient` (line 35)
  - Lightweight REST client for the OPTICA visualization microservice.
  - `__init__(self, base_url, timeout)` (line 50)
  - `plot_generate_url(self)` (line 62)
  - `request_plot(self, plot_type, journal_template)` (line 66)
  - `_error(message, exc)` (line 123)

### Dependencies

- config/settings.py
- src/core/database_manager.py

---

## Module: src/integration/synapse_client.py

**Summary:** Module: synapse_client.py

### Classes

- `EventEmitter` (line 85)
  - Thread-safe, non-blocking emitter for the SYNAPSE Event-Driven Protocol.
  - `__init__(self, bus_url, source, timeout, max_retries)` (line 113)
  - `emit(self, event_type, payload, callback, blocking)` (line 170)
  - `_build_event(self, event_type, payload)` (line 219)
  - `_buffer_event(self, event)` (line 238)
  - `_do_emit(self, event, callback)` (line 260)
  - `close(self)` (line 395)
  - `__del__(self)` (line 407)

### Functions

- `get_emission_stats()` (line 54)
- `_record_emission(counter)` (line 64)

---

## Module: src/integration/visualizer_bridge.py

**Summary:** Module: visualizer_bridge.py

### Functions

- `push_visualizer_event(event_type, source, score, title, **extra)` (line 27)

---

## Module: src/mcp_server.py

**Summary:** Module: mcp_server.py

### Functions

- `talos_system_status()` (line 60)
- `talos_semantic_search(query, top_k)` (line 124)
- `talos_get_paper_details(paper_id)` (line 199)
- `talos_trigger_scrape(sources)` (line 325)

---

## Module: src/prisma/__init__.py

**Summary:** Module: __init__.py

### Dependencies

- src/prisma/dspy_modules.py
- src/prisma/dspy_signatures.py
- src/prisma/mermaid_generator.py
- src/prisma/quality_appraisal.py
- src/prisma/quality_swarm.py
- src/prisma/scoping_review_synthesizer.py
- src/prisma/swarm_evaluators.py

---

## Module: src/prisma/dspy_modules.py

**Summary:** Module: dspy_modules.py

### Classes

- `PrismaPlanner` (line 171)
  - Synthesize multi-database search protocols and query facets.
  - `__init__(self, ai_manager)` (line 179)
  - `plan(self, research_topic, domain_scope)` (line 187)
  - `_deterministic_plan(self, research_topic, domain_scope)` (line 214)
- `PrismaEvaluator` (line 243)
  - Perform structured Chain-of-Thought title/abstract screening.
  - `__init__(self, ai_manager, evaluation_mode)` (line 254)
  - `screen(self, title, abstract, inclusion_criteria, exclusion_criteria)` (line 269)
  - `_screen_swarm(self, title, abstract, inclusion_criteria, exclusion_criteria)` (line 309)
  - `_deterministic_screen(self, title, abstract, inclusion_criteria, exclusion_criteria)` (line 394)
- `PrismaEligibilityJudge` (line 448)
  - Assess full abstract/methodology suitability for inclusion.
  - `__init__(self, ai_manager)` (line 456)
  - `assess(self, title, abstract, methodology_tags, deep_criteria)` (line 464)
  - `_deterministic_assess(self, title, abstract, methodology_tags, deep_criteria)` (line 502)
- `PrismaExecutor` (line 581)
  - Orchestrate the 4-phase PRISMA-ScR flow end-to-end.
  - `__init__(self, ai_manager, db_manager, evaluation_mode)` (line 592)
  - `_ensure_ai_manager(self)` (line 620)
  - `_ensure_components(self)` (line 635)
  - `_collect_papers(self, papers, limit)` (line 642)
  - `_deduplicate(papers)` (line 670)
  - `run(self, research_topic, domain_scope, papers, max_papers, deep_criteria, evaluation_mode, render)` (line 695)
  - `_render_counters(self)` (line 838)
  - `_print_counters_plain(counts)` (line 870)
  - `_write_report(self, markdown, topic)` (line 886)
  - `run_interactive(self)` (line 905)

### Functions

- `_resolve_project_root()` (line 53)
- `_load_config()` (line 68)
- `_keyword_hits(text, keywords)` (line 134)
- `_criteria_keywords(criteria)` (line 150)
- `main()` (line 958)

### Dependencies

- src/core/ai_manager.py
- src/core/database_manager.py
- src/prisma/dspy_signatures.py
- src/prisma/mermaid_generator.py
- src/prisma/scoping_review_synthesizer.py
- src/prisma/swarm_evaluators.py

---

## Module: src/prisma/dspy_signatures.py

**Summary:** Module: dspy_signatures.py

### Classes

- `DspySignature` (line 118)
  - Base class for typed declarative PRISMA-ScR signatures.
  - `_normalize(cls, data)` (line 130)
  - `parse_output(cls, text)` (line 142)
- `PrismaPlanSignature` (line 165)
  - Declarative signature synthesizing a multi-database search protocol.
  - `_normalize(cls, data)` (line 185)
- `PrismaScreeningSignature` (line 202)
  - Declarative signature for title/abstract screening with chain-of-thought.
  - `_normalize(cls, data)` (line 228)
- `PrismaEligibilitySignature` (line 259)
  - Declarative signature for full-abstract/methodology eligibility.
  - `_normalize(cls, data)` (line 281)
- `PrismaSynthesisSignature` (line 302)
  - Declarative signature for thematic synthesis of included studies.
  - `_normalize(cls, data)` (line 320)

### Functions

- `extract_json_payload(text)` (line 46)
- `_string_list(value)` (line 91)

---

## Module: src/prisma/mermaid_generator.py

**Summary:** Module: mermaid_generator.py

### Functions

- `_n(counts, key, default)` (line 25)
- `generate_prisma_mermaid(counts)` (line 43)
- `mermaid_to_markdown(mermaid, caption)` (line 98)
- `mermaid_to_html(mermaid, title)` (line 114)

---

## Module: src/prisma/quality_appraisal.py

**Summary:** Module: quality_appraisal.py

### Classes

- `KitchenhamRubric` (line 143)
  - Standardized six-question Kitchenham et al.
  - `_coerce_ternary(cls, value)` (line 207)
  - `question_sum(self)` (line 219)
  - `quality_score(self)` (line 235)
- `QualityAppraisalResult` (line 291)
  - Structured result of a single Kitchenham quality appraisal.
- `PrismaQualityAppraiser` (line 343)
  - Standardized Kitchenham (2007) quality appraisal engine.
  - `__init__(self, ai_manager, db_manager, appraisal_mode)` (line 359)
  - `_ensure_ai_manager(self)` (line 378)
  - `_ensure_db_manager(self)` (line 392)
  - `_build_prompt(paper)` (line 407)
  - `appraise_paper(self, paper_dict, relevance_score)` (line 456)
  - `_appraise_paper_swarm(self, paper_dict, relevance_score)` (line 500)
  - `appraise_candidates_batch(self, min_relevance, active_profile, render, force_reappraise)` (line 550)
  - `_get_console(self)` (line 712)
  - `_render_existing_quadrant_distribution(self, db, min_relevance, render)` (line 723)
  - `render_quadrant_summary(self, results)` (line 780)
  - `run(self, min_relevance, active_profile, force_reappraise)` (line 839)

### Functions

- `_resolve_project_root()` (line 65)
- `_load_config()` (line 80)
- `_normalize_ternary(value)` (line 102)
- `map_evidence_quadrant(relevance_score, quality_score)` (line 259)
- `_resolve_batch_concurrency()` (line 323)
- `main(argv)` (line 865)

### Dependencies

- src/core/ai_manager.py
- src/core/database_manager.py
- src/prisma/dspy_signatures.py
- src/prisma/quality_swarm.py

---

## Module: src/prisma/quality_swarm.py

**Summary:** Module: quality_swarm.py

### Classes

- `SkillCompiler` (line 177)
  - One-time compiler of domain-specialized auditor skill files.
  - `__init__(self, ai_manager, profile_name)` (line 195)
  - `_load_profile_config(self, profile_name)` (line 208)
  - `_inject_placeholders(template_text, config)` (line 235)
  - `_select_compiler_model(self)` (line 268)
  - `_polish_with_llm(self, skill_key, injected_text)` (line 289)
  - `compiled_skills_exist(self, profile_name)` (line 331)
  - `compile_profile_skills(self, profile_name, force_recompile)` (line 349)
- `SmartSectionSlicer` (line 406)
  - Extract targeted text slices from a paper record for each auditor.
  - `_cap_words(text, max_words)` (line 448)
  - `_extract_sections(self, text)` (line 463)
  - `_cached_section_dir(paper)` (line 511)
  - `_load_cached_sections(self, paper)` (line 529)
  - `slice_for_auditor(self, auditor_key, paper, max_words)` (line 553)
- `TheoryAuditResult` (line 611)
  - TheoryAuditor output for Kitchenham Q1 (aims/formulation/scope).
  - `_coerce(cls, value)` (line 624)
  - `mean_score(self)` (line 629)
- `OperationalAuditResult` (line 634)
  - OperationalAuditor output for Kitchenham Q2 (context realism).
  - `_coerce(cls, value)` (line 647)
  - `mean_score(self)` (line 652)
- `BenchmarkAuditResult` (line 657)
  - BenchmarkAuditor output for Kitchenham Q3 and Q4.
  - `_coerce(cls, value)` (line 673)
  - `mean_score(self)` (line 678)
- `OpenScienceAuditResult` (line 684)
  - OpenScienceAuditor output for Kitchenham Q5 and Q6.
  - `_coerce(cls, value)` (line 700)
  - `mean_score(self)` (line 705)
- `SkillAuditor` (line 715)
  - Base class for the four forensic quality auditor personas.
  - `__init__(self, skill_text, ai_manager)` (line 744)
  - `load_compiled_skill(cls, profile_name)` (line 756)
  - `_build_prompt(self, title, slice_text)` (line 787)
  - `_result_from_json(self, data)` (line 813)
  - `_deterministic_audit(self, text)` (line 829)
  - `audit(self, paper, slice_text)` (line 862)
- `TheoryAuditor` (line 889)
  - Forensic auditor for Kitchenham Q1 (formal problem formulation).
- `OperationalAuditor` (line 915)
  - Forensic auditor for Kitchenham Q2 (operational context realism).
- `BenchmarkAuditor` (line 941)
  - Forensic auditor for Kitchenham Q3 and Q4 (empirical rigor).
- `OpenScienceAuditor` (line 971)
  - Forensic auditor for Kitchenham Q5 and Q6 (open science).
- `SwarmQualityVerdict` (line 1007)
  - Aggregated result of the four-auditor forensic quality swarm.
- `KitchenhamQualitySynthesizer` (line 1029)
  - Concurrent dispatcher and consensus synthesizer of the Tier-2 swarm.
  - `__init__(self, ai_manager, profile_name)` (line 1048)
  - `_ensure_ai_manager(self)` (line 1060)
  - `_build_auditors(self, profile_name)` (line 1074)
  - `_score_band(cls, mean_score)` (line 1095)
  - `compute_kappa_qual(cls, audits)` (line 1111)
  - `_synthesize_narrative(audits, rubric, quadrant, kappa)` (line 1132)
  - `synthesize(self, paper, relevance_score, active_profile)` (line 1176)

### Functions

- `_resolve_project_root()` (line 65)
- `_templates_dir()` (line 102)
- `_profile_skills_dir(profile_name)` (line 112)
- `_default_profile_name()` (line 125)
- `resolve_quality_swarm_workers()` (line 157)
- `main(argv)` (line 1284)

### Dependencies

- src/core/ai_manager.py
- src/core/hardware_advisor.py
- src/core/profile_manager.py
- src/prisma/dspy_signatures.py
- src/prisma/quality_appraisal.py
- src/prisma/swarm_evaluators.py

---

## Module: src/prisma/scoping_review_synthesizer.py

**Summary:** Module: scoping_review_synthesizer.py

### Functions

- `_title(paper)` (line 23)
- `_authors(paper)` (line 35)
- `_reference_line(paper, index)` (line 48)
- `_methodology_map(included_papers)` (line 67)
- `synthesize_scoping_review(included_papers, prisma_counts, topic)` (line 94)
- `synthesize_scoping_review_latex(included_papers, prisma_counts, topic)` (line 204)

### Dependencies

- src/prisma/mermaid_generator.py

---

## Module: src/prisma/skills/__init__.py

**Summary:** Module: __init__.py (src/prisma/skills)

---

## Module: src/prisma/swarm_evaluators.py

**Summary:** Module: swarm_evaluators.py

### Classes

- `ReviewerVerdict` (line 87)
  - A single reviewer persona's structured judgement of one study.
- `ConsensusVerdict` (line 106)
  - The aggregated result of the multi-agent consensus arbitration.
- `ReviewerPersona` (line 251)
  - Typed base persona for a specialized multi-agent reviewer.
  - `_build_prompt(self, title, abstract, inclusion_criteria, exclusion_criteria)` (line 268)
  - `_verdict_from_json(self, data)` (line 283)
  - `_deterministic_review(self, title, abstract)` (line 322)
  - `review(self, title, abstract, inclusion_criteria, exclusion_criteria, ai_manager)` (line 360)
- `AlgorithmicReviewer` (line 396)
  - Algorithmic rigor reviewer persona.
- `EmpiricalReviewer` (line 429)
  - Empirical rigor reviewer persona.
- `OperationalReviewer` (line 459)
  - Swarm operational reviewer persona.
- `SwarmConsensusArbiter` (line 493)
  - Aggregate individual reviewer verdicts into a consensus decision.
  - `__init__(self, ai_manager)` (line 505)
  - `adjudicate(self, verdicts)` (line 514)
  - `_unanimous_synthesis(self, decision, verdicts, consensus_score, kappa)` (line 564)
  - `_split_synthesis(self, decision, verdicts, counts, kappa)` (line 580)
  - `_adjudicate_split(self, votes, verdicts, counts)` (line 604)
  - `_cot_prompt(self, verdicts)` (line 640)

### Functions

- `resolve_swarm_workers()` (line 50)
- `_keyword_hits(text, keywords)` (line 66)
- `calculate_cohens_kappa(votes)` (line 132)
- `cohens_kappa_pairwise(votes_a, votes_b)` (line 183)
- `_review_prompt(persona_name, role, focus)` (line 226)

### Dependencies

- src/prisma/dspy_signatures.py

---

## Module: src/search/__init__.py

**Summary:** Module: __init__.py

### Dependencies

- src/search/citation_snowballing.py
- src/search/code_first_search.py
- src/search/neural_vector_search.py

---

## Module: src/search/citation_snowballing.py

**Summary:** Module: citation_snowballing.py

### Classes

- `CitationSnowballEngine` (line 75)
  - Traverse the citation graph around a seed paper and import relevant nodes.
  - `__init__(self, ai_manager, db_manager, timeout)` (line 89)
  - `_get_json(self, url, params)` (line 104)
  - `_work_by_doi(self, doi)` (line 121)
  - `_works_by_ids(self, openalex_ids, limit)` (line 135)
  - `_citing_works(self, work_id, year_from, year_to, limit)` (line 152)
  - `_reconstruct_abstract(inverted_index)` (line 175)
  - `_normalize_openalex_work(work)` (line 193)
  - `_normalize_crossref_item(self, item)` (line 219)
  - `_crossref_references(self, doi, limit)` (line 239)
  - `_semantic_scholar_edges(self, doi, kind, limit)` (line 258)
  - `_dedupe(self, papers)` (line 292)
  - `_filter_relevant(self, papers, criteria)` (line 323)
  - `_deterministic_relevant(title, abstract)` (line 363)
  - `_import_papers(self, papers)` (line 382)
  - `resolve_seed(self, seed)` (line 417)
  - `_short_id(openalex_id)` (line 465)
  - `backward_snowball(self, seed, depth, limit)` (line 476)
  - `forward_snowball(self, seed, year_from, year_to, limit)` (line 512)
  - `generate_genealogy(seed, backward, forward)` (line 538)
  - `render_genealogy(self, results)` (line 572)
  - `export_snowball_report(self, seed, results, output_dir)` (line 639)
  - `run(self, seed, depth, year_from, year_to, import_to_db, criteria, render)` (line 723)

### Functions

- `_md_escape(text)` (line 41)
- `_format_link(doi, url)` (line 55)

### Dependencies

- src/core/database_manager.py
- src/prisma/dspy_modules.py

---

## Module: src/search/code_first_search.py

**Summary:** Module: code_first_search.py

### Classes

- `CodeFirstSearchEngine` (line 81)
  - Discover code-linked, reproducible research papers.
  - `__init__(self, timeout)` (line 93)
  - `_search_github_repos(self, query, limit)` (line 105)
  - `_is_reproducible(self, record)` (line 136)
  - `_search_paperswithcode(self, query, limit)` (line 151)
  - `run(self, query, limit, render)` (line 180)
  - `render_results(self, results)` (line 211)
  - `export_search_report(self, query, results, output_dir)` (line 293)
  - `_match_db_papers(self, query)` (line 385)

### Functions

- `_md_escape(text)` (line 39)
- `_format_link(doi, url)` (line 53)

### Dependencies

- src/core/database_manager.py

---

## Module: src/search/fulltext_search.py

**Summary:** Module: fulltext_search.py

### Classes

- `FullTextSearchEngine` (line 65)
  - SQLite FTS5 full-text search over cached paper full-text bodies.
  - `__init__(self, db_path)` (line 72)
  - `_resolve_active_db_path()` (line 83)
  - `_connect(self)` (line 88)
  - `_ensure_fts_table(self)` (line 95)
  - `index_paper(self, paper_id, title, fulltext_content)` (line 105)
  - `index_from_cache(self)` (line 124)
  - `_paper_titles(self)` (line 161)
  - `search_fulltext(self, query, limit)` (line 168)
  - `_estimate_page(fulltext, snippet)` (line 209)
  - `render_results(self, results)` (line 231)
  - `run(self, query, limit)` (line 267)

### Functions

- `_resolve_project_root()` (line 55)

### Dependencies

- src/core/database_manager.py

---

## Module: src/search/neural_vector_search.py

**Summary:** Module: neural_vector_search.py

### Classes

- `NeuralVectorSearchEngine` (line 67)
  - Rank papers semantically using local dense embeddings and cosine similarity.
  - `__init__(self, model, base_url, timeout)` (line 84)
  - `embed(self, text)` (line 99)
  - `_extract_vector(data)` (line 128)
  - `cosine_similarity(u, v)` (line 144)
  - `rank(self, query, candidates)` (line 162)
  - `_lexical_rank(query, candidates)` (line 193)
  - `_load_cached_embeddings(self)` (line 219)
  - `_index_uncached(self, uncached, batch_size, max_workers)` (line 232)
  - `_matrix_rank(self, query, candidates, cached)` (line 287)
  - `_snippet(text, query, width)` (line 337)
  - `render_results(self, results, query)` (line 366)
  - `_md_escape(text)` (line 403)
  - `_format_link(doi, url)` (line 418)
  - `export_search_report(self, query, results, output_dir, corpus_size)` (line 437)
  - `search(self, query, candidates, top_k)` (line 520)
  - `run(self, query, top_k, render)` (line 534)
  - `_load_candidates(self)` (line 576)

### Functions

- `dump_result(results)` (line 608)

### Dependencies

- config/settings.py
- src/core/database_manager.py

---

## Module: src/services/__init__.py

**Summary:** TALOS in-tree microservices package.

---

## Module: src/services/cognitive_mesh/__init__.py

**Summary:** Module: __init__.py

### Dependencies

- src/services/cognitive_mesh/benchmarks.py
- src/services/cognitive_mesh/buffer_sync.py
- src/services/cognitive_mesh/client.py
- src/services/cognitive_mesh/dto.py
- src/services/cognitive_mesh/rate_limiter.py
- src/services/cognitive_mesh/registry.py
- src/services/cognitive_mesh/reporter.py
- src/services/cognitive_mesh/router.py
- src/services/cognitive_mesh/scavenger.py
- src/services/cognitive_mesh/self_healing.py
- src/services/cognitive_mesh/xai_ledger.py

---

## Module: src/services/cognitive_mesh/benchmarks.py

**Summary:** Module: benchmarks.py

### Classes

- `ModelBenchmarkClient` (line 198)
  - Scientific benchmark client with a local cache and role-based pairing.
  - `__init__(self, cache_path)` (line 205)
  - `_load_cache(self)` (line 215)
  - `_save_cache(self)` (line 228)
  - `_ensure_cache(self)` (line 245)
  - `refresh(self, online)` (line 258)
  - `_fetch_remote_benchmarks(self)` (line 283)
  - `_merge_records(self, records)` (line 310)
  - `ingest_remote_records(self, records)` (line 318)
  - `get_top_models_by_role(self)` (line 342)
  - `reconcile_local_budget(self)` (line 373)
  - `render_discovery_table(self)` (line 409)
  - `_render_plain(self)` (line 450)

### Functions

- `fuzzy_enrich_benchmarks(model_id, developer)` (line 163)
- `run_discover_llms(online)` (line 464)

### Dependencies

- src/core/hardware_advisor.py

---

## Module: src/services/cognitive_mesh/buffer_sync.py

**Summary:** Module: buffer_sync.py

### Classes

- `BufferSyncEngine` (line 38)
  - Store-and-forward JSONL sync between remote workers and the cache.
  - `__init__(self, cache_path)` (line 41)
  - `_resolve_root()` (line 48)
  - `ingest_jsonl_buffer(self, file_path)` (line 58)
  - `export_worker_buffer(self, models, output_path)` (line 85)
  - `_parse_jsonl(self, file_path)` (line 109)
  - `_deduplicate(records)` (line 134)
  - `_merge_into_cache(self, records)` (line 143)
  - `_cache_record_count(self)` (line 150)

### Dependencies

- src/services/cognitive_mesh/benchmarks.py

---

## Module: src/services/cognitive_mesh/client.py

**Summary:** Module: client.py

### Classes

- `CognitiveMeshClient` (line 49)
  - Unified facade for in-process and HTTP Cognitive Mesh consumption.
  - `__init__(self, base_url, router)` (line 59)
  - `dispatch(self, request)` (line 71)
  - `_dispatch_http(self, request)` (line 84)
  - `providers(self)` (line 104)
  - `scavenge(self, window_days)` (line 128)

### Dependencies

- src/services/cognitive_mesh/dto.py
- src/services/cognitive_mesh/registry.py
- src/services/cognitive_mesh/router.py
- src/services/cognitive_mesh/scavenger.py

---

## Module: src/services/cognitive_mesh/dto.py

**Summary:** Module: dto.py

### Classes

- `RoutingStrategy` (line 48)
  - The five named cognitive routing strategies.
- `ProviderHealthState` (line 65)
  - The six-state self-healing circuit-breaker health machine.
- `AccessTier` (line 90)
  - The four explicit model/endpoint access tiers for zero-config failover.
- `TaskComplexity` (line 109)
  - The four civilian task-complexity bands used by the dynamic swarm sizer.
- `RouterTaskRequest` (line 129)
  - Standalone Pydantic v2 request DTO for a cognitive routing dispatch.
- `RouterTaskResponse` (line 155)
  - Standalone Pydantic v2 response DTO for a cognitive routing dispatch.
- `ModelSpec` (line 183)
  - Canonical model identity shared across routing, discovery, and reporting.
- `ProviderSpec` (line 205)
  - Provider identity and runtime status DTO (Pydantic mirror of the registry).
- `BenchmarkScorecard` (line 231)
  - Benchmark metrics for a single model.
- `ScavengedModel` (line 255)
  - A single discovered model with market and hardware metadata.
- `MarketIntelligenceReport` (line 302)
  - Aggregate autonomous scavenging report.
- `ProviderHealthReport` (line 338)
  - Single provider health probe result produced by ApiHealthProbeEngine.
- `MeshDiagnosticReport` (line 363)
  - Aggregate self-healing mesh diagnostic produced by ApiHealthProbeEngine.
- `XAiDecisionRecord` (line 385)
  - Append-only Explainable AI (XAI) audit record for a routing decision.
- `SwarmSizingRecommendation` (line 418)
  - Dynamic swarm-sizing recommendation produced by ``DynamicSwarmSizer``.

---

## Module: src/services/cognitive_mesh/rate_limiter.py

**Summary:** Module: rate_limiter.py

### Classes

- `TokenBucketRateLimiter` (line 61)
  - Proactive smooth micro-throttling token bucket for LLM providers.
  - `__init__(self, sleep_fn, clock)` (line 76)
  - `acquire(self, provider_name, tokens)` (line 90)
  - `get_provider_status(self)` (line 127)
  - `_normalize(provider_name)` (line 157)
  - `_rpm(key)` (line 161)
  - `_refill_rate(rpm)` (line 165)
  - `_capacity(r)` (line 169)
  - `_is_unbounded(r)` (line 173)
  - `_ensure_bucket(self, key, r, now)` (line 176)
  - `_refill(self, bucket, r, now)` (line 183)

### Functions

- `get_rate_specs()` (line 52)

---

## Module: src/services/cognitive_mesh/registry.py

**Summary:** Module: registry.py

### Classes

- `LLMProvider` (line 86)
  - Canonical enumeration of the sixteen registered inference providers.
- `ProviderDescriptor` (line 114)
  - Value object describing a single inference provider adapter.
- `ProviderRegistry` (line 142)
  - Extensible registry of LLM provider descriptors.
  - `__init__(self)` (line 157)
  - `_register_defaults(self)` (line 165)
  - `register(self, descriptor)` (line 309)
  - `_refresh(self, descriptor)` (line 320)
  - `_evaluate_active(self, descriptor)` (line 339)
  - `_is_port_open(base_url, timeout)` (line 358)
  - `get(self, name)` (line 383)
  - `list_all(self)` (line 398)
  - `list_active(self)` (line 406)

### Functions

- `get_provider_registry()` (line 419)
- `get_available_providers()` (line 431)

### Dependencies

- config/settings.py

---

## Module: src/services/cognitive_mesh/reporter.py

**Summary:** Module: reporter.py

### Classes

- `IntelligenceReporter` (line 40)
  - Render dual market-intelligence reports (Markdown and standalone HTML).
  - `generate_reports(self, report_data, output_dir)` (line 45)
  - `_render_markdown(self, report)` (line 72)
  - `_md_cell(value)` (line 209)
  - `_finops_cost(prompt_usd, completion_usd, screening)` (line 218)
  - `_select_champions(cls, report)` (line 245)
  - `_render_html(self, report)` (line 321)
  - `_render_card(model)` (line 394)
  - `_render_champion_cards(report)` (line 427)

### Functions

- `_badge(vram_class)` (line 458)
- `_tier_badge(tier)` (line 475)

### Dependencies

- src/services/cognitive_mesh/dto.py

---

## Module: src/services/cognitive_mesh/router.py

**Summary:** Module: router.py

### Classes

- `ProviderHttpError` (line 147)
  - Transport error carrying an HTTP status code.
  - `__init__(self, provider, status_code, message)` (line 155)
- `_ProviderMetrics` (line 161)
  - Per-provider runtime telemetry tracked by the router.
  - `__init__(self)` (line 164)
- `DynamicSwarmSizer` (line 172)
  - Dynamic swarm cardinality selector mapping task complexity to K.
  - `__init__(self, registry, ledger)` (line 213)
  - `recommend_swarm(self, task_type, input_payload)` (line 221)
  - `_compute_complexity(self, task_type, payload)` (line 274)
  - `_reasoning_depth(cls, task_type)` (line 283)
  - `_token_score(payload)` (line 291)
  - `_safety_score(payload)` (line 299)
  - `_band_for_complexity(complexity)` (line 308)
  - `_swarm_size_for_band(band)` (line 318)
  - `_build_rationale(task_type, complexity, swarm_size, band)` (line 327)
  - `_safety_flags(payload)` (line 337)
  - `_active_provider_names(self)` (line 349)
  - `_free_tier_frontier(self, active)` (line 355)
  - `_ordered_model_chain(self, active, k)` (line 364)
  - `_chain_slot(self, provider)` (line 392)
- `CognitiveMetaRouter` (line 402)
  - Decoupled multi-strategy cognitive meta-router with circuit breaking.
  - `__init__(self, registry, transport, local_semaphore_limit, ema_alpha, breaker, rate_limiter, swarm_sizer, ledger)` (line 421)
  - `dispatch(self, task_type, strategy, payload, **kwargs)` (line 448)
  - `recommend_swarm(self, task_type, input_payload)` (line 480)
  - `_get_swarm_sizer(self)` (line 499)
  - `record_result(self, provider, latency_ms, prompt_tokens, completion_tokens, http_status)` (line 505)
  - `latch_provider(self, provider, reason)` (line 537)
  - `release_provider(self, provider)` (line 546)
  - `get_metrics(self)` (line 556)
  - `_execute(self, request)` (line 577)
  - `_zero_config_free_failover(self, active)` (line 643)
  - `_invoke(self, provider_name, request)` (line 667)
  - `_transport_call(self, provider_name, model, request)` (line 710)
  - `_candidates_for_strategy(self, strategy, active)` (line 727)
  - `_ema_ttft(self, provider)` (line 749)
  - `_quality(self, provider)` (line 753)
  - `_combined_cost(self, provider)` (line 756)
  - `_estimate_cost(self, provider, prompt_tokens, completion_tokens)` (line 760)
  - `_record_success(self, provider, latency_ms, prompt_tokens, completion_tokens)` (line 768)
  - `_record_error(self, provider)` (line 783)
  - `_latch(self, provider, reason)` (line 786)
  - `_is_latched(self, provider)` (line 791)
  - `_active_provider_names(self)` (line 794)

### Dependencies

- src/services/cognitive_mesh/dto.py
- src/services/cognitive_mesh/rate_limiter.py
- src/services/cognitive_mesh/registry.py
- src/services/cognitive_mesh/self_healing.py
- src/services/cognitive_mesh/xai_ledger.py

---

## Module: src/services/cognitive_mesh/scavenger.py

**Summary:** Module: scavenger.py

### Classes

- `ModelScoutAgent` (line 154)
  - Autonomous Model Scout reconciling LLM catalogues against the RTX 4070 budget.
  - `__init__(self, vram_gb)` (line 166)
  - `scavenge_market(self, window_days, fetch_all)` (line 173)
  - `_forage_huggingface(self)` (line 246)
  - `_parse_huggingface_payload(payload)` (line 257)
  - `_forage_openrouter(self, window_days, fetch_all)` (line 298)
  - `_parse_openrouter_payload(payload, window_days, fetch_all)` (line 309)
  - `_forage_ollama(self)` (line 368)
  - `_parse_ollama_payload(payload)` (line 382)
  - `_load_cached_benchmarks(self)` (line 420)
  - `_has_token(name, token)` (line 462)
  - `_classify_model(model_id, params, price, context, source)` (line 481)
  - `_classify_vram(self, model)` (line 542)
  - `_recommend_role(model)` (line 563)
  - `_apply_fuzzy_benchmarks(model)` (line 589)
  - `_compute_summary(self, report)` (line 618)
  - `_http_get_json(url, params)` (line 657)
  - `_active_provider_count(self)` (line 670)
  - `_parse_param_count(text)` (line 678)
  - `_extract_license(item)` (line 688)
  - `_iso_date(item)` (line 700)
  - `_price_per_1m(value)` (line 708)

### Dependencies

- src/services/cognitive_mesh/benchmarks.py
- src/services/cognitive_mesh/dto.py
- src/services/cognitive_mesh/registry.py
- src/services/cognitive_mesh/self_healing.py

---

## Module: src/services/cognitive_mesh/self_healing.py

**Summary:** Module: self_healing.py

### Classes

- `SelfHealingCircuitBreaker` (line 138)
  - Six-state self-healing circuit breaker with exponential backoff.
  - `__init__(self, initial_backoff_seconds, max_backoff_seconds)` (line 159)
  - `state(self, provider)` (line 175)
  - `error_count(self, provider)` (line 187)
  - `backoff_until(self, provider)` (line 199)
  - `should_attempt(self, provider)` (line 211)
  - `record_success(self, provider)` (line 247)
  - `record_http_status(self, provider, status)` (line 258)
  - `record_timeout(self, provider)` (line 279)
  - `record_unreachable(self, provider)` (line 287)
  - `force_probe(self, provider)` (line 297)
  - `_set_backoff(self, provider, state)` (line 314)
- `ApiHealthProbeEngine` (line 335)
  - Concurrent lightweight health probe over all sixteen providers.
  - `__init__(self, registry, breaker, timeout, max_workers, probe_fn)` (line 353)
  - `probe_all(self)` (line 373)
  - `_list_all(self)` (line 416)
  - `_probe_one(self, descriptor)` (line 427)
  - `_run_probe(self, descriptor)` (line 453)
  - `_build_report(self, descriptor, tier, status, latency)` (line 473)
  - `_inert_report(descriptor)` (line 504)
  - `_tcp_reachable(base_url, timeout)` (line 521)

### Functions

- `classify_access_tier(provider_name)` (line 103)
- `classify_model_access_tier(source, provider)` (line 118)

### Dependencies

- src/services/cognitive_mesh/dto.py
- src/services/cognitive_mesh/registry.py

---

## Module: src/services/cognitive_mesh/server.py

**Summary:** Module: server.py

### Classes

- `ScavengeRequest` (line 86)
  - Request body for the autonomous scavenge endpoint.
- `SwarmRecommendRequest` (line 142)
  - Request body for the dynamic swarm-recommendation endpoint.

### Functions

- `_get_ledger()` (line 69)
- `_get_router()` (line 77)
- `dispatch(request)` (line 93)
- `providers()` (line 106)
- `benchmarks()` (line 116)
- `scavenge(request)` (line 130)
- `swarm_recommend(request)` (line 152)
- `xai_trail(limit)` (line 165)
- `_normalize_sync_payload(payload)` (line 183)
- `mesh_sync(raw_request)` (line 204)
- `health()` (line 244)

### Dependencies

- src/services/cognitive_mesh/benchmarks.py
- src/services/cognitive_mesh/buffer_sync.py
- src/services/cognitive_mesh/dto.py
- src/services/cognitive_mesh/registry.py
- src/services/cognitive_mesh/router.py
- src/services/cognitive_mesh/scavenger.py
- src/services/cognitive_mesh/xai_ledger.py

---

## Module: src/services/cognitive_mesh/xai_ledger.py

**Summary:** Module: xai_ledger.py

### Classes

- `XAiDecisionLedger` (line 50)
  - Append-only Explainable AI (XAI) decision audit ledger.
  - `__init__(self, log_path)` (line 62)
  - `append(self, record)` (line 70)
  - `latest(self, limit)` (line 94)
  - `explain(self, record)` (line 117)
  - `_coerce(record)` (line 158)

### Functions

- `_iso_now()` (line 176)
- `_ensure_dir(path)` (line 185)

---

## Module: src/utils/academic_export.py

**Summary:** Module: academic_export.py

### Functions

- `_escape_latex(text)` (line 52)
- `_escape_bibtex(text)` (line 59)
- `_authors(paper)` (line 66)
- `_first_author_surname(authors_str)` (line 71)
- `_make_citation_key(paper, used_keys)` (line 80)
- `_paper_entry_type(paper)` (line 96)
- `export_bibtex(papers, output_path)` (line 104)
- `export_latex_table(papers, output_path, caption)` (line 139)
- `export_prisma_candidate_table(candidate_sets, output_path)` (line 173)
- `_load_elite_papers(min_score)` (line 198)
- `main(argv)` (line 218)

### Dependencies

- src/core/database_manager.py

---

## Module: src/utils/ai_strategy_selector.py

**Summary:** Module: ai_strategy_selector.py

### Functions

- `_current_strategy()` (line 49)
- `_render_confirmation(strategy_key)` (line 62)
- `select_ai_execution_strategy(target_strategy)` (line 77)
- `_recommendation_stack()` (line 127)
- `_active_provider_names()` (line 140)
- `_persist_stack(exec_strategy, screening_local, screening_cloud, reasoning_local, reasoning_cloud)` (line 149)
- `_render_apply_confirmation(strategy, ok)` (line 210)
- `apply_optimal_models(strategy)` (line 221)
- `_render_impact_matrix(recs)` (line 270)
- `configure_ai_strategy()` (line 314)

### Dependencies

- src/core/hardware_advisor.py
- src/core/profile_manager.py
- src/services/cognitive_mesh/registry.py
- src/utils/research_setup_wizard.py
- src/utils/ui_theme.py

---

## Module: src/utils/api_health_check.py

**Summary:** Module: api_health_check.py (v1.1)

### Functions

- `ping_api(url, headers, timeout)` (line 24)
- `_format_result(name, status, detail)` (line 33)
- `check_source(source_name, key_env_var, ping_url, headers_fn, pbar)` (line 47)
- `check_ai_provider(provider_name, env_var, pbar)` (line 81)
- `run_diagnostics()` (line 121)

---

## Module: src/utils/bibtex_exporter.py

**Summary:** Module: bibtex_exporter.py

### Classes

- `BibTeXExporter` (line 97)
  - Automated BibTeX / LaTeX scientific library exporter.
  - `__init__(self)` (line 116)
  - `_first_author_surname(authors_str)` (line 126)
  - `_first_title_keyword(title)` (line 142)
  - `_build_cite_key(self, paper, used_keys)` (line 160)
  - `_entry_type(paper)` (line 188)
  - `_venue(paper)` (line 206)
  - `_rigor_label(quality_score)` (line 227)
  - `_format_entry(self, paper, used_keys)` (line 245)
  - `export_library(self, output_path, min_score, only_prisma_included, active_profile, min_quality, quadrant)` (line 305)
  - `render_export_summary(self, filepath, count)` (line 380)
  - `export_and_render(self, output_path, min_score, only_prisma_included, active_profile, min_quality, quadrant)` (line 400)

### Functions

- `_escape_bibtex(text)` (line 69)
- `_clean_key_token(text)` (line 83)
- `main(argv)` (line 427)

### Dependencies

- src/core/database_manager.py

---

## Module: src/utils/codebase_documenter/__init__.py

**Summary:** Module: __init__.py

### Dependencies

- src/utils/codebase_documenter/architecture_ledger.py
- src/utils/codebase_documenter/ast_analyzer.py
- src/utils/codebase_documenter/markdown_html_generator.py
- src/utils/codebase_documenter/relay_orchestrator.py

---

## Module: src/utils/codebase_documenter/architecture_ledger.py

**Summary:** Module: architecture_ledger.py

### Classes

- `ArchitectureLedger` (line 43)
  - Living architectural decision ledger with a global symbol table.
  - `__init__(self, ledger_path)` (line 50)
  - `load(self)` (line 58)
  - `save(self, data)` (line 80)
  - `_empty_state()` (line 98)
  - `record_decision(self, module, decision, rationale)` (line 111)
  - `decisions(self)` (line 131)
  - `mark_documented(self, module_path)` (line 143)
  - `documented_modules(self)` (line 155)
  - `register_symbols(self, module_path, classes, functions)` (line 163)
  - `symbol_table(self)` (line 182)
  - `get_undocumented(self, discovered_modules)` (line 190)

### Functions

- `_iso_now()` (line 203)

---

## Module: src/utils/codebase_documenter/ast_analyzer.py

**Summary:** Module: ast_analyzer.py

### Classes

- `FunctionSymbol` (line 34)
  - A single function or method symbol extracted from a module.
- `ClassSymbol` (line 51)
  - A single class symbol extracted from a module.
- `ModuleBlueprint` (line 68)
  - Static analysis result for one source module.
- `CodebaseAstAnalyzer` (line 90)
  - AST parser that extracts a documentation blueprint for every module.
  - `__init__(self, root_dir, include_roots, exclude_dirs)` (line 99)
  - `_resolve_root()` (line 123)
  - `discover_modules(self)` (line 134)
  - `_relative(self, path)` (line 160)
  - `analyze_file(self, rel_path)` (line 167)
  - `_extract_classes(tree)` (line 206)
  - `_extract_functions(tree)` (line 230)
  - `analyze_all(self)` (line 248)
  - `build_dependency_graph(self, analyses)` (line 261)
  - `_file_index(self, paths)` (line 287)
  - `to_serializable(self, analyses)` (line 305)
  - `_blueprint_to_dict(blueprint)` (line 319)

### Functions

- `_format_args(node)` (line 355)
- `_first_sentence(docstring)` (line 377)

---

## Module: src/utils/codebase_documenter/markdown_html_generator.py

**Summary:** Module: markdown_html_generator.py

### Classes

- `CodebaseDocGenerator` (line 38)
  - Compile codebase blueprints into Markdown and standalone HTML.
  - `__init__(self, output_dir, version)` (line 46)
  - `generate(self, records, llm_contents, graph)` (line 56)
  - `_build_markdown(self, records, llm_contents, graph)` (line 97)
  - `_markdown_section(self, record, llm_contents, graph)` (line 128)
  - `_stats(records, graph)` (line 190)
  - `_build_html(self, records, llm_contents, graph)` (line 207)
  - `_render_module_card(self, record, llm_contents, graph)` (line 232)

### Functions

- `_html_page(body)` (line 299)
- `_iso_now()` (line 384)
- `_anchor(path)` (line 389)
- `_escape(text)` (line 401)

---

## Module: src/utils/codebase_documenter/relay_orchestrator.py

**Summary:** Module: relay_orchestrator.py

### Classes

- `MultiLlmRelayOrchestrator` (line 53)
  - Stateful multi-LLM relay orchestrator with XAI tracking.
  - `__init__(self, analyzer, architecture_ledger, xai_ledger, router, generator)` (line 64)
  - `run(self, mode, dry_run, limit)` (line 82)
  - `_build_prompt(self, blueprint, prior_paths, handoff_memo)` (line 168)
  - `_handoff(path, blueprint)` (line 197)
  - `_extract_content(response)` (line 203)

### Dependencies

- src/services/cognitive_mesh/dto.py
- src/services/cognitive_mesh/router.py
- src/services/cognitive_mesh/xai_ledger.py
- src/utils/codebase_documenter/architecture_ledger.py
- src/utils/codebase_documenter/ast_analyzer.py
- src/utils/codebase_documenter/markdown_html_generator.py

---

## Module: src/utils/console_dashboard/__init__.py

**Summary:** Module: __init__.py

### Dependencies

- src/utils/console_dashboard/hud_renderer.py
- src/utils/console_dashboard/layout_builder.py
- src/utils/console_dashboard/progress_monitors.py
- src/utils/console_dashboard/submenu_renderer.py
- src/utils/console_dashboard/terminal_previewer.py
- src/utils/console_dashboard/tree_views.py

---

## Module: src/utils/console_dashboard/hud_renderer.py

**Summary:** Module: hud_renderer.py

### Classes

- `HudRenderer` (line 64)
  - Render the persistent telemetry HUD as a compact Rich Panel.
  - `__init__(self)` (line 76)
  - `build_hud(self)` (line 84)
  - `_vault_status(self)` (line 175)
  - `_rate_limiter_status(self)` (line 191)
  - `_profile_name(self)` (line 205)
  - `_paper_metrics(self)` (line 220)
  - `_gpu_name(self)` (line 248)
  - `_vram_gb(self)` (line 267)
  - `_ollama_status(self, host, port)` (line 280)
  - `_mesh_health(self)` (line 296)
  - `_strategy_label(self)` (line 331)
  - `_model_metrics(self)` (line 349)

### Functions

- `_re_first_int(pattern, text)` (line 45)

### Dependencies

- config/settings.py
- src/core/database_manager.py
- src/core/database_vault.py
- src/core/hardware.py
- src/core/profile_manager.py
- src/services/cognitive_mesh/dto.py
- src/services/cognitive_mesh/rate_limiter.py
- src/services/cognitive_mesh/registry.py
- src/services/cognitive_mesh/self_healing.py

---

## Module: src/utils/console_dashboard/layout_builder.py

**Summary:** Module: layout_builder.py

### Classes

- `DashboardLayoutBuilder` (line 39)
  - Construct the 4-panel Scientific Terminal Dashboard layout.
  - `__init__(self, hud_panel)` (line 51)
  - `build_dashboard(self, hud_panel)` (line 64)
  - `_placeholder_header(self)` (line 107)
  - `_panel(self, title, body, border_style)` (line 123)
  - `_panel_cognitive(self)` (line 136)
  - `_panel_discovery(self)` (line 154)
  - `_panel_prisma(self)` (line 172)
  - `_panel_system(self)` (line 190)
  - `_footer(self)` (line 208)

---

## Module: src/utils/console_dashboard/progress_monitors.py

**Summary:** Module: progress_monitors.py

### Classes

- `MultiMetricProgress` (line 46)
  - Convenience wrapper around the multi-metric scientific Progress.
  - `__init__(self, progress)` (line 53)
  - `add_metric_task(self, description, total, rate, vram)` (line 61)

### Functions

- `create_scientific_progress()` (line 29)

---

## Module: src/utils/console_dashboard/submenu_renderer.py

**Summary:** Module: submenu_renderer.py

### Classes

- `RichSubmenuRenderer` (line 44)
  - Render a strict ISO/IEC 25010 three-tier Rich sub-menu.
  - `__init__(self, title, subtitle, border_style, domain)` (line 60)
  - `build(self, entries, context_shortcuts, back_label)` (line 71)
  - `prompt_choice(self, valid_range, default)` (line 96)
  - `_build_header(self)` (line 144)
  - `_build_body(self, entries, back_label)` (line 163)
  - `_build_footer(self, item_count, context_shortcuts)` (line 213)
  - `_items(entries)` (line 242)
  - `_cell(number, label, status)` (line 256)

### Functions

- `render_submenu(title, subtitle, entries, border_style, domain, context_shortcuts)` (line 275)

---

## Module: src/utils/console_dashboard/terminal_previewer.py

**Summary:** Module: terminal_previewer.py

### Classes

- `TerminalPreviewer` (line 27)
  - Preview Markdown and syntax-highlighted files in the terminal.
  - `__init__(self, console)` (line 34)
  - `preview_markdown(self, file_path)` (line 47)
  - `render_markdown(self, file_path)` (line 60)
  - `preview_syntax(self, file_path, lexer)` (line 82)
  - `render_syntax(self, file_path, lexer)` (line 100)

---

## Module: src/utils/console_dashboard/tree_views.py

**Summary:** Module: tree_views.py

### Classes

- `ScientificTreeViewer` (line 40)
  - Render scientific knowledge as styled Rich Trees.
  - `render_architecture_tree(self)` (line 48)
  - `render_research_taxonomy_tree(self)` (line 62)
  - `render_mesh_health_tree(self)` (line 80)
  - `_provider_descriptors(self)` (line 106)

### Dependencies

- src/services/cognitive_mesh/registry.py

---

## Module: src/utils/daemon_autostart.py

**Summary:** Module: daemon_autostart.py

### Functions

- `_project_root()` (line 50)
- `generate_boot_batch(profile_name)` (line 55)
- `select_daemon_profile()` (line 104)
- `install_windows_autostart(profile_name)` (line 153)
- `persist_daemon_config(profile_name, strategy, sources)` (line 204)
- `main()` (line 256)

### Dependencies

- src/core/profile_manager.py
- src/utils/ui_theme.py

---

## Module: src/utils/db_stats.py

**Summary:** Module: db_stats.py (v1.0 - The Metrics Update)

### Functions

- `print_header(title)` (line 33)
- `optimize_database(db_path)` (line 38)
- `main()` (line 98)

### Dependencies

- src/core/database_manager.py
- src/utils/snapshot_manager.py

---

## Module: src/utils/desktop_shortcut.py

**Summary:** Module: desktop_shortcut.py

### Functions

- `_project_root()` (line 34)
- `_desktop_dir()` (line 49)
- `_icon_location(root)` (line 67)
- `create_desktop_shortcut()` (line 82)
- `_render_result(success, shortcut_path, detail)` (line 129)

---

## Module: src/utils/evaluation_history.py

**Summary:** Module: evaluation_history.py

### Functions

- `_history_dir()` (line 33)
- `_history_path()` (line 43)
- `verdict_for_score(score)` (line 52)
- `normalize_authors(paper)` (line 70)
- `record_evaluation(title, authors, source, score, verdict, provider, timestamp)` (line 155)
- `read_evaluation_history(limit)` (line 185)

---

## Module: src/utils/frontend_provisioner.py

**Summary:** Module: frontend_provisioner.py

### Functions

- `_detect_architecture()` (line 93)
- `_fetch_latest_release_assets()` (line 119)
- `_get_cherry_version_from_release(release_json)` (line 146)
- `_arch_matches(combined, target_arch)` (line 178)
- `_match_asset_for_os(assets, os_name)` (line 197)
- `_match_windows_asset(assets, arch)` (line 229)
- `_match_linux_asset(assets, arch)` (line 285)
- `_match_macos_asset(assets, arch)` (line 330)
- `_resolve_download_urls()` (line 385)
- `get_os_name()` (line 426)
- `resolve_target_dir(project_root)` (line 445)
- `generate_mcp_config(output_path)` (line 465)
- `download_cherry_studio(target_dir, force)` (line 511)
- `provision_full(target_dir, force)` (line 613)

---

## Module: src/utils/generate_docs.py

**Summary:** Module: generate_docs.py (v2.0)

### Functions

- `check_ollama(url)` (line 110)
- `load_configuration()` (line 129)
- `_is_excluded(path_str)` (line 153)
- `get_code_files(selected_dirs)` (line 177)
- `estimate_file_info(file_paths)` (line 218)
- `generate_documentation(source_code, file_path, model, ollama_url, language_keyword)` (line 246)
- `save_documentation(file_path, content, output_dir, lang_code)` (line 291)
- `main()` (line 326)

### Dependencies

- src/utils/logger.py
- src/utils/ui_theme.py

---

## Module: src/utils/help_system.py

**Summary:** Module: help_system.py

### Functions

- `_section_a_sop_runbooks()` (line 66)
- `_section_b_command_matrix()` (line 126)
- `_section_c_diagnostics()` (line 196)
- `_section_d_environment()` (line 231)
- `_build_manual_group()` (line 276)
- `_open_web_manual()` (line 290)
- `render_help_manual(interactive)` (line 344)

### Dependencies

- config/settings.py
- src/utils/ui_theme.py

---

## Module: src/utils/http_client.py

**Summary:** Module: http_client.py

### Functions

- `build_session(pool_connections, pool_maxsize, timeout, user_agent)` (line 24)

---

## Module: src/utils/interactive_dashboard.py

**Summary:** Module: interactive_dashboard.py (v2.2 - Soft Shutdown)

### Functions

- `load_configuration()` (line 40)
- `index()` (line 63)
- `get_data()` (line 69)
- `get_paper_details(paper_id)` (line 75)
- `update_zotero_status()` (line 89)
- `semantic_search()` (line 101)
- `shutdown()` (line 125)

### Dependencies

- src/core/ai_manager.py
- src/core/database_manager.py

---

## Module: src/utils/logger.py

**Summary:** Module: logger.py

### Functions

- `_configure()` (line 45)
- `get_logger(name)` (line 84)

---

## Module: src/utils/migrate_database_schema.py

**Summary:** Module: migrate_database_schema.py (v2.2 - Final Migration Fix)

### Functions

- `extract_from_old_analysis(analysis_text, field)` (line 40)
- `migrate_schema()` (line 61)

### Dependencies

- src/core/database_manager.py
- src/utils/ui_theme.py

---

## Module: src/utils/model_provisioner.py

**Summary:** Module: model_provisioner.py

### Classes

- `ModelProvisioner` (line 77)
  - Universal model provisioner with deterministic protocol detection and a
  - `__init__(self, project_root, models_dir)` (line 113)
  - `detect_protocol(self, model_name)` (line 122)
  - `_sanitize(self, model_name)` (line 155)
  - `_has_valid_artifacts(self, directory)` (line 159)
  - `resolve_local_model_path(self, model_name)` (line 169)
  - `_ollama_list(self)` (line 202)
  - `_ollama_has_model(self, model_name)` (line 220)
  - `_ollama_pull(self, model_name)` (line 226)
  - `_cloud_key_for(self, model_name)` (line 246)
  - `check_available(self, model_name)` (line 258)
  - `ensure_model_available(self, model_name, silent)` (line 280)
  - `_ensure_cloud(self, model_name)` (line 300)
  - `_ensure_ollama(self, model_name)` (line 310)
  - `_ensure_huggingface(self, model_name)` (line 317)

### Functions

- `_report(model_name, protocol, available)` (line 353)
- `main(argv)` (line 359)

### Dependencies

- config/settings.py
- src/utils/logger.py

---

## Module: src/utils/recalculate_scores.py

**Summary:** Module: recalculate_scores.py (v2.0 - Recalibration Tool)

### Functions

- `recalculate_database_scores()` (line 42)

### Dependencies

- src/core/database_manager.py
- src/utils/snapshot_manager.py
- src/utils/ui_theme.py

---

## Module: src/utils/reevaluate_database.py

**Summary:** Module: reevaluate_database.py (v5.13.0 - Concurrent Cognitive Re-Evaluation Pool)

### Functions

- `load_configuration()` (line 41)
- `_apply_evaluation_batch(db_manager, updates)` (line 53)
- `main()` (line 88)

### Dependencies

- src/core/ai_manager.py
- src/core/database_manager.py
- src/utils/snapshot_manager.py
- src/utils/ui_theme.py

---

## Module: src/utils/research_setup_wizard.py

**Summary:** Module: research_setup_wizard.py

### Functions

- `_project_root()` (line 237)
- `_load_config(project_root)` (line 242)
- `_save_config(config, path)` (line 259)
- `_profiles_dir(project_root)` (line 274)
- `_active_profile_file(project_root)` (line 291)
- `_list_profiles(project_root)` (line 304)
- `_get_active_profile(project_root)` (line 320)
- `_set_active_profile(project_root, name)` (line 336)
- `_validate_profile_name(name)` (line 351)
- `_seed_profile_config(project_root, name)` (line 367)
- `_load_profile_config_to_root(project_root, name)` (line 397)
- `_persist_active_config(project_root, name)` (line 417)
- `_port_reachable(host, port, timeout)` (line 442)
- `_spawn_local_ai()` (line 460)
- `_ensure_local_ai_runtime()` (line 481)
- `_get_ai_manager()` (line 522)
- `_call_llm_text(prompt, timeout)` (line 533)
- `_analyze_scope_heuristic(topic)` (line 562)
- `_suggest_subdomains_heuristic(topic)` (line 590)
- `_analyze_scope_with_llm(topic)` (line 607)
- `_extract_salient_terms(topic, max_terms)` (line 647)
- `_generate_queries_heuristic(topic, config)` (line 682)
- `_generate_queries_llm(topic, config)` (line 721)
- `_update_env_key(env_path, key, value)` (line 780)
- `_apply_execution_strategy(strategy_key, project_root)` (line 796)
- `_write_search_window(config, path, strategy_key, days)` (line 831)
- `_sentinel_path(project_root)` (line 867)
- `_sentinel_exists(project_root)` (line 873)
- `_create_sentinel(project_root)` (line 878)
- `_api_is_alive()` (line 890)
- `_ensure_api_server()` (line 895)
- `_trigger_test_search()` (line 932)
- `_run_first_flight()` (line 949)
- `_step0_profile_selection(project_root)` (line 968)
- `_render_header(target_profile)` (line 1056)
- `_render_query_preview(config)` (line 1092)
- `_step1_research_topic(active_llm, config, config_path)` (line 1134)
- `_step2_execution_strategy(project_root)` (line 1205)
- `_prompt_custom_days()` (line 1238)
- `_step3_search_window(config, config_path)` (line 1258)
- `_step4_first_flight()` (line 1300)
- `_render_summary(topic, strategy_key, window_key, first_flight, config)` (line 1323)
- `_render_cancelled()` (line 1352)
- `main()` (line 1366)

### Dependencies

- src/ai/llm/query_translator.py
- src/core/ai_manager.py
- src/core/profile_manager.py
- src/utils/logger.py
- src/utils/ui_theme.py

---

## Module: src/utils/snapshot_manager.py

**Summary:** Module: snapshot_manager.py

### Functions

- `_resolve_backup_dir(db_path)` (line 34)
- `_prune_snapshots(backup_dir, keep)` (line 49)
- `snapshot_database(db_path, backup_dir, keep)` (line 72)

### Dependencies

- src/core/database_manager.py

---

## Module: src/utils/system_diagnostics.py

**Summary:** Module: system_diagnostics.py

### Classes

- `SystemDiagnosticsEngine` (line 121)
  - Executes and renders the 8-point TALOS diagnostic health scan.
  - `__init__(self)` (line 134)
  - `check_python_environment(self)` (line 141)
  - `check_database_integrity(self)` (line 183)
  - `check_local_ai_runtime(self)` (line 255)
  - `_port_listening(port, host)` (line 304)
  - `check_port_availability(self)` (line 324)
  - `check_filesystem_permissions(self)` (line 370)
  - `check_environment_credentials(self)` (line 410)
  - `check_daemon_status(self)` (line 448)
  - `_probe_single_endpoint(name, url)` (line 489)
  - `check_network_endpoints(self)` (line 539)
  - `run_diagnostics(self, verbose)` (line 568)
  - `_flatten_results(results)` (line 590)
  - `render_report(self, results)` (line 608)
  - `run_and_render(self)` (line 645)

### Functions

- `_result(component, target, status, detail, remediation)` (line 55)
- `_status(ok)` (line 77)

### Dependencies

- config/settings.py
- src/core/database_manager.py

---

## Module: src/utils/tray_icon.py

**Summary:** Module: tray_icon.py

### Functions

- `_project_root()` (line 61)
- `_open_path(path)` (line 81)
- `_is_api_alive(port)` (line 98)
- `_ensure_api_server()` (line 117)
- `_build_tray_icon_image()` (line 162)
- `_get_console_window_handle()` (line 184)
- `_toggle_console_visibility()` (line 197)
- `_log_minimized_to_tray()` (line 228)
- `enable_close_to_tray()` (line 243)
- `launch_tray_icon_async(on_show_hide, on_open_visualizer, on_exit)` (line 315)

---

## Module: src/utils/ui_theme.py

**Summary:** Module: ui_theme.py

---

## Module: src/utils/verify_dependency_map.py

**Summary:** Module: verify_dependency_map.py (v1.1)

### Functions

- `parse_section_7(map_path)` (line 154)
- `extract_actual_imports(py_file, project_root)` (line 226)
- `scan_all_files(project_root)` (line 293)
- `normalize_dep(dep)` (line 318)
- `compare_dependencies(documented, actual)` (line 330)
- `generate_console_summary(results, label)` (line 453)
- `generate_html_report(results, output_path, title)` (line 462)
- `generate_markdown_report(results, output_path, title)` (line 576)
- `generate_json_report(results, output_path)` (line 639)
- `parse_function_docs(map_path)` (line 661)
- `extract_actual_functions(py_file)` (line 763)
- `scan_all_functions(project_root)` (line 799)
- `compare_functions(documented, actual)` (line 837)
- `main()` (line 886)

---

## Module: talos.py

**Summary:** Module: talos.py

### Functions

- `_make_clickable_path(path_str)` (line 459)
- `_enable_windows_vt100()` (line 491)
- `_maybe_generate_focus_summary(config_path)` (line 520)
- `safe_select(message, choices, style, **kwargs)` (line 655)
- `safe_pause(msg)` (line 675)
- `prompt_source_selection()` (line 697)
- `_resolve_script_path(script_name)` (line 713)
- `_build_info_panel(title, message, border_style)` (line 734)
- `_build_results_table(papers, title)` (line 762)
- `run_script(script_name, python_exe, args, capture)` (line 817)
- `check_first_run(python_exe)` (line 861)
- `author_tools_menu(python_exe)` (line 884)
- `database_data_menu(python_exe)` (line 918)
- `system_health_menu(python_exe)` (line 972)
- `api_keys_menu(python_exe)` (line 1071)
- `_current_strategy_key()` (line 1151)
- `_launch_strategy_selector()` (line 1164)
- `_run_ai_strategy_configurator()` (line 1173)
- `profile_settings_menu(python_exe)` (line 1182)
- `_read_active_focus()` (line 1254)
- `_build_status_table()` (line 1276)
- `_view_and_pivot_research_focus(python_exe, project_root)` (line 1364)
- `_configure_daemon_autostart(project_root)` (line 1527)
- `_launch_daemon_in_new_console(project_root, python_exe)` (line 1611)
- `_launch_visualizer()` (line 1652)
- `_generate_optica_plots()` (line 1733)
- `_show_drl_status(project_root)` (line 1804)
- `_show_evaluation_history(limit)` (line 1854)
- `_run_hardware_advisor()` (line 1912)
- `_run_discover_llms()` (line 1931)
- `_render_scavenge_summary(report)` (line 1937)
- `_run_scavenge_models(days, fetch_all, report_only)` (line 1969)
- `_run_model_discovery()` (line 1999)
- `_probe_api_backend()` (line 2044)
- `_open_capabilities_viewer()` (line 2068)
- `_open_d3_architecture_graph(python_exe, project_root)` (line 2109)
- `_launch_gwo_dashboard(python_exe)` (line 2130)
- `search_ingestion_menu(python_exe)` (line 2159)
- `analysis_visualization_menu(python_exe)` (line 2265)
- `drl_gwo_menu(python_exe)` (line 2439)
- `main_menu()` (line 2532)
- `_cli_help_table()` (line 2631)
- `_parse_strategy_flag(argv)` (line 2645)
- `_flag_value(argv, flag)` (line 2663)
- `_render_harvest_summary(summary)` (line 2679)
- `_open_local_pdf(paper_id)` (line 2708)
- `_run_api_probe()` (line 2748)
- `_render_vault_verify(result)` (line 2796)
- `_render_sync_summary(result)` (line 2823)
- `_run_codebase_documentation(argv)` (line 2845)
- `_render_xai_log(limit)` (line 2891)
- `_dispatch_slash_command(raw, python_exe)` (line 2930)
- `_render_tree(which)` (line 3010)
- `_render_preview(path)` (line 3029)
- `_handle_cli_flags(argv)` (line 3048)

### Dependencies

- config/settings.py
- src/ai/llm/model_discovery.py
- src/ai/llm/model_manager.py
- src/ai/testing/red_tester.py
- src/core/ai_manager.py
- src/core/database_manager.py
- src/core/database_vault.py
- src/core/hardware_advisor.py
- src/core/model_benchmark_client.py
- src/core/profile_manager.py
- src/ingestion/pdf_harvester/harvester.py
- src/integration/optica_client.py
- src/prisma/dspy_modules.py
- src/prisma/quality_appraisal.py
- src/prisma/quality_swarm.py
- src/search/citation_snowballing.py
- src/search/code_first_search.py
- src/search/fulltext_search.py
- src/search/neural_vector_search.py
- src/services/cognitive_mesh/buffer_sync.py
- src/services/cognitive_mesh/reporter.py
- src/services/cognitive_mesh/router.py
- src/services/cognitive_mesh/scavenger.py
- src/services/cognitive_mesh/self_healing.py
- src/services/cognitive_mesh/xai_ledger.py
- src/utils/ai_strategy_selector.py
- src/utils/bibtex_exporter.py
- src/utils/daemon_autostart.py
- src/utils/desktop_shortcut.py
- src/utils/evaluation_history.py
- src/utils/help_system.py
- src/utils/logger.py
- src/utils/system_diagnostics.py
- src/utils/ui_theme.py

---

