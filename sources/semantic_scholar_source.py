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
Module: semantic_scholar_source.py (v3.4 - Resilient Init)
Project: TALOS v3.2

Description:
Η τελική έκδοση του "Πράκτορα" για το Semantic Scholar.
- Χρησιμοποιεί τη μέθοδο .get() για την ανάκτηση ρυθμίσεων, αποτρέποντας
  το 'KeyError'.
- Ενσωματώνει τον ανθεκτικό μηχανισμό "Exponential Backoff".
"""
import os
import requests
import time
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any

class SemanticScholarSource:
    def __init__(self, config: dict):
        self.config = config
        # Χρησιμοποιούμε .get() για ασφάλεια, με μια λογική προεπιλεγμένη τιμή
        self.query = config.get("semantic_scholar_query", "swarm intelligence")
        self.api_key = os.getenv("SEMANTIC_SCHOLAR_API_KEY")
        self.base_url = "https://api.semanticscholar.org/graph/v1"
        self.headers = {'x-api-key': self.api_key} if self.api_key else {}
        print("INFO: SemanticScholarSource αρχικοποιήθηκε (v3.4 - Resilient Init).")

    def _make_request(self, endpoint, params, max_retries=4, initial_backoff=2):
        for attempt in range(max_retries):
            try:
                response = requests.get(f"{self.base_url}{endpoint}", params=params, headers=self.headers, timeout=15)
                if response.status_code == 429:
                    if attempt == max_retries - 1: response.raise_for_status()
                    backoff_time = initial_backoff * (2 ** attempt) + random.uniform(0, 1)
                    print(f"  > WARNING [S2]: Rate limit hit. Retrying in {backoff_time:.2f}s...")
                    time.sleep(backoff_time)
                    continue
                response.raise_for_status()
                return response.json()
            except requests.exceptions.RequestException as e:
                print(f"ERROR [Semantic Scholar]: API call to {endpoint} failed after {attempt + 1} attempts. Error: {e}")
                return None
        return None

    def _format_paper(self, paper: dict) -> dict:
        if not paper: return None
        authors = ", ".join([author.get('name', '') for author in paper.get('authors', []) if author])
        doi = paper.get('externalIds', {}).get('DOI', '') if paper.get('externalIds') else ''
        url = paper.get('url') or (f"https://doi.org/{doi}" if doi else "")
        return {'doi': doi, 'url': url, 'title': paper.get('title'), 'authors_str': authors, 'publication_year': paper.get('year'), 'abstract': paper.get('abstract'), 'source': 'Semantic Scholar'}

    def search_papers(self, query: str, limit: int = 10) -> list:
        params = {'query': query, 'limit': limit, 'fields': 'title,authors,year,abstract,url,externalIds'}
        data = self._make_request("/paper/search", params)
        if not data or 'data' not in data:
            return []
        return [self._format_paper(p) for p in data['data'] if p]

    def fetch_new_papers(self) -> list:
        print("-> Αναζήτηση στο Semantic Scholar για νέα άρθρα...")
        days_to_search = self.config.get("days_to_search_daily", 1)
        limit = self.config.get("max_results_config", {}).get('semantic_scholar', 100)
        
        all_papers = []
        offset = 0
        while len(all_papers) < limit:
            params = {'query': self.query, 'offset': offset, 'limit': min(100, limit - len(all_papers)), 'fields': 'title,authors,year,abstract,url,externalIds,publicationDate'}
            data = self._make_request("/paper/search", params)
            if not data or 'data' not in data or not data['data']: break
            all_papers.extend(data['data'])
            if 'next' in data and data['next'] is not None:
                offset = data['next']
            else: break
            
        start_date = datetime.now() - timedelta(days=days_to_search)
        recent_papers = []
        for paper in all_papers:
            pub_date_str = paper.get('publicationDate')
            if pub_date_str:
                try:
                    if datetime.strptime(pub_date_str, '%Y-%m-%d') >= start_date:
                        recent_papers.append(self._format_paper(paper))
                except ValueError: continue
        print(f"   SUCCESS [Semantic Scholar]: Βρέθηκαν {len(recent_papers)} πρόσφατα άρθρα.")
        return recent_papers

    def get_paper_details(self, paper_id: str, fields: str = 'title,paperId,url,year,authors') -> dict:
        return self._make_request(f"/paper/{paper_id}", {'fields': fields})

    def _get_paginated_paper_list(self, url: str, limit: int) -> list:
        all_results = []
        params = {'fields': 'title,url,year,authors', 'limit': min(limit, 1000)}
        offset = 0
        while len(all_results) < limit:
            params['offset'] = offset
            data = self._make_request(url, params)
            if not data or not data.get('data'): break
            results_on_page = data['data']
            cleaned_results = [item.get('citedPaper') or item.get('citingPaper') for item in results_on_page if item]
            all_results.extend([res for res in cleaned_results if res])
            if 'next' in data and data['next'] is not None:
                offset = data['next']
            else: break
        return all_results[:limit]

    def get_paper_references(self, paper_id: str, limit: int = 100) -> list:
        url = f"{self.base_url}/paper/{paper_id}/references"
        return self._get_paginated_paper_list(url, limit)

    def get_paper_citations(self, paper_id: str, limit: int = 100) -> list:
        url = f"{self.base_url}/paper/{paper_id}/citations"
        return self._get_paginated_paper_list(url, limit)