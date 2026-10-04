# PROJECT_MAP.md -- Πλήρης Χάρτης του Project TALOS v5.24.0

> **Σκοπός:** Αυτό το αρχείο είναι η "μνήμη" του project. Διαβάζεται υποχρεωτικά από κάθε νέο chat ώστε ο AI agent να γνωρίζει ακριβώς τι υπάρχει, πού, και πώς συνδέεται -- χωρίς να ξαναδιαβάζει όλα τα αρχεία.
>
> **Κανόνας:** Μετά από ΚΑΘΕ αλλαγή κώδικα (νέα συνάρτηση, τροποποίηση υπογραφής, νέο/διαγραμμένο αρχείο), αυτό το αρχείο ΠΡΕΠΕΙ να ενημερώνεται.
>
> **Τελευταία Ενημέρωση:** 2026-10-04 (v5.24.0 -- Επιχειρηματικό Θησαυροφυλάκιο Δεδομένων, Προληπτικός Περιοριστής Ρυθμού Token-Bucket & Κατανεμημένος Συγχρονισμός Προσωρινής Μνήμης JSONL)

---

## 1. Επισκόπηση Αρχιτεκτονικής

```text
USER INTERFACES
  talos.py (Rich TUI -- ιεραρχικό μενού 6 ομάδων)   src/api/main_api.py (FastAPI -- 23 endpoints E01-E23)
  React 18 + Tailwind CSS + Shadcn UI             templates/dashboard.html (Flask, legacy)
  src/utils/tray_icon.py (system tray)            templates/live_foraging_visualizer.html (Three.js)

        | subprocess / direct import
        v

SRC PACKAGES
  src/core/          (8 αρχεία)  ai_manager, database_manager, database_vault, hardware, notifier, profile_manager, provider_registry, hardware_advisor
  src/services/      (12 αρχεία) cognitive_mesh/ (dto, registry, router, rate_limiter, benchmarks, buffer_sync, scavenger, reporter, server, client) -- έτοιμο για εξαγωγή SYNAPSE
  src/ai/drl/       (10 αρχεία)  drl_agent, drl_networks, talos_env, train_agent, live_agent_*
  src/ai/optimizers/ (3 αρχεία)  gwo_foraging_hyperparameter_tuner, gwo_live_dashboard, gwo_llm_router_reward_shaper
  src/ai/embeddings/ (2 αρχεία)  embedding_generator, db_embedding_upgrade
  src/ai/llm/        (4 αρχεία)  model_manager, query_translator, research_pivot, model_discovery
  src/ai/testing/    (1 αρχείο)  red_tester
  src/analysis/     (10 αρχεία)  citation_analyzer, author_profiler, recommender, knowledge_path, κ.ά.
  src/ingestion/    (23 αρχεία)  16 source agents + 7 pipelines
  src/integration/   (3 αρχεία)  synapse_client, optica_client, visualizer_bridge
  src/utils/        (21 αρχεία)  db_stats, logger, tray_icon, help_system, model_provisioner, daemon_autostart, http_client, snapshot_manager, academic_export, evaluation_history, research_setup_wizard, κ.ά.
  src/api/           (4 αρχεία)  main_api, synapse_routes, red_tester_routes, talos_service_api
  src/prisma/        (8 αρχεία + skills/)  dspy_signatures, dspy_modules, swarm_evaluators (Επίπεδο-1), quality_swarm (Επίπεδο-2: SkillCompiler, SmartSectionSlicer, 4 ελεγκτές, KitchenhamQualitySynthesizer), mermaid_generator, scoping_review_synthesizer, quality_appraisal
  src/mcp_server.py              MCP stdio server (4 tools)

        | import
        v

GLOBAL HANDLERS (src/core)
  ai_manager.py (multi-provider LLM)      database_manager.py (SQLite + embeddings)
  hardware.py (GPU / VRAM detection)      notifier.py (ειδοποιήσεις)     profile_manager.py (profiles)

        | HTTP requests
        v

EXTERNAL APIs & SERVICES
  Gemini  DeepSeek  HuggingFace  Ollama  Discord  Zotero  Unpaywall  ORCID
  Semantic Scholar  IEEE  Elsevier  Springer  Crossref  OpenAIRE  OpenReview
  SYNAPSE bus (θύρα 8000)    OPTICA bridge (θύρα 8002)
```

Ροή Δεδομένων:

```text
User > talos.py > run_script() > src/<package>/*.py > src/core/*.py
                                        > src/ingestion/*.py > External APIs
                                                |
                                        data/talos_research.db (SQLite)
                                                |
                                        config.json + .env
```

## 2. Core Modules (src/core)

| Module | Ρόλος |
|--------|-------|
| `ai_manager.py` | Multi-provider LLM manager (Gemini, DeepSeek, HuggingFace, Ollama) με circuit breakers, λειτουργίες JSON/text/embedding, και απόδοση `last_provider_used`; v5.12.2 προσθέτει αυτο-θεραπευόμενο έλεγχο/εκκίνηση Ollama (`probe_local_ollama`), περικοπή παρόχων (`STANDBY_NO_KEY`), έγχυση κλειδιού .env κατά παραγγελία, google.genai GA SDK, αναλυτή μοντέλων σκέψης (`_strip_thinking_tags()` / `_extract_assistant_content()`) και βάση `LOCAL_GPU_MODEL`; v5.18.5 προσθέτει Quota Latching (`exhausted_providers`) για γρήγορη παράκαμψη παρόχων 402/401 |
| `database_manager.py` | Αποθήκευση SQLite (20+ στήλες), βαθμολόγηση 4 επιπέδων (strategic/operational/tactical/playground), πίνακας embeddings, σημασιολογική αναζήτηση συνημιτόνου, state machine εμπλουτισμού |
| `hardware.py` | Μοναδική πηγή αλήθειας για ανίχνευση GPU και ερωτήματα VRAM; CPU fallback με ομαλή υποβάθμιση |
| `provider_registry.py` | Ενθέσιμο μητρώο παρόχων LLM (Αρχή Ανοικτού-Κλειστού): `ProviderDescriptor` + `ProviderRegistry` με `register`/`get`/`list_all`/`list_active` -- τοπικό Ollama + 9 πάροχοι νέφους |
| `hardware_advisor.py` | Σύμβουλος μοντέλων με επίγνωση υλικού: `HardwareModelAdvisor` -- `get_hardware_profile()`, `calculate_vram_budget()` (4-bit), `get_recommendations()`, `scan_sota_models()` |
| `notifier.py` | Ειδοποιήσεις Telegram / Discord / Email για papers υψηλής βαθμολογίας |
| `profile_manager.py` | Εναλλαγή και ανάκτηση profile (απομονωμένο config + DB ανά ερευνητικό θέμα) |
| `hierarchical_evaluator.py` | Κεντρική Μηχανή Αποσύζευξης Αυστηρότητας Δύο Σταδίων (v5.19.0): `HierarchicalEvaluationEngine` με Στάδιο 1 (γρήγορο κόσκινο 8B → S_rel_prelim) + Στάδιο 2 Διπλό Έλεγχο (Βαθμονόμηση Συνάφειας S_rel_calibrated + Kitchenham 2007 S_qual μέσω `PrismaQualityAppraiser`) + χαρτογράφηση Δισδιάστατου Τεταρτημορίου Τεκμηρίων -- μέσω `evaluate_paper()` / `evaluate_batch()` (ThreadPoolExecutor + `Semaphore(2)`) |

