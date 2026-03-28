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
Module: osti_source.py (v2.0 - Genesis Update)
Project: TALOS v3.2

Description:
Η πλήρως αναβαθμισμένη έκδοση του "Πράκτορα" για το OSTI.gov, εναρμονισμένη
με τις απαιτήσεις του "Operation Genesis".
- Ανακτά πλέον το κρίσιμο μεταδεδομένο: `publication_year`.
- Χρησιμοποιεί μια ξεχωριστή μέθοδο `_format_paper` για καλύτερη οργάνωση.
- Επιστρέφει τα δεδομένα σε πλήρη συμμόρφωση με το νέο, τυποποιημένο λεξικό.
"""
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Any

class OSTISource:
    """
    Ένας "Πράκτορας" του TALOS που ανακτά δεδομένα από το OSTI.gov API.
    """
    def __init__(self, config: Dict[str, Any]):
        """
        Αρχικοποιεί τον πράκτορα του OSTI.gov.
        """
        self.query = config.get("osti_query", "swarm intelligence")
        self.days_to_search = config.get("days_to_search_daily", 1)
        self.max_results = config.get("max_results_config", {}).get("osti", 100)
        self.base_url = "https://www.osti.gov/api/v1/records"
        print("INFO: OSTISource (v2.0 - Genesis) αρχικοποιήθηκε.")

    def fetch_new_papers(self) -> List[Dict[str, Any]]:
        """
        Εκτελεί την αναζήτηση στο OSTI.gov API και επιστρέφει τα νέα άρθρα.
        """
        print(f"-> Αναζήτηση στο OSTI.gov...")
        
        # Το API δέχεται ημερομηνίες σε format MM/DD/YYYY
        start_date = (datetime.now() - timedelta(days=self.days_to_search)).strftime('%m/%d/%Y')
        
        params = {
            'q': self.query,
            'size': self.max_results,
            'sort': 'publication_date desc',
            'publication_date_start': start_date
        }
        try:
            response = requests.get(self.base_url, params=params, timeout=20)
            response.raise_for_status()
            data = response.json()
            
            papers = []
            for record in data:
                formatted_paper = self._format_paper(record)
                if formatted_paper:
                    papers.append(formatted_paper)
            
            print(f"   SUCCESS [OSTI.gov]: Βρέθηκαν {len(papers)} νέα άρθρα.")
            return papers
            
        except requests.exceptions.RequestException as e:
            print(f"   ERROR [OSTI.gov]: Παρουσιάστηκε σφάλμα κατά την ανάκτηση: {e}")
            return []

    def _format_paper(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Μετατρέπει ένα αντικείμενο από το OSTI.gov API στην τυποποιημένη μορφή του TALOS.
        """
        try:
            # Το πεδίο 'authors' μπορεί να είναι string ή list, το χειριζόμαστε
            authors_data = record.get("authors", "N/A")
            if isinstance(authors_data, list):
                authors_str = ", ".join(authors_data)
            elif isinstance(authors_data, str):
                authors_str = authors_data
            else:
                authors_str = "N/A"

            doi_suffix = record.get("doi", "").replace("https://doi.org/", "")
            doi = doi_suffix if doi_suffix else None
            
            url = f"https://doi.org/{doi}" if doi else record.get("osti_url", "#")
            
            publication_year = None
            date_str = record.get("publication_date")
            if date_str:
                try:
                    # Η ημερομηνία είναι σε format YYYY-MM-DD
                    publication_year = datetime.strptime(date_str, '%Y-%m-%d').year
                except ValueError:
                    pass

            return {
                "doi": doi,
                "url": url,
                "title": record.get("title", "N/A"),
                "authors_str": authors_str,
                "publication_year": publication_year,
                "abstract": record.get("description", "Δεν υπάρχει διαθέσιμη περίληψη."),
                "source": "OSTI.gov"
            }
        except Exception as e:
            print(f"   WARNING [OSTI.gov]: Αποτυχία μορφοποίησης ενός άρθρου: {e}")
            return None