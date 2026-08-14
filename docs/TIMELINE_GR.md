# Project TALOS -- Ιστορικό Χρονολόγιο (Ελληνικά)

> **Σκοπός:** Το παρόν έγγραφο αποτελεί την έγκυρη χρονολογική καταγραφή όλων των αναπτυξιακών, ερευνητικών και αρχιτεκτονικών οροσήμων του Project TALOS. Κάθε αλλαγή έκδοσης, νέο χαρακτηριστικό και breaking change καταγράφεται εδώ.
>
> **Κανόνας:** Μετά από ΚΑΘΕ αλλαγή έκδοσης, αυτό το αρχείο ΠΡΕΠΕΙ να ενημερώνεται με το νέο ορόσημο και την κατάστασή του.
>
> **Τελευταία Ενημέρωση:** 2026-08-14 (v5.9.16 -- Αναβάθμιση Αυτόνομου Κόκκινου Ελεγκτή: Μετονομασία, Βαθύ API Fuzzing & Περικοπή Περιεχομένου)

---

## Φάση 27: Αναβάθμιση Αυτόνομου Κόκκινου Ελεγκτή - Μετονομασία, Βαθύ API Fuzzing & Περικοπή Περιεχομένου (v5.9.16)

### Κατάσταση: ΟΛΟΚΛΗΡΩΜΕΝΗ (2026-08-14)

- [x] **Μετονομασία `src/ai/testing/autonomous_tester.py` σε `red_tester.py`** και `src/api/tester_routes.py` σε `red_tester_routes.py` -- σημείο εισόδου `run_red_tester()`, ετικέτα δρομολογητή `red_tester`, διατήρηση προθέματος `/api/v1/tester` για συμβατότητα με το frontend.
- [x] **Μετεγκατάσταση αρχείων μονιμότητας** -- `data/tester_q_table.json` σε `data/red_tester_q_table.json`, `data/reports/autonomous_tester/` σε `data/reports/red_tester/`.
- [x] **Βαθύ API Fuzzing** -- η υβριδική ανακάλυψη βραχιόνων (`_discover_all_targets()`) προσθέτει τέσσερις βραχίονες API fuzzing κατά του `http://127.0.0.1:8001` (ακατάλληλο JSON webhook Synapse, αρνητικό αναγνωριστικό εργασίας, κενό ερώτημα σημασιολογικής αναζήτησης, άκυρη πηγή scrape). Οι ευγενείς απορρίψεις (400/404/422) είναι επιτυχία· τα HTTP 5xx και τα timeouts είναι καταρρεύσεις.
- [x] **Περικοπή Περιεχομένου LLM** -- το `_protect_context_window()` περικόπτει το stderr κατάρρευσης στους τελευταίους 2.000 χαρακτήρες πριν τη διάγνωση από το Fast Edge LLM.
- [x] **Συγχρονισμός και των 5 αρχείων κώδικα και 15 αρχείων τεκμηρίωσης σε v5.9.16**

## Φάση 26: Ενίσχυση DRL & Δαιμόνων, Αυτόματη Λήψη Μοντέλων, Σιωπηλή Εκκίνηση & Συμφιλίωση Χάρτη Εξαρτήσεων (v5.9.15)

### Κατάσταση: ΟΛΟΚΛΗΡΩΜΕΝΗ (2026-08-14)

- [x] **Πλήρης έλεγχος υποσυστημάτων DRL και δαιμόνων** -- Ελέγχθηκαν και τα 10 σενάρια Ενισχυτικής Μάθησης και παρασκηνιακών υπηρεσιών στα `src/ai/drl/`, `src/ai/optimizers/` και `src/ai/testing/`. Επιβεβαιώθηκαν η κανονικοποίηση ώρας `/24.0`, ο τερματισμός χρονικού ορίου Gymnasium, τα soft updates, η κανονική διατύπωση GWO και η ακεραιότητα του MAB chaos fuzzer.
- [x] **Συμφιλίωση Γράφου Εξαρτήσεων Ενότητας 7 στα αρχεία PROJECT_MAP** -- Αναδομήθηκε η Ενότητα 7 με τη νέα διάταξη `src.*` (DDD), εξαλείφοντας τις προειδοποιήσεις απόκλισης.
- [x] **Σιωπηλή Γρήγορη Εκκίνηση** -- Αφαιρέθηκε ο παλαιός έλεγχος μοντέλων κατά την εκκίνηση, ώστε το `talos.py` να εκκινεί απευθείας στο Rich dashboard.
- [x] **Αυτόματη λήψη τοπικών μοντέλων AI στους εκκινητές** -- Τα `run_talos.bat` και `run_talos.sh` ανακτούν τα Neutrino-8B και Qwen2.5:14b κατά την εγκατάσταση.
- [x] **Δημιουργία docs/TECH_RADAR_GR.md** -- Πλήρης ελληνική απόδοση του Τεχνολογικού Ραντάρ.
- [x] **Συγχρονισμός και των 5 αρχείων κώδικα και 15 αρχείων τεκμηρίωσης σε v5.9.15**

## Φάση 25: Διόρθωση Υποδομής Docker & Οδηγός Χρήσης (v5.9.14)

### Κατάσταση: ΟΛΟΚΛΗΡΩΜΕΝΗ (2026-08-14)

- [x] **Διόρθωση ξεπερασμένων αρχείων Docker και προσθήκη αναλυτικού οδηγού χρήσης** -- Διορθώθηκαν οι κεφαλίδες v5.8.2 σε `Dockerfile`, `docker-compose.yml`, `.dockerignore` και `example.env` σε v5.9.14. Προστέθηκε bootstrap `config.json` από το `config.template.json`, volume `_profiles/`, αφαιρέθηκε το deprecated κλειδί `version:` και οι τοπικές διευθύνσεις μοντέλων ορίστηκαν σε `host.docker.internal`. Προστέθηκε το `docs/DOCKER.md` και διορθώθηκαν οι οδηγίες Docker στο README.

---

## Φάση 24: Συγχρονισμός Τεκμηρίωσης & Έκδοσης (v5.9.14)

### Κατάσταση: ΟΛΟΚΛΗΡΩΜΕΝΗ (2026-08-04)

- [x] **Συγχρονισμός συμβολοσειρών έκδοσης σε 4 αρχεία κώδικα και 15 αρχεία τεκμηρίωσης σε v5.9.14** -- `config/settings.py` TALOS_VERSION από 5.9.13 σε 5.9.14. `talos.py` docstring ενότητας ενημερώθηκε. `src/api/main_api.py` έκδοση FastAPI, περιγραφή και μήνυμα εκκίνησης ενημερώθηκαν. `tests/test_multi_tier.py` ισχυρισμός και docstring ενημερώθηκαν. Τα changelogs (EN, GR) έλαβαν καταχωρήσεις v5.9.14. Τα έγγραφα δυνατοτήτων (MD, HTML) και οι εκκινητές batch/POSIX είχαν ήδη ενημερωθεί από τον χρήστη.
- [x] **Έλεγχοι μεταγλώττισης και επαλήθευση pytest** -- Και τα 4 τροποποιημένα αρχεία `.py` περνούν `python -m py_compile`. Ο ισχυρισμός `test_talos_version` περνάει με επιτυχία.

---

## Φάση 23: Academic Print Theme (Light Mode) Injection for AST Graphs (v5.9.13)

### Κατάσταση: ΟΛΟΚΛΗΡΩΜΕΝΗ (2026-08-02)

- [x] **Υλοποίηση μετα-επεξεργασίας HTML στο graphify_adapter.py για εισαγωγή εναλλαγής Light/Dark** -- Προστέθηκε η βοηθητική συνάρτηση `_inject_light_mode_toggle()` η οποία ανοίγει το παραγόμενο `graph.html`, εισάγει ένα πλήρες μπλοκ CSS που ορίζει την κλάση `.light-mode` στο `<body>` (λευκό φόντο, σκούρο κείμενο, κόμβοι υψηλής αντίθεσης για ακαδημαϊκή εκτύπωση), και εισάγει ένα αιωρούμενο κουμπί εναλλαγής στην επάνω δεξιά γωνία. Το αρχικό σκούρο θέμα διατηρείται ως προεπιλογή. Ο χρήστης εναλλάσσει θεματολογία με ένα μόνο κλικ. Όλο το CSS χρησιμοποιεί `!important` για να υπερισχύει των δυναμικά εισαγόμενων σκούρων στυλ του Graphify. Χαριτωμένη υποβάθμιση σε σφάλματα εισόδου/εξόδου -- η διοχέτευση δεν αποτυγχάνει ποτέ λόγω αποτυχίας εισαγωγής.
- [x] **Υποχρεωτικός συγχρονισμός και των 15 αρχείων τεκμηρίωσης και 5 αρχείων κώδικα σε v5.9.13**

