# -*- coding: utf-8 -*-
"""
Module: database_vault.py
Project: TALOS v5.24.0
Description:
    Enterprise database vault for TALOS. Provides automated SQLite integrity
    verification, atomic snapshot (backup) creation via ``VACUUM INTO``, and
    safe snapshot restoration with rolling retention. The vault is the
    Reliability (Fault Tolerance / Recoverability) and Security / Integrity
    enforcement point of the ISO/IEC 25010 standard: it detects corruption at
    startup and preserves a recoverable, rotation-managed snapshot lineage.

    Key design decisions:
    - ``verify_integrity`` runs ``PRAGMA integrity_check``, ``PRAGMA
      quick_check``, and ``PRAGMA foreign_key_check``, returning a structured
      verdict instead of raising so callers degrade gracefully (Constitution
      II / III).
    - ``create_atomic_snapshot`` uses the native ``VACUUM INTO`` statement so
      the backup is a single, transactionally-consistent file with no partial
      copy window; the target filename embeds a UTC timestamp.
    - ``restore_snapshot`` verifies the snapshot's integrity BEFORE it is
      swapped in, preventing a corrupt backup from replacing a healthy live
      database.
    - The 7-day rolling retention prunes snapshots older than the retention
      window, keeping the vault bounded and deterministic.

Dependencies:
    - sqlite3: integrity PRAGMAs and ``VACUUM INTO`` atomic backup.
    - os, pathlib, time, shutil: filesystem resolution, timestamping, and safe
      file replacement.
    - typing: type annotations.
"""

import shutil
import sqlite3
import time
from pathlib import Path
from typing import Any, Dict, Optional


