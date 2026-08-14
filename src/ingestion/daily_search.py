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
Module: daily_search.py (Quad-Layer & Rate Limit Safe)
Project: TALOS v5.9.17

Description:
    The daily search orchestrator. Fetches new papers from all 14 configured
    source agents, deduplicates them by DOI/URL, and runs a two-stage AI
    evaluation pipeline: fast pre-screening (Flash model) for all new papers,
    followed by deep analysis (Pro model) for papers that exceed the minimum
    threshold. Generates a Markdown briefing report and optionally posts it
    to Discord via webhook. Respects configurable API call limits and rate
    delays to avoid quota exhaustion.
"""
import sys
import os, sys
_P = os.path.abspath(os.path.dirname(__file__))
while _P and not os.path.exists(os.path.join(_P, 'talos.py')):
    _P = os.path.dirname(_P)
if _P: sys.path.insert(0, _P)
import os
import json
from datetime import datetime
import time
import requests
from dotenv import load_dotenv

from src.ingestion.arxiv_source import ArxivSource
from src.ingestion.elsevier_source import ElsevierSource
from src.ingestion.semantic_scholar_source import SemanticScholarSource
from src.ingestion.ieee_source import IEEEXploreSource
from src.ingestion.springer_source import SpringerNatureSource
from src.ingestion.openalex_source import OpenAlexSource
from src.ingestion.dblp_source import DBLPSource
from src.ingestion.core_source import CORESource
from src.ingestion.crossref_source import CrossrefSource
from src.ingestion.openarchives_source import OpenArchivesSource
from src.ingestion.pubmed_source import PubMedSource
from src.ingestion.scigov_source import ScienceGovSource
from src.ingestion.osti_source import OSTISource
from src.ingestion.plos_source import PLOSSource

from src.core.database_manager import DatabaseManager
from src.core.ai_manager import AIManager


def generate_markdown_report(report_data: list) -> str:
    """Generate a Markdown briefing report from evaluation results.

    Args:
        report_data (list of dict): List of {'paper': ..., 'eval': ...} dictionaries.

    Returns:
        str: Complete Markdown report as a string.
    """
    timestamp = datetime.now().strftime('%d-%m-%Y')
    report_content = [f"# TALOS Daily Briefing - {timestamp}\n", f"Found **{len(report_data)}** high-relevance articles today.\n---"]
    for item in report_data:
        paper, evaluation = item['paper'], item['eval']
        scores = evaluation.get('scores', {})

        s_score = scores.get('strategic', 0)
        o_score = scores.get('operational', 0)
        t_score = scores.get('tactical', 0)
        p_score = scores.get('playground', 0)
        overall = evaluation.get('overall_score', 0)

        tags_str = f"`{'`, `'.join(evaluation.get('tags', []))}`" if evaluation.get('tags') else 'N/A'

        report_content.extend([
            f"\n## {paper.get('title', 'N/A')}",
            f"**Source:** {paper.get('source', 'N/A')} | **Link:** [{paper.get('doi', 'No DOI')}]({paper.get('url', '#')})",
            f"**Authors:** {paper.get('authors_str', 'N/A')}\n",
            f"### Scores: **{overall:.1f}** (Str: {s_score} | Opr: {o_score} | Tac: {t_score} | Sim: {p_score})",
            f"> **Reasoning:** {evaluation.get('reasoning', 'N/A')}",
            f"> **Key Contribution:** {evaluation.get('contribution', 'N/A')}",
            f"> **Potential Utilization:** {evaluation.get('utilization', 'N/A')}",
            f"> **Suggested Tags:** {tags_str}"
        ])
    return "\n".join(report_content)


def post_report_to_discord(config: dict, markdown_content: str, filename: str):
    """Post the daily briefing report to Discord via webhook.

    Args:
        config (dict): Application configuration.
        markdown_content (str): The Markdown report content.
        filename (str): Filename for the attachment.
    """
    load_dotenv()
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
    if not webhook_url:
        print("WARNING: DISCORD_WEBHOOK_URL not found. Skipping report.")
        return
    payload = {"content": f"TALOS Daily Briefing\nToday's report is ready."}
    files = {'file': (filename, markdown_content, 'text/markdown')}
    try:
        response = requests.post(webhook_url, data=payload, files=files, timeout=30)
        response.raise_for_status()
        print("  > Report sent to Discord successfully!")
    except requests.exceptions.RequestException as e:
        print(f"  > Discord Webhook Error: {e}")


def load_configuration():
    """Load the project configuration from config.json.

    Returns:
        dict: Configuration dictionary.

    Raises:
        SystemExit: If config.json is missing or invalid.
    """
    print("PHASE 1: Loading configuration...")
    project_root = _P if _P else os.getcwd()
    config_path = os.path.join(project_root, 'config.json')
    if not os.path.exists(config_path):
        config_path = os.path.join(project_root, 'config.template.json')
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"FATAL: Error loading config.json: {e}")
        sys.exit(1)


def main():
    """Run the daily search pipeline: fetch, filter, evaluate, report."""
    print("--- DAILY SEARCH (Quad-Layer & Rate Limit Safe) ---")
    config = load_configuration()
    print("SUCCESS: Configuration loaded.\n")
    ai_manager = AIManager(config)
    db_manager = DatabaseManager()
    db_manager.create_table()

    print("\n--- PHASE 2: Fetching & Filtering ---")
    sources_to_search = [
        ArxivSource(config),
        ElsevierSource(config),
        SemanticScholarSource(config),
        IEEEXploreSource(config),
        SpringerNatureSource(config),
        OpenAlexSource(config),
        DBLPSource(config),
        CrossrefSource(config),
        OpenArchivesSource(config),
        PubMedSource(config),
        OSTISource(config),
        ScienceGovSource(config),
        PLOSSource(config)
    ]
    import logging
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    logger = logging.getLogger(__name__)
    
    all_new_papers = []
    for source in sources_to_search:
        if not getattr(source, "enabled", True):
            logger.warning("Skipping %s — disabled (no valid API key)", type(source).__name__)
            continue
        try:
            papers = source.fetch_new_papers()
            if papers:
                all_new_papers.extend(papers)
            else:
                logger.info("No new papers from %s", type(source).__name__)
        except Exception as e:
            logger.error("Error fetching from %s: %s. Skipping source.", type(source).__name__, e)
            continue
    unique_papers_dict = {}
    for p in all_new_papers:
        key = p.get('doi') if p.get('doi') else p.get('url')
        if key:
            unique_papers_dict[key] = p
    papers_to_process = []
    for p in unique_papers_dict.values():
        if p.get('doi'):
            if not db_manager.paper_exists_by_doi(p['doi']):
                papers_to_process.append(p)
        elif p.get('url'):
            if not db_manager.paper_exists_by_url(p['url']):
                papers_to_process.append(p)

    if not papers_to_process:
        print("\nNo new articles found. Terminating.")
        return

    print(f"\n--- PHASE 3: Pre-screening (Flash Model) for {len(papers_to_process)} new articles ---")

    API_CALL_LIMIT = config.get("api_call_limit_flash", 950)
    REQUEST_DELAY = config.get("ai_request_delay", 5)
    min_score_for_deep_analysis = config.get("min_pre_screening_score", 6)

    api_calls_made = 0
    promising_papers = []

    for i, paper in enumerate(papers_to_process):
        if api_calls_made >= API_CALL_LIMIT:
            print(f"\nWARNING: Flash model API call limit reached. Stopping pre-screening.")
            break

        print(f"-> Pre-screening {i+1}/{len(papers_to_process)}: '{paper['title'][:80]}...'")
        content_for_ai = f"Title: {paper['title']}\nAbstract: {paper.get('abstract', '')}"

        evaluation_data = ai_manager.evaluate_paper_json(content_for_ai, model_type='flash')
        api_calls_made += 1

        if evaluation_data:
            db_manager.add_paper(paper, evaluation_data)
            overall = evaluation_data.get('overall_score', 0)
            print(f"   Score: {overall:.2f} (Saved)")
            if overall >= min_score_for_deep_analysis:
                promising_papers.append(paper)
        else:
            print(f"   WARNING: Flash evaluation failed for {paper['doi']}. Skipping.")

        time.sleep(REQUEST_DELAY)

    if not promising_papers:
        print("\nNo articles passed the threshold for deep analysis. Terminating.")
        return

    print(f"\n--- PHASE 4: Deep Analysis (Pro Model) for {len(promising_papers)} articles ---")
    PRO_LIMIT = config.get("api_call_limit_pro", 95)
    pro_calls_made = 0
    final_results_for_report = []

    for i, paper in enumerate(promising_papers):
        if pro_calls_made >= PRO_LIMIT:
            print(f"\nWARNING: Pro model API call limit reached. Stopping deep analysis.")
            break

        print(f"-> Deep Analysis {i+1}/{len(promising_papers)}: '{paper['title'][:80]}...'")
        content_for_ai = f"Title: {paper['title']}\nAbstract: {paper.get('abstract', '')}"

        deep_evaluation_data = ai_manager.evaluate_paper_json(content_for_ai, model_type='pro')
        pro_calls_made += 1

        if deep_evaluation_data:
            db_manager.update_paper_evaluation(db_manager.get_paper_id_by_doi(paper['doi']), deep_evaluation_data)
            final_results_for_report.append({'paper': paper, 'eval': deep_evaluation_data})

            scores = deep_evaluation_data.get('scores', {})
            print(f"   SUCCESS: S:{scores.get('strategic')} O:{scores.get('operational')} T:{scores.get('tactical')} P:{scores.get('playground')}")
        else:
            print(f"   WARNING: Pro evaluation failed for {paper['doi']}.")

        time.sleep(REQUEST_DELAY)

    if final_results_for_report:
        print("\n--- PHASE 5: Creating & Sending Report ---")
        report_filename = f"talos_briefing_{datetime.now().strftime('%Y%m%d')}.md"
        markdown_report = generate_markdown_report(final_results_for_report)
        briefings_dir = os.path.join(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')), "reports", "briefings")
        os.makedirs(briefings_dir, exist_ok=True)
        report_path = os.path.join(briefings_dir, report_filename)
        with open(report_path, 'w', encoding='utf-8') as f: f.write(markdown_report)
        print(f"  > Daily report saved to: {report_path}")
        post_report_to_discord(config, markdown_report, report_filename)

    print("\nScript completed successfully.")


if __name__ == "__main__":
    main()