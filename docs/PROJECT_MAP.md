# PROJECT_MAP.md -- Πλήρης Χάρτης του Project TALOS v5.9.18

> **Σκοπός:** Αυτό το αρχείο είναι η "μνήμη" του project. Διαβάζεται υποχρεωτικά από κάθε νέο chat ώστε ο AI agent να γνωρίζει ακριβώς τι υπάρχει, πού, και πώς συνδέεται -- χωρίς να ξαναδιαβάζει όλα τα αρχεία.
>
> **Κανόνας:** Μετά από ΚΑΘΕ αλλαγή κώδικα (νέα συνάρτηση, τροποποίηση υπογραφής, νέο/διαγραμμένο αρχείο), αυτό το αρχείο ΠΡΕΠΕΙ να ενημερώνεται.
>
> **Τελευταία Ενημέρωση:** 2026-08-14 (v5.9.18 -- Καθολικό Πλέγμα Νέφους & Επέκταση Πολυπαρόχου Εφεδρείας)

---

## 1. Επισκόπηση Αρχιτεκτονικής

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER INTERFACES                          │
│  talos.py (CLI menu)     src/api/main_api.py (FastAPI — 15 endpoints)   │
│  React 18 + Tailwind CSS + Shadcn UI     templates/dashboard.html (Flask)│
└──────────────────────────┬──────────────────────────────────────┘
│                            │ subprocess / direct import
│                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    src/ SRV PACKAGES (55 αρχεία)                 │
│  src/ai/drl/   (9 files) — DRL agent, networks, env, trainer,   │
│                            live agent, service                   │
│  src/ai/optimizers/ (2)  — GWO optimizer + live dashboard       │
│  src/ai/embeddings/  (2) — embedding_generator, db upgrade      │
│  src/ai/llm/         (3) — PYTHIA, model_manager, research_pivot│
│  src/analysis/       (9) — citation_analyzer, author_profiler,  │
│                            knowledge_path, recommender, etc.    │
│  src/utils/          (8) — db_stats, api_health_check, docs,    │
│                            verify_dep_map, dashboard, etc.      │
│  src/api/            (2) — talos_service_api, main_api.py (15 endpoints) │
└──────────────────────────┬──────────────────────────────────────┘
│                            │ import
│                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    src/core/ (5 αρχεία — Global Handlers)       │
│  ai_manager.py          database_manager.py        hardware.py  │
│  notifier.py            profile_manager.py                      │
│  (Multi-provider LLM)   (SQLite + Embeddings)     (GPU detect)  │
└──────────────────────────┬──────────────────────────────────────┘
│                            │ import
│                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    src/ingestion/ (21 αρχεία)                    │
│  14 APIs: arxiv  elsevier  semantic_scholar  ieee  springer     │
│           openalex  dblp  core  crossref  openarchives  pubmed  │
│           scigov  osti  plos                                    │
│  7 pipelines: daily_search  historic_search  grey_lit  pdf      │
│               zotero  metadata_enricher  data_enricher          │
│  Standardized output: {doi, url, title, authors_str,            │
│                        publication_year, abstract, source}      │
└──────────────────────────┬──────────────────────────────────────┘
│                            │ HTTP requests
│                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    EXTERNAL APIs & SERVICES                     │
│  Gemini API  DeepSeek API  HuggingFace  Ollama  Discord  Zotero │
│  Unpaywall  ORCID  Semantic Scholar  IEEE  Elsevier  Springer   │
└─────────────────────────────────────────────────────────────────┘

