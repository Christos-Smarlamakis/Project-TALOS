# Project TALOS -- Strategic Roadmap & Architecture Chronicle

This document serves as both the **development compass** and the **architectural narrative** of Project TALOS. It chronicles the evolution from a research aggregator to a fully autonomous, DRL-driven research intelligence platform -- and maps the path forward toward Project ALEXANDRIA.

> **Current Version:** v5.10.8 (Enterprise TUI Overhaul & Academic Aesthetics)
> **Last Updated:** 2026-08-22

---

## 1. The Vision: From Aggregator to Autonomous Research Architect

Project TALOS was born from a simple question: **what if a literature review system could think for itself?**

The exponential growth of academic publishing (over 5 million papers per year) has broken the traditional Systematic Literature Review (SLR) workflow. A PhD researcher simply cannot manually monitor, evaluate, and synthesize the firehose of daily publications. TALOS answers this challenge by evolving through three generations:

1. **Gen 1 (v1-v4): The Aggregator** -- Searched 14 APIs, evaluated papers with AI, stored results in SQLite.
2. **Gen 2 (v5.0-v5.9): The Orchestrator** -- A Deep Reinforcement Learning agent that learns to select optimal APIs in real-time, backed by Multi-Tier LLM routing and Autonomous Red Testing.
3. **Gen 3 (v5.10-v6.0+): The Topological Ecosystem (Project ALEXANDRIA)** -- Automated PRISMA 2020 pipelines (PlanEval/DSPy), Bi-Level GWO AutoRL, Knowledge Graphs, and SYNAPSE Event Mesh interoperability.

---

## 2. v5.0.x -- The AI Core (COMPLETED)

The v5.0 series represents a **paradigm shift** -- TALOS ceased being a passive aggregator and became an **active, learning orchestrator**.

### 2.1 Phase 0: Multi-Provider Hybrid Embeddings
| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Ollama Embeddings** | `nomic-embed-text` (local) | Free, offline, zero-latency embeddings |
| **Gemini Embeddings** | `gemini-embedding-001` (cloud) | High-precision 768-dim vectors, `RETRIEVAL_DOCUMENT` task type |
| **Embeddings Table** | SQLite with B-tree indexes | Multi-model vector storage, backward-compatible |
| **Migration Script** | `db_embedding_upgrade.py` | Seamlessly migrated 3,849 legacy records to the new schema |
| **Google GenAI GA SDK** | `google.genai.Client` | Future-proof API |

### 2.2 Phase 1: Deep Reinforcement Learning Stack
| Component | File | Description |
|-----------|------|-------------|
| **Gymnasium Environment** | `src/ai/drl/talos_env.py` | Observation Space (6-dim): normalized hour, API usage ratios, streaks. Action Space (4): ArXiv, OpenAlex, Semantic Scholar, Sleep. |
| **DRL Agent** | `src/ai/drl/drl_agent.py` | 3-layer LSTM (128-64-32) with LayerNorm + Dueling heads (V + A). Double Dueling DQN, soft updates (t=1e-3), replay memory (10K). |
| **Training Loop** | `src/ai/drl/drl_trainer.py` | Interactive episode selection, profile-aware DB, real-time timing. |
| **GPU Acceleration** | RTX 4070, CUDA 12.1 | CuDNN optimization: `flatten_parameters()` before LSTM forward pass. **10x speedup** over CPU. |

---

## 3. v5.1.0 -- The Insights UI (COMPLETED)
- GWO optimization metrics display.
- Agent training status and reward progression visualization.
- Training details hardware table.

---

## 4. v5.2.x -- Onboarding & Dynamic Orchestration (COMPLETED)
- 4-step guided onboarding wizard.
- First-run auto-detection.
- Interactive research pivot workflow (`src/ai/llm/research_pivot.py`).
- Dynamic DRL stack supporting N sources dynamically.

---

## 5. v5.3.x -- DRL Scientific Integrity & UI Hardening (COMPLETED)
- **v5.3.1**: DRL Live Agent with provider-aware orchestration and 5-step cooldown lockout.
- **v5.3.2**: Pluggable network architecture (`src/ai/drl/drl_networks.py`).
- **v5.3.3**: Universal documentation rule, light-only UI theme.
- **v5.3.4**: Mythological names replaced with academic module titles.
- **v5.3.5**: GWO v2.0 real fitness evaluation (canonical Mirjalili 2014 algorithm).
- **v5.3.6**: Ctrl+C robustness and CLI hardening across all entry points.
- **v5.3.7**: Full 9.5-hour GWO hyperparameter optimization run (`LR=3.361e-05`, `GAMMA=0.6983`, `EPS_DECAY=0.9202`).

