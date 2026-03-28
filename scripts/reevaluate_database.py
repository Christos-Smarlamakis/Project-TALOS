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
Module: reevaluate_database.py (v5.0 - Quad-Layer Update)
Project: TALOS v4.0

Description:
Η πλήρως αναβαθμισμένη έκδοση του script επανα-αξιολόγησης για την v4.0.
- Υποστηρίζει την αρχιτεκτονική 4 επιπέδων (Strategic, Operational, Tactical, Playground).
- Χρησιμοποιεί την 'ai_manager.evaluate_paper_json()' με το νέο prompt.
- Εμφανίζει αναλυτικά logs και για τα 4 scores.
- Διαβάζει την καθυστέρηση από το config για ασφάλεια (Rate Limiting).
"""
import os
import sys
import json
import time
from datetime import timedelta
import questionary

# Προσθέτουμε το root του project στο path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.database_manager import DatabaseManager
from core.ai_manager import AIManager

def load_configuration():
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    config_path = os.path.join(project_root, 'config.json')
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"FATAL: Δεν ήταν δυνατή η φόρτωση του config.json. Σφάλμα: {e}")
        sys.exit(1)

def main():
    print("--- ΕΝΑΡΞΗ ΕΞΥΠΝΗΣ ΕΠΑΝΑ-ΑΞΙΟΛΟΓΗΣΗΣ (v5.0 - Quad-Layer) ---")
    
    config = load_configuration()
    ai_manager = AIManager(config)
    db_manager = DatabaseManager() # Αυτό θα δημιουργήσει/ελέγξει τις στήλες

    # Ρυθμίσεις
    BATCH_LIMIT = config.get("api_call_limit_flash", 950)
    DAYS_WINDOW = config.get("reevaluation_days_window", 7)
    REQUEST_DELAY = config.get("ai_request_delay", 5)

    print(f"\nINFO: Αναζήτηση για άρθρα που δεν έχουν αξιολογηθεί τις τελευταίες {DAYS_WINDOW} ημέρες...")
    # Σημείωση: Αν μόλις έτρεξες το upgrade_to_v4.py, όλα τα last_evaluated_at είναι NULL,
    # οπότε θα τα φέρει όλα.
    papers_to_update = db_manager.get_papers_not_recently_evaluated(DAYS_WINDOW, BATCH_LIMIT)

    if not papers_to_update:
        print(f"\nSUCCESS: Δεν βρέθηκαν άρθρα προς ενημέρωση. Η βάση είναι πλήρως συγχρονισμένη.")
        return

    total_to_recalibrate = len(papers_to_update)
    print(f"\nΒρέθηκαν {total_to_recalibrate} άρθρα προς επανα-αξιολόγηση (Quad-Layer).")
    
    if not questionary.confirm(f"Θα γίνει επανα-αξιολόγηση των πρώτων {total_to_recalibrate} άρθρων. Συνέχεια;", default=False).ask():
        print("Η διαδικασία ακυρώθηκε.")
        return

    updated_count = 0
    for i, paper in enumerate(papers_to_update):
        # Το paper είναι tuple: (id, title, abstract, overall_score)
        paper_id = paper[0]
        title = paper[1]
        abstract = paper[2]
        old_score = paper[3] if paper[3] is not None else 0.0

        print(f"-> Επεξεργασία {i+1}/{total_to_recalibrate}: '{title[:60]}...' (Παλιό score: {old_score:.2f})")

        content_for_ai = f"Title: {title}\nAbstract: {abstract}"
        
        # Χρησιμοποιούμε το 'flash' model με το ΝΕΟ prompt (που έχει 4 scores)
        evaluation_data = ai_manager.evaluate_paper_json(content_for_ai, model_type='flash')
        
        if evaluation_data:
            db_manager.update_paper_evaluation(paper_id, evaluation_data)
            updated_count += 1
            
            # Logging για τα 4 scores
            scores = evaluation_data.get('scores', {})
            s = scores.get('strategic', 0)
            o = scores.get('operational', 0)
            t = scores.get('tactical', 0)
            p = scores.get('playground', 0)
            new_overall = evaluation_data.get('overall_score', 0)
            
            print(f"   SUCCESS: Νέα Scores [Str:{s} | Opr:{o} | Tac:{t} | Sim:{p}] -> Overall: {new_overall:.2f}")
        else:
            print(f"   WARNING: Η ανάλυση απέτυχε. Παράλειψη.")
        
        time.sleep(REQUEST_DELAY)

    print("\n" + "="*50)
    print("  Η ΣΥΝΕΔΡΙΑ ΕΠΑΝΑ-ΑΞΙΟΛΟΓΗΣΗΣ ΟΛΟΚΛΗΡΩΘΗΚΕ")
    print(f"  > Ενημερώθηκαν: {updated_count} άρθρα.")
    print("="*50)

if __name__ == "__main__":
    main()