# PROJECT_MAP.md — Πλήρης Χάρτης του Project TALOS v5.3.1

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
│  talos_live_agent.py (thin entry, v3.1 cooldown)                │
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
│                    CORE MODULES (7 αρχεία)                       │
│  ai_manager.py          database_manager.py        hardware.py  │
│  drl_agent.py           talos_env.py                            │
│  live_agent_sources.py  live_agent_orchestrator.py              │
│  (Multi-provider LLM)   (SQLite + Embeddings)     (GPU detect)  │
│  (DDQN Agent)           (Gym Env)  (Source Disc) (Live Loop)    │
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

### 2.0 `core/talos_env.py` — Gymnasium Environment (v2.1, Provider-Aware)

**Ρόλος:** RL environment για API source selection. **V2.1:** Fixed hour normalization `/23.0` → `/24.0`. **v3.0:** Provider-aware observation — state vector includes 4 provider ratios (gemini, deepseek, huggingface, local) για τον DRL agent.

**Module-level constants:**
- `_PROVIDER_NAMES` = ["gemini", "deepseek", "huggingface", "local"]
- `_PROVIDER_COUNT` = 4

| Μέθοδος | Υπογραφή | Περιγραφή |
|---------|----------|-----------|
| `_load_source_list` | `(config=None) -> list` | Διαβάζει τη λίστα πηγών από config.json (source_names ή auto-detect από _query keys). |
| `_try_load_config` | `() -> dict or None` | Φορτώνει config.json από το project root. |
| `_load_source_limits` | `(source_names, config=None) -> np.ndarray` | Διαβάζει per-source API limits από config. |
| `__init__` | `(self, source_names=None, source_limits=None, config=None)` | Dynamic init με N πηγές. Obs size = 1 + N + 2 + 4 (providers). |
| `reset` | `(seed=None, options=None) -> (obs, info)` | Μηδενίζει όλους τους counters. |
| `step` | `(action) -> (obs, reward, terminated, truncated, info)` | Εκτελεί action. Actions 0..N-1 = query πηγή, N = sleep. |
| `_build_obs` | `() -> np.ndarray` | v3.0: [hour/24, usage_ratios..., low/10, err/10, 4x zeros] — provider zeros during training. |
| `get_default_state_space` | `() -> int` | v3.0: 1 + N + 2 + 4. |
| `get_default_action_space` | `() -> int` | N + 1 sleep. |

### 2.1 `core/ai_manager.py` — Κλάση `AIManager` (v3.5, 380 γραμμές)

**Ρόλος:** Multi-provider LLM interface με circuit breaker pattern. Διαχειρίζεται 4 providers: Gemini (πρωτεύων cloud), DeepSeek (fallback), HuggingFace (δωρεάν cloud), Local/Ollama (offline).

| Μέθοδος | Υπογραφή | Περιγραφή |
|---------|----------|-----------|
| `__init__` | `(self, config: Dict[str, Any])` | Αρχικοποιεί όλους τους providers από config + .env. Θέτει provider_priority, FAILURE_THRESHOLD. |
| `_clean_json_string` | `(self, text: str) -> str` | Εξάγει καθαρό JSON από LLM response. |
| `evaluate_paper_json` | `(self, paper_content: str, model_type: str = 'pro', system_prompt_override: str = None) -> Union[Dict, None]` | Αξιολογεί paper με AI, structured JSON. |
| `analyze_generic_text` | `(self, full_prompt: str) -> str` | Αναλύει arbitrary text. |
| `_execute_request` | `(self, prompt: str, model_type: str, response_format: str = 'text') -> Union[Dict, str, None]` | Multi-provider request με circuit breaker. |
| `_handle_failure` | `(self, provider_name: str)` | Αυξάνει failure counter, ανοίγει circuit στα 3+. |

**Providers:**
- `gemini`: flash_model (pre-screening), pro_model (deep analysis)
- `deepseek`: OpenAI client, model: deepseek-chat
- `huggingface`: OpenAI client, free inference
- `local`: Ollama OpenAI-compatible, model: gemma3:12b

---

### 2.2 `core/live_agent_sources.py` — Source Discovery (v1.0, NEW in v5.3.1)

