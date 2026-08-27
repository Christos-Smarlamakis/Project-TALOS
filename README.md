﻿# Project TALOS (v5.10.11)

### **Tactical Agentic Literature Orchestration System**

> **An Autonomous Research Intelligence Platform -- Multi-Tier LLM Routing (CPU/GPU/Cloud), Headless FastAPI Backend with 19 REST Endpoints, SYNAPSE Event-Driven Protocol, RL-Driven Autonomous Red Tester with LLM-as-a-Judge Diagnostics, Academic Print Mode for AST Knowledge Graphs, React 18 + Tailwind CSS + Shadcn UI Frontend.**

[![IEEE Computer Society](https://img.shields.io/badge/IEEE_Computer_Society-WEIGD_Fund_Recipient_2026-006699?style=flat-square&logo=ieee&logoColor=white)](https://www.computer.org/volunteering/awards/scholarships/weigd-student-fund)
![Python](https://img.shields.io/badge/Python-3.11%2B-blue)
![License](https://img.shields.io/badge/License-AGPLv3-red)
[![DOI](https://zenodo.org/badge/1191928488.svg)](https://doi.org/10.5281/zenodo.19224912)
![Status](https://img.shields.io/badge/Status-Active%20Research-green)
![Methodology](https://img.shields.io/badge/Methodology-Scientometrics%20%7C%20AI%20Evaluation-teal)
![Maintained](https://img.shields.io/badge/Maintained%3F-yes-brightgreen.svg)
![Docker](https://img.shields.io/badge/Docker-Supported-2496ED?logo=docker)

---

## 1. Introduction: The Vision

In Greek mythology, **Talos** was a giant bronze automaton built to serve as the tireless guardian of Crete. **Project TALOS** embodies this spirit for the 21st century. It is not a mere literature aggregator but a **Research Intelligence Platform** that utilizes **AI Agents** to discover, evaluate, synthesize, and visualize scientific knowledge, significantly accelerating the **Systematic Literature Review (SLR)** process.

### The Problem
The exponential growth of scientific publications, especially in fields like *Drone Swarm Intelligence* and *AI*, makes manual monitoring impossible.

### The Solution
TALOS acts as an autonomous "Research Architect," filtering noise and highlighting strategic knowledge through a "Human-in-the-loop" agentic workflow.

---

## 2. Technical Architecture & Ecosystem

### A. Core Intelligence Layer (DRL-Powered)
- **DRL Agent (The Autonomous Orchestrator):** A **Double Dueling DQN with 3-layer LSTM** that learns to select the optimal academic API source in real-time. Trained on 3,849 real paper scores from the database with **RTX 4070 CUDA 12.1** acceleration. Features include:
  - **Gymnasium RL environment** (`src/ai/drl/talos_env.py`) -- Dynamic N-source Observation Space, Action Space (N + 1)
  - **Grey Wolf Optimizer** (`src/ai/optimizers/gwo_rl_optimizer.py`) for hyperparameter tuning
  - **24/7 Autonomous Service** (`src/ai/drl/talos_service.py`) -- background research agent with Telegram/Discord/Email notifications
- **Flask API server** (`src/api/talos_service_api.py`) -- real-time service status at `localhost:5002/api/status`
- **FastAPI REST API** (`src/api/main_api.py`) -- full REST facade with 19 endpoints at `localhost:8001`
  - Semantic search, paginated papers, scrape/GWO triggers with BackgroundTasks
  - Single-paper AI evaluation, natural-language to boolean query translation
  - GWO history for Recharts, architecture graph HTML, top authors for BarChart
  - Bulk score recalculation, DB health stats, System Capabilities Master Reference
  - **Autonomous Red Tester** (`GET /api/v1/tester/status`, `GET /api/v1/tester/reports`) -- Q-table status and crash report listing
  - **SYNAPSE webhook receiver** (`POST /api/v1/synapse/webhook`) and **SYNAPSE status endpoint** (`GET /api/v1/synapse/status`) for ALEXANDRIA ecosystem interoperability
  - **Port 8001** (port 8000 reserved for SYNAPSE event bus)
  - Auto-generated interactive docs at `http://localhost:8001/docs`
  - Models saved at `models/dddqn_trained.pth` and `models/talos_drl.pth`
- **Autonomous Red Tester (RL-Driven Chaos Engineering)** (`src/ai/testing/red_tester.py`)
- **Daemon OS Autostart Orchestrator** (`src/utils/daemon_autostart.py`) -- Windows Startup hook + boot batch generator for the 24/7 daemon (v5.10.6)
- **OPTICA Bridge Integration** (`src/integration/optica_client.py`) -- API client to Project OPTICA (port 8002) for heavy cnsplots/PyVis graphics; TUI "Data Visualizations (via OPTICA)" menu (v5.10.7)
  - **Non-Stationary Multi-Armed Bandit** with Epsilon-Greedy (epsilon=0.2, alpha=0.1) stress-tests system components via subprocess
  - **LLM-as-a-Judge Diagnostics**: Crash stderr sent to Fast Edge LLM (Neutrino-8B) for two-sentence human-readable diagnosis
  - **Rich TUI Visualization**: Spinners, red crash Panels, yellow AI Diagnosis Panels, green PASS confirmations, color-coded Q-Table (Component Fragility)
  - **Crash Reports**: Timestamped Markdown files in `data/reports/red_tester/`
  - **Synapse Event Emission**: `agent_episode_end` events on each test cycle
  - **Q-Table Persistence**: `data/red_tester_q_table.json` for continuity across runs
  - Integrated into `talos.py` menu (Option 7), `run_talos.bat` (Option 8), and `run_talos.sh` (Option 8)
- **Graphify AST Knowledge Graph** (`src/analysis/graphify_adapter.py`) -- NEW in v5.9.10
  - Vendored Graphify engine invoked as subprocess for pure-local AST extraction
  - Generates interactive HTML knowledge graph with D3.js visualization
  - Auto-executes cluster-only command for `GRAPH_REPORT.md` and community labels
  - **Academic Print Mode (Light/Dark Toggle)** injected automatically into `graph.html` -- NEW in v5.9.15
  - All operations 100% air-gapped (no LLM calls required)
- **SYNAPSE Event-Driven Protocol** (`src/integration/synapse_client.py`, `src/api/synapse_routes.py`)
  - Thread-safe EventEmitter pushes JSON events (paper_discovered, paper_evaluated, etc.) to the SYNAPSE bus
  - APIRouter receives inbound commands (trigger_search, trigger_evaluation, get_status, shutdown) via webhook
  - Designed for distributed ALEXANDRIA ecosystem microservice interoperability
- **Database Manager (The Knowledge Hub):** A SQLite3-powered hub using **B-Tree indexing**. It serves as a bridge between ecosystems by storing multiple identifiers (`DOI`, `OpenAlex ID`, `PMID`, `PMCID`).
- **AI Manager (The Cognitive Engine):** A model-agnostic engine (Gemini, DeepSeek, Ollama) using the **Adapter Design Pattern**. It features **Circuit Breakers** for resilience and **Surgical JSON Extraction** via regex to ensure data integrity.
- **Quad-Layer Evaluation Framework:** A proprietary scoring methodology that evaluates papers across four dimensions:
  1. **Strategic:** Theoretical framework and high-level decision making.
  2. **Operational:** Resource allocation, auctions, and consensus mechanisms.
  3. **Tactical:** Algorithmic implementation and DRL/Neural policies.
  4. **Playground:** Simulation environments, datasets, and benchmarks.

### B. Data Acquisition & Enrichment Layer
- **Operation "Genesis" (Native Agents):** Orchestrates simultaneous searches across 14+ sources (ArXiv, Scopus, IEEE, PubMed, etc.) using custom-built Python agents with **Exponential Backoff** logic.
- **Project "HERMES" (Data Enricher):** Automatically retrieves legal **Open Access (OA)** PDF links via the Unpaywall API and augments metadata (ISSN, Publisher) to create a cohesive knowledge web.

### C. 18-Language Codebase Documentation Builder
- **`src/utils/generate_docs.py` v2.0:** A fully interactive tool that documents the **entire TALOS codebase (93+ files)** in any of **18 languages** (Greek, English, Chinese, Hindi, Spanish, Arabic, French, Bengali, Russian, Portuguese, Urdu, Indonesian, German, Japanese, Italian, Korean, Turkish, Persian).
- **100% LOCAL:** Uses your local Ollama instance exclusively -- **zero cloud cost, full privacy**. Never touches Gemini, DeepSeek, or any cloud API.
- **Interactive:** No CLI arguments needed -- select language and folders via `questionary` prompts, see token estimates before starting, track progress with `tqdm`.
- **Output:** Professional Markdown documentation in `docs/{lang_code}/` -- ready for thesis methodology chapters, PhD defense preparation, and developer onboarding.
- **Accessible from TUI (talos.py)** under System Diagnostics.

---

## 3. Installation & Zero-Friction Usage

Project TALOS is designed to run seamlessly across all operating systems. Choose your preferred method:

### Method A: Docker (Recommended)
Run TALOS in a completely isolated environment without installing Python or dependencies.
1. Install [Docker Desktop](https://www.docker.com/products/docker-desktop/) (or Docker Engine + Docker Compose v2 on Linux).
2. Create your `.env` file from `example.env`.
3. Start the headless FastAPI server (port 8001):
   ```bash
   docker compose up -d --build
   ```
4. Verify it is healthy:
   ```bash
   curl http://localhost:8001/api/v1/health
   ```
5. To run the interactive TALOS menu (search, analysis, DRL, autonomous research) inside the container:
   ```bash
   docker compose run --rm talos python talos.py
   ```

For the full Docker reference (host Ollama connectivity, GPU notes, volumes, environment variables, and troubleshooting), see **[docs/DOCKER.md](docs/DOCKER.md)**.

### Method B: 1-Click Launcher (Windows)
For users without Docker.
1. Set up your `.env` file.
2. Double-click **`run_talos.bat`**. The script provides a 10-option menu: Full Setup (Conda env + pip install), Start FastAPI Server (port 8001), MCP Server, Interim UI, TALOS CLI, Research Daemon, Live DRL Agent, Autonomous Red Tester, Run Test Suite, or Exit.

### Method C: Traditional Python Environment (Linux/Mac)
```bash
git clone https://github.com/Christos-Smarlamakis/Project-TALOS.git
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python talos.py
```

### Documentation Builder
To generate professional Markdown documentation for the entire codebase in any of 18 languages:
```bash
python src/utils/generate_docs.py
```
Requires **Ollama** for running locally the `gemma4` model.

---

## 4. Citation & Academic Use

This software is part of ongoing research. If you use **TALOS** in your work, please cite it as follows:

**IEEE Style:**
> C. Smarlamakis and E. Georgopoulos, "Project TALOS: Tactical Agentic Literature Orchestration System," v5.10.11, August 2026. [Online]. Available: https://github.com/Christos-Smarlamakis/Project-TALOS. doi: 10.5281/zenodo.19224912

**BibTeX:**
```bibtex
@software{smarlamakis_talos_2026,
  author = {Smarlamakis, Christos and Georgopoulos, Efstratios},
  title = {{Project TALOS: Tactical Agentic Literature Orchestration System}},
  url = {https://github.com/Christos-Smarlamakis/Project-TALOS},
  doi = {10.5281/zenodo.19224912},
  version = {v5.10.11},
  year = {2026}
}
```

**A formal paper presenting the methodology and agentic framework of TALOS is currently in preparation.**

---

## 5. License & Commercial Use

This project is licensed under the **GNU Affero General Public License v3.0 (AGPLv3)**.
- **Academic/Research Use:** Free to use and modify, provided changes are open-sourced under AGPLv3.
- **Commercial/Proprietary Use:** Requires a **Commercial License**.
- **Contact:** [christossmarlamakis@gmail.com](mailto:christossmarlamakis@gmail.com)

---

## 6. Acknowledgements & Support

The Lead Architect and Author, **Christos Smarlamakis**, is an officially selected recipient of the **IEEE Computer Society WEIGD Student Support Fund (2026)**. We gratefully acknowledge the support and resources provided by the IEEE Computer Society and the enduring legacy of Dr. Grace C. N. Wei in empowering open-source, democratized research tools for the global scientific community.

*Designed & AI-Augmented Developed by Christos Smarlamakis.*

---

## ------------------------------------------------------------

## �������� (Greek)

### 1. ��������: �� �����

���� �������� ���������, � **�����** ���� � �������� ��������-�������� ��� ���������� ��� �����. �� **Project TALOS** ���������� ���� �� ������ ���� 21� �����. ��� ����� ���� ����� ����������� �������������, ���� ��� **��������� ����������� ���������� (Research Intelligence Platform)** ��� ������������ **��������� �������� ����������** ��� �� ���������, ���������, �������� ��� ����������� ��� ������������ �����, ������������� ��������� �� ���������� **������������ �������������� ����������� (SLR)**.

#### �� ��������
� �������� �������� ��� ������������� ������������, ������ �� ����� ���� �� *Drone Swarm Intelligence* ��� *AI*, ������� ������� �� ����������� �������������.

#### � ����
�� TALOS ���������� �� ��������� "Research Architect," ������������ ��� ������ ��� �������������� �� ���������� ����� ���� ���� ���� �������� "Human-in-the-loop."

### 2. ������� ������������� & �����������

#### �. ������� ������ ���������� (�� DRL)
- **��������� DRL (� ��������� �������������):** ��� **Double Dueling DQN �� 3-������� LSTM** ��� �������� �� �������� �� �������� ���������� ���� API �� ���������� �����. ������������ �� 3.849 ����������� ����������� papers ��� �� ���� ��������� �� ���������� **RTX 4070 CUDA 12.1**. ������������:
  - **���������� Gymnasium RL** (`src/ai/drl/talos_env.py`) -- ��������� ����� ����������� N-�����, ����� ������ (N + 1)
  - **Grey Wolf Optimizer** (`src/ai/optimizers/gwo_rl_optimizer.py`) ��� �������������� ��������������
  - **24/7 �������� ��������** (`src/ai/drl/talos_service.py`) -- ��������� ��������� �� ������������ Telegram/Discord/Email
- **Flask API server** (`src/api/talos_service_api.py`) -- ��������� ��������� �� ���������� ����� ��� `localhost:5002/api/status`
- **FastAPI REST API** (`src/api/main_api.py`) -- ������ ������� REST �� 18 endpoints ��� `localhost:8001`
  - ������������� ���������, �������������� papers, ������������� scrape/GWO �� BackgroundTasks
  - ���������� ����������� paper �� AI, ��������� ������� ������� �� boolean query
  - �������� GWO ��� Recharts, ������� �������������� HTML, ��������� ���������� ��� BarChart
  - ������� ��������������� �����������, ���������� ����� ���������, ������� ����������� ����������
  - **��������� �������� ��������** (`GET /api/v1/tester/status`, `GET /api/v1/tester/reports`) -- ��������� ������ Q ��� ����� �������� ������������
  - **SYNAPSE webhook** (`POST /api/v1/synapse/webhook`) ��� ������������������ �������������� ALEXANDRIA
  - **���� 8001** (� ���� 8000 ����������� ��� ��� ������ SYNAPSE)
  - �������� ���������� ����������� docs ��� `http://localhost:8001/docs`
  - ������� ������������ ��� `models/dddqn_trained.pth` ��� `models/talos_drl.pth`
- **��������� �������� �������� (RL-Driven Chaos Engineering)** (`src/ai/testing/red_tester.py`)
  - **�� �������� ������������� ������** �� Epsilon-Greedy (epsilon=0.2, alpha=0.1) ��������� ��� ����� �� ������������ ��� TALOS ���� �������������
  - **LLM-as-a-Judge �����������**: �� stderr ������������ ������������ ��� Fast Edge LLM (Neutrino-8B) ��� �������� ��� ���������
  - **������������ Rich TUI**: Spinners, ������� Panels ������������, ������� Panels ��������� AI, �������� ������������� PASS, �������� ������� Q (������������� ���������)
  - **�������� ������������**: �������������� ������ Markdown ��� `data/reports/red_tester/`
  - **������� ��������� Synapse**: �������� `agent_episode_end` �� ���� ����� �������
  - **��������� ������ Q**: `data/red_tester_q_table.json` ��� �������� ������ ����������
  - ������������ ��� ����� `talos.py` (������� 7), `run_talos.bat` (������� 8), ��� `run_talos.sh` (������� 8)
- **������ ������ AST Graphify** (`src/analysis/graphify_adapter.py`) -- ��� ���� v5.9.10
  - Vendored ������ Graphify ��� �������� �� ������������ ��� ������ ������ ������� AST
  - ������� ����������� ����� ������ HTML �� ������������ D3.js
  - �������� �������� cluster-only ��� `GRAPH_REPORT.md` ��� �������� ����������
  - **���������� ����������� ��������� (�������� Light/Dark)** ��� ��������� �������� ��� `graph.html` -- ��� ���� v5.9.15
  - ���� �� ����������� 100% ����� �������� (air-gapped, ����� ������� LLM)
- **���������� SYNAPSE** (`src/integration/synapse_client.py`, `src/api/synapse_routes.py`)
  - Thread-safe EventEmitter ������� �������� JSON (paper_discovered, paper_evaluated, �.��.) ���� ������ SYNAPSE
  - APIRouter �������� ������������ ������� (trigger_search, trigger_evaluation, get_status, shutdown) ���� webhook
  - ����������� ��� ������������������ ������������� �������������� �������������� ALEXANDRIA
- **Database Manager (� ������ ������):** ��� ���� SQLite3 �� **B-Tree indexing** ��� ���������� �� ������ ������ �������������� ������������� �������� ������������� (`DOI`, `OpenAlex ID`, `PMID`, `PMCID`).
- **AI Manager (� �������� ������):** ��� model-agnostic ������ (Gemini, DeepSeek, Ollama) ��� ������������ �� **Adapter Design Pattern** �� **Circuit Breakers** ��� ������������� ��� **Surgical JSON Extraction** ��� ����������� ���������.
- **������� ����������� �������� ��������:** ��� ��������� ����������� ������������ ��� ��������� papers �� �������� ����������:
  1. **���������� (Strategic):** ��������� ������� ��� ���� ��������� ������ ��������.
  2. **����������� (Operational):** �������� �����, �����������, ���������� consensus.
  3. **������� (Tactical):** ����������� ��������� ��� ��������� DRL/����������.
  4. **����� ������� (Playground):** ������������ ������������, ������ ���������, benchmarks.

#### �. ������� ��������� & ������������ ���������
- **���������� "Genesis" (Native Agents):** ������������� ����������� ����������� �� 14+ ����� (ArXiv, Scopus, IEEE, PubMed, �.��.) ��������������� custom-built Python agents �� ������ **Exponential Backoff**.
- **��������� "HERMES" (Data Enricher):** ������ �������� �������� ���������� **Open Access (OA)** PDF ���� ��� Unpaywall API ��� ����������� �� ������������ (ISSN, Publisher).

#### �. �������� ���������� ����������� ������ �� 18 �������
- **`src/utils/generate_docs.py` v2.0:** ��� ������ ����������� �������� ��� ����������� **�������� ��� ������ ��� TALOS (93+ ������)** �� ����������� ��� **18 �������** (��������, �������, ��������, �����, ��������, �������, �������, ���������, ������, �����������, �������, �����������, ���������, ��������, �������, ���������, ��������, �������).
- **100% ������:** ������������ ������������ �� ������ Ollama -- **�������� ������ cloud, ������ ������������**. ���� ��� ����� Gemini, DeepSeek � ���� cloud API.
- **�����������:** ����� ���������� CLI -- ������� ������� ��� ������� ���� `questionary` prompts, �������� tokens ���� ��� ������, ������������� ������� �� `tqdm`.
- **������:** ������������� ���������� Markdown ��� `docs/{lang_code}/` -- ������ ��� �������� ������������ ���������, ������������ ����������� PhD, ��� onboarding ���������������.
- **���������� ��� TUI (talos.py)** ���� ������� System Diagnostics.

### 3. ����������� & �����

�������� �� ������ ��� ��� ���������� ��������:

#### ������� �: Docker (������������)
��������� �� TALOS �� ������ ����������� ���������� ����� ����������� Python � ����������.
1. ������������ �� [Docker Desktop](https://www.docker.com/products/docker-desktop/) (� Docker Engine + Docker Compose v2 �� Linux).
2. ������������ �� ������ `.env` ��� �� `example.env`.
3. ��������� ��� headless FastAPI server (���� 8001):
   ```bash
   docker compose up -d --build
   ```
4. ����������� ��� ����������:
   ```bash
   curl http://localhost:8001/api/v1/health
   ```
5. ��� �� ����������� ����� TALOS (���������, �������, DRL, �������� ������) ���� ��� container:
   ```bash
   docker compose run --rm talos python talos.py
   ```

��� ��� ����� ����� Docker (������� �� host Ollama, ���������� GPU, volumes, ���������� �������������, ������������ �����������), ����� �� **[docs/DOCKER.md](docs/DOCKER.md)**.

#### ������� �: 1-Click Launcher (Windows)
1. ����������� �� ������ `.env`.
2. ����� ����� ���� ��� ������ **`run_talos.bat`**. ��������� ����� 10 ��������: ������ ����������� (Conda env + pip install), �������� FastAPI Server (���� 8001), MCP Server, ��������� UI, TALOS CLI, ����������� ��������, Live DRL Agent, ��������� �������� ����������, �������� Test Suite (pytest -v), � ������.

#### ������� �: ����������� ���������� Python
```bash
git clone https://github.com/Christos-Smarlamakis/Project-TALOS.git
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python talos.py
```

#### ���������� �����������
��� �� �������� ������������� ���������� Markdown ��� �������� ��� ������ �� ����������� ��� 18 �������:
```bash
python src/utils/generate_docs.py
```
���������� **Ollama** ��� ������ �������� ��� �������� `gemma4`.

### 4. ���������� ������� (Citation)

���� �� ��������� �������� ����� �� �������� �������. ��� ��������������� �� **TALOS** ���� ������� ���, ����������� �� �� ��������� �� ����:

**IEEE Style:**
> C. Smarlamakis and E. Georgopoulos, "Project TALOS: Tactical Agentic Literature Orchestration System," v5.10.11, ��������� 2026. [Online]. Available: https://github.com/Christos-Smarlamakis/Project-TALOS. doi: 10.5281/zenodo.19224912

**BibTeX:**
```bibtex
@software{smarlamakis_talos_2026,
  author = {Smarlamakis, Christos and Georgopoulos, Efstratios},
  title = {{Project TALOS: Tactical Agentic Literature Orchestration System}},
  url = {https://github.com/Christos-Smarlamakis/Project-TALOS},
  doi = {10.5281/zenodo.19224912},
  version = {v5.10.11},
  year = {2026}
}
```

**������� ������� ��� ����������� �� ����������� ��� �� agentic ������� ��� TALOS ��������� ��� ������������.**

### 5. ����� ������ & �������� ������������

�� ��������� ���������� ��� ��� ����� **GNU Affero General Public License v3.0 (AGPLv3)**.
- **���������� �����:** ��������, �� ��� ���������� ��� ����� ������������� �� ����������� �������� ������ ��� ��� ���� �����.
- **�������� �����:** ���������� � ����� **��������� ������ (Commercial License)**.
- **�����������:** [christossmarlamakis@gmail.com](mailto:christossmarlamakis@gmail.com)

### 6. ����������� & ����������

� ������ ������������ ��� ����������, **������� �����������**, ����� �������� ��������� ��� **IEEE Computer Society WEIGD Student Support Fund (2026)**. ���������� ��� ����������� ��� ��� ��� ���������� ��� ���� ������ ��� ���������� ��� ��� IEEE Computer Society ��� �� ������ ���������� ��� Dr. Grace C. N. Wei ���� �������� ��������� ������� �������� ������ ��� ����������������� ��������� ��� ��� ��������� ������������ ���������.

*���������� & �������� �� ���������� �������� ���������� ��� ��� ������ ����������.*
