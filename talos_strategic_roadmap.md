# Project TALOS - Στρατηγικός Οδικός Χάρτης Εξέλιξης (Έκδοση v4.2.0)

## 1. Όραμα & Αρχιτεκτονική

**Όραμα:** Το TALOS δεν είναι πλέον απλά ένας aggregator. Είναι ένας **Προσωπικός Στρατηγικός Μέντορας Έρευνας (Personal Strategic Research Mentor)**. Στόχος είναι η μετάβαση από τη συλλογή πληροφορίας ("τι υπάρχει;") στη σύνθεση γνώσης ("τι σημαίνει για εμένα;") και την ενεργή καθοδήγηση.

**Αρχιτεκτονική:** Υβριδική, αρθρωτή δομή με κεντρική βάση δεδομένων (SQLite), ανεξάρτητους πράκτορες συλλογής (Requests-based Agents) και κεντρικό εγκέφαλο AI (Model-Agnostic AIManager). Υποστηρίζει πολλαπλά ερευνητικά προφίλ (Profiles) και πολυδιάστατη αξιολόγηση (Quad-Layer).

**Status:** **PRODUCTION STABLE (v4.2.0)**. Όλα τα υποσυστήματα (Genesis, CHIRON, PYTHIA, Profiles) λειτουργούν αρμονικά.

---

## 2. Επίπεδο 0: Τα Κεκτημένα (The Foundation - v4.2+)

Αυτά τα modules έχουν ολοκληρωθεί και αποτελούν τον πυρήνα του συστήματος.

*   **Project "PYTHIA" & Profile System (v4.x):**
    *   Πλήρης διαχείριση πολλαπλών ερευνητικών προφίλ (`profile_manager.py`).
    *   Αυτόματη διαμόρφωση (Auto-Configuration) μέσω AI για νέα ερευνητικά πεδία.
    *   Αξιολόγηση 4 επιπέδων (Strategic, Operational, Tactical, Playground).
*   **Operation "Genesis" (Data Layer - v3.2 Refined):**
    *   Μια αψεγάδιαστη βάση δεδομένων με 12+ αναβαθμισμένους πράκτορες (Direct API access, Multi-Query strategy).
    *   Robust Rate Limiting και Error Handling.
*   **Project "CHIRON" (Strategy Layer):**
    *   Δημιουργία αφηγηματικών "Μονοπατιών Γνώσης" με clickable links και scores.
*   **Project "NAFSIKA" (UI Layer):**
    *   Διαδραστικό Dashboard με Semantic Search και Article DNA.
*   **Core Infrastructure:**
    *   JSON-enforced AI outputs, Circuit Breakers, Database Migration tools.

---

## 3. Επίπεδο 1: Η Επόμενη Φάση - Βάθος & Πρόσβαση (The Immediate Future)

Ο στόχος εδώ είναι η μετάβαση από τα Metadata στο **Full Content**.

### **Project "HERMES" (The Content Retriever)**
*   **Στόχος:** Η αυτόματη ανάκτηση του **πλήρους κειμένου (PDF)** των άρθρων.
*   **Στρατηγική:**
    *   Ενσωμάτωση "shadow libraries" (π.χ., Anna's Archive metadata scraping) ή Open Access APIs (Unpaywall) για την εύρεση direct download links.
    *   Δημιουργία τοπικής βιβλιοθήκης PDF συνδεδεμένης με τα IDs της βάσης SQLite.

### **Project "MNEMOSYNE" (The RAG Engine)**
*   **Στόχος:** Η δυνατότητα του TALOS να "διαβάζει" τα PDF που κατέβασε ο HERMES και να απαντά σε ερωτήσεις.
*   **Στρατηγική:**
    *   Αξιοποίηση του νέου **Google Gemini File Search API** (Managed RAG).
    *   Ανέβασμα των "Elite Papers" στο Cloud Vector Store της Google.
    *   Δυνατότητα ερωτήσεων ("Chat with your Library").

### **Project "CHIRON" v2.0 (The Conversationalist)**
*   **Στόχος:** Μετατροπή του CHIRON από γεννήτρια αναφορών σε συνομιλητή.
*   **Στρατηγική:**
    *   Υλοποίηση interactive loop όπου το AI ζητά διευκρινίσεις ("Εννοείς DRL για path planning ή για task allocation;") πριν δημιουργήσει το μονοπάτι γνώσης.

---

## 4. Επίπεδο 2: Ανεξαρτησία & Οικονομία (The Sovereign Era)

Ο στόχος εδώ είναι η μείωση του κόστους και η απεξάρτηση από cloud APIs.

### **Project "HEPHAESTUS" (The Local Forge - OLLAMA)**
*   **Στόχος:** Εκτέλεση του TALOS αποκλειστικά σε τοπικό hardware.
*   **Στρατηγική:**
    *   Ενσωμάτωση του **Ollama** στον `AIManager` ως νέου provider.
    *   Χρήση μοντέλων όπως `Llama-3` ή `Mistral` για εργασίες ρουτίνας (π.χ., extraction, summarization) για μηδενικό κόστος.
    *   Κράτημα του Gemini/DeepSeek μόνο για τις πολύ απαιτητικές "Strategic" αναλύσεις.

---

## 5. Επίπεδο 3: Το Τελικό Όραμα (The Endgame)

Μακροπρόθεσμα projects μεγάλης κλίμακας.

### **Project "ATHENA" (The GUI)**
*   **Στόχος:** Η δημιουργία μιας πλήρους Desktop εφαρμογής.
*   **Στρατηγική:**
    *   Αντικατάσταση του CLI και του Web Dashboard με μια ενιαία εφαρμογή σε **PyQt**.
    *   Drag-and-drop λειτουργίες, real-time logs, ενσωματωμένος PDF viewer.

### **Project "GAIA" (The Big Data)**
*   **Στόχος:** Η δημιουργία τοπικών mirrors ολόκληρων ακαδημαϊκών βάσεων.
*   **Στρατηγική:**
    *   OAI-PMH Harvesters για ScienceGate.
    *   *Προαπαιτούμενο:* Αναβάθμιση hardware (Storage/RAM).

---

## 6. Συνοπτικός Πίνακας Εκδόσεων

| Έκδοση | Κωδικό Όνομα | Κύριος Στόχος | Κατάσταση |
| :--- | :--- | :--- | :--- |
| **v2.x** | The Reliability Update | Σταθεροποίηση, JSON Mode, Database Migration | ✅ **ΟΛΟΚΛΗΡΩΘΗΚΕ** |
| **v3.x** | The Strategic Mentor | CHIRON, Genesis (Data Quality), Resilience | ✅ **ΟΛΟΚΛΗΡΩΘΗΚΕ** |
| **v4.0-4.2** | The Adaptive Architecture | **Profiles, Quad-Layer, Pythia** | ✅ **ΤΡΕΧΟΥΣΑ (STABLE)** |
| **v4.3** | The Content Retriever | **Project HERMES (PDF Downloading)** | ⏳ **ΕΠΟΜΕΝΟ** |
| **v4.4** | The RAG Intelligence | **Project MNEMOSYNE (Chat with PDFs)** | 📅 Σχεδιασμός |
| **v5.0** | The Sovereign System | **Ollama Integration (Local LLMs)** | 📅 Σχεδιασμός |
| **v6.0** | The Desktop Experience | **Project ATHENA (GUI)** | 🔮 Μελλοντικό |

---