---

## 6. v5.4.x -- DDD Migration & Root Cleanup (COMPLETED)
- **v5.4.0**: Domain-Driven Design package layout, all source files relocated to `src/` hierarchy (`src/core`, `src/ingestion`, `src/ai`, `src/analysis`, `src/utils`, `src/api`).
- **v5.4.1**: Root directory cleanup, `docs/` and `tools/` structure.

---

## 7. v5.5.x -- FastAPI REST Facade & Ecosystem Coverage (COMPLETED)
- **v5.5.0**: FastAPI REST facade with 8 core endpoints, database path resolution fix.
- **v5.5.1**: Frontend DX endpoints (GWO history for Recharts, architecture graph HTML).
- **v5.5.2**: 100% ecosystem API coverage (14 total endpoints, 16 Pydantic models).

---

## 8. v5.6.x -- Streamlit Deprecation & Headless Modernization (COMPLETED)
- **BREAKING**: Streamlit fully deprecated. Sole frontend: React 18 + Tailwind CSS + Shadcn UI.
- FastAPI upgraded to 15 endpoints (+`/api/v1/capabilities`).
- Created `docs/SYSTEM_CAPABILITIES_MASTER.md` and `.html`.
- Enforced 12-file documentation synchronicity rule.

---

## 9. v5.7.x -- Master Standard v2.0 & SYNAPSE Protocol (COMPLETED)
- Upgraded `.clinerules` to 8-Point Constitution v2.0 and 15-file sync rule.
- Scaffolded SYNAPSE Event-Driven Protocol (`src/integration/synapse_client.py`, `src/api/synapse_routes.py`).
- Port reallocation: TALOS FastAPI on port 8001, SYNAPSE bus on port 8000.
- Created `run_talos.bat` and `run_talos.sh` automated launchers.

---

## 10. v5.8.x -- Multi-Tier LLM Routing, Launchers & Enterprise TUI (COMPLETED)
- **v5.8.0 - v5.8.3**: Three-tier LLM routing (Fast Edge Neutrino-8B on port 11435, Heavy Reasoning Qwen2.5-14B on port 11434, Cloud Provider). Native MCP Server (`src/mcp_server.py`, 4 tools) for Cherry Studio. Isolated interim UI provisioner.
- **v5.8.4 - v5.8.9**: Rich TUI Dashboard in `talos.py`. Model Manager CLI integration. Auto-Conda detection and detached POSIX daemons in launchers. Expanded test suite (96+ unit tests). 15-file sync rule solidified.

---

## 11. v5.9.x -- Chaos Engineering, Universal Cloud Mesh & Hardening (COMPLETED)
- **v5.9.0 - v5.9.7**: Autonomous System Tester (`src/ai/testing/autonomous_tester.py`) with Non-Stationary Epsilon-Greedy MAB and LLM-as-a-Judge diagnostics. Scaled from 4 to 70+ dynamic test arms. Added `/api/v1/tester` REST endpoints.
- **v5.9.8 - v5.9.13**: Clickable terminal hyperlinks. Local-to-local fallback (CPU tier -> GPU Ollama before cloud). Vendored Graphify AST engine integration (`src/analysis/graphify_adapter.py`) with Academic Print Light Mode CSS injection.
- **v5.9.14 - v5.9.15**: Docker infrastructure overhaul (`host.docker.internal` local connectivity, `docs/DOCKER.md`). Fixed `pandas 3.0` DLL incompatibility. Silent fast boot (purged blocking startup model verification). Reconciled Section 7 dependency map.
- **v5.9.16**: Renamed tester to **Autonomous Red Tester** (`src/ai/testing/red_tester.py`). Implemented Deep API Fuzzing arms and LLM Context Window Truncation (2,000 chars limit).
- **v5.9.17**: Universal Rich TUI enforcement and Enterprise Logging (`src/utils/logger.py` with `RichHandler` and `RotatingFileHandler` to `data/logs/talos_system.log`).
- **v5.9.18**: **Universal Cloud Mesh** -- unified 8 OpenAI-compatible cloud providers (NVIDIA NIM 1M, Groq LPU, Cerebras, GitHub Models, Mistral AI, OpenRouter, DeepSeek, HuggingFace) alongside Google Gemini SDK. Model Manager Cloud TUI with `[ACTIVE]` vs `[UNCONFIGURED]` status indicators.

