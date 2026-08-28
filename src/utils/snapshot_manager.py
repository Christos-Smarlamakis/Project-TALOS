# -*- coding: utf-8 -*-
"""
Module: snapshot_manager.py
Project: TALOS v5.10.16
Description:
    Lightweight, dependency-free SQLite snapshotting for destructive maintenance
    operations (VACUUM, full re-scoring, full re-evaluation). Produces a consistent
    online backup using the standard-library sqlite3.Connection.backup() API, which
    is safe while WAL mode is active and other connections are live, and falls back
    to shutil.copy2 when the backup API is unavailable. Timestamped snapshots are
    written under _profiles/<active>/backups/ with a rolling retention policy.

Dependencies:
    - os, shutil, sqlite3, datetime: Standard library utilities.
    - src.core.database_manager.get_active_profile_db_path: Active DB resolution.
"""

import os
import sys
import shutil
import sqlite3
from datetime import datetime

# -- Resolve project root (same pattern as all src/*.py modules) --------------
_P = os.path.abspath(os.path.dirname(__file__))
while _P and not os.path.exists(os.path.join(_P, 'talos.py')):
    _P = os.path.dirname(_P)
if _P:
    sys.path.insert(0, _P)

from src.core.database_manager import get_active_profile_db_path


def _resolve_backup_dir(db_path):
    """Return the backup directory adjacent to the active profile database.

    Args:
        db_path (str): Path to the active database file.

    Returns:
        str: Absolute path to the snapshot directory.
    """
    if db_path:
        return os.path.join(os.path.dirname(os.path.abspath(db_path)), 'backups')
    project_root = _P or os.getcwd()
    return os.path.join(project_root, 'data', 'backups')


def _prune_snapshots(backup_dir, keep):
    """Retain only the most recent ``keep`` snapshot files.

    Args:
        backup_dir (str): Directory containing timestamped snapshots.
        keep (int): Number of snapshots to retain.
    """
    try:
        files = sorted(
            (os.path.join(backup_dir, f) for f in os.listdir(backup_dir)
             if f.startswith('talos_research_') and f.endswith('.db')),
            key=os.path.getmtime,
            reverse=True,
        )
        for stale in files[keep:]:
            try:
                os.remove(stale)
            except OSError:
                pass
    except OSError:
        pass


def snapshot_database(db_path=None, backup_dir=None, keep=5):
    """Create a consistent, timestamped snapshot of the SQLite database.

    Uses the sqlite3 online backup API so the snapshot is transactionally
    consistent even while WAL mode is active. Falls back to a plain file copy
    when the backup API is unavailable.

    Args:
        db_path (str | None): Explicit database path. Defaults to the active
            profile database.
        backup_dir (str | None): Target directory. Defaults to
            ``<db_dir>/backups``.
        keep (int): Number of most recent snapshots to retain.

    Returns:
        str | None: Absolute path to the created snapshot, or None on failure.
    """
    if not db_path:
        db_path = get_active_profile_db_path()

    if not db_path or not os.path.exists(db_path):
        print("[SNAPSHOT] Skipped: database not found.")
        return None

    backup_dir = backup_dir or _resolve_backup_dir(db_path)
    os.makedirs(backup_dir, exist_ok=True)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    target = os.path.join(backup_dir, f"talos_research_{timestamp}.db")

    try:
        source = sqlite3.connect(db_path)
        try:
            dest = sqlite3.connect(target)
            try:
                source.backup(dest)
                dest.commit()
            finally:
                dest.close()
        finally:
            source.close()
    except Exception as exc:
        print(f"[SNAPSHOT] Backup API failed ({exc}); falling back to file copy.")
        try:
            shutil.copy2(db_path, target)
        except Exception as copy_exc:
            print(f"[SNAPSHOT] File copy also failed: {copy_exc}")
            return None

    _prune_snapshots(backup_dir, keep)
    print(f"[SNAPSHOT] Created: {target}")
    return target


if __name__ == "__main__":
    path = snapshot_database()
    print("Snapshot complete." if path else "Snapshot failed.")
