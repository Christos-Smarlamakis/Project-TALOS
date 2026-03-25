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
# upgrade_database.py (v3.2 - Embedding Column)
import sqlite3
import os

DB_FILENAME = "talos_research.db"

def upgrade():
    """
    Αναβαθμίζει το σχήμα της βάσης δεδομένων, προσθέτοντας νέες στήλες
    καθώς το project εξελίσσεται, χωρίς να χάνονται δεδομένα.
    """
    print(f"Έλεγχος για αναβάθμιση της βάσης '{DB_FILENAME}'...")
    
    project_root = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(project_root, DB_FILENAME)

    if not os.path.exists(db_path):
        print(f"Σφάλμα: Το αρχείο '{db_path}' δεν βρέθηκε. Τρέξτε πρώτα ένα script που δημιουργεί τη βάση.")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Παίρνουμε τις υπάρχουσες στήλες για να αποφύγουμε σφάλματα
        cursor.execute("PRAGMA table_info(papers)")
        existing_columns = [row[1] for row in cursor.fetchall()]
        
        # --- ΛΟΓΙΚΗ ΑΝΑΒΑΘΜΙΣΗΣ ---
        
        # Προσθήκη στήλης in_zotero (από την v2.15.1)
        if 'in_zotero' not in existing_columns:
            cursor.execute("ALTER TABLE papers ADD COLUMN in_zotero INTEGER DEFAULT 0")
            print("INFO: Η στήλη 'in_zotero' προστέθηκε με επιτυχία.")
        else:
            print("INFO: Η στήλη 'in_zotero' υπάρχει ήδη.")
            
        # Προσθήκη στήλης embedding (για την v2.15.3)
        if 'embedding' not in existing_columns:
            # Ο τύπος BLOB (Binary Large Object) είναι ιδανικός για αποθήκευση binary data,
            # όπως ένα serialized embedding vector.
            cursor.execute("ALTER TABLE papers ADD COLUMN embedding BLOB")
            print("ΕΠΙΤΥΧΙΑ: Η στήλη 'embedding' προστέθηκε με επιτυχία.")
        else:
            print("INFO: Η στήλη 'embedding' υπάρχει ήδη.")

        conn.commit()
        print("\nΗ διαδικασία αναβάθμισης του σχήματος ολοκληρώθηκε.")

    except sqlite3.Error as e:
        print(f"Παρουσιάστηκε σφάλμα κατά την αναβάθμιση: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    upgrade()
    input("\nΠατήστε Enter για έξοδο.")