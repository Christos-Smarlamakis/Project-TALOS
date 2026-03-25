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
Module: historic_search.py (v5.5 - Final Quad-Layer & Rate Limit)
Project: TALOS v3.2

Description:
Η τελική, βελτιστοποιημένη έκδοση για την ιστορική αναζήτηση.
- Χρησιμοποιεί το Flash model για ταχύτητα.
- Εφαρμόζει το 'ai_request_delay' για να αποφύγει το rate limiting.
- Καταγράφει και εμφανίζει τα Quad-Layer scores (Strategic, Operational, Tactical, Playground).
- Είναι πλήρως εναρμονισμένη με τον νέο DatabaseManager v4.6.
"""
import sys
import os
import time
import json
from dotenv import load_dotenv

# Προσθέτουμε το root του project στο path για να βρει τα modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# --- Τοπικές Εισαγωγές ---
from sources.arxiv_source import ArxivSource
from sources.elsevier_source import ElsevierSource
from sources.semantic_scholar_source import SemanticScholarSource
from sources.ieee_source import IEEEXploreSource
from sources.springer_source import SpringerNatureSource
from sources.openalex_source import OpenAlexSource
from sources.dblp_source import DBLPSource
from sources.crossref_source import CrossrefSource
from sources.openarchives_source import OpenArchivesSource
from sources.pubmed_source import PubMedSource
from sources.osti_source import OSTISource
from sources.scigov_source import ScienceGovSource
from sources.plos_source import PLOSSource

from core.database_manager import DatabaseManager
from core.ai_manager import AIManager 

def load_configuration():
    print("ΦΑΣΗ 1: Φόρτωση ρυθμίσεων...")
    load_dotenv()
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    config_path = os.path.join(project_root, 'config.json')
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
        print("SUCCESS: Οι ρυθμίσεις φορτώθηκαν.\n")
        return config
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"FATAL: Σφάλμα φόρτωσης του config.json: {e}")
        sys.exit(1)

def main():
    print("--- ΕΝΑΡΞΗ ΙΣΤΟΡΙΚΗΣ ΑΝΑΖΗΤΗΣΗΣ (v5.5 - Quad-Layer) ---")
    
    config = load_configuration()
    ai_manager = AIManager(config)    
    db_manager = DatabaseManager() # Ο πίνακας δημιουργείται αυτόματα στο __init__
    
    # Ρυθμίζουμε το config για την ιστορική αναζήτηση
    historic_config = config.copy()
    days_historic = config.get("days_to_search_historic", 2190) # ~6 χρόνια
    historic_config["days_to_search_daily"] = days_historic 
    print(f"INFO: Η αναζήτηση ρυθμίστηκε για τις τελευταίες {days_historic} ημέρες.\n")

    # --- ΦΑΣΗ 2: ΑΝΑΚΤΗΣΗ ΑΠΟ ΠΗΓΕΣ ---
    sources_to_search = [
        ArxivSource(historic_config), 
        ElsevierSource(historic_config),
        SemanticScholarSource(historic_config), 
        IEEEXploreSource(historic_config),
        SpringerNatureSource(historic_config), 
        OpenAlexSource(historic_config),
        DBLPSource(historic_config), 
        CrossrefSource(historic_config), 
        OpenArchivesSource(historic_config),
        PubMedSource(historic_config),
        ScienceGovSource(historic_config),
        OSTISource(historic_config),
        PLOSSource(historic_config)
    ]
    
    all_historic_papers = []
    for source in sources_to_search:
        # Χρησιμοποιούμε extend για να προσθέσουμε τα αποτελέσματα στη λίστα
        fetched = source.fetch_new_papers()
        if fetched:
            all_historic_papers.extend(fetched)
        
    print(f"\nSUCCESS: Βρέθηκαν συνολικά {len(all_historic_papers)} πιθανά άρθρα από όλες τις πηγές.\n")

    # Φιλτράρουμε για μοναδικά άρθρα και για αυτά που δεν υπάρχουν ήδη στη βάση
    # Προτεραιότητα στο DOI, αν δεν υπάρχει ελέγχουμε το URL (μέσω του dictionary key)
    unique_papers_dict = {}
    for p in all_historic_papers:
        key = p.get('doi') if p.get('doi') else p.get('url')
        if key:
            unique_papers_dict[key] = p

    # Τελικό φιλτράρισμα με τη βάση
    papers_to_process = []
    for p in unique_papers_dict.values():
        if p.get('doi'):
            if not db_manager.paper_exists_by_doi(p['doi']):
                papers_to_process.append(p)
        elif p.get('url'):
             if not db_manager.paper_exists_by_url(p['url']):
                 papers_to_process.append(p)
    
    if not papers_to_process:
        print("INFO: Η βάση δεδομένων φαίνεται να είναι ήδη ενημερωμένη. Τερματισμός.")
        return
        
    print(f"INFO: Βρέθηκαν {len(papers_to_process)} νέα, μοναδικά άρθρα για προσθήκη στη βάση δεδομένων.")
    
    # --- ΦΑΣΗ 3: ΜΑΖΙΚΗ ΑΞΙΟΛΟΓΗΣΗ & ΑΠΟΘΗΚΕΥΣΗ ---
    API_CALL_LIMIT = config.get("api_call_limit_flash", 950)
    REQUEST_DELAY = config.get("ai_request_delay", 5)
    api_calls_made = 0

    for i, paper in enumerate(papers_to_process):
        if api_calls_made >= API_CALL_LIMIT:
            print(f"\nWARNING: Έφτασε το όριο των {API_CALL_LIMIT} κλήσεων. Το script θα σταματήσει για σήμερα.")
            break    

        print(f"-> Επεξεργασία άρθρου {i+1}/{len(papers_to_process)}: '{paper['title'][:80]}...'")
        
        content_for_ai = f"Title: {paper['title']}\nAbstract: {paper.get('abstract', '')}"

        evaluation_data = ai_manager.evaluate_paper_json(content_for_ai, model_type='flash')
        api_calls_made += 1

        if evaluation_data:
            db_manager.add_paper(paper, evaluation_data)
            
            # --- Quad-Layer Logging (Η Προσθήκη) ---
            scores = evaluation_data.get('scores', {})
            s = scores.get('strategic', 0)
            o = scores.get('operational', 0)
            t = scores.get('tactical', 0)
            p = scores.get('playground', 0)
            overall = evaluation_data.get('overall_score', 0)
            
            print(f"   SUCCESS: [S:{s} O:{o} T:{t} P:{p}] -> Overall: {overall:.2f}")
        else:
            print(f"   WARNING: Η αξιολόγηση απέτυχε. Παράλειψη.")

        time.sleep(REQUEST_DELAY)

    print("\n--- Η ΙΣΤΟΡΙΚΗ ΑΝΑΖΗΤΗΣΗ ΟΛΟΚΛΗΡΩΘΗΚΕ ---")

if __name__ == "__main__":
    main()