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
Module: elsevier_source.py
Project: TALOS v5.3.7

Description:
    Search agent for the Elsevier Scopus API via the elsapy library.
    Requires both an API key and institutional token. Fetches new papers
    matching the configured Scopus query, with an additional targeted
    call to the Abstract Retrieval API when abstracts are missing from
    the initial search results. Gracefully disables itself if API keys
    are not configured.
"""
import os
from datetime import datetime, timedelta
from elsapy.elsclient import ElsClient
from elsapy.elssearch import ElsSearch
from elsapy.elsdoc import AbsDoc
from typing import List, Dict, Any


class ElsevierSource:
    """Search agent for the Elsevier Scopus API.

    Uses elsapy for authenticated access. Performs a Scopus search
    and enriches results with full abstracts via AbsDoc when needed.

    Attributes:
        enabled (bool): False if API keys are missing; agent skips gracefully.
        client (ElsClient): Authenticated Elsevier API client.
        query (str): Scopus search query from config.
    """

    def __init__(self, config: Dict[str, Any]):
        """Initialize the Elsevier agent.

        Args:
            config (dict): Application configuration dictionary.
        """
        self.enabled = True

        self.api_key = os.getenv("ELSEVIER_API_KEY")
        self.inst_token = os.getenv("ELSEVIER_INST_TOKEN")
        if not self.api_key or not self.inst_token:
            print("WARNING: Elsevier API keys not found in .env file. Skipping source.")
            self.enabled = False
            return
        self.client = ElsClient(self.api_key, inst_token=self.inst_token)
        self.query = config.get("elsevier_query", "TITLE-ABS-KEY(robotics)")
        self.days_to_search = config.get("days_to_search_daily", 1)
        self.total_max_results = config.get("max_results_config", {}).get("elsevier", 200)
        print("INFO: ElsevierSource initialized.")

    def fetch_new_papers(self) -> List[Dict[str, Any]]:
        """Fetch recent papers from Elsevier Scopus.

        Returns:
            list of dict: Standardized paper dictionaries, empty if disabled.
        """
        if not getattr(self, "enabled", True): return []

        print(f"-> Searching Elsevier (Scopus)...")
        all_papers = []
        try:
            start_year = datetime.now().year - (self.days_to_search // 365) - 1
            date_filter = f" AND PUBYEAR > {start_year}"
            doc_srch = ElsSearch(self.query + date_filter, 'scopus')
            doc_srch.execute(self.client, get_all=True)
            print(f"   INFO [Elsevier]: API returned {len(doc_srch.results)} initial results.")

            for result in doc_srch.results[:self.total_max_results]:
                formatted_paper = self._format_paper(result)
                if formatted_paper:
                    if "not provide" in formatted_paper.get('abstract', '') and formatted_paper.get('scopus_id'):
                        print(f"      -> Enriching abstract for Scopus ID: {formatted_paper['scopus_id']}...")
                        abstract = self._fetch_abstract(formatted_paper['scopus_id'])
                        if abstract:
                            formatted_paper['abstract'] = abstract
                    all_papers.append(formatted_paper)
        except Exception as e:
            print(f"   ERROR [Elsevier]: An error occurred during fetch: {e}")
            return []
        print(f"   SUCCESS [Elsevier]: Found and processed {len(all_papers)} new articles.")
        return all_papers

    def _fetch_abstract(self, scopus_id: str) -> str:
        """Retrieve a full abstract using the Scopus Abstract Retrieval API.

        Args:
            scopus_id (str): Scopus document identifier.

        Returns:
            str: The abstract text, or None if retrieval fails.
        """
        try:
            scp_doc = AbsDoc(scp_id=scopus_id)
            if scp_doc.read(self.client):
                return scp_doc.data.get('coredata', {}).get('dc:description', 'Abstract retrieval failed.')
            return None
        except Exception as e:
            print(f"      -> WARNING: Abstract retrieval failed. Error: {e}")
            return None

    def _format_paper(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Convert a Scopus search result to the standardized TALOS format.

        Args:
            result (dict): Raw result from the Scopus Search API.

        Returns:
            dict: Standardized paper dictionary, or None if formatting fails.
        """
        try:
            doi = result.get('prism:doi')
            url = f"https://doi.org/{doi}" if doi else result.get('prism:url', '#').replace("http://", "https://")
            scopus_id = result.get('dc:identifier', '').replace('SCOPUS_ID:', '')

            publication_year = None
            cover_date = result.get('prism:coverDate')
            if cover_date:
                try:
                    publication_year = datetime.strptime(cover_date, '%Y-%m-%d').year
                except ValueError: pass

            return {
                "doi": doi,
                "url": url,
                "scopus_id": scopus_id,
                "title": result.get('dc:title', 'N/A'),
                "authors_str": result.get('dc:creator', 'N/A'),
                "publication_year": publication_year,
                "abstract": result.get('dc:description', 'Elsevier does not provide an abstract in this call.'),
                "source": "Elsevier Scopus"
            }
        except Exception as e:
            print(f"   WARNING [Elsevier]: Failed to format an article: {e}")
            return None