# -*- coding: utf-8 -*-
import os
import re

# Οι "νόμοι" του τι δεν ανεβαίνει ποτέ στο GitHub
CRITICAL_IGNORES =[
    ".env",                 
    "*.db",                 
    "talos_research.db",    
    "talos_backup*.db",
    "_profiles/",           
    "_library/",            
    "reports/",             
    "__pycache__/",         
    ".DS_Store",            
    "*.log",                
    ".vscode/",             
    "config.json"           # Το config.template.json ανεβαίνει, το κανονικό ΟΧΙ
]

AGPL_LICENSE_TEXT = """GNU AFFERO GENERAL PUBLIC LICENSE
Version 3, 19 November 2007

Copyright (C) 2026 Christos Smarlamakis

Everyone is permitted to copy and distribute verbatim copies
of this license document, but changing it is not allowed.

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>."""

def setup_gitignore():
    print("\n--- 1. Ρύθμιση .gitignore ---")
    with open(".gitignore", "w", encoding="utf-8") as f:
        f.write("# Αρχείο αγνόησης ευαίσθητων δεδομένων για το Project TALOS\n")
        for rule in CRITICAL_IGNORES:
            f.write(f"{rule}\n")
    print("✅ Δημιουργήθηκε/Ενημερώθηκε το .gitignore επιτυχώς.")

def create_license():
    print("\n--- 2. Δημιουργία Άδειας (AGPLv3) ---")
    with open("LICENSE", "w", encoding="utf-8") as f:
        f.write(AGPL_LICENSE_TEXT)
    print("✅ Δημιουργήθηκε το αρχείο LICENSE (AGPLv3).")

def scan_for_secrets():
    print("\n--- 3. Σάρωση Κώδικα για Ξεχασμένα Μυστικά ---")
    patterns = {
        "Google API Key": r"AIza[0-9A-Za-z-_]{35}",
        "Hardcoded Email": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
    }
    warnings = 0
    exclude_dirs = {'.git', '__pycache__', '_profiles', 'env', 'venv', '.conda'}
    
    for root, dirs, files in os.walk("."):
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        for file in files:
            if file.endswith(".py") and file != "prepare_for_github.py":
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()
                    for name, pattern in patterns.items():
                        matches = re.findall(pattern, content)
                        for match in matches:
                            if "example.com" in match or "email=" in match: continue
                            print(f"⚠️  ΠΡΟΣΟΧΗ: Στο αρχείο '{file}' βρέθηκε πιθανό {name} -> {match[:10]}...")
                            warnings += 1
                except: pass

    if warnings == 0:
        print("✅ Δεν βρέθηκαν εκτεθειμένα κλειδιά/emails στον κώδικα.")
    else:
        print(f"\n🛑 ΣΗΜΑΝΤΙΚΟ: Βρέθηκαν {warnings} πιθανά μυστικά. Σβήστα από τον κώδικα πριν συνεχίσεις!")

if __name__ == "__main__":
    print("🛡️  TALOS GITHUB PRE-FLIGHT CHECK 🛡️")
    setup_gitignore()
    create_license()
    scan_for_secrets()
    print("\n✅ Έτοιμοι για το Git!")