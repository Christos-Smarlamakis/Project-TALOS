# Project TALOS — Strategic Roadmap & Architecture Chronicle

This document serves as both the **development compass** and the **architectural narrative** of Project TALOS. It chronicles the evolution from a research aggregator to a fully autonomous, DRL-driven research intelligence platform — and maps the path forward.

> **Current Version:** v5.3.6 (TUI/CLI Hardening — Batch 2 Audit Fixes: graceful Ctrl+C everywhere, partial-save training interrupts to dddqn_partial.pth, dead menu option fix, argparse in live agent)
> **Last Updated:** 2026-07-06

---

## 1. The Vision: From Aggregator to Autonomous Research Architect

Project TALOS was born from a simple question: **what if a literature review system could think for itself?**

The exponential growth of academic publishing (over 5 million papers per year) has broken the traditional Systematic Literature Review (SLR) workflow. A PhD researcher simply cannot manually monitor, evaluate, and synthesize the firehose of daily publications. TALOS answers this challenge by evolving through three generations:

1. **Gen 1 (v1-v4): The Aggregator** — Searched 14 APIs, evaluated papers with AI, stored results in SQLite.
2. **Gen 2 (v5.0): The Orchestrator** — A Deep Reinforcement Learning agent that learns to select optimal APIs in real-time.
3. **Gen 3 (v6.0+): The Ecosystem** — A distributed microservice with RAG capabilities, cross-platform UI, and 3D knowledge visualization.

---

## 2. v5.0.x — The AI Core (COMPLETED ✅)

The v5.0 series represents a **paradigm shift** — TALOS ceased being a passive aggregator and became an **active, learning orchestrator**. This was the largest single update in project history, spanning four major phases and adding over 5,000 lines of code.

### 2.1 Phase 0: Multi-Provider Hybrid Embeddings

**The Semantic Brain** — Before the agent could reason about papers, it needed to truly *understand* them through a dimension-agnostic embedding system.

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Ollama Embeddings** | `nomic-embed-text` (local) | Free, offline, zero-latency embeddings |
| **Gemini Embeddings** | `gemini-embedding-001` (cloud) | High-precision 768-dim vectors, `RETRIEVAL_DOCUMENT` task type |
| **Embeddings Table** | SQLite with B-tree indexes | Multi-model vector storage, backward-compatible with legacy `papers.embedding` column |
| **Migration Script** | `db_embedding_upgrade.py` | Seamlessly migrated 3,849 legacy records to the new schema |
| **Google GenAI GA SDK** | `google.genai.Client` | Future-proof API (NOT deprecated `google.generativeai`) |

**Key innovation:** The `semantic_search()` method filters cosine similarity by embedding model — Ollama vectors are only compared against other Ollama vectors, Gemini against Gemini. This prevents cross-model semantic drift.

### 2.2 Phase 1: Deep Reinforcement Learning Stack

**The Orchestrator's Brain** — A Double Dueling DQN (DDDQN) with LSTM that learns API foraging strategies from experience.

| Component | File | Description |
|-----------|------|-------------|
| **Gymnasium Environment** | `core/talos_env.py` | Observation Space (6-dim): normalized hour, 3 API usage ratios, error/low-score streaks. Action Space (4): ArXiv, OpenAlex, Semantic Scholar, Sleep. |
| **DRL Agent** | `core/drl_agent.py` | 3-layer LSTM (128→64→32) with LayerNorm + Dueling heads (V + A). Online + Target networks, soft updates (τ=1e-3), experience replay (deque, 10K capacity). |
| **Training Loop** | `scripts/train_agent.py` | Interactive episode selection (50/100/500/1000), profile-aware DB, real-time timing with ETA. |
| **GPU Acceleration** | RTX 4070, CUDA 12.1 | CuDNN optimization: `flatten_parameters()` before every LSTM forward pass, networks permanently in `.train()` mode to avoid mode-lock errors. **10x speedup** over CPU. |

**CuDNN Challenge:** The RTX 4070 initially threw `cudnn RNN backward can only be called in training mode` when `act()` (inference) and `learn()` (training) shared the same LSTM. Solution: removed all `.eval()` calls, kept both networks permanently in `.train()` mode, used `torch.no_grad()` only for gradient suppression — not mode switching.

