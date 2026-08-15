# PROJECT_MAP_EN.md -- Complete Project TALOS Map v5.10.3

> **Purpose:** This file is the "memory" of the project. It is mandatory reading for every new chat so the AI agent knows exactly what exists, where, and how it connects -- without re-reading all files.
>
> **Rule:** After ANY code change (new function, modified signature, new/deleted file), this file MUST be updated.
>
> **Last Updated:** 2026-08-14 (v5.10.3 -- Hierarchical DRL Orchestration: Daemon & Foraging Sub-Agent Integration)

---

## 1. Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER INTERFACES                          │
│  talos.py (CLI menu)          app.py (Streamlit Web GUI)        │
│  _gui_runner.py (wrapper)     templates/dashboard.html (Flask)  │
└──────────────────────────┬──────────────────────────────────────┘
                           │ subprocess / direct import
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                    SCRIPTS (21 files)                           │
│  talos_live_agent.py (thin entry, v3.1 cooldown)                │
│  daily_search.py          historic_search.py                    │
│  knowledge_path_generator.py                                    │
│  citation_analyzer.py              recommender.py               │
│  grey_literature_miner.py          query_translator.py          │
│  author_profiler.py      author_trajectory_analyzer.py          │
│  db_stats.py    data_enricher.py    embedding_generator.py      │
│  metadata_enricher.py               model_manager.py            │
│  pdf_downloader.py      profile_manager.py                      │
│  recalculate_scores.py  reevaluate_database.py                  │
│  trend_analyzer.py      zotero_connector.py                     │
│  interactive_dashboard.py          api_health_check.py          │
│  migrate_database_schema.py                                     │
│  generate_docs.py                                               │
└──────────────────────────┬──────────────────────────────────────┘
                           │ import
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                    CORE MODULES (7 files)                       │
│  ai_manager.py          database_manager.py        hardware.py  │
│  drl_agent.py           talos_env.py                            │
│  live_agent_sources.py  live_agent_orchestrator.py              │
│  (Multi-provider LLM)   (SQLite + Embeddings)     (GPU detect)  │
│  (DDQN Agent)           (Gym Env)  (Source Disc) (Live Loop)    │
└──────────────────────────┬──────────────────────────────────────┘
                           │ import
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                    SOURCES (16 APIs)                            │
│  arxiv  elsevier  semantic_scholar  ieee  springer  openalex    │
│  dblp  core  crossref  openarchives  pubmed  scigov  osti  plos │
│  openreview  openaire                                           │
│                                                                 │
│  Standardized output: {doi, url, title, authors_str,            │
│                        publication_year, abstract, source}      │
└──────────────────────────┬──────────────────────────────────────┘
                           │ HTTP requests
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                    EXTERNAL APIs & SERVICES                     │
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

### 2.0 `core/talos_env.py` — Gymnasium Environment (v3.2, 16-source / 23-dim scaling)

**v3.1 (Batch 1 audit):** The 200-step cutoff is now reported as `truncated=True` (not `terminated`) per Gymnasium time-limit semantics, so Bellman targets bootstrap across the artificial cutoff.

**v3.2 (v5.10.1):** Environment scaled to a **23-dimensional state space** (1 hour + 16 source ratios + 2 streaks + 4 provider ratios) and a **17-action space** (16 sources + sleep). `_load_source_list()` guarantees `openreview` and `openaire` are present.

**Role:** RL environment for API source selection. **V2.1:** Fixed hour normalization `/23.0` → `/24.0`. **v3.0:** Provider-aware observation — state vector includes 4 provider ratios (gemini, deepseek, huggingface, local) for the DRL agent.

**Module-level constants:**
- `_PROVIDER_NAMES` = ["gemini", "deepseek", "huggingface", "local"]
- `_PROVIDER_COUNT` = 4

| Method | Signature | Description |
|--------|-----------|-------------|
| `_load_source_list` | `(config=None) -> list` | Reads source list from config.json (source_names or auto-detect from _query keys). |
| `_try_load_config` | `() -> dict or None` | Loads config.json from project root. |
| `_load_source_limits` | `(source_names, config=None) -> np.ndarray` | Reads per-source API limits from config. |
| `__init__` | `(self, source_names=None, source_limits=None, config=None)` | Dynamic init with N sources. Obs size = 1 + N + 2 + 4 (providers) = 23 for 16 sources. |
| `reset` | `(seed=None, options=None) -> (obs, info)` | Resets all counters. |
| `step` | `(action) -> (obs, reward, terminated, truncated, info)` | Executes action. Actions 0..N-1 = query source, N = sleep. |
| `_build_obs` | `() -> np.ndarray` | v3.2: [hour/24, 16 usage_ratios..., low/10, err/10, 4 provider ratios] — 23 dimensions. |
| `get_default_state_space` | `() -> int` | v3.2: 23 (1 + 16 + 2 + 4). |
| `get_default_action_space` | `() -> int` | v3.2: 17 (16 sources + 1 sleep). |

