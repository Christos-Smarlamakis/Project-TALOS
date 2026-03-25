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
Module: metadata_enricher.py (v1.0 - Project "APOLLO")
Project: TALOS v3.1

Description:
Ένα εργαλείο συντήρησης που "εμπλουτίζει" τις υπάρχουσες εγγραφές στη βάση
δεδομένων. Σαρώνει τη βάση για άρθρα με ελλιπή μεταδεδομένα (όπως έτος
δημοσίευσης ή DOI) και προσπαθεί να τα βρει χρησιμοποιώντας εξωτερικές πηγές
(π.χ., Semantic Scholar), συμπληρώνοντας τα κενά.
"""
import os
import sys
import json
import time
from tqdm import tqdm
import questionary

# Προσθέτουμε το root του project στο path για να βρει τα modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.database_manager import DatabaseManager
from sources.semantic_scholar_source import SemanticScholarSource

class MetadataEnricher:
    """
    Η κλάση που ενορχηστρώνει τη διαδικασία εμπλουτισμού των μεταδεδομένων.
    """
    def __init__(self, config: dict):
        """
        Αρχικοποιεί τον Enricher.

        Args:
            config (dict): Το λεξικό ρυθμίσεων του project.
        """
        self.db_manager = DatabaseManager()
        self.s2_source = SemanticScholarSource(config)
        print("INFO: Metadata Enricher 'APOLLO' (v1.0) initialized.")

    def find_papers_to_enrich(self) -> list:
        """
        Εντοπίζει τα άρθρα στη βάση δεδομένων που έχουν ελλιπή μεταδεδομένα.

        Returns:
            list: Μια λίστα από tuples, όπου κάθε tuple περιέχει το id και τον
                  τίτλο ενός άρθρου προς εμπλουτισμό.
        """
        print("INFO: Αναζήτηση για άρθρα με ελλιπή μεταδεδομένα (DOI ή Έτος)...")
        query = "SELECT id, title FROM papers WHERE doi IS NULL OR publication_year IS NULL"
        results = self.db_manager.execute_query(query, fetch_all=True)
        return results if results else []

    def update_paper_metadata(self, paper_id: int, new_data: dict):
        """
        Ενημερώνει μια συγκεκριμένη εγγραφή άρθρου με τα νέα μεταδεδομένα.

        Args:
            paper_id (int): Το ID του άρθρου προς ενημέρωση.
            new_data (dict): Ένα λεξικό που περιέχει τα νέα δεδομένα (π.χ.,
                             'doi', 'publication_year', 'authors_str').
        """
        sql = """
            UPDATE papers SET
                doi = COALESCE(?, doi),
                publication_year = COALESCE(?, publication_year),
                authors = COALESCE(?, authors),
                url = COALESCE(?, url)
            WHERE id = ?
        """
        params = (
            new_data.get('doi'),
            new_data.get('publication_year'),
            new_data.get('authors_str'),
            new_data.get('url'),
            paper_id
        )
        self.db_manager.execute_query(sql, params, commit=True)

    def run(self):
        """
        Εκτελεί την πλήρη ροή εργασίας του εμπλουτισμού.
        """
        papers_to_enrich = self.find_papers_to_enrich()

        if not papers_to_enrich:
            print("\nSUCCESS: Όλα τα άρθρα στη βάση φαίνεται να έχουν πλήρη μεταδεδομένα.")
            return

        print(f"Βρέθηκαν {len(papers_to_enrich)} άρθρα που μπορεί να χρειάζονται εμπλουτισμό.")
        if not questionary.confirm("Θέλετε να ξεκινήσει η διαδικασία αναζήτησης και ενημέρωσης;", default=True).ask():
            print("Η διαδικασία ακυρώθηκε από τον χρήστη.")
            return

        enriched_count = 0
        for paper_id, title in tqdm(papers_to_enrich, desc="Enriching Metadata"):
            if not title:
                continue

            # Κάνουμε αναζήτηση στον Semantic Scholar με βάση τον τίτλο
            search_results = self.s2_source.search_papers(title, limit=1)
            
            # Ελέγχουμε αν βρέθηκε αποτέλεσμα και αν ο τίτλος ταιριάζει ακριβώς
            # (για να αποφύγουμε την ενημέρωση με λάθος άρθρο)
            if search_results and search_results[0]['title'].lower() == title.lower():
                found_paper = search_results[0]
                
                # Ενημερώνουμε την εγγραφή στη βάση
                self.update_paper_metadata(paper_id, found_paper)
                tqdm.write(f"  -> SUCCESS: Εμπλουτίστηκε το άρθρο ID:{paper_id} ('{title[:40]}...')")
                enriched_count += 1
            else:
                tqdm.write(f"  -> INFO: Δεν βρέθηκε ακριβής αντιστοιχία για το ID:{paper_id} ('{title[:40]}...')")

            # Rate limit για να σεβόμαστε το API του Semantic Scholar
            time.sleep(1)

        print("\n" + "="*50)
        print("  Η ΔΙΑΔΙΚΑΣΙΑ ΕΜΠΛΟΥΤΙΣΜΟΥ ΟΛΟΚΛΗΡΩΘΗΚΕ")
        print(f"  > Εμπλουτίστηκαν επιτυχώς: {enriched_count} / {len(papers_to_enrich)} άρθρα.")
        print("="*50)


def load_configuration():
    """Φορτώνει τις ρυθμίσεις από το αρχείο config.json."""
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    config_path = os.path.join(project_root, 'config.json')
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"FATAL: Δεν ήταν δυνατή η φόρτωση του config.json. Σφάλμα: {e}")
        sys.exit(1)

if __name__ == "__main__":
    config = load_configuration()
    enricher = MetadataEnricher(config)
    enricher.run()
    input("\nΠατήστε Enter για έξοδο.")