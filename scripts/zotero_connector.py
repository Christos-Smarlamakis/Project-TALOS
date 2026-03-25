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
Module: zotero_connector.py (v2.0 - JSON Reliability Update)
Project: TALOS v2.21.0

Description:
Η πλήρως αναβαθμισμένη έκδοση του "Zotero Bridge", εναρμονισμένη με την αρχιτεκτονική
της "Αναβάθμισης Αξιοπιστίας".
- Υλοποιεί τη στρατηγική "Zotero is Ground Truth" χρησιμοποιώντας τη νέα, αξιόπιστη
  μέθοδο `ai_manager.evaluate_paper_json()`.
- Επιβάλλει ΠΑΝΤΑ τη χρήση του Pro model για να διασφαλίσει την ύψιστη ποιότητα
  ανάλυσης για τα άρθρα που έχει επιλέξει ο χρήστης.
- Επικοινωνεί απρόσκοπτα με τον νέο DatabaseManager (v4.2), χρησιμοποιώντας
  τόσο DOI όσο και URL για μέγιστη ευελιξία.
"""
import os
import sys
import json
import time
from pyzotero import zotero
from dotenv import load_dotenv
from tqdm import tqdm

# Προσθέτουμε το root του project στο path για να βρει τα core modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.database_manager import DatabaseManager
from core.ai_manager import AIManager

def main():
    """
    Κύρια συνάρτηση που ενορχηστρώνει τον συγχρονισμό και την επανα-αξιολόγηση
    της βιβλιοθήκης Zotero.
    """
    print("--- ΕΝΑΡΞΗ ZOTERO BRIDGE (v2.0 - PRO MODEL JSON EVALUATION) ---")
    
    # --- ΦΑΣΗ 1: ΑΡΧΙΚΟΠΟΙΗΣΗ ---
    print("INFO: Φόρτωση ρυθμίσεων...")
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    config_path = os.path.join(project_root, 'config.json')
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
    except Exception as e:
        print(f"FATAL: Δεν ήταν δυνατή η φόρτωση του config.json. Σφάλμα: {e}")
        return

    load_dotenv()
    db_manager = DatabaseManager()
    ai_manager = AIManager(config)
    
    # Φόρτωση των credentials του Zotero από το .env αρχείο
    library_id = os.getenv("ZOTERO_USER_ID")
    api_key = os.getenv("ZOTERO_API_KEY")
    
    if not library_id or not api_key:
        print("FATAL: Δεν βρέθηκαν τα ZOTERO_USER_ID ή/και ZOTERO_API_KEY στο .env αρχείο.")
        return
        
    try:
        zot = zotero.Zotero(library_id, 'user', api_key)
        # Μια απλή κλήση για να επιβεβαιώσουμε ότι τα credentials είναι σωστά
        zot.key_info()
        print("SUCCESS: Η σύνδεση με το Zotero API πέτυχε.")
    except Exception as e:
        print(f"FATAL: Αποτυχία σύνδεσης με το Zotero. Ελέγξτε τα κλειδιά. Σφάλμα: {e}")
        return

    # --- ΦΑΣΗ 2: ΑΝΑΚΤΗΣΗ & ΦΙΛΤΡΑΡΙΣΜΑ ΑΠΟ ZOTERO ---
    print("\nINFO: Ανάκτηση όλων των αντικειμένων από τη βιβλιοθήκη Zotero...")
    try:
        items = zot.items()
        print(f"SUCCESS: Βρέθηκαν {len(items)} αντικείμενα στο Zotero.")
    except Exception as e:
        print(f"FATAL: Αποτυχία ανάκτησης δεδομένων από το Zotero. Σφάλμα: {e}")
        return

    # Φιλτράρουμε για να κρατήσουμε μόνο τα journal articles που έχουν DOI ή URL
    articles_to_process = [
        item for item in items if item.get('data', {}).get('itemType') == 'journalArticle' and \
        (item.get('data', {}).get('DOI') or item.get('data', {}).get('url'))
    ]
    print(f"INFO: Βρέθηκαν {len(articles_to_process)} άρθρα (journalArticle) με URL/DOI για επεξεργασία.")

    if not articles_to_process:
        print("Δεν βρέθηκαν κατάλληλα άρθρα στο Zotero για επεξεργασία. Τερματισμός.")
        return

    # --- ΦΑΣΗ 3: ΠΛΗΡΗΣ ΕΠΑΝΑ-ΑΞΙΟΛΟΓΗΣΗ (SYNC, ENRICH & UPGRADE) ---
    upsert_count = 0 # Μετράει και τα inserts (προσθήκες) και τα updates (ενημερώσεις)

    # Χρησιμοποιούμε tqdm για μια όμορφη μπάρα προόδου
    for item in tqdm(articles_to_process, desc="Syncing & Evaluating Zotero Library"):
        data = item.get('data', {})
        
        # Εξάγουμε με συνέπεια το DOI και το URL
        doi = data.get('DOI', '')
        url = data.get('url', '')
        
        # Δίνουμε προτεραιότητα σε ένα "καθαρό" URL από το DOI
        if doi and not url.startswith('https://doi.org'):
             url = f"https://doi.org/{doi}"
        
        title = data.get('title', 'N/A')
        
        tqdm.write(f"\n-> Επεξεργασία: '{title[:70]}...'")
        
        # 1. Δημιουργούμε το αντικείμενο `paper_data` με όλα τα διαθέσιμα δεδομένα
        abstract = data.get('abstractNote', 'Δεν υπάρχει διαθέσιμη περίληψη.')
        authors_list = data.get('creators', [])
        authors_str = ", ".join([f"{a.get('lastName', '')}, {a.get('firstName', '')}".strip(', ') for a in authors_list])
        publication_year = None
        date_str = data.get('date', '')
        if date_str and len(date_str) >= 4:
            try:
                publication_year = int(date_str[:4])
            except ValueError:
                publication_year = None

        paper_data = {
            'doi': doi,
            'url': url,
            'title': title, 
            'authors_str': authors_str, 
            'abstract': abstract,
            'publication_year': publication_year,
            'source': 'Zotero Sync & Upgrade'
        }

        # 2. Στέλνουμε ΠΑΝΤΑ για νέα, Pro-level αξιολόγηση μέσω της νέας, αξιόπιστης μεθόδου.
        content_for_ai = f"Title: {paper_data['title']}\nAbstract: {paper_data.get('abstract', '')}"
        evaluation_data = ai_manager.evaluate_paper_json(content_for_ai, model_type='pro')
        
        if not evaluation_data:
            tqdm.write(f"  >!> Η αξιολόγηση για το '{title[:50]}...' απέτυχε. Παραλείπεται.")
            continue

        # 3. Βρίσκουμε αν το άρθρο υπάρχει ήδη στη βάση (ψάχνοντας πρώτα με DOI, μετά με URL)
        existing_paper_id = db_manager.get_paper_id_by_doi(doi) or db_manager.get_paper_id_by_url(url)
        
        if existing_paper_id:
            # Στρατηγική "Upgrade": Αν υπάρχει, αναβαθμίζουμε την αξιολόγησή του
            db_manager.update_paper_evaluation(existing_paper_id, evaluation_data)
            db_manager.update_zotero_status_by_id(existing_paper_id, 1) # Διασφαλίζουμε ότι είναι 'in_zotero'
            tqdm.write(f"  > SUCCESS: Το άρθρο ID:{existing_paper_id} αναβαθμίστηκε με νέα Pro-level αξιολόγηση.")
        else:
            # Στρατηγική "Enrich": Αν δεν υπάρχει, το προσθέτουμε στη βάση με Pro-level αξιολόγηση
            db_manager.add_paper(paper_data, evaluation_data, in_zotero=1)
        
        upsert_count += 1
        time.sleep(2) # Rate limit για να σεβόμαστε τα όρια του Pro model

    # --- ΦΑΣΗ 4: ΤΕΛΙΚΗ ΑΝΑΦΟΡΑ ---
    print("\n" + "="*50)
    print("  Η ΔΙΑΔΙΚΑΣΙΑ ΤΟΥ ZOTERO BRIDGE ΟΛΟΚΛΗΡΩΘΗΚΕ")
    print(f"  > Συγχρονίστηκαν (Updated/Inserted): {upsert_count} άρθρα.")
    print("="*50)

if __name__ == "__main__":
    main()