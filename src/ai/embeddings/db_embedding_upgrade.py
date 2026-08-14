# -*- coding: utf-8 -*-
"""
Module: db_embedding_upgrade.py (v2.0)
Project: TALOS v5.9.18
Description:
    Phase 0: Database schema upgrade for Multi-Provider Hybrid Embeddings.

    Creates a standalone ``embeddings`` table that supports storing multiple
    embedding vectors per paper (one per provider). Migrates existing
    embeddings from the legacy ``embedding`` column.

    Usage:
        python scripts/db_embedding_upgrade.py

    New table:
        embeddings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            paper_id INTEGER NOT NULL,
            embedding BLOB NOT NULL,
            embedding_model TEXT NOT NULL,
            FOREIGN KEY (paper_id) REFERENCES papers(id)
        )
"""
import os
import sys
import sqlite3
import pickle
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def get_db_path() -> str:
    """Resolve the active database path, checking profile first.

    Returns:
        str: Absolute path to the target SQLite database.
    """
    profile_dir = PROJECT_ROOT / "_profiles"
    active_file = profile_dir / "active_profile.txt"
    if active_file.exists():
        try:
            active_profile = active_file.read_text(encoding="utf-8").strip()
            profile_db = profile_dir / active_profile / "talos_research.db"
            if profile_db.exists():
                return str(profile_db)
        except Exception:
            pass
    root_db = PROJECT_ROOT / "data" / "talos_research.db"
    return str(root_db)


def upgrade_database(db_path: str) -> bool:
    """Create embeddings table and migrate legacy data.

    Args:
        db_path (str): Full path to the SQLite database.

    Returns:
        bool: True if upgrade was successful.
    """
    if not os.path.exists(db_path):
        print(f"ERROR: Database not found at: {db_path}")
        return False

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # ── Step 1: Create embeddings table ──
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS embeddings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                paper_id INTEGER NOT NULL,
                embedding BLOB NOT NULL,
                embedding_model TEXT NOT NULL,
                FOREIGN KEY (paper_id) REFERENCES papers(id)
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_embeddings_paper_id ON embeddings(paper_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_embeddings_model ON embeddings(embedding_model)")
        conn.commit()
        print("  embeddings table ready (with indexes).")

        # ── Step 2: Migrate legacy data ──
        cursor.execute("SELECT id, embedding FROM papers WHERE embedding IS NOT NULL")
        legacy_rows = cursor.fetchall()
        
        migrated = 0
        if legacy_rows:
            print(f"  Migrating {len(legacy_rows)} legacy embeddings...")
            for paper_id, blob in legacy_rows:
                try:
                    # Validate the blob is a valid pickle
                    pickle.loads(blob)
                    cursor.execute(
                        "INSERT INTO embeddings (paper_id, embedding, embedding_model) VALUES (?, ?, ?)",
                        (paper_id, blob, "gemini")
                    )
                    migrated += 1
                except (pickle.UnpicklingError, EOFError):
                    print(f"  WARNING: Corrupted embedding for paper ID {paper_id}, skipping.")
            conn.commit()
            print(f"  {migrated} legacy embeddings migrated to 'gemini'.")

        # ── Step 3: Add embedding_model to papers (backwards compat) ──
        cursor.execute("PRAGMA table_info(papers)")
        columns = [row[1] for row in cursor.fetchall()]
        if "embedding_model" not in columns:
            cursor.execute("ALTER TABLE papers ADD COLUMN embedding_model TEXT DEFAULT 'gemini'")
            conn.commit()
            cursor.execute("UPDATE papers SET embedding_model = 'gemini' WHERE embedding IS NOT NULL AND embedding_model IS NULL")
            conn.commit()
            print("  Column 'embedding_model' added to papers table.")

        # ── Step 4: Summary ──
        cursor.execute("SELECT COUNT(*) FROM papers")
        total_papers = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM embeddings")
        total_embeddings = cursor.fetchone()[0]
        cursor.execute(
            "SELECT embedding_model, COUNT(*) FROM embeddings GROUP BY embedding_model ORDER BY COUNT(*) DESC"
        )
        distribution = cursor.fetchall()

        print(f"\n  Database: {db_path}")
        print(f"  Total papers: {total_papers}")
        print(f"  Total embeddings: {total_embeddings}")
        print(f"  Embedding distribution:")
        for model, count in distribution:
            print(f"    {model}: {count} vectors")
        
        # Show papers still needing embeddings
        cursor.execute("""
            SELECT COUNT(*) FROM papers p
            WHERE p.id NOT IN (SELECT DISTINCT paper_id FROM embeddings)
            AND p.abstract IS NOT NULL AND p.abstract != ''
        """)
        needing = cursor.fetchone()[0]
        print(f"  Papers still needing embeddings: {needing}")

        conn.close()
        return True

    except sqlite3.OperationalError as e:
        print(f"  ERROR (SQLite operational): {e}")
        return False
    except Exception as e:
        print(f"  ERROR (unexpected): {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Execute the database embedding upgrade."""
    print("=" * 60)
    print("  Project TALOS — Phase 0: Embedding Schema Upgrade v2.0")
    print("  Multi-Provider Embeddings Table")
    print("=" * 60)
    print()

    db_path = get_db_path()
    print(f"  Target database: {db_path}")

    if not os.path.exists(db_path):
        print(f"\nERROR: Database file not found at {db_path}")
        print("Create a database first by running a search.")
        sys.exit(1)

    success = upgrade_database(db_path)

    if success:
        print(f"\n  Upgrade completed successfully at {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    else:
        print(f"\n  Upgrade FAILED. Check errors above.")
        sys.exit(1)


if __name__ == "__main__":
    main()