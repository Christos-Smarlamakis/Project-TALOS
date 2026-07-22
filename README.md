# Project TALOS (v5.3.8)

### **Tactical Agentic Literature Orchestration System**
*(Τακτικό Πρακτορικό Σύστημα Ενορχήστρωσης Βιβλιογραφίας)*

> **An Autonomous Research Intelligence Platform for the AI Era.**

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

### 1.1 Εισαγωγή: Το Όραμα
Στην ελληνική μυθολογία, ο **Τάλως** ήταν ο χάλκινος γίγαντας-αυτόματο που προστάτευε την Κρήτη. Το **Project TALOS** ενσαρκώνει αυτό το πνεύμα στον 21ο αιώνα. Δεν είναι ένας απλός συσσωρευτής βιβλιογραφίας, αλλά μια **Πλατφόρμα Ερευνητικής Νοημοσύνης (Research Intelligence Platform)** που χρησιμοποιεί **AI Agents** για να εντοπίζει, αξιολογεί, συνθέτει και οπτικοποιεί την επιστημονική γνώση, επιταχύνοντας τη διαδικασία **Συστηματικής Βιβλιογραφικής Ανασκόπησης (SLR)**.

### **Το Πρόβλημα**
Η εκθετική ανάπτυξη των επιστημονικών δημοσιεύσεων, ειδικά σε πεδία όπως τα *Drone Swarm Intelligence* και *AI*, καθιστά αδύνατη τη χειροκίνητη παρακολούθηση.
### **Η Λύση**
TALOS λειτουργεί ως αυτόνομος "Research Architect," φιλτράροντας τον θόρυβο και τονίζοντας τη στρατηγική γνώση μέσω ενός "Human-in-the-loop" agentic workflow.

---

## 2. Technical Architecture & Ecosystem

### **A. Core Intelligence Layer (now DRL-powered)**
- **DRL Agent (The Autonomous Orchestrator):** A **Double Dueling DQN with 3-layer LSTM** that learns to select the optimal academic API source in real-time. Trained on 3,849 real paper scores from the database with **RTX 4070 CUDA 12.1** acceleration. Features include:
  - **Gymnasium RL environment** (`src/ai/drl/talos_env.py`) — Dynamic N-source Observation Space, Action Space (N + 1)
  - **Grey Wolf Optimizer** (`src/ai/optimizers/gwo_rl_optimizer.py`) for hyperparameter tuning
  - **24/7 Autonomous Service** (`src/ai/drl/talos_service.py`) — background research agent with Telegram/Discord/Email notifications
  - **API server** (`src/api/talos_service_api.py`) — real-time status at `localhost:5002/api/status`
  - Models saved at `models/dddqn_trained.pth` and `models/talos_drl.pth`
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
*   **100% LOCAL:** Uses your local Ollama instance exclusively — **zero cloud cost, full privacy**. Never touches Gemini, DeepSeek, or any cloud API.
*   **Interactive:** No CLI arguments needed — select language and folders via `questionary` prompts, see token estimates before starting, track progress with `tqdm`.
*   **Output:** Professional Markdown documentation in `docs/{lang_code}/` — ready for thesis methodology chapters, PhD defense preparation, and developer onboarding.
*   **Accessible from both GUI (Streamlit)** and **TUI (talos.py)** under System Diagnostics.

### 2.1 Τεχνική Αρχιτεκτονική & Οικοσύστημα

### **A. Core Intelligence Layer (πλέον με DRL)**
* **DRL Agent (Ο Αυτόνομος Ενορχηστρωτής):** Ένα **Double Dueling DQN με 3-layer LSTM** που μαθαίνει να επιλέγει τη βέλτιστη ακαδημαϊκή πηγή API σε πραγματικό χρόνο. Εκπαιδευμένο σε 3.849 πραγματικές βαθμολογίες paper από τη βάση δεδομένων με επιτάχυνση **RTX 4070 CUDA 12.1**. Περιλαμβάνει:
  - **Gymnasium RL περιβάλλον** (`src/ai/drl/talos_env.py`) — Δυναμικό Observation Space N πηγών, Action Space (N + 1)
  - **Grey Wolf Optimizer** (`src/ai/optimizers/gwo_rl_optimizer.py`) για βελτιστοποίηση υπερπαραμέτρων
  - **24/7 Αυτόνομη Υπηρεσία** (`src/ai/drl/talos_service.py`) — πράκτορας φόντου με ειδοποιήσεις Telegram/Discord/Email
  - **API server** (`src/api/talos_service_api.py`) — real-time status στο `localhost:5002/api/status`
  - Μοντέλα αποθηκευμένα σε `models/dddqn_trained.pth` και `models/talos_drl.pth`
