# Project TALOS — Στρατηγικός Οδικός Χάρτης & Δεξαμενή Ιδεών

Αυτό το έγγραφο λειτουργεί ως η "πυξίδα" ανάπτυξης και η δεξαμενή σκέψης (Think Tank) του Project TALOS. Καταγράφει τον βραχυπρόθεσμο σχεδιασμό (Actionable Roadmap) και τους μακροπρόθεσμους στρατηγικούς άξονες για την εξέλιξη της πλατφόρμας μετά την ολοκλήρωση της v5.0.1.

---

## 1. Το Όραμα & Η Τρέχουσα Κατάσταση

**Το Όραμα:** Η μετάβαση από ένα εργαλείο αναζήτησης (Aggregator) σε έναν **Πλήρως Αυτόνομο Ερευνητικό Βοηθό (Autonomous Research Intelligence Platform)**, ικανό να επιλέγει βέλτιστα APIs μέσω Deep Reinforcement Learning, να αξιολογεί σημασιολογικά την επιστημονική γνώση, να ειδοποιεί ενεργά τον ερευνητή, και να προετοιμάζει περιβάλλοντα δοκιμών (Simulations).

**Τρέχουσα Κατάσταση — v5.0.1 (Production Stable):**
Το σύστημα διαθέτει:
- **DRL Agent (LSTM-DDDQN)** εκπαιδευμένο σε 3.849 πραγματικά paper scores με RTX 4070 CUDA 12.1
- **Grey Wolf Optimizer** για hyperparameter tuning με αποθήκευση σε JSON
- **Quad-Layer Framework** (Strategic, Operational, Tactical, Playground) για αξιολόγηση papers
- **Multi-Provider Hybrid Embeddings** (Ollama nomic-embed-text + Gemini gemini-embedding-001)
- **Baseline Report Generator** με academic-quality plots (600 DPI, IEEE/Springer)
- **24/7 Autonomous Research Service** με Telegram/Discord/Email notifications
- **Streamlit Web GUI** + **CLI TUI** με πλήρη πρόσβαση σε όλες τις λειτουργίες
- **Profile Management System** για απομονωμένα research profiles
- **14 API Sources** (6 keyless, 4 optional, 4 premium) με graceful degradation

---

## 2. Βραχυπρόθεσμο Σχέδιο Δράσης (Actionable Roadmap) — v5.x

Τα άμεσα επόμενα βήματα ανάπτυξης, αξιοποιώντας τις νέες δυνατότητες του DRL agent.

### **v5.1.0 — DRL Dashboard & TUI/GUI Reorganization**

**Στόχος:** Οπτικοποίηση της απόδοσης του DRL agent και αναδιάταξη των μενού για καλύτερη εμπειρία χρήστη.

**Υλοποίηση:**
- **DRL Agent Status** στο System Diagnostics: δείχνει αν το μοντέλο είναι trained, GWO best params, training metrics
- **Training Visualization**: reward/επεισόδιο γράφημα, epsilon decay, action distribution
- **Compare Baselines**: τρέχει baseline report και συγκρίνει πριν/μετά τον DRL agent
- **Αναδιάταξη TUI**: DRL Training → Analysis & Insights (από ξεχωριστό entry)
- **GUI DRL Tab**: γραφήματα εκπαίδευσης, "Apply GWO Best Params" button

**Κατάσταση:** 📅 Σχεδιασμός (επόμενο βήμα)

### **v5.2.0 — Real API Integration for DRL Agent**

**Στόχος:** Ο DRL agent να κάνει **πραγματικά API calls** αντί για simulated scores από τη βάση.

**Υλοποίηση:**
- Το `TalosEnv.step()` να καλεί πραγματικά APIs (ArXiv, OpenAlex, Semantic Scholar)
- Online learning: ο agent βελτιώνεται συνεχώς από πραγματικά αποτελέσματα
- A/B Testing: σύγκριση random selection vs DRL selection σε πραγματικό σενάριο

**Κατάσταση:** 🔮 Μελλοντικό

### **v5.3.0 — Advanced DRL Architectures**

**Στόχος:** Βελτίωση του DRL agent με πιο προηγμένες αρχιτεκτονικές.

**Υλοποίηση:**
- **PPO (Proximal Policy Optimization)** ή **SAC (Soft Actor-Critic)** ως εναλλακτικές του DDQN
- **Multi-Agent RL**: ξεχωριστοί agents ανά API source που συνεργάζονται
- **Curiosity-driven exploration**: intrinsic rewards για unexplored states
- **Transfer Learning**: pre-training σε simulated data, fine-tuning σε real data

**Κατάσταση:** 🔮 Μελλοντικό

---

## 3. Μακροπρόθεσμοι Στρατηγικοί Άξονες (Think Tank) — v6.0+

Ιδέες και τεχνολογίες που εξετάζονται για τις μελλοντικές εκδόσεις.

