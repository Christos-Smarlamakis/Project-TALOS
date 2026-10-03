# -*- coding: utf-8 -*-
"""
Module: test_resilient_gateway.py
Project: TALOS v5.19.0
Description:
    Hermetic unit tests for the overarching ResilientIngestionGateway and the
    daemon autostart profile selector. Verifies fast-fail classification on
    raised and printed 403 / "Developer Inactive" / "Quota Exceeded" errors,
    OpenAlex publisher mirroring for IEEE / Elsevier / Springer, canonical
    schema normalization with source-key preservation, clean empty returns for
    unmapped sources, and the ``--profile`` embedding in the generated boot
    batch plus the full profile list rendered by the selector.

    Key design decisions:
    - All tests are hermetic -- no live OpenAlex or questionary interaction.
    - ``_mirror_via_openalex`` is mocked so no network I/O occurs.

Dependencies:
    - pytest: Test framework.
    - unittest.mock: Patching source agents, HTTP sessions, and prompts.
"""
import pytest
from unittest import mock

from src.ingestion.resilient_gateway import (
    ResilientIngestionGateway,
    PUBLISHER_FALLBACK_MAP,
)


class _FakeSource:
    """Minimal source adapter that raises or prints a configurable failure."""

    def __init__(self, behavior="raise_403"):
        self.behavior = behavior

    def fetch_new_papers(self):
        if self.behavior == "raise_403":
            raise Exception("403 Client Error: Forbidden for url")
        if self.behavior == "print_developer_inactive":
            print("WARNING [IEEE]: Developer Inactive")
            return []
        if self.behavior == "print_quota":
            print("ERROR [Springer]: Quota Exceeded")
            return []
        if self.behavior == "ok":
            return [{
                "doi": "10.1/test", "url": "https://doi.org/10.1/test",
                "title": "Primary", "authors_str": "A",
                "publication_year": 2026, "abstract": "abs", "source": "ieee",
            }]
        return []

class TestResilientGateway:
    """Tests for fast-fail detection and OpenAlex publisher mirroring."""

    def test_fast_fail_raises_then_mirrors(self):
        gateway = ResilientIngestionGateway()
        with mock.patch.object(gateway, "_mirror_via_openalex", return_value=[
            {"doi": "10.2/m", "url": "https://doi.org/10.2/m", "title": "Mirrored",
             "authors_str": "B", "publication_year": 2026, "abstract": "abs",
             "source": "ieee"}]) as mirror:
            papers = gateway.harvest_source(
                _FakeSource("raise_403"), query="drone swarm", source_key="ieee")
        assert mirror.called
        assert gateway.last_recovered is True
        assert gateway.last_status == "RECOVERED"
        assert papers and papers[0]["source"] == "ieee"

    def test_stdout_developer_inactive_detected(self):
        gateway = ResilientIngestionGateway()
        with mock.patch.object(gateway, "_mirror_via_openalex", return_value=[
            {"doi": "10.3/m", "url": "https://doi.org/10.3/m", "title": "M",
             "authors_str": "C", "publication_year": 2026, "abstract": "a",
             "source": "ieee"}]):
            papers = gateway.harvest_source(
                _FakeSource("print_developer_inactive"), query="robotics",
                source_key="ieee")
        assert gateway.last_recovered is True
        assert papers[0]["source"] == "ieee"

    def test_quota_exceeded_detected_via_stdout(self):
        gateway = ResilientIngestionGateway()
        with mock.patch.object(gateway, "_mirror_via_openalex", return_value=[]):
            papers = gateway.harvest_source(
                _FakeSource("print_quota"), query="robotics", source_key="springer")
        assert papers == []
        assert gateway.last_status == "FAILED"
        assert gateway.last_error is not None

    def test_unmapped_source_fails_cleanly(self):
        gateway = ResilientIngestionGateway()
        papers = gateway.harvest_source(
            _FakeSource("raise_403"), query="robotics", source_key="arxiv")
        assert papers == []
        assert gateway.last_error is not None
        assert gateway.last_recovered is False

    def test_primary_success_no_fallback(self):
        gateway = ResilientIngestionGateway()
        papers = gateway.harvest_source(
            _FakeSource("ok"), query="robotics", source_key="ieee")
        assert len(papers) == 1
        assert gateway.last_recovered is False
        assert gateway.last_error is None

    def test_publisher_fallback_map_keys(self):
        assert set(PUBLISHER_FALLBACK_MAP) == {"ieee", "elsevier", "springer"}

    def test_normalize_openalex_work_preserves_source_key(self):
        work = {
            "doi": "https://doi.org/10.1000/xyz",
            "title": "A Study",
            "publication_year": 2025,
            "authorships": [{"author": {"display_name": "Alice"}},
                            {"author": {"display_name": "Bob"}}],
            "abstract_inverted_index": {"hello": [0], "world": [1]},
            "primary_location": {"landing_page_url": "https://x"},
        }
        paper = ResilientIngestionGateway._normalize_openalex_work(work, "ieee")
        assert paper["source"] == "ieee"
        assert paper["doi"] == "10.1000/xyz"
        assert paper["authors_str"] == "Alice, Bob"
        assert paper["abstract"] == "hello world"

    def test_reconstruct_abstract_empty(self):
        assert ResilientIngestionGateway._reconstruct_abstract(
            None) == "No abstract available."

class TestDaemonAutostartProfileSelector:
    """Tests for the autostart profile selector and boot batch generation."""

    def test_generate_boot_batch_embeds_profile(self, tmp_path):
        from src.utils import daemon_autostart
        with mock.patch.object(daemon_autostart, "_project_root",
                               return_value=str(tmp_path)):
            bat_path = daemon_autostart.generate_boot_batch(
                profile_name="uav_test")
        content = open(bat_path, "r", encoding="utf-8").read()
        assert "--profile uav_test" in content
        assert "talos_service.py" in content

    def test_select_daemon_profile_renders_full_profile_list(self):
        from src.utils import daemon_autostart
        captured = {}
        with mock.patch("src.core.profile_manager.ProfileManager") as pm:
            pm.return_value.list_profiles.return_value = ["alpha", "beta", "gamma"]
            pm.return_value.get_active_profile_name.return_value = "beta"

            def _fake_select(message, choices, default, style):
                captured["choices"] = choices
                captured["default"] = default
                return mock.MagicMock(ask=lambda: "gamma")

            with mock.patch("questionary.select", side_effect=_fake_select):
                result = daemon_autostart.select_daemon_profile()
        assert result == "gamma"
        assert captured["choices"] == ["alpha", "beta", "gamma"]
        assert captured["default"] == "beta"

    def test_select_daemon_profile_cancel_returns_none(self):
        from src.utils import daemon_autostart
        with mock.patch("src.core.profile_manager.ProfileManager") as pm:
            pm.return_value.list_profiles.return_value = ["a", "b"]
            pm.return_value.get_active_profile_name.return_value = "a"
            with mock.patch("questionary.select") as select:
                select.return_value.ask.side_effect = KeyboardInterrupt()
                result = daemon_autostart.select_daemon_profile()
        assert result is None