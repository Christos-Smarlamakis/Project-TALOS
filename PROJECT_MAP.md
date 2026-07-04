# PROJECT_MAP.md — Πλήρης Χάρτης του Project TALOS v5.3.0

> **Σκοπός:** Αυτό το αρχείο είναι η "μνήμη" του project. Διαβάζεται υποχρεωτικά από κάθε νέο chat ώστε ο AI agent να γνωρίζει ακριβώς τι υπάρχει, πού, και πώς συνδέεται — χωρίς να ξαναδιαβάζει όλα τα αρχεία.
>
> **Κανόνας:** Μετά από ΚΑΘΕ αλλαγή κώδικα (νέα συνάρτηση, τροποποίηση υπογραφής, νέο/διαγραμμένο αρχείο), αυτό το αρχείο ΠΡΕΠΕΙ να ενημερώνεται.

---

## 1. Επισκόπηση Αρχιτεκτονικής

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER INTERFACES                          │
│  talos.py (CLI menu)          app.py (Streamlit Web GUI)        │
│  _gui_runner.py (wrapper)     templates/dashboard.html (Flask)  │
└──────────────────────────┬──────────────────────────────────────┘
                           │ subprocess / direct import
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                    SCRIPTS (21 αρχεία)                           │
│  daily_search.py          historic_search.py                    │
│  knowledge_path_generator.py (CHIRON)                           │
│  citation_analyzer.py (ORPHEUS)    recommender.py               │
│  grey_literature_miner.py          query_translator.py (PYTHIA) │
│  author_profiler.py      author_trajectory_analyzer.py          │
│  db_stats.py    data_enricher.py    embedding_generator.py      │
│  metadata_enricher.py (APOLLO)      model_manager.py            │
│  pdf_downloader.py      profile_manager.py                      │
│  recalculate_scores.py  reevaluate_database.py                  │
│  trend_analyzer.py      zotero_connector.py                     │
│  interactive_dashboard.py          api_health_check.py          │
│  migrate_database_schema.py                                     │
│  generate_docs.py                                                │
└──────────────────────────┬──────────────────────────────────────┘
                           │ import
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                    CORE MODULES (3 αρχεία)                       │
│  ai_manager.py          database_manager.py        hardware.py  │
│  (Multi-provider LLM)   (SQLite + Embeddings)     (GPU detect)  │
└──────────────────────────┬──────────────────────────────────────┘
                           │ import
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                    SOURCES (14 APIs)                             │
│  arxiv  elsevier  semantic_scholar  ieee  springer  openalex    │
│  dblp  core  crossref  openarchives  pubmed  scigov  osti  plos │
│                                                                  │
│  Standardized output: {doi, url, title, authors_str,            │
│                        publication_year, abstract, source}       │
└──────────────────────────┬──────────────────────────────────────┘
                           │ HTTP requests
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                    EXTERNAL APIs & SERVICES                      │
│  Gemini API  DeepSeek API  HuggingFace  Ollama  Discord  Zotero │
│  Unpaywall  ORCID  Semantic Scholar  IEEE  Elsevier  Springer   │
└─────────────────────────────────────────────────────────────────┘