### 2.1 DRL Environment (`src/ai/drl/talos_env.py`, v3.2)

| Μέθοδος | Υπογραφή | Περιγραφή |
|---------|----------|-----------|
| `_load_source_list` | `(config=None) -> list` | Διαβάζει τη λίστα πηγών από το config.json |
| `_build_obs` | `() -> np.ndarray` | Κατάσταση 23 διαστάσεων: [ώρα/24, 16 λόγοι πηγών, low/10, err/10, 4 λόγοι παρόχων] |
| `step` | `(action) -> (obs, reward, terminated, truncated, info)` | Εκτελεί action (0..N-1 ερώτημα πηγής, N ύπνος) |
| `get_default_state_space` | `() -> int` | 23 |
| `get_default_action_space` | `() -> int` | 17 (16 πηγές + ύπνος) |

### 2.2 DRL Agent (`src/ai/drl/drl_agent.py`)

`TalosDRLAgent` -- DDDQN agent με pluggable δίκτυα (`drl_networks.py`), epsilon-greedy (eps=0.0 κατά τη live inference), και αυτόματη ανακατασκευή για νέες διαστάσεις.

## 3. Σημεία Εισόδου

| Σημείο | Περιγραφή |
|--------|-----------|
| `talos.py` | Rich TUI (μενού 15 επιλογών σε πέντε οπτικές ομάδες) |
| `src/api/main_api.py` | Headless FastAPI facade (23 endpoints E01-E23, θύρα 8001) με Synapse webhook + Red Tester routers |
| `run_talos.bat` / `run_talos.sh` | Scripts εκκίνησης (TUI, API server, daemon, tests). v5.11.2: το `run_talos.bat` προσθέτει `:AUTO_PREFLIGHT` (οδηγός onboarding 5 βημάτων με σιωπηλό bootstrap Miniconda3), `:DISCOVER_CONDA` (ανίχνευση `condabin\conda.bat` σε πολλαπλές ρίζες + PATH, συμπλήρωση `CONDA_ACTIVATE_PATH`) και σιωπηλή πύλη ταχείας παράκαμψης (εκκίνηση < 1 δευτ. όταν Conda + `talosenv` + `.env` + βασικά πακέτα υπάρχουν ήδη) |
| `src/mcp_server.py` | MCP stdio server με 4 tools (system_status, semantic_search, paper_details, trigger_scrape) |

## 4. Απογραφή Πακέτων & Scripts

| Πακέτο | Αρχεία | Βασικά modules |
|--------|--------|----------------|
| `src/ai/drl/` | 10 | `talos_service.py` (δαίμονας 24/7), `talos_live_agent.py`, `live_agent_orchestrator.py`, `llm_router_subagent.py`, `train_agent.py`, `drl_trainer.py` |
| `src/ai/optimizers/` | 3 | GWO foraging tuner, live dashboard, reward shaper |
| `src/ai/embeddings/` | 2 | `embedding_generator.py`, `db_embedding_upgrade.py` |
| `src/ai/llm/` | 4 | `model_manager.py`, `query_translator.py`, `research_pivot.py`, `model_discovery.py` |
| `src/analysis/` | 10 | `citation_analyzer.py`, `author_profiler.py`, `recommender.py`, `knowledge_path_generator.py`, `trend_analyzer.py`, `graphify_adapter.py`, `generate_baseline_report.py`, κ.ά. |
| `src/ingestion/` | 22 | 16 source agents + `daily_search.py`, `historic_search.py`, `grey_literature_miner.py`, `zotero_connector.py`, `metadata_enricher.py`, `data_enricher.py` |
| `src/utils/` | 18 | `db_stats.py`, `logger.py`, `tray_icon.py`, `help_system.py`, `model_provisioner.py`, `daemon_autostart.py`, `ui_theme.py`, `api_health_check.py`, `http_client.py`, `snapshot_manager.py`, `academic_export.py`, κ.ά. |
| `src/prisma/` | 8 | `dspy_signatures.py` (τυπικές δηλωτικές υπογραφές Pydantic v2), `dspy_modules.py` (PlanEval: Planner/Evaluator/EligibilityJudge/Executor), `swarm_evaluators.py` (Επίπεδο-1 σμήνος ομότιμης αναθεώρησης 3 πρακτόρων + Kappa του Cohen + διαιτητής συναίνεσης), `quality_swarm.py` (Επίπεδο-2 Εγκληματολογικό Σμήνος Ποιότητας: `SkillCompiler`, `SmartSectionSlicer`, `TheoryAuditor`/`OperationalAuditor`/`BenchmarkAuditor`/`OpenScienceAuditor`, `KitchenhamQualitySynthesizer`, `SwarmQualityVerdict`), `mermaid_generator.py`, `scoping_review_synthesizer.py`, `quality_appraisal.py` (ρουμπρίκα Kitchenham 2007 + 2D τεταρτημόρια), συν πακέτο `skills/` με 4 πρότυπα αγνωστικισμού πεδίου |

