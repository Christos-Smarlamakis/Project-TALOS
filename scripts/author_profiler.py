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
Module: author_profiler.py (v3.9 - Intelligent Input & Final)
Project: TALOS v3.1

Description:
Η τελική, πλήρως λειτουργική έκδοση του Unified Profiler.
- Ενσωματώνει "έξυπνη" ανίχνευση εισόδου: μπορεί να δεχτεί είτε όνομα
  συγγραφέα είτε απευθείας ORCID iD.
- Αν ανιχνεύσει ORCID iD, παρακάμπτει τη διαδικασία αναζήτησης/επιλογής
  και προχωρά απευθείας στη συλλογή δεδομένων.
- Εμπλουτίζει τη λίστα επιλογών με το ίδρυμα του συγγραφέα για εύκολη
  ταυτοποίηση.
- Είναι πλήρως συμβατή με Python 3.8+ και περιέχει όλες τις απαραίτητες
  εξαρτήσεις και διορθώσεις.
"""
import os
import sys
import requests
import json
import re
from dotenv import load_dotenv
from datetime import datetime
import questionary
from typing import Union, List, Dict, Any
from tqdm import tqdm

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

class UnifiedProfiler:
    def __init__(self, mailto_email: str):
        load_dotenv()
        self.mailto = mailto_email
        self.ss_api_key = os.getenv("SEMANTIC_SCHOLAR_API_KEY")
        self.orcid_api_base = "https://pub.orcid.org/v3.0/"
        self.openalex_base_url = "https://api.openalex.org/authors/"
        self.ss_base_url = "https://api.semanticscholar.org/graph/v1/author/"
        self.project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        self.reports_dir = os.path.join(self.project_root, "reports", "authors")
        os.makedirs(self.reports_dir, exist_ok=True)
        print("INFO: Unified Profiler v3.9 (Intelligent Input) αρχικοποιήθηκε.")

    def _is_orcid(self, identifier: str) -> bool:
        """Ελέγχει αν ένα string έχει τη μορφή ενός ORCID iD."""
        return re.match(r'^\d{4}-\d{4}-\d{4}-\d{3}[\dX]$', identifier.strip()) is not None

    def _query_api(self, url: str, source_name: str, headers: Dict[str, Any] = None, params: Dict[str, Any] = None) -> Union[Dict[str, Any], None]:
        """Κεντρική, ασφαλής μέθοδος για την εκτέλεση κλήσεων σε REST APIs."""
        try:
            response = requests.get(url, headers=headers, params=params, timeout=15)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"WARNING [{source_name}]: API call failed. Error: {e}")
            return None

    def _query_orcid_search(self, author_name: str) -> Union[List[Any], None]:
        """Αναζητά συγγραφείς στο ORCID με βάση το όνομα."""
        params = {'q': f'given-and-family-names:"{author_name}"'}
        data = self._query_api(f"{self.orcid_api_base}search/", "ORCID Search", headers={'Accept': 'application/json'}, params=params)
        return data.get('result') if data else None

    def _query_openalex(self, orcid_id: str) -> Union[Dict[str, Any], None]:
        """Ανακτά δεδομένα συγγραφέα από το OpenAlex μέσω του ORCID iD."""
        return self._query_api(f"{self.openalex_base_url}orcid:{orcid_id}?mailto={self.mailto}", "OpenAlex")
        
    def _get_doi_from_work(self, work_summary: dict) -> str:
        """Βοηθητική συνάρτηση για την εξαγωγή του DOI από τα εξωτερικά IDs."""
        ids = work_summary.get('external-ids', {}).get('external-id', [])
        for ext_id in ids:
            if ext_id.get('external-id-type') == 'doi':
                return f"https://doi.org/{ext_id.get('external-id-value', '')}"
        return ""

    def run(self, identifier: str) -> Union[str, None]:
        """
        Ενορχηστρώνει την πλήρη ροή, χειριζόμενη είτε ORCID iD είτε όνομα.
        """
        final_orcid_id = None

        if self._is_orcid(identifier):
            print(f"🔎 [1/5] ORCID iD detected: {identifier}. Skipping name search.")
            final_orcid_id = identifier
        else:
            print(f"\n🔎 [1/5] Searching ORCID for '{identifier}'...")
            orcid_results = self._query_orcid_search(identifier)
            if not orcid_results:
                print(f"❌ No results found in ORCID. Terminating.")
                return None
            
            if len(orcid_results) > 1:
                print(f"🔎 [2/5] Found {len(orcid_results)} potential profiles. Enriching data for disambiguation...")
                choices = []
                for res in tqdm(orcid_results, desc="Enriching results"):
                    orcid_id_res = res.get('orcid-identifier', {}).get('path')
                    if not orcid_id_res: continue
                    
                    oa_data = self._query_openalex(orcid_id_res)
                    institution = oa_data.get('last_known_institution', {}).get('display_name', 'Unknown Institution') if oa_data else 'Unknown Institution'
                    
                    given = res.get('given-names', {}).get('value', '')
                    family = res.get('family-names', {}).get('value', '')
                    display_name = f"{given} {family}".strip() or f"ID: {orcid_id_res}"
                    
                    choices.append({'name': f"{display_name}  --  [{institution}]", 'value': res})
                
                choice = questionary.select("Multiple authors found. Please choose the correct one:", choices=choices, use_indicator=True).ask()
                if not choice: return None
                selected_author_info = choice
            else:
                selected_author_info = orcid_results[0]
            
            final_orcid_id = selected_author_info['orcid-identifier']['path']
        
        if not final_orcid_id:
            print("❌ Identification failed. Terminating.")
            return None

        print(f"\n🔎 [3/5] Fetching full profile from ORCID ({final_orcid_id})...")
        person_details = self._query_api(f"{self.orcid_api_base}{final_orcid_id}/person", "ORCID Details", headers={'Accept': 'application/json'}) or {}
        works_data = self._query_api(f"{self.orcid_api_base}{final_orcid_id}/works", "ORCID Works", headers={'Accept': 'application/json'})
        works = works_data.get('group') if works_data else []

        given_name = person_details.get('name', {}).get('given-names', {}).get('value', '')
        family_name = person_details.get('name', {}).get('family-name', {}).get('value', '')
        verified_name = f"{given_name} {family_name}".strip() or final_orcid_id
        print(f"✔️ Verified: {verified_name}")

        print(f"\n🔎 [4/5] Fetching data from OpenAlex...")
        openalex_data = self._query_openalex(final_orcid_id)

        print(f"\n🔎 [5/5] Fetching metrics from Semantic Scholar...")
        ss_data = self._query_api(f"https://api.semanticscholar.org/graph/v1/author/search?query={requests.utils.quote(verified_name)}&fields=hIndex,citationCount", "Semantic Scholar")
        ss_data = ss_data['data'][0] if ss_data and ss_data.get('data') else None
        
        self.display_unified_dossier(verified_name, final_orcid_id, openalex_data, ss_data, works)
        self.export_to_markdown(identifier, verified_name, final_orcid_id, openalex_data, ss_data, works)
        
        return final_orcid_id

    def display_unified_dossier(self, name, orcid_id, oa_data, ss_data, works):
        """Εμφανίζει μια συνοπτική αναφορά στο τερματικό."""
        print("\n" + "="*60 + "\n      ** ACADEMIC DOSSIER (Unified Intel) **\n" + "="*60)
        print(f"\n👤 Name: \t\t{name or 'N/A'}")
        print(f"🆔 ORCID iD: \t{orcid_id} (✔️ Verified Ground Truth)")
        if oa_data: print(f"🏢 Institution: \t{oa_data.get('last_known_institution', {}).get('display_name', 'N/A')}")
        
        print("\n--- Metrics ---")
        if oa_data:
            print(f"  📊 h-index (OpenAlex): \t{oa_data.get('summary_stats', {}).get('h_index', 'N/A')}")
            print(f"  📈 Citations (OpenAlex): \t{oa_data.get('cited_by_count', 'N/A')}")
        if ss_data:
            print(f"  📊 h-index (Semantic Scholar): {ss_data.get('hIndex', 'N/A')}")
            print(f"  📈 Citations (Semantic Scholar): {ss_data.get('citationCount', 'N/A')}")
        
        if oa_data and oa_data.get('x_concepts'):
            print("\n--- Top Research Fields (OpenAlex) ---")
            for concept in oa_data.get('x_concepts', [])[:5]:
                print(f"  - {concept['display_name']} (Score: {concept['score']:.2f})")
        
        if works:
            print("\n--- Recent Publications (from ORCID) ---")
            # Στιβαρός έλεγχος για την ύπαρξη ημερομηνίας πριν την ταξινόμηση
            sortable_works = [w for w in works if w.get('work-summary') and w['work-summary'][0].get('publication-date') and w['work-summary'][0]['publication-date'].get('year')]
            sorted_works = sorted(sortable_works, key=lambda w: int(w['work-summary'][0]['publication-date']['year']['value']), reverse=True)
            for i, work_group in enumerate(sorted_works[:10]): 
                summary = work_group['work-summary'][0]
                title = summary.get('title', {}).get('title', {}).get('value', 'N/A')
                year = summary.get('publication-date', {}).get('year', {}).get('value', 'N/A')
                print(f"  {i+1}. [{year}] {title}")
        print("\n" + "="*60)

    def export_to_markdown(self, search_term, name, orcid_id, oa_data, ss_data, works):
        """Δημιουργεί και αποθηκεύει μια πλήρη, καλοформаρισμένη αναφορά Markdown."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = "".join(x for x in name if x.isalnum() or x in " _-").strip()
        filename = os.path.join(self.reports_dir, f"profiler_report_{safe_name}_{timestamp}.md")
        
        content = [
            f"# TALOS Profiler Report: {name}",
            f"_Report for search term '{search_term}' ({datetime.now().strftime('%d-%m-%Y %H:%M')})_\n",
            "## 1. Identity & Affiliation",
            f"- **Verified Name:** {name or 'N/A'}",
            f"- **ORCID iD:** [{orcid_id}](https://orcid.org/{orcid_id})",
        ]
        if oa_data:
            content.append(f"- **OpenAlex ID:** [{oa_data.get('id')}](https://openalex.org/{oa_data.get('id')})")
            content.append(f"- **Last Known Institution:** {oa_data.get('last_known_institution', {}).get('display_name', 'N/A')}")
        
        content.extend(["\n---\n", "## 2. Academic Metrics"])
        content.extend([
            "| Source             | h-index | Total Citations |", "|-------------------|---------|-----------------|",
            f"| OpenAlex          | {oa_data.get('summary_stats', {}).get('h_index', 'N/A') if oa_data else 'N/A'}    | {oa_data.get('cited_by_count', 'N/A') if oa_data else 'N/A'}           |",
            f"| Semantic Scholar  | {ss_data.get('hIndex', 'N/A') if ss_data else 'N/A'}    | {ss_data.get('citationCount', 'N/A') if ss_data else 'N/A'}           |",
        ])

        if oa_data and oa_data.get('x_concepts'):
            content.extend(["\n---\n", "## 3. Top Research Fields (from OpenAlex)"])
            for concept in oa_data.get('x_concepts', [])[:5]:
                content.append(f"- **{concept['display_name']}** (Score: {concept['score']:.2f})")
        
        content.extend(["\n---\n", "## 4. Recent Publications (Top 10 from ORCID)"])
        if works:
            sortable_works = [w for w in works if w.get('work-summary') and w['work-summary'][0].get('publication-date') and w['work-summary'][0]['publication-date'].get('year')]
            sorted_works = sorted(sortable_works, key=lambda w: int(w['work-summary'][0]['publication-date']['year']['value']), reverse=True)
            for work_group in sorted_works[:10]:
                summary = work_group['work-summary'][0]
                title = summary.get('title', {}).get('title', {}).get('value', 'N/A')
                year = summary.get('publication-date', {}).get('year', {}).get('value', 'N/A')
                doi_url = self._get_doi_from_work(summary)
                content.append(f"- **[{year}]** {title}")
                if doi_url: content.append(f"  - **DOI:** [{doi_url}]({doi_url})")
        else:
            content.append("- *(No publications found in this ORCID profile.)*")

        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write("\n".join(content))
            print(f"\nSUCCESS: Markdown report saved to:\n{filename}")
        except Exception as e:
            print(f"\nERROR: Could not save Markdown report: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/author_profiler.py \"Author Name or ORCID iD\"")
        sys.exit(1)
    
    author_identifier = " ".join(sys.argv[1:])
    
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    config_path = os.path.join(project_root, 'config.json')
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
        mailto = config.get("mailto")
        if not mailto:
            raise ValueError("'mailto' email is missing from config.json and is required for OpenAlex.")
    except (FileNotFoundError, ValueError) as e:
        print(f"FATAL ERROR: {e}")
        sys.exit(1)
        
    profiler = UnifiedProfiler(mailto_email=mailto)
    selected_orcid_id = profiler.run(author_identifier)
    
    if selected_orcid_id:
        print(f"SELECTED_ORCID_ID:{selected_orcid_id}")