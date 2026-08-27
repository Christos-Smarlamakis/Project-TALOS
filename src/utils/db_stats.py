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
Module: db_stats.py (v1.0 - The Metrics Update)
Project: TALOS v5.10.0

Description:
Ένα εργαλείο αναφοράς που παρέχει μια γρήγορη, οπτική επισκόπηση της
κατάστασης της βάσης δεδομένων. Εμφανίζει τον όγκο των δεδομένων, την
προέλευσή τους και την ποιότητά τους (missing DOIs, embeddings).
"""
import sys
import os, sys
_P = os.path.abspath(os.path.dirname(__file__))
while _P and not os.path.exists(os.path.join(_P, 'talos.py')):
    _P = os.path.dirname(_P)
if _P: sys.path.insert(0, _P)
import os

# Προσθέτουμε το root path
from src.core.database_manager import DatabaseManager, get_active_profile_db_path

def print_header(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def optimize_database(db_path):
    """Run a SQLite integrity check and VACUUM maintenance pass.

    Executes ``PRAGMA integrity_check;`` to validate the on-disk B-tree
    structure, then ``VACUUM;`` to reclaim free pages and defragment the
    database file. Reports clean console metrics for the operation.

    Args:
        db_path (str): Path to the SQLite database file to optimize.

    Returns:
        dict: Summary with ``ok``, ``integrity``, ``size_before``,
            ``size_after``, and ``freed_bytes`` keys.
    """
    import sqlite3

    report = {
        "ok": False,
        "integrity": "unknown",
        "size_before": 0,
        "size_after": 0,
        "freed_bytes": 0,
    }

    if not db_path or not os.path.exists(db_path):
        print(f"[DB-OPTIMIZE] Skipped: database not found at {db_path}")
        return report

    try:
        report["size_before"] = os.path.getsize(db_path)
    except OSError:
        pass

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        result = cursor.execute("PRAGMA integrity_check;").fetchone()
        report["integrity"] = str(result[0]) if result else "unknown"
        cursor.execute("VACUUM;")
        conn.commit()
        conn.close()
        report["ok"] = True
    except Exception as exc:  # pragma: no cover - defensive
        print(f"[DB-OPTIMIZE] Failed: {exc}")
        return report

    try:
        report["size_after"] = os.path.getsize(db_path)
    except OSError:
        pass
    report["freed_bytes"] = report["size_before"] - report["size_after"]

    print("[DB-OPTIMIZE] Integrity check:", report["integrity"])
    print(f"[DB-OPTIMIZE] Size before:  {report['size_before']} bytes")
    print(f"[DB-OPTIMIZE] Size after:   {report['size_after']} bytes")
    print(f"[DB-OPTIMIZE] Freed:        {report['freed_bytes']} bytes")
    return report


def main():
    db = DatabaseManager()
    print("\nΥπολογισμός στατιστικών βάσης δεδομένων...")
    stats = db.get_database_statistics()
    
    # --- Γενική Εικόνα ---
    print_header("ΓΕΝΙΚΗ ΕΙΚΟΝΑ (OVERVIEW)")
    print(f"📚 Συνολικά Άρθρα:      {stats['total_papers']}")
    elite_pct = (stats['elite_papers'] / stats['total_papers'] * 100) if stats['total_papers'] > 0 else 0.0
    print(f"💎 Elite Papers (>7/10): {stats['elite_papers']} ({elite_pct:.1f}%)")
    print(f"🧠 Μέσος Όρος Score:    {stats['avg_score']} / 10")
    
    # --- Κατανομή ανά Πηγή ---
    print_header("ΚΑΤΑΝΟΜΗ ΑΝΑ ΠΗΓΗ (BY SOURCE)")
    print(f"{'Πηγή':<30} | {'Πλήθος':<10}")
    print("-" * 45)
    for source, count in stats['by_source']:
        print(f"{source:<30} | {count:<10}")
        
    # --- Υγεία Δεδομένων ---
    print_header("ΥΓΕΙΑ ΔΕΔΟΜΕΝΩΝ (DATA HEALTH)")
    print(f"✅ Με DOI:              {stats['total_papers'] - stats['missing_doi']}")
    print(f"⚠️ Χωρίς DOI:           {stats['missing_doi']}")
    print(f"🧠 Με Embeddings:       {stats['embedded_papers']}")
    if stats['total_papers'] > stats['embedded_papers']:
        diff = stats['total_papers'] - stats['embedded_papers']
        print(f"   -> Σύσταση: Τρέξτε το 'embedding_generator.py' για {diff} άρθρα.")
    
    print("\n")

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="TALOS database statistics and optimizer."
    )
    parser.add_argument(
        "--optimize",
        action="store_true",
        help="Run PRAGMA integrity_check and VACUUM on the active profile database.",
    )
    parser.add_argument(
        "--db",
        default=None,
        help="Optional explicit database path (defaults to the active profile DB).",
    )
    args = parser.parse_args()

    if args.optimize:
        optimize_database(args.db or get_active_profile_db_path())
    else:
        main()
        input("Press Enter to exit.")