## 5. Πηγές (18 APIs)

arxiv, ieee, semantic_scholar, springer, openalex, dblp, elsevier, core, crossref, openarchives, pubmed, scigov, osti, plos, openreview, openaire

Τυποποιημένη έξοδος: `{doi, url, title, authors_str, publication_year, abstract, source}`

## 6. Διαμόρφωση & Ροή Δεδομένων

### 6.1 Σχήμα config.json (κλειδιά ανώτατου επιπέδου)

Μοντέλα & δρομολόγηση: `model_for_daily_search`, `pre_screening_model`, `grey_research_model`, `deepseek_model_chat`, `ai_provider_priority`, `gemini_tier`, `provider_limits`, `failure_threshold`

Κατώφλια & όρια: `min_pre_screening_score`, `reevaluation_days_window`, `api_call_limit_flash`, `api_call_limit_pro`, `ai_request_delay`, `days_to_search_daily`, `days_to_search_historic`, `max_results_config`

Ερωτήματα: `arxiv_query`, `ieee_query`, `springer_query`, `openalex_query`, `dblp_query`, `elsevier_query`, `crossref_query`, `openarchives_query`, `pubmed_query`, `osti_query`, `plos_query`, `semantic_scholar_query`, `core_query`, `scigov_query`, `openreview_query`, `openaire_query`

Prompts: `phd_focus_system_prompt`, `pre_screening_prompt`, `trajectory_analyzer_prompt`, `orpheus_references_prompt_instruction`, `orpheus_citations_prompt_instruction`, `chiron_synthesizer_prompt`, `query_translator_prompt`

Daemon: `daemon_target_sources`, `daemon_reporting_mode`, `active_focus_summary`, `mailto`

### 6.2 Κλειδιά .env (example.env)

LLM & runtime: `FAST_EDGE_MODEL`, `FAST_EDGE_BASE_URL`, `HEAVY_REASONING_MODEL`, `OLLAMA_BASE_URL`, `TALOS_CLOUD_PROVIDER`, `TALOS_EXECUTION_MODE`, `TALOS_API_PORT`, `SYNAPSE_BUS_URL`, `OPTICA_API_BASE`

Κλειδιά παρόχων: `GEMINI_API_KEY`, `DEEPSEEK_API_KEY`, `HF_TOKEN`, `NVIDIA_API_KEY`, `GROQ_API_KEY`, `CEREBRAS_API_KEY`, `GITHUB_TOKEN`, `MISTRAL_API_KEY`, `OPENROUTER_API_KEY`

Κλειδιά πηγών: `ZOTERO_API_KEY`, `SEMANTIC_SCHOLAR_API_KEY`, `IEEE_API_KEY`, `SPRINGER_API_KEY`, `ELSEVIER_API_KEY`, `CORE_API_KEY`, `OPENARCHIVES_API_KEY`, `OPENREVIEW_USERNAME/PASSWORD`, `OPENAIRE_TOKEN`, `ORCID_CLIENT_ID/SECRET`

Ειδοποιήσεις: `DISCORD_WEBHOOK_URL`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `SMTP_*`, `MAILTO`

### 6.3 Μεταβλητές Περιβάλλοντος (Runtime)

`TALOS_USE_LOCAL`, `TALOS_MODELS_VERIFIED`, `TALOS_ALLOW_CLOUD_FALLBACK`, `TALOS_ALLOW_LOCAL_FALLBACK`, `TALOS_NETWORK_STRATEGY`, `TALOS_HARDWARE_STRATEGY`, `HF_MODEL_NAME`

### 6.4 Σύστημα Profile

Ο φάκελος `_profiles/<name>/` περιέχει απομονωμένο `config.json` και `talos_research.db` ανά ερευνητικό θέμα. Το `active_profile.txt` παρακολουθεί το ενεργό profile.

**v5.16.1:** Το `src/core/profile_manager.py` είναι η αυστηρή μοναδική πηγή αλήθειας. Η κλάση `ProfileManager` (αγκυρωμένη στον `_profiles/` της ρίζας) εκθέτει `get_profiles_dir()`, `get_active_profile_name()`, `set_active_profile()`, `list_profiles()`, `create_profile()`, `get_active_db_path()` και `get_active_config_path()`. Η `database_manager.get_active_profile_db_path()` και τα βοηθητικά wizard/TUI αναθέτουν σε αυτήν.

## 7. Γράφος Εξαρτήσεων

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
  +-- src/utils/tray_icon.py (προαιρετικό)
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
  +-- src/prisma/quality_swarm.py (lazy, λειτουργία swarm)
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

## 8. Περιγραφές Modules (επισημασμένες πρόσφατες προσθήκες)

