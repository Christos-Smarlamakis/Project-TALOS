# Project TALOS (v5.9.13)

### **Tactical Agentic Literature Orchestration System**

> **An Autonomous Research Intelligence Platform -- Multi-Tier LLM Routing (CPU/GPU/Cloud), Headless FastAPI Backend with 18 REST Endpoints, SYNAPSE Event-Driven Protocol, RL-Driven Autonomous System Tester with LLM-as-a-Judge Diagnostics, Academic Print Mode for AST Knowledge Graphs, React 18 + Tailwind CSS + Shadcn UI Frontend.**

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
- **FastAPI REST API** (`src/api/main_api.py`) -- full REST facade with 18 endpoints at `localhost:8001`
  - Semantic search, paginated papers, scrape/GWO triggers with BackgroundTasks
  - Single-paper AI evaluation, natural-language to boolean query translation
  - GWO history for Recharts, architecture graph HTML, top authors for BarChart
  - Bulk score recalculation, DB health stats, System Capabilities Master Reference
  - **Autonomous System Tester** (`GET /api/v1/tester/status`, `GET /api/v1/tester/reports`) -- Q-table status and crash report listing
  - **SYNAPSE webhook receiver** (`POST /api/v1/synapse/webhook`) for ALEXANDRIA ecosystem interoperability
  - **Port 8001** (port 8000 reserved for SYNAPSE event bus)
  - Auto-generated interactive docs at `http://localhost:8001/docs`
  - Models saved at `models/dddqn_trained.pth` and `models/talos_drl.pth`
- **Autonomous System Tester (RL-Driven Chaos Engineering)** (`src/ai/testing/autonomous_tester.py`)
  - **Non-Stationary Multi-Armed Bandit** with Epsilon-Greedy (epsilon=0.2, alpha=0.1) stress-tests system components via subprocess
  - **LLM-as-a-Judge Diagnostics**: Crash stderr sent to Fast Edge LLM (Neutrino-8B) for two-sentence human-readable diagnosis
  - **Rich TUI Visualization**: Spinners, red crash Panels, yellow AI Diagnosis Panels, green PASS confirmations, color-coded Q-Table (Component Fragility)
  - **Crash Reports**: Timestamped Markdown files in `data/reports/autonomous_tester/`
  - **Synapse Event Emission**: `agent_episode_end` events on each test cycle
  - **Q-Table Persistence**: `data/tester_q_table.json` for continuity across runs
  - Integrated into `talos.py` menu (Option 7), `run_talos.bat` (Option 8), and `run_talos.sh` (Option 8)
