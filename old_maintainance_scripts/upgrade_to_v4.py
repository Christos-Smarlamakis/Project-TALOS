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
Module: upgrade_to_v4.py
Description: Εργαλείο μίας χρήσης για την αναβάθμιση της βάσης στην έκδοση v4.0 (Quad-Layer).
"""
import sqlite3
import shutil
import os
from datetime import datetime

def upgrade_database():
    print("--- TALOS DB UPGRADE TOOL (v3.x -> v4.0) ---")
    
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    db_path = os.path.join(project_root, "talos_research.db")
    backup_path = os.path.join(project_root, f"talos_research_backup_pre_v4_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db")

    if not os.path.exists(db_path):
        print("ERROR: Δεν βρέθηκε η βάση δεδομένων.")
        return

    # 1. Backup
    try:
        print(f"Creating backup at: {backup_path}")
        shutil.copyfile(db_path, backup_path)
        print("Backup successful.")
    except Exception as e:
        print(f"FATAL: Backup failed: {e}")
        return

    # 2. Alter Table
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            print("Adding 'operational_score' column...")
            try:
                cursor.execute("ALTER TABLE papers ADD COLUMN operational_score INTEGER DEFAULT 0;")
                print("SUCCESS: Column added.")
            except sqlite3.OperationalError as e:
                if "duplicate column" in str(e):
                    print("INFO: Column 'operational_score' already exists.")
                else:
                    raise e
            
            # Reset evaluation date to force re-evaluation
            print("Resetting evaluation dates to force re-calculation...")
            # Θέτουμε το last_evaluated_at σε NULL για να τα "πιάσει" το reevaluate script
            cursor.execute("UPDATE papers SET last_evaluated_at = NULL")
            print("SUCCESS: Evaluation dates reset.")
            conn.commit()

    except sqlite3.Error as e:
        print(f"FATAL Error: {e}")
        return

    print("\nUpgrade complete! You can now run 'reevaluate_database.py'.")

if __name__ == "__main__":
    upgrade_database()