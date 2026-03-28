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
Module: crossref_source.py (v2.0 - Genesis Update)
Project: TALOS v3.2

Description:
Η πλήρως αναβαθμισμένη έκδοση του "Πράκτορα" για το Crossref, εναρμονισμένη
με τις απαιτήσεις του "Operation Genesis".
- Ανακτά πλέον τα κρίσιμα μεταδεδομένα: `doi` και `publication_year`.
- Χρησιμοποιεί μια ξεχωριστή μέθοδο `_format_paper` για καλύτερη οργάνωση
  και αξιόπιστη εξαγωγή δεδομένων από την πολύπλοκη απάντηση του API.
- Επιστρέφει τα δεδομένα σε πλήρη συμμόρφωση με το νέο, τυποποιημένο λεξικό.
"""
import requests
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any

class CrossrefSource:
    """
    Ένας "Πράκτορας" του TALOS που ειδικεύεται στην ανάκτηση δεδομένων
    από το Crossref API.
    """
    def __init__(self, config: Dict[str, Any]):
        """
        Αρχικοποιεί τον πράκτορα του Crossref.
        """
        self.query = config.get("crossref_query", "swarm intelligence")
        self.days_to_search = config.get("days_to_search_daily", 1)
        self.total_max_results = config.get("max_results_config", {}).get("crossref", 100)
        self.mailto = config.get("mailto", "user@example.com")
        self.base_url = "https://api.crossref.org/works"
        print("INFO: CrossrefSource (v2.0 - Genesis) αρχικοποιήθηκε.")

    def fetch_new_papers(self) -> List[Dict[str, Any]]:
        """
        Εκτελεί την αναζήτηση στο Crossref API και επιστρέφει τα νέα άρθρα.
        """
        print(f"-> Αναζήτηση στο Crossref...")
        all_papers = []
        offset = 0
        page_size = 100

        cutoff_date = (datetime.now().date() - timedelta(days=self.days_to_search))
        date_filter = f"from-pub-date:{cutoff_date.strftime('%Y-%m-%d')}"

        while len(all_papers) < self.total_max_results:
            params = {
                "query.bibliographic": self.query,
                "rows": page_size,
                "offset": offset,
                "sort": "published",
                "order": "desc",
                "filter": date_filter,
                "mailto": self.mailto
            }
            try:
                response = requests.get(self.base_url, params=params, timeout=20)
                if response.status_code == 429:
                    print("   WARNING [Crossref]: Rate limit. Αναμονή 5 δευτερολέπτων...")
                    time.sleep(5)
                    continue
                
                response.raise_for_status()
                data = response.json()
                items = data.get('message', {}).get('items', [])

                if not items:
                    break

                for item in items:
                    formatted_paper = self._format_paper(item)
                    if formatted_paper:
                        all_papers.append(formatted_paper)
                    
                    if len(all_papers) >= self.total_max_results:
                        break
                
                if len(all_papers) >= self.total_max_results or len(items) < page_size:
                    break

                offset += page_size
                time.sleep(1)

            except requests.exceptions.RequestException as e:
                print(f"   ERROR [Crossref]: Παρουσιάστηκε σφάλμα κατά την ανάκτηση: {e}")
                break

        print(f"   SUCCESS [Crossref]: Βρέθηκαν {len(all_papers)} νέα άρθρα.")
        return all_papers

    def _format_paper(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """
        Μετατρέπει ένα αντικείμενο από το Crossref API στην τυποποιημένη μορφή του TALOS.
        """
        try:
            # Ο τίτλος είναι μια λίστα, παίρνουμε το πρώτο στοιχείο.
            title = item.get("title", ["N/A"])[0]
            
            # Συνθέτουμε τη λίστα των συγγραφέων.
            authors_list = item.get('author', [])
            authors_str = ", ".join([f"{a.get('given', '')} {a.get('family', '')}".strip() for a in authors_list])
            
            # Το Crossref δεν παρέχει πάντα περίληψη.
            abstract = item.get("abstract", "Το Crossref δεν παρέχει πάντα περίληψη.")
            # Καθαρίζουμε τυχόν HTML tags από την περίληψη.
            abstract = abstract.replace('<jats:p>', '').replace('</jats:p>', '').replace('\n', ' ')

            # --- ΝΕΕΣ ΠΡΟΣΘΗΚΕΣ ---
            doi = item.get("DOI")
            
            publication_year = None
            date_parts = item.get("published", {}).get("date-parts", [[None]])[0]
            if date_parts and date_parts[0] is not None:
                publication_year = int(date_parts[0])

            # Κατασκευάζουμε το URL. Προτεραιότητα στο DOI.
            url = f"https://doi.org/{doi}" if doi else item.get("URL", "#")

            return {
                "doi": doi,
                "url": url,
                "title": title,
                "authors_str": authors_str,
                "publication_year": publication_year,
                "abstract": abstract,
                "source": "Crossref"
            }
        except Exception as e:
            print(f"   WARNING [Crossref]: Αποτυχία μορφοποίησης ενός άρθρου: {e}")
            return None