### 2.1 `core/ai_manager.py` — Class `AIManager` (v3.9)

**v3.7 (Batch 1 audit):** New attribute `last_provider_used` — set on every successful `_execute_request()` with the name of the provider that actually served the request. Consumed by the live orchestrator for correct provider attribution.
**v3.8 (Batch 3 hotfix):** Implemented `analyze_generic_text(full_prompt) -> str|None` — it was documented in this map and called by grey_literature_miner.py, but did NOT exist in the code (AttributeError). Thin wrapper around `_execute_request(model_type='pro', response_format='text')`.

**Role:** Multi-provider LLM interface with circuit breaker pattern. Manages 9 providers via the Universal Cloud Mesh (v5.9.18): Gemini (Google GenAI SDK, non-OpenAI) + 8 OpenAI-compatible redundancy providers (NVIDIA NIM, Groq, Cerebras, GitHub Models, Mistral, OpenRouter, DeepSeek, HuggingFace) + Local/Ollama (offline).

| Method | Signature | Description |
|--------|-----------|-------------|
| `__init__` | `(self, config: Dict[str, Any])` | Initializes all providers from config + .env via `OPENAI_COMPATIBLE_REGISTRY`. Sets provider_priority, FAILURE_THRESHOLD. |
| `_clean_json_string` | `(self, text: str) -> str` | Extracts clean JSON from LLM response. |
| `evaluate_paper_json` | `(self, paper_content: str, model_type: str = 'pro', system_prompt_override: str = None) -> Union[Dict, None]` | Evaluates paper with AI, structured JSON. |
| `analyze_generic_text` | `(self, full_prompt: str) -> str` | Analyzes arbitrary text. |
| `_execute_request` | `(self, prompt: str, model_type: str, response_format: str = 'text') -> Union[Dict, str, None]` | Multi-provider request with 2D Execution Matrix routing. |
| `_execute_cloud_chain` | `(self, prompt: str, model_type: str, response_format: str) -> Union[Dict, str, None]` | Routes through `provider_priority` (Universal Cloud Mesh), skipping unconfigured/open-circuit providers. |
| `_execute_openai_compatible_request` | `(self, provider_name: str, prompt: str, model_type: str, response_format: str) -> Union[Dict, str, None]` | Unified OpenAI-compatible provider handler with circuit breaker. |
| `_handle_failure` | `(self, provider_name: str)` | Increments failure counter, opens circuit at 5+. |

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

**Role:** Source discovery and dynamic import for the TALOS Live DRL Agent. Scans config.json for `_query` keys, imports source classes by scanning modules for any class ending in "Source" (handles mixed naming: DBLP→DBLPSource, IEEE→IEEEXploreSource, etc.).

| Function | Signature | Description |
|----------|-----------|-------------|
| `import_source_class` | `(source_name: str) -> class or None` | Dynamic import with auto-detect class (searches for *Source). |
| `build_source_map` | `(source_names: list) -> (dict, list)` | DENSE action mapping: {0: (name, cls), ...}. Also returns the list of working source names. |

### 2.3 `core/live_agent_orchestrator.py` — Main Loop + Cooldown (v1.1, Batch 1 audit)

**v1.1 fixes:** (1) `LOW_SCORE_MAX` 20 → 10 so streak normalization matches the training env (/10) — eliminates train/inference distribution mismatch. (2) `evaluate_paper()` now credits the provider that ACTUALLY answered (`ai_manager.last_provider_used`), not always "gemini".

**Role:** Core orchestration loop for the TALOS Live DRL Agent. Handles state calculation, action selection, API fetch, AI evaluation, reward, counters, and provider tracking. **v3.1 Cooldown:** `active_cooldowns` dict prevents deadlocks — actions with negative reward get 5-step lockout, overridden by random free action.

