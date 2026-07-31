# Project TALOS (v5.8.4)

### **Tactical Agentic Literature Orchestration System**
*(Takriko Praktoriko Systima Enorchistrosis Vivliografias)*

> **An Autonomous Research Intelligence Platform -- Multi-Tier LLM Routing (CPU/GPU/Cloud), Headless FastAPI Backend with 16 REST Endpoints, SYNAPSE Event-Driven Protocol, React 18 + Tailwind CSS + Shadcn UI Frontend.**

[![IEEE Computer Society](https://img.shields.io/badge/IEEE_Computer_Society-WEIGD_Fund_Recipient_2026-006699?style=flat-square&logo=ieee&logoColor=white)](https://www.computer.org/volunteering/awards/scholarships/weigd-student-fund)
![Python](https://img.shields.io/badge/Python-3.9%2B-blue)
![License](https://img.shields.io/badge/License-AGPLv3-red)
[![DOI](https://zenodo.org/badge/1191928488.svg)](https://doi.org/10.5281/zenodo.19224912)
![Status](https://img.shields.io/badge/Status-Active%20Research-green)
![Methodology](https://img.shields.io/badge/Methodology-Scientometrics%20%7C%20AI%20Evaluation-teal)
![Maintained](https://img.shields.io/badge/Maintained%3F-yes-brightgreen.svg)
![Docker](https://img.shields.io/badge/Docker-Supported-2496ED?logo=docker)

---

## 1. Introduction: The Vision
In Greek mythology, **Talos** was a giant bronze automaton built to serve as the tireless guardian of Crete. **Project TALOS** embodies this spirit for the 21st century. It is not a mere literature aggregator but a **Research Intelligence Platform** that utilizes **AI Agents** to discover, evaluate, synthesize, and visualize scientific knowledge, significantly accelerating the **Systematic Literature Review (SLR)** process.

### **The Problem**
The exponential growth of scientific publications, especially in fields like *Drone Swarm Intelligence* and *AI*, makes manual monitoring impossible.
### **The Solution**
TALOS acts as an autonomous "Research Architect," filtering noise and highlighting strategic knowledge through a "Human-in-the-loop" agentic workflow.

### 1.1 Eisagogi: To Orama
Stin elliniki mythologia, o **Talos** itan o chalkinos gigantas-aftomato pou prostateve tin Kriti. To **Project TALOS** ensarkonei afto to pnevma ston 21o aiona. Den einai enas aplos syssoreftis vivliografias, alla mia **Platforma Erevnitikis Noimosynis (Research Intelligence Platform)** pou chrisimopoiei **AI Agents** gia na entopizei, axiologei, synthetei kai optikopoiei tin epistimoniki gnosi, epitachynontas ti diadikasia **Systimatikis Vivliografikis Anaskopisis (SLR)**.

### **To Provlima**
I ekthetiki anaptyxi ton epistimonikon dimosiefseon, eidika se pedia opos ta *Drone Swarm Intelligence* kai *AI*, kathista adynati ti cheirokiniti parakolouthisi.
### **I Lysi**
TALOS leitourgei os aftonomos "Research Architect," filtrarontas ton thoryvo kai tonizontas ti stratigiki gnosi meso enos "Human-in-the-loop" agentic workflow.

---

## 2. Technical Architecture & Ecosystem

### **A. Core Intelligence Layer (now DRL-powered)**
- **DRL Agent (The Autonomous Orchestrator):** A **Double Dueling DQN with 3-layer LSTM** that learns to select the optimal academic API source in real-time. Trained on 3,849 real paper scores from the database with **RTX 4070 CUDA 12.1** acceleration. Features include:
  - **Gymnasium RL environment** (`src/ai/drl/talos_env.py`) -- Dynamic N-source Observation Space, Action Space (N + 1)
  - **Grey Wolf Optimizer** (`src/ai/optimizers/gwo_rl_optimizer.py`) for hyperparameter tuning
  - **24/7 Autonomous Service** (`src/ai/drl/talos_service.py`) -- background research agent with Telegram/Discord/Email notifications
- **Flask API server** (`src/api/talos_service_api.py`) -- real-time service status at `localhost:5002/api/status`
- **FastAPI REST API** (`src/api/main_api.py`) -- full REST facade with 16 endpoints at `localhost:8001`
  - Semantic search, paginated papers, scrape/GWO triggers with BackgroundTasks
  - Single-paper AI evaluation, natural-language to boolean query translation
  - GWO history for Recharts, architecture graph HTML, top authors for BarChart
  - Bulk score recalculation, DB health stats, System Capabilities Master Reference
  - **SYNAPSE webhook receiver** (`POST /api/v1/synapse/webhook`) for ALEXANDRIA ecosystem interoperability
  - **Port 8001** (port 8000 reserved for SYNAPSE event bus)
  - Auto-generated interactive docs at `http://localhost:8001/docs`
  - Models saved at `models/dddqn_trained.pth` and `models/talos_drl.pth`
- **SYNAPSE Event-Driven Protocol** (`src/integration/synapse_client.py`, `src/api/synapse_routes.py`) -- NEW in v5.8.0
  - Thread-safe EventEmitter pushes JSON events (paper_discovered, paper_evaluated, etc.) to the SYNAPSE bus
  - APIRouter receives inbound commands (trigger_search, trigger_evaluation, get_status, shutdown) via webhook
  - Designed for distributed ALEXANDRIA ecosystem microservice interoperability
*   **Database Manager (The Knowledge Hub):** A SQLite3-powered hub using **B-Tree indexing**. It serves as a bridge between ecosystems by storing multiple identifiers (`DOI`, `OpenAlex ID`, `PMID`, `PMCID`).
*   **AI Manager (The Cognitive Engine):** A model-agnostic engine (Gemini, DeepSeek, Ollama) using the **Adapter Design Pattern**. It features **Circuit Breakers** for resilience and **Surgical JSON Extraction** via regex to ensure data integrity.
*   **Quad-Layer Evaluation Framework:** A proprietary scoring methodology that evaluates papers across four dimensions:
    1.  **Strategic:** Theoretical framework and high-level decision making.
    2.  **Operational:** Resource allocation, auctions, and consensus mechanisms.
    3.  **Tactical:** Algorithmic implementation and DRL/Neural policies.
    4.  **Playground:** Simulation environments, datasets, and benchmarks.

### **B. Data Acquisition & Enrichment Layer**
*   **Operation "Genesis" (Native Agents):** Orchestrates simultaneous searches across 14+ sources (ArXiv, Scopus, IEEE, PubMed, etc.) using custom-built Python agents with **Exponential Backoff** logic.
*   **Project "HERMES" (Data Enricher):** Automatically retrieves legal **Open Access (OA)** PDF links via the Unpaywall API and augments metadata (ISSN, Publisher) to create a cohesive knowledge web.

### **C. 18-Language Codebase Documentation Builder**
*   **`src/utils/generate_docs.py` v2.0:** A fully interactive tool that documents the **entire TALOS codebase (93+ files)** in any of **18 languages** (Greek, English, Chinese, Hindi, Spanish, Arabic, French, Bengali, Russian, Portuguese, Urdu, Indonesian, German, Japanese, Italian, Korean, Turkish, Persian).
*   **100% LOCAL:** Uses your local Ollama instance exclusively -- **zero cloud cost, full privacy**. Never touches Gemini, DeepSeek, or any cloud API.
*   **Interactive:** No CLI arguments needed -- select language and folders via `questionary` prompts, see token estimates before starting, track progress with `tqdm`.
*   **Output:** Professional Markdown documentation in `docs/{lang_code}/` -- ready for thesis methodology chapters, PhD defense preparation, and developer onboarding.
*   **Accessible from TUI (talos.py)** under System Diagnostics.

### 2.1 Techniki Architektoniki & Oikosystima

### **A. Core Intelligence Layer (pleon me DRL)**
* **DRL Agent (O Aftonomos Enorchistrotis):** Ena **Double Dueling DQN me 3-layer LSTM** pou mathainei na epilegei ti veltisti akadimaiki pigi API se pragmatiko chrono. Ekpaidevmeno se 3.849 pragmatikes vathmologies paper apo ti vasi dedomenon me epitachynsi **RTX 4070 CUDA 12.1**. Perilamvanei:
  - **Gymnasium RL perivallon** (`src/ai/drl/talos_env.py`) -- Dynamiko Observation Space N pigon, Action Space (N + 1)
  - **Grey Wolf Optimizer** (`src/ai/optimizers/gwo_rl_optimizer.py`) gia veltistopoiisi yperparametron
  - **24/7 Aftonomi Ypiresia** (`src/ai/drl/talos_service.py`) -- praktoras fontou me eidopoiiseis Telegram/Discord/Email
  - **API server** (`src/api/talos_service_api.py`) -- real-time status sto `localhost:5002/api/status`
  - Montela apothikevmena se `models/dddqn_trained.pth` kai `models/talos_drl.pth`
- **FastAPI REST API** (`src/api/main_api.py`) -- 16 endpoints sto `localhost:8001` (port 8000 gia SYNAPSE bus)
  - **SYNAPSE webhook** (`POST /api/v1/synapse/webhook`) gia dialeitourgikotita oikosystimatos ALEXANDRIA -- NEO stin v5.8.0
*   **Database Manager (The Knowledge Hub):** Mia SQLite3 vasi me **B-Tree indexing** pou leitourgei os gefyra metaxy oikosystimaton apothikevontas pollapla anagnoristika (`DOI`, `OpenAlex ID`, `PMID`, `PMCID`).
*   **AI Manager (The Cognitive Engine):** Mia model-agnostic michani (Gemini, DeepSeek, Ollama) pou chrisimopoiei to **Adapter Design Pattern** me **Circuit Breakers** gia anthektikotita kai **Surgical JSON Extraction** gia akeraiotita dedomenon.
*   **Quad-Layer Evaluation Framework:** Mia idioktiti methodologia vathmologisis pou axiologei papers se tesseris diastaseis:
    1.  **Strategic:** Theoritiko plaisio kai ypsilou epipedou lipsi apofaseon.
    2.  **Operational:** Katanomi poron, dimoprasies, michanismoi consensus.
    3.  **Tactical:** Algorithmiki ylopoiisi kai DRL/Neural policies.
    4.  **Playground:** Perivallonta prosomoisis, datasets, benchmarks.

### **B. Data Acquisition & Enrichment Layer**
*   **Operation "Genesis" (Native Agents):** Enorchistronei taftochrones anazitiseis se 14+ piges (ArXiv, Scopus, IEEE, PubMed, k.lp.) chrisimopoiontas custom-built Python agents me logiki **Exponential Backoff**.
*   **Project "HERMES" (Data Enricher):** Anakta aftomata nomimous **Open Access (OA)** syndesmous PDF meso tou Unpaywall API kai emploutizei ta metadedomena (ISSN, Publisher).

### **C. Aftomati Dimiourgia Tekmiriosis (Documentation Builder) se 18 glosses**
*   **`src/utils/generate_docs.py` v2.0:** Ena pliros diadrastiko ergaleio pou tekmirionei **olokliro ton kodika tou TALOS (93+ archeia)** se opoiadipote apo **18 glosses** (Ellinika, English, Zhongwen, Hindi, Espanol, Arabiya, Francais, Bangla, Russkii, Portugues, Urdu, Bahasa Indonesia, Deutsch, Nihongo, Italiano, Hangugeo, Turkce, Farsi).
*   **100% TOPIKO:** Chrisimopoiei apokleistika to topiko sou Ollama instance -- **mideniko kostos cloud, pliris idiotikotita**. Pote den kalei Gemini, DeepSeek, i allo cloud API.
*   **Diadrastiko:** Kanena CLI argument -- epilogi glossas kai fakelon meso `questionary` prompts, token estimate prin tin enarxi, tqdm progress bar.
*   **Exodos:** Epangelmatiki Markdown tekmiriosi sto `docs/{lang_code}/` -- etoimi gia kefalaia methodologias diatrivis, proetoimasia yperaspisis PhD, kai onboarding developers.
*   **Prosvasimo apo TUI (talos.py)** sto System Diagnostics.

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
2. Double-click **`run_talos.bat`**. The script provides a 3-option menu: Full Setup (Conda env + pip install), Start FastAPI Server (port 8001), or Run Test Suite (pytest -v).

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

### 3.1 Egkatastasi & Chrisi (Zero-Friction)

Epilexte ti methodo pou sas exypiretei kalytera:

### Methodos A: Ektelesi me Docker (Proteinomeno)
Choris anagki egkatastasis Python i vivliothikon sto systima sas.
1. Egkatastiste to [Docker Desktop](https://www.docker.com/products/docker-desktop/).
2. Symplirote to archeio `.env` me ta API Keys sas.
3. Anoixte to termatiko sas ston fakelo tou project kai trexte:
   ```bash
   docker-compose run --rm talos
   ```

### Methodos B: 1-Click Launcher (Gia Windows)
1. Symplirote to archeio `.env`.
2. Kante diplo klik sto archeio **`run_talos.bat`**. Prosferei menou 3 epilogon: Pliris Egkatastasi (Conda env + pip install), Ekkinisi FastAPI Server (thyra 8001), i Ektelesi Test Suite (pytest -v).

### Methodos G: Paradosiako Perivallon Python
```bash
pip install -r requirements.txt
python talos.py
```

### Documentation Builder
Gia na parageis epangelmatiki Markdown tekmiriosi gia olokliro ton kodika se opoiadipote apo 18 glosses:
```bash
python src/utils/generate_docs.py
```
Apaiteitai **Ollama** gia na dynatai na trechei topika to montelo `gemma4`.

---

## Citation & Academic Use

This software is part of ongoing PhD research. If you use **TALOS** in your work, please cite it as follows:

**IEEE Style:**
> C. Smarlamakis and E. Georgopoulos, "Project TALOS: Tactical Agentic Literature Orchestration System," v5.8.0, July 2026. [Online]. Available: https://github.com/Christos-Smarlamakis/Project-TALOS. doi: 10.5281/zenodo.19224912

**BibTeX:**
```bibtex
@software{smarlamakis_talos_2026,
  author = {Smarlamakis, Christos and Georgopoulos, Efstratios},
  title = {{Project TALOS: Tactical Agentic Literature Orchestration System}},
  url = {https://github.com/Christos-Smarlamakis/Project-TALOS},
  doi = {10.5281/zenodo.19224912},
  version = {v5.8.0},
  year = {2026}
}
```

**A formal paper presenting the methodology and agentic framework of TALOS is currently in preparation.**

### Akadimaiki Anafora (Citation)
Ean chrisimopoiisete to TALOS stin erevna sas, parakaloume na to anaferete os exis:

**IEEE Style:**
> C. Smarlamakis and E. Georgopoulos, "Project TALOS: Tactical Agentic Literature Orchestration System," v5.8.0, July 2026. [Online]. Available: https://github.com/Christos-Smarlamakis/Project-TALOS. doi: 10.5281/zenodo.19224912

**BibTeX:**
```bibtex
@software{smarlamakis_talos_2026,
  author = {Smarlamakis, Christos and Georgopoulos, Efstratios},
  title = {{Project TALOS: Tactical Agentic Literature Orchestration System}},
  url = {https://github.com/Christos-Smarlamakis/Project-TALOS},
  doi = {10.5281/zenodo.19224912},
  version = {v5.8.0},
  year = {2026}
}
```

---

## License & Commercial Use
This project is licensed under the **GNU Affero General Public License v3.0 (AGPLv3)**.
*   **Academic/Research Use:** Free to use and modify, provided changes are open-sourced under AGPLv3.
*   **Commercial/Proprietary Use:** Requires a **Commercial License**.
*   **Contact:** [christossmarlamakis@gmail.com](mailto:christossmarlamakis@gmail.com)

### Adeia Chrisis & Emporiki Ekmetallefsi
To logismiko diatithetai ypo tin adeia **GNU Affero General Public License v3.0 (AGPLv3)**.
*   **Akadimaiki Chrisi:** Eleftheri, me tin proypothesi oti tyxon tropopoiiseis tha parameinoun anoichtou kodika ypo tin idia adeia.
*   **Emporiki Chrisi:** Apaiteitai i agora **Emporikis Adeias (Commercial License)**.
*   **Epikoinonia:** [christossmarlamakis@gmail.com](mailto:christossmarlamakis@gmail.com)

---

## Acknowledgements & Support

Project TALOS is developed as part of ongoing Ph.D. research at the **University of Peloponnese** (Business Intelligence & Analytics Laboratory).

The Lead Architect and Author, **Christos Smarlamakis**, is an officially selected recipient of the **IEEE Computer Society WEIGD Student Support Fund (2026)**. 
We gratefully acknowledge the support and resources provided by the IEEE Computer Society and the enduring legacy of Dr. Grace C. N. Wei in empowering open-source, 
democratized research tools for the global scientific community.

*Designed & AI-Augmented Developed by Christos Smarlamakis.*