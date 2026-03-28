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
Module: openalex_source.py (v2.0 - Genesis Update)
Project: TALOS v3.2

Description:
Η πλήρως αναβαθμισμένη έκδοση του "Πράκτορα" για το OpenAlex, εναρμονισμένη
με τις απαιτήσεις του "Operation Genesis".
- Ανακτά πλέον όλα τα κρίσιμα μεταδεδομένα (`doi`, `publication_year`).
- Χρησιμοποιεί μια ξεχωριστή μέθοδο `_format_paper` για καλύτερη οργάνωση.
- Επιστρέφει τα δεδομένα σε πλήρη συμμόρφωση με το νέο, τυποποιημένο λεξικό.
- Διατηρεί την "έξυπνη" λογική ανακατασκευής της περίληψης.
"""
import requests
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any

class OpenAlexSource:
    """
    Ένας "Πράκτορας" του TALOS που ειδικεύεται στην ανάκτηση δεδομένων από το OpenAlex API.
    """
    def __init__(self, config: Dict[str, Any]):
        """
        Αρχικοποιεί τον πράκτορα του OpenAlex.
        """
        self.query = config.get("openalex_query", "drone swarm intelligence")
        self.days_to_search = config.get("days_to_search_daily", 1)
        self.total_max_results = config.get("max_results_config", {}).get("openalex", 100)
        self.mailto = config.get("mailto", "user@example.com")
        self.base_url = "https://api.openalex.org/works"
        print("INFO: OpenAlexSource (v2.0 - Genesis) αρχικοποιήθηκε.")

    def fetch_new_papers(self) -> List[Dict[str, Any]]:
        """
        Εκτελεί την αναζήτηση στο OpenAlex API, χρησιμοποιώντας σελιδοποίηση.
        """
        print(f"-> Αναζήτηση στο OpenAlex...")
        all_papers = []
        page = 1
        per_page = 50 

        cutoff_date = (datetime.now().date() - timedelta(days=self.days_to_search))
        date_filter = f"from_publication_date:{cutoff_date.strftime('%Y-%m-%d')}"

        while len(all_papers) < self.total_max_results:
            params = {
                "search": self.query,
                "per_page": per_page,
                "page": page,
                "sort": "publication_date:desc",
                "filter": date_filter,
                "mailto": self.mailto
            }
            try:
                response = requests.get(self.base_url, params=params, timeout=20)
                if response.status_code == 429:
                    print("   WARNING [OpenAlex]: Rate limit. Αναμονή 10 δευτερολέπτων...")
                    time.sleep(10)
                    continue
                
                response.raise_for_status()
                data = response.json()
                results_on_page = data.get('results', [])

                if not results_on_page:
                    break

                for work in results_on_page:
                    formatted_paper = self._format_paper(work)
                    if formatted_paper:
                        all_papers.append(formatted_paper)

                    if len(all_papers) >= self.total_max_results:
                        break
                
                if len(all_papers) >= self.total_max_results:
                    break
                
                # Ελέγχουμε αν υπάρχει επόμενη σελίδα (cursor pagination)
                if 'next_page' not in data['meta'] or not data['meta']['next_page']:
                    break
                
                page += 1
                time.sleep(0.2) # "Ευγενική" παύση

            except requests.exceptions.RequestException as e:
                print(f"   ERROR [OpenAlex]: Παρουσιάστηκε σφάλμα κατά την ανάκτηση: {e}")
                break

        print(f"   SUCCESS [OpenAlex]: Βρέθηκαν {len(all_papers)} νέα άρθρα.")
        return all_papers

    def _reconstruct_abstract(self, inverted_index: Dict[str, List[int]]) -> str:
        """
        Ανακατασκευάζει την περίληψη από το inverted index του OpenAlex.
        """
        if not inverted_index:
            return "Δεν υπάρχει διαθέσιμη περίληψη."
        
        # Δημιουργούμε ένα λεξικό για να αντιστοιχίσουμε τη θέση κάθε λέξης
        word_positions = {}
        for word, positions in inverted_index.items():
            for pos in positions:
                word_positions[pos] = word
        
        # Παίρνουμε τις λέξεις ταξινομημένες με βάση τη θέση τους
        abstract_list = [word_positions[i] for i in sorted(word_positions.keys())]
        return " ".join(abstract_list)

    def _format_paper(self, work: Dict[str, Any]) -> Dict[str, Any]:
        """
        Μετατρέπει ένα αντικείμενο από το OpenAlex API στην τυποποιημένη μορφή του TALOS.
        """
        try:
            authors_str = ", ".join([a.get("author", {}).get("display_name", "") for a in work.get("authorships", []) if a.get("author")])
            
            # Το OpenAlex επιστρέφει το DOI χωρίς το URL prefix
            doi_suffix = work.get("doi")
            doi = doi_suffix.replace("https://doi.org/", "") if doi_suffix else None
            
            # Προτεραιότητα στο DOI link, αλλιώς το landing page
            url = doi_suffix or work.get("primary_location", {}).get("landing_page_url", "#")
            
            abstract = self._reconstruct_abstract(work.get('abstract_inverted_index'))

            return {
                "doi": doi,
                "url": url,
                "title": work.get("title", "N/A"),
                "authors_str": authors_str,
                "publication_year": work.get("publication_year"),
                "abstract": abstract,
                "source": "OpenAlex"
            }
        except Exception as e:
            print(f"   WARNING [OpenAlex]: Αποτυχία μορφοποίησης ενός άρθρου: {e}")
            return None