### 2.3 Phase 2: Meta-Optimization & Offline Training

**The Wolf Pack** — Grey Wolf Optimizer (GWO) for hyperparameter tuning, inspired by wolf pack hunting behavior.

| Component | File | Description |
|-----------|------|-------------|
| **GWO Optimizer** | `scripts/gwo_rl_optimizer.py` | 15 wolves, 50 iterations. Search space: LR∈[1e-5, 1e-3], γ∈[0.5, 0.99], ε_decay∈[0.9, 0.999]. Fitness = -avg_reward (GWO minimizes). |
| **Offline Training** | `train_agent.py` | Uses **real paper scores** from the database (3,849 records, mean 3.49) instead of simulated random scores. |
| **JSON Export** | `models/gwo_best_params.json` | Saves best hyperparameters (LR, γ, ε_decay, fitness, reward, iterations, time) for reproducibility and academic papers. |

**Architecture insight:** The GWO fitness function evaluates each wolf by running 30 fast episodes × 200 steps *without learning* (pure exploration, ε=1.0). This tests the raw environment dynamics — how well a random policy performs under different hyperparameter regimes — rather than training convergence speed.

### 2.4 Phase 4: Autonomous Service & Notifications

**The 24/7 Guardian** — A background research agent that never sleeps, running at OS-level LOW priority.

| Component | File | Description |
|-----------|------|-------------|
| **Notifier** | `core/notifier.py` | Multi-channel: Telegram Bot API, Discord Webhooks (2000-char truncation), SMTP Email (STARTTLS). All fire-and-forget — never crashes the caller. |
| **Autonomous Service** | `scripts/talos_service.py` | Interactive reporting (Silent/Normal/Verbose), daily reports in 3 formats (JSON+MD+HTML), weekly email digest every Friday 17:00. |
| **Service API** | `scripts/talos_service_api.py` | Micro-Flask server on port 5002. `GET /api/status` and `GET /api/report`. |

### 2.5 Baseline Reports & Visualization

**The Pre-DRL Snapshot** — Academic-quality reports capturing the knowledge base state *before* the DRL agent alters the distribution.

| Feature | Tool | Capability |
|---------|------|------------|
| **Score Distribution** | Histogram + KDE | Mean 3.49, Elite (≥8) 3.0%, 25-bin resolution |
| **Quad-Layer Averages** | Bar chart | Strategic, Operational, Tactical, Playground |
| **Source Distribution** | Pie chart | Top 8 sources + Other |
| **Embedding Coverage** | Horizontal bar | Ollama vs Gemini model counts |
| **Academic Mode** | `--academic` flag | 600 DPI, serif fonts (Times New Roman), muted palette — IEEE/Springer ready |

---

## 3. v5.1.0 — The Insights UI (COMPLETED ✅)

With the AI Core stable, v5.1.0 focused on **visibility and usability** — bringing the DRL ecosystem to the user through both terminal and browser interfaces.

### 3.1 Streamlit DRL Agent Dashboard

| Section | Content |
|---------|---------|
| **GWO Optimization Results** | 4 metric cards (LR, γ, ε_decay, Best Fitness) from `gwo_best_params.json` |
| **Agent Training Status** | Checks for `dddqn_trained.pth`, shows success/warning with file size |
| **Reward Progression** | Upward-trending `st.line_chart` simulating 500 training episodes |
| **Training Details** | 2-column table: architecture, hyperparameters, GPU specs |
| **Load GWO Parameters** | Button saves params to `st.session_state` for use in training |

### 3.2 TUI Reorganization

| Change | Before | After |
|--------|--------|-------|
| **DRL Training** | Standalone option (confusing placement) | Analysis & Insights (Option 9) |
| **DRL Agent Status** | Did not exist | Diagnostics → Option 7 (Rich-formatted panel) |
| **Compare Baselines** | Did not exist | Analysis → Option 10 (Δ comparison of Total/Elite/Avg) |
| **Menu size** | 12 items | 13 items (expanded) |

### 3.3 Project Documentation

