# Project TALOS -- Ιστορικό Χρονολόγιο (Ελληνικά)

> **Σκοπός:** Το παρόν έγγραφο αποτελεί την έγκυρη χρονολογική καταγραφή όλων των αναπτυξιακών, ερευνητικών και αρχιτεκτονικών οροσήμων του Project TALOS. Κάθε αλλαγή έκδοσης, νέο χαρακτηριστικό και breaking change καταγράφεται εδώ.
>
> **Κανόνας:** Μετά από ΚΑΘΕ αλλαγή έκδοσης, αυτό το αρχείο ΠΡΕΠΕΙ να ενημερώνεται με το νέο ορόσημο και την κατάστασή του.
>
> **Τελευταία Ενημέρωση:** 2026-10-02 (v5.17.1 -- Διαφάνεια UX Αξιολόγησης Ποιότητας PRISMA & Μηχανή Αναγκαστικής Επαναξιολόγησης)

---

## Φάση 71: Διαφάνεια UX Αξιολόγησης Ποιότητας PRISMA & Αναγκαστική Επαναξιολόγηση (v5.17.1)

### Κατάσταση: ΟΛΟΚΛΗΡΩΜΕΝΗ (2026-10-02)

- [x] **Κατάργηση σιωπηλής εξόδου** -- `src/prisma/quality_appraisal.py`: η `appraise_candidates_batch()` δεν επιστρέφει πλέον κενή όταν κάθε υποψήφιος φέρει ήδη `quality_score`. Η προεπιλεγμένη διαδρομή αποδίδει ενημερωτικό πλαίσιο Rich και επαναπροβάλλει την αποθηκευμένη κατανομή 2D Τεταρτημορίων Τεκμηρίων (`_render_existing_quadrant_distribution`), εξασφαλίζοντας ιδιοδύναμη, ντετερμινιστική ανατροφοδότηση.
- [x] **Μηχανή αναγκαστικής επαναξιολόγησης** -- νέα παράμετρος `force_reappraise: bool = False` επιλέγει κάθε υποψήφιο (`overall_score >= min_relevance`, αγνοώντας προηγούμενο `quality_score`), εκπέμπει κίτρινη ειδοποίηση και αντικαθιστά `quality_score` / `quality_rubric_json` / `evidence_quadrant` στο WAL της SQLite.
- [x] **Ενσωμάτωση CLI & TUI** -- `--appraise-quality [--min-score 7.0] [--swarm] [--force]`· η Επιλογή 15 της Ομάδας 3 εντοπίζει ήδη αξιολογημένο σώμα και ρωτά πριν από σκόπιμη επαναξιολόγηση, με εφεδρική εμφάνιση πίνακα τεταρτημορίων σε άρνηση.
- [x] **Συγχρονισμός Βοήθειας Διπλής Επιφάνειας** -- ο Πίνακας 1 και η Κάρτα 6 τεκμηριώνουν το `--force` και την εφεδρική διαφάνεια UX.
- [x] **Συγχρονισμός έκδοσης** -- 6 βασικά αρχεία + docker-compose.yml (`talos:5.17.1`) + CITATION.cff (5.17.1, 2026-10-02) + config.template.json + μεταδεδομένα tray/visualizer/wizard/strategy/diagnostics/bibtex/help + docstrings src/prisma/ και src/search/ + 19 κανονικά έγγραφα σε v5.17.1 (2026-10-02).
- [x] **Πύλες επαλήθευσης πέρασαν** -- compileall (0 σφάλματα), test_quality_appraisal (17), test_quality_swarm (17), test_system_integrity, test_talos_version (5.17.1), `--help` τεκμηριώνει `--force`, verify_dependency_map --ci (έξοδος 0), bash -n, σάρωση UTF-8 (0 U+FFFD).

## Φάση 70: Αρχιτεκτονική Ιεραρχικού Σμήνους Δύο Επιπέδων & Μηχανή Εγκληματολογικής Ποιότητας (v5.17.0)

### Κατάσταση: ΟΛΟΚΛΗΡΩΜΕΝΗ (2026-10-02)

- [x] **Αρχιτεκτονική Ιεραρχικού Σμήνους Δύο Επιπέδων** -- το `src/prisma/quality_swarm.py` (1.261 γραμμές) διαχωρίζει τυπικά τη Θεματική Διαλογή Επιπέδου-1 (`swarm_evaluators.py`: τρεις προσωπικότητες κριτών με ψήφους INCLUDE/EXCLUDE/UNCERTAIN) από την Εγκληματολογική Ποιοτική Επιθεώρηση Επιπέδου-2 (τέσσερις εξειδικευμένοι ελεγκτές δεξιοτήτων που βαθμολογούν τη ρουμπρίκα Kitchenham 2007 σε εισαχθείσες μελέτες). Το Επίπεδο-1 απαντά "είναι εντός θέματος;", το Επίπεδο-2 "είναι μεθοδολογικά αξιόπιστη;".
- [x] **Τέσσερις εξειδικευμένοι εγκληματολογικοί ελεγκτές δεξιοτήτων** -- `TheoryAuditor` (Q1), `OperationalAuditor` (Q2), `BenchmarkAuditor` (Q3-Q4), `OpenScienceAuditor` (Q5-Q6)· τυποποιημένα αποτελέσματα Pydantic-v2 με τριαδικές βαθμολογίες στο πλέγμα {0.0, 0.5, 1.0} και ονοματισμένες κριτικές.
- [x] **Πρότυπα Αγνωστικισμού Πεδίου & Δεξιότητες ανά Προφίλ** -- το `src/prisma/skills/templates/` φιλοξενεί τέσσερα αμετάβλητα πρότυπα με μόνο τα placeholder `{{RESEARCH_DOMAIN}}` / `{{DOMAIN_CONSTRAINTS}}`· η `SkillCompiler.compile_profile_skills()` εγχέει το `research_topic` / `inclusion_criteria` / `exclusion_criteria`, προαιρετικά βελτιώνει με το βαρύ μοντέλο (`qwen2.5:14b` τοπικά, `deepseek-reasoner` / `gemini-2.5-flash` cloud) και εγγράφει τα `_profiles/<name>/skills/*.md`.
- [x] **SmartSectionSlicer & σύνθεση συναίνεσης** -- εξαγωγή ενοτήτων με κανονικές εκφράσεις, όρια ~300-500 λέξεων, εφεδρική περίληψη· ο `KitchenhamQualitySynthesizer` υπολογίζει `S_qual = (10/6) * sum(Q_i)`, τη συμφωνία Fleiss `kappa_qual`, το τεταρτημόριο και την ενοποιημένη αφήγηση.
- [x] **Λειτουργία swarm & αποθήκευση** -- `PrismaQualityAppraiser(appraisal_mode='single'|'swarm')`· εκτεταμένο φορτίο στις υπάρχουσες στήλες SQLite χωρίς αλλαγές σχήματος.
- [x] **CLI, TUI & διπλή βοήθεια** -- `--appraise-quality [--swarm]` και `--compile-skills [--force]`· Επιλογή 15 Ομάδας 3· Πίνακας 1 + Κάρτα 6.
- [x] **Φάκελος Κανόνα 10, αρ. 06** -- `docs/internal/academic/06_TWO_TIER_HIERARCHICAL_SWARM_QUALITY.md` (7 ενότητες).
- [x] **Συγχρονισμός έκδοσης** -- 6 βασικά αρχεία + docker-compose.yml (`talos:5.17.0`) + CITATION.cff (5.17.0, 2026-10-02) + config.template.json + μεταδεδομένα + docstrings src/prisma/ και src/search/ + 19 κανονικά έγγραφα σε v5.17.0 (2026-10-02).
- [x] **Πύλες επαλήθευσης πέρασαν** -- compileall (0 σφάλματα), test_quality_swarm (17 ερμητικές), test_quality_appraisal (17 -- συμβατές), test_system_integrity, test_talos_version (5.17.0), `--compile-skills` (προφίλ UAV), `--help`, φάκελος 06 (0 U+FFFD), verify_dependency_map --ci (έξοδος 0), bash -n, σάρωση UTF-8 (0 U+FFFD).

## Φάση 69: Ενθέσιμο Μητρώο Παρόχων & Σύμβουλος Μοντέλων με Επίγνωση Υλικού (v5.16.2)

### Κατάσταση: ΟΛΟΚΛΗΡΩΘΗΚΕ (2026-10-02)

- [x] **Ενθέσιμο Μητρώο Παρόχων** -- το `src/core/provider_registry.py` εισάγει `ProviderDescriptor` (dataclass) και `ProviderRegistry` που υλοποιούν την Αρχή Ανοικτού-Κλειστού. Το μητρώο προ-καταχωρίζει το τοπικό Ollama συν εννέα παρόχους νέφους (NVIDIA NIM, DeepSeek, Gemini, Groq, Cerebras, Mistral, Hugging Face, OpenRouter, Anthropic) και εκθέτει `register` / `get` / `list_all` / `list_active`· το `is_active` αξιολογείται δυναμικά από την παρουσία κλειδιού (νέφος) ή την απόκριση θύρας (τοπικό Ollama).
- [x] **Σύμβουλος Μοντέλων με Επίγνωση Υλικού** -- το `src/core/hardware_advisor.py` εισάγει `HardwareModelAdvisor` με `get_hardware_profile()` (`{has_cuda, device_name, total_vram_gb, system_ram_gb, is_laptop_cpu}`), `calculate_vram_budget()` (τμηματικός τύπος 4-bit: >=11 GB -> 14B, 5.5-11 -> 8B, <5.5/CPU -> 3B), `get_recommendations()` (στοίβα ανά ρόλο) και `scan_sota_models()` (ραντάρ SOTA με ομαλή υποβάθμιση εκτός σύνδεσης για Qwen 3/4 και Llama 4).
- [x] **Αποσύζευξη AIManager χωρίς παλινδρόμηση** -- ο `AIManager` καταναλώνει το μητρώο μέσω `list_active_providers()` / `get_provider_descriptor()` χωρίς να αγγίζει το `OPENAI_COMPATIBLE_REGISTRY`, τους βρόχους εκκίνησης SDK, τους διακόπτες κυκλώματος ή τα δημόσια συμβόλαια μεθόδων.
- [x] **CLI & TUI** -- αποστολή `--hardware-advisor` / `--recommend-models` στην `_handle_cli_flags()`· Επιλογή 8 Διαμόρφωσης & Προφίλ· τεκμηρίωση στον Πίνακα 1 του εγχειριδίου.
- [x] **Συγχρονισμός έκδοσης** -- 6 βασικά αρχεία + docker-compose.yml (`talos:5.16.2`) + CITATION.cff (5.16.2, 2026-10-02) + μεταδεδομένα tray/visualizer/wizard/strategy/diagnostics + docstrings src/prisma/ και src/search/ + 19 κανονικά έγγραφα σε v5.16.2 (2026-10-02).
- [x] **Πύλες επαλήθευσης πέρασαν** -- compileall, 18 νέες ερμητικές δοκιμές, test_system_integrity, test_talos_version (5.16.2), `--recommend-models` (RTX 4070 -> προϋπολογισμός 14B), verify_dependency_map --ci (έξοδος 0), bash -n, σάρωση UTF-8 (0 U+FFFD).

## Φάση 68: Ενοποιημένη Αρχιτεκτονική Προφίλ & Συγχρονισμός Χώρου Εργασίας (v5.16.1)

### Κατάσταση: ΟΛΟΚΛΗΡΩΘΗΚΕ (2026-10-02)

- [x] **ProfileManager ως μοναδική πηγή αλήθειας** -- το `src/core/profile_manager.py` αναδομείται στην κανονική κλάση `ProfileManager`, αγκυρωμένη στον `_profiles/` της ρίζας (`Path(__file__).resolve().parents[2]`), εκθέτοντας `get_profiles_dir()`, `get_active_profile_name()`, `set_active_profile()`, `list_profiles()`, `create_profile()`, `get_active_db_path()` και `get_active_config_path()`, με συμβατά ψευδώνυμα module για το `talos.py`.
- [x] **Ανάθεση DatabaseManager** -- η `get_active_profile_db_path()` αναθέτει στην `ProfileManager.get_active_db_path()`, συμπτύσσοντας κάθε διπλό επιλύτη διαδρομών σε έναν.
- [x] **Μετεγκατάσταση κανονικού χώρου εργασίας PhD** -- το σώμα 5.472 άρθρων (114 elite, 325 αξιολογημένα ως προς την ποιότητα) ενοποιείται στο `_profiles/uav_mission_planning/`· ο `active_profile.txt` δείχνει σε αυτό· το root config κλειδώνει `research_topic: "Drone Mission Planning (Task Allocation-Path Planning) with DRL and ST-GAT"`.
- [x] **Ενοποίηση τοπικής εκτέλεσης ΤΝ** -- το `FAST_EDGE_URL` ορίζει προεπιλογή 11434, αποσύροντας τη φανταστική θύρα 11435· τα διαγνωστικά/βοήθεια/εγχειρίδιο τεκμηριώνουν τη 11434 ως Καθολικό Τοπικό Runtime ΤΝ (GPU/CPU).
- [x] **Κεφαλίδα TUI** -- η κεφαλίδα αποδίδει `Profile: [uav_mission_planning]` και `Active Research Focus: ...`.
- [x] **Συγχρονισμός έκδοσης** -- 6 αρχεία κώδικα + docker-compose.yml (`talos:5.16.1`) + CITATION.cff (5.16.1, 2026-10-02) + μεταδεδομένα tray/visualizer/wizard/strategy/diagnostics + docstrings src/prisma/ και src/search/ + 19 κανονικά έγγραφα σε v5.16.1 (2026-10-02).
- [x] **Πύλες επαλήθευσης** -- compileall, test_system_integrity, test_talos_version (5.16.1), Profile SSOT, `--diagnostics` (χωρίς 11435), verify_dependency_map --ci (exit 0), bash -n, σάρωση UTF-8 (0 U+FFFD).

