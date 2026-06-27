"""Fix B2, B3, B4, B6"""
import os
os.chdir(r"c:\Users\Chris\Desktop\Project_Talos_v4.8.1_GitHub")

def patch(path, old, new, desc):
    with open(path, 'r', encoding='utf-8') as f:
        data = f.read()
    if old not in data:
        print(f"FAIL [{desc}]: not found")
        return
    data = data.replace(old, new)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(data)
    print(f"OK   [{desc}]")

# B2: Elsevier graceful degradation
patch("sources/elsevier_source.py",
    'if not self.api_key or not self.inst_token:\n            raise ValueError("Elsevier API keys not found in .env file.")\n        self.client = ElsClient(self.api_key, inst_token=self.inst_token)',
    'self.enabled = True\n        if not self.api_key or not self.inst_token:\n            print("WARNING: Elsevier API keys not found. Skipping.")\n            self.enabled = False\n            return\n        self.client = ElsClient(self.api_key, inst_token=self.inst_token)',
    "B2-Elsevier")

# B2: IEEE graceful degradation
patch("sources/ieee_source.py",
    'if not self.api_key: raise ValueError("IEEE_API_KEY not found in .env file.")\n        self.query',
    'self.enabled = True\n        if not self.api_key:\n            print("WARNING: IEEE_API_KEY not found. Skipping.")\n            self.enabled = False\n            return\n        self.query',
    "B2-IEEE")

# B3: recommender operational_score
patch("scripts/recommender.py",
    'strategic_score, tactical_score, playground_score, overall_score,',
    'strategic_score, operational_score, tactical_score, playground_score, overall_score,',
    "B3-recommender")

# B4: dashboard safe sort
patch("scripts/interactive_dashboard.py",
    "results_data.sort(key=lambda x: sorted_paper_ids.index(x['id']))",
    "id_order = {pid: i for i, pid in enumerate(sorted_paper_ids)}\n        results_data.sort(key=lambda x: id_order.get(x['id'], len(sorted_paper_ids)))",
    "B4-dashboard")

# B6: daily_search DOI fallback
patch("scripts/daily_search.py",
    "all_new_papers = [p for source in sources_to_search for p in source.fetch_new_papers() if p]\n    unique_papers_dict = {p['doi']: p for p in all_new_papers if p.get('doi')}\n    papers_to_process = [p for p in unique_papers_dict.values() if not db_manager.paper_exists_by_doi(p['doi'])]",
    "all_new_papers = [p for source in sources_to_search for p in source.fetch_new_papers() if p]\n    unique_papers_dict = {}\n    for p in all_new_papers:\n        key = p.get('doi') if p.get('doi') else p.get('url')\n        if key:\n            unique_papers_dict[key] = p\n    papers_to_process = []\n    for p in unique_papers_dict.values():\n        if p.get('doi'):\n            if not db_manager.paper_exists_by_doi(p['doi']):\n                papers_to_process.append(p)\n        elif p.get('url'):\n            if not db_manager.paper_exists_by_url(p['url']):\n                papers_to_process.append(p)",
    "B6-daily_search")

print("Part A done!")
