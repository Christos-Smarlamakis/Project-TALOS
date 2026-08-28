# Project TALOS (v5.10.14)

### **Tactical Agentic Literature Orchestration System**

> **An Autonomous Research Intelligence Platform -- Multi-Tier LLM Routing (CPU/GPU/Cloud), Headless FastAPI Backend with 23 REST Endpoints, SYNAPSE Event-Driven Protocol, RL-Driven Autonomous Red Tester with LLM-as-a-Judge Diagnostics, Academic Print Mode for AST Knowledge Graphs, React 18 + Tailwind CSS + Shadcn UI Frontend.**

[![IEEE Computer Society](https://img.shields.io/badge/IEEE_Computer_Society-WEIGD_Fund_Recipient_2026-006699?style=flat-square&logo=ieee&logoColor=white)](https://www.computer.org/volunteering/awards/scholarships/weigd-student-fund/weigd-recipients#summer-2026)
[![Conference Paper](https://img.shields.io/badge/Conference_Paper-HOU_ICBE_2026-002B49?style=flat-square)](https://icbe-hou.eap.gr/)
[![System Integrity](https://img.shields.io/badge/System_Integrity-ISO%2FIEC_25010_Verified-005A9C?style=flat-square)](docs/SYSTEM_CAPABILITIES_MASTER.md)
[![Architecture](https://img.shields.io/badge/Architecture-100%25_Air--Gapped_%26_Local--First-111827?style=flat-square)](config/settings.py)
[![RL Environment](https://img.shields.io/badge/RL_Env-Gymnasium_23D%20%2F%2017A-3B82F6?style=flat-square)](src/ai/drl/talos_env.py)
[![PyTorch](https://img.shields.io/badge/PyTorch-CUDA_Accelerated-EE4C2C?style=flat-square&logo=pytorch&logoColor=white)](src/ai/drl/drl_agent.py)
[![FastAPI](https://img.shields.io/badge/FastAPI-23_REST_Endpoints-009688?style=flat-square&logo=fastapi&logoColor=white)](src/api/main_api.py)
![Python](https://img.shields.io/badge/Python-3.11%2B-blue?style=flat-square)
[![License](https://img.shields.io/badge/License-AGPLv3-red?style=flat-square)](LICENSE)
[![DOI](https://zenodo.org/badge/1191928488.svg)](https://doi.org/10.5281/zenodo.19224912)
[![Docker](https://img.shields.io/badge/Docker-Supported-2496ED?style=flat-square&logo=docker)](docs/DOCKER.md)

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
- **FastAPI REST API** (`src/api/main_api.py`) -- full REST facade with 23 endpoints at `localhost:8001`
  - Semantic search, paginated papers, scrape/GWO triggers with BackgroundTasks
  - Single-paper AI evaluation, natural-language to boolean query translation
  - GWO history for Recharts, architecture graph HTML, top authors for BarChart
  - Bulk score recalculation, DB health stats, System Capabilities Master Reference
  - **Autonomous Red Tester** (`GET /api/v1/tester/status`, `GET /api/v1/tester/reports`) -- Q-table status and crash report listing
  - **SYNAPSE webhook receiver** (`POST /api/v1/synapse/webhook`) and **SYNAPSE status endpoint** (`GET /api/v1/synapse/status`) for ALEXANDRIA ecosystem interoperability
  - **Port 8001** (port 8000 reserved for SYNAPSE event bus)
  - Auto-generated interactive docs at `http://localhost:8001/docs`
  - Models saved at `models/dddqn_trained.pth` and `models/talos_drl.pth`
- **3D Knowledge Constellation Visualizer** (`templates/live_foraging_visualizer.html`) -- vendored Three.js r128 (zero CDN) with 60 FPS animated laser beams, traveling photon pulses, interactive click-to-fire nodes, PNG snapshot, fullscreen and help overlays, and a 1000ms pure-AJAX state poller (`GET /api/v1/visualizer/state`) resolving the active profile database.
- **Test Suite** -- `python -m pytest tests/test_system_integrity.py -q` for system health; `python -m pytest tests/test_multi_tier.py -k test_talos_version` for the version assertion.
- **Autonomous Red Tester (RL-Driven Chaos Engineering)** (`src/ai/testing/red_tester.py`)
- **Daemon OS Autostart Orchestrator** (`src/utils/daemon_autostart.py`) -- Windows Startup hook + boot batch generator for the 24/7 daemon (v5.10.6)
- **Desktop Control Hub System Tray** (`src/utils/tray_icon.py`) -- a seven-item tray menu (Open 3D Visualizer, Open Reports Folder, Open System Log, Open API Docs (Swagger), Trigger Instant Search Cycle, Show / Hide Console Window, Terminate Daemon) with self-healing API auto-bootstrap (`_is_api_alive` / `_ensure_api_server`) that spawns the FastAPI backend on demand (v5.10.13)
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
1. Set up your `.env` file (copy from `example.env` -- a fully commented, six-section environment canon).
2. Double-click **`run_talos.bat`**. The script provides a 10-option menu: Full Setup (Conda env + pip install), Start FastAPI Server (port 8001), MCP Server, Interim UI, TALOS CLI, Research Daemon, Live DRL Agent, Autonomous Red Tester, Run Test Suite, or Exit. The 24/7 daemon also exposes a **Desktop Control Hub** system tray icon with self-healing backend auto-bootstrap.

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
> C. Smarlamakis and E. Georgopoulos, "Project TALOS: Tactical Agentic Literature Orchestration System," v5.10.12, August 2026. [Online]. Available: https://github.com/Christos-Smarlamakis/Project-TALOS. doi: 10.5281/zenodo.19224912

**BibTeX:**
```bibtex
@software{smarlamakis_talos_2026,
  author = {Smarlamakis, Christos and Georgopoulos, Efstratios},
  title = {{Project TALOS: Tactical Agentic Literature Orchestration System}},
  url = {https://github.com/Christos-Smarlamakis/Project-TALOS},
  doi = {10.5281/zenodo.19224912},
  version = {v5.10.12},
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

# Οδηγός Ελληνικής Έκδοσης (Greek Reference)

## 1. Εισαγωγή: Το Όραμα

Στην ελληνική μυθολογία, ο **Τάλως** ήταν ένας γιγάντιος χάλκινος αυτόματος που κατασκευάστηκε για να υπηρετεί ως ο ακούραστος φύλακας της Κρήτης. Το **Project TALOS** ενσαρκώνει αυτό το πνεύμα για τον 21ο αιώνα. Δεν είναι ένας απλός συλλέκτης βιβλιογραφίας, αλλά μια **Πλατφόρμα Ερευνητικής Νοημοσύνης (Research Intelligence Platform)** που χρησιμοποιεί **πράκτορες τεχνητής νοημοσύνης** για να ανακαλύπτει, να αξιολογεί, να συνθέτει και να οπτικοποιεί επιστημονική γνώση, επιταχύνοντας σημαντικά τη διαδικασία της **Συστηματικής Βιβλιογραφικής Ανασκόπησης (SLR)**.

### Το Πρόβλημα
Η εκθετική αύξηση των επιστημονικών δημοσιεύσεων, ιδίως σε πεδία όπως η *Νοημοσύνη Σμηνών Μη Επανδρωμένων Αεροσκαφών* και η *Τεχνητή Νοημοσύνη*, καθιστά αδύνατη τη χειροκίνητη παρακολούθηση.

### Η Λύση
Το TALOS δρα ως ένας αυτόνομος «Ερευνητικός Αρχιτέκτονας», φιλτράροντας τον θόρυβο και αναδεικνύοντας τη στρατηγική γνώση μέσα από μια ροή εργασίας «Human-in-the-loop».

## 2. Τεχνική Αρχιτεκτονική & Οικοσύστημα

### Α. Επίπεδο Πυρήνα Νοημοσύνης (Με Ενισχυτική Μάθηση)
- **Πράκτορας DRL (Ο Αυτόνομος Ενορχηστρωτής):** Ένα **Double Dueling DQN με 3-επίπεδο LSTM** που μαθαίνει να επιλέγει τη βέλτιστη ακαδημαϊκή πηγή API σε πραγματικό χρόνο. Εκπαιδεύτηκε σε 3.849 πραγματικές βαθμολογίες εργασιών με επιτάχυνση **RTX 4070 CUDA 12.1**.
  - **Περιβάλλον Gymnasium RL** (`src/ai/drl/talos_env.py`) -- Δυναμικός χώρος παρατήρησης Ν-πηγών και χώρος δράσης (Ν + 1)
  - **Grey Wolf Optimizer** (`src/ai/optimizers/gwo_foraging_hyperparameter_tuner.py`) για τη βελτιστοποίηση υπερπαραμέτρων
  - **24/7 Αυτόνομη Υπηρεσία** (`src/ai/drl/talos_service.py`) -- ερευνητικός πράκτορας παρασκηνίου με ειδοποιήσεις Telegram/Discord/Email
- **FastAPI REST API** (`src/api/main_api.py`) -- πλήρες REST facade με 23 endpoints στη διεύθυνση `localhost:8001`
  - Σημασιολογική αναζήτηση, σελιδοποιημένα έγγραφα, ενεργοποιητές scrape/GWO με BackgroundTasks
  - Αξιολόγηση μεμονωμένου εγγράφου με τεχνητή νοημοσύνη, μετάφραση φυσικής γλώσσας σε ερώτημα boolean
  - **Αυτόνομος Κόκκινος Ελεγκτής (Red Tester)** (`GET /api/v1/tester/status`, `GET /api/v1/tester/reports`)
  - **Δέκτης webhook SYNAPSE** (`POST /api/v1/synapse/webhook`) για διαλειτουργικότητα του οικοσυστήματος ALEXANDRIA
  - **Θύρα 8001** (η θύρα 8000 διατηρείται για τον δίαυλο συμβάντων SYNAPSE)
  - Αυτόματη διαδραστική τεκμηρίωση docs στη διεύθυνση `http://localhost:8001/docs`
- **Τρισδιάστατος Οπτικοποιητής Αστερισμού Γνώσης** (`templates/live_foraging_visualizer.html`) -- vendored Three.js r128 με 60 FPS ακτίνες λέιζερ και δειγματολήπτη κατάστασης 1000ms
- **Κεντρικός Κόμβος Ελέγχου Επιφάνειας Εργασίας** (`src/utils/tray_icon.py`) -- μενού επτά στοιχείων με αυτοθεραπευόμενη αυτόματη εκκίνηση του backend

### Β. Επίπεδο Απόκτησης & Εμπλουτισμού Δεδομένων
- **Επιχείρηση «Genesis» (Native Agents):** Ενορχηστρώνει ταυτόχρονες αναζητήσεις σε 16 ακαδημαϊκές πηγές με λογική **Exponential Backoff**.
- **Έργο «HERMES» (Data Enricher):** Ανακτά αυτόματα νόμιμους συνδέσμους **Open Access (OA)** PDF μέσω του Unpaywall API.

### Γ. Ενσωματωμένο Σύστημα Τεκμηρίωσης Κώδικα 18 Γλωσσών
- **`src/utils/generate_docs.py`:** Τεκμηριώνει ολόκληρη τη βάση κώδικα TALOS σε 18 γλώσσες, 100% τοπικά μέσω Ollama χωρίς κόστος cloud.

## 3. Εγκατάσταση & Χρήση

### Μέθοδος Α: Docker (Συνιστάται)
1. Εγκαταστήστε το Docker Desktop.
2. Δημιουργήστε το αρχείο `.env` από το `example.env` (ένας πλήρως σχολιασμένος κανόνας έξι ενοτήτων).
3. Εκκινήστε τον headless FastAPI server (θύρα 8001): `docker compose up -d --build`
4. Επιβεβαιώστε την υγεία: `curl http://localhost:8001/api/v1/health`

### Μέθοδος Β: Εκκινητής 1-Κλικ (Windows)
1. Ρυθμίστε το αρχείο `.env`.
2. Κάντε διπλό κλικ στο **`run_talos.bat`**. Ο δαίμονας 24/7 εκθέτει επίσης έναν **Κεντρικό Κόμβο Ελέγχου Επιφάνειας Εργασίας** στο δίσκο συστήματος.

### Μέθοδος Γ: Παραδοσιακό Περιβάλλον Python (Linux/Mac)
Ακολουθήστε τις οδηγίες της αγγλικής ενότητας.

## 4. Άδεια Χρήσης & Εμπορική Χρήση

Το έργο διανέμεται υπό την **GNU Affero General Public License v3.0 (AGPLv3)**.
- **Ακαδημαϊκή/Ερευνητική Χρήση:** Δωρεάν, με την προϋπόθεση ανοιχτής διάθεσης των αλλαγών υπό AGPLv3.
- **Εμπορική Χρήση:** Απαιτείται εμπορική άδεια.

## 5. Ευχαριστίες & Υποστήριξη

Ο Επικεφαλής Αρχιτέκτονας και Συγγραφέας, **Χρήστος Σμαρλαμάκης**, είναι επίσημα επιλεγμένος αποδέκτης του **IEEE Computer Society WEIGD Student Support Fund (2026)**. Ευχαριστούμε θερμά την IEEE Computer Society και τη διαχρονική κληρονομιά της Dr. Grace C. N. Wei για την υποστήριξη ανοιχτού κώδικα και εκδημοκρατισμένων ερευνητικών εργαλείων για την παγκόσμια επιστημονική κοινότητα.

*Σχεδιάστηκε & αναπτύχθηκε με υποβοήθηση τεχνητής νοημοσύνης από τον Χρήστο Σμαρλαμάκη.*