## Φάση 67: Αξιολόγηση Ποιότητας PRISMA & Μηχανή Διαξονικής Επιστημονικής Αυστηρότητας (v5.16.0)

### Κατάσταση: ΟΛΟΚΛΗΡΩΘΗΚΕ (2026-10-01)

- [x] **Τυποποιημένη ρουμπρίκα ποιότητας Kitchenham (2007)** -- το `src/prisma/quality_appraisal.py` παρέχει `KitchenhamRubric` (έξι τριμερείς κατηγορικές ερωτήσεις), `QualityAppraisalResult` και `PrismaQualityAppraiser`, με κανονικοποιητή `_normalize_ternary` για απόκλιση τοπικών μοντέλων.
- [x] **Τυπικός διαχωρισμός συνάφειας/αυστηρότητας** -- το `S_qual = (άθροισμα(Q_i)/6.0)*10.0` υπολογίζεται ανεξάρτητα από το `overall_score` τεσσάρων επιπέδων· η `map_evidence_quadrant()` προβάλλει κάθε μελέτη στο Δισδιάστατο Επίπεδο Απόφασης Τεκμηρίων (ELITE_FOUNDATIONAL, IDEA_MINE, METHODOLOGICAL_EXEMPLAR, METHODOLOGICAL_NOISE).
- [x] **Μαζική αξιολόγηση ποιότητας** -- `--appraise-quality [--min-score 7.0]` (CLI) και Επιλογή 15 της Ομάδας 3 TUI αξιολογούν μη αποθηκευμένα υποψήφια άρθρα ταυτόχρονα μέσω `ThreadPoolExecutor` (`Semaphore(2)` τοπικά / 8 Cloud Mesh) και αποδίδουν πίνακα κατανομής τεταρτημορίων Rich.
- [x] **Επέκταση σχήματος SQLite** -- στήλες `quality_score REAL`, `quality_rubric_json TEXT`, `evidence_quadrant TEXT` προστίθενται ιδιοδύναμα με νέα βοηθητική μέθοδο `update_paper_quality()`.
- [x] **Εξαγωγή BibTeX με διπλό φίλτρο** -- `export_library(min_quality, quadrant)` συν πεδίο `note` με Συνάφεια, Επιστημονική Ποιότητα και Τεταρτημόριο.
- [x] **Παραπομπές IEEE Kitchenham [11]-[12]** στο `README.md` (EN και αντίστοιχη ελληνική ενότητα).
- [x] **Φάκελος Κανόνα 10, αρ. 05** -- `docs/internal/academic/05_PRISMA_QUALITY_APPRAISAL_KITCHENHAM.md` (7 ενότητες, ανιχνευσιμότητα διπλού επιπέδου).
- [x] **Συγχρονισμός έκδοσης** -- 6 βασικά αρχεία + docker-compose.yml (`talos:5.16.0`) + CITATION.cff (5.16.0, 2026-10-01) + μεταδεδομένα tray/visualizer/wizard/strategy/diagnostics + docstrings src/prisma/ και src/search/ + 19 κανονικά έγγραφα σε v5.16.0 (2026-10-01).
- [x] **Πύλες επαλήθευσης πέρασαν** -- compileall, test_quality_appraisal (17 ερμητικά), test_system_integrity, test_talos_version (5.16.0), CLI `--appraise-quality`, BibTeX `min_quality=7.5`, `--help` / `GET /help`, README [11]/[12], φάκελος 0 U+FFFD, verify_dependency_map --ci (έξοδος 0), bash -n, σάρωση UTF-8 (0 U+FFFD).

## Φάση 66: Σύστημα Βοήθειας Διπλής Επιφάνειας & Επιστημονικά Θεμέλια IEEE (v5.15.5)

### Κατάσταση: ΟΛΟΚΛΗΡΩΘΗΚΕ (2026-10-01)

- [x] **Αρχιτεκτονική Βοήθειας Διπλής Επιφάνειας** -- το `src/utils/help_system.py` αποδίδει ένα εγχειρίδιο κονσόλας Rich τεσσάρων πινάκων (Σημαίες Ταχείας Αποστολής CLI, Διαδραστικά Στοιχεία Ελέγχου & Πλοήγηση, Χαρτογράφηση Θυρών & Αρχιτεκτονική Υπηρεσιών, Παραγόμενες Αναφορές & Τεχνουργήματα Αποθήκευσης), εξυπηρετούμενο μέσω `talos.py --help` και της Επιλογής 7 του TUI με διαδραστικό μήνυμα `[O] Άνοιγμα Διαδραστικού Διαδικτυακού Εγχειριδίου` / `[Enter] Επιστροφή στο Μενού` (ISO/IEC 25010 Πλαίσιο Χρήσης).
- [x] **Διαδραστικό Διαδικτυακό Εγχειρίδιο** -- `templates/help_manual.html` (αυτοδύναμο, μηδενικού CDN, αποκρίσιμο ακαδημαϊκό σκοτεινό θέμα) εξυπηρετούμενο στο `GET /help` με ζωντανή αναζήτηση, αντιγραφή με κλικ, δομημένες κάρτες και εναλλαγή σκοτεινής/εκτυπώσιμης λειτουργίας· το `GET /manual` εκδίδει ανακατεύθυνση 307. Το πλήθος endpoint αυξάνεται 23 -> 25.
- [x] **Τυπικές Επιστημονικές Αναφορές IEEE** -- η Ενότητα 5 του `README.md` (αγγλική) και η αντικατοπτρισμένη ελληνική «Επιστημονικές Αναφορές & Θεωρητικό Υπόβαθρο» παρουσιάζουν 10 αυστηρά διαμορφωμένες αναφορές IEEE ([1]-[10]).
- [x] **Ενσωμάτωση TUI & CLI** -- η `_cli_help_table()` αναθέτει στην `help_system.render_help_manual(interactive=False)`· το κύριο μενού αποκτά την Επιλογή 7 (η Έξοδος αναριθμείται σε 8).
- [x] **Συγχρονισμός έκδοσης** -- 6 βασικά αρχεία + docker-compose.yml (`talos:5.15.5`) + CITATION.cff (5.15.5, 2026-10-01) + μεταδεδομένα tray/visualizer/wizard/diagnostics + docstrings src/prisma/ και src/search/ + 19 κανονικά αρχεία σε v5.15.5 (2026-10-01).
- [x] **Πέρασαν οι πύλες επαλήθευσης** -- compileall, test_system_integrity, test_talos_version (5.15.5), `talos.py --help` (κωδικός 0), `GET /help` (200) / `GET /manual` (307), verify_dependency_map --ci (κωδικός 0), bash -n, σάρωση UTF-8 (0 U+FFFD).

## Φάση 65: Επέκταση Χώρου Δράσεων DRL & Μετανάστευση Checkpoint Net2Net (v5.15.4)

### Κατάσταση: ΟΛΟΚΛΗΡΩΘΗΚΕ (2026-10-01)

- [x] **Επέκταση χώρου δράσεων DRL σε 18 πηγές** -- η `ALL_KNOWN_SOURCES` αποκτά `nasa_ntrs` και `hal_inria`· χώρος δράσεων Gymnasium `Discrete(17) -> Discrete(19)` (18 πηγές + ύπνος) και χώρος καταστάσεων 23 -> 25 διαστάσεις· η `_load_source_list()` εγγυάται την πλήρη λίστα 18 πηγών.
- [x] **Χειρουργική checkpoint Net2Net** -- το `scripts/migrate_d3qn_checkpoint.py` διευρύνει την κεφαλή πλεονεκτήματος DuelingLSTM (15 -> 19) και το στρώμα εισόδου LSTM (21 -> 25) στο `models/dddqn_trained.pth`, διατηρώντας όλα τα εκπαιδευμένα βάρη bit προς bit και αρχικοποιώντας αισιόδοξα τις τέσσερις νέες κεφαλές πηγών· επαληθεύτηκε με αυστηρή `DuelingLSTM(25, 19).load_state_dict()` (μηδενική ασυμφωνία)· αντίγραφο ασφαλείας `models/dddqn_trained.pth.bak`.
- [x] **Συγχρονισμός προφίλ 18 πηγών** -- `nasa_ntrs`/`hal_inria` προστέθηκαν στο `max_results_config` + κλειδιά ερωτημάτων στα `config.json`, `config.template.json`, `_profiles/default_drones/config.json`.
- [x] **Κλείδωμα κανονικοποίησης συγγραφέων Scopus/Elsevier** -- η `normalize_authors()` χειρίζεται `$`, `@name`/`@surname`, και `given_name`/`surname` με περικοπή 4 συγγραφέων + et al.
- [x] **Συγχρονισμός έκδοσης** -- 6 αρχεία κώδικα + docker-compose.yml (`talos:5.15.4`) + CITATION.cff (5.15.4, 2026-10-01) + μεταδεδομένα tray/visualizer/wizard/diagnostics + docstrings src/prisma/ και src/search/ + 19 κανονικά αρχεία σε v5.15.4 (2026-10-01).
- [x] **Πέρασαν οι πύλες επαλήθευσης** -- compileall, test_system_integrity, test_talos_version (5.15.4), αυστηρή φόρτωση μοντέλου DRL, ανίχνευση πηγών δαίμονα (18/18), verify_dependency_map --ci (κωδικός 0), bash -n, σάρωση UTF-8 (0 U+FFFD).

## Φάση 64: Διακόπτης Κυκλώματος Επιπέδου Συνόδου & Ενίσχυση Εξαγωγής Συγγραφέων (v5.15.3)

### Κατάσταση: ΟΛΟΚΛΗΡΩΘΗΚΕ (2026-09-29)

- [x] **Διακόπτης Κυκλώματος Επιπέδου Συνόδου** -- μάνδαλο διάρκειας διεργασίας `AIManager.fast_tier_offline`: η πρώτη αποτυχία σύνδεσης CPU Edge (11435) μανδαλώνει το επίπεδο εκτός σύνδεσης και εκπέμπει μία εφάπαξ ειδοποίηση· κάθε επόμενη κλήση γρήγορου επιπέδου παρακάμπτει τη θύρα 11435 με ΜΗΔΕΝ ανιχνεύσεις, ΜΗΔΕΝ καθυστέρηση και ΜΗΔΕΝ ανεπιθύμητη υποχώρηση, δρομολογώντας απευθείας στο τοπικό GPU (11434).
- [x] **Ισχυρή κανονικοποίηση συγγραφέων πολλαπλών κλειδιών** -- η `normalize_authors(paper)` επιλύει `authors_str` / `authors` (λίστα λεξικών, λίστα συμβολοσειρών) / `author` στο δίκτυο 18 πηγών, εξαλείφοντας τα ψευδή θετικά "Unknown Authors"· συνδεδεμένη στον δαίμονα (`talos_service.py`) και στον ζωντανό ενορχηστρωτή.
- [x] **Καθαρή τηλεμετρία δαίμονα [EVAL]** -- ένα απερίσπαστο μπλοκ Rich ανά πραγματική αξιολόγηση (`[EVAL] <τίτλος> | Authors: <συγγραφείς> | Score: <X.X>/10 | [<ΑΠΟΦΑΣΗ>] -> DB`), φραγμένο σε επιλυμένο τίτλο.
- [x] **Σιωπηλή αποθήκευση Standalone SYNAPSE** -- το `SynapseClient.synapse_available` μανδαλώνει εκτός σύνδεσης στην πρώτη ανίχνευση θύρας 8000 και αποθηκεύει σιωπηλά γεγονότα σε μνήμη + JSONL (`data/synapse_buffer.jsonl`) χωρίς προειδοποιήσεις ανά άρθρο.
- [x] **Συγχρονισμός έκδοσης** -- 6 αρχεία κώδικα + docker-compose.yml (`talos:5.15.3`) + CITATION.cff (5.15.3, 2026-09-29) + μεταδεδομένα tray/visualizer/wizard/diagnostics + docstrings src/prisma/ και src/search/ + 19 κανονικά αρχεία σε v5.15.3 (2026-09-29).
- [x] **Πέρασαν οι πύλες επαλήθευσης** -- compileall, test_system_integrity, test_talos_version (5.15.3), test_session_circuit_breaker (12 επιτυχίες), verify_dependency_map --ci (κωδικός 0), bash -n, σάρωση UTF-8 (0 U+FFFD).

## Φάση 63: Εναρμόνιση UX & Αναφορών Καθολικού Κόμβου Αναζήτησης (v5.15.2)

