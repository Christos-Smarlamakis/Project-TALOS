# Changelog - Project TALOS

All notable changes to the TALOS project will be documented in this file. The project adheres to [Semantic Versioning](https://semver.org/).

## [v4.8.3] - 2026-06-27 - The "Secure Local AI & Privacy" Update

This release strengthens the **security and privacy** of local mode. It adds **model pre-verification with auto-install** at startup, **user consent** before any cloud fallback, and **bidirectional fallback** (local↔cloud) with explicit approval.

### Added
- **Model Pre-Verification (`_verify_local_models`):**
  - When LOCAL mode is selected, TALOS verifies **once** that all required models (chat + embedding) are installed.
  - Missing models are automatically pulled via `ollama pull`.
  - `TALOS_MODELS_VERIFIED=1` is passed to all subprocesses, avoiding redundant checks.
- **Privacy Guard: Cloud Fallback Consent:**
  - When the local model fails, TALOS does **NOT** automatically send data to the cloud.
  - User is prompted at startup: "Allow cloud fallback if local fails?"
  - If answered **NO**, data stays **fully offline** — no API calls leave the machine.
- **Bidirectional Fallback:**
  - In CLOUD mode, user can allow fallback to local model if cloud fails ("Allow local fallback if cloud fails?").
  - `TALOS_ALLOW_CLOUD_FALLBACK` and `TALOS_ALLOW_LOCAL_FALLBACK` env vars control behavior.

### Fixed
- **Local Provider Priority:**
  - Fixed: when LOCAL mode is selected, local model is placed **first** in `provider_priority` (using `insert(0, 'local')` instead of `append`).
  - Previously, local was appended last and only tried after Gemini and DeepSeek failed.
- **Embedding Model Missing:**
  - `_ensure_local_model()` did not check for the embedding model (`nomic-embed-text`).
  - Added automatic check and installation for the embedding model.
- **Embedding Priority:**
  - `generate_embeddings()` now tries the local embedding model **first**, then falls back to Gemini.
- **Maintenance Menu:**
  - Restored options 4-8 (Embedding Generator, Re-evaluate, Recalculate, Data Enricher, Trend Analyzer) lost during refactoring.

### Changed
- **`talos.py`:**
  - Added `_verify_local_models()` for centralized model checks.
  - Added interactive prompts for cloud/local fallback consent.
  - Automatic propagation of `TALOS_MODELS_VERIFIED`, `TALOS_ALLOW_CLOUD_FALLBACK`, `TALOS_ALLOW_LOCAL_FALLBACK` to subprocesses.
- **`ai_manager.py` v3.5:**
  - Skips `_ensure_local_model()` in subprocesses when models already verified.
  - Added security check before cloud fallback (requires `TALOS_ALLOW_CLOUD_FALLBACK=1`).
  - Fixed provider ordering (local first) and embedding fallback (local first).

---


## [v4.8.2] - 2026-06-27 - The "Local AI & Resilience" Update

This release focuses on **autonomy** and **resilience**. It introduces **local AI model support (Ollama)** enabling fully offline operation without cloud dependencies, while also fixing **16 critical bugs** that impacted system stability.

### Added
- **Local AI Model Support (Ollama):**
  - Integration of Ollama as a third AI provider in `AIManager`, alongside Gemini and DeepSeek.
  - Uses Ollama's **OpenAI-compatible API** for seamless compatibility with existing code (`/v1/chat/completions`).
  - **Auto-install:** If the selected model is not found locally, TALOS automatically runs `ollama pull`.
  - **Local Embeddings:** Support for Ollama Embeddings API (`/api/embed`) using `nomic-embed-text` for semantic search without cloud dependency.
  - **Interactive Mode Selection:** `talos.py` prompts the user at the start of each session to choose between local or cloud model.
  - **Graceful Degradation:** If the Ollama server is unreachable or the model fails, it automatically disables and falls back to cloud providers.
  - **New environment variables:** `TALOS_USE_LOCAL`, `LOCAL_MODEL_NAME`, `LOCAL_MODEL_BASE_URL`, `LOCAL_EMBEDDING_MODEL`, `LOCAL_MODEL_API_KEY`.

### Fixed
- **CRITICAL: `db_stats.py` KeyError Crash:**
  - `get_database_statistics()` was missing `elite_papers`, `missing_doi`, and `embedded_papers` fields, causing a `KeyError` crash in `db_stats.py`. All missing fields have been added.
- **CRITICAL: Source Agents Crash Without API Keys:**
  - Agents `elsevier_source`, `ieee_source`, `springer_source`, and `openarchives_source` raised `ValueError` during `__init__` if API keys were missing, killing the entire `daily_search.py` even when the other 10 agents were functional.
  - **Fix:** Added `self.enabled` flag with graceful skip. Added guard `if not getattr(self, "enabled", True): return []` to every `fetch_new_papers()`.
- **HIGH: `recommender.py` — Missing `operational_score`:**
  - The SQL query in Recommender was not selecting `operational_score`, causing operational evaluations to be completely ignored in the Reading Recommendation report. Added the missing field.
- **HIGH: `interactive_dashboard.py` — ValueError in Semantic Search Sort:**
  - When a paper ID from the database was not present in semantic search results, `.index()` threw a `ValueError`. Replaced with dictionary-based lookup.
- **HIGH: `daily_search.py` — Silent Loss of Papers Without DOI:**
  - Deduplication used only DOI as key, silently dropping papers without DOI (e.g., from DBLP, OpenArchives). Added URL fallback, aligning logic with `historic_search.py`.
- **MEDIUM: `crossref_source.py` — IndexError on Empty Title:**
  - If the Crossref API returned `"title": []`, `[][0]` caused an `IndexError`. Added empty list check.
- **MEDIUM: `openalex_source.py` — KeyError on Missing `meta`:**
  - `data['meta']` access replaced with `data.get('meta', {})` for safe handling of malformed API responses.
- **MEDIUM: `plos_source.py` — Dead Code `title_display`:**
  - The `title_display` field was not included in the `fl` parameter of the API request, making `doc.get("title_display", ...)` always return `None`. Fixed fallback order.
- **MEDIUM: `database_manager.py` — `duplicate column name` Warning:**
  - The `ALTER TABLE` for `operational_score` ran without an existence check, producing noisy error messages at every startup. Added `PRAGMA table_info` check before ALTER.

### Changed
- **`ai_manager.py` v3.4 → v3.5:**
  - Complete reorganization of the provider system with local model support.
  - `generate_embeddings()` now supports fallback to local embedding model.
  - `_execute_request()` supports the `local` provider alongside Gemini and DeepSeek.
- **`talos.py`:**
  - Added interactive prompt for Local/Cloud selection at the start of each session.
  - Automatic propagation of selection to all subprocesses via `TALOS_USE_LOCAL` environment variable.
- **`database_manager.py`:**
  - `get_database_statistics()` now returns `elite_papers`, `missing_doi`, and `embedded_papers`.

---


## [v4.8.1] - 2026-05-08 - The Dockerization & Portability Update

This update focuses on zero-friction deployment, ensuring that Project TALOS is environment-agnostic and accessible to researchers regardless of their technical background.

### Added
- **Docker Integration:**
  - Added `Dockerfile` optimized for `python:3.10-slim`.
  - Added `docker-compose.yml` for simplified orchestration, persistent volumes, and interactive TTY support for terminal menus.
- **Windows 1-Click Launcher:**
  - Added `start_talos.bat` which autonomously handles virtual environment creation, dependency installation, and `.env` initialization.
- **Documentation Update:** 
  - Updated `README.md` to reflect the new deployment methods, ensuring "Zero-Friction" setup for all users.

---
 
##[v4.8.0] - 2026-03-20 - The "Enrichment & Scientometrics" Update

This release is a major milestone for Project TALOS, transforming the database from a passive bibliography list into an **active, interconnected Knowledge Hub**. It introduces bulk data enrichment capabilities from third-party sources and offers, for the first time, "macroscopic" oversight of the research field through advanced visualizations.

### Added
- **NEW MODULE: Scientometrics Suite (`scripts/trend_analyzer.py`):**
  - A new subsystem that generates **HTML Reports** with statistical analyses and visualizations using `matplotlib`, `seaborn`, and `wordcloud`.
  - **Available Visualizations:**
    - **Research Timeline:** Bar chart of publications per year (identifying interest "bursts").
    - **Quality Landscape (KDE Plots):** Density curves for Strategic/Tactical/Overall score distributions.
    - **Open Access Landscape:** Pie Chart for accessibility distribution (Gold, Green, Hybrid, Closed).
    - **Keyword Dominance (WordCloud):** Semantic analysis of titles to identify dominant trends (e.g., "Reinforcement Learning", "UAV").
    - **Top Authors:** Analysis of the most productive researchers in the database.

- **NEW MODULE: Data Enricher (`scripts/data_enricher.py`):**
  - Replaces and heavily expands the legacy `pdf_retriever.py`.
  - **"Hub" Functionality:** Connects to the **Unpaywall API** and retrieves external identifiers (`openalex_id`, `pmid`, `pmcid`), turning the local DB into a bridge between different academic ecosystems.
  - **Smart Metadata:** Enriches records with `oa_status`, `journal_issn`, and corrected `publisher` strings.
  - **Aggressive Initialization:** Incorporates a `force_reset_status` mechanism that automatically fixes older records with `NULL` status, ensuring no article is left unprocessed.

- **Infrastructure & Migration Tools:**
  - **`scripts/upgrade_to_v4_8.py`:** A standalone safe upgrade tool that creates a backup and applies the new schema (Schema Migration) to the active profile's database.
  - **`scripts/fix_missing_columns.py`:** Emergency script that recursively scans all profile folders to locate and repair databases with outdated schemas.

### Changed
- **Database Schema Evolution (Core v5.2):**
  - The `papers` table was expanded with 9 new columns: `oa_pdf_url`, `openalex_id`, `pmid`, `pmcid`, `oa_status`, `journal_issn`, `publisher`, `enrichment_status`.
  - The `enrichment_status` column (INTEGER) acts as a state machine (0=Pending, 1=Enriched, 2=Failed) to control the workflow.

- **Core Architecture (`core/database_manager.py`):**
  - **Profile Awareness:** The `DatabaseManager` now accepts an optional `db_path` argument during initialization, allowing maintenance scripts to dynamically target the active profile's database instead of the default one.
  - **Batch Operations Fix:** The `update_papers_enrichment_batch` method was implemented using `executemany` for speed, and a critical `sqlite3.InterfaceError` (Binding Error) was fixed.

- **UX / Menu (`talos.py`):**
  - The "Maintenance Tools" menu was completely reorganized.
  - Added automatic detection of the active Database Path, which is passed as an argument to the `trend_analyzer` and `data_enricher` scripts, resolving incompatibility issues in multi-profile environments.

### Fixed
- **Critical Binding Error:** Fixed a bug in `data_enricher.py` where failure to find data resulted in incomplete dictionaries and database crashes during writing. The script now correctly returns full dictionaries with `None` values (Null Object Pattern).
- **Null Status Bug:** Fixed a logical error where SQL queries ignored records with `enrichment_status IS NULL`.

---

## [v4.7.1] - 2025-11-30 - The "HERMES" Performance Update

This release dramatically improves the execution speed of `pdf_retriever.py` (Project HERMES).

### Changed
- **Multithreaded PDF Retrieval:**
  - The logic of `pdf_retriever.py` was completely rewritten to utilize **Multithreading** via a `ThreadPoolExecutor`.
  - The script now executes multiple (default: 15) Unpaywall API calls concurrently, rather than serially.
  - **Result:** The Open Access PDF checking process is now ~10-15 times faster.

---

##[v4.7.0] - 2025-11-30 - The PDF Retriever Update (Ethical Edition)

### Added
- **NEW MODULE: Project PDF Retriever (`scripts/pdf_retriever.py`):**
  - A maintenance tool that scans the database for articles with DOIs.
  - Calls the **Unpaywall API** to locate legal, **Open Access** versions of PDFs.
  - Saves the links in a new `oa_pdf_url` column in the DB, promoting "Open Science".

### Changed
- **Database Schema (v5.1):** Added the `oa_pdf_url` column for storing links.

---

##[v4.6.0] - 2025-11-30 - The "ORACLE" Update

Introduction of Project ORACLE for discovering "Grey Literature", leveraging the new Gemini 2.0 models and Google Search Grounding capabilities.

### Added
- **NEW MODULE: Project "ORACLE" (`scripts/oracle_agent.py`):**
  - **Role:** Performs "Horizon Scanning" on the web for resources not found in traditional academic databases (GitHub code, Datasets, Technical Reports).
  - **Technology:** Uses the `google-genai` SDK and the `gemini-2.0-flash-exp` (or Pro) model with the **Google Search** tool enabled.
  - **Output:** Produces Markdown reports with links, saved in `reports/oracle_deep_research/`.

---

##[v4.4.0] & [v4.5.0] - 2025-11-30 - The "Open Access & Onboarding" Update

This release dramatically improves the accessibility of TALOS. It introduces an automated onboarding wizard for new users and expands data sources with the addition of PLOS (Public Library of Science).

### Added
- **NEW AGENT: `sources/plos_source.py` (Project ALEXANDRIA):**
  - Integration of the PLOS API. Ensures access to high-quality, Open Access articles.
- **Onboarding Wizard (`talos.py`):**
  - Automatically creates `config.json` from a template and launches "PYTHIA" to set up the user's first research profile, minimizing Time-to-Value.

---

##[v4.3.1] - 2025-11-30 - The Batch Execution Fix

### Fixed
- **Database Batch Operations (`core/database_manager.py` v4.7):**
  - Fixed the `sqlite3.ProgrammingError: Incorrect number of bindings supplied` error during bulk embedding updates.
  - Added the `execute_many()` method leveraging SQLite's `executemany` for safe and fast bulk inserts/updates.

---

## [v4.3.0] - 2025-11-28 - The "Soft Shutdown" Update

### Added
- **Dashboard Soft Shutdown:**
  - Added a "🔴 Exit & Return to Menu" button in the Dashboard UI.
  - Implemented a new `/api/shutdown` endpoint to gracefully terminate the Flask server using threading and signals.

---

## [v4.2.0] - 2025-11-28 - The Pythia Refinement & Architecture Hardening

### Changed
- **AIManager v3.4 (System Prompt Override):**
  - Introduced the ability to override the default `system_prompt` so specialized agents (like PYTHIA) can assume different personas.
- **AIManager v3.3 (Surgical JSON Cleaning):**
  - Implemented a new mechanism to "surgically" clean AI responses (extracting the JSON object from Markdown blocks).
- **ArxivSource v3.8 (Config-Driven Architecture):**
  - Removed hardcoded search terms. The agent dynamically reads `arxiv_query` from `config.json`.

---

##[v4.1.0] - 2025-11-28 - The Quad-Layer Architecture & Profile System

### Added
- **Quad-Layer Evaluation Framework:**
  - The evaluation system expanded from 3 to **4 levels**:
    1. **Strategic** (High-level decision making)
    2. **Operational** (Auction-based mechanisms, resource allocation) - **NEW**
    3. **Tactical** (DRL/MARL policies)
    4. **Playground** (Simulation)
- **Profile Management System (`scripts/profile_manager.py`):**
  - Ability to create and switch between isolated "Profiles" (e.g., "Drones", "Bioinformatics"), each with its own DB and config.

---

## [v4.0.0] - 2025-11-28 - Project "PYTHIA" (Automated Configuration)

### Added
- **NEW MODULE: Project "PYTHIA" (`scripts/query_translator.py`):**
  - An automation that uses AI to translate a natural language research goal into optimized Boolean Search Queries for 10+ APIs and customized System Prompts.

---

## [v3.2.0] - 2025-09-27 - Operation "Genesis"

### Changed
- **BREAKING CHANGE - Complete Overhaul of "Agents" (`sources/*.py`):**
  - All Agents (ArXiv, Scopus, IEEE, Semantic Scholar, Springer, OpenAlex, DBLP, CORE, Crossref, OpenArchives, OSTI, PubMed, Science.gov) were completely rewritten.
  - **Standardized Output:** Every Agent now returns a standardized dictionary ensuring critical fields (`doi`, `publication_year`, `authors_str`) are always present.

---

## [v3.0.0] - 2025-09-26 - The Strategic Mentor (CHIRON)

### Added
- **NEW MAJOR MODULE: Project "CHIRON" (`scripts/knowledge_path_generator.py`)**
  - Allows users to initiate a natural language dialogue.
  - Performs deep semantic search, applies Knowledge Structuring (K-Means Clustering), and generates narrative Markdown reports explaining *why* the user should follow a specific study path.

---

## [v2.21.0] - 2025-09-26 - The Reliability Update

### Changed
- **BREAKING CHANGE - JSON Architecture:**
  - `AIManager` completely redesigned to be **Model-Independent**, natively supporting JSON mode and provider-specific Circuit Breakers.
  - Removed all legacy Regex Parsing functions for data extraction.

---

## [v2.20.0] - 2025-09-22 - The "ORPHEUS" Interactive Knowledge Graph

### Added
- **NEW MODULE: Citation Analyzer ("ORPHEUS"):**
  - Accepts a target paper DOI, queries Semantic Scholar for references/citations, and generates a fully interactive HTML network graph using `pyvis`.

---

##[v2.19.0] - 2025-09-21 - The Zotero Bridge & "Smart Sync" Update

### Added
- **NEW MODULE: Zotero Connector:**
  - Connects to the Zotero Web API (`pyzotero`). Fetches user's papers, runs them through the deep Pro AI evaluation, and synchronizes the local database.

---

## [v2.18.0] - 2025-09-21 - The AI Resilience & Agent Expansion Update

### Added
- **AI Manager (`core/ai_manager.py`):**
  - Centralized class handling all LLM calls. Includes automatic Fallback logic (Circuit Breaker) from Google Gemini to DeepSeek if quota is exceeded.

### Changed
- **"Smart Store-First" Strategy:**
  - `daily_search.py` now performs a fast pre-screening (Flash model), stores the paper, and selectively upgrades "Elite" papers to Deep Analysis (Pro model), drastically reducing API calls.

---

## [v2.15.0] - 2025-09-19 - The "NAFSIKA" Interactive Dashboard

### Added
- **Interactive Dashboard (`scripts/interactive_dashboard.py`):**
  - A lightweight local Flask web server.
  - Integrates `Tabulator.js` for dynamic sorting, filtering, and real-time database updates without page reloads. Includes Semantic Search backend and "Article DNA" visualization.

---

## [v1.0.0] - 2025-08-27 - The Genesis

### Added
- **Initial Creation:** The project started as a simple script (`main.py`) querying arXiv and evaluating abstracts via Gemini AI, sending Discord notifications via Webhook.