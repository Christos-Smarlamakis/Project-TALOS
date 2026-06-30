# Ημερολόγιο Αλλαγών (Changelog) - Project TALOS

Αυτό το αρχείο καταγράφει όλες τις σημαντικές αλλαγές στο Project TALOS. Το project ακολουθεί τις αρχές του [Semantic Versioning](https://semver.org/).


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