- [x] **Αναφορά Αναζήτησης με Προτεραιότητα στον Κώδικα** -- `render_results()` (box.ROUNDED, Κατάταξη / Αστέρια / Αποθετήριο / Περιγραφή / Θέματα / URL GitHub, χωρίς emoji) + `export_search_report()` (χρονικά σημασμένο `data/reports/code_search/code_search_*.md`)· η `run()` καλεί αυτόματα και τα δύο.
- [x] **Αναφορά Χιονοστιβάδας Παραπομπών** -- `render_genealogy()` (box.ROUNDED, Διάσχιση / Βάθος / Τίτλος / Έτος-Πηγή / DOI-URL / Σχετικότητα) + `export_snowball_report()` (χρονικά σημασμένο `data/reports/snowball/snowball_*.md` με πίνακες Πίσω + Μπροστά 2024-2026)· η `run()` καλεί αυτόματα και τα δύο.
- [x] **Κατάργηση JSON dumps TUI/CLI** -- οι σημαίες `--code-search` / `--snowball` και οι επιλογές 3/5 του μενού Ομάδας 2 καλούν απευθείας την `run()`· ο `_render_search_result()` αφαιρέθηκε.
- [x] **Συγχρονισμός έκδοσης** -- 6 αρχεία κώδικα + docker-compose.yml + CITATION.cff + μεταδεδομένα tray/visualizer/wizard/diagnostics + docstrings src/prisma/ και src/search/ + 19 κανονικά αρχεία σε v5.15.2 (2026-09-28).
- [x] **Πέρασαν οι πύλες επαλήθευσης** -- compileall, test_system_integrity, test_talos_version (5.15.2), δοκιμές --code-search και --snowball, verify_dependency_map --ci (κωδικός 0), bash -n, σάρωση UTF-8 (0 U+FFFD).

## Φάση 62: Νευρική Διανυσματική Κρυφή Μνήμη & Επιταχυνόμενη Μηχανή Ενσωματώσεων (v5.15.1)

- [x] **Μόνιμη διανυσματική κρυφή μνήμη** -- πίνακας SQLite `paper_embeddings` + `get_cached_embeddings` / `save_embeddings_batch` στο `src/core/database_manager.py` (BLOB float32, ευρετήριο ανά μοντέλο, ON DELETE CASCADE).
- [x] **Σταδιακή δεικτοδότηση + πρόοδος Rich** -- η `_index_uncached` αποδίδει ζωντανή γραμμή `rich.progress.Progress` (ETA + ρυθμαπόδοση) για το μη αποθηκευμένο δέλτα· ταυτόχρονη ενσωμάτωση μέσω `ThreadPoolExecutor`, αποθήκευση σε παρτίδες (64).
- [x] **Διανυσματική ομοιότητα συνημιτόνου μητρώου** -- η `_matrix_rank` υπολογίζει `S_C(q, D)` για όλες τις N εργασίες σε ένα πέρασμα NumPy (<50ms).
- [x] **Παρουσίαση Rich Table** -- η `render_results` αποδίδει Κατάταξη / Ομοιότητα (%) / Τίτλο / Έτος-Πηγή / DOI-URL / απόσπασμα σε `box.ROUNDED`· η JSON διατηρείται μέσω `render=False`.
- [x] **Συγχρονισμός έκδοσης** -- 6 αρχεία κώδικα + docker-compose.yml + CITATION.cff + μεταδεδομένα tray/visualizer/wizard/diagnostics + docstrings src/prisma/ + 19 κανονικά αρχεία σε v5.15.1 (2026-09-28).
- [x] **Πέρασαν οι πύλες επαλήθευσης** -- compileall, test_system_integrity, test_talos_version (5.15.1), test_neural_vector_search (mock ενσωματώσεις), δοκιμή μόνιμης κρυφής μνήμης, verify_dependency_map --ci (κωδικός 0), bash -n, σάρωση UTF-8 (0 U+FFFD).

## Φάση 61: Καθολικός Κόμβος Επιστημονικής Αναζήτησης & Μηχανή Ανακάλυψης Νευρικών Γράφων (v5.15.0)

- [x] **Αρθρωτή αναδιάρθρωση κατάποσης** -- το υποπακέτο `src/ingestion/sources/` φιλοξενεί και τους 18 προσαρμογείς πίσω από ένα ενιαίο `SOURCE_REGISTRY`· τα `daily_search.py` και `historic_search.py` εισάγουν από αυτό.
- [x] **Μηχανή Χιονοστιβάδας Παραπομπών** -- `src/search/citation_snowballing.py` (διάσχιση γράφου προς τα πίσω/εμπρός, φίλτρο συνάφειας PRISMA, γράφος γενεαλογίας, εισαγωγή στη βάση).
- [x] **Νευρική Διανυσματική Αναζήτηση** -- `src/search/neural_vector_search.py` (τοπικό `nomic-embed-text`, κατάταξη ομοιότητας συνημιτόνου, λεκτική υποχώρηση).
- [x] **Αναζήτηση με Προτεραιότητα στον Κώδικα** -- `src/search/code_first_search.py` (σήματα αναπαραγωγιμότητας GitHub / PapersWithCode / σημείων αναφοράς).
- [x] **Ενσωμάτωση CLI & TUI** -- σημαίες `--snowball` / `--vector-search` / `--code-search` + μενού Ομάδας 2 «Καθολικός Κόμβος Αναζήτησης».
- [x] **Φάκελος Κανόνα 10 04** -- `docs/internal/academic/04_NEURAL_GRAPH_SEARCH_PARADIGMS.md` (7 ενοτήτων, gitignored).
- [x] **Συγχρονισμός έκδοσης** -- 6 βασικά αρχεία + docker-compose.yml + CITATION.cff + μεταδεδομένα tray/visualizer/wizard/diagnostics + docstrings src/prisma/ + 19 κανονικά αρχεία σε v5.15.0 (2026-09-28).
- [x] **Πέρασαν οι πύλες επαλήθευσης** -- compileall, test_system_integrity, test_talos_version (5.15.0), test_neural_vector_search (mock ενσωματώσεις), verify_dependency_map --ci (κωδικός 0), bash -n, σάρωση UTF-8 (0 U+FFFD).

## Φάση 60: Εξαγωγέας BibTeX, Κατάποση Αεροδιαστημικής 18 Πηγών & Πάγωμα Χαρακτηριστικών (v5.14.2)

- [x] **Επιστημονικός Εξαγωγέας BibTeX** -- το `src/utils/bibtex_exporter.py` παρέχει `BibTeXExporter` (κλειδιά παραπομπής `AuthorYearTitleKeyword`, απολύμανση LaTeX, `export_library`/`render_export_summary`, σημαία CLI `--export-bib` και επιλογή Ομάδας 5).
- [x] **Κατάποση 18 πηγών** -- τα `nasa_ntrs_source.py` και `hal_inria_source.py` καταχωρήθηκαν στο `SOURCE_REGISTRY` (daily + historic), `max_workers=18`, το TUI πλαισίων επιλογής και ο χάρτης υγείας API επεκτάθηκαν σε 18, προστέθηκαν ανιχνεύσεις διαγνωστικών.
- [x] **Επίμονη απόφαση PRISMA** -- προστέθηκε η στήλη `papers.prisma_decision` για το φίλτρο INCLUDE του εξαγωγέα.
- [x] **Φάκελος Κανόνα 10 03** -- `docs/internal/academic/03_GREY_LITERATURE_AEROSPACE_EXPANSION.md` (7 ενοτήτων, gitignored).
- [x] **Συγχρονισμός έκδοσης** -- 6 βασικά αρχεία + docker-compose.yml + CITATION.cff + μεταδεδομένα tray/visualizer/wizard + docstrings src/prisma/ + 19 κανονικά αρχεία σε v5.14.2 (2026-09-28).
- [x] **Πέρασαν οι πύλες επαλήθευσης** -- compileall, test_system_integrity, test_talos_version (5.14.2), --export-bib (κωδικός 0), mocks εργοστασίου πηγών, verify_dependency_map --ci (κωδικός 0), bash -n, σάρωση UTF-8 (0 U+FFFD).

## Φάση 59: Σμήνος Ομότιμης Αναθεώρησης Πολλαπλών Πρακτόρων & Μηχανή Συναίνεσης (v5.14.1)

### Κατάσταση: ΟΛΟΚΛΗΡΩΘΗΚΕ (2026-09-28)

- [x] **Σμήνος ομότιμης αναθεώρησης πολλαπλών πρακτόρων** -- `src/prisma/swarm_evaluators.py` (εξειδικευμένες προσωπικότητες AlgorithmicReviewer / EmpiricalReviewer / OperationalReviewer).
- [x] **Αυτοματοποιημένη αξιοπιστία μεταξύ αξιολογητών** -- `calculate_cohens_kappa()` (γενίκευση πολλαπλών αξιολογητών του Kappa του Cohen κατά Fleiss) + `cohens_kappa_pairwise()`.
- [x] **Διαιτητής συναίνεσης με αλυσίδα σκέψης** -- `SwarmConsensusArbiter` (ομόφωνη βραχυκύκλωση, διαιτησία διχασμού, `ConsensusVerdict`).
- [x] **Ενσωμάτωση στον αγωγό PRISMA** -- `PrismaEvaluator.evaluation_mode` (`'single'` / `'swarm'`) με `ThreadPoolExecutor` οριοθετημένο από VRAM και καταγραφή συναίνεσης από τον `PrismaExecutor`.
- [x] **Ενσωμάτωση CLI & TUI** -- σημαία `--prisma --swarm` + προτροπή λειτουργίας διαλογής Ομάδας 3.
- [x] **Ακαδημαϊκός φάκελος Κανόνα 10** -- `docs/internal/academic/02_MULTI_AGENT_CONSENSUS_SWARM.md`.
- [x] **Συγχρονισμός έκδοσης** -- 6 αρχεία κώδικα + εικόνα Docker + CITATION.cff + 19 έγγραφα τεκμηρίωσης σε v5.14.1.
- [x] **Πύλες επαλήθευσης** -- compileall, test_system_integrity, test_talos_version (5.14.1), verify_dependency_map, bash -n, σάρωση UTF-8.

## Φάση 58: Αγωγός PRISMA-ScR του Stanford DSPy (v5.14.0)

### Κατάσταση: ΟΛΟΚΛΗΡΩΘΗΚΕ (2026-09-28)

- [x] **Δηλωτικές υπογραφές PRISMA-ScR** -- `src/prisma/dspy_signatures.py` (τυποποιημένα μοντέλα σχήματος Pydantic v2 που καθρεφτίζουν το παράδειγμα `dspy.Signature` του Stanford DSPy).
- [x] **Ενότητες αγωγού PlanEval** -- `src/prisma/dspy_modules.py` (PrismaPlanner / PrismaEvaluator / PrismaEligibilityJudge / PrismaExecutor με γραμμική ροή 4 φάσεων και ζωντανούς μετρητές εγγραφών).
- [x] **Γεννήτρια διαγράμματος ροής PRISMA 2020 Mermaid** -- `src/prisma/mermaid_generator.py` (`generate_prisma_mermaid()` με ακριβείς μετρήσεις).
- [x] **Συνθέτης ανασκόπησης πεδίου** -- `src/prisma/scoping_review_synthesizer.py` (προσχέδια Markdown + LaTeX σύμφωνα με το PRISMA-ScR).
- [x] **Ενσωμάτωση CLI & TUI** -- σημαία ταχείας αποστολής `--prisma` + επιλογή μενού Ομάδας 3 Προηγμένη Ανάλυση.
- [x] **Ακαδημαϊκός φάκελος Κανόνα 10** -- `docs/internal/academic/01_STANFORD_DSPY_PRISMA_PIPELINE.md` (εμπιστευτικός φάκελος 7 ενοτήτων).
- [x] **Συγχρονισμός έκδοσης** -- 6 αρχεία κώδικα + εικόνα Docker + CITATION.cff + 19 έγγραφα τεκμηρίωσης σε v5.14.0.
- [x] **Επαναπροσδιορισμός οδικού χάρτη** -- CORTEX & n8n -> v5.15.0.
- [x] **Πύλες επαλήθευσης** -- compileall, test_system_integrity, test_talos_version (5.14.0), verify_dependency_map, bash -n, σάρωση UTF-8.

## Φάση 45: Καθολική Αποκατάσταση Χαρακτηριστικών TUI & 100% Κάλυψη Κώδικα (v5.10.15)

### Κατάσταση: ΟΛΟΚΛΗΡΩΜΕΝΗ (2026-08-28)

- [x] **Ενοποιημένο ιεραρχικό TUI 6 ομάδων** -- η `main_menu()` αναδιοργανώθηκε σε έξι οπτικά ομαδοποιημένες ενότητες με `TALOS_QUESTIONARY_STYLE`.
- [x] **Αναβίωση νεκρών υπομενού** -- `profile_settings_menu()`, `database_data_menu()`, `system_health_menu()` επανασυνδέθηκαν; νέα `search_ingestion_menu()`, `analysis_visualization_menu()`, `drl_gwo_menu()`.
- [x] **100% κάλυψη εκτελέσιμων αρθρωμάτων (45/45)** -- κάθε ορφανό άρθρωμα συνδέθηκε στην ιεραρχία.
- [x] **Σουίτα σμήνους GWO** -- δέκτης, διαμορφωτής ανταμοιβής δρομολογητή LLM και ζωντανός πίνακας 3D ενοποιήθηκαν.
- [x] **Ενίσχυση χάρτη σεναρίων** -- η `_resolve_script_path()` εγείρει πλέον `FileNotFoundError` για μη χαρτογραφημένα σενάρια.
- [x] **Συγχρονισμός έκδοσης** -- 6 αρχεία κώδικα + εικόνα Docker + CITATION.cff σε v5.10.15.
- [x] **Επαναπροσδιορισμός οδικού χάρτη** -- DSPy PRISMA -> v5.10.16; CORTEX & n8n -> v5.10.17.
- [x] **Πύλες επαλήθευσης** -- compileall, test_system_integrity, test_talos_version.