---

## Φάση 22: Graphify Output Path Resolution & Auto-Clustering Fix (v5.9.12)

### Κατάσταση: ΟΛΟΚΛΗΡΩΜΕΝΗ (2026-08-02)

- [x] **Διόρθωση ανάλυσης διαδρομής graphify-out στο graphify_adapter.py** -- Το Graphify παράγει το ``graphify-out/`` εντός του καταλόγου προορισμού (π.χ., ``src/graphify-out/``) αντί στη ρίζα του project. Ο προσαρμογέας επιλύει πλέον τη σωστή διαδρομή πηγής ενώνοντας το ``target_dir`` με το ``graphify-out``, με εφεδρική συμβατότητα προς τη ρίζα του project.
- [x] **Προσθήκη αυτόματης εκτέλεσης cluster-only για παραγωγή HTML/Markdown** -- Μετά την επιτυχή εξαγωγή, ο προσαρμογέας εκκινεί αυτόματα μια δεύτερη υποδιεργασία που εκτελεί ``python -m graphify cluster-only <target_dir> --no-label``. Η σημαία ``--no-label`` παρακάμπτει τις κλήσεις LLM για ονοματοδοσία κοινοτήτων, διατηρώντας 100% λειτουργία εκτός σύνδεσης (air-gapped). Αυτό παράγει το ``GRAPH_REPORT.md`` και αποδίδει αριθμητικές ετικέτες κοινοτήτων χωρίς να απαιτείται ξεχωριστή χειροκίνητη εντολή.
- [x] **Υποχρεωτικός συγχρονισμός και των 15 αρχείων τεκμηρίωσης και 5 αρχείων κώδικα σε v5.9.12**

---

## Φάση 21: Hotfix Εξαρτήσεων Vendored Graphify (v5.9.11)

### Κατάσταση: ΟΛΟΚΛΗΡΩΜΕΝΗ (2026-08-02)

- [x] **Προσθήκη των tree-sitter-python και rapidfuzz στο requirements.txt** -- Η υποδιεργασία του vendored Graphify AST engine απέτυχε με `ModuleNotFoundError: No module named 'rapidfuzz'` και έλλειψη του `tree_sitter_python`. Προστέθηκαν και τα δύο στην ενότητα "Graphify AST Knowledge Graph".
- [x] **Υποχρεωτικός συγχρονισμός και των 15 αρχείων τεκμηρίωσης και 5 αρχείων κώδικα σε v5.9.11**

---

## Φάση 20: Ενσωμάτωση Vendored Graphify AST & Αναδιοργάνωση Μενού Rich (v5.9.10)

### Κατάσταση: ΟΛΟΚΛΗΡΩΜΕΝΗ (2026-08-02)

- [x] **Προσθήκη εξαρτήσεων graphify (tree-sitter, networkx) στο requirements.txt**
- [x] **Δημιουργία src/analysis/graphify_adapter.py με αναφορά στο vendor/graphify**
- [x] **Αναδιοργάνωση του κεντρικού μενού talos.py σε οπτικές ομάδες Rich**
- [x] **Υποχρεωτικός συγχρονισμός και των 15 αρχείων τεκμηρίωσης και 5 αρχείων κώδικα σε v5.9.10**

---

## Φάση 19: Ενοποίηση Διαδρομών Αναφορών & Απομόνωση Καταλόγου Δεδομένων (v5.9.9)

### Κατάσταση: ΟΛΟΚΛΗΡΩΜΕΝΗ (2026-08-02)

