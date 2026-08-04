# Ιστορικό Αλλαγών - Έργο TALOS

Όλες οι σημαντικές αλλαγές στο έργο TALOS καταγράφονται σε αυτό το αρχείο. Το έργο τηρεί το [Σημασιολογικό Versioning](https://semver.org/).

## [v5.9.14] - 2026-08-04 -- Συγχρονισμός Τεκμηρίωσης & Έκδοσης

### Άλλαξε
- **Συγχρονισμός συμβολοσειρών έκδοσης σε 4 αρχεία κώδικα και 15 αρχεία τεκμηρίωσης** σε v5.9.14.
- **`config/settings.py`**: `TALOS_VERSION` ενημερώθηκε από "5.9.13" σε "5.9.14". Το docstring της ενότητας ενημερώθηκε.
- **`talos.py`**: Η έκδοση στο docstring της ενότητας ενημερώθηκε από v5.9.13 σε v5.9.14.
- **`src/api/main_api.py`**: Το `version`, `description` και το μήνυμα καταγραφής εκκίνησης του FastAPI ενημερώθηκαν από v5.9.13 σε v5.9.14.
- **`tests/test_multi_tier.py`**: Ο ισχυρισμός `test_talos_version` ενημερώθηκε από "5.9.13" σε "5.9.14". Το docstring της ενότητας ενημερώθηκε.
- **`docs/CHANGELOG_EN.md`**: Προστέθηκε καταχώρηση v5.9.14.
- **`docs/CHANGELOG_GR.md`**: Προστέθηκε καταχώρηση v5.9.14.
- **`docs/SYSTEM_CAPABILITIES_MASTER.md`**: Η έκδοση και η ημερομηνία τελευταίας ενημέρωσης συγχρονίστηκαν σε v5.9.14 (εφαρμόστηκε από τον χρήστη).
- **`docs/SYSTEM_CAPABILITIES_MASTER.html`**: Η έκδοση και η ημερομηνία τελευταίας ενημέρωσης συγχρονίστηκαν σε v5.9.14 (εφαρμόστηκε από τον χρήστη).
- **`run_talos.bat`**: Οι συμβολοσειρές έκδοσης ενημερώθηκαν σε v5.9.14 (εφαρμόστηκε από τον χρήστη).
- **`run_talos.sh`**: Οι συμβολοσειρές έκδοσης ενημερώθηκαν σε v5.9.14 (εφαρμόστηκε από τον χρήστη).

### Επαλήθευση
- Το `python -m py_compile` ολοκληρώθηκε με επιτυχία και στα 4 τροποποιημένα αρχεία `.py`.
- Ο ισχυρισμός `pytest` `test_talos_version` περνάει με επιτυχία.
- Πρωτόκολλο μηδενικών emojis τηρείται σε όλο τον κώδικα και την τεκμηρίωση.

## [v5.9.9] - 2026-08-02 -- Ενοποίηση Διαδρομών Αναφορών & Απομόνωση Καταλόγου Δεδομένων

## [v5.9.12] - 2026-08-02 -- Hotfix Εξαρτήσεων Vendored Graphify

### Προστέθηκε
- **`tree-sitter-python` στο `requirements.txt`**: Γραμματική της γλώσσας Python για το vendored Graphify AST Knowledge Graph engine. Η υποδιεργασία απέτυχε χωρίς αυτήν τη γραμματική κατά την εκτέλεση του "Full Setup".
- **`rapidfuzz` στο `requirements.txt`**: Βιβλιοθήκη ασαφούς αντιστοίχισης συμβολοσειρών που απαιτείται από το Graphify για την επίλυση οντοτήτων κατά την κατασκευή του γράφου γνώσης AST. Επιλύει το `ModuleNotFoundError: No module named 'rapidfuzz'` κατά τη δημιουργία του γράφου.

### Άλλαξε
- **Συγχρονισμός συμβολοσειρών έκδοσης σε 5 αρχεία κώδικα και 15 αρχεία τεκμηρίωσης** σε v5.9.12.
- **`tests/test_multi_tier.py`**: Ο ισχυρισμός `test_talos_version` ενημερώθηκε από "5.9.10" σε "5.9.12".

### Επαλήθευση
- Το `python -m py_compile` ολοκληρώθηκε με επιτυχία σε όλα τα τροποποιημένα αρχεία `.py`.
- Πλήρης σουίτα δοκιμών: 181 επιτυχείς, 0 αποτυχίες (`pytest -v`).
- Πρωτόκολλο μηδενικών emojis τηρείται σε όλο τον κώδικα και την τεκμηρίωση.


### Άλλαξε
- **Ενοποίηση όλων των διαδρομών εξόδου αναφορών στο `data/reports/`** (8 σενάρια ανάλυσης + tester routes): Όλες οι αναφορές που παράγονται κατά την εκτέλεση από τα σενάρια του `src/analysis/` (`architecture_intelligence_report.py`, `generate_baseline_report.py`, `author_profiler.py`, `author_trajectory_analyzer.py`, `citation_analyzer.py`, `trend_analyzer.py`, `knowledge_path_generator.py`, `recommender.py`) εγγράφουν πλέον στους υποκαταλόγους του `data/reports/` αντί του `reports/` επιπέδου ρίζας. Ο αυτόνομος ελεγκτής (`src/ai/testing/autonomous_tester.py`) και το REST API του (`src/api/tester_routes.py`) είχαν ήδη μεταφερθεί στη Φάση 16.
- **Μεταφορά όλων των υπαρχόντων περιεχομένων του root `reports/` στο `data/reports/`**: 124 ιστορικά αρχεία αναφορών (audits, authors, citations, general, general_status_report, grey_literature, knowledge_paths, recommendations, snapshots, trends) μετακινήθηκαν στο `data/reports/` με πλήρη διατήρηση της δομής καταλόγων.
- **Διαγραφή του καταλόγου root `reports/`**: Η ρίζα του έργου είναι πλέον καθαρή. Όλα τα παραγόμενα αποτελέσματα βρίσκονται υπό τον κατάλογο `data/` για σωστό αποκλεισμό μέσω `.gitignore`.
- **Ενημέρωση των δηλώσεων `print` του `generate_baseline_report.py`**: Η έξοδος κονσόλας εμφανίζει πλέον `data/reports/general_status_report/` αντί για `reports/general_status_report/`.
- **Συγχρονισμός συμβολοσειρών έκδοσης σε 5 αρχεία κώδικα και 15 αρχεία τεκμηρίωσης** σε v5.9.9.
- **`tests/test_multi_tier.py`**: Ο ισχυρισμός `test_talos_version` ενημερώθηκε από "5.9.8" σε "5.9.9".

### Επαλήθευση
- To `python -m py_compile` ολοκληρώθηκε με επιτυχία και στα 13 τροποποιημένα αρχεία `.py` (8 ανάλυσης + autonomous_tester + tester_routes + config/settings + main_api + talos.py).
- Πλήρης σουίτα δοκιμών: 181 επιτυχείς, 0 αποτυχίες (`pytest -v`).
- Πρωτόκολλο μηδενικών emojis τηρείται σε όλο τον κώδικα και την τεκμηρίωση.

## [v5.9.7] - 2026-08-01 -- Ενοποίηση Καταλόγου Δεδομένων & Δυναμική Ανακάλυψη Στόχων

### Άλλαξε
- **Μετεγκατάσταση REPORTS_DIR σε data/reports/autonomous_tester/** (`src/ai/testing/autonomous_tester.py`, `src/api/tester_routes.py`): Αλλαγή από `reports/autonomous_tester/` (ρίζα έργου) σε `data/reports/autonomous_tester/`. Όλες οι αναφορές καταρρίψεων που παράγονται κατά την εκτέλεση βρίσκονται πλέον υπό τον κατάλογο `data/`, εξασφαλίζοντας καθαρή ρίζα έργου και σωστό αποκλεισμό μέσω `.gitignore`.
- **Δυναμική ανακάλυψη στόχων (`_discover_all_python_targets()`)** (`src/ai/testing/autonomous_tester.py`): Αντικατάσταση της σκληρά κωδικοποιημένης λίστας 4 στόχων `TARGET_ARMS` με δυναμικό σαρωτή αρχείων που διατρέχει τους καταλόγους `src/analysis/`, `src/ingestion/`, `src/ai/`, `src/utils/`, `src/core/` και `src/api/`, ανακαλύπτοντας όλα τα μη-`__init__.py` αρχεία Python ως βραχίονες δοκιμής. Κάθε βραχίονας καλείται με `--help` για γρήγορη έξοδο υποδιεργασίας. Ο αυτόνομος ελεγκτής κλιμακώνεται από 4 σε 70+ βραχίονες.
- **Συμφιλίωση Q-Table κατά την εκκίνηση** (`run_autonomous_tester()`): Συμφιλιώνει τον αποθηκευμένο πίνακα Q με τον τρέχοντα αριθμό βραχιόνων, διατηρώντας υπάρχουσες τιμές Q και μηδενίζοντας νέους βραχίονες.
- **Δυναμική ανακάλυψη βραχιόνων στα tester routes** (`src/api/tester_routes.py`): Η `_discover_target_arms()` αντικατοπτρίζει την ίδια λογική σάρωσης για το endpoint `/api/v1/tester/status`.
- **Συγχρονισμός συμβολοσειρών έκδοσης σε 5 αρχεία κώδικα και 15 αρχεία τεκμηρίωσης** σε v5.9.7.
- **`tests/test_multi_tier.py`**: Ο ισχυρισμός `test_talos_version` ενημερώθηκε από "5.9.5" σε "5.9.6".
- **Ενημέρωση εκκινητών** (`run_talos.bat`, `run_talos.sh`): Ενημερώθηκαν οι συμβολοσειρές έκδοσης, οι διαδρομές καταλόγων αναφορών και οι περιγραφές του ελεγκτή.

### Επαλήθευση
- Όλα τα τροποποιημένα αρχεία `.py` περνούν το `python -m py_compile`.
- Πλήρης σουίτα δοκιμών: 181 επιτυχείς, 0 αποτυχίες (`pytest -v`).
- Πρωτόκολλο μηδενικών emojis τηρείται σε όλο τον κώδικα και την τεκμηρίωση.

## [v5.9.3] - 2026-08-01 -- Αυτόνομος Ελεγκτής Συστήματος (RL-Driven, LLM-Judged)

### Προστέθηκε
- **Αυτόνομος Ελεγκτής Συστήματος (RL-Driven Chaos Engineering)** (`src/ai/testing/autonomous_tester.py`, 390 γραμμές): Μη Σταθερός Πολυβραχίονας Ληστής (Non-Stationary Multi-Armed Bandit) με Epsilon-Greedy (epsilon=0.2) και σταθερό βήμα Alpha (0.1). Δοκιμάζει υπό πίεση 4 υποσυστήματα TALOS (FastAPI Server, MCP Server, Daily Search, Citation Analyzer) μέσω υποδιεργασιών με χρονικό όριο 5 δευτερολέπτων ανά κύκλο. Αν κάποιος στόχος καταρρεύσει, το stderr αποστέλλεται στο Fast Edge LLM (tier="fast") για διάγνωση δύο προτάσεων. Τα αποτελέσματα οπτικοποιούνται μέσω Rich TUI (Spinners, κόκκινα Panels για καταρρεύσεις, κίτρινα Panels για Διάγνωση AI, πράσινες επιβεβαιώσεις PASS, έγχρωμος Πίνακας Q). Ο Πίνακας Q αποθηκεύεται ως JSON στο `data/tester_q_table.json`. Αναφορές καταρρεύσεων σε Markdown με χρονική σήμανση αποθηκεύονται στο `reports/autonomous_tester/CRASH_REPORT_{timestamp}.md`. Συμβάντα Synapse εκπέμπονται σε κάθε κύκλο δοκιμής. Σήμα ανταμοιβής: +50 για κατάρρευση, -1 για επιτυχία. Αυτόνομη εκτέλεση: `python src/ai/testing/autonomous_tester.py [κύκλοι]`.
- **REST API Αυτόνομου Ελεγκτή** (`src/api/tester_routes.py`, 200 γραμμές): FastAPI APIRouter με πρόθεμα `/api/v1/tester`. `GET /api/v1/tester/status` επιστρέφει τον τρέχοντα Πίνακα Q με ταξινομήσεις ευθραυστότητας (STABLE/LOW/MODERATE/HIGH_FRAGILITY). `GET /api/v1/tester/reports` παραθέτει διαθέσιμες αναφορές καταρρεύσεων Markdown ταξινομημένες κατά χρονική σήμανση. Μοντέλα Pydantic v2: `ArmStatus`, `TesterStatus`, `CrashReportEntry`, `TesterReports`. Σχεδιασμός βασισμένος στο σύστημα αρχείων (read-only), ανθεκτικός σε επανεκκινήσεις.
- **TALOS Terminal CLI -- Επιλογή 6 (Αυτόνομος Ελεγκτής Συστήματος)**: Ενσωματωμένος στο `talos.py` στο μενού 11 επιλογών υπό τη νέα ενότητα "TESTING & CI/CD". Ζητά από τον χρήστη αριθμό κύκλων (προεπιλογή 10). Καλεί απευθείας το `run_autonomous_tester()` μέσω εισαγωγής.
- **Ενσωμάτωση στους Εκκινητές**: `run_talos.bat` επιλογή 8 και `run_talos.sh` επιλογή 8 εκκινούν το `python src/ai/testing/autonomous_tester.py` με αυτόματη ενεργοποίηση περιβάλλοντος.
- **Κανόνας Συγχρονισμού Έκδοσης Κώδικα** (`.clinerules`): Νέος ΚΡΙΣΙΜΟΣ κανόνας που επιβάλλει ακριβή συγχρονισμό της συμβολοσειράς έκδοσης σε 5 αρχεία κώδικα (`talos.py`, `run_talos.bat`, `run_talos.sh`, `config/settings.py`, `src/api/main_api.py`) κατά την αλλαγή έκδοσης.

### Τροποποιήθηκε
- **Αριθμός endpoints FastAPI**: 16 -> 18 (προστέθηκαν `GET /api/v1/tester/status` και `GET /api/v1/tester/reports` μέσω `app.include_router(tester_router)`).
- **`talos.py` αναδιάρθρωση μενού**: 10 -> 11 επιλογές. Νέα ενότητα "TESTING & CI/CD" με Επιλογή 6 (Αυτόνομος Ελεγκτής). Οι επιλογές 7-11 μετατοπίστηκαν: Baseline Standard (7), Baseline Academic (8), DRL Status (9), Docs Generator (10), Έξοδος (11).
- **`run_talos.bat` και `run_talos.sh`**: 9 -> 10 επιλογές. Αυτόνομος Ελεγκτής ως Επιλογή 8. Test Suite μετατοπίστηκε στην Επιλογή 9, Έξοδος στην 10.
- **Συγχρονισμός συμβολοσειρών έκδοσης** σε 5 αρχεία κώδικα και 15 αρχεία τεκμηρίωσης σε v5.9.3.
- **Επιβολή περιγραφικών ονομάτων**: Αναφορές σε "PYTHIA" αντικαταστάθηκαν με "Query Translator".
- **`test_multi_tier.py`**: Βεβαίωση `test_talos_version` ενημερώθηκε από "5.8.9" σε "5.9.1".

### Επαλήθευση
- Και τα 7 τροποποιημένα αρχεία `.py` περνούν `python -m py_compile`.
- Πρωτόκολλο μηδενικών emojis σε όλο τον νέο κώδικα.

---

## [v5.8.9] - 2026-08-01 -- Πλήρης Ανάπτυξη Οικοσυστήματος, Multi-Tier LLM, και Κυριαρχία TUI

### Προστέθηκε
- **Πίνακας Ελέγχου Rich Terminal UI**: Πλήρης ανακατασκευή TUI στο `talos.py` με τη βιβλιοθήκη `rich` (`Console`, `Panel`, `Table`, `Box`, `Text`). Δυναμικός πίνακας κατάστασης με: περιβάλλον Conda, θύρα API (8001), δίαυλος Synapse (8000), λειτουργία εκτέλεσης, ενεργά επίπεδα LLM, ενεργή ερευνητική εστίαση (από config.json).
- **Εμφάνιση Ενεργής Ερευνητικής Εστίασης**: `_build_status_table()` διαβάζει το `user_research_goal` από config.json, το περικόπτει στους 65 χαρακτήρες, το εμφανίζει με λαμπερό πράσινο.
- **Διαδραστική Προβολή & Περιστροφή Ερευνητικής Εστίασης**: Η επιλογή 4 αναδιαρθρώθηκε σε διαδραστική ροή εργασίας με Panel προεπισκόπησης στόχου, προεπισκόπηση Boolean ερωτημάτων, και υπομενού 3 ενεργειών.
- **Model Manager CLI**: `talos.py` επιλογή 1 καλεί το `src.ai.llm.model_manager.main()` απευθείας μέσω εισαγωγής.
- **Εγγενής MCP Server** (`src/mcp_server.py`, 269 γραμμές): MCP Server με stdio transport και 4 εργαλεία: `talos_system_status`, `talos_semantic_search`, `talos_get_paper_details`, `talos_trigger_scrape`.
- **Σουίτα Unit Tests MCP Server** (`tests/test_mcp_server.py`, 334 γραμμές, 27 tests).
- **Πρωτόκολλο SYNAPSE** (`src/integration/synapse_client.py`, 310 γραμμές): Κλάση `EventEmitter` με thread-safe, μη-αποκλειστική αποστολή συμβάντων JSON. 6 τύποι συμβάντων. Module-level singleton `synapse_emitter`.
- **Δέκτης Webhook SYNAPSE** (`src/api/synapse_routes.py`, 200 γραμμές): FastAPI APIRouter για `POST /api/v1/synapse/webhook`.
- **Σύστημα Τεκμηρίωσης Timeline**: `docs/TIMELINE_EN.md` και `docs/TIMELINE_GR.md` -- καταγεγραμμένο ιστορικό ορόσημων TALOS.
- **Αρχιτεκτονική Multi-Tier LLM Routing**: `config/settings.py` (113 γραμμές). Επίπεδα: fast (Neutrino-8B), heavy (qwen2.5:14b), cloud. Τρεις λειτουργίες: local (air-gapped), hybrid, cloud. `src/core/ai_manager.py` v3.9 με παράμετρο `tier`.
- **Εκκινητής POSIX** (`run_talos.sh`, 525 γραμμές): Πλήρης ισοτιμία με run_talos.bat. Αυτόματος εντοπισμός περιβάλλοντος.
- **Αυτοματοποιημένος Batch Runner** (`run_talos.bat` v5.8.9): 9 επιλογών μενού. Αυτόματος εντοπισμός Conda. Αυτόματη εκκίνηση Fermion.
- **Επεκταμένη Σουίτα Δοκιμών**: 96 unit tests (από 29). `test_synapse.py` (21), `test_multi_tier.py` (20), `test_provisioner.py` (23), `test_mcp_server.py` (27).
- **Απομονωμένο Ενδιάμεσο UI** (`src/utils/frontend_provisioner.py`): Λήψη Cherry Studio με αυτόματη παραγωγή MCP config.
- **Βιβλιοθήκη `rich`** προστέθηκε στο `requirements.txt`.

### Τροποποιήθηκε
- **Σύνταγμα v2.0** (`.clinerules`): Πρότυπο 8 Σημείων: ΠΡΩΤΟΚΟΛΛΟ ΜΗΔΕΝΙΚΩΝ EMOJIS, 100% AIR-GAPPED & LOCAL-FIRST, HARDWARE-AWARE VRAM, ΑΥΣΤΗΡΗ ΓΡΑΜΜΙΚΗ ΕΚΤΕΛΕΣΗ, VERIFICATION-FIRST, 15-ΑΡΧΕΙΩΝ ΣΥΓΧΡΟΝΙΣΜΟΣ, ΠΡΩΤΟΚΟΛΛΟ SYNAPSE, ΠΡΟΤΥΠΑ ΤΕΚΜΗΡΙΩΣΗΣ ΚΩΔΙΚΑ.
- **Κανόνας Συγχρονισμού 15 Αρχείων**: Το κανονικό σύνολο επεκτάθηκε από 12 σε 15 αρχεία.
- **Ανακατανομή Θύρας**: Port 8000 -> 8001. O δίαυλος SYNAPSE καταλαμβάνει τη θύρα 8000.
- **Εκσυγχρονισμός Docker**: `python:3.10-slim` -> `python:3.11-slim`. Exposed port 8001. Προστέθηκε `HEALTHCHECK`.
- **Ενημέρωση Templates**: `example.env`, `config.template.json`, `requirements.txt` με πλήρες σετ κλειδιών.
- **Ενημέρωση Χαρτών Έργου**: `PROJECT_MAP.md` και `PROJECT_MAP_EN.md` με Πρωτόκολλο Synapse, MCP Server, Multi-Tier LLM. Πλήθος αρχείων 67 -> 69.
- **Συγχρονισμός εκδόσεων** σε όλα τα σημεία εισόδου και 15 αρχεία τεκμηρίωσης.

### Διορθώθηκε
- **Εμφάνιση Ονομάτων Μοντέλων TUI**: Πλήρεις ακατέργαστες συμβολοσειρές αντί περικοπής `split(":")`.
- **Αναντιστοιχία Στηλών SQLite**: 23 τιμές για 22 στήλες -- διορθώθηκε.
- **Fast Tier Connection Refused Fallback**: Σωστή επιστροφή None κατά το σφάλμα σύνδεσης.
- **Σφάλμα Διαστάσεων Μοντέλου**: `drl_agent.py load()` προελέγχει διαστάσεις πριν το `load_state_dict()`.
- **Ασυνέπεια Κανονικοποίησης Ώρας**: `/23.0` -> `/24.0`.
- **8 Ονόματα Κλάσεων Πηγών Σπασμένα**: Αυτόματος εντοπισμός μέσω σάρωσης module.
- **Τοπική Επαλήθευση Μοντέλου Hardcoded**: Τώρα διαβάζει `LOCAL_MODEL_NAME` από `.env`.
- **Αναντιστοιχία Διαδρομής Αποθήκευσης**: Ενοποίηση σε `dddqn_trained.pth`.

### Αφαιρέθηκε
- **Streamlit Πλήρως Απαρχαιωμένο**: `app.py`, `.streamlit/`, `tools/_gui_runner.py`. Το Streamlit αφαιρέθηκε από το requirements.txt.
- **Εκκαθάριση Φακέλου Tools**: `tools/start_talos.bat`, `tools/_bump.py`, `tools/_git_status.ps1`.
- **Παρωχημένα Αρχεία**: `talos.bat`, `venv/`, scripts επιδιόρθωσης δεδομένων, `dump.json`.

---

## [v5.6.0] - 2026-07-29 -- Απαρχαίωση Streamlit, Έγγραφα Δυνατοτήτων, Κανόνας Συγχρονισμού 12 Αρχείων

### BREAKING -- Πλήρης Απαρχαίωση του Streamlit
- Διαγράφηκαν: app.py (1,175 γραμμές), .streamlit/, tools/_gui_runner.py.
- Το Streamlit αφαιρέθηκε από το requirements.txt. Μοναδικό frontend: React 18 + Tailwind CSS + Shadcn UI.

### Προστέθηκε
- docs/SYSTEM_CAPABILITIES_MASTER.md + .html: Αναφορά δυνατοτήτων 9 ενοτήτων.
- GET /api/v1/capabilities endpoint (15 endpoints συνολικά).
- docs/API_HANDOVER_FOTIS.md, docs/UX_UI_BLUEPRINT_FOTIS.md, docs/IP_PROTECTION_STRATEGY.md.

### Τροποποιήθηκε
- src/api/main_api.py v1.3: version 5.5.2 -> 5.6.0, 14 -> 15 endpoints.
- .clinerules v5.6.0: 3 νέοι ΚΡΙΣΙΜΟΙ κανόνες.
- README.md, ROADMAP.md: ενημέρωση εκδόσεων.

---

## [v5.5.2] - 2026-07-22 -- 100% Κάλυψη API Οικοσυστήματος (4 Νέα Endpoints)

### Προστέθηκε
- **`src/api/main_api.py` v1.2 -- Τέσσερα νέα endpoints για πλήρη κάλυψη οικοσυστήματος:**
  - `POST /api/v1/papers/{paper_id}/evaluate`
  - `POST /api/v1/ai/translate-query`
  - `GET /api/v1/analysis/authors`
  - `POST /api/v1/db/recalculate-scores`
- 4 νέα μοντέλα Pydantic. Σύνολο endpoints: **14** (100% κάλυψη TALOS).

## [v5.5.1] - 2026-07-22 -- Endpoints Frontend DX (Ιστορικό GWO + Γράφος Αρχιτεκτονικής)

### Προστέθηκε
- `GET /api/v1/optimize/gwo/history` -- Ιστορικό GWO για Recharts.
- `GET /api/v1/graph/view` -- Γράφος αρχιτεκτονικής HTML. Σύνολο endpoints: **10**.

## [v5.5.0] - 2026-07-22 -- FastAPI REST API Facade & Διόρθωση Διαδρομής Βάσης

### Προστέθηκε
- **`src/api/main_api.py` v1.0 (ΝΕΟ, ~470 γραμμές)** με 8 endpoints REST και 10 μοντέλα Pydantic.

### Τροποποιήθηκε
- **`src/core/database_manager.py` v5.4.2 -- Διόρθωση διαδρομής βάσης (ΚΡΙΣΙΜΟ):** Σωστή επίλυση ρίζας έργου.

## [v5.4.1] - 2026-07-22 -- Εκκαθάριση Ριζικού Καταλόγου

### Τροποποιήθηκε
- Δημιουργία καταλόγων `docs/` και `tools/`. Μετακίνηση αρχείων τεκμηρίωσης.
- `.gitignore` v5.4.1: προστέθηκαν μοτίβα άρνησης `!docs/PROJECT_MAP*.md`.

## [v5.4.0] - 2026-07-22 -- Διάταξη Πακέτου src/ (Μετανάστευση DDD)

### BREAKING -- Πλήρης αναδιοργάνωση δομής καταλόγων
Όλα τα αρχεία (~55) μετακινήθηκαν σε `src/` με Domain-Driven Design. Όλες οι δηλώσεις εισαγωγής ξαναγράφτηκαν.

### Τροποποιήθηκε
- **talos.py v5.4.1**: `run_script()` με `_SCRIPT_MAP`. `from core.*` -> `from src.core.*`.
- **app.py v5.4.1**: `run()` με `_SCRIPT_DIRS`. Όλες οι εισαγωγές ενημερώθηκαν.
- **10 `__init__.py` αρχεία** δημιουργήθηκαν (ένα ανά πακέτο).
- **Παλαιοί κατάλογοι διαγράφηκαν**: `core/`, `scripts/`, `sources/`.

## [v5.3.7] - 2026-07-07 -- Επαναβελτιστοποίηση Υπερπαραμέτρων GWO v2.0

### Τροποποιήθηκε
- **core/drl_agent.py v2.3**: LR=3.361e-05, GAMMA=0.6983.
- **scripts/drl_trainer.py v1.4**: EPS_DECAY=0.9202.

## [v5.3.6 hotfix] - 2026-07-06 -- Διόρθωση Κατάρρευσης Grey Literature Miner (Batch 3)

### Διορθώθηκε
- **core/ai_manager.py v3.8 -- `analyze_generic_text()` υλοποιήθηκε.**
- **scripts/grey_literature_miner.py v2.1**: Προσαρμοστική εισαγωγή DuckDuckGo.

## [v5.3.6] - 2026-07-06 -- Ενημέρωση "TUI/CLI Hardening" (Batch 2)

### Διορθώθηκε
- **talos.py v5.3.6**: Διπλή επιλογή "6." διορθώθηκε. Προστέθηκε `safe_pause()`. Το `safe_select()` χειρίζεται KeyboardInterrupt.
- **scripts/drl_trainer.py v1.3**: Μερική αποθήκευση μοντέλου κατά το Ctrl+C.
- **scripts/talos_live_agent.py v3.2**: argparse αντί ad-hoc σάρωσης sys.argv.

## [v5.3.5] - 2026-07-06 -- Ενημέρωση "DRL/GWO Scientific Integrity" (Batch 1)

### Διορθώθηκε (5 ΚΡΙΣΙΜΑ σφάλματα)
- **scripts/gwo_rl_optimizer.py v2.0**: `calculate_fitness()` ξαναγράφτηκε με φάσεις εκπαίδευσης + αξιολόγησης.
- **core/talos_env.py v3.1**: `step()` επιστρέφει terminated=False, truncated=True στο όριο 200 βημάτων.
- **scripts/drl_trainer.py v1.2**: NameError στα `args.episodes` διορθώθηκε.
- **core/live_agent_orchestrator.py v1.1**: LOW_SCORE_MAX 20 -> 10.
- **core/ai_manager.py v3.7**: `last_provider_used` παρακολουθεί τον πραγματικό πάροχο.

## [v5.3.4] - 2026-07-05 -- Ενημέρωση "Περιγραφικά Ονόματα"

### Τροποποιήθηκε
- Αντικατάσταση μυθολογικών ονομάτων με περιγραφικούς τίτλους σε όλη την τεκμηρίωση.

## [v5.3.3] - 2026-07-05 -- Ενημέρωση "Φωτεινό Θέμα & Καθολική Τεκμηρίωση"

### Τροποποιήθηκε
- app.py v5.3.3: Αφαίρεση σκοτεινού θέματος.
- .clinerules v5.3.3: Καθολικός κανόνας τεκμηρίωσης για όλους τους τύπους αρχείων.

## [v5.3.2] - 2026-07-05 -- Ενημέρωση "Αρθρωτή Αρχιτεκτονική Δικτύου"

### Προστέθηκε
- **core/drl_networks.py v1.0 (ΝΕΟ)**: DuelingLSTM σε αποκλειστικό module.

## [v5.3.1] - 2026-07-05 -- Ενημέρωση "DRL Live Agent & Provider-Aware Orchestration"

### Προστέθηκε
- **core/live_agent_sources.py v1.0 (ΝΕΟ)**, **core/live_agent_orchestrator.py v1.0 (ΝΕΟ)**.
- Μηχανισμός Cooldown v3.1, 21-διάστατο διάνυσμα κατάστασης.

## [v5.3.0] - 2026-07-04 -- Ενημέρωση "Πολυγλωσσική Τεκμηρίωση"

### Προστέθηκε
- **scripts/generate_docs.py v2.0 (ΕΠΑΝΑΓΡΑΦΗ, ~350 γραμμές)**: 18 γλώσσες, 93+ αρχεία.

## [v5.2.1] - 2026-07-04 -- Ενημέρωση "Ακαδημαϊκό GUI & DRL Ναυαρχίδα"

### Προστέθηκε
- templates/gui_theme.css, templates/gui_strings.py. Dual-Mode GUI.

## [v5.2.0] - 2026-07-04 -- Ενημέρωση "Onboarding & Dynamic Orchestration"

### Προστέθηκε
- app.py v5.2.0: Οδηγός εισαγωγής. core/talos_env.py v2.0: Δυναμικό N-Source περιβάλλον.
- core/drl_agent.py v2.0: Δυναμικός πράκτορας. scripts/research_pivot.py v1.0 (ΝΕΟ).

## [v5.1.0] - 2026-07-04 -- DRL Dashboard & Αναδιοργάνωση TUI/GUI

### Προστέθηκε
- app.py -- Σελίδα DRL Agent Dashboard. talos.py -- Κατάσταση DRL Agent (Επιλογή 7).

## [v5.0.1] - 2026-07-04 -- Εξαγωγή JSON GWO

### Προστέθηκε
- scripts/gwo_rl_optimizer.py: Αποθήκευση υπερπαραμέτρων σε models/gwo_best_params.json.

## [v5.0.0] - 2026-07-03 -- Ενημέρωση "Hybrid Embeddings & Deep RL"

### Προστέθηκε (6 Φάσεις, 14 νέα αρχεία, 22 τροποποιημένα)
- **Φάση 0**: Multi-Provider Hybrid Embeddings v2.
- **Φάση 1**: DRL Environment & Agent v1.0.
- **Φάση 2**: Meta-Optimization & Offline Training.
- **Φάση 4**: Αυτόνομη Υπηρεσία & Ειδοποιήσεις.
- **Baseline Report System** (generate_baseline_report.py v1.1).
- **Επιτάχυνση GPU**: RTX 4070 CUDA 12.1, 10x ταχύτερη εκπαίδευση.

## [v4.11.0] - 2026-07-02 -- Ενημέρωση "Χάρτης Έργου & Διαγνωστικά"

### Προστέθηκε
- PROJECT_MAP.md, .clinerules v5.0.0, architecture_graph.html, verify_dependency_map.py.

## [v4.10.1] - 2026-06-30 -- Ενημέρωση "Διαχείριση Μοντέλων"

### Προστέθηκε
- scripts/model_manager.py (ΝΕΟ, 608 γραμμές), core/hardware.py: εκτίμηση μεγέθους κβαντισμού.

## [v4.10.0] - 2026-06-30 -- Ενημέρωση "Zero-Config & Resilience"

### Προστέθηκε
- Κλιμακωτή Διαχείριση Κλειδιών API, Έλεγχος Υγείας API, Έξυπνος Επιλογέας Μοντέλων.

## [v4.9.0] - 2026-06-29 -- Ενημέρωση "Streamlit GUI & Ποιότητα"

### Προστέθηκε
- app.py: Πλήρης εφαρμογή Streamlit 6 σελίδων. test_smoke.py: 78 αυτοματοποιημένοι έλεγχοι.

## [v4.8.5] - 2026-06-29 -- Ενημέρωση "Κυνήγι Σφαλμάτων & Ποιότητα"

### Διορθώθηκε
- 15+ σφάλματα σε όλα τα modules συμπεριλαμβανομένων elsevier_source, grey_literature_miner, recalculate_scores, metadata_enricher.

## [v4.8.4] - 2026-06-28 -- Ενημέρωση "Multi-Provider & Αναζήτηση Ιστού"

### Προστέθηκε
- Πάροχος Hugging Face, Live Web Search (DuckDuckGo), core/hardware.py.

## [v4.8.3] - 2026-06-27 -- Ενημέρωση "Ασφαλής Τοπική AI & Ιδιωτικότητα"

### Προστέθηκε
- Προεπαλήθευση μοντέλων, συναίνεση cloud fallback, αμφίδρομο fallback.

## [v4.8.2] - 2026-06-27 -- Ενημέρωση "Τοπική AI & Ανθεκτικότητα"

### Προστέθηκε
- Υποστήριξη τοπικής AI μέσω Ollama. Διορθώθηκαν 16 κρίσιμα σφάλματα.

## [v4.8.1] - 2026-05-08 -- Ενημέρωση "Dockerization & Φορητότητα"

### Προστέθηκε
- Dockerfile, docker-compose.yml, start_talos.bat.

## [v4.8.0] - 2026-03-20 -- Ενημέρωση "Εμπλουτισμός & Scientometrics"

### Προστέθηκε
- Σουίτα Scientometrics (trend_analyzer.py), Data Enricher, 9 νέες στήλες βάσης.

## [v4.7.1] - 2025-11-30 -- Ενημέρωση Απόδοσης

### Τροποποιήθηκε
- pdf_retriever.py με ThreadPoolExecutor (10-15x ταχύτερο).

## [v4.7.0] - 2025-11-30 -- PDF Retriever (Ηθική Έκδοση)

### Προστέθηκε
- pdf_retriever.py με ενσωμάτωση Unpaywall API.

## [v4.6.0] - 2025-11-30 -- Grey Literature "Horizon Scanning"

### Προστέθηκε
- oracle_agent.py με Gemini 2.0 και Google Search Grounding.

## [v4.4.0] & [v4.5.0] - 2025-11-30 -- Ενημέρωση "Ανοικτή Πρόσβαση & Onboarding"

### Προστέθηκε
- Πράκτορας PLOS, Οδηγός Εισαγωγής στο talos.py.

## [v4.3.1] - 2025-11-30 -- Διόρθωση Μαζικής Εκτέλεσης

### Διορθώθηκε
- sqlite3.ProgrammingError σε μαζικές ενημερώσεις embeddings.

## [v4.3.0] - 2025-11-28 -- Ενημέρωση "Soft Shutdown"

### Προστέθηκε
- Κουμπί Soft Shutdown στο Dashboard και endpoint /api/shutdown.

## [v4.2.0] - 2025-11-28 -- Εξευγενισμός Pythia & Ενίσχυση Αρχιτεκτονικής

### Τροποποιήθηκε
- AIManager v3.4: system_prompt_override. AIManager v3.3: Χειρουργικός καθαρισμός JSON.

## [v4.1.0] - 2025-11-28 -- Αρχιτεκτονική Τεσσάρων Επιπέδων & Σύστημα Προφίλ

### Προστέθηκε
- Πλαίσιο αξιολόγησης 4 επιπέδων. Σύστημα Διαχείρισης Προφίλ.

## [v4.0.0] - 2025-11-28 -- Αυτοματοποιημένη Διαμόρφωση ("Μεταφραστής Ερωτημάτων")

### Προστέθηκε
- scripts/query_translator.py: Φυσική γλώσσα -> Boolean ερωτήματα αναζήτησης μέσω AI.

## [v3.2.0] - 2025-09-27 -- Επιχείρηση "Genesis"

### Τροποποιήθηκε
- Όλοι οι πράκτορες πηγών ξαναγράφτηκαν με τυποποιημένη μορφή εξόδου.

## [v3.0.0] - 2025-09-26 -- Στρατηγικός Μέντορας (Knowledge Path Generator)

### Προστέθηκε
- scripts/knowledge_path_generator.py: Διάλογος φυσικής γλώσσας, σημασιολογική αναζήτηση, K-Means clustering.

## [v2.21.0] - 2025-09-26 -- Ενημέρωση Αξιοπιστίας

### Τροποποιήθηκε
- AIManager επανασχεδιάστηκε ως Model-Independent με εγγενή λειτουργία JSON και Circuit Breakers.

## [v2.20.0] - 2025-09-22 -- Διαδραστικός Γράφος Γνώσης

### Προστέθηκε
- Citation Analyzer: DOI -> διαδραστικός γράφος δικτύου HTML μέσω pyvis.

## [v2.19.0] - 2025-09-21 -- Γέφυρα Zotero & "Έξυπνος Συγχρονισμός"

### Προστέθηκε
- Zotero Connector με pyzotero για συγχρονισμό Web API.

## [v2.18.0] - 2025-09-21 -- Ανθεκτικότητα AI & Επέκταση Πρακτόρων

### Προστέθηκε
- Κεντρικοποιημένος AIManager με αυτόματο fallback (Circuit Breaker) από Gemini σε DeepSeek.

## [v2.15.0] - 2025-09-19 -- Διαδραστικός Πίνακας Ελέγχου

### Προστέθηκε
- scripts/interactive_dashboard.py: Flask + Tabulator.js web dashboard.

## [v1.0.0] - 2025-08-27 -- Η Γένεση

### Προστέθηκε
- Αρχική δημιουργία: ερωτήματα arXiv, αξιολόγηση μέσω Gemini AI, ειδοποιήσεις Discord μέσω Webhook.