**Ρόλος:** Source discovery and dynamic import for the TALOS Live DRL Agent. Scans config.json for `_query` keys, imports source classes by scanning modules for any class ending in "Source" (handles mixed naming: DBLP→DBLPSource, IEEE→IEEEXploreSource, etc.).

| Συνάρτηση | Υπογραφή | Περιγραφή |
|-----------|----------|-----------|
| `import_source_class` | `(source_name: str) -> class or None` | Δυναμικό import με auto-detect κλάσης (ψάχνει για *Source). |
| `build_source_map` | `(source_names: list) -> (dict, list)` | DENSE action mapping: {0: (name, cls), ...}. Επιστρέφει και τη λίστα των working source names. |

### 2.3 `core/live_agent_orchestrator.py` — Main Loop + Cooldown (v1.0, NEW in v5.3.1)

**Ρόλος:** Core orchestration loop για το TALOS Live DRL Agent. Handles state calculation, action selection, API fetch, AI evaluation, reward, counters, and provider tracking. **v3.1 Cooldown:** `active_cooldowns` dict prevents deadlocks — actions with negative reward get 5-step lockout, overridden by random free action.

| Συνάρτηση | Υπογραφή | Περιγραφή |
|-----------|----------|-----------|
| `_get_provider_limits` | `(config: dict) -> dict` | Διαβάζει per-provider limits με tier-based Gemini. |
| `calculate_state` | `(...) -> np.ndarray` | v3.0 Provider-Aware state: 1 + N_sources + 2 + 4. |
| `execute_live_fetch` | `(action, action_map, config) -> tuple` | Εκτελεί ΕΝΑ live API call. |
| `evaluate_paper` | `(paper, ai_manager, provider_call_counts) -> float` | AI evaluation + provider tracking. |
| `calculate_reward` | `(score: float) -> float` | Score-to-reward mapping (+20, +5, -10). |
| `run_live_loop` | `(agent, action_map, sources, config, ai_manager, verbose) -> dict` | **Main loop.** Cooldown: epsilon=0.05, 5-step lockout, random override. |

**Cooldown mechanism (v3.1):**
- `reward < 0` → `active_cooldowns[action] = 5`
- All cooldowns decrement each iteration, removed at 0
- If agent picks cooldown action → random free action override
- Cooldowns reset on sleep (new "day")

---

### 2.4 `core/drl_networks.py` — Neural Network Architectures (v1.0, NEW in v5.3.2)

**Ρόλος:** Pluggable neural network architectures for the DRL agent. **v1.0:** Contains `DuelingLSTM` — 3-layer LSTM with dueling heads (V + A). Designed for future architectures (Transformer, xLSTM) via a common `(input_dim, output_dim)` interface.

| Κλάση | Υπογραφή | Περιγραφή |
|-------|----------|-----------|
| `DuelingLSTM` | `__init__(input_dim, output_dim)` | 3-layer LSTM (128→64→32) με LayerNorm + dueling heads. `forward(state) -> Q-values`. |

### 2.5 `core/drl_agent.py` — DRL Agent (v2.2, Pluggable Network)

**Ρόλος:** Double Dueling DQN agent. **V2.2:** `network_class` parameter — any network from `drl_networks.py` can be injected. Save/load includes network class name for correct reconstruction.

**Hyperparameters (GWO-optimized):** `LR=4.735e-05`, `GAMMA=0.575`.

**Κλάση `TalosDRLAgent`:**
| Μέθοδος | Υπογραφή | Περιγραφή |
|---------|----------|-----------|
| `__init__` | `(state_dim=None, action_dim=None, network_class=None)` | v2.2: `network_class` param (default: DuelingLSTM). |
| `act` | `(state, eps=0.0) -> int` | ε-greedy action selection. |
| `learn` | `()` | DDQN learning step. |
| `save` | `(path)` | Αποθηκεύει weights + metadata **including** `network_class` name. |
| `load` | `(path)` | v2.2: Resolves network class from saved metadata, uses DuelingLSTM as fallback. |

