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
Module: arxiv_source.py (v3.8 - Config Driven Multi-Query)
Project: TALOS v4.2

Description:
Η απόλυτη έκδοση του "Πράκτορα" για το arXiv.
- Διορθώνει το αρχιτεκτονικό λάθος των hardcoded όρων.
- Διαβάζει το 'arxiv_query' από το config.json και το μετατρέπει δυναμικά
  σε λίστα όρων, επιτρέποντας στο σύστημα να αλλάζει θέμα (Προφίλ/Πυθία).
- Διατηρεί τη στρατηγική Multi-Query για να παρακάμπτει τα bugs του API.
"""
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any
import time

class ArxivSource:
    def __init__(self, config: Dict[str, Any]):
        # 1. Διαβάζουμε το query string από το config
        raw_query = config.get("arxiv_query", 'all:"mission planning"')
        
        # 2. Το μετατρέπουμε δυναμικά σε λίστα για τη στρατηγική Multi-Query
        # Αφαιρούμε παρενθέσεις και χωρίζουμε με το " OR "
        clean_query = raw_query.replace("(", "").replace(")", "")
        self.search_terms = [term.strip() for term in clean_query.split(" OR ") if term.strip()]
        
        # Αν για κάποιο λόγο η λίστα βγει κενή, κρατάμε το raw query ως μοναδικό όρο
        if not self.search_terms:
            self.search_terms = [raw_query]

        self.days_to_search = config.get("days_to_search_daily", 1)
        
        # Υπολογίζουμε το όριο ανά όρο
        total_max = config.get("max_results_config", {}).get("arxiv", 1000)
        self.max_results_per_term = max(10, total_max // len(self.search_terms))
        
        self.base_url = "http://export.arxiv.org/api/query"
        print(f"INFO: ArxivSource (v3.8 - Config Driven) αρχικοποιήθηκε με {len(self.search_terms)} όρους.")

    def fetch_new_papers(self) -> List[Dict[str, Any]]:
        print(f"-> Αναζήτηση στο arXiv (Multi-Query Strategy)...")
        
        all_papers_dict = {} # Λεξικό για αυτόματη αφαίρεση διπλοτύπων
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=self.days_to_search)

        for term in self.search_terms:
            # print(f"   - Αναζήτηση για: '{term}'...") # Προαιρετικό log για λιγότερο θόρυβο
            
            start = 0
            page_size = 100
            term_papers_count = 0

            while term_papers_count < self.max_results_per_term:
                params = {
                    'search_query': term,
                    'start': start,
                    'max_results': page_size,
                    'sortBy': 'submittedDate',
                    'sortOrder': 'descending'
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
                        published_date = datetime.fromisoformat(entry.find('atom:published', namespace).text.replace('Z', '+00:00'))
                        
                        # Έλεγχος ημερομηνίας
                        if published_date < cutoff_date:
                            stop_for_this_term = True
                            break
                        
                        formatted_paper = self._format_paper(entry, namespace, published_date)
                        if formatted_paper and formatted_paper['url']:
                            # Αν το άρθρο δεν υπάρχει ήδη, το προσθέτουμε
                            if formatted_paper['url'] not in all_papers_dict:
                                all_papers_dict[formatted_paper['url']] = formatted_paper
                                term_papers_count += 1

                    if stop_for_this_term or len(entries) < page_size:
                        break
                    
                    start += page_size
                    time.sleep(2) # Μικρή καθυστέρηση ανάμεσα στις σελίδες
                except requests.exceptions.RequestException as e:
                    print(f"     ERROR [arXiv]: Σφάλμα στο query '{term}': {e}")
                    break
            
            # Καθυστέρηση ανάμεσα στους όρους για να μην "χτυπήσουμε" το API
            time.sleep(1)
        
        final_papers = list(all_papers_dict.values())
        print(f"   SUCCESS [arXiv]: Βρέθηκαν {len(final_papers)} μοναδικά άρθρα.")
        return final_papers

    def _format_paper(self, entry: ET.Element, ns: Dict[str, str], published_date: datetime) -> Dict[str, Any]:
        try:
            url = entry.find('atom:id', ns).text
            doi_element = entry.find('arxiv:doi', {'arxiv': 'http://arxiv.org/schemas/atom'})
            doi = doi_element.text if doi_element is not None else None
            authors_elements = entry.findall('atom:author', ns)
            authors_str = ", ".join([author.find('atom:name', ns).text for author in authors_elements])
            return {
                'doi': doi, 'url': url, 'title': entry.find('atom:title', ns).text.strip(),
                'authors_str': authors_str, 'publication_year': published_date.year,
                'abstract': entry.find('atom:summary', ns).text.strip().replace('\n', ' '), 'source': 'arXiv'
            }
        except Exception as e:
            print(f"   WARNING [arXiv]: Αποτυχία μορφοποίησης: {e}")
            return None