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
Module: plos_source.py
Project: TALOS v5.9.15

Description:
    Search agent for the PLOS (Public Library of Science) API. All PLOS content
    is Open Access, making this a high-value source for full-text availability.
    Uses the Solr-based search API with date filtering and pagination. Free
    to use -- no API key required.
"""
import requests
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any

class PLOSSource:
    """Search agent for the PLOS API (Open Access)."""
    def __init__(self, config: Dict[str, Any]):
        self.query = config.get("plos_query", "swarm intelligence")
        self.days_to_search = config.get("days_to_search_daily", 1)
        self.total_max_results = config.get("max_results_config", {}).get("plos", 100)
        self.base_url = "http://api.plos.org/search"
        print("INFO: PLOSSource initialized.")

    def fetch_new_papers(self) -> List[Dict[str, Any]]:
        print(f"-> Searching PLOS...")
        all_papers = []
        start_row = 0
        rows_per_page = 100
        cutoff_date = (datetime.now() - timedelta(days=self.days_to_search)).strftime('%Y-%m-%dT00:00:00Z')
        solr_query = f'title:"{self.query}" OR abstract:"{self.query}"'
        filter_query = f'publication_date:[{cutoff_date} TO *]'

        while len(all_papers) < self.total_max_results:
            params = {
                'q': solr_query, 'fq': [filter_query, 'doc_type:Full'],
                'wt': 'json', 'rows': rows_per_page, 'start': start_row,
                'fl': 'id,title,author_display,publication_date,abstract'
            }
            try:
                response = requests.get(self.base_url, params=params, timeout=20)
                if response.status_code == 429:
                    print("   WARNING [PLOS]: Rate limit. Waiting 10 seconds...")
                    time.sleep(10); continue
                response.raise_for_status()
                data = response.json()
                docs = data.get('response', {}).get('docs', [])
                if not docs: break
                for doc in docs:
                    formatted = self._format_paper(doc)
                    if formatted: all_papers.append(formatted)
                    if len(all_papers) >= self.total_max_results: break
                if len(all_papers) >= self.total_max_results or len(docs) < rows_per_page: break
                start_row += rows_per_page; time.sleep(1)
            except requests.exceptions.RequestException as e:
                print(f"   ERROR [PLOS]: Fetch failed: {e}"); break
        print(f"   SUCCESS [PLOS]: Found {len(all_papers)} new papers.")
        return all_papers

    def _format_paper(self, doc: Dict[str, Any]) -> Dict[str, Any]:
        try:
            doi = doc.get('id')
            url = f"https://doi.org/{doi}" if doi else "#"
            pub_date_str = doc.get('publication_date')
            pub_year = int(pub_date_str[:4]) if pub_date_str else None
            authors = ", ".join(doc.get('author_display', []))
            abstract_raw = doc.get('abstract', ["No abstract available."])
            abstract = abstract_raw[0] if isinstance(abstract_raw, list) and abstract_raw else str(abstract_raw)
            return {"doi": doi, "url": url, "title": doc.get("title", doc.get("title_display", "N/A")),
                    "authors_str": authors, "publication_year": pub_year, "abstract": abstract, "source": "PLOS"}
        except Exception as e:
            print(f"   WARNING [PLOS]: Formatting failed: {e}")
            return None