## Φάση 44: Αυτόνομος Πίνακας με Προστατευτικές Δικλείδες Απορρήτου & Ενσωμάτωση DeepSeek V4 (v5.10.14)

### Κατάσταση: ΟΛΟΚΛΗΡΩΜΕΝΗ (2026-08-28)

- [x] **Αυτόνομη Δυναμική Ενορχήστρωση (Επιλογή 5)** -- η `select_execution_mode()` απέκτησε `auto_dynamic` με πλήρη κάλυψη πίνακα/επιλογών/ετικετών/σύνοψης/.env.
- [x] **Μηχανή Επίλυσης Προστατευτικών Δικλείδων** -- η `_resolve_strategies(model_type)` καταρρέει την `auto_dynamic` κατά τον χρόνο εκτέλεσης (`_is_network_online`, `_detect_vram_gb`, `_resolve_auto_dynamic`, `_prompt_auto_dynamic_consent`, `_log_auto_matrix`).
- [x] **ΑΠΟΛΥΤΟΣ ΠΕΡΙΟΡΙΣΜΟΣ** -- το `strict_local` βραχυκυκλώνει πριν από κάθε λογική cloud/auto-dynamic.
- [x] **Γνωσιακή Ενσωμάτωση DeepSeek V4** -- η `_execute_openai_compatible_request()` εγχέει `thinking` + `reasoning_effort` για μοντέλα DeepSeek V4.
- [x] **Κατάλογος DeepSeek V4** -- `deepseek-v4-pro` (SWE-bench 75.0 / MMLU-Pro 82.0) και `deepseek-v4-flash` προστέθηκαν στον διαχειριστή μοντέλων και στο μητρώο benchmarks.
- [x] **Συγχρονισμός έκδοσης** -- 6 αρχεία κώδικα + εικόνα Docker + CITATION.cff σε v5.10.14.
- [x] **Επαναπροσδιορισμός οδικού χάρτη** -- DSPy PRISMA -> v5.10.15; CORTEX & n8n -> v5.10.16.
- [x] **Πύλες επαλήθευσης** -- compileall, test_system_integrity, test_talos_version.

## Φάση 43: Κεντρικός Κόμβος Ελέγχου Επιφάνειας Εργασίας, Αυτοθεραπευόμενη Υποδομή & Εγγύηση Εμμονής (v5.10.13)

### Κατάσταση: ΟΛΟΚΛΗΡΩΜΕΝΗ (2026-08-28)

- [x] **Κεντρικός Κόμβος Ελέγχου Επιφάνειας Εργασίας** -- `src/utils/tray_icon.py` επεκτάθηκε σε μενού επτά στοιχείων (Άνοιγμα 3D Visualizer, Άνοιγμα Φακέλου Αναφορών, Άνοιγμα Καταγραφής Συστήματος, Άνοιγμα Τεκμηρίωσης API (Swagger), Ενεργοποίηση Άμεσου Κύκλου Αναζήτησης, Εμφάνιση / Απόκρυψη Παραθύρου Κονσόλας, Τερματισμός Δαίμονα); τίτλος εργαλείου `"TALOS v5.10.13 | Research Intelligence Mesh"`.
- [x] **Αυτοθεραπευόμενη Αυτόματη Εκκίνηση** -- `_is_api_alive(port=8001)` έλεγχος υγείας (0.6s) και `_ensure_api_server()` που εκκινεί κρυφό `uvicorn src.api.main_api:app --host 127.0.0.1 --port 8001` (CREATE_NO_WINDOW) με δειγματοληψία έως 3s.
- [x] **Γέφυρα Επιφάνειας Εργασίας Εγγενούς Λειτουργικού** -- διασταυρωμένα ανοίγματα για `data/reports` και `data/logs/talos_system.log`.
- [x] **Ενιαίο Σημείο Αλήθειας Εμμονής Βάσης Δεδομένων** -- `DatabaseManager.__init__` προεπιλέγει `db_path=None` σε `get_active_profile_db_path()` (βάση ενεργού προφίλ).
- [x] **Αμφίδρομη 4-Καταστάσεων Παραβολική Τηλεμετρία & Μηχανή Συνθετικού Αναγνωριστικού** -- τεκμηρίωση της γέφυρας δεσμών 4 καταστάσεων και της συνθετικής επικάλυψης (`_live_eval_seq` / `_live_eval_state`).
- [x] **Ξεδίπλωμα Ένθετου Τίτλου XML/JSON OpenAIRE** -- `_first()` ξεδιπλώνει `$` / `#text` / `value`.
- [x] **Ανανέωση Κανόνα Περιβάλλοντος** -- `example.env` + `.env` ανακατασκευάστηκαν σε έξι ενότητες.
- [x] **Επαναπροσδιορισμός οδικού χάρτη** -- DSPy PRISMA στην v5.10.14; CORTEX & n8n Gateway στην v5.10.15.
- [x] **Συγχρονισμός έκδοσης** σε 6 αρχεία κώδικα και στην κανονική τεκμηρίωση σε v5.10.13.
- [x] **Πύλες επαλήθευσης** -- compileall, test_system_integrity, test_talos_version, db_stats.

## Φάση 42: Αυτόνομη Ενίσχυση Daemon, Τηλεμετρία 3D Laser & Εργαλεία (v5.10.12)

### Κατάσταση: ΟΛΟΚΛΗΡΩΜΕΝΗ (2026-08-27)

- [x] **Τρισδιάστατες Δέσμες Laser & Παλμοί Φωτονίων** -- Πίνακας `activeBeams` με δέσμες `THREE.Line` και κινούμενες σφαίρες φωτονίων στα 60 FPS.
- [x] **Διαδραστικά Εργαλεία Οπτικοποιητή** -- κλικ-σε-κόμβο raycaster, SNAPSHOT (PNG), FULLSCREEN, THEME, HELP (R/T/F/S/Space/1-3).
- [x] **Pure AJAX Δειγματοληψία 1000ms** -- ανανέωση 16 αυρών υγείας και δεσμών laser.
- [x] **Επίλυση Ενεργής Βάσης Προφίλ** -- το visualizer state επιλύει `get_active_profile_db_path()`.
- [x] **Βελτιστοποιητής SQLite VACUUM** -- `optimize_database(db_path)` με `PRAGMA integrity_check;` + `VACUUM;`.
- [x] **Επαναπροσδιορισμός οδικού χάρτη** -- DSPy PRISMA στην v5.10.13; CORTEX & n8n Gateway στην v5.10.14.
- [x] **Συγχρονισμός έκδοσης** σε 6 αρχεία κώδικα και στην κανονική τεκμηρίωση σε v5.10.12.
- [x] **Πύλες επαλήθευσης** -- compileall, test_system_integrity, test_talos_version.

## Φάση 41: Τρισδιάστατος Αστερισμός Γνώσης με Vendored Three.js (v5.10.11)

### Κατάσταση: ΟΛΟΚΛΗΡΩΜΕΝΗ (2026-08-24)

- [x] **Ενσωματωμένο Three.js** -- Παραγωγική δέσμη Three.js r128 (UMD, MIT) στο `static/js/three.min.js`; ταυτοδύναμη προσάρτηση `app.mount("/static", StaticFiles(directory="static"))` στο `src/api/main_api.py`. Μηδενικές κλήσεις CDN.
- [x] **Ανακατασκευή Οπτικοποιητή Three.js** -- Το `templates/live_foraging_visualizer.html` ανακατασκευάστηκε με Three.js: χρυσός εικοσαεδρικός πυρήνας, 16 δορυφορικοί κόμβοι με κατανομή Fibonacci, φωτοστέφανα υγείας (Πράσινο/Κεχριμπάρι/Κόκκινο/Κυανό), γραμμές σύνδεσης πυρήνα-κόμβων και πλέγμα γειτόνων, δέσμη λέιζερ ενέργειας με εξασθένιση 1.2s.
- [x] **Ακαδημαϊκή Λειτουργία Εκτύπωσης** -- Εναλλαγή THEME αλλάζει το χρώμα καθαρισμού σε λευκό (`0xffffff`) με μπλε ναυτικό HUD υψηλής αντίθεσης.
- [x] **Γέφυρα Ζωντανής Δειγματοληψίας** -- Δειγματοληψία 1.5 δευτερολέπτων στο `GET /api/v1/visualizer/demo-data` παράλληλα με το SSE.
- [x] **Επαναπροσδιορισμός οδικού χάρτη** -- DSPy PRISMA στην v5.10.12; CORTEX & n8n Gateway στην v5.10.13.
- [x] **Συγχρονισμός έκδοσης** σε 6 αρχεία κώδικα και 15 αρχεία τεκμηρίωσης σε v5.10.11.
- [x] **Πύλες επαλήθευσης** -- compileall, test_system_integrity, test_talos_version.
## Φάση 40: Τρισδιάστατος Ολογραφικός Αστερισμός Γνώσης (v5.10.10)

### Κατάσταση: ΟΛΟΚΛΗΡΩΜΕΝΗ (2026-08-24)

- [x] **Τρισδιάστατος Οπτικοποιητής WebGL 1.0** -- Αυτόνομο μονο-αρχειακό HTML με ενσωματωμένους shaders GLSL, χειρόγραφη βιβλιοθήκη τρισδιάστατων μαθηματικών, μηδενικές εξαρτήσεις CDN.
- [x] **Ζωντανή Ροή SSE FastAPI** -- Τρία νέα τερματικά σημεία με υποδομή broadcast `queue.Queue`.
- [x] **Σύνδεση Γεγονότων Πολλαπλών Σωληνώσεων** -- Τα `daily_search.py` και `historic_search.py` εκπέμπουν `paper_evaluated`.
- [x] **Ενσωμάτωση TUI** -- Επιλογή "3. 3D Knowledge Constellation Visualizer (Browser)" με αυτόματο άνοιγμα.
- [x] **Λειτουργία Διπλής Κατάστασης** -- Ζωντανή ροή SSE και Αναπαραγωγή Συνεδρίου Χωρίς Σύνδεση.
- [x] **Ο αριθμός τερματικών σημείων API** αυξήθηκε από 19 σε 22.
- [x] **Συγχρονισμός έκδοσης** σε 6 αρχεία κώδικα και 15 αρχεία τεκμηρίωσης σε v5.10.10.
- [x] **Πύλες επαλήθευσης** -- compileall, test_system_integrity, test_talos_version.
## Φάση 39: Ολοκληρωμένος Έλεγχος Λειτουργιών TUI & Αποκατάσταση Διαχείρισης Προφίλ (v5.10.9)

### Κατάσταση: ΟΛΟΚΛΗΡΩΜΕΝΗ (2026-08-23)

- [x] **Ιεραρχική Αναδιάρθρωση TUI** -- Μενού 16 επιλογών προοδευτικής αποκάλυψης σε έξι οπτικές ομάδες. Εννέα νέες συναρτήσεις χειρισμού υπομενού.
- [x] **Αποκατάσταση Διαχείρισης Προφίλ** -- Εναλλαγή, δημιουργία, προβολή και αποθήκευση προφίλ μέσω του `ProfileManager`.
- [x] **Αποκατάσταση όλων των παραλειπόμενων εργαλείων** -- Ημερήσια και Ιστορική Αναζήτηση, Εξορύκτης Γκρίζας Βιβλιογραφίας, Λήψη PDF, Αναλυτής Αναφορών, Γεννήτρια Μονοπατιών Γνώσης, Σύστημα Συστάσεων, Προφίλ Συγγραφέων, Αναλυτής Τάσεων, Σουίτα GWO, Συντήρηση ΒΔ, Στατιστικά ΒΔ, Έλεγχος Υγείας API.
- [x] **Εκκαθάριση emoji** από τον Διαχειριστή Προφίλ.
- [x] **DSPy PRISMA** μεταφέρθηκε στην v5.10.11. **CORTEX & n8n Gateway** στην v5.10.12.
- [x] **Συγχρονισμός έκδοσης** σε 6 αρχεία κώδικα και 15 αρχεία τεκμηρίωσης σε v5.10.9.
- [x] **Πύλες επαλήθευσης** -- compileall, test_talos_version.
## Φάση 38: Ανακαίνιση Επιχειρησιακού TUI & Ακαδημαϊκή Αισθητική (v5.10.8)

### Κατάσταση: ΟΛΟΚΛΗΡΩΜΕΝΗ (2026-08-22)

