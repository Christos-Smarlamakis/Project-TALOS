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
Module: springer_source.py (v2.1 - Resilient)
Project: TALOS v3.2

Description:
Αυτή η έκδοση ενσωματώνει έναν ανθεκτικό μηχανισμό "Exponential Backoff"
για τον χειρισμό των σφαλμάτων rate limiting (429) και προσωρινών σφαλμάτων
'Forbidden' (403), κάνοντας τον πράκτορα πιο αξιόπιστο.
"""
import os
import time
import requests
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any

class SpringerNatureSource:
    def __init__(self, config: Dict[str, Any]):
        self.api_key = os.getenv("SPRINGER_API_KEY")
        if not self.api_key:
            raise ValueError("Δεν βρέθηκε το SPRINGER_API_KEY στο αρχείο .env.")
        self.query = config.get("springer_query", "keyword:robotics")
        self.days_to_search = config.get("days_to_search_daily", 1)
        self.total_max_results = config.get("max_results_config", {}).get("springer", 50)
        self.base_url = "https://api.springernature.com/meta/v2/json"
        print("INFO: SpringerNatureSource (v2.1 - Resilient) αρχικοποιήθηκε.")

    def _make_request(self, params: Dict[str, Any], max_retries: int = 4, initial_backoff: int = 5) -> Dict[str, Any]:
        """
        Εκτελεί μια κλήση στο API με λογική αυτόματης επανάληψης.
        """
        for attempt in range(max_retries):
            try:
                response = requests.get(self.base_url, params=params, timeout=30)
                if response.status_code in [429, 403]:
                    if attempt == max_retries - 1:
                        response.raise_for_status()
                    backoff = initial_backoff * (2 ** attempt) + random.uniform(0, 1)
                    print(f"   WARNING [Springer]: API returned {response.status_code}. Retrying in {backoff:.2f}s...")
                    time.sleep(backoff)
                    continue
                response.raise_for_status()
                return response.json()
            except requests.exceptions.RequestException as e:
                print(f"   ERROR [Springer]: API call failed after {attempt + 1} attempts. Error: {e}")
                return None
        return None

    def fetch_new_papers(self) -> List[Dict[str, Any]]:
        print("-> Αναζήτηση στο Springer Nature...")
        all_papers = []
        page_size = 100
        current_record = 1
        cutoff_date = (datetime.now().date() - timedelta(days=self.days_to_search))
        date_filter = f" onlinedatefrom:{cutoff_date.strftime('%Y-%m-%d')}"
        full_query = f'({self.query}){date_filter}'

        while len(all_papers) < self.total_max_results:
            params = {"api_key": self.api_key, "p": page_size, "s": current_record, "q": full_query}
            
            data = self._make_request(params)
            if not data or not data.get('records'):
                break
                
            records = data.get('records', [])
            for article in records:
                formatted_paper = self._format_paper(article)
                if formatted_paper:
                    all_papers.append(formatted_paper)
                if len(all_papers) >= self.total_max_results:
                    break
            
            if len(all_papers) >= self.total_max_results or len(records) < page_size:
                break
            
            current_record += page_size
        
        print(f"   SUCCESS [Springer]: Βρέθηκαν {len(all_papers)} νέα άρθρα.")
        return all_papers

    def _format_paper(self, article: Dict[str, Any]) -> Dict[str, Any]:
        try:
            authors_str = ", ".join([creator.get('creator') for creator in article.get('creators', [])])
            abstract = article.get('abstract', 'Δεν υπάρχει διαθέσιμη περίληψη.')
            if isinstance(abstract, str) and abstract.startswith('<p>'):
                abstract = abstract.replace('<p>', '').replace('</p>', '')
            doi = article.get("doi")
            url = f"https://doi.org/{doi}" if doi else (article.get('url', [{}])[0].get('value', '#') if article.get('url') else '#')
            
            publication_year = None
            date_str = article.get("publicationDate")
            if date_str:
                try:
                    publication_year = datetime.strptime(date_str, '%Y-%m-%d').year
                except ValueError: pass
                
            return {
                "doi": doi, "url": url, "title": article.get("title", "N/A"),
                "authors_str": authors_str, "publication_year": publication_year,
                "abstract": abstract.replace("\n", " "), "source": "Springer Nature"
            }
        except Exception as e:
            print(f"   WARNING [Springer]: Failed to format an article: {e}")
            return None