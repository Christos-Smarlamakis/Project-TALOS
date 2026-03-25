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
Module: fix_column_order.py
Description: Εργαλείο τακτοποίησης της σειράς των στηλών στη βάση δεδομένων.
Διορθώνει το θέμα όπου το 'operational_score' εμφανίζεται στο τέλος.
"""
import sqlite3
import os
import shutil
from datetime import datetime

def fix_order():
    print("--- TALOS DB COLUMN REORDERING TOOL ---")
    
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    db_path = os.path.join(project_root, "talos_research.db")
    backup_path = os.path.join(project_root, f"talos_research_backup_reorder_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db")

    if not os.path.exists(db_path):
        print("ERROR: Δεν βρέθηκε η βάση δεδομένων.")
        return

    # 1. Backup
    try:
        print(f"Creating backup at: {backup_path}")
        shutil.copyfile(db_path, backup_path)
    except Exception as e:
        print(f"FATAL: Backup failed: {e}")
        return

    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # 2. Rename current table
            print("Renaming current table...")
            cursor.execute("ALTER TABLE papers RENAME TO papers_temp;")

            # 3. Create new table with CORRECT ORDER
            print("Creating new table with correct column order...")
            create_sql = '''
            CREATE TABLE papers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                doi TEXT UNIQUE,
                url TEXT,
                title TEXT,
                authors TEXT,
                publication_year INTEGER,
                abstract TEXT,
                source TEXT,
                
                -- SCORES IN CORRECT ORDER --
                strategic_score INTEGER DEFAULT 0,
                operational_score INTEGER DEFAULT 0,
                tactical_score INTEGER DEFAULT 0,
                playground_score INTEGER DEFAULT 0,
                overall_score REAL DEFAULT 0.0,
                
                evaluation_reasoning TEXT,
                evaluation_contribution TEXT,
                evaluation_utilization TEXT,
                suggested_tags TEXT,
                suggested_folder TEXT,
                suggested_discord_channel TEXT,
                in_zotero INTEGER DEFAULT 0,
                embedding BLOB,
                processed_at DATE,
                last_evaluated_at DATETIME
            )
            '''
            cursor.execute(create_sql)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_papers_url ON papers(url);")

            # 4. Copy data mapping columns correctly
            print("Copying data to new structure...")
            # Επιλέγουμε ρητά τις στήλες από τον παλιό πίνακα για να είμαστε σίγουροι
            # ότι θα μπουν στη σωστή θέση στον νέο πίνακα.
            insert_sql = """
            INSERT INTO papers (
                id, doi, url, title, authors, publication_year, abstract, source,
                strategic_score, operational_score, tactical_score, playground_score, overall_score,
                evaluation_reasoning, evaluation_contribution, evaluation_utilization,
                suggested_tags, suggested_folder, suggested_discord_channel,
                in_zotero, embedding, processed_at, last_evaluated_at
            )
            SELECT 
                id, doi, url, title, authors, publication_year, abstract, source,
                strategic_score, operational_score, tactical_score, playground_score, overall_score,
                evaluation_reasoning, evaluation_contribution, evaluation_utilization,
                suggested_tags, suggested_folder, suggested_discord_channel,
                in_zotero, embedding, processed_at, last_evaluated_at
            FROM papers_temp
            """
            cursor.execute(insert_sql)
            
            # 5. Cleanup
            print("Dropping temporary table...")
            cursor.execute("DROP TABLE papers_temp;")
            
            conn.commit()
            print("\nSUCCESS: Η βάση δεδομένων τακτοποιήθηκε! Οι στήλες είναι στη σωστή σειρά.")

    except sqlite3.Error as e:
        print(f"\nFATAL Error: {e}")
        print("Η βάση μπορεί να είναι σε ασταθή κατάσταση. Επαναφέρετε το backup.")

if __name__ == "__main__":
    fix_order()