*   **Database Manager (The Knowledge Hub):** Μια SQLite3 βάση με **B-Tree indexing** που λειτουργεί ως γέφυρα μεταξύ οικοσυστημάτων αποθηκεύοντας πολλαπλά αναγνωριστικά (`DOI`, `OpenAlex ID`, `PMID`, `PMCID`).
*   **AI Manager (The Cognitive Engine):** Μια model-agnostic μηχανή (Gemini, DeepSeek, Ollama) που χρησιμοποιεί το **Adapter Design Pattern** με **Circuit Breakers** για ανθεκτικότητα και **Surgical JSON Extraction** για ακεραιότητα δεδομένων.
*   **Quad-Layer Evaluation Framework:** Μια ιδιόκτητη μεθοδολογία βαθμολόγησης που αξιολογεί papers σε τέσσερις διαστάσεις:
    1.  **Strategic:** Θεωρητικό πλαίσιο και υψηλού επιπέδου λήψη αποφάσεων.
    2.  **Operational:** Κατανομή πόρων, δημοπρασίες, μηχανισμοί consensus.
    3.  **Tactical:** Αλγοριθμική υλοποίηση και DRL/Neural policies.
    4.  **Playground:** Περιβάλλοντα προσομοίωσης, datasets, benchmarks.

### **B. Data Acquisition & Enrichment Layer**
*   **Operation "Genesis" (Native Agents):** Ενορχηστρώνει ταυτόχρονες αναζητήσεις σε 14+ πηγές (ArXiv, Scopus, IEEE, PubMed, κ.λπ.) χρησιμοποιώντας custom-built Python agents με λογική **Exponential Backoff**.
*   **Project "HERMES" (Data Enricher):** Ανακτά αυτόματα νόμιμους **Open Access (OA)** συνδέσμους PDF μέσω του Unpaywall API και εμπλουτίζει τα μεταδεδομένα (ISSN, Publisher).

### **C. Αυτόματη Δημιουργία Τεκμηρίωσης (Documentation Builder) σε 18 γλώσσες**
*   **`src/utils/generate_docs.py` v2.0:** Ένα πλήρως διαδραστικό εργαλείο που τεκμηριώνει **ολόκληρο τον κώδικα του TALOS (93+ αρχεία)** σε οποιαδήποτε από **18 γλώσσες** (Ελληνικά, English, 中文, हिन्दी, Español, العربية, Français, বাংলা, Русский, Português, اردو, Bahasa Indonesia, Deutsch, 日本語, Italiano, 한국어, Türkçe, فارسی).
*   **100% ΤΟΠΙΚΟ:** Χρησιμοποιεί αποκλειστικά το τοπικό σου Ollama instance — **μηδενικό κόστος cloud, πλήρης ιδιωτικότητα**. Ποτέ δεν καλεί Gemini, DeepSeek, ή άλλο cloud API.
*   **Διαδραστικό:** Κανένα CLI argument — επιλογή γλώσσας και φακέλων μέσω `questionary` prompts, token estimate πριν την έναρξη, tqdm progress bar.
*   **Έξοδος:** Επαγγελματική Markdown τεκμηρίωση στο `docs/{lang_code}/` — έτοιμη για κεφάλαια μεθοδολογίας διατριβής, προετοιμασία υπεράσπισης PhD, και onboarding developers.
*   **Προσβάσιμο από GUI (Streamlit)** και **TUI (talos.py)** στο System Diagnostics.

---

## 3. Installation & Zero-Friction Usage

Project TALOS is designed to run seamlessly across all operating systems. Choose your preferred method:

