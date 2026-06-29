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
Module: metadata_enricher.py (v2.0 - Multi-Source Fallback)
Project: TALOS v4.8.5

Description:
Ένα εργαλείο συντήρησης που "εμπλουτίζει" τις υπάρχουσες εγγραφές στη βάση
δεδομένων. Σαρώνει τη βάση για άρθρα με ελλιπή μεταδεδομένα (όπως έτος
δημοσίευσης ή DOI) και προσπαθεί να τα βρει χρησιμοποιώντας πολλαπλές
εξωτερικές πηγές με fallback chain:

  OpenAlex → Crossref → DBLP → Semantic Scholar

Κάθε πηγή δοκιμάζεται με τη σειρά — αν αποτύχει ή δεν βρει match,
προχωράμε στην επόμενη. Οι OpenAlex, Crossref, DBLP είναι δωρεάν
και δεν χρειάζονται API keys.
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
from sources.openalex_source import OpenAlexSource
from sources.crossref_source import CrossrefSource
from sources.dblp_source import DBLPSource
from sources.semantic_scholar_source import SemanticScholarSource

class MetadataEnricher:
    """
    Η κλάση που ενορχηστρώνει τη διαδικασία εμπλουτισμού των μεταδεδομένων.
    v2.0: Multi-source fallback chain (OpenAlex → Crossref → DBLP → S2).
    """
    def __init__(self, config: dict):
        """
        Αρχικοποιεί τον Enricher με πολλαπλές πηγές.

        Args:
            config (dict): Το λεξικό ρυθμίσεων του project.
        """
        self.db_manager = DatabaseManager()
        self.sources = [
            ("OpenAlex", OpenAlexSource(config)),
            ("Crossref", CrossrefSource(config)),
            ("DBLP", DBLPSource(config)),
        ]
        # Only include Semantic Scholar if API key is available
        s2_source = SemanticScholarSource(config)
        if s2_source.api_key:
            self.sources.append(("Semantic Scholar", s2_source))
        else:
            print("INFO: Semantic Scholar skipped (no API key). Using OpenAlex + Crossref + DBLP.")
        print("INFO: Metadata Enricher 'APOLLO' (v2.0 - Multi-Source) initialized.")

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

    def _search_with_fallback(self, query: str) -> dict:
        """
        Δοκιμάζει όλες τις πηγές με τη σειρά.
        Επιστρέφει το πρώτο αποτέλεσμα που ταιριάζει ακριβώς (case-insensitive title match).

        Args:
            query: truncated title (max 100 chars)

        Returns:
            dict ή None αν καμία πηγή δεν βρήκε ακριβές match.
        """
        for source_name, source in self.sources:
            try:
                search_results = source.search_papers(query, limit=3)
                if search_results:
                    # Έλεγχος για case-insensitive title match
                    for paper in search_results:
                        if paper.get('title', '').strip().lower() == query.strip().lower():
                            return paper
            except Exception:
                continue
        return None

    def run(self):
        """
        Εκτελεί την πλήρη ροή εργασίας του εμπλουτισμού με multi-source fallback.
        """
        papers_to_enrich = self.find_papers_to_enrich()

        if not papers_to_enrich:
            print("\nSUCCESS: Όλα τα άρθρα στη βάση φαίνεται να έχουν πλήρη μεταδεδομένα.")
            return

        print(f"Βρέθηκαν {len(papers_to_enrich)} άρθρα που μπορεί να χρειάζονται εμπλουτισμό.")
        print("Πηγές (fallback chain): OpenAlex → Crossref → DBLP → Semantic Scholar")
        if not questionary.confirm("Θέλετε να ξεκινήσει η διαδικασία αναζήτησης και ενημέρωσης;", default=True).ask():
            print("Η διαδικασία ακυρώθηκε από τον χρήστη.")
            return

        enriched_count = 0
        stats = {"OpenAlex": 0, "Crossref": 0, "DBLP": 0, "Semantic Scholar": 0}

        for paper_id, title in tqdm(papers_to_enrich, desc="Enriching Metadata"):
            if not title:
                continue

            # Truncate query to avoid 403 errors from overly long URLs
            query = title[:100]

            # Try each source in fallback order
            found = False
            for source_name, source in self.sources:
                try:
                    search_results = source.search_papers(query, limit=3)
                    if search_results:
                        # Check for case-insensitive exact title match
                        for paper in search_results:
                            if paper.get('title', '').strip().lower() == title.strip().lower():
                                found_paper = paper
                                self.update_paper_metadata(paper_id, found_paper)
                                tqdm.write(f"  -> [{source_name}] Εμπλουτίστηκε ID:{paper_id} ('{title[:40]}...')")
                                enriched_count += 1
                                stats[source_name] += 1
                                found = True
                                break
                    if found:
                        break
                except Exception:
                    continue

            if not found:
                tqdm.write(f"  -> INFO: Δεν βρέθηκε αντιστοιχία για ID:{paper_id} ('{title[:40]}...')")

            # Rate limit — 1 δευτερόλεπτο ανά paper
            time.sleep(1)

        print("\n" + "="*50)
        print("  Η ΔΙΑΔΙΚΑΣΙΑ ΕΜΠΛΟΥΤΙΣΜΟΥ ΟΛΟΚΛΗΡΩΘΗΚΕ")
        print(f"  > Εμπλουτίστηκαν επιτυχώς: {enriched_count} / {len(papers_to_enrich)} άρθρα.")
        print("  > Ανά πηγή:")
        for src, cnt in stats.items():
            if cnt > 0:
                print(f"      - {src}: {cnt}")
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