| Document | Status |
|----------|--------|
| **ROADMAP.md** | Rewritten with architectural narrative |
| **CHANGELOG_EN.md** | v5.1.0 section added |
| **CHANGELOG_GR.md** | v5.1.0 section added |

---

## 4. v5.2.0 — Onboarding & Dynamic Orchestration (COMPLETED ✅)

This version transforms TALOS into a **fully guided research platform** with a 4-step onboarding wizard, research pivot workflow, and a fundamentally upgraded DRL stack supporting all 14 sources dynamically.

### 4.1 Onboarding & User Experience

| Feature | Description | Status |
|---------|-------------|--------|
| **Onboarding Wizard** | 4-step guided wizard: Profile → Research Domain → PYTHIA → Launch | ✅ Complete |
| **First-Run Detection** | Auto-detects new installations, wizard replaces dashboard | ✅ Complete |
| **Research Pivot** | Interactive wizard for users whose research interests shifted | ✅ Complete |
| **Research Pivot GUI** | Button in Profile & Settings for in-place recalibration | ✅ Complete |

### 4.2 Dynamic DRL Stack (14-Source Upgrade)

| Component | Change | Status |
|-----------|--------|--------|
| **TalosEnv v2.0** | Dynamic N-source environment (was hardcoded 3) | ✅ Complete |
| **DRL Agent v2.0** | Dynamic state_dim/action_dim, metadata save/load | ✅ Complete |
| **Daemon v2.0** | Profile-aware, dynamic source mapping | ✅ Complete |
| **Live Agent v2.0** | Dynamic source class import, all 14 APIs | ✅ Complete |

### 4.3 Documentation

| Document | Change | Status |
|----------|--------|--------|
| **PROJECT_MAP.md** | Major update — 7 new modules documented, 166→183 functions matched | ✅ Complete |
| **.clinerules** | Version sync enforcement rule | ✅ Complete |
| **CHANGELOG_EN.md** | v5.2.0 section | ✅ Complete |
| **CHANGELOG_GR.md** | v5.2.0 section | ✅ Complete |

### 4.4 Files Changed

| File | Change |
|---|---|
| `app.py` | Onboarding Wizard, Research Pivot, first-run detection |
| `core/talos_env.py` | v2.0 — Dynamic N-Source Environment |
| `core/drl_agent.py` | v2.0 — Dynamic agent, metadata save/load |
| `scripts/talos_service.py` | v2.0 — Profile-aware daemon |
| `scripts/talos_live_agent.py` | v2.0 — Dynamic live agent |
| `scripts/train_agent.py` | Dynamic source display |
| `scripts/research_pivot.py` | **NEW** — Research Pivot Wizard |

**Total: 8 files changed, 1 new file**

---

## 5. v5.3.1 — Provider-Aware DRL & Live Agent Refactoring (COMPLETED ✅)

**The DRL Awakening** — The Live DRL Agent undergoes a complete architectural overhaul with modular `core/` components, a provider-aware observation space (tracking Gemini/DeepSeek/HuggingFace/Local limits), GWO-optimized hyperparameters, tier-based Gemini rate limits, and a cooldown mechanism to prevent deterministic action loops.

| Component | Technology | Purpose |
|-----------|-----------|---------|
| `core/live_agent_sources.py` | Dynamic import + module scanning | Auto-discovers 14 source classes regardless of naming conventions |
| `core/live_agent_orchestrator.py` | Dense action mapping + cooldown | Core loop with 5-step lockout for negative-reward actions, ε=0.05 |
| `core/talos_env.py` v3.0 | 4 provider ratios in observation | Agent learns to respect provider rate limits (free tier: 5 RPM) |
| `core/drl_agent.py` v2.1 | GWO hyperparameters + load() pre-check | LR=4.735e-05, GAMMA=0.575, weights_only=True |
| `config.json` provider_limits | Tier-based config | Free/tier1/tier2 Gemini, DeepSeek, HuggingFace, Local |
| `models/dddqn_trained.pth` | 14-source retraining | state_dim=21, action_dim=15, avg reward 2220.5 (+30.9% over baseline) |

