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
Module: query_translator.py (v2.3 - Final with Override)
Project: TALOS v4.2

Description:
Ο απόλυτος αυτοματισμός ρύθμισης (Project PYTHIA).
- Χρησιμοποιεί το `system_prompt_override` στον AIManager για να διασφαλίσει
  ότι το AI λειτουργεί ως "Research Architect" και όχι ως "PhD Advisor".
- Εφαρμόζει αναδρομικό flattening στο JSON για να εντοπίσει τα queries
  ανεξάρτητα από τη δομή που επιστρέφει το μοντέλο.
"""
import os
import sys
import json
import questionary

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from core.ai_manager import AIManager

def load_config():
    path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'config.json'))
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f), path

def save_config(config, path):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    print("SUCCESS: Το config.json ενημερώθηκε πλήρως (Queries & Prompts).")

def flatten_json(y):
    """
    Αναδρομική συνάρτηση που ισοπεδώνει (flattens) ένα nested JSON.
    Στόχος είναι να φέρει τα κλειδιά 'arxiv_query', 'phd_focus...', κλπ.
    στο πρώτο επίπεδο, όπου κι αν βρίσκονται.
    """
    out = {}
    
    def flatten(x, name=''):
        if type(x) is dict:
            for a in x:
                flatten(x[a], name + a + '_')
        else:
            # Καθαρισμός ονόματος κλειδιού
            key = name[:-1]
            # Λογική για να κρατήσουμε το καθαρό όνομα αν είναι nested (π.χ. queries_arxiv_query -> arxiv_query)
            known_keys = [
                'arxiv_query', 'ieee_query', 'semantic_scholar_query', 'springer_query', 
                'openalex_query', 'dblp_query', 'elsevier_query', 'crossref_query', 
                'openarchives_query', 'pubmed_query', 'osti_query', 'scigov_query', 'core_query', 
                'phd_focus_system_prompt', 'pre_screening_prompt', 'trajectory_analyzer_prompt'
            ]
            
            # Αν το τρέχον κλειδί (ή μέρος του) ανήκει στα γνωστά, το χρησιμοποιούμε ως έχει
            found_key = None
            for k in known_keys:
                if k == key or key.endswith('_' + k) or key.endswith(k):
                    found_key = k
                    break
            
            if found_key:
                out[found_key] = x
            else:
                # Fallback για άγνωστα κλειδιά
                out[key] = x

    flatten(y)
    return out

def main():
    print("\n--- PROJECT PYTHIA: RESEARCH CONTEXT SETUP (v2.3 - Final) ---")
    
    config, config_path = load_config()
    ai_manager = AIManager(config)

    # 1. Λήψη της ερευνητικής πρόθεσης
    research_goal = questionary.text(
        "Περιέγραψε το νέο ερευνητικό σου θέμα (στα Αγγλικά):",
        validate=lambda text: True if len(text.strip()) > 10 else "Please describe your topic in more detail."
    ).ask()

    if not research_goal: return

    print("\n⏳ Η Πυθία σκέφτεται...")
    
    # 2. Σύνθεση του Prompt
    # Παίρνουμε το meta-prompt. Αν δεν υπάρχει στο config, χρησιμοποιούμε ένα ισχυρό default.
    meta_prompt = config.get("query_translator_prompt", 
        "Act as a Research Architect. Generate a flat JSON object with optimized search queries (keys like 'arxiv_query') and customized system prompts (keys like 'phd_focus_system_prompt') for the user's research goal. Do NOT nest the JSON.")
    
    template_guidance = f"""
    
    **REFERENCE TEMPLATE FOR PROMPTS (Keep JSON structure, change content):**
    {config.get('phd_focus_system_prompt', '')}

    **USER RESEARCH GOAL:**
    {research_goal}
    """
    
    # 3. Κλήση στο AI με SYSTEM PROMPT OVERRIDE
    # Αυτό είναι το κρίσιμο σημείο για να μην μπερδευτεί το AI
    generated_config_raw = ai_manager.evaluate_paper_json(
        paper_content=template_guidance, 
        model_type='pro',
        system_prompt_override=meta_prompt 
    )

    if not generated_config_raw:
        print("ERROR: Το AI δεν επέστρεψε έγκυρο JSON. Δοκίμασε να κάνεις το ερώτημα πιο συγκεκριμένο.")
        return

    # 4. Επεξεργασία Απάντησης
    generated_config = flatten_json(generated_config_raw)

    # Debugging Print
    # print(f"\n[DEBUG] Keys found: {list(generated_config.keys())}")

    new_queries = [k for k in generated_config.keys() if 'query' in k and k != "query_translator_prompt"]
    
    print("\n--- ΠΡΟΤΕΙΝΟΜΕΝΕΣ ΑΛΛΑΓΕΣ ---")
    print(f"🔹 Νέα Queries που βρέθηκαν: {len(new_queries)}")
    for q in new_queries:
        val = generated_config[q]
        preview = val[:60] + "..." if isinstance(val, str) and len(val) > 60 else val
        print(f"   - {q}: {preview}")
    
    if 'phd_focus_system_prompt' in generated_config:
        print("\n🔹 Νέο System Prompt (Preview):")
        print(generated_config['phd_focus_system_prompt'][:150] + "...\n")
    
    if len(new_queries) == 0 and 'phd_focus_system_prompt' not in generated_config:
        print("\n⚠️ Προσοχή: Η Πυθία δεν επέστρεψε τα αναμενόμενα πεδία. Ελέγξτε το Output.")
        return

    if questionary.confirm("\nΘέλεις να εφαρμόσω αυτές τις αλλαγές;", default=True).ask():
        count = 0
        for key, value in generated_config.items():
            # Ενημερώνουμε μόνο τα γνωστά πεδία για ασφάλεια
            if key in config or 'query' in key or 'prompt' in key:
                config[key] = value
                count += 1
        
        save_config(config, config_path)
        print(f"\n✅ Ενημερώθηκαν {count} ρυθμίσεις στο config.json.")
    else:
        print("Η διαδικασία ακυρώθηκε.")

if __name__ == "__main__":
    main()