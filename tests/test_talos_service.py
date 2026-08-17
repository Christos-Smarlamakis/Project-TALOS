# -*- coding: utf-8 -*-
"""
Module: test_talos_service.py
Project: TALOS v5.10.5
Description:
    Hermetic unit tests for the daemon hotfix logic in
    src/ai/drl/talos_service.py. Covers the freshness filter
    (_is_fresh_paper), the 3-hour live-search interval trigger, and the
    live-search subprocess invocation (_run_live_search).

    Key design decisions:
    - _is_fresh_paper is exercised against a temporary SQLite database and a
      monkeypatched get_active_profile_db_path so no real profile database is
      touched.
    - The interval trigger is tested through _run_daemon_iteration with a
      minimal fake environment, a fake agent, and monkeypatched time and
      _run_live_search so no network, disk, or model activity occurs.
    - _run_live_search is tested by recording subprocess.run calls. The
      daemon invokes talos_live_agent.py (the DRL live agent) with
      --episodes and --verbose and streams output (stdout/stderr are not
      captured), which is asserted explicitly.

Dependencies:
    - pytest: monkeypatch and tmp_path fixtures.
    - sqlite3, subprocess, sys, os: Test doubles and call recording.
"""
import os
import sqlite3
import subprocess
import sys
from datetime import datetime, timedelta
from types import SimpleNamespace

import pytest

import src.ai.drl.talos_service as talos


# ---------------------------------------------------------------------------
# Freshness filter
# ---------------------------------------------------------------------------

@pytest.fixture
def freshness_db(tmp_path, monkeypatch):
    """Create a temp SQLite papers table and redirect freshness lookups to it."""
    db_path = str(tmp_path / "freshness.db")
    conn = sqlite3.connect(db_path)
    conn.execute(
        "CREATE TABLE papers (doi TEXT, url TEXT, processed_at TEXT, "
        "last_evaluated_at TEXT)"
    )
    conn.commit()
    conn.close()
    monkeypatch.setattr(
        "src.core.database_manager.get_active_profile_db_path", lambda: db_path
    )
    return db_path


def _insert_paper(db_path, doi, processed_at, last_evaluated_at, url=None):
    conn = sqlite3.connect(db_path)
    conn.execute(
        "INSERT INTO papers (doi, url, processed_at, last_evaluated_at) "
        "VALUES (?, ?, ?, ?)",
        (doi, url, processed_at, last_evaluated_at),
    )
    conn.commit()
    conn.close()