| Function | Signature | Description |
|----------|-----------|-------------|
| `_get_provider_limits` | `(config: dict) -> dict` | Reads per-provider limits with tier-based Gemini. |
| `calculate_state` | `(...) -> np.ndarray` | v3.0 Provider-Aware state: 1 + N_sources + 2 + 4. |
| `execute_live_fetch` | `(action, action_map, config) -> tuple` | Executes ONE live API call. |
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

**Role:** Pluggable neural network architectures for the DRL agent. **v1.0:** Contains `DuelingLSTM` — 3-layer LSTM with dueling heads (V + A). Designed for future architectures (Transformer, xLSTM) via a common `(input_dim, output_dim)` interface.

| Class | Signature | Description |
|-------|-----------|-------------|
| `DuelingLSTM` | `__init__(input_dim, output_dim)` | 3-layer LSTM (128→64→32) with LayerNorm + dueling heads. `forward(state) -> Q-values`. |

### 2.5 `core/drl_agent.py` — DRL Agent (v2.2, Pluggable Network)

**Role:** Double Dueling DQN agent. **V2.2:** `network_class` parameter — any network from `drl_networks.py` can be injected. Save/load includes network class name for correct reconstruction.

**Hyperparameters (GWO-optimized v2.0):** `LR=3.361e-05`, `GAMMA=0.6983`, `EPS_DECAY=0.9202` (80 iters, 9.5h, fitness -2353.0).

**Class `TalosDRLAgent`:**
| Method | Signature | Description |
|--------|-----------|-------------|
| `__init__` | `(state_dim=None, action_dim=None, network_class=None)` | v2.2: `network_class` param (default: DuelingLSTM). |
| `act` | `(state, eps=0.0) -> int` | ε-greedy action selection. |
| `learn` | `()` | DDQN learning step. |
| `save` | `(path)` | Saves weights + metadata **including** `network_class` name. |
| `load` | `(path)` | v2.2: Resolves network class from saved metadata, uses DuelingLSTM as fallback. |

**Hyperparameters (GWO-optimized v2.0):**
- `LR = 3.361e-05` (GWO-optimized learning rate)
- `GAMMA = 0.6983` (GWO-optimized discount factor)
- `EPS_DECAY = 0.9202` (GWO-optimized epsilon decay, in drl_trainer.py)
- `TAU = 1e-3`, `MEMORY_LEN = 10000`, `BATCH_SIZE = 200`

### 2.6 `core/notifier.py` — Class `TalosNotifier` (v1.0, ~202 lines)

**Role:** Multi-channel notification system (Telegram, Discord, Email).

### 2.7 `core/database_manager.py` — Class `DatabaseManager` (v4.8.5, 569 lines)

**Role:** SQLite database layer with embeddings, semantic search, profile-aware.

### 2.8 `core/hardware.py` (v4.8.5, 429 lines)

**Role:** GPU VRAM detection, Ollama model recommendations.

### 2.9 `templates/gui_theme.css` — Academic Theme CSS (v5.3.3)

**Role:** Light-only CSS theme for the Streamlit Web GUI (dark mode removed in v5.3.3). **CSS variables injected by `app.py:render_css()`** — academic blue/teal palette with glassmorphism cards, custom scrollbar, and professional typography.

### 2.10 `templates/gui_strings.py` — Translation System (v5.3.3)

**Role:** Translation strings in English + Greek for the Streamlit GUI. Exports `STR` dict and `t(key, en_default="")` function. Dark theme toggle string removed in v5.3.3.

---

## 3. Entry Points

### 3.1 `talos.py` (v5.3.6 — TUI Hardening)
CLI entry point with interactive menu. **v5.3.6 (Batch 2 TUI audit):** New `safe_pause()` (Ctrl+C at "Press Enter" prompts returns to menu); `safe_select()` catches KeyboardInterrupt → None; fixed duplicate "6." in System Diagnostics (dead "Baseline Report (Standard)" branch — menu renumbered 1-10); bare `except:` → `except Exception:`; `TALOS_VERSION` constant in header; top-level guard with `sys.exit(0)`.

### 3.2 `app.py` (v5.3.3, ~940 lines)
Streamlit Web GUI — light-only theme (dark mode removed in v5.3.3).

### 3.3 `_gui_runner.py`
Wrapper for Streamlit stdin piping.

### 3.4 `start_talos.bat`
Batch script for launching Streamlit GUI.

---

## 4. Scripts (21 files)

