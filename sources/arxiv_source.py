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
Module: arxiv_source.py
Project: TALOS v5.3.7

Description:
    Search agent for the arXiv API (export.arxiv.org). Reads the search query
    dynamically from config.json and splits it into multiple sub-queries
    (by "OR") to work around API bugs with complex boolean expressions.
    Fetches new papers using the Atom XML API with date filtering, sorting by
    submission date descending. Does not require an API key.
"""
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any
import time


class ArxivSource:
    """Search agent for the arXiv API.

    Dynamically splits the configured query into multiple search terms
    for reliability, then fetches papers via the Atom API with pagination
    and date filtering.

    Attributes:
        search_terms (list of str): Individual search terms from the config query.
        days_to_search (int): Lookback window in days.
        max_results_per_term (int): Maximum results per sub-query.
        base_url (str): arXiv API base URL.
    """

    def __init__(self, config: Dict[str, Any]):
        """Initialize the arXiv agent from configuration.

        Args:
            config (dict): Application configuration dictionary containing
                ``arxiv_query``, ``days_to_search_daily``, and ``max_results_config``.
        """
        raw_query = config.get("arxiv_query", 'all:"mission planning"')
        clean_query = raw_query.replace("(", "").replace(")", "")
        self.search_terms = [term.strip() for term in clean_query.split(" OR ") if term.strip()]
        if not self.search_terms:
            self.search_terms = [raw_query]

        self.days_to_search = config.get("days_to_search_daily", 1)
        total_max = config.get("max_results_config", {}).get("arxiv", 1000)
        self.max_results_per_term = max(10, total_max // len(self.search_terms))
        self.base_url = "http://export.arxiv.org/api/query"
        print(f"INFO: ArxivSource initialized with {len(self.search_terms)} terms.")

    def fetch_new_papers(self) -> List[Dict[str, Any]]:
        """Fetch recent papers from arXiv using the multi-query strategy.

        Returns:
            list of dict: Standardized paper dictionaries.
        """
        print(f"-> Searching arXiv (Multi-Query Strategy)...")
        all_papers_dict = {}
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=self.days_to_search)

        for term in self.search_terms:
            start = 0
            page_size = 100
            term_papers_count = 0

            while term_papers_count < self.max_results_per_term:
                params = {
                    'search_query': term, 'start': start, 'max_results': page_size,
                    'sortBy': 'submittedDate', 'sortOrder': 'descending'
                }
                try:
                    response = requests.get(self.base_url, params=params, timeout=30)
                    response.raise_for_status()
                    root = ET.fromstring(response.content)
                    namespace = {'atom': 'http://www.w3.org/2005/Atom'}
                    entries = root.findall('atom:entry', namespace)
                    if not entries: break

                    stop_for_this_term = False
                    for entry in entries:
                        published_date = datetime.fromisoformat(
                            entry.find('atom:published', namespace).text.replace('Z', '+00:00'))
                        if published_date < cutoff_date:
                            stop_for_this_term = True
                            break
                        formatted_paper = self._format_paper(entry, namespace, published_date)
                        if formatted_paper and formatted_paper['url']:
                            if formatted_paper['url'] not in all_papers_dict:
                                all_papers_dict[formatted_paper['url']] = formatted_paper
                                term_papers_count += 1

                    if stop_for_this_term or len(entries) < page_size:
                        break
                    start += page_size
                    time.sleep(2)
                except requests.exceptions.RequestException as e:
                    print(f"     ERROR [arXiv]: Error for query '{term}': {e}")
                    break
            time.sleep(1)

        final_papers = list(all_papers_dict.values())
        print(f"   SUCCESS [arXiv]: Found {len(final_papers)} unique papers.")
        return final_papers

    def _format_paper(self, entry: ET.Element, ns: Dict[str, str],
                      published_date: datetime) -> Dict[str, Any]:
        """Convert an arXiv Atom entry to the standardized TALOS format.

        Args:
            entry (ET.Element): Raw Atom entry element.
            ns (dict): XML namespace mapping.
            published_date (datetime): Parsed publication date.

        Returns:
            dict: Standardized paper dictionary, or None if formatting fails.
        """
        try:
            url = entry.find('atom:id', ns).text
            doi_element = entry.find('arxiv:doi', {'arxiv': 'http://arxiv.org/schemas/atom'})
            doi = doi_element.text if doi_element is not None else None
            authors_elements = entry.findall('atom:author', ns)
            authors_str = ", ".join([author.find('atom:name', ns).text for author in authors_elements])
            return {
                'doi': doi, 'url': url,
                'title': entry.find('atom:title', ns).text.strip(),
                'authors_str': authors_str,
                'publication_year': published_date.year,
                'abstract': entry.find('atom:summary', ns).text.strip().replace('\n', ' '),
                'source': 'arXiv'
            }
        except Exception as e:
            print(f"   WARNING [arXiv]: Formatting failed: {e}")
            return None