Data Flow:
  User → talos.py → run_script() → src/*/*.py → src/core/*.py
                                              → src/ingestion/*.py → External APIs
                                                       ↕
                                               data/talos_research.db (SQLite)
                                                       ↕
                                               config.json + .env
```

---

## 2. Core Modules

### 2.0 `core/talos_env.py` — Gymnasium Environment (v3.1, Time-limit Truncation Fix)

**Ρόλος:** RL environment για API source selection. **V2.1:** Fixed hour normalization `/23.0` → `/24.0`. **v3.0:** Provider-aware observation — state vector includes 4 provider ratios (gemini, deepseek, huggingface, local) για τον DRL agent. **v3.1 (Batch 1 audit):** Το 200-step cutoff επιστρέφεται πλέον ως `truncated=True` (όχι `terminated`) — Gymnasium time-limit semantics, ώστε το Bellman target να κάνει bootstrap πέρα από το τεχνητό όριο.

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

### 2.1 `core/ai_manager.py` — Κλάση `AIManager` (v3.9)

**v3.7 (Batch 1 audit):** Νέο attribute `last_provider_used` — ενημερώνεται σε κάθε επιτυχημένο `_execute_request()` με το όνομα του provider που εξυπηρέτησε το request. Χρησιμοποιείται από τον live orchestrator για σωστό provider attribution.
**v3.8 (Batch 3 hotfix):** Υλοποιήθηκε η `analyze_generic_text(full_prompt) -> str|None` — ήταν τεκμηριωμένη στον χάρτη και καλούνταν από το grey_literature_miner.py, αλλά ΔΕΝ υπήρχε στον κώδικα (AttributeError). Thin wrapper γύρω από `_execute_request(model_type='pro', response_format='text')`.

**Ρόλος:** Multi-provider LLM interface με circuit breaker pattern. Διαχειρίζεται 9 providers μέσω Καθολικού Πλέγματος Νέφους (v5.9.18): Gemini (Google GenAI SDK, μη-OpenAI) + 8 συμβατοί με OpenAI πάροχοι εφεδρείας (NVIDIA NIM, Groq, Cerebras, GitHub Models, Mistral, OpenRouter, DeepSeek, HuggingFace) + Local/Ollama (offline).

| Μέθοδος | Υπογραφή | Περιγραφή |
|---------|----------|-----------|
| `__init__` | `(self, config: Dict[str, Any])` | Αρχικοποιεί όλους τους providers από config + .env μέσω του `OPENAI_COMPATIBLE_REGISTRY`. Θέτει provider_priority, FAILURE_THRESHOLD. |
| `_clean_json_string` | `(self, text: str) -> str` | Εξάγει καθαρό JSON από LLM response. |
| `evaluate_paper_json` | `(self, paper_content: str, model_type: str = 'pro', system_prompt_override: str = None) -> Union[Dict, None]` | Αξιολογεί paper με AI, structured JSON. |
| `analyze_generic_text` | `(self, full_prompt: str) -> str` | Αναλύει arbitrary text. |
| `_execute_request` | `(self, prompt: str, model_type: str, response_format: str = 'text') -> Union[Dict, str, None]` | Multi-provider request με 2D Execution Matrix routing. |
| `_execute_cloud_chain` | `(self, prompt: str, model_type: str, response_format: str) -> Union[Dict, str, None]` | Δρομολογεί μέσω `provider_priority` (Universal Cloud Mesh), παρακάμπτοντας unconfigured/open-circuit providers. |
| `_execute_openai_compatible_request` | `(self, provider_name: str, prompt: str, model_type: str, response_format: str) -> Union[Dict, str, None]` | Ενοποιημένος χειριστής OpenAI-compatible providers με circuit breaker. |
| `_handle_failure` | `(self, provider_name: str)` | Αυξάνει failure counter, ανοίγει circuit στα 5+. |

**Providers:**
- `gemini`: Google GenAI SDK, flash_model (pre-screening), pro_model (deep analysis)
- `nvidia`: OpenAI-compatible, model: nvidia/nemotron-3-ultra
- `groq`: OpenAI-compatible, model: llama-3.3-70b-versatile
- `cerebras`: OpenAI-compatible, model: llama-3.1-70b
- `github`: OpenAI-compatible, model: gpt-4o-mini
- `mistral`: OpenAI-compatible, model: mistral-small-latest
- `openrouter`: OpenAI-compatible, model: meta-llama/llama-3.3-70b-instruct:free
- `deepseek`: OpenAI-compatible, model: deepseek-chat
- `huggingface`: OpenAI-compatible, model: meta-llama/Llama-3.3-70B-Instruct
- `local`: Ollama OpenAI-compatible, model: gemma3:12b

---

### 2.2 `core/live_agent_sources.py` — Source Discovery (v1.0, NEW in v5.3.1)

**Ρόλος:** Source discovery and dynamic import for the TALOS Live DRL Agent. Scans config.json for `_query` keys, imports source classes by scanning modules for any class ending in "Source" (handles mixed naming: DBLP→DBLPSource, IEEE→IEEEXploreSource, etc.).

| Συνάρτηση | Υπογραφή | Περιγραφή |
|-----------|----------|-----------|
| `import_source_class` | `(source_name: str) -> class or None` | Δυναμικό import με auto-detect κλάσης (ψάχνει για *Source). |
| `build_source_map` | `(source_names: list) -> (dict, list)` | DENSE action mapping: {0: (name, cls), ...}. Επιστρέφει και τη λίστα των working source names. |

### 2.3 `core/live_agent_orchestrator.py` — Main Loop + Cooldown (v1.1, Batch 1 audit)

**v1.1 fixes:** (1) `LOW_SCORE_MAX` 20 → 10 ώστε το streak normalization να ταιριάζει με το training env (/10) — εξάλειψη train/inference distribution mismatch. (2) `evaluate_paper()` πλέον πιστώνει τον provider που ΠΡΑΓΜΑΤΙΚΑ απάντησε (`ai_manager.last_provider_used`), όχι πάντα "gemini".

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

**Hyperparameters (GWO-optimized v2.0):** `LR=3.361e-05`, `GAMMA=0.6983`, `EPS_DECAY=0.9202` (80 iters, 9.5h, fitness -2353.0).

**Κλάση `TalosDRLAgent`:**
| Μέθοδος | Υπογραφή | Περιγραφή |
|---------|----------|-----------|
| `__init__` | `(state_dim=None, action_dim=None, network_class=None)` | v2.2: `network_class` param (default: DuelingLSTM). |
| `act` | `(state, eps=0.0) -> int` | ε-greedy action selection. |
| `learn` | `()` | DDQN learning step. |
| `save` | `(path)` | Αποθηκεύει weights + metadata **including** `network_class` name. |
| `load` | `(path)` | v2.2: Resolves network class from saved metadata, uses DuelingLSTM as fallback. |

**Hyperparameters (GWO-optimized v2.0):**
- `LR = 3.361e-05` (GWO-optimized learning rate)
- `GAMMA = 0.6983` (GWO-optimized discount factor)
- `EPS_DECAY = 0.9202` (GWO-optimized epsilon decay, in drl_trainer.py)
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

### 2.8 `templates/gui_theme.css` — Academic Theme CSS (v5.3.3)
**Ρόλος:** Light-only CSS theme για το Streamlit Web GUI (dark mode removed in v5.3.3).
**CSS variables injected by `app.py:render_css()`** — academic blue/teal palette με glassmorphism cards, custom scrollbar, και professional typography.

### 2.9 `templates/gui_strings.py` — Translation System (v5.3.3)
**Ρόλος:** Translation strings σε English + Greek για το Streamlit GUI. Εξάγει `STR` dict και `t(key, en_default="")` function. Dark theme toggle string removed in v5.3.3.

---

## 3. Entry Points

### 3.1 `talos.py` (v5.3.6 — TUI Hardening)
CLI entry point με interactive menu. **v5.3.6 (Batch 2 TUI audit):** Νέα `safe_pause()` (Ctrl+C σε "Press Enter" prompts επιστρέφει στο μενού)· `safe_select()` πιάνει KeyboardInterrupt → None· διόρθωση διπλού "6." στο System Diagnostics (το "Baseline Report (Standard)" ήταν dead code — μενού αναριθμήθηκε 1-10)· bare `except:` → `except Exception:`· `TALOS_VERSION` constant στο header· top-level guard με `sys.exit(0)`.

### 3.2 `src/api/main_api.py` (v1.3, ~1000 γραμμές)
Headless FastAPI REST facade (15 endpoints) — sole backend for React 18 frontend. Streamlit deprecated in v5.6.0.

### 3.3 `start_talos.bat`
Batch script για εκκίνηση του TALOS CLI.

---

## 4. Scripts (21 αρχεία)

### 4.1 Search Scripts
- `daily_search.py` (v5.4) — Καθημερινή αναζήτηση σε 14 APIs
- `historic_search.py` (v5.5) — Deep archive search
- `grey_literature_miner.py` (v2.1) — Grey literature με Gemini Search Grounding. **v2.1 (Batch 3):** `ddgs` import με fallback στο legacy `duckduckgo_search`· το missing GEMINI_API_KEY δεν είναι πλέον fatal (τρέχει με AIManager fallback + DuckDuckGo grounding).

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

#### `scripts/drl_trainer.py` (v1.3 — Batch 2 TUI hardening)
**Σκοπός:** Training script με GWO-optimized hyperparameters. **v1.1:** `EPS_DECAY=0.9415` (GWO), saves as `dddqn_trained.pth`. **v1.2:** Fix fatal `NameError` (`args.episodes` → `episodes` σε interactive mode)· αποθηκεύει `done=terminated` μόνο (truncation bootstrap). **v1.3 (Batch 2, μόνο presentation):** Ctrl+C μεσα στην εκπαίδευση → αποθήκευση partial model σε `models/dddqn_partial.pth` + clean exit(0)· single-line progress ticker (`\r`) ανάμεσα στα 50-episode summaries· Ctrl+C guards σε prompt και top-level.

#### `scripts/gwo_rl_optimizer.py` (v2.0 — Real Fitness + Canonical GWO)
**Σκοπός:** GWO hyperparameter tuning. **v2.0 (Batch 1 audit):** (1) `calculate_fitness()` εκπαιδεύει ΠΡΑΓΜΑΤΙΚΑ τον agent (store + learn + decayed epsilon) και μετρά fitness σε ξεχωριστή greedy evaluation phase (`EVAL_EPISODES=5`) — πριν, το fitness ήταν καθαρός θόρυβος (eps=1.0, χωρίς learn()). (2) `update_wolf_position()` = canonical GWO (Mirjalili 2014): fresh r1/r2/A/C ανά alpha/beta/delta term. (3) Fitness values cached ανά iteration — το `_build_history_entry()` δέχεται `fitness_values` αντί να επανα-υπολογίζει.
**Συναρτήσεις:** `main()` — 700 episodes, simulated scores, provider-aware state (dim=21).
**Imports:** `core.talos_env.TalosEnv`, `core.drl_agent`

#### `scripts/talos_live_agent.py` (v3.2 — Batch 2 TUI hardening)
**Σκοπός:** Thin entry point. **v3.1:** epsilon=0.05, 5-step cooldown για negative-reward actions, ASCII output. Delegates to `core.live_agent_orchestrator.run_live_loop()`. **v3.2:** argparse (`--verbose`, `--help`) αντί για ad-hoc sys.argv· formatted startup summary table· top-level KeyboardInterrupt guard (clean exit(0) σε Ctrl+C κατά το startup).
**Συναρτήσεις:** `_parse_args()`, `main()` — config load, source discovery, model load, run loop.
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
  "ai_provider_priority": ["local", "nvidia", "groq", "cerebras", "github", "gemini", "deepseek", "mistral", "openrouter", "huggingface"],
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
  "failure_threshold": 5,
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
- **Universal Cloud Mesh (v5.9.18):** `NVIDIA_API_KEY`, `GROQ_API_KEY`, `CEREBRAS_API_KEY`, `GITHUB_TOKEN`, `MISTRAL_API_KEY`, `OPENROUTER_API_KEY`
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

## 7. Dependency Graph (v5.9.18 DDD Layout)

```
src/core/ai_manager.py (Universal Cloud Mesh, v5.9.18)
  └── config.settings

talos.py (Rich TUI Master)
  ├── src.ai.llm.model_manager
  ├── src.analysis.graphify_adapter
  ├── src.ai.testing.red_tester
  └── subprocess → src/*/*.py

