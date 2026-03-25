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
Module: author_trajectory_analyzer.py (v3.2 - Unified Input)
Project: TALOS v3.1

Description:
Η τελική, πλήρως λειτουργική έκδοση του αναλυτή ερευνητικής πορείας.
- Είναι πλέον "ευφυής" και μπορεί να δεχτεί ως είσοδο είτε ένα ORCID iD
  είτε ένα όνομα συγγραφέα.
- Αν δοθεί όνομα, καλεί εσωτερικά τον `author_profiler` για να εκτελέσει
  την ταυτοποίηση πριν συνεχίσει με την ανάλυση.
"""
import os
import re
import sys
import requests
import json
from dotenv import load_dotenv
from datetime import datetime
from typing import Tuple, Union, List, Dict, Any


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.ai_manager import AIManager
# Νέα εισαγωγή: χρειαζόμαστε τον profiler για την ταυτοποίηση
from scripts.author_profiler import UnifiedProfiler

class TrajectoryAnalyzer:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.ai_manager = AIManager(config)
        self.orcid_api_base = "https://pub.orcid.org/v3.0/"
        self.project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        self.reports_dir = os.path.join(self.project_root, "reports", "authors")
        os.makedirs(self.reports_dir, exist_ok=True)
        print("INFO: Trajectory Analyzer v3.2 (Unified Input) αρχικοποιήθηκε.")

    def _query_api(self, url: str, source_name: str, headers: Dict[str, Any] = None) -> Union[Dict[str, Any], None]:
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"ERROR [{source_name}]: Η κλήση απέτυχε. Σφάλμα: {e}")
            return None

    def get_author_data(self, orcid_id: str) -> Tuple[Union[str, None], Union[List[Any], None]]:
        person_details = self._query_api(f"{self.orcid_api_base}{orcid_id}/person", "ORCID Details", headers={'Accept': 'application/json'})
        if not person_details: return None, None
        given = person_details.get('name', {}).get('given-names', {}).get('value', '')
        family = person_details.get('name', {}).get('family-name', {}).get('value', '')
        author_name = f"{given} {family}".strip()
        works_data = self._query_api(f"{self.orcid_api_base}{orcid_id}/works", "ORCID Works", headers={'Accept': 'application/json'})
        return author_name, works_data.get('group') if works_data else []

    def analyze_trajectory(self, author_name: str, works: List[Any]) -> str:
        current_year = datetime.now().year
        recent_works = []
        for work_group in works:
            summary = work_group.get('work-summary', [{}])[0]
            pub_date = summary.get('publication-date')
            if not pub_date or not pub_date.get('year'): continue
            try:
                year = int(pub_date['year']['value'])
                if current_year - 5 <= year <= current_year:
                    title = summary.get('title', {}).get('title', {}).get('value', 'N/A')
                    recent_works.append(f"[{year}] {title}")
            except (ValueError, TypeError): continue
        if not recent_works:
            return "Δεν βρέθηκαν πρόσφατες δημοσιεύσεις (τελευταία 5 έτη) για ανάλυση."
        publications_list_str = "\n".join(recent_works)
        system_prompt = self.config["trajectory_analyzer_prompt"]
        user_prompt = f"// AUTHOR & PUBLICATIONS TO ANALYZE //\nAuthor: {author_name}\n\n{publications_list_str}"
        full_prompt = system_prompt + "\n\n" + user_prompt
        return self.ai_manager.analyze_generic_text(full_prompt)
        
    def _is_orcid(self, identifier: str) -> bool:
        """Ελέγχει αν ένα string μοιάζει με ORCID iD."""
        return re.match(r'^\d{4}-\d{4}-\d{4}-\d{3}[\dX]$', identifier) is not None

    def run(self, identifier: str):
        """
        Ενορχηστρώνει την πλήρη ροή, χειριζόμενη είτε ORCID iD είτε όνομα.
        """
        orcid_id = None
        # --- ΝΕΑ ΛΟΓΙΚΗ ΑΝΙΧΝΕΥΣΗΣ ---
        if self._is_orcid(identifier):
            print("INFO: Ανιχνεύτηκε ORCID iD. Παράκαμψη αναζήτησης ονόματος.")
            orcid_id = identifier
        else:
            print(f"INFO: Ανιχνεύτηκε όνομα συγγραφέα. Εκκίνηση του Profiler για ταυτοποίηση...")
            profiler = UnifiedProfiler(mailto_email=self.config.get("mailto"))
            # Καλούμε τον profiler για να βρει το ORCID iD
            orcid_id = profiler.run(identifier)

        if not orcid_id:
            print("❌ Αποτυχία ταυτοποίησης του συγγραφέα. Η ανάλυση πορείας δεν μπορεί να συνεχιστεί.")
            return

        print(f"\n--- Έναρξη Ανάλυσης Πορείας για το ORCID: {orcid_id} ---")
        author_name, works = self.get_author_data(orcid_id)
        if author_name is None or works is None:
            print(f"❌ Αποτυχία ανάκτησης δεδομένων από το ORCID. Τερματισμός.")
            return
        if not works:
            print(f"❌ Δεν βρέθηκαν δημοσιεύσεις για τον/την '{author_name}'.")
            return

        print(f"✔️ Βρέθηκαν {len(works)} δημοσιεύσεις για τον/την '{author_name}'.")
        print(f"🔎 Αποστολή στο AI για στρατηγική ανάλυση...")
        analysis_report = self.analyze_trajectory(author_name, works)
        
        # Παρουσίαση και αποθήκευση της αναφοράς
        print("\n" + "="*80 + "\n      ** TALOS: ΑΝΑΦΟΡΑ ΑΝΑΛΥΣΗΣ ΕΡΕΥΝΗΤΙΚΗΣ ΠΟΡΕΙΑΣ **\n" + "="*80)
        print(f"\nΑνάλυση για: {author_name} (ORCID: {orcid_id})\n" + "-"*80)
        print(analysis_report)
        print("\n" + "="*80)
        
        safe_name = "".join(x for x in author_name if x.isalnum() or x in " _-").strip()
        timestamp = datetime.now().strftime("%Y%m%d")
        report_filename = os.path.join(self.reports_dir, f"trajectory_report_{safe_name}_{timestamp}.md")
        try:
            with open(report_filename, "w", encoding="utf-8") as f:
                f.write(f"# Ανάλυση Ερευνητικής Πορείας: {author_name}\n")
                f.write(f"_ORCID iD: [{orcid_id}](https://orcid.org/{orcid_id})_\n")
                f.write(f"_Αναφορά από TALOS στις {datetime.now().strftime('%d-%m-%Y %H:%M')}._\n\n---\n\n")
                f.write(analysis_report)
            print(f"✔️ Η αναφορά αποθηκεύτηκε στο:\n{report_filename}")
        except IOError as e:
            print(f"ERROR: Αποτυχία αποθήκευσης αναφοράς: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("ERROR: Πρέπει να δώσετε ένα ORCID iD ή ένα όνομα συγγραφέα σε εισαγωγικά.")
        print("Παράδειγμα (ORCID): python scripts/author_trajectory_analyzer.py 0000-0002-1825-0097")
        print("Παράδειγμα (Όνομα): python scripts/author_trajectory_analyzer.py \"Demis Hassabis\"")
        sys.exit(1)
        
    author_identifier = " ".join(sys.argv[1:])
    
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    config_path = os.path.join(project_root, 'config.json')
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
        if "trajectory_analyzer_prompt" not in config:
            raise ValueError("Το 'trajectory_analyzer_prompt' λείπει από το config.json.")
        if "mailto" not in config:
             raise ValueError("Το 'mailto' email λείπει από το config.json.")
    except (FileNotFoundError, ValueError) as e:
        print(f"FATAL ERROR: {e}")
        sys.exit(1)

    analyzer = TrajectoryAnalyzer(config=config)
    analyzer.run(author_identifier)