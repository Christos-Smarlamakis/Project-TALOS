# Project TALOS (v5.15.2)

### Tactical Agentic Literature Orchestration System

> **An autonomous research intelligence platform: declarative Stanford DSPy PRISMA-ScR synthesis, a 3-agent peer-review swarm with automated Cohen's and Fleiss' Kappa, an 18-source concurrent ingestion mesh, a Universal Scientific Search Hub with neural vector discovery, and a 5-tier AI execution matrix -- fully air-gapped and local-first.**

[![IEEE Computer Society](https://img.shields.io/badge/IEEE_Computer_Society-WEIGD_Fund_Recipient_2026-006699?style=flat-square&logo=ieee&logoColor=white)](https://www.computer.org/volunteering/awards/scholarships/weigd-student-fund/weigd-recipients#summer-2026)
[![Conference Paper](https://img.shields.io/badge/Conference_Paper-HOU_ICBE_2026-002B49?style=flat-square)](https://icbe-hou.eap.gr/)
[![System Integrity](https://img.shields.io/badge/System_Integrity-ISO%2FIEC_25010_Verified-005A9C?style=flat-square)](docs/SYSTEM_CAPABILITIES_MASTER.md)
[![License](https://img.shields.io/badge/License-AGPLv3-red?style=flat-square)](LICENSE)
[![DOI](https://zenodo.org/badge/1191928488.svg)](https://doi.org/10.5281/zenodo.19224912)
[![Docker](https://img.shields.io/badge/Docker-Supported-2496ED?style=flat-square&logo=docker)](docs/DOCKER.md)
![Version](https://img.shields.io/badge/Version-v5.15.2-006699?style=flat-square)
![Python](https://img.shields.io/badge/Python-3.11%2B-blue?style=flat-square)
[![FastAPI](https://img.shields.io/badge/FastAPI-23_REST_Endpoints-009688?style=flat-square&logo=fastapi&logoColor=white)](src/api/main_api.py)
[![Architecture](https://img.shields.io/badge/Architecture-100%25_Air--Gapped_%26_Local--First-111827?style=flat-square)](config/settings.py)
[![System Capabilities](https://img.shields.io/badge/System_Capabilities-006699?style=flat-square&logo=html5&logoColor=white)](https://christos-smarlamakis.github.io/Project-TALOS/)

---

## 1. Executive Overview & Scientific Scope

Project TALOS is a universal, domain-agnostic Autonomous Research Intelligence
Platform. It accelerates Systematic Literature Reviews (SLR) and PRISMA-ScR
scoping reviews across any scientific discipline -- from Robotics and Applied
AI to Biomedicine and Quantum Systems -- by discovering, evaluating,
synthesizing, and visualizing scientific knowledge through an agentic,
human-in-the-loop workflow.

### A Universal Platform

TALOS is not bound to any single research topic. It operates entirely
air-gapped and local-first: a local Ollama runtime (`llama3.1:8b`,
`nomic-embed-text`) supplies inference and embeddings with zero cloud
dependency, zero telemetry, and full offline PRISMA execution. The platform is
equally at home reviewing the literature of autonomous systems, complex
cyber-physical networks, clinical research, or fundamental physics.

### Illustrative Benchmark Case Study

Autonomous systems and complex cyber-physical networks -- for example,
cooperative mission planning and task allocation for autonomous Unmanned
Aerial Vehicle (UAV) swarms, formalised through Heterogeneous Multi-Agent Deep
Reinforcement Learning (HMADRL), Spatio-Temporal Graph Neural Networks
(ST-GNNs), and Decentralized Partially Observable Markov Decision Processes
(Dec-POMDPs) -- serve as an illustrative benchmark workload that demonstrates
the platform's throughput, relevance filtering, and reproducibility guarantees.
The platform itself remains fully domain-agnostic.

### The Problem

The exponential growth of scientific publication makes manual monitoring of
interdisciplinary fields -- such as autonomous systems -- practically
impossible, and keyword-only retrieval misses semantically related work.

### The Solution

TALOS acts as an autonomous "Research Architect": it filters noise, surfaces
strategic knowledge, and produces reproducible, publication-grade artifacts.

---

## 2. Core Architectural Pillars

### Pillar A -- Declarative Stanford DSPy PRISMA-ScR Pipeline (`src/prisma/`)

A four-phase, PRISMA 2020-compliant scoping-review synthesis engine built on
typed declarative signatures that mirror the Stanford DSPy `dspy.Signature`
paradigm, without any hard `dspy-ai` dependency:

- **Typed signatures** (`dspy_signatures.py`): `PrismaPlanSignature`,
  `PrismaScreeningSignature`, `PrismaEligibilitySignature`, and
  `PrismaSynthesisSignature`, each with a robust `extract_json_payload()`
  recovery helper.
- **Chain-of-Thought PlanEval screening** (`dspy_modules.py`): `PrismaPlanner`,
  `PrismaEvaluator` (structured Chain-of-Thought title/abstract screening),
  `PrismaEligibilityJudge`, and `PrismaExecutor` (end-to-end four-phase
  orchestration with live record counters).
- **Dynamic PRISMA 2020 Mermaid flowchart** (`mermaid_generator.py`):
  `generate_prisma_mermaid()` emits a standard-compliant flowchart.
- **LaTeX scoping-review synthesizer** (`scoping_review_synthesizer.py`):
  `synthesize_scoping_review()` and `synthesize_scoping_review_latex()`.

### Pillar B -- Multi-Agent Peer-Review Swarm & Consensus Engine

A specialised 3-agent review swarm (`src/prisma/swarm_evaluators.py`) that
replaces the single-screener decision with three personas:

- **Algorithmic Reviewer** -- scrutinises method correctness.
- **Empirical Rigor Reviewer** -- audits experimental validity.
- **Operational / NATO Reviewer** -- assesses real-world deployability under
  mission constraints.

The swarm computes automated inter-rater agreement via both Cohen's Kappa and
its Fleiss multi-rater generalisation ($\kappa$), and a Chain-of-Thought
`SwarmConsensusArbiter` adjudicates split verdicts into a single consensus
decision.

### Pillar C -- Full-Stack Concurrent Ingestion & Evaluation Mesh

A `ThreadPoolExecutor(max_workers=18)` harvests all 18 official academic APIs
simultaneously, reducing end-to-end literature-harvest latency from
approximately 45 seconds to approximately 3 seconds. A dynamic, VRAM-safe batch
evaluation pool (8 cloud workers / 2 VRAM-guarded local workers behind a bounded
semaphore) scores the corpus without exceeding the 80% training / 2GB inference
headroom mandate.

### Pillar D -- Universal Scientific Search Hub

The Group 2 TUI and the CLI expose six coordinated discovery modes under a
single Universal Search Hub:

1. **Daily Concurrent Ingestion** -- 18 APIs harvested in parallel.
2. **Historical Deep Window Search** -- configurable days-window archive crawl.
3. **Autonomous Citation Snowballing** -- backward/forward citation-graph
   traversal (`src/search/citation_snowballing.py`).
4. **Neural Vector Semantic Search** -- local `nomic-embed-text` dense
   retrieval with cosine-similarity ranking (`src/search/neural_vector_search.py`).
5. **Reproducible Code-First Search** -- GitHub / PapersWithCode / benchmark
   linked discovery (`src/search/code_first_search.py`).
6. **PRISMA-ScR Declarative Synthesis** -- the four-phase scoping-review pipeline.

### Pillar E -- 18-Source Academic Data Acquisition Layer

The modular `src/ingestion/sources/` subpackage hosts a unified
`SOURCE_REGISTRY` across eighteen official academic APIs:

arXiv, IEEE Xplore, Elsevier Scopus, OpenAlex, Semantic Scholar, Springer Link,
DBLP, CORE, Crossref, OpenArchives (EADD), PubMed, Science.gov, OSTI, PLOS,
OpenReview, OpenAIRE, NASA NTRS, and HAL/Inria.

Each adapter emits the canonical `{doi, url, title, authors_str,
publication_year, abstract, source}` record, degrades gracefully when offline,
and honours exponential backoff on rate-limited endpoints.

### Pillar F -- Research Setup Wizard & 5-Tier AI Execution Matrix

The Research Setup Wizard (`src/utils/research_setup_wizard.py`) provides a
Step 0 multi-profile isolation gate that partitions every research topic into
its own `_profiles/<name>/` workspace, and synthesizes strict academic-English
inclusion and exclusion criteria. The 5-tier AI execution matrix
(`strict_local`, `local_first`, `cloud_first`, `strict_cloud` with VRAM
preservation, and `auto_dynamic`) routes inference across the CPU edge tier
(`Neutrino-8B`), the GPU heavy tier (`qwen2.5:14b`), and the optional Universal
Cloud Mesh.

### Pillar G -- ISO/IEC 25010 System Diagnostics Analyzer

An 8-point automated pre-flight healthcheck (`src/utils/system_diagnostics.py`)
-- Python environment, SQLite integrity and WAL state, local AI runtime, port
availability, filesystem permissions, environment credentials, daemon status,
and optional network endpoints -- rendered as a Rich health report with one-line
copy-paste remediation, exposed via `--diagnostics` / `--doctor`.

### Pillar H -- Automated BibTeX / LaTeX Scientific Exporter

A one-click exporter (`--export-bib`) writes the curated elite literature set to
`data/exports/talos_library.bib` with `AuthorYearTitleKeyword` cite keys, full
LaTeX reserved-character sanitization, and a Rich summary panel.

### Pillar I -- 3D WebGL Constellation Visualizer & Desktop Hub

A vendored Three.js knowledge-constellation visualizer renders the evaluated
corpus as a live 3D starfield, paired with a native Win32 close-to-tray desktop
hub and a glassmorphism telemetry HUD console (`src/utils/tray_icon.py`).

---

## 3. Installation & Zero-Friction Usage

### Method A -- Docker Compose

1. Install Docker Desktop.
2. Create `.env` from the fully annotated `example.env` template.
3. Start the headless FastAPI server (port 8001): `docker compose up -d --build`
4. Confirm health: `curl http://localhost:8001/api/v1/health`

### Method B -- Windows 1-Click Launcher

1. Configure `.env`.
2. Double-click `run_talos.bat`. The 24/7 daemon also exposes a Desktop Control
   Hub in the system tray.

### Method C -- Linux Zero-Touch Launcher

1. Configure `.env`.
2. Run `./run_talos.sh` for the POSIX dashboard with IEEE WEIGD telemetry.

### Method D -- CLI Fast-Dispatch Cheat Sheet

| Flag | Purpose |
|------|---------|
| `--wizard` | Launch the 4-step Research Setup Wizard. |
| `--daily` | Trigger the concurrent daily ingestion pipeline. |
| `--prisma [--swarm]` | Run the PRISMA-ScR pipeline (add `--swarm` for 3-agent consensus). |
| `--doctor` / `--diagnostics` | Run the 8-point ISO/IEC 25010 healthcheck. |
| `--export-bib [min_score]` | Export the curated library to BibTeX / LaTeX. |
| `--strategy [mode]` | Switch the AI execution strategy. |
| `--snowball [seed]` | Autonomous citation snowballing from a seed DOI / title / DB ID. |
| `--vector-search [query]` | Neural vector semantic search over `nomic-embed-text`. |
| `--code-search [query]` | Reproducible code-first search. |

---

## 4. Academic Citation

### IEEE Citation

C. Smarlamakis and E. Georgopoulos, "Project TALOS: Tactical Agentic Literature
Orchestration System," version 5.15.2, 2026. [Online]. Available:
https://github.com/Christos-Smarlamakis/Project-TALOS, doi: 10.5281/zenodo.19224912.

### BibTeX

```bibtex
@software{talos2026,
  author       = {Smarlamakis, Christos and Georgopoulos, Efstratios},
  title        = {Project TALOS: Tactical Agentic Literature Orchestration System},
  version      = {5.15.2},
  year         = {2026},
  doi          = {10.5281/zenodo.19224912},
  url          = {https://github.com/Christos-Smarlamakis/Project-TALOS},
  license      = {AGPL-3.0},
  note         = {IEEE Computer Society WEIGD Student Support Fund (2026) recipient}
}
```

---

## 5. License & Acknowledgements

Project TALOS is distributed under the **GNU Affero General Public License v3.0
(AGPLv3)**.

- **Academic / Research Use:** Free, provided derivative works remain open under
  AGPLv3.
- **Commercial Use:** A separate commercial license is required.

The Lead Architect and Author, **Christos Smarlamakis**, is an officially
selected recipient of the **IEEE Computer Society WEIGD Student Support Fund
(2026)**. The project gratefully acknowledges the IEEE Computer Society and the
enduring legacy of Dr. Grace C. N. Wei in supporting open-source,
democratised research tools for the global scientific community.

---

## Οδηγός Ελληνικής Έκδοσης

### Εισαγωγή & Όραμα TALOS

Το Project TALOS είναι μια καθολική, ανεξάρτητη από γνωστικό πεδίο, Αυτόνομη
Πλατφόρμα Ερευνητικής Νοημοσύνης. Επιταχύνει τις Συστηματικές Ανασκοπήσεις
Βιβλιογραφίας (SLR) και τις σκοπικές ανασκοπήσεις PRISMA-ScR σε κάθε
επιστημονικό πεδίο -- από τη Ρομποτική και την Εφαρμοσμένη Τεχνητή Νοημοσύνη
έως τη Βιοϊατρική και τα Κβαντικά Συστήματα -- ανακαλύπτοντας, αξιολογώντας,
συνθέτοντας και οπτικοποιώντας την επιστημονική γνώση μέσω μιας πρακτορικής,
ανθρωποκεντρικής ροής εργασίας.

### Μια Καθολική Πλατφόρμα

Το TALOS δεν δεσμεύεται σε κανένα συγκεκριμένο ερευνητικό θέμα. Λειτουργεί
πλήρως απομονωμένο και τοπικά: το τοπικό περιβάλλον εκτέλεσης Ollama
(`llama3.1:8b`, `nomic-embed-text`) παρέχει συμπερασμό και ενσωματώσεις με
μηδενική εξάρτηση από νέφος, μηδενική τηλεμετρία και πλήρη εκτός σύνδεσης
εκτέλεση PRISMA. Η πλατφόρμα εξυπηρετεί εξίσου τη βιβλιογραφία αυτόνομων
συστημάτων, πολύπλοκων κυβερνοφυσικών δικτύων, κλινικής έρευνας ή θεμελιώδους
φυσικής.

### Ενδεικτική Μελέτη Περίπτωσης Αναφοράς

Τα αυτόνομα συστήματα και τα πολύπλοκα κυβερνοφυσικά δίκτυα -- για παράδειγμα,
ο συνεργατικός σχεδιασμός αποστολών και η κατανομή καθηκόντων σε αυτόνομα
σμήνη Μη Επανδρωμένων Αεροχημάτων (UAV), μέσω Ετερογενούς Πολυπρακτορικής
Βαθιάς Ενισχυτικής Μάθησης (HMADRL), Χωροχρονικών Νευρωνικών Δικτύων Γράφων
(ST-GNN) και Αποκεντρωμένων Μερικώς Παρατηρήσιμων Μαρκοβιανών Μοντέλων
Απόφασης (Dec-POMDP) -- χρησιμεύουν ως ενδεικτικός φόρτος εργασίας αναφοράς που
καταδεικνύει την απόδοση, το φιλτράρισμα συνάφειας και τις εγγυήσεις
αναπαραγωγιμότητας της πλατφόρμας. Η ίδια η πλατφόρμα παραμένει πλήρως
ανεξάρτητη από γνωστικό πεδίο.

### Οι 9 Αρχιτεκτονικοί Πυλώνες

**Πυλώνας Α -- Δηλωτικός Αγωγός PRISMA-ScR του Stanford DSPy (`src/prisma/`).**
Ένας αγωγός σύνθεσης σκοπικής ανασκόπησης τεσσάρων φάσεων, συμβατός με το
πρότυπο PRISMA 2020, που βασίζεται σε τυποποιημένες δηλωτικές υπογραφές
(`PrismaPlanSignature`, `PrismaScreeningSignature`, `PrismaEligibilitySignature`,
`PrismaSynthesisSignature`), διαλογή PlanEval με Αλυσίδα Σκέψης
(`PrismaEvaluator`), δυναμική γεννήτρια διαγράμματος ροής PRISMA 2020 Mermaid και
συνθέτη σκοπικής ανασκόπησης LaTeX.

**Πυλώνας Β -- Σμήνος Ομότιμης Αναθεώρησης Πολλαπλών Πρακτόρων & Μηχανή
Συναίνεσης.** Ένα εξειδικευμένο σμήνος τριών κριτών (Αλγοριθμικός, Εμπειρική
Αυστηρότητα, Επιχειρησιακός/NATO) με αυτοματοποιημένο υπολογισμό συμφωνίας
μεταξύ κριτών κατά Cohen's Kappa και τη γενίκευση Fleiss, και Διαιτητή
Συναίνεσης με Αλυσίδα Σκέψης.

**Πυλώνας Γ -- Πλήρης Πολυνηματική Συλλογή & Αξιολόγηση.** Ένα
`ThreadPoolExecutor(max_workers=18)` συλλέγει ταυτόχρονα και από τα 18 επίσημα
ακαδημαϊκά API, μειώνοντας την καθυστέρηση από περίπου 45 δευτερόλεπτα σε
περίπου 3 δευτερόλεπτα, με δυναμική αξιολόγηση παρτίδας ασφαλή ως προς τη VRAM.

**Πυλώνας Δ -- Καθολικός Κόμβος Επιστημονικής Αναζήτησης.** Έξι συντονισμένες
λειτουργίες ανακάλυψης: (1) Ημερήσια Ταυτόχρονη Κατάποση, (2) Ιστορική
Αναζήτηση Παραθύρου Ημερών, (3) Αυτόνομη Χιονοστιβάδα Παραπομπών, (4) Νευρική
Διανυσματική Σημασιολογική Αναζήτηση (`nomic-embed-text`), (5) Αναπαραγώγιμη
Αναζήτηση με Προτεραιότητα στον Κώδικα, και (6) Δηλωτική Σύνθεση PRISMA-ScR.

**Πυλώνας Ε -- Επίπεδο Απόκτησης 18 Ακαδημαϊκών Πηγών.** Το αρθρωτό υποπακέτο
`src/ingestion/sources/` φιλοξενεί ένα ενιαίο `SOURCE_REGISTRY` για: arXiv,
IEEE Xplore, Elsevier Scopus, OpenAlex, Semantic Scholar, Springer Link, DBLP,
CORE, Crossref, OpenArchives (EADD), PubMed, Science.gov, OSTI, PLOS, OpenReview,
OpenAIRE, NASA NTRS και HAL/Inria.

**Πυλώνας ΣΤ -- Οδηγός Ερευνητικής Ρύθμισης & Μήτρα Εκτέλεσης AI 5 Επιπέδων.**
Ο Οδηγός Ερευνητικής Ρύθμισης παρέχει πύλη απομόνωσης πολλαπλών προφίλ (Βήμα 0)
και σύνθεση αυστηρών ακαδημαϊκών κριτηρίων ένταξης/αποκλεισμού στα αγγλικά. Η
μήτρα 5 επιπέδων (`strict_local`, `local_first`, `cloud_first`, `strict_cloud`
με διατήρηση VRAM, `auto_dynamic`) δρομολογεί τον συμπερασμό μεταξύ CPU edge,
GPU heavy και προαιρετικού Universal Cloud Mesh.

**Πυλώνας Ζ -- Διαγνωστικός Αναλυτής ISO/IEC 25010.** Ένας αυτοματοποιημένος
προληπτικός έλεγχος υγείας οκτώ σημείων (περιβάλλον Python, ακεραιότητα SQLite,
τοπικό περιβάλλον εκτέλεσης AI, διαθεσιμότητα θυρών, δικαιώματα συστήματος
αρχείων, διαπιστευτήρια περιβάλλοντος, κατάσταση δαίμονα, προαιρετικά άκρα
δικτύου) με οδηγίες αποκατάστασης μίας γραμμής, μέσω `--diagnostics` / `--doctor`.

**Πυλώνας Η -- Αυτοματοποιημένος Εξαγωγέας BibTeX/LaTeX.** Εξαγωγή με ένα κλικ
(`--export-bib`) της επιμελημένης βιβλιοθήκης στο `data/exports/talos_library.bib`
με κλειδιά παραπομπής `AuthorYearTitleKeyword` και πλήρη απολύμανση δεσμευμένων
χαρακτήρων LaTeX.

**Πυλώνας Θ -- Οπτικοποιητής Αστερισμού Γνώσης 3D WebGL & Κεντρικός Κόμβος
Επιφάνειας Εργασίας.** Ένας ενσωματωμένος οπτικοποιητής Three.js αποδίδει το
αξιολογημένο σώμα εργασιών ως ζωντανό τρισδιάστατο αστερισμό, σε συνδυασμό με
εγγενή κεντρικό κόμβο επιφάνειας εργασίας Win32 (κλείσιμο στο δίσκο συστήματος)
και κονσόλα τηλεμετρίας glassmorphism.

---

### Οδηγίες Εγκατάστασης & Χρήσης

**Μέθοδος Α -- Docker Compose.**
1. Εγκαταστήστε το Docker Desktop.
2. Δημιουργήστε το `.env` από το πλήρως σχολιασμένο `example.env`.
3. Εκκινήστε τον headless FastAPI server (θύρα 8001): `docker compose up -d --build`
4. Επιβεβαιώστε την υγεία: `curl http://localhost:8001/api/v1/health`

**Μέθοδος Β -- Εκκινητής 1-Κλικ (Windows).**
1. Ρυθμίστε το `.env`.
2. Κάντε διπλό κλικ στο `run_talos.bat`.

**Μέθοδος Γ -- Εκκινητής Linux.**
1. Ρυθμίστε το `.env`.
2. Εκτελέστε το `./run_talos.sh`.

**Μέθοδος Δ -- Σημαίες CLI Fast-Dispatch.** `--wizard`, `--daily`,
`--prisma [--swarm]`, `--doctor`, `--diagnostics`, `--export-bib`, `--strategy`,
`--snowball`, `--vector-search`, `--code-search`.

---

### Ακαδημαϊκή Παραπομπή

C. Smarlamakis and E. Georgopoulos, "Project TALOS: Tactical Agentic Literature
Orchestration System," version 5.15.2, 2026. [Online]. Available:
https://github.com/Christos-Smarlamakis/Project-TALOS, doi: 10.5281/zenodo.19224912.

```bibtex
@software{talos2026,
  author       = {Smarlamakis, Christos and Georgopoulos, Efstratios},
  title        = {Project TALOS: Tactical Agentic Literature Orchestration System},
  version      = {5.15.2},
  year         = {2026},
  doi          = {10.5281/zenodo.19224912},
  url          = {https://github.com/Christos-Smarlamakis/Project-TALOS},
  license      = {AGPL-3.0},
  note         = {IEEE Computer Society WEIGD Student Support Fund (2026) recipient}
}
```

---

### Άδεια Χρήσης & Ευχαριστίες

Το έργο διανέμεται υπό την **GNU Affero General Public License v3.0 (AGPLv3)**.
Η ακαδημαϊκή και ερευνητική χρήση είναι δωρεάν, με την προϋπόθεση ανοιχτής
διάθεσης των τροποποιήσεων υπό AGPLv3. Η εμπορική χρήση απαιτεί ξεχωριστή άδεια.

Ο Επικεφαλής Αρχιτέκτονας και Συγγραφέας, **Χρήστος Σμαρλαμάκης**, είναι
επίσημα επιλεγμένος αποδέκτης του **IEEE Computer Society WEIGD Student Support
Fund (2026)**. Ευχαριστούμε θερμά την IEEE Computer Society και τη διαχρονική
κληρονομιά της Dr. Grace C. N. Wei για την υποστήριξη ανοιχτού κώδικα και
εκδημοκρατισμένων ερευνητικών εργαλείων για την παγκόσμια επιστημονική κοινότητα.

*Σχεδιάστηκε και αναπτύχθηκε με υποβοήθηση τεχνητής νοημοσύνης από τον Χρήστο
Σμαρλαμάκη.*



