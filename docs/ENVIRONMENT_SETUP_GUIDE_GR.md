# Οδηγός Ρύθμισης Περιβάλλοντος & Διαπιστευτηρίων

**Project TALOS v5.13.1 -- Κανονική Ελληνική Αναφορά**

> **Σκοπός:** Το παρόν έγγραφο αποτελεί την αυθεντική, ενιαία αναφορά για τη
> διαμόρφωση της επιφάνειας περιβάλλοντος του TALOS. Καλύπτει τον αυστηρό
> διαχωρισμό μεταξύ `config/settings.py`, `.env` και `config.json`, το τοπικό
> σύστημα εκτέλεσης Ollama, το Καθολικό Πλέγμα Cloud AI, τα API εισαγωγής
> ακαδημαϊκής βιβλιογραφίας και τον πίνακα στρατηγικών δικτύου και θυρών.
>
> **Κοινό:** Επικεφαλής Αρχιτέκτονας Συστημάτων, Επικεφαλής DevOps και
> Ακαδημαϊκός Επιστημονικός Υπεύθυνος.
>
> **Τελευταία ενημέρωση:** 2026-09-28

---

## Ενότητα 1: Ασφάλεια & Αρχιτεκτονική (Ο Διαχωρισμός .env και settings.py)

Το TALOS επιβάλλει έναν αυστηρό τριμερή διαχωρισμό αρμοδιοτήτων διαμόρφωσης,
ώστε τα μυστικά να μην εισέρχονται ποτέ στον πηγαίο κώδικα και η τοπική
(απομονωμένη) λειτουργία να μην εξαρτάται ποτέ από διαπιστευτήριο.

| Επιφάνεια | Ρόλος | Επιτρέπονται μυστικά; | Δεσμεύεται στο Git; |
|-----------|-------|------------------------|---------------------|
| `config/settings.py` | Κανονικό σχήμα και προεπιλογές. Διαβάζει `os.getenv(KEY, DEFAULT)`. | **Όχι** | Ναι |
| `.env` | Μυστικά εκτέλεσης και παρακάμψεις χειριστή (κλειδιά API, tokens, webhooks). | **Ναι** | **Όχι** (gitignored) |
| `config.json` | Μη-μυστική συμπεριφορική διαμόρφωση (ερωτήματα, prompts, όρια ρυθμού, `mailto`, `auto_start_local_llm`). | **Όχι** | Ναι |
| `example.env` | Σχολιασμένο πρότυπο χωρίς μυστικά για την ενσωμάτωση νέων χρηστών. | **Όχι** | Ναι |

**Αρχές μηδενικής διαρροής στο Git:**

1. Κάθε μυστικό διαβάζεται κατά την εκτέλεση μέσω `os.getenv(...)` με
   προεπιλογή κενής συμβολοσειράς. Ένα κλειδί που απουσιάζει υποβαθμίζει
   ομαλά τη λειτουργία (ο πάροχος σταθμεύει σε `STANDBY_NO_KEY`) και δεν
   προκαλεί ποτέ κατάρρευση.
2. Το `.env` εξαιρείται από τον έλεγχο εκδόσεων. Το `example.env` δεν περιέχει
   **κανένα** πραγματικό διαπιστευτήριο -- μόνο κλειδιά, κενές τιμές και
   διευθύνσεις εγγραφής.
3. Τα κλειδιά API **απαγορεύεται** να δεσμεύονται στο Git και **απαγορεύεται**
   να σκληροκωδικοποιούνται στο `settings.py` ή στο `config.json`. Εάν ένα
   κλειδί εκτεθεί ποτέ, ανανεώστε το αμέσως στην κονσόλα του παρόχου.
4. Σε περιβάλλοντα CI/CD και containers, εισάγετε μυστικά μέσω μεταβλητών
   περιβάλλοντος ή διαχειριστή μυστικών. Η εικόνα Docker είναι
   αυτοτελής και δεν περιέχει κλειδιά.
5. **Σύμβαση τιμών χωρίς εισαγωγικά:** το `load_dotenv` δεν αφαιρεί τα
   εισαγωγικά. Γράψτε `TALOS_NETWORK_STRATEGY=local_first` και **όχι**
   `"local_first"`. Ένα περιττό ζεύγος εισαγωγικών γίνεται μέρος της τιμής
   και καταστρέφει τους ελέγχους ισότητας.

---

## Ενότητα 2: Ρύθμιση Τοπικού Χρόνου Εκτέλεσης AI (Μηδέν Κλειδιά, Μηδέν Διαδίκτυο)

