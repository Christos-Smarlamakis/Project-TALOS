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
Module: embedding_generator.py (v3.1 - Full Documentation & Harmonization)
Project: TALOS v2.21.0

Description:
Η τελική, πλήρως τεκμηριωμένη έκδοση του script δημιουργίας σημασιολογικών
embeddings. Αυτή η έκδοση είναι πλήρως εναρμονισμένη με τη νέα αρχιτεκτονική:
- Αξιοποιεί τον κεντρικό AIManager για τη δημιουργία των embeddings.
- Χρησιμοποιεί αποδοτική επεξεργασία κατά δόσεις (batch processing).
- Περιλαμβάνει στιβαρό χειρισμό σφαλμάτων και πλήρη ελληνική τεκμηρίωση.
"""
import os
import sys
import json
import time
import pickle
from tqdm import tqdm
import numpy as np

# Προσθέτουμε το root του project στο path για να βρει τα core modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.database_manager import DatabaseManager
from core.ai_manager import AIManager

# Ορίζουμε το μέγεθος της κάθε δόσης (batch) για τις κλήσεις στο API.
# Αυτό βοηθά στη διαχείριση της μνήμης και στον σεβασμό των rate limits.
BATCH_SIZE = 100 

def load_configuration():
    """
    Φορτώνει τις ρυθμίσεις από το αρχείο config.json.

    Returns:
        dict: Ένα λεξικό με τις ρυθμίσεις του project.
    """
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    config_path = os.path.join(project_root, 'config.json')
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"FATAL: Δεν ήταν δυνατή η φόρτωση του config.json. Σφάλμα: {e}")
        sys.exit(1)

def main():
    """
    Κύρια συνάρτηση που ενορχηστρώνει τη διαδικασία δημιουργίας embeddings:
    1. Αρχικοποιεί τα core modules.
    2. Βρίσκει τα άρθρα στη βάση που δεν έχουν embedding.
    3. Τα επεξεργάζεται σε δόσεις (batches).
    4. Για κάθε δόση, καλεί το AI για να δημιουργήσει τα embeddings.
    5. Αποθηκεύει τα νέα embeddings μαζικά στη βάση δεδομένων.
    """
    print("--- ΕΝΑΡΞΗ ΔΗΜΙΟΥΡΓΙΑΣ EMBEDDINGS (v3.1) ---")
    
    # --- ΦΑΣΗ 1: ΑΡΧΙΚΟΠΟΙΗΣΗ ---
    config = load_configuration()
    ai_manager = AIManager(config)
    db_manager = DatabaseManager()

    # --- ΦΑΣΗ 2: ΑΝΑΚΤΗΣΗ ΔΕΔΟΜΕΝΩΝ ---
    print("INFO: Ανάκτηση άρθρων που χρειάζονται embedding από τη βάση...")
    papers_to_embed = db_manager.get_papers_without_embedding()

    # Αν δεν βρεθούν άρθρα, δεν υπάρχει λόγος να συνεχίσουμε.
    if not papers_to_embed:
        print("INFO: Όλα τα άρθρα στη βάση έχουν ήδη embedding. Τερματισμός.")
        return

    print(f"Βρέθηκαν {len(papers_to_embed)} άρθρα για επεξεργασία.")
    
    # --- ΦΑΣΗ 3: ΕΠΕΞΕΡΓΑΣΙΑ ΣΕ BATCHES ---
    # Η `tqdm` δημιουργεί μια όμορφη μπάρα προόδου στο τερματικό.
    with tqdm(total=len(papers_to_embed), desc="Generating Embeddings") as pbar:
        # Διασχίζουμε τη λίστα των άρθρων σε βήματα μεγέθους BATCH_SIZE
        for i in range(0, len(papers_to_embed), BATCH_SIZE):
            # Παίρνουμε την τρέχουσα "δόση" (batch) των άρθρων
            batch = papers_to_embed[i:i + BATCH_SIZE]
            
            # Συνθέτουμε το κείμενο που θα σταλεί στο AI για κάθε άρθρο.
            # Η μορφή "Title: ... Abstract: ..." είναι καλή πρακτική για embeddings.
            texts_to_embed = [f"Title: {paper['title']}\nAbstract: {paper['abstract']}" for paper in batch]
            
            # --- ΚΕΝΤΡΙΚΗ ΛΟΓΙΚΗ: ΚΛΗΣΗ ΣΤΟ AI ---
            # Καλούμε την εξειδικευμένη μέθοδο του AIManager.
            embedding_vectors = ai_manager.generate_embeddings(texts_to_embed)
            
            # Στιβαρός έλεγχος σφαλμάτων: Ελέγχουμε αν το AI επέστρεψε κάτι
            # και αν ο αριθμός των vectors που επέστρεψε είναι ίσος με τον αριθμό
            # των κειμένων που στείλαμε.
            if not embedding_vectors or len(batch) != len(embedding_vectors):
                print(f"\nWARNING: Ασυμφωνία μεγέθους ή σφάλμα API για το batch index {i}. Παράλειψη αυτού του batch.")
                pbar.update(len(batch)) # Ενημερώνουμε την μπάρα προόδου ακόμα και σε αποτυχία
                time.sleep(1) # Μικρή παύση σε περίπτωση σφάλματος
                continue

            # --- ΠΡΟΕΤΟΙΜΑΣΙΑ ΓΙΑ ΑΠΟΘΗΚΕΥΣΗ ---
            updates = []
            for paper, vector in zip(batch, embedding_vectors):
                # Μετατρέπουμε το διάνυσμα (vector) σε μια σειρά από bytes (serialization)
                # χρησιμοποιώντας το pickle, ώστε να μπορεί να αποθηκευτεί σε πεδίο BLOB της βάσης.
                embedding_blob = pickle.dumps(np.array(vector))
                updates.append((embedding_blob, paper['id']))
            
            # --- ΑΠΟΘΗΚΕΥΣΗ ΣΤΗ ΒΑΣΗ ---
            # Εκτελούμε μία μόνο μαζική κλήση UPDATE για ολόκληρο το batch.
            # Αυτό είναι δραματικά πιο γρήγορο από το να κάνουμε UPDATE για κάθε άρθρο ξεχωριστά.
            db_manager.update_embeddings_batch(updates)
            
            # Ενημερώνουμε την μπάρα προόδου
            pbar.update(len(batch))
            
            # Κάνουμε μια παύση για να είμαστε "ευγενικοί" με το API και να αποφύγουμε
            # το rate limiting.
            time.sleep(2)

    print("\n--- Η ΔΗΜΙΟΥΡΓΙΑ EMBEDDINGS ΟΛΟΚΛΗΡΩΘΗΚΕ ---")

if __name__ == "__main__":
    main()