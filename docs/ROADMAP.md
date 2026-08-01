# Project TALOS -- Strategic Roadmap & Architecture Chronicle

This document serves as both the **development compass** and the **architectural narrative** of Project TALOS. It chronicles the evolution from a research aggregator to a fully autonomous, DRL-driven research intelligence platform -- and maps the path forward.

> **Current Version:** v5.9.3 (Autonomous System Tester, RL Chaos Fuzzer, LLM-as-a-Judge Diagnostics, Rich Q-Table, 18 Endpoints, 11-Option TUI)
> **Last Updated:** 2026-08-01

---

## 1. The Vision: From Aggregator to Autonomous Research Architect

Project TALOS was born from a simple question: **what if a literature review system could think for itself?**

The exponential growth of academic publishing (over 5 million papers per year) has broken the traditional Systematic Literature Review (SLR) workflow. A PhD researcher simply cannot manually monitor, evaluate, and synthesize the firehose of daily publications. TALOS answers this challenge by evolving through three generations:

1. **Gen 1 (v1-v4): The Aggregator** -- Searched 14 APIs, evaluated papers with AI, stored results in SQLite.
2. **Gen 2 (v5.0): The Orchestrator** -- A Deep Reinforcement Learning agent that learns to select optimal APIs in real-time.
3. **Gen 3 (v6.0+): The Ecosystem** -- A distributed microservice with RAG capabilities, cross-platform UI, and 3D knowledge visualization.

---

## 2. v5.0.x -- The AI Core (COMPLETED)

The v5.0 series represents a **paradigm shift** -- TALOS ceased being a passive aggregator and became an **active, learning orchestrator**. This was the largest single update in project history, spanning four major phases and adding over 5,000 lines of code.

### 2.1 Phase 0: Multi-Provider Hybrid Embeddings

**The Semantic Brain** -- Before the agent could reason about papers, it needed to truly *understand* them through a dimension-agnostic embedding system.

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Ollama Embeddings** | `nomic-embed-text` (local) | Free, offline, zero-latency embeddings |
| **Gemini Embeddings** | `gemini-embedding-001` (cloud) | High-precision 768-dim vectors, `RETRIEVAL_DOCUMENT` task type |
| **Embeddings Table** | SQLite with B-tree indexes | Multi-model vector storage, backward-compatible with legacy `papers.embedding` column |
| **Migration Script** | `db_embedding_upgrade.py` | Seamlessly migrated 3,849 legacy records to the new schema |
| **Google GenAI GA SDK** | `google.genai.Client` | Future-proof API (NOT deprecated `google.generativeai`) |

**Key innovation:** The `semantic_search()` method filters cosine similarity by embedding model -- Ollama vectors are only compared against other Ollama vectors, Gemini against Gemini. This prevents cross-model semantic drift.

### 2.2 Phase 1: Deep Reinforcement Learning Stack

**The Orchestrator's Brain** -- A Double Dueling DQN (DDDQN) with LSTM that learns API foraging strategies from experience.

| Component | File | Description |
|-----------|------|-------------|
| **Gymnasium Environment** | `core/talos_env.py` | Observation Space (6-dim): normalized hour, 3 API usage ratios, error/low-score streaks. Action Space (4): ArXiv, OpenAlex, Semantic Scholar, Sleep. |
| **DRL Agent** | `core/drl_agent.py` | 3-layer LSTM (128-64-32) with LayerNorm + Dueling heads (V + A). Online + Target networks, soft updates (t=1e-3), experience replay (deque, 10K capacity). |
| **Training Loop** | `scripts/train_agent.py` | Interactive episode selection (50/100/500/1000), profile-aware DB, real-time timing with ETA. |
| **GPU Acceleration** | RTX 4070, CUDA 12.1 | CuDNN optimization: `flatten_parameters()` before every LSTM forward pass, networks permanently in `.train()` mode to avoid mode-lock errors. **10x speedup** over CPU. |

---

## 3. v5.1.0 -- The Insights UI (COMPLETED)

With the AI Core stable, v5.1.0 focused on **visibility and usability** -- bringing the DRL ecosystem to the user through both terminal and browser interfaces.

| Section | Content |
|---------|---------|
| **GWO Optimization Results** | 4 metric cards (LR, Gamma, Epsilon Decay, Best Fitness) from `gwo_best_params.json` |
| **Agent Training Status** | Checks for `dddqn_trained.pth`, shows success/warning with file size |
| **Reward Progression** | Upward-trending chart simulating 500 training episodes |
| **Training Details** | 2-column table: architecture, hyperparameters, GPU specs |

---

## 4. v5.2.x -- Onboarding & Dynamic Orchestration (COMPLETED)

This version transforms TALOS into a **fully guided research platform** with a 4-step onboarding wizard, research pivot workflow, and a fundamentally upgraded DRL stack supporting all 14 sources dynamically.

