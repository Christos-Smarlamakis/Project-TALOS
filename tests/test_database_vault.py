# -*- coding: utf-8 -*-
"""
Module: test_database_vault.py
Project: TALOS v5.24.0
Description:
    Unit tests for the Enterprise Database Vault
    (src/core/database_vault.py). Verifies integrity verification, atomic
    snapshot creation (VACUUM INTO), rolling snapshot rotation, and snapshot
    restoration using an isolated temporary SQLite database.

Dependencies:
    - pytest, sqlite3, time, os: test framework, database fixture, and aging.
    - src.core.database_vault: DatabaseVault.
"""

import os
import sqlite3
import time

import pytest

from src.core.database_vault import DatabaseVault


@pytest.fixture
def vault_db(tmp_path):
    db_path = tmp_path / "talos_research.db"
    conn = sqlite3.connect(str(db_path))
    conn.execute("CREATE TABLE papers (id INTEGER PRIMARY KEY, title TEXT)")
    conn.execute("INSERT INTO papers (title) VALUES ('alpha')")
    conn.commit()
    conn.close()
    return db_path


class TestDatabaseVault:
    def test_verify_integrity_passes_on_healthy_db(self, vault_db):
        vault = DatabaseVault(backup_dir="data/backups", db_path=vault_db)
        result = vault.verify_integrity(vault_db)
        assert result["ok"] is True
        assert result["integrity_check"] == "ok"
        assert result["quick_check"] == "ok"
        assert result["foreign_key_check"] == 0

    def test_verify_integrity_missing_file(self, tmp_path):
        vault = DatabaseVault(backup_dir="data/backups")
        result = vault.verify_integrity(tmp_path / "nope.db")
        assert result["ok"] is False
        assert result["error"] == "database file not found"

    def test_create_atomic_snapshot(self, vault_db, tmp_path):
        backup_dir = tmp_path / "backups"
        vault = DatabaseVault(backup_dir=backup_dir, db_path=vault_db)
        snapshot = vault.create_atomic_snapshot()
        assert snapshot.exists()
        assert snapshot.name.startswith("talos_backup_")
        conn = sqlite3.connect(str(snapshot))
        rows = conn.execute("SELECT COUNT(*) FROM papers").fetchone()[0]
        conn.close()
        assert rows == 1

    def test_snapshot_rotation_prunes_old(self, vault_db, tmp_path):
        backup_dir = tmp_path / "backups"
        vault = DatabaseVault(backup_dir=backup_dir, db_path=vault_db)
        snap = vault.create_atomic_snapshot()
        old = time.time() - (8 * 86400)
        os.utime(snap, (old, old))
        vault.create_atomic_snapshot()  # triggers rotation
        assert not snap.exists()

    def test_restore_snapshot(self, vault_db, tmp_path):
        backup_dir = tmp_path / "backups"
        vault = DatabaseVault(backup_dir=backup_dir, db_path=vault_db)
        snapshot = vault.create_atomic_snapshot()
        conn = sqlite3.connect(str(vault_db))
        conn.execute("DROP TABLE papers")
        conn.commit()
        conn.close()
        assert vault.restore_snapshot(snapshot) is True
        conn = sqlite3.connect(str(vault_db))
        rows = conn.execute("SELECT COUNT(*) FROM papers").fetchone()[0]
        conn.close()
        assert rows == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
