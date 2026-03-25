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
Project: TALOS v3.2.1

Description:
Ένα εργαλείο αναφοράς που παρέχει μια γρήγορη, οπτική επισκόπηση της
κατάστασης της βάσης δεδομένων. Εμφανίζει τον όγκο των δεδομένων, την
προέλευσή τους και την ποιότητά τους (missing DOIs, embeddings).
"""
import sys
import os

# Προσθέτουμε το root path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.database_manager import DatabaseManager

def print_header(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def main():
    db = DatabaseManager()
    print("\nΥπολογισμός στατιστικών βάσης δεδομένων...")
    stats = db.get_database_statistics()
    
    # --- Γενική Εικόνα ---
    print_header("ΓΕΝΙΚΗ ΕΙΚΟΝΑ (OVERVIEW)")
    print(f"📚 Συνολικά Άρθρα:      {stats['total_papers']}")
    print(f"💎 Elite Papers (>7/10): {stats['elite_papers']} ({(stats['elite_papers']/stats['total_papers']*100):.1f}%)")
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
    main()
    input("Πατήστε Enter για έξοδο.")