---

## 12. v5.10.x -- The Topological Space & Ingestion Expansion (CURRENT PHASE)

The v5.10.x series transitions Project TALOS from an aggregator to a fully adaptive, multi-agent cognitive architecture, paving the way for Project ALEXANDRIA.

| Sub-Version | Codename | Focus | Status |
|:------------|:---------|:------|:-------|
| **v5.10.0** | Ingestion Expansion | Added OpenReview (Source #15, ICLR/NeurIPS peer reviews via `openreview-py`) and OpenAIRE (Source #16, EU Horizon open access). Expanded `daily_search` and `historic_search` to 16 sources. Added 34 unit tests. | Complete |
| **v5.10.1** | DRL Environment Scaling | Scaled Gymnasium environment (`talos_env.py`) to **23 State Dimensions** and **17 Action Dimensions** (16 sources + Sleep). Dynamic DuelingLSTM network auto-reconstruction. | Complete |
| **v5.10.2** | LLM Router & GWO Shaper | Created `LLMRouterSubAgent` (`src/ai/drl/llm_router_subagent.py`) implementing Contextual Bandit decision policy. Created `GWOLLMRouterRewardShaper` (`src/ai/optimizers/gwo_llm_router_reward_shaper.py`) for Bi-Level multi-objective reward weight optimization. Renamed hyperparameter tuner to `gwo_foraging_hyperparameter_tuner.py`. Implemented Interactive 16-Source Checkbox TUI in `talos.py`. | Complete |
| **v5.10.3** | Hierarchical DRL | Integrated `LLMRouterSubAgent` directly into 24/7 research daemon (`talos_service.py`), live foraging orchestrator (`live_agent_orchestrator.py`), and search pipelines. Implemented dynamic SWE-bench relative quality normalization ($Q_p = \text{Score}_p / \max_k \text{Score}_k$). | Complete |
| **v5.10.4** | Model Discovery & SYNAPSE | Created `ModelDiscoveryEngine` (`src/ai/llm/model_discovery.py`) with local `data/model_benchmarks.json` cache and live API model scanning. Exposed 19th REST endpoint `GET /api/v1/synapse/status`. | Complete |
| **v5.10.5** | Dynamic Provisioner | Created `ModelProvisioner` (`src/utils/model_provisioner.py`) with 3-tier path resolution (custom vault `FAST_EDGE_MODEL_PATH`, in-tree `models/`, auto-download) and JIT auto-pull for Ollama and HuggingFace Hub with self-healing fallback. 296 Pytest tests passing. | Complete |
| **v5.10.6** | Daemon OS Autostart & Orchestrator | Added `src/utils/daemon_autostart.py` (Windows Startup shortcut), interactive daemon pre-flight in `talos.py`, and `daemon_target_sources` injection into `talos_live_agent.py`. | Complete |
| **v5.10.7** | OPTICA Bridge Integration | Added `src/integration/optica_client.py` (`OpticaClient`) REST client to offload cnsplots/PyVis graphics to Project OPTICA (port 8002); new "Data Visualizations (via OPTICA)" TUI menu option. | Complete |
| **v5.10.8** | Enterprise TUI Overhaul & Academic Aesthetics | Unified questionary prompt style (Cyan/Teal #00ced1 selection colors, bright-white separators, IEEE blue #4a9eff question mark) canonicalized in `src/utils/ui_theme.py` and applied to every CLI prompt. | Complete |
| **v5.10.9** | DSPy PRISMA Pipeline | Automated 4-stage PRISMA 2020 Systematic Literature Review pipeline (`src/ai/dspy_prisma_pipeline.py`) leveraging PlanEval architecture (Fast Edge Planner/Evaluator + Heavy Reasoning Executor). | Next |
| **v5.10.10** | CORTEX & n8n Gateway | Live arXiv RSS & text evaluation Discord Bot (`src/integration/discord_evaluator.py`) and SYNAPSE n8n Workflow Gateway templates (`templates/n8n_workflows/`). | Upcoming |

---

## 13. v6.0.0+ -- Project ALEXANDRIA: The Distributed Ecosystem (FUTURE)

Project ALEXANDRIA marks the full desktop and distributed release of the platform:

| Component | Technology | Description |
|-----------|-----------|-------------|
| **Desktop Application** | Tauri / Electron | 100% standalone offline `.exe` desktop application wrapping React 18 + Shadcn UI |
| **Database Layer** | PostgreSQL + pgvector | High-concurrency vector database replacing local SQLite for multi-user labs |
| **Semantic Knowledge Graphs** | Graphify AST + Leiden | Multi-document topological concept extraction and interactive 3D graph visualization |
| **Offline Deep MoE Reasoning** | Kimi K3 C-Engine | 2.78-Trillion parameter MoE inference running on CPU in 8.24GB RAM for deep offline paper synthesis |
| **Hardware Nexus** | AMD AI Halo (128GB UMA) | High-throughput local research workstation serving as the central compute node for TALOS, ALEXANDRIA, and ATHENA |

---

## 14. Summary Version Table

| Version | Codename | Primary Focus | Status |
|:--------|:---------|:--------------|:-------|
| **v1.0 - v4.11** | The Aggregator | 14-source scraping, Gemini AI evaluation, SQLite storage | Complete |
| **v5.0.0** | The AI Core | Hybrid Embeddings, DDDQN Agent, GWO Hyperparameter Optimizer | Complete |
| **v5.1.0** | The Insights UI | DRL Terminal & Browser Dashboard, GPU Acceleration | Complete |
| **v5.2.0** | The Live Agent | 14-source Dynamic DRL live agent, Onboarding Wizard | Complete |
| **v5.3.x** | Scientific Integrity | GWO v2.0 canonical math, DuelingLSTM extraction, CLI hardening | Complete |
| **v5.4.x** | DDD Migration | Domain-Driven Design package layout (`src/` hierarchy) | Complete |
| **v5.5.x** | REST API Facade | Headless FastAPI backend (14 endpoints, 16 Pydantic models) | Complete |
| **v5.6.0** | Headless Standard | Streamlit fully deprecated, React 18 sole frontend, 15 endpoints | Complete |
| **v5.7.2** | Constitution v2.0 | SYNAPSE Event Bus (:8000), FastAPI port 8001, 15-file sync rule | Complete |
| **v5.8.x** | Multi-Tier TUI | 3-Tier LLM routing, Native MCP Server, Rich TUI Dashboard | Complete |
| **v5.9.x** | Red Team & Mesh | Autonomous Red Tester (Deep Fuzzing), Universal Cloud Mesh (9 Providers), Enterprise Logger | Complete |
| **v5.10.0** | Ingestion Expansion | 16 Academic Sources (+OpenReview, +OpenAIRE), 225 Pytest tests | Complete |
| **v5.10.1** | DRL 17-Actions | 23 State Dimensions, 17 Action Dimensions, Environment Scaling | Complete |
| **v5.10.2** | Sub-Agent & Shaper | `LLMRouterSubAgent` Contextual Bandit, Bi-Level GWO Reward Shaper, 16-Source Checkbox TUI | Complete |
| **v5.10.3** | HMADRL Orchestrator | Hierarchical DRL coupling in Daemon, Live Agent, Search pipelines, Dynamic SWE-bench $Q_p$ | Complete |
| **v5.10.4** | Model Discovery | `ModelDiscoveryEngine`, local JSON cache, 19th REST endpoint (`GET /api/v1/synapse/status`) | Complete |
| **v5.10.5** | Dynamic Provisioner | `ModelProvisioner`, 3-tier path resolution (`FAST_EDGE_MODEL_PATH`), JIT auto-pull, 296 tests | Complete |
| **v5.10.6** | Daemon OS Autostart & Orchestrator | Windows Startup shortcut, daemon pre-flight, source injection | Complete |
| **v5.10.7** | OPTICA Bridge Integration | `OpticaClient` REST client offloading cnsplots/PyVis to OPTICA (8002), TUI plot menu | Complete |
| **v5.10.8** | Enterprise TUI Overhaul & Academic Aesthetics | Unified Cyan/Teal questionary style applied to every CLI prompt | Complete |
| **v5.10.9** | DSPy PRISMA Pipeline | Automated 4-stage PRISMA 2020 Systematic Literature Review pipeline via PlanEval architecture | Next |
| **v5.10.10** | CORTEX & n8n Gateway | Discord evaluation bot, SYNAPSE n8n workflow templates | Upcoming |
| **v6.0.0+** | Project ALEXANDRIA | Tauri Desktop App, PostgreSQL+pgvector, 3D Knowledge Graphs, Kimi K3 C-Engine | Future |

---

> **Project TALOS** -- From Aggregator to Autonomous Research Architect.
> Built in Greece.
> (C) 2026 Christos Smarlamakis