class TestIsFreshPaper:
    """Tests for the freshness filter that mutes old DB papers."""

    def test_paper_added_within_24h_returns_true(self, freshness_db):
        today = datetime.now().strftime("%Y-%m-%d")
        _insert_paper(freshness_db, "10.1/fresh", today,
                      datetime.now().isoformat())
        assert talos._is_fresh_paper({"doi": "10.1/fresh"}) is True

    def test_paper_added_over_24h_returns_false(self, freshness_db):
        old = (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d")
        _insert_paper(freshness_db, "10.1/old", old,
                      (datetime.now() - timedelta(days=2)).isoformat())
        assert talos._is_fresh_paper({"doi": "10.1/old"}) is False

    def test_missing_paper_returns_false(self, freshness_db):
        assert talos._is_fresh_paper({"doi": "10.1/ghost"}) is False

    def test_never_evaluated_paper_returns_true(self, freshness_db):
        _insert_paper(freshness_db, "10.1/uneval", None, None)
        assert talos._is_fresh_paper({"doi": "10.1/uneval"}) is True

    def test_no_identifier_returns_false(self, freshness_db):
        assert talos._is_fresh_paper({"title": "no identifier"}) is False

    def test_db_error_returns_false(self, monkeypatch):
        monkeypatch.setattr(
            "src.core.database_manager.get_active_profile_db_path",
            lambda: "/nonexistent/dir/db.sqlite",
        )
        assert talos._is_fresh_paper({"doi": "10.1/x"}) is False


# ---------------------------------------------------------------------------
# 3-hour live search interval
# ---------------------------------------------------------------------------

@pytest.fixture
def daemon_env(monkeypatch):
    """Provide a minimal fake env/agent/notifier plus no-op side-effect patches."""
    env = SimpleNamespace(
        SLEEP_ACTION=16,
        reset=lambda: (None, {}),
        step=lambda action: (
            None, 0.0, True, False,
            {"source": "arxiv", "score": 0, "paper_data": {}},
        ),
    )
    agent = SimpleNamespace(
        act=lambda obs, eps=0.0: 0,
        reset_hidden_states=lambda: None,
    )
    notifier = SimpleNamespace(
        telegram_send=lambda *a, **k: None,
        discord_send=lambda *a, **k: None,
        email_daily_digest=lambda papers: None,
    )
    monkeypatch.setattr(talos, "_save_daily_report", lambda today=None: None)
    monkeypatch.setattr(talos, "should_send_daily_digest", lambda last: False)
    monkeypatch.setattr(
        talos, "route_daemon_evaluation", lambda source, prompt_length=512: None
    )
    monkeypatch.setattr("time.sleep", lambda s: None)
    return env, agent, notifier


class TestLiveSearchInterval:
    """Tests for the 3-hour live-search trigger and startup behaviour."""

    def test_interval_constant_is_three_hours(self):
        assert talos.LIVE_SEARCH_INTERVAL_SECONDS == 3 * 3600

    def test_startup_search_fires_immediately(self, daemon_env, monkeypatch):
        env, agent, notifier = daemon_env
        calls = []
        monkeypatch.setattr(
            talos, "_run_live_search", lambda: (calls.append(1) or True)
        )
        monkeypatch.setattr("time.time", lambda: 1_800_000_000.0)
        talos._run_daemon_iteration(
            env, agent, notifier, sleep_action=16, verbose=False, epsilon=0.0,
            last_live_search=0, last_digest_date=None,
            papers_discovered=0, high_score_count=0,
        )
        assert len(calls) == 1

    def test_no_search_before_interval_elapses(self, daemon_env, monkeypatch):
        env, agent, notifier = daemon_env
        calls = []
        monkeypatch.setattr(
            talos, "_run_live_search", lambda: (calls.append(1) or True)
        )
        t_now = 1_800_000_000.0
        monkeypatch.setattr("time.time", lambda: t_now)
        talos._run_daemon_iteration(
            env, agent, notifier, sleep_action=16, verbose=False, epsilon=0.0,
            last_live_search=t_now, last_digest_date=None,
            papers_discovered=0, high_score_count=0,
        )
        assert len(calls) == 0

    def test_search_fires_after_three_hours(self, daemon_env, monkeypatch):
        env, agent, notifier = daemon_env
        calls = []
        monkeypatch.setattr(
            talos, "_run_live_search", lambda: (calls.append(1) or True)
        )
        t_now = 1_800_000_000.0
        monkeypatch.setattr("time.time", lambda: t_now)
        talos._run_daemon_iteration(
            env, agent, notifier, sleep_action=16, verbose=False, epsilon=0.0,
            last_live_search=t_now - 3 * 3600, last_digest_date=None,
            papers_discovered=0, high_score_count=0,
        )
        assert len(calls) == 1


# ---------------------------------------------------------------------------
# Live search subprocess invocation
# ---------------------------------------------------------------------------

class TestRunLiveSearch:
    """Tests for the _run_live_search subprocess wrapper."""

    def test_subprocess_run_call_signature(self, monkeypatch):
        recorded = {}

        def fake_run(args, **kwargs):
            recorded["args"] = args
            recorded["kwargs"] = kwargs
            return SimpleNamespace(returncode=0)

        monkeypatch.setattr(subprocess, "run", fake_run)
        assert talos._run_live_search() is True
        assert recorded["args"][0] == sys.executable
        assert recorded["args"][1].endswith("talos_live_agent.py")
        assert os.path.isabs(recorded["args"][1])
        # The live DRL agent runs autonomously for 15 episodes, streaming output.
        assert recorded["args"][2:] == ["--episodes", "15", "--verbose"]
        # Output is streamed to the daemon terminal, not captured.
        assert recorded["kwargs"].get("stdout") is None
        assert recorded["kwargs"].get("stderr") is None
        assert "capture_output" not in recorded["kwargs"]
        assert recorded["kwargs"]["timeout"] == 3600
        # The child runs in strict headless mode (no interactive fallback).
        assert recorded["kwargs"]["env"]["TALOS_HEADLESS"] == "1"

    def test_nonzero_returncode_returns_false(self, monkeypatch):
        monkeypatch.setattr(
            subprocess, "run", lambda *a, **k: SimpleNamespace(returncode=1)
        )
        assert talos._run_live_search() is False

    def test_subprocess_exception_returns_false(self, monkeypatch):
        def boom(*a, **k):
            raise subprocess.CalledProcessError(1, "cmd")

        monkeypatch.setattr(subprocess, "run", boom)
        assert talos._run_live_search() is False