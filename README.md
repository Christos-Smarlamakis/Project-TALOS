# Project TALOS (v4.8.0)

### **Tactical Agentic Literature Orchestration System**
*(Τακτικό Πρακτορικό Σύστημα Ενορχήστρωσης Βιβλιογραφίας)*

> **An Autonomous Research Intelligence Platform for the AI Era.**


![Python](https://img.shields.io/badge/Python-3.9%2B-blue)
![License](https://img.shields.io/badge/License-AGPLv3-red)
![Status](https://img.shields.io/badge/Status-Active%20Research-green)
![Methodology](https://img.shields.io/badge/Methodology-Scientometrics%20%7C%20AI%20Evaluation-teal)


---

## 1. Εισαγωγή: Τι είναι το TALOS;

Στην καρδιά της ελληνικής μυθολογίας, ο Τάλως ήταν ένας χάλκινος γίγαντας, ένα τεχνολογικό θαύμα, κατασκευασμένος για να λειτουργεί ως ο **αυτόματος, ακούραστος φρουρός** της Κρήτης.

Το **Project TALOS** ενσαρκώνει το ίδιο πνεύμα στον 21ο αιώνα. Δεν είναι απλώς ένας "aggregator" βιβλιογραφίας, αλλά μια **Πλατφόρμα Ερευνητικής Νοημοσύνης (Research Intelligence Platform)** που χρησιμοποιεί πράκτορες Τεχνητής Νοημοσύνης (AI Agents) για να **εντοπίζει, αξιολογεί, συνθέτει και οπτικοποιεί** την επιστημονική γνώση.

**Το Πρόβλημα:** Ο καταιγισμός καθημερινών δημοσιεύσεων (ειδικά σε τομείς όπως τα Drone Swarms και το AI) καθιστά αδύνατη τη χειροκίνητη παρακολούθηση.
**Η Λύση:** Το TALOS λειτουργεί ως ο προσωπικός σου "Research Assistant" που δουλεύει 24/7, φιλτράροντας τον θόρυβο και αναδεικνύοντας τη στρατηγική γνώση.

---

## 2. Βασικές Δυνατότητες (Key Features)

*   **🕵️ Multi-Source Intelligence:** Σαρώνει ταυτόχρονα 12+ πηγές (ArXiv, Scopus, IEEE, PubMed, OpenAlex, Semantic Scholar, κ.α.).
*   **🧠 Quad-Layer AI Evaluation:** Δεν βαθμολογεί απλά. Χρησιμοποιεί LLMs (Gemini/DeepSeek) για να αξιολογήσει κάθε άρθρο σε 4 διαστάσεις: **Strategic, Operational, Tactical, Playground**.
*   **📊 Scientometrics Suite (Project VISUALIZER):** Παράγει αυτόματα αναφορές με διαγράμματα για την εξέλιξη του πεδίου, τους κορυφαίους ερευνητές και τα "Hot Topics" (WordClouds).
*   **🧬 Data Enrichment (Project HERMES):** Συνδέεται με το Unpaywall και το OpenAlex για να βρει αυτόματα **Open Access PDF links**, IDs και μεταδεδομένα.
*   **🔮 Automated Configuration (Project PYTHIA):** Ρυθμίζει αυτόματα το σύστημα για οποιοδήποτε ερευνητικό θέμα περιγράψετε με φυσική γλώσσα.
*   **🕸️ Knowledge Graphs (Project ORPHEUS):** Δημιουργεί διαδραστικούς γράφους αναφορών για να δείξει πώς συνδέονται τα άρθρα μεταξύ τους.
*   **📜 Narrative Synthesis (Project CHIRON):** Γράφει αφηγηματικές αναφορές ("Knowledge Paths") που εξηγούν τη λογική σειρά μελέτης των άρθρων.

---

## 3. Αρχιτεκτονική & Modules

Το σύστημα είναι αρθρωτό (modular) και αποτελείται από εξειδικευμένα scripts:

### **Core Layer (Ο Πυρήνας)**
*   **`talos.py`:** Το Κέντρο Ελέγχου (Command Center). Ένα TUI (Terminal User Interface) για τη διαχείριση όλων των λειτουργιών.
*   **`core/database_manager.py`:** Διαχειρίζεται την SQLite βάση, τα Embeddings και το Schema Migration.
*   **`core/ai_manager.py`:** Ο "εγκέφαλος" που διαχειρίζεται τα LLMs με Circuit Breakers και failover μηχανισμούς.

### **Operational Layer (Συλλογή & Εμπλουτισμός)**
*   **`daily_search.py`:** Καθημερινή περιπολία για νέα άρθρα.
*   **`historic_search.py`:** Μαζική ιστορική αναζήτηση.
*   **`data_enricher.py` (v4.8):** Μαζικός εμπλουτισμός δεδομένων (PDF links, IDs) μέσω Unpaywall.

### **Strategic & Analytical Layer (Ανάλυση)**
*   **`trend_analyzer.py` (v4.8):** Δημιουργία επιστημομετρικών αναφορών και γραφημάτων.
*   **`knowledge_path_generator.py` (CHIRON):** Δημιουργία στρατηγικών μονοπατιών ανάγνωσης.
*   **`citation_analyzer.py` (ORPHEUS):** Ανάλυση δικτύου αναφορών (Citation Network).
*   **`author_profiler.py`:** Ανάλυση προφίλ και πορείας ερευνητών.

### **Presentation Layer (Οπτικοποίηση)**
*   **`interactive_dashboard.py` (NAFSIKA):** Ένα πλήρες Web Dashboard (Flask) για την εξερεύνηση της βάσης με Semantic Search και Article DNA visualization.

---

## 4. Εγκατάσταση & Χρήση

### Βήμα 1: Προετοιμασία
1.  **Python 3.9+** απαιτείται. Προτείνεται η χρήση Conda environment.
2.  Εγκατάσταση εξαρτήσεων:
    ```bash
    pip install -r requirements.txt
    ```

### Βήμα 2: Ρύθμιση
1.  Μετονομάστε το `env.example` σε `.env` και προσθέστε τα κλειδιά σας (Google Gemini API, Unpaywall Email, κλπ).
2.  Αν είναι η πρώτη φορά, το `talos.py` θα ξεκινήσει αυτόματα τον οδηγό εγκατάστασης και την "Πυθία" για να φτιάξετε το πρώτο σας προφίλ.

### Βήμα 3: Εκτέλεση
Τρέξτε το κεντρικό μενού:
```bash
python talos.py
```

---

## 5. Δομή Φακέλων

```
Project_TALOS/
├── talos.py                 # Main Launcher
├── _profiles/               # Isolated Research Profiles (DBs, Configs)
├── core/                    # System Core (DB, AI Manager)
├── scripts/                 # Functional Modules
│   ├── data_enricher.py     # Unpaywall Integration
│   ├── trend_analyzer.py    # Scientometrics
│   ├── ...
├── sources/                 # API Agents (ArXiv, Scopus, etc.)
├── reports/                 # Generated HTML/Markdown reports
└── templates/               # HTML Templates for Dashboard
```

---

## 📄 Citation & Academic Use

This software is part of ongoing PhD research. If you use TALOS in your work, please cite it as follows until the official paper is published:

> **Smarlamakis, C., & Georgopoulos, E., [Αρχικό]. (2025).** *Project TALOS: Tactical Agentic Literature Orchestration System.* GitHub Repository. https://github.com/Christos-Smarlamakis/Project-TALOS

**⚠️ A formal paper presenting the methodology and scientometric analysis capabilities of TALOS is currently in preparation.**

---

## ⚖️ License & Commercial Use

This project is open-source software licensed under the **GNU Affero General Public License v3.0 (AGPLv3)**.

### 🎓 For Researchers, Students, and Open Source Developers
You are free to use, modify, and distribute this software for academic, research, and personal purposes, provided that any modifications or derived works are also open-sourced under the AGPLv3 license.

### 🏢 For Commercial & Proprietary Use
If you wish to use **Project TALOS** in a proprietary software product, a commercial service (SaaS), or any environment where you do not wish to release your source code, you **must purchase a Commercial License**.

A Commercial License grants you:
*   The right to use TALOS in closed-source / proprietary products.
*   Exemption from the copyleft requirements of AGPLv3.
*   Priority support and guidance on integration.

📩 **For commercial inquiries and licensing, please contact:** [christossmarlamakis@gmail.com](christossmarlamakis@gmail.com)

---
*Designed & AI-Augmented Developed by Christos Smarlamakis.*