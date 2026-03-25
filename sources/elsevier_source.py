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
Module: elsevier_source.py (v2.1 - Abstract Retrieval Fix)
Project: TALOS v3.2
Description:
Διορθώνει οριστικά το σφάλμα κατά την ανάκτηση της περίληψης, προσαρμόζοντας
την κλήση στη σωστή σύνταξη της βιβλιοθήκης elsapy. Πλέον χρησιμοποιεί το
scopus_id για να αρχικοποιήσει το αντικείμενο AbsDoc, όπως απαιτείται.
"""
import os
from datetime import datetime, timedelta
from elsapy.elsclient import ElsClient
from elsapy.elssearch import ElsSearch
from elsapy.elsdoc import AbsDoc
from typing import List, Dict, Any

class ElsevierSource:
    def __init__(self, config: Dict[str, Any]):
        self.api_key = os.getenv("ELSEVIER_API_KEY")
        self.inst_token = os.getenv("ELSEVIER_INST_TOKEN")
        if not self.api_key or not self.inst_token:
            raise ValueError("Elsevier API keys not found in .env file.")
        self.client = ElsClient(self.api_key, inst_token=self.inst_token)
        self.query = config.get("elsevier_query", "TITLE-ABS-KEY(robotics)")
        self.days_to_search = config.get("days_to_search_daily", 1)
        self.total_max_results = config.get("max_results_config", {}).get("elsevier", 200) 
        print("INFO: ElsevierSource (v2.1 - Abstract Fix) initialized.")

    def fetch_new_papers(self) -> List[Dict[str, Any]]:
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
                    # Αν η περίληψη λείπει και έχουμε Scopus ID, προσπαθούμε να την εμπλουτίσουμε
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
        """
        Ανακτά την περίληψη ενός άρθρου χρησιμοποιώντας το Scopus ID του.
        """
        # --- Η ΟΡΙΣΤΙΚΗ ΔΙΟΡΘΩΣΗ ΕΙΝΑΙ ΕΔΩ ---
        try:
            # Δημιουργούμε το αντικείμενο AbsDoc με το scp_id, όπως δείχνει η τεκμηρίωση
            scp_doc = AbsDoc(scp_id=scopus_id)
            if scp_doc.read(self.client):
                # Το coredata->dc:description περιέχει την περίληψη
                return scp_doc.data.get('coredata', {}).get('dc:description', 'Abstract retrieval failed.')
            return None
        except Exception as e:
            print(f"      -> WARNING: Abstract retrieval failed. Error: {e}")
            return None

    def _format_paper(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Μετατρέπει ένα αποτέλεσμα από το Scopus Search API στην τυποποιημένη μορφή του TALOS.
        """
        try:
            doi = result.get('prism:doi')
            url = f"https://doi.org/{doi}" if doi else result.get('prism:url', '#').replace("http://", "https://")
            # Εξάγουμε το Scopus ID καθαρό (χωρίς το "SCOPUS_ID:")
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
                "scopus_id": scopus_id, # Το χρειαζόμαστε για τον εμπλουτισμό
                "title": result.get('dc:title', 'N/A'),
                "authors_str": result.get('dc:creator', 'N/A'),
                "publication_year": publication_year,
                "abstract": result.get('dc:description', 'Elsevier does not provide an abstract in this call.'),
                "source": "Elsevier Scopus"
            }
        except Exception as e:
            print(f"   WARNING [Elsevier]: Failed to format an article: {e}")
            return None