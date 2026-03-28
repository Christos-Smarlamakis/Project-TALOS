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
Module: openarchives_source.py (v2.0 - Genesis Update)
Project: TALOS v3.2

Description:
Η πλήρως αναβαθμισμένη έκδοση του "Πράκτορα" για το OpenArchives.gr,
εναρμονισμένη με τις απαιτήσεις του "Operation Genesis".
- Προσπαθεί να ανακτήσει το `doi` από το πεδίο `dc_identifier`.
- Χρησιμοποιεί μια ξεχωριστή μέθοδο `_format_paper` για καλύτερη οργάνωση.
- Επιστρέφει τα δεδομένα σε πλήρη συμμόρφωση με το νέο, τυποποιημένο λεξικό.
"""
import os
import requests
import time
from datetime import datetime
from typing import List, Dict, Any

class OpenArchivesSource:
    """
    Ένας "Πράκτορας" του TALOS που ανακτά δεδομένα από τον εθνικό συσσωρευτή
    OpenArchives.gr.
    """
    def __init__(self, config: Dict[str, Any]):
        """
        Αρχικοποιεί τον πράκτορα.
        """
        self.api_key = os.getenv("OPENARCHIVES_API_KEY")
        if not self.api_key:
            raise ValueError("Δεν βρέθηκε το OPENARCHIVES_API_KEY στο αρχείο .env.")
            
        self.query = config.get("openarchives_query", "robotics")
        self.days_to_search = config.get("days_to_search_daily", 1)
        self.total_max_results = config.get("max_results_config", {}).get("openarchives", 100)
        self.base_url = "https://www.openarchives.gr/aggregator-openarchives/api/search.json"
        
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json'
        }
        print("INFO: OpenArchivesSource (v2.0 - Genesis) αρχικοποιήθηκε.")

    def fetch_new_papers(self) -> List[Dict[str, Any]]:
        """
        Εκτελεί την αναζήτηση στο OpenArchives.gr API, υποστηρίζοντας σελιδοποίηση.
        """
        print(f"-> Αναζήτηση στο OpenArchives.gr...")
        all_papers = []
        page = 1
        page_size = 50

        # Φιλτράρουμε τοπικά με βάση το έτος, καθώς το API δεν έχει αξιόπιστο φίλτρο ημερομηνίας
        cutoff_year = datetime.now().year - (self.days_to_search // 365) - 1

        while len(all_papers) < self.total_max_results:
            params = {
                'apiKey': self.api_key,
                'general_term': self.query,
                'page': page,
                'pageSize': page_size
            }
            try:
                response = requests.get(self.base_url, params=params, headers=self.headers, timeout=20)
                response.raise_for_status()
                
                if not response.text:
                    print("   WARNING [OpenArchives]: Ο server επέστρεψε κενή απάντηση.")
                    break
                
                data = response.json()
                results_on_page = data.get('results', [])
                if not results_on_page:
                    break

                for item in results_on_page:
                    # Ελέγχουμε αν το έτος είναι εντός του ορίου μας
                    year_str = item.get("ekt_chronology", ["0"])[0].strip()
                    if not year_str.isdigit() or int(year_str) < cutoff_year:
                        continue
                        
                    formatted_paper = self._format_paper(item)
                    if formatted_paper:
                        all_papers.append(formatted_paper)
                    
                    if len(all_papers) >= self.total_max_results:
                        break
                
                if len(results_on_page) < page_size or len(all_papers) >= self.total_max_results:
                    break
                
                page += 1
                time.sleep(1)

            except requests.exceptions.RequestException as e:
                print(f"   ERROR [OpenArchives]: Παρουσιάστηκε σφάλμα κατά την ανάκτηση: {e}")
                break

        print(f"   SUCCESS [OpenArchives]: Βρέθηκαν {len(all_papers)} νέα άρθρα.")
        return all_papers

    def _format_paper(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """
        Μετατρέπει ένα αντικείμενο από το OpenArchives API στην τυποποιημένη μορφή του TALOS.
        """
        try:
            # Τα πεδία στο OpenArchives είναι λίστες, οπότε παίρνουμε το πρώτο στοιχείο
            title = item.get("dc_title", ["N/A"])[0]
            authors_str = ", ".join(item.get("dc_creator", []))
            
            # --- ΝΕΕΣ ΠΡΟΣΘΗΚΕΣ ---
            doi = None
            # Προσπαθούμε να βρούμε το DOI μέσα στα identifiers
            for identifier in item.get("dc_identifier", []):
                if 'doi.org' in identifier:
                    doi = identifier.split('doi.org/')[-1]
                    break
            
            year_str = item.get("ekt_chronology", ["0"])[0].strip()
            publication_year = int(year_str) if year_str.isdigit() else None

            # Προτεραιότητα στο URL του DOI, αν βρέθηκε
            url = f"https://doi.org/{doi}" if doi else item.get("edm_isShownAt", item.get("uri", "#"))

            return {
                "doi": doi,
                "url": url,
                "title": title,
                "authors_str": authors_str,
                "publication_year": publication_year,
                "abstract": item.get("dc_description", ["Η περίληψη δεν παρέχεται από το OpenArchives.gr API."])[0],
                "source": "OpenArchives.gr"
            }
        except Exception as e:
            print(f"   WARNING [OpenArchives]: Αποτυχία μορφοποίησης ενός άρθρου: {e}")
            return None