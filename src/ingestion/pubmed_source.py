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
Module: pubmed_source.py 
Project: TALOS v5.9.18

Description:
    Search agent for the PubMed biomedical literature database via the pymed
    library. Fetches papers matching the configured query with date filtering.
    Does not require an API key but needs a valid email address in config.
"""
from pymed import PubMed
from datetime import datetime, timedelta
from typing import List, Dict, Any

class PubMedSource:
    """Search agent for PubMed."""
    def __init__(self, config: Dict[str, Any]):
        self.query = config.get("pubmed_query", "bio-inspired algorithms")
        self.days_to_search = config.get("days_to_search_daily", 1)
        self.max_results = config.get("max_results_config", {}).get("pubmed", 100)
        self.mailto = config.get("mailto", "a@b.com")
        if self.mailto == "a@b.com":
            print("WARNING: Using default email for PubMed. Please set 'mailto' in config.json.")
        self.pubmed = PubMed(tool="ProjectTALOS", email=self.mailto)
        print("INFO: PubMedSource initialized.")

    def fetch_new_papers(self) -> List[Dict[str, Any]]:
        print(f"-> Searching PubMed...")
        cutoff_date = (datetime.now() - timedelta(days=self.days_to_search)).strftime('%Y/%m/%d')
        full_query = f'({self.query}) AND ("{cutoff_date}"[Date - Publication] : "3000"[Date - Publication])'
        try:
            results = self.pubmed.query(full_query, max_results=self.max_results)
            papers = []
            for article in results:
                formatted_paper = self._format_paper(article)
                if formatted_paper: papers.append(formatted_paper)
            print(f"   SUCCESS [PubMed]: Found {len(papers)} new papers.")
            return papers
        except Exception as e:
            print(f"   ERROR [PubMed]: Fetch failed: {e}")
            return []

    def _format_paper(self, article) -> Dict[str, Any]:
        try:
            authors_str = "N/A"
            if article.authors:
                authors_str = ", ".join([f"{a.get('lastname', '')}, {a.get('firstname', '')}".strip(', ') for a in article.authors])
            doi = article.doi
            publication_year = article.publication_date.year if article.publication_date else None
            url = f"https://doi.org/{doi}" if doi else f"https://pubmed.ncbi.nlm.nih.gov/{article.pubmed_id}/"
            return {"doi": doi, "url": url, "title": article.title or "N/A", "authors_str": authors_str,
                    "publication_year": publication_year,
                    "abstract": article.abstract or "No abstract available.", "source": "PubMed"}
        except Exception as e:
            print(f"   WARNING [PubMed]: Formatting failed: {e}")
            return None