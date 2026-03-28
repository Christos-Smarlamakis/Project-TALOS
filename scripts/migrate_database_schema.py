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
Module: migrate_database_schema.py (v2.2 - Final Migration Fix)
Project: TALOS v2.21.0

Description:
Η τελική, διορθωμένη έκδοση του εργαλείου μετάβασης. Διορθώνει το σφάλμα
'AttributeError: 'sqlite3.Row' object has no attribute 'get'' μετατρέποντας
ρητά κάθε σειρά από τη βάση σε ένα λεξικό Python (dict) πριν προσπαθήσει
να διαβάσει τα δεδομένα, εξασφαλίζοντας πλήρη συμβατότητα και ανθεκτικότητα.
"""
import sys
import os
import sqlite3
import shutil
import re
from datetime import datetime
from tqdm import tqdm
import questionary

# Προσθέτουμε το root του project στο path για να βρει τα core modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.database_manager import DatabaseManager

def extract_from_old_analysis(analysis_text: str, field: str) -> str:
    """
    Χρησιμοποιεί regex για να εξάγει συγκεκριμένα πεδία από το παλιό,
    ακατέργαστο κείμενο του ai_analysis.
    """
    patterns = {
        'reasoning': r"2\.\s*Αιτιολόγηση:([\s\S]*?)(?:3\.\s*Πυρήνας|$)",
        'contribution': r"3\.\s*Πυρήνας Συνεισφοράς:([\s\S]*?)(?:4\.\s*Στρατηγική|$)",
        'utilization': r"4\.\s*Στρατηγική Αξιοποίηση:([\s\S]*?)(?:5\.\s*Προτεινόμενα|$)",
        'tags': r"5\.\s*Προτεινόμενα Tags \(Zotero\):([\s\S]*?)(?:6\.\s*Προτεινόμενος|$)",
        'folder': r"6\.\s*Προτεινόμενος Φάκελος \(Zotero\):([\s\S]*?)(?:7\.\s*Προτεινόμενο|$)",
        'channel': r"7\.\s*Προτεινόμενο Κανάλι Discord:([\s\S]*)$"
    }
    if not isinstance(analysis_text, str) or field not in patterns:
        return ""
    
    match = re.search(patterns[field], analysis_text, re.IGNORECASE)
    if match:
        return match.group(1).strip().replace('*', '')
    return ""

def migrate_schema():
    """
    Κύρια συνάρτηση που εκτελεί την πλήρη, στιβαρή διαδικασία μετάβασης.
    """
    print("--- TALOS DB MIGRATION TOOL (v2.2 - Final Fix) ---")
    
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    db_path = os.path.join(project_root, "talos_research.db")
    backup_path = os.path.join(project_root, f"talos_research_backup_pre_v2.21_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db")

    if not os.path.exists(db_path):
        print("ERROR: Database 'talos_research.db' not found. Nothing to migrate.")
        return

    if not questionary.confirm(f"This script will permanently modify '{db_path}'. A backup will be created at '{backup_path}'. Continue?", default=False).ask():
        print("Migration cancelled by user.")
        return

    # --- ΒΗΜΑ 1: Δημιουργία Backup ---
    try:
        print(f"\n[1/5] Creating backup...")
        shutil.copyfile(db_path, backup_path)
        print("SUCCESS: Backup complete.")
    except Exception as e:
        print(f"FATAL: Backup failed: {e}. Aborting.")
        return

    try:
        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # --- ΒΗΜΑ 2: Μετονομασία Παλιού Πίνακα ---
            print("\n[2/5] Preparing old data...")
            cursor.execute("ALTER TABLE papers RENAME TO papers_old;")
            print("SUCCESS: Old table renamed to 'papers_old'.")

            # --- ΒΗΜΑ 3: Δημιουργία Νέου, Σωστού Πίνακα ---
            print("\n[3/5] Creating new table with the correct schema...")
            db_manager_instance = DatabaseManager()
            db_manager_instance.create_table()
            
            # --- ΒΗΜΑ 4: Μεταφορά Δεδομένων ---
            print("\n[4/5] Migrating and transforming data...")
            cursor.execute("SELECT * FROM papers_old")
            all_old_papers_rows = cursor.fetchall()
            
            data_to_insert = []
            for paper_row in tqdm(all_old_papers_rows, desc="Migrating records"):
                # **Η ΔΙΟΡΘΩΣΗ ΕΙΝΑΙ ΕΔΩ**: Μετατρέπουμε το sqlite3.Row σε dict
                paper = dict(paper_row)
                
                url = paper.get('url', '')
                doi = url.split('doi.org/')[-1] if url and 'doi.org/' in url else None
                analysis_text = paper.get('ai_analysis', '')
                
                data_to_insert.append((
                    paper.get('id'), doi, url, paper.get('title'), paper.get('authors'),
                    paper.get('publication_year'), paper.get('abstract'), paper.get('source'),
                    paper.get('strategic_score', 0), paper.get('tactical_score', 0),
                    paper.get('simulation_score', 0), paper.get('overall_score', 0.0),
                    extract_from_old_analysis(analysis_text, 'reasoning'),
                    extract_from_old_analysis(analysis_text, 'contribution'),
                    extract_from_old_analysis(analysis_text, 'utilization'),
                    extract_from_old_analysis(analysis_text, 'tags'),
                    extract_from_old_analysis(analysis_text, 'folder'),
                    extract_from_old_analysis(analysis_text, 'channel'),
                    paper.get('in_zotero', 0), paper.get('embedding'),
                    paper.get('processed_date'), paper.get('evaluation_date')
                ))
            
            insert_sql = """
                INSERT OR IGNORE INTO papers (
                    id, doi, url, title, authors, publication_year, abstract, source,
                    strategic_score, tactical_score, playground_score, overall_score,
                    evaluation_reasoning, evaluation_contribution, evaluation_utilization,
                    suggested_tags, suggested_folder, suggested_discord_channel,
                    in_zotero, embedding, processed_at, last_evaluated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            cursor.executemany(insert_sql, data_to_insert)
            print(f"SUCCESS: {cursor.rowcount}/{len(all_old_papers_rows)} records migrated (duplicates were ignored).")

            # --- ΒΗΜΑ 5: Καθαρισμός ---
            print("\n[5/5] Cleaning up temporary table...")
            cursor.execute("DROP TABLE papers_old;")
            print("SUCCESS: Temporary table dropped.")
            
            conn.commit()

    except sqlite3.Error as e:
        print(f"\nFATAL: A database error occurred: {e}")
        print("INFO: The database might be in an unstable state. Please restore from backup.")
        return

    print("\n\nDatabase migration completed successfully!")
    print("INFO: You can now use the new TALOS v2.21.0 scripts.")

if __name__ == "__main__":
    migrate_schema()
    input("\nPress Enter to exit.")