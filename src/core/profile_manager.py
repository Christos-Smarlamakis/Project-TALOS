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
Module: profile_manager.py (v2.1 - Auto-Save Fix)
Project: TALOS v4.2

Description:
Διαχειρίζεται τα ερευνητικά προφίλ και ενσωματώνει τη διαδικασία ρύθμισης (PYTHIA).
- Διορθώνει το bug όπου οι αλλαγές της Πυθίας δεν αποθηκεύονταν μόνιμα στο
  νέο προφίλ μετά την αρχική δημιουργία.
- Πλέον, μετά την εκτέλεση της Πυθίας, γίνεται αυτόματη αποθήκευση (force save)
  στο ενεργό προφίλ.
"""
import os
import sys
import shutil
import json
import questionary
import subprocess

PROFILES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '_profiles'))
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
ACTIVE_PROFILE_FILE = os.path.join(PROFILES_DIR, 'active_profile.txt')

def run_pythia_script():
    """Εκτελεί το script της Πυθίας (query_translator.py)."""
    python_exe = sys.executable
    script_path = os.path.join(os.path.dirname(__file__), 'query_translator.py')
    
    print(f"\n--- Εκκίνηση PYTHIA (Ρύθμιση Στόχου)... ---\n")
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    try:
        subprocess.run([python_exe, script_path], check=True, env=env)
        return True # Επιστρέφει True αν ολοκληρώθηκε με επιτυχία
    except Exception as e:
        print(f"Error running Pythia: {e}")
        return False

def ensure_profiles_dir():
    if not os.path.exists(PROFILES_DIR):
        os.makedirs(PROFILES_DIR)

def get_active_profile_name():
    ensure_profiles_dir()
    if os.path.exists(ACTIVE_PROFILE_FILE):
        with open(ACTIVE_PROFILE_FILE, 'r', encoding='utf-8') as f:
            return f.read().strip()
    return "default"

def set_active_profile_name(name):
    ensure_profiles_dir()
    with open(ACTIVE_PROFILE_FILE, 'w', encoding='utf-8') as f:
        f.write(name)

def save_current_state_to_profile(profile_name):
    """Αποθηκεύει τα τρέχοντα αρχεία root στον φάκελο του προφίλ."""
    profile_path = os.path.join(PROFILES_DIR, profile_name)
    os.makedirs(profile_path, exist_ok=True)
    
    config_src = os.path.join(ROOT_DIR, 'config.json')
    db_src = os.path.join(ROOT_DIR, 'talos_research.db')
    
    if os.path.exists(config_src):
        shutil.copy2(config_src, os.path.join(profile_path, 'config.json'))
    
    if os.path.exists(db_src):
        shutil.copy2(db_src, os.path.join(profile_path, 'talos_research.db'))
    
    print(f"✅ Η κατάσταση του προφίλ '{profile_name}' αποθηκεύτηκε.")

def load_profile_to_root(profile_name):
    """Φέρνει τα αρχεία του προφίλ στον κεντρικό φάκελο."""
    profile_path = os.path.join(PROFILES_DIR, profile_name)
    
    config_src = os.path.join(profile_path, 'config.json')
    db_src = os.path.join(profile_path, 'talos_research.db')
    
    config_dest = os.path.join(ROOT_DIR, 'config.json')
    db_dest = os.path.join(ROOT_DIR, 'talos_research.db')
    
    if os.path.exists(db_dest): os.remove(db_dest)
    
    if os.path.exists(config_src):
        shutil.copy2(config_src, config_dest)
    else:
        print("⚠️ Δεν βρέθηκε config για αυτό το προφίλ. Χρήση του τρέχοντος ως βάση.")

    if os.path.exists(db_src):
        shutil.copy2(db_src, db_dest)
        print(f"📚 Φορτώθηκε η βάση δεδομένων του '{profile_name}'.")
    else:
        print(f"🆕 Δεν υπάρχει βάση για το '{profile_name}'. Θα δημιουργηθεί νέα.")

    set_active_profile_name(profile_name)
    print(f"🚀 Το προφίλ '{profile_name}' είναι τώρα ενεργό!")

def create_new_profile():
    name = questionary.text("Δώσε όνομα για το νέο προφίλ (π.χ. bioinformatics):").ask()
    if not name: return
    
    safe_name = "".join([c for c in name if c.isalnum() or c in (' ', '_', '-')]).strip().replace(' ', '_')
    
    # Σώζουμε το τρέχον πριν αλλάξουμε
    current = get_active_profile_name()
    save_current_state_to_profile(current)
    
    profile_path = os.path.join(PROFILES_DIR, safe_name)
    os.makedirs(profile_path, exist_ok=True)
    
    # Αντιγράφουμε το config ως template
    shutil.copy2(os.path.join(ROOT_DIR, 'config.json'), os.path.join(profile_path, 'config.json'))
    
    load_profile_to_root(safe_name)
    
    print(f"\n--- Το νέο προφίλ '{safe_name}' δημιουργήθηκε! ---")
    
    if questionary.confirm("Θέλεις να ρυθμίσεις τον ερευνητικό στόχο (PYTHIA) τώρα;", default=True).ask():
        success = run_pythia_script()
        if success:
            # --- Η ΔΙΟΡΘΩΣΗ ΕΙΝΑΙ ΕΔΩ ---
            # Μετά την επιτυχή εκτέλεση της Πυθίας (η οποία αλλάζει το root config),
            # αποθηκεύουμε ΑΜΕΣΩΣ το root config πίσω στον φάκελο του προφίλ.
            print("\n💾 Αποθήκευση νέων ρυθμίσεων στο προφίλ...")
            save_current_state_to_profile(safe_name)

def switch_profile():
    current = get_active_profile_name()
    profiles = [d for d in os.listdir(PROFILES_DIR) if os.path.isdir(os.path.join(PROFILES_DIR, d))]
    if not profiles:
        print("Δεν υπάρχουν αποθηκευμένα προφίλ.")
        return

    if current not in profiles:
        save_current_state_to_profile(current)
        profiles.append(current)

    choice = questionary.select(
        f"Τρέχον Προφίλ: [{current}]. Επίλεξε προφίλ για φόρτωση:",
        choices=profiles + ["Ακύρωση"]
    ).ask()

    if choice == "Ακύρωση" or choice is None: return
    if choice == current:
        print("Είσαι ήδη σε αυτό το προφίλ.")
        return

    print(f"\n💾 Αποθήκευση κατάστασης '{current}'...")
    save_current_state_to_profile(current)
    
    print(f"\n📂 Φόρτωση προφίλ '{choice}'...")
    load_profile_to_root(choice)

def configure_current_profile():
    """Εκτελεί την Πυθία για το τρέχον προφίλ."""
    current = get_active_profile_name()
    if questionary.confirm(f"ΠΡΟΣΟΧΗ: Αυτό θα αλλάξει τις ρυθμίσεις (Queries/Prompts) για το προφίλ '{current}'. Συνέχεια;", default=False).ask():
        success = run_pythia_script()
        if success:
            # --- ΚΑΙ ΕΔΩ Η ΔΙΟΡΘΩΣΗ ---
            print(f"\n💾 Αποθήκευση νέων ρυθμίσεων στο προφίλ '{current}'...")
            save_current_state_to_profile(current)

def main():
    # Πρώτη εκτέλεση: Αν δεν υπάρχει active profile, ορίζουμε το 'default'
    if not os.path.exists(ACTIVE_PROFILE_FILE):
        set_active_profile_name("default")
        save_current_state_to_profile("default")
        
    current = get_active_profile_name()
    
    try:
        choice = questionary.select(
            f"ΔΙΑΧΕΙΡΙΣΗ ΠΡΟΦΙΛ | Ενεργό: [{current}]",
            choices=[
                "1. Εναλλαγή Προφίλ (Switch)",
                "2. Δημιουργία Νέου Προφίλ (+ Auto Setup)",
                "3. 🔮 Ρύθμιση Στόχου Τρέχοντος Προφίλ (PYTHIA)",
                "4. Αποθήκευση Τρέχουσας Κατάστασης (Save)",
                questionary.Separator(),
                "Επιστροφή"
            ]
        ).ask()
    except Exception:
         choice = questionary.select("Επιλογές:", choices=["1. Switch", "2. Create", "3. Configure (PYTHIA)", "4. Save", "Return"]).unsafe_ask()

    if not choice or "Επιστροφή" in choice or "Return" in choice: return

    if choice.startswith("1."): switch_profile()
    elif choice.startswith("2."): create_new_profile()
    elif choice.startswith("3."): configure_current_profile()
    elif choice.startswith("4."): save_current_state_to_profile(current)

if __name__ == "__main__":
    main()