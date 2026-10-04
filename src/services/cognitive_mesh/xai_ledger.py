# -*- coding: utf-8 -*-
"""
Module: xai_ledger.py
Project: TALOS v5.25.0
Description:
    Explainable AI (XAI) decision ledger for the Cognitive Mesh microservice.
    Every swarm-sizing and model-selection decision is persisted as an
    append-only JSONL audit record under ``data/cache/xai_decision_log.jsonl``
    so that high-consequence operational outcomes remain auditable by external
    consumers (Robotic Operations Stations, MEMEX, Project ATHENA field
    stations). The ledger generates structured human-readable explanations of
    why models were chosen, the cost/latency trade-offs evaluated, and any
    fallback cascade that occurred before the final selection.

    Key design decisions:
    - Append-only and idempotent: every call writes exactly one new line and
      never mutates prior records, preserving a tamper-evident audit trail.
    - Thread-safe: a re-entrant lock serializes writes so the router and the
      relay orchestrator can log concurrently without interleaved lines.
    - Zero external coupling: imports only the Python standard library and the
      in-package Pydantic DTO, so it remains extraction-ready.

Dependencies:
    - json, os, threading, uuid, datetime: JSONL I/O, locking, identifiers,
      and ISO 8601 timestamps.
    - typing: type annotations.
    - src.services.cognitive_mesh.dto: XAiDecisionRecord Pydantic DTO.
"""

import json
import os
import threading
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union

# -- Resolve project root (same pattern as all src/*.py modules) --------------
_P = os.path.abspath(os.path.dirname(__file__))
while _P and not os.path.exists(os.path.join(_P, "talos.py")):
    _P = os.path.dirname(_P)

_DEFAULT_LOG_PATH = os.path.join(
    _P or os.path.abspath(os.path.dirname(__file__)),
    "data",
    "cache",
    "xai_decision_log.jsonl",
)


class XAiDecisionLedger:
    """Append-only Explainable AI (XAI) decision audit ledger.

    Writes one JSON object per line to a JSONL file so that every routing and
    swarm-sizing decision can be reconstructed by an external auditor. The
    ledger is deliberately hermetic: it performs no network I/O, opens no
    database, and imports no PRISMA or CLI module.

    Attributes:
        log_path (str): Absolute path to the append-only JSONL audit file.
    """

    def __init__(self, log_path: Optional[str] = None) -> None:
        self.log_path = log_path or _DEFAULT_LOG_PATH
        self._lock = threading.RLock()

    # ------------------------------------------------------------------
    # -- Public API -----------------------------------------------------
    # ------------------------------------------------------------------

    def append(self, record: Union[Dict[str, Any], "object"]) -> Dict[str, Any]:
        """Append one structured XAI audit record to the JSONL ledger.

        Accepts either a ``XAiDecisionRecord`` Pydantic model or a plain dict.
        A timestamp and UUID4 decision id are injected when absent so every
        record is independently traceable.

        Args:
            record (Union[dict, XAiDecisionRecord]): The decision to persist.

        Returns:
            dict: The canonicalized record that was written (with any injected
                ``timestamp`` and ``decision_id`` fields).
        """
        data = self._coerce(record)
        if not data.get("timestamp"):
            data["timestamp"] = _iso_now()
        if not data.get("decision_id"):
            data["decision_id"] = str(uuid.uuid4())

        with self._lock:
            _ensure_dir(self.log_path)
            with open(self.log_path, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(data, ensure_ascii=False) + "\n")
        return data

    def latest(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Return the most recent audit records in chronological order.

        Args:
            limit (int): Maximum number of records to return.

        Returns:
            list[dict]: The most recent records (oldest first among the tail).
        """
        limit = max(0, int(limit))
        if limit == 0 or not os.path.exists(self.log_path):
            return []
        with self._lock:
            with open(self.log_path, "r", encoding="utf-8") as fh:
                lines = [ln for ln in fh if ln.strip()]
        records = []
        for ln in lines[-limit:]:
            try:
                records.append(json.loads(ln))
            except ValueError:
                continue
        return records

    def explain(self, record: Union[Dict[str, Any], "object"]) -> str:
        """Generate a structured human-readable explanation of a decision.

        Args:
            record (Union[dict, XAiDecisionRecord]): The decision to explain.

        Returns:
            str: A multi-line plain-language rationale covering the task, the
                complexity score, the selected swarm cardinality, the chosen
                model chain, and the fallback cascade.
        """
        data = self._coerce(record)
        task = data.get("task_type", "general")
        complexity = data.get("complexity_score", 0.0)
        swarm = data.get("swarm_size", 1)
        models = data.get("candidate_models", [])
        rationale = data.get("pareto_rationale", "")
        cascade = data.get("fallback_cascade", [])
        safety = data.get("safety_flags", {})

        lines = [
            "XAI Decision {}".format(data.get("decision_id", "")),
            "  Task Type      : {}".format(task),
            "  Complexity C   : {:.3f}".format(float(complexity)),
            "  Swarm Size K   : {}".format(swarm),
            "  Model Chain    : {}".format(", ".join(models) if models else "(decision-only)"),
        ]
        if rationale:
            lines.append("  Rationale      : {}".format(rationale))
        if cascade:
            lines.append("  Fallback Path  : {}".format(" -> ".join(cascade)))
        if safety:
            flags = ", ".join("{}={}".format(k, v) for k, v in safety.items())
            lines.append("  Safety Flags   : {}".format(flags))
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # -- Internal helpers ------------------------------------------------
    # ------------------------------------------------------------------

    @staticmethod
    def _coerce(record: Union[Dict[str, Any], "object"]) -> Dict[str, Any]:
        """Normalize a record (dict or Pydantic model) into a plain dict.

        Args:
            record (Union[dict, object]): The input decision record.

        Returns:
            dict: A plain JSON-serializable dictionary.
        """
        if isinstance(record, dict):
            return dict(record)
        if hasattr(record, "model_dump"):
            return record.model_dump()
        if hasattr(record, "dict"):
            return record.dict()
        raise TypeError("record must be a dict or a Pydantic model")


def _iso_now() -> str:
    """Return the current UTC wall-clock time as an ISO 8601 string.

    Returns:
        str: ISO 8601 timestamp with timezone offset.
    """
    return datetime.now(timezone.utc).astimezone().isoformat()


def _ensure_dir(path: str) -> None:
    """Create the parent directory of a file path when it does not exist.

    Args:
        path (str): The target file path whose parent directory is ensured.
    """
    parent = os.path.dirname(os.path.abspath(path))
    if parent and not os.path.isdir(parent):
        os.makedirs(parent, exist_ok=True)
