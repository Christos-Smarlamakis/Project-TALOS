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
"""
import os, time, requests, random
from datetime import datetime, timedelta
from typing import List, Dict, Any

class SpringerNatureSource:
    def __init__(self, config: Dict[str, Any]):
        self.enabled = True
        self.api_key = os.getenv("SPRINGER_API_KEY")
        if not self.api_key:
            print("WARNING: SPRINGER_API_KEY not found. Skipping source.")
            self.enabled = False
            return
        self.query = config.get("springer_query", "keyword:robotics")
        self.days_to_search = config.get("days_to_search_daily", 1)
        self.total_max_results = config.get("max_results_config", {}).get("springer", 50)
        self.base_url = "https://api.springernature.com/meta/v2/json"
        print("INFO: SpringerNatureSource initialized.")

    def _make_request(self, params, max_retries=4, initial_backoff=5):
        for attempt in range(max_retries):
            try:
                response = requests.get(self.base_url, params=params, timeout=30)
                if response.status_code in [429, 403]:
                    if attempt == max_retries - 1:
                        response.raise_for_status()
                    backoff = initial_backoff * (2 ** attempt) + random.uniform(0, 1)
                    time.sleep(backoff)
                    continue
                response.raise_for_status()
                return response.json()
            except requests.exceptions.RequestException as e:
                return None
        return None

    def fetch_new_papers(self) -> List[Dict[str, Any]]:
        if not getattr(self, "enabled", True):
            return []
        all_papers = []
        page_size, current_record = 100, 1
        cutoff_date = datetime.now().date() - timedelta(days=self.days_to_search)
        full_query = f'({self.query}) onlinedatefrom:{cutoff_date}'
        while len(all_papers) < self.total_max_results:
            params = {"api_key": self.api_key, "p": page_size, "s": current_record, "q": full_query}
            data = self._make_request(params)
            if not data or not data.get('records'):
                break
            for article in data.get('records', []):
                paper = self._format_paper(article)
                if paper:
                    all_papers.append(paper)
                if len(all_papers) >= self.total_max_results:
                    break
            if len(data.get('records', [])) < page_size:
                break
            current_record += page_size
        return all_papers

    def _format_paper(self, article):
        try:
            authors_str = ", ".join([c.get('creator') for c in article.get('creators', [])])
            abstract = article.get('abstract', '')
            if isinstance(abstract, str) and abstract.startswith('<p>'):
                abstract = abstract.replace('<p>', '').replace('</p>', '')
            doi = article.get("doi")
            url = f"https://doi.org/{doi}" if doi else (article.get('url', [{}])[0].get('value', '#') if article.get('url') else '#')
            pub_year = None
            ds = article.get("publicationDate")
            if ds:
                try:
                    pub_year = datetime.strptime(ds, '%Y-%m-%d').year
                except ValueError:
                    pass
            return {"doi": doi, "url": url, "title": article.get("title", "N/A"),
                    "authors_str": authors_str, "publication_year": pub_year,
                    "abstract": abstract.replace("\n", " "), "source": "Springer Nature"}
        except:
            return None
