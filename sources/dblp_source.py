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
Module: dblp_source.py (v2.0 - Genesis Update)
Project: TALOS v3.2

Description:
Η πλήρως αναβαθμισμένη έκδοση του "Πράκτορα" για το DBLP, εναρμονισμένη
με τις απαιτήσεις του "Operation Genesis".
- Ανακτά πλέον το κρίσιμο μεταδεδομένο: `doi`.
- Χρησιμοποιεί μια ξεχωριστή μέθοδο `_format_paper` για καλύτερη οργάνωση.
- Επιστρέφει τα δεδομένα σε πλήρη συμμόρφωση με το νέο, τυποποιημένο λεξικό.
"""
import requests
import time
from datetime import datetime
from typing import List, Dict, Any

class DBLPSource:
    """
    Ένας "Πράκτορας" του TALOS που ειδικεύεται στην ανάκτηση δεδομένων από το DBLP API.
    """
    def __init__(self, config: Dict[str, Any]):
        """
        Αρχικοποιεί τον πράκτορα του DBLP.
        """
        self.query = config.get("dblp_query", "swarm intelligence")
        self.days_to_search = config.get("days_to_search_daily", 1)
        self.total_max_results = config.get("max_results_config", {}).get("dblp", 100)
        self.base_url = "https://dblp.org/search/publ/api"
        print("INFO: DBLPSource (v2.0 - Genesis) αρχικοποιήθηκε.")

    def fetch_new_papers(self) -> List[Dict[str, Any]]:
        """
        Εκτελεί την αναζήτηση στο DBLP API και επιστρέφει τα νέα άρθρα.
        """
        print(f"-> Αναζήτηση στο DBLP...")
        all_papers = []
        offset = 0
        page_size = 100

        # Η αναζήτηση στο DBLP δεν έχει καλό φίλτρο ημερομηνίας, οπότε
        # φιλτράρουμε τοπικά με βάση το έτος.
        start_year = datetime.now().year - (self.days_to_search // 365) -1 # -1 για ασφάλεια

        while len(all_papers) < self.total_max_results:
            params = {
                "q": self.query,
                "h": page_size, # h = max number of hits
                "f": offset,   # f = first hit to show
                "format": "json"
            }
            try:
                response = requests.get(self.base_url, params=params, timeout=20)
                response.raise_for_status()
                data = response.json()
                
                hits = data.get('result', {}).get('hits', {}).get('hit', [])
                if not hits:
                    break # Δεν υπάρχουν άλλα αποτελέσματα

                stop_searching = False
                for item in hits:
                    info = item.get('info', {})
                    
                    # Τοπικό φιλτράρισμα με βάση το έτος
                    year_str = info.get("year")
                    if year_str and int(year_str) < start_year:
                        stop_searching = True
                        continue # Αγνοούμε τα πολύ παλιά άρθρα
                        
                    formatted_paper = self._format_paper(info)
                    if formatted_paper:
                        all_papers.append(formatted_paper)

                    if len(all_papers) >= self.total_max_results:
                        break
                
                if stop_searching or len(all_papers) >= self.total_max_results or len(hits) < page_size:
                    break

                offset += page_size
                time.sleep(1)

            except requests.exceptions.RequestException as e:
                print(f"   ERROR [DBLP]: Παρουσιάστηκε σφάλμα κατά την ανάκτηση: {e}")
                break

        print(f"   SUCCESS [DBLP]: Βρέθηκαν {len(all_papers)} νέα άρθρα.")
        return all_papers

    def _format_paper(self, info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Μετατρέπει ένα αντικείμενο 'info' από το DBLP API στην τυποποιημένη μορφή του TALOS.
        """
        try:
            # Το πεδίο 'authors' μπορεί να είναι είτε λίστα είτε ένα μόνο αντικείμενο
            authors_data = info.get('authors', {}).get('author', [])
            if isinstance(authors_data, list):
                authors_str = ", ".join([a.get('text', '') for a in authors_data])
            elif isinstance(authors_data, dict):
                authors_str = authors_data.get('text', '')
            else:
                authors_str = ""

            # --- ΝΕΕΣ ΠΡΟΣΘΗΚΕΣ ---
            doi = info.get("doi")
            year_str = info.get("year")
            publication_year = int(year_str) if year_str and year_str.isdigit() else None
            
            # Το DBLP παρέχει το καλύτερο link στο πεδίο "ee" (electronic edition)
            url = info.get("ee") or (f"https://doi.org/{doi}" if doi else info.get("url", "#"))
            
            return {
                "doi": doi,
                "url": url,
                "title": info.get("title", "N/A"),
                "authors_str": authors_str,
                "publication_year": publication_year,
                "abstract": "Το DBLP δεν παρέχει περιλήψεις μέσω του API.",
                "source": "DBLP"
            }
        except Exception as e:
            print(f"   WARNING [DBLP]: Αποτυχία μορφοποίησης ενός άρθρου: {e}")
            return None