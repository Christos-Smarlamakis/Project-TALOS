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
Module: ieee_source.py (v2.2 - Robust Date Search)
Project: TALOS v3.2
Description:
Αυτή η έκδοση βελτιώνει το φιλτράρισμα ημερομηνίας για να διασφαλίσει την
πλήρη κάλυψη του χρονικού διαστήματος, ειδικά για τις ιστορικές αναζητήσεις.
"""
import requests
import os
import time
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any

class IEEEXploreSource:
    def __init__(self, config: Dict[str, Any]):
        self.api_key = os.getenv("IEEE_API_KEY")
        if not self.api_key: raise ValueError("IEEE_API_KEY not found in .env file.")
        self.query = config.get("ieee_query", "robotics")
        self.days_to_search = config.get("days_to_search_daily", 1)
        self.total_max_results = config.get("max_results_config", {}).get("ieee", 100)
        self.base_url = "https://ieeexploreapi.ieee.org/api/v1/search/articles"
        print("INFO: IEEEXploreSource (v2.2 - Robust Date Search) initialized.")

    def _make_request(self, params, max_retries=4, initial_backoff=5):
        # ... (η _make_request παραμένει η ίδια) ...
        for attempt in range(max_retries):
            try:
                response = requests.get(self.base_url, params=params, timeout=30)
                if response.status_code in [429, 403]:
                    if attempt == max_retries - 1: response.raise_for_status()
                    backoff = initial_backoff * (2 ** attempt) + random.uniform(0, 1)
                    print(f"   WARNING [IEEE]: API returned {response.status_code}. Retrying in {backoff:.2f}s...")
                    time.sleep(backoff)
                    continue
                response.raise_for_status()
                return response.json()
            except requests.exceptions.RequestException as e:
                print(f"   ERROR [IEEE]: API call failed after {attempt + 1} attempts. Error: {e}")
                return None
        return None

    def fetch_new_papers(self) -> List[Dict[str, Any]]:
        print(f"-> Αναζήτηση στο IEEE Xplore...")
        all_papers = []
        start_record = 1
        page_size = 200
        start_year = datetime.now().year - (self.days_to_search // 365) - 1
        cutoff_date = datetime.now() - timedelta(days=self.days_to_search)

        while len(all_papers) < self.total_max_results:
            params = {"apikey": self.api_key, "format": "json", "max_records": page_size, "start_record": start_record, "sort_order": "desc", "sort_field": "publication_year", "querytext": self.query, "start_year": start_year}
            data = self._make_request(params)
            if not data or not data.get('articles'): break
            articles_on_page = data.get('articles', [])

            for article in articles_on_page:
                if len(all_papers) >= self.total_max_results: break

                # --- Η ΔΙΟΡΘΩΜΕΝΗ ΛΟΓΙΚΗ ΕΙΝΑΙ ΕΔΩ ---
                # Φιλτράρουμε κάθε άρθρο, αλλά ΔΕΝ σταματάμε ολόκληρη τη σελιδοποίηση
                pub_year_str = article.get("publication_year")
                if pub_year_str and pub_year_str.isdigit():
                    pub_year = int(pub_year_str)
                    # Μια απλή προσέγγιση: αν το έτος είναι παλαιότερο από το έτος αποκοπής, το αγνοούμε
                    if pub_year >= cutoff_date.year:
                        formatted = self._format_paper(article)
                        if formatted: all_papers.append(formatted)
                
            if len(all_papers) >= self.total_max_results or len(articles_on_page) < page_size:
                break
            start_record += page_size

        print(f"   SUCCESS [IEEE]: Βρέθηκαν {len(all_papers)} νέα άρθρα.")
        return all_papers

    def _format_paper(self, article: Dict[str, Any]) -> Dict[str, Any]:
        # ... (η _format_paper παραμένει η ίδια) ...
        try:
            authors_list = article.get('authors', {}).get('authors', [])
            authors_str = ", ".join([author.get('full_name', '') for author in authors_list])
            doi = article.get("doi")
            url = f"https://doi.org/{doi}" if doi else article.get("html_url", "#")
            year_str = article.get("publication_year")
            publication_year = int(year_str) if year_str and year_str.isdigit() else None
            return {"doi": doi, "url": url, "title": article.get("title", "N/A"), "authors_str": authors_str, "publication_year": publication_year, "abstract": article.get("abstract", "Abstract not provided by IEEE API.").replace("\n", " "), "source": "IEEE Xplore"}
        except Exception as e:
            print(f"   WARNING [IEEE]: Failed to format an article: {e}")
            return None