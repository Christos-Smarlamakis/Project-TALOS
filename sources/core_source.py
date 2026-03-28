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
Module: core_source.py (v2.1 - Robust Date Search)
Project: TALOS v3.2

Description:
Διορθώνει ένα λογικό σφάλμα στο φιλτράρισμα ημερομηνίας. Η αναζήτηση
πλέον δεν σταματά πρόωρα, επιτρέποντας την πλήρη κάλυψη του χρονικού
διαστήματος που ορίζεται στην ιστορική αναζήτηση.
"""
import requests
import time
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any

class CORESource:
    def __init__(self, config: Dict[str, Any]):
        self.api_key = os.getenv("CORE_API_KEY")
        self.query = config.get("core_query", "swarm intelligence")
        self.days_to_search = config.get("days_to_search_daily", 1)
        self.total_max_results = config.get("max_results_config", {}).get("core", 100)
        self.base_url = "https://api.core.ac.uk/v3/search/works"
        self.headers = {'User-Agent': 'Mozilla/5.0'}
        if self.api_key:
            self.headers["Authorization"] = f"Bearer {self.api_key}"
        print("INFO: CORESource (v2.1 - Robust Date Search) αρχικοποιήθηκε.")

    def fetch_new_papers(self) -> List[Dict[str, Any]]:
        print(f"-> Αναζήτηση στο CORE...")
        all_papers = []
        page = 1
        page_size = 100
        cutoff_date = (datetime.now().date() - timedelta(days=self.days_to_search))

        while len(all_papers) < self.total_max_results:
            params = {"q": self.query, "limit": page_size, "page": page, "sort": "publishedDate:desc"}
            try:
                response = requests.get(self.base_url, params=params, headers=self.headers, timeout=20)
                response.raise_for_status()
                data = response.json()
                results_on_page = data.get('results', [])
                if not results_on_page: break

                for item in results_on_page:
                    if len(all_papers) >= self.total_max_results: break
                    
                    # --- Η ΔΙΟΡΘΩΜΕΝΗ ΛΟΓΙΚΗ ΕΙΝΑΙ ΕΔΩ ---
                    # Φιλτράρουμε κάθε άρθρο, αλλά ΔΕΝ σταματάμε ολόκληρη τη σελιδοποίηση
                    pub_date_str = item.get("publishedDate")
                    is_recent_enough = False
                    if pub_date_str:
                        try:
                            paper_date = datetime.strptime(pub_date_str[:10], '%Y-%m-%d').date()
                            if paper_date >= cutoff_date:
                                is_recent_enough = True
                        except ValueError:
                            continue
                    
                    if is_recent_enough:
                        formatted_paper = self._format_paper(item)
                        if formatted_paper:
                            all_papers.append(formatted_paper)

                if len(all_papers) >= self.total_max_results or len(results_on_page) < page_size:
                    break
                page += 1
                time.sleep(1)
            except requests.exceptions.RequestException as e:
                print(f"   ERROR [CORE]: Παρουσιάστηκε σφάλμα: {e}")
                break
        print(f"   SUCCESS [CORE]: Βρέθηκαν {len(all_papers)} νέα άρθρα.")
        return all_papers

    def _format_paper(self, item: Dict[str, Any]) -> Dict[str, Any]:
        # ... (η _format_paper παραμένει η ίδια) ...
        authors_str = ", ".join([author.get('name', '') for author in item.get('authors', [])])
        doi = item.get('doi')
        url = f"https://doi.org/{doi}" if doi else item.get('downloadUrl', '#')
        return {
            "doi": doi, "url": url, "title": item.get("title", "N/A"),
            "authors_str": authors_str, "publication_year": item.get("yearPublished"),
            "abstract": item.get("abstract", "Δεν υπάρχει διαθέσιμη περίληψη."), "source": "CORE"
        }