| Module | Διαδρομή | Περιγραφή |
|--------|----------|-----------|
| **Universal TUI (v5.10.15)** | `talos.py` | Ενοποιημένο ιεραρχικό μενού 6 ομάδων -- 45/45 εκτελέσιμα modules, αναβίωση νεκρών υπομενού, σουίτα GWO Swarm |
| **Desktop Control Hub (v5.10.13)** | `src/utils/tray_icon.py` | `launch_tray_icon_async()` -- pystray εικονίδιο 7 στοιχείων (3D Visualizer, Φάκελος Αναφορών, Καταγραφή Συστήματος, Swagger, Άμεση Αναζήτηση, Κονσόλα, Τερματισμός) με `_is_api_alive()` / `_ensure_api_server()` αυτοθεραπεία |
| **DatabaseManager Persistence (v5.10.13)** | `src/core/database_manager.py` | Προεπιλογή `db_path=None` -> `get_active_profile_db_path()` (βάση ενεργού προφίλ `_profiles/<active>/talos_research.db`) |
| **Profile Manager SSOT (v5.16.1)** | `src/core/profile_manager.py` | Κανονική κλάση `ProfileManager` (ριζικός `_profiles/`), εκθέτοντας `get_profiles_dir()` / `get_active_profile_name()` / `set_active_profile()` / `list_profiles()` / `create_profile()` / `get_active_db_path()` / `get_active_config_path()`· κανονικός χώρος `uav_mission_planning` |
| **Pluggable Provider Registry (v5.16.2)** | `src/core/provider_registry.py` | `ProviderDescriptor` (dataclass) + `ProviderRegistry` με `register` / `get` / `list_all` / `list_active` -- 10 πάροχοι (Ollama + NVIDIA NIM, DeepSeek, Gemini, Groq, Cerebras, Mistral, Hugging Face, OpenRouter, Anthropic)· δυναμική αξιολόγηση `is_active` |
| **Hardware-Aware Model Advisor (v5.16.2)** | `src/core/hardware_advisor.py` | `HardwareModelAdvisor` -- `get_hardware_profile()` (`{has_cuda, device_name, total_vram_gb, system_ram_gb, is_laptop_cpu}`), `calculate_vram_budget()` (4-bit τμηματικός), `get_recommendations()`, `scan_sota_models()` (ραντάρ SOTA) |
| **Ηθικός Συλλέκτης Ακαδημαϊκών PDF, Έξυπνος Τεμαχισμός Ενοτήτων & Μηχανή SQLite FTS5 (v5.18.0)** | `src/ingestion/pdf_harvester/`, `src/search/fulltext_search.py`, `src/core/database_manager.py` | `resolve_oa_url()` (αλυσιδωτός επιλυτής 13 νόμιμων πηγών Ανοικτής Πρόσβασης)· `AcademicPDFHarvester.harvest_candidates()` (μαγικά byte `%PDF-`, ατομικές εγγραφές, SHA-256, ευγενικός ρυθμός)· `PDFSectionExtractor.extract_sections()` (παράθυρα methodology/experiments/code_availability/limitations)· `FullTextSearchEngine.search_fulltext()` (FTS5 `papers_fts` + BM25 + snippet)· ενσωμάτωση αποθηκευμένων ενοτήτων `SmartSectionSlicer`· CLI `--download-pdfs` / `--fts` / `--open-pdf`· στήλες `local_pdf_path` / `pdf_sha256` / `pdf_status` |
| **Εγκληματολογικό Σμήνος Ποιότητας Δύο Επιπέδων (v5.17.0)** | `src/prisma/quality_swarm.py` | Σμήνος Επιπέδου-2: `SkillCompiler.compile_profile_skills()` (πρότυπα αγνωστικισμού πεδίου -> `_profiles/<name>/skills/*.md`), `SmartSectionSlicer.slice_for_auditor()`, τέσσερις εξειδικευμένοι ελεγκτές (`TheoryAuditor` Q1 / `OperationalAuditor` Q2 / `BenchmarkAuditor` Q3-Q4 / `OpenScienceAuditor` Q5-Q6), `KitchenhamQualitySynthesizer.synthesize()` (`S_qual` + Fleiss `kappa_qual` + τεταρτημόριο + αφήγηση) και `SwarmQualityVerdict` |
| **3D Visualizer (v5.10.12)** | `templates/live_foraging_visualizer.html` | Αστερισμός Three.js με 60 FPS ακτίνες λέιζερ, παλμούς φωτονίων, raycaster, στιγμιότυπο |
| **OPTICA Bridge (v5.10.7)** | `src/integration/optica_client.py` | REST client στο Project OPTICA (θύρα 8002) εκφορτώνοντας βαριά γραφικά |
| **Daemon OS Autostart (v5.10.6)** | `src/utils/daemon_autostart.py` | Συντόμευση Windows Startup + γεννήτρια boot batch |
| **Universal Model Provisioner (v5.10.5)** | `src/utils/model_provisioner.py` | Ανάλυση τοπικού μονοπατιού 3 επιπέδων + self-healing fallback |
| **Enterprise Logger** | `src/utils/logger.py` | `get_logger(name)` -- RichHandler κονσόλα + RotatingFileHandler |
| **MCP Server** | `src/mcp_server.py` | 4-tool stdio server που αναθέτει στο FastAPI |
| **SYNAPSE Emitter** | `src/integration/synapse_client.py` | EventEmitter που στέλνει JSON events στη θύρα 8000 |
| **Visualizer Bridge (v5.10.12)** | `src/integration/visualizer_bridge.py` | `push_visualizer_event()` -- κεντρική γέφυρα HTTP push προς τον 3D Visualizer (θύρα 8001) |

