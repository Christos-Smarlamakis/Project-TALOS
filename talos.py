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
Module: talos.py (v4.8 - The Onboarding Update)
Project: TALOS v4.4

Description:
Το κεντρικό σημείο εισόδου.
- Περιλαμβάνει "Onboarding Wizard": Αν δεν βρει config.json (νέος χρήστης),
  αντιγράφει το template και εκκινεί αυτόματα την Πυθία για να ρυθμίσει
  το πρώτο ερευνητικό προφίλ.
"""
import questionary
import os
import subprocess
import sys
import time
import shutil

# Προσθέτουμε το path για να βλέπουμε τα scripts
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'scripts')))
from scripts.profile_manager import get_active_profile_name, save_current_state_to_profile, set_active_profile_name

def safe_select(message, choices):
    
    try:
        return questionary.select(message, choices=choices, use_indicator=True, pointer="»").ask()
    except Exception:
        print("\nWARNING: Advanced terminal UI failed. Falling back to simple mode.")
        return questionary.select(message, choices=choices).unsafe_ask()

def run_script(script_name: str, python_exe: str, args: list = None, capture: bool = False):
    project_root = os.path.dirname(os.path.abspath(__file__))
    script_path = os.path.join(project_root, 'scripts', script_name)
    command = [python_exe, script_path] + (args or [])
    
    print(f"\n--- Εκκίνηση του '{script_name}'... ---\n")
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    
    try:
        if capture:
            result = subprocess.run(command, check=True, capture_output=True, text=True, encoding="utf-8", env=env)
            print(result.stdout)
            print(f"\n--- Η εκτέλεση του '{script_name}' ολοκληρώθηκε. ---")
            return result
        else:
            try:
                subprocess.run(command, check=True, env=env)
                print(f"\n--- Η εκτέλεση του '{script_name}' ολοκληρώθηκε. ---")
                return True
            except subprocess.CalledProcessError as e:
                # Αν είναι το dashboard και έχει exit code 1 (συχνό σε windows kill), το αγνοούμε
                if "interactive_dashboard.py" in script_name and e.returncode in [1, 2, -2, 3221225786]: # Κοινοί κωδικοί τερματισμού
                     print(f"\n--- Ο server τερματίστηκε από τον χρήστη. ---")
                     return True
                else:
                    raise e # Για άλλα scripts, είναι όντως σφάλμα

    except (subprocess.CalledProcessError, FileNotFoundError, Exception) as e:
        print(f"\n---! Σφάλμα κατά την εκτέλεση του '{script_name}': {e} !---")       
        return None

def check_first_run(python_exe):
    """
    Ελέγχει αν είναι η πρώτη φορά που τρέχει το TALOS (λείπει το config.json).
    Αν ναι, ξεκινάει τον οδηγό εγκατάστασης.
    """
    config_path = "config.json"
    template_path = "config.template.json"
    
    if not os.path.exists(config_path):
        print("\n👋 Καλώς ήρθες στο Project TALOS!")
        print("   Φαίνεται πως είναι η πρώτη φορά που τρέχεις το σύστημα.")
        print("   Θα δημιουργήσω ένα αρχικό προφίλ για σένα.\n")
        
        if os.path.exists(template_path):
            shutil.copy(template_path, config_path)
            print("✅ Δημιουργήθηκε το 'config.json' από το πρότυπο.")
        else:
            print("❌ ΣΦΑΛΜΑ: Δεν βρέθηκε το 'config.template.json'.")
            return

        # Ρύθμιση αρχικού προφίλ
        if not os.path.exists("_profiles"):
            os.makedirs("_profiles")
        
        # Ζητάμε από τον χρήστη να τρέξει την Πυθία
        print("\n🤖 Ας ρυθμίσουμε τον ερευνητικό σου στόχο με τη βοήθεια του AI (Project PYTHIA).")
        if questionary.confirm("Θέλεις να ξεκινήσεις τη ρύθμιση τώρα;", default=True).ask():
            run_script("query_translator.py", python_exe)
            
            # Αποθήκευση του νέου προφίλ ως 'default'
            print("\n💾 Αποθήκευση του νέου προφίλ ως 'default'...")
            set_active_profile_name("default")
            save_current_state_to_profile("default")
        
        print("\n--- Η αρχική ρύθμιση ολοκληρώθηκε! ---\n")
        time.sleep(2)



def author_tools_menu(python_exe: str):
    os.system('cls' if os.name == 'nt' else 'clear')
    choice = safe_select(
        "Εργαλεία Ανάλυσης Συγγραφέα:",
        choices=[
            "1. Γρήγορο Προφίλ (Profiler)",
            "2. Ανάλυση Πορείας (Trajectory Analyzer)",
            "3. Πλήρης Αναφορά (Profiler -> Trajectory)",
            questionary.Separator(),
            "Επιστροφή στο Κύριο Μενού"
        ]
    )
    if choice is None or choice.startswith("Επιστροφή"): return

    if choice.startswith("1."):
        author_identifier = questionary.text("Πληκτρολόγησε το όνομα ή το ORCID iD:").ask()
        if author_identifier: run_script("author_profiler.py", python_exe, args=[author_identifier.strip()])

    elif choice.startswith("2."):
        author_identifier = questionary.text("Πληκτρολόγησε το όνομα ή το ORCID iD:").ask()
        if author_identifier: run_script("author_trajectory_analyzer.py", python_exe, args=[author_identifier.strip()])

    elif choice.startswith("3."):
        author_name = questionary.text("Πληκτρολόγησε το όνομα του συγγραφέα:").ask()
        if author_name:
            print("\n--- [ΒΗΜΑ 1/2] Ταυτοποίηση ερευνητή... ---")
            profiler_result = run_script("author_profiler.py", python_exe, args=author_name.strip().split(), capture=True)
            if profiler_result and profiler_result.stdout:
                selected_id = next((line.split(":", 1)[1].strip() for line in profiler_result.stdout.splitlines() if line.startswith("SELECTED_ORCID_ID:")), None)
                if selected_id:
                    print(f"\n--- [ΒΗΜΑ 2/2] Εκκίνηση Trajectory Analyzer... ---")
                    run_script("author_trajectory_analyzer.py", python_exe, args=[selected_id])
                else:
                    print("\n---! Δεν επιλέχθηκε ORCID iD. Διακοπή. !---")

def maintenance_menu(python_exe: str):
    os.system('cls' if os.name == 'nt' else 'clear')

    project_root = os.path.dirname(os.path.abspath(__file__))
    active_profile = get_active_profile_name()
    profile_db_path = os.path.join(project_root, '_profiles', active_profile, 'talos_research.db')    
    root_db_path = os.path.join(project_root, 'talos_research.db')
    target_db = profile_db_path if os.path.exists(profile_db_path) else root_db_path
    choice = safe_select(
        "Εργαλεία Συντήρησης Βάσης:",
        choices=[
            "1. Στατιστικά & Υγεία Βάσης (Metrics)",
            "2. Εμπλουτισμός Μεταδεδομένων",
            "3. Συγχρονισμός TALOS με Zotero",
            "4. Δημιουργία/Ενημέρωση Embeddings (Semantic Brain)",
            "5. Έξυπνη Επαναξιολόγηση Βάσης (AI Re-evaluation)",
            "7. 🧬 Εμπλουτισμός Δεδομένων (Data Enricher - Unpaywall/IDs)",
            "8. 📊 Επιστημονικά Στατιστικά (Scientometrics Report)",
            questionary.Separator(),
            "Επιστροφή στο Κύριο Μενού"
        ]
    )
    if choice is None or choice.startswith("Επιστροφή"): return

    if choice.startswith("1."): run_script("db_stats.py", python_exe)
    elif choice.startswith("2."): run_script("metadata_enricher.py", python_exe)
    elif choice.startswith("3."): run_script("zotero_connector.py", python_exe)
    elif choice.startswith("4."):
        if questionary.confirm("Αυτή η διαδικασία θα κάνει πολλαπλές κλήσεις στο Gemini API. Συνέχεια;", default=False).ask():
            run_script("embedding_generator.py", python_exe)
    elif choice.startswith("5."): run_script("reevaluate_database.py", python_exe)
    elif choice.startswith("6."): run_script("recalculate_scores.py", python_exe)
    elif choice.startswith("7."): run_script("data_enricher.py", python_exe, args=[target_db])
    elif choice.startswith("8."): run_script("trend_analyzer.py", python_exe, args=[target_db])
# --- ΚΥΡΙΟ ΜΕΝΟΥ ---

def main_menu():
    python_exe = sys.executable or "python"
    print(f"INFO: Χρησιμοποιείται η Python από: {python_exe}")
    
    check_first_run(python_exe)
    
    time.sleep(1)

    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        active_profile = get_active_profile_name()
        
        choice = safe_select(
            f"TALOS v4.8 | Profile: [{active_profile}]",
            choices=[
                "0. 👤 Διαχείριση Προφίλ / Αλλαγή Θέματος", # Εδώ μέσα είναι πλέον η Πυθία
                questionary.Separator(),
                "1. Έλεγχος για Νέα άρθρα",                
                "2. Εκτέλεση Ιστορικής Αναζήτησης",
                questionary.Separator(),
                "--- Intel & Analysis Tools ---",
                "3. Δημιουργία Μονοπατιού Γνώσης",
                "4. Έρευνα Γκρίζας Βιβλιογραφίας/Web (Horizon Scan)",
                "5. Εργαλεία Ανάλυσης Συγγραφέα", 
                "6. Ανάλυση Δικτύου Γνώσης",
                "7. Στρατηγική Αναφορά Ανάγνωσης",
                "8. Εκκίνηση Διαδραστικού Dashboard",
                questionary.Separator(),
                "--- Database Maintenance ---",
                "9. Εργαλεία Συντήρησης Βάσης",
                questionary.Separator(),
                "Έξοδος"
            ]
        )

        if choice is None or choice == "Έξοδος": break
        
        final_message = "Πατήστε Enter για να επιστρέψετε στο μενού..."

        if choice.startswith("0."): run_script("profile_manager.py", python_exe)
        elif choice.startswith("1."): run_script("daily_search.py", python_exe)
        elif choice.startswith("2."):
            if questionary.confirm("Αυτή η διαδικασία μπορεί να διαρκέσει πολλή ώρα. Είσαι σίγουρος;", default=False).ask():
                run_script("historic_search.py", python_exe)
        elif choice.startswith("3."): run_script("knowledge_path_generator.py", python_exe)
        elif choice.startswith("4."): run_script("grey_literature_miner.py", python_exe) 
        elif choice.startswith("5."): author_tools_menu(python_exe)
        elif choice.startswith("6."): run_script("citation_analyzer.py", python_exe)
        elif choice.startswith("7."): run_script("recommender.py", python_exe)
        elif choice.startswith("8."):
            run_script("interactive_dashboard.py", python_exe)
            final_message = "Ο server του Dashboard τερματίστηκε. Πατήστε Enter για να επιστρέψετε στο μενού..."
        elif choice.startswith("9."): maintenance_menu(python_exe)
        
        if choice != "Έξοδος": input(final_message)

    print("\nTalos Command Center Closing...\nBye Bye...\n")

if __name__ == "__main__":
    try:
        main_menu()
    except KeyboardInterrupt:
        print("\n\nTalos Command Center Closing...\nBye Bye...")