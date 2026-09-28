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
Module: reevaluate_database.py (v5.13.0 - Concurrent Cognitive Re-Evaluation Pool)
Project: TALOS v5.13.0

Description:
Η πλήρως αναβαθμισμένη έκδοση του script επανα-αξιολόγησης για την v4.0.
- Υποστηρίζει την αρχιτεκτονική 4 επιπέδων (Strategic, Operational, Tactical, Playground).
- Χρησιμοποιεί την 'ai_manager.evaluate_paper_json()' με το νέο prompt.
- Εμφανίζει αναλυτικά logs και για τα 4 scores.
- Διαβάζει την καθυστέρηση από το config για ασφάλεια (Rate Limiting).
"""
import os
import sys
import os, sys
_P = os.path.abspath(os.path.dirname(__file__))
while _P and not os.path.exists(os.path.join(_P, 'talos.py')):
    _P = os.path.dirname(_P)
if _P: sys.path.insert(0, _P)
import json
import time
from datetime import timedelta, datetime
import questionary
from src.utils.ui_theme import TALOS_QUESTIONARY_STYLE

# Προσθέτουμε το root του project στο path
from src.core.database_manager import DatabaseManager
from src.core.ai_manager import AIManager
from src.utils.snapshot_manager import snapshot_database

def load_configuration():
    project_root = _P if _P else os.getcwd()
    config_path = os.path.join(project_root, 'config.json')
    if not os.path.exists(config_path):
        config_path = os.path.join(project_root, 'config.template.json')
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"FATAL: Δεν ήταν δυνατή η φόρτωση του config.json. Σφάλμα: {e}")
        sys.exit(1)

def _apply_evaluation_batch(db_manager, updates):
    """Persist a batch of re-evaluations on a single WAL connection.

    Opens one connection (WAL is enabled by the DatabaseManager connection
    factory) and applies every UPDATE in the batch before issuing a single
    commit. This keeps the LLM-heavy re-evaluation pipeline from blocking on
    per-row transaction commits and reduces SQLite write contention.

    Args:
        db_manager (DatabaseManager): Active database manager.
        updates (list of tuple): List of (paper_id, evaluation_data) pairs.
    """
    sql = """UPDATE papers SET strategic_score=?,operational_score=?,tactical_score=?,
        playground_score=?,overall_score=?,evaluation_reasoning=?,
        evaluation_contribution=?,evaluation_utilization=?,
        suggested_tags=?,suggested_folder=?,suggested_discord_channel=?,
        last_evaluated_at=? WHERE id=?"""
    conn = db_manager._connect()
    try:
        cursor = conn.cursor()
        for paper_id, evaluation_data in updates:
            scores = evaluation_data.get('scores', {})
            tags_str = ','.join(evaluation_data.get('tags', []))
            overall_score = evaluation_data.get('overall_score') or db_manager._calculate_overall_score(scores)
            params = (scores.get('strategic', 0), scores.get('operational', 0),
                      scores.get('tactical', 0), scores.get('playground', 0), overall_score,
                      evaluation_data.get('reasoning', ''), evaluation_data.get('contribution', ''),
                      evaluation_data.get('utilization', ''), tags_str,
                      evaluation_data.get('folder', ''), evaluation_data.get('discord_channel', ''),
                      datetime.now(), paper_id)
            cursor.execute(sql, params)
        conn.commit()
    finally:
        conn.close()

def main():
    print("--- ΕΝΑΡΞΗ ΕΞΥΠΝΗΣ ΕΠΑΝΑ-ΑΞΙΟΛΟΓΗΣΗΣ (v5.13.0 - Concurrent Pool) ---")
    
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
    
    if not questionary.confirm(f"Θα γίνει επανα-αξιολόγηση των πρώτων {total_to_recalibrate} άρθρων. Συνέχεια;", default=False, style=TALOS_QUESTIONARY_STYLE).ask():
        print("Η διαδικασία ακυρώθηκε.")
        return

    snapshot_database()

    # -- v5.13.0: concurrent cognitive re-evaluation pool + batched WAL commits.
    papers_for_eval = [
        {"_id": paper[0], "title": paper[1], "abstract": paper[2]}
        for paper in papers_to_update
    ]

    BATCH_SIZE = 25
    updated_count = 0
    evaluated = ai_manager.batch_evaluate_papers(papers_for_eval, max_workers=None)

    pending = []
    for paper, evaluation_data in evaluated:
        paper_id = paper["_id"]
        if evaluation_data:
            pending.append((paper_id, evaluation_data))
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
        if len(pending) >= BATCH_SIZE:
            _apply_evaluation_batch(db_manager, pending)
            pending = []
    if pending:
        _apply_evaluation_batch(db_manager, pending)

    print("\n" + "="*50)
    print("  Η ΣΥΝΕΔΡΙΑ ΕΠΑΝΑ-ΑΞΙΟΛΟΓΗΣΗΣ ΟΛΟΚΛΗΡΩΘΗΚΕ")
    print(f"  > Ενημερώθηκαν: {updated_count} άρθρα.")
    print("="*50)

if __name__ == "__main__":
    main()