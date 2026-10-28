# Ιστορικό Αλλαγών - Έργο TALOS

Όλες οι σημαντικές αλλαγές στο έργο TALOS καταγράφονται σε αυτό το αρχείο. Το έργο τηρεί το [Σημασιολογικό Versioning](https://semver.org/).

## [v5.10.8] - 2026-08-22 -- Ανακαίνιση Επιχειρησιακού TUI & Ακαδημαϊκή Αισθητική

### Προστέθηκε
- **Ενοποιημένο Θέμα Ερωτήσεων** (`src/utils/ui_theme.py`): Νέα κανονική ενότητα `TALOS_QUESTIONARY_STYLE` που ορίζει την επιχειρησιακή παλέτα TUI "Cyan/Teal & Bright White". Οι διαχωριστές κατηγοριών αποδίδονται σε έντονο λευκό (`bold fg:#ffffff`), το ερωτηματικό σε μπλε IEEE (`bold fg:#4a9eff`) και όλοι οι τόνοι επιλογής, δείκτη και απάντησης σε κυανό/τιρκουάζ (`bold fg:#00ced1`) με `noinherit` για την καταστολή της αντιστροφής φόντου, εξασφαλίζοντας στιγμιότυπα έτοιμα για δημοσίευση IEEE.

### Άλλαξε
- **Θεματοποιήθηκε κάθε διαδραστική ερώτηση** -- τα `talos.py`, `src/ai/llm/model_manager.py`, `src/ai/llm/research_pivot.py`, `src/ai/llm/query_translator.py`, `src/analysis/citation_analyzer.py`, `src/analysis/author_profiler.py`, `src/analysis/knowledge_path_generator.py`, `src/core/profile_manager.py`, `src/core/ai_manager.py`, `src/ai/drl/drl_trainer.py`, `src/ai/drl/talos_service.py`, `src/ingestion/grey_literature_miner.py`, `src/ingestion/metadata_enricher.py`, `src/ingestion/pdf_downloader.py`, `src/utils/generate_docs.py`, `src/utils/migrate_database_schema.py`, `src/utils/recalculate_scores.py` και `src/utils/reevaluate_database.py` εισάγουν πλέον και διαβιβάζουν το `TALOS_QUESTIONARY_STYLE` σε κάθε ερώτηση `questionary.select`, `questionary.checkbox` και `questionary.text`.
- **Περίγραμμα πίνακα κεφαλίδας** -- ο κορυφαίος πίνακας Rich στο `talos.py` χρησιμοποιεί πλέον `border_style="#006699"` (μπλε IEEE) για κομψό ακαδημαϊκό πλαίσιο.
- **Η διοχέτευση DSPy PRISMA αναβλήθηκε** για την v5.10.9 υπέρ της Ανακαίνισης Επιχειρησιακού TUI.
- **Συγχρονισμός συμβολοσειρών έκδοσης** σε 5 αρχεία κώδικα και 15 κανονικά αρχεία τεκμηρίωσης σε v5.10.8.

## [v5.10.7] - 2026-08-21 -- Ενσωμάτωση Γέφυρας OPTICA

### Προστέθηκε
- **Πελάτης REST OPTICA** (`src/integration/optica_client.py`): Νέα κλάση `OpticaClient` που επιτρέπει στο TALOS να λειτουργεί ως πελάτης API προς την αδελφή μικροϋπηρεσία Project OPTICA (θύρα 8002), εκφορτώνοντας τη βαριά απόδοση γραφικών cnsplots/PyVis. Η `request_plot(plot_type, journal_template)` επιλύει δυναμικά τη διαδρομή της ενεργής βάσης δεδομένων μέσω της `get_active_profile_db_path()`, κατασκευάζει φορτίο `{data_source, plot_type, journal_template, override_params}`, αποστέλλει POST στο `{OPTICA_API_BASE}/plot/generate` και επιστρέφει ευπρεπή λεξικά σφάλματος σε περίπτωση αδυναμίας σύνδεσης αντί να καταρρεύσει.
- **Διαμόρφωση** (`config/settings.py`): Νέα ρύθμιση περιβάλλοντος `OPTICA_API_BASE` με προεπιλογή `http://127.0.0.1:8002/api/v1`, καθρεπτισμένη στα `config.template.json` και `example.env`.
- **Είσοδος TUI** (`talos.py`): Νέα επιλογή μενού "Data Visualizations (via OPTICA)" στην ομάδα Ανάλυση & Ευρήματα, που ζητά τύπο γραφήματος (`opex_dashboard` / `semantic_topology`) και πρότυπο περιοδικού (`nature` / `science` / `cell`), και αποδίδει το αποτέλεσμα σε πίνακα Rich.

### Άλλαξε
- **Η διοχέτευση DSPy PRISMA αναβλήθηκε** για την v5.10.8 υπέρ της ενσωμάτωσης Γέφυρας OPTICA.
- Συγχρονισμός συμβολοσειρών έκδοσης σε 5 αρχεία κώδικα και 15 κανονικά αρχεία τεκμηρίωσης σε v5.10.7.

## [v5.10.6] - 2026-08-17 -- Αυτόματη Εκκίνηση Δαίμονα Λειτουργικού Συστήματος & Ενορχηστρωτής

### Προστέθηκε
- **Γεννήτρια Αυτόματης Εκκίνησης Δαίμονα** (`src/utils/daemon_autostart.py`): η `install_windows_autostart()` δημιουργεί ένα σενάριο εκκίνησης (`talos_daemon_boot.bat`) και καταχωρεί μια συντόμευση στον φάκελο Εκκίνησης των Windows (pywin32 Shell COM) με εικονίδιο συστήματος (`shell32.dll, 43`) και ελαχιστοποιημένο στυλ παραθύρου.
- **Διαδραστικός Έλεγχος Πριν την Πτήση Δαίμονα** (`talos.py`): νέα επιλογή μενού "Configure Daemon & OS Autostart" για τη στρατηγική δικτύου, τις πηγές-στόχους και την προαιρετική εγκατάσταση αυτόματης εκκίνησης.
- **Έγχυση Πηγών Δαίμονα** (`src/ai/drl/talos_service.py`): η `_run_live_search()` διαβάζει το `daemon_target_sources` από το `config.json` και το προωθεί στο `talos_live_agent.py` μέσω `--sources`.

### Άλλαξε
- Συγχρονισμός συμβολοσειρών έκδοσης σε 5 αρχεία κώδικα και 15 κανονικά αρχεία τεκμηρίωσης σε v5.10.6.

### Διορθώθηκε
- **Σφάλμα διαδρομής αυτόματης εκκίνησης** (`src/utils/daemon_autostart.py`): το παραγόμενο `talos_daemon_boot.bat` καλούσε προηγουμένως `conda activate talosenv` και απλές εντολές `python`/`fermion`, γεγονός που μπορούσε να υποχωρήσει σιωπηρά στο Python του συστήματος (χάνοντας πηγές και προκαλώντας αναντιστοιχία τανυστή 22 έναντι 23). Το σενάριο χρησιμοποιεί πλέον την απόλυτη διαδρομή `sys.executable` (σε εισαγωγικά) για τον δαίμονα και τον CPU server, καταργώντας την εξάρτηση από το conda.

## [v5.10.5] - 2026-08-15 -- Καθολικός Δυναμικός Πάροχος Μοντέλων & Μηχανή Αυτοθεραπευόμενου Πλεονασμού

### Προστέθηκε
- **Καθολικός Δυναμικός Πάροχος Μοντέλων** (`src/utils/model_provisioner.py`): Νέα κλάση `ModelProvisioner` με ντετερμινιστική `detect_protocol()` (προθέματα παρόχων cloud, Ollama με άνω-κάτω τελεία, HuggingFace Hub με κάθετο), κλιμάκωση τοπικής επίλυσης διαδρομής 3 επιπέδων (`resolve_local_model_path()`: `FAST_EDGE_MODEL_PATH`, στη συνέχεια ενσωματωμένο `models/<sanitized_name>`, στη συνέχεια δίκτυο) και `ensure_model_available()` που εκτελεί JIT αυτόματη λήψη για Ollama (`ollama pull`) και HuggingFace Hub (`huggingface_hub.snapshot_download`) με εφεδρεία αυτοθεραπείας που καταγράφει `[WARNING] Auto-provisioning failed ... Reverting to baseline model.` και επιστρέφει `False` χωρίς κατάρρευση.
- **Αυτόνομο CLI** (`python src/utils/model_provisioner.py [--model <name>] [--check-only]`): παρέχει τα προεπιλεγμένα μοντέλα fast edge και heavy ή ελέγχει τη διαθεσιμότητα χωρίς μεταλλάξεις.
- **Ενσωμάτωση ρουτίνας SETUP** (`run_talos.bat` / `run_talos.sh`): το βήμα [5/5] εκτελεί πλέον τον Καθολικό Πάροχο Μοντέλων για αυτόματη παροχή των προεπιλεγμένων μοντέλων fast edge και heavy.
- **Ενσωμάτωση Διαχειριστή Μοντέλων** (`src/ai/llm/model_manager.py`): νέος βοηθός `_provision_model()` δρομολογεί τις επιλογές μη εγκατεστημένων μοντέλων Ollama και HuggingFace μέσω του παρόχου με ανατροφοδότηση κατάστασης Rich.
- **Απομονωμένες δοκιμές** (`tests/test_model_provisioner.py`): 22 δοκιμές για ανίχνευση πρωτοκόλλου, προτεραιότητα επίλυσης διαδρομής, εικονική λήψη HuggingFace, εικονική λήψη Ollama και συμπεριφορά εφεδρείας αυτοθεραπείας.

### Άλλαξε
- **Συγχρονισμός συμβολοσειρών έκδοσης σε 6 αρχεία κώδικα και 15 αρχεία τεκμηρίωσης** σε v5.10.5.

### Επαλήθευση
- Το `python -m compileall src config tests talos.py` ολοκληρώθηκε με μηδέν σφάλματα.
- Η πλήρης σουίτα `python -m pytest -v` περνά (272 δοκιμές).
- Το `python tests/test_smoke.py` περνά με επιτυχία.
- Το `python src/utils/verify_dependency_map.py --ci` αναφέρει 0 παλαιωμένες και 0 ελλείπουσες εξαρτήσεις.

## [v5.10.4] - 2026-08-15 -- Δυναμική Μηχανή Ανακάλυψης Μοντέλων & Διαλειτουργικότητα Πρωτοκόλλου SYNAPSE

### Προστέθηκε
- **Δυναμική Μηχανή Ανακάλυψης Μοντέλων** (`src/ai/llm/model_discovery.py`): Νέα κλάση `ModelDiscoveryEngine` που ανακαλύπτει ενεργά μοντέλα LLM στο τοπικό επίπεδο Ollama (GET /api/tags) και στους προαιρετικούς παρόχους cloud (NVIDIA NIM, Groq, OpenRouter, Gemini GET /v1/models), με πλήρως απομονωμένη εφεδρεία σε τοπικό μητρώο JSON στο `data/model_benchmarks.json` (ακατέργαστες βαθμολογίες SWE-bench / MMLU-Pro, παράθυρα πλαισίου, επίπεδα τιμολόγησης· δημιουργείται αυτόματα αν απουσιάζει).
- **Δυναμική σχετική βαθμολόγηση ποιότητας** -- η `get_normalized_quality_scores()` υπολογίζει `Q_p = raw_score(p) / max_k(raw_score(k))` επί του συνόλου ενεργών μοντέλων· η `get_provider_quality_scores()` συναθροίζει σε επίπεδο παρόχου για τον δρομολογητή.
- **Δυναμική ενσωμάτωση ποιότητας στον Δρομολογητή LLM** (`src/ai/drl/llm_router_subagent.py`): Νέες μέθοδοι `refresh_quality_scores()` / `load_quality_scores()` επιτρέπουν στον `LLMRouterSubAgent` να υπερκαλύπτει τα στατικά σήματα `PROVIDER_PROFILES` με τιμές Q_p της μηχανής ανακάλυψης· η `select_provider()` εκπέμπει πλέον μη-μπλοκαριστό συμβάν `router_decision` Synapse.
- **Endpoint κατάστασης SYNAPSE** (`src/api/synapse_routes.py`): Νέο `GET /api/v1/synapse/status` που επιστρέφει προσβασιμότητα διαύλου, υγεία ουράς (μετρητές εκπομπής), υποστηριζόμενους τύπους συμβάντων και κατάσταση συνδρομητών.
- **Νέοι τύποι συμβάντων SYNAPSE** (`src/integration/synapse_client.py`): Οι `model_discovered` και `router_decision` προστέθηκαν στο `EventEmitter.VALID_EVENT_TYPES`, με στατιστικά εκπομπής ασφαλή ως προς νήματα (`get_emission_stats()`).
- **Εκπομπή συμβάντων αγωγών** (`daily_search.py`, `ai_manager.py`): Μη-μπλοκαριστή εκπομπή `router_decision` στη δρομολόγηση παρόχου· το `red_tester.py` εκπέμπει ήδη `agent_episode_end` ανά κύκλο.
- **Απομονωμένες δοκιμές** (`tests/test_model_discovery.py`): 15 δοκιμές για ανάλυση Ollama/cloud, εφεδρεία εκτός δικτύου, δυναμική βαθμολόγηση ποιότητας, συνάθροιση παρόχων και το endpoint κατάστασης.

### Άλλαξε
- **Συγχρονισμός συμβολοσειρών έκδοσης σε 6 αρχεία κώδικα και 15+ αρχεία τεκμηρίωσης** σε v5.10.4.
- **Αριθμός endpoints 18 σε 19** με την προσθήκη του `GET /api/v1/synapse/status`.

### Επαλήθευση
- Το `python -m compileall src config tests talos.py` ολοκληρώθηκε με μηδέν σφάλματα.
- Η πλήρης σουίτα `python -m pytest -v` περνά (253+ δοκιμές).
- Το `python tests/test_smoke.py` περνά με επιτυχία.
- Το `python src/utils/verify_dependency_map.py --ci` αναφέρει 0 παλαιωμένες και 0 ελλείπουσες εξαρτήσεις.

## [v5.10.3] - 2026-08-14 -- Ιεραρχική Ενορχήστρωση DRL (Ενσωμάτωση Δαίμονα & Υποπράκτορα Αναζήτησης)

### Προστέθηκε
- **Ιεραρχική Ενορχήστρωση DRL**: Ο `LLMRouterSubAgent` καλείται πλέον απευθείας από τον ζωντανό ενορχηστρωτή αναζήτησης DRL, τον αυτόνομο ερευνητικό δαίμονα 24/7 και τους αγωγούς ημερήσιας/ιστορικής αναζήτησης για βέλτιστη επιλογή παρόχου πριν από κάθε αξιολόγηση εργασίας.
- **Τροποποιητής εργασίας `foraging_evaluation`** (`src/ai/drl/llm_router_subagent.py`): Νέος τύπος εργασίας δρομολόγησης καταχωρημένος στο `TASK_MODIFIERS` με `prompt_scale=1.0` και `quality_bias=0.02`, ώστε οι αξιολογήσεις αναζήτησης να δρομολογούνται με ειδικό προφίλ σήματος.
- **`estimate_prompt_tokens()`** (`src/ai/drl/llm_router_subagent.py`): Κοινός εκτιμητής μήκους προτρέποντος με τον ευρετικό κανόνα των τεσσάρων χαρακτήρων ανά token, που καταναλώνεται από τον ενορχηστρωτή, τον δαίμονα και τους αγωγούς αναζήτησης.

### Άλλαξε
- **`src/ai/drl/live_agent_orchestrator.py` (v1.3)**: Η `evaluate_paper()` συμβουλεύεται πλέον την `ai_manager.router.select_provider(prompt_length, task_type="foraging_evaluation")` πριν την ενεργοποίηση της αξιολόγησης και καταγράφει την επιλογή δρομολόγησης μέσω εξόδου κονσόλας (`[ROUTER]`) και καταγραφέα (logger) ενότητας.
- **`src/ai/drl/talos_service.py` (v2.1)**: Ο δαίμονας 24/7 δρομολογεί πλέον κάθε παρασκηνιακή αξιολόγηση εργασίας μέσω της `route_daemon_evaluation()`, η οποία επερωτά τον `LLMRouterSubAgent` και καταγράφει τις αποφάσεις στο `data/logs/talos_system.log` με την ετικέτα `[DAEMON/ROUTER]`.
- **`src/ingestion/daily_search.py` / `src/ingestion/historic_search.py`**: Προστέθηκε η `route_evaluation_provider()`· η διαδικασία αξιολόγησης δύο σταδίων (προκαταρκτική διαλογή Fast Edge μέσω `fast_screening`, βαθιά ανάλυση Heavy Reasoning μέσω `deep_research`) επερωτά πλέον τον δρομολογητή για επιλογή παρόχου.
- **Συγχρονισμός συμβολοσειρών έκδοσης σε 6 αρχεία κώδικα και 15 αρχεία τεκμηρίωσης** σε v5.10.3.

### Επαλήθευση
- Το `python -m compileall src config tests talos.py` ολοκληρώθηκε με μηδέν σφάλματα.
- Η πλήρης σουίτα `python -m pytest -v` περνά (245+ δοκιμές, συμπεριλαμβανομένων των νέων δοκιμών ενσωμάτωσης του δρομολογητή).
- Το `python tests/test_smoke.py` περνά με επιτυχία.
- Το `python src/utils/verify_dependency_map.py --ci` αναφέρει 0 παλαιωμένες και 0 ελλείπουσες εξαρτήσεις.


## [v5.10.2] - 2026-08-14 -- Υποπράκτορας Δρομολογητή LLM, Διεπίπεδη Διαμόρφωση Ανταμοιβής GWO & Διαδραστικό TUI Πλαισίων Επιλογής 16 Πηγών

### Προστέθηκε
- **Υποπράκτορας Δρομολογητή LLM (`src/ai/drl/llm_router_subagent.py`)**: Νέα κλάση `LLMRouterSubAgent` που επιλέγει τον βέλτιστο ενεργό πάροχο για ένα αίτημα συμπερασμού. Φορτώνει βάρη ανταμοιβής από το `models/gwo_llm_router_reward_weights.json` (με εφεδρεία στα προεπιλεγμένα βάρη Pareto), αξιολογεί το μήκος των tokens του προτρέποντος, την κατάσταση rate-limit του παρόχου και την καθυστέρηση έναντι ενός στατικού πίνακα προφίλ παρόχων, και επιστρέφει τον πάροχο που μεγιστοποιεί το `R = w_quality * QualityScore - w_latency * LatencyRatio - w_cost * CostRatio - w_penalty * RateLimitPenalty`. Ενσωματώθηκε στον `AIManager` ώστε η επιλογή παρόχου cloud/legacy να ανατίθεται στον υποπράκτορα.
- **Διαμορφωτής Ανταμοιβής Δρομολογητή LLM με GWO (`src/ai/optimizers/gwo_llm_router_reward_shaper.py`)**: Νέα κλάση `GWOLLMRouterRewardShaper` που υλοποιεί Διεπίπεδη Βελτιστοποίηση Ανταμοιβής Πολλαπλών Στόχων με κανονικό GWO (Mirjalili 2014). Ο εξωτερικός βρόχος εκτελεί αγέλη λύκων (άλφα/βήτα/δέλτα) στον συνεχή υπερκύβο 4 διαστάσεων, προβάλλοντας κάθε υποψήφιο στο simplex (`sum(w) == 1.0`, `w_i >= 0.0`). Ο εσωτερικός βρόχος αξιολογεί τον Δρομολογητή LLM υπό τη συνάρτηση διαμόρφωσης ανταμοιβής `R = w_quality * QualityScore - w_latency * LatencyRatio - w_cost * CostRatio - w_penalty * RateLimitPenalty`. Εξάγει βελτιστοποιημένα βάρη, τροχιά σύγκλισης και τρία προφίλ Pareto (Βαθιά Έρευνα, Γρήγορη Διαλογή, Τοπικό Απομονωμένο) στο `models/gwo_llm_router_reward_weights.json`. Αυτόνομο CLI: `python src/ai/optimizers/gwo_llm_router_reward_shaper.py [--wolves 10] [--iterations 30]`.
- **Διαδραστικό TUI Πλαισίων Επιλογής 16 Πηγών (`talos.py`)**: Οι επιλογές 3α (Ημερήσια Αναζήτηση) και 3β (Ιστορική Αναζήτηση) εμφανίζουν πλέον `questionary.checkbox()` με όλες τις 16 καταγεγραμμένες ακαδημαϊκές πηγές (`arxiv`, `ieee`, `semantic_scholar`, `springer`, `openalex`, `dblp`, `elsevier`, `core`, `crossref`, `openarchives`, `pubmed`, `scigov`, `osti`, `plos`, `openreview`, `openaire`), όλες προεπιλεγμένες. Οι επιλεγμένες πηγές μεταβιβάζονται στα σενάρια αναζήτησης μέσω `--sources`.
- **Φιλτράρισμα πηγών (`daily_search.py` / `historic_search.py`)**: Προστέθηκαν κανονικό `SOURCE_REGISTRY` + `ALL_SOURCE_NAMES` και βοηθός `build_sources(config, selected)`. Και τα δύο σενάρια δέχονται `--sources arxiv ieee ...` (χωρισμένες με κενό) για εκτέλεση μόνο των καθορισμένων πηγών.
- **Απομονωμένες δοκιμές (`tests/test_gwo_llm_router_reward_shaper.py`)**: Έξι δοκιμές με χρήση mock που καλύπτουν την προβολή simplex, την ντετερμινιστική σπορά και την εξαγωγή JSON.

### Άλλαξε
- **Μετονομασία `src/ai/optimizers/gwo_rl_optimizer.py` σε `src/ai/optimizers/gwo_foraging_hyperparameter_tuner.py`**: Προστέθηκε η κλάση `GWOForagingHyperparameterTuner` με διατήρηση των `run_gwo()` και `DEFAULT_RL_EPISODES` για την παρασκηνιακή εργασία GWO του FastAPI. Η εξαγωγή καλύτερων παραμέτρων μετονομάστηκε από `models/gwo_best_params.json` σε `models/gwo_foraging_hyperparameters.json`.
- **`src/api/main_api.py`**: Η εισαγωγή GWO ενημερώθηκε σε `gwo_foraging_hyperparameter_tuner`· το `_run_scrape_background` μεταβιβάζει πλέον το `source_filter` στο `daily_search.main(source_filter)`· οι παραχημένες αναφορές «14 πηγών» διορθώθηκαν σε «16».
- **Συγχρονισμός συμβολοσειρών έκδοσης σε 6 αρχεία κώδικα και 15 αρχεία τεκμηρίωσης** σε v5.10.2.

### Επαλήθευση
- Το `python -m compileall src config tests talos.py` ολοκληρώθηκε με μηδέν σφάλματα.
- Η πλήρης σουίτα δοκιμών (συμπεριλαμβανομένων των νέων δοκιμών του Διαμορφωτή Ανταμοιβής GWO) και η δοκιμή smoke περνούν με επιτυχία.
- Πρωτόκολλο μηδενικών emojis τηρείται αυστηρά· διατηρείται καθαρό ελληνικό unicode σε όλα τα αρχεία `_GR.md`.


## [v5.10.1] - 2026-08-14 -- Κλιμάκωση Περιβάλλοντος DRL & Επανεκπαίδευση (Χώρος Δράσης 17)

### Προστέθηκε
- **Κλιμάκωση περιβάλλοντος DRL (`src/ai/drl/talos_env.py` v3.2)**: Ο χώρος καταστάσεων του Gymnasium `TalosEnv` κλιμακώθηκε σε 23 διαστάσεις -- 1 κανονικοποιημένη ώρα (/24.0) + 16 λόγοι χρήσης πηγών + 2 σερί (low_score/10, error/10) + 4 λόγοι παρόχων (gemini, deepseek, huggingface, local). Ο χώρος δράσεων κλιμακώθηκε σε 17 δράσεις -- οι δράσεις 0..15 αντιστοιχούν στις 16 πηγές, η δράση 16 είναι ο ύπνος.
- **Κανονική ανακάλυψη 16 πηγών**: Η `_load_source_list()` εγγυάται πλέον ότι οι `openreview` και `openaire` είναι παρούσες (προσαρτώνται αν λείπουν) και υποβαθμίζεται στην πλήρη λίστα 16 πηγών `ALL_KNOWN_SOURCES` όταν δεν υπάρχει διαμόρφωση.
- **Δοκιμές επαλήθευσης περιβάλλοντος DRL (`tests/test_multi_tier.py`)**: Νέα κλάση `TestDRLEnvironment` που βεβαιώνει ότι το `TalosEnv` παράγει σχήμα παρατήρησης `(23,)` και χώρο δράσεων `Discrete(17)`, καθώς και `get_default_state_space() == 23` και `get_default_action_space() == 17`.

### Άλλαξε
- **`src/ai/drl/drl_agent.py` (v2.1)**: Η εφεδρική τιμή διαστάσεων κατά την εισαγωγή ενημερώθηκε από (6, 4) σε (23, 17)· τεκμηριώθηκε η αυτόματη ανακατασκευή του `load()` για τις νέες διαστάσεις.
- **`src/ai/drl/drl_trainer.py` (v1.4)**: Τεκμηριώθηκαν οι υπερπαράμετροι βελτιστοποιημένες με GWO (LR=3.361e-05, GAMMA=0.6983, EPS_DECAY=0.9202).
- **`src/ai/drl/live_agent_sources.py` (v1.1)** και **`src/ai/drl/live_agent_orchestrator.py` (v1.2)**: Ευθυγράμμιση χαρτογράφησης πηγών και τεκμηρίωσης σε 16 πηγές και διάνυσμα καταστάσεων 23 διαστάσεων.
- **Συγχρονισμός συμβολοσειρών έκδοσης σε 6 αρχεία κώδικα και 15 αρχεία τεκμηρίωσης** σε v5.10.1.

### Επαλήθευση
- Το `python -m compileall src config tests talos.py` ολοκληρώθηκε με μηδέν σφάλματα.
- Η πλήρης σουίτα δοκιμών (συμπεριλαμβανομένων των νέων δοκιμών κλιμάκωσης περιβάλλοντος DRL) και η δοκιμή smoke περνούν με επιτυχία.
- Πρωτόκολλο μηδενικών emojis τηρείται αυστηρά· διατηρείται καθαρό ελληνικό unicode σε όλα τα αρχεία `_GR.md`.


## [v5.10.0] - 2026-08-14 -- Επέκταση Ακαδημαϊκής Κατάποσης (Ενσωμάτωση OpenReview & OpenAIRE)

### Προστέθηκε
- **Πηγή OpenReview (`src/ingestion/openreview.py`)**: Νέος πράκτορας `OpenReviewSource` που ερωτά το OpenReview API V2 (https://api2.openreview.net) για σημειώσεις φόρουμ. Χρησιμοποιεί πιστοποιημένο `openreview.api.OpenReviewClient` όταν υπάρχουν `OPENREVIEW_USERNAME`/`OPENREVIEW_PASSWORD` και υποβαθμίζεται ομαλά σε πρόσβαση επισκέπτη/δημόσιων σημειώσεων διαφορετικά. Αντιστοιχίζει τις σημειώσεις στο πρότυπο σχήμα `{doi, url, title, authors_str, publication_year, abstract, source="OpenReview"}` και προσαρτά αποφάσεις αξιολόγησης, βαθμολογίες, συστάσεις και μεταδεδομένα συνεδρίου στο πεδίο περίληψης.
- **Πηγή OpenAIRE (`src/ingestion/openaire.py`)**: Νέος πράκτορας `OpenAIRESource` που ερωτά το OpenAIRE Research Graph API v11.3.0 (`/search/researchProducts`). Υποστηρίζει την προαιρετική κεφαλίδα `Authorization: Bearer` όταν υπάρχει `OPENAIRE_TOKEN` ή `OPENAIRE_API_KEY` και υποβαθμίζεται σε δημόσια αιτήματα χωρίς πιστοποίηση. Αντιστοιχίζει τα αποτελέσματα στο πρότυπο σχήμα (`source="OpenAIRE"`) και προσαρτά μεταδεδομένα επιχορηγήσεων/χρηματοδότησης έργων στο πεδίο περίληψης.
- **Κατάποση 16 πηγών**: Τα `daily_search.py` και `historic_search.py` εισάγουν και εκτελούν πλέον και τις δύο νέες πηγές. Το ημερήσιο δίκτυο αποκτά επίσης την `CORESource` (προηγουμένως εισαγόταν αλλά δεν εκτελούνταν ποτέ), αποκαθιστώντας την τεκμηριωμένη βάση των 14 πηγών και φέρνοντας και τα δύο δίκτυα σε 16 ενεργές πηγές.
- **Μοναδιαίες δοκιμές για τις νέες πηγές**: `tests/test_openreview_source.py` (13 δοκιμές) και `tests/test_openaire_source.py` (21 δοκιμές) -- απομονωμένη κάλυψη εκκίνησης, εξαγωγής πεδίων, τυποποιημένης μορφοποίησης, εμπλουτισμού αξιολόγησης/χρηματοδότησης και ομαλής υποβάθμισης, με προσομοίωση (mock).

### Άλλαξε
- **`requirements.txt`**: Προστέθηκε το `openreview-py` στην ενότητα Academic APIs· η κεφαλίδα ενημερώθηκε σε v5.10.0.
- **`example.env`**: Προστέθηκαν `OPENREVIEW_USERNAME=`, `OPENREVIEW_PASSWORD=`, `OPENAIRE_TOKEN=`· η κεφαλίδα ενημερώθηκε σε v5.10.0.
- **`config.template.json` / `config.json`**: Προστέθηκαν `openreview_query`, `openaire_query` και καταχωρήσεις `max_results_config` (`openreview`, `openaire`).
- **`verify_dependency_map.py`**: Καταχώριση των δύο νέων ενοτήτων πηγών στον `IMPORT_TO_DOC_MAP`.
- **Καθολική ενημέρωση κεφαλίδων**: κάθε docstring ενότητας `Project: TALOS v5.9.18` συγχρονίστηκε σε `v5.10.0` σε 72 αρχεία στα `src/`, `config/` και `tests/` -- συμπεριλαμβανομένου του υποσυστήματος Αυτόνομου Κόκκινου Ελεγκτή (`red_tester.py`, `red_tester_routes.py`, `src/ai/testing/__init__.py`) και συμβολοσειρών έκδοσης που εμφανίζονται στον χρήστη (υποσέλιδο αναφοράς και τίτλος TUI του Red Tester, γεννήτρια βασικής αναφοράς, προσαρμογέας graphify).

### Επαλήθευση
- Το `python -m compileall src config tests talos.py` ολοκληρώθηκε με μηδέν σφάλματα.
- Η πλήρης σουίτα δοκιμών (225 δοκιμές, συμπεριλαμβανομένων 34 νέων δοκιμών πηγών) και η δοκιμή smoke περνούν με επιτυχία.
- Πρωτόκολλο μηδενικών emojis τηρείται αυστηρά· διατηρείται καθαρό ελληνικό unicode σε όλα τα αρχεία `_GR.md`.


## [v5.9.18] - 2026-08-14 -- Καθολικό Πλέγμα Νέφους & Επέκταση Πολυπαρόχου Εφεδρείας

### Προστέθηκε
- **Καθολικό Πλέγμα Νέφους (`config/settings.py` + `src/core/ai_manager.py`)**: Επέκταση της βαθμίδας νέφους από τρεις παρόχους (Gemini, DeepSeek, Hugging Face) σε πλέγμα εννέα παρόχων. Νέοι συμβατοί με OpenAI πάροχοι: NVIDIA NIM (`https://integrate.api.nvidia.com/v1`, `nvidia/nemotron-3-ultra`), Groq (`https://api.groq.com/openai/v1`, `llama-3.3-70b-versatile`), Cerebras (`https://api.cerebras.ai/v1`, `llama-3.1-70b`), GitHub Models (`https://models.inference.ai.azure.com`, `gpt-4o-mini`), Mistral (`https://api.mistral.ai/v1`, `mistral-small-latest`) και OpenRouter (`https://openrouter.ai/api/v1`, `meta-llama/llama-3.3-70b-instruct:free`). Προστέθηκε η κανονική λίστα διάταξης `TALOS_CLOUD_PROVIDERS`.
- **Μητρώο παρόχων συμβατών με OpenAI (`OPENAI_COMPATIBLE_REGISTRY`)**: Εκκίνηση καθοδηγούμενη από λεξικό στον `AIManager` που αντιστοιχίζει το όνομα παρόχου σε κλειδί περιβάλλοντος, βασική διεύθυνση URL, προεπιλεγμένο μοντέλο και κλειδί παράκαμψης μοντέλου. Οι πάροχοι χωρίς διαμορφωμένο κλειδί παραλείπονται ομαλά (Σύνταγμα ΙΙ -- το νέφος είναι ΠΡΟΑΙΡΕΤΙΚΟ).
- **Ενοποιημένος χειριστής αιτημάτων (`_execute_openai_compatible_request`)**: Ενιαία διαδρομή εκτέλεσης συμβατή με OpenAI με ανεξάρτητους διακόπτες κυκλώματος ανά πάροχο (5 συνεχόμενες αποτυχίες = ενεργοποίηση διακόπτη) και καταμέτρηση αποτυχιών μέσω `_handle_failure()`.
- **TUI Ρυθμίσεων Νέφους του Διαχειριστή Μοντέλων**: Ανακατασκευή της `select_cloud_models()` για απόδοση πίνακα Rich και των εννέα παρόχων με στήλες Όνομα Παρόχου, Κλειδί Περιβάλλοντος, Κατάσταση (`[ACTIVE]` πράσινο / `[UNCONFIGURED]` κίτρινο), Προεπιλεγμένο Μοντέλο και Βασική Διεύθυνση URL. Οποιοσδήποτε πάροχος μπορεί να επιλεγεί για προβολή λεπτομερειών, αποθήκευση κλειδιού API στο `.env` ή τροποποίηση του προεπιλεγμένου μοντέλου. Προστέθηκαν `CLOUD_PROVIDER_CATALOG` και βοηθός `get_cloud_provider_rows()`.

### Άλλαξε
- **`example.env`**: Προστέθηκαν πρότυπα καταχωρήσεων `NVIDIA_API_KEY`, `GROQ_API_KEY`, `CEREBRAS_API_KEY`, `GITHUB_TOKEN`, `MISTRAL_API_KEY`, `OPENROUTER_API_KEY` και παρακάμψεις προεπιλεγμένου μοντέλου· η κεφαλίδα ενημερώθηκε σε v5.9.18.
- **`config.template.json` / `config.json`**: Η προεπιλεγμένη λίστα `ai_provider_priority` είναι πλέον `["local", "nvidia", "groq", "cerebras", "github", "gemini", "deepseek", "mistral", "openrouter", "huggingface"]`· το `failure_threshold` αυξήθηκε σε 5.
- **`src/core/ai_manager.py`**: Οι `_execute_cloud_chain()` και `_execute_legacy_request()` δρομολογούν πλέον όλους τους μη-Gemini παρόχους μέσω του ενοποιημένου χειριστή. Οι `_execute_openai_compatible` και `_execute_deepseek_request` διατηρούνται ως καταργημένα περιτυλίγματα.
- **Συγχρονισμός συμβολοσειρών έκδοσης σε 6 αρχεία κώδικα και 15 αρχεία τεκμηρίωσης** σε v5.9.18 (και καθολική ενημέρωση κεφαλίδων σε `src/`, `config/` και `tests/`).

### Επαλήθευση
- Το `python -m compileall src config tests talos.py` ολοκληρώθηκε με μηδέν σφάλματα.
- Η πλήρης σουίτα δοκιμών (συμπεριλαμβανομένων των νέων δοκιμών μητρώου/καταλόγου Πλέγματος Νέφους) και η δοκιμή smoke περνούν με επιτυχία.
- Πρωτόκολλο μηδενικών emojis τηρείται αυστηρά· διατηρείται καθαρό ελληνικό unicode σε όλα τα αρχεία `_GR.md`.


## [v5.9.17] - 2026-08-14 -- Καθολικό Rich TUI, Αναβάθμιση Επιχειρησιακής Καταγραφής & Καθολική Ενημέρωση Κεφαλίδων

### Προστέθηκε
- **Επιχειρησιακή Καταγραφή (`src/utils/logger.py`)**: Ένα ενιαίο εργοστάσιο `get_logger(name)` που συνδέει έναν `rich.logging.RichHandler` (χωρίς emoji, έγχρωμη έξοδος κονσόλας) και έναν `logging.handlers.RotatingFileHandler` που εγγράφει στο `data/logs/talos_system.log` (10 MB ανά αρχείο, 5 κυλιόμενα αντίγραφα) με τον ακαδημαϊκό μορφοποιητή `%(asctime)s - %(name)s - %(levelname)s - %(message)s`. Ο κατάλογος `data/logs/` δημιουργείται αυτόματα.

### Άλλαξε
- **Καθολικό Rich TUI & Επιβολή Καταγραφής**: Έλεγχος όλων των διαδραστικών μονάδων (`talos.py`, `src/ai/llm/model_manager.py`, `src/ai/llm/research_pivot.py`, `src/utils/generate_docs.py`, `src/ai/testing/red_tester.py`). Αντικατάσταση των γυμνών `print()` κατάστασης/διάγνωσης με `logger.info/warning/error`, επιβολή `rich.console.Console` και `rich.panel.Panel` για μενού, πίνακες και πλαίσια, διατήρηση του `questionary` για όλα τα προτρέποντα δεδομένων και αφαίρεση του παλαιού γυμνού `input()` (πλέον `console.input`). Αφαίρεση όλων των emoji από το `research_pivot.py` και μετάφραση των ενσωματωμένων ελληνικών συμβολοσειρών στο `generate_docs.py` στα αγγλικά.
- **`src/api/main_api.py`**: Μετεγκατάσταση του ενσωματωμένου `logging.basicConfig` στον επιχειρησιακό `get_logger("api")`; ενημέρωση `version="5.9.17"` και των συμβολοσειρών εκκίνησης/περιγραφής.
- **Καθολική Ενημέρωση Κεφαλίδων**: Ενημέρωση κάθε docstring ενότητας `Project: TALOS v5.9.15`/`v5.9.16` σε `Project: TALOS v5.9.17` σε όλα τα `src/`, `config/` και `tests/` (78 αρχεία).
- **Ενημέρωση Docker & Εκκινητών**: Συγχρονισμός κεφαλίδων `Dockerfile` και `docker-compose.yml` και της ετικέτας εικόνας `talos:5.9.17`; ενημέρωση κεφαλίδας `requirements.txt` και ετικετών `docs/DOCKER.md`; συγχρονισμός banner και τίτλων `run_talos.bat` και `run_talos.sh`.
- **Συγχρονισμός συμβολοσειρών έκδοσης σε 5 αρχεία κώδικα και 15 αρχεία τεκμηρίωσης** σε v5.9.17.
- **`tests/test_multi_tier.py`**: Ο ισχυρισμός `test_talos_version` ενημερώθηκε σε "5.9.17".

### Επαλήθευση
- Το `python -m compileall src config tests talos.py` ολοκληρώθηκε με μηδέν σφάλματα.
- Η πλήρης σουίτα δοκιμών και η δοκιμή smoke περνούν με επιτυχία.
- Πρωτόκολλο μηδενικών emojis τηρείται αυστηρά· διατηρείται καθαρό ελληνικό unicode σε όλα τα αρχεία `_GR.md`.


## [v5.9.16] - 2026-08-14 -- Αναβάθμιση Αυτόνομου Κόκκινου Ελεγκτή (Μετονομασία, Βαθύ API Fuzzing & Περικοπή Περιεχομένου)

### Προστέθηκε
- **Βαθύ API Fuzzing**: Ο Κόκκινος Ελεγκτής ανακαλύπτει πλέον υβριδικούς βραχίονες δοκιμής -- στόχους CLI καθώς και τέσσερις βραχίονες API fuzzing κατά του τοπικού FastAPI (`POST /api/v1/synapse/webhook` με ακατάλληλο JSON, `GET /api/v1/papers/-999`, `POST /api/v1/search/semantic` με κενό σώμα, `POST /api/v1/scrape/trigger` με άκυρες πηγές). Οι ευγενείς απορρίψεις (400/404/422) θεωρούνται επιτυχία· τα HTTP 5xx και τα timeouts θεωρούνται καταρρεύσεις (ανταμοιβή +50).
- **Περικοπή Περιεχομένου LLM**: Η έξοδος σφαλμάτων που αποστέλλεται στο Fast Edge LLM περικόπτεται στους τελευταίους 2.000 χαρακτήρες μέσω του `_protect_context_window()`, αποτρέποντας την υπερχείλιση παραθύρου περιεχομένου (OOM) σε τεράστιες στοίβες κλήσεων.

### Άλλαξε
- **Μετονομασία `autonomous_tester.py` σε `red_tester.py`** και `tester_routes.py` σε `red_tester_routes.py`. Το σημείο εισόδου `run_autonomous_tester()` είναι πλέον `run_red_tester()`. Το πρόθεμα `/api/v1/tester` διατηρείται για συμβατότητα με το frontend.
- **Μετονομασία διαδρομών μονιμότητας**: Q-table `data/red_tester_q_table.json`, αναφορές `data/reports/red_tester/` (μετεγκατάσταση υπαρχόντων αρχείων).
- **Συγχρονισμός συμβολοσειρών έκδοσης σε 5 αρχεία κώδικα και 15 αρχεία τεκμηρίωσης** σε v5.9.16.
- **`tests/test_multi_tier.py`**: Ο ισχυρισμός `test_talos_version` ενημερώθηκε σε "5.9.16".

### Επαλήθευση
- Επιτυχής έλεγχος `python -m compileall` σε όλα τα αρχεία Python.
- Πλήρης σουίτα δοκιμών (180+ δοκιμές) και smoke test περνούν επιτυχώς.
- Πρωτόκολλο μηδενικών emojis τηρείται αυστηρά σε όλο τον κώδικα και την τεκμηρίωση.

## [v5.9.15] - 2026-08-14 -- Ενίσχυση DRL & Δαιμόνων, Αυτόματη Λήψη Μοντέλων, Σιωπηλή Εκκίνηση & Συμφιλίωση Χάρτη Εξαρτήσεων

### Προστέθηκε
- **`docs/TECH_RADAR_GR.md`**: Πλήρης ελληνική απόδοση του Τεχνολογικού Ραντάρ σύμφωνα με το πρωτόκολλο καθαρής ελληνικής γραφής.
- **Αυτόματη Λήψη Τοπικών Μοντέλων AI στους Εκκινητές**: Προστέθηκε το βήμα [5/5] στα σενάρια εγκατάστασης `run_talos.bat` και `run_talos.sh` για αυτόματη εκτέλεση των `fermion pull fermionresearch/Neutrino-8B` και `ollama pull qwen2.5:14b`.
- **Σιωπηλή Γρήγορη Εκκίνηση**: Αφαιρέθηκε ο παλαιός έλεγχος μοντέλων κατά την εκκίνηση (`_verify_local_models` στο `talos.py`). Το CLI εκκινεί πλέον σιωπηλά και άμεσα στο Rich dashboard, ενώ η επιθεώρηση και εγκατάσταση μοντέλων γίνεται μόνο on-demand (Επιλογή 1).

### Άλλαξε
- **Συμφιλίωση Γράφου Εξαρτήσεων Ενότητας 7** (`docs/PROJECT_MAP.md`, `docs/PROJECT_MAP_EN.md`): Πλήρης αναδόμηση του γράφου εξαρτήσεων με τη νέα ιεραρχία πακέτων `src.*` (Domain-Driven Design), εξαλείφοντας τις προειδοποιήσεις απόκλισης.
- **Συμφιλίωση `verify_dependency_map.py`**: Μετεγκατάσταση των `IMPORT_TO_DOC_MAP` και `COVERED_BY_PARENT` σε ονόματα `src.*` και προσθήκη ταξινόμησης εσωτερικών πακέτων ώστε το `--ci` να αναφέρει μηδενική απόκλιση.
- **Ενίσχυση Υποσυστημάτων DRL & Δαιμόνων**: Πλήρης έλεγχος και επιβεβαίωση σταθερότητας και στα 10 modules Ενισχυτικής Μάθησης και παρασκηνιακών υπηρεσιών.
- **Συγχρονισμός συμβολοσειρών έκδοσης σε 5 αρχεία κώδικα και 15 αρχεία τεκμηρίωσης** σε v5.9.15.
- **`tests/test_multi_tier.py`**: Ο ισχυρισμός `test_talos_version` ενημερώθηκε σε "5.9.15".

### Επαλήθευση
- Επιτυχής έλεγχος `python -m compileall` σε όλα τα αρχεία Python.
- Πλήρης σουίτα δοκιμών: 180 επιτυχείς, 0 αποτυχίες (`pytest -v`).
- `test_smoke.py`: 445 επιτυχείς έλεγχοι.
- Πρωτόκολλο μηδενικών emojis τηρείται αυστηρά σε όλο τον κώδικα και την τεκμηρίωση.

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
- **Διόρθωση υποδομής Docker & οδηγός χρήσης**: Διορθώθηκαν οι ξεπερασμένες κεφαλίδες v5.8.2 σε `Dockerfile`, `docker-compose.yml`, `.dockerignore` και `example.env` σε v5.9.14. Προστέθηκε bootstrap `config.json` από το `config.template.json`, volume `_profiles/`, αφαιρέθηκε το deprecated κλειδί `version:` και οι τοπικές διευθύνσεις μοντέλων ορίστηκαν σε `host.docker.internal`. Προστέθηκε αναλυτικός οδηγός `docs/DOCKER.md` και διορθώθηκαν οι οδηγίες Docker στο README.

### Επαλήθευση
- Το `python -m py_compile` ολοκληρώθηκε με επιτυχία και στα 4 τροποποιημένα αρχεία `.py`.
- Ο ισχυρισμός `pytest` `test_talos_version` περνάει με επιτυχία.
- Πρωτόκολλο μηδενικών emojis τηρείται σε όλο τον κώδικα και την τεκμηρίωση.

---

## [v5.9.13] - 2026-08-03 -- Συγχρονισμός Έκδοσης

### Άλλαξε
- Συγχρονισμός συμβολοσειρών έκδοσης σε 5 αρχεία κώδικα και 15 αρχεία τεκμηρίωσης σε v5.9.13.

---

---

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

---

## [v5.9.11] - 2026-08-02 -- Hotfix Εξαρτήσεων Vendored Graphify

### Προστέθηκε
- **`tree-sitter-python` στο `requirements.txt`**: Γραμματική της γλώσσας Python για το vendored Graphify AST Knowledge Graph engine. Η υποδιεργασία απέτυχε χωρίς αυτήν τη γραμματική κατά την εκτέλεση του "Full Setup".
- **`rapidfuzz` στο `requirements.txt`**: Βιβλιοθήκη ασαφούς αντιστοίχισης συμβολοσειρών που απαιτείται από το Graphify για την επίλυση οντοτήτων κατά την κατασκευή του γράφου γνώσης AST. Επιλύει το `ModuleNotFoundError: No module named 'rapidfuzz'` κατά τη δημιουργία του γράφου.

### Άλλαξε
- **Συγχρονισμός συμβολοσειρών έκδοσης σε 5 αρχεία κώδικα και 15 αρχεία τεκμηρίωσης** σε v5.9.11.
- **`tests/test_multi_tier.py`**: Ο ισχυρισμός `test_talos_version` ενημερώθηκε από "5.9.10" σε "5.9.11".

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

---

---

## [v5.9.10] - 2026-08-02 -- Vendored Graphify AST Integration & Rich Menu Reorganization

(Changes documented in Phase 20 timeline)

---

## [v5.9.9] - 2026-08-02 -- Ενοποίηση Διαδρομών Αναφορών & Απομόνωση Καταλόγου Δεδομένων

---

## [v5.9.8] - 2026-08-02 -- Συγχρονισμός Έκδοσης

### Άλλαξε
- Συγχρονισμός συμβολοσειρών έκδοσης σε 5 αρχεία κώδικα και 15 αρχεία τεκμηρίωσης σε v5.9.8.

---

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

---

## [v5.9.6] - 2026-08-01 -- Ενοποίηση Καταλόγου Δεδομένων & Δυναμική Ανακάλυψη Στόχων

### Άλλαξε
- **Μετεγκατάσταση REPORTS_DIR σε data/reports/autonomous_tester/** (`src/ai/testing/autonomous_tester.py`, `src/api/tester_routes.py`): Αλλαγή από `reports/autonomous_tester/` (ρίζα έργου) σε `data/reports/autonomous_tester/`. Όλες οι αναφορές καταρρίψεων που παράγονται κατά την εκτέλεση βρίσκονται πλέον υπό τον κατάλογο `data/`, εξασφαλίζοντας καθαρή ρίζα έργου και σωστό αποκλεισμό μέσω `.gitignore`.
- **Δυναμική ανακάλυψη στόχων (`_discover_all_python_targets()`)** (`src/ai/testing/autonomous_tester.py`): Αντικατάσταση της σκληρά κωδικοποιημένης λίστας 4 στόχων `TARGET_ARMS` με δυναμικό σαρωτή αρχείων που διατρέχει τους καταλόγους `src/analysis/`, `src/ingestion/`, `src/ai/`, `src/utils/`, `src/core/` και `src/api/`, ανακαλύπτοντας όλα τα μη-`__init__.py` αρχεία Python ως βραχίονες δοκιμής. Κάθε βραχίονας καλείται με `--help` για γρήγορη έξοδο υποδιεργασίας. Ο αυτόνομος ελεγκτής κλιμακώνεται από 4 σε 70+ βραχίονες.
- **Συμφιλίωση Q-Table κατά την εκκίνηση** (`run_autonomous_tester()`): Συμφιλιώνει τον αποθηκευμένο πίνακα Q με τον τρέχοντα αριθμό βραχιόνων, διατηρώντας υπάρχουσες τιμές Q και μηδενίζοντας νέους βραχίονες.
- **Δυναμική ανακάλυψη βραχιόνων στα tester routes** (`src/api/tester_routes.py`): Η `_discover_target_arms()` αντικατοπτρίζει την ίδια λογική σάρωσης για το endpoint `/api/v1/tester/status`.
- **Συγχρονισμός συμβολοσειρών έκδοσης σε 5 αρχεία κώδικα και 15 αρχεία τεκμηρίωσης** σε v5.9.6.
- **`tests/test_multi_tier.py`**: Ο ισχυρισμός `test_talos_version` ενημερώθηκε από "5.9.5" σε "5.9.6".
- **Ενημέρωση εκκινητών** (`run_talos.bat`, `run_talos.sh`): Ενημερώθηκαν οι συμβολοσειρές έκδοσης, οι διαδρομές καταλόγων αναφορών και οι περιγραφές του ελεγκτή.

### Επαλήθευση
- Όλα τα τροποποιημένα αρχεία `.py` περνούν το `python -m py_compile`.
- Πλήρης σουίτα δοκιμών: 181 επιτυχείς, 0 αποτυχίες (`pytest -v`).
- Πρωτόκολλο μηδενικών emojis τηρείται σε όλο τον κώδικα και την τεκμηρίωση.

---

---

## [v5.9.5] - 2026-08-02 -- Συγχρονισμός Έκδοσης

### Άλλαξε
- Συγχρονισμός συμβολοσειρών έκδοσης σε 5 αρχεία κώδικα και 15 αρχεία τεκμηρίωσης σε v5.9.5.

---

---

## [v5.9.4] - 2026-08-02 -- Συγχρονισμός Έκδοσης

### Άλλαξε
- Συγχρονισμός συμβολοσειρών έκδοσης σε 5 αρχεία κώδικα και 15 αρχεία τεκμηρίωσης σε v5.9.4.

---

---

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

---

## [v5.9.2] - 2026-08-01 -- Αυτόνομος Ελεγκτής Συστήματος (RL-Driven, LLM-Judged)

### Προστέθηκε
- **Αυτόνομος Ελεγκτής Συστήματος (RL-Driven Chaos Engineering)** (`src/ai/testing/autonomous_tester.py`, 390 γραμμές): Εφαρμόζει αλγόριθμο Non-Stationary Multi-Armed Bandit με πολιτική Epsilon-Greedy (epsilon=0.2) και ρυθμό μάθησης Alpha (0.1). Δοκιμάζει αυτόματα τα 4 βασικά υποσυστήματα TALOS (FastAPI Server, MCP Server, Daily Search, Citation Analyzer) μέσω υποδιεργασιών υποβάθρου με μέγιστο 5 δευτερολέπτων ανά εκτέλεση. Όταν μια υποδιεργασία καταρρέει, το stderr αποστέλλεται στο Fast Edge LLM (tier="fast") για διάγνωση σε φυσική γλώσσα. Τα αποτελέσματα προβάλλονται μέσω Rich TUI (Spinners, κόκκινα Panels καταρρεύσεων, κίτρινα Panels διάγνωσης AI, πράσινες επιβεβαιώσεις PASS, χρωματισμένος πίνακας Q). Ο πίνακας Q αποθηκεύεται σε JSON στο `data/tester_q_table.json`. Οι καταρρεύσεις καταγράφονται σε Markdown με πλήρες traceback στο `reports/autonomous_tester/CRASH_REPORT_{timestamp}.md`. Εκπέμπει συμβάντα Synapse για κάθε βήμα δοκιμής. Σχήμα ανταμοιβής: +50 για επιτυχία, -1 για αποτυχία. Εντολή εκτέλεσης: `python src/ai/testing/autonomous_tester.py [στόχοι]`.
- **REST API διαδρομές ελεγκτή** (`src/api/tester_routes.py`, 200 γραμμές): FastAPI APIRouter που εκθέτει το `/api/v1/tester`. Η διαδρομή `GET /api/v1/tester/status` επιστρέφει τον πίνακα Q με ταξινόμηση ευθραυστότητας (STABLE/LOW/MODERATE/HIGH_FRAGILITY). Η διαδρομή `GET /api/v1/tester/reports` επιστρέφει μεταδεδομένα των Markdown αναφορών καταρρεύσεων. Μοντέλα Pydantic v2: `ArmStatus`, `TesterStatus`, `CrashReportEntry`, `TesterReports`. Όλες οι διαδρομές είναι ασφαλείς και μόνο για ανάγνωση.
- **TALOS Terminal CLI -- Επιλογή 6 (Αυτόνομος Ελεγκτής Συστήματος)**: Ενσωματώθηκε στο `talos.py` με συνολικά 11 επιλογές και νέα κατηγορία "TESTING & CI/CD". Οδηγεί στην άμεση εκκίνηση του ελεγκτή και καλεί τη συνάρτηση `run_autonomous_tester()`.
- **Ενημέρωση εκκινητών συστήματος**: Το `run_talos.bat` επιλογή 8 και το `run_talos.sh` επιλογή 8 εκτελούν το `python src/ai/testing/autonomous_tester.py` με προαιρετικά ορίσματα.
- **Κανόνας υποχρεωτικού συγχρονισμού εκδόσεων** (`.clinerules`): Νέος κανόνας που απαιτεί την επαλήθευση των συμβολοσειρών έκδοσης στα 5 αρχεία κώδικα (`talos.py`, `run_talos.bat`, `run_talos.sh`, `config/settings.py`, `src/api/main_api.py`) και στα 15 αρχεία τεκμηρίωσης.

### Άλλαξε
- **Αριθμός endpoints FastAPI**: 16 -> 18 (προστέθηκαν τα `GET /api/v1/tester/status` και `GET /api/v1/tester/reports` μέσω `app.include_router(tester_router)`).
- **`talos.py` μενού επιλογών**: 10 -> 11 επιλογές. Η κατηγορία "TESTING & CI/CD" είναι η επιλογή 6 (αυτόνομος ελεγκτής). Οι επιλογές 7-11 αναδιατάχθηκαν: Baseline Standard (7), Baseline Academic (8), DRL Status (9), Docs Generator (10), Έξοδος (11).
- **`run_talos.bat` και `run_talos.sh`**: 9 -> 10 επιλογές. Προστέθηκε ο αυτόνομος ελεγκτής στην επιλογή 8. Το Test Suite μετακινήθηκε στην επιλογή 9, η Έξοδος στην 10.
- **Υποχρεωτικός συγχρονισμός εκδόσεων** σε 5 αρχεία κώδικα και 15 αρχεία τεκμηρίωσης σε v5.9.2.
- **Μετονομασία μεταφραστή ερωτημάτων**: Αλλαγή από "PYTHIA" σε "Query Translator".
- **`test_multi_tier.py`**: Ο ισχυρισμός `test_talos_version` ενημερώθηκε από "5.8.9" σε "5.9.1".

### Διορθώθηκε
- Και τα 7 τροποποιημένα αρχεία `.py` περνούν τον έλεγχο `python -m py_compile`.
- Αφαιρέθηκαν όλα τα emojis από την έξοδο του κώδικα.

---

---

---

## [v5.9.1] - 2026-08-01 -- Αυτόνομος Ελεγκτής Συστήματος (RL-Driven, LLM-Judged)

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
- **Συγχρονισμός συμβολοσειρών έκδοσης** σε 5 αρχεία κώδικα και 15 αρχεία τεκμηρίωσης σε v5.9.1.
- **Επιβολή περιγραφικών ονομάτων**: Αναφορές σε "PYTHIA" αντικαταστάθηκαν με "Query Translator".
- **`test_multi_tier.py`**: Βεβαίωση `test_talos_version` ενημερώθηκε από "5.8.9" σε "5.9.1".

### Επαλήθευση
- Και τα 7 τροποποιημένα αρχεία `.py` περνούν `python -m py_compile`.
- Πρωτόκολλο μηδενικών emojis σε όλο τον νέο κώδικα.

---

---

---

## [v5.9.0] - 2026-08-01 -- Αυτόνομος Ελεγκτής Συστήματος (RL-Driven, LLM-Judged)

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
- **Συγχρονισμός συμβολοσειρών έκδοσης** σε 5 αρχεία κώδικα και 15 αρχεία τεκμηρίωσης σε v5.9.0.
- **Επιβολή περιγραφικών ονομάτων**: Αναφορές σε "PYTHIA" αντικαταστάθηκαν με "Query Translator".
- **`test_multi_tier.py`**: Βεβαίωση `test_talos_version` ενημερώθηκε από "5.8.9" σε "5.9.0".

### Επαλήθευση
- Και τα 7 τροποποιημένα αρχεία `.py` περνούν `python -m py_compile`.
- Πρωτόκολλο μηδενικών emojis σε όλο τον νέο κώδικα.

---

---

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

---

## [v5.8.8] - 2026-08-01 -- Συγχρονισμός Έκδοσης & Σφράγιση Καθαρής Κυκλοφορίας

### Άλλαξε
- Συγχρονισμός συμβολοσειρών έκδοσης σε 5 αρχεία κώδικα και 15 αρχεία τεκμηρίωσης σε v5.8.8.

---

---

## [v5.8.7] - 2026-08-01 -- Συγχρονισμός Έκδοσης & Διόρθωση TUI

### Άλλαξε
- Συγχρονισμός συμβολοσειρών έκδοσης σε 5 αρχεία κώδικα και 15 αρχεία τεκμηρίωσης σε v5.8.7.

---

---

## [v5.8.6] - 2026-08-01 -- Διόρθωση Εμφάνισης Ονόματος Μοντέλου TUI, Σφράγιση Καθαρής Κυκλοφορίας

### Διορθώθηκε -- Εμφάνιση Ονόματος Μοντέλου στον Πίνακα Κατάστασης TUI
- `talos.py`: Η `_build_status_table()` εμφανίζει πλέον την πλήρη ακατέργαστη συμβολοσειρά ρύθμισης και για τα τρία ενεργά επίπεδα αντί για περικοπή μέσω `split(":")`. Το Επίπεδο Βαριάς Συλλογιστικής τώρα δείχνει "qwen2.5:14b" αντί για "14b". Το Επίπεδο Γρήγορης Ακμής δείχνει "fermionresearch/Neutrino-8B" αντί για "fermionresearch". Ο Πάροχος Cloud δείχνει το πλήρες όνομα παρόχου και μοντέλου.
- Το πρόβλημα προκλήθηκε από τη λογική `split(":")[-1]` που κρατούσε μόνο την ετικέτα κβαντισμού, απορρίπτοντας το όνομα του μοντέλου βάσης.

### Άλλαξε -- Συμβολοσειρές Έκδοσης
- `config/settings.py`: `TALOS_VERSION` από `"5.8.4"` σε `"5.8.6"`.
- `src/api/main_api.py`: App `version` από `"5.8.4"` σε `"5.8.6"`. Module docstring, αρχείο καταγραφής εκκίνησης και περιγραφή ενημερώθηκαν.
- `tests/test_multi_tier.py`: Διορθώθηκε η βεβαίωση `TALOS_VERSION` από `"5.8.4"` σε `"5.8.6"`.

### Συγχρονίστηκε -- Όλα τα 15 Κανονικά Αρχεία Τεκμηρίωσης
- Όλες οι συμβολοσειρές έκδοσης ενημερώθηκαν σε `v5.8.6`. Όλες οι ημερομηνίες "Last Updated" ορίστηκαν σε `2026-08-01`.
- Νέες καταχωρήσεις v5.8.6 προστέθηκαν στα `CHANGELOG_EN.md`, `CHANGELOG_GR.md`, `TIMELINE_EN.md`, `TIMELINE_GR.md`.
- Το `.clinerules` ενημερώθηκε στην έκδοση v5.8.6.

---

---

---

## [v5.8.5] - 2026-08-01 -- Διόρθωση Εμφάνισης Ονόματος Μοντέλου TUI, Σφράγιση Καθαρής Κυκλοφορίας

### Διορθώθηκε -- Εμφάνιση Ονόματος Μοντέλου στον Πίνακα Κατάστασης TUI
- `talos.py`: Η `_build_status_table()` εμφανίζει πλέον την πλήρη ακατέργαστη συμβολοσειρά ρύθμισης και για τα τρία ενεργά επίπεδα αντί για περικοπή μέσω `split(":")`. Το Επίπεδο Βαριάς Συλλογιστικής τώρα δείχνει "qwen2.5:14b" αντί για "14b". Το Επίπεδο Γρήγορης Ακμής δείχνει "fermionresearch/Neutrino-8B" αντί για "fermionresearch". Ο Πάροχος Cloud δείχνει το πλήρες όνομα παρόχου και μοντέλου.
- Το πρόβλημα προκλήθηκε από τη λογική `split(":")[-1]` που κρατούσε μόνο την ετικέτα κβαντισμού, απορρίπτοντας το όνομα του μοντέλου βάσης.

### Άλλαξε -- Συμβολοσειρές Έκδοσης
- `config/settings.py`: `TALOS_VERSION` από `"5.8.4"` σε `"5.8.5"`.
- `src/api/main_api.py`: App `version` από `"5.8.4"` σε `"5.8.5"`. Module docstring, αρχείο καταγραφής εκκίνησης και περιγραφή ενημερώθηκαν.
- `tests/test_multi_tier.py`: Διορθώθηκε η βεβαίωση `TALOS_VERSION` από `"5.8.4"` σε `"5.8.5"`.

### Συγχρονίστηκε -- Όλα τα 15 Κανονικά Αρχεία Τεκμηρίωσης
- Όλες οι συμβολοσειρές έκδοσης ενημερώθηκαν σε `v5.8.5`. Όλες οι ημερομηνίες "Last Updated" ορίστηκαν σε `2026-08-01`.
- Νέες καταχωρήσεις v5.8.5 προστέθηκαν στα `CHANGELOG_EN.md`, `CHANGELOG_GR.md`, `TIMELINE_EN.md`, `TIMELINE_GR.md`.
- Το `.clinerules` ενημερώθηκε στην έκδοση v5.8.5.

---

---

---

## [v5.8.4] - 2026-08-01 -- Πίνακας Ελέγχου Rich TUI, Ενσωμάτωση Model Manager CLI, Μενού 10 Επιλογών

### Προστέθηκε -- Πίνακας Ελέγχου Rich Terminal UI
- `talos.py`: Πλήρης ανακατασκευή με τη βιβλιοθήκη `rich`. Αντικατάσταση όλων των `print()` με μορφοποίηση `rich` (`Console`, `Panel`, `Table`, `Box`, `Text`). Επαγγελματικός χρωματικός συνδυασμός σκούρου σχιστόλιθου/μπλε με περιγράμματα `box.ROUNDED`.
- Δυναμικός πίνακας κατάστασης στην κεφαλίδα του κύριου μενού: περιβάλλον Conda, θύρα API (8001), δίαυλος Synapse (8000), λειτουργία εκτέλεσης (Air-Gapped Local / Hybrid / Cloud), ενεργά επίπεδα LLM (Fast Edge, Heavy Reasoning, Cloud Provider).
- Μενού αναδιαρθρωμένο σε 10 επιλογές με τον Model Manager ως αποκλειστική επιλογή 1.
- Πρωτόκολλο μηδενικών emojis σε όλη την έξοδο με μορφοποίηση Rich.

### Προστέθηκε -- Ενσωμάτωση Model Manager CLI
- `talos.py` επιλογή 1: "Configure AI Models & Execution Modes (Model Manager)" -- καλεί το `src.ai.llm.model_manager.main()` απευθείας μέσω εισαγωγής αντί για υποδιεργασία.

### Προστέθηκε -- Εξάρτηση
- `requirements.txt`: Προστέθηκε η βιβλιοθήκη `rich`.

### Άλλαξε -- Συμβολοσειρές Έκδοσης
- `config/settings.py`: `TALOS_VERSION` από `"5.8.3"` σε `"5.8.4"`.
- `src/api/main_api.py`: App `version` από `"5.8.3"` σε `"5.8.4"`.
- `tests/test_multi_tier.py`: Διορθώθηκε η βεβαίωση `TALOS_VERSION` από `"5.8.3"` σε `"5.8.4"`. Αποτέλεσμα: 173 επιτυχείς, 0 αποτυχίες.

### Συγχρονίστηκε -- Όλα τα 15 Κανονικά Αρχεία Τεκμηρίωσης
- Όλες οι συμβολοσειρές έκδοσης ενημερώθηκαν σε `v5.8.4`.
- Νέες καταχωρήσεις v5.8.4 προστέθηκαν στα `CHANGELOG_EN.md`, `CHANGELOG_GR.md`, `TIMELINE_EN.md`, `TIMELINE_GR.md`.

---

---

---

## [v5.8.3] - 2026-08-01 -- Εκκαθάριση Χώρου Εργασίας, Ενημέρωση Templates, Εκσυγχρονισμός Docker, Συγχρονισμός 15 Αρχείων

### Αφαιρέθηκε -- Παρωχημένα Αρχεία
- `talos.bat` (παλαιός εκκινητής, αντικαταστάθηκε από το `run_talos.bat` v5.8.1+).
- Κατάλογος `venv/` στη ρίζα (χρήση `.venv` ή Conda `talosenv`).
- Επιβεβαιώθηκε η διατήρηση του καταλόγου `tools/` (ενεργά scripts: `_bump_docs.py`, `_fix_changelogs.py`).

### Ενημερώθηκε -- Πρότυπα Περιβάλλοντος και Ρυθμίσεων
- `example.env`: Πλήρες σετ κλειδιών v5.8.3: `FAST_EDGE_MODEL`, `FAST_EDGE_BASE_URL`, `HEAVY_REASONING_MODEL`, `OLLAMA_BASE_URL`, `TALOS_API_PORT`, `SYNAPSE_BUS_URL`, `TALOS_EXECUTION_MODE`, `TALOS_CLOUD_PROVIDER`, `GEMINI_API_KEY`, `GEMINI_FLASH_MODEL`, `GEMINI_PRO_MODEL`, `DEEPSEEK_API_KEY`, `DEEPSEEK_MODEL_CHAT`, `HF_TOKEN`, `HF_MODEL_NAME`.
- `config.template.json`: Προστέθηκε το block `ai_models` με ενότητες fast_edge, heavy_reasoning και cloud_fallback. Προστέθηκε το κλειδί `execution_mode`.
- `requirements.txt`: Αναδιοργάνωση με ρητές ενότητες. Προστέθηκαν `httpx`, `mcp`, `pytest`. Σειρά: API Framework, MCP, Πάροχοι LLM, Ακαδημαϊκά APIs, Data Science, Οπτικοποίηση, UX, Αναφορές, DRL, Testing, Αναζήτηση Ιστού.

### Ενημερώθηκε -- Υποδομή Docker
- `Dockerfile`: Βασική εικόνα `python:3.10-slim` αναβαθμίστηκε σε `python:3.11-slim`. Exposed port 8001 (ήταν 5000+8501). Προστέθηκε `HEALTHCHECK` στο `/api/v1/health`. Εντολή `CMD` άλλαξε σε `["python", "-m", "uvicorn", "src.api.main_api:app", "--host", "0.0.0.0", "--port", "8001"]`. Αφαιρέθηκε η λογική πολλαπλής εκκίνησης Streamlit.
- `docker-compose.yml`: Υπηρεσία `talos` μετονομάστηκε σε `talos_api`, container `talos_api_v5.8.3`. Αντιστοίχιση θύρας `8001:8001` (ήταν `5000:5000,8501:8501`). Οι τόμοι άλλαξαν από γενική προσάρτηση `.` σε ρητούς `./data`, `./models`, `./logs`. Προστέθηκε `restart: unless-stopped`.
- `.dockerignore`: Προστέθηκαν `venv/`, `.venv/`, `cherry_ui_isolated/`, `frontend_ui/`, `config.json`, `.clinerules`, `docs/`, `.pytest_cache/`, `reports/`. Οργάνωση κατά κατηγορία με σαφείς κεφαλίδες ενοτήτων.

### Άλλαξε -- Συμβολοσειρές Έκδοσης
- `.clinerules`: Έκδοση `v5.8.1` σε `v5.8.3`. Υποσέλιδο ημερομηνίας και περίληψης ενημερώθηκε.
- `config/settings.py`: `TALOS_VERSION` από `"5.8.0"` σε `"5.8.3"`. Docstring ενημερώθηκε.
- `src/api/main_api.py`: Η `version` της εφαρμογής από `"5.8.0"` σε `"5.8.3"`. Docstring, αρχείο καταγραφής εκκίνησης και `description` ενημερώθηκαν.
- `src/api/synapse_routes.py`: Αναφορά έκδοσης στο docstring ενημερώθηκε.

### Συγχρονίστηκε -- Όλα τα 15 Κανονικά Αρχεία Τεκμηρίωσης
- Όλες οι συμβολοσειρές έκδοσης ενημερώθηκαν σε `v5.8.3`. Όλες οι ημερομηνίες "Τελευταίας Ενημέρωσης" ορίστηκαν σε `2026-08-01`.
- Νέες καταχωρήσεις v5.8.3 προστέθηκαν στα `CHANGELOG_EN.md`, `CHANGELOG_GR.md`, `TIMELINE_EN.md`, `TIMELINE_GR.md`.

### Προστέθηκε -- Εγγενής MCP Server (src/mcp_server.py)
- `src/mcp_server.py` (269 γραμμές): Επίσημος MCP (Model Context Protocol) Server για το Οικοσύστημα TALOS. Χρησιμοποιεί `MCPServer` από το `mcp.server.mcpserver` (MCP SDK v2.0.0) με stdio transport. Αποσυνδεδεμένη αρχιτεκτονική: και τα 4 tools αναθέτουν στο TALOS FastAPI backend μέσω HTTP στη ρυθμιζόμενη διεύθυνση `TALOS_API_BASE` (προεπιλογή: `http://127.0.0.1:8001/api/v1`).
- Τέσσερα MCP tools που εκτίθενται:
  - `talos_system_status()`: GET `/api/v1/health` -- μορφοποιημένα στατιστικά βάσης δεδομένων και κάλυψη μοντέλων embedding. Επιστρέφει μήνυμα εκτός σύνδεσης αν το backend δεν είναι προσβάσιμο.
  - `talos_semantic_search(query, top_k=5)`: POST `/api/v1/search/semantic` -- διανυσματική αναζήτηση με μορφοποιημένα αποτελέσματα (ID, Τίτλος, Συγγραφείς, Έτος, Βαθμολογία).
  - `talos_get_paper_details(paper_id)`: GET `/api/v1/papers/{paper_id}` -- πλήρης εγγραφή άρθρου με περίληψη, βαθμολογίες 4 επιπέδων, AI συλλογιστική, δεδομένα εμπλουτισμού.
  - `talos_trigger_scrape(sources=None)`: POST `/api/v1/scrape/trigger` -- εκκινεί ακαδημαϊκή ανίχνευση στο παρασκήνιο, επιστρέφει task_id.
- Διαχείριση σφαλμάτων: Όλα τα tools επιστρέφουν περιγραφικά μηνύματα σφαλμάτων (όχι exceptions) για φιλικές προς το LLM αποκρίσεις. Διαχειρίζεται ConnectionError, Timeout, HTTP σφάλματα και αποτυχίες ανάλυσης JSON.
- Ρύθμιση: `TALOS_API_BASE` env var (προεπιλογή: `http://127.0.0.1:8001/api/v1`), `TALOS_MCP_TIMEOUT` env var (προεπιλογή: 30s). Συμβατό με air-gapped περιβάλλον.
- Αυτόνομη εκτέλεση: `python src/mcp_server.py` εκκινεί τον MCP server μέσω stdio. Το Cherry Studio έχει ρυθμιστεί για σύνδεση μέσω stdio.

### Προστέθηκε -- Σουίτα Unit Tests για τον MCP Server (tests/test_mcp_server.py)
- `tests/test_mcp_server.py` (334 γραμμές, 27 tests): Ολοκληρωμένη σουίτα pytest με πλήρη HTTP mocking μέσω `unittest.mock.patch`.
- Κλάσεις δοκιμών: `TestMCPServerRegistration` (4 tests), `TestTalosSystemStatus` (4), `TestTalosSemanticSearch` (6), `TestTalosGetPaperDetails` (5), `TestTalosTriggerScrape` (6), `TestConfiguration` (2).
- Κάλυψη: επαλήθευση ονόματος/έκδοσης server, καταμέτρηση εγγεγραμμένων tools, επιτυχείς αποκρίσεις, μονοπάτια σφαλμάτων εκτός σύνδεσης/χρονικού ορίου/μη αναλύσιμης απόκρισης, επικύρωση (σύντομο ερώτημα, μη έγκυρο paper ID), φιλτραρισμένες πηγές, προεπιλεγμένες ρυθμίσεις.

### Άλλαξε -- Ενημερώθηκαν οι Χάρτες Έργου
- `docs/PROJECT_MAP.md` και `docs/PROJECT_MAP_EN.md`: Προστέθηκε καταχώρηση `src/mcp_server.py` στις Περιγραφές Modules (Ενότητα 8). Ενημερώθηκε το υποσέλιδο "Τελευταία Ενημέρωση" με αναφορές MCP Server και 27-unit test suite. Συνολικός αριθμός αρχείων: 69 (από 67).
- Ο κατάλογος `tests/` περιλαμβάνεται πλέον στην καταμέτρηση αρχείων μαζί με src/, integration/ και root.

---

---

## [v5.8.2] - 2026-08-01 -- Εκκαθάριση Χώρου Εργασίας, Ενημέρωση Templates, Εκσυγχρονισμός Docker, Συγχρονισμός 15 Αρχείων

### Αφαιρέθηκε -- Παρωχημένα Αρχεία
- `talos.bat` (παλαιός εκκινητής, αντικαταστάθηκε από το `run_talos.bat` v5.8.1+).
- Κατάλογος `venv/` στη ρίζα (χρήση `.venv` ή Conda `talosenv`).
- Επιβεβαιώθηκε η διατήρηση του καταλόγου `tools/` (ενεργά scripts: `_bump_docs.py`, `_fix_changelogs.py`).

### Ενημερώθηκε -- Πρότυπα Περιβάλλοντος και Ρυθμίσεων
- `example.env`: Πλήρες σετ κλειδιών v5.8.2: `FAST_EDGE_MODEL`, `FAST_EDGE_BASE_URL`, `HEAVY_REASONING_MODEL`, `OLLAMA_BASE_URL`, `TALOS_API_PORT`, `SYNAPSE_BUS_URL`, `TALOS_EXECUTION_MODE`, `TALOS_CLOUD_PROVIDER`, `GEMINI_API_KEY`, `GEMINI_FLASH_MODEL`, `GEMINI_PRO_MODEL`, `DEEPSEEK_API_KEY`, `DEEPSEEK_MODEL_CHAT`, `HF_TOKEN`, `HF_MODEL_NAME`.
- `config.template.json`: Προστέθηκε το block `ai_models` με ενότητες fast_edge, heavy_reasoning και cloud_fallback. Προστέθηκε το κλειδί `execution_mode`.
- `requirements.txt`: Αναδιοργάνωση με ρητές ενότητες. Προστέθηκαν `httpx`, `mcp`, `pytest`. Σειρά: API Framework, MCP, Πάροχοι LLM, Ακαδημαϊκά APIs, Data Science, Οπτικοποίηση, UX, Αναφορές, DRL, Testing, Αναζήτηση Ιστού.

### Ενημερώθηκε -- Υποδομή Docker
- `Dockerfile`: Βασική εικόνα `python:3.10-slim` αναβαθμίστηκε σε `python:3.11-slim`. Exposed port 8001 (ήταν 5000+8501). Προστέθηκε `HEALTHCHECK` στο `/api/v1/health`. Εντολή `CMD` άλλαξε σε `["python", "-m", "uvicorn", "src.api.main_api:app", "--host", "0.0.0.0", "--port", "8001"]`. Αφαιρέθηκε η λογική πολλαπλής εκκίνησης Streamlit.
- `docker-compose.yml`: Υπηρεσία `talos` μετονομάστηκε σε `talos_api`, container `talos_api_v5.8.2`. Αντιστοίχιση θύρας `8001:8001` (ήταν `5000:5000,8501:8501`). Οι τόμοι άλλαξαν από γενική προσάρτηση `.` σε ρητούς `./data`, `./models`, `./logs`. Προστέθηκε `restart: unless-stopped`.
- `.dockerignore`: Προστέθηκαν `venv/`, `.venv/`, `cherry_ui_isolated/`, `frontend_ui/`, `config.json`, `.clinerules`, `docs/`, `.pytest_cache/`, `reports/`. Οργάνωση κατά κατηγορία με σαφείς κεφαλίδες ενοτήτων.

### Άλλαξε -- Συμβολοσειρές Έκδοσης
- `.clinerules`: Έκδοση `v5.8.1` σε `v5.8.2`. Υποσέλιδο ημερομηνίας και περίληψης ενημερώθηκε.
- `config/settings.py`: `TALOS_VERSION` από `"5.8.0"` σε `"5.8.2"`. Docstring ενημερώθηκε.
- `src/api/main_api.py`: Η `version` της εφαρμογής από `"5.8.0"` σε `"5.8.2"`. Docstring, αρχείο καταγραφής εκκίνησης και `description` ενημερώθηκαν.
- `src/api/synapse_routes.py`: Αναφορά έκδοσης στο docstring ενημερώθηκε.

### Συγχρονίστηκε -- Όλα τα 15 Κανονικά Αρχεία Τεκμηρίωσης
- Όλες οι συμβολοσειρές έκδοσης ενημερώθηκαν σε `v5.8.2`. Όλες οι ημερομηνίες "Τελευταίας Ενημέρωσης" ορίστηκαν σε `2026-08-01`.
- Νέες καταχωρήσεις v5.8.2 προστέθηκαν στα `CHANGELOG_EN.md`, `CHANGELOG_GR.md`, `TIMELINE_EN.md`, `TIMELINE_GR.md`.

---

---

## [v5.8.1] - 2026-07-31 -- Κεντρικοί Εκκινητές 9 Επιλογών, Σουίτα 96 Unit Tests, Πολυεπίπεδη Δρομολόγηση Neutrino-8B, Εκκαθάριση Φακέλου Tools

### Προστέθηκε -- Αυτόνομοι Δαίμονες στους Κεντρικούς Εκκινητές
- `run_talos.bat` v5.8.1: Επεκτάθηκε από μενού 3 επιλογών σε 9 επιλογές σε τρεις ενότητες:
  - Ενότητα 1 (REST API και FRONTEND): Πλήρης Εγκατάσταση, FastAPI Server (θύρα 8001), MCP Server, Ενδιάμεση Διεπαφή (Cherry Studio)
  - Ενότητα 2 (CLI και ΑΥΤΟΝΟΜΟΙ ΔΑΙΜΟΝΕΣ): TALOS Terminal CLI, Αυτόνομος Ερευνητικός Δαίμονας (`talos_service.py`), Ζωντανός DRL Πράκτορας (`talos_live_agent.py --verbose`)
  - Ενότητα 3 (TESTING και SYSTEM): Εκτέλεση Test Suite (`pytest -v`), Έξοδος
  - Η Πλήρης Εγκατάσταση (Επιλογή 1) περιλαμβάνει πλέον τον Frontend Provisioner ως βήμα 4/4
- `run_talos.sh` v5.8.1: Αντικατοπτρίζει το `.bat` με μενού 9 επιλογών χρησιμοποιώντας virtualenv αντί για conda.

### Προστέθηκε -- Διευρυμένη Σουίτα Δοκιμών (96 unit tests, από 29)
- `tests/test_smoke.py` (ΜΕΤΑΦΕΡΘΗΚΕ από `tools/`): Ενοποιημένο system smoke test με ετικέτες [PASS]/[FAIL]/[SKIP] χωρίς emoji. Ενισχυμένη `check()` για διαχείριση `BaseException` και διάδοση `SystemExit`/`KeyboardInterrupt`. Προστέθηκαν skip entries για τα `data_enricher.py`, `metadata_enricher.py`, `pdf_downloader.py`, `talos_service.py`, `train_agent.py`.
- `tests/test_multi_tier.py`: Διορθώθηκε η παλιά βεβαίωση `TALOS_VERSION` από `"5.7.1"` σε `"5.8.0"`.

### Άλλαξε
- `tools/test_smoke.py` --> `tests/test_smoke.py`: Μεταφέρθηκε στον κανονικό κατάλογο δοκιμών. Τα docstrings και τα σχόλια διαδρομών ενημερώθηκαν.
- `.clinerules`: Και οι δύο αναφορές `tools/test_smoke.py` ενημερώθηκαν σε `tests/test_smoke.py`.
- `.clinerules` υποσέλιδο: Η έκδοση από v5.8.0 σε v5.8.1 με ενημερωμένη περίληψη χαρακτηριστικών.

### Αφαιρέθηκε -- Εκκαθάριση Φακέλου Tools
- Διαγράφηκε `tools/start_talos.bat` (αντικαταστάθηκε από το ριζικό `run_talos.bat` με μενού 9 επιλογών).
- Διαγράφηκε `tools/_bump.py` (αχρησιμοποίητο παλαιό script).
- Διαγράφηκε `tools/_git_status.ps1` (αχρησιμοποίητο παλαιό script).
- Τα `tools/_gui_runner.py` και `tools/_git_out.txt` ήταν ήδη απόντα (εκκαθαρίστηκαν σε προηγούμενη έκδοση).
- Ο φάκελος `tools/` διατηρήθηκε (περιέχει ακόμη τα ενεργά `_bump_docs.py` και `_fix_changelogs.py`).

### Επαλήθευση
- `pytest -v` σε 96 δοκιμές -- ΟΛΕΣ ΠΕΡΑΣΑΝ (96 passed, 0 failed, 4 warnings).
- Πρωτόκολλο Μηδενικών Emoji σε όλα τα νέα/αλλαγμένα αρχεία.

---

---

---

## [v5.8.0] - 2026-07-31 -- Πολυεπίπεδη Δρομολόγηση LLM, Εκκινητής POSIX, Απομονωμένη Ενδιάμεση Διεπαφή, Κάλυψη Pytest

### Προστέθηκε -- Αρχιτεκτονική Πολυεπίπεδης Δρομολόγησης LLM
- `config/settings.py` (ΝΕΟ): Κανονικός κόμβος ρυθμίσεων. Ορίζει `FAST_EDGE_MODEL` ("fermionresearch/Neutrino-8B"), `FAST_EDGE_BASE_URL` ("http://127.0.0.1:11435/v1"), `HEAVY_REASONING_MODEL` ("qwen2.5:14b"), `OLLAMA_BASE_URL` ("http://127.0.0.1:11434"), `TALOS_VERSION` ("5.8.0"), `TALOS_API_PORT` (8001).
- `src/core/ai_manager.py` v3.9: Προστέθηκε παράμετρος `tier` ("fast"|"heavy") στην `_execute_request()`. Το γρήγορο επίπεδο καλεί τη νέα μέθοδο `_execute_fast_tier_request()` που κάνει HTTP POST στο `FAST_EDGE_BASE_URL/chat/completions` με το Neutrino-8B. Το βαρύ επίπεδο χρησιμοποιεί την τυπική αλυσίδα παρόχων.
- `src/utils/frontend_provisioner.py` (ΝΕΟ): Κατεβάζει το φορητό Cherry Studio βάσει λειτουργικού συστήματος στον φάκελο `cherry_ui_isolated/`. Αυτόματα παράγει αρχείο ρυθμίσεων MCP JSON.
- `run_talos.sh` (ΝΕΟ): Σενάριο bash με 5 επιλογές που αντικατοπτρίζει το `run_talos.bat`. Virtualenv, FastAPI, MCP server, Ενδιάμεση Διεπαφή, Pytest.
- Μοναδιαίες δοκιμές: `tests/test_synapse.py` (21 δοκιμές), `tests/test_multi_tier.py` (20 δοκιμές), `tests/test_provisioner.py` (23 δοκιμές). Και οι 66 δοκιμές περνούν μέσω `pytest -v`.

### Άλλαξε
- `.clinerules`: Έκδοση v5.8.0 -> v5.8.0. Υποσέλιδο ενημερώθηκε.
- `docs/TIMELINE_EN.md` + `docs/TIMELINE_GR.md`: Προστέθηκε Φάση 3 με ορόσημα v5.8.0.
- `docs/PROJECT_MAP_EN.md`: Έκδοση ενημερώθηκε σε v5.8.0.
- `run_talos.bat`: Έκδοση ενημερώθηκε σε v5.8.0.

### Έλεγχος Anti-Greeklish
- Σαρώθηκαν όλα τα αρχεία `*_GR.md`. Όλο το περιεχόμενο χρησιμοποιεί σωστή ακαδημαϊκή ελληνική γραφή με τόνους Unicode. Δεν εντοπίστηκαν Greeklish.

### Επαλήθευση
- `py_compile` σε όλα τα 6 νέα/τροποποιημένα αρχεία `.py` -- ΕΠΙΤΥΧΙΑ. `pytest -v` σε 66 δοκιμές -- ΟΛΕΣ ΕΠΙΤΥΧΕΙΣ.

---

---

---

## [v5.7.2] - 2026-07-31 -- Πολυεπίπεδη Δρομολόγηση LLM, Εκκινητής POSIX, Απομονωμένη Ενδιάμεση Διεπαφή, Κάλυψη Pytest

### Προστέθηκε -- Αρχιτεκτονική Πολυεπίπεδης Δρομολόγησης LLM
- `config/settings.py` (ΝΕΟ): Κανονικός κόμβος ρυθμίσεων. Ορίζει `FAST_EDGE_MODEL` ("fermionresearch/Neutrino-8B"), `FAST_EDGE_BASE_URL` ("http://127.0.0.1:11435/v1"), `HEAVY_REASONING_MODEL` ("qwen2.5:14b"), `OLLAMA_BASE_URL` ("http://127.0.0.1:11434"), `TALOS_VERSION` ("5.7.2"), `TALOS_API_PORT` (8001).
- `src/core/ai_manager.py` v3.9: Προστέθηκε παράμετρος `tier` ("fast"|"heavy") στην `_execute_request()`. Το γρήγορο επίπεδο καλεί τη νέα μέθοδο `_execute_fast_tier_request()` που κάνει HTTP POST στο `FAST_EDGE_BASE_URL/chat/completions` με το Neutrino-8B. Το βαρύ επίπεδο χρησιμοποιεί την τυπική αλυσίδα παρόχων.
- `src/utils/frontend_provisioner.py` (ΝΕΟ): Κατεβάζει το φορητό Cherry Studio βάσει λειτουργικού συστήματος στον φάκελο `cherry_ui_isolated/`. Αυτόματα παράγει αρχείο ρυθμίσεων MCP JSON.
- `run_talos.sh` (ΝΕΟ): Σενάριο bash με 5 επιλογές που αντικατοπτρίζει το `run_talos.bat`. Virtualenv, FastAPI, MCP server, Ενδιάμεση Διεπαφή, Pytest.
- Μοναδιαίες δοκιμές: `tests/test_synapse.py` (21 δοκιμές), `tests/test_multi_tier.py` (20 δοκιμές), `tests/test_provisioner.py` (23 δοκιμές). Και οι 66 δοκιμές περνούν μέσω `pytest -v`.

### Άλλαξε
- `.clinerules`: Έκδοση v5.7.2 -> v5.7.2. Υποσέλιδο ενημερώθηκε.
- `docs/TIMELINE_EN.md` + `docs/TIMELINE_GR.md`: Προστέθηκε Φάση 3 με ορόσημα v5.7.2.
- `docs/PROJECT_MAP_EN.md`: Έκδοση ενημερώθηκε σε v5.7.2.
- `run_talos.bat`: Έκδοση ενημερώθηκε σε v5.7.2.

### Έλεγχος Anti-Greeklish
- Σαρώθηκαν όλα τα αρχεία `*_GR.md`. Όλο το περιεχόμενο χρησιμοποιεί σωστή ακαδημαϊκή ελληνική γραφή με τόνους Unicode. Δεν εντοπίστηκαν Greeklish.

### Επαλήθευση
- `py_compile` σε όλα τα 6 νέα/τροποποιημένα αρχεία `.py` -- ΕΠΙΤΥΧΙΑ. `pytest -v` σε 66 δοκιμές -- ΟΛΕΣ ΕΠΙΤΥΧΕΙΣ.

---

---

---

## [v5.7.1] - 2026-07-31 -- Πολυεπίπεδη Δρομολόγηση LLM, Εκκινητής POSIX, Απομονωμένη Ενδιάμεση Διεπαφή, Κάλυψη Pytest

### Προστέθηκε -- Αρχιτεκτονική Πολυεπίπεδης Δρομολόγησης LLM
- `config/settings.py` (ΝΕΟ): Κανονικός κόμβος ρυθμίσεων. Ορίζει `FAST_EDGE_MODEL` ("fermionresearch/Neutrino-8B"), `FAST_EDGE_BASE_URL` ("http://127.0.0.1:11435/v1"), `HEAVY_REASONING_MODEL` ("qwen2.5:14b"), `OLLAMA_BASE_URL` ("http://127.0.0.1:11434"), `TALOS_VERSION` ("5.7.1"), `TALOS_API_PORT` (8001).
- `src/core/ai_manager.py` v3.9: Προστέθηκε παράμετρος `tier` ("fast"|"heavy") στην `_execute_request()`. Το γρήγορο επίπεδο καλεί τη νέα μέθοδο `_execute_fast_tier_request()` που κάνει HTTP POST στο `FAST_EDGE_BASE_URL/chat/completions` με το Neutrino-8B. Το βαρύ επίπεδο χρησιμοποιεί την τυπική αλυσίδα παρόχων.
- `src/utils/frontend_provisioner.py` (ΝΕΟ): Κατεβάζει το φορητό Cherry Studio βάσει λειτουργικού συστήματος στον φάκελο `cherry_ui_isolated/`. Αυτόματα παράγει αρχείο ρυθμίσεων MCP JSON.
- `run_talos.sh` (ΝΕΟ): Σενάριο bash με 5 επιλογές που αντικατοπτρίζει το `run_talos.bat`. Virtualenv, FastAPI, MCP server, Ενδιάμεση Διεπαφή, Pytest.
- Μοναδιαίες δοκιμές: `tests/test_synapse.py` (21 δοκιμές), `tests/test_multi_tier.py` (20 δοκιμές), `tests/test_provisioner.py` (23 δοκιμές). Και οι 66 δοκιμές περνούν μέσω `pytest -v`.

### Άλλαξε
- `.clinerules`: Έκδοση v5.7.0 -> v5.7.1. Υποσέλιδο ενημερώθηκε.
- `docs/TIMELINE_EN.md` + `docs/TIMELINE_GR.md`: Προστέθηκε Φάση 3 με ορόσημα v5.7.1.
- `docs/PROJECT_MAP_EN.md`: Έκδοση ενημερώθηκε σε v5.7.1.
- `run_talos.bat`: Έκδοση ενημερώθηκε σε v5.7.1.

### Έλεγχος Anti-Greeklish
- Σαρώθηκαν όλα τα αρχεία `*_GR.md`. Όλο το περιεχόμενο χρησιμοποιεί σωστή ακαδημαϊκή ελληνική γραφή με τόνους Unicode. Δεν εντοπίστηκαν Greeklish.

### Επαλήθευση
- `py_compile` σε όλα τα 6 νέα/τροποποιημένα αρχεία `.py` -- ΕΠΙΤΥΧΙΑ. `pytest -v` σε 66 δοκιμές -- ΟΛΕΣ ΕΠΙΤΥΧΕΙΣ.

---

---

---

## [v5.7.0] - 2026-07-31 -- Αναβάθμιση Συντάγματος v2.0, Πρωτόκολλο SYNAPSE, Συγχρονισμός 15 Αρχείων

### Αναβαθμίστηκε -- 8-Σημείο Πρότυπο Κύριας Αρχικοποίησης (Σύνταγμα v2.0)
- `.clinerules` ΠΛΗΡΗΣ ΕΠΑΝΕΓΓΡΑΦΗ από τον κανόνα 12 αρχείων του v5.6.0 στο Σύνταγμα 8 Σημείων v2.0.
- **Σημείο I: ΠΡΩΤΟΚΟΛΛΟ ΜΗΔΕΝΙΚΩΝ EMOJIS** -- Όλο το νέο κείμενο πρέπει να χρησιμοποιεί αυστηρά ακαδημαϊκό τόνο.
- **Σημείο VI: ΚΑΝΟΝΑΣ ΣΥΓΧΡΟΝΙΣΜΟΥ 15 ΑΡΧΕΙΩΝ** -- Αναβαθμίστηκε από 12 σε 15 κανονικά αρχεία. Προστέθηκαν τα Timeline docs (EN+GR) ως αρχεία #8 και #9.
- **Σημείο VII: ΠΡΩΤΟΚΟΛΛΟ ΔΙΑΛΕΙΤΟΥΡΓΙΚΟΤΗΤΑΣ SYNAPSE** -- Ορισμός του event-driven διαύλου μεταξύ TALOS και άλλων μικροϋπηρεσιών ALEXANDRIA.

### Προστέθηκε -- Πρωτόκολλο SYNAPSE
- `src/integration/__init__.py` (ΝΕΟ), `src/integration/synapse_client.py` (ΝΕΟ, ~220 γραμμές): Κλάση EventEmitter για αποστολή JSON events στον δίαυλο SYNAPSE.
- `src/api/synapse_routes.py` (ΝΕΟ, ~200 γραμμές): FastAPI APIRouter με `POST /api/v1/synapse/webhook`.

### Προστέθηκε -- Σύστημα Χρονολογίου
- `docs/TIMELINE_EN.md` και `docs/TIMELINE_GR.md` (ΝΕΑ): Έγκυρα ιστορικά αρχεία όλων των οροσήμων ανάπτυξης.

### Προστέθηκε -- Αυτοματοποιημένος Batch Runner
- `run_talos.bat` (ΝΕΟ): Μενού 3 επιλογών στη ρίζα: Πλήρης Εγκατάσταση, Εκκίνηση FastAPI Server (θύρα 8001), Εκτέλεση Test Suite.

### Άλλαξε -- Ανακατανομή Θυρών
- `src/api/main_api.py`: Θύρα 8000 -> 8001. Ο δίαυλος SYNAPSE καταλαμβάνει τη θύρα 8000.
- `src/api/main_api.py`: 15 -> 16 endpoints (προστέθηκε Synapse webhook). Module docstring πλήρως αναθεωρημένο.

### Επαλήθευση
- `python -m py_compile` όλων των 4 νέων/τροποποιημένων αρχείων -- ΕΠΙΤΥΧΙΑ.

---

## [v5.6.0] - 2026-07-29 -- Κατάργηση Streamlit, Docs Δυνατοτήτων, Κανόνας 12-Αρχείων

### BREAKING -- Πλήρης Κατάργηση Streamlit
- Το app.py (1,175 γραμμές) διαγράφηκε. Ο φάκελος .streamlit/ διαγράφηκε. Το tools/_gui_runner.py διαγράφηκε.
- Το streamlit αφαιρέθηκε από το requirements.txt. Μοναδικό frontend: React 18 + Tailwind CSS + Shadcn UI.
### Προστέθηκαν
- docs/SYSTEM_CAPABILITIES_MASTER.md + .html (αναφορά δυνατοτήτων 9 ενοτήτων).
- GET /api/v1/capabilities endpoint. docs/API_HANDOVER_FOTIS.md, docs/UX_UI_BLUEPRINT_FOTIS.md, docs/IP_PROTECTION_STRATEGY.md.
- Κανόνας Συγχρονισμού 12 Αρχείων και Κανόνας Master Capabilities στο .clinerules.
### Τροποποιήθηκαν
- src/api/main_api.py v1.3: έκδοση 5.6.0, 15 endpoints. .clinerules, README.md, ROADMAP.md.
### Έλεγχος Υγείας Κώδικα
- Database path: data/talos_research.db επιβεβαιώθηκε. Τα API endpoints δεν μπλοκάρουν. sys.exit monkey-patched.

# Ημερολόγιο Αλλαγών (Changelog) - Project TALOS

Αυτό το αρχείο καταγράφει όλες τις σημαντικές αλλαγές στο Project TALOS. Το project ακολουθεί τις αρχές του [Semantic Versioning](https://semver.org/).

## [v5.5.2] - 2026-07-22 — 100% Κάλυψη Οικοσυστήματος API (4 Νέα Endpoints)

### Προστέθηκε
- **`src/api/main_api.py` v1.2 — Τέσσερα νέα "Deep Integration" endpoints για πλήρη κάλυψη του οικοσυστήματος:**
  - **`POST /api/v1/papers/{paper_id}/evaluate`** — Ενεργοποιεί αξιολόγηση AI για ένα paper μέσω BackgroundTasks.
    - Ανακτά τίτλο+abstract από τη βάση, τα στέλνει στο `_get_ai().evaluate_paper_json()` με το configured system prompt.
    - Αποθηκεύει scores (strategic, operational, tactical, playground), reasoning, contribution, utilization, tags, folder, και discord channel μέσω `db.update_paper_evaluation()`.
    - Επιστρέφει `TaskStatus` άμεσα.
  - **`POST /api/v1/ai/translate-query`** — Σύγχρονη μετάφραση φυσικής γλώσσας → boolean queries.
    - Ενσωματώνει τη βασική λογική του `query_translator.py` (αποφεύγει το διαδραστικό `questionary` prompt).
    - Pydantic models: `TranslateQueryRequest` (min_length=10) και `TranslateQueryResponse` (original_query + boolean_query dict).
  - **`GET /api/v1/analysis/authors`** — Επιστρέφει κορυφαίους συγγραφείς από την τοπική βάση μέσω SQL aggregation.
    - Απευθείας `SELECT authors, COUNT(*) ... GROUP BY authors ORDER BY cnt DESC LIMIT ?`.
    - Επιστρέφει `List[AuthorSummary]` με `author: str` και `count: int` — ιδανικό για Recharts `<BarChart>`.
  - **`POST /api/v1/db/recalculate-scores`** — Μαζικός επαναϋπολογισμός overall_score μέσω BackgroundTasks.
    - Αναπαράγει τη βασική λογική του `recalculate_scores.py` χωρίς το διαδραστικό `questionary.confirm()`.
    - Ενημερώσεις προόδου κάθε 500 εγγραφές. Επιστρέφει `TaskStatus`.
- **Νέα Pydantic models (4):** `TranslateQueryRequest`, `TranslateQueryResponse`, `AuthorSummary`, `EvaluatePaperRequest`
- **Συνολικά endpoints: 14** (10 από v5.5.0/v5.5.1 + 4 νέα) — **100% κάλυψη οικοσυστήματος TALOS**.
- **~200 νέες γραμμές κώδικα**.

### Σκεπτικό Σχεδιασμού
- **Γιατί inline λογική του `query_translator` αντί για import του `main()`;** Η `main()` του `query_translator.py` είναι πλήρως διαδραστική (χρησιμοποιεί `questionary` prompts). Το import θα μπλόκαρε επ' αόριστον. Το `main_api.py` αναπαράγει την κεντρική κλήση AI διατηρώντας το ίδιο prompt engineering.
- **Γιατί το `/api/v1/analysis/authors` χρησιμοποιεί DB aggregation αντί για το `author_profiler.py`;** Το `UnifiedProfiler.run()` κάνει 5+ εξωτερικές κλήσεις API ανά συγγραφέα (5-10 δευτερόλεπτα). Το SQL `GROUP BY` είναι άμεσο και εξυπηρετεί τέλεια το Recharts use case.
- **Γιατί το `/api/v1/db/recalculate-scores` χρησιμοποιεί BackgroundTasks;** Ο μαζικός επαναϋπολογισμός για 5,000+ εγγραφές μπορεί να πάρει αρκετά δευτερόλεπτα. Το `TaskStatus` κρατά το API responsive.

### Επαλήθευση
- `python -m py_compile src/api/main_api.py` ✅
- Συνολικά endpoints: **14** (100% κάλυψη)

### Ενημερωμένη Τεκμηρίωση
- `CHANGELOG_EN.md` + `CHANGELOG_GR.md` — αυτή η καταχώρηση
- `README.md` — έκδοση v5.5.2

## [v5.5.1] - 2026-07-22 — Frontend DX Endpoints (GWO History + Architecture Graph)

### Προστέθηκε
- **`src/api/main_api.py` v1.1 — Δύο νέα "Frontend DX" endpoints για React development:**
  - **`GET /api/v1/optimize/gwo/history`** — Επιστρέφει το ιστορικό βελτιστοποίησης GWO ως `List[dict]` για άμεση κατανάλωση από Recharts `<LineChart>`.
    - Διαβάζει πρώτα το `models/gwo_history.json`, με fallback στο `models/gwo_progress.json`.
    - Επιστρέφει `[]` αν δεν υπάρχει κανένα από τα δύο αρχεία (graceful degradation).
    - Χωρίς Pydantic model — raw JSON array για μέγιστη ευελιξία στο frontend.
  - **`GET /api/v1/graph/view`** — Σερβίρει το Alexandria Architecture Dependency Graph ως HTML σελίδα μέσω `FileResponse`.
    - Επιλύει το `templates/architecture_graph.html` από το project root.
    - Επιστρέφει 404 με χρήσιμο μήνυμα αν το αρχείο δεν υπάρχει.
    - Οι σχετικές αναφορές CSS/JS του HTML (`architecture_graph.css`, `architecture_graph.js`) επιλύονται σωστά επειδή το `FileResponse` σερβίρει το αρχείο από τον φάκελο `templates/`.
  - **StaticFiles mount** (`/static/templates`) προστέθηκε μέσω `app.mount()` ώστε η σελίδα του γράφου να μπορεί να φορτώνει τα assets της και μέσω απόλυτων διαδρομών `/static/templates/architecture_graph.css`.
  - **Νέα imports:** `HTMLResponse`, `FileResponse` από `fastapi.responses`, `StaticFiles` από `fastapi.staticfiles`.
- **Συνολικός νέος κώδικας:** ~45 γραμμές (2 endpoints + 1 mount + 2 γραμμές import).

### Σκεπτικό Σχεδιασμού
- **Γιατί `FileResponse` για τον γράφο;** Η σελίδα HTML χρησιμοποιεί σχετικές διαδρομές για CSS/JS. Το σερβίρισμα μέσω `FileResponse` από τον φάκελο `templates/` διατηρεί αυτές τις διαδρομές — ο browser τις επιλύει σχετικά με την προέλευση της σελίδας. Το `StaticFiles` mount στο `/static/templates` παρέχει εναλλακτική πρόσβαση μέσω απόλυτων διαδρομών.
- **Γιατί raw `List[dict]` για το ιστορικό GWO;** Το Recharts καταναλώνει εγγενώς arrays από objects. Το τύλιγμα των δεδομένων GWO σε Pydantic model θα προσέθετε ένα περιττό επίπεδο σειριοποίησης. Η απευθείας μεταβίβαση του JSON επιτρέπει στον React developer να τροφοδοτήσει την απόκριση κατευθείαν στο `<LineChart data={response} />`.

### Επαλήθευση
- `python -m py_compile src/api/main_api.py` ✅
- Συνολικά endpoints πλέον: **10** (8 αρχικά + 2 νέα)

### Ενημερωμένη Τεκμηρίωση
- `CHANGELOG_EN.md` + `CHANGELOG_GR.md` — αυτή η καταχώρηση
- `README.md` — έκδοση v5.5.1

## [v5.5.0] - 2026-07-22 — FastAPI REST API Façade & Διόρθωση Διαδρομής Βάσης

### Προστέθηκε
- **`src/api/main_api.py` v1.0 (ΝΕΟ, ~470 γραμμές) — FastAPI Façade Layer**
  - **8 REST endpoints** που τυλίγουν τις υπάρχουσες core συναρτήσεις χωρίς καμία επανάληψη λογικής:
    - `GET  /api/v1/health` — health check, στατιστικά βάσης, embedding model coverage
    - `GET  /api/v1/papers` — σελιδοποιημένη λίστα papers (page + page_size params)
    - `GET  /api/v1/papers/{id}` — πλήρεις λεπτομέρειες paper μέσω database ID
    - `POST /api/v1/search/semantic` — semantic search φυσικής γλώσσας (3-βήμα pipeline: embed query → cosine similarity → fetch papers)
    - `POST /api/v1/scrape/trigger` — έναρξη daily search και στις 14 πηγές (BackgroundTasks)
    - `POST /api/v1/optimize/gwo` — έναρξη GWO βελτιστοποίησης υπερπαραμέτρων (BackgroundTasks)
    - `GET  /api/v1/tasks/{id}` — έλεγχος κατάστασης background task
    - `GET  /api/v1/tasks` — λίστα όλων των background tasks (τα νεότερα πρώτα)
  - **Βασικές σχεδιαστικές αποφάσεις:**
    - Port 8000 — καμία σύγκρουση με Flask dashboard (5000), Flask service (5002), Streamlit (8501)
    - Όλα τα endpoints είναι synchronous — δεν χρειάζεται async def (οι core συναρτήσεις είναι blocking)
    - `BackgroundTasks` για χρονοβόρα scrape και GWO (όχι Celery)
    - Lazy singleton pattern για `DatabaseManager` και `AIManager`
    - `sys.exit()` monkey-patching για να μην σκοτώνεται ο server από το `daily_search.main()`
    - Pydantic v2 models με `extra="ignore"` για forward compatibility
    - GWO progress monitor μέσω daemon thread που διαβάζει `gwo_history.json` κάθε 2 δευτερόλεπτα
    - Πλήρες logging μέσω του `logging` module (όχι print)
  - **Pydantic models (10):** `PaperSummary`, `PaperDetail`, `PaginatedPapers`, `SemanticSearchRequest`, `SemanticSearchResponse`, `ScrapeRequest`, `GWORunRequest`, `GWOResult`, `TaskStatus`, `SystemHealth`
  - **Εντολή εκκίνησης:** `python -m uvicorn src.api.main_api:app --host 0.0.0.0 --port 8000`
  - **API docs** αυτόματα στο `http://localhost:8000/docs`

### Άλλαξε
- **`src/core/database_manager.py` v5.0 → v5.4.2 — Διόρθωση ανάλυσης διαδρομής βάσης (ΚΡΙΣΙΜΟ)**
  - **Bug:** Το `__init__` line 24 υπολόγιζε το `project_root` ως `os.path.join(os.path.dirname(__file__), '..')` = `src/` (ένα επίπεδο πάνω από `src/core/`), δημιουργώντας ένα άδειο `src/talos_research.db` αντί να συνδέεται στο γεμάτο `data/talos_research.db` με 5,366 papers.
  - **Fix:** Αντικαταστάθηκε με βρόχο αναζήτησης του `talos.py` (ίδιο pattern που χρησιμοποιεί κάθε άλλο `src/*.py` script) → επιλύει σωστά στο project root `f:\Project_TALOS\Project_Talos_v5.4.2_GitHub\`.
  - **Προτεραιότητα διαδρομών:**
    1. Ρητό `db_path` argument (αμετάβλητο)
    2. `data/talos_research.db` αν υπάρχει (**νέα κανονική τοποθεσία** — έχει προτεραιότητα)
    3. Ενεργό profile DB (`_profiles/<name>/talos_research.db`) αν έχει ρυθμιστεί (fallback)
    4. Δημιουργία `data/talos_research.db` αν δεν υπάρχει τίποτα (ήταν `src/talos_research.db`)
  - **Αποτέλεσμα:** Το `DatabaseManager()` πλέον συνδέεται στη γεμάτη βάση των 40 MB με 5,366 papers.

- **`src/api/talos_service_api.py`** — παραμένει ως ξεχωριστό Flask micro-service στην πόρτα 5002 (αμετάβλητο).

### Dependencies
- `fastapi`, `uvicorn[standard]`, `pydantic` (εγκατεστημένα, pinned στις τελευταίες εκδόσεις)

### Επαλήθευση
- `python -m py_compile src/api/main_api.py` ✅
- `python -m py_compile src/core/database_manager.py` ✅
- Module import test: 12 routes registered ✅
- `GET /api/v1/papers?page=1&page_size=50` → 200 OK ✅
- `DatabaseManager()` επιλύει σε `data/talos_research.db` (40 MB, 5,366 papers) ✅

### Ενημερωμένη Τεκμηρίωση
- `docs/PROJECT_MAP.md` + `docs/PROJECT_MAP_EN.md` — έκδοση v5.5.0, footer ενημερώθηκε
- `CHANGELOG_EN.md` + `CHANGELOG_GR.md` — αυτή η καταχώρηση
- `README.md` — έκδοση v5.5.0
- `ROADMAP.md` — v5.5.0 milestone completed

## [v5.4.1] - 2026-07-22 — Root Directory Cleanup

### ⚠️ BREAKING — Καθαρισμός ριζικού καταλόγου
Η τεκμηρίωση και τα dev scripts μεταφέρθηκαν από το root σε `docs/` και `tools/`. Ο ριζικός κατάλογος περιέχει πλέον μόνο standard GitHub/Enterprise αρχεία.

### Άλλαξε
- **`docs/` κατάλογος** για μόνιμη τεκμηρίωση: `PROJECT_MAP.md`, `PROJECT_MAP_EN.md`, `TECH_RADAR.md`.
- **`tools/` κατάλογος** για dev/utility scripts: `_bump.py`, `_git_status.ps1`, `_gui_runner.py`, `test_smoke.py`, `start_talos.bat`.
- **Όλες οι εσωτερικές διαδρομές διορθώθηκαν:**
  - `tools/test_smoke.py` — `os.chdir()` πηγαίνει ένα επίπεδο πάνω (στο root).
  - `tools/_gui_runner.py` — δυναμική εύρεση project root (βρίσκει το `talos.py`).
  - `tools/_bump.py` — δυναμικό root αντί για hardcoded `c:\Users\...`; `core/ai_manager.py` → `src/core/ai_manager.py`.
  - `tools/_git_status.ps1` — δυναμικό root.
  - `tools/start_talos.bat` — όλες οι διαδρομές με `..\` πρόθεμα; `scripts\` → `..\src\...`.
- **`.gitignore` v5.4.1** — κρίσιμη διόρθωση: `!docs/PROJECT_MAP*.md` negate patterns (το blanket `docs/` αγνοούσε τα project maps). Προστέθηκαν: `dump.json`, `logs/`, `data/`, `tools/_git_out.txt`.
- **`README.md`** — έκδοση v5.4.1, ενημερωμένες διαδρομές, citation IEEE/BibTeX.

### Επαλήθευση
- **`python -m py_compile tools/*.py`** → ✅ ΟΛΑ ΠΕΡΑΣΑΝ
- **`python tools/test_smoke.py`** → ✅ 78 αρχεία syntax-check, core imports OK, DB/AIManager OK

### Αρχεία που Άλλαξαν
| Αρχείο | Αλλαγή |
|------|--------|
| `docs/PROJECT_MAP.md` | Μεταφέρθηκε από root (no changes) |
| `docs/PROJECT_MAP_EN.md` | Μεταφέρθηκε από root (no changes) |
| `docs/TECH_RADAR.md` | Μεταφέρθηκε από root (no changes) |
| `tools/_bump.py` | Δυναμικό root path + src/ path fix |
| `tools/_git_status.ps1` | Δυναμικό root path |
| `tools/_gui_runner.py` | Δυναμική εύρεση project root |
| `tools/test_smoke.py` | `os.chdir(..)` + config path fix |
| `tools/start_talos.bat` | `..\` prefix + `scripts\` → `..\src\...` |
| `.gitignore` | `!docs/PROJECT_MAP*.md` negate patterns |
| `README.md` | v5.4.1, ενημερωμένες διαδρομές |

## [v5.4.0] - 2026-07-22 — `src/` Αναδιάρθρωση Πακέτων (DDD Migration)

### ⚠️ BREAKING — Πλήρης αναδιοργάνωση δομής καταλόγων
Όλα τα Python αρχεία (~55) μεταφέρθηκαν από την παλιά χαλαρή δομή `core/`, `scripts/`, `sources/` σε μια οργανωμένη δομή πακέτων `src/` Domain-Driven Design. **Κάθε δήλωση import σε κάθε αρχείο έχει ξαναγραφεί.**

### Νέα Δομή Καταλόγων
```
src/
├── core/          (5 αρχεία) — ai_manager, database_manager, hardware, notifier, profile_manager
├── ingestion/     (21 αρχεία) — 14 API sources + 7 ingestion pipelines
├── ai/
│   ├── drl/       (9 αρχεία) — DRL agent, networks, env, trainer, live agent, service
│   ├── optimizers/(2 αρχεία) — GWO optimizer + live dashboard
│   ├── embeddings/ (2 αρχεία) — embedding_generator, db_embedding_upgrade
│   └── llm/       (3 αρχεία) — query_translator (PYTHIA), model_manager, research_pivot
├── analysis/      (9 αρχεία) — citation_analyzer, author_profiler, knowledge_path_generator, κλπ.
├── utils/         (8 αρχεία) — db_stats, api_health_check, verify_dependency_map, κλπ.
└── api/           (1 αρχείο) — talos_service_api + άδειο __init__.py (FastAPI placeholder)
data/
├── talos_research.db
├── dump.json
└── pdfs/
```

### Άλλαξε
- **`talos.py` v5.4.1 — `run_script()` ανακατασκευάστηκε με `_SCRIPT_MAP` dict + `_resolve_script_path()`.**
  - Παλιές διαδρομές `os.path.join(project_root, 'scripts', name)` → `os.path.join(project_root, 'src', subdir, name)`.
  - Όλα τα `from core.*` → `from src.core.*`, `from scripts.profile_manager` → `from src.core.profile_manager`.
  - Έκδοση `v5.4.1`.
  - Hardcoded `scripts/` διαδρομές στο `system_health_menu()` (GWO dashboard, API diagnostics) → `_resolve_script_path()`.
  - Διαδρομή βάσης δεδομένων: `talos_research.db` → `data/talos_research.db`.
- **`app.py` v5.4.1 — `run()` ανακατασκευάστηκε με `_SCRIPT_DIRS` dict + `_resolve_script()`.**
  - `from core.database_manager` → `from src.core.database_manager`, `from core.ai_manager` → `from src.core.ai_manager`.
  - `from core.hardware` → `from src.core.hardware` (στο `advanced_settings()`).
  - GWO Live Dashboard: `os.path.join(..., "scripts", ...)` → `_resolve_script()`.
  - `sys.path.insert(0, ...)` αφαιρέθηκε.
  - Simple mode: εντολή εκπαίδευσης `python src/ai/drl/train_agent.py`.
- **`core/` → `src/core/` (+ `profile_manager.py` από `scripts/`):**
  - `scripts/profile_manager.py` → `src/core/profile_manager.py` — οι διαδρομές subprocess προς `query_translator.py` ενημερώθηκαν σε `src/ai/llm/query_translator.py`.
- **`core/` (DRL) → `src/ai/drl/`:**
  - `core/live_agent_sources.py` — **διόρθωση δυναμικού import:** `f"sources.{source_name}_source"` → `f"src.ingestion.{source_name}_source"`.
- **`sources/` (14 αρχεία) → `src/ingestion/`** + 7 ingestion scripts.
- **`scripts/` → διάφοροι υποκατάλογοι `src/`:**
  - `drl_trainer.py`, `train_agent.py`, `talos_live_agent.py`, `talos_service.py` → `src/ai/drl/`
  - `gwo_rl_optimizer.py`, `gwo_live_dashboard.py` → `src/ai/optimizers/`
  - `embedding_generator.py`, `db_embedding_upgrade.py` → `src/ai/embeddings/`
  - `query_translator.py`, `model_manager.py`, `research_pivot.py` → `src/ai/llm/`
  - `citation_analyzer.py`, `author_profiler.py`, κλπ. (9 αρχεία) → `src/analysis/`
  - `db_stats.py`, `api_health_check.py`, κλπ. (8 αρχεία) → `src/utils/`
  - `talos_service_api.py` → `src/api/`
- **`test_smoke.py` v5.4.1 — διαδρομές ενημερωμένες:** `core.database_manager` → `src.core.database_manager`, σάρωση `scripts/` → 9 υποκατάλογοι `src/`.
- **10 αρχεία `__init__.py`** δημιουργήθηκαν (ένα ανά πακέτο).
- **Παλιοί κατάλογοι διαγράφηκαν:** `core/`, `scripts/`, `sources/` (αναδρομικά).
- **Bulk migration script** (`_migrate_imports.py`, μίας χρήσης, διαγράφηκε μετά την εκτέλεση): 32 αρχεία μεταφέρθηκαν με regex import rewrites. Όλα τα `sys.path` hacks (~30 εμφανίσεις) αφαιρέθηκαν.

### Επαλήθευση
- **`python -m py_compile talos.py`** → ✅ ΠΕΡΑΣΕ
- **`python -m py_compile app.py`** → ✅ ΠΕΡΑΣΕ
- **Όλα τα 60+ αρχεία src/ ελέγχθηκαν** → ✅ ΠΕΡΑΣΑΝ
- **`python test_smoke.py`** → ✅ 79 αρχεία syntax-check, core imports OK, DB συνδεδεμένη, AIManager αρχικοποιημένος
- **Όλα τα `sys.path` hacks αφαιρέθηκαν** — το project χρησιμοποιεί πλέον αποκλειστικά proper package imports

### Ενημερωμένη Τεκμηρίωση
- `PROJECT_MAP.md` + `PROJECT_MAP_EN.md` — Ενότητες 2, 3, 7 ενημερώθηκαν με νέες διαδρομές και δομή.
- `CHANGELOG_EN.md` + `CHANGELOG_GR.md` — εγγραφή v5.4.1 ξαναγράφτηκε (src/ migration).

## [v5.3.7] - 2026-07-07 — GWO v2.0 Επανάληψη Βελτιστοποίησης Υπερπαραμέτρων

### Άλλαξε
- **`core/drl_agent.py` v2.3 — Ενημερωμένες GWO-optimized υπερπαράμετροι:**
  - `LR`: `4.735e-05` → `3.361e-05` (29% χαμηλότερο — πιο σταθερά βήματα gradient).
  - `GAMMA`: `0.575` → `0.6983` (21% υψηλότερο — ο agent κοιτάζει πιο μακριά στο μέλλον).
- **`scripts/drl_trainer.py` v1.4 — Ενημερωμένο GWO-optimized epsilon decay:**
  - `EPS_DECAY`: `0.9415` → `0.9202` (πιο αργή μείωση — ο agent εξερευνά περισσότερο).
- **Στατιστικά GWO run:** 80 επαναλήψεις, ~9.5 ώρες, καλύτερο fitness −2353.0 (μέσο reward 2353.0). Αποθηκεύτηκαν στα `models/gwo_best_params.json` και `models/gwo_history.json`.
- **`models/dddqn_trained.pth`** επανεκπαιδεύτηκε με τις νέες υπερπαραμέτρους (554.6 KB).
- **Live agent δοκιμάστηκε** — το μοντέλο φορτώνεται σωστά και με τις 14 πηγές και CUDA inference.

### Ενημερωμένη Τεκμηρίωση
- `PROJECT_MAP.md` + `PROJECT_MAP_EN.md` — Ενότητα 2.5 ενημερώθηκε με νέες τιμές, footer ημερομηνία/έκδοση v5.3.7.


## [v5.3.6 hotfix] - 2026-07-06 — Διόρθωση Crash στο Grey Literature Miner (Batch 3)

### Διορθώθηκε
- **`core/ai_manager.py` v3.8 — Απούσα `analyze_generic_text()` (ΚΡΙΣΙΜΟ).**
  - Η μέθοδος ήταν τεκμηριωμένη στο PROJECT_MAP.md και καλούνταν σε ΔΥΟ σημεία από το `grey_literature_miner.py` (query optimization + AIManager fallback), αλλά **δεν είχε υλοποιηθεί ποτέ** — και τα δύο paths κατέρρεαν με `AttributeError`, οπότε όταν το Gemini αποτύγχανε (π.χ. 429 εξάντληση credits) ο miner δεν παρήγαγε καμία αναφορά.
  - Υλοποιήθηκε ως thin wrapper: `return self._execute_request(full_prompt, model_type='pro', response_format='text')` — κληρονομεί circuit breaker, πλήρη αλυσίδα fallback (local → HF → Gemini → DeepSeek) και `last_provider_used` tracking.
- **`scripts/grey_literature_miner.py` v2.1:**
  - DuckDuckGo import: δοκιμάζει πρώτα το μετονομασμένο πακέτο `ddgs`, με fallback στο legacy `duckduckgo_search`.
  - Το ελλείπον `GEMINI_API_KEY` δεν είναι πλέον fatal — το Search Grounding παρακάμπτεται με [WARN] και η αναφορά παράγεται μέσω της αλυσίδας AIManager (π.χ. τοπικό Ollama) με grounding από τα αποτελέσματα DuckDuckGo.

### Δεν είναι bug (ενημερωτικό)
- Το `429 RESOURCE_EXHAUSTED: prepayment credits depleted` του Gemini στα logs είναι κατάσταση χρέωσης, όχι σφάλμα κώδικα — αναπλήρωση credits στο ai.studio επαναφέρει το Search Grounding· ο miner πλέον υποβαθμίζεται ομαλά χωρίς αυτό.


## [v5.3.6] - 2026-07-06 — Η Ενημέρωση "TUI/CLI Hardening" (Batch 2 Audit Fixes)

Αυτή η έκδοση υλοποιεί το **Batch 2** του code audit: διορθώσεις ΜΟΝΟ στο interface layer του TUI/CLI. **Καμία αλλαγή σε DRL λογική, state representations, rewards, environment steps ή GWO μαθηματικά** — τα `core/drl_agent.py`, `core/talos_env.py` και `scripts/gwo_rl_optimizer.py` δεν αγγίχτηκαν.

### Διορθώθηκε
- **`talos.py` v5.3.6 — Νεκρή επιλογή μενού + Ctrl+C robustness.**
  - Το System Diagnostics είχε **δύο επιλογές με αρίθμηση "6."** — το `choice.startswith("6.")` ταίριαζε πάντα την πρώτη, καθιστώντας το "Baseline Report (Standard)" απρόσιτο dead code. Το μενού αναριθμήθηκε 1-10 (7=Standard, 8=Academic, 9=DRL Status, 10=Docs Generator).
  - Νέα helper `safe_pause(msg)`: Ctrl+C σε οποιοδήποτε "Press Enter" prompt επιστρέφει ήσυχα στο μενού αντί να τερματίζει την εφαρμογή. Αντικαθιστά και τα 5 γυμνά `input()`.
  - Η `safe_select()` πιάνει πλέον `KeyboardInterrupt` (και στο fallback `unsafe_ask`) και επιστρέφει `None` (όλα τα μενού το χειρίζονται ως "Back").
  - 4 γυμνά `except:` → `except Exception:` — το Ctrl+C δεν "καταπίνεται" πλέον σιωπηλά.
  - `check_first_run()`: `None` από το confirm (Ctrl+C) δεν εμφανίζει πια παραπλανητικό "setup complete".
  - Version string κεντρικά στη σταθερά `TALOS_VERSION = "v5.3.6"` (το header είχε hardcoded stale "v5.3.0").
  - Top-level guard με `sys.exit(0)` στο Ctrl+C.
- **`scripts/drl_trainer.py` v1.3 — Graceful interrupt με partial save.**
  - Ctrl+C στη μέση της εκπαίδευσης πετούσε traceback και **έχανε όλα τα βάρη**. Ο βρόχος επεισοδίων τυλίγεται πλέον σε `try/except KeyboardInterrupt`: το μερικό μοντέλο αποθηκεύεται στο **`models/dddqn_partial.pth`** (σκόπιμα ΟΧΙ στο `dddqn_trained.pth`, ώστε να μην καταστραφεί ποτέ πλήρως εκπαιδευμένο μοντέλο), τυπώνεται καθαρή σύνοψη και exit code 0. Το σώμα του βρόχου είναι byte-identical — μηδενικές αλλαγές στα μαθηματικά.
  - Νέος single-line `\r` progress ticker ανάμεσα στα 50-episode summaries (χωρίς εξωτερικά deps, ≤40 chars).
  - Ctrl+C guards στο interactive prompt και σε top level.
- **`scripts/talos_live_agent.py` v3.2 — argparse + startup guard.**
  - Το `argparse` αντικαθιστά το ad-hoc `"--verbose" in sys.argv` — τα `--verbose` και `--help` δουλεύουν σωστά.
  - Νέος formatted key:value startup summary πίνακας.
  - Top-level `KeyboardInterrupt` guard: Ctrl+C κατά το startup (config load, `AIManager` init, model load) τερματίζει καθαρά με exit code 0.

### Σημειώσεις audit (χωρίς ενέργεια)
- Logger/print isolation: τα entry points είναι print-only — δεν υπάρχει διαδρομή αλλοίωσης TUI/log.
- Console layout: οι 65-char γραμμές και το Rich table είναι ασφαλή στο ελάχιστο 80 στηλών.


## [v5.3.5] - 2026-07-06 — Η Ενημέρωση "Επιστημονική Ακεραιότητα DRL/GWO" (Batch 1 Audit Fixes)

Αυτή η έκδοση υλοποιεί το **Batch 1** του pre-ICBE code audit: πέντε ΚΡΙΣΙΜΕΣ (TIER 1) διορθώσεις στα υποσυστήματα DRL και GWO. Τα bugs αυτά ακύρωναν σιωπηλά τις αναφερόμενες "GWO-optimized" υπερπαραμέτρους. **⚠️ BREAKING (σε επίπεδο αποτελεσμάτων):** Το GWO πρέπει να ξανατρέξει και το DDDQN να επανεκπαιδευτεί — τα προηγούμενα `models/gwo_best_params.json` και `models/dddqn_trained.pth` προέκυψαν από optimizer που δεν εκπαίδευε ποτέ τον agent.

### Διορθώθηκε
- **`scripts/gwo_rl_optimizer.py` v2.0 — Το GWO fitness ήταν καθαρός θόρυβος (ΚΡΙΣΙΜΟ).**
  - Η `calculate_fitness()` είχε hardcoded `agent.act(obs, eps=1.0)` (100% τυχαίες ενέργειες), δεν καλούσε ποτέ `agent.memory.store()` ή `agent.learn()`, και το decayed `epsilon` δεν χρησιμοποιούνταν ποτέ. Αποτέλεσμα: τα `lr`, `gamma`, `eps_decay` δεν είχαν καμία αιτιώδη επίδραση στο fitness — το GWO βελτιστοποιούσε τη διακύμανση ενός random walk.
  - v2.0: δύο φάσεις — **Φάση 1 (εκπαίδευση):** `memory.store(Transition(...))` + `agent.learn()` ανά βήμα, `act(obs, eps=epsilon)` με decay ανά επεισόδιο κατά το υποψήφιο `eps_decay`· **Φάση 2 (greedy αξιολόγηση):** νέα σταθερά `EVAL_EPISODES=5`, rollouts με `eps=0.0` χωρίς μάθηση· fitness = −(μέσο eval reward).
  - `update_wolf_position()`: πλέον canonical GWO (Mirjalili 2014, Εξ. 3.5–3.7) — fresh `r1, r2` (άρα fresh `A`, `C`) ανεξάρτητα για κάθε alpha/beta/delta όρο. Πριν, κοινά `A, C` συσχέτιζαν τους τρεις όρους έλξης, μειώνοντας την ποικιλομορφία εξερεύνησης.
  - `find_best_three_wolves()` επιστρέφει πλέον και το cached `fitness_values` array· η `_build_history_entry(..., fitness_values)` το χρησιμοποιεί αντί να ξανα-καλεί `calculate_fitness()` ανά λύκο — εξάλειψη 2× runtime κόστους και ασυνέπειας στο logging (τα στοχαστικά re-evaluations κατέγραφαν τιμές διαφορετικές από αυτές της κατάταξης).
- **`core/talos_env.py` v3.1 — Time-limit termination bug (ΚΡΙΣΙΜΟ).**
  - Το `step()` επέστρεφε `terminated=True` στο cutoff των 200 βημάτων. Κατά τη σημασιολογία του Gymnasium, το time limit είναι **truncation**, όχι terminal state· η αποθήκευση `done=True` μηδένιζε το bootstrap `(1−done)·γ·Q'`, μεροληπτώντας τα Q-values κοντά στο τέλος επεισοδίου. Τώρα: `terminated=False, truncated=(current_step >= 200)`.
- **`scripts/drl_trainer.py` v1.2 — Fatal `NameError` σε interactive mode (ΚΡΙΣΙΜΟ).**
  - Τέσσερις αναφορές `args.episodes` κατέρρεαν όποτε το script έτρεχε χωρίς `--episodes` (questionary mode), γιατί το `args` οριζόταν μόνο στο CLI branch. Όλες αντικαταστάθηκαν με τη τοπική μεταβλητή `episodes`. Σχόλιο στο replay storage τεκμηριώνει ότι αποθηκεύεται `done=terminated` (όχι `truncated`).
- **`core/live_agent_orchestrator.py` v1.1 — Train/inference distribution mismatch (ΚΡΙΣΙΜΟ).**
  - `LOW_SCORE_MAX` 20 → 10: το training env κανονικοποιεί τα streaks με /10, ενώ το live inference διαιρούσε με 20 — σιωπηλή συμπίεση 2× των χαρακτηριστικών κατάστασης (domain shift). Fix στην πλευρά inference, χωρίς retraining για αυτό το item.
- **`core/ai_manager.py` v3.7 + `core/live_agent_orchestrator.py` v1.1 — Provider attribution bug (ΚΡΙΣΙΜΟ).**
  - Η `evaluate_paper()` πίστωνε πάντα το `provider_call_counts["gemini"]` ανεξάρτητα από τον provider που εξυπηρέτησε το request (fallback σε DeepSeek/HF/Ollama), αλλοιώνοντας το provider-aware τμήμα του state vector του DRL agent. Ο `AIManager` εκθέτει πλέον `last_provider_used` (ορίζεται σε κάθε επιτυχημένο `_execute_request()`) και ο orchestrator πιστώνει τον σωστό provider.

### Migration
1. Ξανατρέξτε GWO: `python scripts/gwo_rl_optimizer.py --wolves 15 --iters 50`
2. Ενημερώστε τα `LR`/`GAMMA` στο `core/drl_agent.py` και το `EPS_DECAY` στο `scripts/drl_trainer.py` από το νέο `models/gwo_best_params.json`.
3. Επανεκπαίδευση: `python scripts/drl_trainer.py --episodes 700`
4. Αρχειοθετήστε τα παλιά model artifacts — μην τα επαναχρησιμοποιήσετε σε δημοσιευμένα αποτελέσματα.


## [v5.3.4] - 2026-07-05 — Η Ενημέρωση "Περιγραφικά Ονόματα Modules"

Αυτή η μικρή έκδοση αφαιρεί όλα τα μυθολογικά κωδικά ονόματα (APOLLO, CHIRON, ORPHEUS, PYTHIA, NAFSIKA, HERMES, ORACLE, ARGUS, ALEXANDRIA) από το codebase του TALOS, αντικαθιστώντας τα με περιγραφικούς, ακαδημαϊκά κατάλληλους τίτλους. Το project παρουσιάζεται πλέον ως σοβαρή ακαδημαϊκή πλατφόρμα και όχι ως εργαλείο με μυθολογικό θέμα.

### Άλλαξε
- **`.clinerules`:** Προστέθηκε υποχρεωτικός κανόνας συγχρονισμού του `PROJECT_MAP_EN.md` — ο αγγλικός χάρτης πρέπει να ενημερώνεται μαζί με τον ελληνικό master στην ίδια σύνοδο αλλαγών.
- **`PROJECT_MAP.md` & `PROJECT_MAP_EN.md`:** Η Ενότητα 8 μετονομάστηκε από "Greek Code Name Glossary" σε "Module Descriptions" με 9 περιγραφικές καταχωρήσεις (TALOS, Query Translator, Knowledge Path Generator, Citation Network Analyzer, Metadata Enricher, Grey Literature Miner, Interactive Dashboard, PDF Downloader, Autonomous Research Service).
- **`app.py`:** Αφαιρέθηκαν τα επιθήματα "(CHIRON)", "(ORPHEUS)" από τα Analysis dropdown labels. Άλλαξε το "APOLLO Metadata Enrichment" → "Metadata Enrichment", το κλειδί MAP "APOLLO" → "Metadata", το "reconfigure PYTHIA" → "reconfigure the Query Translator".
- **`README.md`:** Ενημερώθηκε το tagline από "Light-Only Academic Theme" σε "Descriptive Module Names & University-Ready Documentation".
- **`ROADMAP.md`:** Η επικεφαλίδα της Ενότητας 7 "ALEXANDRIA Ecosystem" → "Distributed Ecosystem". Αναβάθμιση τρέχουσας έκδοσης.

### Σκεπτικό Σχεδιασμού
- **Γιατί αφαιρέθηκαν τα μυθολογικά ονόματα:** Το codebase είναι ένα εργαλείο διδακτορικής έρευνας που προορίζεται για ακαδημαϊκή δημοσίευση και υποστήριξη διατριβής. Ονόματα όπως "CHIRON", "ORPHEUS" και "APOLLO" υπονομεύουν την επαγγελματική αξιοπιστία της εργασίας. Οι περιγραφικοί τίτλοι (π.χ., "Knowledge Path Generator") είναι αυτο-επεξηγηματικοί και κατάλληλοι για άρθρα σε περιοδικά, παρουσιάσεις σε συνέδρια και κεφάλαια μεθοδολογίας διατριβής. Μόνο το "TALOS" διατηρείται — είναι το όνομα του project και το δικό του ακρωνύμιο (Tactical Agentic Literature Orchestration System).

### Αρχεία που Άλλαξαν
| Αρχείο | Αλλαγή |
|--------|--------|
| `.clinerules` | +κανόνας συγχρονισμού PROJECT_MAP_EN.md, αφαίρεση μυθολογικών ονομάτων |
| `PROJECT_MAP.md` | Ενότητα 8 → Module Descriptions, footer v5.3.4 |
| `PROJECT_MAP_EN.md` | Ενότητα 8 → Module Descriptions, footer v5.3.4 |
| `app.py` | Αφαίρεση μυθολογικών επιθημάτων από όλα τα UI labels + εσωτερικά κλειδιά |
| `README.md` | Ενημερωμένο tagline |
| `ROADMAP.md` | ALEXANDRIA → Distributed Ecosystem, version bump |

### Migration / Breaking
- **Καμία breaking αλλαγή** — πρόκειται μόνο για ενημέρωση τεκμηρίωσης και ετικετών UI.
- **Καμία αλλαγή στη συμπεριφορά κώδικα** — όλα τα scripts παραμένουν λειτουργικά πανομοιότυπα.

---

## [v5.3.3] - 2026-07-05 — Η Ενημέρωση "Light-Only Θέμα & Καθολική Τεκμηρίωση"

Αυτή η μικρή έκδοση αφαιρεί το χαλασμένο dark theme από το Streamlit GUI (δεν λειτουργούσε σωστά, δεν άξιζε συντήρηση) και αναβαθμίζει τον κανόνα Progressive Documentation Rule των .clinerules από μόνο `.py` αρχεία σε ΟΛΟΥΣ τους τύπους αρχείων.

### Άλλαξε
- **`app.py` v5.3.0 → v5.3.3 (~940 γραμμές):**
  - Αφαιρέθηκε το `dark_mode` από το session state initialization (ήταν `st.session_state.dark_mode = True`).
  - `render_css()`: Αντικαταστάθηκε η ternary λογική `dark_mode` με hardcoded light-only CSS μεταβλητές (bg, card_bg, border, text, accent, muted, sidebar, header). Τέλος η δυναμική εναλλαγή θέματος.
  - Sidebar: Αφαιρέθηκε το theme badge (`col2` με Dark/Light ετικέτα) και το dark toggle button (`st.toggle("🌙 Dark", ...)`). Το Advanced Mode toggle είναι πλέον standalone full-width button (`st.toggle("🔧 Advanced Mode", ...)`).
  - Docstring: Ενημερώθηκε για να αντικατοπτρίζει τον σχεδιασμό single-theme.
  - THEME MANAGEMENT ενότητα: Ενημερώθηκε το σχόλιο που εξηγεί το σκεπτικό αφαίρεσης του dark mode.
- **`templates/gui_theme.css` v5.2.1 → v5.3.3:**
  - Σχόλιο επικεφαλίδας: Από "Dark/Light dual-mode" σε "Light-only theme".
  - Αφαιρέθηκε ο κανόνας `:root[data-theme="dark"]` CSS (12 γραμμές dark mode μεταβλητών).
  - Αφαιρέθηκε ο κανόνας `:root[data-theme="light"]` CSS (4 γραμμές στατικών light μεταβλητών — πλέον γίνονται inject δυναμικά από το `app.py:render_css()`).
  - Αντικαταστάθηκε με σχόλιο που εξηγεί ότι οι CSS μεταβλητές γίνονται inject στο runtime.
- **`templates/gui_strings.py` v5.2.1 → v5.3.3:**
  - Αφαιρέθηκε το translation string `"dark_toggle"` (EN: "Dark Theme", GR: "Σκοτεινό Θέμα").
  - Ενημερώθηκε το string `"footer"` από v5.2.1 → v5.3.3.
  - Docstring: Σημειώθηκε η κατάργηση του dark theme.
- **`.clinerules` v5.0.0 → v5.3.3:**
  - Προστέθηκε νέος CRITICAL κανόνας: "Progressive Documentation Rule — ALL File Types" (μετά το CRITICAL: Compile Check section).
  - Ο κανόνας ισχύει πλέον για `.py`, `.css`, `.md`, `.bat`, `.json`, `.html`, `.js`, `.yml`, `.toml`, `.txt` — όχι μόνο για `.py` αρχεία.
  - Ο παλιός "Progressive Documentation Rule (v5.0.0)" μαρκαρίστηκε ως SUPERSEDED, διατηρείται για ιστορική αναφορά.
  - Περιλαμβάνει format για module docstring και συμβάσεις για inline σχόλια.
- **`PROJECT_MAP.md` v5.3.2 → v5.3.3:**
  - Ενημερώθηκε η έκδοση σε header και footer.
  - Προστέθηκαν οι ενότητες 2.8 (`gui_theme.css`) και 2.9 (`gui_strings.py`) στα Core Modules.
  - Ενημερώθηκε η περιγραφή της ενότητας 3.2 (`app.py`) για να σημειώνει το light-only theme.

### Αφαιρέθηκε
- **Το dark theme εξ ολοκλήρου** — η μεταβλητή session state `dark_mode`, το sidebar theme toggle button, το theme badge, η δυναμική ternary λογική CSS στο `render_css()`, και οι στατικοί dark/light CSS κανόνες `:root` στο `gui_theme.css`. Το GUI χρησιμοποιεί πλέον μία ενιαία light-only ακαδημαϊκή blue/teal παλέτα.

### Σκεπτικό Σχεδιασμού
- **Γιατί αφαιρέθηκε το dark mode:** Το Streamlit dark theme toggle δεν λειτουργούσε σωστά — το Streamlit διαβάζει το `config.toml` μόνο κατά την εκκίνηση, όχι στο runtime. Το workaround με CSS injection παρήγαγε ασυνεπή αποτελέσματα (π.χ. το sidebar δεν άλλαζε, τα input fields διατηρούσαν light φόντο). Η συντήρηση δύο μονοπατιών θέματος διπλασίαζε την πολυπλοκότητα του CSS για οριακό όφελος. Η light-only ακαδημαϊκή παλέτα είναι πιο καθαρή, πιο επαγγελματική και εξαλείφει ώρες debugging.
- **Γιατί καθολικός κανόνας τεκμηρίωσης:** Προηγουμένως, ο Progressive Documentation Rule κάλυπτε μόνο `.py` αρχεία. Ωστόσο, CSS, Markdown, batch scripts, JSON configs και HTML templates επωφελούνται όλα από inline τεκμηρίωση. Η επέκταση του κανόνα σε ΟΛΟΥΣ τους τύπους αρχείων εξασφαλίζει σταθερή ποιότητα τεκμηρίωσης σε ολόκληρο το codebase.

### Αρχεία που Άλλαξαν
| Αρχείο | Αλλαγή |
|--------|--------|
| `app.py` | v5.3.0→v5.3.3 — αφαίρεση dark_mode, light-only CSS, καθαρισμός sidebar |
| `templates/gui_theme.css` | v5.2.1→v5.3.3 — αφαίρεση dark/light :root κανόνων |
| `templates/gui_strings.py` | v5.2.1→v5.3.3 — αφαίρεση dark_toggle string |
| `.clinerules` | v5.0.0→v5.3.3 — καθολικός κανόνας τεκμηρίωσης για όλους τους τύπους αρχείων |
| `PROJECT_MAP.md` | v5.3.2→v5.3.3 — νέες ενότητες 2.8, 2.9 |

### Migration / Breaking
- **⚠️ MINOR BREAKING:** Κάθε κώδικας που αναφέρεται εξωτερικά στο `st.session_state.dark_mode` θα εμφανίσει `AttributeError`. Η μεταβλητή έχει αφαιρεθεί εντελώς.
- **Καμία αλλαγή στη βάση δεδομένων** — πρόκειται για ενημέρωση μόνο του UI.
- **Καμία αλλαγή στο config.json** — το θέμα είναι πλέον hardcoded.

---

## [v5.3.2] - 2026-07-05 — Η Ενημέρωση "Pluggable Network Architecture"

Αυτή η μικρή έκδοση εξάγει το νευρωνικό δίκτυο του DRL σε αποκλειστικό pluggable module, επιτρέποντας μελλοντική εναλλαγή αρχιτεκτονικών (Transformer, xLSTM) χωρίς να πειραχτεί ο πυρήνας του agent.

### Προστέθηκε
- **`core/drl_networks.py` v1.0 (~100 γραμμές, 1 κλάση):** Αποκλειστικό module νευρωνικών δικτύων.
  - **`DuelingLSTM`** — 3-layer LSTM (128→64→32) με LayerNorm + dueling heads (V + A). Ίδια αρχιτεκτονική με πριν, τώρα σε δικό της αρχείο.
  - Σχεδιασμένο για μελλοντικές αρχιτεκτονικές μέσω κοινού `(input_dim, output_dim)` interface.

### Άλλαξε
- **`core/drl_agent.py` v2.1 → v2.2:**
  - Ο `__init__` δέχεται προαιρετική παράμετρο `network_class` (default: `DuelingLSTM`).
  - Το `save()` αποθηκεύει το όνομα της κλάσης (`network_class`) στα metadata του μοντέλου.
  - Το `load()` επιλύει την κλάση δικτύου από τα αποθηκευμένα metadata, με fallback στο `DuelingLSTM` για παλιά μοντέλα.
  - Πλήρως backward compatible — τα παλιά μοντέλα φορτώνονται κανονικά.
- **`PROJECT_MAP.md`:** Προστέθηκε Section 2.4 για το `drl_networks.py`, ενημερώθηκε το 2.5 για το `drl_agent.py` v2.2.

### Αρχεία που Άλλαξαν
| Αρχείο | Αλλαγή |
|------|--------|
| `core/drl_networks.py` | **ΝΕΟ** — Pluggable network module (100 γραμμές) |
| `core/drl_agent.py` | v2.1→v2.2 — network_class param, save/load class name |
| `PROJECT_MAP.md` | Nέο section 2.4, ενημερωμένο 2.5 |

## [v5.3.1] - 2026-07-05 — Η Ενημέρωση "DRL Live Agent & Provider-Aware Orchestration"

Αυτή η έκδοση προσφέρει εκτεταμένη αναβάθμιση του Deep Reinforcement Learning συστήματος του TALOS. Ο Live DRL Agent αναδιοργανώθηκε σε επαναχρησιμοποιήσιμα `core/` modules με νέο **provider-aware observation space** (παρακολούθηση ορίων Gemini/DeepSeek/HuggingFace/Local), **cooldown μηχανισμό** για αποφυγή deterministic loops, **GWO-βελτιστοποιημένες υπερπαραμέτρους**, και **tier-based Gemini rate limits** στο `config.json`. O DRL agent πλέον ενορχηστρώνει και τις 14 ακαδημαϊκές πηγές API.

### Προστέθηκε
- **`core/live_agent_sources.py` v1.0 (~40 γραμμές, 2 συναρτήσεις):** Module ανακάλυψης πηγών — δυναμικό import με auto-detection (σκανάρει το module για `*Source` κλάσεις — διορθώνει τα broken class names για DBLP, IEEE, OpenAlex, OSTI, PLOS, PubMed, Springer, OpenArchives). Dense action mapping.
- **`core/live_agent_orchestrator.py` v1.0 (~420 γραμμές, 6 συναρτήσεις):** Core orchestration loop — state calculation, action selection, API fetch, AI evaluation, reward, provider tracking. **v3.1 Cooldown:** negative-reward actions → 5-step lockout, random free action override. epsilon=0.05. ASCII-only ακαδημαϊκό output.
- **Tier-based Gemini configuration στο `config.json`:** `"gemini_tier": "free"` (free/tier1/tier2), `"provider_limits"` (RPM/RPD/TPM για 4 providers), 3 νέα query keys (`semantic_scholar_query`, `core_query`, `scigov_query`).

### Διορθώθηκε
- **Sparse action mapping bug:** ~73% πιθανότητα άκυρου action. Fix: Dense mapping.
- **Model dimension mismatch crash:** `load_state_dict()` πριν τον έλεγχο διαστάσεων. Fix: Pre-check + `weights_only=True`.
- **Hour normalization inconsistency:** `/23.0` vs `/24.0`. Fix: `/24.0` παντού.
- **8 σπασμένες κλάσεις πηγών:** Το `.capitalize()` guessing απέτυχε. Fix: Auto-detection στο `live_agent_sources.import_source_class()`.
- **Hardcoded local model verification:** `_ensure_local_model()` έψαχνε πάντα `gemma3:12b`. Fix: Διαβάζει `LOCAL_MODEL_NAME` από `.env`.
- **Save path mismatch:** `talos_drl.pth` vs `dddqn_trained.pth`. Fix: Ενοποιήθηκε.

### Άλλαξε
- **`core/drl_agent.py` v2.0 → v2.1:** GWO υπερπαράμετροι — `LR=4.735e-05`, `GAMMA=0.575`. `load()` pre-check, `weights_only=True`.
- **`core/talos_env.py` v2.0 → v3.0:** Hour fix, provider-aware state (21-dim obs με 4 provider ratios).
- **`scripts/drl_trainer.py` v1.0 → v1.1:** `EPS_DECAY=0.9415` (GWO), save path fix.
- **`scripts/talos_live_agent.py` v2.0 → v3.1:** Από 530 γραμμές monolith σε 110 γραμμές thin entry. Όλα τα emoji αντικαταστάθηκαν με ASCII tags.
- **`config.json`:** Προστέθηκαν `gemini_tier`, `provider_limits`, 3 νέα query keys.
- **`PROJECT_MAP.md`:** v5.3.0→v5.3.1. Core modules: 3→7. Nέα sections. 59→61 αρχεία.

### Αποτελέσματα Εκπαίδευσης (v5.3.1)
| Μετρική | v5.2.0 (3 πηγές) | v5.3.1 (14 πηγές) |
|---|---|---|
| State dimension | 6 | 21 |
| Action dimension | 4 | 15 |
| Πηγές | 3 | 14 |
| Μέσο reward επεισοδίου | 1695.8 | 2220.5 |
| Βελτίωση GWO | — | +30.9% |
| Provider tracking | Κανένα | 4 provider ratios |

### Αρχεία που Άλλαξαν
| Αρχείο | Αλλαγή |
|------|--------|
| `core/live_agent_sources.py` | **ΝΕΟ** — Source discovery module |
| `core/live_agent_orchestrator.py` | **ΝΕΟ** — Main loop + cooldown |
| `core/drl_agent.py` | v2.0→v2.1 — GWO params, load() pre-check |
| `core/talos_env.py` | v2.0→v3.0 — Provider-aware state |
| `core/ai_manager.py` | `_ensure_local_model()` fix |
| `scripts/talos_live_agent.py` | v2.0→v3.1 — Thin entry, cooldown, ASCII |
| `scripts/drl_trainer.py` | v1.0→v1.1 — GWO EPS_DECAY |
| `config.json` | Προστέθηκαν gemini_tier, provider_limits, 3 queries |
| `PROJECT_MAP.md` | v5.3.0→v5.3.1 — 7 core modules, νέο config schema |
| `models/dddqn_trained.pth` | **ΕΠΑΝΕΚΠΑΙΔΕΥΣΗ** — 14 πηγές, dims=(21,15) |

## [v5.3.0] - 2026-07-04 — Η Ενημέρωση "Multi-Language Documentation Builder"

Αυτή η έκδοση εισάγει το `scripts/generate_docs.py` v2.0, μια **πλήρως διαδραστική, 18-γλωσση γεννήτρια τεκμηρίωσης για 93+ αρχεία** που χρησιμοποιεί τοπικό Ollama instance. Πλήρης επανεγγραφή από την v1.0 με υποστήριξη για όλα τα αρχεία του project (όχι μόνο `.py`), language-agnostic prompt system, διαδραστική επιλογή φακέλων μέσω checkbox, token estimation, και ενσωμάτωση σε GUI και TUI.

### Προστέθηκε
- **`scripts/generate_docs.py` v2.0 (~350 γραμμές, 7 συναρτήσεις):** Πλήρης επανεγγραφή — τεκμηριώνει πλέον **ΟΛΟΚΛΗΡΟ το codebase (93+ αρχεία)** συμπεριλαμβανομένων `.py`, `.html`, `.css`, `.js`, `.json`, Dockerfile, `.bat`, `.ps1`, `.cff`, `.clinerules` και άλλων.
  - **`check_ollama(url) -> bool`:** Health check κατά την εκκίνηση — επαληθεύει ότι το Ollama τρέχει. Αν είναι offline, εμφανίζει σαφές μήνυμα σφάλματος και τερματίζει. **Ποτέ δεν κάνει fallback σε cloud APIs.**
  - **`load_configuration() -> Dict[str, str]`:** Διαβάζει το όνομα μοντέλου με προτεραιότητα: `OLLAMA_MODEL` → `LOCAL_MODEL_NAME` → `gemma4` fallback. Διαβάζει επίσης το `OLLAMA_HOST` για custom endpoints.
  - **`get_code_files(selected_dirs) -> List[str]`:** Συλλέγει αναδρομικά ΟΛΑ τα code/text files από 6 ομάδες φακέλων: `core/` (7 αρχεία), `scripts/` (35 αρχεία), `sources/` (14 αρχεία), `templates/` (7 αρχεία — HTML/CSS/JS/JSON), `reference_code/` (17 αρχεία), και Root files (~9 αρχεία). Εξαιρεί binary, cache, data, logs, models.
  - **`estimate_file_info(file_paths) -> Dict`:** Μετράει συνολικά αρχεία, γραμμές, και bytes πριν ξεκινήσει η παραγωγή — εμφανίζεται στο summary.
  - **`generate_documentation(source_code, file_path, model, ollama_url, language_keyword) -> Optional[str]`:** Δυναμικό multi-language prompt — στέλνει περιεχόμενο αρχείου + οδηγία γλώσσας στο Ollama `/api/generate`. Υποστηρίζει 18 γλώσσες μέσω keyword mapping (GREEK, ENGLISH, CHINESE, HINDI, κ.λπ.).
  - **`save_documentation(file_path, content, output_dir, lang_code) -> None`:** Δημιουργεί δομή `docs/{lang_code}/`. Ονόματα αρχείων από σχετικές διαδρομές: `core_ai_manager_doc.md`, `templates_dashboard_doc.md`, `Dockerfile_doc.md`.
  - **`main() -> None`:** 7-βήμα διαδραστική ροή: (1) Ollama health check, (2) questionary select για γλώσσα (18 επιλογές), (3) questionary checkbox για επιλογή φακέλων, (4) συλλογή αρχείων + estimate, (5) confirmation με summary, (6) tqdm progress bar, (7) τελική αναφορά.
- **18 υποστηριζόμενες γλώσσες:** Ελληνικά, English, 中文 (Mandarin), हिन्दी (Hindi), Español, العربية (Arabic), Français, বাংলা (Bengali), Русский, Português, اردو (Urdu), Bahasa Indonesia, Deutsch, 日本語, Italiano, 한국어 (Korean), Türkçe, فارسی (Persian/Farsi).
- **GUI integration (`app.py` v5.3.0):** Η σελίδα System Diagnostics περιλαμβάνει πλέον:
  - Language dropdown με και τις 18 γλώσσες
  - 6 checkboxes για επιλογή φακέλων (core, scripts, sources, templates, reference_code, root)
  - Κουμπί "Generate Codebase Documentation" που εκτελεί το `generate_docs.py`
- **TUI integration (`talos.py` v5.3.0):** Το μενού System Diagnostics περιλαμβάνει πλέον την Επιλογή 8: "Generate Codebase Docs (18 Languages, LOCAL Only)".
- **Νέο `.env` key:** `OLLAMA_MODEL` — προαιρετικό override για το μοντέλο παραγωγής τεκμηρίωσης (πέφτει σε `LOCAL_MODEL_NAME` και μετά `gemma4`).
- **Νέα δομή εξόδου:** `docs/{lang_code}/` — multi-language directory tree.
- **Token estimator:** Πριν ξεκινήσει η παραγωγή, δείχνει συνολικά αρχεία, γραμμές, εκτιμώμενο χρόνο, και επιβεβαιώνει "💰 Κόστος: €0.00 (τοπικό Ollama)".

### Άλλαξε
- **`PROJECT_MAP.md`:** Αναβάθμιση v5.2.1→v5.3.0. Ενημερώθηκε η καταχώρηση Section 4.7 `generate_docs.py` από v1.0 → v2.0 (7 συναρτήσεις, 18 γλώσσες, 93+ αρχεία). Ενημερώθηκε το διάγραμμα αρχιτεκτονικής και το dependency graph. Version strings παντού.
- **`example.env`:** Προστέθηκε το key `OLLAMA_MODEL = ""` με σχόλιο.
- **`ROADMAP.md`:** Το milestone v5.3.0 σημειώθηκε COMPLETED ✅ με αναλυτικό πίνακα υλοποίησης.
- **`README.md`:** v5.2.0→v5.3.0, δίγλωσσες ενότητες EN+GR σε όλο το κείμενο, νέα ενότητα "Documentation Builder".

### Σχεδιαστική Λογική
- **Γιατί 18 γλώσσες;** Η διδακτορική διατριβή είναι δίγλωσση (Ελληνικά/Αγγλικά) και ο ερευνητής θέλει να παρουσιάσει το codebase σε διαφορετικά διεθνή ακροατήρια. Και οι 18 είναι οι πιο ομιλούμενες γλώσσες παγκοσμίως.
- **Γιατί 100% τοπικό (Ollama);** Μηδενικό κόστος cloud, πλήρης ιδιωτικότητα πηγαίου κώδικα, απεριόριστη χρήση. Η συνάρτηση `check_ollama()` εγγυάται ότι δεν θα συμβεί ποτέ cloud fallback.
- **Γιατί 93+ αρχεία (όχι μόνο .py);** Το codebase περιλαμβάνει κρίσιμα μη-Python αρχεία (HTML dashboards, CSS themes, JS graphs, JSON configs, Docker setup) που είναι απαραίτητα για την τεκμηρίωση ενός πλήρους κεφαλαίου μεθοδολογίας.
- **Γιατί πλήρως διαδραστικό (χωρίς CLI args);** Ο χρήστης ζήτησε ρητά τερματικές προτροπές — μηδενικά command-line arguments. Όλα γίνονται μέσω `questionary.select()` και `questionary.checkbox()`.
- **Γιατί ανθεκτικότητα ανά αρχείο;** Με 93+ αρχεία, ένα μεμονωμένο timeout δεν πρέπει να διακόπτει ολόκληρη τη διαδικασία. Τα αποτυχημένα αρχεία καταμετρώνται και αναφέρονται, τα επιτυχημένα αποθηκεύονται άμεσα.

### Αρχεία που Άλλαξαν
| Αρχείο | Αλλαγή |
|------|--------|
| `scripts/generate_docs.py` | **ΕΠΑΝΕΓΓΡΑΦΗ** — v1.0→v2.0, ~197→~350 γραμμές, 5→7 συναρτήσεις, 18 γλώσσες, 93+ αρχεία |
| `talos.py` | System Diagnostics menu + Επιλογή 8, version v5.2.1→v5.3.0 |
| `app.py` | System Diagnostics page + language dropdown + checkboxes + button, version v5.2.1→v5.3.0 |
| `PROJECT_MAP.md` | Section 4.7 ενημερώθηκε σε v2.0, version bump, dependency graph |
| `example.env` | Προστέθηκε `OLLAMA_MODEL` key |
| `ROADMAP.md` | v5.3.0 marked COMPLETED με πλήρη πίνακα χαρακτηριστικών |
| `README.md` | v5.3.0, bilingual EN+GR, νέα ενότητα Documentation Builder |
| `CHANGELOG_EN.md` | v5.3.0 entry rewritten from v1.0 |
| `CHANGELOG_GR.md` | Αυτή η καταχώρηση (rewritten from v1.0) |

**Σύνολο: 1 αρχείο επανεγγράφη, 8 αρχεία ενημερώθηκαν**


## [v5.2.1] - 2026-07-04 — Η Ενημέρωση "Academic Conference GUI & DRL Flagship"

Αυτή η έκδοση επανασχεδιάζει πλήρως το Streamlit GUI για **παρουσίαση σε ακαδημαϊκό συνέδριο** — dual-mode (Simple/Advanced), επαγγελματικό CSS theme, πλήρης δίγλωσση υποστήριξη (EN/GR), και η DRL-powered **AI Αναζήτηση** ως flagship feature.

### Προσθήκες
- **`templates/gui_theme.css` (ΝΕΟ, 140 γραμμές):** Επαγγελματικό CSS theme με glassmorphism, animations, custom scrollbar, dark/light mode
- **`templates/gui_strings.py` (ΝΕΟ, 124 γραμμές):** Λεξικό μετάφρασης (100+ κλειδιά EN/GR) με δυναμική `t()`
- **`app.py` — GUI Διπλής Λειτουργίας:** Language toggle, Simple (5 σελίδες) / Advanced (8 σελίδες), AI-Powered Search ως flagship tab, Autonomous Daemon, Model Management με VRAM-aware badges
- **`.clinerules`:** NO AUTO-GIT κανόνας

### Αλλαγές
- **Search & Discovery σειρά tabs:** 1. AI-Powered Search (DRL) → 2. Daily Search → 3. Historical → 4. Autonomous Daemon → 5. Grey Literature
- **`app.py`:** STR dict → `templates/gui_strings.py`, CSS → `templates/gui_theme.css`

### Διορθώσεις
- **Theme switching:** CSS injection αντί για broken `config.toml` — άμεση εναλλαγή
- **Academic emoji:** Μονόχρωμα σύμβολα (◆ ▷ ▣ ▨ ⊞ ⚙ ⊠ ⊙)


## [v5.2.0] - 2026-07-04 — Η Ενημέρωση "Onboarding & Δυναμική Ενορχήστρωση"

Αυτή η έκδοση μετατρέπει το TALOS σε μια **πλήρως καθοδηγούμενη ερευνητική πλατφόρμα** με onboarding wizard για πρώτη εκτέλεση, ροή research pivot, και ένα ριζικά αναβαθμισμένο DRL stack που υποστηρίζει πλέον **ΚΑΙ τις 14 ακαδημαϊκές πηγές δυναμικά** (όχι μόνο τις αρχικές 3). **8 αρχεία άλλαξαν, 1 νέο αρχείο, ~2,000 γραμμές κώδικα προστέθηκαν/αναδιοργανώθηκαν.**

---

### `app.py` v5.2.0 — Onboarding Wizard & Research Pivot (από v4.11.0, ~1022 → ~1400 γραμμές)

**ΓΙΑΤΙ:** Πριν την v5.2.0, ο TALOS δεν είχε καθοδηγούμενο onboarding — οι νέοι χρήστες έπρεπε να γνωρίζουν ήδη για την PYTHIA, τα profiles, και την αρχιτεκτονική 14 πηγών για να χρησιμοποιήσουν το σύστημα. Δεν υπήρχε τρόπος μέσω GUI για δημιουργία profile ή επαναβαθμονόμηση όταν άλλαζε το ερευνητικό ενδιαφέρον. Αυτό ήταν ένα σημαντικό κενό UX σε σύγκριση με επαγγελματικά ερευνητικά εργαλεία (Zotero, ResearchRabbit, Elicit).

**ΤΙ άλλαξε — Νέες συναρτήσεις:**

| Συνάρτηση | Υπογραφή | Περιγραφή |
|-----------|----------|-----------|
| `render_onboarding_wizard()` | `() -> None` | Αποδίδει έναν οδηγό 4 βημάτων στο Streamlit: (1) Όνομα Προφίλ, (2) Περιγραφή Ερευνητικού Τομέα, (3) PYTHIA AI configuration με inline επεξεργασία των παραγόμενων queries/prompts, (4) Review & Launch με προαιρετικό historic search και daemon start. Χρησιμοποιεί `st.session_state.onboarding_step` για πλοήγηση, progress bar για οπτική ανατροφοδότηση. |
| `_is_first_run()` | `() -> bool` | Επιστρέφει `True` αν δεν υπάρχει `_profiles/active_profile.txt` ή δεν βρέθηκαν profiles. Καλείται πριν την απόδοση του dashboard — αν True, ο wizard καταλαμβάνει ολόκληρη τη σελίδα μέσω `st.stop()`. |

**ΤΙ άλλαξε — Νέες ενότητες UI:**
- **Research Pivot** ενότητα στο Profile & Settings → Profiles tab: text area για νέα ερευνητική κατεύθυνση + κουμπί "Start Research Pivot" που ενεργοποιεί την αναγέννηση της PYTHIA μέσω subprocess, με καθοδήγηση βήμα-βήμα για re-evaluation και retraining.
- **Imports που προστέθηκαν:** `scripts.profile_manager` (6 συναρτήσεις: PROFILES_DIR, ROOT_DIR, ensure_profiles_dir, set_active_profile_name, save_current_state_to_profile, load_profile_to_root), `scripts.query_translator.flatten_json`, `shutil`, `socket`, `webbrowser`, `traceback`.

**ΤΙ άλλαξε — Πλοήγηση:**
- **Sidebar επεκτάθηκε:** 7 → 8 σελίδες (προστέθηκε "🧠 DRL Agent Dashboard" ως ξεχωριστή σελίδα).
- **Έκδοση:** `v4.11.0` → `v5.2.0` σε sidebar header, footer, και docstring.

---

### `core/talos_env.py` v2.0 — Δυναμικό Περιβάλλον N Πηγών (από v1.0, ~303 → ~380 γραμμές)

**ΓΙΑΤΙ:** Το αρχικό `TalosEnv` είχε hardcoded ακριβώς 3 πηγές (ArXiv, OpenAlex, Semantic Scholar) με 4 actions (3 query + 1 sleep). Αυτό σήμαινε ότι ο DRL agent μπορούσε να μάθει να δρομολογεί μόνο μεταξύ αυτών των 3 APIs — αγνοώντας τις άλλες 11 πηγές που υποστηρίζει ο TALOS. Για να κλιμακωθεί ο agent και στις 14 πηγές, το περιβάλλον έπρεπε να γίνει δυναμικό.

**⚠️ BREAKING ΑΛΛΑΓΕΣ (3):**
1. Observation space: hardcoded `Box(6,)` → δυναμικό `Box(1 + N + 2,)` όπου N = αριθμός πηγών. Δομή: `[ώρα/23, usage_ratio_0, ..., usage_ratio_N-1, low_streak/10, error_streak/10]`.
2. Action space: hardcoded `Discrete(4)` → δυναμικό `Discrete(N + 1)` όπου N = αριθμός πηγών. Sleep action = δείκτης N (ήταν hardcoded 3).
3. Εσωτερική κατάσταση: αφαιρέθηκαν τα `self.arxiv_calls`, `self.openalex_calls`, `self.s2_calls`. Αντικαταστάθηκαν με παράλληλους numpy πίνακες: `self.source_calls` (σχήμα N) και `self.source_limits` (σχήμα N).

**Οδηγός μετάβασης:** Παλιός κώδικας που αναφέρεται σε `env.arxiv_calls`, `action == 3` (sleep), ή 6-στοιχείων observations πρέπει να ενημερωθεί. Νέος κώδικας πρέπει να χρησιμοποιεί `env.source_calls[idx]`, `action == env.SLEEP_ACTION`, και το δυναμικό μήκος observation.

**ΤΙ άλλαξε — Νέες συναρτήσεις επιπέδου module:**

| Συνάρτηση | Υπογραφή | Περιγραφή |
|-----------|----------|-----------|
| `_load_source_list(config)` | `(dict ή None) -> list[str]` | Διαβάζει ονόματα πηγών από το config με προτεραιότητα 3 επιπέδων: (1) ρητό κλειδί `source_names`, (2) auto-detect από `_query` keys, (3) fallback σε `["arxiv", "openalex", "semantic_scholar"]`. |
| `_try_load_config()` | `() -> dict ή None` | Φορτώνει `config.json` από το project root με graceful χειρισμό JSONDecodeError. |
| `_load_source_limits(source_names, config)` | `(list, dict) -> np.ndarray` | Διαβάζει per-source limits από `config.json` (κλειδιά `<source>_limit`), default 100. |
| `get_default_state_space()` | `() -> int` | Επιστρέφει `1 + len(sources) + 2` — το μέγεθος observation για τον default αριθμό πηγών. |
| `get_default_action_space()` | `() -> int` | Επιστρέφει `len(sources) + 1` — το πλήθος actions (N πηγές + sleep). |

**ΤΙ άλλαξε — Constructor κλάσης `TalosEnv`:**
- `TalosEnv(source_names=None, source_limits=None, config=None)` — όλες οι παράμετροι προαιρετικές. Αν `source_names` είναι None, auto-detected από config.
- Deduplication ονομάτων πηγών με διατήρηση σειράς.
- `self.SLEEP_ACTION = self.num_sources` — δυναμικά υπολογισμένος δείκτης sleep.
- Νέα attributes: `source_names` (list), `num_sources` (int), `source_limits` (np.ndarray), `source_calls` (np.ndarray).

**ΤΙ άλλαξε — Μέθοδος `step(action)`:**
- Παλιό: τεράστια αλυσίδα `if action == 3: ... elif action == 0: ... elif action == 1: ... elif action == 2: ...`.
- Νέο: `if action == self.SLEEP_ACTION: ... elif 0 <= action < self.num_sources: source_name = self.source_names[action]; ...` — καθαρός γενικός βρόχος.
- Λογική reward ΠΑΝΟΜΟΙΟΤΥΠΗ: +20 score≥8, +5 score=7, -10 score<7, -50 API error, +2 sleep όταν max usage > 80%.
- Το info dict περιλαμβάνει πλέον `"source": source_name` επιπλέον των `"action"` και `"score"`.

**ΤΙ άλλαξε — Backward compatibility:**
- Properties `arxiv_limit`, `openalex_limit`, `s2_limit` εξακολουθούν να υπάρχουν — αναζητούν την ονομασμένη πηγή στο `self.source_names` και επιστρέφουν το limit της.
- `_simulate_score()` και `_score_to_reward()` αμετάβλητες.

---

### `core/drl_agent.py` v2.0 — Δυναμικός Agent (από v1.1, ~393 → ~320 γραμμές)

**ΓΙΑΤΙ:** Ο αρχικός agent είχε hardcoded `STATE_SPACE = 6` και `ACTION_SPACE = 4` σε επίπεδο module. Με το δυναμικό περιβάλλον που υποστηρίζει N πηγές, ο agent έπρεπε να προσαρμόζει τις διαστάσεις εισόδου/εξόδου του νευρωνικού δικτύου κατά την κατασκευή. Επιπλέον, τα αποθηκευμένα μοντέλα δεν είχαν metadata — η φόρτωση ενός μοντέλου 3 πηγών σε config 14 πηγών θα αποτύγχανε σιωπηλά ή θα παρήγαγε λάθος αποτελέσματα.

**ΤΙ άλλαξε — Σταθερές επιπέδου module:**
- `STATE_SPACE` και `ACTION_SPACE` υπολογίζονται πλέον δυναμικά κατά το import: `STATE_SPACE = get_default_state_space()`, `ACTION_SPACE = get_default_action_space()`. Fallback σε (6, 4) αν το import αποτύχει.
- ΟΛΕΣ οι υπερπαράμετροι αμετάβλητες: `LR=1e-4`, `GAMMA=0.8`, `TAU=1e-3`, `BATCH_SIZE=200`, κλπ.

**ΤΙ άλλαξε — Κλάση `DuelingLSTM`:**
- Constructor: `DuelingLSTM(input_dim, output_dim)` — και οι δύο παράμετροι περνιούνται κατά την κατασκευή, δεν βασίζονται πλέον σε σταθερές επιπέδου module. Τα LSTM layers δέχονται πλέον `input_size=input_dim` για το πρώτο layer και εξάγουν `output_dim` Q-values από το advantage head.

**ΤΙ άλλαξε — Κλάση `TalosDRLAgent`:**
- Constructor: `TalosDRLAgent(state_dim=None, action_dim=None)` — όταν None, χρησιμοποιεί τις προεπιλογές επιπέδου module. Αποθηκεύει `self.state_dim`, `self.action_dim`, και `self.source_names` (φορτωμένο από `talos_env._load_source_list()`).

**ΤΙ άλλαξε — Μέθοδος `save(path)`:**
- Παλιό format: `T.save(self.actor_online.state_dict(), path)` — raw `OrderedDict`.
- Νέο format: `T.save({"state_dim": ..., "action_dim": ..., "source_names": ..., "weights": ...}, path)` — dict με metadata.

**ΤΙ άλλαξε — Μέθοδος `load(path)`:**
- Ανιχνεύει παλιό vs νέο format: ελέγχει αν τα φορτωμένα δεδομένα είναι dict με κλειδί `"weights"`.
- Εξάγει metadata: `state_dim`, `action_dim`, `source_names` από το αποθηκευμένο dict.
- Αν οι διαστάσεις δεν ταιριάζουν με τα υπάρχοντα δίκτυα, **αναδημιουργεί** και τα δύο `actor_online` και `actor_target` με το σωστό `DuelingLSTM(input_dim, output_dim)`, αναδημιουργεί τον optimizer, και μετά φορτώνει weights μέσω `load_state_dict()`.
- Αυτό επιτρέπει τη φόρτωση μοντέλου 3 πηγών σε config 14 πηγών (και αντίστροφα).

---

### `scripts/talos_service.py` v2.0 — Profile-Aware Daemon (από v1.1, ~472 → ~430 γραμμές)

**ΓΙΑΤΙ:** Ο v1.1 daemon είχε 4 hardcoded προβλήματα: (1) `action == 3` για sleep, (2) `{0: "ArXiv", 1: "OpenAlex", 2: "S2"}` για source names, (3) πάντα φόρτωνε μοντέλο από `models/dddqn_trained.pth` αγνοώντας profiles, (4) agent δημιουργούνταν με προεπιλεγμένες διαστάσεις που μπορεί να μην ταίριαζαν με το περιβάλλον. Αυτό σήμαινε ότι ο daemon δεν μπορούσε να προσαρμοστεί όταν ο χρήστης άλλαζε profile ή όταν άλλαζαν οι πηγές.

**ΤΙ άλλαξε — Αρχικοποίηση:**
- Διαβάζει ενεργό profile από `_profiles/active_profile.txt` κατά την εκκίνηση, εμφανίζει όνομα profile στην κεφαλίδα.
- Δημιουργεί `OfflineTalosEnv()` ΠΡΩΤΑ για να πάρει το πραγματικό `num_sources` και `SLEEP_ACTION`.
- Δημιουργεί agent με: `TalosDRLAgent(state_dim=env.observation_space.shape[0], action_dim=env.action_space.n)`.
- Φόρτωση μοντέλου: ελέγχει πρώτα `_profiles/<name>/models/dddqn_trained.pth`, μετά το global `models/dddqn_trained.pth` ως fallback.

**ΤΙ άλλαξε — Κυρίως βρόχος:**
- `action == 3` → `action == sleep_action` (όπου `sleep_action = env.SLEEP_ACTION`).
- `action_name = {0: "ArXiv", 1: "OpenAlex", 2: "S2"}.get(action, "?")` → `source_name = info.get("source", "unknown")`.
- Μορφοποίηση ειδοποιήσεων: `format_paper_alert()` χρησιμοποιεί πλέον δυναμικά ονόματα εμφάνισης πηγών (`source.replace('_', ' ').title()`).

**ΤΙ άλλαξε — Strings έκδοσης:**
- Κεφαλίδα: `v5.0.0 (Phase 4)` → `v5.2.0`
- Εβδομαδιαίο digest: `v5.0.0` → `v5.2.0`

---

### `scripts/talos_live_agent.py` v2.0 — Dynamic N-Source Live Agent (από v1.0, ~409 → ~390 γραμμές)

**ΓΙΑΤΙ:** Ο v1.0 live agent είχε hardcoded imports για ακριβώς 3 κλάσεις πηγών (`ArxivSource`, `OpenAlexSource`, `SemanticScholarSource`) και hardcoded 6-στοιχείων state vector. Μπορούσε να κάνει πραγματικά API calls μόνο σε αυτές τις 3 πηγές. Για να ενορχηστρώσει ο agent και τις 14 πηγές, κάθε hardcoded αναφορά έπρεπε να αντικατασταθεί με δυναμική ανακάλυψη.

**ΤΙ άλλαξε — Νέες συναρτήσεις:**

| Συνάρτηση | Υπογραφή | Περιγραφή |
|-----------|----------|-----------|
| `_import_source_class(source_name)` | `(str) -> class ή None` | Εισάγει δυναμικά `sources.<name>_source.<Name>Source` χρησιμοποιώντας `__import__()` και `getattr()`. Χειρίζεται μετατροπή TitleCase (π.χ., `semantic_scholar` → `SemanticScholarSource`). Επιστρέφει `None` με warning σε αποτυχία import. |
| `_build_source_map(source_names)` | `(list[str]) -> dict` | Χτίζει dict `{action_index: (source_name, SourceClass)}` για όλες τις εισαγώγιμες πηγές. Οι πηγές που αποτυγχάνουν στο import εξαιρούνται σιωπηλά. |

**ΤΙ άλλαξε — Τροποποιημένες συναρτήσεις:**
- `calculate_state()`: Η υπογραφή άλλαξε από σταθερό 6-στοιχείων πίνακα σε δυναμικό `(normalized_hour, call_counts, source_limits, low_score_streak, error_streak, source_names)`. Επιστρέφει `np.array([hour] + ratios + [low_norm, error_norm])`.
- `execute_live_fetch()`: Προστέθηκε παράμετρος `action_map` (χρησιμοποιούσε hardcoded `{0: ("ArXiv", ArxivSource), ...}`). Πλέον επιστρέφει 3-πλέτα `(papers, error, source_name)`.
- `main()`: Auto-detects πηγές μέσω `_load_source_list(config)`, χτίζει `action_map` μέσω `_build_source_map()`, υπολογίζει `sleep_action = len(source_names)`. Profile-aware φόρτωση μοντέλου (ίδια με τον daemon).

**ΤΙ άλλαξε — Imports που αφαιρέθηκαν:**
- Παλιό: `from sources.arxiv_source import ArxivSource`, `from sources.openalex_source import OpenAlexSource`, `from sources.semantic_scholar_source import SemanticScholarSource`.
- Νέο: `from core.talos_env import _load_source_list, _try_load_config` — καθόλου source-specific imports.

---

### `scripts/train_agent.py` — Δυναμική Εμφάνιση Πηγών (από v1.0, ~283 → ~290 γραμμές)

**ΓΙΑΤΙ:** Το training script δεν άλλαξε σε λογική αλλά χρειαζόταν να εμφανίζει δυναμικές πληροφορίες πηγών ώστε οι χρήστες να γνωρίζουν πόσες πηγές και ποιες διαστάσεις έχει ο agent κατά την εκπαίδευση.

**ΤΙ άλλαξε:**
- Εμφάνιση εκκίνησης: προστέθηκε αριθμός πηγών, ονόματα πηγών (περικομμένα στα πρώτα 5 αν >5), διάσταση observation, και διάσταση action.
- Δημιουργία agent: `TalosDRLAgent()` → `TalosDRLAgent(state_dim=env.observation_space.shape[0], action_dim=env.action_space.n)`.
- String έκδοσης: `Database-Driven` → `Database-Driven (v5.2.0)`.

---

### `scripts/research_pivot.py` v1.0 — **ΝΕΟ ΑΡΧΕΙΟ** (~180 γραμμές)

**ΓΙΑΤΙ:** Δεν υπήρχε αυτοματοποιημένη ροή εργασίας για χρήστες που άλλαξαν ερευνητικό ενδιαφέρον. Έπρεπε χειροκίνητα να: (1) ξανατρέξουν PYTHIA μέσω CLI, (2) θυμηθούν να κάνουν re-evaluate τη βάση, (3) θυμηθούν να κάνουν retrain τον agent, (4) αποθηκεύσουν χειροκίνητα στο profile. Αυτό το script αυτοματοποιεί ολόκληρη τη ροή pivot.

**Συναρτήσεις:**

| Συνάρτηση | Υπογραφή | Περιγραφή |
|-----------|----------|-----------|
| `get_active_profile_name()` | `() -> str` | Διαβάζει το ενεργό profile από `_profiles/active_profile.txt`, default "default". |
| `save_state_to_profile(profile_name)` | `(str) -> None` | Αντιγράφει το root `config.json` και `talos_research.db` στο `_profiles/<name>/`. |
| `run_script(script_name, stdin_text, args)` | `(str, str, list) -> (int, str)` | Εκτελεί ένα TALOS script ως subprocess με piping `TALOS_GUI_STDIN`. Timeout 30 λεπτών. |
| `main()` | `() -> None` | Διαδραστικός οδηγός 5 βημάτων: (1) συλλογή νέας κατεύθυνσης, (2) εκτέλεση PYTHIA, (3) προαιρετικό re-evaluate βάσης, (4) προαιρετικό retrain agent με προσαρμοσμένο αριθμό επεισοδίων, (5) αποθήκευση στο profile. Υποστηρίζει `--auto` flag για ενσωμάτωση GUI (διαβάζει από env var). |

**Imports:** `questionary`, `subprocess`, `shutil`, `sys`, `os`.

---

### Ενημερώσεις Τεκμηρίωσης

**`PROJECT_MAP.md`:**
- Προστέθηκε Section 2.0: `core/talos_env.py` v2.0 με όλες τις 8 συναρτήσεις τεκμηριωμένες.
- Προστέθηκε Section 2.3: `core/notifier.py` (TalosNotifier — ήταν εντελώς ατεκμηρίωτο πριν).
- Ενημερώθηκε Section 2.2: `core/drl_agent.py` από v1.1 → v2.0 με νέες υπογραφές.
- Ενημερώθηκε Section 3.2: `app.py` από v4.10.1 → v5.2.0, σελίδες 6 → 8, νέος πίνακας συναρτήσεων.
- Προστέθηκαν νέα docs για integration scripts: `scripts/drl_trainer.py`, `scripts/talos_live_agent.py` v2.0, `scripts/talos_service_api.py`, `scripts/research_pivot.py`.
- Τελευταία Ενημέρωση: 2026-07-04, Έκδοση: v5.2.0, Αριθμός αρχείων: 56.
- **Βελτίωση function audit:** 166 → 183 matched (+17 νέες τεκμηριωμένες συναρτήσεις).

**`.clinerules`:**
- Προστέθηκε κανόνας "CRITICAL: Project Version & PROJECT_MAP.md Synchronization" — επιβάλλει ενημέρωση χάρτη μετά από κάθε αλλαγή .py, υπερισχύει όλων των άλλων κανόνων.
- Προστέθηκε κανόνας "CRITICAL: Documentation Sync — CHANGELOG, README, ROADMAP" — επιβάλλει υπερ-αναλυτικές καταχωρήσεις changelog με ακριβή ονόματα αρχείων, υπογραφές, και αιτιολόγηση μετά από κάθε σημαντική αλλαγή.

**`README.md`:** Έκδοση v5.0.0 → v5.2.0. Tagline ενημερώθηκε σε "Now with Guided Onboarding, Research Pivot & Dynamic 14-Source DRL Orchestration".

**`ROADMAP.md`:** Ενότητα v5.2.0 ενημερώθηκε από "In Progress" σε "COMPLETED ✅" με αναλυτικό πίνακα χαρακτηριστικών που καλύπτει Onboarding, DRL Stack, Documentation, και Files Changed.

---

### `scripts/pdf_downloader.py` — Hotfix: Μη Ορισμένη Σταθερά `MAX_WORKERS`

**ΓΙΑΤΙ:** Η λειτουργία multi-threaded batch download (που προστέθηκε στην αρχική έκδοση v5.2.0 Live Agent & PDF Downloader) αναφερόταν στη σταθερά `MAX_WORKERS` στη γραμμή 255 χωρίς να την έχει ορίσει σε επίπεδο module. Αυτό προκαλούσε `NameError` κατά την εκτέλεση όταν ο χρήστης επέλεγε batch mode μέσω του prompt `questionary.confirm("Use multi-threaded batch download?")`, σπάζοντας εντελώς τη multi-threaded διαδρομή λήψης.

**ΤΙ άλλαξε:**
- **Γραμμή 32:** Προστέθηκε η δήλωση σταθεράς `MAX_WORKERS = 10` αμέσως μετά το `MAX_RETRIES = 2` στο πάνω μέρος του μπλοκ ρυθμίσεων του module (μαζί με `DOWNLOAD_TIMEOUT=30`, `MAX_RETRIES=2`, `REQUEST_DELAY=1.0`).
- Καμία άλλη γραμμή δεν τροποποιήθηκε — οι υπάρχουσες κλήσεις `print(f"\n  ⚡ Multi-threaded mode: {MAX_WORKERS} workers")` και `ThreadPoolExecutor(max_workers=MAX_WORKERS)` πλέον επιλύονται σωστά στη νέα σταθερά.

**Αρχεία που άλλαξαν:** 1 (`scripts/pdf_downloader.py` — 1 γραμμή προστέθηκε)

---

**Σύνολο: 8 αρχεία άλλαξαν, 1 νέο αρχείο, ~2,000 γραμμές κώδικα προστέθηκαν/αναδιοργανώθηκαν**
**Integration test: 43/43 Python files περνούν `py_compile` validation**


## [v5.2.0] - 2026-07-04 — The Live Agent & PDF Downloader

Αυτή η έκδοση συνδέει τον εκπαιδευμένο DRL agent στο ζωντανό διαδίκτυο και προσθέτει multi-threaded PDF batch downloading.

### Προσθήκες
- **`scripts/talos_live_agent.py` v1.0 (330 γραμμές):** Live DRL inference engine — φορτώνει το εκπαιδευμένο μοντέλο, pure exploitation (ε=0.0), πραγματικά API calls, AI evaluation μέσω Flash model, graceful 429 handling
- **TUI entry** (`talos.py` → Analysis Option 11): "Live DRL Agent (Real APIs)"
- **GUI entry** (`app.py` → Analysis & Insights dropdown): "🧠 Live DRL Agent (Real APIs)"
- **`.bat` entry** (`start_talos.bat` Option 6): "Live DRL Agent (Real APIs)"
- **`scripts/pdf_downloader.py` v2.0:** Multi-threaded batch download με ThreadPoolExecutor (15 workers), ~10x speedup

### Αλλαγές
- **`scripts/talos_service.py`:** Epsilon 0.05 → 0.0 (pure exploitation)
- **`ROADMAP.md`:** Πλήρες αρχιτεκτονικό narrative — v5.2.0 marked as current

---

## [v5.1.0] - 2026-07-04 — DRL Dashboard & Αναδιοργάνωση TUI/GUI

Αυτή η έκδοση φέρνει το DRL οικοσύστημα στο προσκήνιο με ένα αποκλειστικό Streamlit dashboard, διαδραστικές λειτουργίες TUI, και μια ολοκληρωμένη ενημέρωση του project roadmap.

### Προσθήκες
- **`app.py` — 🧠 DRL Agent Dashboard (νέα σελίδα):** Streamlit σελίδα που δείχνει:
  - **GWO Optimization Results**: 4 metric cards (Learning Rate, Gamma, Epsilon Decay, Best Fitness) από το `models/gwo_best_params.json`
  - **"Load GWO Parameters"** κουμπί αποθήκευσης παραμέτρων στο `st.session_state`
  - **Agent Training Status**: έλεγχος για `models/dddqn_trained.pth`
  - **Reward Progression Chart**: ανοδικό `st.line_chart` 500 επεισοδίων
  - **Training Details**: πίνακας 2 στηλών με αρχιτεκτονική, υπερπαραμέτρους, GPU
- **`talos.py` — DRL Agent Status (Diagnostics → Επιλογή 7):** Πάνελ με trained model status + GWO hyperparameters. Πτώση σε απλό κείμενο αν δεν υπάρχει το `rich`.
- **`talos.py` — Compare Baselines (Analysis → Επιλογή 10):** Δημιουργεί νέο baseline report και το συγκρίνει με το προηγούμενο, δείχνοντας Δ για Total Papers, Elite Papers, και Average Score.

### Αλλαγές
- **`talos.py` — Αναδιοργάνωση TUI:** Το DRL Training μεταφέρθηκε από standalone επιλογή στο Analysis & Insights (Επιλογή 9). Το μενού επεκτάθηκε από 12→13 επιλογές.
- **`ROADMAP.md`:** Πλήρης επανεγγραφή — v5.0.1 ως τρέχουσα σταθερή, αναλυτικό πλάνο v5.1→v5.3, v6.0+ Think Tank με 4 στρατηγικούς άξονες.


## [v5.0.1] - 2026-07-04 — Εξαγωγή JSON από GWO

### Προσθήκες
- **`scripts/gwo_rl_optimizer.py`**: Αποθηκεύει τις καλύτερες υπερπαραμέτρους στο `models/gwo_best_params.json` μετά την ολοκλήρωση του optimization. Περιλαμβάνει learning_rate, gamma, epsilon_decay, best_fitness, best_avg_reward, iterations, και χρόνο εκτέλεσης. Δημιουργεί αυτόματα τον φάκελο `models/` αν δεν υπάρχει.


## [v5.0.0] - 2026-07-03 — Ενημέρωση "Hybrid Embeddings & Deep RL"

Αυτή η **τεράστια κύρια έκδοση** καλύπτει έξι διακριτές φάσεις: multi-provider embeddings, πλήρες Deep Reinforcement Learning stack (περιβάλλον + πράκτορας + optimizer + offline εκπαίδευση), επιτάχυνση GPU RTX 4070, αυτοματοποιημένο baseline reporting module, και τεκμηρίωση/νοικοκύρεμα του project. Πρόκειται για τη μεγαλύτερη μεμονωμένη ενημέρωση στην ιστορία του TALOS με **14 νέα αρχεία** και **22 τροποποιημένα αρχεία**.

---

### Phase 0 — Multi-Provider Hybrid Embeddings v2

#### Προσθήκες
- **`scripts/db_embedding_upgrade.py` v2.0:** Δημιουργία πίνακα `embeddings` (id, paper_id FK, embedding BLOB, embedding_model TEXT) με indexes. Μετέφερε 3.849 legacy `papers.embedding` εγγραφές.
- **`core/database_manager.py` v5.0:**  
  - **`store_embeddings_batch(updates)`**: INSERT INTO `embeddings` (πολλαπλά vectors ανά paper — ένα ανά provider)  
  - **`get_papers_needing_embedding(model)`**: Ελέγχει τον πίνακα embeddings ανά συγκεκριμένο μοντέλο  
  - **`get_all_embeddings(model_filter)`**: Αυτόματο fallback σε legacy `papers.embedding` αν δεν υπάρχει ο πίνακας  
  - **`get_embedding_model_stats()`**: Επιστρέφει model → count από τον πίνακα embeddings  
  - **`reload_embeddings_for_model(model)`**: Φορτώνει στη μνήμη vectors μόνο για το επιλεγμένο μοντέλο  
  - **`semantic_search(query_vector, top_k=100, model_filter=None)`**: Φιλτράρει cosine similarity μόνο για vectors από το ίδιο μοντέλο  
  - **Profile-aware init**: Αυτόματη ανίχνευση `_profiles/<name>/talos_research.db` μέσω `_resolve_profile_db()`
- **`core/ai_manager.py` v3.6:**  
  - **Hybrid multi-provider embeddings**: Σειρά: Ollama (nomic-embed-text, τοπικό/δωρεάν) → Gemini (gemini-embedding-001, cloud/επί πληρωμή)  
  - **`generate_embeddings(texts)` επιστρέφει `(vectors, model_name)` tuple**: Η βάση μπορεί να μαρκάρει κάθε εγγραφή με το μοντέλο που την παρήγαγε  
  - **Google GenAI GA SDK**: Χρήση `google.genai.Client` (ΟΧΙ deprecated `google.generativeai`) με `gemini-embedding-001`, `RETRIEVAL_DOCUMENT`, 768-dim output  
  - **Rate-limit handling**: BATCH_SIZE=10, sleep=3s, retry έως 10 φορές με parsed `retryDelay` από 429 errors  
  - **HuggingFace αφαιρέθηκε** από την αλυσίδα embeddings: DNS προβλήματα
- **`scripts/embedding_generator.py` v4.0:**  
  - **`--all` seed-all mode**: Περνά από ΟΛΑ τα διαθέσιμα μοντέλα (Ollama → Gemini)  
  - **BATCH_SIZE=10** με sleep=3s (~20 RPM, εντός του ορίου 100 RPM του free tier)  
  - **Summary report**: Σύνολο papers, papers χωρίς abstract, generated/failed ανά μοντέλο  
- **Semantic search**: `model_filter` dropdown σε GUI και Flask dashboard — συγκρίνει μόνο vectors από το ίδιο μοντέλο. `semantic_search()` επιστρέφει έως 200 αποτελέσματα.
- **`_fix_embedding_labels.py`** (μιας χρήσης): Μετονόμασε legacy "gemini" → "gemini:gemini-embedding-001" σε 3.849 εγγραφές.

---

### Phase 1 — DRL Περιβάλλον & Πράκτορας v1.0

#### Προσθήκες
- **`core/talos_env.py` v1.0 (225 γραμμές):** Gymnasium RL περιβάλλον για επιλογή API πηγής  
  - **Observation Space**: `Box(6,)` — [κανονικοποιημένη_ώρα, arxiv_ratio, openalex_ratio, s2_ratio, χαμηλά_scores_streak, errors_streak]  
  - **Action Space**: `Discrete(4)` — 0=ArXiv, 1=OpenAlex, 2=SemanticScholar, 3=Sleep/Cooldown  
  - **Reward Logic**: +20 score≥8, +5 score=7, -10 score<7, -50 API error (429), +2 sleep όταν limits >80%  
- **`core/drl_agent.py` v1.1 (395 γραμμές):** Double Dueling DQN με LSTM  
  - **`DuelingLSTM`**: 3-layer LSTM (128→64→32) με LayerNorm + Dueling heads (V + A)  
  - **`TalosDRLAgent`**: Online + Target δίκτυα, ε-greedy exploration, soft updates (τ=1e-3), experience replay  
  - **`ReplayMemory`**: deque(maxlen=10000), batch_size=200, LEARN_AFTER=500  
  - **CuDNN fix**: `flatten_parameters()` πριν από κάθε LSTM forward pass, `actor_target.train()` αντί `.eval()`  
  - **Hyperparameters**: LR=1e-4, GAMMA=0.8, TAU=1e-3, BATCH_SIZE=200
- **`scripts/drl_trainer.py` v1.0 (135 γραμμές):** CLI training loop — `--episodes 500` flag, αποθήκευση σε `models/talos_drl.pth`

---

### Phase 2 — Meta-Optimization & Offline Training

#### Προσθήκες
- **`scripts/gwo_rl_optimizer.py` v1.0 (360 γραμμές):** Grey Wolf Optimizer για hyperparameter tuning  
  - **Search space**: LR ∈ [1e-5, 1e-3], GAMMA ∈ [0.5, 0.99], EPS_DECAY ∈ [0.9, 0.999]  
  - **15 λύκοι, 50 επαναλήψεις**: X_new = (X1 + X2 + X3) / 3, `a` μειώνεται 2→0  
- **`scripts/train_agent.py` v1.0 (260 γραμμές):** Offline εκπαίδευση με ΠΡΑΓΜΑΤΙΚΑ scores από τη βάση  
  - **`OfflineTalosEnv`**: Επεκτείνει `TalosEnv`, κάνει override `_simulate_score()` → δειγματοληψία πραγματικών `overall_score` από SQLite  
  - **Profile-aware**: Διαβάζει `_profiles/active_profile.txt`  
  - **Per-episode timing**: `X.XXs` ανά επεισόδιο με `flush=True`, ETA σε λεπτά  
  - Αποθήκευση σε `models/dddqn_trained.pth`

---

### Phase 3 — Graceful Degradation & Documentation

#### Αλλαγές
- **Και οι 3 premium API πηγές (IEEE, Elsevier, Springer):** Ήδη υλοποιημένο graceful degradation — έλεγχος API key → `self.enabled=False` + warning → `fetch_new_papers()` επιστρέφει `[]`. Επαληθεύτηκε.
- **`scripts/data_enricher.py` v4.8.1:** Προστέθηκε πλήρης τεκμηρίωση: module docstring, Google-style docstrings, inline comments σε απλά αγγλικά.
- **`sources/ieee_source.py` v2.2:** Προστέθηκαν inline comments για pagination logic.

---

### Επιτάχυνση GPU/CUDA

#### Αλλαγές
- **RTX 4070**: Απεγκατάσταση CPU-only PyTorch 2.12.1, εγκατάσταση `torch 2.5.1+cu121` (CUDA 12.1)  
- **CuDNN mode-lock fix**: Αφαίρεση όλων των `.eval()` από το online δίκτυο, `actor_target.eval()` → `actor_target.train()`  
- **Επαληθεύτηκε**: `torch.cuda.is_available()` = True, CUDA 12.1, GPU: NVIDIA GeForce RTX 4070 (12 GB VRAM)  
- **Ταχύτητα**: ~0.5s/επεισόδιο σε CPU → ~0.05s/επεισόδιο σε GPU (10x βελτίωση)

#### Προσθήκη dependencies
- `gymnasium`, `torch`, `streamlit`

---

### Σύστημα Baseline Report

#### Προσθήκες
- **`scripts/generate_baseline_report.py` v1.1 (480 γραμμές):** Αυτοματοποιημένη γεννήτρια baseline snapshot  
  - **4 plots σε 300/600 DPI**: Score distribution (histogram + KDE), Quad-Layer averages (bar), Source distribution (pie, top 8 + Other), Embedding coverage (horizontal bar)  
  - **`--academic` flag**: Ποιότητα δημοσίευσης — serif γραμματοσειρές (Times New Roman), 600 DPI, muted ακαδημαϊκή παλέτα, κατάλληλο για IEEE/Springer journals  
  - **Οργάνωση κατά ημερομηνία**: `reports/general_status_report/YYYY-MM-DD/` με `report.md` + `report.html`  
  - **Dark-themed HTML**: Ταιριάζει με το TALOS dashboard aesthetic

#### Προσθήκη στο TUI/GUI
- **TUI** (`talos.py` → System Diagnostics): Επιλογές 5 "Baseline Report (Standard)" και 6 "Baseline Report (Academic — 600 DPI)"  
- **GUI** (`app.py` → Analysis & Insights): Dropdown "📊 Baseline Report (Standard)" και "🎓 Baseline Report (Academic)"

---

### Κανόνες Τεκμηρίωσης & Γνώσης

- **`.clinerules` v5.0.0 — Progressive Documentation Rule**: ΥΠΟΧΡΕΩΤΙΚΗ τεκμηρίωση σε ΚΑΘΕ άνοιγμα `.py` αρχείου (ανάγνωση Ή επεξεργασία)
- **`CHANGELOG_EN.md`** και **`CHANGELOG_GR.md`**: Ενημερώθηκαν και στις δύο γλώσσες
- **`requirements.txt`**: Προστέθηκαν `gymnasium`, `torch`, `streamlit`

---

### Νοικοκύρεμα

#### Διαγραφή
- `_fix_ai.py`, `_fix_embedding_labels.py`, `_fix_now.py`, `_fix2.py`, `_fix3.py`, `_fix4.py` — scripts μιας χρήσης, ήδη εφαρμόστηκαν
- `dump.json` — παλιό data dump

#### Αλλαγές
- **`start_talos.bat` v2.0**: Χρήση conda `talosenv`, menu: CLI, GUI, Dashboard, Baseline Report, Exit
- **TUI menu επέκταση**: 9→12 επιλογές (DRL Training + αναρίθμηση)
- **GUI menu επέκταση**: Baseline Report επιλογές στο Analysis & Insights

---

### Phase 4 — Αυτόνομη Υπηρεσία & Ειδοποιήσεις

#### Προσθήκες
- **`core/notifier.py` v1.0 (185 γραμμές):** Σύστημα ειδοποιήσεων πολλαπλών καναλιών  
  - **Telegram**: Bot API, `TELEGRAM_BOT_TOKEN` + `TELEGRAM_CHAT_ID`  
  - **Discord**: Webhook με truncation στα 2000 chars, `DISCORD_WEBHOOK_URL`  
  - **Email**: SMTP με STARTTLS για Gmail/Outlook (`SMTP_*` keys)  
  - Όλα τα exceptions πιάνονται εσωτερικά — fire-and-forget, ποτέ δεν ρίχνει τον caller
- **`scripts/talos_service.py` v1.1 (470 γραμμές):** 24/7 αυτόνομη ερευνητική υπηρεσία  
  - **Interactive reporting**: Silent (μόνο alerts) / Normal (σύνοψη επεισοδίων) / Verbose (κάθε ενέργεια)  
  - **Ημερήσιες αναφορές**: `reports/argus/YYYY-MM-DD/discoveries.{json,md,html}` — τρία formats  
  - **Εβδομαδιαίο digest**: Email κάθε Παρασκευή 17:00 με DB stats + δραστηριότητα  
  - **Ultra-lightweight**: `os.nice(10)` / `BELOW_NORMAL_PRIORITY_CLASS`, `time.sleep(5)`, `gc.collect()`, RAM < 100 MB  
  - **Action 3 (Sleep)**: `time.sleep(3600)` — 1 ώρα cooldown  
  - **Τεράστιο try/except** — η υπηρεσία ΠΟΤΕ δεν κρασάρει  
  - **Graceful shutdown**: SIGINT/SIGTERM handlers
- **`scripts/talos_service_api.py` v1.0 (90 γραμμές):** Micro-Flask API (port 5002)  
  - `GET /api/status` — uptime, papers σήμερα, DB stats  
  - `GET /api/report` — σημερινή HTML αναφορά
- **Μετονομάστηκε**: `talos_daemon.py` → `talos_service.py` (επιστημονικά σωστή ορολογία)
- **`requirements.txt`**: Προστέθηκε `psutil` για διαχείριση προτεραιότητας διεργασίας

#### Αλλαγές
- **`start_talos.bat` v2.0**: Προσθήκη `[5] Autonomous Research Service (24/7)`, Daemon→Service
- **GUI (`app.py`)**: Προσθήκη "🤖 Autonomous Research Service (24/7)" και "📡 Service API (Port 5002)" στο Analysis & Insights dropdown
- **`drl_trainer.py`**: Interactive επιλογή επεισοδίων (1=50, 2=100, 3=500, 4=1000)
- **`example.env`**: Προσθήκη Phase 4 keys (Telegram, SMTP, Discord notification config)

#### Αναφορές
- **Ημερήσια**: JSON + Markdown + HTML στο `reports/argus/YYYY-MM-DD/`
- **Εβδομαδιαία**: HTML email με DB stats κάθε Παρασκευή 17:00
- **API**: Real-time JSON status μέσω `localhost:5002/api/status`

---

**Σύνολο: 17 νέα αρχεία, 26 τροποποιημένα, 7 διαγραμμένα**
**Γραμμές κώδικα που προστέθηκαν: ~5,000+**

---

## [v4.11.0] - 2026-07-02 - Ενημέρωση "Project Map & Diagnostics"

Αυτή η έκδοση εισάγει ένα πλήρες σύστημα διαχείρισης γνώσης του project, συμπεριλαμβανομένου ενός κεντρικού χάρτη (PROJECT_MAP.md), διαδραστικού γράφου εξαρτήσεων, εργαλείων επαλήθευσης βασισμένων σε AST, και αναδιοργανωμένων μενού CLI/GUI.

### Προσθήκες
- **PROJECT_MAP.md:** Πλήρης χάρτης του project που τεκμηριώνει και τα 55 αρχεία, συναρτήσεις, εξαρτήσεις, σχήμα βάσης, γλωσσάρι ελληνικών κωδικών ονομάτων, και γνωστά προβλήματα
- **`.clinerules` v5.0.0:** Υποχρεωτικοί κανόνες ανάγνωσης του PROJECT_MAP.md για AI agents — διαβάζει τον χάρτη πρώτα σε κάθε νέο chat, τον ενημερώνει μετά από κάθε αλλαγή κώδικα
- **`templates/architecture_graph.html`:** Διαδραστικός γράφος εξαρτήσεων Cytoscape.js με 50+ nodes, 80+ edges, φιλτράρισμα επιπέδων, και audit mode (χρωματική κωδικοποίηση από dependency_audit.json)
- **`scripts/verify_dependency_map.py`:** Εργαλείο επαλήθευσης βασισμένο σε AST:
  - Dependency audit (Section 7 vs πραγματικά imports)
  - Function documentation audit (`--functions`: Sections 2-4 vs AST)
  - Συνδυασμένη λειτουργία (`--all`)
  - 81% μείωση θορύβου μέσω έξυπνου φιλτραρίσματος
  - 3 formats εξόδου: HTML, Markdown, JSON
- **Αναφορές ελέγχου** στο `reports/audits/`

### Αλλαγές
- **TUI αναδιοργάνωση** σε 11 επιλογές με 3 υπο-μενού: Database & Data, System Diagnostics, Profile & Settings
- **GUI sidebar** αναδιαρθρώθηκε σε 7 σελίδες που αντιστοιχούν στο TUI
- **GUI System Diagnostics** με 2 tabs: Code Integrity Check + Documentation Audit
- **Έκδοση** bumped σε v4.11.0
- **Architecture Intelligence Report:** Ανάλυση από LLM των PROJECT_MAP.md, audit, και graph data που παράγει αναφορές 8 ενοτήτων στα Αγγλικά και Ελληνικά (`scripts/architecture_intelligence_report.py`)
- **Γράφος αρχιτεκτονικής:** Διαδραστικός γράφος Cytoscape.js με 102 nodes, 318 edges, particle background, edge type legend, futuristic academic theme, zoom controls, fullscreen mode, Dark/Light toggle
- **Αυτόματη παραγωγή γράφου:** Το `scripts/generate_architecture_graph.py` χτίζει τον γράφο από AST analysis + documented dependencies, παράγοντας `templates/architecture_graph.html` με inline data
- **SVG export:** Background rect injection για μη-διαφανή έξοδο, CDN fallback μέσω PNG-wrapped SVG
- **Αυτόματη εκκίνηση HTTP server:** Το CLI και το GUI ανοίγουν τον γράφο στο `http://localhost:8765` για πλήρη υποστήριξη CDN (cytoscape-svg, navigator)
- **Real-time progress:** Η υπο-σελίδα του Architecture Report στο GUI δείχνει line-by-line output κατά τη διάρκεια του generation
- **Timestamped filenames:** Οι αναφορές αποθηκεύονται ως `architecture_intelligence_report_{lang}_{YYYY-MM-DD_HH-MM}.md`
- **TUI menu integration:** System Diagnostics → επιλογή 4 → Architecture Intelligence Report (AI Analysis)
- **GUI υπο-σελίδα:** Αποκλειστική σελίδα με Generate button, progress display, browser-open buttons (EN+GR), Back navigation, και history archive count
- **Free-first provider chain:** Το architecture report χρησιμοποιεί το AIManager priority chain (Ollama → HuggingFace → Gemini → DeepSeek)

### Διορθώσεις
- Το κουμπί Interactive Graph στο Streamlit GUI χρησιμοποιεί πλέον HTTP server (port 8765) + `webbrowser.open()` αντί για broken `file:///` links
- Το κουμπί SVG export λειτουργεί μέσω CDN (`cytoscape-svg@1.4.0`) με PNG fallback
- Το layout του γράφου είναι ισορροπημένο (nodeRepulsion 30000, gravity 0.2, padding 60)
- Τα διπλά `<script id="graph-data">` blocks αφαιρούνται μέσω regex cleanup στον generator
- Διορθώθηκαν λάθη στο dependency documentation (metadata_enricher, interactive_dashboard)
- Το dependency audit φιλτράρει σωστά third-party βιβλιοθήκες και standard library imports

## [v4.10.1] - 2026-06-30 - Ενημέρωση "Model Management"

Αυτή η έκδοση εισάγει ένα εξειδικευμένο Model Management TUI (`scripts/model_manager.py`) με quantization-aware επιλογή μοντέλων Ollama, δυναμική ανακάλυψη μοντέλων από τη βιβλιοθήκη Ollama, VRAM-fit δείκτες, και ρύθμιση cloud μοντέλων — όλα προσβάσιμα τόσο από το TUI όσο και από το Streamlit GUI.

### Προσθήκες
- **Model Management TUI (`scripts/model_manager.py`):**
  - Διαδραστική επιλογή τοπικών + cloud μοντέλων προσβάσιμη μέσω TUI (Profile & Settings → AI Model Management)
  - Quantization-aware model picker: ανιχνεύει όλα τα διαθέσιμα quant tags (Q8_0, Q4_K_M, Q2_K, IQ2_XXS, κλπ.) μέσω `ollama show`
  - Tags ομαδοποιημένα ανά bit-depth (8-bit, 6-bit, 4-bit, 3-bit, 2-bit, 1-bit) με εκτιμώμενο VRAM ανά quant
  - Αυτόματο download μοντέλων που λείπουν μέσω `ollama pull` με confirmation prompt
  - Cloud model configuration: επιλογείς Gemini Flash/Pro, DeepSeek chat/reasoner, HuggingFace
  - Επιλογέας embedding model (nomic-embed-text, bge-m3, mxbai-embed-large, κλπ.)
  - Δυνατότητα manual `ollama pull`
- **Quantization size estimation (`core/hardware.py`):**
  - `estimate_size_for_quant(model_name, quant_tag)` — υπολογίζει το μέγεθος μοντέλου σε GB για οποιοδήποτε quantization level
  - Πίνακας `QUANT_SIZE_PER_BILLION` με 30+ quantization types (Q8_0=1.0GB/B, Q4_K_M=0.55GB/B, Q2_K=0.28GB/B, IQ2_XXS=0.20GB/B, Q1_0=0.20GB/B, κλπ.)
  - `extract_params_b(model_name)` — εξάγει τον αριθμό παραμέτρων από το όνομα του μοντέλου
- **Δυναμική ανακάλυψη μοντέλων:**
  - Η hardcoded λίστα `POPULAR_MODELS` αφαιρέθηκε από το `model_manager.py` — τώρα τραβάει ζωντανά από το `ollama.com/api/tags`
  - Fallback στο `OLLAMA_LIBRARY_FALLBACK` του `hardware.py` όταν είναι offline
  - Λίστα μοντέλων σε 3 sections: Installed, Ollama Library, BitNet 1-bit (Edge/CPU)
- **VRAM-aware δείκτες:**
  - `[FITS ✓]` / `[TIGHT ~]` / `[TOO BIG ✗]` badges σε κάθε μοντέλο τόσο στο TUI όσο και στο GUI
  - Το VRAM headroom άλλαξε από 85% → **70%** (`VRAM_HEADROOM = 0.70`) για να αφήνει χώρο για το λειτουργικό και άλλες διεργασίες
- **GUI model configuration (Streamlit `app.py`):**
  - Quantization dropdown με εκτιμώμενο VRAM ανά quant level
  - Cloud model selectors στο Settings: Gemini Flash/Pro, DeepSeek, HuggingFace
- **Νέα `.env` keys:** `GEMINI_FLASH_MODEL`, `GEMINI_PRO_MODEL`, `DEEPSEEK_MODEL_CHAT`

### Αλλαγές
- **TUI (`talos.py`):**
  - `profile_settings_menu`: προστέθηκε "3. AI Model Management (Local & Cloud)" → εκκινεί το `model_manager.py`
  - Το main header δείχνει πλέον το τρέχον τοπικό μοντέλο (π.χ. `LOCAL (gemma4:12b-q4_K_M)`) αντί για το γενικό `LOCAL (Ollama)`
  - Έκδοση αναβαθμίστηκε σε v4.10.1
- **GUI (`app.py`):**
  - Έκδοση αναβαθμίστηκε σε v4.10.1 (docstring, sidebar, footer)
  - Το hardware import επεκτάθηκε για να περιλαμβάνει `estimate_size_for_quant`, `VRAM_HEADROOM`
  - Το VRAM metric δείχνει πλέον το διαθέσιμο headroom (π.χ. `24.0 GB` + `16.8GB usable (70%)`)
  - Το κουμπί Save αποθηκεύει πλέον και τις επιλογές cloud μοντέλων στο `.env`
- **`core/hardware.py`:**
  - Όλα τα VRAM thresholds ενοποιήθηκαν υπό το `VRAM_HEADROOM = 0.70`
  - `recommend_model()`, `get_all_chat_models_sorted()`, `get_ollama_library_models()`, `get_bitnet_models()` — όλα χρησιμοποιούν `VRAM_HEADROOM`

### Διορθώσεις
- **`PermissionError` στο `api_keys_menu`:** Η εγγραφή του `.env` χρησιμοποιεί πλέον στρατηγική 3 προσπαθειών (direct write → chmod + write → atomic tempfile + `os.replace()`), με graceful fallback μήνυμα σφάλματος αν το αρχείο είναι read-only στα Windows

### Αρχεία που άλλαξαν
| Αρχείο | Αλλαγή |
|---|---|
| `talos.py` | v4.10.1, Model Management καταχώρηση μενού, header με μοντέλο, PermissionError fix |
| `app.py` | v4.10.1, quantization dropdown, VRAM badges, cloud model selectors |
| `core/hardware.py` | `estimate_size_for_quant()`, `QUANT_SIZE_PER_BILLION`, `VRAM_HEADROOM=0.70` |
| `scripts/model_manager.py` | **Νέο** — 608 γραμμών TUI για model management |

---

## [v4.10.0] - 2026-06-30 - "Zero-Config & Resilience"

Αυτή η έκδοση μετατρέπει τον TALOS σε ένα πλήρως αυτόνομο σύστημα που λειτουργεί με 100% δωρεάν, keyless APIs. Προσθέτει Tiered API Keys management (GUI + TUI), API Health Check με tqdm progress bar, Smart Ollama Model Selector (installed + Ollama library + BitNet 1-bit), PDF Downloader (Unpaywall / OpenAlex), Health Check στο TUI, και πολλές διορθώσεις UX/UI.

### Προσθήκες
- **Tiered API Keys Management:**
  - GUI: Ενιαία σελίδα Settings με 3 tabs (API Keys & Models, Profiles & PYTHIA, Diagnostics)
  - 4 sections: Free & Keyless, Premium AI, Academic APIs, Integrations
  - TUI: Νέο sub-menu Profile & Settings / API Keys Management με δυνατότητα edit κάθε key
  - Αποθήκευση μέσω python-dotenv στο αρχείο .env
- **API Health Check (v1.1):**
  - 25 API checks με tqdm progress bar σε πραγματικό χρόνο
  - Κατάσταση: [OK], [FAIL], [FREE], [NONE] χωρίς emoji
  - Real-time feedback — κανένα "πάγωμα" κατά τον έλεγχο
- **Smart Ollama Model Selector:**
  - 3-section dropdown: Installed on this PC | Available via Ollama | BitNet 1-bit (Edge/CPU)
  - VRAM detection + αυτόματο download μέσω ollama pull
  - BitNet b1.58 μοντέλα (7 μοντέλα, ~0.2GB ανα 1B παραμέτρους)
- **PDF Downloader (pdf_downloader.py):**
  - Unpaywall / OpenAlex keyless fallback
  - Λήψη PDF στο data/pdfs/ με timeout και retries
- **System Health Check (test_smoke.py):**
  - 78 checks (σύνταξη, imports, DB, AI Manager)
  - Ενσωμάτωση σε GUI και TUI
- **Docker Updates:**
  - Dockerfile με streamlit, TALOS_START_MODE
  - docker-compose.yml με port 8501
- **Onboarding Wizard (GUI):**
  - Full-screen wizard για νέους χρήστες (research goal / PYTHIA)
  - Αυτόματη αντιγραφή config.template.json εάν λείπει το config.json

### Αλλαγές
- **Sidebar: 8 → 6 σελίδες** (συνένωση Setup + Profile σε Settings)
- **Settings page:** 3 tabs αντί για 2 ξεχωριστές σελίδες
- **TUI:** VRAM detection στο header, KeyboardInterrupt graceful handling
- **example.env:** Πλήρες template με 21 keys σε 5 sections
- **start_talos.bat:** Interactive launcher με επιλογή CLI/GUI/Dashboard
- **Scientometrics Report:** Dark mode HTML, Quad-Layer KDE fix, Top Venues chart, Score table

### Διορθώσεις
- 17 use_container_width deprecation warnings
- KeyboardInterrupt (Ctrl+C) στο daily_search — επιστροφή στο menu αντί για crash
- API Health Check "πάγωμα" — tqdm progress bar με real-time feedback
- KeyError στο CHIRON knowledge_path_generator.py
- UnicodeDecodeError σε subprocess output λόγω ελληνικών χαρακτήρων

---

## [v4.9.0] - 2026-06-29 - Ενημέρωση "Streamlit GUI & Quality"

Αυτή η έκδοση μετατρέπει τον TALOS σε μια **πλήρη Web GUI εφαρμογή** με επαγγελματικό Streamlit interface, διατηρώντας παράλληλα το CLI μενού. Προσθέτει **smoke test suite** για ελέγχους υγείας, αναβαθμίζει την αναφορά επιστημομετρίας με dark mode και Quad-Layer στατιστικά, και διορθώνει σφάλματα που ανακαλύφθηκαν κατά την ενσωμάτωση του GUI.

### Προσθήκες
- **Streamlit Web GUI (`app.py`):** Πλήρης αντικατάσταση του CLI μενού σε 6 σελίδες (Home, Search & Discovery, Single Paper Evaluation, Analysis & Insights, Database Maintenance, Profile & Settings). Περιλαμβάνει επιλογή παρόχου AI (Local/Cloud), Database Dashboard με semantic search και φίλτρα, inline rendering αναφορών Markdown/HTML.
- **_gui_runner.py:** Wrapper που κάνει monkey-patch το `questionary` ώστε τα TALOS scripts να τρέχουν χωρίς πραγματική κονσόλα, επιτρέποντας εκτέλεση από subprocess.
- **Smoke Test Suite (`test_smoke.py`):** 78 αυτοματοποιημένοι έλεγχοι (σύνταξη 43 αρχείων, imports, database, AI Manager). Ενσωματωμένο σε CLI (Database Maintenance → επιλογή 8) και GUI (Profile & Settings).
- **Docker:** Το `Dockerfile` εγκαθιστά το `streamlit`, υποστηρίζει `TALOS_START_MODE` (streamlit/dashboard/cli). Το `docker-compose.yml` εκθέτει τις πόρτες 5000 και 8501.

### Αλλαγές
- **Αναβάθμιση έκδοσης σε v4.9.0** σε όλα τα αρχεία.
- **Αναφορά Επιστημομετρίας (`trend_analyzer.py`):** Dark mode HTML, διόρθωση KDE (προσθήκη operational_score), νέο γράφημα Top Venues, πίνακας Quad-Layer στατιστικών.
- Διόρθωση seaborn `FutureWarning` με προσθήκη `hue` και `legend=False`.

### Διορθώσεις
- **`KeyError: 'id'` στο CHIRON** όταν το sota_papers είναι κενό DataFrame.
- **`NoConsoleScreenBufferError`** κατά την εκτέλεση questionary-based scripts από subprocess.
- **`UnicodeDecodeError`** στα subprocess outputs λόγω ελληνικών χαρακτήρων.
- **Markdown table rendering** στο Streamlit expander.

## [v4.8.5] - 2026-06-29 - Ενημέρωση "Bug Hunt & Quality"

Αυτή η έκδοση είναι ένα εκτεταμένο **sprint διόρθωσης σφαλμάτων** που αντιμετωπίζει 15+ bugs σε όλα τα modules. Βασικές βελτιώσεις: ο εμπλουτισμός μεταδεδομένων χρησιμοποιεί πλέον **multi-source fallback chain** (OpenAlex → Crossref → DBLP → Semantic Scholar), ο recommender παράγει **δομημένες αναφορές** που ταιριάζουν με το terminal, και το κατώφλι ποιότητας προτάσεων αυξήθηκε από 4.0 σε **7.0**.

### Διορθώσεις
- **`sources/elsevier_source.py`:** Διορθώθηκε αναφορά `self` σε επίπεδο κλάσης που προκαλούσε `NameError` (Critical B1).
- **`scripts/grey_literature_miner.py`:** Διορθώθηκε λογική `try/except/else` που απέρριπτε πάντα τα αποτελέσματα Gemini (Critical B2). Διορθώθηκε config key `grey_literature_model` → `grey_research_model` (Critical B3).
- **`scripts/recalculate_scores.py`:** Διορθώθηκε απών `operational_score` στο SELECT και `scores_dict` (Critical B4).
- **`scripts/interactive_dashboard.py`:** Διορθώθηκε `AttributeError` όταν το semantic search επιστρέφει κενά αποτελέσματα (Critical B6).
- **`core/ai_manager.py`:** Διορθώθηκε ανύπαρκτο μοντέλο `gemma4:12b` → `gemma3:12b` (High B7).
- **`scripts/historic_search.py`:** Προστέθηκε απών `CORESource` (High B8).
- **`scripts/trend_analyzer.py`:** Διορθώθηκε CSS `max_width` → `max-width` (High B9).
- **`scripts/zotero_connector.py`:** Διορθώθηκε crash όταν το Zotero επιστρέφει `None` URL (High B10).
- **`core/database_manager.py`:** Αφαιρέθηκε duplicate `ALTER TABLE` που προκαλούσε "duplicate column" errors (High B11).
- **`scripts/metadata_enricher.py`:** Διορθώθηκαν 403 errors από υπερβολικά μεγάλα URLs (High B12).
- **`scripts/db_stats.py`:** Διορθώθηκε division by zero για άδεια βάση (Medium B17).
- **`talos.py`:** Καθαρίστηκε duplicate γραμμή env, περιττό `time.sleep`, κενά whitespace (Low B24/B25).

### Προσθήκες
- **Multi-Source Metadata Enrichment (v2.0):**
  - Νέες μέθοδοι `search_papers()` σε **OpenAlex**, **Crossref**, και **DBLP**.
  - Fallback chain: OpenAlex → Crossref → DBLP → Semantic Scholar.
  - Το Semantic Scholar παραλείπεται αυτόματα χωρίς API key.
  - Και οι 3 κύριες πηγές είναι δωρεάν.
- **Δομημένες Αναφορές Recommender (v4.1):**
  - Τα exports HTML, DOCX, MD ταιριάζουν πλέον με το terminal: Foundational → Clusters → SOTA.
  - Προστέθηκε `operational_score` σε όλα τα formats.
  - Φιλτράρισμα placeholder abstracts για καλύτερο clustering.
  - Το HTML έχει δύο tabs: **Structured Path** + **Top 50 Interactive Table**.

### Αλλαγές
- **Recommender threshold:** Default `min_score` από **4.0 → 7.0**.
- **Foundational papers:** Φιλτράρονται κατά score (≥7.0, fallback ≥5.0).
- **State-of-the-Art:** Ταξινόμηση κατά `publication_year` και φίλτρο score ≥7.0.

### Αφαίρεση
- **`core/ai_manager_clean.py`:** Διαγράφηκε ακέφαλο fragment (Critical B5).

## [v4.8.4] - 2026-06-28 - The "Multi-Provider & Web Search" Update

Αυτή η έκδοση μετατρέπει τον TALOS σε ένα **πλήρες multi-provider AI σύστημα** με 4 ανεξάρτητους παρόχους (Local, Hugging Face, DeepSeek, Gemini) και προσθέτει **ζωντανή αναζήτηση ιστού** στο Grey Literature Miner.

### Προσθήκες
- **Hugging Face Provider (Δωρεάν Cloud Inference):**
  - Ενσωμάτωση του Hugging Face Inference Providers API ως 4ου παρόχου AI.
  - Χρήση του νέου **OpenAI-compatible unified API** (`router.huggingface.co/v1`) για πλήρη συμβατότητα.
  - **Δωρεάν** χρήση χωρίς όρια — χρειάζεται μόνο ένα `HF_TOKEN` από το https://huggingface.co/settings/tokens.
  - **Interactive Model Selection:** Το `talos.py` εμφανίζει λίστα με τα 6 καλύτερα δωρεάν μοντέλα (Mixtral 8x7B, Llama 3.1 8B, Qwen2.5 7B, Mistral 7B, Phi-3, Gemma 2 2B).
  - **Auto-priority:** Το HF μπαίνει **πρώτο** στο `provider_priority` όταν είναι διαθέσιμο (δωρεάν > επί πληρωμή).

- **Live Web Search (Grey Literature Miner):**
  - Ενσωμάτωση του **DuckDuckGo Search** για ζωντανή αναζήτηση ιστού (`duckduckgo-search`).
  - **Δωρεάν, χωρίς API key** — άμεση λειτουργία.
  - **Query Optimization:** Το ελεύθερο κείμενο του χρήστη μετατρέπεται αυτόματα σε optimized search query από LLM πριν την αναζήτηση.
  - Τα web results ενσωματώνονται στο prompt για καλύτερη ποιότητα αναφορών.
  
- **Multi-Provider Fallback στο Grey Literature Miner:**
  - Το Miner πλέον χρησιμοποιεί τον **AIManager** αντί για απευθείας κλήσεις στο Gemini.
  - Ροή: Gemini Search Grounding → AIManager fallback (HF → DeepSeek → Local).
  - **Ανθεκτικότητα:** Ακόμα κι αν το Gemini έχει quota issues, το Miner συνεχίζει με άλλον provider.

- **`core/hardware.py` — Hardware Detection Module:**
  - Αυτόματη ανίχνευση GPU VRAM μέσω `nvidia-smi`.
  - Βάση δεδομένων με μεγέθη μοντέλων (4-bit quantized) για 20+ μοντέλα.
  - **Smart Model Recommendation:** Προτείνει το καλύτερο μοντέλο με βάση τη διαθέσιμη VRAM.

### Διορθώσεις Σφαλμάτων
- **`talos.py` — Missing `load_dotenv()`:**
  - Το `.env` δεν φορτωνόταν στο `talos.py`, με αποτέλεσμα το `HF_TOKEN` και άλλες μεταβλητές να μην είναι διαθέσιμες.
  - Προστέθηκε `from dotenv import load_dotenv; load_dotenv()` στο module level.
- **`grey_literature_miner.py` — Import Error:**
  - Διορθώθηκε το `from google import genai` που απαιτούσε το πακέτο `google-genai`.
  - Προστέθηκε το `google-genai` στο `requirements.txt`.
  - Προστέθηκε το `duckduckgo-search` στο `requirements.txt`.
- **Provider Priority:**
  - Διορθώθηκε: το Hugging Face μπαίνει **πρώτο** στο priority (insert(0)) αντί για τελευταίο (append).
  - Διορθώθηκε: το `TALOS_USE_LOCAL=1` αφαιρέθηκε από το `.env` — πλέον ορίζεται **μόνο** από το interactive prompt του `talos.py`.
- **HF Token with spaces:**
  - Τεκμηριώθηκε ότι τα `.env` values **δεν** πρέπει να έχουν κενά γύρω από το `=` (το `load_dotenv` δεν τα αφαιρεί).

### Βελτιώσεις
- **`ai_manager.py` v3.5:**
  - Προσθήκη Hugging Face provider με OpenAI-compatible client.
  - Κατάργηση του custom `_execute_huggingface_request` — χρησιμοποιεί το γενικό `_execute_openai_compatible`.
  - Το `generate_embeddings()` δοκιμάζει **πρώτα** local, μετά Gemini.
- **`talos.py`:**
  - **HF Model Selection Menu** με τα 6 καλύτερα δωρεάν μοντέλα.
  - Αυτόματη μεταβίβαση `HF_MODEL_NAME` σε subprocesses.
  - Το `load_dotenv()` καλείται στο module level για έγκαιρη φόρτωση του `.env`.
  - Διαχωρισμός `TALOS_USE_LOCAL` (ορίζεται μόνο από το prompt) από το `.env`.
- **`grey_literature_miner.py`:**
  - Πλήρης αναβάθμιση: DuckDuckGo search + query optimization + AIManager fallback.
  - **Graceful degradation:** κάθε βήμα έχει fallback — web search, Gemini, AIManager.
- **`requirements.txt`:**
  - Προσθήκη `google-genai`, `duckduckgo-search`.
- **`.clinerules`:**
  - Προστέθηκε documentation για την αδυναμία του editor να κάνει match ελληνικό κείμενο.
  - Τεκμηρίωση της αρχιτεκτονικής, των providers, και των γνωστών gotchas.

---


## [v4.8.3] - 2026-06-27 - The "Secure Local AI & Privacy" Update

Αυτή η έκδοση ενισχύει την **ασφάλεια και το απόρρητο** του τοπικού mode. Προσθέτει **έλεγχο και αυτόματη εγκατάσταση όλων των μοντέλων** κατά την εκκίνηση, **user consent** πριν από οποιοδήποτε fallback σε cloud, και **αμφίδρομο fallback** (local↔cloud) με ρητή έγκριση χρήστη.

### Προσθήκες
- **Model Pre-Verification (`_verify_local_models`):**
  - Κατά την επιλογή LOCAL mode, ο TALOS ελέγχει **μία φορά** ότι όλα τα απαιτούμενα μοντέλα (chat + embedding) είναι εγκατεστημένα.
  - Αν κάποιο μοντέλο λείπει, γίνεται αυτόματο `ollama pull`.
  - Το περιβάλλον `TALOS_MODELS_VERIFIED=1` μεταβιβάζεται σε όλα τα subprocesses, αποφεύγοντας επαναληπτικούς ελέγχους.
- **Privacy Guard: Cloud Fallback Consent:**
  - Όταν το τοπικό μοντέλο αποτύχει, ο TALOS **ΔΕΝ** στέλνει αυτόματα δεδομένα στο cloud.
  - Ο χρήστης ερωτάται κατά την εκκίνηση: "Allow cloud fallback if local fails?"
  - Αν απαντήσει **NO**, τα δεδομένα παραμένουν **πλήρως offline** — κανένα API call δεν φεύγει από τον υπολογιστή.
- **Αμφίδρομο Fallback:**
  - Σε CLOUD mode, ο χρήστης μπορεί να επιτρέψει fallback σε τοπικό μοντέλο αν το cloud αποτύχει ("Allow local fallback if cloud fails?").
  - Οι μεταβλητές `TALOS_ALLOW_CLOUD_FALLBACK` και `TALOS_ALLOW_LOCAL_FALLBACK` ελέγχουν τη συμπεριφορά.

### Διορθώσεις Σφαλμάτων
- **Local Provider Priority:**
  - Διορθώθηκε: όταν επιλέγεται LOCAL mode, το τοπικό μοντέλο μπαίνει **πρώτο** στο `provider_priority` (χρησιμοποιήθηκε `insert(0, 'local')` αντί για `append`).
  - Προηγουμένως το local προστίθετο τελευταίο, με αποτέλεσμα να δοκιμάζεται μόνο αφού αποτύχουν Gemini και DeepSeek.
- **Embedding Model Missing:**
  - Το `_ensure_local_model()` δεν έλεγχε την ύπαρξη του embedding model (`nomic-embed-text`).
  - Προστέθηκε αυτόματος έλεγχος και εγκατάσταση και για το embedding model.
- **Embedding Priority:**
  - Η `generate_embeddings()` δοκιμάζει πλέον **πρώτα** το τοπικό embedding model και μετά το Gemini (ήταν ανάποδα).
- **Maintenance Menu:**
  - Αποκαταστάθηκαν οι επιλογές 4-8 (Embedding Generator, Re-evaluate, Recalculate, Data Enricher, Trend Analyzer) που είχαν χαθεί κατά το refactoring.

### Βελτιώσεις
- **`talos.py`:**
  - Προσθήκη `_verify_local_models()` για κεντρικό έλεγχο μοντέλων.
  - Προσθήκη interactive prompts για cloud/local fallback consent.
  - Αυτόματη μεταβίβαση των `TALOS_MODELS_VERIFIED`, `TALOS_ALLOW_CLOUD_FALLBACK`, `TALOS_ALLOW_LOCAL_FALLBACK` σε subprocesses.
- **`ai_manager.py` v3.5:**
  - Παρακάμπτει το `_ensure_local_model()` στα subprocesses όταν τα μοντέλα έχουν ήδη επαληθευτεί.
  - Προστέθηκε security check πριν από cloud fallback (απαιτεί `TALOS_ALLOW_CLOUD_FALLBACK=1`).
  - Διόρθωση σειράς providers (`local` πρώτο) και embedding fallback (`local` πρώτο).

---


## [v4.8.2] - 2026-06-27 - The "Local AI & Resilience" Update

Αυτή η έκδοση εστιάζει στην **αυτονομία** και την **ανθεκτικότητα** του TALOS. Εισάγει υποστήριξη για **τοπικά μοντέλα AI (Ollama)** επιτρέποντας πλήρως offline λειτουργία χωρίς cloud dependencies, ενώ παράλληλα διορθώνει **16 κρίσιμα σφάλματα** που επηρέαζαν τη σταθερότητα του συστήματος.

### Προσθήκες
- **Υποστήριξη Τοπικού Μοντέλου AI (Ollama):**
  - Ενσωμάτωση του Ollama ως τρίτου παρόχου AI στον `AIManager`, παράλληλα με Gemini και DeepSeek.
  - Χρήση του **OpenAI-compatible API** του Ollama για πλήρη συμβατότητα με τον υπάρχοντα κώδικα (`/v1/chat/completions`).
  - **Αυτόματη εγκατάσταση μοντέλου:** Αν το επιλεγμένο μοντέλο δεν υπάρχει τοπικά, ο TALOS εκτελεί αυτόματα `ollama pull`.
  - **Τοπικά embeddings:** Υποστήριξη του Ollama Embeddings API (`/api/embed`) με το `nomic-embed-text` για semantic search χωρίς εξάρτηση από cloud.
  - **Interactive Mode Selection:** Το `talos.py` ρωτά τον χρήστη στην αρχή κάθε συνεδρίας αν θέλει να χρησιμοποιήσει τοπικό ή cloud μοντέλο.
  - **Graceful Degradation:** Αν ο Ollama server δεν είναι προσβάσιμος ή το μοντέλο αποτύχει, γίνεται αυτόματη απενεργοποίηση και fallback στους cloud providers.
  - **Νέες μεταβλητές περιβάλλοντος:** `TALOS_USE_LOCAL`, `LOCAL_MODEL_NAME`, `LOCAL_MODEL_BASE_URL`, `LOCAL_EMBEDDING_MODEL`, `LOCAL_MODEL_API_KEY`.

### Διορθώσεις Σφαλμάτων
- **🔴 CRITICAL: `db_stats.py` KeyError Crash:**
  - Η `get_database_statistics()` δεν επέστρεφε τα πεδία `elite_papers`, `missing_doi`, `embedded_papers` προκαλώντας `KeyError` στο `db_stats.py`. Προστέθηκαν όλα τα πεδία που λείπουν.
- **🔴 CRITICAL: Source Agents Crash χωρίς API Keys:**
  - Οι agents `elsevier_source`, `ieee_source`, `springer_source` και `openarchives_source` έκαναν `raise ValueError()` κατά το `__init__` αν έλειπαν API keys, σκοτώνοντας ολόκληρο το `daily_search.py` ακόμα και αν οι υπόλοιποι 10 agents ήταν λειτουργικοί.
  - **Λύση:** Προσθήκη `self.enabled` flag και graceful skip αντί για crash. Προσθήκη guard `if not getattr(self, "enabled", True): return []` σε κάθε `fetch_new_papers()`.
- **🟠 HIGH: `recommender.py` — Missing `operational_score`:**
  - Το SQL query στον Recommender δεν επέλεγε το `operational_score`, με αποτέλεσμα οι operational αξιολογήσεις να αγνοούνται πλήρως στη Στρατηγική Αναφορά Ανάγνωσης. Προστέθηκε το πεδίο που έλειπε.
- **🟠 HIGH: `interactive_dashboard.py` — ValueError στο Semantic Search Sort:**
  - Όταν κάποιο paper ID από τη βάση δεν υπήρχε στα αποτελέσματα του semantic search, η `.index()` πετούσε `ValueError`. Αντικαταστάθηκε με dictionary-based lookup.
- **🟠 HIGH: `daily_search.py` — Σιωπηλή Απώλεια Papers χωρίς DOI:**
  - Το deduplication χρησιμοποιούσε μόνο το DOI ως κλειδί, απορρίπτοντας σιωπηλά papers χωρίς DOI (π.χ. από DBLP, OpenArchives). Προστέθηκε fallback στο URL, ευθυγραμμίζοντας τη λογική με το `historic_search.py`.
- **🟡 MEDIUM: `crossref_source.py` — IndexError σε Κενό Title:**
  - Αν το Crossref API επέστρεφε `"title": []`, το `[][0]` προκαλούσε `IndexError`. Προστέθηκε έλεγχος κενής λίστας.
- **🟡 MEDIUM: `openalex_source.py` — KeyError αν Λείπει το `meta`:**
  - Η πρόσβαση `data['meta']` αντικαταστάθηκε με `data.get('meta', {})` για ασφαλή χειρισμό malformed API responses.
- **🟡 MEDIUM: `plos_source.py` — Dead Code `title_display`:**
  - Το πεδίο `title_display` δεν περιλαμβανόταν στο `fl` parameter του API request, καθιστώντας το `doc.get("title_display", ...)` πάντα `None`. Διορθώθηκε η σειρά των fallbacks.
- **🟡 MEDIUM: `database_manager.py` — `duplicate column name` Warning:**
  - Το `ALTER TABLE` για το `operational_score` εκτελούνταν χωρίς έλεγχο ύπαρξης, προκαλώντας θορυβώδες error message σε κάθε εκκίνηση. Προστέθηκε `PRAGMA table_info` check πριν το ALTER.

### Βελτιώσεις
- **`ai_manager.py` v3.4 → v3.5:**
  - Πλήρης αναδιοργάνωση του provider system με υποστήριξη local models.
  - Το `generate_embeddings()` υποστηρίζει πλέον fallback σε τοπικό embedding model.
  - Το `_execute_request()` υποστηρίζει τον `local` provider παράλληλα με Gemini και DeepSeek.
- **`talos.py`:**
  - Προσθήκη interactive prompt για επιλογή Local/Cloud στην αρχή κάθε συνεδρίας.
  - Αυτόματη μεταβίβαση της επιλογής σε όλα τα subprocesses μέσω `TALOS_USE_LOCAL` environment variable.
- **`database_manager.py`:**
  - Η `get_database_statistics()` επιστρέφει πλέον `elite_papers`, `missing_doi` και `embedded_papers`.

---


## [v4.8.1] - 2026-05-08 - Ενημέρωση Φορητότητας & Docker

Αυτή η έκδοση εστιάζει στην άμεση και απρόσκοπτη εκτέλεση της εφαρμογής (Zero-Friction Deployment), καθιστώντας τον Τάλω προσβάσιμο σε ερευνητές ανεξαρτήτως του τεχνικού τους υπόβαθρου.

### Προσθήκες
- **Υποστήριξη Docker:**
  - Προσθήκη `Dockerfile` βασισμένο στο ελαφρύ `python:3.10-slim`.
  - Προσθήκη `docker-compose.yml` για εύκολη ενορχήστρωση, μόνιμη αποθήκευση δεδομένων (volumes) και υποστήριξη διαδραστικού τερματικού (TTY).
- **1-Click Launcher (Windows):**
  - Προσθήκη του `start_talos.bat` που αυτοματοποιεί πλήρως τη δημιουργία εικονικού περιβάλλοντος (venv) και την εγκατάσταση βιβλιοθηκών, επιτρέποντας την εκκίνηση με διπλό κλικ.
- **Τεκμηρίωση:** 
  - Ενημέρωση του `README.md` με τις νέες μεθόδους εγκατάστασης για άμεση χρήση.

---

## [v4.8.0] - 2025-12-20 - The "Enrichment & Scientometrics" Update

Αυτή η έκδοση αποτελεί ορόσημο για το Project TALOS, καθώς μετασχηματίζει τη βάση δεδομένων από μια παθητική λίστα βιβλιογραφίας σε έναν **ενεργό κόμβο (Hub) διασυνδεδεμένης γνώσης**. Εισάγει τη δυνατότητα μαζικού εμπλουτισμού δεδομένων από τρίτες πηγές και προσφέρει για πρώτη φορά "μακροσκοπική" εποπτεία του ερευνητικού πεδίου μέσω προηγμένων οπτικοποιήσεων.

### Added
- **NEW MODULE: Scientometrics Suite (`scripts/trend_analyzer.py`):**
  - Ένα νέο υποσύστημα που παράγει **HTML Reports** με στατιστικές αναλύσεις και οπτικοποιήσεις, χρησιμοποιώντας `matplotlib`, `seaborn` και `wordcloud`.
  - **Available Visualizations:**
    - **Research Timeline:** Ραβδόγραμμα δημοσιεύσεων ανά έτος (εντοπισμός "εκρήξεων" ενδιαφέροντος).
    - **Quality Landscape (KDE Plots):** Καμπύλες πυκνότητας για την κατανομή των Strategic/Tactical/Overall scores.
    - **Open Access Landscape:** Κυκλικό διάγραμμα (Pie Chart) για την κατανομή της προσβασιμότητας (Gold, Green, Hybrid, Closed).
    - **Keyword Dominance (WordCloud):** Σημασιολογική ανάλυση τίτλων για τον εντοπισμό κυρίαρχων τάσεων (π.χ. "Reinforcement Learning", "UAV").
    - **Top Authors:** Ανάλυση των πιο παραγωγικών ερευνητών στη βάση.

- **NEW MODULE: Data Enricher (`scripts/data_enricher.py`):**
  - Αντικαθιστά και επεκτείνει το παλιό `pdf_retriever.py`.
  - **Λειτουργία "Hub":** Συνδέεται με το **Unpaywall API** και ανακτά εξωτερικά αναγνωριστικά (`openalex_id`, `pmid`, `pmcid`) μετατρέποντας την τοπική βάση σε γέφυρα μεταξύ διαφορετικών ακαδημαϊκών οικοσυστημάτων.
  - **Smart Metadata:** Εμπλουτίζει τις εγγραφές με `oa_status`, `journal_issn` και διορθωμένους εκδότες (`publisher`).
  - **Aggressive Initialization:** Ενσωματώνει μηχανισμό `force_reset_status` που διορθώνει αυτόματα παλαιότερες εγγραφές με `NULL` status, διασφαλίζοντας ότι κανένα άρθρο δεν μένει ανεπεξέργαστο.

- **Infrastructure & Migration Tools:**
  - **`scripts/upgrade_to_v4_8.py`:** Αυτόνομο εργαλείο ασφαλούς αναβάθμισης που δημιουργεί Backup και εφαρμόζει το νέο σχήμα (Schema Migration) στη βάση του ενεργού προφίλ.
  - **`scripts/fix_missing_columns.py`:** Emergency script που σαρώνει αναδρομικά όλους τους φακέλους προφίλ για να εντοπίσει και να επιδιορθώσει βάσεις με παρωχημένο σχήμα.

### Changed
- **Database Schema Evolution (Core v5.2):**
  - Ο πίνακας `papers` επεκτάθηκε με 9 νέες στήλες: `oa_pdf_url`, `openalex_id`, `pmid`, `pmcid`, `oa_status`, `journal_issn`, `publisher`, `enrichment_status`.
  - Η στήλη `enrichment_status` (INTEGER) λειτουργεί ως state machine (0=Pending, 1=Enriched, 2=Failed) για τον έλεγχο της ροής εργασιών.

- **Core Architecture (`core/database_manager.py`):**
  - **Profile Awareness:** Ο `DatabaseManager` πλέον δέχεται προαιρετικό όρισμα `db_path` κατά την αρχικοποίηση, επιτρέποντας στα scripts συντήρησης να στοχεύουν δυναμικά τη βάση του ενεργού προφίλ αντί για τη default.
  - **Batch Operations Fix:** Η μέθοδος `update_papers_enrichment_batch` υλοποιήθηκε με χρήση `executemany` για ταχύτητα, ενώ διορθώθηκε κρίσιμο σφάλμα `sqlite3.InterfaceError` (Binding Error) που προέκυπτε όταν έλειπαν κλειδιά από το λεξικό ενημέρωσης.

- **UX / Menu (`talos.py`):**
  - Το μενού "Εργαλεία Συντήρησης" αναδιοργανώθηκε πλήρως.
  - Προστέθηκε αυτόματη ανίχνευση του ενεργού Database Path, το οποίο περνιέται ως όρισμα στα scripts `trend_analyzer` και `data_enricher`, λύνοντας προβλήματα ασυμβατότητας σε περιβάλλοντα με πολλαπλά προφίλ.

### Fixed
- **Critical Binding Error:** Διορθώθηκε σφάλμα στο `data_enricher.py` όπου η αποτυχία εύρεσης δεδομένων οδηγούσε σε ελλιπή λεξικά και κατάρρευση της βάσης κατά την εγγραφή. Πλέον, το script επιστρέφει πλήρη λεξικά με τιμές `None` (Null Object Pattern).
- **Null Status Bug:** Διορθώθηκε λογικό σφάλμα όπου τα SQL queries αγνοούσαν εγγραφές με `enrichment_status IS NULL`.
---

## [v4.7.1] - 2025-11-30 - The "HERMES" Performance Update

Αυτή η έκδοση βελτιώνει δραματικά την ταχύτητα του `pdf_retriever.py` (Project HERMES).

### Changed
- **Multithreaded PDF Retrieval:**
  - Η λογική του `pdf_retriever.py` ξαναγράφτηκε πλήρως για να χρησιμοποιεί **Multithreading** μέσω ενός `ThreadPoolExecutor`.
  - Το script πλέον εκτελεί πολλαπλές (default: 15) κλήσεις στο Unpaywall API ταυτόχρονα, αντί για σειριακά.
  - **Αποτέλεσμα:** Η διαδικασία ελέγχου για Open Access PDFs είναι πλέον ~10-15 φορές ταχύτερη, μειώνοντας τον χρόνο αναμονής από ώρες σε λεπτά.
---

## [v4.7.0] - 2025-11-30 - The PDF Retriever Update (Ethical Edition)

### Added
- **NEW MODULE: Project PDF Retriever (`scripts/pdf_retriever.py`):**
  - Ένα εργαλείο συντήρησης που σαρώνει τη βάση για άρθρα με DOI.
  - Καλεί το **Unpaywall API** για να εντοπίσει νόμιμες, **Open Access** εκδόσεις των PDF.
  - Αποθηκεύει τα links σε μια νέα στήλη `oa_pdf_url` στη βάση, προωθώντας την "Ανοιχτή Επιστήμη".

### Changed
- **Database Schema (v5.1):** Προστέθηκε η στήλη `oa_pdf_url` για την αποθήκευση των links.
---

## [v4.6.0] - 2025-11-30 - The "ORACLE" Update

Εισαγωγή του Project ORACLE για τον εντοπισμό "Γκρίζας Βιβλιογραφίας" (Grey Literature), αξιοποιώντας τα νέα μοντέλα Gemini 2.0 και τη δυνατότητα Google Search Grounding.

### Added
- **NEW MODULE: Project "ORACLE" (`scripts/oracle_agent.py`):**
  - **Ρόλος:** Εκτελεί "Horizon Scanning" στο διαδίκτυο για πόρους που δεν βρίσκονται σε ακαδημαϊκές βάσεις (GitHub code, Datasets, Technical Reports).
  - **Τεχνολογία:** Χρησιμοποιεί το SDK `google-genai` και το μοντέλο `gemini-2.0-flash-exp` (ή Pro) με ενεργοποιημένο το εργαλείο **Google Search**.
  - **Έξοδος:** Παράγει Markdown αναφορές με συνδέσμους, αποθηκευμένες στο `reports/oracle_deep_research/`.
- **Config:** Προστέθηκε η ρύθμιση `deep_research_model`.

### Changed
- **TALOS Menu:** Προστέθηκε η επιλογή "4. ORACLE" στο κεντρικό μενού.
---

## [v4.4.0] & [v4.5.0] - 2025-11-30 - The "Open Access & Onboarding" Update

Αυτή η έκδοση βελτιώνει δραματικά την προσβασιμότητα του TALOS. Από τη μία πλευρά, "ανοίγει" το σύστημα σε νέους χρήστες μέσω ενός αυτοματοποιημένου οδηγού εγκατάστασης. Από την άλλη, επεκτείνει τις πηγές δεδομένων με την προσθήκη του PLOS, ενός κολοσσού της Ανοιχτής Πρόσβασης.

### Added
- **NEW AGENT: `sources/plos_source.py` (Project ALEXANDRIA):**
  - Ενσωμάτωση του Public Library of Science (PLOS) API.
  - Εξασφαλίζει πρόσβαση σε υψηλής ποιότητας, Open Access άρθρα, διευκολύνοντας τη μελλοντική ανάκτηση πλήρους κειμένου.
  - Χρησιμοποιεί σύνταξη Apache Solr για ακριβή ερωτήματα.
- **Onboarding Wizard (`talos.py`):**
  - Νέα λειτουργία `check_first_run` που ανιχνεύει νέες εγκαταστάσεις.
  - Δημιουργεί αυτόματα το `config.json` από πρότυπο.
  - Εκκινεί αυτόματα την "Πυθία" για να ρυθμίσει το πρώτο ερευνητικό προφίλ του χρήστη, μειώνοντας το χρόνο εκμάθησης (Time-to-Value) στο ελάχιστο.
- **Config Templates:** Προστέθηκαν τα αρχεία `config.template.json` και `.gitignore` για την υποστήριξη της διανομής Open Source.

### Changed
- **Config Update:** Ενημερώθηκαν τα `daily_search.py` και `historic_search.py` για να συμπεριλάβουν το PLOS στις πηγές αναζήτησης.
---

## [v4.3.1] - 2025-11-30 - The Batch Execution Fix

Αυτή η έκδοση διορθώνει ένα κρίσιμο σφάλμα στη βάση δεδομένων που εμπόδιζε τη μαζική αποθήκευση των embeddings, και βελτιστοποιεί την ταχύτητα εγγραφής.

### Fixed
- **Database Batch Operations (`core/database_manager.py` v4.7):**
  - Διορθώθηκε το σφάλμα `sqlite3.ProgrammingError: Incorrect number of bindings supplied` που εμφανιζόταν κατά τη μαζική ενημέρωση των embeddings.
  - Προστέθηκε η νέα μέθοδος `execute_many()` στον `DatabaseManager`, η οποία αξιοποιεί τη λειτουργία `executemany` της SQLite για ασφαλείς και ταχύτατες μαζικές εγγραφές/ενημερώσεις.
  - Η μέθοδος `update_embeddings_batch` ενημερώθηκε ώστε να χρησιμοποιεί τη νέα λειτουργικότητα, επιτρέποντας την αποθήκευση χιλιάδων embeddings σε δευτερόλεπτα.


## [v4.3.0] - 2025-11-28 - The "Soft Shutdown" Update

Αυτή η έκδοση εστιάζει στη βελτίωση της Εμπειρίας Χρήστη (UX) και στη διαχείριση των διεργασιών, λύνοντας το πρόβλημα του "βίαιου" τερματισμού του Dashboard και επιτρέποντας την ομαλή επιστροφή στο μενού.

### Added
- **Dashboard Soft Shutdown:**
  - Προστέθηκε κουμπί **"🔴 Έξοδος & Επιστροφή στο Μενού"** στο UI του `dashboard.html`.
  - Υλοποιήθηκε νέο API endpoint `/api/shutdown` στο `interactive_dashboard.py` (v2.2), το οποίο τερματίζει ομαλά τον Flask server χρησιμοποιώντας threading και signals, χωρίς να "σκοτώνει" το κέλυφος.

### Changed
- **Talos Process Manager (`talos.py` v3.5):**
  - Η συνάρτηση `run_script` αναβαθμίστηκε ώστε να αναγνωρίζει και να διαχειρίζεται "έξυπνα" τους κωδικούς εξόδου του Dashboard.
  - Πλέον, ο τερματισμός του server δεν εκλαμβάνεται ως "Σφάλμα" (Crash), αλλά ως ηθελημένη ενέργεια, επιστρέφοντας τον χρήστη απευθείας στο Κεντρικό Μενού.

### Fixed
- **Workflow Interruption:** Εξαλείφθηκε η ανάγκη χρήσης `Ctrl+C` στο τερματικό για τη διακοπή του Web Server, η οποία προηγουμένως τερμάτιζε ολόκληρη την εφαρμογή TALOS.
---

## [v4.2.0] - 2025-11-28 - The Pythia Refinement & Architecture Hardening

Αυτή η έκδοση αποτελεί την οριστική ωρίμανση του υποσυστήματος "PYTHIA" και του μηχανισμού διαχείρισης προφίλ. Αντιμετωπίζει σύνθετα αρχιτεκτονικά προβλήματα που προέκυψαν κατά τη δημιουργία εντελώς νέων ερευνητικών θεμάτων (π.χ. Ιστορία αντί για Ρομποτική) και καθιστά τον TALOS πραγματικά "Universal Research Tool".

### Changed
- **AIManager v3.4 (System Prompt Override):**
  - Εισήχθη η δυνατότητα **παράκαμψης (override)** του προεπιλεγμένου `system_prompt`.
  - **Αιτιολόγηση:** Όταν η "Πυθία" προσπαθούσε να ρυθμίσει το σύστημα, το AI μπερδευόταν επειδή το `AIManager` φόρτωνε αυτόματα το prompt του "PhD Advisor". Τώρα, η Πυθία μπορεί να επιβάλει το δικό της ρόλο ("Research Architect") χωρίς παρεμβολές.
- **AIManager v3.3 (Surgical JSON Cleaning):**
  - Υλοποιήθηκε νέος μηχανισμός "χειρουργικού" καθαρισμού των απαντήσεων του AI.
  - Αντί να αποτυγχάνει όταν το μοντέλο (ειδικά το DeepSeek) επιστρέφει Markdown code blocks ή προλογικά σχόλια, ο AIManager εντοπίζει και εξάγει αυστηρά το JSON αντικείμενο (από το πρώτο `{` έως το τελευταίο `}`).
- **ArxivSource v3.8 (Config-Driven Architecture):**
  - Καταργήθηκαν οι "καρφωτοί" (hardcoded) όροι αναζήτησης μέσα στον κώδικα Python.
  - Ο πράκτορας πλέον διαβάζει το `arxiv_query` απευθείας από το `config.json` και το μετατρέπει δυναμικά σε λίστα για τη στρατηγική Multi-Query. Αυτό επιτρέπει στην Πυθία να αλλάζει αποτελεσματικά το αντικείμενο αναζήτησης του ArXiv.

### Fixed
- **Profile Manager Auto-Save Bug:** Διορθώθηκε ένα κρίσιμο σφάλμα όπου οι αλλαγές που έκανε η Πυθία στο `config.json` δεν αποθηκεύονταν μόνιμα στον φάκελο του ενεργού προφίλ (`_profiles/<name>/`). Πλέον, μετά την εκτέλεση της Πυθίας, γίνεται αυτόματη αποθήκευση (force save) στο προφίλ.
- **Pythia JSON Flattening:** Το script `query_translator.py` (v2.3) έγινε ανθεκτικό σε nested JSON απαντήσεις. Χρησιμοποιεί αναδρομική συνάρτηση `flatten_json` για να εντοπίσει τα κλειδιά των queries (`arxiv_query`, κλπ.) ανεξάρτητα από το πόσο βαθιά τα έχει "κρύψει" το AI στη δομή της απάντησης.

---

## [v4.1.0] - 2025-11-28 - The Quad-Layer Architecture & Profile System

Αυτή η έκδοση επανακαθορίζει τον πυρήνα της επιστημονικής αξιολόγησης του TALOS και εισάγει τη δυνατότητα διαχείρισης πολλαπλών ερευνητικών ταυτοτήτων.

### Added
- **Quad-Layer Evaluation Framework:**
  - Το σύστημα αξιολόγησης επεκτάθηκε από 3 σε **4 επίπεδα**, αντικατοπτρίζοντας πλήρως την αρχιτεκτονική της διατριβής:
    1.  **Strategic** (High-level decision making)
    2.  **Operational** (Auction-based mechanisms, resource allocation) - **ΝΕΟ**
    3.  **Tactical** (DRL/MARL policies)
    4.  **Playground** (Simulation)
  - Η βαρύτητα του `overall_score` αναπροσαρμόστηκε σε: 30% Strategic, 30% Operational, 30% Tactical, 10% Playground.
- **Profile Management System (`scripts/profile_manager.py`):**
  - Δυνατότητα δημιουργίας και εναλλαγής μεταξύ διαφορετικών "Προφίλ" έρευνας (π.χ., "Drones", "Bioinformatics").
  - Κάθε προφίλ διατηρεί το δικό του απομονωμένο `config.json` και τη δική του βάση δεδομένων `talos_research.db` μέσα στον φάκελο `_profiles/`.
  - Ενσωμάτωση στο κεντρικό μενού (`talos.py`) με νέα επιλογή "Διαχείριση Προφίλ".

### Changed
- **Database Schema Upgrade (v5.0):**
  - Προστέθηκε η στήλη `operational_score` στον πίνακα `papers`.
  - Δημιουργήθηκε το script `scripts/upgrade_to_v4.py` για την αυτόματη αναβάθμιση υφιστάμενων βάσεων και τον μηδενισμό των ημερομηνιών αξιολόγησης, ώστε να επιβληθεί επανα-αξιολόγηση με τα 4 επίπεδα.
  - Δημιουργήθηκε το script `scripts/fix_column_order.py` για την τακτοποίηση της σειράς των στηλών στη SQLite.
- **Re-evaluation Logic:** Το script `reevaluate_database.py` αναβαθμίστηκε (v5.0) για να υποστηρίζει και να καταγράφει τα 4 scores στα logs.
- **Dashboard Update:** Το `dashboard.html` και το `interactive_dashboard.py` ενημερώθηκαν για να εμφανίζουν το "Article DNA" με 4 μπάρες (συμπεριλαμβανομένης της Operational) και τη νέα στήλη βαθμολογίας.
- **Config & Prompts:** Τα `phd_focus_system_prompt` και `pre_screening_prompt` ξαναγράφτηκαν πλήρως για να εκπαιδεύσουν το AI στη νέα δομή των 4 επιπέδων.

---

## [v4.0.0] - 2025-11-28 - Project "PYTHIA" (Automated Configuration)

Η γέννηση της "Πυθίας". Αυτή η έκδοση μετατρέπει τον TALOS από ένα στατικό εργαλείο σε μια δυναμική πλατφόρμα που μπορεί να αυτο-ρυθμίζεται.

### Added
- **NEW MODULE: Project "PYTHIA" (`scripts/query_translator.py`):**
  - Ένας αυτοματισμός που χρησιμοποιεί το AI για να μετατρέψει έναν ερευνητικό στόχο φυσικής γλώσσας (π.χ., "I want to study climate change") σε:
    1.  Βελτιστοποιημένα **Boolean Search Queries** για 10+ διαφορετικά APIs (ArXiv, Scopus, IEEE, κλπ), τηρώντας τους συντακτικούς κανόνες του καθενός.
    2.  Προσαρμοσμένα **System Prompts** (`phd_focus`, `pre_screening`) που επαναπροσδιορίζουν τα κριτήρια αξιολόγησης για το νέο θέμα.
  - Αυτόματη ενημέρωση του αρχείου `config.json` με τις νέες παραμέτρους.

### Changed
- **Config Expansion:** Προστέθηκε το `query_translator_prompt` στο `config.json`, το οποίο λειτουργεί ως "Meta-Prompt", δίνοντας οδηγίες στο AI για το πώς να συμπεριφέρεται ως "Research Architect" για τη δημιουργία των ρυθμίσεων.




## [v3.2.2] - 2025-11-27 - API Rate Limit Optimization

Αυτή η έκδοση εστιάζει αποκλειστικά στη βελτιστοποίηση της διαχείρισης των κλήσεων προς το AI API, προκειμένου να αποφευχθεί η υπέρβαση των ορίων ταχύτητας (RPM - Requests Per Minute) κατά τη διάρκεια μαζικών εργασιών.

### Changed
- **Δυναμικό Rate Limiting:**
  - Εισήχθη η παράμετρος `ai_request_delay` στο `config.json` (default: 5 δευτερόλεπτα).
  - Τα scripts `historic_search.py`, `daily_search.py` και `reevaluate_database.py` ενημερώθηκαν ώστε να διαβάζουν αυτή την παράμετρο και να εφαρμόζουν την αντίστοιχη καθυστέρηση μεταξύ των αξιολογήσεων.
  - Αυτή η αλλαγή αποτρέπει το σφάλμα `429 Resource Exhausted` στο Gemini Flash, διασφαλίζοντας τη συνεχή λειτουργία χωρίς την πρόωρη ενεργοποίηση του Circuit Breaker.

## [v3.2.1] - 2025-09-27 - The "Metrics" Update

Μια μικρή αλλά χρήσιμη αναβάθμιση που προσθέτει ορατότητα στην κατάσταση της βάσης δεδομένων μετά από μαζικές εισαγωγές.

### Added
- **NEW SCRIPT: `scripts/db_stats.py`:** Ένα εργαλείο που παρέχει μια γρήγορη αναφορά για το πλήθος των άρθρων, την κατανομή ανά πηγή, τον μέσο όρο βαθμολογίας και την πληρότητα των μεταδεδομένων (DOIs, Embeddings).
- **Database Statistics:** Νέα μέθοδος `get_database_statistics` στον `DatabaseManager`.

## [v3.2.0] - 2025-09-27 - Operation "Genesis"

Αυτή η έκδοση αποτελεί μια θεμελιώδη αναβάθμιση της υποδομής συλλογής δεδομένων του TALOS. Ο στόχος του "Operation Genesis" ήταν να διασφαλίσει ότι όλα τα δεδομένα που εισέρχονται στο σύστημα είναι της υψηλότερης δυνατής ποιότητας και πληρότητας, λύνοντας οριστικά το πρόβλημα των ελλιπών μεταδεδομένων από παλαιότερες εκδόσεις.

### Changed
- **BREAKING CHANGE - Πλήρης Αναβάθμιση όλων των "Πρακτόρων" (`sources/*.py`):**
  - Όλοι οι "Πράκτορες" (ArXiv, Scopus, IEEE, Semantic Scholar, Springer, OpenAlex, DBLP, CORE, Crossref, OpenArchives, OSTI, PubMed, Science.gov) ξαναγράφτηκαν και αναβαθμίστηκαν πλήρως.
  - **Τυποποιημένη Έξοδος:** Κάθε "Πράκτορας" επιστρέφει πλέον ένα τυποποιημένο λεξικό που περιέχει **ΠΑΝΤΑ** τα κρίσιμα πεδία: `doi`, `publication_year`, και `authors_str`, επιπλέον των ήδη υπαρχόντων.
  - **Βελτιωμένη Εξαγωγή Δεδομένων:** Η λογική εξαγωγής για κάθε "Πράκτορα" βελτιώθηκε για να χειρίζεται με μεγαλύτερη ακρίβεια τις ιδιαιτερότητες του κάθε API (π.χ., σύνθετη δομή συγγραφέων, διαφορετικά format ημερομηνιών).
  - **Καθαρότερος Κώδικας:** Όλοι οι "Πράκτορες" αναδιαρθρώθηκαν για να χρησιμοποιούν μια ξεχωριστή μέθοδο `_format_paper()`, κάνοντας τον κώδικα πιο αρθρωτό, ευανάγνωστο και εύκολο στη συντήρηση.
- **Βελτιωμένη Ανθεκτικότητα `ElsevierSource`:** Ο πράκτορας του Scopus υλοποιεί πλέον μια "έξυπνη" στρατηγική εμπλουτισμού, κάνοντας μια δεύτερη, στοχευμένη κλήση στο Abstract Retrieval API για να ανακτήσει την πλήρη περίληψη όταν αυτή λείπει από την αρχική αναζήτηση.

### Removed
- **Κατάργηση της Ανάγκης για "Μπαλώματα":** Με την ολοκλήρωση του "Genesis", η ανάγκη για το script `metadata_enricher.py` ("APOLLO") μειώνεται δραματικά για τις **νέες** εγγραφές. Το script παραμένει χρήσιμο για τη διόρθωση τυχόν παλαιότερων βάσεων, αλλά η στρατηγική είναι πλέον η συλλογή σωστών δεδομένων εξ αρχής.

## [v3.1.1] - 2025-09-27 - Stability & UX Finalization

Αυτή η έκδοση αποτελεί ένα "hotfix" release που ολοκληρώνει τη σταθεροποίηση του οικοσυστήματος μετά τις μεγάλες αλλαγές της v3.0 και βελτιώνει κρίσιμα σημεία της εμπειρίας χρήστη (UX) που εντοπίστηκαν κατά τις δοκιμές.

### Added
- **NEW MAINTENANCE MODULE: Project "APOLLO" (`scripts/metadata_enricher.py`)**
  - **Αιτιολόγηση:** Τα άρθρα που είχαν εισαχθεί στη βάση πριν την έκδοση v2.21.0 δεν είχαν πλήρη μεταδεδομένα (π.χ., έτος δημοσίευσης, DOI).
  - **Υλοποίηση:** Δημιουργήθηκε ένα νέο, "έξυπνο" εργαλείο συντήρησης που σαρώνει τη βάση για ελλιπείς εγγραφές. Για κάθε εγγραφή, κάνει μια στοχευμένη αναζήτηση στο Semantic Scholar API για να βρει το αντίστοιχο άρθρο και να "εμπλουτίσει" την τοπική εγγραφή με τα μεταδεδομένα που λείπουν.
  - **Ανθεκτικότητα:** Ο `SemanticScholarSource` αναβαθμίστηκε (v3.3) για να ενσωματώνει έναν στιβαρό μηχανισμό **"Exponential Backoff"**, κάνοντάς τον ανθεκτικό σε σφάλματα rate limiting (429) κατά τις μαζικές κλήσεις.

### Changed
- **"Έξυπνη" Ταυτοποίηση Συγγραφέα (`author_profiler.py` v3.9):**
  - **Ανίχνευση Εισόδου:** Το script μπορεί πλέον να δεχτεί ως είσοδο είτε **όνομα συγγραφέα** είτε απευθείας **ORCID iD**. Αν ανιχνεύσει ORCID iD, παρακάμπτει έξυπνα τη διαδικασία αναζήτησης.
  - **Εμπλουτισμένη Επιλογή (Enriched Disambiguation):** Όταν η αναζήτηση με όνομα επιστρέφει πολλαπλά αποτελέσματα, το script πλέον κάνει επιπλέον κλήσεις στο OpenAlex για να ανακτήσει το **τελευταίο γνωστό ίδρυμα** κάθε υποψηφίου. Η λίστα επιλογών που παρουσιάζεται στον χρήστη είναι πλέον εμπλουτισμένη (π.χ., "John Doe - [University of Oxford]"), κάνοντας την ταυτοποίηση εύκολη και αξιόπιστη.
- **Ενοποίηση `author_trajectory_analyzer.py` (v3.2):** Το script αναβαθμίστηκε για να μπορεί να δέχεται και αυτό είτε όνομα είτε ORCID iD, καλώντας εσωτερικά τον `author_profiler` όταν χρειάζεται.
- **Αναδιοργάνωση Κεντρικού Μενού (`talos.py` v3.4):** Οι λειτουργίες ανάλυσης συγγραφέα ομαδοποιήθηκαν σε ένα νέο, καθαρό υπο-μενού "Εργαλεία Ανάλυσης Συγγραφέα" για καλύτερη εμπειρία χρήστη.

### Fixed
- **Συμβατότητα Terminal (`talos.py` v3.3):** Διορθώθηκε το σφάλμα `NoConsoleScreenBufferError` που εμφανιζόταν σε περιβάλλοντα όπως το ενσωματωμένο τερματικό του VS Code. Το κεντρικό μενού χρησιμοποιεί πλέον μια ασφαλή μέθοδο "fallback".
- **Σφάλμα `TypeError` στο `author_profiler.py`:** Διορθώθηκε ένα `TypeError` που προκαλούνταν από την έλλειψη της σωστής εισαγωγής (`import`) της βιβλιοθήκης `tqdm`.
- **Σφάλμα `FileNotFoundError` στο `talos.py`:** Η συνάρτηση `run_script` αναβαθμίστηκε για να χρησιμοποιεί **απόλυτες διαδρομές (absolute paths)**, λύνοντας οριστικά τα προβλήματα εύρεσης των scripts.

---

## [v3.0.0] - 2025-09-26 - The Strategic Mentor (CHIRON)

Αυτή η έκδοση σηματοδοτεί τη μετάβαση του TALOS από ένα σύστημα ανακάλυψης και αξιολόγησης πληροφορίας σε έναν ενεργό στρατηγικό σύμβουλο που συνθέτει και παρουσιάζει τη γνώση με έξυπνο και εξατομικευμένο τρόπο. Η εστίαση μετατοπίζεται από το "τι" (what) στο "πώς" (how) και "γιατί" (why).

### Added
- **NEW MAJOR MODULE: Project "CHIRON" (`scripts/knowledge_path_generator.py`)**
  - Εισάγεται μια νέα, πανίσχυρη λειτουργία στο κεντρικό μενού (`talos.py`) που επιτρέπει στον χρήστη να ξεκινήσει έναν διάλογο σε φυσική γλώσσα.
  - Ο χρήστης περιγράφει έναν ερευνητικό στόχο (π.χ., "θέλω να μάθω για DRL και metaheuristics").
  - Ο "CHIRON" εκτελεί μια βαθιά σημασιολογική αναζήτηση σε ολόκληρη τη βάση δεδομένων για να βρει το πιο σχετικό "Σώμα Γνώσης".
  - Εφαρμόζει έναν αλγόριθμο **Δόμησης Γνώσης**, ο οποίος ταυτοποιεί τα "Θεμελιώδη", τα "State-of-the-Art" και ομαδοποιεί τα υπόλοιπα άρθρα σε "Θεματικές Ενότητες" χρησιμοποιώντας K-Means Clustering.
  - Στέλνει αυτή τη δομημένη γνώση σε ένα LLM (μέσω του `AIManager`), το οποίο συνθέτει μια πλήρη, **αφηγηματική αναφορά** σε Markdown, εξηγώντας στον χρήστη *γιατί* πρέπει να ακολουθήσει αυτό το μονοπάτι μελέτης.
- **Έξυπνη Οργάνωση Αναφορών "CHIRON":**
  - Οι αναφορές αποθηκεύονται πλέον σε **υποφακέλους με βάση την ημερομηνία** (`reports/knowledge_paths/YYYY-MM-DD/`).
  - Το όνομα του αρχείου της αναφοράς δημιουργείται "έξυπνα" καλώντας το AI για να **αποστάξει το ερώτημα του χρήστη σε 2-3 λέξεις-κλειδιά**, αποφεύγοντας τα τυπογραφικά λάθη και τα μεγάλα ονόματα αρχείων.

### Changed
- **Βελτιωμένες Αναφορές "CHIRON":**
  - Οι αναφορές περιλαμβάνουν πλέον **clickable Markdown links** για κάθε άρθρο, οδηγώντας απευθείας στο DOI ή το URL του.
  - Το **`overall_score`** κάθε άρθρου εμφανίζεται ευκρινώς δίπλα στον τίτλο του για άμεσο οπτικό πλαίσιο.
- **Αρχιτεκτονική Αναβάθμιση (Refactoring for CHIRON):**
  - Η λογική της σημασιολογικής αναζήτησης μεταφέρθηκε από το `interactive_dashboard.py` και ενσωματώθηκε ως κεντρική, επαναχρησιμοποιήσιμη μέθοδος (`semantic_search`) μέσα στον `DatabaseManager` (v4.4).
  - Ο `DatabaseManager` φορτώνει πλέον όλα τα embeddings στη μνήμη κατά την αρχικοποίηση για αστραπιαίες αναζητήσεις.
  - Το back-end του `interactive_dashboard.py` (v2.1) απλοποιήθηκε δραματικά.
- **Αρχείο Ρυθμίσεων (`config.json`):**
  - Προστέθηκε το νέο, εξειδικευμένο prompt `chiron_synthesizer_prompt` που καθοδηγεί το LLM στη συγγραφή των αφηγηματικών αναφορών, με ρητή οδηγία να διατηρεί τις βαθμολογίες και τα links.

### Fixed
- **Bug Μορφοποίησης Αναφοράς "CHIRON":** Διορθώθηκε το σφάλμα όπου εμφανιζόταν το `[None]` για άρθρα χωρίς έτος δημοσίευσης.
- **Bug Εκτέλεσης "CHIRON":** Διορθώθηκε το `AttributeError` που προκαλούσε τη συντριβή του script λόγω μιας μεθόδου που έλειπε.

## [v2.21.0] - 2025-09-26 - The Reliability Update

Αυτή είναι μια θεμελιώδης αναβάθμιση που εστιάζει στην αξιοπιστία, τη συμβατότητα και την ποιότητα του κώδικา, θέτοντας τις βάσεις για τις μελλοντικές εκδόσεις v3.x.

### Added
- **Πλήρης Τεκμηρίωση & Σχολιασμός:** Όλα τα core modules και τα scripts του project εμπλουτίστηκαν με αναλυτική τεκμηρίωση Google Style και εκτενή σχολιασμό στα ελληνικά.
- **Εργαλείο Μετάβασης Βάσης:** Δημιουργήθηκε το script `scripts/migrate_database_schema.py` (v2.2) για την ασφαλή και στιβαρή αναβάθμιση του σχήματος της βάσης δεδομένων από παλαιότερες εκδόσεις.

### Changed
- **BREAKING CHANGE - Αρχιτεκτονική JSON:**
  - Αναδιαμορφώθηκαν πλήρως τα prompts `phd_focus_system_prompt` και `pre_screening_prompt` στο `config.json` ώστε να απαιτούν αυστηρά έξοδο σε μορφή JSON.
  - Ο `AIManager` (v3.1) ανασχεδιάστηκε πλήρως για να είναι **Model-Independent**, να υποστηρίζει εγγενώς JSON mode και να διαθέτει provider-specific Circuit Breakers.
  - Ο `DatabaseManager` (v4.3) αναβαθμίστηκε με νέο, επεκτάσιμο σχήμα πίνακα για την αποθήκευση των δομημένων δεδομένων και εμπλουτίστηκε με πολλαπλές μεθόδους για πλήρη συμβατότητα.
  - Όλα τα scripts (`daily_search`, `zotero_connector`, `historic_search`, `reevaluate_database`, `interactive_dashboard`) αναβαθμίστηκαν πλήρως για να αξιοποιούν τη νέα, αξιόπιστη αρχιτεκτονική, καταργώντας την ανάγκη για parsing με regular expressions.
- **Συμβατότητα Python:** Διορθώθηκαν όλα τα `TypeError` στα core modules (`AIManager`, `DatabaseManager`) και στα scripts (`author_profiler`, `author_trajectory_analyzer`) αντικαθιστώντας τη σύνταξη type hinting `type | None` με το `typing.Union`, διασφαλίζοντας συμβατότητα με Python < 3.10.
- **Βελτιωμένες Αναφορές:** Οι αναφορές που παράγονται από το `recommender.py` και το `dashboard.html` (Info Card) αξιοποιούν πλέον τα νέα, πλούσια, δομημένα δεδομένα της βάσης.

### Removed
- **Κατάργηση Regex Parsing:** Όλες οι βοηθητικές συναρτήσεις που βασίζονταν σε regular expressions για την εξαγωγή δεδομένων από τις απαντήσεις του AI (π.χ., `extract_all_scores`) καταργήθηκαν οριστικά από ολόκληρο το project, καθώς είναι πλέον παρωχημένες.

## [2.20.1] - 2025-09-24 - "Smart Target" Selector for ORPHEUS

Αυτή η έκδοση αποτελεί μια σημαντική βελτίωση ποιότητας ζωής (quality of life) για το module "ORPHEUS" (`citation_analyzer.py`). Η διαδικασία επιλογής του "άρθρου-στόχου" γίνεται δραματικά πιο γρήγορη, έξυπνη και ενοποιημένη με το υπόλοιπο οικοσύστημα του TALOS.

### Βελτιώσεις

-   **Διαδραστική Επιλογή Άρθρου-Στόχου:**
    -   **Αιτιολόγηση:** Η προηγούμενη έκδοση απαιτούσε από τον χρήστη να βρίσκει και να αντιγράφει χειροκίνητα το DOI ή το URL ενός άρθρου για να ξεκινήσει η ανάλυση, μια διαδικασία αργή και επιρρεπής σε λάθη.
    -   **Υλοποίηση:** Το script `citation_analyzer.py` αναβαθμίστηκε για να προσφέρει πλέον δύο τρόπους επιλογής:
        1.  **Χειροκίνητη Εισαγωγή:** Η κλασική μέθοδος παραμένει διαθέσιμη.
        2.  **"Έξυπνη" Επιλογή από τη Βάση:** Το script συνδέεται πλέον με τη βάση `talos_research.db` και ανακτά μια λίστα με τα 10 πιο πρόσφατα "Core Papers" (άρθρα με `overall_score >= 7`). Στη συνέχεια, παρουσιάζει αυτή τη λίστα στον χρήστη μέσω ενός διαδραστικού μενού του `questionary`, επιτρέποντάς του να επιλέξει το άρθρο-στόχο με τα βελάκια του πληκτρολογίου.
-   **Βελτιωμένη Ταξινόμηση Επιλογών:** Η λίστα των "Core Papers" που παρουσιάζεται είναι πλέον ταξινομημένη κατά **φθίνοντα βαθμό συνάφειας (`overall_score`)**, εξασφαλίζοντας ότι τα πιο σημαντικά άρθρα εμφανίζονται πάντα στην κορυφή για ευκολότερη επιλογή.
-   **Αναβάθμιση του `DatabaseManager`:** Προστέθηκε μια νέα βοηθητική μέθοδος, `get_recent_core_papers`, για την αποδοτική ανάκτηση των παραπάνω δεδομένων από τη βάση.
-   **"Αλεξίσφαιρος" Χειρισμός Εισόδου:** Η λογική του `get_paper_identifier` βελτιώθηκε για να "καθαρίζει" αυτόματα τυχόν κενά που μπορεί να υπάρχουν σε ένα DOI που αντιγράφεται από ιστοσελίδες, αποτρέποντας σφάλματα `404 Not Found`.

## [2.20.0] - 2025-09-22 - The "ORPHEUS" Interactive Knowledge Graph

Αυτή η μεγάλη έκδοση εισάγει μια πανίσχυρη, νέα λειτουργία "Intel" στον TALOS: την **Ανάλυση Δικτύου Γνώσης**. Με το νέο module, με κωδικό όνομα "ORPHEUS", ο χρήστης μπορεί πλέον να επιλέξει ένα οποιοδήποτε "άρθρο-στόχο" και να λάβει μια πλήρη, οπτικοποιημένη ανάλυση του "οικοσυστήματός" του – δηλαδή, πάνω σε ποια θεμελιώδη έρευνα βασίστηκε και πώς η δική του συνεισφορά επηρέασε την επιστήμη που ακολούθησε.

### Νέα Λειτουργικότητα (Features)

-   **Δημιουργία του `scripts/citation_analyzer.py` ("ORPHEUS"):**
    -   Ένα νέο, αυτόνομο script που ενορχηστρώνει ολόκληρη τη διαδικασία ανάλυσης αναφορών.
    -   **Ροή Εργασίας:**
        1.  Δέχεται ως είσοδο ένα DOI ή URL ενός άρθρου.
        2.  Χρησιμοποιεί τον `SemanticScholarSource` για να βρει το άρθρο-στόχο.
        3.  Ανακτά τις λίστες με τις **βιβλιογραφικές αναφορές (references)** και τα **άρθρα που το αναφέρουν (citations)**.
        4.  Στέλνει αυτές τις λίστες στον `AIManager` για μια ποιοτική αξιολόγηση από το **Pro model**, εντοπίζοντας τα πιο σημαντικά "θεμελιώδη" και "εξελικτικά" άρθρα.
-   **Δημιουργία Διαδραστικού Γραφήματος Δικτύου:**
    -   **Αιτιολόγηση:** Μια απλή λίστα αναφορών δεν αρκεί για να αποτυπώσει τις πολύπλοκες σχέσεις. Η οπτικοποίηση είναι κρίσιμη.
    -   **Υλοποίηση:** Το script χρησιμοποιεί τη βιβλιοθήκη **`pyvis`** για να δημιουργήσει ένα **πλήρως διαδραστικό, αυτοτελές αρχείο HTML**. Αυτό το γράφημα απεικονίζει:
        -   Το άρθρο-στόχο ως κεντρικό, διακεκριμένο κόμβο.
        -   Τις αναφορές (references) ως κόμβους που "δείχνουν" προς τον στόχο.
        -   Τα citations ως κόμβους προς τους οποίους "δείχνει" ο στόχος.
        -   **Πλήρης Διαδραστικότητα:** Οι χρήστες μπορούν να κάνουν zoom, να μετακινούν τους κόμβους, και το πιο σημαντικό, να **κάνουν κλικ σε οποιονδήποτε κόμβο για να ανοίξουν το αντίστοιχο paper** σε νέα καρτέλα.
-   **Παραγωγή Αναφοράς Markdown:** Στο τέλος, το script παράγει μια πλήρη αναφορά σε μορφή Markdown που περιέχει την ανάλυση του AI και **ενσωματώνει έναν σύνδεσμο** προς το διαδραστικό γράφημα HTML.

### Βελτιώσεις

-   **Αναβάθμιση του `SemanticScholarSource`:** Ο πράκτορας του Semantic Scholar επεκτάθηκε δραματικά. Πλέον περιλαμβάνει νέες, εξειδικευμένες μεθόδους (`get_paper_details`, `get_paper_references`, `get_paper_citations`) που αξιοποιούν τα αντίστοιχα endpoints του API v1, καθιστώντας τον το κεντρικό εργαλείο για την ανάλυση αναφορών.
-   **Εκτενές Debugging & Σταθεροποίηση:** Επιλύθηκε μια σειρά από σφάλματα που σχετίζονταν με τη σύνταξη των παραγόμενων αρχείων (`JSONDecodeError` στο `pyvis`, λανθασμένες καταλήξεις αρχείων, λανθασμένη μορφοποίηση συνδέσμων Markdown) για να διασφαλιστεί η ομαλή και αξιόπιστη λειτουργία του νέου module.

## [2.19.1] - 2025-09-21 - Αναβάθμιση του "Trajectory Analyzer" με AIManager

Αυτή η έκδοση αποτελεί μια σημαντική αναβάθμιση "κάτω από το καπό" για το module ανάλυσης της ερευνητικής πορείας ενός συγγραφέα. Ο `author_trajectory_analyzer.py` αναδιαρθρώθηκε πλήρως για να ενσωματωθεί με τον κεντρικό `AIManager`, καθιστώντας τον πιο στιβαρό, συνεπή με την υπόλοιπη αρχιτεκτονική του TALOS και ικανό να παράγει αναλύσεις υψηλότερης ποιότητας.

### Βελτιώσεις

-   **Ενσωμάτωση με τον `AIManager`:**
    -   **Αιτιολόγηση:** Η προηγούμενη έκδοση του `Trajectory Analyzer` έκανε απευθείας κλήσεις στο Gemini API, παρακάμπτοντας την κεντρική λογική fallback και τον "Circuit Breaker" που είχαμε ήδη υλοποιήσει.
    -   **Υλοποίηση:** Ο κώδικας του `scripts/author_trajectory_analyzer.py` ξαναγράφτηκε για να μην αρχικοποιεί πλέον το δικό του AI client. Αντ' αυτού, δημιουργεί ένα instance του `AIManager` και του αναθέτει την εκτέλεση της ανάλυσης.
-   **Χρήση του "Pro" Model για Βέλτιστη Ποιότητα:**
    -   Η κλήση προς τον `AIManager` ορίζει ρητά τη χρήση του `model_type='pro'`. Αυτό διασφαλίζει ότι αυτή η κρίσιμη, στρατηγική ανάλυση θα εκτελείται πάντα από το πιο ισχυρό διαθέσιμο γλωσσικό μοντέλο (π.χ., Gemini Pro), παρέχοντας τα πιο βαθιά και διορατικά αποτελέσματα.
-   **Συνέπεια Κώδικα:** Με αυτή την αλλαγή, **όλα** τα scripts του TALOS που απαιτούν γλωσσική ανάλυση χρησιμοποιούν πλέον τον `AIManager`, ολοκληρώνοντας την αρχιτεκτονική μετάβαση σε ένα κεντρικοποιημένο, model-agnostic σύστημα AI.

## [2.19.0] - 2025-09-21 - The Zotero Bridge & "Smart Sync" Update

Αυτή η έκδοση-ορόσημο γεφυρώνει το χάσμα μεταξύ της ανακάλυψης νέας βιβλιογραφίας (TALOS) και της προσωπικής διαχείρισης γνώσης (Zotero). Εισάγεται ένα νέο, πανίσχυρο module, το "Zotero Bridge", το οποίο μετατρέπει τον TALOS σε έναν κεντρικό εγκέφαλο που μπορεί να συγχρονίσει, να εμπλουτίσει και να αναβαθμίσει την υπάρχουσα βιβλιοθήκη Zotero του χρήστη.

### Νέα Λειτουργικότητα (Features)

-   **Δημιουργία του "Zotero Bridge" (`scripts/zotero_connector.py`):**
    -   **Αιτιολόγηση:** Τα άρθρα που προστίθενται χειροκίνητα στο Zotero παρέμεναν εκτός του οικοσυστήματος αξιολόγησης του TALOS, ενώ οι αξιολογήσεις που γίνονταν από τον TALOS μπορούσαν να είναι χαμηλότερης ποιότητας (Flash model) από ό,τι θα άρμοζε σε ένα άρθρο που ο χρήστης έχει ήδη επιμεληθεί.
    -   **Υλοποίηση:** Δημιουργήθηκε ένα νέο, αυτόνομο script που υλοποιεί μια στρατηγική "Sync & Enrich with Pro Upgrade":
        1.  **Σύνδεση:** Χρησιμοποιεί τη βιβλιοθήκη `pyzotero` για να συνδεθεί με ασφάλεια στο Zotero Web API.
        2.  **Ανάκτηση:** "Διαβάζει" όλα τα άρθρα από τη βιβλιοθήκη Zotero του χρήστη.
        3.  **Έξυπνος Συγχρονισμός:** Για κάθε άρθρο από το Zotero, το script:
            -   **Το στέλνει ΠΑΝΤΑ για μια νέα, πλήρη, πολυδιάστατη αξιολόγηση** χρησιμοποιώντας το ισχυρό **Pro model** του AI.
            -   Ελέγχει αν το άρθρο υπάρχει ήδη στη βάση του TALOS.
            -   Αν υπάρχει, **αναβαθμίζει (UPDATE)** την υπάρχουσα εγγραφή με τη νέα, ανώτερης ποιότητας ανάλυση.
            -   Αν δεν υπάρχει, **δημιουργεί (INSERT)** μια νέα, πλήρως αξιολογημένη εγγραφή.
            -   Σε κάθε περίπτωση, διασφαλίζει ότι η στήλη `in_zotero` είναι ενημερωμένη.

### Βελτιώσεις

-   **Αναβάθμιση του `DatabaseManager`:**
    -   Προστέθηκαν νέες βοηθητικές μέθοδοι (`get_paper_id_by_url`, `get_single_paper_by_url`) για την υποστήριξη της νέας λειτουργίας.
    -   Η μέθοδος `add_paper` αναβαθμίστηκε για να δέχεται την κατάσταση `in_zotero` κατά τη δημιουργία μιας νέας εγγραφής.
-   **Ενοποίηση Ροής Εργασίας:** Το νέο script ενσωματώθηκε πλήρως στο κεντρικό μενού του `talos.py`, κάνοντας τη διαδικασία συγχρονισμού και εμπλουτισμού προσβάσιμη με το πάτημα ενός κουμπιού.

## [2.18.1] - 2025-09-21 - "Circuit Breaker" Smart Fallback

Αυτή η έκδοση αποτελεί μια σημαντική αναβάθμιση στην ευφυΐα και την ανθεκτικότητα του `AIManager`. Αντί για έναν απλό μηχανισμό "fallback", το σύστημα ενσωματώνει πλέον μια προηγμένη λογική "Circuit Breaker", κάνοντάς το δραματικά πιο γρήγορο και αποδοτικό όταν ο κύριος πάροχος AI (Gemini) φτάνει τα όριά του.

### Βελτιώσεις

-   **Υλοποίηση "Circuit Breaker" στον `core/ai_manager.py`:**
    -   **Αιτιολόγηση:** Η προηγούμενη έκδοση προσπαθούσε να καλέσει το Gemini API για *κάθε* άρθρο, ακόμα και αν το ημερήσιο όριο είχε ήδη εξαντληθεί. Αυτό προκαλούσε σημαντικές, περιττές καθυστερήσεις, καθώς περίμενε την αποτυχημένη απάντηση του Gemini πριν ενεργοποιήσει το fallback στο DeepSeek.
    -   **Υλοποίηση:** Ο `AIManager` είναι πλέον "κατάστασης-ενήμερος" (state-aware). Διατηρεί έναν εσωτερικό μετρητή συνεχόμενων αποτυχιών του Gemini που οφείλονται σε υπέρβαση ορίου (quota errors).
        -   Μετά από έναν προκαθορισμένο αριθμό αποτυχιών (π.χ., 5), ο "αυτόματος διακόπτης" (circuit breaker) "πέφτει".
        -   Για όλες τις επόμενες κλήσεις μέσα στην ίδια εκτέλεση του script, ο `AIManager` **παρακάμπτει εντελώς** την προσπάθεια κλήσης στο Gemini και στέλνει τα αιτήματα **απευθείας στον εναλλακτικό πάροχο (DeepSeek)**.
    -   **Αποτέλεσμα:** Εξαλείφονται οι περιττές καθυστερήσεις, και η διαδικασία ανάλυσης συνεχίζεται με μέγιστη ταχύτητα μόλις διαπιστωθεί ότι ο κύριος πάροχος είναι μη διαθέσιμος. Ο μετρητής μηδενίζεται αυτόματα αν μια κλήση στο Gemini πετύχει, κάνοντας το σύστημα δυναμικά προσαρμοζόμενο.

## [2.18.0] - 2025-09-21 - The AI Resilience & Agent Expansion Update

Αυτή η έκδοση-ορόσημο καθιστά τον TALOS ένα πραγματικά ανθεκτικό (resilient) και επεκτάσιμο σύστημα, εισάγοντας έναν κεντρικό **"AI Manager"** με λογική αυτόματου fallback. Παράλληλα, επεκτείνει δραματικά την εμβέλεια του συστήματος με την προσθήκη νέων, στρατηγικής σημασίας "πρακτόρων" και την υιοθέτηση μιας πιο ώριμης στρατηγικής αξιολόγησης.

### Αρχιτεκτονικές Αλλαγές & Νέα Λειτουργικότητα

-   **Δημιουργία του "AI Manager" (`core/ai_manager.py`):**
    -   **Αιτιολόγηση:** Η αποκλειστική εξάρτηση από ένα μόνο AI API (Google Gemini) αποτελούσε ένα κεντρικό σημείο αποτυχίας (single point of failure), ειδικά λόγω των ημερήσιων ορίων του δωρεάν tier.
    -   **Υλοποίηση:** Δημιουργήθηκε μια νέα, κεντρική κλάση `AIManager` η οποία είναι πλέον υπεύθυνη για **όλες τις κλήσεις** προς τα γλωσσικά μοντέλα.
    -   **Λογική Αυτόματου Fallback:** Ο `AIManager` είναι προγραμματισμένος να προσπαθεί πρώτα να εκτελέσει μια ανάλυση χρησιμοποιώντας το **Google Gemini**. Αν ανιχνεύσει σφάλμα ορίου χρήσης (`429 Quota Exceeded`), αλλάζει **αυτόματα και απρόσκοπτα** στον επόμενο διαθέσιμο πάροχο, το **DeepSeek**, για να ολοκληρώσει την εργασία.
    -   **Αποτέλεσμα:** Ο TALOS μπορεί πλέον να συνεχίσει να λειτουργεί ακόμα και μετά την εξάντληση του δωρεάν ορίου του Gemini, καθιστώντας τον δραματικά πιο αξιόπιστο.

-   **Υιοθέτηση της "Smart Store-First" Στρατηγικής:**
    -   **Αιτιολόγηση:** Η στρατηγική "Elite-Only" οδηγούσε σε περιττές, επαναλαμβανόμενες κλήσεις στα API των πηγών.
    -   **Υλοποίηση:** Η λογική του `daily_search.py` αναδιαρθρώθηκε πλήρως. Κάθε νέο άρθρο λαμβάνει πλέον μια γρήγορη, πολυδιάστατη αξιολόγηση από το Flash model (χρησιμοποιώντας ένα νέο `pre_screening_prompt`) και **αποθηκεύεται αμέσως** στη βάση. Μόνο τα άρθρα που περνούν το όριο συνάφειας **αναβαθμίζονται** με μια δεύτερη, βαθιά ανάλυση από το Pro model.

### Βελτιώσεις & Διορθώσεις

-   **Πλήρης Αναδιάρθρωση των Scripts:** Όλα τα scripts που εκτελούν αξιολογήσεις (`daily_search.py`, `historic_search.py`, `reevaluate_database.py`, `embedding_generator.py`) αναβαθμίστηκαν για να χρησιμοποιούν αποκλειστικά τον νέο `AIManager`, κάνοντας τον κώδικα πιο καθαρό, αρθρωτό και εύκολο στη συντήρηση.
-   **Διόρθωση Πολλαπλών Σφαλμάτων σε "Πράκτορες":** Επιλύθηκαν κρίσιμα σφάλματα συνδεσιμότητας και parsing στους πράκτορες `CORESource` και `ScienceGovSource`, βελτιώνοντας τη σταθερότητά τους.

## [2.17.0] - 2025-09-20 - The "Smart Store-First" Strategy & Agent Expansion

Αυτή η έκδοση αποτελεί μια θεμελιώδη αναβάθμιση στην κεντρική λογική του TALOS, επιστρέφοντας σε μια πιο ώριμη και αποδοτική στρατηγική "Store-First", ενώ παράλληλα επεκτείνει δραματικά την εμβέλεια του συστήματος με την προσθήκη δύο νέων, στρατηγικής σημασίας "πρακτόρων".

### Αρχιτεκτονικές Αλλαγές & Νέα Λειτουργικότητα

-   **Υιοθέτηση της "Smart Store-First" Στρατηγικής:**
    -   **Αιτιολόγηση:** Η προηγούμενη "Elite-Only" στρατηγική, αν και παρήγαγε μια καθαρή βάση δεδομένων, αποδείχθηκε αναποτελεσματική καθώς οδηγούσε σε περιττές, επαναλαμβανόμενες κλήσεις στα API των πηγών για άρθρα που είχαν ήδη αξιολογηθεί ως μη-σχετικά.
    -   **Υλοποίηση:** Ο κώδικας του `daily_search.py` αναδιαρθρώθηκε πλήρως για να ακολουθεί μια νέα, υβριδική ροή εργασίας:
        1.  **Προ-αξιολόγηση & Άμεση Αποθήκευση:** Κάθε νέο άρθρο λαμβάνει μια γρήγορη, **πολυδιάστατη** αξιολόγηση από το Flash model (χρησιμοποιώντας ένα νέο, πιο σύνθετο `pre_screening_prompt`) και **αποθηκεύεται αμέσως** στη βάση. Αυτό διασφαλίζει ότι κάθε άρθρο αξιολογείται μία και μόνο μία φορά, μεγιστοποιώντας την αποδοτικότητα.
        2.  **Βαθιά Ανάλυση & Αναβάθμιση:** Μόνο τα άρθρα που περνούν το όριο συνάφειας στέλνονται στο Pro model για μια ανώτερης ποιότητας, βαθιά ανάλυση. Η υπάρχουσα εγγραφή τους στη βάση δεδομένων **ενημερώνεται (UPDATE)** με τη νέα, ανώτερη ανάλυση και τις νέες βαθμολογίες.
-   **Προσθήκη "Πράκτορα" PubMed (`sources/pubmed_source.py`):**
    -   Ενσωματώθηκε ένας νέος πράκτορας που αντλεί δεδομένα από τη βιοϊατρική βάση δεδομένων PubMed, ξεκλειδώνοντας την πρόσβαση σε έρευνα σχετική με βιο-εμπνευσμένους αλγορίθμους και συμπεριφορά σμήνους.
-   **Προσθήκη "Πράκτορα" OSTI.gov (`sources/osti_source.py`):**
    -   Ενσωματώθηκε ένας νέος πράκτορας για την πύλη του Υπουργείου Ενέργειας των ΗΠΑ, παρέχοντας πρόσβαση σε τεχνικές αναφορές υψηλής ποιότητας από εθνικά εργαστήρια (π.χ., NASA, Los Alamos).

### Βελτιώσεις & Διορθώσεις

-   **Απενεργοποίηση του `ScienceGovSource`:** Ο πράκτορας για το Science.gov απενεργοποιήθηκε προσωρινά λόγω συνεχούς αστάθειας και σφαλμάτων του API του.
-   **Βελτιστοποίηση του `PubMed Query`:** Το query για το PubMed έγινε πιο αυστηρό και στοχευμένο για να μειωθεί ο "θόρυβος" από άσχετα, καθαρά ιατρικά άρθρα.


## [2.16.0] - 2025-09-20 - The Health & Government Intel Update

Αυτή η έκδοση επεκτείνει δραματικά την εμβέλεια συλλογής δεδομένων του TALOS, προσθέτοντας δύο νέους, στρατηγικής σημασίας "πράκτορες". Το σύστημα πλέον αντλεί πληροφορίες όχι μόνο από τις κλασικές ακαδημαϊκές βάσεις, αλλά και από τον τεράστιο κόσμο της βιοϊατρικής έρευνας και των δημοσιεύσεων των κυβερνητικών οργανισμών των ΗΠΑ.

### Νέα Λειτουργικότητα (Features)

-   **Ενσωμάτωση του "Πράκτορα" PubMed (`sources/pubmed_source.py`):**
    -   **Αιτιολόγηση:** Πολλές θεμελιώδεις έννοιες της τεχνητής νοημοσύνης, όπως οι βιο-εμπνευσμένοι αλγόριθμοι και η συμπεριφορά σμήνους, έχουν τις ρίζες τους στη βιολογία. Η πρόσβαση στο PubMed ξεκλειδώνει μια τεράστια δεξαμενή γνώσης σε αυτούς τους τομείς.
    -   **Υλοποίηση:** Δημιουργήθηκε ένας νέος, αποδοτικός πράκτορας που αξιοποιεί την εξειδικευμένη βιβλιοθήκη `pymed`. Δεν απαιτεί API key για άμεση λειτουργία, παρά μόνο ένα email, κάνοντας την ενσωμάτωση άμεση.

-   **Ενσωμάτωση του "Πράκτορα" Science.gov (`sources/scigov_source.py`):**
    -   **Αιτιολόγηση:** Κρίσιμοι ερευνητικοί οργανισμοί όπως η NASA και το Υπουργείο Άμυνας των ΗΠΑ παράγουν τεράστιο όγκο έρευνας αιχμής σε τομείς όπως τα αυτόνομα και μη επανδρωμένα συστήματα, η οποία δεν είναι πάντα διαθέσιμη στις κλασικές ακαδημαϊκές πηγές.
    -   **Υλοποίηση:** Δημιουργήθηκε ένας νέος, ελαφρύς πράκτορας που επικοινωνεί με το απλό και ανοιχτό REST API του Science.gov. Η πρόσβαση είναι εντελώς ανώνυμη και δεν απαιτεί κανενός είδους κλειδί.

### Βελτιώσεις

-   **Αναβάθμιση Υποδομής:**
    -   Το αρχείο `requirements.txt` ενημερώθηκε για να περιλαμβάνει τη νέα εξάρτηση `pymed`.
    -   Το αρχείο `config.json` εμπλουτίστηκε με νέα, εξειδικευμένα queries (`pubmed_query`, `scigov_query`) και παραμέτρους για τον μέγιστο αριθμό αποτελεσμάτων των νέων πηγών.
-   **Ενεργοποίηση Πυρήνα:** Οι νέοι πράκτορες ενσωματώθηκαν πλήρως στις ροές εργασίας τόσο της καθημερινής (`daily_search.py`) όσο και της ιστορικής αναζήτησης (`historic_search.py`), αυξάνοντας τον συνολικό αριθμό των ενεργών πηγών δεδομένων του TALOS.

## [2.15.3] - 2025-09-20 - The Semantic Brain (Semantic Search Integration)

Αυτή η έκδοση ολοκληρώνει τη μεταμόρφωση του Διαδραστικού Dashboard σε ένα πλήρως λειτουργικό εργαλείο ερευνητικής νοημοσύνης, εισάγοντας την πιο προηγμένη λειτουργία μέχρι σήμερα: τη **σημασιολογική αναζήτηση**.

### Νέα Λειτουργικότητα (Features)

-   **Υποδομή Σημασιολογικών Embeddings:**
    -   **Αναβάθμιση Βάσης Δεδομένων:** Το σχήμα της βάσης επεκτάθηκε με μια νέα στήλη `embedding` (τύπου `BLOB`) για την αποθήκευση του "σημασιολογικού DNA" κάθε άρθρου.
    -   **Δημιουργία Embeddings (`embedding_generator.py`):** Υλοποιήθηκε ένα νέο, στιβαρό script συντήρησης. Χρησιμοποιώντας το `text-embedding-004` μοντέλο του Google Gemini, το script διατρέχει τη βάση, βρίσκει άρθρα χωρίς embedding, και τα δημιουργεί μαζικά (one-by-one για μέγιστη αξιοπιστία), αποθηκεύοντάς τα μόνιμα.
-   **Back-end για Σημασιολογική Αναζήτηση:**
    -   Ένα νέο API endpoint, το `/api/semantic_search`, προστέθηκε στον Flask server (`interactive_dashboard.py`). Η λογική του είναι η εξής:
        1.  Δέχεται μια φράση αναζήτησης σε φυσική γλώσσα.
        2.  Δημιουργεί ένα "query embedding" για τη φράση.
        3.  Υπολογίζει την ομοιότητα συνημιτόνου (cosine similarity) μεταξύ του query embedding και όλων των αποθηκευμένων embeddings των άρθρων.
        4.  Επιστρέφει μια λίστα με τα πλήρη δεδομένα των 100 πιο σχετικών άρθρων, ήδη ταξινομημένα κατά σειρά συνάφειας.
-   **Front-end για Σημασιολογική Αναζήτηση:**
    -   Το `dashboard.html` εμπλουτίστηκε με ένα νέο πεδίο αναζήτησης και την αντίστοιχη λογική Javascript. Όταν ο χρήστης εκτελεί μια αναζήτηση, το front-end καλεί το νέο API και αντικαθιστά τα δεδομένα του πίνακα Tabulator με τα ταξινομημένα αποτελέσματα που λαμβάνει.

### Βελτιώσεις & Διορθώσεις

-   **Εκτενές Debugging:** Επιλύθηκε μια σειρά από πολύπλοκα σφάλματα που σχετίζονταν με τη δημιουργία, αποθήκευση και ανάκτηση των embeddings (`TypeError: 'list' object has no attribute 'values'`, `TypeError: Object of type bytes is not JSON serializable`, `AttributeError`, `NameError`). Ο κώδικας του `embedding_generator.py` και του `interactive_dashboard.py` ξαναγράφτηκε πολλαπλές φορές για να επιτευχθεί η τελική, στιβαρή και λειτουργική έκδοση.

## [2.15.2] - 2025-09-19 - The "Article DNA" Visualization

Αυτή η έκδοση αποτελεί μια σημαντική οπτική και λειτουργική αναβάθμιση του Διαδραστικού Dashboard. Εισάγει μια νέα, καινοτόμο μέθοδο για τη γρήγορη κατανόηση του προφίλ κάθε ακαδημαϊκού άρθρου.

### Νέα Λειτουργικότητα (Features)

-   **Οπτικοποίηση "Article DNA":**
    -   **Αιτιολόγηση:** Οι τρεις ξεχωριστές αριθμητικές βαθμολογίες (Tactical, Strategic, Simulation) ήταν δύσκολο να συγκριθούν γρήγορα και οπτικά.
    -   **Υλοποίηση:** Μια νέα, δυναμική στήλη "Article DNA" προστέθηκε στον πίνακα του Tabulator. Χρησιμοποιώντας έναν custom Javascript formatter, η στήλη αυτή οπτικοποιεί τις τρεις επιμέρους βαθμολογίες ως μικρά, χρωματιστά bar charts (sparklines). Αυτό προσφέρει μια άμεση, "με μια ματιά" κατανόηση του προφίλ και της χρησιμότητας κάθε άρθρου, επιτρέποντας στον χρήστη να εντοπίζει οπτικά τα άρθρα με την επιθυμητή ισορροπία.

### Βελτιώσεις

-   **Βελτιστοποίηση Διάταξης Dashboard:** Για να γίνει χώρος για τη νέα οπτικοποίηση, οι τρεις αριθμητικές στήλες των επιμέρους scores (`Tactical`, `Strategic`, `Simulation`) έχουν πλέον οριστεί ως **αόρατες** (`visible:false`). Τα δεδομένα τους παραμένουν διαθέσιμα για τα "Έξυπνα Φίλτρα" και την "Κάρτα Πληροφοριών", αλλά ο κύριος πίνακας είναι πλέον πιο καθαρός και εστιασμένος.


## [2.15.1] - 2025-09-19 - The "NAFSIKA" Dashboard Refinement

Αυτή η έκδοση αποτελεί την τελειοποίηση του νέου Διαδραστικού Dashboard. Εστιάζει στη βελτίωση της εμπειρίας χρήστη (UX), στην επίλυση προβλημάτων απεικόνισης και στην προσθήκη νέων, "έξυπνων" λειτουργιών που μετατρέπουν το dashboard σε ένα πλήρες κέντρο ελέγχου για την ερευνητική βάση δεδομένων.

### Νέα Λειτουργικότητα (Features)

-   **"Έξυπνα" Φίλτρα (Smart Filter Buttons):**
    -   **Αιτιολόγηση:** Η χειροκίνητη εφαρμογή φίλτρων για κοινές αναζητήσεις ήταν χρονοβόρα.
    -   **Υλοποίηση:** Προστέθηκε στο `dashboard.html` μια σειρά από προκαθορισμένα κουμπιά (`Core Papers`, `Tactical Focus`, κ.λπ.). Κάθε κουμπί, με τη χρήση Javascript, εφαρμόζει αυτόματα ένα φίλτρο στον πίνακα του Tabulator, εμφανίζοντας ακαριαία μόνο τα άρθρα που πληρούν συγκεκριμένα κριτήρια (π.χ., `overall_score >= 7`).
-   **"Κάρτα Αναγνώρισης Άρθρου" (Modal Info Card):**
    -   **Αιτιολόγηση:** Η ανάγνωση της πλήρους περίληψης και της ανάλυσης AI απαιτούσε άβολο οριζόντιο scroll στον πίνακα.
    -   **Υλοποίηση:** Προστέθηκε μια νέα στήλη "Info" με ένα κουμπί σε κάθε γραμμή. Με το πάτημα του κουμπιού, ένα αναδυόμενο παράθυρο (modal) εμφανίζει με καθαρή και ευανάγνωστη μορφή όλες τις λεπτομέρειες του άρθρου. Αυτό επιτεύχθηκε με τη δημιουργία ενός νέου API endpoint (`/api/paper/<id>`) στο `interactive_dashboard.py`.

### Βελτιώσεις & Διορθώσεις Σφαλμάτων

-   **Αισθητική & Λειτουργική Αναβάθμιση του Dashboard:**
    -   **Επαναφορά Θέματος:** Το dashboard επανήλθε στο προτιμώμενο, καθαρό και απλό θέμα (`tabulator_simple.min.css`) για μέγιστη ευκρίνεια.
    -   **Διόρθωση Checkbox:** Επιλύθηκε ένα πρόβλημα όπου τα checkboxes της στήλης "In Zotero" δεν εμφανίζονταν σωστά. Προστέθηκαν εξειδικευμένοι κανόνες CSS για να διασφαλιστεί η ορατότητα και η σωστή τους στοίχιση.
    -   **Προηγμένο Φιλτράρισμα:** Ενσωματώθηκε ένα ενσωματωμένο φίλτρο "tick/cross" στην επικεφαλίδα της στήλης "In Zotero", επιτρέποντας την άμεση εμφάνιση μόνο των τσεκαρισμένων ή των μη-τσεκαρισμένων άρθρων.
-   **Διόρθωση Σφάλματος `NameError` στο Back-end:**
    -   Επιλύθηκε ένα κρίσιμο σφάλμα `NameError: name 'sqlite3' is not defined` στο `interactive_dashboard.py` με την προσθήκη του απαραίτητου `import sqlite3`.
-   **Σταθεροποίηση Βάσης Δεδομένων:**
    -   Το `upgrade_database.py` script αναβαθμίστηκε για να προσθέτει με ασφάλεια τη νέα στήλη `in_zotero` στις υπάρχουσες βάσεις δεδομένων.
    -   Η μέθοδος `get_all_papers_for_dashboard` στο `database_manager.py` βελτιστοποιήθηκε για να επιστρέφει τα δεδομένα σε μορφή λεξικού, ιδανική για την αποστολή μέσω JSON στο front-end.

## [2.15.0] - 2025-09-19 - The "NAFSIKA" Interactive Dashboard

Αυτή η μεγάλη έκδοση εισάγει μια εντελώς νέα, πανίσχυρη λειτουργία στο οικοσύστημα του TALOS: ένα **ζωντανό, διαδραστικό dashboard** που παρέχει μια πλήρη, real-time επισκόπηση ολόκληρης της βάσης δεδομένων. Αυτή η λειτουργία, με την κωδική ονομασία "NAFSIKA", λύνει το πρόβλημα της στατικής φύσης των αναφορών και επιτρέπει στον χρήστη να αλληλεπιδρά άμεσα με τα δεδομένα του.

### Νέα Λειτουργικότητα (Features)

-   **Δημιουργία του `scripts/interactive_dashboard.py`:**
    -   **Αρχιτεκτονική:** Υλοποιήθηκε ένας ελαφρύς, τοπικός web server χρησιμοποιώντας τη βιβλιοθήκη **Flask**. Αυτός ο server λειτουργεί ως η "γέφυρα" μεταξύ του browser και της τοπικής βάσης δεδομένων.
    -   **API Endpoints:** Το script παρέχει δύο βασικά API endpoints:
        -   `/api/data`: Διαβάζει όλα τα άρθρα από τη βάση `talos_research.db` και τα στέλνει στον browser σε μορφή JSON.
        -   `/api/update_zotero`: Δέχεται αιτήματα από τον browser για να ενημερώσει την κατάσταση ενός άρθρου ("In Zotero") απευθείας στη βάση δεδομένων.

-   **Μόνιμη Αποθήκευση Κατάστασης "In Zotero":**
    -   **Αιτιολόγηση:** Η προηγούμενη λύση με το `localStorage` του browser ήταν "εύθραυστη" και μη-φορητή.
    -   **Υλοποίηση:** Προστέθηκε μια νέα στήλη `in_zotero` (INTEGER) στον πίνακα `papers` της βάσης δεδομένων. Η κατάσταση των checkboxes αποθηκεύεται πλέον μόνιμα και αξιόπιστα.

-   **Δημιουργία του `templates/dashboard.html`:**
    -   Ένα νέο HTML αρχείο που λειτουργεί ως το "front-end" του dashboard.
    -   Ενσωματώνει τη βιβλιοθήκη **Tabulator.js** για να μετατρέψει τα δεδομένα JSON σε έναν πλήρως διαδραστικό πίνακα με δυνατότητες ταξινόμησης, φιλτραρίσματος και σελιδοποίησης.
    -   Περιλαμβάνει Javascript για την ασύγχρονη επικοινωνία με το Flask back-end, επιτρέποντας την ενημέρωση της βάσης δεδομένων σε πραγματικό χρόνο χωρίς επαναφόρτωση της σελίδας.

-   **Ενοποίηση στο Κεντρικό Μενού (`talos.py`):**
    -   Προστέθηκε μια νέα, κεντρική επιλογή στο μενού που επιτρέπει στον χρήστη να εκκινήσει τον server του dashboard με ένα μόνο κλικ.

## [2.14.0] - 2025-09-17 - The Multi-Axis Evaluation & Interactive Dashboard Update

Αυτή είναι μια θεμελιώδης αναβάθμιση που μεταμορφώνει τον πυρήνα της ευφυΐας και της χρηστικότητας του TALOS. Το σύστημα εγκαταλείπει το μονοδιάστατο σύστημα βαθμολόγησης και υιοθετεί ένα **πολυδιάστατο πλαίσιο αξιολόγησης**, ενώ ταυτόχρονα αναβαθμίζει τις στατικές αναφορές του σε ένα **πλήρως διαδραστικό dashboard**.

### Νέα Λειτουργικότητα & Αρχιτεκτονικές Αλλαγές

-   **Πολυδιάστατη Αξιολόγηση (Multi-Axis Scoring):**
    -   **Αιτιολόγηση:** Ένα μοναδικό score συνάφειας δεν μπορούσε να αποτυπώσει την διαφορετική χρησιμότητα κάθε paper. Ένα άρθρο μπορεί να είναι στρατηγικά σημαντικό για το πλαίσιο της έρευνας, αλλά αλγοριθμικά αδύναμο, και το αντίστροφο.
    -   **Υλοποίηση:** Ο "εγκέφαλος" του TALOS (`phd_focus_system_prompt`) αναβαθμίστηκε ριζικά για να αξιολογεί κάθε άρθρο σε **τρεις ξεχωριστούς άξονες**:
        1.  **Tactical Score (Στρατηγικό/Αλγοριθμικό):** Η αξία του paper για την ανάπτυξη νέων αλγορίθμων.
        2.  **Strategic Score (Στρατηγικό/Πλαισίου):** Η χρησιμότητά του για την κατανόηση του ερευνητικού τοπίου.
        3.  **Simulation Score (Playground):** Η πρακτική του αξία για την υλοποίηση του προσομοιωτή.
-   **Αναβάθμιση Σχήματος Βάσης Δεδομένων:**
    -   Το σχήμα του πίνακα `papers` στη βάση `talos_research.db` αναδιαμορφώθηκε πλήρως. Η παλιά στήλη `relevance_score` καταργήθηκε και αντικαταστάθηκε από τις `tactical_score`, `strategic_score`, `simulation_score` και μια νέα, υπολογιζόμενη στήλη `overall_score` (σταθμισμένος μέσος όρος).
    -   Δημιουργήθηκε ένα στιβαρό script μετανάστευσης (`upgrade_database.py`) για την ομαλή αναβάθμιση των υπαρχουσών βάσεων δεδομένων χωρίς απώλεια δεδομένων.
-   **Διαδραστικό Dashboard Αναφορών (DataTables.js Integration):**
    -   **Αιτιολόγηση:** Οι στατικές αναφορές HTML ήταν δύσχρηστες με μεγάλο όγκο δεδομένων. Η ανάγκη για δυναμική ταξινόμηση και φιλτράρισμα ήταν επιτακτική.
    -   **Υλοποίηση:** Η συνάρτηση `export_to_html` στο `recommender.py` ξαναγράφτηκε πλήρως. Πλέον, παράγει ένα σύγχρονο HTML αρχείο που ενσωματώνει τη βιβλιοθήκη **DataTables.js**. Αυτό μετατρέπει την αναφορά σε ένα πλήρες dashboard με δυνατότητες:
        -   **Client-Side Ταξινόμησης:** Ο χρήστης μπορεί να ταξινομήσει τον πίνακα με ένα κλικ σε οποιαδήποτε στήλη (π.χ., κατά Tactical Score, κατά ημερομηνία).
        -   **Δυναμικής Αναζήτησης:** Ένα πεδίο αναζήτησης επιτρέπει το άμεσο φιλτράρισμα ολόκληρου του πίνακα.
        -   **Σελιδοποίησης (Pagination):** Τα αποτελέσματα παρουσιάζονται σε διαχειρίσιμες σελίδες.

### Βελτιώσεις & Διορθώσεις

-   **Πλήρης Συγχρονισμός του Οικοσυστήματος:** Όλα τα scripts που αλληλεπιδρούν με τη βάση δεδομένων (`main_search.py`, `historic_search.py`, `recommender.py`, `reevaluate_database.py`) αναβαθμίστηκαν πλήρως για να είναι συμβατά με το νέο, πολυδιάστατο σχήμα δεδομένων.
-   **Οργανωμένη Δομή Αναφορών:** Τα scripts που παράγουν αναφορές (`main_search`, `recommender`, `author_profiler`) αποθηκεύουν πλέον τα αρχεία τους σε εξειδικευμένους υποφακέλους (`reports/briefings/`, `reports/general/`, `reports/authors/`) για καλύτερη τάξη και διαχείριση.
-   **Διόρθωση `KeyError`:** Επιλύθηκε ένα σφάλμα `KeyError: 'days_to_search'` που προκαλούνταν από ασυνέπεια μεταξύ των κεντρικών scripts και των "πρακτόρων" (`sources`).
-   **Έξυπνος Χειρισμός `ResourceExhausted`:** Το `daily_search.py` αναβαθμίστηκε για να ανιχνεύει το σφάλμα `429 Quota Exceeded` του Gemini API, να σταματά ομαλά τη διαδικασία προ-αξιολόγησης και να επιτρέπει τη συνέχισή της την επόμενη ημέρα.

## [2.13.0] - 2025-09-16 - The Scopus Integration & Query Optimization

Αυτή η έκδοση-ορόσημο ενεργοποιεί πλήρως την πρόσβαση στην τεράστια βιβλιογραφική βάση δεδομένων Scopus της Elsevier, αναβαθμίζοντας δραματικά την ποιότητα και το εύρος των αποτελεσμάτων του TALOS. Παράλληλα, περιλαμβάνει μια πλήρη αναθεώρηση και βελτιστοποίηση όλων των queries αναζήτησης για να ευθυγραμμιστούν απόλυτα με την εξειδικευμένη ερευνητική κατεύθυνση του project.

### Νέα Λειτουργικότητα (Features)

-   **Πλήρης Ενεργοποίηση του `ElsevierSource`:**
    -   **Αυθεντικοποίηση Δύο Παραγόντων:** Ο πράκτορας `sources/elsevier_source.py` αναβαθμίστηκε πλήρως για να υποστηρίζει την απαιτούμενη αυθεντικοποίηση της Elsevier με συνδυασμό `APIKey` και `Institutional Token (insttoken)`.
    -   **Σύγχρονη Σελιδοποίηση:** Η λογική ανάκτησης δεδομένων ξαναγράφτηκε για να χρησιμοποιεί τη σύγχρονη, αυτόματη μέθοδο `get_all=True` της βιβλιοθήκης `elsapy`, αντικαθιστώντας την παλιά, μη συμβατή χειροκίνητη σελιδοποίηση. Αυτό λύνει το σφάλμα `AttributeError: 'ElsSearch' object has no attribute 'has_next'` και καθιστά τον πράκτορα στιβαρό και αποδοτικό.

### Βελτιώσεις

-   **Στρατηγική Βελτιστοποίηση των Queries:**
    -   **Αιτιολόγηση:** Μετά την οριστικοποίηση του νέου, εστιασμένου `phd_focus_system_prompt`, τα παλιά queries ήταν υπερβολικά γενικά, φέρνοντας μεγάλο όγκο άσχετων αποτελεσμάτων ("θόρυβο").
    -   **Υλοποίηση:** Όλα τα queries στο `config.json` αναθεωρήθηκαν. Πλέον ακολουθούν μια αυστηρή boolean λογική που συνδυάζει πολλαπλούς πυλώνες ενδιαφέροντος: **(Το Πρόβλημα) AND (Η Μέθοδος) AND (Το Πλαίσιο/Η Πλατφόρμα)**.
    -   **Προσαρμογή ανά Πηγή:** Κάθε query προσαρμόστηκε στις συντακτικές ιδιαιτερότητες του κάθε API (π.χ., η χρήση `OR` αντί για `AND` στο `openarchives_query` για μέγιστη συμβατότητα).
-   **Εμπλουτισμός `openarchives_query` με Ελληνικούς Όρους:** Το query για τον εθνικό συσσωρευτή εμπλουτίστηκε με τις ελληνικές μεταφράσεις των βασικών όρων έρευνας, αυξάνοντας δραματικά την ικανότητα του TALOS να εντοπίζει τη σχετική ελληνόφωνη βιβλιογραφία.

## [2.12.0] - 2025-09-16 - The Smart Recalibrator & Agent Activation

Αυτή η σημαντική έκδοση εισάγει μια νέα, "έξυπνη" λειτουργία συντήρησης και ενεργοποιεί τον πρώτο από τους νέους "πράκτορες", εμπλουτίζοντας δραματικά την ποιότητα και το εύρος των δεδομένων του TALOS. Το επίκεντρο είναι η διασφάλιση της μακροπρόθεσμης συνέπειας και αξιοπιστίας της βάσης δεδομένων.

### Νέα Λειτουργικότητα (Features)

-   **Δημιουργία του "Smart Recalibrator" (`scripts/reevaluate_database.py`):**
    -   **Αιτιολόγηση:** Η αλλαγή του κεντρικού `phd_focus_system_prompt` καθιστούσε τις παλιές αξιολογήσεις στη βάση δεδομένων ασυνεπείς με τις νέες. Μια μαζική επανα-αξιολόγηση ήταν απαραίτητη.
    -   **Υλοποίηση:** Δημιουργήθηκε ένα νέο, αυτόνομο script που επιτρέπει την επανα-αξιολόγηση ολόκληρης της βάσης. Η νέα λειτουργία είναι "έξυπνη" και διαθέτει:
        -   **Στρατηγική Προτεραιοποίηση:** Το script ανακτά και επεξεργάζεται τα άρθρα με σειρά φθίνουσας σημασίας (ξεκινώντας από τα υψηλότερα παλιά scores), διασφαλίζοντας ότι τα πιο πολύτιμα άρθρα ενημερώνονται πρώτα.
        -   **Διαχείριση API Limits (Batching):** Η διαδικασία εκτελείται σε "πακέτα" (π.χ., 950 άρθρα τη φορά) για να αποφεύγεται η υπέρβαση των ημερήσιων ορίων κλήσεων του AI API.
        -   **Ανθεκτικότητα & Συνέχιση:** Μια νέα στήλη `evaluation_date` προστέθηκε στη βάση. Το script αξιολογεί μόνο άρθρα που δεν έχουν "φρεσκαριστεί" πρόσφατα, επιτρέποντας στον χρήστη να συνεχίσει τη διαδικασία σε βάθος ημερών χωρίς να επαναλαμβάνει την ίδια δουλειά.

### Βελτιώσεις

-   **Ενεργοποίηση του `OpenArchivesSource`:** Ο "πράκτορας" για τον εθνικό συσσωρευτή OpenArchives.gr ενσωματώθηκε και ενεργοποιήθηκε πλήρως στον πυρήνα του TALOS.
    -   **Αντιμετώπιση Προβλημάτων:** Επιλύθηκε ένα κρίσιμο σφάλμα `JSONDecodeError` που προκαλούνταν από την επιστροφή κενής απάντησης από τον server. Η λύση περιελάμβανε την προσθήκη κρίσιμων HTTP headers (`User-Agent`, `Accept`) στο αίτημα, ώστε να προσομοιώνει πλήρως έναν κανονικό browser.
    -   **Εξειδικευμένα Queries:** Δημιουργήθηκε ένα νέο, προσαρμοσμένο query (`openarchives_query`) στο `config.json` που περιλαμβάνει και ελληνικούς όρους, μεγιστοποιώντας την ανάκτηση σχετικού περιεχομένου από την ελληνική βιβλιογραφία.
-   **Αναβάθμιση Σχήματος Βάσης Δεδομένων (`database_manager.py`):**
    -   Η δομή του πίνακα `papers` επεκτάθηκε για να συμπεριλάβει τη νέα στήλη `evaluation_date`.
    -   Οι μέθοδοι `add_paper` και `update_paper_evaluation` αναβαθμίστηκαν για να διαχειρίζονται τη νέα στήλη.
    -   Δημιουργήθηκε ένα βοηθητικό script `upgrade_database.py` για την ομαλή μετάβαση των υπαρχουσών βάσεων δεδομένων στο νέο σχήμα.
-   **Βελτιωμένη Στοχοθεσία Queries:** Όλα τα queries στο `config.json` αναθεωρήθηκαν και έγιναν πιο αυστηρά και εστιασμένα, ώστε να αντικατοπτρίζουν πλήρως τη νέα, εξειδικευμένη ερευνητική κατεύθυνση του `phd_focus_system_prompt`.


## [2.11.1] - 2025-08-31 - Διόρθωση Κρίσιμου Σφάλματος Κωδικοποίησης (Unicode Fix)

Αυτή η έκδοση διορθώνει ένα κρίσιμο σφάλμα `UnicodeDecodeError` που εμφανιζόταν σε περιβάλλοντα Windows κατά την εκτέλεση των "αλυσιδωτών" λειτουργιών του Profiler και του Analyzer. Το πρόβλημα προκαλούνταν από την ασυμβατότητα μεταξύ της προεπιλεγμένης κωδικοποίησης του τερματικού των Windows και της αναμενόμενης κωδικοποίησης UTF-8 της Python.

### Διορθώσεις Σφαλμάτων (Bug Fixes)

-   **Αναβάθμιση της `run_script` στο `talos.py`:** Η συνάρτηση ξαναγράφτηκε πλήρως για να είναι "αλεξίσφαιρη" σε θέματα κωδικοποίησης. Πλέον:
    -   Δημιουργεί ένα προσαρμοσμένο περιβάλλον εκτέλεσης (`env`) για τα υπο-scripts, το οποίο **εξαναγκάζει** την Python να χρησιμοποιεί **UTF-8** για όλη την επικοινωνία εισόδου/εξόδου μέσω της μεταβλητής `PYTHONIOENCODING`.
    -   Δηλώνει ρητά `encoding="utf-8"` κατά την "αιχμαλώτιση" της εξόδου, διασφαλίζοντας συνεπή αποκωδικοποίηση.
-   **Επιβολή UTF-8 στα Scripts:** Προστέθηκε η δήλωση `# -*- coding: utf-8 -*-` ως η πρώτη γραμμή στα αρχεία `author_profiler.py` και `author_trajectory_analyzer.py` για μέγιστη συμβατότητα.

Αυτή η διόρθωση καθιστά την επικοινωνία μεταξύ των scripts του TALOS ανεξάρτητη από το λειτουργικό σύστημα και τις τοπικές του ρυθμίσεις, λύνοντας οριστικά το πρόβλημα του "αναβοσβήματος" του τερματικού.

## [2.11.0] - 2025-08-31 - The Strategic Dossier Update

Αυτή η έκδοση-ορόσημο εισάγει μια εντελώς νέα διάσταση στρατηγικής ανάλυσης στο TALOS. Αντί να εξετάζει μεμονωμένα άρθρα ή στατικά προφίλ, το σύστημα αποκτά την ικανότητα να αναλύει τη **συνολική ερευνητική πορεία** ενός συγγραφέα, προσφέροντας μια βαθιά, συνθετική αξιολόγηση της συνάφειάς του με την έρευνα του χρήστη. Αυτό επιτυγχάνεται μέσω μιας νέας, "αλυσιδωτής" ροής εργασίας που συνδυάζει πολλαπλά scripts και AI models σε μια ενιαία, απρόσκοπτη λειτουργία.

### Νέα Λειτουργικότητα (Features)

-   **Δημιουργία του `scripts/author_trajectory_analyzer.py`:** Ένα νέο, πανίσχυρο script που:
    -   Δέχεται ένα ORCID iD.
    -   Ανακτά τις δημοσιεύσεις του ερευνητή τα τελευταία 5 χρόνια.
    -   Χρησιμοποιεί ένα νέο, εξειδικευμένο prompt (`trajectory_analyzer_prompt`) για να δώσει εντολή στο AI (`Gemini 1.5 Flash`) να εκτελέσει μια ολιστική, στρατηγική ανάλυση ολόκληρου του πρόσφατου έργου του συγγραφέα.
-   **Ενοποιημένη Ροή Εργασίας "Profiler -> Analyzer":** Η πιο σημαντική αναβάθμιση στη λειτουργικότητα του TALOS. Το κεντρικό μενού (`talos.py`) ενορχηστρώνει πλέον μια πλήρη αναφορά:
    1.  Ο χρήστης εισάγει ένα **όνομα**.
    2.  Το `talos.py` εκτελεί τον `author_profiler.py` και "αιχμαλωτίζει" την έξοδό του.
    3.  Αναλύει την έξοδο για να εξάγει αυτόματα το επιλεγμένο ORCID iD.
    4.  Εκτελεί **αυτόματα** το `author_trajectory_analyzer.py`, περνώντας του το ID που μόλις βρήκε.

### Βελτιώσεις

-   **Αναβάθμιση του `author_profiler.py`:** Το script τροποποιήθηκε ώστε να μπορεί να "επικοινωνεί" με άλλα μέρη του συστήματος. Πλέον, εκτός από την εμφάνιση και εξαγωγή της αναφοράς, τυπώνει το επιλεγμένο ORCID iD σε μια ειδική, μηχανικά αναγνώσιμη μορφή (`SELECTED_ORCID_ID:...`), επιτρέποντας την αλυσιδωτή εκτέλεση.
-   **Ανασχεδιασμός Κεντρικού Μενού (`talos.py`):** Το μενού έγινε πιο έξυπνο και φιλικό προς τον χρήστη. Οι ξεχωριστές επιλογές για "Γρήγορο Προφίλ" και "Ανάλυση Τροχιάς" συγχωνεύτηκαν σε μια ενιαία, πανίσχυρη επιλογή **"5. Πλήρης Αναφορά Συγγραφέα"**, καθοδηγώντας τον χρήστη σε μια λογική και ολοκληρωμένη ροή εργασίας.
---

## [2.10.0] - 2025-08-31 - The Unified Profiler Update

Αυτή η μεγάλη έκδοση αναβαθμίζει ριζικά τη λειτουργία "Ανάλυση Προφίλ Συγγραφέα", μετατρέποντάς την από ένα απλό script σε ένα πανίσχυρο εργαλείο ερευνητικής νοημοσύνης. Ο παλιός `Scopus Profiler` αντικαθίσταται πλήρως από τον νέο **"Unified Profiler"**, ο οποίος συνδυάζει δεδομένα από τρεις κορυφαίες ακαδημαϊκές πηγές για να δημιουργήσει έναν πλήρη, διασταυρωμένο "φάκελο" για κάθε ερευνητή.

### Νέα Λειτουργικότητα & Βελτιώσεις

-   **Ανασχεδιασμός του `author_profiler.py`:** Το script ξαναγράφτηκε πλήρως για να λειτουργεί ως "ορχηστρωτής", ακολουθώντας μια στρατηγική τριών βημάτων:
    1.  **ORCID API (Η Ταυτότητα):** Χρησιμοποιείται ως η "πηγή της αλήθειας" για την αδιαμφισβήτητη ταυτοποίηση του ερευνητή.
    2.  **OpenAlex API (Ο Συνδετής):** Αξιοποιείται ως "Ροζέτα" για να συνδέσει το ORCID iD με άλλα αναγνωριστικά και να αντλήσει ποιοτικά δεδομένα, όπως το ίδρυμα και τα κορυφαία ερευνητικά πεδία ("concepts").
    3.  **Semantic Scholar API (Οι Μετρικές):** Χρησιμοποιείται για την ανάκτηση υπολογισμένων μετρικών, όπως το `h-index` και ο συνολικός αριθμός αναφορών.
-   **Ανθεκτικότητα & "Αλεξίσφαιρη" Λογική:** Ο νέος profiler είναι σχεδιασμένος για να χειρίζεται κομψά ελλιπή ή ανύπαρκτα δεδομένα. Αν ένας ερευνητής δεν βρεθεί σε μία από τις πηγές, το script συνεχίζει κανονικά, παρουσιάζοντας όσα δεδομένα κατάφερε να συλλέξει.
-   **Εξαγωγή Αναφορών σε Markdown:** Μετά την ανάλυση, ο profiler δημιουργεί αυτόματα μια πλήρη, καλοδιατηρημένη αναφορά σε αρχείο Markdown (`.md`) μέσα στον φάκελο `reports/`, ιδανική για αρχειοθέτηση και μελλοντική χρήση.
-   **Εξαγωγή DOI:** Στη λίστα των πρόσφατων δημοσιεύσεων, το script πλέον εξάγει και το link του DOI, κάνοντας την πρόσβαση στο πλήρες κείμενο άμεση.
-   **Διαδραστική Επιλογή:** Όταν η αναζήτηση επιστρέφει πολλαπλούς ερευνητές, το script χρησιμοποιεί το `questionary` για να επιτρέψει στον χρήστη να επιλέξει διαδραστικά τον σωστό.

---

## [2.9.2] - 2025-08-30 - Βελτιστοποίηση Διαφάνειας & Φιλτραρίσματος

Αυτή η έκδοση βελτιώνει δραματικά την επικοινωνία του `main_search.py` με τον χρήστη και κάνει τη διαδικασία φιλτραρίσματος πιο "έξυπνη" και αξιόπιστη.

### Βελτιώσεις
-   **Πλήρης Διαφάνεια:** Το `main_search.py` τυπώνει πλέον αναλυτικά βήματα για τη διαδικασία φιλτραρίσματος, δείχνοντας πόσα άρθρα βρέθηκαν αρχικά, πόσα ήταν μοναδικά, και πόσα ήταν πραγματικά νέα για τη βάση.
-   **Λίστα Νέων Ευρημάτων:** Προστέθηκε η εκτύπωση μιας καθαρής λίστας με τους τίτλους και τα IDs **μόνο** των άρθρων που είναι νέα για τη βάση, δίνοντας στον χρήστη μια άμεση εικόνα της "συγκομιδής" της ημέρας.
-   **"VIP Pass" για Τίτλους:** Ενσωματώθηκε μια νέα, πιο "έξυπνη" λογική ποιοτικού ελέγχου. Ένα άρθρο προκρίνεται για αξιολόγηση αν έχει είτε καλή περίληψη, **είτε** ο τίτλος του περιέχει "VIP" λέξεις-κλειδιά (π.χ., "drone", "swarm"). Αυτό διασφαλίζει ότι κανένα σημαντικό άρθρο δεν απορρίπτεται λόγω έλλειψης περίληψης από το API.

---

## [2.9.1] - 2025-08-30 - Διόρθωση Bug στην Αποθήκευση Score

### Διορθώσεις Σφαλμάτων (Bug Fixes)
-   **Δομική Αναδιάρθρωση:** Διορθώθηκε ένα κρίσιμο λογικό σφάλμα όπου ο `recommender.py` προσπαθούσε να υπολογίσει ξανά το score, αντί να το διαβάζει από τη βάση. Η λογική του `extract_relevance_score` μεταφέρθηκε οριστικά και αποκλειστικά στα scripts που γράφουν στη βάση (`main_search.py` & `historic_search.py`).
-   **Αναβάθμιση Βάσης Δεδομένων:** Εδραιώθηκε η δομή του πίνακα `papers` ώστε να περιλαμβάνει τη στήλη `relevance_score` που γράφεται τη στιγμή της αρχικής ανάλυσης.
-   **Συνέπεια Ονομάτων:** Διορθώθηκαν ασυνέπειες στα ονόματα των αρχείων της βάσης δεδομένων μεταξύ των διαφόρων scripts.

---

## [2.8.0] - 2025-08-30 - "The Two-Stage Sentinel" Update

Αυτή η μεγάλη αναβάθμιση εισήγαγε μια νέα, ιδιοφυή στρατηγική δύο σταδίων για την καθημερινή αναζήτηση, κάνοντας τον TALOS δραματικά πιο αποδοτικό και το κανάλι του Discord απόλυτα καθαρό.

### Νέα Λειτουργικότητα (Features)
-   **Προ-Αξιολόγηση (Pre-screening):** Το `main_search.py` πλέον εκτελεί μια αρχική, γρήγορη αξιολόγηση όλων των νέων άρθρων χρησιμοποιώντας ένα γρήγορο μοντέλο (Flash-Lite) και ένα απλοποιημένο prompt.
-   **Στρατηγική "Store-First":** Όλα τα προ-αξιολογημένα άρθρα αποθηκεύονται αμέσως στη βάση με το αρχικό τους σκορ, δημιουργώντας ένα πλήρες αρχείο.
-   **Βαθιά Ανάλυση "Elite" Άρθρων:** Μόνο τα άρθρα που περνούν ένα υψηλό όριο στην προ-αξιολόγηση στέλνονται στο ισχυρό Pro model για πλήρη, σε βάθος ανάλυση.
-   **Συνοπτική Αναφορά στο Discord:** Αντί για πολλαπλά μηνύματα, ο TALOS πλέον δημιουργεί ένα ενιαίο αρχείο Markdown (`.md`) με την ανάλυση των κορυφαίων άρθρων και το στέλνει ως **ένα και μοναδικό επισυναπτόμενο αρχείο** στο Discord.

---

## [2.7.2] - 2025-08-29 - Τελειοποίηση Διάταξης HTML

Μια τελική αισθητική διόρθωση για την τέλεια στοίχιση των στηλών στις αναφορές HTML.

### Διορθώσεις Σφαλμάτων (Bug Fixes)
-   **`recommender.py`:** Προστέθηκε η ιδιότητα CSS `table-layout: fixed;` στον πίνακα της αναφοράς HTML. Αυτό αναγκάζει τον browser να τηρεί αυστηρά το καθορισμένο πλάτος για κάθε στήλη, λύνοντας το πρόβλημα όπου οι στήλες με πολύ κείμενο "συμπιέζονταν" υπερβολικά.

---

## [2.7.1] - 2025-08-29 - Βελτιστοποίηση Διάταξης HTML

Μια αισθητική βελτίωση για την καλύτερη αναγνωσιμότητα των αναφορών HTML.

### Βελτιώσεις
-   **`recommender.py`:** Αναθεωρήθηκε η λογική CSS στην `export_to_html`. Πλέον, ορίζονται συγκεκριμένα, βελτιστοποιημένα πλάτη για κάθε στήλη, δίνοντας περισσότερο χώρο στις στήλες με εκτενές κείμενο (`abstract`, `cleaned_analysis`) και συμπιέζοντας τις στήλες με μικρό περιεχόμενο (`id`, `source`). Αυτό έχει ως αποτέλεσμα μια πολύ πιο ισορροπημένη και ευανάγνωστη εμφάνιση του πίνακα στον browser.

---

## [2.7.0] - 2025-08-29 - Κομψές & Συνοπτικές Αναφορές

Αυτή η έκδοση αναβαθμίζει ριζικά την ποιότητα και τη χρηστικότητα των αναφορών που εξάγει ο Recommender, εστιάζοντας στη σαφήνεια αντί για τον όγκο των δεδομένων.

### Βελτιώσεις
-   **Ανασχεδιασμός Εξαγωγής σε Markdown:** Η συνάρτηση `export_to_markdown` ξαναγράφτηκε πλήρως. Αντί να εξάγει έναν τεράστιο, δύσχρηστο πίνακα, πλέον δημιουργεί ένα όμορφα δομημένο, συνοπτικό αρχείο, παρουσιάζοντας τα κορυφαία άρθρα σε μορφή λίστας με επικεφαλίδες και callouts, ιδανικό για το Obsidian.
-   **Ανασχεδιασμός Εξαγωγής σε DOCX:** Παρόμοια, η `export_to_docx` τροποποιήθηκε για να παράγει ένα κομψό, κάθετο (portrait) έγγραφο Word. Αντί για πίνακα, χρησιμοποιεί επικεφαλίδες και παραγράφους για να παρουσιάσει τα κορυφαία άρθρα με τρόπο φιλικό προς την ανάγνωση και την εκτύπωση.
-   **Αφαίρεση της Βιβλιοθήκης `tabulate`:** Ως αποτέλεσμα του ανασχεδιασμού, η εξάρτηση από τη βιβλιοθήκη `tabulate` (πρώην `pandas-to-markdown`) αφαιρέθηκε, κάνοντας το project πιο λιτό.

---

## [2.6.1] - 2025-08-29 - Διόρθωση Εξαγωγής σε DOCX

### Διορθώσεις Σφαλμάτων (Bug Fixes)
-   **`recommender.py`:** Προστέθηκε λογική "απολύμανσης" κειμένου στη συνάρτηση `export_to_docx` για την αφαίρεση μη συμβατών με XML χαρακτήρων. Αυτό λύνει το σφάλμα `ValueError: All strings must be XML compatible` που προέκυπτε κατά την προσπάθεια αποθήκευσης του αρχείου Word.
-   **Προσανατολισμός Landscape στο DOCX:** Προστέθηκε η δυνατότητα εξαγωγής του αρχείου Word σε οριζόντιο (landscape) προσανατολισμό για καλύτερη αναγνωσιμότητα των πινάκων. (Αργότερα αντικαταστάθηκε στην v2.7.0).

---

## [2.6.0] - 2025-08-29 - The Scribe Update

Αυτή η έκδοση μετατρέπει τον Recommender σε έναν πολυ-εργαλείο εξαγωγής αναφορών, προσθέτοντας υποστήριξη για νέα, ευρέως χρησιμοποιούμενα format αρχείων.

### Νέα Λειτουργικότητα (Features)
-   **Εξαγωγή σε Microsoft Word (.docx):** Ο `recommender.py` μπορεί πλέον να εξάγει την πλήρη αναφορά σε ένα καλά μορφοποιημένο έγγραφο Word, ιδανικό για επεξεργασία και διαμοιρασμό.
-   **Εξαγωγή σε Markdown (.md):** Προστέθηκε η δυνατότητα εξαγωγής της αναφοράς σε αρχείο Markdown, έτοιμο για άμεση εισαγωγή και χρήση σε εφαρμογές όπως το Obsidian.
-   **Προσθήκη Νέων Βιβλιοθηκών:** Το project πλέον απαιτεί τις βιβλιοθήκες `python-docx` και `pandas-to-markdown`.

---

## [2.5.1] - 2025-08-29 - Διόρθωση Κωδικοποίησης HTML

Μια μικρή, αλλά σημαντική διόρθωση για τη σωστή εμφάνιση των ελληνικών χαρακτήρων στις αναφορές HTML.

### Διορθώσεις Σφαλμάτων (Bug Fixes)
-   **`recommender.py`:** Προστέθηκε το meta tag `<meta charset="UTF-8">` στην κεφαλίδα (header) του παραγόμενου αρχείου HTML. Αυτό λύνει οριστικά το πρόβλημα "mojibake", όπου οι ελληνικοί χαρακτήρες εμφανίζονταν ως ακατανόητα σύμβολα σε ορισμένους browsers.

---

## [2.5.0] - 2025-08-28 - The Keystone Update

Αυτή η έκδοση προσθέτει υποστήριξη για το Crossref API, τον θεμέλιο λίθο των ακαδημαϊκών μεταδεδομένων, δίνοντας στον TALOS πρόσβαση σε μια τεράστια, κεντρική βάση δεδομένων που καλύπτει σχεδόν όλους τους μεγάλους εκδότες.

### Νέα Λειτουργικότητα (Features)
-   **Νέος "Πράκτορας" (`crossref_source.py`):** Δημιουργήθηκε ένας νέος, εξειδικευμένος ανιχνευτής που επικοινωνεί με το Crossref REST API.
-   **Αναβάθμιση `config.json`:** Προστέθηκαν ρυθμίσεις (`crossref_query`, `crossref` στο `max_results_config`) για την παραμετροποίηση του νέου πράκτορα.
-   **Αύξηση Πηγών σε 8:** Ο Τάλως πλέον αντλεί δεδομένα από οκτώ διαφορετικές, μεγάλες ακαδημαϊκές πηγές.

---

## [2.4.0] - 2025-08-28 - The Profiler Update

Αυτή η έκδοση προσθέτει μια ισχυρή λειτουργία "Intel", επιτρέποντας στον χρήστη να ανακτά και να προβάλλει τα ακαδημαϊκά προφίλ ερευνητών απευθείας από το Scopus.

### Νέα Λειτουργικότητα (Features)
-   **Νέο Script (`author_profiler.py`):** Δημιουργήθηκε ένα νέο, αυτόνομο script που αξιοποιεί το Scopus Author Profile API.
-   **Αναζήτηση & Προβολή Προφίλ:** Το script μπορεί να ψάξει για έναν συγγραφέα με βάση το όνομά του και να παρουσιάσει τις βασικές του μετρικές (h-index, αριθμό δημοσιεύσεων, αναφορές) και το τρέχον ίδρυμά του.
-   **Ενσωμάτωση στο `talos.py`:** Προστέθηκε μια νέα επιλογή "4. Ανάλυση Προφίλ Συγγραφέα" στο κεντρικό μενού, κάνοντας τη νέα λειτουργία εύκολα προσβάσιμη.

---

## [2.3.0] - 2025-08-28 - The Elsevier Integration

Αυτή η αναβάθμιση προσθέτει υποστήριξη για την τεράστια βιβλιογραφική βάση δεδομένων Scopus της Elsevier, αυξάνοντας δραματικά την ποιότητα και την κάλυψη των αποτελεσμάτων.

### Νέα Λειτουργικότητα (Features)
-   **Νέος "Πράκτορας" (`elsevier_source.py`):** Δημιουργήθηκε ένας νέος, εξειδικευμένος ανιχνευτής που επικοινωνεί με το Scopus Search API χρησιμοποιώντας την επίσημη βιβλιοθήκη `elsapy`.
-   **Προσθήκη Βιβλιοθήκης `elsapy`:** Το project πλέον εξαρτάται από και χρησιμοποιεί την `elsapy`.
-   **Αναβάθμιση `config.json`:** Προστέθηκαν νέες ρυθμίσεις (`elsevier_query`, `elsevier` στο `max_results_config`) για την παραμετροποίηση του νέου πράκτορα.

---

## [2.2.0] - 2025-08-28 - Αυτόματη Ονομασία Θεματικών Ομάδων

Αυτή η έκδοση προσθέτει ένα επίπεδο "ερμηνευσιμότητας" (interpretability) στον Recommender, κάνοντας τις προτάσεις του ακόμα πιο σαφείς και χρήσιμες.

### Νέα Λειτουργικότητα (Features)
-   **Αυτόματη Εξαγωγή Λέξεων-Κλειδιών:** Ο `recommender.py` αναβαθμίστηκε για να αναλύει το περιεχόμενο κάθε θεματικής ομάδας (cluster) που δημιουργεί.
-   **Δυναμικοί Τίτλοι Clusters:** Χρησιμοποιώντας τα αποτελέσματα του `TfidfVectorizer`, το script εξάγει αυτόματα τις 4 πιο αντιπροσωπευτικές λέξεις-κλειδιά για κάθε cluster και τις παρουσιάζει ως δυναμικό τίτλο στην αναφορά "Στρατηγικό Μονοπάτι Ανάγνωσης". Αυτό επιτρέπει στον χρήστη να καταλαβαίνει με μια ματιά το θέμα κάθε ομάδας άρθρων.

---

## [2.1.0] - 2025-08-28 - Έξυπνο "Μονοπάτι Ανάγνωσης"

Αυτή η έκδοση αναβαθμίζει δραματικά την "ευφυΐα" του `recommender.py`, μετατρέποντας την έξοδό του από μια απλή λίστα σε ένα πραγματικό, στρατηγικό πλάνο μελέτης.

### Βελτιώσεις
-   **Αναβάθμιση Στρατηγικής Recommender:** Η λογική για την πρόταση "Θεμελιωδών Άρθρων" άλλαξε ριζικά. Πλέον, το script πρώτα φιλτράρει για να βρει τα άρθρα με την υψηλότερη βαθμολογία (π.χ., >8/10) και *μετά* επιλέγει τα παλαιότερα από αυτή την ελίτ ομάδα.
-   **Προσθήκη Κατηγορίας "State-of-the-Art":** Ο Recommender πλέον προτείνει και μια ξεχωριστή λίστα με τα πιο **πρόσφατα** από τα κορυφαία άρθρα, δίνοντας μια άμεση εικόνα για τις τελευταίες εξελίξεις.
-   **Βελτιωμένη Παραμετροποίηση:** Η κύρια συνάρτηση του Recommender δέχεται πλέον διαφορετικά όρια συνάφειας για τη γενική ανάλυση και για την επιλογή των θεμελιωδών άρθρων, προσφέροντας μεγαλύτερη ευελιξία.

---
## [2.0.0] - 2025-08-27 - The Pantheon Update

Αυτή η μεγάλη αναβάθμιση μετατρέπει τον TALOS σε ένα πραγματικό "θηρίο" βιβλιογραφικής έρευνας, προσθέτοντας δύο νέες, μεγάλες, ανοιχτές πηγές δεδομένων και αυξάνοντας δραματικά την κάλυψή του.

### Προσθήκες
-   **Ενσωμάτωση του DBLP:** Δημιουργήθηκε ο "πράκτορας" `dblp_source.py` για την ανάκτηση δεδομένων από τη DBLP, μια βάση δεδομένων υψηλής ποιότητας εστιασμένη στην Επιστήμη Υπολογιστών.
-   **Ενσωμάτωση του CORE:** Δημιουργήθηκε ο "πράκτορας" `core_source.py` για την ανάκτηση δεδομένων από τον αθροιστή CORE, που περιέχει εκατομμύρια open-access άρθρα.
-   **Αναβάθμιση `config.json` & `.env`** για την υποστήριξη των νέων πηγών.
---

## [1.11.0] - 2025-08-28 - Τελειοποίηση & Σταθεροποίηση

Αυτή η έκδοση αποτελεί ένα μεγάλο "καθάρισμα" και μια σειρά από κρίσιμες διορθώσεις που κάνουν τον TALOS πιο στιβαρό, αξιόπιστο και "έξυπνο" από ποτέ.

### Βελτιώσεις & Νέα Λειτουργικότητα
-   **"Έξυπνος" Launcher (`talos.py`):** Το κεντρικό μενού αναβαθμίστηκε ριζικά. Πλέον **εντοπίζει αυτόματα το σωστό εκτελέσιμο της Python** (`sys.executable`) μέσα από το ενεργό περιβάλλον Conda και το χρησιμοποιεί για να καλέσει τα υπο-scripts. Αυτό λύνει οριστικά το πρόβλημα του "αναβοσβήματος" και εξασφαλίζει ότι τα scripts τρέχουν πάντα με τις σωστές, εγκατεστημένες βιβλιοθήκες.
-   **Αλεξίσφαιρη Εξαγωγή Score:** Η συνάρτηση `extract_relevance_score` (στα `main_search.py` & `historic_search.py`) ξαναγράφτηκε πλήρως. Πλέον χρησιμοποιεί **πολλαπλές στρατηγικές (regular expressions)** για να εντοπίσει το σκορ, κάνοντάς την ανθεκτική σε παραλλαγές της απάντησης του Gemini.
-   **Προσθήκη Script Διόρθωσης Βάσης (`fix_scores.py`):** Δημιουργήθηκε ένα νέο, βοηθητικό script που μπορεί να διατρέξει την υπάρχουσα βάση δεδομένων και να διορθώσει αναδρομικά τυχόν λανθασμένες βαθμολογίες χρησιμοποιώντας την τελευταία, πιο έξυπνη λογική εξαγωγής.

### Διορθώσεις Σφαλμάτων (Bug Fixes)
-   **Διόρθωση Ασυμφωνίας Βάσης Δεδομένων:** Διορθώθηκε ένα κρίσιμο σφάλμα όπου διαφορετικά scripts αναφέρονταν σε διαφορετικά ονόματα αρχείων `.db`, οδηγώντας σε ασυνέπεια δεδομένων. Πλέον, όλο το σύστημα χρησιμοποιεί ένα και μοναδικό, κεντρικό αρχείο βάσης.
-   **Διόρθωση `AttributeError` στο `springer_source.py`:** Διορθώθηκε ένα σφάλμα που προκαλούσε "κράσαρισμα" κατά την ανάκτηση από το Springer.
-   **Διόρθωση Λανθασμένης Διαδρομής `config.json`:** Διορθώθηκε η λογική φόρτωσης του `config.json` μέσα στα scripts για να είναι απόλυτα στιβαρή, ανεξάρτητα από τον φάκελο εκτέλεσης.

---

## [1.10.0] - 2025-08-28 - Ενσωμάτωση του OpenAlex

Αυτή η μεγάλη αναβάθμιση προσθέτει το OpenAlex ως την 5η πηγή δεδομένων, αυξάνοντας δραματικά την κάλυψη και την ισχύ του TALOS.

### Προσθήκες
-   **Νέος "Πράκτορας" (`openalex_source.py`):** Δημιουργήθηκε μια νέα κλάση `OpenAlexSource` για την επικοινωνία με το OpenAlex API. Ο πράκτορας υποστηρίζει πλήρως τη σελιδοποίηση για την ανάκτηση μεγάλου όγκου δεδομένων.
-   **Ανακατασκευή Περίληψης:** Ενσωματώθηκε μια ειδική συνάρτηση (`reconstruct_abstract`) που "χτίζει" την περίληψη από το `inverted_index` που παρέχει το OpenAlex.
-   **Αναβάθμιση του `config.json`:** Προστέθηκαν νέες ρυθμίσεις (`openalex_query`, `openalex` στο `max_results_config`, και `mailto`) για την πλήρη παραμετροποίηση του νέου πράκτορα.
-   **Ενεργοποίηση του Πράκτορα:** Ο `OpenAlexSource` προστέθηκε στη λίστα `sources_to_search` στα κεντρικά scripts (`main_search.py` & `historic_search.py`).

---

## [1.9.0] - 2025-08-28 - Αναβάθμιση του Semantic Scholar

Αυτή η έκδοση επεκτείνει τη στιβαρή λογική ανάκτησης δεδομένων και στον "πράκτορα" του Semantic Scholar, διορθώνοντας προβλήματα που σχετίζονται με την τελευταία έκδοση της βιβλιοθήκης του.

### Αλλαγές
-   **Μετάβαση σε Απευθείας Κλήσεις API:** Ο `semantic_scholar_source.py` ξαναγράφτηκε για να χρησιμοποιεί απευθείας τη βιβλιοθήκη `requests` αντί για τη βιβλιοθήκη `semanticscholar`, παρέχοντας απόλυτο έλεγχο στη σελιδοποίηση μέσω `offset` και `limit`.
-   **Βελτιωμένη Συμβατότητα:** Η νέα προσέγγιση είναι ανεξάρτητη από τις αλλαγές στην εξωτερική βιβλιοθήκη `semanticscholar`, κάνοντας τον πράκτορα πιο στιβαρό μακροπρόθεσμα.

---

## [1.8.0] - 2025-08-28 - Αναβάθμιση του Springer

Αυτή η έκδοση εισήγαγε προχωρημένες τεχνικές ανάκτησης δεδομένων για να κάνει τον "πράκτορα" του Springer πιο αξιόπιστο.

### Βελτιώσεις
-   **Προσθήκη Σελιδοποίησης στον `SpringerNatureSource`:** Η κλάση ξαναγράφτηκε για να υποστηρίζει σελιδοποίηση, ανακτώντας τα αποτελέσματα σε "πακέτα" των 100.
-   **Έξυπνη Διαχείριση Rate Limit:** Ενσωματώθηκε λογική για την ανίχνευση του σφάλματος `429 Too Many Requests` και την αυτόματη επανάληψη της προσπάθειας μετά από παύση.
-   **"Ευγενικές" Κλήσεις API:** Προστέθηκε μικρή παύση (`time.sleep`) μεταξύ των διαδοχικών κλήσεων.

---
## [1.7.1] - 2025-08-27 - Ευέλικτη Παραμετροποίηση

Αυτή η έκδοση βελτιώνει δραματικά την ευελιξία και την καθαρότητα του κώδικα, μεταφέροντας περισσότερη λογική στο αρχείο ρυθμίσεων.

### Βελτιώσεις
-   **Ευέλικτο `days_to_search`:** Το `config.json` αναβαθμίστηκε για να υποστηρίζει ξεχωριστές παραμέτρους για τις ημέρες αναζήτησης (`days_to_search_daily` και `days_to_search_historic`).
-   **Απλοποίηση του `historic_search.py`:** Αφαιρέθηκε η "hardcoded" λογική παράκαμψης των ρυθμίσεων από το script. Πλέον, το `historic_search.py` και το `main_search.py` διαβάζουν τις αντίστοιχες παραμέτρους τους απευθείας από το `config.json`, κάνοντας τον κώδικα πιο καθαρό και συνεπή.
-   **Βελτίωση του `arxiv_query`:** Το query για το arXiv έγινε πιο σύνθετο και ισχυρό, συνδυάζοντας αναζήτηση σε κατηγορίες (`cat:`) και σε όλο το κείμενο (`all:`).

---

## [1.7.0] - 2025-08-27 - Βελτιστοποίηση Ορίων & Υιοθέτηση Flash-Lite

Αυτή η έκδοση εστιάζει στην πλήρη παραμετροποίηση των ορίων ανά πηγή και στην αξιοποίηση του πιο αποδοτικού μοντέλου Gemini για μαζικές εργασίες.

### Βελτιώσεις
-   **Πλήρης Παραμετροποίηση Ορίων:** Το `config.json` αναβαθμίστηκε για να υποστηρίζει ένα αντικείμενο `max_results_config`, επιτρέποντας τον ορισμό ξεχωριστού ορίου αποτελεσμάτων για κάθε πηγή (ArXiv, IEEE, κ.λπ.) ανεξάρτητα.
-   **Αναβάθμιση "Πρακτόρων":** Όλες οι κλάσεις στον φάκελο `sources/` ενημερώθηκαν για να διαβάζουν το εξειδικευμένο τους όριο από το νέο `max_results_config`.
-   **Υιοθέτηση του `gemini-2.5-flash-lite`:** Το μοντέλο για την ιστορική αναζήτηση άλλαξε σε `gemini-2.5-flash-lite`, εκμεταλλευόμενο το τεράστιο δωρεάν όριο των 1000+ αιτημάτων/ημέρα για ταχύτερη και πιο ολοκληρωμένη αρχική δόμηση της βάσης δεδομένων.

---

## [1.6.0] - 2025-08-27 - Διόρθωση Κρίσιμου Σφάλματος (Bug Fix)

Αυτή η έκδοση διορθώνει ένα κρίσιμο λογικό σφάλμα που προκαλούσε τη λανθασμένη αποθήκευση του `relevance_score` στη βάση δεδομένων.

### Διορθώσεις
-   **Δομική Αλλαγή στη Ροή Δεδομένων:** Η λογική του `extract_relevance_score` μεταφέρθηκε από τον `recommender.py` στα scripts που γράφουν στη βάση (`main_search.py` και `historic_search.py`).
-   **Αναβάθμιση Βάσης Δεδομένων:** Προστέθηκε μια νέα, αποκλειστική στήλη `relevance_score` στον πίνακα `papers` του `database_manager.py`.
-   **Απλοποίηση του `recommender.py`:** Ο Recommender πλέον διαβάζει το έτοιμο, σωστό σκορ απευθείας από τη βάση, αντί να προσπαθεί να το υπολογίσει.

---

## [1.5.0] - 2025-08-27 - Η Εγκυκλοπαιδική Τεκμηρίωση

Αυτή η έκδοση εστιάζει στην ολοκλήρωση και τον εμπλουτισμό της τεκμηρίωσης του project.

### Προσθήκες
-   **Προσθήκη αρχείου `CHANGELOG.md`:** Δημιουργήθηκε αυτό το αρχείο για την καταγραφή της ιστορικότητας του project.
-   **Πλήρης Αναβάθμιση του `README.md`:** Το `README.md` ξαναγράφτηκε πλήρως για να γίνει ένα υπερ-αναλυτικό, εγκυκλοπαιδικό εγχειρίδιο, εξηγώντας κάθε κλάση, βιβλιοθήκη και τεχνολογία AI που χρησιμοποιείται.

---

## [1.4.0] - 2025-08-27 - Αναφορές & Στρατηγική

### Προσθήκες
-   **Αναβάθμιση του `recommender.py`:** Ο Recommender πλέον δεν προτείνει απλά, αλλά:
    -   Δημιουργεί ένα **"Στρατηγικό Μονοπάτι Ανάγνωσης"**, προτείνοντας πρώτα θεμελιώδη και μετά εξειδικευμένα άρθρα.
    -   **Εξάγει αναφορές** σε αρχεία **CSV** και **HTML** μέσα σε έναν νέο φάκελο `reports/`.
-   **Προσθήκη βιβλιοθήκης `jinja2`** για τη δημιουργία των όμορφων HTML αναφορών.

---

## [1.3.0] - 2025-08-27 - Το Κέντρο Ελέγχου

### Προσθήκες
-   **"Βάφτιση" του Project σε "TALOS"**: Υιοθετήθηκε το νέο, επίσημο όνομα.
-   **Δημιουργία του `talos.py` (πρώην `run.py`):** Ένα κεντρικό, διαδραστικό μενού τερματικού που λειτουργεί ως launcher για όλες τις λειτουργίες.
-   **Προσθήκη βιβλιοθήκης `questionary`** για τη δημιουργία των μενού.
-   **Αναδιοργάνωση Αρχείων:** Τα αρχεία ομαδοποιήθηκαν σε λογικούς υποφακέλους (`core/`, `scripts/`) για καλύτερη οργάνωση.
-   **Αυτόματη Επιλογή Μοντέλου Gemini:** Το `config.json` αναβαθμίστηκε για να ορίζει διαφορετικά μοντέλα (Pro/Flash) για την καθημερινή και την ιστορική αναζήτηση, αυτοματοποιώντας πλήρως τη διαδικασία.

---

## [1.2.0] - 2025-08-27 - Η Μνήμη

### Προσθήκες
-   **Ενσωμάτωση Βάσης Δεδομένων:** Προστέθηκε ο `database_manager.py` που δημιουργεί και διαχειρίζεται μια τοπική βάση δεδομένων **SQLite** (`research_bot.db`).
-   **Αποφυγή Διπλοτύπων:** Το `main_search.py` πλέον ελέγχει τη βάση και επεξεργάζεται μόνο τα άρθρα που δεν έχει ξαναδεί.

---

## [1.1.0] - 2025-08-27 - Η Πολυφωνία

### Προσθήκες
-   **Υποστήριξη Πολλαπλών Πηγών:** Το project ξαναγράφτηκε σε **αντικειμενοστρεφή** μορφή.
-   **Δημιουργία "Πρακτόρων":** Προστέθηκαν οι κλάσεις `ArxivSource`, `SemanticScholarSource`, `IEEESource`, `SpringerSource` στον νέο φάκελο `sources/`.
-   **Deduplication:** Προστέθηκε λογική στο `main.py` για την αφαίρεση διπλότυπων άρθρων που μπορεί να βρεθούν σε πολλαπλές πηγές.

---

## [1.0.0] - 2025-08-27 - Η Γέννηση

### Προσθήκες
-   **Αρχική Δημιουργία:** Το project ξεκίνησε ως ένα απλό script (`main.py`) που έψαχνε μόνο στο arXiv.
-   **Επικοινωνία με Gemini AI:** Υλοποιήθηκε η βασική λογική για την αποστολή περιλήψεων στο Gemini και τη λήψη της ανάλυσης.
-   **Ειδοποιήσεις στο Discord:** Υλοποιήθηκε η λειτουργία αποστολής της ανάλυσης σε ένα κανάλι Discord μέσω Webhook.
-   **Ρύθμιση μέσω `.env` και `config.json`:** Δημιουργήθηκε η βασική υποδομή για την παραμετροποίηση.