- [x] **Ενοποιημένο Θέμα Ερωτήσεων** -- Νέα κανονική ενότητα `src/utils/ui_theme.py` που εξάγει το `TALOS_QUESTIONARY_STYLE` με την παλέτα Cyan/Teal & Bright White (λευκοί διαχωριστές, μπλε IEEE ερωτηματικό, κυανό/τιρκουάζ επιλογή `noinherit`).
- [x] **Στυλ σε Κάθε Ερώτηση** -- Κάθε `questionary.select`/`checkbox`/`text`/`confirm` σε 18 ενότητες που χρησιμοποιούν ερωτήσεις διαβιβάζει πλέον `style=TALOS_QUESTIONARY_STYLE`.
- [x] **Περίγραμμα Πίνακα Κεφαλίδας** -- Ο κορυφαίος πίνακας Rich στο `talos.py` χρησιμοποιεί πλέον `border_style="#006699"`.
- [x] **Αναβολή DSPy PRISMA** -- μεταφέρθηκε στην v5.10.9. Η CORTEX & n8n Gateway μεταφέρθηκε στην v5.10.10.
- [x] **Συγχρονισμός Έκδοσης & Τεκμηρίωσης** -- v5.10.8 συγχρονισμένη σε 5 αρχεία κώδικα και 15 αρχεία τεκμηρίωσης.

## Φάση 37: Ενσωμάτωση Γέφυρας OPTICA (v5.10.7)

### Κατάσταση: ΟΛΟΚΛΗΡΩΜΕΝΗ (2026-08-21)

- [x] **Πελάτης REST OPTICA** -- Προστέθηκε το `src/integration/optica_client.py` (`OpticaClient`) ώστε το TALOS να λειτουργεί ως πελάτης API προς το Project OPTICA (θύρα 8002), εκφορτώνοντας γραφικά cnsplots/PyVis.
- [x] **Δυναμική Επίλυση Διαδρομής ΒΔ** -- Η `request_plot()` επιλύει τη διαδρομή της ενεργής βάσης δεδομένων μέσω της `get_active_profile_db_path()` και αποστέλλει `{data_source, plot_type, journal_template, override_params}` στο `{OPTICA_API_BASE}/plot/generate` με ευπρεπή χειρισμό σφαλμάτων σύνδεσης.
- [x] **Επέκταση Διαμόρφωσης** -- Η ρύθμιση `OPTICA_API_BASE` προστέθηκε στα `config/settings.py`, `config.template.json` και `example.env`.
- [x] **Είσοδος TUI** -- Προστέθηκε η επιλογή "Data Visualizations (via OPTICA)" στην ομάδα Ανάλυση & Ευρήματα με ερωτήσεις τύπου γραφήματος και προτύπου περιοδικού.
- [x] **Αναβολή DSPy PRISMA** -- μεταφέρθηκε στην v5.10.8.
- [x] **Συγχρονισμός Έκδοσης & Τεκμηρίωσης** -- v5.10.7 συγχρονισμένη σε 5 αρχεία κώδικα και 15 αρχεία τεκμηρίωσης.

## Φάση 36: Ενορχηστρωτής Αυτόματης Εκκίνησης Δαίμονα Λειτουργικού Συστήματος (v5.10.6)

- [x] **Γεννήτρια Αυτόματης Εκκίνησης Windows** -- Προστέθηκε το `src/utils/daemon_autostart.py` με την `install_windows_autostart()` που παράγει το `talos_daemon_boot.bat` και μια συντόμευση `.lnk` στον φάκελο Εκκίνησης (pywin32, εικονίδιο `shell32.dll,43`, ελαχιστοποιημένο).
- [x] **Διαδραστικός Έλεγχος Πριν την Πτήση** -- Το `talos.py` αποκτά επιλογή "Configure Daemon & OS Autostart" για στρατηγική δικτύου, πηγές-στόχους και αυτόματη εκκίνηση.
- [x] **Έγχυση Πηγών Δαίμονα** -- Η `_run_live_search()` διαβάζει το `daemon_target_sources` από το `config.json` και τα προωθεί στο `talos_live_agent.py --sources`.
- [x] **Συγχρονισμός Έκδοσης & Τεκμηρίωσης** -- v5.10.6 συγχρονισμένη σε 5 αρχεία κώδικα και 15 αρχεία τεκμηρίωσης.

## Φάση 35: Καθολικός Δυναμικός Πάροχος Μοντέλων & Μηχανή Αυτοθεραπευόμενου Πλεονασμού (v5.10.5)

### Κατάσταση: ΟΛΟΚΛΗΡΩΜΕΝΗ (2026-08-15)

- [x] **Καθολικός Δυναμικός Πάροχος Μοντέλων** -- το `src/utils/model_provisioner.py` (`ModelProvisioner`) με ντετερμινιστική ανίχνευση πρωτοκόλλου (Ollama με άνω-κάτω τελεία / HuggingFace με κάθετο / προθέματα cloud), κλιμάκωση τοπικής επίλυσης διαδρομής 3 επιπέδων (`FAST_EDGE_MODEL_PATH`, ενσωματωμένο `models/<sanitized_name>`, δίκτυο) και `ensure_model_available()` για JIT λήψη Ollama και HuggingFace Hub με εφεδρεία αυτοθεραπείας.
- [x] **Ενσωμάτωση SETUP** -- τα `run_talos.bat` / `run_talos.sh` στο βήμα [5/5] εκτελούν πλέον τον πάροχο για έτοιμη παροχή μοντέλων fast edge + heavy.
- [x] **Ενσωμάτωση Διαχειριστή Μοντέλων** -- ο `_provision_model()` δρομολογεί τις επιλογές μη εγκατεστημένων Ollama/HuggingFace μέσω του παρόχου με ανατροφοδότηση Rich.
- [x] **Απομονωμένες δοκιμές** -- `tests/test_model_provisioner.py` (22 δοκιμές).
- [x] **Συγχρονισμός και των 6 αρχείων κώδικα και 15 αρχείων τεκμηρίωσης σε v5.10.5**.

## Φάση 34: Δυναμική Μηχανή Ανακάλυψης Μοντέλων & Διαλειτουργικότητα Πρωτοκόλλου SYNAPSE (v5.10.4)

### Κατάσταση: ΟΛΟΚΛΗΡΩΜΕΝΗ (2026-08-15)

- [x] **Δυναμική Μηχανή Ανακάλυψης Μοντέλων** -- το `src/ai/llm/model_discovery.py` (`ModelDiscoveryEngine`) ανακαλύπτει ενεργά μοντέλα σε Ollama (GET /api/tags) και παρόχους cloud (NVIDIA NIM, Groq, OpenRouter, Gemini), με εφεδρεία στο απομονωμένο μητρώο `data/model_benchmarks.json`· υπολογίζει κανονικοποιημένες βαθμολογίες ποιότητας `Q_p = raw / max(raw)`.
- [x] **Ενσωμάτωση Δρομολογητή LLM** -- υπερκάλυψη `refresh_quality_scores()` / `load_quality_scores()` και μη-μπλοκαριστή εκπομπή `router_decision` στην `select_provider()`.
- [x] **Ετοιμότητα SYNAPSE** -- νέοι τύποι συμβάντων `model_discovered` / `router_decision`, στατιστικά εκπομπής και endpoint `GET /api/v1/synapse/status`· τα `daily_search.py` / `ai_manager.py` εκπέμπουν μη-μπλοκαριστά συμβάντα `router_decision`.
- [x] **Απομονωμένες δοκιμές** -- `tests/test_model_discovery.py` (15 δοκιμές).
- [x] **Συγχρονισμός και των 6 αρχείων κώδικα και 15+ αρχείων τεκμηρίωσης σε v5.10.4**.

## Φάση 33: Ιεραρχική Ενορχήστρωση DRL - Ενσωμάτωση Δαίμονα & Υποπράκτορα Αναζήτησης (v5.10.3)

### Κατάσταση: ΟΛΟΚΛΗΡΩΜΕΝΗ (2026-08-14)

- [x] **Ενσωμάτωση ζωντανού ενορχηστρωτή αναζήτησης DRL** -- η `evaluate_paper()` στο `src/ai/drl/live_agent_orchestrator.py` (v1.3) συμβουλεύεται την `LLMRouterSubAgent.select_provider()` με τύπο εργασίας `foraging_evaluation` πριν την αξιολόγηση, καταγράφοντας την επιλογή δρομολόγησης στην κονσόλα και στον καταγραφέα ενότητας.
- [x] **Ενσωμάτωση αυτόνομου ερευνητικού δαίμονα** -- το `src/ai/drl/talos_service.py` (v2.1) δρομολογεί όλες τις παρασκηνιακές αξιολογήσεις εργασιών μέσω της `route_daemon_evaluation()`, καταγράφοντας αποφάσεις `[DAEMON/ROUTER]` στο `data/logs/talos_system.log`.
- [x] **Ενσωμάτωση αγωγών αναζήτησης** -- τα `daily_search.py` και `historic_search.py` επερωτούν τον δρομολογητή μέσω `route_evaluation_provider()` για επιλογή παρόχου Fast Edge (`fast_screening`) και Heavy Reasoning (`deep_research`).
- [x] **Βελτιώσεις δρομολογητή** -- προστέθηκαν ο τροποποιητής εργασίας `foraging_evaluation` και ο κοινός βοηθός `estimate_prompt_tokens()` στο `llm_router_subagent.py`.
- [x] **Δοκιμές μονάδας** -- νέες κλάσεις `TestLLMRouterSubAgentPipelineIntegration` και δοκιμές δρομολογητή/εκτιμητή που επιβεβαιώνουν ότι ο ενορχηστρωτής, ο δαίμονας και οι αγωγοί αναζήτησης καλούν την `select_provider()`.
- [x] **Συγχρονισμός και των 6 αρχείων κώδικα και 15 αρχείων τεκμηρίωσης σε v5.10.3**.


## Φάση 32: Υποπράκτορας Δρομολογητή LLM, Διεπίπεδη Διαμόρφωση Ανταμοιβής GWO & Διαδραστικό TUI Πλαισίων Επιλογής 16 Πηγών (v5.10.2)

### Κατάσταση: ΟΛΟΚΛΗΡΩΜΕΝΗ (2026-08-14)

- [x] **Υποπράκτορας Δρομολογητή LLM (`src/ai/drl/llm_router_subagent.py`)** -- ο `LLMRouterSubAgent` επιλέγει τον βέλτιστο ενεργό πάροχο από τα βάρη `models/gwo_llm_router_reward_weights.json` (με εφεδρεία Pareto), βαθμολογώντας σήματα ποιότητας/καθυστέρησης/κόστους/rate-limit· ο `AIManager` αναθέτει σε αυτόν την επιλογή παρόχου cloud/legacy.
- [x] **Διαμορφωτής Ανταμοιβής Δρομολογητή LLM με GWO (`src/ai/optimizers/gwo_llm_router_reward_shaper.py`)** -- κλάση `GWOLLMRouterRewardShaper` για Διεπίπεδη Βελτιστοποίηση Ανταμοιβής Πολλαπλών Στόχων με κανονικό GWO· διάνυσμα βαρών 4 διαστάσεων με προβολή simplex, εσωτερική αξιολόγηση δρομολογητή υπό `R = w_q*Quality - w_l*Latency - w_c*Cost - w_p*Penalty`· εξάγει `models/gwo_llm_router_reward_weights.json`.
- [x] **Μετονομασία δέκτη GWO** -- `gwo_rl_optimizer.py` σε `gwo_foraging_hyperparameter_tuner.py`· προστέθηκε κλάση `GWOForagingHyperparameterTuner`· η εξαγωγή μετονομάστηκε σε `models/gwo_foraging_hyperparameters.json`.
- [x] **Διαδραστικό TUI Πλαισίων Επιλογής 16 Πηγών** -- `questionary.checkbox()` στο `talos.py` στις επιλογές 3α/3β για όλες τις 16 πηγές (προεπιλεγμένες), μεταβίβαση μέσω `--sources`.
- [x] **Φιλτράρισμα πηγών** -- `SOURCE_REGISTRY` + `build_sources()` + `--sources` argparse στα `daily_search.py` / `historic_search.py`.
- [x] **Απομονωμένες δοκιμές** -- `tests/test_gwo_llm_router_reward_shaper.py` (6 δοκιμές).
- [x] **Συγχρονισμός και των 6 αρχείων κώδικα και 15 αρχείων τεκμηρίωσης σε v5.10.2**.


## Φάση 31: Κλιμάκωση Περιβάλλοντος DRL & Επέκταση Χώρου Δράσεων (v5.10.1)

### Κατάσταση: ΟΛΟΚΛΗΡΩΜΕΝΗ (2026-08-14)

