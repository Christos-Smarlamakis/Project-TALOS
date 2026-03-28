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
# scripts/data_enricher.py
# (v4.8.1 - Fix Binding Error Update)

import requests
import sqlite3
import concurrent.futures
from tqdm import tqdm
import os
import sys
from dotenv import load_dotenv
import json

# --- SETUP PATHS & ENV ---
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

# Load Environment Variables
load_dotenv(os.path.join(project_root, '.env'))
UNPAYWALL_EMAIL = os.getenv("UNPAYWALL_EMAIL")

if not UNPAYWALL_EMAIL:
    try:
        with open(os.path.join(project_root, 'config.json'), 'r', encoding='utf-8') as f:
            config = json.load(f)
            UNPAYWALL_EMAIL = config.get("mailto")
    except:
        pass

if not UNPAYWALL_EMAIL:
    print("❌ ERROR: 'UNPAYWALL_EMAIL' missing via .env or config.json.")
    sys.exit(1)

from core.database_manager import DatabaseManager

# --- CONFIGURATION ---
MAX_WORKERS = 10 

# Handle Database Path
if len(sys.argv) > 1:
    DB_PATH = sys.argv[1]
else:
    DB_PATH = os.path.join(project_root, 'talos_research.db') 
    if not os.path.exists(DB_PATH):
         DB_PATH = os.path.join(project_root, '_profiles', 'default', 'talos_research.db')

def get_enrichment_data(doi):
    url = f"https://api.unpaywall.org/v2/{doi}?email={UNPAYWALL_EMAIL}"
    try:
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            return response.json()
    except requests.RequestException:
        return None
    return None

def process_paper(paper_data):
    # paper_data is tuple: (id, doi, abstract)
    paper_id = paper_data[0]
    doi = paper_data[1]
    
    # --- ΔΙΟΡΘΩΣΗ: Αρχικοποίηση όλων των πεδίων με None ---
    result_dict = {
        "paper_id": paper_id,
        "oa_pdf_url": None,
        "openalex_id": None,
        "pmid": None,
        "pmcid": None,
        "oa_status": None,
        "journal_issn": None,
        "publisher": None,
        "status": 2 # Default to Failed/No Data
    }

    if not doi:
        return result_dict

    data = get_enrichment_data(doi)
    
    if data and isinstance(data, dict) and 'error' not in data:
        # Extract fields
        best_oa_location = data.get('best_oa_location')
        pdf_url = best_oa_location.get('url_for_pdf') if best_oa_location else None
        if not pdf_url and best_oa_location:
             pdf_url = best_oa_location.get('url')

        openalex_id = None
        pmid = None
        pmcid = None
        
        if 'ids' in data:
            openalex_id = data['ids'].get('openalex')
            pmid = data['ids'].get('pmid')
            pmcid = data['ids'].get('pmcid')

        if openalex_id and 'openalex.org' in openalex_id:
            openalex_id = openalex_id.split('/')[-1]

        # Ενημερώνουμε το λεξικό με τα δεδομένα που βρήκαμε
        result_dict.update({
            "oa_pdf_url": pdf_url,
            "openalex_id": openalex_id,
            "pmid": pmid,
            "pmcid": pmcid,
            "oa_status": data.get('oa_status'),
            "journal_issn": data.get('journal_issn_l'),
            "publisher": data.get('publisher'), 
            "status": 1 # Success
        })
        
    return result_dict

def force_reset_status(db_path):
    """
    Διορθώνει το πρόβλημα με τα NULL values.
    """
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE papers SET enrichment_status = 0 WHERE enrichment_status IS NULL")
            conn.commit()
    except Exception as e:
        pass

def main():
    print(f"\n--- Project TALOS v4.8.1: Data Enrichment Agent (Fixed) ---")
    print(f"--- Database: {os.path.basename(DB_PATH)} ---")
    
    force_reset_status(DB_PATH)
    db_manager = DatabaseManager(DB_PATH)

    # Custom aggressive targeting
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            query = "SELECT id, doi, abstract FROM papers WHERE (enrichment_status != 1 OR enrichment_status IS NULL) AND doi IS NOT NULL AND doi != ''"
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
    
    # 3. Execution
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

    # 4. Batch Update
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