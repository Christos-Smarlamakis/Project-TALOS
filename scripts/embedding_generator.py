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
Module: embedding_generator.py (v3.1 - Full Documentation & Harmonization)
Project: TALOS v4.8.5

Description:
    Generates semantic embeddings for all papers in the database that lack them.
    Processes papers in configurable batches via the AIManager's embedding
    provider (local Ollama or Gemini), serializes vectors with pickle, and
    stores them in the database for cosine similarity semantic search.
    Includes progress bars, error handling, and rate-limit-friendly delays
    between batches.
"""
import os
import sys
import json
import time
import pickle
from tqdm import tqdm
import numpy as np

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.database_manager import DatabaseManager
from core.ai_manager import AIManager

BATCH_SIZE = 100


def load_configuration():
    """Load the project configuration from config.json.

    Returns:
        dict: Configuration dictionary.

    Raises:
        SystemExit: If config.json is missing or invalid.
    """
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    config_path = os.path.join(project_root, 'config.json')
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"FATAL: Could not load config.json. Error: {e}")
        sys.exit(1)


def main():
    """Generate embeddings for all papers missing them.

    1. Initializes core modules and AIManager.
    2. Fetches papers without embeddings from the database.
    3. Processes them in batches of BATCH_SIZE.
    4. For each batch, calls the AI to generate embedding vectors.
    5. Serializes vectors with pickle and stores them in bulk.
    """
    print("--- EMBEDDING GENERATION STARTED (v3.1) ---")

    config = load_configuration()
    ai_manager = AIManager(config)
    db_manager = DatabaseManager()

    print("INFO: Fetching papers that need embeddings from the database...")
    papers_to_embed = db_manager.get_papers_without_embedding()

    if not papers_to_embed:
        print("INFO: All papers already have embeddings. Terminating.")
        return

    print(f"Found {len(papers_to_embed)} papers to process.")

    with tqdm(total=len(papers_to_embed), desc="Generating Embeddings") as pbar:
        for i in range(0, len(papers_to_embed), BATCH_SIZE):
            batch = papers_to_embed[i:i + BATCH_SIZE]

            texts_to_embed = [
                f"Title: {paper['title']}\nAbstract: {paper['abstract']}"
                for paper in batch
            ]

            embedding_vectors = ai_manager.generate_embeddings(texts_to_embed)

            if not embedding_vectors or len(batch) != len(embedding_vectors):
                print(f"\nWARNING: Size mismatch or API error for batch index {i}. Skipping this batch.")
                pbar.update(len(batch))
                time.sleep(1)
                continue

            updates = []
            for paper, vector in zip(batch, embedding_vectors):
                embedding_blob = pickle.dumps(np.array(vector))
                updates.append((embedding_blob, paper['id']))

            db_manager.update_embeddings_batch(updates)
            pbar.update(len(batch))
            time.sleep(2)

    print("\n--- EMBEDDING GENERATION COMPLETE ---")


if __name__ == "__main__":
    main()