**Hyperparameters (GWO-optimized):**
- `LR = 4.735e-05` (GWO-optimized learning rate)
- `GAMMA = 0.575` (GWO-optimized discount factor)
- `TAU = 1e-3`, `MEMORY_LEN = 10000`, `BATCH_SIZE = 200`

**Κλάση `DuelingLSTM`:**
| Μέθοδος | Υπογραφή | Περιγραφή |
|---------|----------|-----------|
| `__init__` | `(input_dim=STATE_SPACE, output_dim=ACTION_SPACE)` | 3-layer LSTM (128→64→32) με dueling heads. |
| `forward` | `(state) -> Q-values` | Forward pass με CuDNN flatten_parameters(). |

**Κλάση `TalosDRLAgent`:**
| Μέθοδος | Υπογραφή | Περιγραφή |
|---------|----------|-----------|
| `__init__` | `(state_dim=None, action_dim=None)` | Δυναμική αρχικοποίηση. |
| `act` | `(state, eps=0.0) -> int` | ε-greedy action selection. |
| `learn` | `()` | DDQN learning step. |
| `save` | `(path)` | Αποθηκεύει weights + metadata. |
| `load` | `(path)` | v2.1: Pre-checks dims, recreates networks if needed, THEN load_state_dict. `weights_only=True`. |

### 2.5 `core/notifier.py` — Κλάση `TalosNotifier` (v1.0, ~202 γραμμές)

**Ρόλος:** Multi-channel notification system (Telegram, Discord, Email).

### 2.6 `core/database_manager.py` — Κλάση `DatabaseManager` (v4.8.5, 569 γραμμές)

**Ρόλος:** SQLite database layer με embeddings, semantic search, profile-aware.

### 2.7 `core/hardware.py` (v4.8.5, 429 γραμμές)

**Ρόλος:** Ανίχνευση GPU VRAM, προτάσεις μοντέλων Ollama.

---

## 3. Entry Points

### 3.1 `talos.py` (v4.10.1, 653 γραμμές)
CLI entry point με interactive menu.

### 3.2 `app.py` (v5.2.0, ~1400 γραμμές)
Streamlit Web GUI.

### 3.3 `_gui_runner.py`
Wrapper για Streamlit stdin piping.

### 3.4 `start_talos.bat`
Batch script για Streamlit GUI.

---

## 4. Scripts (21 αρχεία)

### 4.1 Search Scripts
- `daily_search.py` (v5.4) — Καθημερινή αναζήτηση σε 14 APIs
- `historic_search.py` (v5.5) — Deep archive search
- `grey_literature_miner.py` — Grey literature με Gemini Search Grounding

### 4.2 Analysis & Insights
- `knowledge_path_generator.py` (v1.8) — "CHIRON"
- `citation_analyzer.py` (v2.1) — "ORPHEUS"
- `recommender.py` (v4.1) — "Strategic Reading Report"

### 4.3 Configuration & AI
- `query_translator.py` (v2.3) — "PYTHIA"
- `model_manager.py` — Interactive model management
- `profile_manager.py` — Profile switching

### 4.4 Database Maintenance
- `db_stats.py`, `metadata_enricher.py` (APOLLO), `embedding_generator.py`, `data_enricher.py`, `reevaluate_database.py`, `recalculate_scores.py`, `trend_analyzer.py`

### 4.5 Integration Scripts

#### `scripts/drl_trainer.py` (v1.1 — GWO-Optimized)
**Σκοπός:** Training script με GWO-optimized hyperparameters. **v1.1:** `EPS_DECAY=0.9415` (GWO), saves as `dddqn_trained.pth`.
**Συναρτήσεις:** `main()` — 700 episodes, simulated scores, provider-aware state (dim=21).
**Imports:** `core.talos_env.TalosEnv`, `core.drl_agent`

#### `scripts/talos_live_agent.py` (v3.1 — Thin Entry, Cooldown)
**Σκοπός:** Thin entry point (~110 γραμμές). **v3.1:** epsilon=0.05, 5-step cooldown για negative-reward actions, ASCII output. Delegates to `core.live_agent_orchestrator.run_live_loop()`.
**Συναρτήσεις:** `main()` only — config load, source discovery, model load, run loop.
**Imports:** `core.drl_agent`, `core.ai_manager`, `core.talos_env`, `core.live_agent_sources`, `core.live_agent_orchestrator`