| Feature | Description | Status |
|---------|-------------|--------|
| **Onboarding Wizard** | 4-step guided wizard: Profile - Research Domain - PYTHIA - Launch | Complete |
| **First-Run Detection** | Auto-detects new installations, wizard replaces dashboard | Complete |
| **Research Pivot** | Interactive wizard for users whose research interests shifted | Complete |
| **Dynamic DRL Stack** | Dynamic N-source environment (was hardcoded 3), 14-source agent | Complete |

---

## 5. v5.3.x -- DRL Scientific Integrity & UI Hardening (COMPLETED)

| Version | Codename | Focus |
|---------|----------|-------|
| **v5.3.1** | DRL Live Agent | Provider-Aware Orchestration + GWO hyperparams |
| **v5.3.2** | Pluggable Networks | DRL network architecture extraction |
| **v5.3.3** | Light-Only Theme | Dark mode removal, universal docs rule |
| **v5.3.4** | Descriptive Names | Mythological names replaced with academic module titles |
| **v5.3.5** | DRL Sci. Integrity | GWO v2.0 real fitness, Canonical GWO, Batch 1 audit |
| **v5.3.6** | TUI/CLI Hardening | Ctrl+C robustness, dead menu fix, Batch 2 audit |
| **v5.3.7** | GWO Re-optimization | LR=3.361e-05, GAMMA=0.6983, 9.5h training |

---

## 6. v5.4.x -- DDD Migration & Root Cleanup (COMPLETED)

| Version | Codename | Focus |
|---------|----------|-------|
| **v5.4.0** | DDD Migration | `src/` package layout, all 55 files relocated |
| **v5.4.1** | Root Cleanup | `docs/` + `tools/` dirs, .gitignore negate patterns |

---

## 7. v5.5.x -- FastAPI REST Facade & Ecosystem Coverage (COMPLETED)

| Version | Codename | Focus |
|---------|----------|-------|
| **v5.5.0** | FastAPI + DB Fix | 8 REST endpoints (health, papers, semantic search, scrape/GWO triggers, task status) + Database path fix to `data/talos_research.db` |
| **v5.5.1** | Frontend DX | +2 endpoints: GWO history for Recharts, architecture graph HTML via FileResponse |
| **v5.5.2** | 100% Coverage | +4 endpoints: single-paper AI evaluation, query translation, top authors, bulk score recalculation -- **14 total endpoints (16 Pydantic models)** |

---

## 8. v5.6.x -- Streamlit Deprecation & Documentation Enforcement (COMPLETED)

| Version | Codename | Focus |
|---------|----------|-------|
| **v5.6.0** | Headless API + Docs | **BREAKING: Streamlit fully deprecated.** Deleted `app.py`, `.streamlit/`, `tools/_gui_runner.py`. Removed `streamlit` from `requirements.txt`. Sole frontend is React 18 + Tailwind CSS + Shadcn UI. FastAPI upgraded to 15 endpoints (+`/api/v1/capabilities`). Created `docs/SYSTEM_CAPABILITIES_MASTER.md` and `.html` (9-section structured reference). Enforced 12-file documentation sync rule in `.clinerules`. Created `docs/API_HANDOVER_FOTIS.md`, `docs/UX_UI_BLUEPRINT_FOTIS.md`, `docs/IP_PROTECTION_STRATEGY.md`. |

---

## 9. v5.7.x -- Master Standard v2.0 Alignment & Synapse Protocol (CURRENT)