- [x] **Κλιμάκωση περιβάλλοντος DRL (`src/ai/drl/talos_env.py` v3.2)** -- ο χώρος καταστάσεων κλιμακώθηκε σε 23 διαστάσεις (1 ώρα + 16 λόγοι πηγών + 2 σερί + 4 λόγοι παρόχων) και ο χώρος δράσεων σε 17 δράσεις (16 πηγές + ύπνος).
- [x] **Κανονική ανακάλυψη 16 πηγών** -- η `_load_source_list()` εγγυάται την παρουσία των `openreview` και `openaire` και υποβαθμίζεται στην πλήρη λίστα 16 πηγών `ALL_KNOWN_SOURCES`.
- [x] **Ετοιμότητα επανεκπαίδευσης DDDQN** -- το `drl_agent.py` (v2.1) ανακατασκευάζει αυτόματα τα δίκτυα για input_dim=23 / action_dim=17· υπερπαράμετροι GWO (LR=3.361e-05, GAMMA=0.6983, EPS_DECAY=0.9202) τεκμηριωμένες στο `drl_trainer.py` (v1.4).
- [x] **Χαρτογράφηση ζωντανού ενορχηστρωτή** -- τα `live_agent_sources.py` (v1.1) και `live_agent_orchestrator.py` (v1.2) ευθυγραμμίζουν τη χαρτογράφηση πηγών και το διάνυσμα καταστάσεων 23 διαστάσεων `calculate_state()`.
- [x] **Δοκιμές επαλήθευσης περιβάλλοντος DRL** -- `TestDRLEnvironment` στο `tests/test_multi_tier.py` που βεβαιώνει σχήμα παρατήρησης `(23,)` και χώρο δράσεων `Discrete(17)`.
- [x] **Συγχρονισμός και των 6 αρχείων κώδικα και 15 αρχείων τεκμηρίωσης σε v5.10.1**.


## Φάση 30: Επέκταση Ακαδημαϊκής Κατάποσης - Ενσωμάτωση OpenReview & OpenAIRE (v5.10.0)

### Κατάσταση: ΟΛΟΚΛΗΡΩΜΕΝΗ (2026-08-14)

- [x] **Πηγή OpenReview (`src/ingestion/openreview.py`)** -- Πράκτορας `OpenReviewSource` για το OpenReview API V2 με εφεδρική πρόσβαση πιστοποιημένου/επισκέπτη πελάτη και σύνοψη αποφάσεων/βαθμολογιών αξιολόγησης προσαρτημένη στις περιλήψεις.
- [x] **Πηγή OpenAIRE (`src/ingestion/openaire.py`)** -- Πράκτορας `OpenAIRESource` για το OpenAIRE Research Graph API v11.3.0 με προαιρετικό διακριτικό φορέα και μεταδεδομένα επιχορηγήσεων/χρηματοδότησης προσαρτημένα στις περιλήψεις.
- [x] **Κατάποση 16 πηγών** -- Τα `daily_search.py` και `historic_search.py` εκτελούν πλέον και τις δύο νέες πηγές· η `CORESource` αποκαταστάθηκε στο ημερήσιο δίκτυο (προηγουμένως εισαγόταν αλλά δεν εκτελούνταν).
- [x] **Πρότυπα Διαμόρφωσης & Περιβάλλοντος** -- Το `example.env` απέκτησε `OPENREVIEW_USERNAME`, `OPENREVIEW_PASSWORD`, `OPENAIRE_TOKEN`· το `requirements.txt` απέκτησε `openreview-py`· τα `config.template.json`/`config.json` απέκτησαν `openreview_query`, `openaire_query` και καταχωρήσεις `max_results_config`.
- [x] **Χάρτης εξαρτήσεων** -- Ο `IMPORT_TO_DOC_MAP` του `verify_dependency_map.py` καταχώρισε τις δύο νέες ενότητες πηγών.
- [x] **Μοναδιαίες δοκιμές** -- Προστέθηκαν `tests/test_openreview_source.py` (13 δοκιμές) και `tests/test_openaire_source.py` (21 δοκιμές) για απομονωμένη κάλυψη των νέων πηγών.
- [x] **Συγχρονισμός και των 6 αρχείων κώδικα και 15 αρχείων τεκμηρίωσης σε v5.10.0** και καθολική ενημέρωση κεφαλίδων σε 72 αρχεία στα `src/`, `config/` και `tests/` (συμπεριλαμβανομένου του υποσυστήματος Αυτόνομου Κόκκινου Ελεγκτή).


## Φάση 29: Καθολικό Πλέγμα Νέφους & Επέκταση Πολυπαρόχου Εφεδρείας (v5.9.18)

### Κατάσταση: ΟΛΟΚΛΗΡΩΜΕΝΗ (2026-08-14)

- [x] **Καθολικό Πλέγμα Νέφους (`config/settings.py`)** -- Προστέθηκαν `NVIDIA_BASE_URL`, `GROQ_BASE_URL`, `CEREBRAS_BASE_URL`, `GITHUB_MODELS_BASE_URL`, `MISTRAL_BASE_URL`, `OPENROUTER_BASE_URL`, `HF_BASE_URL`, προεπιλεγμένα μοντέλα ανά πάροχο, λήπτες κλειδιών API και η κανονική λίστα `TALOS_CLOUD_PROVIDERS` (9 πάροχοι).
- [x] **Μητρώο παρόχων συμβατών με OpenAI (`src/core/ai_manager.py`)** -- Προστέθηκε το `OPENAI_COMPATIBLE_REGISTRY` (8 πάροχοι εφεδρείας), εκκίνηση `__init__` καθοδηγούμενη από λεξικό με ομαλή παράλειψη ελλιπών κλειδιών, ενοποιημένος `_execute_openai_compatible_request()` με ανεξάρτητους διακόπτες 5 αποτυχιών και `_execute_cloud_chain()` καθοδηγούμενη από μητρώο.
- [x] **TUI Ρυθμίσεων Νέφους του Διαχειριστή Μοντέλων** -- Η `select_cloud_models()` αποδίδει πίνακα Rich και των 9 παρόχων (Όνομα Παρόχου, Κλειδί Περιβάλλοντος, Κατάσταση, Προεπιλεγμένο Μοντέλο, Βασική Διεύθυνση URL) με επεξεργασία κλειδιού/μοντέλου ανά πάροχο μέσω `CLOUD_PROVIDER_CATALOG` και `get_cloud_provider_rows()`.
- [x] **Πρότυπα Διαμόρφωσης & Περιβάλλοντος** -- Το `example.env` απέκτησε 6 νέα κλειδιά παρόχων· η `ai_provider_priority` των `config.template.json`/`config.json` ενημερώθηκε στη λίστα 10 στοιχείων με προτεραιότητα τοπικού· το `failure_threshold` αυξήθηκε σε 5.
- [x] **Μοναδιαίες Δοκιμές** -- Επέκταση των `tests/test_multi_tier.py` (εκκίνηση μητρώου, ανακάλυψη παρόχων, παράλειψη ελλιπών κλειδιών, εφεδρεία κλιμάκωσης) και `tests/test_model_manager.py` (πίνακας καταλόγου).
- [x] **Συγχρονισμός και των 6 αρχείων κώδικα και 15 αρχείων τεκμηρίωσης σε v5.9.18** (καθολική ενημέρωση κεφαλίδων σε `src/`, `config/`, `tests/`)


## Φάση 28: Καθολικό Rich TUI, Αναβάθμιση Επιχειρησιακής Καταγραφής & Καθολική Ενημέρωση Κεφαλίδων (v5.9.17)

### Κατάσταση: ΟΛΟΚΛΗΡΩΜΕΝΗ (2026-08-14)

- [x] **Επιχειρησιακή Καταγραφή (`src/utils/logger.py`)** -- Εργοστάσιο `get_logger(name)` με `rich.logging.RichHandler` (κονσόλα χωρίς emoji) και `logging.handlers.RotatingFileHandler` στο `data/logs/talos_system.log` (10 MB, 5 αντίγραφα, `%(asctime)s - %(name)s - %(levelname)s - %(message)s`).
- [x] **Καθολικό Rich TUI & Επιβολή Καταγραφής** -- Έλεγχος των `talos.py`, `model_manager.py`, `research_pivot.py`, `generate_docs.py`, `red_tester.py`: `print()` -> logger, Rich Console/Panel για μενού/πίνακες, `questionary` για προτροπές, αφαίρεση παλαιού γυμνού `input()`.
- [x] **Μηδενικά Emojis** -- Αφαίρεση όλων των emoji από το `research_pivot.py`· μετάφραση των ενσωματωμένων ελληνικών συμβολοσειρών στο `generate_docs.py` στα αγγλικά.
- [x] **Καθολική Ενημέρωση Κεφαλίδων** -- 78 αρχεία συγχρονίστηκαν από `Project: TALOS v5.9.15/v5.9.16` σε `v5.9.17`.
- [x] **Ενημέρωση Docker & Εκκινητών** -- `Dockerfile`, `docker-compose.yml` (`talos:5.9.17`), `requirements.txt`, `docs/DOCKER.md`, `run_talos.bat`, `run_talos.sh`.
- [x] **Συγχρονισμός και των 5 αρχείων κώδικα και 15 αρχείων τεκμηρίωσης σε v5.9.17**


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

## Φάση 46: Βελτιστοποίηση Απόδοσης Μηδενικού Κινδύνου & Μηχανή Ακαδημαϊκής Εξαγωγής LaTeX/BibTeX (v5.10.16)

- [x] **Λειτουργία SQLite WAL + εργοστάσιο σύνδεσης PRAGMA** στο `DatabaseManager` (`busy_timeout=5000`, `cache_size=-64000`, `synchronous=NORMAL`, `temp_store=MEMORY`).
- [x] **Ασφαλής διαδικτυακή στιγμιοληψία** (`snapshot_manager.py`) πριν από VACUUM, επαναβαθμολόγηση και επαναξιολόγηση.
- [x] **Συγκέντρωση συνόδων HTTP** (`http_client.py`) σε 13 πηγές και τοπική εξαγωγή Ollama/Fast-edge.
- [x] **Ντετερμινιστική LRU αποθήκευση** σε αγνές βοηθητικές συναρτήσεις δρομολόγησης.
- [x] **Ακαδημαϊκός εξαγωγέας μηδενικών εξαρτήσεων** (`academic_export.py`) για BibTeX (.bib) και LaTeX (.tex).
- [x] **Συγχρονισμός έκδοσης** σε 6 αρχεία κώδικα, docker-compose.yml, CITATION.cff και 15+ αρχεία τεκμηρίωσης σε v5.10.16.

## Φάση 47: Ζωντανή Τηλεμετρία HUD, Ελαχιστοποίηση-σε-Δίσκο Win32 & Bootstrap Linux (v5.11.0)

### Κατάσταση: ΟΛΟΚΛΗΡΩΜΕΝΗ (2026-09-23)

- [x] **Κονσόλα Ζωντανής Τηλεμετρίας HUD** -- ροή glassmorphism κάτω δεξιά στο `templates/live_foraging_visualizer.html` (buffer 40 γραμμών, αυτόματη κύλιση, συντομεύσεις `C`/`L`, απόκρυψη κατά το στιγμιότυπο).
- [x] **Ελαχιστοποίηση σε Δίσκο Win32** -- η `enable_close_to_tray()` υποκλέπτει τη WndProc της κονσόλας (WM_CLOSE / SC_CLOSE σε SW_HIDE) στο `src/utils/tray_icon.py`.
- [x] **Τηλεμετρία Πλήρους Τίτλου & Συγγραφέων** -- το [EVAL] αποδίδει τον πλήρη τίτλο και τους κανονικοποιημένους συγγραφείς σε δομή Rich δύο γραμμών· η `_sanitize_connection_error()` δίνει καθαρό αγγλικό μήνυμα σφαλμάτων socket.
- [x] **Μόνιμο Ιστορικό Αξιολόγησης** -- `src/utils/evaluation_history.py` (JSONL) + `_show_evaluation_history(limit=30)` προβολή πίνακα Rich στο `talos.py`.
- [x] **Αυτόνομο Bootstrap Linux** -- `run_talos.sh` `detect_or_install_conda()` + `ensure_talosenv()` για Ubuntu/Debian/Linux Mint.
- [x] **Συγχρονισμός έκδοσης** -- 6 αρχεία κώδικα + docker-compose.yml + CITATION.cff + 15 κανονικά έγγραφα σε v5.11.0 (2026-09-23).
- [x] **Πύλες επαλήθευσης** -- compileall, test_system_integrity, test_talos_version, bash -n.

## Φάση 48: Εξυγίανση Υπομενού TUI & Πλήρης Έλεγχος Ιεραρχίας (v5.11.1)

### Κατάσταση: ΟΛΟΚΛΗΡΩΜΕΝΗ (2026-09-24)

- [x] **Διόρθωση λίστας επιλογών Questionary** -- η `profile_settings_menu()` στο `talos.py` ξαναγράφτηκε με `questionary.Choice(title=..., value=...)`, φρουρό `__back__` και αυστηρά διαδοχική αρίθμηση 1-8.
- [x] **Διορθώσεις δρομολόγησης** -- «1. Manage Profiles» -> `run_script("profile_manager.py", ...)`· «5. Model Discovery (Quality Scoring)» -> ενσωματωμένος `_run_model_discovery()`.
- [x] **Ενιαία αισθητική υπομενού** -- κάθε υπομενού τυποποιήθηκε με ετικέτες `[ Back / Return to Main Menu ]` και `TALOS_QUESTIONARY_STYLE`.
- [x] **Συγχρονισμός έκδοσης** -- 6 αρχεία κώδικα + docker-compose.yml + CITATION.cff + 19 κανονικά έγγραφα σε v5.11.1 (2026-09-24).
- [x] **Πύλες επαλήθευσης** -- compileall, test_system_integrity, test_talos_version, bash -n.

## Φάση 49: Onboarding Windows Μηδενικών Κλικ & Μηχανή Προετοιμασίας (v5.11.2)

