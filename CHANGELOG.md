# Changelog - Project TALOS

All notable changes to the TALOS project will be documented in this file. The project adheres to [Semantic Versioning](https://semver.org/).

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