src/api/main_api.py (FastAPI Facade :8001)
  ├── src.core.database_manager
  ├── src.core.ai_manager
  ├── src.api.synapse_routes
  └── src.api.red_tester_routes

src/ai/drl/talos_live_agent.py (CLI entry)
  ├── src.ai.drl.drl_agent
  ├── src.core.ai_manager
  ├── src.ai.drl.talos_env
  ├── src.ai.drl.live_agent_sources
  └── src.ai.drl.live_agent_orchestrator

src/ai/drl/drl_trainer.py
  ├── src.ai.drl.talos_env
  └── src.ai.drl.drl_agent

src/ai/optimizers/gwo_rl_optimizer.py
  ├── src.ai.drl.talos_env
  └── src.ai.drl.drl_agent

src/ingestion/daily_search.py / historic_search.py
  ├── src.core.database_manager
  ├── src.core.ai_manager
  └── src.ingestion.*

src/analysis/citation_analyzer.py
  ├── src.core.ai_manager
  ├── src.core.database_manager
  └── src.ingestion.semantic_scholar_source

src/analysis/graphify_adapter.py
  └── vendor.graphify

src/integration/synapse_client.py
  └── requests

src/mcp_server.py
  └── requests

src/utils/logger.py (Enterprise Logging)
  ├── rich.logging
  └── logging.handlers
