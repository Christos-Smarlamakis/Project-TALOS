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
Module: recalculate_scores.py (v2.0 - Recalibration Tool)
Project: TALOS v2.21.0

Description:
Ένα σύγχρονο εργαλείο συντήρησης, πλήρως εναρμονισμένο με τη νέα αρχιτεκτονική.
Αντί να κάνει parsing, αυτό το script διαβάζει τα ήδη αποθηκευμένα, δομημένα
scores (tactical, strategic, playground) από τη βάση δεδομένων και
επανα-υπολογίζει το 'overall_score' για κάθε άρθρο.

Είναι εξαιρετικά χρήσιμο σε περιπτώσεις που αλλάζει η κεντρική φόρμουλα
στάθμισης του overall score, διασφαλίζοντας ότι ολόκληρη η βάση δεδομένων
μπορεί να επανα-βαθμονομηθεί γρήγορα και με συνέπεια.
"""
import sys
import os
import sqlite3
from tqdm import tqdm
import questionary

# Προσθέτουμε το root του project στο path για να βρει τα core modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.database_manager import DatabaseManager

def recalculate_database_scores():
    """
    Ενορχηστρώνει τη διαδικασία επανα-υπολογισμού των overall scores.
    1. Συνδέεται στη βάση και ανακτά όλα τα άρθρα.
    2. Για κάθε άρθρο, χρησιμοποιεί την κεντρική λογική του DatabaseManager
       για να υπολογίσει το νέο overall_score.
    3. Εκτελεί μια μαζική ενημέρωση (bulk update) για μέγιστη απόδοση.
    """
    print("--- ΕΝΑΡΞΗ ΕΠΑΝΑ-ΒΑΘΜΟΝΟΜΗΣΗΣ ΒΑΣΗΣ (v2.0) ---")
    
    # --- ΦΑΣΗ 1: ΑΡΧΙΚΟΠΟΙΗΣΗ & ΑΝΑΚΤΗΣΗ ΔΕΔΟΜΕΝΩΝ ---
    
    # Χρησιμοποιούμε τον DatabaseManager για να έχουμε πρόσβαση στην κεντρική
    # λογική υπολογισμού του overall score.
    db_manager = DatabaseManager()

    try:
        # Συνδεόμαστε απευθείας στη βάση για να διαβάσουμε τα δεδομένα
        with sqlite3.connect(db_manager.db_path) as conn:
            # Χρησιμοποιούμε Row Factory για να δουλεύουμε με λεξικά, που είναι πιο εύκολο
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            print("Ανάκτηση όλων των άρθρων από τη βάση δεδομένων...")
            # Διαβάζουμε μόνο τα πεδία που χρειαζόμαστε: το ID και τα τρία επιμέρους scores.
            cursor.execute("SELECT id, tactical_score, strategic_score, playground_score FROM papers")
            all_papers = cursor.fetchall()

    except sqlite3.Error as e:
        print(f"FATAL: Αποτυχία σύνδεσης ή ανάγνωσης από τη βάση. Σφάλμα: {e}")
        return

    if not all_papers:
        print("Η βάση δεδομένων είναι άδεια. Τερματισμός.")
        return

    print(f"Βρέθηκαν {len(all_papers)} άρθρα. Έναρξη επανα-υπολογισμού...")
    
    # --- ΦΑΣΗ 2: ΥΠΟΛΟΓΙΣΜΟΣ & ΠΡΟΕΤΟΙΜΑΣΙΑ ΓΙΑ UPDATE ---
    
    updates_to_perform = []
    
    # Χρησιμοποιούμε tqdm για μια όμορφη μπάρα προόδου
    for paper in tqdm(all_papers, desc="Recalculating Scores"):
        # Παίρνουμε τα υπάρχοντα scores από το αντικείμενο paper
        scores_dict = {
            'tactical': paper['tactical_score'],
            'strategic': paper['strategic_score'],
            'playground': paper['playground_score']
        }
        
        # Καλούμε την κεντρική μέθοδο του db_manager για να υπολογίσουμε το νέο score.
        # Αυτό διασφαλίζει ότι αν αλλάξει η φόρμουλα εκεί, θα αλλάξει και εδώ.
        new_overall_score = db_manager._calculate_overall_score(scores_dict)
        
        # Προσθέτουμε το νέο score και το ID του άρθρου σε μια λίστα
        # για τη μαζική ενημέρωση.
        updates_to_perform.append((
            new_overall_score,
            paper['id']
        ))

    # --- ΦΑΣΗ 3: ΕΠΙΒΕΒΑΙΩΣΗ & ΜΑΖΙΚΗ ΕΝΗΜΕΡΩΣΗ ---
    
    print(f"\nΠροετοιμασία για μαζική ενημέρωση {len(updates_to_perform)} εγγραφών.")
    
    if not questionary.confirm("Είστε σίγουροι ότι θέλετε να ενημερώσετε τα overall scores για ΟΛΑ τα άρθρα;", default=False).ask():
        print("Η διαδικασία ακυρώθηκε από τον χρήστη.")
        return

    try:
        with sqlite3.connect(db_manager.db_path) as conn:
            cursor = conn.cursor()
            # Το query ενημερώνει ΜΟΝΟ το overall_score
            update_query = "UPDATE papers SET overall_score = ? WHERE id = ?"
            # Η executemany είναι εξαιρετικά γρήγορη για μαζικές ενημερώσεις
            cursor.executemany(update_query, updates_to_perform)
            conn.commit()
            print(f"SUCCESS: Η βάση δεδομένων ενημερώθηκε με επιτυχία για {cursor.rowcount} άρθρα.")
    except sqlite3.Error as e:
        print(f"ERROR: Αποτυχία μαζικής ενημέρωσης. Αιτία: {e}")
    
    print("\nΗ διαδικασία επανα-βαθμονόμησης ολοκληρώθηκε.")

if __name__ == "__main__":
    recalculate_database_scores()
    input("\nΠατήστε Enter για έξοδο.")