Data Flow:
  User → talos.py → run_script() → scripts/*.py → core/*.py → sources/*.py → External APIs
                                                      ↕
                                              talos_research.db (SQLite)
                                                      ↕
                                              config.json + .env
```

---

## 2. Core Modules

### 2.0 `core/talos_env.py` — Gymnasium Environment (v2.0, Dynamic N-Source)

**Ρόλος:** RL environment για API source selection. **V2.0:** υποστηρίζει ΔΥΝΑΜΙΚΟ αριθμό πηγών (όχι μόνο 3).

| Μέθοδος | Υπογραφή | Περιγραφή |
|---------|----------|-----------|
| `_load_source_list` | `(config=None) -> list` | Διαβάζει τη λίστα πηγών από config.json (source_names ή auto-detect από _query keys). |
| `_try_load_config` | `() -> dict or None` | Φορτώνει config.json από το project root. |
| `_load_source_limits` | `(source_names, config=None) -> np.ndarray` | Διαβάζει per-source API limits από config. |
| `__init__` | `(self, source_names=None, source_limits=None, config=None)` | Dynamic init με N πηγές. Το source_names auto-detected αν είναι None. |
| `reset` | `(seed=None, options=None) -> (obs, info)` | Μηδενίζει όλους τους counters. |
| `step` | `(action) -> (obs, reward, terminated, truncated, info)` | Εκτελεί action. Actions 0..N-1 = query πηγή, N = sleep. |
| `_build_obs` | `() -> np.ndarray` | Κατασκευάζει δυναμικό observation vector: [hour, usage_ratios..., low_streak, error_streak]. |
| `get_default_state_space` | `() -> int` | Επιστρέφει default STATE_SPACE (1 + N + 2). |
| `get_default_action_space` | `() -> int` | Επιστρέφει default ACTION_SPACE (N + 1 sleep). |

**Key attributes:** `source_names` (list), `num_sources` (int), `source_limits` (np.ndarray), `source_calls` (np.ndarray), `SLEEP_ACTION` (int).

**Backward compat:** Properties `arxiv_limit`, `openalex_limit`, `s2_limit` επιστρέφουν limits για τα αντίστοιχα sources αν υπάρχουν.

### 2.1 `core/ai_manager.py` — Κλάση `AIManager` (v3.5, 380 γραμμές)

**Ρόλος:** Multi-provider LLM interface με circuit breaker pattern. Διαχειρίζεται 4 providers: Gemini (πρωτεύων cloud), DeepSeek (fallback), HuggingFace (δωρεάν cloud), Local/Ollama (offline).

| Μέθοδος | Υπογραφή | Περιγραφή |
|---------|----------|-----------|
| `__init__` | `(self, config: Dict[str, Any])` | Αρχικοποιεί όλους τους providers από config + .env. Θέτει provider_priority, FAILURE_THRESHOLD. |
| `_clean_json_string` | `(self, text: str) -> str` | Εξάγει καθαρό JSON από LLM response (αφαιρεί markdown fences, εξωτερικό κείμενο). |
| `evaluate_paper_json` | `(self, paper_content: str, model_type: str = 'pro', system_prompt_override: str = None) -> Union[Dict, None]` | Αξιολογεί paper με AI, επιστρέφει structured JSON. Το `system_prompt_override` χρησιμοποιείται από την PYTHIA. |
| `analyze_generic_text` | `(self, full_prompt: str) -> str` | Αναλύει arbitrary text με το Pro model, επιστρέφει text response. |
| `generate_embeddings` | `(self, texts, task_type=None)` | Παράγει embeddings (πρώτα local Ollama, μετά Gemini fallback). |
| `_execute_request` | `(self, prompt: str, model_type: str, response_format: str = 'text') -> Union[Dict, str, None]` | Εκτελεί request σε όλους τους providers με σειρά προτεραιότητας, με circuit breaker. |
| `_execute_gemini_request` | `(self, prompt: str, model_type: str, response_format: str)` | Στέλνει request στο Gemini API (json ή text mode). |
| `_execute_deepseek_request` | `(self, prompt: str, response_format: str)` | Στέλνει request στο DeepSeek API (OpenAI-compatible). |
| `_execute_openai_compatible` | `(self, prompt: str, response_format: str, provider_name='local')` | Στέλνει request σε Local/HuggingFace (OpenAI-compatible API). |
| `_handle_failure` | `(self, provider_name: str)` | Αυξάνει failure counter, ανοίγει circuit αν ξεπεραστεί το threshold. |
| `_ensure_local_model` | `(self)` | Ελέγχει/κατεβάζει local Ollama models (gemma3:12b, nomic-embed-text). |

**Providers:**
- `gemini`: flash_model (pre-screening), pro_model (deep analysis), embedding_model (text-embedding-004)
- `deepseek`: OpenAI client στο `https://api.deepseek.com/v1`, model: deepseek-chat
- `huggingface`: OpenAI client στο `https://router.huggingface.co/v1`, δωρεάν inference
- `local`: OpenAI client στο `http://localhost:11434/v1`, model: gemma3:12b, embedding: nomic-embed-text

**Circuit Breaker:** 3+ συνεχόμενα failures → circuit_open = True → ο provider παρακάμπτεται για το υπόλοιπο session.

**System Prompt Override:** Χρησιμοποιείται από `query_translator.py` (PYTHIA) για να αλλάξει το AI από "PhD Advisor" σε "Research Architect".

---

### 2.2 `core/drl_agent.py` — DRL Agent (v2.0, Dynamic N-Source)

**Ρόλος:** Double Dueling DQN agent. **V2.0:** δυναμικό state_dim/action_dim από το environment.

**Κλάση `DuelingLSTM`:**
| Μέθοδος | Υπογραφή | Περιγραφή |
|---------|----------|-----------|
| `__init__` | `(input_dim=STATE_SPACE, output_dim=ACTION_SPACE)` | 3-layer LSTM (128→64→32) με dueling heads. Δυναμικά input/output dims. |
| `forward` | `(state) -> Q-values` | Forward pass με CuDNN flatten_parameters(). |

**Κλάση `TalosDRLAgent`:**
| Μέθοδος | Υπογραφή | Περιγραφή |
|---------|----------|-----------|
| `__init__` | `(state_dim=None, action_dim=None)` | Δυναμική αρχικοποίηση. Αν None, auto-detect από config. |
| `act` | `(state, eps=0.0) -> int` | ε-greedy action selection. |
| `learn` | `()` | DDQN learning step (experience replay + target network). |
| `save` | `(path)` | Αποθηκεύει weights + metadata (state_dim, action_dim, source_names). |
| `load` | `(path)` | Φορτώνει weights + metadata. Αναδημιουργεί networks αν δεν ταιριάζουν τα dimensions. |

**Module-level:** `STATE_SPACE`, `ACTION_SPACE` υπολογίζονται δυναμικά από `talos_env.get_default_*()`.

### 2.3 `core/notifier.py` — Κλάση `TalosNotifier` (v1.0, ~202 γραμμές)

**Ρόλος:** Multi-channel notification system για τον TALOS daemon.

| Μέθοδος | Υπογραφή | Περιγραφή |
|---------|----------|-----------|
| `__init__` | `(self)` | Διαβάζει Telegram/Discord/Email ρυθμίσεις από environment variables. |
| `telegram_send` | `(self, message: str)` | Στέλνει μήνυμα μέσω Telegram Bot API (HTML parse mode, truncation στα 4000 chars). |
| `discord_send` | `(self, message: str)` | Στέλνει μήνυμα μέσω Discord Webhook (truncation στα 1950 chars). |
| `email_send` | `(self, subject: str, body: str)` | Στέλνει email μέσω SMTP (STARTTLS, HTML body). |

**Imports:** `smtplib`, `requests`, `email.mime.text.MIMEText`, `email.mime.multipart.MIMEMultipart`

**Channel config (.env keys):** `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `DISCORD_WEBHOOK_URL`, `SMTP_SERVER`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `SMTP_FROM`, `SMTP_TO`

### 2.4 `core/database_manager.py` — Κλάση `DatabaseManager` (v4.8.5, 569 γραμμές)

**Ρόλος:** SQLite database layer με embeddings, semantic search, και profile-aware initialization.

| Μέθοδος | Υπογραφή | Περιγραφή |
|---------|----------|-----------|
| `__init__` | `(self, db_path=None, db_name="talos_research.db")` | Profile-aware init. Αν δεν δοθεί db_path, ψάχνει στο project root. |
| `_table_exists` | `(self, table_name: str) -> bool` | Ελέγχει αν υπάρχει table. |
| `_load_embeddings_into_memory` | `(self)` | Φορτώνει όλα τα embeddings (pickled numpy arrays) στη μνήμη για γρήγορο search. |
| `execute_query` | `(self, query, params=(), commit=False, fetch_one=False, fetch_all=False)` | Εκτελεί SQL query με παραμέτρους. |
| `execute_many` | `(self, query, params_list, commit=False)` | Batch εκτέλεση με executemany. |
| `create_table` | `(self)` | Δημιουργεί το `papers` table με 20+ στήλες (v4.8.0 schema). Κάνει auto-migration για παλιές βάσεις. |
| `paper_exists_by_doi` | `(self, doi: str) -> bool` | Dedup έλεγχος μέσω DOI. |
| `paper_exists_by_url` | `(self, url: str) -> bool` | Dedup έλεγχος μέσω URL. |
| `get_paper_id_by_doi` | `(self, doi: str) -> Union[int, None]` | Επιστρέφει paper ID από DOI. |
| `get_paper_id_by_url` | `(self, url: str) -> Union[int, None]` | Επιστρέφει paper ID από URL. |
| `_calculate_overall_score` | `(self, scores: Dict) -> float` | Υπολογίζει weighted score: Strategic 30% + Operational 30% + Tactical 30% + Playground 10%. |
| `add_paper` | `(self, paper_data, evaluation_data, in_zotero=0) -> Union[int, None]` | Εισάγει νέο paper με όλα τα evaluation data. |
| `update_paper_evaluation` | `(self, paper_id: int, evaluation_data: Dict)` | Ενημερώνει evaluation για υπάρχον paper. |
| `get_papers_not_recently_evaluated` | `(self, days_window: int, limit: int) -> List[Tuple]` | Επιστρέφει papers που χρειάζονται re-evaluation. |
| `get_all_papers_for_dashboard` | `(self) -> List[Dict]` | Όλα τα papers για το dashboard. |
| `get_single_paper_details` | `(self, paper_id: int) -> Union[Dict, None]` | Λεπτομέρειες ενός paper. |
| `update_zotero_status_by_id` | `(self, paper_id: int, status: int)` | Ενημερώνει το in_zotero flag. |
| `get_papers_without_embedding` | `(self) -> List[Dict]` | Papers που δεν έχουν embeddings ακόμα. |
| `update_embeddings_batch` | `(self, updates: List[Tuple])` | Batch update embeddings (pickled numpy arrays). |
| `get_all_embeddings` | `(self) -> List[Dict]` | Όλα τα embeddings από τη βάση. |
| `get_papers_by_ids` | `(self, ids: list) -> List[Dict]` | Papers για συγκεκριμένα IDs. |
| `get_recent_core_papers` | `(self, limit=10, min_score=7.0) -> List[Dict]` | Top papers με υψηλό score για επιλογή σε ORPHEUS. |
| `semantic_search` | `(self, query_vector: np.ndarray, top_k=100) -> List[int]` | Cosine similarity search σε όλα τα embeddings. |
| `get_all_papers_as_dataframe` | `(self) -> pd.DataFrame` | Όλα τα papers ως pandas DataFrame. |
| `get_database_statistics` | `(self) -> Dict` | Στατιστικά: total_papers, elite_papers, avg_score, by_source, κ.λπ. |
| `get_papers_for_enrichment` | `(self)` | Papers που χρειάζονται enrichment (Unpaywall/IDs). |
| `update_papers_enrichment_batch` | `(self, update_list)` | Batch update enrichment δεδομένων. |

**Database Schema (papers table):**
- `id` (PK), `doi` (UNIQUE), `url`, `title`, `authors`, `publication_year`, `abstract`, `source`
- 4-layer scores: `strategic_score`, `operational_score`, `tactical_score`, `playground_score` (INT 0-10)
- `overall_score` (REAL), `evaluation_reasoning`, `evaluation_contribution`, `evaluation_utilization`
- `suggested_tags`, `suggested_folder`, `suggested_discord_channel`
- `in_zotero` (INT 0/1), `embedding` (BLOB - pickled numpy array)
- `processed_at`, `last_evaluated_at`
- Enrichment: `oa_pdf_url`, `openalex_id`, `pmid`, `pmcid`, `oa_status`, `journal_issn`, `publisher`
- `enrichment_status` (0=Pending, 1=Enriched, 2=Failed)

---

### 2.5 `core/hardware.py` (v4.8.5, 429 γραμμές)

**Ρόλος:** Ανίχνευση GPU VRAM, προτάσεις μοντέλων Ollama, εκτίμηση μεγεθών quantization.

| Συνάρτηση | Υπογραφή | Περιγραφή |
|-----------|----------|-----------|
| `detect_vram_gb` | `() -> float or None` | Ανιχνεύει VRAM μέσω nvidia-smi. |
| `recommend_model` | `(preferred="gemma3:12b") -> tuple` | Προτείνει το καλύτερο μοντέλο με βάση το διαθέσιμο VRAM. |
| `extract_params_b` | `(model_name) -> float or None` | Εξάγει parameter count από όνομα μοντέλου (π.χ. "gemma3:12b" → 12). |
| `estimate_size_for_quant` | `(model_name, quant_tag=None) -> float` | Εκτιμά μέγεθος σε GB για συγκεκριμένο quantization. |
| `estimate_size` | `(model_name) -> float` | Εκτιμά μέγεθος 4-bit quantized μοντέλου. |
| `get_installed_models` | `() -> list of str` | Λίστα εγκατεστημένων μοντέλων από το Ollama API. |
| `get_all_chat_models_sorted` | `(vram_gb=None) -> list of dict` | Όλα τα chat models με sections: installed, library, bitnet. |
| `get_embedding_models` | `() -> list of dict` | Διαθέσιμα embedding models. |
| `pull_model` | `(model_name) -> bool` | Κατεβάζει μοντέλο μέσω ollama pull. |

**Δομές δεδομένων:**
- `MODEL_SIZES`: dict με ~25 μοντέλα → εκτιμώμενο μέγεθος 4-bit σε GB
- `RECOMMENDED`: VRAM tier → recommended model
- `QUANT_SIZE_PER_BILLION`: 30+ quantization formats → GB ανά 1B parameters
- `BITNET_MODELS`: 7 μοντέλα 1-bit για edge devices
- `VRAM_HEADROOM = 0.70` (30% reserve)

---

## 3. Entry Points

### 3.1 `talos.py` (v4.10.1, 653 γραμμές)

**Ρόλος:** CLI entry point με interactive menu system (questionary).

| Συνάρτηση | Υπογραφή | Περιγραφή |
|-----------|----------|-----------|
| `safe_select` | `(message, choices) -> str or None` | Questionary select με fallback για limited terminals. |
| `run_script` | `(script_name: str, python_exe: str, args: list = None, capture: bool = False)` | Εκκινεί script ως subprocess, προωθεί environment variables (TALOS_USE_LOCAL, TALOS_ALLOW_CLOUD_FALLBACK, κ.λπ.). |
| `check_first_run` | `(python_exe)` | Αν δεν υπάρχει config.json, αντιγράφει από template και εκκινεί PYTHIA onboarding. |
| `main_menu` | `()` | Κύριο μενού: AI provider selection → search/discovery → analysis → maintenance → profiles → exit. |
| `author_tools_menu` | `(python_exe)` | Sub-menu για author tools (Profiler, Trajectory, Full Report). |
| `maintenance_menu` | `(python_exe)` | Sub-menu για database maintenance (Stats, APOLLO, Zotero, Embeddings, Re-eval, κ.λπ.). |
| `api_keys_menu` | `(python_exe)` | Sub-menu για προβολή/επεξεργασία API keys στο .env. |
| `profile_settings_menu` | `(python_exe)` | Sub-menu για profiles, PYTHIA, model management. |
| `_verify_local_models` | `()` | Ελέγχει/κατεβάζει gemma3:12b και nomic-embed-text μέσω Ollama. |

**Menu structure:**
1. SEARCH & DISCOVERY: Daily Search → Historical Search → Grey Literature
2. ANALYSIS & INSIGHTS: CHIRON → ORPHEUS → Reading Report → Author Tools → Dashboard
3. DATABASE & SETTINGS: Maintenance → Profile & Settings

**Imports:** `questionary`, `subprocess`, `dotenv`, `core.database_manager`, `core.hardware`, `scripts.profile_manager`

---

### 3.2 `app.py` (v5.2.0, ~1400 γραμμές)

**Ρόλος:** Streamlit Web GUI — πλήρες UI που αντικαθιστά το CLI. Εκτελεί όλα τα scripts ως subprocesses με stdin piping μέσω `_gui_runner.py`.

| Συνάρτηση | Υπογραφή | Περιγραφή |
|-----------|----------|-----------|
| `get_active_profile` | `() -> str` | Διαβάζει το ενεργό profile από `_profiles/active_profile.txt`. |
| `system_info` | `() -> dict` | System info (OS, Python version, provider). |
| `run` | `(name, args=None, stdin_text="", confirm="y")` | Εκτελεί script μέσω `_gui_runner.py` wrapper. Το stdin περνάει μέσω env var `TALOS_GUI_STDIN`. |
| `show_output` | `(key, label)` | Εμφανίζει output script και parse reports (.md, .html). |
| `_extract_report_path` | `(output) -> str or None` | Εξάγει path report από το output κειμένου. |
| `reload_config` | `()` | Ξαναφορτώνει config.json + AIManager. |
| `reload_db` | `()` | Ξαναφορτώνει DatabaseManager. |

**Pages (8):**
1. Home & Knowledge Base (semantic search, filters, analytics)
2. Search & Discovery (daily, historic, grey literature)
3. Single Paper Evaluation (quad-layer framework, DOI fetch, DB select)
4. Analysis & Insights (CHIRON, ORPHEUS, Recommender, Author Tools, Dashboard)
5. Database Maintenance (Stats, APOLLO, Zotero, Embeddings, Re-eval, Enrichment, Scientometrics, PDF)
6. System Diagnostics (Code Integrity, Documentation Audit, Architecture Intelligence Report)
7. DRL Agent Dashboard (GWO params, training status, reward progression chart)
8. Profile & Settings (API keys, model selection, profiles, PYTHIA, Research Pivot)

**Νέες συναρτήσεις (v5.2.0):**
| Συνάρτηση | Υπογραφή | Περιγραφή |
|-----------|----------|-----------|
| `render_onboarding_wizard` | `()` | 4-step onboarding: Profile → Research Domain → PYTHIA → Launch. |
| `_is_first_run` | `() -> bool` | Επιστρέφει True αν δεν υπάρχει active profile (πρώτη εκτέλεση). |

**Imports:** `streamlit`, `core.database_manager`, `core.ai_manager`, `core.hardware`, `pandas`, `numpy`, `scripts.profile_manager`, `scripts.query_translator`, `shutil`, `socket`, `webbrowser`, `traceback`

---

### 3.3 `_gui_runner.py`

**Ρόλος:** Wrapper που πατσάρει το `questionary` ώστε να παίρνει input από env vars αντί για interactive prompts, επιτρέποντας στο Streamlit GUI να τρέχει τα CLI scripts.

### 3.4 `start_talos.bat`

**Ρόλος:** Batch script για εύκολη εκκίνηση του Streamlit GUI (`streamlit run app.py`).

---

## 4. Scripts (21 αρχεία)

### 4.1 Search Scripts

#### `scripts/daily_search.py` (v5.4, ~270 γραμμές)
**Σκοπός:** Καθημερινή αναζήτηση σε 14 APIs, dedup, two-stage AI evaluation (Flash pre-screening → Pro deep analysis), Markdown report, Discord webhook.
**Συναρτήσεις:** `generate_markdown_report(report_data)`, `post_report_to_discord(config, markdown_content, filename)`, `load_configuration()`, `main()`
**Imports:** `core.database_manager.DatabaseManager`, `core.ai_manager.AIManager`, και τα 14 `sources.*`

#### `scripts/historic_search.py` (v5.5, ~182 γραμμές)
**Σκοπός:** Deep archive search για αρχική πλήρωση βάσης (~6 χρόνια). Dedup + Flash evaluation.
**Συναρτήσεις:** `load_configuration()`, `main()`
**Imports:** `DatabaseManager`, `AIManager`, 14 sources (εκτός PLOS)

#### `scripts/grey_literature_miner.py` (~205 γραμμές)
**Σκοπός:** Αναζήτηση grey literature (open source code, datasets, technical reports) με Gemini Search Grounding + DuckDuckGo fallback.
**Συναρτήσεις:** `load_config()`, `save_report(topic, content)`, `run_miner()`
**Imports:** `google.genai` (Search Grounding), `questionary`

---

### 4.2 Analysis & Insights Scripts

#### `scripts/knowledge_path_generator.py` (v1.8, ~187 γραμμές) — "CHIRON"
**Σκοπός:** Δημιουργεί εξατομικευμένο μονοπάτι γνώσης (semantic search + K-Means clustering + AI narrative synthesis).
**Κλάση:** `KnowledgePathGenerator`
- `__init__(config)`, `_get_user_goal()`, `_find_relevant_papers(goal_text, top_k=100)`
- `_extract_keywords_for_filename(goal_text)`, `_get_top_keywords_for_cluster(vectorizer, kmeans, cluster_id, top_n=4)`
- `_structure_knowledge(df, num_clusters=4, min_score=7.0)`, `_synthesize_narrative(structured_knowledge, user_goal)`
- `_save_report(topic_keywords, narrative_report)`, `run()`
**Imports:** `DatabaseManager`, `AIManager`, `sklearn.cluster.KMeans`, `sklearn.feature_extraction.text.TfidfVectorizer`

#### `scripts/citation_analyzer.py` (v2.1, ~224 γραμμές) — "ORPHEUS"
**Σκοπός:** Ανάλυση citation networks (references + citations) με pyvis network visualization και AI analysis.
**Συναρτήσεις:** `get_paper_identifier(user_input)`, `analyze_paper_list(ai_manager, papers, analysis_type, config)`, `create_interactive_citation_graph(target, references, citations, output_path)`, `get_target_paper_from_user(db_manager)`, `main()`
**Imports:** `AIManager`, `DatabaseManager`, `SemanticScholarSource`, `pyvis.network.Network`

#### `scripts/recommender.py` (v4.1, ~460 γραμμές) — "Strategic Reading Report"
**Σκοπός:** TF-IDF clustering + AI analysis για θεματικές αναγνωστικές προτάσεις. Εξάγει HTML, DOCX, MD reports.
**Κλάση:** `ReadingRecommender`
- `__init__(db_name)`, `load_papers_from_db()`, `get_top_keywords_for_cluster(...)`, `_clean_abstract(text)`
- `run_analysis_and_reporting(num_clusters=5, min_score=7.0)`, `_print_structured_report(...)`, `_paper_to_dict(row)`
- `export_structured_reports(...)`, `_export_structured_html(...)`, `_export_structured_docx(...)`, `_export_structured_markdown(...)`
**Imports:** `sqlite3` (direct — not DatabaseManager!), `sklearn`, `python-docx`
**Προσοχή:** Διαβάζει από SQLite απευθείας, όχι μέσω DatabaseManager. Queries πρέπει να είναι ενημερωμένα.

---

### 4.3 Configuration & AI Scripts

#### `scripts/query_translator.py` (v2.3, ~159 γραμμές) — "PYTHIA"
**Σκοπός:** Αυτοματοποιημένη ρύθμιση config.json από φυσική γλώσσα. Χρησιμοποιεί `system_prompt_override` για να λειτουργήσει το AI ως "Research Architect".
**Συναρτήσεις:** `load_config()`, `save_config(config, path)`, `flatten_json(y)` (recursive nested JSON flattening), `main()`
**Imports:** `AIManager`

#### `scripts/model_manager.py`
**Σκοπός:** Interactive διαχείριση AI μοντέλων (Ollama + cloud). Επιλογή, pull, quantization.
**Συναρτήσεις:** `get_ollama_base()`, `check_ollama_alive()`, `get_installed_models()`, `get_available_tags(model_name)`, `get_quantized_variants(model_base_name)`, `pull_model(full_name)`, `select_ollama_model(env_path)`, `select_cloud_models(env_path)`, `select_embedding_model(env_path)`, `main()`

#### `scripts/profile_manager.py`
**Σκοπός:** Διαχείριση research profiles (switch, create, PYTHIA integration). Κάθε profile έχει δικό του config.json + talos_research.db.
**Συναρτήσεις:** `run_pythia_script()`, `ensure_profiles_dir()`, `get_active_profile_name()`, `set_active_profile_name(name)`, `save_current_state_to_profile(profile_name)`, `load_profile_to_root(profile_name)`, `create_new_profile()`, `switch_profile()`, `configure_current_profile()`, `main()`

---

### 4.4 Database Maintenance Scripts

#### `scripts/db_stats.py`
**Σκοπός:** Στατιστικά και health check της βάσης.
**Συναρτήσεις:** `print_header(title)`, `main()`

#### `scripts/metadata_enricher.py` — "APOLLO"
**Σκοπός:** Εμπλουτισμός μεταδεδομένων (DOI, abstracts, author info) με fallback αναζήτηση.
**Κλάση:** `MetadataEnricher`
- `__init__(config)`, `find_papers_to_enrich()`, `update_paper_metadata(paper_id, new_data)`, `_search_with_fallback(query)`, `run()`
**Βοηθητική:** `load_configuration()`

#### `scripts/embedding_generator.py`
**Σκοπός:** Δημιουργία/ενημέρωση embeddings για papers που δεν έχουν.
**Συναρτήσεις:** `load_configuration()`, `main()`

#### `scripts/data_enricher.py`
**Σκοπός:** Εμπλουτισμός με Unpaywall/IDs (openalex_id, pmid, pmcid, oa_status).
**Συναρτήσεις:** `get_enrichment_data(doi)`, `process_paper(paper_data)`, `force_reset_status(db_path)`, `main()`

#### `scripts/reevaluate_database.py`
**Σκοπός:** AI re-evaluation papers που δεν έχουν ξανα-αξιολογηθεί πρόσφατα.
**Συναρτήσεις:** `load_configuration()`, `main()`

#### `scripts/recalculate_scores.py`
**Σκοπός:** Επανυπολογισμός overall_score για όλα τα papers (αν άλλαξαν τα βάρη).
**Συναρτήσεις:** `recalculate_database_scores()`

#### `scripts/trend_analyzer.py`
**Σκοπός:** Scientometrics report με plots και HTML export.
**Κλάση:** `TrendAnalyzer`
- `__init__(db_path)`, `load_data()`, `fig_to_base64(fig)`, `generate_plots(df)`, `generate_html_report(plots, count)`
**Βοηθητική:** `main()`

---

### 4.5 Integration Scripts

#### `scripts/drl_trainer.py` (v1.0)

**Σκοπός:** Απλοποιημένο training script για τον DRL agent (παρόμοιο με train_agent.py αλλά χωρίς φόρτωση real scores από τη βάση).

**Συναρτήσεις:** `main()` — Εκτελεί training loop με simulated scores. Χρησιμοποιεί `TalosEnv` (όχι OfflineTalosEnv).

**Imports:** `core.talos_env.TalosEnv`, `core.drl_agent`

#### `scripts/talos_live_agent.py` (v2.0 — Dynamic N-Source)

**Σκοπός:** Live DRL inference engine που κάνει ΠΡΑΓΜΑΤΙΚΑ API calls με βάση τις αποφάσεις του agent. **V2.0:** δυναμική υποστήριξη όλων των πηγών.

**Συναρτήσεις:** `_import_source_class(source_name)`, `_build_source_map(source_names)`, `calculate_state(...)`, `execute_live_fetch(action, action_map, config)`, `evaluate_paper(paper, ai_manager)`, `calculate_reward(score)`, `main()`

**Imports:** `core.drl_agent`, `core.ai_manager`, `core.talos_env`, `sources.*` (δυναμικό import)

#### `scripts/talos_service_api.py` (v1.0)

**Σκοπός:** Micro-Flask API server (port 5002) για έκθεση του status του autonomous service.

**Endpoints:** `GET /api/status` (uptime, papers found, DB stats), `GET /api/report` (σημερινό HTML report)

**Συναρτήσεις:** `_get_today_folder()`, `api_status()`, `api_report()`

#### `scripts/research_pivot.py` (v1.0 — NEW in v5.2.0)

**Σκοπός:** Interactive Research Pivot Wizard. Καθοδηγεί τον χρήστη όταν αλλάζει ερευνητικό ενδιαφέρον.

**Βήματα:**
1. Συλλογή νέας ερευνητικής κατεύθυνσης
2. Εκτέλεση PYTHIA για αναγέννηση queries/prompts
3. Προαιρετικό re-evaluate βάσης δεδομένων
4. Προαιρετικό retrain DRL agent
5. Αποθήκευση στο ενεργό profile

**Συναρτήσεις:** `get_active_profile_name()`, `save_state_to_profile(profile_name)`, `run_script(script_name, stdin_text, args)`, `main()`

**Usage:** `python scripts/research_pivot.py` (interactive), `python scripts/research_pivot.py --auto` (non-interactive)

#### `scripts/talos_service.py` (v2.0 — Profile-Aware)

**Σκοπός:** 24/7 autonomous research daemon. **V2.0:** profile-aware, δυναμικό source mapping.

**Αλλαγές από v1.1:**
- Διαβάζει active profile και φορτώνει profile-specific model
- Χρησιμοποιεί `env.SLEEP_ACTION` αντί για hardcoded `action == 3`
- Διαβάζει source names από `info["source"]` (δυναμικό, όχι hardcoded {0: "ArXiv"...})
- Δημιουργεί agent με exact dimensions από το environment

#### `scripts/zotero_connector.py`
**Σκοπός:** Συγχρονισμός με Zotero library.
**Συναρτήσεις:** `main()`

#### `scripts/pdf_downloader.py`
**Σκοπός:** Κατέβασμα open access PDFs μέσω Unpaywall, OpenAlex, και CORE API. Multi-threaded batch download με ThreadPoolExecutor.
**Συναρτήσεις:** `get_mailto()`, `find_oa_pdf(doi, mailto)`, `download_pdf(pdf_url, filename, max_retries=MAX_RETRIES)`, `get_papers_to_process(db_manager, limit=None)`, `update_paper_pdf(db_manager, paper_id, pdf_url, local_path)`, `main()`
**Σταθερές:** `DOWNLOAD_TIMEOUT=30`, `MAX_RETRIES=2`, `MAX_WORKERS=10`, `REQUEST_DELAY=1.0`

#### `scripts/interactive_dashboard.py`
**Σκοπός:** Flask/Tabulator.js dashboard στο port 5000 (legacy).
**Συναρτήσεις:** `load_configuration()`, `index()`, `get_data()`, `get_paper_details(paper_id)`, `update_zotero_status()`, `semantic_search()`, `shutdown()`, `kill_server()`

### 4.6 Author Tools

#### `scripts/author_profiler.py`
**Σκοπός:** Ενοποιημένο προφίλ ερευνητή (ORCID + OpenAlex + Semantic Scholar).
**Κλάση:** `UnifiedProfiler`
- `__init__(mailto_email)`, `_is_orcid(identifier)`, `_query_api(url, source_name, headers, params)`, `_query_orcid_search(author_name)`, `_query_openalex(orcid_id)`, `_get_doi_from_work(work_summary)`, `run(identifier)`, `display_unified_dossier(...)`, `export_to_markdown(...)`

#### `scripts/author_trajectory_analyzer.py`
**Σκοπός:** Ανάλυση πορείας ερευνητή (trajectory analysis).
**Κλάση:** `TrajectoryAnalyzer`
- `__init__(config)`, `_query_api(url, source_name, headers)`, `get_author_data(orcid_id)`, `analyze_trajectory(author_name, works)`, `_is_orcid(identifier)`, `run(identifier)`

### 4.7 Utilities

#### `scripts/generate_docs.py` (v2.0 — NEW in v5.3.0)

**Ρόλος:** Multi-Language Interactive Documentation Builder. Πλήρως διαδραστικό (questionary) — χωρίς CLI arguments. Σαρώνει **93+ αρχεία** (όχι μόνο `.py` — και HTML, CSS, JS, JSON, Dockerfile, `.bat`, `.cff`, `.clinerules`) και στέλνει το καθένα σε τοπικό Ollama instance για παραγωγή επαγγελματικής Markdown τεκμηρίωσης σε **18 γλώσσες**. LOCAL-only — ποτέ δεν καλεί cloud APIs.

| Συνάρτηση | Υπογραφή | Περιγραφή |
|-----------|----------|-----------|
| `check_ollama` | `(url: str) -> bool` | Health check — επαληθεύει ότι το Ollama τρέχει και απαντά. Επιστρέφει False αν offline → abort με σαφές μήνυμα. |
| `load_configuration` | `() -> Dict[str, str]` | Φορτώνει ρυθμίσεις από .env (OLLAMA_MODEL → LOCAL_MODEL_NAME → "gemma4" fallback). |
| `get_code_files` | `(selected_dirs: List[str]) -> List[str]` | Συλλέγει **όλα** τα code/text files από επιλεγμένους φακέλους (core, scripts, sources, templates, reference_code, root). Εξαιρεί binary, __pycache__, data, logs, models. |
| `estimate_file_info` | `(file_paths: List[str]) -> Dict[str, int]` | Μετράει total_files, total_lines, total_bytes πριν την εκτέλεση για το summary. |
| `generate_documentation` | `(source_code, file_path, model, ollama_url, language_keyword) -> Optional[str]` | POST στο Ollama `/api/generate` με δυναμικό prompt βασισμένο στην επιλεγμένη γλώσσα. Timeout 120s. |
| `save_documentation` | `(file_path, content, output_dir, lang_code) -> None` | Δημιουργεί `docs/{lang_code}/` φάκελο. Ονομασία: `core_ai_manager_doc.md`, `Dockerfile_doc.md`, κλπ. |
| `main` | `() -> None` | Πλήρως διαδραστικό: (1) Ollama health check, (2) questionary select για 18 γλώσσες, (3) questionary checkbox για επιλογή φακέλων, (4) summary με token estimate + χρόνο, (5) confirmation, (6) tqdm progress bar, (7) final report. |

**18 γλώσσες:** Ελληνικά, English, 中文, हिन्दी, Español, العربية, Français, বাংলা, Русский, Português, اردو, Bahasa Indonesia, Deutsch, 日本語, Italiano, 한국어, Türkçe, فارسی.

**Imports:** `requests`, `dotenv.load_dotenv`, `tqdm.tqdm`, `questionary`, `pathlib.Path`

**Usage:** `python scripts/generate_docs.py` (πλήρως διαδραστικό, χωρίς arguments)

#### `scripts/api_health_check.py`
**Σκοπός:** Διαγνωστικός έλεγχος όλων των APIs.
**Συναρτήσεις:** `ping_api(url, headers, timeout)`, `_format_result(name, status, detail)`, `check_source(source_name, key_env_var, ping_url, headers_fn, pbar)`, `check_ai_provider(provider_name, env_var, pbar)`, `run_diagnostics()`

#### `scripts/migrate_database_schema.py`
**Σκοπός:** Μετεγκατάσταση παλιού schema (extraction από analysis text).
**Συναρτήσεις:** `extract_from_old_analysis(analysis_text, field)`, `migrate_schema()`

---

## 5. Sources (14 APIs)

Όλα τα sources ακολουθούν το ίδιο interface:

```python
class XxxSource:
    def __init__(self, config: Dict[str, Any])  # διαβάζει query από config.json
    def fetch_new_papers(self) -> List[Dict[str, Any]]  # κύρια μέθοδος
    def _format_paper(self, item) -> Dict[str, Any]     # standardized output
```

**Standardized output format:**
```python
{
    "doi": str or None,
    "url": str or None,
    "title": str,
    "authors_str": str,        # "Author1, Author2, ..."
    "publication_year": int or None,
    "abstract": str or "",
    "source": str              # το όνομα του source (π.χ. "arXiv")
}
```

**Κανόνες:**
- Missing API keys → `self.enabled = False`, skip gracefully, ΠΟΤΕ raise
- Exponential backoff για rate-limited APIs
- Το query διαβάζεται από `config.get("<source>_query")` δυναμικά (PYTHIA-compatible)

| Source | Αρχείο | API Key Required | Query Key | Ειδικές Μέθοδοι |
|--------|--------|-----------------|-----------|-----------------|
| arXiv | `arxiv_source.py` | ❌ (keyless) | `arxiv_query` | `_format_paper(entry, ns)` |
| CORE | `core_source.py` | ⚠️ optional | `core_query` | |
| Crossref | `crossref_source.py` | ⚠️ optional | `crossref_query` | `search_papers(query, limit)` |
| DBLP | `dblp_source.py` | ❌ (keyless) | `dblp_query` | `search_papers(query, limit)` |
| Elsevier/Scopus | `elsevier_source.py` | ✅ required | `elsevier_query` | `_fetch_abstract(scopus_id)` |
| IEEE Xplore | `ieee_source.py` | ✅ required | `ieee_query` | `_make_request(params, max_retries, backoff)` |
| OpenAlex | `openalex_source.py` | ❌ (keyless) | `openalex_query` | `search_papers`, `_reconstruct_abstract(inverted_index)` |
| OpenArchives.gr | `openarchives_source.py` | ⚠️ optional | `openarchives_query` | |
| OSTI | `osti_source.py` | ❌ (keyless) | `osti_query` | |
| PLOS | `plos_source.py` | ❌ (keyless) | `plos_query` | |
| PubMed | `pubmed_source.py` | ❌ (keyless) | `pubmed_query` | |
| Science.gov | `scigov_source.py` | ❌ (keyless) | `scigov_query` | |
| Semantic Scholar | `semantic_scholar_source.py` | ⚠️ optional | `semantic_scholar_query` | `search_papers`, `get_paper_details`, `get_paper_references`, `get_paper_citations` |
| Springer Nature | `springer_source.py` | ✅ required | `springer_query` | `_make_request(params, max_retries, backoff)` |

**Keyless sources (6):** arXiv, DBLP, OpenAlex, OSTI, PLOS, PubMed, Science.gov
**Optional key (4):** CORE, Crossref, OpenArchives, Semantic Scholar
**Required key (4):** Elsevier, IEEE, Springer

---

## 6. Configuration & Data Flow

### 6.1 `config.json` Schema
```json
{
  "ai_provider_priority": ["gemini", "deepseek"],
  "failure_threshold": 3,
  "model_for_daily_search": "gemini-2.5-pro",
  "pre_screening_model": "gemini-2.5-flash-lite",
  "deepseek_model_chat": "deepseek-chat",
  "min_pre_screening_score": 6,
  "days_to_search_daily": 7,
  "days_to_search_historic": 365,
  "api_call_limit_flash": 950,
  "api_call_limit_pro": 95,
  "ai_request_delay": 5,
  "mailto": "your_email@example.com",
  "max_results_config": { "arxiv": 100, ... },
  "<source>_query": "...",     // 14 queries
  "phd_focus_system_prompt": "...",
  "pre_screening_prompt": "...",
  "query_translator_prompt": "...",
  "chiron_synthesizer_prompt": "...",
  "orpheus_references_prompt_instruction": "...",
  "orpheus_citations_prompt_instruction": "...",
  "trajectory_analyzer_prompt": "..."
}
```

### 6.2 `.env` Keys
- **Premium AI:** `GEMINI_API_KEY`, `DEEPSEEK_API_KEY`, `HF_TOKEN`
- **Academic:** `SEMANTIC_SCHOLAR_API_KEY`, `IEEE_API_KEY`, `ELSEVIER_API_KEY`, `SPRINGER_API_KEY`, `CORE_API_KEY`, `OPENARCHIVES_API_KEY`
- **Integrations:** `DISCORD_WEBHOOK_URL`, `ZOTERO_USER_ID`, `ZOTERO_API_KEY`, `ORCID_CLIENT_ID`, `ORCID_CLIENT_SECRET`
- **Local:** `LOCAL_MODEL_NAME`, `LOCAL_EMBEDDING_MODEL`
- **Contact:** `MAILTO`

### 6.3 Environment Variables (Runtime)
- `TALOS_USE_LOCAL=1` — ενεργοποιεί local mode
- `TALOS_ALLOW_CLOUD_FALLBACK=1` — επιτρέπει cloud fallback όταν είσαι σε local mode
- `TALOS_ALLOW_LOCAL_FALLBACK=1` — επιτρέπει local fallback όταν είσαι σε cloud mode
- `TALOS_MODELS_VERIFIED=1` — τα local models είναι έτοιμα
- `HF_MODEL_NAME` — HuggingFace model για free inference
- `PYTHONIOENCODING=utf-8` — προωθείται σε όλα τα subprocesses

### 6.4 Profile System
```
_profiles/
  <profile_name>/
    config.json          # απομονωμένο config
    talos_research.db    # απομονωμένη βάση
active_profile.txt       # όνομα ενεργού profile
```
- Profile switching μέσω `profile_manager.py`
- Το `DatabaseManager` δέχεται `db_path` για profile-aware λειτουργία

---

## 7. Dependency Graph

```
talos.py
  ├── core.database_manager.DatabaseManager (για stats στο header)
  ├── core.hardware.detect_vram_gb (για VRAM display)
  ├── scripts.profile_manager (get_active_profile_name, save_current_state_to_profile, set_active_profile_name)
  └── subprocess → scripts/*.py (μέσω run_script)

app.py
  ├── core.database_manager.DatabaseManager
  ├── core.ai_manager.AIManager
  ├── core.hardware (για model selection UI)
  ├── sources.semantic_scholar_source.SemanticScholarSource (για DOI fetch)
  ├── scripts.api_health_check.run_diagnostics
  └── subprocess → scripts/*.py (μέσω _gui_runner.py wrapper)

daily_search.py / historic_search.py
  ├── core.database_manager.DatabaseManager
  ├── core.ai_manager.AIManager
  └── sources.* (14 imports)

knowledge_path_generator.py (CHIRON)
  ├── core.database_manager.DatabaseManager
  ├── core.ai_manager.AIManager
  └── sklearn (KMeans, TfidfVectorizer)

citation_analyzer.py (ORPHEUS)
  ├── core.ai_manager.AIManager
  ├── core.database_manager.DatabaseManager
  ├── sources.semantic_scholar_source.SemanticScholarSource
  └── pyvis.network.Network

recommender.py
  ├── sqlite3 (direct, NOT DatabaseManager!)
  ├── sklearn (TfidfVectorizer, KMeans)
  └── python-docx

grey_literature_miner.py
  └── google.genai (Search Grounding)

query_translator.py (PYTHIA)
  └── core.ai_manager.AIManager (με system_prompt_override)

profile_manager.py
  ├── subprocess → query_translator.py (PYTHIA)
  └── shutil (copy config.json, talos_research.db)

metadata_enricher.py (APOLLO)
  ├── core.database_manager.DatabaseManager
  ├── sources.openalex_source.OpenAlexSource
  ├── sources.crossref_source.CrossrefSource
  ├── sources.dblp_source.DBLPSource
  └── sources.semantic_scholar_source.SemanticScholarSource

model_manager.py
  ├── core.hardware (detect_vram_gb, get_all_chat_models_sorted, pull_model, κ.λπ.)
  └── requests (Ollama API)

interactive_dashboard.py
  ├── core.database_manager.DatabaseManager
  ├── core.ai_manager.AIManager
  └── Flask (flask.Flask, jsonify, render_template, request)

verify_dependency_map.py (NEW in v5.0.0)
  ├── ast (Python AST for import analysis)
  └── outputs reports/audits/dependency_audit.{json,html}

generate_docs.py (NEW in v5.3.0)
  ├── requests (Ollama /api/generate)
  ├── dotenv.load_dotenv
  └── tqdm.tqdm
```

---

## 8. Greek Code Name Glossary

| Όνομα | Αρχείο/Λειτουργία | Περιγραφή |
|-------|-------------------|-----------|
| **TALOS** | `talos.py` (entry point) | Ο χάλκινος γίγαντας της ελληνικής μυθολογίας — προστάτευε την Κρήτη. Το project είναι ο "προστάτης" του ερευνητή. |
| **PYTHIA** | `scripts/query_translator.py` | Η ιέρεια του Μαντείου των Δελφών — μετέφραζε τα λόγια του θεού. Μεταφράζει τον ερευνητικό στόχο σε queries + prompts. |
| **CHIRON** | `scripts/knowledge_path_generator.py` | Ο σοφός κένταυρος — δάσκαλος ηρώων. Δημιουργεί εξατομικευμένα μονοπάτια γνώσης. |
| **ORPHEUS** | `scripts/citation_analyzer.py` | Ο μυθικός μουσικός — η μουσική του γοήτευε τα πάντα. Χαρτογραφεί citation networks. |
| **APOLLO** | `scripts/metadata_enricher.py` | Ο θεός της γνώσης και της μουσικής. Εμπλουτίζει μεταδεδομένα. |

---

## 9. Βοηθητικά Αρχεία

| Αρχείο | Ρόλος |
|--------|-------|
| `_bump.py`, `_fix_ai.py`, `_fix_now.py`, `_fix2.py`, `_fix3.py`, `_fix4.py` | Dev utility scripts για hotfixes |
| `_git_status.ps1` | PowerShell script για git status |
| `_gui_runner.py` | Wrapper για Streamlit → CLI subprocess stdin piping |
| `test_smoke.py` | Smoke test για system health |
| `templates/dashboard.html` | Tabulator.js template για το interactive dashboard |
| `Dockerfile`, `docker-compose.yml` | Containerization |
| `requirements.txt` | Python dependencies |
| `README.md` | Documentation |
| `CHANGELOG_EN.md`, `CHANGELOG_GR.md` | Δίγλωσσο changelog |
| `ROADMAP.md` | Roadmap |
| `TECH_RADAR.md` | Technology radar |
| `CITATION.cff` | Citation metadata |
| `LICENSE` | GNU AGPL v3 (commercial licensing available) |

---

## 10. Known Gotchas & Conventions

1. **Greek comments** σε source files μπορεί να προκαλέσουν προβλήματα στο text matching του editor
2. **`.env` values χωρίς quotes** — το `load_dotenv` δεν αφαιρεί quotes
3. **`daily_search.py` και `historic_search.py`** πρέπει να παραμένουν συγχρονισμένα για dedup logic
4. **4-layer framework** (strategic, operational, tactical, playground) είναι INVARIANT — η PYTHIA επαναπροσδιορίζει τα semantics, όχι τα keys
5. **`recommender.py`** διαβάζει από SQLite απευθείας, όχι μέσω DatabaseManager — προσοχή στα queries
6. **Circuit breaker** ανοίγει στα 3+ failures (configurable: `failure_threshold`)
7. **Profile-aware λειτουργία**: DatabaseManager δέχεται `db_path`, profile_manager διαχειρίζεται switching
8. **Questionary stdin piping** στο Streamlit GUI γίνεται μέσω env var `TALOS_GUI_STDIN` + `_gui_runner.py`
9. **Subprocess environment propagation**: `run_script()` στο `talos.py` προωθεί ρητά όλα τα TALOS_* env vars
10. **Embeddings** αποθηκεύονται ως pickled numpy arrays σε BLOB column, φορτώνονται στη μνήμη κατά το init

---

> **Τελευταία ενημέρωση:** 2026-07-04 (v5.3.0: Automated Documentation Builder — Greek codebase tutor via Ollama)
> **Έκδοση Project:** v5.3.0
> **Συνολικά αρχεία που καλύπτονται:** 59 (προστέθηκαν research_pivot.py, talos_live_agent.py, gui_theme.css, gui_strings.py, generate_docs.py)
