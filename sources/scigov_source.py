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
Module: scigov_source.py (v2.0 - Genesis Update)
Project: TALOS v3.2

Description:
Η πλήρως αναβαθμισμένη έκδοση του "Πράκτορα" για το Science.gov, εναρμονισμένη
με τις απαιτήσεις του "Operation Genesis".
- Ανακτά πλέον όλα τα κρίσιμα μεταδεδομένα (`doi`, `publication_year`).
- Χρησιμοποιεί μια ξεχωριστή μέθοδο `_format_paper` για καλύτερη οργάνωση.
- Επιστρέφει τα δεδομένα σε πλήρη συμμόρφωση με το νέο, τυποποιημένο λεξικό.
"""
import requests
from typing import List, Dict, Any

class ScienceGovSource:
    """
    Ένας "Πράκτορας" του TALOS που ανακτά δεδομένα από το Science.gov API v2.
    """
    def __init__(self, config: Dict[str, Any]):
        """
        Αρχικοποιεί τον πράκτορα του Science.gov.
        """
        self.query = config.get("scigov_query", "unmanned systems")
        self.max_results = config.get("max_results_config", {}).get("scigov", 100)
        self.base_url = "https://api.science.gov/search/v2/records"
        print("INFO: ScienceGovSource (v2.0 - Genesis) αρχικοποιήθηκε.")

    def fetch_new_papers(self) -> List[Dict[str, Any]]:
        """
        Εκτελεί την αναζήτηση στο Science.gov API και επιστρέφει τα νέα άρθρα.
        Το API δεν υποστηρίζει φίλτρο ημερομηνίας, οπότε η ταξινόμηση γίνεται
        με βάση τη συνάφεια ή την ημερομηνία δημοσίευσης.
        """
        print(f"-> Αναζήτηση στο Science.gov...")
        
        params = {
            'q': self.query,
            'size': self.max_results,
            'sort': 'published_date:desc'
        }
        try:
            response = requests.get(self.base_url, params=params, timeout=20)
            response.raise_for_status()
            data = response.json()
            
            papers = []
            for record in data.get('results', []):
                formatted_paper = self._format_paper(record)
                if formatted_paper:
                    papers.append(formatted_paper)
                    
            print(f"   SUCCESS [Science.gov]: Βρέθηκαν {len(papers)} άρθρα.")
            return papers

        except requests.exceptions.RequestException as e:
            print(f"   ERROR [Science.gov]: Παρουσιάστηκε σφάλμα κατά την ανάκτηση: {e}")
            return []

    def _format_paper(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Μετατρέπει ένα αντικείμενο από το Science.gov API στην τυποποιημένη μορφή του TALOS.
        """
        try:
            authors_list = record.get('authors', [])
            authors_str = ", ".join([author['name'] for author in authors_list if 'name' in author])

            # --- ΝΕΕΣ ΠΡΟΣΘΗΚΕΣ ---
            doi = record.get("doi")
            url = f"https://doi.org/{doi}" if doi else record.get("doiLink", record.get("link", "#"))
            
            # Το έτος μπορεί να είναι σε διαφορετικά πεδία ανάλογα την πηγή
            publication_year = record.get("publication_year") or record.get("year")
            if publication_year and isinstance(publication_year, str) and publication_year.isdigit():
                publication_year = int(publication_year)
            elif not isinstance(publication_year, int):
                publication_year = None
            
            return {
                "doi": doi,
                "url": url,
                "title": record.get("title", "N/A"),
                "authors_str": authors_str if authors_str else "N/A",
                "publication_year": publication_year,
                "abstract": record.get("description", "Δεν υπάρχει διαθέσιμη περίληψη."),
                "source": "Science.gov"
            }
        except Exception as e:
            print(f"   WARNING [Science.gov]: Αποτυχία μορφοποίησης ενός άρθρου: {e}")
            return None