### 4.1 Search Scripts
- `daily_search.py` (v5.4) — Daily search across 16 APIs
- `historic_search.py` (v5.5) — Deep archive search
- `grey_literature_miner.py` (v2.1) — Grey literature with Gemini Search Grounding. **v2.1 (Batch 3):** `ddgs` import with fallback to legacy `duckduckgo_search`; missing GEMINI_API_KEY is no longer fatal (runs on AIManager fallback + DuckDuckGo grounding).

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
**Purpose:** Training script with GWO-optimized hyperparameters. **v1.1:** `EPS_DECAY=0.9415` (GWO), saves as `dddqn_trained.pth`. **v1.2:** Fixed fatal `NameError` (`args.episodes` → `episodes` in interactive mode); stores `done=terminated` only (truncation still bootstraps). **v1.3 (Batch 2, presentation only):** Ctrl+C mid-training → saves partial model to `models/dddqn_partial.pth` + clean exit(0); single-line `\r` progress ticker between 50-episode summaries; Ctrl+C guards at prompt and top level.

#### `scripts/gwo_foraging_hyperparameter_tuner.py` (v2.1 — GWOForagingHyperparameterTuner)
**Purpose:** GWO hyperparameter tuning (renamed from `gwo_rl_optimizer.py` in v5.10.2). **v2.0 (Batch 1 audit):** (1) `calculate_fitness()` now ACTUALLY trains the agent (store + learn + decayed epsilon) and measures fitness in a separate greedy evaluation phase (`EVAL_EPISODES=5`) — previously fitness was pure noise (eps=1.0, no learn()). (2) `update_wolf_position()` follows canonical GWO (Mirjalili 2014): fresh r1/r2/A/C per alpha/beta/delta term. (3) Fitness values cached per iteration — `_build_history_entry()` receives `fitness_values` instead of re-evaluating. **v2.1:** added `GWOForagingHyperparameterTuner` class facade; export renamed to `models/gwo_foraging_hyperparameters.json`.
**Functions:** `main()`, `run_gwo()`, `calculate_fitness()`, `find_best_three_wolves()`, `update_wolf_position()`, `GWOForagingHyperparameterTuner.optimize()`.
**Imports:** `core.talos_env.TalosEnv`, `core.drl_agent`

#### `src/ai/drl/llm_router_subagent.py` (v5.10.3 — LLM Router Sub-Agent)
**Purpose:** `LLMRouterSubAgent` selects the optimal active provider for an inference request. Loads reward weights from `models/gwo_llm_router_reward_weights.json` (Pareto fallback), evaluates prompt token length, rate-limit status, and latency against a static `PROVIDER_PROFILES` table, and returns the provider maximizing `R = w_q*Quality - w_l*Latency - w_c*Cost - w_p*Penalty`. Integrated into `AIManager`. v5.10.3: added the `foraging_evaluation` task modifier and the shared `estimate_prompt_tokens()` helper; now invoked directly by the live DRL foraging orchestrator, the 24/7 daemon, and the search pipelines.
**Functions:** `LLMRouterSubAgent` (`select_provider()`, `estimate_signals()`, `score_provider()`, `load_weights()`, `set_weights()`), module-level `estimate_prompt_tokens()`.
**Imports:** `numpy`, `json`

#### `src/ai/optimizers/gwo_llm_router_reward_shaper.py` (v5.10.2 — Bi-Level Reward Shaping)
**Purpose:** `GWOLLMRouterRewardShaper` bi-level multi-objective optimizer for the LLM Router reward weights `[w_quality, w_latency, w_cost, w_penalty]` (simplex-projected). Outer GWO loop + inner router evaluation under `R = w_q*Quality - w_l*Latency - w_c*Cost - w_p*Penalty`. Exports `models/gwo_llm_router_reward_weights.json`.
**Functions:** `GWOLLMRouterRewardShaper` (`optimize()`, `_evaluate_router()`, `_update_position()`, `export()`, `run()`), `main()`.
**Imports:** `numpy`, `json`, `argparse`

#### `scripts/talos_live_agent.py` (v3.2 — Batch 2 TUI hardening)
**Purpose:** Thin entry point. **v3.1:** epsilon=0.05, 5-step cooldown for negative-reward actions, ASCII output. Delegates to `core.live_agent_orchestrator.run_live_loop()`. **v3.2:** argparse (`--verbose`, `--help`) replaces ad-hoc sys.argv scanning; formatted startup summary table; top-level KeyboardInterrupt guard (clean exit(0) on Ctrl+C during startup).
**Functions:** `_parse_args()`, `main()` — config load, source discovery, model load, run loop.
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

