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
Module: knowledge_path_generator.py (v1.8 - Final Bugfix)
Project: TALOS v3.0 - Project "CHIRON"

Description:
Η τελική, διορθωμένη έκδοση του "CHIRON".
- Επαναφέρει τη μέθοδο `_get_top_keywords_for_cluster` που είχε αφαιρεθεί
  κατά λάθος, διορθώνοντας το AttributeError κατά την εκτέλεση.
"""
import json
import os
import sys
import re
from datetime import datetime
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer
import questionary

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.database_manager import DatabaseManager
from core.ai_manager import AIManager

class KnowledgePathGenerator:
    def __init__(self, config: dict):
        self.config = config
        self.db_manager = DatabaseManager()
        self.ai_manager = AIManager(config)
        self.reports_dir = os.path.join(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')), "reports", "knowledge_paths")
        os.makedirs(self.reports_dir, exist_ok=True)
        print("INFO: Knowledge Path Generator 'CHIRON' (v1.8 - Final Bugfix) initialized.")
    
    def _get_user_goal(self) -> str:
        print("\n--- Project CHIRON: The Knowledge Path Forger ---")
        goal = questionary.text(
            "Τι θέλεις να μάθεις σε βάθος σήμερα; Περιέγραψε τον στόχο σου:",
            validate=lambda text: True if len(text.strip()) > 10 else "Please provide a more detailed goal."
        ).ask()
        return goal

    def _find_relevant_papers(self, goal_text: str, top_k: int = 100) -> pd.DataFrame:
        print(f"\n🔎 [1/5] Εκτέλεση σημασιολογικής αναζήτησης για '{goal_text[:50]}...'")
        query_vector_list = self.ai_manager.generate_embeddings([goal_text], task_type="RETRIEVAL_QUERY")
        if not query_vector_list: return pd.DataFrame()
        query_vector = np.array(query_vector_list[0])
        paper_ids = self.db_manager.semantic_search(query_vector, top_k=top_k)
        if not paper_ids: return pd.DataFrame()
        all_papers_df = self.db_manager.get_all_papers_as_dataframe()
        results_df = all_papers_df[all_papers_df['id'].isin(paper_ids)].copy()
        results_df['sort_order'] = pd.Categorical(results_df['id'], categories=paper_ids, ordered=True)
        results_df.sort_values('sort_order', inplace=True)
        print(f"SUCCESS: Βρέθηκαν {len(results_df)} σχετικά άρθρα.")
        return results_df

    def _extract_keywords_for_filename(self, goal_text: str) -> str:
        print("🔎 [2/5] Απόσταξη λέξεων-κλειδιών από τον στόχο...")
        try:
            prompt = f"Read the user query. Extract 2-3 keywords for the core topic. Return ONLY these keywords, in English, separated by underscore. Example: 'drone_swarms_drl'.\n\nQUERY: \"{goal_text}\""
            keywords = self.ai_manager.analyze_generic_text(prompt)
            safe_keywords = re.sub(r'[\W_]+', '_', keywords.strip().lower())
            return safe_keywords if safe_keywords else "general_query"
        except Exception:
            return "general_query"
            
    # **Η ΔΙΟΡΘΩΣΗ ΕΙΝΑΙ ΕΔΩ**: Επαναφέρουμε τη μέθοδο μέσα στην κλάση
    def _get_top_keywords_for_cluster(self, vectorizer, kmeans_model, cluster_id: int, top_n=4) -> str:
        """Βρίσκει τις πιο σημαντικές λέξεις-κλειδιά για ένα συγκεκριμένο cluster."""
        cluster_center = kmeans_model.cluster_centers_[cluster_id]
        top_term_indices = cluster_center.argsort()[::-1][:top_n]
        feature_names = vectorizer.get_feature_names_out()
        return ", ".join([feature_names[i] for i in top_term_indices])

    def _structure_knowledge(self, df: pd.DataFrame, num_clusters=4, min_score=7.0) -> dict:
        print("🔎 [3/5] Δόμηση της γνώσης (Foundational, Thematic, State-of-the-Art)...")
        cols_to_keep = ['title', 'publication_year', 'url', 'doi', 'overall_score']
        elite_papers = df[df['overall_score'] >= min_score].copy()
        sorted_by_year = elite_papers.sort_values(by='publication_year', ascending=True)
        foundational_papers = sorted_by_year.head(3)
        sota_papers = sorted_by_year.tail(3)
        if foundational_papers.equals(sota_papers): sota_papers = pd.DataFrame()
        core_ids = pd.concat([foundational_papers['id'], sota_papers['id']]).unique()
        papers_for_clustering = df[~df['id'].isin(core_ids)].copy()
        thematic_clusters = {}
        if len(papers_for_clustering) >= num_clusters:
            corpus = (papers_for_clustering['title'] + ' ' + papers_for_clustering['abstract']).fillna('')
            vectorizer = TfidfVectorizer(stop_words='english', max_features=1500, ngram_range=(1,2))
            X = vectorizer.fit_transform(corpus)
            kmeans = KMeans(n_clusters=num_clusters, random_state=42, n_init='auto')
            papers_for_clustering['cluster'] = kmeans.fit_predict(X)
            for i in range(num_clusters):
                cluster_df = papers_for_clustering[papers_for_clustering['cluster'] == i]
                if cluster_df.empty: continue
                keywords = self._get_top_keywords_for_cluster(vectorizer, kmeans, i)
                top_papers = cluster_df.sort_values(by='overall_score', ascending=False).head(4)
                thematic_clusters[f"Cluster - Focus on: {keywords}"] = top_papers[cols_to_keep].to_dict('records')
        structured_path = {'foundational': foundational_papers[cols_to_keep].to_dict('records'), 'state_of_the_art': sota_papers[cols_to_keep].to_dict('records'),'thematic_clusters': thematic_clusters}
        print("SUCCESS: Η δόμηση της γνώσης ολοκληρώθηκε.")
        return structured_path

    def _synthesize_narrative(self, structured_knowledge: dict, user_goal: str) -> str:
        print("🔎 [4/5] Σύνθεση αφηγηματικής αναφοράς με AI...")
        system_prompt = self.config.get("chiron_synthesizer_prompt", "Analyze:")
        data_prompt = [f"\n**// STUDENT'S GOAL: {user_goal} //**\n"]
        def format_paper_list(papers):
            lines = []
            for paper in papers:
                title, year, url, score = paper.get('title', 'N/A'), paper.get('publication_year'), paper.get('url', '#'), paper.get('overall_score', 0.0)
                year_str = f"[{int(year)}]" if year and pd.notna(year) else ""
                score_str = f"**[{score:.1f}/10]**"
                lines.append(f"- {score_str} {year_str} [{title}]({url})".strip())
            return lines
        if structured_knowledge['foundational']:
            data_prompt.append("\n**1. Foundational Papers (Start Here):**")
            data_prompt.extend(format_paper_list(structured_knowledge['foundational']))
        if structured_knowledge['thematic_clusters']:
            data_prompt.append("\n**2. Thematic Exploration (Dive Deeper):**")
            for cluster_name, papers in structured_knowledge['thematic_clusters'].items():
                data_prompt.append(f"\n  - **{cluster_name}**")
                data_prompt.extend([f"    {line}" for line in format_paper_list(papers)])
        if structured_knowledge['state_of_the_art']:
            data_prompt.append("\n**3. State-of-the-Art Papers (Finish Here):**")
            data_prompt.extend(format_paper_list(structured_knowledge['state_of_the_art']))
        full_prompt = system_prompt + "\n".join(data_prompt)
        narrative = self.ai_manager.analyze_generic_text(full_prompt)
        print("SUCCESS: Η αφηγηματική αναφορά δημιουργήθηκε.")
        return narrative

    def _save_report(self, topic_keywords: str, narrative_report: str):
        print("🔎 [5/5] Αποθήκευση αναφοράς...")
        date_str = datetime.now().strftime("%Y-%m-%d")
        date_dir = os.path.join(self.reports_dir, date_str)
        os.makedirs(date_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%H%M%S")
        filename = f"chiron_report_{topic_keywords}_{timestamp}.md"
        filepath = os.path.join(date_dir, filename)
        report_title = topic_keywords.replace('_', ' ').title()
        report_content = [
            f"# CHIRON Knowledge Path: {report_title}",
            f"_Report generated by TALOS v3.0 on {datetime.now().strftime('%d-%m-%Y %H:%M')}._",
            "\n---\n",
            narrative_report
        ]
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write("\n".join(report_content))
            print(f"SUCCESS: Η αναφορά αποθηκεύτηκε με επιτυχία στο:\n{filepath}")
        except IOError as e:
            print(f"ERROR: Δεν ήταν δυνατή η αποθήκευση της αναφοράς: {e}")

    def run(self):
        user_goal = self._get_user_goal()
        if not user_goal: return
        topic_keywords = self._extract_keywords_for_filename(user_goal)
        knowledge_corpus_df = self._find_relevant_papers(user_goal)
        if knowledge_corpus_df.empty:
            print("Δεν βρέθηκαν σχετικά άρθρα στη βάση για αυτόν τον στόχο.")
            return
        structured_knowledge = self._structure_knowledge(knowledge_corpus_df)
        narrative_report = self._synthesize_narrative(structured_knowledge, user_goal)
        self._save_report(topic_keywords, narrative_report)
        print("\n--- Η διαδικασία του CHIRON ολοκληρώθηκε ---")

if __name__ == '__main__':
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    config_path = os.path.join(project_root, 'config.json')
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config_data = json.load(f)
        generator = KnowledgePathGenerator(config_data)
        generator.run()
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"FATAL: Δεν ήταν δυνατή η φόρτωση του config.json. Σφάλμα: {e}")