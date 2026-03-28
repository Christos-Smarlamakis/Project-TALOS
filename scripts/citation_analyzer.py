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
Module: citation_analyzer.py (v2.1 - Robust Interactive Selection)
Project: TALOS v2.21.0

Description:
Η τελική, διορθωμένη έκδοση του "ORPHEUS".
- Διορθώνει το σφάλμα όπου ολόκληρο το κείμενο της επιλογής περνούσε ως DOI.
- Χρησιμοποιεί σωστά τα αντικείμενα `questionary.Choice` για να διαχωρίσει
  τον τίτλο που βλέπει ο χρήστης από την τιμή (το DOI) που επιστρέφεται
  στον κώδικα, κάνοντας την "έξυπνη" επιλογή πλήρως λειτουργική.
"""
import os
import sys
import json
from datetime import datetime
from pyvis.network import Network
import questionary
from typing import Union, List, Dict, Any, Tuple # <-- Συμβατότητα με Python < 3.10

# Προσθέτουμε το root του project στο path για να βρει τα core modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.ai_manager import AIManager
from core.database_manager import DatabaseManager
from sources.semantic_scholar_source import SemanticScholarSource

# --- ΒΟΗΘΗΤΙΚΕΣ ΣΥΝΑΡΤΗΣΕΙΣ ---

def get_paper_identifier(user_input: str) -> str:
    if not user_input: return ""
    cleaned_input = user_input.strip()
    if 'doi.org/' in cleaned_input:
        return cleaned_input.split('doi.org/')[-1]
    return cleaned_input

def analyze_paper_list(ai_manager: AIManager, papers: List[Dict[str, Any]], analysis_type: str, config: Dict[str, Any]) -> str:
    if not papers:
        return "Δεν βρέθηκαν σχετικά άρθρα για ανάλυση από το API."

    titles_text = "\n".join([f"- {p.get('title', 'N/A')}" for p in papers])
    
    prompt_key = f"orpheus_{analysis_type}_prompt_instruction"
    prompt_instruction = config.get(prompt_key, f"Analyze these {analysis_type}.")

    full_prompt = (
        config["phd_focus_system_prompt"] + 
        f"\n\n**// TASK: ANALYZE PAPER LIST //**\n{prompt_instruction}\n\n**// PAPER TITLES TO ANALYZE //**\n{titles_text}"
    )

    print(f"\nINFO: Αποστολή {len(papers)} τίτλων στο AI για ανάλυση {analysis_type}...")
    analysis_text = ai_manager.analyze_generic_text(full_prompt)
    
    if "failed" in analysis_text.lower() or not analysis_text.strip():
        return "Η ανάλυση από το AI απέτυχε ή δεν επέστρεψε κάποιο αποτέλεσμα."
        
    return analysis_text

def create_interactive_citation_graph(target_paper: Dict[str, Any], references: List[Dict[str, Any]], citations: List[Dict[str, Any]], output_path: str):
    net = Network(height="800px", width="100%", directed=True, notebook=False, bgcolor="#222222", font_color="white")
    target_id, target_title, target_url = target_paper.get('paperId'), target_paper.get('title', 'Target'), target_paper.get('url')
    
    net.add_node(target_id, label=target_title[:40]+'...', title=f"{target_title}\nURL:{target_url}", color='#e74c3c', size=25, shape='star')

    for ref in references[:20]:
        ref_id, ref_title, ref_url = ref.get('paperId'), ref.get('title', 'N/A'), ref.get('url')
        if not all([ref_id, ref_title, ref_url]): continue
        net.add_node(ref_id, label=ref_title[:40]+'...', title=f"{ref_title}\nURL:{ref_url}", color='#3498db', size=15)
        net.add_edge(ref_id, target_id)

    for cit in citations[:20]:
        cit_id, cit_title, cit_url = cit.get('paperId'), cit.get('title', 'N/A'), cit.get('url')
        if not all([cit_id, cit_title, cit_url]): continue
        net.add_node(cit_id, label=cit_title[:40]+'...', title=f"{cit_title}\nURL:{cit_url}", color='#2ecc71', size=15)
        net.add_edge(target_id, cit_id)
        
    net.show_buttons(filter_=['physics'])
    
    try:
        html_content = net.generate_html(notebook=False)
        click_handler_script = """
        <script type="text/javascript">
            network.on("stabilizationIterationsDone", function () {
                network.on("click", function(params) {
                    if (params.nodes.length > 0) {
                        var nodeId = params.nodes[0];
                        var node = network.body.data.nodes.get(nodeId);
                        if (node.title) {
                            var urlMatch = node.title.match(/URL:(https?:\\/\\/[^\\s]+)/);
                            if (urlMatch && urlMatch[1]) { window.open(urlMatch[1], '_blank'); }
                        }
                    }
                });
            });
        </script>
        """
        final_html = html_content.replace('</body>', click_handler_script + '</body>')
        with open(output_path, "w", encoding="utf-8") as f: f.write(final_html)
        print(f"\nINFO: Το διαδραστικό γράφημα αποθηκεύτηκε στο: {output_path}")
    except Exception as e:
        print(f"ERROR: Αποτυχία αποθήκευσης διαδραστικού γραφήματος: {e}")

def get_target_paper_from_user(db_manager: DatabaseManager) -> Union[str, None]:
    """
    Ρωτά τον χρήστη πώς θέλει να επιλέξει το άρθρο-στόχο και επιστρέφει το DOI.
    """
    choice = questionary.select(
        "Πώς θέλεις να επιλέξεις το άρθρο-στόχο;",
        choices=[
            "1. Εισαγωγή DOI ή URL του Semantic Scholar χειροκίνητα",
            "2. Επιλογή από τα πρόσφατα 'Core Papers' της βάσης TALOS"
        ],
        pointer="»"
    ).ask()

    if choice is None: return None

    if choice.startswith("1."):
        user_input = questionary.text("Εισάγετε το DOI ή το URL:").ask()
        return get_paper_identifier(user_input)
    
    if choice.startswith("2."):
        print("INFO: Ανάκτηση των πιο πρόσφατων 'Core Papers' (Overall Score >= 7)...")
        core_papers = db_manager.get_recent_core_papers(limit=15, min_score=7.0)
        
        if not core_papers:
            print("WARNING: Δεν βρέθηκαν 'Core Papers' στη βάση. Δοκιμάστε χειροκίνητη εισαγωγή.")
            return get_target_paper_from_user(db_manager)
            
        core_papers.sort(key=lambda p: p['overall_score'], reverse=True)
        
        # **Η ΔΙΟΡΘΩΣΗ ΕΙΝΑΙ ΕΔΩ**
        # Χρησιμοποιούμε questionary.Choice για να διαχωρίσουμε τον τίτλο (title)
        # από την τιμή που θα επιστραφεί (value).
        paper_choices = [
            questionary.Choice(
                title=f"[{p['overall_score']:.1f}] {p['title']}", 
                value=p['doi'] # Η τιμή που θα επιστραφεί είναι ΜΟΝΟ το DOI
            ) for p in core_papers
        ]
        
        selected_doi = questionary.select(
            "Διάλεξε ένα άρθρο από τη λίστα (ταξινομημένα κατά συνάφεια):",
            choices=paper_choices,
            pointer="»"
        ).ask()

        return selected_doi

def main():
    print("--- ΕΝΑΡΞΗ ORPHEUS CITATION ANALYZER (v2.1) ---")
    
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    config_path = os.path.join(project_root, 'config.json')
    try:
        with open(config_path, "r", encoding="utf-8") as f: config = json.load(f)
    except Exception as e:
        print(f"FATAL: Δεν ήταν δυνατή η φόρτωση του config.json. Σφάλμα: {e}")
        return

    ai_manager = AIManager(config)
    db_manager = DatabaseManager()
    s2_source = SemanticScholarSource(config)

    paper_doi = get_target_paper_from_user(db_manager)
    if not paper_doi:
        print("Δεν επιλέχθηκε άρθρο. Τερματισμός.")
        return
        
    print(f"INFO: Αναζήτηση για το άρθρο με DOI: {paper_doi}...")
    target_paper = s2_source.get_paper_details(paper_doi)
    if not target_paper:
        print(f"FATAL: Δεν βρέθηκε το άρθρο με DOI '{paper_doi}' στο Semantic Scholar.")
        return
    print(f"SUCCESS: Βρέθηκε το άρθρο-στόχος: '{target_paper['title']}'")

    target_paper_id = target_paper.get('paperId')
    print("\n[Ανάλυση 1/3] Ανάκτηση και ανάλυση βιβλιογραφικών αναφορών (references)...")
    references = s2_source.get_paper_references(target_paper_id, limit=100)
    references_analysis = analyze_paper_list(ai_manager, references, 'references', config)

    print("\n[Ανάλυση 2/3] Ανάκτηση και ανάλυση αναφορών προς το άρθρο (citations)...")
    citations = s2_source.get_paper_citations(target_paper_id, limit=100)
    citations_analysis = analyze_paper_list(ai_manager, citations, 'citations', config)

    print("\n[Ανάλυση 3/3] Δημιουργία γραφήματος δικτύου και σύνθεση τελικής αναφοράς...")
    safe_title = "".join(x for x in target_paper['title'][:50] if x.isalnum() or x in " _-").strip()
    reports_dir = os.path.join(project_root, "reports", "citations")
    os.makedirs(reports_dir, exist_ok=True)
    
    graph_filename = f"graph_{safe_title}.html"
    graph_filepath = os.path.join(reports_dir, graph_filename)
    create_interactive_citation_graph(target_paper, references, citations, graph_filepath)

    report_content = [
        f"# Ανάλυση Δικτύου Γνώσης: {target_paper['title']}",
        f"\n_Αναφορά από τον ORPHEUS στις {datetime.now().strftime('%d-%m-%Y %H:%M')}_",
        f"\n**Άρθρο-Στόχος:** [{target_paper['title']}]({target_paper.get('url')})",
        "\n---", "## 🏛️ Θεμελιώδεις Αναφορές (Foundational Pillars)",
        "_Τα πιο σημαντικά άρθρα πάνω στα οποία βασίστηκε η έρευνα:_",
        f"\n{references_analysis}", "\n---", "## 🚀 Εξέλιξη & Επιρροή (Legacy & Influence)",
        "_Έτσι εξελίχθηκε η έρευνα μετά από αυτή τη δημοσίευση:_",
        f"\n{citations_analysis}", "\n---", "## 📊 Διαδραστικό Δίκτυο Γνώσης",
        f"**Ανοίξτε το παρακάτω αρχείο στον browser σας για μια πλήρως διαδραστική εμπειρία:**",
        f"[{graph_filename}](./{graph_filename.replace(' ', '%20')})" 
    ]
    
    report_filename = os.path.join(reports_dir, f"orpheus_report_{safe_title}.md")
    with open(report_filename, 'w', encoding='utf-8') as f: f.write("\n".join(report_content))
    
    print(f"\n\nSUCCESS: Η αναφορά 'ORPHEUS' αποθηκεύτηκε με επιτυχία στο:\n{report_filename}")

if __name__ == "__main__":
    main()