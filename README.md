# Project TALOS (v4.8.0)
### **Tactical Agentic Literature Orchestration System**

> **An Autonomous Research Intelligence Platform for the AI Era.**

![Python](https://img.shields.io/badge/Python-3.9%2B-blue)
![License](https://img.shields.io/badge/License-AGPLv3-red)
[![DOI](https://zenodo.org/badge/1191928488.svg)](https://doi.org/10.5281/zenodo.19224912)
![Status](https://img.shields.io/badge/Status-Active%20Research-green)
![Maintained](https://img.shields.io/badge/Maintained%3F-yes-brightgreen.svg)

---

## 1. Introduction: The Vision
In Greek mythology, **Talos** was a giant bronze automaton built to serve as the tireless guardian of Crete. **Project TALOS** embodies this spirit for the 21st century. It is not a mere literature aggregator but a **Research Intelligence Platform** that utilizes **AI Agents** to discover, evaluate, synthesize, and visualize scientific knowledge, significantly accelerating the **Systematic Literature Review (SLR)** process.

### **The Problem**
The exponential growth of scientific publications, especially in fields like *Drone Swarm Intelligence* and *AI*, makes manual monitoring impossible.
### **The Solution**
TALOS acts as an autonomous "Research Architect," filtering noise and highlighting strategic knowledge through a "Human-in-the-loop" agentic workflow.

---

## 2. Technical Architecture & Ecosystem

### **A. Core Intelligence Layer**
*   **Database Manager (The Knowledge Hub):** A SQLite3-powered hub using **B-Tree indexing**. It serves as a bridge between ecosystems by storing multiple identifiers (`DOI`, `OpenAlex ID`, `PMID`, `PMCID`).
*   **AI Manager (The Cognitive Engine):** A model-agnostic engine (Gemini, DeepSeek, Ollama) using the **Adapter Design Pattern**. It features **Circuit Breakers** for resilience and **Surgical JSON Extraction** via regex to ensure data integrity.
*   **Quad-Layer Evaluation Framework:** A proprietary scoring methodology that evaluates papers across four dimensions:
    1.  **Strategic:** Theoretical framework and high-level decision making.
    2.  **Operational:** Resource allocation, auctions, and consensus mechanisms.
    3.  **Tactical:** Algorithmic implementation and DRL/Neural policies.
    4.  **Playground:** Simulation environments, datasets, and benchmarks.

### **B. Data Acquisition & Enrichment Layer**
*   **Operation "Genesis" (Native Agents):** Orchestrates simultaneous searches across 12+ sources (ArXiv, Scopus, IEEE, PubMed, etc.) using custom-built Python agents with **Exponential Backoff** logic.
*   **Project "HERMES" (Data Enricher):** Automatically retrieves legal **Open Access (OA)** PDF links via the Unpaywall API and augments metadata (ISSN, Publisher) to create a cohesive knowledge web.

---

## 3. Installation & Usage
1.  **Clone & Install:**
    ```bash
    git clone https://github.com/Christos-Smarlamakis/Project-TALOS.git
    pip install -r requirements.txt
    ```
2.  **Configure:** Rename `env.example` to `.env` and add your keys.
3.  **Run:** Launch the Command Center: `python talos.py`

---

## 📄 Citation & Academic Use

If you use **TALOS** in your work, please cite it as follows:

**IEEE Style:**
> C. Smarlamakis and E. Georgopoulos, "Project TALOS: Tactical Agentic Literature Orchestration System," v4.8.0, Mar. 2026. [Online]. Available: https://github.com/Christos-Smarlamakis/Project-TALOS. doi: 10.5281/zenodo.19224912

**BibTeX:**
```bibtex
@software{smarlamakis_talos_2026,
  author = {Smarlamakis, Christos and Georgopoulos, Efstratios},
  title = {{Project TALOS: Tactical Agentic Literature Orchestration System}},
  url = {https://github.com/Christos-Smarlamakis/Project-TALOS},
  doi = {10.5281/zenodo.19224912},
  version = {v4.8.0},
  year = {2026}
}
```

**⚠️ A formal paper presenting the methodology and agentic framework of TALOS is currently in preparation.**

---

## ⚖️ License & Commercial Use
This project is licensed under the **GNU Affero General Public License v3.0 (AGPLv3)**.
*   **Academic/Research Use:** Free to use and modify, provided changes are open-sourced under AGPLv3.
*   **Commercial/Proprietary Use:** Requires a **Commercial License**.
*   **Contact:** [christossmarlamakis@gmail.com](mailto:christossmarlamakis@gmail.com)

---
*Designed & AI-Augmented Developed by Christos Smarlamakis.*

---

# Project TALOS (v4.8.0)
### **Tactical Agentic Literature Orchestration System**

> **Μια Αυτόνομη Πλατφόρμα Ερευνητικής Νοημοσύνης για την Εποχή του AI.**

---

## 1. Εισαγωγή: Το Όραμα
Στην ελληνική μυθολογία, ο **Τάλως** ήταν ο χάλκινος γίγαντας-αυτόματο που προστάτευε την Κρήτη. Το **Project TALOS** ενσαρκώνει αυτό το πνεύμα στον 21ο αιώνα. Δεν είναι ένας απλός συσσωρευτής βιβλιογραφίας, αλλά μια **Πλατφόρμα Ερευνητικής Νοημοσύνης (Research Intelligence Platform)** που χρησιμοποιεί **AI Agents** για να εντοπίζει, αξιολογεί, συνθέτει και οπτικοποιεί την επιστημονική γνώση, επιταχύνοντας τη διαδικασία **Συστηματικής Βιβλιογραφικής Ανασκόπησης (SLR)**.

---

## 2. Τεχνική Αρχιτεκτονική & Οικοσύστημα

### **Α. Επίπεδο Νοημοσύνης (Core Layer)**
*   **Database Manager (The Knowledge Hub):** Κεντρικός κόμβος γνώσης σε SQLite3 με βελτιστοποιημένη ευρετηρίαση. Λειτουργεί ως γέφυρα μεταξύ βάσεων δεδομένων αποθηκεύοντας αναγνωριστικά `DOI`, `OpenAlex ID` και `PMID`.
*   **AI Manager (The Cognitive Engine):** "Εγκέφαλος" αγνωστικιστικός ως προς το μοντέλο (Gemini, DeepSeek, Ollama). Διαθέτει μηχανισμούς **Circuit Breaker** για ανθεκτικότητα και **Surgical JSON Extraction** για την ακεραιότητα των δεδομένων.
*   **Quad-Layer Evaluation Framework:** Μεθοδολογία αξιολόγησης σε 4 επίπεδα: **Strategic**, **Operational**, **Tactical** και **Playground**.

### **Β. Επίπεδο Συλλογής & Εμπλουτισμού**
*   **Operation "Genesis":** Χρήση **Custom Native Agents** για ταυτόχρονη σάρωση σε 12+ πηγές (ArXiv, Scopus, IEEE, PubMed κ.α.).
*   **Project "HERMES" (Data Enricher):** Αυτόματος εντοπισμός νόμιμων **Open Access** PDF links μέσω του Unpaywall API και εμπλουτισμός μεταδεδομένων (v4.8).

### **Γ. Στρατηγική Ανάλυση & Οπτικοποίηση**
*   **Project "VISUALIZER":** Σουίτα επιστημομετρίας που παράγει reports με διαγράμματα για την εξέλιξη του πεδίου, την ποιότητα και τις θεματικές τάσεις (WordClouds).
*   **Project "NAFSIKA":** Διαδραστικό Web Dashboard (Flask) με οπτικοποίηση **Article DNA** και Σημασιολογική Αναζήτηση σε πραγματικό χρόνο.

---

## 📄 Ακαδημαϊκή Αναφορά (Citation)
Εάν χρησιμοποιήσετε το TALOS στην έρευνά σας, παρακαλούμε να το αναφέρετε ως εξής:

**IEEE Style:**
> C. Smarlamakis and E. Georgopoulos, "Project TALOS: Tactical Agentic Literature Orchestration System," v4.8.0, Mar. 2026. [Online]. Available: https://github.com/Christos-Smarlamakis/Project-TALOS. doi: 10.5281/zenodo.19224912

**BibTeX:**
```bibtex
@software{smarlamakis_talos_2026,
  author = {Smarlamakis, Christos and Georgopoulos, Efstratios},
  title = {{Project TALOS: Tactical Agentic Literature Orchestration System}},
  url = {https://github.com/Christos-Smarlamakis/Project-TALOS},
  doi = {10.5281/zenodo.19224912},
  version = {v4.8.0},
  year = {2026}
}
```

---

## ⚖️ Άδεια Χρήσης & Εμπορική Εκμετάλλευση
Το λογισμικό διατίθεται υπό την άδεια **GNU Affero General Public License v3.0 (AGPLv3)**.
*   **Ακαδημαϊκή Χρήση:** Ελεύθερη, με την προϋπόθεση ότι τυχόν τροποποιήσεις θα παραμείνουν ανοιχτού κώδικα υπό την ίδια άδεια.
*   **Εμπορική Χρήση:** Απαιτείται η αγορά **Εμπορικής Άδειας (Commercial License)**.
*   **Επικοινωνία:** [christossmarlamakis@gmail.com](mailto:christossmarlamakis@gmail.com)

---
*Designed & AI-Augmented Developed by Christos Smarlamakis.*