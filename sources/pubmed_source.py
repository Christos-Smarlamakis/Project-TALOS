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
Module: pubmed_source.py (v2.0 - Genesis Update)
Project: TALOS v3.2

Description:
Η πλήρως αναβαθμισμένη έκδοση του "Πράκτορα" για το PubMed, εναρμονισμένη
με τις απαιτήσεις του "Operation Genesis".
- Ανακτά πλέον όλα τα κρίσιμα μεταδεδομένα (`doi`, `publication_year`).
- Χρησιμοποιεί μια ξεχωριστή μέθοδο `_format_paper` για καλύτερη οργάνωση.
- Επιστρέφει τα δεδομένα σε πλήρη συμμόρφωση με το νέο, τυποποιημένο λεξικό.
"""
from pymed import PubMed
from datetime import datetime, timedelta
from typing import List, Dict, Any

class PubMedSource:
    """
    Ένας "Πράκτορας" του TALOS που ειδικεύεται στην ανάκτηση δεδομένων από το PubMed.
    """
    def __init__(self, config: Dict[str, Any]):
        """
        Αρχικοποιεί τον πράκτορα του PubMed.
        """
        self.query = config.get("pubmed_query", "bio-inspired algorithms")
        self.days_to_search = config.get("days_to_search_daily", 1)
        self.max_results = config.get("max_results_config", {}).get("pubmed", 100)
        self.mailto = config.get("mailto", "a@b.com")
        if self.mailto == "a@b.com":
            print("WARNING: Using default email for PubMed. Please set 'mailto' in config.json.")
        
        self.pubmed = PubMed(tool="ProjectTALOS", email=self.mailto)
        print("INFO: PubMedSource (v2.0 - Genesis) αρχικοποιήθηκε.")

    def fetch_new_papers(self) -> List[Dict[str, Any]]:
        """
        Εκτελεί την αναζήτηση στο PubMed API και επιστρέφει τα νέα άρθρα.
        """
        print(f"-> Αναζήτηση στο PubMed...")
        
        # Το pymed επιτρέπει τη σύνθεση του query για φιλτράρισμα ημερομηνίας
        cutoff_date = (datetime.now() - timedelta(days=self.days_to_search)).strftime('%Y/%m/%d')
        full_query = f'({self.query}) AND ("{cutoff_date}"[Date - Publication] : "3000"[Date - Publication])'
        
        try:
            results = self.pubmed.query(full_query, max_results=self.max_results)
            papers = []
            for article in results:
                formatted_paper = self._format_paper(article)
                if formatted_paper:
                    papers.append(formatted_paper)
            
            print(f"   SUCCESS [PubMed]: Βρέθηκαν {len(papers)} νέα άρθρα.")
            return papers
            
        except Exception as e:
            print(f"   ERROR [PubMed]: Παρουσιάστηκε σφάλμα κατά την ανάκτηση: {e}")
            return []

    def _format_paper(self, article) -> Dict[str, Any]:
        """
        Μετατρέπει ένα αντικείμενο Article από το pymed στην τυποποιημένη μορφή του TALOS.
        """
        try:
            # Το pymed επιστρέφει μια λίστα από λεξικά για τους συγγραφείς
            authors_str = "N/A"
            if article.authors:
                authors_str = ", ".join([f"{a.get('lastname', '')}, {a.get('firstname', '')}".strip(', ') for a in article.authors])

            # --- ΝΕΕΣ ΠΡΟΣΘΗΚΕΣ ---
            doi = article.doi
            publication_year = article.publication_date.year if article.publication_date else None
            
            # Προτεραιότητα στο URL του DOI
            url = f"https://doi.org/{doi}" if doi else f"https://pubmed.ncbi.nlm.nih.gov/{article.pubmed_id}/"

            return {
                "doi": doi,
                "url": url,
                "title": article.title or "N/A",
                "authors_str": authors_str,
                "publication_year": publication_year,
                "abstract": article.abstract or "Δεν υπάρχει διαθέσιμη περίληψη.",
                "source": "PubMed"
            }
        except Exception as e:
            print(f"   WARNING [PubMed]: Αποτυχία μορφοποίησης ενός άρθρου: {e}")
            return None