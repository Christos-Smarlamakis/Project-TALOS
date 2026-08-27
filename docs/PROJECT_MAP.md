# PROJECT_MAP.md -- Πλήρης Χάρτης του Project TALOS v5.10.12

> **Σκοπός:** Αυτό το αρχείο είναι η "μνήμη" του project. Διαβάζεται υποχρεωτικά από κάθε νέο chat ώστε ο AI agent να γνωρίζει ακριβώς τι υπάρχει, πού, και πώς συνδέεται -- χωρίς να ξαναδιαβάζει όλα τα αρχεία.
>
> **Κανόνας:** Μετά από ΚΑΘΕ αλλαγή κώδικα (νέα συνάρτηση, τροποποίηση υπογραφής, νέο/διαγραμμένο αρχείο), αυτό το αρχείο ΠΡΕΠΕΙ να ενημερώνεται.
>
> **Τελευταία Ενημέρωση:** 2026-08-27 (v5.10.12 -- Ενίσχυση Αυτόνομου Δαίμονα, 3D Τηλεμετρία Λέιζερ, Διαδραστικός Οπτικοποιητής, System Tray Companion & Rich TrueColor Τηλεμετρία)

---

## 1. Επισκόπηση Αρχιτεκτονικής

```text
USER INTERFACES
  talos.py (Rich TUI -- μενού 15 επιλογών)       src/api/main_api.py (FastAPI -- 23 endpoints E01-E23)
  React 18 + Tailwind CSS + Shadcn UI             templates/dashboard.html (Flask, legacy)
  src/utils/tray_icon.py (system tray)            templates/live_foraging_visualizer.html (Three.js)

        | subprocess / direct import
        v

SRC PACKAGES
  src/core/          (5 αρχεία)  ai_manager, database_manager, hardware, notifier, profile_manager
  src/ai/drl/       (10 αρχεία)  drl_agent, drl_networks, talos_env, train_agent, live_agent_*
  src/ai/optimizers/ (3 αρχεία)  gwo_foraging_hyperparameter_tuner, gwo_live_dashboard, gwo_llm_router_reward_shaper
  src/ai/embeddings/ (2 αρχεία)  embedding_generator, db_embedding_upgrade
  src/ai/llm/        (4 αρχεία)  model_manager, query_translator, research_pivot, model_discovery
  src/ai/testing/    (1 αρχείο)  red_tester
  src/analysis/     (10 αρχεία)  citation_analyzer, author_profiler, recommender, knowledge_path, κ.ά.
  src/ingestion/    (23 αρχεία)  16 source agents + 7 pipelines
  src/integration/   (3 αρχεία)  synapse_client, optica_client, visualizer_bridge
  src/utils/        (14 αρχεία)  db_stats, logger, tray_icon, model_provisioner, daemon_autostart, κ.ά.
  src/api/           (4 αρχεία)  main_api, synapse_routes, red_tester_routes, talos_service_api
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
| `ai_manager.py` | Multi-provider LLM manager (Gemini, DeepSeek, HuggingFace, Ollama) με circuit breakers, λειτουργίες JSON/text/embedding, και απόδοση `last_provider_used` |
| `database_manager.py` | Αποθήκευση SQLite (20+ στήλες), βαθμολόγηση 4 επιπέδων (strategic/operational/tactical/playground), πίνακας embeddings, σημασιολογική αναζήτηση συνημιτόνου, state machine εμπλουτισμού |
| `hardware.py` | Μοναδική πηγή αλήθειας για ανίχνευση GPU και ερωτήματα VRAM; CPU fallback με ομαλή υποβάθμιση |
| `notifier.py` | Ειδοποιήσεις Telegram / Discord / Email για papers υψηλής βαθμολογίας |
| `profile_manager.py` | Εναλλαγή και ανάκτηση profile (απομονωμένο config + DB ανά ερευνητικό θέμα) |

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
| `run_talos.bat` / `run_talos.sh` | Scripts εκκίνησης (TUI, API server, daemon, tests) |
| `src/mcp_server.py` | MCP stdio server με 4 tools (system_status, semantic_search, paper_details, trigger_scrape) |

## 4. Απογραφή Πακέτων & Scripts

| Πακέτο | Αρχεία | Βασικά modules |
|--------|--------|----------------|
| `src/ai/drl/` | 10 | `talos_service.py` (δαίμονας 24/7), `talos_live_agent.py`, `live_agent_orchestrator.py`, `llm_router_subagent.py`, `train_agent.py`, `drl_trainer.py` |
| `src/ai/optimizers/` | 3 | GWO foraging tuner, live dashboard, reward shaper |
| `src/ai/embeddings/` | 2 | `embedding_generator.py`, `db_embedding_upgrade.py` |
| `src/ai/llm/` | 4 | `model_manager.py`, `query_translator.py`, `research_pivot.py`, `model_discovery.py` |
| `src/analysis/` | 10 | `citation_analyzer.py`, `author_profiler.py`, `recommender.py`, `knowledge_path_generator.py`, `trend_analyzer.py`, `graphify_adapter.py`, `generate_baseline_report.py`, κ.ά. |
| `src/ingestion/` | 23 | 16 source agents + `daily_search.py`, `historic_search.py`, `grey_literature_miner.py`, `pdf_downloader.py`, `zotero_connector.py`, `metadata_enricher.py`, `data_enricher.py` |
| `src/utils/` | 14 | `db_stats.py`, `logger.py`, `tray_icon.py`, `model_provisioner.py`, `daemon_autostart.py`, `ui_theme.py`, `api_health_check.py`, κ.ά. |

## 5. Πηγές (16 APIs)

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

## 7. Γράφος Εξαρτήσεων

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
  +-- src/utils/tray_icon.py (προαιρετικό)
  +-- src/integration/visualizer_bridge.py

src/ai/drl/live_agent_orchestrator.py
  +-- src/integration/visualizer_bridge.py

src/ingestion/*.py
  +-- src/core/database_manager.py
  +-- src/integration/synapse_client.py
  +-- src/integration/visualizer_bridge.py
```