**Key achievements:**
- 8 broken class names fixed (DBLP→DBLPSource, IEEE→IEEEXploreSource, etc.)
- 3 critical bugs resolved (sparse mapping, load crash, hour normalization)
- 530-line monolith → 110-line entry + 2 reusable `core/` modules
- Cooldown mechanism prevents deterministic loops (e.g., Springer returning empty)
- All emoji replaced with ASCII tags for academic output

### 5.1 Files Changed
| File | Status |
|------|--------|
| `core/live_agent_sources.py` | **NEW** — Source discovery (40 lines, 2 functions) |
| `core/live_agent_orchestrator.py` | **NEW** — Main loop + cooldown (420 lines, 6 functions) |
| `core/drl_agent.py` | v2.0 → v2.1 — GWO params, load() pre-check |
| `core/talos_env.py` | v2.0 → v3.0 — Provider-aware state (21-dim obs) |
| `core/ai_manager.py` | v3.6 — `_ensure_local_model()` reads LOCAL_MODEL_NAME |
| `scripts/talos_live_agent.py` | v2.0 → v3.1 — Thin entry (530→110 lines) |
| `scripts/drl_trainer.py` | v1.0 → v1.1 — GWO EPS_DECAY, save path fix |
| `config.json` | Added gemini_tier, provider_limits, 3 query keys |
| `PROJECT_MAP.md` | v5.3.0 → v5.3.1 — 7 core modules, 61 files |
| `CHANGELOG_EN.md`, `CHANGELOG_GR.md`, `README.md` | v5.3.1 entries |

### 5.2 Training Results
| Metric | v5.2.0 (3 sources) | v5.3.1 (14 sources) |
|---|---|---|
| State dimension | 6 | 21 |
| Action dimension | 4 | 15 |
| Sources | 3/14 | 14/14 |
| Avg reward | 1695.8 | 2220.5 |
| GWO improvement | — | +30.9% |
| Provider tracking | None | 4 ratios |

---

## 6. v5.3.0 — Automated Documentation (COMPLETED ✅)

### 5.1 `scripts/generate_docs.py` v1.0

| Component | Description | Status |
|-----------|-------------|--------|
| **generate_docs.py** | Iterates through all `.py` files in `core/` and `scripts/`, sends each to local Ollama (`/api/generate`), saves Greek Markdown in `docs/` | ✅ Complete |
| **load_configuration()** | Reads `OLLAMA_MODEL` → `LOCAL_MODEL_NAME` → `gemma4` fallback, plus `OLLAMA_HOST` for custom endpoints | ✅ Complete |
| **get_python_files()** | Recursively discovers all `.py` files in given directories, sorted alphabetically | ✅ Complete |
| **generate_documentation()** | POSTs source code to Ollama with 120s timeout, returns Greek Markdown or None on failure | ✅ Complete |
| **save_documentation()** | Creates `docs/` directory, writes UTF-8 Markdown as `{basename}_doc.md` | ✅ Complete |
| **main()** | Orchestrator with tqdm progress bar, per-file try/except, 1s delay between requests, final summary | ✅ Complete |
| **Prompt** | English instruction: "Act as a Senior Python Architect..." → output entirely in Greek | ✅ Complete |
| **Robustness** | Timeout handling, connection error handling, JSON decode error handling, per-file resilience (one failure never aborts the batch) | ✅ Complete |

**Model:** Uses local Ollama (default: `gemma4`). Zero cost, offline, full privacy — source code never leaves the local machine.

**Why Greek?** The PhD thesis and academic papers are written in Greek/English. Having the codebase documented in Greek ensures the researcher can fluently explain technical decisions during the defense and in the methodology sections of papers.

### 5.2 Integration with Existing Tools

The generated documentation complements:
- **`.clinerules`** Progressive Documentation Rule (English — for AI agents)
- **`PROJECT_MAP.md`** (English — architectural blueprint)
- **`docs/*.md`** (Greek — for the researcher and thesis)
- **New `.env` key `OLLAMA_MODEL`** added to `example.env`

### 5.3 Files Changed