### 🐳 Method A: Docker (Recommended)
Run TALOS in a completely isolated environment without installing Python or dependencies.
1. Install [Docker Desktop](https://www.docker.com/products/docker-desktop/).
2. Create your `.env` file (see `example.env`).
3. Open your terminal in the project folder and run:
   ```bash
   docker-compose run --rm talos
   ```
*(If you launch the interactive dashboard via this menu, it will be available at `http://localhost:5000`)*

### 🖱️ Method B: 1-Click Launcher (Windows)
For users without Docker.
1. Set up your `.env` file.
2. Double-click **`start_talos.bat`**. The script will automatically create a virtual environment, install dependencies, and launch the platform.

### 💻 Method C: Traditional Python Environment (Linux/Mac)
```bash
git clone https://github.com/Christos-Smarlamakis/Project-TALOS.git
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python talos.py
```

### 🧠 Documentation Builder
To generate professional Markdown documentation for the entire codebase in any of 18 languages:
```bash
python src/utils/generate_docs.py
```
Requires **Ollama** for running locally the `gemma4` model.

### 3.1 Εγκατάσταση & Χρήση (Zero-Friction)

Επιλέξτε τη μέθοδο που σας εξυπηρετεί καλύτερα:

### 🐳 Μέθοδος Α: Εκτέλεση με Docker (Προτεινόμενο)
Χωρίς ανάγκη εγκατάστασης Python ή βιβλιοθηκών στο σύστημά σας.
1. Εγκαταστήστε το [Docker Desktop](https://www.docker.com/products/docker-desktop/).
2. Συμπληρώστε το αρχείο `.env` με τα API Keys σας.
3. Ανοίξτε το τερματικό σας στον φάκελο του project και τρέξτε:
   ```bash
   docker-compose run --rm talos
   ```

### 🖱️ Μέθοδος Β: 1-Click Launcher (Για Windows)
1. Συμπληρώστε το αρχείο `.env`.
2. Κάντε διπλό κλικ στο αρχείο **`start_talos.bat`**. Θα δημιουργήσει αυτόματα το εικονικό περιβάλλον και θα ξεκινήσει το μενού.

### 💻 Μέθοδος Γ: Παραδοσιακό Περιβάλλον Python
```bash
pip install -r requirements.txt
python talos.py
```

### 🧠 Documentation Builder
Για να παράγεις επαγγελματική Markdown τεκμηρίωση για ολόκληρο τον κώδικα σε οποιαδήποτε από 18 γλώσσες:
```bash
python src/utils/generate_docs.py
```
Απαιτείται **Ollama** για να δύναται να τρέχει τοπικά το μοντέλο `gemma4`.

---

## 📄 Citation & Academic Use

This software is part of ongoing PhD research. If you use **TALOS** in your work, please cite it as follows:

**IEEE Style:**
> C. Smarlamakis and E. Georgopoulos, "Project TALOS: Tactical Agentic Literature Orchestration System," v5.3.8, July 2026. [Online]. Available: https://github.com/Christos-Smarlamakis/Project-TALOS. doi: 10.5281/zenodo.19224912

**BibTeX:**
```bibtex
@software{smarlamakis_talos_2026,
  author = {Smarlamakis, Christos and Georgopoulos, Efstratios},
  title = {{Project TALOS: Tactical Agentic Literature Orchestration System}},
  url = {https://github.com/Christos-Smarlamakis/Project-TALOS},
  doi = {10.5281/zenodo.19224912},
  version = {v5.3.8},
  year = {2026}
}
```

**⚠️ A formal paper presenting the methodology and agentic framework of TALOS is currently in preparation.**

### 📄 Ακαδημαϊκή Αναφορά (Citation)
Εάν χρησιμοποιήσετε το TALOS στην έρευνά σας, παρακαλούμε να το αναφέρετε ως εξής:

**IEEE Style:**
> C. Smarlamakis and E. Georgopoulos, "Project TALOS: Tactical Agentic Literature Orchestration System," v5.3.8, July 2026. [Online]. Available: https://github.com/Christos-Smarlamakis/Project-TALOS. doi: 10.5281/zenodo.19224912

**BibTeX:**
```bibtex
@software{smarlamakis_talos_2026,
  author = {Smarlamakis, Christos and Georgopoulos, Efstratios},
  title = {{Project TALOS: Tactical Agentic Literature Orchestration System}},
  url = {https://github.com/Christos-Smarlamakis/Project-TALOS},
  doi = {10.5281/zenodo.19224912},
  version = {v5.3.8},
  year = {2026}
}
```

---

## ⚖️ License & Commercial Use
This project is licensed under the **GNU Affero General Public License v3.0 (AGPLv3)**.
*   **Academic/Research Use:** Free to use and modify, provided changes are open-sourced under AGPLv3.
*   **Commercial/Proprietary Use:** Requires a **Commercial License**.
*   **Contact:** [christossmarlamakis@gmail.com](mailto:christossmarlamakis@gmail.com)

### ⚖️ Άδεια Χρήσης & Εμπορική Εκμετάλλευση
Το λογισμικό διατίθεται υπό την άδεια **GNU Affero General Public License v3.0 (AGPLv3)**.
*   **Ακαδημαϊκή Χρήση:** Ελεύθερη, με την προϋπόθεση ότι τυχόν τροποποιήσεις θα παραμείνουν ανοιχτού κώδικα υπό την ίδια άδεια.
*   **Εμπορική Χρήση:** Απαιτείται η αγορά **Εμπορικής Άδειας (Commercial License)**.
*   **Επικοινωνία:** [christossmarlamakis@gmail.com](mailto:christossmarlamakis@gmail.com)

---
*Designed & AI-Augmented Developed by Christos Smarlamakis.*