| **Ιστορικό Αξιολόγησης (v5.11.0)** | `src/utils/evaluation_history.py` | `record_evaluation()` / `read_evaluation_history()` / `verdict_for_score()` -- JSONL recorder στο `data/history/daemon_evaluations.jsonl`; προβολή πίνακα Rich `_show_evaluation_history(limit=30)` στο `talos.py` |
| **Κονσόλα Ζωντανής Τηλεμετρίας HUD (v5.11.0)** | `templates/live_foraging_visualizer.html` | ροή glassmorphism κάτω δεξιά (buffer 40 γραμμών, αυτόματη κύλιση, συντομεύσεις `C`/`L`, απόκρυψη κατά το στιγμιότυπο) μέσω `appendConsoleLog()` |
| **Ελαχιστοποίηση σε Δίσκο Win32 (v5.11.0)** | `src/utils/tray_icon.py` | η `enable_close_to_tray()` υποκλέπτει τη WndProc της κονσόλας (WM_CLOSE / SC_CLOSE σε SW_HIDE) ώστε το κλείσιμο να ελαχιστοποιεί σε δίσκο |
| **Οδηγός Ρύθμισης Έρευνας (v5.12.0)** | `src/utils/research_setup_wizard.py` | `_ensure_local_ai_runtime()` (έλεγχος/εκκίνηση θυρών 11434+11435 με οριοθετημένη αναμονή 2s), `_analyze_scope_heuristic()` / `_analyze_scope_with_llm()`, `_generate_queries_llm()` / `_generate_queries_heuristic()`, `_apply_execution_strategy()`, `_write_search_window()`, `_create_sentinel()`, `_render_query_preview()` (πίνακας διαφάνειας ερωτημάτων + επιβεβαίωση, v5.12.1), `_extract_salient_terms()` (ευρετικό φίλτρο stopwords, v5.12.2), `_prompt_custom_days()` / `_step3_search_window()` (παράθυρο βάσει ημερών), `_render_cancelled()` (ακεραιότητα ακύρωσης), `LANGUAGE_AND_SYNTAX_MANDATE` (εντολή αγγλικής πρώτης γλώσσας), 5-tier `EXECUTION_STRATEGIES` + `ai_strategy_selector.py` (διακόπτης στρατηγικής) -- πύλη προφίλ Βήματος 0 (_step0_profile_selection + _list_profiles/_get_active_profile/_set_active_profile/_seed_profile_config/_persist_active_config, v5.12.4) + ενσωμάτωση 4 βημάτων με προτεραιότητα στα Αγγλικά και failsafe ευρετική παράκαμψη |
| **Οδηγός Αναπροσανατολισμού Έρευνας (v5.12.3)** | `src/ai/llm/research_pivot.py` | `_resolve_script_path()` / `run_script()` -- επίλυση κανονικών διαδρομών αγκυρωμένων στο `REPO_ROOT` μέσω `_SCRIPT_MAP` (Γνωσιακός Μεταγλωττιστής Ερωτημάτων, επαναξιολόγηση βάσης, εκπαιδευτής DRL) με εκτέλεση `sys.executable`· αυστηρή επαλήθευση `proc.returncode` (YES μόνο για κωδικό 0, αλλιώς `FAILED (Code X)`)· εξάλειψη κωδικών ονομάτων PYTHIA/CHIRON κατά Κανόνα 9 |
| **Πλέγμα Ταυτόχρονης Κατάποσης (v5.12.4)** | `src/ingestion/daily_search.py` | `_harvest_single_source()` (απομόνωση πηγής ανά νήμα με σύλληψη stdout + πλήρη φύλαξη εξαιρέσεων), `_deduplicate_papers()` (DOI + SHA-1 κατακερματισμός κανονικοποιημένου τίτλου), `_normalize_title()` / `_title_hash()`, `ThreadPoolExecutor(max_workers=min(16, len(enabled_scrapers)))` με `as_completed()` + πίνακα τηλεμετρίας Rich Live (WAITING/HARVESTING/COMPLETED/FAILED) και πίνακα σύνοψης κατάποσης (~35-45s σε ~3-4s) |