Η τοπική βαθμίδα είναι η **πρωταρχική και προεπιλεγμένη** επιφάνεια εξαγωγής
συμπεράσματος. Απαιτεί **μηδέν κλειδιά API** και **μηδέν πρόσβαση στο
διαδίκτυο** όταν ισχύει `TALOS_USE_LOCAL=1`.

| Τερματικό | Θύρα | Ρόλος | Κλειδί env | Προεπιλεγμένο μοντέλο |
|-----------|------|-------|------------|------------------------|
| Ollama (GPU) | `11434` | Βαριά βαθμίδα συλλογισμού | `OLLAMA_BASE_URL` | `qwen2.5:14b` (`HEAVY_REASONING_MODEL`) |
| CPU Edge | `11435` | Γρήγορη βαθμίδα προδιαλογής | `FAST_EDGE_BASE_URL` | `fermionresearch/Neutrino-8B` (`FAST_EDGE_MODEL`) |

**Επαληθευμένα τοπικά μοντέλα:**

- `llama3.1:8b` -- προτιμώμενο μοντέλο συνομιλίας GPU (`LOCAL_GPU_MODEL`, `LOCAL_MODEL_NAME`). Μηδενική επιβάρυνση συλλογισμού, γρήγορο και ντετερμινιστικό.
- `qwen2.5:14b` -- βαρύ μοντέλο συλλογισμού για βαθιά ανάλυση και σύνθεση.
- `gemma3:12b` -- εναλλακτική ονομασία τοπικού μοντέλου (ιστορική προεπιλογή).
- `nomic-embed-text` -- μοντέλο ενσωμάτωσης για διανύσματα σημασιολογικής αναζήτησης (`LOCAL_EMBEDDING_MODEL`).

**Προμήθεια (εφάπαξ):**

```bash
ollama pull llama3.1:8b
ollama pull qwen2.5:14b
ollama pull nomic-embed-text
```

**Σχετικές μεταβλητές περιβάλλοντος:**

| Κλειδί env | Προεπιλογή | Σκοπός |
|------------|------------|--------|
| `LOCAL_GPU_MODEL` | `llama3.1:8b` | Τοπικό μοντέλο συνομιλίας GPU |
| `LOCAL_MODEL_NAME` | `gemma3:12b` | Ψευδώνυμο παλαιού τύπου που καταναλώνει το `ai_manager` |
| `LOCAL_MODEL_BASE_URL` | `http://127.0.0.1:11434/v1` | Τοπικό τερματικό συμβατό με OpenAI (παράγεται από `OLLAMA_BASE_URL` + `/v1`) |
| `HEAVY_REASONING_MODEL` | `qwen2.5:14b` | Μοντέλο βαριάς βαθμίδας |
| `FAST_EDGE_MODEL` | `fermionresearch/Neutrino-8B` | Γρήγορο μοντέλο CPU edge |
| `FAST_EDGE_BASE_URL` | `http://127.0.0.1:11435/v1` | Τερματικό CPU edge |
| `OLLAMA_BASE_URL` | `http://127.0.0.1:11434` | Τυπικό τερματικό Ollama (χωρίς τελικό `/v1`) |
| `LOCAL_EMBEDDING_MODEL` | `nomic-embed-text` | Μοντέλο ενσωμάτωσης σημασιολογικής αναζήτησης |
| `TALOS_USE_LOCAL` | `1` | Διακόπτης απομονωμένης λειτουργίας (το `1` απενεργοποιεί το cloud) |
| `TALOS_DEFAULT_TIER` | `fast` | Προεπιλεγμένη βαθμίδα αιτημάτων (`fast` / `heavy`) |

**Αυτόματη εκκίνηση του τοπικού χρόνου εκτέλεσης:** η σημαία
`auto_start_local_llm` βρίσκεται στο `config.json` (όχι στο `.env`). Όταν το
runtime είναι εκτός σύνδεσης, ο `AIManager` ελέγχει το
`http://127.0.0.1:11434/api/tags` και (όταν το `auto_start_local_llm` είναι
`true`) εκκινεί το `ollama serve` αποσπασμένα πριν υποβαθμίσει ομαλά.

## Ενότητα 3: Καθολικό Πλέγμα Cloud AI