```

---

## 8. Module Descriptions

| Module | File | Description |
|--------|------|-------------|
| **TALOS** | `talos.py` | Main entry point — CLI menu and script launcher |
| **Query Translator** | `scripts/query_translator.py` | Translates research goals into optimized API queries and system prompts |
| **Knowledge Path Generator** | `scripts/knowledge_path_generator.py` | Generates structured reading paths with clustering and AI synthesis |
| **Citation Network Analyzer** | `scripts/citation_analyzer.py` | Builds interactive citation network graphs from DOI input |
| **Metadata Enricher** | `scripts/metadata_enricher.py` | Enriches paper records with external metadata (OpenAlex, Crossref, DBLP, Semantic Scholar) |
| **Grey Literature Miner** | `scripts/grey_literature_miner.py` | Performs horizon scanning for grey literature via Gemini Search Grounding |
| **Interactive Dashboard** | `scripts/interactive_dashboard.py` | Flask web dashboard with Tabulator.js for real-time database exploration |
| **PDF Downloader** | `scripts/pdf_downloader.py` | Downloads Open Access PDFs via Unpaywall API with multi-threaded batch support |
| **Autonomous Research Service** | `scripts/talos_service.py` | 24/7 background research daemon with Telegram/Discord/Email notifications |
| **MCP Server** | `src/mcp_server.py` | Native MCP (Model Context Protocol) stdio server που εκθέτει 4 tools (system_status, semantic_search, paper_details, trigger_scrape) μέσω MCPServer v2.0.0. Decoupled αρχιτεκτονική: τα tools καλούν το FastAPI backend μέσω HTTP. |
| **Enterprise Logger** | `src/utils/logger.py` | Central `get_logger(name)` factory -- `rich.logging.RichHandler` console + `RotatingFileHandler` to `data/logs/talos_system.log` (10 MB, 5 backups) |

---

## 9. Βοηθητικά Αρχεία

| Αρχείο | Ρόλος |
|--------|-------|
| **docs/** | Μόνιμη τεκμηρίωση (CHANGELOG, ROADMAP, TIMELINE, PROJECT_MAP, SYSTEM_CAPABILITIES, TECH_RADAR) |
| **docs/internal/** | Ιδιόκτητα έγγραφα (API_HANDOVER, UX_UI_BLUEPRINT, IP_PROTECTION) |
| **docs/generated/** | Αυτόματα παραγόμενα docs (ανά γλώσσα, από generate_docs.py) |
| **tools/** | Dev & utility scripts (_bump_docs.py, _fix_changelogs.py) |
| `Dockerfile`, `docker-compose.yml` | Containerization |
| `README.md`, `CHANGELOG_EN.md`, `CHANGELOG_GR.md`, `ROADMAP.md` | Documentation (root) |
| `CITATION.cff`, `LICENSE` | Metadata |

---

## 10. Known Gotchas & Conventions

1. **Greek comments** break editor text matching
2. **`.env` values χωρίς quotes** — load_dotenv δεν αφαιρεί quotes
3. **`daily_search.py` και `historic_search.py`** πρέπει να συγχρονίζονται για dedup
4. **4-layer framework** (strategic, operational, tactical, playground) είναι INVARIANT
5. **`recommender.py`** διαβάζει SQLite απευθείας, όχι μέσω DatabaseManager
6. **Circuit breaker** στα 5+ failures
7. **Profile-aware**: DatabaseManager δέχεται `db_path`
8. **Questionary stdin piping** μέσω `TALOS_GUI_STDIN` + `_gui_runner.py`
9. **Subprocess env propagation**: `run_script()` προωθεί TALOS_* vars
10. **Embeddings** ως pickled numpy arrays σε BLOB column
11. **Source class names** έχουν mixed conventions (DBLPSource, IEEEXploreSource, OpenAlexSource) — χρήση `live_agent_sources.import_source_class()` που σκανάρει το module
12. **Cooldown mechanism** (v3.1): negative reward → 5-step lockout → random override — αποτρέπει Deterministic Loops
13. **`.gitignore` & `docs/`**: Το blanket `docs/` rule αγνοεί όλα τα αρχεία εκτός από αυτά με `!` negate pattern (`!docs/PROJECT_MAP*.md`). Αν προσθέσεις νέο μόνιμο doc στο docs/, πρέπει να προσθέσεις και το αντίστοιχο `!` στο `.gitignore`.
14. **`tools/` path awareness**: Τα scripts στο `tools/` χρησιμοποιούν `os.chdir(os.path.join(os.path.dirname(__file__), '..'))` για να βρίσκουν το project root. Αν μετακινηθούν αλλού, πρέπει να ενημερωθεί το path.

---

> **Τελευταία ενημέρωση:** 2026-08-14 (v5.9.18 -- Καθολικό Πλέγμα Νέφους & Επέκταση Πολυπαρόχου Εφεδρείας)
> **Έκδοση Project:** v5.9.18
> **Συνολικά αρχεία που καλύπτονται:** 75+ (62 src/ + 3 integration/ + 10 root entry/config/docs/tests + 1 testing/)
>
> ### Νέο στην v5.9.9: Ενοποίηση Αναφορών
> - **Όλες οι αναφορές** πλέον αποθηκεύονται στο **`data/reports/`** (όχι στη ρίζα `reports/`).
> - Τα υποσυστήματα αναφορών (`reports/audits/`, `reports/authors/`, `reports/citations/`, `reports/general/`, `reports/general_status_report/`, `reports/grey_literature/`, `reports/knowledge_paths/`, `reports/recommendations/`, `reports/trends/`) μεταφέρθηκαν όλα στο `data/reports/`.
> - **8 scripts ανάλυσης** (`src/analysis/`) ενημερώθηκαν για να γράφουν στο `data/reports/`.
> - Ο **Αυτόνομος Κόκκινος Ελεγκτής** (`red_tester.py`) γράφει στο `data/reports/red_tester/`.
> - Το REST API `red_tester_routes` διαβάζει από `data/reports/red_tester/`.
> - Ολόκληρος ο κατάλογος root `reports/` διαγράφηκε -- καθαρή ρίζα έργου.
