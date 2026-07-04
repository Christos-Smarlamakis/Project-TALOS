# -*- coding: utf-8 -*-
"""
Module: gui_strings.py
Project: TALOS v5.2.1
Description:
    Translation strings for the Streamlit GUI. Exports the STR dict and t()
    function. All UI strings in English (default) and Greek.
"""

# ── Translation dictionary ───────────────────────────────────────────────────
STR = {
    # Sidebar
    "sidebar_title": {"en": "Research Intelligence Platform", "gr": "Πλατφόρμα Ερευνητικής Νοημοσύνης"},
    "sidebar_papers": {"en": "papers · elite", "gr": "papers · κορυφαία"},
    # Navigation labels
    "home": {"en": "◆ Home & Knowledge Base", "gr": "◆ Αρχική & Γνωσιακή Βάση"},
    "search_disc": {"en": "▷ Search & Discovery", "gr": "▷ Αναζήτηση & Ανακάλυψη"},
    "paper_eval": {"en": "▣ Paper Evaluation", "gr": "▣ Αξιολόγηση Paper"},
    "analysis": {"en": "▨ Analysis & Insights", "gr": "▨ Ανάλυση & Ευρήματα"},
    "db_data": {"en": "⊞ Database & Data", "gr": "⊞ Βάση Δεδομένων & Συντήρηση"},
    "diagnostics": {"en": "⚙ System Diagnostics", "gr": "⚙ Διαγνωστικά Συστήματος"},
    "drl_dash": {"en": "⊠ DRL Agent Dashboard", "gr": "⊠ Πίνακας DRL Πράκτορα"},
    "profile": {"en": "⊙ Profile & Settings", "gr": "⊙ Προφίλ & Ρυθμίσεις"},
    # Simple mode labels
    "simple_home_label": {"en": "◆ Knowledge Overview", "gr": "◆ Αρχική — Επισκόπηση Γνώσης"},
    "simple_search_label": {"en": "▷ Literature Search", "gr": "▷ Αναζήτηση — Βρες νέα papers"},
    "simple_library_label": {"en": "▤ Knowledge Library", "gr": "▤ Βιβλιοθήκη — Διάβασε τη γνώση σου"},
    "simple_eval_label": {"en": "▣ Paper Evaluation", "gr": "▣ Αξιολόγηση Paper"},
    "simple_agent_label": {"en": "⊠ Autonomous Research Agent", "gr": "⊠ Αυτόματος Ερευνητής — DRL Agent"},
    # Simple mode content
    "sh_hero_title": {"en": "Project TALOS", "gr": "Project TALOS"},
    "sh_hero_subtitle": {"en": "The Intelligent Research Knowledge Platform — No Technical Skills Required", "gr": "Η Έξυπνη Πλατφόρμα Ερευνητικής Γνώσης — Χωρίς τεχνικές γνώσεις!"},
    "sh_search_title": {"en": "Search for Papers", "gr": "Αναζήτηση Papers"},
    "sh_search_desc": {"en": "Tell us what interests you and TALOS will search 14 academic databases for you.", "gr": "Πες μας τι σε ενδιαφέρει και το TALOS θα ψάξει 14 ακαδημαϊκές βάσεις για σένα."},
    "sh_search_placeholder": {"en": "What would you like to research?", "gr": "Τι θέλεις να βρεις;"},
    "sh_search_button": {"en": "▶ Start Search", "gr": "▶ Ξεκίνα Αναζήτηση"},
    "sh_search_error": {"en": "Please provide a more detailed description (at least 15 characters).", "gr": "Παρακαλώ δώσε μια πιο αναλυτική περιγραφή (τουλάχιστον 15 χαρακτήρες)."},
    "sh_search_running": {"en": "Searching for '{topic}'... This may take a few minutes.", "gr": "Ψάχνω για '{topic}'... Αυτό μπορεί να πάρει μερικά λεπτά."},
    "sh_search_success": {"en": "Search complete! Results have been added to your library.", "gr": "Η αναζήτηση ολοκληρώθηκε! Τα αποτελέσματα προστέθηκαν στη βιβλιοθήκη σου."},
    "sh_search_partial": {"en": "Search completed but there may be issues.", "gr": "Η αναζήτηση ολοκληρώθηκε αλλά μπορεί να υπάρχουν προβλήματα."},
    "sh_library_title": {"en": "My Knowledge Library", "gr": "Η Βιβλιοθήκη μου"},
    "sh_library_desc": {"en": "Browse your collected papers. All are evaluated and organized by the AI.", "gr": "Περιηγήσου στα papers που έχεις ήδη βρει. Όλα είναι αξιολογημένα από το AI."},
    "sh_library_sem_label": {"en": "Search by meaning (semantic search)", "gr": "Αναζήτηση με νόημα (semantic search)"},
    "sh_library_sem_btn": {"en": "▶ Search", "gr": "▶ Αναζήτηση"},
    "sh_library_sem_found": {"en": "Found {n} semantically similar papers!", "gr": "Βρέθηκαν {n} σχετικά papers!"},
    "sh_library_sem_unavail": {"en": "Semantic search is unavailable: {e}", "gr": "Η σημασιολογική αναζήτηση δεν είναι διαθέσιμη: {e}"},
    "sh_library_empty": {"en": "No papers yet. Run a search first!", "gr": "Δεν υπάρχουν papers ακόμα. Τρέξε μια αναζήτηση πρώτα!"},
    "sh_library_load_error": {"en": "Could not load library: {e}", "gr": "Δεν μπόρεσε να φορτώσει η βιβλιοθήκη: {e}"},
    "sh_agent_title": {"en": "Autonomous Research Agent", "gr": "Αυτόματος Ερευνητής"},
    "sh_agent_desc": {"en": "TALOS uses Artificial Intelligence to automatically select the best academic sources and find the most important papers for you. No action needed — just press the button!", "gr": "Το TALOS χρησιμοποιεί Τεχνητή Νοημοσύνη για να επιλέγει αυτόματα τις καλύτερες ακαδημαϊκές πηγές και να βρίσκει τα πιο σημαντικά papers για σένα. Δεν χρειάζεται να κάνεις τίποτα — απλά πάτα το κουμπί!"},
    "sh_agent_ready": {"en": "The research agent is trained and ready! ({size:.1f} KB)", "gr": "Ο ερευνητής είναι εκπαιδευμένος και έτοιμος! ({size:.1f} KB)"},
    "sh_agent_btn": {"en": "▷ Start Autonomous Researcher", "gr": "▷ Εκκίνηση Αυτόματου Ερευνητή"},
    "sh_agent_running": {"en": "The agent is searching autonomously... Press Stop to end.", "gr": "Ο ερευνητής ψάχνει αυτόματα... Πάτα Stop για να σταματήσεις."},
    "sh_agent_done": {"en": "The researcher has completed!", "gr": "Ο ερευνητής ολοκλήρωσε!"},
    "sh_agent_untrained": {"en": "The research agent has not been trained yet. An administrator needs to run training first.", "gr": "Ο ερευνητής δεν έχει εκπαιδευτεί ακόμα. Χρειάζεται να τρέξεις πρώτα την εκπαίδευση."},
    "sh_eval_title": {"en": "Paper Evaluation", "gr": "Αξιολόγηση Paper"},
    "sh_eval_desc": {"en": "Paste a paper abstract and TALOS will evaluate its relevance to your research.", "gr": "Επικόλλησε την περίληψη (abstract) ενός paper και το TALOS θα το αξιολογήσει."},
    "sh_eval_label": {"en": "Paste the abstract here:", "gr": "Επικόλλησε την περίληψη εδώ:"},
    "sh_eval_btn": {"en": "▶ Evaluate", "gr": "▶ Αξιολόγησε"},
    "sh_eval_error": {"en": "At least 50 characters are needed.", "gr": "Χρειάζεται τουλάχιστον 50 χαρακτήρες."},
    "sh_eval_spinner": {"en": "Evaluating with AI...", "gr": "Αξιολογώ με AI..."},
    "sh_eval_fail": {"en": "Evaluation failed. Check API keys.", "gr": "Η αξιολόγηση απέτυχε. Έλεγξε τα API keys."},
    "sh_eval_strategic": {"en": "Strategic", "gr": "Στρατηγικό"},
    "sh_eval_operational": {"en": "Operational", "gr": "Λειτουργικό"},
    "sh_eval_tactical": {"en": "Tactical", "gr": "Τακτικό"},
    "sh_eval_playground": {"en": "Playground", "gr": "Πειραματικό"},
    "sh_eval_overall": {"en": "Overall Score", "gr": "Συνολική Βαθμολογία"},
    "sh_eval_reasoning": {"en": "Reasoning", "gr": "Σκεπτικό"},
    "sh_eval_tags": {"en": "Tags", "gr": "Ετικέτες"},
    # Home cards (Simple)
    "sh_card_search_title": {"en": "Literature Search", "gr": "Αναζήτηση"},
    "sh_card_search_desc": {"en": "Find the latest scientific papers on your topic. TALOS searches 14 academic databases for you.", "gr": "Βρες τα πιο πρόσφατα επιστημονικά papers στο θέμα που σε ενδιαφέρει. Το TALOS ψάχνει 14 ακαδημαϊκές βάσεις για σένα."},
    "sh_card_library_title": {"en": "Knowledge Library", "gr": "Η Βιβλιοθήκη μου"},
    "sh_card_library_desc": {"en": "Browse your personal library. All papers are already evaluated and organized by topic.", "gr": "Περιήγησε στην προσωπική σου βιβλιοθήκη. Όλα τα papers είναι ήδη αξιολογημένα και οργανωμένα ανά θεματική περιοχή."},
    "sh_card_eval_title": {"en": "Paper Evaluation", "gr": "Αξιολόγηση"},
    "sh_card_eval_desc": {"en": "Have a paper to evaluate? Paste its abstract and TALOS will tell you how important it is for your research.", "gr": "Έχεις ένα paper που θες να αξιολογήσεις; Επικόλλησε την περίληψη και το TALOS θα σου πει πόσο σημαντικό είναι για σένα."},
    "sh_home_papers": {"en": "Papers in database", "gr": "Papers στη βάση"},
    "sh_home_elite": {"en": "Top-tier (≥8)", "gr": "Κορυφαία (≥8)"},
    "sh_home_avg": {"en": "Average score", "gr": "Μέσος όρος"},
    "sh_home_empty": {"en": "The database is empty. Run a search to get started!", "gr": "Η βάση δεδομένων είναι άδεια. Τρέξε μια αναζήτηση για να ξεκινήσεις!"},
    # Toggles
    "advanced_toggle": {"en": "Advanced Mode", "gr": "Προχωρημένο"},
    "dark_toggle": {"en": "Dark Theme", "gr": "Σκοτεινό Θέμα"},
    "footer": {"en": "TALOS v5.2.1 · Research Intelligence Platform", "gr": "TALOS v5.2.1 · Πλατφόρμα Ερευνητικής Νοημοσύνης"},
    "simple_prompt": {"en": "What would you like to do?", "gr": "Τι θα θέλατε να κάνετε;"},
    "nav_advanced": {"en": "▶ Navigation", "gr": "▶ Πλοήγηση"},
    # AI Search (flagship)
    "ai_search_title": {"en": "AI-Powered Search (DRL Orchestrator)", "gr": "Αναζήτηση με AI (DRL Ενορχηστρωτής)"},
    "ai_search_desc": {"en": "Our trained Deep Reinforcement Learning agent intelligently selects the best academic API in real-time, avoiding rate limits and maximizing high-score paper discovery.", "gr": "Ο εκπαιδευμένος Deep Reinforcement Learning πράκτοράς μας επιλέγει έξυπνα το καλύτερο ακαδημαϊκό API σε πραγματικό χρόνο, αποφεύγοντας τα rate limits και μεγιστοποιώντας την ανακάλυψη υψηλής βαθμολογίας papers."},
    "ai_daemon_title": {"en": "Autonomous Research Daemon (24/7 + DRL)", "gr": "Αυτόνομος Ερευνητικός Δαίμονας (24/7 + DRL)"},
    "ai_daemon_desc": {"en": "Background service that runs continuously, using the DRL agent to discover high-value papers around the clock. Sends Telegram/Discord/Email notifications.", "gr": "Υπηρεσία παρασκηνίου που τρέχει συνεχώς, χρησιμοποιώντας τον DRL πράκτορα για να ανακαλύπτει υψηλής αξίας papers όλο το 24ωρο. Στέλνει ειδοποιήσεις Telegram/Discord/Email."},
    # Model Management
    "model_local": {"en": "LOCAL (Ollama)", "gr": "ΤΟΠΙΚΟ (Ollama)"},
    "model_cloud": {"en": "CLOUD (Gemini+DeepSeek)", "gr": "CLOUD (Gemini+DeepSeek)"},
    "model_select": {"en": "Select AI Model", "gr": "Επιλογή Μοντέλου AI"},
    "model_provider": {"en": "AI Provider", "gr": "Πάροχος AI"},
    "model_chat": {"en": "Chat Model", "gr": "Μοντέλο Συνομιλίας"},
    "model_embed": {"en": "Embedding Model", "gr": "Μοντέλο Embedding"},
    "model_quant": {"en": "Quantization", "gr": "Κβαντισμός"},
    "model_vram": {"en": "GPU VRAM", "gr": "VRAM Κάρτας Γραφικών"},
    "model_installed": {"en": "Installed on this PC", "gr": "Εγκατεστημένα στον υπολογιστή"},
    "model_library": {"en": "Available via Ollama", "gr": "Διαθέσιμα μέσω Ollama"},
    "model_bitnet": {"en": "BitNet 1-bit (Edge/CPU)", "gr": "BitNet 1-bit (Edge/CPU)"},
    "model_fits": {"en": "FITS ✓", "gr": "ΧΩΡΑΕΙ ✓"},
    "model_tight": {"en": "TIGHT ~", "gr": "ΟΡΙΑΚΑ ~"},
    "model_toobig": {"en": "TOO BIG ✗", "gr": "ΔΕΝ ΧΩΡΑΕΙ ✗"},
    "model_save": {"en": "Save Model Configuration", "gr": "Αποθήκευση Ρυθμίσεων"},
    "model_gemini_flash": {"en": "Gemini Flash Model", "gr": "Μοντέλο Gemini Flash"},
    "model_gemini_pro": {"en": "Gemini Pro Model", "gr": "Μοντέλο Gemini Pro"},
    "model_deepseek": {"en": "DeepSeek Model", "gr": "Μοντέλο DeepSeek"},
    "model_hf": {"en": "HuggingFace Model", "gr": "Μοντέλο HuggingFace"},
    "daemon_start": {"en": "Start Daemon", "gr": "Εκκίνηση Δαίμονα"},
    "daemon_stop": {"en": "The daemon runs indefinitely. Press the stop button or close this page to end it.", "gr": "Ο δαίμονας τρέχει επ' αόριστον. Πάτα το κουμπί stop ή κλείσε τη σελίδα για να τον σταματήσεις."},
    "daemon_reporting": {"en": "Reporting Mode", "gr": "Λειτουργία Αναφοράς"},
    "daemon_silent": {"en": "Silent (alerts only)", "gr": "Αθόρυβη (μόνο ειδοποιήσεις)"},
    "daemon_normal": {"en": "Normal (episode summaries)", "gr": "Κανονική (σύνοψη επεισοδίων)"},
    "daemon_verbose": {"en": "Verbose (every action)", "gr": "Αναλυτική (κάθε ενέργεια)"},
}

import streamlit as st

def t(key, en_default=""):
    """Return the translated string for the current language using the STR dict."""
    if key not in STR:
        return en_default or key
    return STR[key].get(st.session_state.lang, STR[key].get("en", key))