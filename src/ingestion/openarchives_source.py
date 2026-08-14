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
Module: openarchives_source.py
Project: TALOS v5.9.17

Description:
    Search agent for the OpenArchives.gr API, the Greek national aggregator
    for academic content. Fetches papers with year-based filtering. Requires
    an API key via ``OPENARCHIVES_API_KEY``. Gracefully disables itself if
    no key is configured.
"""
import os, requests, time
from datetime import datetime
from typing import List, Dict, Any


class OpenArchivesSource:
    """Search agent for OpenArchives.gr."""
    def __init__(self, config: Dict[str, Any]):
        self.enabled = True
        self.api_key = os.getenv("OPENARCHIVES_API_KEY")
        if not self.api_key:
            print("WARNING: OPENARCHIVES_API_KEY not found. Skipping source.")
            self.enabled = False
            return
        self.query = config.get("openarchives_query", "robotics")
        self.days_to_search = config.get("days_to_search_daily", 1)
        self.total_max_results = config.get("max_results_config", {}).get("openarchives", 100)
        self.base_url = "https://www.openarchives.gr/aggregator-openarchives/api/search.json"
        self.headers = {'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json'}
        print("INFO: OpenArchivesSource initialized.")

    def fetch_new_papers(self) -> List[Dict[str, Any]]:
        if not getattr(self, "enabled", True): return []
        all_papers = []
        page, page_size = 1, 50
        cutoff_year = datetime.now().year - (self.days_to_search // 365) - 1
        while len(all_papers) < self.total_max_results:
            params = {'apiKey': self.api_key, 'general_term': self.query, 'page': page, 'pageSize': page_size}
            try:
                response = requests.get(self.base_url, params=params, headers=self.headers, timeout=20)
                response.raise_for_status()
                if not response.text: break
                data = response.json()
                results_on_page = data.get('results', [])
                if not results_on_page: break
                for item in results_on_page:
                    year_str = item.get("ekt_chronology", ["0"])[0].strip()
                    if not year_str.isdigit() or int(year_str) < cutoff_year: continue
                    paper = self._format_paper(item)
                    if paper: all_papers.append(paper)
                    if len(all_papers) >= self.total_max_results: break
                if len(results_on_page) < page_size or len(all_papers) >= self.total_max_results: break
                page += 1; time.sleep(1)
            except requests.exceptions.RequestException: break
        return all_papers

    def _format_paper(self, item):
        try:
            title = item.get("dc_title", ["N/A"])[0]
            authors_str = ", ".join(item.get("dc_creator", []))
            doi = None
            for identifier in item.get("dc_identifier", []):
                if 'doi.org' in identifier:
                    doi = identifier.split('doi.org/')[-1]; break
            year_str = item.get("ekt_chronology", ["0"])[0].strip()
            publication_year = int(year_str) if year_str.isdigit() else None
            url = f"https://doi.org/{doi}" if doi else item.get("edm_isShownAt", item.get("uri", "#"))
            return {"doi": doi, "url": url, "title": title, "authors_str": authors_str,
                    "publication_year": publication_year,
                    "abstract": item.get("dc_description", ["No abstract available."])[0],
                    "source": "OpenArchives.gr"}
        except: return None