| Version | Codename | Focus |
|---------|----------|-------|
| **v5.7.2** | Constitution v2.0 + Synapse | **Upgraded `.clinerules` to 8-Point Constitution v2.0.** Enforced 15-file documentation synchronization rule (added Timeline documents as files #8 and #9). Created `docs/TIMELINE_EN.md` and `docs/TIMELINE_GR.md` as authoritative historical records. **Scaffolded SYNAPSE Event-Driven Protocol:** `src/integration/synapse_client.py` (EventEmitter class) pushes JSON events to the SYNAPSE bus at port 8000; `src/api/synapse_routes.py` (FastAPI APIRouter) receives inbound commands via `POST /api/v1/synapse/webhook`. **Port reallocation:** TALOS FastAPI now on port 8001 (was 8000) to leave port 8000 for the SYNAPSE event bus. **Created `run_talos.bat`** at project root with 3-option menu (Full Setup, Start FastAPI Server on port 8001, Run Test Suite via pytest -v). Upgraded `src/api/main_api.py` module-level docstring to v5.7.2 standard with strict format. |

| Feature | Description |
|---------|-------------|
| **8-Point Constitution v2.0** | Zero Emojis Protocol, Air-Gapped Local-First, VRAM Containment, Agentic Rails, Verification-First, 15-File Sync, Synapse Protocol, Strict Module-level Docstrings |
| **Synapse Protocol** | EventEmitter (outbound: paper_discovered, paper_evaluated, etc.) + APIRouter (inbound webhook: trigger_search, trigger_evaluation, get_status, shutdown) for ALEXANDRIA ecosystem interoperability |
| **Port Reallocation** | TALOS FastAPI: 8001, SYNAPSE event bus: 8000 |
| **15-File Documentation Sync** | Upgraded from 12-file rule; Timeline documents (EN + GR) added as authoritative historical records |
| **Automated Batch Runner** | `run_talos.bat` at project root with 3-option menu; legacy `tools/start_talos.bat` preserved |
| **16 REST Endpoints** | 15 legacy endpoints + SYNAPSE webhook (`POST /api/v1/synapse/webhook`) |

---

## 10. v6.0.0+ -- The Distributed Ecosystem (FUTURE)

The v6.0 series represents the **third generation** of TALOS -- decoupling the monolith into a distributed microservice ecosystem with a modern cross-platform UI.

| Component | Technology | Description |
|-----------|-----------|-------------|
| **Headless Backend** | FastAPI | RESTful microservice with async endpoints (already started in v5.5.0, enhanced in v5.7.2, with multi-tier LLM routing in v5.8.9) |
| **Database Layer** | PostgreSQL + pgvector | Migration from SQLite for concurrent access and vector similarity search |
| **Cross-Platform Frontend** | Flutter | Desktop app (Windows, Linux, macOS, iOS, Android) |
| **Local RAG** | Ollama + Chroma | Chat with your papers, PDF ingestion, knowledge graph |
| **Advanced Viz** | Three.js / Deck.gl | 3D clustering, citation network graphs, timeline animations |
| **Deployment** | PyInstaller | Standalone `.exe` for zero-touch installation |

---

## 11. Summary Version Table

| Version | Codename | Focus | Status |
|:--------|:---------|:------|:-------|
| **v1.0 - v4.11** | The Aggregator | Search, Evaluate, Store | Complete |
| **v5.0.0** | The AI Core | Hybrid Embeddings + DRL Agent + GWO | Complete |
| **v5.1.0** | The Insights UI | DRL Dashboard + TUI Reorganization | Complete |
| **v5.2.0** | The Live Agent | Live API Routing + PDF Downloader | Complete |
| **v5.2.1** | Academic Conf. | GUI Redesign, Bilingual (EN/GR), CSS Theme | Complete |
| **v5.3.0** | Auto-Docs | 18-language documentation generator | Complete |
| **v5.3.1** | DRL Live Agent | Provider-Aware Orchestration | Complete |
| **v5.3.2** | Pluggable Nets | DRL network architecture extraction | Complete |
| **v5.3.3** | Light-Only Theme | Dark mode removal, universal docs rule | Complete |
| **v5.3.4** | Descriptive Names | Mythological to academic module titles | Complete |
| **v5.3.5** | DRL Sci. Integrity | GWO v2.0, Canonical GWO, Batch 1 | Complete |
| **v5.3.6** | TUI/CLI Hardening | Ctrl+C robustness, Batch 2 | Complete |
| **v5.3.7** | GWO Re-optimize | LR=3.36e-05, GAMMA=0.698, 9.5h | Complete |
| **v5.4.0** | DDD Migration | `src/` package layout, 55 files moved | Complete |
| **v5.4.1** | Root Cleanup | `docs/` + `tools/` dirs, .gitignore | Complete |
| **v5.5.0** | FastAPI + DB Fix | REST API (8 endpoints) + db path | Complete |
| **v5.5.1** | Frontend DX | +2 endpoints: GWO history + graph HTML | Complete |
| **v5.5.2** | 100% Coverage | +4 endpoints: eval + translate + authors + recalc | Complete |
| **v5.6.0** | Headless API + Docs | Streamlit deprecated, 15 endpoints, 12-file sync | Complete |
| **v5.8.9** | Multi-Tier TUI + Exec Modes | Model Manager Refactoring, Fast/Heavy/Cloud Tiers, System Execution Modes, Zero-Emojis, 29 tests | Complete |
| **v5.8.9** | Launcher Automation | Auto-Conda Detection, Background Window Spawning, POSIX Virtualenv | Complete |
| **v5.8.9** | Rich TUI + Model Manager | Rich Dashboard, Model Manager CLI Integration, 10-Option Menu, 173 Tests | Current |
| **v6.0.0+** | Distributed Eco. | Flutter + RAG + 3D Viz + PyInstaller | Future |

---

> **Project TALOS** -- From Aggregator to Autonomous Research Architect.
> Built in Kalamata, Greece.
> (C) 2026 Christos Smarlamakis
