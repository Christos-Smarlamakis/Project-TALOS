# -*- coding: utf-8 -*-
#  Project TALOS
#  Copyright (C) 2026 Christos Smarlamakis
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Affero General Public License as
#  published by the Free Software Foundation, either version 3 of the
#  License, or (at your option) any later version.
#
#  For commercial licensing, please contact the author.
"""
Module: data_enricher.py (v4.8.1 — Graceful Degradation)
Project: TALOS v5.0.0
Description:
    Data enrichment agent that queries the Unpaywall API to find Open Access
    PDF URLs, OpenAlex IDs, PubMed IDs, and publisher metadata for papers
    in the TALOS database. Runs multi-threaded batch enrichment with a
    configurable thread pool.

    How it works:
    - Reads papers without enrichment (enrichment_status != 1) from the DB.
    - For each DOI, calls api.unpaywall.org to retrieve OA status and IDs.
    - Batch-updates the database with the enriched metadata.
    - Gracefully skips papers without a DOI (marks them as failed=2).
    
    Key design decisions:
    - ThreadPoolExecutor for parallel API calls (configurable MAX_WORKERS).
    - Falls back to config.json mailto if UNPAYWALL_EMAIL env var is missing.
    - Database path auto-detects profile-aware DB when no CLI arg given.
    - Force-resets NULL enrichment_status to 0 before processing to fix
      legacy records from before v4.8.0 schema.
"""

import requests
import sqlite3
import concurrent.futures
from tqdm import tqdm
import os
import sys
import os, sys
_P = os.path.abspath(os.path.dirname(__file__))
while _P and not os.path.exists(os.path.join(_P, 'talos.py')):
    _P = os.path.dirname(_P)
if _P: sys.path.insert(0, _P)
from dotenv import load_dotenv
import json

# ── SETUP PATHS & ENV ───────────────────────────────────────────────────────
# Resolve the project root so that all relative paths work regardless
# of the working directory from which the script was launched.
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

# ── Load Environment Variables ──────────────────────────────────────────────
load_dotenv(os.path.join(project_root, '.env'))
UNPAYWALL_EMAIL = os.getenv("UNPAYWALL_EMAIL")

# Fallback to config.json if env var is missing
if not UNPAYWALL_EMAIL:
    try:
        with open(os.path.join(project_root, 'config.json'), 'r', encoding='utf-8') as f:
            config = json.load(f)
            UNPAYWALL_EMAIL = config.get("mailto")
    except Exception:
        pass

# ── Fail fast if no email is configured ─────────────────────────────────────
if not UNPAYWALL_EMAIL:
    print("❌ ERROR: 'UNPAYWALL_EMAIL' missing via .env or config.json.")
    sys.exit(1)

from src.core.database_manager import DatabaseManager

# ── CONFIGURATION ───────────────────────────────────────────────────────────
MAX_WORKERS = 10  # Number of parallel threads for API calls

# ── Handle Database Path ────────────────────────────────────────────────────
# Priority: CLI argument > project root > profile directory
if len(sys.argv) > 1:
    DB_PATH = sys.argv[1]
else:
    DB_PATH = os.path.join(project_root, 'talos_research.db')
    if not os.path.exists(DB_PATH):
        # Automatically switch to profile database if root DB doesn't exist
        DB_PATH = os.path.join(project_root, '_profiles', 'default', 'talos_research.db')

def get_enrichment_data(doi):
    """Query the Unpaywall API for a paper's Open Access status and metadata.

    The Unpaywall API is free to use with a valid email address. It returns
    the best available OA location, along with identifiers from OpenAlex,
    PubMed, and other sources.

    Args:
        doi (str): Paper DOI to look up.

    Returns:
        dict or None: Parsed JSON response from Unpaywall, or None if the
        request failed or the DOI was not found.
    """
    # ── Build the API URL with the email for polite pool access ──────────
    url = f"https://api.unpaywall.org/v2/{doi}?email={UNPAYWALL_EMAIL}"
    try:
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            return response.json()
    except requests.RequestException:
        # Network timeout or DNS failure — skip this paper gracefully
        return None
    return None

