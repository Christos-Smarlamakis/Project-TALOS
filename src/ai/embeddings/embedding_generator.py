# -*- coding: utf-8 -*-
"""
Module: embedding_generator.py (v4.0 — Multi-Model Seed All)
Project: TALOS v5.0.0
Description:
    Generates semantic embeddings using all available providers.

    Usage:
        python scripts/embedding_generator.py          # current provider only
        python scripts/embedding_generator.py --all    # ALL available models
"""
import os
import sys
import os, sys
_P = os.path.abspath(os.path.dirname(__file__))
while _P and not os.path.exists(os.path.join(_P, 'talos.py')):
    _P = os.path.dirname(_P)
if _P: sys.path.insert(0, _P)
import json
import time
import pickle
from tqdm import tqdm
import numpy as np

from src.core.database_manager import DatabaseManager
from src.core.ai_manager import AIManager

BATCH_SIZE = 10
# All known models we want to seed
ALL_MODELS = [
    ("ollama:nomic-embed-text", "local"),
    ("gemini:gemini-embedding-001", "gemini"),
]


def load_configuration():
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    config_path = os.path.join(project_root, 'config.json')
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"FATAL: Could not load config.json. Error: {e}")
        sys.exit(1)


def generate_for_model(ai_manager, db_manager, model_name, provider_name):
    """Generate embeddings using a specific model and store them.

    Returns (generated, failed) counts.
    """
    print(f"\n{'='*60}")
    print(f"  MODEL: {model_name} (provider: {provider_name})")
    print(f"{'='*60}")

    papers_to_embed = db_manager.get_papers_needing_embedding(model=model_name)

    if not papers_to_embed:
        print(f"  All papers already have {model_name} embeddings. Skipping.")
        return 0, 0

    print(f"  Papers to process: {len(papers_to_embed)}")
    generated = 0
    failed = 0

    with tqdm(total=len(papers_to_embed), desc=f"  {model_name}") as pbar:
        for i in range(0, len(papers_to_embed), BATCH_SIZE):
            batch = papers_to_embed[i:i + BATCH_SIZE]

            texts_to_embed = [
                f"Title: {paper['title']}\nAbstract: {paper['abstract']}"
                for paper in batch
            ]

            result = ai_manager.generate_embeddings(texts_to_embed)
            embedding_vectors, used_model = result if isinstance(result, tuple) else (result, 'unknown')

            if not embedding_vectors or len(batch) != len(embedding_vectors):
                failed += len(batch)
                print(f"\n  WARNING: Batch {i//BATCH_SIZE} failed. Skipping {len(batch)} papers.")
                pbar.update(len(batch))
                time.sleep(1)
                continue

            updates = []
            for paper, vector in zip(batch, embedding_vectors):
                embedding_blob = pickle.dumps(np.array(vector))
                updates.append((paper['id'], embedding_blob, model_name))

            try:
                db_manager.store_embeddings_batch(updates)
                generated += len(batch)
            except Exception as e:
                print(f"\n  ERROR storing batch: {e}")
                failed += len(batch)

            pbar.update(len(batch))
            time.sleep(3)

    print(f"  Model {model_name}: {generated} generated, {failed} failed")
    return generated, failed


def main():
    print("--- EMBEDDING GENERATION STARTED (v4.0) ---")

    config = load_configuration()
    ai_manager = AIManager(config)
    db_manager = DatabaseManager()

    # Collect statistics
    import sqlite3
    with sqlite3.connect(db_manager.db_path) as conn:
        total_papers = conn.cursor().execute("SELECT COUNT(*) FROM papers").fetchone()[0]
        without_abstract = conn.cursor().execute(
            "SELECT COUNT(*) FROM papers WHERE abstract IS NULL OR abstract=''").fetchone()[0]
        with_abstract = total_papers - without_abstract

    print(f"\n  Database: {os.path.basename(db_manager.db_path)}")
    print(f"  Total papers: {total_papers}")
    print(f"  With abstract: {with_abstract}")
    print(f"  Without abstract: {without_abstract}")

    # Show current distribution
    print("\n  Current embedding distribution:")
    stats = db_manager.get_embedding_model_stats()
    if stats:
        for s in stats:
            print(f"    {s['model']}: {s['count']} papers")
    else:
        print("    (no embeddings yet)")

    run_all = "--all" in sys.argv

    if run_all:
        print("\n" + "=" * 60)
        print("  SEED ALL MODE — Processing ALL available models")
        print("=" * 60)

        summary = {}
        for model_name, provider_name in ALL_MODELS:
            gen, fail = generate_for_model(
                AIManager(config),  # fresh AIManager per model to reset circuit breakers
                db_manager,
                model_name,
                provider_name
            )
            summary[model_name] = (gen, fail)
            time.sleep(3)  # brief pause between models

        # ── Final Summary ──
        print("\n" + "=" * 60)
        print("  EMBEDDING GENERATION SUMMARY")
        print("=" * 60)
        print(f"  Total papers in database:    {total_papers}")
        print(f"  Papers without abstract:     {without_abstract}  (skipped — no text to embed)")
        print(f"  Papers with abstract:        {with_abstract}")
        print("  " + "-" * 52)
        for model_name, (gen, fail) in summary.items():
            print(f"  {model_name}:  {gen:>6} generated  |  {fail:>6} failed")
        print("  " + "-" * 52)
        total_gen = sum(g for g, f in summary.values())
        total_fail = sum(f for g, f in summary.values())
        print(f"  TOTAL:                      {total_gen:>6} generated  |  {total_fail:>6} failed")
        if total_fail > 0:
            print(f"\n  Reasons for failures:")
            print(f"    - Missing abstract: {without_abstract} papers")
            print(f"    - Model/API errors: {total_fail} attempts")
        print("=" * 60)
    else:
        # ── Single model mode (backward compatible) ──
        model_name = ai_manager.active_embedding_model
        if not model_name:
            try:
                result = ai_manager.generate_embeddings(["test discovery"])
                _, model_name = result if isinstance(result, tuple) else (result, None)
            except Exception:
                model_name = None

        if not model_name:
            print("\n  WARNING: Could not determine active embedding model.")
            print("  Try: python scripts/embedding_generator.py --all")
            return

        print(f"\n  Active model: {model_name}")
        gen, fail = generate_for_model(ai_manager, db_manager, model_name, "auto-detected")

        # Brief summary
        print("\n  Summary:")
        print(f"    {model_name}: {gen} generated, {fail} failed")
        print(f"    Papers without abstract (skipped): {without_abstract}")

    print("\n--- EMBEDDING GENERATION COMPLETE ---")


if __name__ == "__main__":
    main()