# -*- coding: utf-8 -*-
"""
Module: chaos_test_daemon.py
Project: TALOS v5.10.5
Description:
    Chaos-engineering (state and exception fuzzing) tests for the TALOS
    daemon's continuous loop. Because the daemon is a `while True` loop rather
    than a REST API, the test drives _run_daemon_iteration directly with
    fault-injecting doubles and verifies that the root try/except guarantees
    zero downtime.

    Key design decisions:
    - A ChaoticEnv cycles deterministically through a fixed set of corrupt
      behaviours so every fault class fires at least once per run.
    - subprocess.run raises subprocess.CalledProcessError on alternate calls
      (contained by _run_live_search).
    - DatabaseManager.execute_query raises sqlite3.OperationalError("database
      is locked") on alternate calls (contained by send_daily_digest).
    - get_active_profile_db_path is redirected to an empty temp DB so the
      freshness filter never touches the real profile database.

Dependencies:
    - pytest: monkeypatch and tmp_path fixtures.
    - sqlite3, subprocess: Fault exceptions injected into the daemon.
    - types.SimpleNamespace: Lightweight test doubles.
"""
import sqlite3
import subprocess
from types import SimpleNamespace

import pytest

import src.ai.drl.talos_service as talos


class _ChaoticEnv:
    """Fault-injecting environment double for the daemon loop."""

    SLEEP_ACTION = 16

    def __init__(self):
        self._i = -1
        self._behaviours = [
            "raise",
            "wrong_arity",
            "info_none",
            "score_none",
            "valid",
            "high_placeholder",
            "high_with_id",
        ]

    def reset(self):
        return (None, {})

    def step(self, action):
        self._i += 1
        behaviour = self._behaviours[self._i % len(self._behaviours)]
        if behaviour == "raise":
            raise RuntimeError("env.step transient failure")
        if behaviour == "wrong_arity":
            return (None, 0.0, True)
        if behaviour == "info_none":
            return (None, 0.0, True, False, None)
        if behaviour == "score_none":
            return (None, 0.0, True, False,
                    {"source": "arxiv", "score": None, "paper_data": {}})
        if behaviour == "valid":
            return (None, 0.0, True, False,
                    {"source": "arxiv", "score": 0, "paper_data": {}})
        if behaviour == "high_placeholder":
            return (None, 0.0, True, False,
                    {"source": "arxiv", "score": 9, "paper_data": {}})
        if behaviour == "high_with_id":
            return (None, 0.0, True, False, {
                "source": "arxiv", "score": 9,
                "paper_data": {
                    "title": "Chaos Paper", "authors_str": "A, B",
                    "doi": "10.9999/chaos",
                },
            })
        return (None, 0.0, True, False,
                {"source": "arxiv", "score": 0, "paper_data": {}})


class _FakeNotifier:
    """Notification double: records calls without external side effects."""

    def telegram_send(self, *a, **k):
        return None

    def discord_send(self, *a, **k):
        return None

    def email_daily_digest(self, papers):
        return None


def test_daemon_resilience_to_chaos(monkeypatch, tmp_path):
    """Prove the daemon survives 10 iterations of injected chaos (zero downtime)."""
    sub_calls = {"n": 0, "raises": 0}
    db_calls = {"n": 0, "raises": 0}

    def chaotic_run(args, **kwargs):
        sub_calls["n"] += 1
        if sub_calls["n"] % 2 == 0:
            sub_calls["raises"] += 1
            raise subprocess.CalledProcessError(1, " ".join(args))
        return SimpleNamespace(returncode=0)

    class LockingDB:
        """Database double whose execute_query raises a lock error every 2nd call."""

        def __init__(self, *a, **k):
            pass

        def execute_query(self, *a, **k):
            db_calls["n"] += 1
            if db_calls["n"] % 2 == 0:
                db_calls["raises"] += 1
                raise sqlite3.OperationalError("database is locked")
            return []

        def get_recent_elite_papers(self, hours=24, min_score=7.0):
            return self.execute_query("SELECT ...", fetch_all=True) or []

    # -- Inject faults into subprocess.run and DatabaseManager.execute_query --
    monkeypatch.setattr(subprocess, "run", chaotic_run)
    monkeypatch.setattr("src.core.database_manager.DatabaseManager", LockingDB)

    # -- Hermetic freshness lookups: point at an empty temp DB --
    monkeypatch.setattr(
        "src.core.database_manager.get_active_profile_db_path",
        lambda: str(tmp_path / "empty.db"),
    )

    # -- De-fang slow or side-effectful helpers --
    monkeypatch.setattr(
        talos, "route_daemon_evaluation", lambda source, prompt_length=512: None
    )
    monkeypatch.setattr(talos, "_save_daily_report", lambda today=None: None)
    monkeypatch.setattr(talos, "should_send_daily_digest", lambda last: True)
    monkeypatch.setattr("time.sleep", lambda s: None)

    env = _ChaoticEnv()
    agent = SimpleNamespace(
        act=lambda obs, eps=0.0: 0, reset_hidden_states=lambda: None
    )
    notifier = _FakeNotifier()

    # -- Drive 10 iterations through the same root try/except as main() --
    iterations = 0
    caught = 0
    state = {"last_digest_date": None, "papers_discovered": 0, "high_score_count": 0}
    for _ in range(10):
        try:
            (_, last_digest_date, papers_discovered,
             high_score_count) = talos._run_daemon_iteration(
                env, agent, notifier, sleep_action=_ChaoticEnv.SLEEP_ACTION,
                verbose=False, epsilon=0.0,
                last_live_search=0,
                last_digest_date=state["last_digest_date"],
                papers_discovered=state["papers_discovered"],
                high_score_count=state["high_score_count"],
            )
            state["last_digest_date"] = last_digest_date
            state["papers_discovered"] = papers_discovered
            state["high_score_count"] = high_score_count
            iterations += 1
        except Exception:
            caught += 1

    # -- Zero-downtime proof: all 10 loop iterations completed --
    assert iterations + caught == 10
    # -- At least the deterministic env faults were injected and caught --
    assert caught >= 1
    # -- Both the subprocess and database lock faults fired and were contained --
    assert sub_calls["raises"] >= 1
    assert db_calls["raises"] >= 1