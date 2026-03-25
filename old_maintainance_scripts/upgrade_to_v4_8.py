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
Module: upgrade_to_v4_8.py
Description: Εργαλείο μίας χρήσης για την αναβάθμιση της βάσης στην έκδοση v4.8.0 
             (The "Enrichment & Scientometrics" Update).
             
Χαρακτηριστικά:
- Δημιουργεί Backup της βάσης δεδομένων.
- Προσθέτει τις νέες στήλες για το Data Enrichment (OpenAlex, PubMed, OA Status).
- Προσθέτει τη στήλη ελέγχου enrichment_status.
"""
import sqlite3
import os
import shutil
import sys
import json
from datetime import datetime

# Προσπάθεια εύρεσης του Project Root
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

def get_active_db_path():
    """
    Εντοπίζει τη σωστή βάση δεδομένων ελέγχοντας τα Profiles.
    """
    # 1. Έλεγχος για το config.json για να δούμε το active profile
    config_path = os.path.join(project_root, 'config.json')
    active_profile = "default"
    
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                active_profile = config.get('active_profile', 'default')
        except:
            pass

    # 2. Κατασκευή του path με βάση το profile
    profile_db = os.path.join(project_root, '_profiles', active_profile, 'talos_research.db')
    root_db = os.path.join(project_root, 'talos_research.db')

    # 3. Επιστροφή του path που υπάρχει
    if os.path.exists(profile_db):
        return profile_db, f"Profile: {active_profile}"
    elif os.path.exists(root_db):
        return root_db, "Root (Legacy)"
    else:
        return None, None

def upgrade_database():
    print("\n--- TALOS DB UPGRADE TOOL (v4.7 -> v4.8.0) ---")
    print("--- The Enrichment & Scientometrics Update ---\n")
    
    db_path, context = get_active_db_path()

    if not db_path:
        print("❌ ERROR: Δεν βρέθηκε καμία βάση δεδομένων (ούτε σε Profile, ούτε στο Root).")
        return

    print(f"📍 Target Database: {db_path} ({context})")

    # --- 1. BACKUP ---
    backup_filename = f"talos_backup_pre_v4.8_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    backup_path = os.path.join(os.path.dirname(db_path), backup_filename)

    try:
        print(f"📦 Creating backup...")
        shutil.copyfile(db_path, backup_path)
        print(f"✅ Backup successful: {backup_filename}")
    except Exception as e:
        print(f"❌ FATAL: Backup failed: {e}")
        print("Aborting upgrade to prevent data loss.")
        return

    # --- 2. MIGRATION ---
    new_columns = {
        "openalex_id": "TEXT",
        "pmid": "TEXT",
        "pmcid": "TEXT",
        "oa_status": "TEXT",
        "journal_issn": "TEXT",
        "publisher": "TEXT",
        "oa_pdf_url": "TEXT", # Ελέγχουμε ξανά μήπως λείπει από v4.7
        "enrichment_status": "INTEGER DEFAULT 0"
    }

    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # Παίρνουμε τις υπάρχουσες στήλες για να μην πετάει errors
            cursor.execute("PRAGMA table_info(papers)")
            existing_cols = [row[1] for row in cursor.fetchall()]
            
            print("\n🔧 Applying Schema Changes...")
            
            added_count = 0
            for col_name, col_type in new_columns.items():
                if col_name not in existing_cols:
                    try:
                        print(f"   + Adding column: {col_name} ({col_type})...")
                        cursor.execute(f"ALTER TABLE papers ADD COLUMN {col_name} {col_type};")
                        added_count += 1
                    except sqlite3.OperationalError as e:
                        print(f"   ⚠️ Error adding {col_name}: {e}")
                else:
                    print(f"   - Column '{col_name}' already exists. Skipping.")
            
            conn.commit()
            
            if added_count > 0:
                print(f"\n✅ SUCCESS: Added {added_count} new columns.")
            else:
                print("\n✨ Database is already up to date.")

    except sqlite3.Error as e:
        print(f"\n❌ FATAL DATABASE ERROR: {e}")
        return

    print("\n🚀 Upgrade complete! Database is ready for Data Enrichment.")

if __name__ == "__main__":
    upgrade_database()