## 5. Sources (16 APIs)

| Source | File | API Key | Query Key |
|--------|------|---------|-----------|
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
| OpenAIRE | `openaire.py` | Optional | `openaire_query` |
| OpenReview | `openreview.py` | Optional | `openreview_query` |

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
  "<source>_query": "...",     // 16 queries (all 16 sources)
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

## 7. Dependency Graph (v5.10.0 DDD Layout)

```
src/core/ai_manager.py (Universal Cloud Mesh, v5.9.18)
  ├── config.settings
  └── src.ai.drl.llm_router_subagent

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

src/ai/drl/llm_router_subagent.py
  └── numpy

src/ai/optimizers/gwo_foraging_hyperparameter_tuner.py
  ├── src.ai.drl.talos_env
  └── src.ai.drl.drl_agent

src/ai/optimizers/gwo_llm_router_reward_shaper.py
  ├── src.ai.drl.llm_router_subagent
  └── numpy

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
| **MCP Server** | `src/mcp_server.py` | Native MCP (Model Context Protocol) stdio server exposing 4 tools (system_status, semantic_search, paper_details, trigger_scrape) via MCPServer v2.0.0. Decoupled architecture: tools delegate to FastAPI backend via HTTP. |
| **Enterprise Logger** | `src/utils/logger.py` | Central `get_logger(name)` factory -- `rich.logging.RichHandler` console + `RotatingFileHandler` to `data/logs/talos_system.log` (10 MB, 5 backups) |

---

## 9. Auxiliary Files

| File | Role |
|------|------|
| **docs/** | Permanent documentation (CHANGELOG, ROADMAP, TIMELINE, PROJECT_MAP, SYSTEM_CAPABILITIES, TECH_RADAR) |
| **docs/internal/** | Proprietary documents (API_HANDOVER, UX_UI_BLUEPRINT, IP_PROTECTION) |
| **docs/generated/** | Auto-generated docs (per language, from generate_docs.py) |
| **tools/** | Dev & utility scripts (_bump_docs.py, _fix_changelogs.py) |
| `Dockerfile`, `docker-compose.yml` | Containerization |
| `README.md`, `CITATION.cff`, `LICENSE` | Metadata |

---

## 10. Known Gotchas & Conventions

1. **Greek comments** break editor text matching
2. **`.env` values without quotes** — load_dotenv doesn't strip quotes
3. **`daily_search.py` and `historic_search.py`** must be kept in sync for dedup logic
4. **4-layer framework** (strategic, operational, tactical, playground) is INVARIANT
5. **`recommender.py`** reads SQLite directly, not via DatabaseManager
6. **Circuit breaker** at 5+ failures
7. **Profile-aware**: DatabaseManager accepts `db_path`
8. **Questionary stdin piping** via `TALOS_GUI_STDIN` + `_gui_runner.py`
9. **Subprocess env propagation**: `run_script()` forwards TALOS_* vars
10. **Embeddings** as pickled numpy arrays in BLOB column
11. **Source class names** have mixed conventions (DBLPSource, IEEEXploreSource, OpenAlexSource) — use `live_agent_sources.import_source_class()` which scans the module
12. **Cooldown mechanism** (v3.1): negative reward → 5-step lockout → random override — prevents Deterministic Loops

---

> **Last Updated:** 2026-08-14 (v5.10.3 -- Hierarchical DRL Orchestration: Daemon & Foraging Sub-Agent Integration)
> **Project Version:** v5.10.3
> **Total Files Covered:** 75+ (62 src/ + 3 integration/ + 10 root entry/config/docs/tests + 1 testing/)
>
> ### New in v5.9.9: Report Path Consolidation
> - **All reports** now stored under **`data/reports/`** (no longer at root `reports/`).
> - Report subsystems (`reports/audits/`, `reports/authors/`, `reports/citations/`, `reports/general/`, `reports/general_status_report/`, `reports/grey_literature/`, `reports/knowledge_paths/`, `reports/recommendations/`, `reports/trends/`) all moved to `data/reports/`.
> - **8 analysis scripts** (`src/analysis/`) updated to write to `data/reports/`.
> - **Autonomous Red Tester** writes to `data/reports/red_tester/`.
> - REST API `red_tester_routes` reads from `data/reports/red_tester/`.
> - Root `reports/` directory deleted -- clean project root.
