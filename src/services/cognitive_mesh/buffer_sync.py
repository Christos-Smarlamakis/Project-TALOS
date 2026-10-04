# -*- coding: utf-8 -*-
"""
Module: buffer_sync.py
Project: TALOS v5.24.0
Description:
    Distributed store-and-forward JSONL buffer sync engine for the Cognitive
    Mesh microservice. Remote headless workers (HERMES Ubuntu Server) emit
    append-only ``hermes_buffer.jsonl`` files containing one JSON model
    discovery per line. This engine ingests those files, deduplicates by model
    identifier, merges them into the canonical benchmark cache at
    ``data/cache/llm_benchmarks.json``, and can serialize local discoveries
    back out to a JSONL buffer for offline export. The subsystem is
    featherweight and air-gapped: it operates purely on JSON/JSONL, never opens
    a SQLite connection, a PRISMA pipeline, or a CLI script, and introduces no
    external queue dependency (Constitution II and the strict modularity
    mandate of src/services/cognitive_mesh/).

    Key design decisions:
    - Ingest is append-only and idempotent: duplicate model identifiers are
      resolved to their most recent record, never duplicating cache entries.
    - Merging delegates to the in-package ``ModelBenchmarkClient`` cache
      lifecycle, preserving the canonical schema and atomic UTF-8 writes.
    - The engine tolerates malformed lines silently (skipping them) so a
      partially written remote buffer never crashes the service.

Dependencies:
    - json, os, pathlib: JSONL parsing and filesystem resolution.
    - typing: type annotations.
    - src.services.cognitive_mesh.benchmarks: canonical cache merge/persist.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional


class BufferSyncEngine:
    """Store-and-forward JSONL sync between remote workers and the cache."""

    def __init__(self, cache_path: Optional[str] = None) -> None:
        self._project_root = self._resolve_root()
        self.cache_path = cache_path or os.path.join(
            self._project_root, "data", "cache", "llm_benchmarks.json"
        )

    @staticmethod
    def _resolve_root() -> str:
        p = os.path.abspath(os.path.dirname(__file__))
        while p and not os.path.exists(os.path.join(p, "talos.py")):
            p = os.path.dirname(p)
        return p or os.path.abspath(os.path.dirname(__file__))

    # ------------------------------------------------------------------
    # -- Public API ----------------------------------------------------
    # ------------------------------------------------------------------

    def ingest_jsonl_buffer(self, file_path: Path) -> Dict[str, Any]:
        """Ingest an append-only JSONL buffer and merge into the cache.

        Args:
            file_path (Path): Path to the remote ``hermes_buffer.jsonl``.

        Returns:
            dict: Summary with ``parsed``, ``deduplicated``, ``merged``,
                ``skipped``, and the final ``record_count``.
        """
        records = self._parse_jsonl(file_path)
        parsed = len(records)
        deduplicated = self._deduplicate(records)
        skipped = parsed - len(deduplicated)

        merged = 0
        if deduplicated:
            merged = self._merge_into_cache(deduplicated)

        return {
            "parsed": parsed,
            "deduplicated": len(deduplicated),
            "skipped": skipped,
            "merged": merged,
            "record_count": self._cache_record_count(),
        }

    def export_worker_buffer(
        self, models: List[Dict[str, Any]], output_path: Path
    ) -> Path:
        """Serialize model discoveries to an append-only JSONL buffer.

        Args:
            models (list[dict]): Model records to export.
            output_path (Path): Destination JSONL file path.

        Returns:
            Path: The resolved output path written.
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as fh:
            for model in models:
                if isinstance(model, dict):
                    fh.write(json.dumps(model, ensure_ascii=False) + "\n")
        return output_path

    # ------------------------------------------------------------------
    # -- Helpers -------------------------------------------------------
    # ------------------------------------------------------------------

    def _parse_jsonl(self, file_path: Path) -> List[Dict[str, Any]]:
        """Parse a JSONL (or JSON array) file into a list of record dicts."""
        file_path = Path(file_path)
        if not file_path.exists():
            return []
        records: List[Dict[str, Any]] = []
        try:
            with open(file_path, "r", encoding="utf-8") as fh:
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        obj = json.loads(line)
                    except ValueError:
                        continue
                    if isinstance(obj, dict):
                        records.append(obj)
                    elif isinstance(obj, list):
                        records.extend(r for r in obj if isinstance(r, dict))
        except OSError:
            return []
        return records

    @staticmethod
    def _deduplicate(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Collapse records to the most recent entry per model identifier."""
        merged: Dict[str, Dict[str, Any]] = {}
        for record in records:
            key = record.get("model") or record.get("id") or record.get("name")
            if key:
                merged[str(key)] = record
        return list(merged.values())

    def _merge_into_cache(self, records: List[Dict[str, Any]]) -> int:
        """Merge records into the canonical benchmark cache and persist."""
        from src.services.cognitive_mesh.benchmarks import ModelBenchmarkClient

        client = ModelBenchmarkClient(cache_path=self.cache_path)
        return client.ingest_remote_records(records)

    def _cache_record_count(self) -> int:
        """Return the number of records currently held in the cache file."""
        try:
            with open(self.cache_path, "r", encoding="utf-8") as fh:
                payload = json.load(fh)
            records = payload.get("records") or payload.get("models") or []
            return len(records) if isinstance(records, list) else 0
        except (OSError, ValueError):
            return 0