- **Graphify AST Knowledge Graph** (`src/analysis/graphify_adapter.py`) -- NEW in v5.9.10
  - Vendored Graphify engine invoked as subprocess for pure-local AST extraction
  - Generates interactive HTML knowledge graph with D3.js visualization
  - Auto-executes cluster-only command for `GRAPH_REPORT.md` and community labels
  - **Academic Print Mode (Light/Dark Toggle)** injected automatically into `graph.html` -- NEW in v5.9.13
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
1. Install [Docker Desktop](https://www.docker.com/products/docker-desktop/).
2. Create your `.env` file (see `example.env`).
3. Open your terminal in the project folder and run:
   ```bash
   docker-compose run --rm talos
   ```
*(If you launch the interactive dashboard via this menu, it will be available at `http://localhost:5000`)*

### Method B: 1-Click Launcher (Windows)
For users without Docker.
1. Set up your `.env` file.
2. Double-click **`run_talos.bat`**. The script provides a 10-option menu: Full Setup (Conda env + pip install), Start FastAPI Server (port 8001), MCP Server, Interim UI, TALOS CLI, Research Daemon, Live DRL Agent, Autonomous System Tester, Run Test Suite, or Exit.

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

This software is part of ongoing PhD research. If you use **TALOS** in your work, please cite it as follows:

**IEEE Style:**
> C. Smarlamakis and E. Georgopoulos, "Project TALOS: Tactical Agentic Literature Orchestration System," v5.9.13, August 2026. [Online]. Available: https://github.com/Christos-Smarlamakis/Project-TALOS. doi: 10.5281/zenodo.19224912

**BibTeX:**
```bibtex
@software{smarlamakis_talos_2026,
  author = {Smarlamakis, Christos and Georgopoulos, Efstratios},
  title = {{Project TALOS: Tactical Agentic Literature Orchestration System}},
  url = {https://github.com/Christos-Smarlamakis/Project-TALOS},
  doi = {10.5281/zenodo.19224912},
  version = {v5.9.13},
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

Project TALOS is developed as part of ongoing Ph.D. research at the **University of Peloponnese** (Business Intelligence & Analytics Laboratory).

The Lead Architect and Author, **Christos Smarlamakis**, is an officially selected recipient of the **IEEE Computer Society WEIGD Student Support Fund (2026)**. We gratefully acknowledge the support and resources provided by the IEEE Computer Society and the enduring legacy of Dr. Grace C. N. Wei in empowering open-source, democratized research tools for the global scientific community.

*Designed & AI-Augmented Developed by Christos Smarlamakis.*

---

## ------------------------------------------------------------

## ΕΛΛΗΝΙΚΑ (Greek)

### 1. Εισαγωγή: Το Όραμα

Στην ελληνική μυθολογία, ο **Τάλως** ήταν ο χάλκινος γίγαντας-αυτόματο που προστάτευε την Κρήτη. Το **Project TALOS** ενσαρκώνει αυτό το πνεύμα στον 21ο αιώνα. Δεν είναι ένας απλός συσσωρευτής βιβλιογραφίας, αλλά μια **Πλατφόρμα Ερευνητικής Νοημοσύνης (Research Intelligence Platform)** που χρησιμοποιεί **Πράκτορες Τεχνητής Νοημοσύνης** για να εντοπίζει, αξιολογεί, συνθέτει και οπτικοποιεί την επιστημονική γνώση, επιταχύνοντας σημαντικά τη διαδικασία **Συστηματικής Βιβλιογραφικής Ανασκόπησης (SLR)**.

#### Το Πρόβλημα
Η εκθετική ανάπτυξη των επιστημονικών δημοσιεύσεων, ειδικά σε πεδία όπως τα *Drone Swarm Intelligence* και *AI*, καθιστά αδύνατη τη χειροκίνητη παρακολούθηση.

#### Η Λύση
Το TALOS λειτουργεί ως αυτόνομος "Research Architect," φιλτράροντας τον θόρυβο και αναδεικνύοντας τη στρατηγική γνώση μέσω μιας ροής εργασίας "Human-in-the-loop."

### 2. Τεχνική Αρχιτεκτονική & Οικοσύστημα

#### Α. Επίπεδο Πυρήνα Νοημοσύνης (με DRL)
- **Πράκτορας DRL (Ο Αυτόνομος Ενορχηστρωτής):** Ένα **Double Dueling DQN με 3-επίπεδο LSTM** που μαθαίνει να επιλέγει τη βέλτιστη ακαδημαϊκή πηγή API σε πραγματικό χρόνο. Εκπαιδευμένο σε 3.849 πραγματικές βαθμολογίες papers από τη βάση δεδομένων με επιτάχυνση **RTX 4070 CUDA 12.1**. Περιλαμβάνει:
  - **Περιβάλλον Gymnasium RL** (`src/ai/drl/talos_env.py`) -- Δυναμικός Χώρος Παρατήρησης N-πηγών, Χώρος Δράσης (N + 1)
  - **Grey Wolf Optimizer** (`src/ai/optimizers/gwo_rl_optimizer.py`) για βελτιστοποίηση υπερπαραμέτρων
  - **24/7 Αυτόνομη Υπηρεσία** (`src/ai/drl/talos_service.py`) -- πράκτορας υποβάθρου με ειδοποιήσεις Telegram/Discord/Email
- **Flask API server** (`src/api/talos_service_api.py`) -- κατάσταση υπηρεσίας σε πραγματικό χρόνο στο `localhost:5002/api/status`
- **FastAPI REST API** (`src/api/main_api.py`) -- πλήρης πρόσοψη REST με 18 endpoints στο `localhost:8001`
  - Σημασιολογική αναζήτηση, σελιδοποιημένα papers, ενεργοποιητές scrape/GWO με BackgroundTasks
  - Αξιολόγηση μεμονωμένου paper με AI, μετάφραση φυσικής γλώσσας σε boolean query
  - Ιστορικό GWO για Recharts, γράφημα αρχιτεκτονικής HTML, κορυφαίοι συγγραφείς για BarChart
  - Μαζικός επανυπολογισμός βαθμολογιών, στατιστικά βάσης δεδομένων, Αναφορά Δυνατοτήτων Συστήματος
  - **Αυτόνομος Ελεγκτής Συστήματος** (`GET /api/v1/tester/status`, `GET /api/v1/tester/reports`) -- Κατάσταση Πίνακα Q και λίστα αναφορών καταρρεύσεων
  - **SYNAPSE webhook** (`POST /api/v1/synapse/webhook`) για διαλειτουργικότητα οικοσυστήματος ALEXANDRIA
  - **Θύρα 8001** (η θύρα 8000 προορίζεται για τον δίαυλο SYNAPSE)
  - Αυτόματα παραγόμενα διαδραστικά docs στο `http://localhost:8001/docs`
  - Μοντέλα αποθηκευμένα στα `models/dddqn_trained.pth` και `models/talos_drl.pth`
- **Αυτόνομος Ελεγκτής Συστήματος (RL-Driven Chaos Engineering)** (`src/ai/testing/autonomous_tester.py`)
  - **Μη Στάσιμος Πολυβραχίονας Ληστής** με Epsilon-Greedy (epsilon=0.2, alpha=0.1) δοκιμάζει υπό πίεση τα υποσυστήματα του TALOS μέσω υποδιεργασιών
  - **LLM-as-a-Judge Διαγνωστικά**: Το stderr καταρρεύσεων αποστέλλεται στο Fast Edge LLM (Neutrino-8B) για διάγνωση δύο προτάσεων
  - **Οπτικοποίηση Rich TUI**: Spinners, κόκκινα Panels καταρρεύσεων, κίτρινα Panels Διάγνωσης AI, πράσινες επιβεβαιώσεις PASS, έγχρωμος Πίνακας Q (Ευθραυστότητα Στοιχείων)
  - **Αναφορές Καταρρεύσεων**: Χρονοσημασμένα αρχεία Markdown στο `data/reports/autonomous_tester/`
  - **Εκπομπή Γεγονότων Synapse**: Γεγονότα `agent_episode_end` σε κάθε κύκλο δοκιμής
  - **Διατήρηση Πίνακα Q**: `data/tester_q_table.json` για συνέχεια μεταξύ εκτελέσεων
  - Ενσωματωμένο στο μενού `talos.py` (Επιλογή 7), `run_talos.bat` (Επιλογή 8), και `run_talos.sh` (Επιλογή 8)
- **Γράφος Γνώσης AST Graphify** (`src/analysis/graphify_adapter.py`) -- ΝΕΟ στην v5.9.10
  - Vendored μηχανή Graphify που καλείται ως υποδιεργασία για αμιγώς τοπική εξαγωγή AST
  - Παράγει διαδραστικό γράφο γνώσης HTML με οπτικοποίηση D3.js
  - Αυτόματη εκτέλεση cluster-only για `GRAPH_REPORT.md` και ετικέτες κοινοτήτων
  - **Λειτουργία Ακαδημαϊκής Εκτύπωσης (Εναλλαγή Light/Dark)** που εισάγεται αυτόματα στο `graph.html` -- ΝΕΟ στην v5.9.13
  - Όλες οι λειτουργίες 100% εκτός σύνδεσης (air-gapped, χωρίς κλήσεις LLM)
- **Πρωτόκολλο SYNAPSE** (`src/integration/synapse_client.py`, `src/api/synapse_routes.py`)
  - Thread-safe EventEmitter προωθεί γεγονότα JSON (paper_discovered, paper_evaluated, κ.λπ.) στον δίαυλο SYNAPSE
  - APIRouter λαμβάνει εισερχόμενες εντολές (trigger_search, trigger_evaluation, get_status, shutdown) μέσω webhook
  - Σχεδιασμένο για διαλειτουργικότητα κατανεμημένων μικροϋπηρεσιών οικοσυστήματος ALEXANDRIA
- **Database Manager (Ο Κόμβος Γνώσης):** Μια βάση SQLite3 με **B-Tree indexing** που λειτουργεί ως γέφυρα μεταξύ οικοσυστημάτων αποθηκεύοντας πολλαπλά αναγνωριστικά (`DOI`, `OpenAlex ID`, `PMID`, `PMCID`).
- **AI Manager (Η Γνωστική Μηχανή):** Μια model-agnostic μηχανή (Gemini, DeepSeek, Ollama) που χρησιμοποιεί το **Adapter Design Pattern** με **Circuit Breakers** για ανθεκτικότητα και **Surgical JSON Extraction** για ακεραιότητα δεδομένων.
- **Πλαίσιο Αξιολόγησης Τεσσάρων Επιπέδων:** Μια ιδιόκτητη μεθοδολογία βαθμολόγησης που αξιολογεί papers σε τέσσερις διαστάσεις:
  1. **Στρατηγικό (Strategic):** Θεωρητικό πλαίσιο και λήψη αποφάσεων υψηλού επιπέδου.
  2. **Λειτουργικό (Operational):** Κατανομή πόρων, δημοπρασίες, μηχανισμοί consensus.
  3. **Τακτικό (Tactical):** Αλγοριθμική υλοποίηση και πολιτικές DRL/Νευρωνικές.
  4. **Πεδίο Δοκιμών (Playground):** Περιβάλλοντα προσομοίωσης, σύνολα δεδομένων, benchmarks.

#### Β. Επίπεδο Απόκτησης & Εμπλουτισμού Δεδομένων
- **Επιχείρηση "Genesis" (Native Agents):** Ενορχηστρώνει ταυτόχρονες αναζητήσεις σε 14+ πηγές (ArXiv, Scopus, IEEE, PubMed, κ.λπ.) χρησιμοποιώντας custom-built Python agents με λογική **Exponential Backoff**.
- **Εγχείρημα "HERMES" (Data Enricher):** Ανακτά αυτόματα νόμιμους συνδέσμους **Open Access (OA)** PDF μέσω του Unpaywall API και εμπλουτίζει τα μεταδεδομένα (ISSN, Publisher).

#### Γ. Αυτόματη Δημιουργία Τεκμηρίωσης Κώδικα σε 18 Γλώσσες
- **`src/utils/generate_docs.py` v2.0:** Ένα πλήρως διαδραστικό εργαλείο που τεκμηριώνει **ολόκληρο τον κώδικα του TALOS (93+ αρχεία)** σε οποιαδήποτε από **18 γλώσσες** (Ελληνικά, Αγγλικά, Κινεζικά, Χίντι, Ισπανικά, Αραβικά, Γαλλικά, Μπενγκάλι, Ρωσικά, Πορτογαλικά, Ουρντού, Ινδονησιακά, Γερμανικά, Ιαπωνικά, Ιταλικά, Κορεατικά, Τουρκικά, Περσικά).
- **100% ΤΟΠΙΚΟ:** Χρησιμοποιεί αποκλειστικά το τοπικό Ollama -- **μηδενικό κόστος cloud, πλήρης ιδιωτικότητα**. Ποτέ δεν καλεί Gemini, DeepSeek ή άλλο cloud API.
- **Διαδραστικό:** Καμία παράμετρος CLI -- επιλογή γλώσσας και φακέλων μέσω `questionary` prompts, εκτίμηση tokens πριν την έναρξη, παρακολούθηση προόδου με `tqdm`.
- **Έξοδος:** Επαγγελματική τεκμηρίωση Markdown στο `docs/{lang_code}/` -- έτοιμη για κεφάλαια μεθοδολογίας διατριβής, προετοιμασία υπεράσπισης PhD, και onboarding προγραμματιστών.
- **Προσβάσιμο από TUI (talos.py)** στην ενότητα System Diagnostics.

### 3. Εγκατάσταση & Χρήση

Επιλέξτε τη μέθοδο που σας εξυπηρετεί καλύτερα:

#### Μέθοδος Α: Docker (Προτεινόμενη)
Εκτελέστε το TALOS σε πλήρως απομονωμένο περιβάλλον χωρίς εγκατάσταση Python ή εξαρτήσεων.
1. Εγκαταστήστε το [Docker Desktop](https://www.docker.com/products/docker-desktop/).
2. Δημιουργήστε το αρχείο `.env` (δείτε το `example.env`).
3. Ανοίξτε το τερματικό στον φάκελο του project και εκτελέστε:
   ```bash
   docker-compose run --rm talos
   ```

#### Μέθοδος Β: 1-Click Launcher (Windows)
1. Συμπληρώστε το αρχείο `.env`.
2. Κάντε διπλό κλικ στο αρχείο **`run_talos.bat`**. Προσφέρει μενού 10 επιλογών: Πλήρης Εγκατάσταση (Conda env + pip install), Εκκίνηση FastAPI Server (θύρα 8001), MCP Server, Ενδιάμεσο UI, TALOS CLI, Ερευνητικός Δαίμονας, Live DRL Agent, Αυτόνομος Ελεγκτής Συστήματος, Εκτέλεση Test Suite (pytest -v), ή Έξοδος.

#### Μέθοδος Γ: Παραδοσιακό Περιβάλλον Python
```bash
git clone https://github.com/Christos-Smarlamakis/Project-TALOS.git
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python talos.py
```

#### Δημιουργία Τεκμηρίωσης
Για να παράγετε επαγγελματική τεκμηρίωση Markdown για ολόκληρο τον κώδικα σε οποιαδήποτε από 18 γλώσσες:
```bash
python src/utils/generate_docs.py
```
Απαιτείται **Ollama** για τοπική εκτέλεση του μοντέλου `gemma4`.

### 4. Ακαδημαϊκή Αναφορά (Citation)

Αυτό το λογισμικό αποτελεί μέρος εν εξελίξει διδακτορικής έρευνας. Εάν χρησιμοποιήσετε το **TALOS** στην εργασία σας, παρακαλούμε να το αναφέρετε ως εξής:

**IEEE Style:**
> C. Smarlamakis and E. Georgopoulos, "Project TALOS: Tactical Agentic Literature Orchestration System," v5.9.13, Αύγουστος 2026. [Online]. Available: https://github.com/Christos-Smarlamakis/Project-TALOS. doi: 10.5281/zenodo.19224912

**BibTeX:**
```bibtex
@software{smarlamakis_talos_2026,
  author = {Smarlamakis, Christos and Georgopoulos, Efstratios},
  title = {{Project TALOS: Tactical Agentic Literature Orchestration System}},
  url = {https://github.com/Christos-Smarlamakis/Project-TALOS},
  doi = {10.5281/zenodo.19224912},
  version = {v5.9.13},
  year = {2026}
}
```

**Επίσημη εργασία που παρουσιάζει τη μεθοδολογία και το agentic πλαίσιο του TALOS βρίσκεται υπό προετοιμασία.**

### 5. Άδεια Χρήσης & Εμπορική Εκμετάλλευση

Το λογισμικό διατίθεται υπό την άδεια **GNU Affero General Public License v3.0 (AGPLv3)**.
- **Ακαδημαϊκή Χρήση:** Ελεύθερη, με την προϋπόθεση ότι τυχόν τροποποιήσεις θα παραμείνουν ανοικτού κώδικα υπό την ίδια άδεια.
- **Εμπορική Χρήση:** Απαιτείται η αγορά **Εμπορικής Άδειας (Commercial License)**.
- **Επικοινωνία:** [christossmarlamakis@gmail.com](mailto:christossmarlamakis@gmail.com)

### 6. Ευχαριστίες & Υποστήριξη

Το Project TALOS αναπτύσσεται στο πλαίσιο εν εξελίξει διδακτορικής έρευνας στο **Πανεπιστήμιο Πελοποννήσου** (Εργαστήριο Επιχειρηματικής Ευφυΐας & Αναλυτικής).

Ο Κύριος Αρχιτέκτονας και Συγγραφέας, **Χρήστος Σμαρλαμάκης**, είναι επίσημα επιλεγμένος αποδέκτης του **IEEE Computer Society WEIGD Student Support Fund (2026)**. Εκφράζουμε την ευγνωμοσύνη μας για την υποστήριξη και τους πόρους που παρέχονται από την IEEE Computer Society και τη διαρκή κληρονομιά της Dr. Grace C. N. Wei στην ενδυνάμωση εργαλείων έρευνας ανοικτού κώδικα και εκδημοκρατισμένης πρόσβασης για την παγκόσμια επιστημονική κοινότητα.

*Σχεδιασμός & Ανάπτυξη με Υποβοήθηση Τεχνητής Νοημοσύνης από τον Χρήστο Σμαρλαμάκη.*