### Κατάσταση: ΟΛΟΚΛΗΡΩΜΕΝΗ (2026-09-26)

- [x] **Οδηγός προετοιμασίας με ένδειξη προόδου** -- νέα ρουτίνα `:AUTO_PREFLIGHT` στο `run_talos.bat` με αριθμημένη καθοδήγηση `[Step 1/5]`-`[Step 5/5]`, σημαντικά `[OK]` και ρητές εκτιμήσεις χρόνου για πρωτάρηδες χρήστες.
- [x] **Σιωπηλό bootstrap Miniconda3** -- αυτόματη λήψη ~85 MB μέσω εγγενούς `curl.exe -# -fS` και σιωπηλή εγκατάσταση `/S` στο `%USERPROFILE%\miniconda3` όταν δεν εντοπίζεται χρόνος εκτέλεσης Conda.
- [x] **Υπορουτίνα `:DISCOVER_CONDA`** -- ανίχνευση `condabin\conda.bat` σε πολλαπλές ρίζες και PATH, με συμβατή προς τα πίσω συμπλήρωση της `CONDA_ACTIVATE_PATH` για όλες τις υπάρχουσες επιλογές μενού.
- [x] **Σιωπηλή πύλη ταχείας παράκαμψης** -- τέσσερις αθόρυβοι έλεγχοι εκκίνησης (Conda, talosenv, .env, δοκιμή βασικών πακέτων) παρακάμπτουν πλήρως τον οδηγό· οι καθημερινές εκκινήσεις φτάνουν στο κύριο μενού σε κάτω από ένα δευτερόλεπτο.
- [x] **Ενίσχυση batch** -- διαφυγή παρενθέσεων με caret εντός μπλοκ κώδικα, καθαρή πειθαρχία στοίβας `call`/`goto :EOF`, αυστηρό CRLF επαληθευμένο σε επίπεδο byte (μηδέν μεμονωμένα LF).
- [x] **Συγχρονισμός έκδοσης** -- 6 αρχεία κώδικα + docker-compose.yml + CITATION.cff + 19 κανονικά έγγραφα σε v5.11.2 (2026-09-26).
- [x] **Πύλες επαλήθευσης** -- compileall, test_system_integrity, test_talos_version, bash -n, έλεγχος ετικετών/άλματων, σάρωση ακεραιότητας UTF-8.

## Φάση 50: Ακεραιότητα Οικοσυστήματος & Ευθυγράμμιση Εξαρτήσεων (v5.11.3)

### Κατάσταση: ΟΛΟΚΛΗΡΩΜΕΝΗ (2026-09-26)