| **Μηχανή Ταυτόχρονης Πολυνηματικής Εκτέλεσης Πλήρους Στοίβας (v5.13.0)** | `src/core/ai_manager.py`, `src/ingestion/historic_search.py`, `src/utils/reevaluate_database.py` | `batch_evaluate_papers()` / `_resolve_eval_concurrency()` (8 cloud / 2 τοπικοί εργάτες + φύλακας VRAM `threading.Semaphore(2)`), `historic_search.py` πλέγμα `ThreadPoolExecutor(max_workers=min(16, len(enabled_sources)))` + `_harvest_single_source()` + Rich Live τηλεμετρία, `reevaluate_database.py:_apply_evaluation_batch()` (ομαδικές καταγραφές SQLite WAL) |
| **Αναλυτής Διαγνωστικών Συστήματος (v5.13.1)** | `src/utils/system_diagnostics.py` | `SystemDiagnosticsEngine` -- προκαταρκτικός έλεγχος υγείας 8 σημείων (περιβάλλον Python, ακεραιότητα SQLite, τοπικός χρόνος εκτέλεσης AI, διαθεσιμότητα θυρών, δικαιώματα συστήματος αρχείων, διαπιστευτήρια περιβάλλοντος, κατάσταση δαίμονα, σημεία δικτύου) με `run_diagnostics()` / `render_report()` (πίνακας υγείας Rich + αντιμετώπιση μιας γραμμής); CLI `--diagnostics`/`--doctor`/`-d` και TUI Ομάδα 6 επιλογή 1 |
| **Αγωγός PRISMA-ScR του Stanford DSPy (v5.14.0)** | `src/prisma/dspy_signatures.py`, `dspy_modules.py`, `mermaid_generator.py`, `scoping_review_synthesizer.py` | Δηλωτικές υπογραφές Pydantic v2 (`PrismaPlanSignature`, `PrismaScreeningSignature`, `PrismaEligibilitySignature`, `PrismaSynthesisSignature`) + `extract_json_payload()`· `PrismaPlanner.plan()` (σύνθεση πρωτοκόλλου), `PrismaEvaluator.screen()` (διαλογή με Αλυσίδα Σκέψης), `PrismaEligibilityJudge.assess()`, `PrismaExecutor.run()` (ροή 4 φάσεων + ζωντανοί μετρητές)· `generate_prisma_mermaid()` (PRISMA 2020), `synthesize_scoping_review()` / `synthesize_scoping_review_latex()`· CLI `--prisma` + TUI Ομάδα 3 |
| **Σμήνος Ομότιμης Αναθεώρησης Πολλαπλών Πρακτόρων & Μηχανή Συναίνεσης (v5.14.1)** | `src/prisma/swarm_evaluators.py`, `dspy_modules.py`, `dspy_signatures.py` | `AlgorithmicReviewer` / `EmpiricalReviewer` / `OperationalReviewer` (εξειδικευμένες προσωπικότητες) + `ReviewerVerdict` / `ConsensusVerdict`· `calculate_cohens_kappa()` (Fleiss γενίκευση του Kappa του Cohen) + `cohens_kappa_pairwise()`· `SwarmConsensusArbiter.adjudicate()` (ομόφωνη βραχυκύκλωση + διαιτησία Αλυσίδας Σκέψης)· `PrismaEvaluator.evaluation_mode='swarm'` με VRAM `threading.Semaphore(2)`· CLI `--prisma --swarm` + προτροπή λειτουργίας διαλογής TUI Ομάδας 3 |
| **Εξαγωγέας BibTeX, Κατάποση Αεροδιαστημικής 18 Πηγών & Πάγωμα Χαρακτηριστικών (v5.14.2)** | `src/utils/bibtex_exporter.py`, `src/ingestion/nasa_ntrs_source.py`, `src/ingestion/hal_inria_source.py` | `BibTeXExporter.export_library()` / `render_export_summary()` (κλειδιά `AuthorYearTitleKeyword`, απολύμανση LaTeX, `--export-bib`)· `NasaNtrsSource` (REST NASA NTRS, JSON χωρίς κλειδί)· `HalInriaSource` (REST HAL/Inria, JSON χωρίς κλειδί)· στήλη `papers.prisma_decision` στο `database_manager.create_table()`· CLI `--export-bib` + TUI Ομάδα 5 επιλογή 12 |
| **Καθολικός Κόμβος Επιστημονικής Αναζήτησης & Μηχανή Ανακάλυψης Νευρικών Γράφων (v5.15.0)** | `src/ingestion/sources/`, `src/search/citation_snowballing.py`, `src/search/neural_vector_search.py`, `src/search/code_first_search.py` | Ενιαίο `SOURCE_REGISTRY` (18 προσαρμογείς)· `CitationSnowballEngine` (διάσχιση γράφου προς τα πίσω/εμπρός, φίλτρο PRISMA, γράφος γενεαλογίας)· `NeuralVectorSearchEngine` (τοπικό `nomic-embed-text`, ομοιότητα συνημιτόνου)· `CodeFirstSearchEngine` (σήματα αναπαραγωγιμότητας)· CLI `--snowball`/`--vector-search`/`--code-search` + TUI Ομάδα 2 |
| **Μόνιμη Διανυσματική Κρυφή Μνήμη & Επιταχυνόμενη Μηχανή Νευρικών Ενσωματώσεων (v5.15.1)** | `src/core/database_manager.py`, `src/search/neural_vector_search.py` | Αδρανής πίνακας `paper_embeddings` + `get_cached_embeddings()` / `save_embeddings_batch()`· `NeuralVectorSearchEngine._index_uncached()` (ζωντανό `rich.progress.Progress` + `ThreadPoolExecutor` + αποθήκευση παρτίδων 64), `_matrix_rank()` (διανυσματική ομοιότητα συνημιτόνου μητρώου NumPy, <50ms), `render_results()` (στυλιζαρισμένο Rich Table) |
| **Εναρμόνιση UX & Αναφορών Καθολικού Κόμβου Αναζήτησης (v5.15.2)** | `src/search/code_first_search.py`, `src/search/citation_snowballing.py`, `talos.py` | `CodeFirstSearchEngine.render_results()` / `export_search_report()` (`data/reports/code_search/`)· `CitationSnowballEngine.render_genealogy()` / `export_snowball_report()` (`data/reports/snowball/`)· κατάργηση ακατέργαστων JSON dumps (`_render_search_result` αφαιρέθηκε) |
| **Διακόπτης Κυκλώματος Συνόδου, Ισχυρή Εξαγωγή Συγγραφέων & Ενίσχυση Κύκλου Ζωής Δαίμονα (v5.15.3)** | `src/core/ai_manager.py`, `src/utils/evaluation_history.py`, `src/ai/drl/talos_service.py`, `src/ai/drl/live_agent_orchestrator.py`, `src/integration/synapse_client.py` | `AIManager.fast_tier_offline` (κλείδωμα CPU Edge 11435 εκτός σύνδεσης μετά την πρώτη αποτυχία, μηδενικές επανελεγχές/καταγραφές)· `normalize_authors(paper)` (επίλυση `authors_str`/`authors`/`author`)· καθαρό `[EVAL]` τηλεμετρία δαίμονα· σιωπηλή αποθήκευση SYNAPSE (`synapse_available` + JSONL) |
| **Επέκταση Χώρου Δράσεων DRL σε 18 Πηγές & Μετανάστευση Checkpoint Net2Net (v5.15.4)** | `src/ai/drl/talos_env.py`, `scripts/migrate_d3qn_checkpoint.py`, `config.json`, `config.template.json`, `_profiles/default_drones/config.json` | `ALL_KNOWN_SOURCES` 16 -> 18 (προσθήκη `nasa_ntrs`, `hal_inria`)· χώρος δράσεων `Discrete(17) -> Discrete(19)`, καταστάσεις 23 -> 25 διαστάσεις· χειρουργική Net2Net (`migrate_d3qn_checkpoint.py`) διευρύνει την κεφαλή πλεονεκτήματος DuelingLSTM (15 -> 19) + είσοδο LSTM (21 -> 25) διατηρώντας όλα τα εκπαιδευμένα βάρη· συγχρονισμός προφίλ/δαίμονα 18 πηγών· κλείδωμα κανονικοποίησης συγγραφέων Scopus `$`/`@name`/`@surname` |
| **Σύστημα Βοήθειας Διπλής Επιφάνειας & Κανόνας Επιστημονικών Θεμελίων (v5.15.5)** | `src/utils/help_system.py`, `templates/help_manual.html`, `src/api/main_api.py`, `README.md` | `render_help_manual()` εγχειρίδιο Rich 4 πινάκων (`--help` + TUI Επιλογή 7)· `GET /help` + `GET /manual` (ανακατεύθυνση 307) εξυπηρετούν το zero-CDN `help_manual.html` (ζωντανή αναζήτηση, αντιγραφή με κλικ, εναλλαγή σκοτεινής/εκτυπώσιμης λειτουργίας)· Ενότητα 5 IEEE αναφορών [1]-[10] στο README (EN + GR) |
| **Μηχανή Αξιολόγησης Ποιότητας PRISMA & Διαξονικής Επιστημονικής Αυστηρότητας (v5.16.0)** | `src/prisma/quality_appraisal.py`, `src/core/database_manager.py`, `src/utils/bibtex_exporter.py` | `KitchenhamRubric` / `QualityAppraisalResult` / `PrismaQualityAppraiser`· `map_evidence_quadrant()` (2D τεταρτημόρια, τ_rel=7.0 / τ_qual=7.5)· `appraise_paper()` / `appraise_candidates_batch(force_reappraise)` (ThreadPoolExecutor + `Semaphore(2)`)· `update_paper_quality()` (στήλες `quality_score`/`quality_rubric_json`/`evidence_quadrant`)· `export_library(min_quality, quadrant)` (διπλό φίλτρο BibTeX + πεδίο `note`)· CLI `--appraise-quality [--force]` + TUI Ομάδα 3 Επιλογή 15 (ερώτηση επαναξιολόγησης v5.17.1) |
| **Ενθέσιμο Μητρώο Παρόχων & Σύμβουλος Μοντέλων με Επίγνωση Υλικού (v5.16.2)** | `src/core/provider_registry.py`, `src/core/hardware_advisor.py`, `src/core/ai_manager.py`, `talos.py`, `src/utils/help_system.py` | `ProviderRegistry` (Αρχή Ανοικτού-Κλειστού, 10 πάροχοι)· `HardwareModelAdvisor` (προφίλ υλικού, τμηματικός προϋπολογισμός VRAM 4-bit, στοίβα ανά ρόλο, ραντάρ SOTA)· `AIManager.list_active_providers()` / `get_provider_descriptor()` (μηδενική παλινδρόμηση)· CLI `--hardware-advisor` / `--recommend-models` + TUI Επιλογή 8 |