Η βαθμίδα cloud παρέχει προαιρετικό πλεονασμό και εφεδρεία (failover). **Δεν
απαιτείται ποτέ** για την τοπική λειτουργία. Το TALOS απαριθμεί τους παρόχους
που δηλώνονται στο `OPENAI_COMPATIBLE_REGISTRY` (`src/core/ai_manager.py`) και
σταθμεύει κάθε πάροχο του οποίου το κλειδί απουσιάζει. Η κανονική λίστα
διάταξης είναι η `TALOS_CLOUD_PROVIDERS`.

Εννέα πάροχοι είναι ενσύρματοι σε αυτή την έκδοση: **Gemini, DeepSeek,
HuggingFace, NVIDIA NIM, Groq, Cerebras, GitHub Models, Mistral και OpenRouter**.

| Πάροχος | Κλειδί env (μυστικό) | Κλειδί μοντέλου | Βασική διεύθυνση | Πηγή κλειδιού |
|---------|----------------------|-----------------|------------------|---------------|
| Google Gemini | `GEMINI_API_KEY` | `GEMINI_FLASH_MODEL` / `GEMINI_PRO_MODEL` | (Google GenAI SDK) | https://aistudio.google.com/apikey -- Δωρεάν βαθμίδα |
| DeepSeek | `DEEPSEEK_API_KEY` | `DEEPSEEK_MODEL_CHAT` | `https://api.deepseek.com/v1` | https://platform.deepseek.com -- οικονομία υψηλού συλλογισμού |
| HuggingFace | `HF_TOKEN` | `HF_MODEL_NAME` | `https://router.huggingface.co/hf-inference/v1` | https://huggingface.co/settings/tokens |
| NVIDIA NIM | `NVIDIA_API_KEY` | `NVIDIA_DEFAULT_MODEL` | `https://integrate.api.nvidia.com/v1` | https://build.nvidia.com |
| Groq | `GROQ_API_KEY` | `GROQ_DEFAULT_MODEL` | `https://api.groq.com/openai/v1` | https://console.groq.com/keys |
| Cerebras | `CEREBRAS_API_KEY` | `CEREBRAS_DEFAULT_MODEL` | `https://api.cerebras.ai/v1` | https://cloud.cerebras.ai |
| GitHub Models | `GITHUB_TOKEN` | `GITHUB_MODELS_DEFAULT_MODEL` | `https://models.inference.ai.azure.com` | https://github.com/settings/tokens (PAT) |
| Mistral | `MISTRAL_API_KEY` | `MISTRAL_DEFAULT_MODEL` | `https://api.mistral.ai/v1` | https://console.mistral.ai |
| OpenRouter | `OPENROUTER_API_KEY` | `OPENROUTER_DEFAULT_MODEL` | `https://openrouter.ai/api/v1` | https://openrouter.ai/keys |

**Επιλογή παρόχου:** το `TALOS_CLOUD_PROVIDER` (προεπιλογή `gemini`) επιλέγει
τον κύριο πάροχο cloud· οι υπόλοιποι πάροχοι λειτουργούν ως αλυσίδα εφεδρείας.
Το Gemini χρησιμοποιεί το Google Generative AI SDK· όλοι οι υπόλοιποι πάροχοι
χρησιμοποιούν την ενιαία διαδρομή συμβατή με OpenAI.

**Σημείωση μελλοντικής συμβατότητας:** τα OpenAI και Anthropic περιλαμβάνονται
στον κανονικό χάρτη πορείας του cloud mesh αλλά **δεν είναι ακόμη ενσύρματα**
ως πρώτης τάξεως πάροχοι σε αυτή την έκδοση. Καμία μεταβλητή περιβάλλοντος
`OPENAI_API_KEY` ή `ANTHROPIC_API_KEY` δεν καταναλώνεται από τον τρέχοντα κώδικα.

## Ενότητα 4: API Εισαγωγής Ακαδημαϊκής Βιβλιογραφίας

Το TALOS εισάγει δεδομένα από δεκαέξι πράκτορες πηγών
(`src/ingestion/*_source.py`). Οι πηγές κατηγοριοποιούνται βάσει της
απαίτησης διαπιστευτηρίου.

### Κατηγορία A -- Ανοιχτά API Μηδενικού Κλειδιού

Αυτές οι πηγές δεν απαιτούν **κανένα κλειδί API**. Ορισμένες χρησιμοποιούν το
πεδίο `mailto` από το `config.json` για ένταξη στην «ευγενική δεξαμενή»
(polite pool, συνιστάται, όχι υποχρεωτικό).