#### `scripts/talos_service_api.py` (v1.0)
Micro-Flask API server (port 5002).

#### `scripts/research_pivot.py` (v1.0)
Interactive Research Pivot Wizard.

#### `scripts/talos_service.py` (v2.0)
24/7 autonomous research daemon.

#### `scripts/zotero_connector.py`, `pdf_downloader.py`, `interactive_dashboard.py`

### 4.6 Author Tools
- `author_profiler.py`, `author_trajectory_analyzer.py`

### 4.7 Utilities
- `generate_docs.py` (v2.0), `api_health_check.py`, `migrate_database_schema.py`

---

## 5. Sources (14 APIs)

| Source | Αρχείο | API Key | Query Key |
|--------|--------|---------|-----------|
| arXiv | `arxiv_source.py` | ❌ | `arxiv_query` |
| CORE | `core_source.py` | ⚠️ | `core_query` |
| Crossref | `crossref_source.py` | ⚠️ | `crossref_query` |
| DBLP | `dblp_source.py` | ❌ | `dblp_query` |
| Elsevier | `elsevier_source.py` | ✅ | `elsevier_query` |
| IEEE | `ieee_source.py` | ✅ | `ieee_query` |
| OpenAlex | `openalex_source.py` | ❌ | `openalex_query` |
| OpenArchives | `openarchives_source.py` | ⚠️ | `openarchives_query` |
| OSTI | `osti_source.py` | ❌ | `osti_query` |
| PLOS | `plos_source.py` | ❌ | `plos_query` |
| PubMed | `pubmed_source.py` | ❌ | `pubmed_query` |
| Science.gov | `scigov_source.py` | ❌ | `scigov_query` |
| Semantic Scholar | `semantic_scholar_source.py` | ⚠️ | `semantic_scholar_query` |
| Springer | `springer_source.py` | ✅ | `springer_query` |

---

## 6. Configuration & Data Flow

### 6.1 `config.json` Schema (v5.3.1)
```json
{
  "ai_provider_priority": ["gemini", "deepseek", "huggingface", "local"],
  "gemini_tier": "free",
  "provider_limits": {
    "gemini": {
      "free":    { "rpm": 5,    "rpd": 1500,  "tpm": 32000 },
      "tier1":   { "rpm": 1000, "rpd": 10000, "tpm": 1000000 },
      "tier2":   { "rpm": 2000, "rpd": 50000, "tpm": 2000000 }
    },
    "deepseek":     { "rpm": 60,  "rpd": 1000 },
    "huggingface":  { "rpm": 30,  "rpd": 500 },
    "local":        { "rpm": 9999,"rpd": 99999 }
  },
  "failure_threshold": 3,
  "model_for_daily_search": "gemini-2.5-pro",
  "pre_screening_model": "gemini-2.5-flash",
  "min_pre_screening_score": 6,
  "max_results_config": { ... },
  "<source>_query": "...",     // 14 queries (all 14 sources)
  "phd_focus_system_prompt": "...",
  ...
}
```

### 6.2 `.env` Keys
- **Premium AI:** `GEMINI_API_KEY`, `DEEPSEEK_API_KEY`, `HF_TOKEN`
- **Academic:** `SEMANTIC_SCHOLAR_API_KEY`, `IEEE_API_KEY`, `ELSEVIER_API_KEY`, `SPRINGER_API_KEY`, `CORE_API_KEY`, `OPENARCHIVES_API_KEY`
- **Local:** `LOCAL_MODEL_NAME`, `LOCAL_EMBEDDING_MODEL`

### 6.3 Environment Variables (Runtime)
- `TALOS_USE_LOCAL=1` — local mode (Ollama)
- `TALOS_ALLOW_CLOUD_FALLBACK=1` — cloud fallback

### 6.4 Profile System
```
_profiles/<name>/config.json + talos_research.db
active_profile.txt
```

---

## 7. Dependency Graph (v5.3.1)

