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
Module: historic_search.py (v5.5 - Final Quad-Layer & Rate Limit)
Project: TALOS v4.8.5

Description:
    The deep archive search orchestrator. Fetches papers from all 14 configured
    source agents spanning a multi-year window (configurable via
    ``days_to_search_historic``, default ~6 years), deduplicates by DOI/URL,
    and evaluates all new papers with the Flash model using Quad-Layer scoring.
    Designed for initial database population and periodic deep dives.
    Respects API call limits and rate delays to avoid quota exhaustion.
"""
import sys
import os, sys
_P = os.path.abspath(os.path.dirname(__file__))
while _P and not os.path.exists(os.path.join(_P, 'talos.py')):
    _P = os.path.dirname(_P)
if _P: sys.path.insert(0, _P)
import os
import time
import json
from dotenv import load_dotenv

from src.ingestion.arxiv_source import ArxivSource
from src.ingestion.elsevier_source import ElsevierSource
from src.ingestion.semantic_scholar_source import SemanticScholarSource
from src.ingestion.ieee_source import IEEEXploreSource
from src.ingestion.springer_source import SpringerNatureSource
from src.ingestion.openalex_source import OpenAlexSource
from src.ingestion.dblp_source import DBLPSource
from src.ingestion.crossref_source import CrossrefSource
from src.ingestion.openarchives_source import OpenArchivesSource
from src.ingestion.pubmed_source import PubMedSource
from src.ingestion.osti_source import OSTISource
from src.ingestion.scigov_source import ScienceGovSource
from src.ingestion.plos_source import PLOSSource
from src.ingestion.core_source import CORESource

from src.core.database_manager import DatabaseManager
from src.core.ai_manager import AIManager


def load_configuration():
    """Load the project configuration from config.json.

    Returns:
        dict: Configuration dictionary.

    Raises:
        SystemExit: If config.json is missing or invalid.
    """
    print("PHASE 1: Loading configuration...")
    load_dotenv()
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    config_path = os.path.join(project_root, 'config.json')
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
        print("SUCCESS: Configuration loaded.\n")
        return config
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"FATAL: Error loading config.json: {e}")
        sys.exit(1)


def main():
    """Run the historical search pipeline: fetch all sources, deduplicate, evaluate, store."""
    print("--- HISTORICAL SEARCH STARTED (v5.5 - Quad-Layer) ---")

    config = load_configuration()
    ai_manager = AIManager(config)
    db_manager = DatabaseManager()

    historic_config = config.copy()
    days_historic = config.get("days_to_search_historic", 2190)
    historic_config["days_to_search_daily"] = days_historic
    print(f"INFO: Search configured for the last {days_historic} days.\n")

    sources_to_search = [
        ArxivSource(historic_config),
        ElsevierSource(historic_config),
        SemanticScholarSource(historic_config),
        IEEEXploreSource(historic_config),
        SpringerNatureSource(historic_config),
        OpenAlexSource(historic_config),
        DBLPSource(historic_config),
        CrossrefSource(historic_config),
        OpenArchivesSource(historic_config),
        PubMedSource(historic_config),
        ScienceGovSource(historic_config),
        OSTISource(historic_config),
        PLOSSource(historic_config),
        CORESource(historic_config)
    ]

    import logging
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    logger = logging.getLogger(__name__)
    
    all_historic_papers = []
    for source in sources_to_search:
        if not getattr(source, "enabled", True):
            logger.warning("Skipping %s — disabled (no valid API key)", type(source).__name__)
            continue
        try:
            fetched = source.fetch_new_papers()
            if fetched:
                all_historic_papers.extend(fetched)
            else:
                logger.info("No new papers from %s", type(source).__name__)
        except Exception as e:
            logger.error("Error fetching from %s: %s. Skipping source.", type(source).__name__, e)
            continue

    print(f"\nSUCCESS: Found {len(all_historic_papers)} potential papers across all sources.\n")

    unique_papers_dict = {}
    for p in all_historic_papers:
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
        print("INFO: Database appears to be already up to date. Terminating.")
        return

    print(f"INFO: Found {len(papers_to_process)} new, unique papers to add to the database.")

    API_CALL_LIMIT = config.get("api_call_limit_flash", 950)
    REQUEST_DELAY = config.get("ai_request_delay", 5)
    api_calls_made = 0

    for i, paper in enumerate(papers_to_process):
        if api_calls_made >= API_CALL_LIMIT:
            print(f"\nWARNING: Reached the limit of {API_CALL_LIMIT} calls. Stopping for today.")
            break

        print(f"-> Processing paper {i+1}/{len(papers_to_process)}: '{paper['title'][:80]}...'")

        content_for_ai = f"Title: {paper['title']}\nAbstract: {paper.get('abstract', '')}"

        evaluation_data = ai_manager.evaluate_paper_json(content_for_ai, model_type='flash')
        api_calls_made += 1

        if evaluation_data:
            db_manager.add_paper(paper, evaluation_data)

            scores = evaluation_data.get('scores', {})
            s = scores.get('strategic', 0)
            o = scores.get('operational', 0)
            t = scores.get('tactical', 0)
            p = scores.get('playground', 0)
            overall = evaluation_data.get('overall_score', 0)

            print(f"   SUCCESS: [S:{s} O:{o} T:{t} P:{p}] -> Overall: {overall:.2f}")
        else:
            print(f"   WARNING: Evaluation failed. Skipping.")

        time.sleep(REQUEST_DELAY)

    print("\n--- HISTORICAL SEARCH COMPLETE ---")


if __name__ == "__main__":
    main()