| File | Change |
|------|--------|
| `scripts/generate_docs.py` | **NEW** — 197 lines, 5 functions |
| `PROJECT_MAP.md` | Section 4.7 entry, version v5.2.1→v5.3.0, file count 58→59, dependency graph |
| `example.env` | Added `OLLAMA_MODEL` key |
| `CHANGELOG_EN.md` | v5.3.0 entry |
| `CHANGELOG_GR.md` | v5.3.0 entry |

**Total: 1 new file, 4 updated files**

---

## 6. v5.4.0 — Deployment (UPCOMING 📅)

### 6.1 Standalone Executable

| Component | Description |
|-----------|-------------|
| **PyInstaller Packaging** | Bundle TALOS into a single `.exe` for Windows |
| **Zero-Touch Installation** | End users double-click and run — no Python, no conda, no dependencies |
| **Embedded Models** | Option to include a small local LLM for fully offline operation |

### 6.2 Cross-Platform Support

| Platform | Method |
|----------|--------|
| **Windows** | PyInstaller `.exe` |
| **Linux** | AppImage / Flatpak |
| **macOS** | `.app` bundle |

---

## 7. v6.0.0+ — The Distributed Ecosystem (FUTURE 🔮)

The v6.0 series represents the **third generation** of TALOS — decoupling the monolith into a distributed microservice ecosystem with a modern cross-platform UI.

### 7.1 Architecture Decoupling

| Component | Technology | Description |
|-----------|-----------|-------------|
| **Headless Backend** | FastAPI | RESTful microservice with async endpoints for search, evaluation, and embeddings |
| **Database Layer** | PostgreSQL + pgvector | Migration from SQLite for concurrent access and vector similarity search |
| **Message Queue** | Redis | Asynchronous job processing for long-running searches and enrichment |

### 7.2 Cross-Platform Frontend

| Component | Technology | Description |
|-----------|-----------|-------------|
| **Desktop App** | Flutter | Cross-platform (Windows, Linux, macOS, iOS, Android) |
| **Dark/Light Themes** | Material Design 3 | Professional academic aesthetic |
| **Real-Time Updates** | WebSocket | Live dashboard updates as the agent discovers papers |

### 7.3 Local RAG (Retrieval-Augmented Generation)

| Feature | Description |
|---------|-------------|
| **Chat with Your Papers** | Ask questions about papers in your library — the system retrieves relevant passages and synthesizes answers |
| **PDF Ingestion** | Extract text, figures, and tables from downloaded PDFs |
| **Knowledge Graph** | Build a semantic graph connecting papers by citations, topics, and methods |

### 7.4 Advanced Visualization

| Feature | Description |
|---------|-------------|
| **3D K-Means Clustering** | Interactive 3D scatter plots of the knowledge base, color-coded by cluster and score |
| **Citation Network 3D** | Force-directed graph of citation relationships in WebGL |
| **Timeline Animation** | Animated view of research trends over time |

---

## 8. Summary Version Table

| Version | Codename | Focus | Status |
|:--------|:---------|:------|:-------|
| **v1.0 – v4.11** | The Aggregator | Search, Evaluate, Store | ✅ Complete |
| **v5.0.0** | The AI Core | Hybrid Embeddings + DRL Agent + GWO | ✅ Complete |
| **v5.0.1** | GWO Export | JSON output for hyperparameters | ✅ Complete |
| **v5.1.0** | The Insights UI | DRL Dashboard + TUI Reorganization | ✅ Complete |
| **v5.2.0** | The Live Agent | Live API Routing + PDF Downloader | ⚡ Current |
| **v5.3.0** | Auto-Docs | Local LLM Greek documentation generator | ✅ Complete |
| **v5.3.1** | DRL Live Agent | Provider-Aware Orchestration + GWO hyperparams | ✅ Complete |
| **v5.3.2** | Pluggable Networks | DRL network architecture extraction | ✅ Complete |
| **v5.4.0** | Deployment | PyInstaller .exe packaging | 📅 Upcoming |
| **v6.0.0+** | ALEXANDRIA | FastAPI + Flutter + RAG + 3D Viz | � Future |

---

> **Project TALOS** — From Aggregator to Autonomous Research Architect.
> Built with ❤️ in Kalamata, Greece.
> © 2026 Christos Smarlamakis