| Πηγή | Μονάδα | Σημειώσεις |
|------|--------|------------|
| arXiv | `arxiv_source.py` | Ανοιχτό API arXiv, χωρίς κλειδί |
| OpenAlex | `openalex_source.py` | Χρησιμοποιεί το `mailto` του `config.json` |
| DBLP | `dblp_source.py` | Ανοιχτό βιβλιογραφικό API |
| PubMed | `pubmed_source.py` | NCBI E-utilities· χρησιμοποιεί `mailto` |
| Science.gov | `scigov_source.py` | Ομοσπονδιακή αναζήτηση, χωρίς κλειδί |
| OSTI | `osti_source.py` | Γραφείο Επιστημονικών και Τεχνικών Πληροφοριών του DOE |
| PLOS | `plos_source.py` | PLOS Search API, χωρίς κλειδί |
| OpenReview V2 | `openreview_source.py` | Προαιρετικά `OPENREVIEW_USERNAME` / `OPENREVIEW_PASSWORD` |
| OpenArchives (EADD) | `openarchives_source.py` | Ελληνικά ακαδημαϊκά αποθετήρια |
| Crossref | `crossref_source.py` | Χρησιμοποιεί το `mailto` του `config.json` |
| OpenAIRE | `openaire_source.py` | Προαιρετικό `OPENAIRE_TOKEN` |

### Κατηγορία B -- Δωρεάν Εγγραφή Προγραμματιστή

| Πάροχος | Κλειδί env | Εγγραφή | Σημειώσεις ορίου ρυθμού |
|---------|------------|---------|--------------------------|
| Semantic Scholar | `SEMANTIC_SCHOLAR_API_KEY` | https://www.semanticscholar.org/product/api#api-key-form | Υψηλότερη απόδοση από την ανώνυμη (100 αιτήματα / 5 λεπτά χωρίς έλεγχο ταυτότητας) |
| CORE | `CORE_API_KEY` | https://core.ac.uk/services/api | Πιστοποιημένη πρόσβαση σε μεταδεδομένα πλήρους κειμένου |
| Crossref | `mailto` στο `config.json` | https://www.crossref.org | Το email `mailto` εντάσσει στην ευγενική δεξαμενή |
| Springer Nature | `SPRINGER_API_KEY` | https://dev.springernature.com | Δωρεάν βαθμίδα προγραμματιστή |

### Κατηγορία C -- Ιδρυματική / Συνδρομητική

| Πάροχος | Κλειδί env | Καθοδήγηση |
|---------|------------|------------|
| IEEE Xplore | `IEEE_API_KEY` | https://developer.ieee.org -- ιδρυματικό ή προγραμματιστικό κλειδί |
| Elsevier Scopus | `ELSEVIER_API_KEY` **και** `ELSEVIER_INST_TOKEN` | https://dev.elsevier.com -- απόκτηση μέσω ιδρυματικού διαμεσολαβητή (π.χ. HEAL-Link για τα ελληνικά πανεπιστήμια)· το insttoken απαιτείται μαζί με το κλειδί API |

**Σημείωση ονοματοδοσίας:** τα διαπιστευτήρια του Scopus εκτίθενται ως
`ELSEVIER_API_KEY` / `ELSEVIER_INST_TOKEN` (δεν υπάρχει `SCOPUS_API_KEY` /
`SCOPUS_INST_TOKEN` σε αυτή την έκδοση). Το Crossref χρησιμοποιεί το πεδίο
`mailto` του `config.json` (δεν υπάρχει μεταβλητή περιβάλλοντος
`CROSSREF_MAILTO`).

**Βοηθητικά κλειδιά ενσωμάτωσης:**

| Κλειδί | Σκοπός |
|--------|--------|
| `ORCID_CLIENT_ID` / `ORCID_CLIENT_SECRET` | Ταυτοποίηση συγγραφέα |
| `ZOTERO_API_KEY` / `ZOTERO_USER_ID` | Γέφυρα διαχειριστή αναφορών Zotero |
| `OPENAIRE_TOKEN` | Πιστοποιημένες κλήσεις OpenAIRE |
| `UNPAYWALL_EMAIL` / `MAILTO` | Εντοπισμός PDF ανοιχτής πρόσβασης Unpaywall (εφεδρικά στο `mailto` του `config.json`) |

## Ενότητα 5: Στρατηγικές Δικτύου & Αντιστοιχίσεις Θυρών

### Ο Δισδιάστατος Πίνακας Εκτέλεσης

Το TALOS v5.9.4 αντικατέστησε την παλαιά `TALOS_EXECUTION_MODE` με έναν πίνακα
δύο αξόνων: `TALOS_NETWORK_STRATEGY` (πού δρομολογείται η εξαγωγή
συμπεράσματος) και `TALOS_HARDWARE_STRATEGY` (ποια τοπική συσκευή
χρησιμοποιείται).