```
talos_live_agent.py (thin entry, v3.1)
  ├── core.drl_agent.TalosDRLAgent
  ├── core.ai_manager.AIManager
  ├── core.talos_env (_load_source_list, _try_load_config)
  ├── core.live_agent_sources (build_source_map)
  └── core.live_agent_orchestrator (run_live_loop)

talos.py → subprocess → scripts/*.py
app.py → subprocess → scripts/*.py

drl_trainer.py
  ├── core.talos_env.TalosEnv
  └── core.drl_agent

daily_search.py / historic_search.py
  ├── core.database_manager, core.ai_manager
  └── sources.* (14 imports)

knowledge_path_generator.py (CHIRON)
  ├── core.database_manager, core.ai_manager
  └── sklearn (KMeans, TfidfVectorizer)

citation_analyzer.py (ORPHEUS)
  ├── core.ai_manager, core.database_manager
  ├── sources.semantic_scholar_source
  └── pyvis.network.Network

recommender.py → sqlite3 (direct), sklearn, python-docx
grey_literature_miner.py → google.genai
query_translator.py (PYTHIA) → core.ai_manager
profile_manager.py → subprocess → query_translator.py
metadata_enricher.py (APOLLO) → core.database_manager, 4 sources
model_manager.py → core.hardware, requests
interactive_dashboard.py → core.database_manager, core.ai_manager, Flask
verify_dependency_map.py → ast → reports/audits/
generate_docs.py → requests, dotenv, tqdm
```

---

## 8. Greek Code Name Glossary

| Όνομα | Αρχείο | Περιγραφή |
|-------|--------|-----------|
| **TALOS** | `talos.py` | Ο χάλκινος γίγαντας — προστάτης του ερευνητή |
| **PYTHIA** | `scripts/query_translator.py` | Ιέρεια των Δελφών — μεταφράζει στόχους σε queries |
| **CHIRON** | `scripts/knowledge_path_generator.py` | Σοφός κένταυρος — μονοπάτια γνώσης |
| **ORPHEUS** | `scripts/citation_analyzer.py` | Μυθικός μουσικός — citation networks |
| **APOLLO** | `scripts/metadata_enricher.py` | Θεός της γνώσης — εμπλουτισμός μεταδεδομένων |

---

## 9. Βοηθητικά Αρχεία

| Αρχείο | Ρόλος |
|--------|-------|
| `_gui_runner.py` | Streamlit stdin piping wrapper |
| `test_smoke.py` | System health smoke test |
| `Dockerfile`, `docker-compose.yml` | Containerization |
| `README.md`, `CHANGELOG_EN.md`, `CHANGELOG_GR.md`, `ROADMAP.md` | Documentation |
| `TECH_RADAR.md`, `CITATION.cff`, `LICENSE` | Metadata |

---

## 10. Known Gotchas & Conventions

1. **Greek comments** break editor text matching
2. **`.env` values χωρίς quotes** — load_dotenv δεν αφαιρεί quotes
3. **`daily_search.py` και `historic_search.py`** πρέπει να συγχρονίζονται για dedup
4. **4-layer framework** (strategic, operational, tactical, playground) είναι INVARIANT
5. **`recommender.py`** διαβάζει SQLite απευθείας, όχι μέσω DatabaseManager
6. **Circuit breaker** στα 3+ failures
7. **Profile-aware**: DatabaseManager δέχεται `db_path`
8. **Questionary stdin piping** μέσω `TALOS_GUI_STDIN` + `_gui_runner.py`
9. **Subprocess env propagation**: `run_script()` προωθεί TALOS_* vars
10. **Embeddings** ως pickled numpy arrays σε BLOB column
11. **Source class names** έχουν mixed conventions (DBLPSource, IEEEXploreSource, OpenAlexSource) — χρήση `live_agent_sources.import_source_class()` που σκανάρει το module
12. **Cooldown mechanism** (v3.1): negative reward → 5-step lockout → random override — αποτρέπει Deterministic Loops

---

> **Τελευταία ενημέρωση:** 2026-07-05 (v5.3.1: Provider-Aware DRL, GWO hyperparams, cooldown, modular refactoring)
> **Έκδοση Project:** v5.3.1
> **Συνολικά αρχεία που καλύπτονται:** 61 (προστέθηκαν live_agent_sources.py, live_agent_orchestrator.py)