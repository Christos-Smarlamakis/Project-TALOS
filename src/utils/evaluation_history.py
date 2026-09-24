# -*- coding: utf-8 -*-
"""
Module: evaluation_history.py
Project: TALOS v5.11.1
Description:
    Persistent evaluation history recorder and reader. Every paper evaluated by
    the live DRL agent and the 24/7 daemon is appended as a single JSON line to
    data/history/daemon_evaluations.jsonl. The TUI viewer in talos.py reads this
    file back to render a Rich table of the most recent evaluations.

    Key design decisions:
    - Append-only JSONL (JSON Lines) so records survive daemon restarts and can
      be streamed without loading the whole file into memory.
    - All writes are best-effort: a filesystem or serialization error is
      swallowed so history recording never crashes the foraging or daemon loop.
    - Canonical verdict thresholds match the orchestrator: ELITE (>= 8.0),
      ACCEPT (>= 6.0), REJECT (otherwise).

Dependencies:
    - os: filesystem path resolution and directory creation.
    - json: record serialization and deserialization.
    - datetime: ISO 8601 timestamps.
"""
import os
import json
from datetime import datetime


HISTORY_DIR_NAME = "history"
HISTORY_FILE_NAME = "daemon_evaluations.jsonl"


def _history_dir():
    """Resolve the data/history directory at the project root.

    Returns:
        str: Absolute path to the history directory.
    """
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    return os.path.join(root, "data", HISTORY_DIR_NAME)


def _history_path():
    """Return the absolute path to the evaluation history JSONL file.

    Returns:
        str: Absolute path to daemon_evaluations.jsonl.
    """
    return os.path.join(_history_dir(), HISTORY_FILE_NAME)


def verdict_for_score(score):
    """Return a canonical verdict label for an evaluation score.

    Args:
        score (float | None): Overall score (0-10), or None on failure.

    Returns:
        str: One of "ELITE", "ACCEPT", or "REJECT".
    """
    if score is None:
        return "REJECT"
    if score >= 8.0:
        return "ELITE"
    if score >= 6.0:
        return "ACCEPT"
    return "REJECT"


def record_evaluation(title, authors, source, score, verdict, provider=None,
                      timestamp=None):
    """Append one evaluated paper to the persistent JSONL history.

    Args:
        title (str): Full paper title.
        authors (str): Display string of the paper authors.
        source (str): Source agent that produced the paper.
        score (float): Overall evaluation score (0-10).
        verdict (str): Canonical verdict label (ELITE / ACCEPT / REJECT).
        provider (str | None): LLM provider that served the evaluation.
        timestamp (str | None): ISO 8601 timestamp; defaults to now.
    """
    try:
        os.makedirs(_history_dir(), exist_ok=True)
        entry = {
            "timestamp": timestamp or datetime.now().isoformat(timespec="seconds"),
            "title": title or "Unknown Title",
            "authors": authors or "Unknown Authors",
            "source": source or "unknown",
            "score": float(score) if score is not None else 0.0,
            "verdict": verdict or "REJECT",
            "provider": provider or "unknown",
        }
        with open(_history_path(), "a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception:
        pass


def read_evaluation_history(limit=30):
    """Read the most recent N evaluation records, newest first.

    Args:
        limit (int): Maximum number of records to return.

    Returns:
        list of dict: The most recent records in reverse chronological order.
    """
    path = _history_path()
    if not os.path.exists(path):
        return []
    records = []
    try:
        with open(path, "r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    except Exception:
        return []
    return records[-limit:][::-1]