**Τιμές `TALOS_NETWORK_STRATEGY`:**

| Τιμή | Συμπεριφορά |
|------|-------------|
| `strict_local` | Απομονωμένη. Όλη η εξαγωγή συμπεράσματος μόνο μέσω τοπικών βαθμίδων· το cloud δεν καλείται ποτέ. |
| `local_first` | Τοπικές βαθμίδες πρωταρχικές· αυτόματη εφεδρεία cloud σε σφάλμα σύνδεσης. |
| `cloud_first` | Cloud πρωταρχικό· αυτόματη εφεδρεία τοπικά σε σφάλμα ταυτοποίησης / ορίου ρυθμού / χρονικού ορίου. |
| `strict_cloud` | Αμιγώς cloud· οι τοπικές βαθμίδες δεν καλούνται ποτέ. Απαιτεί έγκυρα κλειδιά cloud. |
| `auto_dynamic` | Αυτόνομος Πίνακας Εκτέλεσης (v5.10.14): επιλύεται κατά την εκτέλεση σε `strict_local` / `local_first` / `cloud_first` βάσει συνδεσιμότητας, VRAM, τύπου εργασίας και συναίνεσης Privacy Guardrail. Το `strict_local` δεν παρακάμπτεται ποτέ. |

**Τιμές `TALOS_HARDWARE_STRATEGY`:** `cpu_only` (όλα τα τοπικά αιτήματα στη
θύρα `11435`), `gpu_only` (όλα τα τοπικά αιτήματα στη θύρα `11434`),
`cpu_gpu_split` (προεπιλογή: γρήγορα σε CPU, βαριά σε GPU).

### Γιατί το `strict_cloud` διατηρεί τη VRAM της GPU

Στο `strict_cloud`, οι τοπικές βαθμίδες Ollama δεν αρχικοποιούνται ποτέ για
εξαγωγή συμπεράσματος. Αυτό αφήνει **το 100% της VRAM της GPU** ελεύθερο για
εξωτερικούς φόρτους βαθιάς μάθησης που εκτελούνται παράλληλα με το TALOS --
για παράδειγμα Χωρο-Χρονικά Γραφικά Νευρωνικά Δίκτυα (ST-GNNs) και Ετερογενή
Πολυ-Πρακτορική Βαθιά Ενισχυτική Μάθηση (HMADRL). Η βαθμίδα CPU Edge παραμένει
επίσης ανενεργή, οπότε ο επιταχυντής του υπολογιστή δεσμεύεται πλήρως για τις
εργασίες PyTorch/CUDA του ερευνητή.

### Χάρτης θυρών

| Θύρα | Υπηρεσία |
|------|----------|
| `8001` | Backend FastAPI του TALOS και επιφάνεια API του TUI |
| `8000` | Δίαυλος συμβάντων SYNAPSE (αδελφή μικροϋπηρεσία) |
| `11434` | Ollama GPU (βαριά βαθμίδα συλλογισμού) |
| `11435` | Ollama CPU Edge (γρήγορη βαθμίδα) |
| `8002` | Γέφυρα OPTICA (μικροϋπηρεσία οπτικοποίησης) |
| `5002` | Παλαιό τερματικό κατάστασης `talos_service_api` |

### Μεταβλητές συστήματος & οικοσυστήματος

| Κλειδί env | Προεπιλογή | Σκοπός |
|------------|------------|--------|
| `SYNAPSE_BUS_URL` | `http://localhost:8000/api/v1/events` | Εξερχόμενα συμβάντα SYNAPSE |
| `OPTICA_API_BASE` | `http://127.0.0.1:8002/api/v1` | Γέφυρα οπτικοποίησης OPTICA |
| `TALOS_API_PORT` | `8001` | Θύρα FastAPI του TALOS |
| `TALOS_ALLOW_CLOUD_FALLBACK` | `0` | Ρητή πύλη εφεδρείας cloud |

---

## Παράρτημα: Συγκεντρωτική Αναφορά Μεταβλητών

Δείτε το `example.env` για το πλήρως σχολιασμένο, χωρίς εισαγωγικά πρότυπο
παραγωγής. Οι κανονικές προεπιλογές ορίζονται στο `config/settings.py`· οι
συμπεριφορικές (μη-μυστικές) ρυθμίσεις όπως `mailto`, `provider_limits` και
`auto_start_local_llm` βρίσκονται στο `config.json`.