| **Αποσύζευξη Αυστηρότητας Δύο Σταδίων & Γνωστικός Αντιστοιχιστής Ρόλων SOTA (v5.19.0)** | `src/core/hierarchical_evaluator.py`, `src/core/hardware_advisor.py`, `src/ingestion/historic_search.py`, `talos.py` | `HierarchicalEvaluationEngine` Διπλός Έλεγχος Σταδίου 2 (Βαθμονόμηση Συνάφειας S_rel_calibrated + Kitchenham S_qual μέσω `PrismaQualityAppraiser`) + Δισδιάστατο Τεταρτημόριο Τεκμηρίων· `get_role_based_matrix()` / `render_role_matrix()` / `apply_recommended_models()` (4-ρόλο SOTA)· ενοποίηση `historic_search` στη μηχανή· CLI `--apply-models` |
| **Ιεραρχική Μηχανή Αξιολόγησης, Γνωστικός Δρομολογητής LLM & Καθαρός Κύκλος Ζωής Εισαγωγής (v5.18.5)** | `src/core/hierarchical_evaluator.py`, `src/core/ai_manager.py`, `src/ingestion/daily_search.py`, `src/ai/drl/live_agent_orchestrator.py`, `src/ingestion/sources/scigov_source.py`, `src/ingestion/sources/dblp_source.py` | `HierarchicalEvaluationEngine.evaluate_paper()` / `evaluate_batch()` (γρήγορο κόσκινο 8B → πύλη S_rel >= 6.0 → βαριά λογική 14B/cloud + Kitchenham S_qual)· `AIManager.exhausted_providers` + `_latch_provider_exhausted()` (παράκαμψη 402/401 με μηδενικές απόπειρες)· `SetConsoleTitleW` δυναμικός τίτλος κονσόλας (χωρίς emoji)· `ScienceGovSource` (απομόνωση DNS + disabled-by-default)· `DBLPSource._sanitize_dblp_query()` (καθαρισμός Boolean + φύλαξη JSONDecodeError) |
| **Αυτοθεραπευόμενη Πύλη Εισαγωγής & Επιλογέας Προφίλ Autostart (v5.18.4)** | `src/ingestion/resilient_gateway.py`, `src/ingestion/daily_search.py`, `src/ingestion/historic_search.py`, `src/utils/daemon_autostart.py` | `ResilientIngestionGateway` (fast-fail 401/403/Quota, αντικατοπτρισμός OpenAlex IEEE/Elsevier/Springer, `source=<source_key>`)· `main()` επιλογέας προφίλ Questionary (Βήμα 1) + εμμονή `daemon_profile` στο `_profiles/<profile>/config.json` |
| **Χειρουργική Net2Net Διπλού Checkpoint & Διάθεση Προφίλ Δαίμονα (v5.18.3)** | `scripts/migrate_d3qn_checkpoint.py`, `src/utils/daemon_autostart.py`, `src/ai/drl/talos_service.py` | Γνήσια χειρουργική τανυστών εισόδου Net2Net ΚΑΙ ΣΤΑ ΔΥΟ checkpoints (`models/` + `src/ai/models/`, `lstm1.weight_ih_l0` [512, 25], `A.weight` [19, 32], εξάλειψη `RuntimeError: Expected 23, got 25`)· `select_daemon_profile()` (Questionary) + `--profile <name>` με δυναμικό banner συγχρονισμένο στο `uav_mission_planning` |
| **Επισκευή Checkpoint Net2Net, Close-to-Tray Win32, Συντόμευση Επιφάνειας Εργασίας & Επιλογέας Προφίλ Autostart (v5.18.2)** | `scripts/migrate_d3qn_checkpoint.py`, `src/utils/tray_icon.py`, `src/utils/desktop_shortcut.py`, `src/utils/daemon_autostart.py`, `src/ai/drl/talos_service.py`, `talos.py` | Επιβεβαίωση/σφράγιση idempotent της μετανάστευσης Net2Net (18 πηγές / 25 διαστάσεις, forward pass χωρίς σφάλματα)· `enable_close_to_tray()` (WNDPROC, SW_HIDE + ειδοποίηση `[TRAY]`)· `create_desktop_shortcut()` (`TALOS Research Hub.lnk` μέσω COM `WScript.Shell`)· `select_daemon_profile()` + `--profile <name>` |

## 9. Βοηθητικά Αρχεία