### Α. Άξονας "Δεδομένα & Νοημοσύνη" (Data & Intelligence Layer)

| Ιδέα | Περιγραφή | Προτεραιότητα |
|------|-----------|-------------|
| **Real-Time API Orchestration** | Ο DRL agent επιλέγει APIs σε πραγματικό χρόνο με real API calls — όχι simulated | 🔴 HIGH |
| **Consensus Scoring** | Πολλαπλά LLMs βαθμολογούν το ίδιο paper, μέσος όρος για αντικειμενικότητα | 🟡 MEDIUM |
| **Local LLM Sovereignty** | Πλήρης ανεξαρτησία από Cloud APIs με τοπικά μοντέλα (Ollama) | 🟡 MEDIUM |
| **RAG Engine (GraphRAG)** | Κατανόηση πλήρους κειμένου PDF με Knowledge Graphs και semantic search | 🔴 HIGH |
| **API Load Balancing** | Dynamic routing σε pool παρόχων (Groq, Cerebras, OpenRouter) για zero-cost inference | 🟢 LOW |
| **Source Agent Expansion** | DataCite (datasets/software), ACM Digital Library, Scilit | 🟢 LOW |

### Β. Άξονας "Προσομοίωση & Εφαρμογή" (Playground Layer)

| Ιδέα | Περιγραφή | Προτεραιότητα |
|------|-----------|-------------|
| **DRL-Driven Simulation** | Ο agent προτείνει simulation configurations με βάση το Playground score | 🟡 MEDIUM |
| **Geospatial Knowledge Graphs** | Αυτόματη παραγωγή αστικών testbeds από papers για UAV navigation | 🟢 LOW |
| **3D Simulation Rendering** | Publication-quality 3D απεικονίσεις τροχιών drones | 🟢 LOW |

### Γ. Άξονας "Εκπαίδευση & Κοινότητα" (Pedagogical & Social Layer)

| Ιδέα | Περιγραφή | Προτεραιότητα |
|------|-----------|-------------|
| **Socratic Tutor** | Study mode με Active Recall — το AI κάνει ερωτήσεις στον χρήστη | 🟢 LOW |
| **Social Sentiment** | Reddit API για community sentiment νέων papers | 🟢 LOW |

### Δ. Άξονας "Διεπαφή & Μεθοδολογία" (Interface & Methodology)

| Ιδέα | Περιγραφή | Προτεραιότητα |
|------|-----------|-------------|
| **DRL Dashboard** | Γραφήματα εκπαίδευσης, reward tracking, action distribution | 🔴 HIGH |
| **Compare Baselines** | Πριν/μετά σύγκριση της επίδρασης του DRL agent στη βάση | 🔴 HIGH |
| **Unified Desktop App** | PyQt/Electron εφαρμογή με ενσωματωμένο PDF viewer | 🟢 LOW |
| **Mobile Notifications** | Push notifications για high-score papers στο κινητό | 🟢 LOW |

---

## 4. Συνοπτικός Πίνακας Εκδόσεων

| Έκδοση | Εστίαση (Focus) | Κατάσταση |
|:---|:---|:---|
| **v4.0 – v4.7** | Quad-Layer Scoring, AI Configuration, Zotero Sync | ✅ ΟΛΟΚΛΗΡΩΘΗΚΕ |
| **v4.8.0** | Data Enrichment & Scientometrics Suite | ✅ ΟΛΟΚΛΗΡΩΘΗΚΕ |
| **v4.9.0 – v4.11.0** | Streamlit GUI, Model Management, Project Map & Diagnostics | ✅ ΟΛΟΚΛΗΡΩΘΗΚΕ |
| **v5.0.0** | **DRL Agent + Hybrid Embeddings + Baseline Reports + Autonomous Service** | ✅ **ΟΛΟΚΛΗΡΩΘΗΚΕ** |
| **v5.0.1** | GWO JSON Export | ✅ **ΟΛΟΚΛΗΡΩΘΗΚΕ** |
| **v5.1.0** | **DRL Dashboard & TUI/GUI Reorganization** | 📅 **ΕΠΟΜΕΝΟ ΒΗΜΑ** |
| **v5.2.0** | Real API Integration for DRL Agent | 🔮 Μελλοντικό |
| **v5.3.0** | Advanced DRL Architectures (PPO, SAC) | 🔮 Μελλοντικό |
| **v6.0.0** | RAG Engine, GraphRAG, PDF Chat | 🔮 Μελλοντικό |

---

> **Τελευταία ενημέρωση:** 2026-07-04
> **Τρέχουσα έκδοση:** v5.0.1
> **DRL Agent:** Εκπαιδευμένος (LSTM-DDDQN, 3.849 scores, RTX 4070 CUDA 12.1)
> **GWO Best Params:** `models/gwo_best_params.json`