## 8. Περιγραφές Modules (επισημασμένες πρόσφατες προσθήκες)

| Module | Διαδρομή | Περιγραφή |
|--------|----------|-----------|
| **System Tray Companion (v5.10.12)** | `src/utils/tray_icon.py` | `launch_tray_icon_async()` -- pystray εικονίδιο (navy/cyan "T") με Άνοιγμα 3D Visualizer, Εμφάνιση/Απόκρυψη Κονσόλας, Τερματισμός Δαίμονα |
| **3D Visualizer (v5.10.12)** | `templates/live_foraging_visualizer.html` | Αστερισμός Three.js με 60 FPS ακτίνες λέιζερ, παλμούς φωτονίων, raycaster, στιγμιότυπο |
| **OPTICA Bridge (v5.10.7)** | `src/integration/optica_client.py` | REST client στο Project OPTICA (θύρα 8002) εκφορτώνοντας βαριά γραφικά |
| **Daemon OS Autostart (v5.10.6)** | `src/utils/daemon_autostart.py` | Συντόμευση Windows Startup + γεννήτρια boot batch |
| **Universal Model Provisioner (v5.10.5)** | `src/utils/model_provisioner.py` | Ανάλυση τοπικού μονοπατιού 3 επιπέδων + self-healing fallback |
| **Enterprise Logger** | `src/utils/logger.py` | `get_logger(name)` -- RichHandler κονσόλα + RotatingFileHandler |
| **MCP Server** | `src/mcp_server.py` | 4-tool stdio server που αναθέτει στο FastAPI |
| **SYNAPSE Emitter** | `src/integration/synapse_client.py` | EventEmitter που στέλνει JSON events στη θύρα 8000 |
| **Visualizer Bridge (v5.10.12)** | `src/integration/visualizer_bridge.py` | `push_visualizer_event()` -- κεντρική γέφυρα HTTP push προς τον 3D Visualizer (θύρα 8001) |

## 9. Βοηθητικά Αρχεία

| Αρχείο/Φάκελος | Ρόλος |
|----------------|-------|
| `docs/` | Μόνιμη τεκμηρίωση (CHANGELOG, ROADMAP, TIMELINE, PROJECT_MAP, SYSTEM_CAPABILITIES, TECH_RADAR) |
| `docs/internal/` | Ιδιόκτητα έγγραφα (API_HANDOVER, UX_UI_BLUEPRINT, IP_PROTECTION) |
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

---

> **Τελευταία Ενημέρωση:** 2026-08-27 (v5.10.12 -- Ενίσχυση Αυτόνομου Δαίμονα, 3D Τηλεμετρία Λέιζερ, Διαδραστικός Οπτικοποιητής, System Tray Companion & Rich TrueColor Τηλεμετρία)
> **Έκδοση Project:** v5.10.12
> **Συνολικά .py modules στο src/:** 80 (core 5 + ai/drl 10 + ai/optimizers 3 + ai/embeddings 2 + ai/llm 4 + ai/testing 1 + analysis 10 + ingestion 23 + integration 3 + utils 14 + api 4 + mcp_server 1)


