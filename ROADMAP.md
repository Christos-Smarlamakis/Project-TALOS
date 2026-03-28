# Project TALOS - Στρατηγικός Οδικός Χάρτης & Δεξαμενή Ιδεών

Αυτό το έγγραφο λειτουργεί ως η "πυξίδα" ανάπτυξης και η δεξαμενή σκέψης (Think Tank) του Project TALOS. Καταγράφει τον βραχυπρόθεσμο σχεδιασμό (Actionable Roadmap) και τους μακροπρόθεσμους στρατηγικούς άξονες για την εξέλιξη της πλατφόρμας, διασφαλίζοντας ότι η ανάπτυξη παραμένει εστιασμένη, καινοτόμα και ακαδημαϊκά αυστηρή.

---

## 1. Το Όραμα & Η Τρέχουσα Κατάσταση

**Το Όραμα:** Η μετάβαση από ένα εργαλείο αναζήτησης (Aggregator) σε έναν **Προσωπικό Στρατηγικό Μέντορα Έρευνας (Autonomous Research Intelligence Platform)**, ικανό να λειτουργεί αυτόνομα, να αξιολογεί σημασιολογικά την επιστημονική γνώση και να προετοιμάζει περιβάλλοντα δοκιμών (Simulations) για τον ερευνητή.

**Τρέχουσα Κατάσταση - v4.8.0 (Production Stable):**
Το σύστημα διαθέτει πλήρη υποστήριξη προφίλ, αξιολόγηση 4 επιπέδων (Quad-Layer Framework: Strategic, Operational, Tactical, Playground), δυναμικό εμπλουτισμό μεταδεδομένων (Data Enrichment via Unpaywall) και παραγωγή επιστημομετρικών αναφορών (Scientometrics Suite).

---

## 2. Βραχυπρόθεσμο Σχέδιο Δράσης (The Actionable Roadmap)

Τα άμεσα επόμενα βήματα ανάπτυξης (Εκδόσεις v4.9.x - v5.x).

### **v4.9.0 - The Content Retriever (PDF Downloader)**
*   **Στόχος:** Η αυτόματη ανάκτηση του πλήρους κειμένου (PDF) των άρθρων.
*   **Υλοποίηση:** Αξιοποίηση των `oa_pdf_url` που συλλέγει το σύστημα εμπλουτισμού για την αυτόματη, μαζική λήψη και οργάνωση των PDF σε τοπική βιβλιοθήκη (`_library/pdfs/`). Ενημέρωση της βάσης δεδομένων με τα τοπικά paths.

### **v5.0.0 - The Agentic Swarm Orchestration (AgentScope Migration)**
*   **Στόχος:** Η μετάβαση από στατικά Python scripts σε ένα δυναμικό "Σμήνος Πρακτόρων" (Agent Swarm).
*   **Υλοποίηση:** Ενσωμάτωση του **AgentScope framework**. 
    *   **Agentic RL (Reinforcement Learning):** Οι πράκτορες αξιολόγησης θα εκπαιδεύονται από το feedback του χρήστη.
    *   **Message Hub:** Οι πράκτορες (Scout, Evaluator, Enricher) θα επικοινωνούν ασύγχρονα, αποφασίζοντας αυτόνομα ποιος αναλαμβάνει δράση.

### **v5.1.0 - The RAG Engine (GraphRAG & Document Processing)**
*   **Στόχος:** Η υπέρβαση του απλού Vector Search και η ικανότητα του συστήματος να "διαβάζει" και να "κατανοεί" το πλήρες κείμενο.
*   **Υλοποίηση:** Ενσωμάτωση τεχνολογιών όπως το **OpenRAG** και το **RAG-Anything**. Δημιουργία τοπικών Knowledge Graphs από τα κατεβασμένα PDF, επιτρέποντας την κατανόηση ιεραρχικών και σημασιολογικών σχέσεων (π.χ. "Σύγκρινε τα αποτελέσματα του Πίνακα 3 από το paper A με τη μεθοδολογία του paper B").

---

## 3. Μακροπρόθεσμοι Στρατηγικοί Άξονες (The Think Tank)

Ιδέες και τεχνολογίες που εξετάζονται για τις μελλοντικές εκδόσεις (v6.0+).

### Α. Άξονας "Δεδομένα & Νοημοσύνη" (Data & Intelligence Layer)