- [x] **Έλεγχος επτά διορθώσεων στον κώδικα (7/7 επαληθευμένες)** -- μη μπλοκάρον SSE μέσω `await asyncio.to_thread(_visualizer_event_queue.get, True, 1.0)` (`main_api.py`)· cached singleton `_get_db()` στα endpoints δειγματοληψίας του οπτικοποιητή· έγχυση `TALOS_HEADLESS=1` στις `_run_scrape_background`/`_run_evaluate_background`· σειριαλοποίηση του monkey-patch του `sys.exit` με `_scrape_task_lock = threading.Lock()`· φράγμα top_k στη `semantic_search` (database_manager.py)· φρουροί payload στη `_record_beam_event`· ανθεκτικότητα `except Exception` στον monitor GWO.
- [x] **Αποστολή OpenReview V2** -- νέο βοηθητικό `OpenReviewSource._query_notes()`: προτιμώμενη `search_notes(term=)`, υποκατάσταση `get_notes(content={"title": ...})`, απλή επανάληψη `get_notes(limit=)` σε `TypeError`· 4 νέες ερμητικές δοκιμές στο `tests/test_openreview_source.py`.
- [x] **Διακόπτης κυκλώματος batch Fast-Edge** -- το `AIManager._fast_edge_offline_memo` παρακάμπτει γνωστό offline endpoint θύρας 11435 για το υπόλοιπο του batch με άμεση υποχώρηση σε GPU (11434) και γραμμή καταγραφής `[INFO]`.
- [x] **Εξάλειψη απαρχαιώσεων** -- ο `lifespan` context manager του FastAPI αντικαθιστά το `@app.on_event("startup")` (μηδέν προειδοποιήσεις `on_event`)· ζεύγος φίλτρων FutureWarning με εμβέλεια module/μηνύματος σιγάζει την ειδοποίηση λήξης υποστήριξης του `google.generativeai`.
- [x] **Έλεγχος κατάστασης GWO πολλαπλών διαδρομών** -- η `_show_drl_status` ελέγχει τα αντικείμενα foraging/router/legacy GWO με μηνύματα `Present` έναντι `Default Baseline Active`.
- [x] **Επισκευή επαληθευτή εξαρτήσεων** -- regex κεφαλίδας Ενότητας 7 δύο γλωσσών (Αγγλικά + ελληνικός master) + υποστήριξη φραχτών με ετικέτα γλώσσας (```text) + διεύρυνση whitelist· παλαιές διαδρομές `scripts/` διορθώθηκαν σε `src/utils/`· αποκαταστάθηκε έξοδος `--ci` με 0.
- [x] **Κωδικοποίηση έκδοσης** -- η σκλήρυνση σταθερότητας πριν από την επίδειξη (πρώην patch ίδιας έκδοσης v5.11.2) σφραγίζεται επίσημα υπό την v5.11.3 μαζί με τις 5 διορθώσεις ακεραιότητας οικοσυστήματος, με πλήρες κανονικό ιστορικό αλλαγών, φάση χρονολογίου και ενότητα λευκώματος δυνατοτήτων.
- [x] **Συγχρονισμός έκδοσης** -- 6 αρχεία κώδικα + docker-compose.yml + CITATION.cff + μεταδεδομένα tray/visualizer/evaluation-history + 19 κανονικά έγγραφα σε v5.11.3 (2026-09-26).
- [x] **Πύλες επαλήθευσης** -- compileall, test_system_integrity (μηδέν προειδοποιήσεις on_event), test_talos_version, test_openreview_source, verify_dependency_map --ci (έξοδος 0), πλήρης παλινδρόμηση multi-tier, bash -n, σάρωση ακεραιότητας UTF-8 (μηδέν glyphs U+FFFD).

---

## Φάση 51: Οδηγός Ρύθμισης Έρευνας & Failsafe Ενσωμάτωση (v5.12.0)

### Κατάσταση: ΟΛΟΚΛΗΡΩΜΕΝΗ (2026-09-27)

- [x] **Οδηγός Ρύθμισης Έρευνας** -- το `src/utils/research_setup_wizard.py` παρέχει ροή ενσωμάτωσης 4 βημάτων με προτεραιότητα στα Αγγλικά (θέμα + γνωσιακή επικύρωση, στρατηγική εκτέλεσης, παράθυρο αναζήτησης, πρώτη πτήση οπτικοποιητή).
- [x] **Αυτόματη εκκίνηση τοπικής ΤΝ με ευρετική παράκαμψη** -- έλεγχος θυρών 11434/11435 (0,8s), σιωπηρή εκκίνηση `ollama serve`, οριοθετημένη αναμονή 2s, ντετερμινιστική υποχώρηση βάσει κανόνων όταν είναι εκτός σύνδεσης.
- [x] **Χρονικό όριο επικύρωσης πεδίου 2 δευτερολέπτων** -- γνωσιακή επικύρωση Fast Edge (Llama-3.1-8B / Neutrino-8B) με σκληρό χρονικό όριο και υποχώρηση πρότασης υποπεδίων.
- [x] **Αυτοματισμός σήματος πρώτης εκτέλεσης** -- το `data/.talos_onboarded` εγγράφεται κατά την ολοκλήρωση· το `talos.py:main_menu()` εκκινεί αυτόματα τον οδηγό μία φορά και εκκινεί γρήγορα (<0,3s) στη συνέχεια.
- [x] **Ενσωμάτωση TUI** -- η επιλογή 2 του `profile_settings_menu()` δρομολογεί στον οδηγό· ο `_SCRIPT_MAP` τον καταχωρεί στην ομάδα `utils`.
- [x] **Ερμητικές δοκιμές** -- το `tests/test_research_setup_wizard.py` καλύπτει σήμα, ευρετική επικύρωση και εμμονή στρατηγικής/παραθύρου.
- [x] **Συγχρονισμός έκδοσης** -- 6 αρχεία κώδικα + docker-compose.yml + CITATION.cff + μεταδεδομένα tray/visualizer/evaluation-history + 19 κανονικά έγγραφα σε v5.12.0 (2026-09-27).
- [x] **Πύλες επαλήθευσης** -- compileall, test_system_integrity, test_talos_version, test_research_setup_wizard, verify_dependency_map --ci (έξοδος 0), bash -n, σάρωση ακεραιότητας UTF-8 (μηδέν glyphs U+FFFD).

---

## Φάση 52: Διαφάνεια Ερωτημάτων Οδηγού Έρευνας & Γρήγορη Αποστολή CLI (v5.12.1)

### Κατάσταση: ΟΛΟΚΛΗΡΩΜΕΝΗ (2026-09-27)

- [x] **Πίνακας διαφάνειας ερωτημάτων οδηγού** -- η `_render_query_preview()` αποδίδει έναν στρογγυλεμένο πίνακα Rich (τίτλος «Generated Academic Search Queries») προεπισκοπώντας τα συνταχθέντα boolean ερωτήματα για τις κύριες πηγές (arXiv, IEEE Xplore, Scopus (Elsevier), OpenAlex, Semantic Scholar, Springer Link) συν τα κριτήρια ένταξης/αποκλεισμού.
- [x] **Πύλη επιβεβαίωσης χρήστη** -- επιβεβαίωση Questionary («Proceed with these compiled search parameters?», προεπιλογή True) προηγείται της εγγραφής στο config.json· η απόρριψη επανεισάγει το πεδίο, η ακύρωση τερματίζει καθαρά.
- [x] **Σημαίες γρήγορης αποστολής CLI** -- το `talos.py` αποκτά `--wizard`, `--daily`, `--stats` και `--help`/`-h` μέσω `_handle_cli_flags()` / `_cli_help_table()`, καθεμία αποστέλλεται μέσω `run_script()` και εξέρχεται με 0.
- [x] **Συγχρονισμός έκδοσης** -- 6 αρχεία κώδικα + docker-compose.yml + CITATION.cff + μεταδεδομένα tray/visualizer/evaluation-history/wizard + 19 κανονικά έγγραφα σε v5.12.1 (2026-09-27).
- [x] **Πύλες επαλήθευσης** -- compileall, test_system_integrity, test_talos_version, `talos.py --help` (έξοδος 0), verify_dependency_map --ci (έξοδος 0), bash -n, σάρωση ακεραιότητας UTF-8 (μηδέν glyphs U+FFFD).

---

## Φάση 53: Αυτο-Θεραπευόμενος Διαχειριστής ΤΝ, Πίνακας 5 Στρατηγικών & Ακεραιότητα Οδηγού (v5.12.2)

### Κατάσταση: ΟΛΟΚΛΗΡΩΜΕΝΗ (2026-09-27)

- [x] **Αυτο-θεραπευόμενος έλεγχος & εκκίνηση Ollama** -- η `probe_local_ollama()` εκδίδει έλεγχο `GET /api/tags` 0,8s πριν την πτήση· η `_ensure_local_ollama_runtime()` συμβουλεύεται το `auto_start_local_llm`, προσφέρει επιβεβαίωση `TALOS_QUESTIONARY_STYLE`, εκκινεί το `ollama serve` αποσπασμένα και ελέγχει έως 3,0s πριν την ομαλή υποβάθμιση.
- [x] **Περικοπή παρόχων** -- οι πάροχοι cloud καταχωρούνται μόνο όταν υπάρχει κλειδί· τα απουσιάζοντα κλειδιά σταθμεύουν σιωπηλά ως `STANDBY_NO_KEY` σε νέο χάρτη `provider_status` (χωρίς καταρράκτες προειδοποιήσεων ή απόπειρες δικτύου).
- [x] **Έγχυση κλειδιού cloud κατά παραγγελία** -- οι `_prompt_cloud_key()` / `_persist_env_key()` / `_register_cloud_provider_on_demand()` προτρέπουν με ασφάλεια, επικυρώνουν, αποθηκεύουν στο `.env` και καταχωρούν πάροχο κατά τη διάρκεια εκτέλεσης.
- [x] **Μετεγκατάσταση Google GenAI GA SDK** -- η `_execute_gemini_request()` προτιμά το `google.genai` (`GenerateContentConfig`), υποχωρώντας στο παλαιό `google.generativeai` μόνο όταν το GA SDK απουσιάζει.
- [x] **Ευρετικό φίλτρο stopwords ερωτημάτων** -- η `_extract_salient_terms()` αφαιρεί αγγλικά stopwords και θόρυβο στίξης από τα fallback boolean ερωτήματα, οριοθετώντας σε 4-6 κύριους όρους για έγκυρα ερωτήματα IEEE Xplore / Scopus / arXiv.
- [x] **Πίνακας στρατηγικών εκτέλεσης 5 επιπέδων** -- οι `EXECUTION_STRATEGIES` + `ai_strategy_selector.py` εκθέτουν `strict_local` / `local_first` / `cloud_first` / `strict_cloud` (αποτύπωμα GPU VRAM 0%) / `auto_dynamic`, αποθηκευμένα σε config.json + .env και εκτεθειμένα μέσω `--strategy [mode]` συν τον διακόπτη TUI.
- [x] **Παράθυρο ιστορικής αναζήτησης βάσει ημερών** -- προεπιλογές Βήματος 3 (30/365/1095/1825/3650 ημέρες) συν προσαρμοσμένες θετικές ακέραιες ημέρες μέσω `_prompt_custom_days()`, αποθηκεύοντας `days_to_search_historic`.
- [x] **Ακεραιότητα σήματος & ακύρωσης** -- η `_render_cancelled()` ματαιώνει σε κάθε ακύρωση, εξαλείφει τις εγγραφές 'N/A' στο config και προστατεύει το σήμα `data/.talos_onboarded`.
- [x] **Ανθεκτικότητα αναλυτή σκέψης/λογικής** -- οι `_strip_thinking_tags()` / `_extract_assistant_content()` ξετυλίγουν τα `reasoning_content`, `thinking` και `<think>`.
- [x] **Εντολή αγγλικής πρώτης γλώσσας** -- η `LANGUAGE_AND_SYNTAX_MANDATE` επιβάλλει ακαδημαϊκά αγγλικά και απαγορεύει τα προθέματα `topic:`.
- [x] **Βάση τοπικής GPU** -- το `LOCAL_GPU_MODEL` ορίζεται στο επαληθευμένο `llama3.1:8b`.
- [x] **Συγχρονισμός έκδοσης** -- 6 αρχεία κώδικα + docker-compose.yml + CITATION.cff + μεταδεδομένα tray/visualizer/evaluation-history/wizard + 19 κανονικά έγγραφα σε v5.12.2 (2026-09-27).
- [x] **Πύλες επαλήθευσης** -- compileall, test_system_integrity, test_talos_version, test_research_setup_wizard (28 δοκιμές), verify_dependency_map --ci (έξοδος 0), bash -n, σάρωση ακεραιότητας UTF-8 (μηδέν glyphs U+FFFD).

## Φάση 54: Εκσυγχρονισμός Αναπροσανατολισμού Έρευνας & Ενσωμάτωση Μενού Οδηγού (v5.12.3)

### Κατάσταση: ΟΛΟΚΛΗΡΩΜΕΝΗ (2026-09-27)

- [x] **Επίλυση κανονικών διαδρομών Αναπροσανατολισμού Έρευνας** -- το `research_pivot.py` απορρίπτει τον σπασμένο υποφάκελο `scripts/` και την απαρχαιωμένη διαδρομή `src/ai/scripts/query_translator.py`· ένας `_SCRIPT_MAP` αγκυρωμένος στο `REPO_ROOT` επιλύει τον Γνωσιακό Μεταγλωττιστή Ερωτημάτων (`src/ai/llm/query_translator.py`), το σενάριο επαναξιολόγησης (`src/utils/reevaluate_database.py` / `recalculate_scores.py`) και τον εκπαιδευτή DRL (`src/ai/drl/train_agent.py`), όλα εκτελούμενα με `sys.executable`.
- [x] **Αυστηρή επαλήθευση κωδικών επιστροφής υποδιεργασιών** -- ο οδηγός καταγράφει τον `proc.returncode` και αναφέρει `YES` μόνο για κωδικό επιστροφής 0· οι μη μηδενικοί κωδικοί εμφανίζονται ως `FAILED (Code X)` με την τελευταία έξοδο, εξαλείφοντας το προηγούμενο `YES` σε κωδικό εξόδου 2.
- [x] **Εξάλειψη κωδικών ονομάτων κατά Κανόνα 9** -- τα εναπομείναντα `PYTHIA` / `CHIRON` αντικαταστάθηκαν με λειτουργική ορολογία ISO/IEC 25010 (Γνωσιακός Μεταγλωττιστής Ερωτημάτων / Αναλυτής Γράφου Αναφορών) σε όλο τον Οδηγό Αναπροσανατολισμού Έρευνας και το μενού TUI «Configuration & Profiles».
- [x] **Προαγωγή Οδηγού Ρύθμισης Έρευνας στο TUI** -- το `profile_settings_menu()` προάγει τον οδηγό στην επιλογή 1 («Full Onboarding & Reconfiguration») και αναριθμεί τις υπόλοιπες καταχωρίσεις, επιτρέποντας την επανεκτέλεση ανά πάσα στιγμή για επαναρύθμιση πεδίου, 16 ερωτημάτων, κριτηρίων, παραθύρου αναζήτησης και στρατηγικής εκτέλεσης ΤΝ.
- [x] **Συγχρονισμός έκδοσης** -- 6 αρχεία κώδικα + docker-compose.yml + CITATION.cff + μεταδεδομένα tray/visualizer/evaluation-history/wizard + 19 κανονικά έγγραφα σε v5.12.3 (2026-09-27).
- [x] **Πύλες επαλήθευσης** -- compileall, test_system_integrity, test_talos_version, test_research_setup_wizard (28 δοκιμές), verify_dependency_map --ci (έξοδος 0), bash -n, σάρωση ακεραιότητας UTF-8 (μηδέν glyphs U+FFFD).

## Φάση 55: Πλέγμα Ταυτόχρονης Κατάποσης & Ενσωμάτωση Έρευνας Πολλαπλών Προφίλ (v5.12.4)

### Κατάσταση: ΟΛΟΚΛΗΡΩΜΕΝΗ (2026-09-28)

- [x] **Επιλογή Προφίλ-Στόχου Βήματος 0** -- το `research_setup_wizard.py:_step0_profile_selection()` θέτει πύλη στον οδηγό με τριπλή επιλογή (επαναρύθμιση ενεργού προφίλ, εναλλαγή σε υπάρχον προφίλ ή δημιουργία φρέσκου απομονωμένου χώρου `_profiles/<name>/`)· η κεφαλίδα αποδίδει πλέον `Target Profile: [<target_profile>]` και ο κανονικός δείκτης `_profiles/active_profile.txt` καθοδηγεί τον `get_active_profile_db_path()`.
- [x] **Πλέγμα Ταυτόχρονης Ακαδημαϊκής Κατάποσης** -- το `daily_search.py` αντικαθιστά τον σειριακό βρόχο 16 πηγών με `ThreadPoolExecutor(max_workers=min(16, len(enabled_scrapers)))`· κάθε πάροχος εκτελείται στο `_harvest_single_source()` με αυστηρή απομόνωση εξαιρέσεων ανά νήμα ώστε ένα timeout σε Science.gov ή OSTI να μην ματαιώνει ποτέ την εκτέλεση.
- [x] **Τηλεμετρία ταυτοχρονισμού Rich Live** -- ζωντανός πίνακας παρακολουθεί WAITING / HARVESTING / COMPLETED / FAILED ανά πηγή με στήλες ευρεθέντων άρθρων και χρόνου, κλείνοντας με πίνακα σύνοψης συνολικού χρόνου / ακατέργαστων / αποδιπλασιασμένων.
- [x] **Αποδιπλασιασμός DOI + κατακερματισμού κανονικοποιημένου τίτλου** -- το `_deduplicate_papers()` καταρρέει τα διπλότυπα μεταξύ πηγών στο κύριο νήμα πριν την εισαγωγή στη βάση.
- [x] **Μείωση καθυστέρησης κατάποσης** -- από ~35-45s σε ~3-4s.
- [x] **Οδηγοί Ρύθμισης Περιβάλλοντος** -- τα `docs/ENVIRONMENT_SETUP_GUIDE.md` / `_GR.md` τεκμηριώθηκαν ως οι επίσημες αναφορές ρύθμισης.
- [x] **Συγχρονισμός έκδοσης** -- 6 αρχεία κώδικα + docker-compose.yml + CITATION.cff + μεταδεδομένα tray/visualizer/evaluation-history/wizard + 19 κανονικά έγγραφα σε v5.12.4 (2026-09-28).
- [x] **Πύλες επαλήθευσης** -- compileall, test_system_integrity, test_talos_version, test_research_setup_wizard (39 δοκιμές), verify_dependency_map --ci (έξοδος 0), bash -n, σάρωση ακεραιότητας UTF-8 (μηδέν glyphs U+FFFD).

## Φάση 57: Αναλυτής Διαγνωστικών Συστήματος & Μηχανή Λειτουργικής Ακεραιότητας (v5.13.1)

### Κατάσταση: ΟΛΟΚΛΗΡΩΜΕΝΗ (2026-09-28)

- [x] **Αναλυτής Διαγνωστικών Συστήματος** -- το `src/utils/system_diagnostics.py` παρέχει την κλάση `SystemDiagnosticsEngine` (ISO/IEC 25010 Διαγνωσιμότητα) με προκαταρκτικό έλεγχο υγείας 8 σημείων (περιβάλλον Python, ακεραιότητα SQLite/WAL, τοπικός χρόνος εκτέλεσης AI, διαθεσιμότητα θυρών, δικαιώματα συστήματος αρχείων, δομή .env, κατάσταση δαίμονα, προαιρετικά σημεία δικτύου) και αναφορά υγείας Rich `box.ROUNDED` με καθοδήγηση αντιμετώπισης μιας γραμμής.
- [x] **Ταχεία αποστολή CLI** -- `--diagnostics` (κανονική) και `--doctor`/`-d` (ψευδώνυμο) εκτελούν τον αναλυτή headless και τερματίζουν με κωδικό 0.
- [x] **Ενσωμάτωση TUI Ομάδας 6** -- το `system_health_menu()` αποκτά Επιλογή 1 "System Health & Diagnostic Analyzer"; οι επιλογές αναριθμούνται 1-8 σε 2-9.
- [x] **Συγχρονισμός έκδοσης** -- 6 αρχεία κώδικα + docker-compose.yml + CITATION.cff + μεταδεδομένα tray/visualizer/evaluation-history/wizard + 19 κανονικά έγγραφα σε v5.13.1 (2026-09-28).
- [x] **Πύλες επαλήθευσης πέρασαν** -- compileall, test_system_integrity, test_talos_version, εκτελέσεις CLI --diagnostics/--doctor, verify_dependency_map --ci (κωδικός 0), bash -n, σάρωση ακεραιότητας UTF-8 (μηδέν γλύφοι U+FFFD).

## Φάση 56: Μηχανή Ταυτόχρονης Πολυνηματικής Εκτέλεσης Πλήρους Στοίβας & Συλλέκτης Υψηλής Διαμεταγωγής (v5.13.0)

### Κατάσταση: ΟΛΟΚΛΗΡΩΜΕΝΗ (2026-09-28)

- [x] **Σύνολο Ταυτόχρονης Γνωσιακής Αξιολόγησης** -- τα `ai_manager.py:batch_evaluate_papers()` / `_resolve_eval_concurrency()` βαθμολογούν μια ομάδα άρθρων ταυτόχρονα· το Cloud Mesh εκτελεί 8 εργάτες ενώ η τοπική GPU εκτελεί 2 εργάτες πίσω από φύλακα VRAM `threading.Semaphore(2)`, διατηρώντας το δομημένο σχήμα αξιολόγησης JSON.
- [x] **Πλέγμα Ταυτόχρονης Ιστορικής Κατάποσης** -- το `historic_search.py` υιοθετεί το μοντέλο `ThreadPoolExecutor(max_workers=min(16, len(enabled_sources)))` με ανακατεύθυνση stdout ανά νήμα `_harvest_single_source()`, συγκέντρωση `as_completed()` και αποδιπλασιασμό DOI + SHA-1 κατακερματισμού τίτλου.
- [x] **Τηλεμετρία ταυτοχρονισμού Rich Live** -- η ιστορική συγκομιδή αποκτά ζωντανό πίνακα WAITING / HARVESTING / COMPLETED / FAILED και πίνακα Σύνοψης Ιστορικής Κατάποσης.
- [x] **Ταυτόχρονη επαναξιολόγηση βάσης δεδομένων** -- το `reevaluate_database.py:_apply_evaluation_batch()` οδηγεί το ταυτόχρονο σύνολο και αποθηκεύει αποτελέσματα με ομαδικές καταγραφές SQLite WAL.
- [x] **Κέρδη καθυστέρησης/διαμεταγωγής** -- μείωση καθυστέρησης βιβλιογραφικής κατάποσης κατά 8x-10x και επιτάχυνση βαθμολόγησης LLM κατά 5x-8x.
- [x] **Συγχρονισμός έκδοσης** -- 6 αρχεία κώδικα + docker-compose.yml + CITATION.cff + μεταδεδομένα tray/visualizer/evaluation-history/wizard + 19 κανονικά έγγραφα σε v5.13.0 (2026-09-28).
- [x] **Πύλες επαλήθευσης** -- compileall, test_system_integrity, test_talos_version, test_research_setup_wizard, verify_dependency_map --ci (έξοδος 0), bash -n, σάρωση ακεραιότητας UTF-8 (μηδέν glyphs U+FFFD).



---

> **Project TALOS** -- Από Αθροιστή σε Αυτόνομο Αρχιτέκτονα Έρευνας.
> Δημιουργήθηκε στην Καλαμάτα, Ελλάδα.
> (C) 2026 Christos Smarlamakis. Με επιφύλαξη παντός δικαιώματος.