def process_paper(paper_data):
    """Process a single paper: query Unpaywall and extract metadata.

    This function is designed to run in a ThreadPoolExecutor. It receives
    a database row tuple, queries Unpaywall, and returns a dictionary
    ready for batch UPDATE.

    Args:
        paper_data (tuple): Database row (id, doi, abstract).

    Returns:
        dict: Enrichment result with paper_id, PDF URL, identifiers, and
        status code (1=Success, 2=Failed/No Data).
    """
    # paper_data is tuple: (id, doi, abstract)
    paper_id = paper_data[0]
    doi = paper_data[1]

    # ── Initialise all fields to None ──────────────────────────────────────
    # Default status=2 (Failed/No Data) — only changed to 1 on success
    result_dict = {
        "paper_id": paper_id,
        "oa_pdf_url": None,
        "openalex_id": None,
        "pmid": None,
        "pmcid": None,
        "oa_status": None,
        "journal_issn": None,
        "publisher": None,
        "status": 2
    }

    # ── Guard: no DOI → nothing to enrich ──────────────────────────────────
    if not doi:
        return result_dict

    # ── Query the Unpaywall API ────────────────────────────────────────────
    data = get_enrichment_data(doi)

    if data and isinstance(data, dict) and 'error' not in data:
        # ── Extract the best Open Access PDF URL ───────────────────────────
        # Unpaywall provides a list of OA locations sorted by quality.
        # 'best_oa_location' is the top-ranked one.
        best_oa_location = data.get('best_oa_location')
        pdf_url = best_oa_location.get('url_for_pdf') if best_oa_location else None
        if not pdf_url and best_oa_location:
            # Fallback: the landing page URL if no direct PDF is available
            pdf_url = best_oa_location.get('url')

        # ── Extract external identifiers ───────────────────────────────────
        openalex_id = None
        pmid = None
        pmcid = None

        if 'ids' in data:
            openalex_id = data['ids'].get('openalex')
            pmid = data['ids'].get('pmid')
            pmcid = data['ids'].get('pmcid')

        # Clean up OpenAlex URL → bare ID (e.g., "https://openalex.org/W123" → "W123")
        if openalex_id and 'openalex.org' in openalex_id:
            openalex_id = openalex_id.split('/')[-1]

        # ── Update the result dictionary with found data ───────────────────
        result_dict.update({
            "oa_pdf_url": pdf_url,
            "openalex_id": openalex_id,
            "pmid": pmid,
            "pmcid": pmcid,
            "oa_status": data.get('oa_status'),
            "journal_issn": data.get('journal_issn_l'),
            "publisher": data.get('publisher'),
            "status": 1  # Success
        })

    return result_dict

def force_reset_status(db_path):
    """Fix legacy NULL values in the enrichment_status column.

    Before v4.8.0, enrichment_status was allowed to be NULL. This
    function sets all NULL values to 0 (Pending) so that the enrichment
    pipeline can process them correctly.

    Args:
        db_path (str): Full path to the SQLite database.
    """
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            # Set any legacy NULL statuses to 0 (Pending)
            cursor.execute("UPDATE papers SET enrichment_status = 0 WHERE enrichment_status IS NULL")
            conn.commit()
    except Exception:
        # Silently ignore — the schema may not have the column yet
        pass

def main():
    """Main entry point: run the data enrichment pipeline.

    Workflow:
    1. Force-reset any NULL enrichment_status values (legacy fix).
    2. Query the database for papers that need enrichment.
    3. Process each paper in parallel via ThreadPoolExecutor.
    4. Batch-update the database with enriched metadata.
    """
    print(f"\n--- Project TALOS v4.8.1: Data Enrichment Agent (Fixed) ---")
    print(f"--- Database: {os.path.basename(DB_PATH)} ---")

    # ── Fix legacy NULL enrichment_status values ─────────────────────────
    force_reset_status(DB_PATH)
    db_manager = DatabaseManager(DB_PATH)

    # ── Query papers that need enrichment ──────────────────────────────────
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            # Only target papers with a DOI that haven't been enriched yet
            query = ("SELECT id, doi, abstract FROM papers "
                     "WHERE (enrichment_status != 1 OR enrichment_status IS NULL) "
                     "AND doi IS NOT NULL AND doi != ''")
            cursor.execute(query)
            papers_to_process = cursor.fetchall()
    except Exception as e:
        print(f"❌ Critical DB Error: {e}")
        return

    if not papers_to_process:
        print(">>> All records are fully enriched (Status=1). Standing by.")
        return

    print(f">>> Target Acquired: {len(papers_to_process)} papers pending enrichment.")

    update_list = []

    # ── Multi-threaded execution ────────────────────────────────────────────
    # Each paper is processed independently (IO-bound API calls).
    # ThreadPoolExecutor lets us run multiple API requests in parallel.
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        with tqdm(total=len(papers_to_process), desc="Enriching Data", unit="paper") as pbar:
            future_to_paper = {executor.submit(process_paper, paper): paper for paper in papers_to_process}

            for future in concurrent.futures.as_completed(future_to_paper):
                try:
                    result = future.result()
                    if result:
                        update_list.append(result)
                except Exception as e:
                    print(f"Thread Error: {e}")
                pbar.update(1)

    # ── Batch update the database ──────────────────────────────────────────
    if update_list:
        print(f"\n>>> Committing Intelligence: Updating {len(update_list)} records...")
        try:
            db_manager.update_papers_enrichment_batch(update_list)
            print(">>> ✅ Database synchronization complete.")
        except Exception as e:
            print(f"!!! DB SAVE ERROR: {e}")
    else:
        print(">>> No actionable intelligence found.")

    print("--- Mission Complete ---")

if __name__ == "__main__":
    main()