# Changelog - Project TALOS

All notable changes to the TALOS project will be documented in this file. The project adheres to [Semantic Versioning](https://semver.org/).


## [v5.2.0] - 2026-07-04 — The "Onboarding & Dynamic Orchestration" Update

This release transforms TALOS into a **fully guided research platform** with a first-run onboarding wizard, research pivot workflow, and a fundamentally upgraded DRL stack that now supports **ALL 14 academic sources dynamically** (not just the original 3). **8 files changed, 1 new file, ~2,000 lines of code added/refactored.**

---

### `app.py` v5.2.0 — Onboarding Wizard & Research Pivot (from v4.11.0, ~1022 → ~1400 lines)

**WHY:** Before v5.2.0, TALOS had no guided onboarding — new users had to know about PYTHIA, profiles, and the 14-source architecture before they could use the system. There was no GUI-based way to create a profile or recalibrate when research interests shifted. This was a major UX gap compared to professional research tools (Zotero, ResearchRabbit, Elicit).

**WHAT changed — New functions added:**

| Function | Signature | Description |
|----------|-----------|-------------|
| `render_onboarding_wizard()` | `() -> None` | Renders a 4-step Streamlit wizard: (1) Profile Name, (2) Research Domain description, (3) PYTHIA AI configuration with inline editing of generated queries/prompts, (4) Review & Launch with optional historic search and daemon start. Uses `st.session_state.onboarding_step` for navigation, progress bar for visual feedback. |
| `_is_first_run()` | `() -> bool` | Returns `True` if no `_profiles/active_profile.txt` exists or no profiles are found. Called before the normal dashboard renders — if True, the wizard takes over the entire page via `st.stop()`. |

**WHAT changed — New UI sections:**
- **Research Pivot** section in Profile & Settings → Profiles tab: text area for new research direction + "Start Research Pivot" button that triggers PYTHIA regeneration via subprocess, with step-by-step guidance for re-evaluation and retraining.
- **Imports added:** `scripts.profile_manager` (6 functions: PROFILES_DIR, ROOT_DIR, ensure_profiles_dir, set_active_profile_name, save_current_state_to_profile, load_profile_to_root), `scripts.query_translator.flatten_json`, `shutil`, `socket`, `webbrowser`, `traceback`.

**WHAT changed — Navigation:**
- **Sidebar expanded:** 7 → 8 pages (added "🧠 DRL Agent Dashboard" as separate page).
- **Version bumped:** `v4.11.0` → `v5.2.0` in sidebar header, footer, and docstring.

---

### `core/talos_env.py` v2.0 — Dynamic N-Source Environment (from v1.0, ~303 → ~380 lines)

**WHY:** The original `TalosEnv` hardcoded exactly 3 sources (ArXiv, OpenAlex, Semantic Scholar) with 4 actions (3 query + 1 sleep). This meant the DRL agent could only learn to route between these 3 APIs — ignoring the other 11 sources TALOS supports. To scale the agent to all 14 sources, the environment needed to become dynamic.

**⚠️ BREAKING CHANGES (3):**
1. Observation space: hardcoded `Box(6,)` → dynamic `Box(1 + N + 2,)` where N = number of sources. Structure: `[hour/23, usage_ratio_0, ..., usage_ratio_N-1, low_streak/10, error_streak/10]`.
2. Action space: hardcoded `Discrete(4)` → dynamic `Discrete(N + 1)` where N = number of sources. Sleep action = index N (was hardcoded 3).
3. Internal state: removed individual `self.arxiv_calls`, `self.openalex_calls`, `self.s2_calls` attributes. Replaced with parallel numpy arrays: `self.source_calls` (shape N) and `self.source_limits` (shape N).

**Migration guide:** Old code referencing `env.arxiv_calls`, `action == 3` (sleep), or 6-element observations must be updated. New code should use `env.source_calls[idx]`, `action == env.SLEEP_ACTION`, and the dynamic observation length.

**WHAT changed — New module-level functions:**

| Function | Signature | Description |
|----------|-----------|-------------|
| `_load_source_list(config)` | `(dict or None) -> list[str]` | Reads source names from config in 3-tier priority: (1) explicit `source_names` key, (2) auto-detect from `_query` keys, (3) fallback to `["arxiv", "openalex", "semantic_scholar"]`. |
| `_try_load_config()` | `() -> dict or None` | Loads `config.json` from project root with graceful JSONDecodeError handling. |
| `_load_source_limits(source_names, config)` | `(list, dict) -> np.ndarray` | Reads per-source limits from `config.json` (`<source>_limit` keys), defaults to 100. |
| `get_default_state_space()` | `() -> int` | Returns `1 + len(sources) + 2` — the observation vector size for the default source count. |
| `get_default_action_space()` | `() -> int` | Returns `len(sources) + 1` — the action count (N sources + sleep). |

**WHAT changed — Class `TalosEnv` constructor:**
- `TalosEnv(source_names=None, source_limits=None, config=None)` — all parameters optional. If `source_names` is None, auto-detected from config.
- Deduplication of source names while preserving order.
- `self.SLEEP_ACTION = self.num_sources` — dynamically computed sleep index.
- New attributes: `source_names` (list), `num_sources` (int), `source_limits` (np.ndarray), `source_calls` (np.ndarray).

**WHAT changed — Method `step(action)`:**
- Old: massive `if action == 3: ... elif action == 0: ... elif action == 1: ... elif action == 2: ...` chain.
- New: `if action == self.SLEEP_ACTION: ... elif 0 <= action < self.num_sources: source_name = self.source_names[action]; ...` — clean generic loop.
- Reward logic IDENTICAL: +20 score≥8, +5 score=7, -10 score<7, -50 API error, +2 sleep when max usage > 80%.
- Info dict now includes `"source": source_name` in addition to `"action"` and `"score"`.

**WHAT changed — Backward compatibility:**
- Properties `arxiv_limit`, `openalex_limit`, `s2_limit` still exist — they look up the named source in `self.source_names` and return its limit.
- `_simulate_score()` and `_score_to_reward()` unchanged.

---

### `core/drl_agent.py` v2.0 — Dynamic Agent (from v1.1, ~393 → ~320 lines)

**WHY:** The original agent had hardcoded `STATE_SPACE = 6` and `ACTION_SPACE = 4` at module level. With the dynamic environment supporting N sources, the agent needed to adapt its neural network input/output dimensions at construction time. Additionally, saved models had no metadata — loading a 3-source model on a 14-source config would silently fail or produce wrong results.

**WHAT changed — Module-level constants:**
- `STATE_SPACE` and `ACTION_SPACE` are now computed dynamically at import time: `STATE_SPACE = get_default_state_space()`, `ACTION_SPACE = get_default_action_space()`. Fallback to (6, 4) if import fails.
- ALL hyperparameters unchanged: `LR=1e-4`, `GAMMA=0.8`, `TAU=1e-3`, `BATCH_SIZE=200`, etc.

**WHAT changed — Class `DuelingLSTM`:**
- Constructor: `DuelingLSTM(input_dim, output_dim)` — both parameters passed at construction, no longer relying on module-level constants. The LSTM layers now accept `input_size=input_dim` for the first layer and output `output_dim` Q-values from the advantage head.

**WHAT changed — Class `TalosDRLAgent`:**
- Constructor: `TalosDRLAgent(state_dim=None, action_dim=None)` — when None, uses module-level defaults. Stores `self.state_dim`, `self.action_dim`, and `self.source_names` (loaded from `talos_env._load_source_list()`).

**WHAT changed — Method `save(path)`:**
- Old format: `T.save(self.actor_online.state_dict(), path)` — raw `OrderedDict`.
- New format: `T.save({"state_dim": ..., "action_dim": ..., "source_names": ..., "weights": ...}, path)` — dict with metadata.

**WHAT changed — Method `load(path)`:**
- Detects old vs new format: checks if loaded data is a dict with `"weights"` key.
- Extracts metadata: `state_dim`, `action_dim`, `source_names` from the saved dict.
- If dimensions don't match existing networks, **re-creates** both `actor_online` and `actor_target` with the correct `DuelingLSTM(input_dim, output_dim)`, re-creates the optimizer, then loads weights via `load_state_dict()`.
- This enables loading a 3-source model on a 14-source config (and vice versa) — a warning should be printed but the code handles it.

---

### `scripts/talos_service.py` v2.0 — Profile-Aware Daemon (from v1.1, ~472 → ~430 lines)

**WHY:** The v1.1 daemon had 4 hardcoded issues: (1) `action == 3` for sleep, (2) `{0: "ArXiv", 1: "OpenAlex", 2: "S2"}` for source names, (3) always loaded model from `models/dddqn_trained.pth` ignoring profiles, (4) agent created with default dimensions that might not match the environment. This meant the daemon couldn't adapt when the user switched profiles or when sources changed.

**WHAT changed — Initialisation:**
- Reads active profile from `_profiles/active_profile.txt` at startup, displays profile name in header.
- Creates `OfflineTalosEnv()` FIRST to get the actual `num_sources` and `SLEEP_ACTION`.
- Creates agent with: `TalosDRLAgent(state_dim=env.observation_space.shape[0], action_dim=env.action_space.n)`.
- Model loading: checks `_profiles/<name>/models/dddqn_trained.pth` first, then global `models/dddqn_trained.pth` as fallback.

**WHAT changed — Main loop:**
- `action == 3` → `action == sleep_action` (where `sleep_action = env.SLEEP_ACTION`).
- `action_name = {0: "ArXiv", 1: "OpenAlex", 2: "S2"}.get(action, "?")` → `source_name = info.get("source", "unknown")`.
- Alert formatting: `format_paper_alert()` now uses dynamic source display names (`source.replace('_', ' ').title()`).

**WHAT changed — Version strings:**
- Header: `v5.0.0 (Phase 4)` → `v5.2.0`
- Weekly digest: `v5.0.0` → `v5.2.0`

---

### `scripts/talos_live_agent.py` v2.0 — Dynamic N-Source Live Agent (from v1.0, ~409 → ~390 lines)

**WHY:** The v1.0 live agent had hardcoded imports for exactly 3 source classes (`ArxivSource`, `OpenAlexSource`, `SemanticScholarSource`) and a hardcoded 6-element state vector. It could only make real API calls to those 3 sources. For the agent to orchestrate all 14 sources, every hardcoded reference needed to be replaced with dynamic discovery.

**WHAT changed — New functions:**

| Function | Signature | Description |
|----------|-----------|-------------|
| `_import_source_class(source_name)` | `(str) -> class or None` | Dynamically imports `sources.<name>_source.<Name>Source` using `__import__()` and `getattr()`. Handles TitleCase conversion (e.g., `semantic_scholar` → `SemanticScholarSource`). Returns `None` with warning on import failure. |
| `_build_source_map(source_names)` | `(list[str]) -> dict` | Builds `{action_index: (source_name, SourceClass)}` dict for all importable sources. Sources that fail import are silently excluded. |

**WHAT changed — Modified functions:**
- `calculate_state()`: Signature changed from fixed 6-element array to dynamic `(normalized_hour, call_counts, source_limits, low_score_streak, error_streak, source_names)`. Returns `np.array([hour] + ratios + [low_norm, error_norm])`.
- `execute_live_fetch()`: Added `action_map` parameter (was using hardcoded `{0: ("ArXiv", ArxivSource), ...}`). Now returns 3-tuple `(papers, error, source_name)`.
- `main()`: Auto-detects sources via `_load_source_list(config)`, builds `action_map` via `_build_source_map()`, computes `sleep_action = len(source_names)`. Profile-aware model loading (same as daemon).

**WHAT changed — Removed imports:**
- Old: `from sources.arxiv_source import ArxivSource`, `from sources.openalex_source import OpenAlexSource`, `from sources.semantic_scholar_source import SemanticScholarSource`.
- New: `from core.talos_env import _load_source_list, _try_load_config` — no source-specific imports.

---

### `scripts/train_agent.py` — Dynamic Source Display (from v1.0, ~283 → ~290 lines)

**WHY:** The training script was unchanged in logic but needed to display dynamic source information so users know how many sources and what dimensions the agent is training with.

**WHAT changed:**
- Startup display: added source count, source names (truncated to first 5 if >5), observation dimension, and action dimension.
- Agent creation: `TalosDRLAgent()` → `TalosDRLAgent(state_dim=env.observation_space.shape[0], action_dim=env.action_space.n)`.
- Version string: `Database-Driven` → `Database-Driven (v5.2.0)`.

---

### `scripts/research_pivot.py` v1.0 — **NEW FILE** (~180 lines)

**WHY:** There was no automated workflow for users whose research interests shifted. They had to manually: (1) re-run PYTHIA via CLI, (2) remember to re-evaluate the database, (3) remember to retrain the agent, (4) manually save to profile. This script automates the entire pivot workflow.

**Functions:**

| Function | Signature | Description |
|----------|-----------|-------------|
| `get_active_profile_name()` | `() -> str` | Reads active profile from `_profiles/active_profile.txt`, defaults to "default". |
| `save_state_to_profile(profile_name)` | `(str) -> None` | Copies root `config.json` and `talos_research.db` into `_profiles/<name>/`. |
| `run_script(script_name, stdin_text, args)` | `(str, str, list) -> (int, str)` | Executes a TALOS script as subprocess with `TALOS_GUI_STDIN` piping. 30-minute timeout. |
| `main()` | `() -> None` | 5-step interactive wizard: (1) collect new direction, (2) run PYTHIA, (3) optionally re-evaluate DB, (4) optionally retrain agent with custom episode count, (5) save to profile. Supports `--auto` flag for GUI integration (reads from env var). |

**Imports:** `questionary`, `subprocess`, `shutil`, `sys`, `os`.

---

### Documentation Updates

**`PROJECT_MAP.md`:**
- Added Section 2.0: `core/talos_env.py` v2.0 with all 8 functions documented.
- Added Section 2.3: `core/notifier.py` (TalosNotifier — was completely undocumented before).
- Updated Section 2.2: `core/drl_agent.py` from v1.1 → v2.0 with new signatures.
- Updated Section 3.2: `app.py` from v4.10.1 → v5.2.0, pages 6 → 8, new functions table.
- Added new integration script docs: `scripts/drl_trainer.py`, `scripts/talos_live_agent.py` v2.0, `scripts/talos_service_api.py`, `scripts/research_pivot.py`.
- Last Updated: 2026-07-04, Version: v5.2.0, File count: 56.
- **Function audit improvement:** 166 → 183 matched (+17 newly documented functions).

**`.clinerules`:**
- Added "CRITICAL: Project Version & PROJECT_MAP.md Synchronization" rule — mandates map update after every .py change, overrides all other rules.
- Added "CRITICAL: Documentation Sync — CHANGELOG, README, ROADMAP" rule — mandates ultra-detailed changelog entries with exact filenames, signatures, and rationale after every significant change.

**`README.md`:** Version v5.0.0 → v5.2.0. Tagline updated to "Now with Guided Onboarding, Research Pivot & Dynamic 14-Source DRL Orchestration".

**`ROADMAP.md`:** v5.2.0 section updated from "In Progress" to "COMPLETED ✅" with detailed feature table covering Onboarding, DRL Stack, Documentation, and Files Changed.

---

**Total: 8 files changed, 1 new file, ~2,000 lines added/refactored**
**Integration test: 43/43 Python files pass `py_compile` validation**


## [v5.2.0] - 2026-07-04 — The Live Agent & PDF Downloader

This release wires the trained DRL agent to the live internet and adds multi-threaded PDF batch downloading.

### Added
- **`scripts/talos_live_agent.py` v1.0 (330 lines):** Live DRL inference engine  
  - Loads trained model (`models/dddqn_trained.pth`)  
  - Pure exploitation (ε=0.0) — agent uses ONLY learned policy  
  - Real-time state calculation: 6-element vector [hour, arxiv_ratio, openalex_ratio, s2_ratio, low_streak, error_streak]  
  - ONE live API call per loop iteration (ArXiv, OpenAlex, Semantic Scholar)  
  - AI evaluation via AIManager (Flash model) after each fetch  
  - Reward logic: +20 (score≥8), +5 (score≥7), -10 (score<7), -50 (429 error)  
  - Action 3 (Sleep): 1-hour cooldown, resets all counters  
  - Graceful 429 handling: exceptions caught, error streak incremented, -50 penalty  
- **TUI entry** (`talos.py` → Analysis Option 11): "Live DRL Agent (Real APIs)" with confirmation prompt
- **GUI entry** (`app.py` → Analysis & Insights dropdown): "🧠 Live DRL Agent (Real APIs)"
- **`.bat` entry** (`start_talos.bat` Option 6): "Live DRL Agent (Real APIs)"
- **`scripts/pdf_downloader.py` v2.0:** Multi-threaded batch download  
  - ThreadPoolExecutor with 15 workers  
  - Interactive prompt: sequential vs batch mode  
  - ~10x speedup for large paper collections

### Changed
- **`scripts/talos_service.py`:** Epsilon changed from 0.05 → 0.0 (pure exploitation)
- **`ROADMAP.md`:** Complete architectural narrative rewrite — v5.2.0 marked as current

---

## [v5.1.0] - 2026-07-04 — DRL Dashboard & TUI/GUI Reorganization

This release brings the DRL ecosystem to the forefront with a dedicated Streamlit dashboard, interactive TUI features, and a comprehensive project roadmap update.

### Added
- **`app.py` — 🧠 DRL Agent Dashboard (new page):** Streamlit page showing:
  - **GWO Optimization Results**: 4 metric cards (Learning Rate, Gamma, Epsilon Decay, Best Fitness) read from `models/gwo_best_params.json`
  - **"Load GWO Parameters"** button saves params to `st.session_state` for use in training
  - **Agent Training Status**: checks for `models/dddqn_trained.pth`, shows success/warning
  - **Reward Progression Chart**: upward-trending `st.line_chart` simulating 500 training episodes
  - **Training Details**: 2-column table with architecture, hyperparameters, GPU info
- **`talos.py` — DRL Agent Status (Diagnostics → Option 7):** Rich-formatted panel showing trained model status + GWO hyperparameters. Falls back to plain text if `rich` library is not installed.
- **`talos.py` — Compare Baselines (Analysis → Option 10):** Generates a new baseline report and compares it against the previous one, displaying Δ for Total Papers, Elite Papers, and Average Score.

### Changed
- **`talos.py` — TUI reorganization:** DRL Training moved from standalone option to Analysis & Insights (Option 9). Menu expanded from 12→13 items.
- **`ROADMAP.md`:** Complete rewrite — v5.0.1 marked as current stable, detailed v5.1→v5.3 roadmap, v6.0+ Think Tank with 4 strategic axes (Data & Intelligence, Playground, Pedagogical, Interface).


## [v5.0.1] - 2026-07-04 — GWO JSON Export

### Added
- **`scripts/gwo_rl_optimizer.py`**: Saves best hyperparameters to `models/gwo_best_params.json` after optimization completes. Includes learning_rate, gamma, epsilon_decay, best_fitness, best_avg_reward, iterations, and execution time. Creates `models/` directory automatically if it doesn't exist.


## [v5.0.0] - 2026-07-03 — The "Hybrid Embeddings & Deep RL" Update

This **massive major release** spans six distinct phases covering multi-provider embeddings, a complete Deep Reinforcement Learning stack (environment + agent + optimizer + offline training), RTX 4070 GPU acceleration, an automated baseline reporting module, and documentation/project housekeeping. This version represents the largest single update in TALOS history with **14 new files** and **22 modified files**.

---

### Phase 0 — Multi-Provider Hybrid Embeddings v2

#### Added
- **`scripts/db_embedding_upgrade.py` v2.0:** Standalone `embeddings` table migration (id, paper_id FK, embedding BLOB, embedding_model TEXT) with indexes on `paper_id` and `embedding_model`. Migrated 3,849 legacy `papers.embedding` records.
- **`core/database_manager.py` v5.0:**  
  - **`store_embeddings_batch(updates)`**: INSERT INTO `embeddings` table (supports multiple vectors per paper — one per provider)  
  - **`get_papers_needing_embedding(model)`**: Checks the embeddings table per specific model (e.g., "ollama:nomic-embed-text")  
  - **`get_all_embeddings(model_filter)`**: Automatic fallback to legacy `papers.embedding` column if `embeddings` table doesn't exist  
  - **`get_embedding_model_stats()`**: Returns model → paper count from embeddings table with DISTINCT  
  - **`reload_embeddings_for_model(model)`**: Reloads in-memory vectors for a specific model  
  - **`semantic_search(query_vector, top_k=100, model_filter=None)`**: Filters cosine similarity to only compare vectors from the same embedding model  
  - **Profile-aware initialization**: Auto-detects `_profiles/<name>/talos_research.db` via `_resolve_profile_db()`
- **`core/ai_manager.py` v3.6:**  
  - **Hybrid multi-provider embeddings**: Provider chain: Ollama (nomic-embed-text, local/free) → Gemini (gemini-embedding-001, cloud/paid)  
  - **`generate_embeddings(texts)` returns `(vectors, model_name)` tuple**: Database can tag each record with the model that generated it  
  - **Google GenAI GA SDK**: Uses `google.genai.Client` (NOT deprecated `google.generativeai`) with `gemini-embedding-001` model, `RETRIEVAL_DOCUMENT` task type, 768-dim output  
  - **Rate-limit handling**: BATCH_SIZE=10, sleep=3s, retry up to 10 times with parsed `retryDelay` from 429 errors, exponential backoff  
  - **HuggingFace removed** from embedding chain: DNS issues with `api-inference.huggingface.co/.com/.org`
- **`scripts/embedding_generator.py` v4.0:**  
  - **`--all` seed-all mode**: Loops through ALL available models (Ollama → Gemini), shows embedding distribution before starting  
  - **BATCH_SIZE=10** with sleep=3s (~20 RPM, well within 100 RPM free tier)  
  - **Summary report**: Total papers, papers without abstract, per-model generated/failed counts, reasons for failures  
  - Per-model fresh AIManager creation (resets circuit breakers between models)
- **Semantic search**: `model_filter` dropdown in both GUI (`app.py`) and Flask dashboard (`interactive_dashboard.py`) — only compares vectors from the same embedding model. `semantic_search()` adapted to return up to 200 results.
- **`_fix_embedding_labels.py`** (one-time): Renamed legacy "gemini" → "gemini:gemini-embedding-001" in 3,849 records.

---

### Phase 1 — DRL Environment & Agent v1.0

#### Added
- **`core/talos_env.py` v1.0 (225 lines):** Gymnasium RL environment for TALOS API source selection  
  - **Observation Space**: `Box(6,)` — [normalized_hour, arxiv_ratio, openalex_ratio, s2_ratio, low_score_streak, error_streak]  
  - **Action Space**: `Discrete(4)` — 0=ArXiv, 1=OpenAlex, 2=SemanticScholar, 3=Sleep/Cooldown  
  - **Reward Logic**: +20 score≥8, +5 score=7, -10 score<7, -50 API error (429), +2 sleep when limits >80%  
  - **`reset()`**: Zeroes all counters, random hour, returns `(obs, info)`  
  - **`step(action)`**: Increments call counters, returns `(obs, reward, terminated, truncated, info)`  
  - **`_simulate_score()`**: Weighted random (20% score 5-6, 40% 7-8, 40% 9-10) — replaced by real DB scores in Phase 2
- **`core/drl_agent.py` v1.1 (395 lines):** Double Dueling DQN agent with LSTM  
  - **`DuelingLSTM`**: 3-layer LSTM (128→64→32) with LayerNorm + Dueling heads (V + A)  
  - **`TalosDRLAgent`**: Online + Target networks, ε-greedy exploration, soft updates (τ=1e-3), experience replay  
  - **`ReplayMemory`**: `deque(maxlen=10000)`, batch_size=200, LEARN_AFTER=500  
  - **`reset_hidden_states()`**: Documented hook — LSTM resets per singleton input  
  - **`save()`/`load()`**: Model persistence to `models/talos_drl.pth`  
  - **CuDNN fix**: `flatten_parameters()` called before every LSTM forward pass to reset CuDNN memory pointers  
  - **`actor_target.train()`** instead of `.eval()` — prevents CuDNN "backward only in training mode" error  
  - **Hyperparameters**: LR=1e-4, GAMMA=0.8, TAU=1e-3, BATCH_SIZE=200, LEARN_EVERY=3, UPDATE_EVERY=9
- **`scripts/drl_trainer.py` v1.0 (135 lines):** CLI training loop  
  - `--episodes 500` flag, tqdm progress bar, save to `models/talos_drl.pth`
  - Real-time per-episode timing output with ETA

---

### Phase 2 — Meta-Optimization & Offline Training

#### Added
- **`scripts/gwo_rl_optimizer.py` v1.0 (360 lines):** Grey Wolf Optimizer for DRL hyperparameter tuning  
  - **Search space**: LR ∈ [1e-5, 1e-3], GAMMA ∈ [0.5, 0.99], EPS_DECAY ∈ [0.9, 0.999]  
  - **Fitness function**: 30 fast episodes × 200 steps, negative average reward (GWO minimizes)  
  - **15 wolves, 50 iters**: GWO equations X_new = (X1 + X2 + X3) / 3, `a` decays 2→0  
  - **`--wolves`, `--iters`, `--rl-episodes`** CLI flags
- **`scripts/train_agent.py` v1.0 (260 lines):** Offline training with REAL database scores  
  - **`OfflineTalosEnv`**: Extends `TalosEnv`, overrides `_simulate_score()` → samples real `overall_score` from SQLite papers table  
  - **Profile-aware DB resolution**: Reads `_profiles/active_profile.txt`  
  - **Score source display**: Loads 3,849 scores, shows range (1.0-10.0) and mean (3.5)  
  - **`--lr`, `--gamma`, `--eps-decay`** CLI flags for custom hyperparameters  
  - **Per-episode timing**: `X.XXs` per episode with `flush=True`, ETA in minutes  
  - Saves to `models/dddqn_trained.pth`

---

### Phase 3 — Graceful Degradation & Documentation

#### Changed
- **All 3 premium API sources (IEEE, Elsevier, Springer):** Already implemented graceful degradation — API key check → `self.enabled=False` + warning → `fetch_new_papers()` returns `[]`. Verified and confirmed working.
- **`scripts/data_enricher.py` v4.8.1:** Added comprehensive English documentation: module docstring, Google-style docstrings on all functions, inline comments on every logical block in simple English for first-year CS students.
- **`sources/ieee_source.py` v2.2:** Added inline comments explaining pagination logic and stop conditions.

---

### GPU/CUDA Acceleration

#### Changed
- **RTX 4070 support**: Uninstalled CPU-only PyTorch 2.12.1, force-installed `torch 2.5.1+cu121` (CUDA 12.1)  
- **CuDNN mode-lock fix**: Removed all `.eval()` calls from online network, changed `actor_target.eval()` → `actor_target.train()`, uses `torch.no_grad()` only for inference  
- **Verified**: `torch.cuda.is_available()` = True, CUDA 12.1, GPU: NVIDIA GeForce RTX 4070 (12 GB VRAM), both networks on `cuda:0`  
- **Training speed**: ~0.5s/episode on CPU → ~0.05s/episode on GPU (10x improvement)

#### Added to dependencies
- `gymnasium` (RL environment standard)  
- `torch` (neural network framework — CUDA 12.1)  
- `streamlit` (Web GUI)

---

### Baseline Report System

#### Added
- **`scripts/generate_baseline_report.py` v1.1 (480 lines):** Automated baseline snapshot generator  
  - **4 plots at 300/600 DPI**: Score distribution (histogram + KDE), Quad-Layer averages (bar chart), Source distribution (pie chart, top 8 + Other), Embedding model coverage (horizontal bar)  
  - **`--academic` flag**: Publication-quality styling — serif fonts (Times New Roman), 600 DPI, muted academic color palette (grayscale + soft blues), clean layout suitable for IEEE/Springer journals  
  - **Date-organized output**: `reports/general_status_report/YYYY-MM-DD/` with `report.md` + `report.html`  
  - **Dark-themed HTML**: Matching TALOS dashboard aesthetic, responsive CSS, embedded images  
  - **Profile-aware DB resolution**: Reads from active profile's database  
  - **Google-style docstrings** on ALL 12 functions

#### Added TUI/GUI Entries
- **TUI** (`talos.py` → System Diagnostics): Options 5 "Generate Baseline Report (Standard)" and 6 "Generate Baseline Report (Academic — 600 DPI)"  
- **GUI** (`app.py` → Analysis & Insights): Dropdown entries "📊 Baseline Report (Standard)" and "🎓 Baseline Report (Academic)"

---

### Documentation Rules & Knowledge Base

#### Added
- **`.clinerules` v5.0.0 — Progressive Documentation Rule**: MANDATORY documentation on EVERY `.py` file open (read OR edit): module docstring, Google-style docstrings, inline comments, section headers. Documentation before edits.
- **`CHANGELOG_EN.md`** and **`CHANGELOG_GR.md`**: v5.0.0 entries in both languages

#### Changed
- **`requirements.txt`**: Added `gymnasium`, `torch`, `streamlit`
- **`PROJECT_MAP.md`** to be updated (if not already)

---

### Housekeeping

#### Removed
- `_fix_ai.py`, `_fix_embedding_labels.py`, `_fix_now.py`, `_fix2.py`, `_fix3.py`, `_fix4.py` — one-time fix scripts, already applied
- `dump.json` — stale data dump

#### Changed
- **`start_talos.bat` v2.0**: Uses conda `talosenv` environment (auto-activation via `C:\ProgramData\miniconda3\Scripts\activate.bat talosenv`), menu includes CLI, GUI, Legacy Dashboard, Baseline Report, Exit
- **TUI menu expanded**: 9→12 items (added DRL Training + renumbered DB/Diagnostics/Settings)
- **GUI menu expanded**: Added Baseline Report options to Analysis & Insights

---

### Phase 4 — Autonomous Service & Notifications

#### Added
- **`core/notifier.py` v1.0 (185 lines):** Multi-channel notification system  
  - **Telegram**: Bot API, `TELEGRAM_BOT_TOKEN` + `TELEGRAM_CHAT_ID`  
  - **Discord**: Webhook with strict 2000-char truncation, `DISCORD_WEBHOOK_URL`  
  - **Email**: SMTP with STARTTLS for Gmail/Outlook compatibility (`SMTP_*` keys)  
  - All exceptions caught internally — fire-and-forget, never crashes the caller
- **`scripts/talos_service.py` v1.1 (470 lines):** 24/7 autonomous research service  
  - **Interactive reporting**: Silent (alerts only) / Normal (episode summaries) / Verbose (every action)  
  - **Daily reports**: `reports/argus/YYYY-MM-DD/discoveries.{json,md,html}` — three formats  
  - **Weekly digest**: Email every Friday 17:00 with DB stats + activity summary  
  - **Ultra-lightweight**: `os.nice(10)` / `BELOW_NORMAL_PRIORITY_CLASS`, `time.sleep(5)`, `gc.collect()`, RAM < 100 MB  
  - **Action 3 (Sleep)**: `time.sleep(3600)` — 1 hour cooldown  
  - **Massive try/except** — the service NEVER crashes  
  - **Graceful shutdown**: SIGINT/SIGTERM handlers
- **`scripts/talos_service_api.py` v1.0 (90 lines):** Micro-Flask API (port 5002)  
  - `GET /api/status` — uptime, papers found today, DB stats  
  - `GET /api/report` — today's HTML report
- **Renamed**: `talos_daemon.py` → `talos_service.py` (scientifically correct terminology)
- **`requirements.txt`**: Added `psutil` for process priority management

#### Changed
- **`start_talos.bat` v2.0**: Added `[5] Autonomous Research Service (24/7)`, renamed Daemon→Service
- **GUI (`app.py`)**: Added "🤖 Autonomous Research Service (24/7)" and "📡 Service API (Port 5002)" to Analysis & Insights dropdown
- **`drl_trainer.py`**: Interactive episode selection (1=50, 2=100, 3=500, 4=1000)
- **`example.env`**: Added Phase 4 keys (Telegram, SMTP, Discord notification config)

#### Reporting
- **Daily**: JSON + Markdown + HTML in `reports/argus/YYYY-MM-DD/`
- **Weekly**: HTML email with DB stats every Friday 17:00
- **API**: Real-time JSON status via `localhost:5002/api/status`

---

**Total: 17 new files, 26 modified files, 7 deleted files**
**Lines of code added: ~5,000+**

---

## [v4.11.0] - 2026-07-02 - The "Project Map & Diagnostics" Update

This release introduces a complete project knowledge management system including a master blueprint file (PROJECT_MAP.md), interactive dependency graph, AST-based verification tooling, and reorganized CLI/GUI menus.

### Added
- **PROJECT_MAP.md:** Complete project blueprint documenting all 55 files, functions, dependencies, configuration schema, database schema, Greek code name glossary, and known gotchas
- **`.clinerules` v5.0.0:** Mandatory PROJECT_MAP.md reading rules for AI agents — reads the map first on every new chat, updates it after every code change
- **`templates/architecture_graph.html`:** Interactive Cytoscape.js dependency graph with 50+ nodes, 80+ edges, layer filtering, physics simulation, and audit mode (color-coded from dependency_audit.json)
- **`scripts/verify_dependency_map.py`:** AST-based verification tool that compares PROJECT_MAP.md against actual source code:
  - Dependency audit mode (Section 7 vs actual imports): 48 matched, 4 stale (false positives), 35 missing
  - Function documentation audit mode (`--functions`): Sections 2-4 vs actual Python def/class definitions
  - Combined mode (`--all`) for complete project health check
  - 81% noise reduction through smart filtering (external packages, submodule paths, standard library)
  - Outputs in 3 formats: HTML (colored report with intro + HOW TO FIX), Markdown, JSON
  - CI/CD mode (`--ci`) for GitHub Actions integration
- **Audit reports** saved to `reports/audits/`: dependency_audit.{html,md,json}, function_audit.{html,md,json}
- **Explanatory descriptions** in all output formats — clear explanations of what MATCHED, STALE, and MISSING mean and how to fix them

### Changed
- **TUI menu reorganized** from 10 items to 11 items with 3 new sub-menus:
  - `9. Database & Data` (8 items: stats, APOLLO, Zotero, embeddings, re-evaluation, enrichment, scientometrics, PDF downloader)
  - `10. System Diagnostics` (3 items: Code Integrity Check, Documentation Audit, Open Architecture Graph)
  - `11. Profile & Settings` (5 items: profiles, PYTHIA, models, API keys, diagnostics)
- **GUI sidebar restructured** to 7 pages matching the TUI: Home, Search, Paper Eval, Analysis, Database & Data, System Diagnostics, Profile & Settings
- **GUI System Diagnostics page** with 2 tabs: Code Integrity Check (Smoke Test) + Documentation Audit with interactive graph button
- **GUI Profile & Settings** simplified to 2 tabs (API Keys & Models, Profiles & PYTHIA)
- **Version bumped** to v4.11.0 across all entry points (talos.py, app.py, PROJECT_MAP.md)
- **Architecture Intelligence Report:** LLM-powered analysis of PROJECT_MAP.md, audit, and graph data producing 8-section reports in English and Greek (`scripts/architecture_intelligence_report.py`)
- **Architecture graph:** Interactive Cytoscape.js dependency graph with 102 nodes, 318 edges, particle background, edge type legend, futuristic academic theme, zoom controls, fullscreen mode, Dark/Light toggle
- **Graph auto-generation:** `scripts/generate_architecture_graph.py` builds graph from AST analysis + documented dependencies, outputs `templates/architecture_graph.html` with inline data
- **SVG export:** Background rect injection for non-transparent output, CDN fallback via PNG-wrapped SVG
- **HTTP server auto-start:** CLI and GUI open the graph at `http://localhost:8765` for full CDN support (cytoscape-svg, navigator)
- **Real-time progress:** Architecture report sub-page in GUI shows line-by-line output during generation
- **Timestamped filenames:** Reports saved as `architecture_intelligence_report_{lang}_{YYYY-MM-DD_HH-MM}.md`
- **TUI menu integration:** System Diagnostics → option 4 → Architecture Intelligence Report (AI Analysis)
- **GUI sub-page:** Dedicated page with Generate button, progress display, browser-open buttons (EN+GR), Back navigation, and history archive count
- **Free-first provider chain:** Architecture report uses AIManager priority chain (Ollama → HuggingFace → Gemini → DeepSeek)

### Fixed
- Interactive Graph button in Streamlit GUI now uses HTTP server (port 8765) + `webbrowser.open()` instead of broken `file:///` links
- SVG export button now works via CDN (`cytoscape-svg@1.4.0`) with PNG fallback
- Graph layout balanced (nodeRepulsion 30000, gravity 0.2, padding 60) for readability
- Duplicate `<script id="graph-data">` blocks removed via regex cleanup in generator
- `metadata_enricher.py (APOLLO)` dependency documentation corrected — AIManager reference removed (not imported)
- `interactive_dashboard.py` dependency corrected from "Flask, Tabulator.js" to "Flask"
- Dependency audit now correctly filters out third-party libraries and standard library imports
- Function documentation parser handles path normalization between documented and actual paths

## [v4.10.1] - 2026-06-30 - The "Model Management" Update

This release introduces a dedicated Model Management TUI (`scripts/model_manager.py`) with quantization-aware Ollama model selection, dynamic model discovery from the Ollama library, 
VRAM-fit indicators, and cloud model configuration — all accessible from both the TUI and Streamlit GUI.

### Added
- **Model Management TUI (`scripts/model_manager.py`):**
  - Interactive local + cloud model selection accessible via TUI (Profile & Settings → AI Model Management)
  - Quantization-aware model picker: detects all available quant tags (Q8_0, Q4_K_M, Q2_K, IQ2_XXS, etc.) via `ollama show`
  - Tags grouped by bit-depth (8-bit, 6-bit, 4-bit, 3-bit, 2-bit, 1-bit) with estimated VRAM per quant
  - Auto-download missing models via `ollama pull` with confirmation prompt
  - Cloud model configuration: Gemini Flash/Pro, DeepSeek chat/reasoner, HuggingFace model selectors
  - Embedding model selector (nomic-embed-text, bge-m3, mxbai-embed-large, etc.)
  - Manual `ollama pull` option
- **Quantization size estimation (`core/hardware.py`):**
  - `estimate_size_for_quant(model_name, quant_tag)` — computes model size in GB for any quantization level
  - `QUANT_SIZE_PER_BILLION` table with 30+ quantization types (Q8_0=1.0GB/B, Q4_K_M=0.55GB/B, Q2_K=0.28GB/B, IQ2_XXS=0.20GB/B, Q1_0=0.20GB/B, etc.)
  - `extract_params_b(model_name)` — extracts parameter count from model name
- **Dynamic model discovery:**
  - Hardcoded `POPULAR_MODELS` list removed from `model_manager.py`; now fetches live from `ollama.com/api/tags`
  - Falls back to `OLLAMA_LIBRARY_FALLBACK` in `hardware.py` when offline
  - 3-section model list: Installed, Ollama Library, BitNet 1-bit (Edge/CPU)
- **VRAM-aware indicators:**
  - `[FITS ✓]` / `[TIGHT ~]` / `[TOO BIG ✗]` badges on every model in both TUI and GUI
  - VRAM headroom changed from 85% → **70%** (`VRAM_HEADROOM = 0.70`) to leave breathing room for OS + other tasks
- **GUI model configuration (Streamlit `app.py`):**
  - Quantization dropdown with estimated VRAM per quant level
  - Cloud model selectors in Settings: Gemini Flash/Pro, DeepSeek, HuggingFace
- **New `.env` keys:** `GEMINI_FLASH_MODEL`, `GEMINI_PRO_MODEL`, `DEEPSEEK_MODEL_CHAT`

### Changed
- **TUI (`talos.py`):**
  - `profile_settings_menu`: added "3. AI Model Management (Local & Cloud)" → launches `model_manager.py`
  - Main header now shows current local model (e.g. `LOCAL (gemma4:12b-q4_K_M)`) instead of generic `LOCAL (Ollama)`
  - Version bumped to v4.10.1
- **GUI (`app.py`):**
  - Version bumped to v4.10.1 (docstring, sidebar, footer)
  - Hardware import expanded to include `estimate_size_for_quant`, `VRAM_HEADROOM`
  - VRAM metric now shows usable headroom (e.g. `24.0 GB` + `16.8GB usable (70%)`)
  - Save button now persists cloud model selections to `.env`
- **`core/hardware.py`:**
  - All VRAM thresholds unified under `VRAM_HEADROOM = 0.70`
  - `recommend_model()`, `get_all_chat_models_sorted()`, `get_ollama_library_models()`, `get_bitnet_models()` — all use `VRAM_HEADROOM`

### Fixed
- **`PermissionError` in `api_keys_menu`:** `.env` file write now uses 3-attempt resilient strategy (direct write → chmod + write → atomic tempfile + `os.replace()`), with a graceful fallback error message if the file is read-only on Windows

### Files Changed
| File | Change |
|---|---|
| `talos.py` | v4.10.1, Model Management menu entry, header shows model, PermissionError fix |
| `app.py` | v4.10.1, quantization dropdown, VRAM badges, cloud model selectors |
| `core/hardware.py` | `estimate_size_for_quant()`, `QUANT_SIZE_PER_BILLION`, `VRAM_HEADROOM=0.70` |
| `scripts/model_manager.py` | **New** — 608-line TUI for model management |


## [v4.10.0] - 2026-06-30 - The "Zero-Config & Resilience" Update

This release transforms TALOS into a fully autonomous system running on 100% free, keyless APIs. It adds Tiered API Keys management (GUI + TUI), API Health Check with tqdm progress bar, Smart Ollama Model Selector, PDF Downloader, System Health Check, and numerous UX/UI fixes.

### Added
- **Tiered API Keys Management:**
  - GUI: Unified Settings page with 3 tabs (API Keys & Models, Profiles & PYTHIA, Diagnostics)
  - 4 sections: Free & Keyless, Premium AI, Academic APIs, Integrations
  - TUI: New sub-menu Profile & Settings -> API Keys Management with interactive editing
  - Saves via python-dotenv to .env file
- **API Health Check (v1.1):**
  - 25 API checks with real-time tqdm progress bar
  - Status: [OK], [FAIL], [FREE], [NONE] — no emoji for full compatibility
  - Real-time feedback — no more hanging during checks
- **Smart Ollama Model Selector:**
  - 3-section dropdown: Installed on this PC | Available via Ollama | BitNet 1-bit (Edge/CPU)
  - VRAM detection + auto-download via ollama pull
  - BitNet b1.58 models (7 models, ~0.2GB per 1B parameters)
- **PDF Downloader (pdf_downloader.py):**
  - Unpaywall -> OpenAlex keyless fallback
  - Downloads PDFs to data/pdfs/ with timeout and retries
- **System Health Check (test_smoke.py):**
  - 78 checks (syntax, imports, database, AI Manager)
  - Integrated into both GUI and TUI
- **Docker Updates:**
  - Dockerfile with streamlit install, TALOS_START_MODE
  - docker-compose.yml with port 8501
- **Onboarding Wizard (GUI):**
  - Full-screen wizard for new users (research goal -> PYTHIA)
  - Auto-copies config.template.json if config.json is missing

### Changed
- **Sidebar: 8 -> 6 pages** (merged Setup + Profile into Settings)
- **Settings page:** 3 tabs instead of 2 separate pages
- **TUI:** VRAM detection in header, KeyboardInterrupt graceful handling
- **example.env:** Complete template with 21 keys in 5 sections
- **start_talos.bat:** Interactive launcher (CLI/GUI/Dashboard)
- **Scientometrics Report:** Dark mode HTML, Quad-Layer KDE fix, Top Venues chart, Score table

### Fixed
- 17 use_container_width deprecation warnings
- KeyboardInterrupt (Ctrl+C) during daily_search — returns to menu instead of crashing
- API Health Check hanging — tqdm progress bar with real-time tqdm.write()
- KeyError in CHIRON knowledge_path_generator.py
- UnicodeDecodeError in subprocess output due to Greek characters



## [v4.9.0] - 2026-06-29 - The "Streamlit GUI & Quality" Update

This release transforms TALOS into a **full Web GUI application** with a professional Streamlit interface, while preserving the CLI menu. It adds a **smoke test suite** for health checking, upgrades the scientometrics report with dark mode and Quad-Layer stats, and fixes several bugs discovered during GUI integration.

### Added
- **Streamlit Web GUI (`app.py`):**
  - Complete 6-page Multi-Page application replacing the CLI menu in a browser.
  - Sidebar navigation: Home, Search & Discovery, Single Paper Evaluation, Analysis & Insights, Database Maintenance, Profile & Settings.
  - **Provider Selection** in sidebar (Local Ollama / Cloud Gemini+DeepSeek) with fallback toggle — exactly mirrors the CLI prompt.
  - **Database Dashboard** on Home page with 6 filter buttons (Core, Strategic, Operational, Tactical, Playground ≥7), semantic search via cosine similarity, and Article DNA progress bars.
  - **Single Paper Evaluation** with 3 input methods: paste abstract, fetch by DOI (Semantic Scholar API), or select from database.
  - **Inline report rendering:** Markdown and HTML reports generated by scripts are displayed directly in the GUI.
  - **CHIRON / ORPHEUS / Recommender / Author Tools / Grey Literature** all accessible with input piped from GUI widgets.
  - **System Health Check** button in Profile & Settings.
- **_gui_runner.py:**
  - Wrapper script that monkey-patches `questionary` to use plain `input()` instead of `prompt_toolkit`, enabling TALOS scripts to run from subprocess without a real Windows console.
  - Input passed via `TALOS_GUI_STDIN` environment variable (stdin piping unreliable on Windows).
  - Auto-cd to project root for correct `config.json` resolution.
- **Smoke Test Suite (`test_smoke.py`):**
  - 78 automated checks: syntax of all 43 `.py` files, core imports, database connectivity, AI Manager initialization, GUI runner patching, script importability, source agent importability.
  - Runs in ~10 seconds with clean pass/fail/skip summary.
  - Integrated into both CLI (Database Maintenance → option 8) and GUI (Profile & Settings).
- **Docker Updates:**
  - `Dockerfile` now installs `streamlit` and supports `TALOS_START_MODE` env var (`streamlit`, `dashboard`, or default CLI).
  - `docker-compose.yml` now exposes both ports 5000 (Flask) and 8501 (Streamlit).

### Changed
- **Bumped version to v4.9.0** across all files (`app.py`, `talos.py`).
- **Scientometrics Report (`trend_analyzer.py`):**
  - **Dark mode HTML:** Full dark theme matching Streamlit GUI (background `#0d1117`, dark cards, colored headers).
  - **Quad-Layer KDE fix:** Added missing `operational_score` distribution line.
  - **Top Venues chart:** New bar chart showing top 10 publishers/journals.
  - **Quad-Layer score table:** Summary table with Avg, Median, Min, Max, Elite% for each layer.
  - Fixed seaborn `FutureWarning` by adding `hue` and `legend=False` to bar plots.
- **CHIRON Knowledge Path Generator:**
  - Code added to the `_gui_runner.py` script to ensure proper display.
- **Daily Search**, **Author Tools**, **Recommender**: Confirmed operational via subprocess with `_gui_runner.py`.
- **Database Maintenance** sub-menu streamlined to require "y" via stdin for scripts with confirm prompts.

### Fixed
- **`KeyError: 'id'` in CHIRON** when `sota_papers` DataFrame is empty (line 93-94 of `knowledge_path_generator.py`).
- **`NoConsoleScreenBufferError`** when running questionary-based scripts from subprocess — solved by `_gui_runner.py`.
- **`UnicodeDecodeError`** in subprocess output due to Greek characters — fixed with `encoding="utf-8", errors="replace"`.
- **Markdown table rendering** in Streamlit expander — added blank line before `|` for proper parsing.
- **`DatabaseManager` init failure** in smoke test — fixed import order.

## [v4.8.5] - 2026-06-29 - The "Bug Hunt & Quality" Update

This release is a comprehensive **bug-fixing sprint** addressing 15+ bugs across all modules. Key improvements: metadata enrichment now uses a **multi-source fallback chain** (OpenAlex → Crossref → DBLP → Semantic Scholar), the recommender generates **structured reports** matching the terminal layout, and the overall recommendation quality threshold was raised from 4.0 to **7.0** to ensure high-relevance suggestions.

### Fixed
- **`sources/elsevier_source.py`:** Fixed class-level `self` reference causing `NameError` on import (Critical B1).
- **`scripts/grey_literature_miner.py`:** Fixed `try/except/else` logic that always discarded Gemini results (Critical B2). Fixed config key `grey_literature_model` → `grey_research_model` (Critical B3). Added fallback try/except on the AIManager fallback path.
- **`scripts/recalculate_scores.py`:** Fixed missing `operational_score` in SELECT query and `scores_dict`, causing systematically wrong recalculations (Critical B4).
- **`scripts/interactive_dashboard.py`:** Fixed `AttributeError` when semantic search returns no results (Critical B6).
- **`core/ai_manager.py`:** Fixed default local model name `gemma4:12b` → `gemma3:12b` (nonexistent model, High B7). Removed unused hardware imports (Low B23).
- **`scripts/historic_search.py`:** Added missing `CORESource` import and instantiation, now matches `daily_search.py` (High B8).
- **`scripts/trend_analyzer.py`:** Fixed CSS `max_width` → `max-width` (High B9).
- **`scripts/zotero_connector.py`:** Fixed `.startswith()` crash when Zotero returns `None` URL (High B10).
- **`core/database_manager.py`:** Removed duplicate `ALTER TABLE ADD COLUMN operational_score` causing "duplicate column" errors on every startup (High B11).
- **`scripts/metadata_enricher.py`:** Fixed 403 errors from excessively long search queries by truncating titles to 100 chars (High B12).
- **`scripts/db_stats.py`:** Fixed division by zero when database is empty (Medium B17).
- **`talos.py`:** Cleaned up duplicate `env["TALOS_MODELS_VERIFIED"]` line, removed redundant second `time.sleep(1)`, cleaned dangling whitespace (Low B24/B25).

### Added
- **Multi-Source Metadata Enrichment (v2.0):**
  - New `search_papers()` methods added to **OpenAlex**, **Crossref**, and **DBLP** sources.
  - Fallback chain: OpenAlex → Crossref → DBLP → Semantic Scholar.
  - Semantic Scholar automatically skipped when no API key is present (eliminates 403 errors).
  - All 3 primary sources are free and require no API keys.
- **Structured Recommender Reports (v4.1):**
  - HTML, DOCX, and Markdown exports now match the terminal layout exactly: Foundational → Clusters → State-of-the-Art.
  - `operational_score` added to all export formats.
  - Placeholder abstracts (DBLP "δεν παρέχει περίληψη", etc.) filtered from clustering for better keyword extraction.
  - HTML report now has two tabs: **Structured Path** + **Top 50 Interactive Table**.

### Changed
- **Recommender quality threshold:** Default `min_score` raised from **4.0 → 7.0** for clustering and all recommendations.
- **Foundational papers:** Now filtered by high score (≥7.0) first, fallback to ≥5.0 — no more low-quality old papers.
- **State-of-the-Art:** Now sorted by `publication_year` (not `processed_at`) and filtered by score ≥7.0.

### Removed
- **`core/ai_manager_clean.py`:** Deleted headless fragment file that crashed on import (Critical B5).

## [v4.8.4] - 2026-06-28 - The "Multi-Provider & Web Search" Update

This release transforms TALOS into a **complete multi-provider AI system** with 4 independent providers (Local, Hugging Face, DeepSeek, Gemini) and adds **live web search** to the Grey Literature Miner.

### Added
- **Hugging Face Provider (Free Cloud Inference):**
  - Integration of Hugging Face Inference Providers API as a 4th AI provider.
  - Uses the new **OpenAI-compatible unified API** (`router.huggingface.co/v1`) for full compatibility.
  - **Free** usage with no limits — only requires an `HF_TOKEN` from https://huggingface.co/settings/tokens.
  - **Interactive Model Selection:** `talos.py` displays a list of the 6 best free models (Mixtral 8x7B, Llama 3.1 8B, Qwen2.5 7B, Mistral 7B, Phi-3, Gemma 2 2B).
  - **Auto-priority:** HF is placed **first** in `provider_priority` when available (free > paid).

- **Live Web Search (Grey Literature Miner):**
  - Integration of **DuckDuckGo Search** for live web search (`duckduckgo-search` package).
  - **Free, no API key required** — works immediately.
  - **Query Optimization:** User's free-text input is automatically converted to an optimized search query by an LLM before searching.
  - Web results are embedded in the prompt for better report quality.

- **Multi-Provider Fallback in Grey Literature Miner:**
  - The Miner now uses **AIManager** instead of direct Gemini API calls.
  - Flow: Gemini Search Grounding → AIManager fallback (HF → DeepSeek → Local).
  - **Resilience:** Even when Gemini has quota issues, the Miner continues with another provider.

- **`core/hardware.py` — Hardware Detection Module:**
  - Automatic GPU VRAM detection via `nvidia-smi`.
  - Database of model sizes (4-bit quantized) for 20+ models.
  - **Smart Model Recommendation:** Recommends the best model based on available VRAM.

### Fixed
- **`talos.py` — Missing `load_dotenv()`:**
  - `.env` was not loaded in `talos.py`, causing `HF_TOKEN` and other variables to be unavailable.
  - Added `from dotenv import load_dotenv; load_dotenv()` at module level.
- **`grey_literature_miner.py` — Import Error:**
  - Fixed `from google import genai` which required the `google-genai` package.
  - Added `google-genai` to `requirements.txt`.
  - Added `duckduckgo-search` to `requirements.txt`.
- **Provider Priority:**
  - Fixed: Hugging Face is placed **first** in priority (insert(0)) instead of last (append).
  - Fixed: `TALOS_USE_LOCAL=1` removed from `.env` — now set **only** by the `talos.py` interactive prompt.
- **HF Token with spaces:**
  - Documented that `.env` values must **not** have spaces around `=` (`load_dotenv` does not strip them).

### Changed
- **`ai_manager.py` v3.5:**
  - Added Hugging Face provider with OpenAI-compatible client.
  - Removed custom `_execute_huggingface_request` — uses generic `_execute_openai_compatible`.
  - `generate_embeddings()` tries **local first**, then Gemini.
- **`talos.py`:**
  - **HF Model Selection Menu** with the 6 best free models.
  - Automatic propagation of `HF_MODEL_NAME` to subprocesses.
  - `load_dotenv()` called at module level for early `.env` loading.
  - Separation of `TALOS_USE_LOCAL` (set only by prompt) from `.env`.
- **`grey_literature_miner.py`:**
  - Complete upgrade: DuckDuckGo search + query optimization + AIManager fallback.
  - **Graceful degradation:** each step has fallback — web search, Gemini, AIManager.
- **`requirements.txt`:**
  - Added `google-genai`, `duckduckgo-search`.
- **`.clinerules`:**
  - Added documentation for editor's inability to match Greek text.
  - Documented architecture, providers, and known gotchas.

---


## [v4.8.3] - 2026-06-27 - The "Secure Local AI & Privacy" Update

This release strengthens the **security and privacy** of local mode. It adds **model pre-verification with auto-install** at startup, **user consent** before any cloud fallback, and **bidirectional fallback** (local↔cloud) with explicit approval.

### Added
- **Model Pre-Verification (`_verify_local_models`):**
  - When LOCAL mode is selected, TALOS verifies **once** that all required models (chat + embedding) are installed.
  - Missing models are automatically pulled via `ollama pull`.
  - `TALOS_MODELS_VERIFIED=1` is passed to all subprocesses, avoiding redundant checks.
- **Privacy Guard: Cloud Fallback Consent:**
  - When the local model fails, TALOS does **NOT** automatically send data to the cloud.
  - User is prompted at startup: "Allow cloud fallback if local fails?"
  - If answered **NO**, data stays **fully offline** — no API calls leave the machine.
- **Bidirectional Fallback:**
  - In CLOUD mode, user can allow fallback to local model if cloud fails ("Allow local fallback if cloud fails?").
  - `TALOS_ALLOW_CLOUD_FALLBACK` and `TALOS_ALLOW_LOCAL_FALLBACK` env vars control behavior.

### Fixed
- **Local Provider Priority:**
  - Fixed: when LOCAL mode is selected, local model is placed **first** in `provider_priority` (using `insert(0, 'local')` instead of `append`).
  - Previously, local was appended last and only tried after Gemini and DeepSeek failed.
- **Embedding Model Missing:**
  - `_ensure_local_model()` did not check for the embedding model (`nomic-embed-text`).
  - Added automatic check and installation for the embedding model.
- **Embedding Priority:**
  - `generate_embeddings()` now tries the local embedding model **first**, then falls back to Gemini.
- **Maintenance Menu:**
  - Restored options 4-8 (Embedding Generator, Re-evaluate, Recalculate, Data Enricher, Trend Analyzer) lost during refactoring.

### Changed
- **`talos.py`:**
  - Added `_verify_local_models()` for centralized model checks.
  - Added interactive prompts for cloud/local fallback consent.
  - Automatic propagation of `TALOS_MODELS_VERIFIED`, `TALOS_ALLOW_CLOUD_FALLBACK`, `TALOS_ALLOW_LOCAL_FALLBACK` to subprocesses.
- **`ai_manager.py` v3.5:**
  - Skips `_ensure_local_model()` in subprocesses when models already verified.
  - Added security check before cloud fallback (requires `TALOS_ALLOW_CLOUD_FALLBACK=1`).
  - Fixed provider ordering (local first) and embedding fallback (local first).

---


## [v4.8.2] - 2026-06-27 - The "Local AI & Resilience" Update

This release focuses on **autonomy** and **resilience**. It introduces **local AI model support (Ollama)** enabling fully offline operation without cloud dependencies, while also fixing **16 critical bugs** that impacted system stability.

### Added
- **Local AI Model Support (Ollama):**
  - Integration of Ollama as a third AI provider in `AIManager`, alongside Gemini and DeepSeek.
  - Uses Ollama's **OpenAI-compatible API** for seamless compatibility with existing code (`/v1/chat/completions`).
  - **Auto-install:** If the selected model is not found locally, TALOS automatically runs `ollama pull`.
  - **Local Embeddings:** Support for Ollama Embeddings API (`/api/embed`) using `nomic-embed-text` for semantic search without cloud dependency.
  - **Interactive Mode Selection:** `talos.py` prompts the user at the start of each session to choose between local or cloud model.
  - **Graceful Degradation:** If the Ollama server is unreachable or the model fails, it automatically disables and falls back to cloud providers.
  - **New environment variables:** `TALOS_USE_LOCAL`, `LOCAL_MODEL_NAME`, `LOCAL_MODEL_BASE_URL`, `LOCAL_EMBEDDING_MODEL`, `LOCAL_MODEL_API_KEY`.

### Fixed
- **CRITICAL: `db_stats.py` KeyError Crash:**
  - `get_database_statistics()` was missing `elite_papers`, `missing_doi`, and `embedded_papers` fields, causing a `KeyError` crash in `db_stats.py`. All missing fields have been added.
- **CRITICAL: Source Agents Crash Without API Keys:**
  - Agents `elsevier_source`, `ieee_source`, `springer_source`, and `openarchives_source` raised `ValueError` during `__init__` if API keys were missing, killing the entire `daily_search.py` even when the other 10 agents were functional.
  - **Fix:** Added `self.enabled` flag with graceful skip. Added guard `if not getattr(self, "enabled", True): return []` to every `fetch_new_papers()`.
- **HIGH: `recommender.py` — Missing `operational_score`:**
  - The SQL query in Recommender was not selecting `operational_score`, causing operational evaluations to be completely ignored in the Reading Recommendation report. Added the missing field.
- **HIGH: `interactive_dashboard.py` — ValueError in Semantic Search Sort:**
  - When a paper ID from the database was not present in semantic search results, `.index()` threw a `ValueError`. Replaced with dictionary-based lookup.
- **HIGH: `daily_search.py` — Silent Loss of Papers Without DOI:**
  - Deduplication used only DOI as key, silently dropping papers without DOI (e.g., from DBLP, OpenArchives). Added URL fallback, aligning logic with `historic_search.py`.
- **MEDIUM: `crossref_source.py` — IndexError on Empty Title:**
  - If the Crossref API returned `"title": []`, `[][0]` caused an `IndexError`. Added empty list check.
- **MEDIUM: `openalex_source.py` — KeyError on Missing `meta`:**
  - `data['meta']` access replaced with `data.get('meta', {})` for safe handling of malformed API responses.
- **MEDIUM: `plos_source.py` — Dead Code `title_display`:**
  - The `title_display` field was not included in the `fl` parameter of the API request, making `doc.get("title_display", ...)` always return `None`. Fixed fallback order.
- **MEDIUM: `database_manager.py` — `duplicate column name` Warning:**
  - The `ALTER TABLE` for `operational_score` ran without an existence check, producing noisy error messages at every startup. Added `PRAGMA table_info` check before ALTER.

### Changed
- **`ai_manager.py` v3.4 → v3.5:**
  - Complete reorganization of the provider system with local model support.
  - `generate_embeddings()` now supports fallback to local embedding model.
  - `_execute_request()` supports the `local` provider alongside Gemini and DeepSeek.
- **`talos.py`:**
  - Added interactive prompt for Local/Cloud selection at the start of each session.
  - Automatic propagation of selection to all subprocesses via `TALOS_USE_LOCAL` environment variable.
- **`database_manager.py`:**
  - `get_database_statistics()` now returns `elite_papers`, `missing_doi`, and `embedded_papers`.

---


## [v4.8.1] - 2026-05-08 - The Dockerization & Portability Update

This update focuses on zero-friction deployment, ensuring that Project TALOS is environment-agnostic and accessible to researchers regardless of their technical background.

### Added
- **Docker Integration:**
  - Added `Dockerfile` optimized for `python:3.10-slim`.
  - Added `docker-compose.yml` for simplified orchestration, persistent volumes, and interactive TTY support for terminal menus.
- **Windows 1-Click Launcher:**
  - Added `start_talos.bat` which autonomously handles virtual environment creation, dependency installation, and `.env` initialization.
- **Documentation Update:** 
  - Updated `README.md` to reflect the new deployment methods, ensuring "Zero-Friction" setup for all users.

---
 
##[v4.8.0] - 2026-03-20 - The "Enrichment & Scientometrics" Update

This release is a major milestone for Project TALOS, transforming the database from a passive bibliography list into an **active, interconnected Knowledge Hub**. It introduces bulk data enrichment capabilities from third-party sources and offers, for the first time, "macroscopic" oversight of the research field through advanced visualizations.

### Added
- **NEW MODULE: Scientometrics Suite (`scripts/trend_analyzer.py`):**
  - A new subsystem that generates **HTML Reports** with statistical analyses and visualizations using `matplotlib`, `seaborn`, and `wordcloud`.
  - **Available Visualizations:**
    - **Research Timeline:** Bar chart of publications per year (identifying interest "bursts").
    - **Quality Landscape (KDE Plots):** Density curves for Strategic/Tactical/Overall score distributions.
    - **Open Access Landscape:** Pie Chart for accessibility distribution (Gold, Green, Hybrid, Closed).
    - **Keyword Dominance (WordCloud):** Semantic analysis of titles to identify dominant trends (e.g., "Reinforcement Learning", "UAV").
    - **Top Authors:** Analysis of the most productive researchers in the database.

- **NEW MODULE: Data Enricher (`scripts/data_enricher.py`):**
  - Replaces and heavily expands the legacy `pdf_retriever.py`.
  - **"Hub" Functionality:** Connects to the **Unpaywall API** and retrieves external identifiers (`openalex_id`, `pmid`, `pmcid`), turning the local DB into a bridge between different academic ecosystems.
  - **Smart Metadata:** Enriches records with `oa_status`, `journal_issn`, and corrected `publisher` strings.
  - **Aggressive Initialization:** Incorporates a `force_reset_status` mechanism that automatically fixes older records with `NULL` status, ensuring no article is left unprocessed.

- **Infrastructure & Migration Tools:**
  - **`scripts/upgrade_to_v4_8.py`:** A standalone safe upgrade tool that creates a backup and applies the new schema (Schema Migration) to the active profile's database.
  - **`scripts/fix_missing_columns.py`:** Emergency script that recursively scans all profile folders to locate and repair databases with outdated schemas.

### Changed
- **Database Schema Evolution (Core v5.2):**
  - The `papers` table was expanded with 9 new columns: `oa_pdf_url`, `openalex_id`, `pmid`, `pmcid`, `oa_status`, `journal_issn`, `publisher`, `enrichment_status`.
  - The `enrichment_status` column (INTEGER) acts as a state machine (0=Pending, 1=Enriched, 2=Failed) to control the workflow.

- **Core Architecture (`core/database_manager.py`):**
  - **Profile Awareness:** The `DatabaseManager` now accepts an optional `db_path` argument during initialization, allowing maintenance scripts to dynamically target the active profile's database instead of the default one.
  - **Batch Operations Fix:** The `update_papers_enrichment_batch` method was implemented using `executemany` for speed, and a critical `sqlite3.InterfaceError` (Binding Error) was fixed.

- **UX / Menu (`talos.py`):**
  - The "Maintenance Tools" menu was completely reorganized.
  - Added automatic detection of the active Database Path, which is passed as an argument to the `trend_analyzer` and `data_enricher` scripts, resolving incompatibility issues in multi-profile environments.

### Fixed
- **Critical Binding Error:** Fixed a bug in `data_enricher.py` where failure to find data resulted in incomplete dictionaries and database crashes during writing. The script now correctly returns full dictionaries with `None` values (Null Object Pattern).
- **Null Status Bug:** Fixed a logical error where SQL queries ignored records with `enrichment_status IS NULL`.

---

## [v4.7.1] - 2025-11-30 - The "HERMES" Performance Update

This release dramatically improves the execution speed of `pdf_retriever.py` (Project HERMES).

### Changed
- **Multithreaded PDF Retrieval:**
  - The logic of `pdf_retriever.py` was completely rewritten to utilize **Multithreading** via a `ThreadPoolExecutor`.
  - The script now executes multiple (default: 15) Unpaywall API calls concurrently, rather than serially.
  - **Result:** The Open Access PDF checking process is now ~10-15 times faster.

---

##[v4.7.0] - 2025-11-30 - The PDF Retriever Update (Ethical Edition)

### Added
- **NEW MODULE: Project PDF Retriever (`scripts/pdf_retriever.py`):**
  - A maintenance tool that scans the database for articles with DOIs.
  - Calls the **Unpaywall API** to locate legal, **Open Access** versions of PDFs.
  - Saves the links in a new `oa_pdf_url` column in the DB, promoting "Open Science".

### Changed
- **Database Schema (v5.1):** Added the `oa_pdf_url` column for storing links.

---

##[v4.6.0] - 2025-11-30 - The "ORACLE" Update

Introduction of Project ORACLE for discovering "Grey Literature", leveraging the new Gemini 2.0 models and Google Search Grounding capabilities.

### Added
- **NEW MODULE: Project "ORACLE" (`scripts/oracle_agent.py`):**
  - **Role:** Performs "Horizon Scanning" on the web for resources not found in traditional academic databases (GitHub code, Datasets, Technical Reports).
  - **Technology:** Uses the `google-genai` SDK and the `gemini-2.0-flash-exp` (or Pro) model with the **Google Search** tool enabled.
  - **Output:** Produces Markdown reports with links, saved in `reports/oracle_deep_research/`.

---

##[v4.4.0] & [v4.5.0] - 2025-11-30 - The "Open Access & Onboarding" Update

This release dramatically improves the accessibility of TALOS. It introduces an automated onboarding wizard for new users and expands data sources with the addition of PLOS (Public Library of Science).

### Added
- **NEW AGENT: `sources/plos_source.py` (Project ALEXANDRIA):**
  - Integration of the PLOS API. Ensures access to high-quality, Open Access articles.
- **Onboarding Wizard (`talos.py`):**
  - Automatically creates `config.json` from a template and launches "PYTHIA" to set up the user's first research profile, minimizing Time-to-Value.

---

##[v4.3.1] - 2025-11-30 - The Batch Execution Fix

### Fixed
- **Database Batch Operations (`core/database_manager.py` v4.7):**
  - Fixed the `sqlite3.ProgrammingError: Incorrect number of bindings supplied` error during bulk embedding updates.
  - Added the `execute_many()` method leveraging SQLite's `executemany` for safe and fast bulk inserts/updates.

---

## [v4.3.0] - 2025-11-28 - The "Soft Shutdown" Update

### Added
- **Dashboard Soft Shutdown:**
  - Added a "🔴 Exit & Return to Menu" button in the Dashboard UI.
  - Implemented a new `/api/shutdown` endpoint to gracefully terminate the Flask server using threading and signals.

---

## [v4.2.0] - 2025-11-28 - The Pythia Refinement & Architecture Hardening

### Changed
- **AIManager v3.4 (System Prompt Override):**
  - Introduced the ability to override the default `system_prompt` so specialized agents (like PYTHIA) can assume different personas.
- **AIManager v3.3 (Surgical JSON Cleaning):**
  - Implemented a new mechanism to "surgically" clean AI responses (extracting the JSON object from Markdown blocks).
- **ArxivSource v3.8 (Config-Driven Architecture):**
  - Removed hardcoded search terms. The agent dynamically reads `arxiv_query` from `config.json`.

---

##[v4.1.0] - 2025-11-28 - The Quad-Layer Architecture & Profile System

### Added
- **Quad-Layer Evaluation Framework:**
  - The evaluation system expanded from 3 to **4 levels**:
    1. **Strategic** (High-level decision making)
    2. **Operational** (Auction-based mechanisms, resource allocation) - **NEW**
    3. **Tactical** (DRL/MARL policies)
    4. **Playground** (Simulation)
- **Profile Management System (`scripts/profile_manager.py`):**
  - Ability to create and switch between isolated "Profiles" (e.g., "Drones", "Bioinformatics"), each with its own DB and config.

---

## [v4.0.0] - 2025-11-28 - Project "PYTHIA" (Automated Configuration)

### Added
- **NEW MODULE: Project "PYTHIA" (`scripts/query_translator.py`):**
  - An automation that uses AI to translate a natural language research goal into optimized Boolean Search Queries for 10+ APIs and customized System Prompts.

---

## [v3.2.0] - 2025-09-27 - Operation "Genesis"

### Changed
- **BREAKING CHANGE - Complete Overhaul of "Agents" (`sources/*.py`):**
  - All Agents (ArXiv, Scopus, IEEE, Semantic Scholar, Springer, OpenAlex, DBLP, CORE, Crossref, OpenArchives, OSTI, PubMed, Science.gov) were completely rewritten.
  - **Standardized Output:** Every Agent now returns a standardized dictionary ensuring critical fields (`doi`, `publication_year`, `authors_str`) are always present.

---

## [v3.0.0] - 2025-09-26 - The Strategic Mentor (CHIRON)

### Added
- **NEW MAJOR MODULE: Project "CHIRON" (`scripts/knowledge_path_generator.py`)**
  - Allows users to initiate a natural language dialogue.
  - Performs deep semantic search, applies Knowledge Structuring (K-Means Clustering), and generates narrative Markdown reports explaining *why* the user should follow a specific study path.

---

## [v2.21.0] - 2025-09-26 - The Reliability Update

### Changed
- **BREAKING CHANGE - JSON Architecture:**
  - `AIManager` completely redesigned to be **Model-Independent**, natively supporting JSON mode and provider-specific Circuit Breakers.
  - Removed all legacy Regex Parsing functions for data extraction.

---

## [v2.20.0] - 2025-09-22 - The "ORPHEUS" Interactive Knowledge Graph

### Added
- **NEW MODULE: Citation Analyzer ("ORPHEUS"):**
  - Accepts a target paper DOI, queries Semantic Scholar for references/citations, and generates a fully interactive HTML network graph using `pyvis`.

---

##[v2.19.0] - 2025-09-21 - The Zotero Bridge & "Smart Sync" Update

### Added
- **NEW MODULE: Zotero Connector:**
  - Connects to the Zotero Web API (`pyzotero`). Fetches user's papers, runs them through the deep Pro AI evaluation, and synchronizes the local database.

---

## [v2.18.0] - 2025-09-21 - The AI Resilience & Agent Expansion Update

### Added
- **AI Manager (`core/ai_manager.py`):**
  - Centralized class handling all LLM calls. Includes automatic Fallback logic (Circuit Breaker) from Google Gemini to DeepSeek if quota is exceeded.

### Changed
- **"Smart Store-First" Strategy:**
  - `daily_search.py` now performs a fast pre-screening (Flash model), stores the paper, and selectively upgrades "Elite" papers to Deep Analysis (Pro model), drastically reducing API calls.

---

## [v2.15.0] - 2025-09-19 - The "NAFSIKA" Interactive Dashboard

### Added
- **Interactive Dashboard (`scripts/interactive_dashboard.py`):**
  - A lightweight local Flask web server.
  - Integrates `Tabulator.js` for dynamic sorting, filtering, and real-time database updates without page reloads. Includes Semantic Search backend and "Article DNA" visualization.

---

## [v1.0.0] - 2025-08-27 - The Genesis

### Added
- **Initial Creation:** The project started as a simple script (`main.py`) querying arXiv and evaluating abstracts via Gemini AI, sending Discord notifications via Webhook.