- [x] **Ανακατεύθυνση όλων των εξόδων αναφορών στα src/analysis/ και autonomous_tester.py στο data/reports/**
- [x] **Μετακίνηση υπαρχόντων περιεχομένων του root reports/ στο data/reports/ και εκκαθάριση του καταλόγου root reports/**
- [x] **Ενημέρωση του tester_routes.py για ανάγνωση αναφορών από data/reports/autonomous_tester/**
- [x] **Υποχρεωτικός συγχρονισμός και των 15 αρχείων τεκμηρίωσης και 5 αρχείων κώδικα σε v5.9.9**

---

## Φάση 1: Αρχιτεκτονική & APIs (v5.0 -- v5.6)

- [x] **v5.0.0 -- Ο Πυρήνας Τεχνητής Νοημοσύνης** -- Υβριδικά embeddings πολλαπλών παρόχων, πράκτορας DRL (DDDQN), βελτιστοποίηση υπερπαραμέτρων GWO, δυναμικό περιβάλλον N-πηγών, πλαίσιο βαθμολόγησης 4 επιπέδων, μοτίβο circuit breaker για παρόχους AI.
- [x] **v5.1.0 -- Το Περιβάλλον Διεπαφής Insights** -- Ταμπλό DRL με κάρτες μετρήσεων, κατάσταση εκπαίδευσης πράκτορα, οπτικοποίηση προόδου ανταμοιβής, εκπαίδευση με επιτάχυνση GPU (CuDNN).
- [x] **v5.2.0 -- Ο Ζωντανός Πράκτορας** -- Οδηγός ενσωμάτωσης (4 βημάτων), ροή ερευνητικής ανακατεύθυνσης, δυναμική στοίβα DRL με 14 ακαδημαϊκές πηγές, λήψη PDF μέσω Unpaywall.
- [x] **v5.2.1 -- Ακαδημαϊκό Συνέδριο** -- Δίγλωσσος επανασχεδιασμός GUI (Αγγλικά/Ελληνικά), αναβάθμιση θέματος CSS, λειτουργία παρουσίασης ακαδημαϊκού συνεδρίου.
- [x] **v5.3.0 -- Αυτόματη Τεκμηρίωση** -- Γεννήτρια τεκμηρίωσης 18 γλωσσών, αναφορά δυνατοτήτων συστήματος, καθολική δημιουργία τεκμηρίωσης.
- [x] **v5.3.1 -- Ζωντανός Πράκτορας DRL** -- Ενορχήστρωση με επίγνωση παρόχου (παρακολούθηση Gemini/DeepSeek/HuggingFace/Local), μηχανισμός cooldown για αποφυγή ντετερμινιστικών βρόχων.
- [x] **v5.3.2 -- Αποσπώμενα Δίκτυα** -- Εξαγωγή αρχιτεκτονικής δικτύου DRL, DuelingLSTM ως εγχύσιμο στοιχείο, επεκτασιμότητα για μελλοντικές αρχιτεκτονικές.
- [x] **v5.3.3 -- Θέμα Μόνο-Φωτεινό** -- Αφαίρεση σκοτεινής λειτουργίας, καθολικός κανόνας τεκμηρίωσης, κάλυψη όλων των τύπων αρχείων από το προοδευτικό πρότυπο τεκμηρίωσης.
- [x] **v5.3.4 -- Περιγραφικά Ονόματα** -- Αντικατάσταση μυθολογικών κωδικών ονομάτων με ακαδημαϊκούς τίτλους ενοτήτων (CHIRON -> Knowledge Path Generator, ORPHEUS -> Citation Network Analyzer, PYTHIA -> Query Translator, APOLLO -> Metadata Enricher).
- [x] **v5.3.5 -- Επιστημονική Ακεραιότητα DRL** -- GWO v2.0 με πραγματική αξιολόγηση fitness (όχι τυχαίο θόρυβο), κανονικός αλγόριθμος Grey Wolf Optimizer (Mirjalili 2014), έλεγχος Batch 1 για mismatch κατανομής εκπαίδευσης/αξιολόγησης.
- [x] **v5.3.6 -- Ενίσχυση TUI/CLI** -- Ανθεκτικότητα σε Ctrl+C σε όλο το CLI, διόρθωση ανενεργής επιλογής μενού, φρουροί safe_pause() και safe_select(), έλεγχος Batch 2.
- [x] **v5.3.7 -- Επαναβελτιστοποίηση GWO** -- Πλήρης εκτέλεση εκπαίδευσης 9.5 ωρών, τελικές υπερπαράμετροι: LR=3.361e-05, GAMMA=0.6983, EPS_DECAY=0.9202.
- [x] **v5.4.0 -- Μετεγκατάσταση DDD** -- Διάταξη πακέτων Domain-Driven Design, μετεγκατάσταση και των 55 αρχείων πηγαίου κώδικα στην ιεραρχία `src/` (ai/, analysis/, api/, core/, ingestion/, utils/).
- [x] **v5.4.1 -- Εκκαθάριση Ρίζας** -- Δημιουργία καταλόγων `docs/` και `tools/`, μοτίβα άρνησης .gitignore για μόνιμα αρχεία τεκμηρίωσης.
- [x] **v5.5.0 -- Πρόσοψη REST FastAPI** -- 8 REST endpoints (health, papers, semantic search, scrape/GWO triggers, task status), διόρθωση διαδρομής βάσης δεδομένων σε `data/talos_research.db`, 16 μοντέλα Pydantic v2.
- [x] **v5.5.1 -- Εμπειρία Προγραμματιστή Frontend** -- +2 endpoints: ιστορικό GWO για Recharts <LineChart> και γράφημα αρχιτεκτονικών εξαρτήσεων HTML μέσω FileResponse.
- [x] **v5.5.2 -- 100% Κάλυψη Οικοσυστήματος** -- +4 endpoints: αξιολόγηση μεμονωμένου paper με AI, μετάφραση φυσικής γλώσσας σε boolean query, συγκέντρωση κορυφαίων συγγραφέων, μαζικός επανυπολογισμός βαθμολογιών. Σύνολο: 14 endpoints.
- [x] **v5.6.0 -- Headless API & Επιβολή Τεκμηρίωσης** -- BREAKING: Πλήρης κατάργηση Streamlit. Διαγραφή `app.py` (1,175 γραμμές), `.streamlit/`, `tools/_gui_runner.py`. Αφαίρεση του `streamlit` από το `requirements.txt`. Μοναδικό frontend είναι React 18 + Tailwind CSS + Shadcn UI. FastAPI αναβαθμισμένο σε 15 endpoints (+`/api/v1/capabilities`). Δημιουργία `docs/SYSTEM_CAPABILITIES_MASTER.md` και `.html` (δομημένη αναφορά 9 ενοτήτων). Επιβολή κανόνα συγχρονισμού 12 αρχείων τεκμηρίωσης στο `.clinerules`. Δημιουργία `docs/API_HANDOVER_FOTIS.md`, `docs/UX_UI_BLUEPRINT_FOTIS.md`, `docs/IP_PROTECTION_STRATEGY.md`.

---

## Φάση 2: Ευθυγράμμιση με το Master Standard v2.0 (v5.7.2)

- [x] **v5.7.2 -- Αναβάθμιση Συντάγματος v2.0** -- Αναβάθμιση του `.clinerules` από κανόνα συγχρονισμού 12 αρχείων σε 15 αρχεία. Προσθήκη των εγγράφων Χρονολογίου ως έγκυρης ιστορικής καταγραφής (αρχεία #8 και #9 στον κανόνα των 15). Δημιουργία `docs/TIMELINE_EN.md` και `docs/TIMELINE_GR.md` (αυτό το αρχείο).
- [x] **Πρωτόκολλο Διαλειτουργικότητας SYNAPSE** -- Δημιουργία `src/integration/synapse_client.py` (κλάση EventEmitter) και `src/api/synapse_routes.py` (FastAPI APIRouter με `POST /api/v1/synapse/webhook`). Ενσωμάτωση του Synapse router στο `main_api.py`. Ανακατανομή θυρών: TALOS FastAPI στη θύρα 8001 (ήταν 8000), SYNAPSE bus στη θύρα 8000.
- [x] **Αυτοματοποιημένος Batch Runner** -- Δημιουργία `run_talos.bat` στη ρίζα του project με μενού 3 επιλογών: (1) Πλήρης Εγκατάσταση με Conda environment και pip install, (2) Εκκίνηση FastAPI Server στη θύρα 8001, (3) Εκτέλεση Test Suite μέσω `pytest -v`. Μετονομασία του παλαιού `tools/start_talos.bat` ως αρχειακή αναφορά.
- [ ] **Αναδόμηση όλων των υπαρχόντων αρχείων Python ώστε να συμμορφώνονται με το νέο αυστηρό πρότυπο Module-level Docstring** -- Εφαρμογή της Ενότητας VIII του Συντάγματος σε κάθε αρχείο `.py` στους καταλόγους `src/`, `tools/` και στη ρίζα. Κάθε module πρέπει να ξεκινά με την ακριβή μορφή: Όνομα module, Έκδοση Project, Περιγραφή (2-4 προτάσεις), Λίστα Εξαρτήσεων.

---

## Φάση 3: Πολυεπίπεδη Δρομολόγηση LLM, POSIX Πολλαπλών Πλατφορμών & Διασφάλιση Ποιότητας (v5.7.2)

- [x] **v5.7.2 -- Πολυεπίπεδη Δρομολόγηση LLM** -- Υλοποίηση παραμέτρου `tier` ("fast"|"heavy") στην `AIManager._execute_request()`. Το γρήγορο επίπεδο δρομολογείται στο Neutrino-8B μέσω αποκλειστικού edge endpoint (127.0.0.1:11435). Το βαρύ επίπεδο χρησιμοποιεί το τυπικό Ollama (127.0.0.1:11434) με το qwen2.5:14b. Μεταβλητές περιβάλλοντος: `FAST_EDGE_MODEL`, `FAST_EDGE_BASE_URL`, `HEAVY_REASONING_MODEL`, `OLLAMA_BASE_URL`. Δημιουργία του `config/settings.py` ως κανονικού κόμβου ρυθμίσεων.
- [x] **Απομονωμένος Προμηθευτής Ενδιάμεσης Διεπαφής** -- Δημιουργία του `src/utils/frontend_provisioner.py`. Κατεβάζει το φορητό Cherry Studio (CherryHQ/cherry-studio) βάσει λειτουργικού συστήματος στον φάκελο `cherry_ui_isolated/` (gitignored). Αυτόματα παράγει αρχείο ρυθμίσεων MCP JSON για το Cherry Studio που δείχνει στο `src/mcp_server.py`.
- [x] **Εκκινητής POSIX Πολλαπλών Πλατφορμών** -- Δημιουργία του `run_talos.sh` που αντικατοπτρίζει το `run_talos.bat` με 5 επιλογές: (1) Πλήρης Εγκατάσταση με virtualenv + pip install, (2) Εκκίνηση FastAPI Server στη θύρα 8001, (3) Εκκίνηση MCP Server, (4) Εκκίνηση Ενδιάμεσης Διεπαφής (Cherry Studio), (5) Εκτέλεση Σουίτας Pytest. Έτοιμο με `chmod +x` για Linux/macOS.
- [x] **Έλεγχος Anti-Greeklish** -- Σάρωση όλων των αρχείων `*_GR.md` (PROJECT_MAP_GR, TIMELINE_GR, CHANGELOG_GR, README_GR, ROADMAP_GR, USER_GUIDE_GR). Αντικατάσταση οποιουδήποτε μεταγραμματισμένου κειμένου Greeklish με επίσημη, ακαδημαϊκή ελληνική γραφή χρησιμοποιώντας σωστούς χαρακτήρες Unicode και τόνους. Οι τεχνικοί όροι διατηρούνται στα Αγγλικά.
- [x] **Μοναδιαίες Δοκιμές (Pytest)** -- Δημιουργία `tests/test_synapse.py` (κάλυψη EventEmitter + webhook route), `tests/test_multi_tier.py` (λογική δρομολόγησης fast vs. heavy), `tests/test_provisioner.py` (ανίχνευση λειτουργικού συστήματος και παραγωγή ρυθμίσεων). Όλες οι δοκιμές περνούν μέσω `pytest -v`.
- [x] **Συγχρονισμός 15 Αρχείων Τεκμηρίωσης** -- Ενημέρωση της συμβολοσειράς έκδοσης σε v5.7.2 και στα 15 κανονικά αρχεία τεκμηρίωσης. Καταγραφή όλων των προσθηκών της v5.7.2 στα CHANGELOG_EN.md και CHANGELOG_GR.md. Συγχρονισμός των PROJECT_MAP_EN.md και PROJECT_MAP.md με νέα modules και εξαρτήσεις.

---

## Φάση 4: Αναδόμηση TUI Πολλαπλών Επιπέδων & Λειτουργίες Εκτέλεσης (v5.8.9)

- [x] **v5.8.9 -- Συνολική Αναδόμηση του Διαχειριστή Μοντέλων** -- Πλήρης έλεγχος και αναδόμηση του `src/ai/llm/model_manager.py`. Αφαίρεση παλαιών `sys.path` hacks (διπλότυπο `import os, sys`, χειροκίνητη αναρρίχηση διαδρομών με while-loop). Τυποποίηση της επίλυσης διαδρομών μέσω `pathlib.Path` προς το `config/settings.py` και τη ρίζα του project. Εξάλειψη όλων των Unicode emojis από banners, υπομενού και ενδείξεις κατάστασης -- αντικατάσταση με επίσημα ASCII text badges ([CONNECTED], [OFFLINE], [INSTALLED], [RECOMMENDED], [FITS], [TIGHT], [TOO BIG]). Αναδιάρθρωση του μενού 5 επιλογών σε μενού 7 επιλογών που υποστηρίζει αρχιτεκτονική τριών επιπέδων.
- [x] **Υλοποίηση Συναρτήσεων Ρύθμισης Πολλαπλών Επιπέδων** -- `select_fast_edge_model()`: Ρυθμίζει το FAST_EDGE_MODEL και το FAST_EDGE_BASE_URL για βελτιστοποιημένη CPU εξαγωγή συμπερασμάτων στη θύρα 11435. `select_heavy_model()`: Ρυθμίζει το HEAVY_REASONING_MODEL και το OLLAMA_BASE_URL για βελτιστοποιημένη GPU συλλογιστική στη θύρα 11434. Και οι δύο επαναχρησιμοποιούν τους κοινούς εσωτερικούς βοηθούς `_browse_and_pick_ollama_model()` και `_pick_quantization()` που εξήχθησαν από την προηγούμενη μονολιθική `select_ollama_model()`. Προστέθηκε ο βοηθός `_install_if_needed()` για συνεπή λογική pull-before-save. `select_execution_mode()`: Ορίζει το TALOS_EXECUTION_MODE σε "local" (απομονωμένο), "hybrid" (τοπικό + cloud εφεδρικό) ή "cloud" (προτεραιότητα cloud), με ενημερώσεις συμβατότητας προς τα πίσω για τα TALOS_USE_LOCAL και TALOS_ALLOW_CLOUD_FALLBACK.
- [x] **Ενημέρωση του `select_cloud_models()`** -- Πλέον εισάγει προεπιλεγμένα ονόματα μοντέλων από το `config/settings.py` (κανονικός κόμβος ρυθμίσεων) αντί για hardcoded συμβολοσειρές. Οι ενότητες ρύθμισης Gemini/DeepSeek/HF παραμένουν αμετάβλητες στη συμπεριφορά. Αφαιρέθηκαν οι μη χρησιμοποιούμενες εισαγωγές `time` και `json` από το module.
- [x] **Επιβολή Πρωτοκόλλου Μηδενικών Emojis** -- Έλεγχος και απολύμανση όλων των συμβολοσειρών εξόδου TUI. Η `_fits_label()` επιστρέφει πλέον καθαρά ASCII text badges: `[FITS]`, `[TIGHT]`, `[TOO BIG]`. Όλες οι κεφαλίδες ενοτήτων (`[CONNECTED]`, `[OFFLINE]`, `[INSTALLED]`, `[RECOMMENDED]`), γραμμές κατάστασης και προτροπές χρήστη χρησιμοποιούν επίσημη ακαδημαϊκή γλώσσα. Κανένα σύμβολο Unicode σε καμία εντολή print.
- [x] **Δημιουργία Σουίτας Μοναδιαίων Δοκιμών** -- `tests/test_model_manager.py` με 29 περιπτώσεις δοκιμών που καλύπτουν: `check_ollama_alive()` (3 δοκιμές), ομαδοποίηση κβαντισμού `_categorize_tags()` (11 δοκιμές), δείκτες καταλληλότητας VRAM `_fits_label()` (6 δοκιμές), συμπεριφορά ενημέρωσης κλειδιών `.env` (3 δοκιμές), `get_installed_models()` (2 δοκιμές), `get_available_tags()` (2 δοκιμές) και επίλυση διαδρομών (2 δοκιμές). Και οι 29 δοκιμές περνούν με `pytest -v`.
- [x] **Αναβάθμιση Έκδοσης σε v5.8.9** -- `config/settings.py`: Προστέθηκε η σταθερά `TALOS_EXECUTION_MODE` με σημασιολογία "local"/"hybrid"/"cloud", το `TALOS_VERSION` άλλαξε σε "5.8.0". `src/api/main_api.py`: Η έκδοση εφαρμογής, η περιγραφή και το αρχείο καταγραφής εκκίνησης ενημερώθηκαν σε v5.8.9 με αναφορά Multi-Tier LLM.
- [x] **Συγχρονισμός 15 Αρχείων Τεκμηρίωσης** -- Ενημέρωση της συμβολοσειράς έκδοσης σε v5.8.9 και στα 15 κανονικά αρχεία τεκμηρίωσης. Καταγραφή των αλλαγών της v5.8.9 στα CHANGELOG_EN.md και CHANGELOG_GR.md. Συγχρονισμός των PROJECT_MAP_EN.md και PROJECT_MAP.md.

---

## Φάση 5: Κεντρικοί Εκκινητές, Αυτόνομοι Δαίμονες, Σουίτα 96 Unit Tests (v5.8.9)

- [x] **v5.8.9 -- Κεντρικοί Εκκινητές 9 Επιλογών** -- Τα `run_talos.bat` και `run_talos.sh` επεκτάθηκαν από μενού 3 επιλογών σε δομημένο μενού 9 επιλογών σε τρεις ενότητες: REST API & FRONTEND (Πλήρης Εγκατάσταση, FastAPI, MCP Server, Cherry Studio), CLI & ΑΥΤΟΝΟΜΟΙ ΔΑΙΜΟΝΕΣ (TALOS Terminal CLI, Αυτόνομος Ερευνητικός Δαίμονας `talos_service.py`, Ζωντανός DRL Πράκτορας `talos_live_agent.py --verbose`), TESTING & SYSTEM (Pytest, Exit). Η Πλήρης Εγκατάσταση περιλαμβάνει πλέον τον Frontend Provisioner ως βήμα 4/4.
- [x] **Διευρυμένη Σουίτα Δοκιμών (96 Unit Tests)** -- Μεταφορά του `tools/test_smoke.py` στο `tests/test_smoke.py` με ετικέτες [PASS]/[FAIL]/[SKIP] χωρίς emoji, ενισχυμένη `check()` για διάδοση BaseException/SystemExit, προστασία `sys.exit()` πίσω από `__name__`. Ενημέρωση της βεβαίωσης TALOS_VERSION στο `tests/test_multi_tier.py`. Σύνολο: 96 επιτυχείς, 0 αποτυχίες.
- [x] **Εκκαθάριση Φακέλου Tools** -- Διαγραφή `tools/start_talos.bat` (αντικαταστάθηκε από το ριζικό `run_talos.bat`), `tools/_bump.py`, `tools/_git_status.ps1`. Μεταφορά `tools/test_smoke.py` στο `tests/`. Τα `tools/_gui_runner.py` και `tools/_git_out.txt` ήταν ήδη απόντα. Ο φάκελος `tools/` διατηρήθηκε (ενεργά `_bump_docs.py` και `_fix_changelogs.py`).
- [x] **Συγχρονισμός 16 Αρχείων Τεκμηρίωσης (v5.8.9)** -- Ενημέρωση της συμβολοσειράς έκδοσης σε v5.8.9 και στα 16 κανονικά αρχεία τεκμηρίωσης. Καταγραφή των αλλαγών της v5.8.9 στα CHANGELOG_EN.md και CHANGELOG_GR.md (επίσημα Ελληνικά με τόνους). Ενημέρωση των TIMELINE_EN.md και TIMELINE_GR.md.

---

## Φάση 7: Αυτοματοποίηση Εκκινητή & Εκκίνηση Μηδενικής Επαφής Πολλαπλών Πλατφορμών (v5.8.9)

- [x] **v5.8.9 -- Αυτόματη Ανίχνευση Διαδρομής Conda στα Windows** -- Το `run_talos.bat` σαρώνει πέντε κοινούς καταλόγους εγκατάστασης Miniconda/Anaconda για το `Scripts\activate.bat`. Η ανιχνευθείσα διαδρομή αποθηκεύεται στη μεταβλητή `CONDA_ACTIVATE_PATH` και χρησιμοποιείται μέσω επαναχρησιμοποιήσιμης υπορουτίνας `:ACTIVATE_CONDA`. Επιστρέφει στην τυπική εντολή `conda` αν δεν βρεθεί το activate.bat. Επιλύει το συνηθισμένο σφάλμα των Windows όπου η `conda` δεν βρίσκεται καθολικά στο PATH.
- [x] **v5.8.9 -- Εκκίνηση σε Ελαχιστοποιημένα Παρασκηνιακά Παράθυρα στα Windows** -- Οι FastAPI (Επιλογή 2) και MCP server (Επιλογή 3) εκκινούν σε ξεχωριστά ελαχιστοποιημένα παράθυρα μέσω `start "..." /min cmd /c`. Η Επιλογή 4 εκκινεί αυτόματα την αλυσίδα υποστήριξης: (1) εκκίνηση FastAPI στο παρασκήνιο, (2) αναμονή 2 δευτερολέπτων, (3) εκτέλεση του frontend provisioner. Το κύριο μενού επιστρέφει αμέσως.
- [x] **v5.8.9 -- Ανίχνευση Virtualenv/Conda σε POSIX** -- Το `run_talos.sh` ανιχνεύει αυτόματα περιβάλλοντα Python με σειρά προτεραιότητας: (1) τοπικό `.venv/bin/activate`, (2) τοπικό `venv/bin/activate`, (3) Conda `talosenv` μέσω δυναμικής επίλυσης `conda info --base`. Επιστρέφει στο Python συστήματος με σαφή προειδοποίηση.
- [x] **v5.8.9 -- Αποσπασμένοι Δαίμονες Παρασκηνίου σε POSIX** -- Οι FastAPI (Επιλογή 2) και MCP server (Επιλογή 3) εκκινούν ως αποσπασμένες διεργασίες παρασκηνίου με ανακατεύθυνση εξόδου στο `/dev/null`. Η Επιλογή 4 υλοποιεί αυτόματη αλυσίδα υποστήριξης: (1) εκκίνηση uvicorn στο παρασκήνιο, (2) αναμονή 2 δευτερολέπτων, (3) εκτέλεση frontend provisioner. Πλήρης ισοτιμία χαρακτηριστικών με τον εκκινητή των Windows.
- [x] **v5.8.9 -- Πλήρης επανεγγραφή `run_talos.sh` πολλαπλών πλατφορμών** -- Πλήρης εκκινητής POSIX με μενού 9 επιλογών, έγχρωμη έξοδο τερματικού, χειρισμό σφαλμάτων `set -e` και κλήσεις `detect_and_activate_env()` ανά επιλογή. Και οι δύο εκκινητές μοιράζονται πανομοιότυπη δομή μενού και σύνολο χαρακτηριστικών.
- [x] **v5.8.9 -- Εξαναγκασμένος Συγχρονισμός Και των 15 Αρχείων Τεκμηρίωσης** -- Όλες οι συμβολοσειρές έκδοσης ενημερώθηκαν σε v5.8.9 στα 15 κανονικά αρχεία τεκμηρίωσης. Τα `.clinerules`, `config/settings.py`, `src/api/main_api.py` ενημερώθηκαν σε "5.8.3".

---

## Φάση 8: Πίνακας Ελέγχου Rich TUI & Ενσωμάτωση Model Manager CLI (v5.8.9)

- [x] **v5.8.9 -- Πίνακας Ελέγχου Rich TUI** -- Αντικατάσταση όλων των απλών `print()` στο `talos.py` με μορφοποίηση της βιβλιοθήκης `rich` (`Console`, `Panel`, `Table`, `Box`, `Text`). Προστέθηκε δυναμικός πίνακας κατάστασης στην κορυφή του κύριου μενού που δείχνει το περιβάλλον Conda, τη θύρα API (8001), τον δίαυλο Synapse (8000), την ενεργή λειτουργία εκτέλεσης (Air-Gapped Local / Hybrid / Cloud) και τα ενεργά επίπεδα (Fast Edge Neutrino-8B, Heavy Reasoning Qwen-14B, Cloud Provider Gemini/DeepSeek). Το μενού αναδιαρθρώθηκε σε 10 επιλογές με τον Model Manager ως αποκλειστική επιλογή 1.
- [x] **v5.8.9 -- Ενσωμάτωση Model Manager CLI** -- Ενσωμάτωση του `src/ai/llm/model_manager.py` στο κύριο μενού του `talos.py` ως επιλογή 1 ("Configure AI Models & Execution Modes"). Καλεί το `model_manager.main()` απευθείας μέσω εισαγωγής αντί για εκκίνηση υποδιεργασίας, επιτρέποντας τη ρύθμιση εντός διεργασίας χωρίς τη δημιουργία θυγατρικής διεργασίας Python.
- [x] **v5.8.9 -- Επιβολή Πρωτοκόλλου Μηδενικών Emojis σε όλο το TUI** -- Όλη η έξοδος με μορφοποίηση Rich επαληθεύτηκε ότι δεν περιέχει Unicode emojis. Επαγγελματικός χρωματικός συνδυασμός σκούρου σχιστόλιθου/μπλε με περιγράμματα πάνελ `box.ROUNDED`. Όλοι οι δείκτες κατάστασης χρησιμοποιούν επίσημο κείμενο ASCII.
- [x] **v5.8.9 -- Ενημέρωση Εξαρτήσεων** -- Προστέθηκε το `rich` στο `requirements.txt` για καλλωπισμό του τερματικού UI.
- [x] **v5.8.9 -- Συγχρονισμός 15 Αρχείων Τεκμηρίωσης** -- Όλες οι συμβολοσειρές έκδοσης ενημερώθηκαν σε v5.8.9 στα 15 κανονικά αρχεία τεκμηρίωσης. Τα `config/settings.py`, `src/api/main_api.py` ενημερώθηκαν σε "5.8.4".

---

---

## Φάση 8β: Καθολική Καλλωπιστική Αναβάθμιση TUI & Σφράγιση Καθαρής Κυκλοφορίας (v5.8.9)

- [x] **v5.8.9 -- Διόρθωση Εμφάνισης Ονόματος Μοντέλου TUI** -- Διορθώθηκε η `_build_status_table()` στο `talos.py` ώστε να εμφανίζει την πλήρη ακατέργαστη συμβολοσειρά ρύθμισης και για τα τρία ενεργά επίπεδα αντί για περικοπή μέσω `split(":")`. Το Επίπεδο Βαριάς Συλλογιστικής τώρα δείχνει "qwen2.5:14b" αντί για "14b".
- [x] **v5.8.9 -- Καθολική Επικάλυψη Υπομενού με Rich Panels** -- Όλες οι εκκινήσεις ενδιάμεσων υπομενού (Επιλογές 2d-2e Live DRL Agent/Autonomous Process, 2l Compare Baselines, 3 Metadata Enrichment, 4 PYTHIA Query Translator, 6-7 Baseline Reports, 9 Docs Generator) εμφανίζουν πλέον πλαίσια πληροφοριών με χρωματικά κωδικοποιημένα περιγράμματα (κυανό/κίτρινο/πράσινο/ματζέντα) πριν την εκκίνηση της υποδιεργασίας. Ο βοηθός `_build_info_panel()` κατασκευάζει μορφοποιημένα αντικείμενα `rich.panel.Panel` με περιγράμματα `box.ROUNDED`.
- [x] **v5.8.9 -- Πίνακας Αποτελεσμάτων Αναζήτησης Rich** -- Προστέθηκε ο βοηθός `_build_results_table()` για την κατασκευή μορφοποιημένων πινάκων αποτελεσμάτων αναζήτησης με στήλες: ID (κυανό), Title (λευκό/έντονο, περιορισμένο στους 100 χαρακτήρες), Source (ματζέντα), Year (κίτρινο), Overall Score (σμαραγδί/έντονο). Τα elite papers (overall_score >= 7) επισημαίνονται με χρυσό χρώμα.
- [x] **v5.8.9 -- Αισθητική Τερματικού Επιστημονικής Φαντασίας** -- Όλη η έξοδος του `run_script()` χρησιμοποιεί πλέον το `rich.console` για μηνύματα εκκίνησης/ολοκλήρωσης/ακύρωσης/σφάλματος με μορφοποιημένα χρώματα (κυανό/κίτρινο/κόκκινο/αχνό πράσινο). Αντικαταστάθηκαν τα απλά `print()` με `console.print()` χρησιμοποιώντας σήμανση Rich.
- [x] **v5.8.9 -- Σφράγιση Καθαρής Κυκλοφορίας** -- Και τα 15 κανονικά αρχεία τεκμηρίωσης συγχρονίστηκαν εξαναγκαστικά στην έκδοση v5.8.9. Οι συμβολοσειρές έκδοσης ενημερώθηκαν στα `config/settings.py`, `src/api/main_api.py`, `tests/test_multi_tier.py`, `.clinerules` και στα 14 αρχεία τεκμηρίωσης. Η βεβαίωση δοκιμής `test_talos_version` αναμένει "5.8.5".

---

## Φάση 8: Enterprise TUI Refactoring, Safety Locks & Navigation Audit (v5.8.9)

## Φάση 8β: Έλεγχος Διαδρομών Υπο-σεναρίων & Διόρθωση Ανάλυσης Config (v5.8.9)

### Κατάσταση: ΟΛΟΚΛΗΡΩΘΗΚΕ (2026-08-01)

- [x] **v5.8.9 -- Έλεγχος όλων των υπο-σεναρίων `src/` για εύθραυστη σχετική ανάλυση διαδρομής του config.json** -- Εντοπίστηκαν 17 αρχεία με μοτίβα `os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'config.json'))` που αποτυγχάνουν όταν τα σενάρια βρίσκονται σε βάθος μεγαλύτερο του ενός επιπέδου κάτω από τη ρίζα του project.
- [x] **v5.8.9 -- Αναδόμηση της ανάλυσης διαδρομής config.json ώστε να χρησιμοποιεί κανονική ανίχνευση ρίζας βάσει `_P`** -- Και τα 17 αρχεία επιλύουν πλέον τη ρίζα του project ανεβαίνοντας από το `__file__` μέχρι να βρεθεί το `talos.py` (μεταβλητή `_P` στην κορυφή του module). Εφεδρική χρήση του `config.template.json` αν το `config.json` απουσιάζει.
- [x] **v5.8.9 -- Αρχεία που αναδομήθηκαν** -- `src/analysis/`: citation_analyzer.py, author_profiler.py, architecture_intelligence_report.py, knowledge_path_generator.py. `src/ingestion/`: daily_search.py, historic_search.py, grey_literature_miner.py, pdf_downloader.py, zotero_connector.py, metadata_enricher.py, data_enricher.py. `src/utils/`: interactive_dashboard.py, reevaluate_database.py. `src/ai/`: embeddings/embedding_generator.py, llm/query_translator.py, drl/talos_env.py, drl/talos_live_agent.py.
- [x] **v5.8.9 -- Αναβάθμιση έκδοσης** -- `config/settings.py` TALOS_VERSION = "5.8.7", `src/api/main_api.py` έκδοση και μεταδεδομένα FastAPI, `tests/test_multi_tier.py` δοκιμή test_talos_version.
- [x] **v5.8.9 -- Επαλήθευση py_compile** -- Και τα 17 τροποποιημένα αρχεία + main_api.py περνούν το `python -m py_compile`.
- [x] **v5.8.9 -- Συγχρονισμός 15 Αρχείων Τεκμηρίωσης** -- Όλες οι συμβολοσειρές έκδοσης ενημερώθηκαν σε v5.8.9 στα 15 κανονικά αρχεία.


- [ ] **v5.8.9 -- Καθολική Αναδόμηση TUI & Κλειδαριές Ασφαλείας Πλοήγησης** -- Πλήρης οπτική αναδόμηση του `src/ai/llm/model_manager.py` με τη βιβλιοθήκη `rich` σε ΟΛΑ τα υπομενού (Fast Tier, Heavy Tier, Cloud Config, Execution Mode, Embedding Selection, Quantization Selector). Υλοποίηση κλειδαριών ασφαλείας επιχειρησιακού επιπέδου: ρητές επιλογές Cancel/Back σε κάθε υπομενού, και βοηθός `_confirm_setting_change()` με πάνελ επιβεβαίωσης `rich.panel.Panel` πριν από κάθε εγγραφή στο `.env`. Πίνακες Rich για επιλογή μοντέλων με στήλες: Model Name, Est. Size, VRAM Headroom Status, Installation State. Οι παραλλαγές κβαντισμού αποδίδονται σε δομημένες ομάδες bit-depth. Ο επιλογέας Execution Mode εμφανίζει πάνελ σύγκρισης. Το Cloud Configuration εμφανίζει την κατάσταση παρόχων σε δομημένα πάνελ. Επιβολή Πρωτοκόλλου Μηδενικών Emojis.
- [ ] **v5.8.9 -- Προστατευτικά Κιγκλιδώματα Πλοήγησης Υπομενού** -- Κάθε υπομενού (Fast Edge, Heavy Reasoning, Cloud Config, Execution Mode, Embedding Selection) περιλαμβάνει ρητή επιλογή `[Ακύρωση / Επιστροφή στο Κύριο Μενού]`. Χαριτωμένη επιστροφή χωρίς αλλαγές ή εξαιρέσεις.
- [ ] **v5.8.9 -- Επέκταση Unit Tests** -- Ενημέρωση του `tests/test_model_manager.py` με δοκιμές για τον βοηθό `_confirm_setting_change()`, ροές ακύρωσης υπομενού και απόδοση πινάκων rich. Όλες οι δοκιμές περνούν με `pytest -v`.
- [ ] **v5.8.9 -- Συγχρονισμός 15 Αρχείων Τεκμηρίωσης** -- Όλες οι συμβολοσειρές έκδοσης ενημερώθηκαν σε v5.8.9 στα 15 κανονικά αρχεία. Τα `config/settings.py`, `src/api/main_api.py`, `tests/test_multi_tier.py` ενημερώθηκαν.

---

## Φάση 10: Αυτόνομος Ελεγκτής Συστήματος (RL & LLM-Driven CI/CD) (v5.9.0)

- [x] **Δημιουργία `src/ai/testing/autonomous_tester.py` με Non-Stationary MAB και LLM-as-a-Judge** -- Mi Statheros Polyvrachionas Listis Epsilon-Greedy (epsilon=0.2, alpha=0.1) dokimazei 4 yposystimata TALOS (FastAPI Server, MCP Server, Daily Search, Citation Analyzer) meso ypodiergasion me 5-deuterolepto timeout. To stderr katarrifseon apostelletai sto Fast Edge LLM (tier="fast") gia diagnostiki anafora dyo protaseon. Antamoives: +50 (katarrefsi), -1 (epitychia). O Pinakas Q apothikevetai sto `data/tester_q_table.json`. Anaforres katarrifseon sto `reports/autonomous_tester/`.
- [x] **Ylopoiisi Optikopoiisis Rich TUI** -- Rich Spinners, kokkina Panels katarrifseon, kitrina Panels Diagnosis AI, prasines epivevaioseis PASS, egchromos Pinakas Q (Efthrafstotita: STABLE/LOW/MODERATE/HIGH_FRAGILITY).
- [x] **Dimiourgia `src/api/tester_routes.py` kai ensomatosi sto `main_api.py`** -- FastAPI APIRouter me `GET /api/v1/tester/status` kai `GET /api/v1/tester/reports`. Synolo endpoints: 16 -> 18.
- [x] **Enimerosi `talos.py`, `run_talos.bat`, kai `run_talos.sh`** -- Aftonomos Elegktis os epilogi 6 (talos.py) kai epilogi 8 (launchers). Menou: 10->11 (talos.py), 9->10 (launchers).
- [x] **Prosthiki 'Kanona Synchronismou Ekdosis Kodika' sto `.clinerules`**
- [x] **Exanagkasmenos Synchronismos 15 Archeion Tekmiriosis kai 5 Archeion Kodika se v5.9.0**

## Φάση 8γ: Ανθεκτική Εισαγωγή & Προστασία Elsapy (v5.8.9)

### Κατάσταση: ΟΛΟΚΛΗΡΩΘΗΚΕ (2026-08-01)

- [x] **v5.8.9 -- Χαριτωμένη Υποβάθμιση Εισαγωγής για το elsevier_source.py** -- Περιτυλίχθηκε η `from elsapy.elsclient import ElsClient`, `from elsapy.elssearch import ElsSearch` και `from elsapy.elsdoc import AbsDoc` σε μπλοκ `try...except ImportError:`. Η σημαία επιπέδου module `ELSAPY_AVAILABLE` ορίζεται σε `False` αν η εισαγωγή αποτύχει. Στην `ElsevierSource.__init__()`, ελέγχεται η `ELSAPY_AVAILABLE` πριν τη συνέχιση; καταγράφει προειδοποίηση `"elsapy library is not installed. Skipping Elsevier source."` και θέτει `self.enabled = False` με χάρη. Αποτρέπει το `ModuleNotFoundError` από το να καταρρεύσει ο αγωγός απόξεσης 14 πηγών.
- [x] **v5.8.9 -- Χαριτωμένη Υποβάθμιση Εισαγωγής για το zotero_connector.py** -- Περιτυλίχθηκε η `from pyzotero import zotero` σε μπλοκ `try...except ImportError:`. Η σημαία επιπέδου module `PYZOTERO_AVAILABLE` ορίζεται σε `False` αν η εισαγωγή αποτύχει. Στην `main()`, ελέγχεται η `PYZOTERO_AVAILABLE` στην είσοδο; καταγράφει προειδοποίηση `"pyzotero library is not installed. Skipping Zotero Bridge."` και επιστρέφει καθαρά.
- [x] **v5.8.9 -- Επαλήθευση requirements.txt** -- Τα `elsapy` και `pyzotero` υπάρχουν ήδη στην ενότητα Academic APIs (γραμμές 23, 25).
- [x] **v5.8.9 -- Αναβάθμιση Έκδοσης** -- `config/settings.py` TALOS_VERSION = "5.8.8", `src/api/main_api.py` έκδοση εφαρμογής και μεταδεδομένα FastAPI, `tests/test_multi_tier.py` ο ισχυρισμός test_talos_version αναμένει "5.8.8".
- [x] **v5.8.9 -- Επαλήθευση py_compile** -- Και τα δύο `elsevier_source.py` και `zotero_connector.py` περνούν το `python -m py_compile`.
- [x] **v5.8.9 -- Συγχρονισμός 15 Αρχείων Τεκμηρίωσης** -- Όλες οι συμβολοσειρές έκδοσης ενημερώθηκαν σε v5.8.9 στα 15 κανονικά αρχεία τεκμηρίωσης. Τα `.clinerules`, `config/settings.py`, `src/api/main_api.py`, `tests/test_multi_tier.py` ενημερώθηκαν.

---

## Φάση 11: Απόλυτη Εμπειρία TUI, Σύνοψη Focus μέσω LLM & Προηγμένοι Τρόποι Εκτέλεσης (v5.9.3)

- [ ] **v5.9.3 -- Ενεργή Σύνοψη Ερευνητικής Εστίασης μέσω LLM** -- Μετά τη δημιουργία των boolean queries από τον Query Translator, μία κλήση Fast Edge LLM συνοψίζει τον ερευνητικό στόχο σε έναν τίτλο 6-10 λέξεων που αποθηκεύεται ως `active_focus_summary` στο `config.json`. Ο πίνακας κατάστασης TUI εμφανίζει αυτήν την καθαρή σύνοψη με έντονο φωτεινό πράσινο χρώμα αντί να περικόπτει το raw system prompt στους 65 χαρακτήρες.
- [ ] **v5.9.3 -- Πίνακας 4 Τρόπων Εκτέλεσης** -- Ανακατασκευή της `select_execution_mode()` στο `model_manager.py` ώστε να προσφέρει 4 διακριτούς συνδυασμούς δρομολόγησης μέσω ενός εντυπωσιακού Rich Table: (1) Pure Local (Fast: Τοπική CPU | Heavy: Τοπική GPU), (2) Edge-to-Cloud Hybrid (Fast: Τοπική CPU | Heavy: Cloud API), (3) Cloud-to-Edge Hybrid (Fast: Cloud API | Heavy: Τοπική GPU), (4) Pure Cloud (Fast: Cloud API | Heavy: Cloud API). Νέες μεταβλητές `.env` `TALOS_FAST_ROUTING` και `TALOS_HEAVY_ROUTING` επιτρέπουν ανεξάρτητη ρύθμιση δρομολόγησης ανά επίπεδο.
- [ ] **v5.9.3 -- 100% Μετεγκατάσταση Υπομενού σε Rich στο model_manager.py** -- Όλες οι εναπομείνασες απλές `print()` στο `model_manager.py` (Fast Edge Tier, Heavy Reasoning Tier, Cloud Config, Execution Mode, Embedding Selection) αντικαταστάθηκαν με `rich.panel.Panel` και `rich.table.Table`. Ο επιλογέας τρόπου εκτέλεσης χρησιμοποιεί συγκριτικό πίνακα 4 γραμμών με στήλες: Ετικέτα Τρόπου, Δρομολόγηση Fast Tier, Δρομολόγηση Heavy Tier, Περίπτωση Χρήσης, Κατάσταση.
- [ ] **v5.9.3 -- Εξαναγκασμένος Συγχρονισμός Και των 15 Αρχείων Τεκμηρίωσης και 5 Αρχείων Κώδικα σε v5.9.3**

---

## Φάση 13: Διόρθωση Ανίχνευσης Περιβάλλοντος Conda (v5.9.3)

### Κατάσταση: ΟΛΟΚΛΗΡΩΘΗΚΕ (2026-08-01)

- [x] **v5.9.3 -- Διόρθωση Ανίχνευσης Περιβάλλοντος Conda** -- Ενημερώθηκε η `_build_status_table()` στο `talos.py` ώστε να χρησιμοποιεί εφεδρικό μηχανισμό `sys.prefix` για την ανίχνευση του περιβάλλοντος Conda. Όταν η μεταβλητή `CONDA_DEFAULT_ENV` δεν είναι ορισμένη (σύνηθες κατά την εκτέλεση μέσω VS Code ή απευθείας μέσω της διαδρομής του εκτελέσιμου Python), το script εξάγει πλέον το όνομα του περιβάλλοντος από το `os.path.basename(sys.prefix)` εάν το `"envs"` βρίσκεται στο `sys.prefix`, ή υποχωρεί στο `sys.base_prefix != sys.prefix` / `hasattr(sys, "real_prefix")` για ανίχνευση virtualenv. Ο πίνακας κατάστασης δεν εμφανίζει πλέον "N/A" κατά την εκτέλεση σε σωστά ενεργοποιημένο περιβάλλον Conda μέσω Python interpreter που εκτελείται με διαδρομή.
- [x] **v5.9.3 -- Εξαναγκασμένος Συγχρονισμός Και των 15 Αρχείων Τεκμηρίωσης και 5 Αρχείων Κώδικα σε v5.9.3** -- Όλες οι συμβολοσειρές έκδοσης ενημερώθηκαν. Ο ισχυρισμός δοκιμής ενημερώθηκε στο `tests/test_multi_tier.py`.

---

## Φάση 14: Προηγμένος Πίνακας 2D Εκτέλεσης & Δρομολόγηση με Εφεδρεία (v5.9.4)

### Κατάσταση: ΟΛΟΚΛΗΡΩΘΗΚΕ (2026-08-01)

- [x] **v5.9.4 -- Πίνακας 2D Εκτέλεσης (Στρατηγικές Δικτύου x Υλικού)** -- Αντικατάσταση του παλαιού `TALOS_EXECUTION_MODE` με ένα πλουσιότερο μοντέλο 2 διαστάσεων. Νέες μεταβλητές `.env`: `TALOS_NETWORK_STRATEGY` (strict_local | local_first | cloud_first | strict_cloud) και `TALOS_HARDWARE_STRATEGY` (cpu_only | gpu_only | cpu_gpu_split). Η στρατηγική δικτύου ελέγχει την εξάρτηση από το διαδίκτυο και τη συμπεριφορά αυτόματης εφεδρείας μεταξύ περιβαλλόντων. Η στρατηγική υλικού ελέγχει την επιλογή CPU/GPU κατά την τοπική εκτέλεση.
- [x] **v5.9.4 -- Ανακατασκευή του Οδηγού TUI στο model_manager.py** -- Η `select_execution_mode()` ξαναγράφτηκε ως οδηγός 2 βημάτων. Βήμα 1: Στρατηγική Δικτύου με πίνακα Rich που συγκρίνει 4 επιλογές. Βήμα 2: Στρατηγική Υλικού με πίνακα Rich που συγκρίνει 3 επιλογές. Πίνακας επιβεβαίωσης σύνοψης με ρητές προφυλάξεις Ακύρωσης/Επιστροφής και στα δύο βήματα.
- [x] **v5.9.4 -- Αναθεώρηση της Λογικής Δρομολόγησης του AIManager** -- Η `_execute_request()` ξαναγράφτηκε για να χρησιμοποιεί την `_resolve_strategies()` για τον πίνακα 2D. Νέες μέθοδοι: `_execute_local_strategy()` (με επίγνωση υλικού: cpu_only/gpu_only/cpu_gpu_split), `_execute_ollama_http()` (ενοποιημένο τοπικό HTTP POST για CPU edge και GPU Ollama), `_execute_cloud_chain()` (εκτέλεση μόνο cloud), `_execute_legacy_request()` (προς τα πίσω συμβατότητα). Αυτόματη εφεδρεία μεταξύ περιβαλλόντων: το local_first ανιχνεύει ConnectionError και επαναδρομολογεί στο cloud με [WARNING]. Το cloud_first επαναδρομολογεί στο τοπικό με [WARNING] σε κάθε αποτυχία cloud. Το strict_local και το strict_cloud δεν διασχίζουν ποτέ το όριο.
- [x] **v5.9.4 -- Ενημέρωση του Πίνακα Κατάστασης TUI στο talos.py** -- Η `_build_status_table()` εμφανίζει πλέον τον Πίνακα 2D Εκτέλεσης ως "Στρατηγική Δικτύου / Στρατηγική Υλικού" (π.χ. "Strict Local / CPU+GPU Split").
- [x] **v5.9.4 -- Εξαναγκασμένος Συγχρονισμός Και των 15 Αρχείων Τεκμηρίωσης και 5 Αρχείων Κώδικα σε v5.9.4** -- Όλες οι συμβολοσειρές έκδοσης ενημερώθηκαν. Ο ισχυρισμός δοκιμής ενημερώθηκε στο `tests/test_multi_tier.py`.

---

## Φάση 16: Ενοποίηση Καταλόγου Δεδομένων & Δυναμική Ανακάλυψη Στόχων σε Όλο το Αποθετήριο (v5.9.7)

### Κατάσταση: ΟΛΟΚΛΗΡΩΘΗΚΕ (2026-08-01)

- [x] **Μετεγκατάσταση REPORTS_DIR σε data/reports/autonomous_tester/** -- Αλλαγή του `REPORTS_DIR` από `reports/autonomous_tester/` (ρίζα) σε `data/reports/autonomous_tester/` στα `src/ai/testing/autonomous_tester.py` και `src/api/tester_routes.py`. Όλες οι αναφορές καταρρίψεων που παράγονται κατά την εκτέλεση βρίσκονται πλέον υπό τον κατάλογο `data/`, εξασφαλίζοντας καθαρή ρίζα έργου και σωστό αποκλεισμό μέσω `.gitignore`.
- [x] **Υλοποίηση _discover_all_python_targets()** -- Αντικατάσταση της σκληρά κωδικοποιημένης λίστας 4 στόχων TARGET_ARMS με έναν δυναμικό σαρωτή αρχείων που διατρέχει τους καταλόγους `src/analysis/`, `src/ingestion/`, `src/ai/`, `src/utils/`, `src/core/` και `src/api/`, ανακαλύπτοντας όλα τα μη-`__init__.py` αρχεία Python ως βραχίονες δοκιμής. Κάθε βραχίονας καλείται με `--help` για γρήγορη έξοδο υποδιεργασίας. Ο αυτόνομος ελεγκτής κλιμακώνεται πλέον από 4 σε 70+ βραχίονες που καλύπτουν ολόκληρη τη βάση κώδικα `src/`.
- [x] **Συμφιλίωση Q-Table κατά την εκκίνηση** -- Η `run_autonomous_tester()` συμφιλιώνει τον αποθηκευμένο πίνακα Q (εάν υπάρχει) με τον τρέχοντα αριθμό βραχιόνων, διατηρώντας τις υπάρχουσες τιμές Q για βραχίονες που εξακολουθούν να υπάρχουν και μηδενίζοντας τους νέους βραχίονες.
- [x] **Εξαναγκασμένος Συγχρονισμός Και των 15 Αρχείων Τεκμηρίωσης και 5 Αρχείων Κώδικα σε v5.9.7**

## Φάση 17: Σήμανση IEEE Computer Society WEIGD Fund & Κυκλοφορία v5.9.7 (2026-08-01)

### Κατάσταση: ΟΛΟΚΛΗΡΩΜΕΝΗ (2026-08-01)

- [x] **Υλοποίηση διχρωμικού σήματος Rich IEEE CS στο talos.py** -- Διχρωμικό σήμα κειμένου με επίσημα χρώματα IEEE (#006699 και #002855) που εμφανίζεται στην κεφαλίδα του τερματικού πίνακα ελέγχου Rich.
- [x] **Προσθήκη σήματος Shields.io IEEE CS στα README.md και SYSTEM_CAPABILITIES_MASTER.md** -- Επίσημο σήμα Shields.io που συνδέεται με τον ιστότοπο της IEEE Computer Society με λογότυπο IEEE.
- [x] **Προσθήκη σήματος CSS IEEE στο SYSTEM_CAPABILITIES_MASTER.html** -- Σήμα CSS pill με χρώματα φόντου #006699 και #002855 που δηλώνει την υποστήριξη του έργου.
- [x] **Ενημέρωση CITATION.cff με μεταδεδομένα επιχορήγησης IEEE Computer Society** -- Ενότητα χρηματοδότησης με τύπο επιχορήγησης, τίτλο και μήνυμα αναγνώρισης του WEIGD Student Support Fund (2026).
- [x] **Υποχρεωτικός συγχρονισμός και των 15 αρχείων τεκμηρίωσης και 5 αρχείων κώδικα σε v5.9.7** -- Οι συμβολοσειρές έκδοσης ενημερώθηκαν στα talos.py, run_talos.bat, run_talos.sh, config/settings.py και src/api/main_api.py. Και τα 15 κανονικά αρχεία τεκμηρίωσης συγχρονίστηκαν.

## Φάση 18: Clickable Terminal Hyperlinks & Τοπική-σε-Τοπική Επαναφορά Fast-Tier (v5.9.8)

### Κατάσταση: ΟΛΟΚΛΗΡΩΜΕΝΗ (2026-08-02)

- [x] **Υλοποίηση συνδέσμων Rich [link=file:///...] στα autonomous_tester.py και talos.py** -- Ο βοηθός `_make_clickable_path()` μετατρέπει διαδρομές αρχείων σε συνδέσμους τερματικού Rich με forward slashes για πλοήγηση CTRL+CLICK. Οι διαδρομές αναφορών καταρρίψεων, πινάκων Q και καταλόγων αναφορών είναι πλέον clickable στο τερματικό.
- [x] **Διόρθωση της επαναφοράς fast-tier του AIManager ώστε να δοκιμάζει το τοπικό Ollama (11434) πριν το cloud** -- Όταν το γρήγορο επίπεδο CPU edge (θύρα 11435) αποτυγχάνει με ConnectionError, η `_execute_ollama_http()` επαναπίπτει αυτόματα στο τοπικό GPU Ollama (θύρα 11434) ΠΡΩΤΑ, διατηρώντας τη λειτουργία χωρίς σύνδεση. Μόνο αν και τα δύο τοπικά endpoints αποτύχουν, επιχειρεί επαναφορά στο cloud. Καταγράφει `[WARNING] Fast tier (11435) offline. Falling back to local Ollama (11434)...` και `[RECOVERY]` σε επιτυχή επαναφορά GPU.
- [x] **Υποχρεωτικός συγχρονισμός και των 15 αρχείων τεκμηρίωσης και 5 αρχείων κώδικα σε v5.9.8** -- Οι συμβολοσειρές έκδοσης ενημερώθηκαν στα talos.py, run_talos.bat, run_talos.sh, config/settings.py, tests/test_multi_tier.py και src/api/main_api.py.

---

## Φάση 15: Κατανεμημένο Οικοσύστημα (Μελλοντικό -- v6.0.0+)

- [ ] **v6.0.0 -- Μετεγκατάσταση PostgreSQL + pgvector** -- Αντικατάσταση SQLite με PostgreSQL για ταυτόχρονη πρόσβαση και διανυσματική αναζήτηση ομοιότητας επιπέδου παραγωγής.
- [ ] **v6.1.0 -- Τοπική Διοχέτευση RAG** -- Ενσωμάτωση Ollama + Chroma για συνομιλία με papers, εισαγωγή PDF και κατασκευή γράφου γνώσης.
- [ ] **v6.2.0 -- Διεπαφή Πολλαπλών Πλατφορμών** -- Εφαρμογή Flutter για desktop/κινητά (Windows, Linux, macOS, iOS, Android).
- [ ] **v6.3.0 -- Προηγμένη Οπτικοποίηση** -- Three.js / Deck.gl για 3D ομαδοποίηση, γραφήματα δικτύου αναφορών και χρονολογικές απεικονίσεις.
- [ ] **v6.4.0 -- Εγκατάσταση Μηδενικής Επαφής** -- Αυτόνομη κατασκευή `.exe` μέσω PyInstaller, ενορχήστρωση Docker Swarm, διαγράμματα Kubernetes Helm.

---

> **Project TALOS** -- Από Αθροιστή σε Αυτόνομο Αρχιτέκτονα Έρευνας.
> Δημιουργήθηκε στην Καλαμάτα, Ελλάδα.
> (C) 2026 Christos Smarlamakis. Με επιφύλαξη παντός δικαιώματος.