*   **API Load Balancing & Zero-Cost Inference:** Εξάλειψη του κόστους API μέσω δυναμικής δρομολόγησης. Ο `AIManager` θα διαθέτει ένα "Pool" από παρόχους (Groq, Cerebras, GitHub Models, OpenRouter). Εργασίες ταχύτητας θα δρομολογούνται σε Llama-3.3 (Groq), ενώ εργασίες βαθιάς σκέψης σε DeepSeek-R1. 
*   **Consensus Scoring:** Πολλαπλά LLM μοντέλα θα βαθμολογούν το ίδιο paper, εξάγοντας τον μέσο όρο για μέγιστη ακαδημαϊκή αντικειμενικότητα και μείωση των "παραισθήσεων" (hallucinations).
*   **Local LLM Sovereignty (Ollama Integration):** Πλήρης ανεξαρτησία από Cloud APIs για απόλυτη ιδιωτικότητα και μηδενικό κόστος, χρησιμοποιώντας τοπικά μοντέλα (π.χ. Llama-3, Mistral) για εργασίες ρουτίνας.
*   **Local Big Data & Offline Mirroring:** Μετάβαση σε offline βάση εκατομμυρίων εγγραφών (ETL pipelines για Semantic Scholar S2ORC dumps, OAI-PMH Harvesters).
*   **Source Agent Expansion:** Προσθήκη εξειδικευμένων πρακτόρων, όπως DataCite (για Datasets/Software), ACM Digital Library, και Scilit.

### Β. Άξονας "Προσομοίωση & Εφαρμογή" (The Playground Layer)
*Αξιοποίηση του "Playground Score" και γεφύρωση της βιβλιογραφίας με τον πειραματισμό.*

*   **Geospatial Knowledge Graphs (Urbanity Integration):** Αυτόματη παραγωγή αστικών περιβαλλόντων δοκιμής (Testbeds). Αν εντοπιστεί άρθρο για "UAV Urban Navigation", το σύστημα θα χρησιμοποιεί το **Urbanity** για να εξάγει τον πραγματικό γράφο της πόλης (δρόμοι, κτίρια) σε μορφή έτοιμη για Graph Machine Learning.
*   **3D Simulation Rendering (Forge3D Integration):** Παραγωγή "Publication-Quality" 3D απεικονίσεων. Χρήση του **forge3d** (GPU-accelerated rendering) για την οπτικοποίηση τοπογραφικών δεδομένων (DEMs, LiDAR) και την αναπαράσταση των τροχιών των Drones (trajectories) σε ρεαλιστικά, 3D περιβάλλοντα δοκιμών.

### Γ. Άξονας "Εκπαίδευση & Κοινότητα" (Pedagogical & Social Layer)

*   **Socratic Tutor Integration (DeepTutor Concept):** Ενσωμάτωση μεθοδολογιών Σωκρατικής διδασκαλίας. Ένα "Study Mode" όπου το AI κάνει ερωτήσεις στον χρήστη για να ελέγξει την κατανόηση ενός paper (Active Recall), προετοιμάζοντάς τον για την υποστήριξη της διατριβής.
*   **Social Sentiment & Community Pulse:** Διασύνδεση με το Reddit API για τον εντοπισμό συζητήσεων σε επιστημονικά subreddits (π.χ. r/MachineLearning), συνοψίζοντας την αποδοχή (community sentiment) και την κριτική ενός νέου paper.

### Δ. Άξονας "Διεπαφή & Μεθοδολογία" (Interface & Methodology)

*   **Spec-Driven Development (SDD):** Αυστηρή, αυτοματοποιημένη μηχανική λογισμικού με χρήση αυτόνομων AI Agents. Αξιοποίηση εργαλείων όπως το **Spec Kit** (specify-cli) και το Claude Code. Ο προγραμματιστής ορίζει τις προδιαγραφές και το AI αναλαμβάνει την υλοποίηση, διατηρώντας την αρχιτεκτονική συνέπεια.
*   **Unified Desktop Application (GUI):** Μετάβαση από CLI/Web dashboard σε αυτόνομη εφαρμογή (PyQt/Electron) με ενσωματωμένο PDF Viewer, Real-time Logs και Interactive Graphs.
*   **Background Automation (The Watchtower):** Υπηρεσία παρασκηνίου (Daemon/Cron Job) που εκτελεί την καθημερινή αναζήτηση/εμπλουτισμό αυτόματα και στέλνει Push Notifications (Discord/Email) μόνο για άρθρα με κορυφαία βαθμολογία.

---

## 4. Συνοπτικός Πίνακας Εκδόσεων

| Έκδοση | Εστίαση (Focus) | Κατάσταση |
| :--- | :--- | :--- |
| **v4.0 - v4.7** | Quad-Layer Scoring, AI Configuration, Zotero Sync | ✅ **ΟΛΟΚΛΗΡΩΘΗΚΕ** |
| **v4.8.0** | **Data Enrichment & Scientometrics Suite** (Hub IDs, Visualizations) | ✅ **ΤΡΕΧΟΥΣΑ (STABLE)** |
| **v4.9.0** | **The Content Retriever** (Αυτόματο κατέβασμα PDF, Directory Management) | ⏳ **ΕΠΟΜΕΝΟ ΒΗΜΑ** |
| **v5.0.0** | **The Agentic Swarm Update** (AgentScope Integration, Agentic RL) | 📅 Σχεδιασμός |
| **v5.1.0** | **The RAG Engine** (OpenRAG, GraphRAG, PDF Chat) | 🔮 Μελλοντικό |
| **v6.0.0** | **The Playground Integration** (Urbanity/Forge3D for Simulations) | 🔮 Μελλοντικό |