| Αρχείο/Φάκελος | Ρόλος |
|----------------|-------|
| `docs/` | Μόνιμη τεκμηρίωση (CHANGELOG, ROADMAP, TIMELINE, PROJECT_MAP, SYSTEM_CAPABILITIES, ENVIRONMENT_SETUP_GUIDE EN/GR) |
| `docs/ENVIRONMENT_SETUP_GUIDE.md` | Κανονικός αγγλικός οδηγός ρύθμισης περιβάλλοντος & διαπιστευτηρίων (διαχωρισμός `.env` / `settings.py`, τοπικό Ollama, cloud mesh, ακαδημαϊκά API, πίνακας δικτύου/θυρών) |
| `docs/ENVIRONMENT_SETUP_GUIDE_GR.md` | Κανονικός ελληνικός οδηγός ρύθμισης περιβάλλοντος & διαπιστευτηρίων (αμιγής ελληνική γραφή) |
| `docs/internal/` | Ιδιόκτητα / απόρρητα έγγραφα (API_HANDOVER, UX_UI_BLUEPRINT, IP_PROTECTION, TECH_RADAR EN/GR -- απόρρητος στρατηγικός χάρτης) |
| `tools/` | Dev & utility scripts |
| `Dockerfile`, `docker-compose.yml` | Containerization |
| `README.md`, `CITATION.cff`, `LICENSE` | Metadata |
| `data/reports/` | Όλες οι παραγόμενες αναφορές (ενοποίηση v5.9.9) |

## 10. Γνωστά Προβλήματα & Συμβάσεις

1. Τα ελληνικά σχόλια σπάνε το text matching του editor
2. Τιμές `.env` χωρίς quotes -- το load_dotenv δεν αφαιρεί quotes
3. Το `daily_search.py` και το `historic_search.py` πρέπει να μένουν συγχρονισμένα για dedup
4. Το 4-layer framework (strategic/operational/tactical/playground) είναι INVARIANT
5. Το `recommender.py` διαβάζει SQLite απευθείας, όχι μέσω DatabaseManager
6. Circuit breaker στα 5+ failures
7. Το μονοπάτι DB επιλύεται σε `data/talos_research.db` (όχι ghost DBs στο `src/`)
8. Τα API endpoints δεν πρέπει ποτέ να ενεργοποιούν διαδραστικό `questionary.confirm()`
9. Το TALOS FastAPI τρέχει στη θύρα 8001 (Synapse 8000, OPTICA 8002)
10. Ο δαίμονας ξεκινά σε νέο παράθυρο κονσόλας (CREATE_NEW_CONSOLE) στα Windows
11. Το `src/utils/tray_icon.py` χρησιμοποιεί lazy imports ώστε να υποβαθμίζεται ομαλά χωρίς pystray
12. Η γεννήτρια SSE στη `visualizer_sse_stream` δεν πρέπει ποτέ να καλεί blocking `queue.Queue.get()` απευθείας στον event loop -- πάντα μέσω `asyncio.to_thread` (pre-demo hardening patch)
13. Τα `get_visualizer_state` / `get_visualizer_demo_data` χρησιμοποιούν το cached singleton `_get_db()` -- μετά από αλλαγή ενεργού προφίλ απαιτείται επανεκκίνηση του uvicorn ώστε να επαναδεσμευτεί το singleton
14. Τα background tasks (`_run_scrape_background`, `_run_evaluate_background`) θέτουν `TALOS_HEADLESS=1` στην είσοδο -- κάθε νέο background task που καλεί AIManager πρέπει να κάνει το ίδιο, αλλιώς κίνδυνος διαδραστικού prompt σε νήμα χωρίς κονσόλα
15. Το monkey-patch του `sys.exit` στη `_run_scrape_background` σειριαλοποιείται από το καθολικό `_scrape_task_lock` -- ποτέ patching καθολικών symbols διεργασίας χωρίς αυτό το lock
16. Η `DatabaseManager.semantic_search` φράσσει το `top_k` στο πλήθος των φορτωμένων embeddings (`min(top_k, len(self._embedding_ids))`) -- το φράγμα πρέπει να διατηρείται σε κάθε τροποποίηση
17. Ο V2 client του OpenReview απορρίπτει το `get_notes(term=...)` με `TypeError` -- όλα τα queries σημειώσεων δρομολογούνται αποκλειστικά μέσω `OpenReviewSource._query_notes()` (search_notes -> content query -> TypeError fallback)
18. Το `AIManager.fast_tier_offline` (μάνδαλο επιπέδου συνόδου, v5.15.3) παρακάμπτει γνωστό offline Fast Edge endpoint (11435) για το υπόλοιπο της ζωής της διεργασίας με μηδενικές καταγραφές -- το παλαιό `_fast_edge_offline_memo` διατηρείται ως συνώνυμο· επαναφέρεται μόνο με νέο instance του AIManager, ποτέ χειροκίνητα εντός βρόχου
19. Η εκκίνηση του FastAPI γίνεται μέσω `lifespan` context manager στο `main_api.py` -- ποτέ επαναφορά `@app.on_event` handlers (απαρχαιωμένα, παράγουν DeprecationWarning)
20. Το `SynapseClient.synapse_available` (v5.15.3) μανδαλώνει τον δίαυλο SYNAPSE (θύρα 8000) εκτός σύνδεσης μετά την πρώτη άρνηση σύνδεσης -- τα γεγονότα αποθηκεύονται σιωπηλά σε μνήμη + `data/synapse_buffer.jsonl`· η `normalize_authors()` αποτρέπει ψευδή "Unknown Authors"

---

> **Τελευταία Ενημέρωση:** 2026-10-04 (v5.24.0 -- Επιχειρηματικό Θησαυροφυλάκιο Δεδομένων, Προληπτικός Περιοριστής Ρυθμού Token-Bucket & Κατανεμημένος Συγχρονισμός Προσωρινής Μνήμης JSONL)
> **Έκδοση Project:** v5.24.0
> **Συνολικά .py modules στο src/:** 115 (core 8 + services 12 + ai/drl 10 + ai/optimizers 3 + ai/embeddings 2 + ai/llm 4 + ai/testing 1 + analysis 10 + ingestion 6 + ingestion/sources 18 + search 3 + integration 3 + utils 23 + api 4 + prisma 8 + mcp_server 1)


