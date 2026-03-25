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
Module: upgrade_to_v4.7.py
Description: Εργαλείο μίας χρήσης για την αναβάθμιση της βάσης στην έκδοση v4.7.0 (HERMES).
"""
import sqlite3
import os
import shutil
from datetime import datetime

def upgrade_database():
    print("--- TALOS DB UPGRADE TOOL (v4.6 -> v4.7) ---")
    
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    db_path = os.path.join(project_root, "talos_research.db")
    backup_path = os.path.join(project_root, f"talos_research_backup_pre_v4.7_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db")

    if not os.path.exists(db_path):
        print("ERROR: Δεν βρέθηκε η βάση δεδομένων.")
        return

    try:
        print(f"Creating backup at: {backup_path}")
        shutil.copyfile(db_path, backup_path)
        print("Backup successful.")
    except Exception as e:
        print(f"FATAL: Backup failed: {e}")
        return

    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            print("Adding 'oa_pdf_url' column...")
            try:
                cursor.execute("ALTER TABLE papers ADD COLUMN oa_pdf_url TEXT;")
                print("SUCCESS: Column added.")
            except sqlite3.OperationalError as e:
                if "duplicate column" in str(e):
                    print("INFO: Column 'oa_pdf_url' already exists.")
                else: raise e
            conn.commit()
    except sqlite3.Error as e:
        print(f"FATAL Error: {e}")
        return

    print("\nUpgrade complete! Database is ready for Project HERMES.")

if __name__ == "__main__":
    upgrade_database()