class DatabaseVault:
    """Automated SQLite integrity vault with atomic snapshot rotation.

    Attributes:
        backup_dir (Path): Default directory for atomic snapshots.
        max_retention_days (int): Rolling retention window in days.
    """

    def __init__(
        self,
        backup_dir: Path = Path("data/backups"),
        max_retention_days: int = 7,
        db_path: Optional[Path] = None,
    ) -> None:
        self.backup_dir = Path(backup_dir)
        self.max_retention_days = max_retention_days
        self._db_path = Path(db_path) if db_path is not None else None

    # ------------------------------------------------------------------
    # -- Integrity -----------------------------------------------------
    # ------------------------------------------------------------------

    def verify_integrity(self, db_path: Path = None) -> Dict[str, Any]:
        """Run the SQLite integrity PRAGMAs and return a structured verdict.

        Args:
            db_path (Path): Target database path. When omitted, the active
                profile database is resolved automatically.

        Returns:
            dict: ``{"ok", "path", "integrity_check", "quick_check",
                "foreign_key_check", "error"}``.
        """
        db_path = self._resolve_db(db_path)
        result: Dict[str, Any] = {
            "ok": True,
            "path": str(db_path),
            "integrity_check": "",
            "quick_check": "",
            "foreign_key_check": 0,
            "error": None,
        }
        if not db_path.exists():
            result["ok"] = False
            result["error"] = "database file not found"
            return result
        try:
            conn = sqlite3.connect(str(db_path))
            try:
                result["integrity_check"] = conn.execute(
                    "PRAGMA integrity_check"
                ).fetchone()[0]
                result["quick_check"] = conn.execute(
                    "PRAGMA quick_check"
                ).fetchone()[0]
                result["foreign_key_check"] = len(
                    conn.execute("PRAGMA foreign_key_check").fetchall()
                )
            finally:
                conn.close()
            result["ok"] = (
                result["integrity_check"] == "ok"
                and result["quick_check"] == "ok"
                and result["foreign_key_check"] == 0
            )
        except sqlite3.Error as exc:
            result["ok"] = False
            result["error"] = str(exc)
        return result

    def quick_status(self) -> bool:
        """Run a lightweight quick_check for HUD display.

        Unlike :meth:`verify_integrity`, this avoids the full ``integrity_check``
        scan so it is safe to call on every HUD render.

        Returns:
            bool: True when the active database passes ``quick_check``.
        """
        db_path = self._resolve_db(None)
        if not db_path.exists():
            return False
        try:
            conn = sqlite3.connect(str(db_path))
            try:
                row = conn.execute("PRAGMA quick_check").fetchone()
                return row is not None and row[0] == "ok"
            finally:
                conn.close()
        except sqlite3.Error:
            return False

    # ------------------------------------------------------------------
    # -- Atomic snapshots ----------------------------------------------
    # ------------------------------------------------------------------

    def create_atomic_snapshot(
        self,
        backup_dir: Path = None,
        max_retention_days: int = None,
    ) -> Path:
        """Create a single atomic snapshot via ``VACUUM INTO`` and rotate.

        Args:
            backup_dir (Path): Destination directory (default: instance value).
            max_retention_days (int): Retention window override.

        Returns:
            Path: The created snapshot file path.
        """
        backup_dir = Path(backup_dir) if backup_dir is not None else self.backup_dir
        retention = (
            max_retention_days
            if max_retention_days is not None
            else self.max_retention_days
        )
        db_path = self._resolve_db(None)
        backup_dir.mkdir(parents=True, exist_ok=True)

        # -- Timestamped filename with a monotonic collision guard for rapid
        #    calls (avoiding the non-portable %f strftime directive). --
        timestamp = time.strftime("%Y%m%d_%H%M%S", time.gmtime())
        snapshot_path = backup_dir / f"talos_backup_{timestamp}.db"
        suffix = 0
        while snapshot_path.exists():
            suffix += 1
            snapshot_path = backup_dir / f"talos_backup_{timestamp}_{suffix}.db"

        conn = sqlite3.connect(str(db_path))
        try:
            conn.execute(f"VACUUM INTO '{snapshot_path}'")
        finally:
            conn.close()

        self._rotate(backup_dir, retention)
        return snapshot_path

    def _rotate(self, backup_dir: Path, max_retention_days: int) -> None:
        """Prune snapshots older than the rolling retention window."""
        cutoff = time.time() - (max_retention_days * 86400)
        for snapshot in backup_dir.glob("talos_backup_*.db"):
            try:
                if snapshot.stat().st_mtime < cutoff:
                    snapshot.unlink()
            except OSError:
                continue

    # ------------------------------------------------------------------
    # -- Restoration ---------------------------------------------------
    # ------------------------------------------------------------------

    def restore_snapshot(self, snapshot_path: Path) -> bool:
        """Verify a snapshot then restore it over the live database.

        Args:
            snapshot_path (Path): Snapshot file to restore from.

        Returns:
            bool: True when the snapshot was verified and restored.
        """
        snapshot_path = Path(snapshot_path)
        if not snapshot_path.exists():
            return False
        verification = self.verify_integrity(snapshot_path)
        if not verification.get("ok"):
            return False

        db_path = self._resolve_db(None)
        db_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(str(snapshot_path), str(db_path))

        # -- Drop stale WAL sidecars so the restored image is authoritative. --
        for suffix in ("-wal", "-shm"):
            sidecar = Path(str(db_path) + suffix)
            try:
                sidecar.unlink(missing_ok=True)
            except OSError:
                continue
        return True

    # ------------------------------------------------------------------
    # -- Path resolution -----------------------------------------------
    # ------------------------------------------------------------------

    def _resolve_db(self, db_path: Optional[Path]) -> Path:
        """Resolve the canonical database path when none is provided.

        Args:
            db_path (Optional[Path]): Explicit path or ``None``.

        Returns:
            Path: The resolved database path.
        """
        if db_path is not None:
            return Path(db_path)
        if self._db_path is not None:
            return self._db_path
        try:
            from src.core.database_manager import get_active_profile_db_path

            return Path(get_active_profile_db_path())
        except Exception:
            project_root = Path(__file__).resolve().parents[2]
            return project_root / "data" / "talos_research.db"
