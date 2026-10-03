# -*- coding: utf-8 -*-
"""
Module: test_scigov_resilience.py
Project: TALOS v5.19.0
Description:
    Hermetic unit tests for the fault-tolerant DNS/connection isolation and
    default-disabled behavior of the Science.gov adapter
    (src/ingestion/sources/scigov_source.py). Verifies that DNS resolution
    failures return an empty list instead of raising, and that the source is
    disabled by default unless explicitly enabled.

Dependencies:
    - pytest: Test framework.
    - requests: Exception types used to simulate connection failures.
"""
import pytest
import requests

from src.ingestion.sources.scigov_source import ScienceGovSource


class TestScigovDisabledByDefault:
    """Tests for the default-disabled lifecycle."""

    def test_disabled_by_default(self):
        source = ScienceGovSource({})
        assert source.enabled is False

    def test_disabled_source_returns_empty(self):
        source = ScienceGovSource({})
        assert source.fetch_new_papers() == []

    def test_explicitly_enabled_via_config(self):
        source = ScienceGovSource({"scigov_enabled": True})
        assert source.enabled is True


class TestScigovDnsResilience:
    """Tests for graceful DNS failure isolation."""

    def _make_enabled_source(self):
        source = ScienceGovSource.__new__(ScienceGovSource)
        source.enabled = True
        source.query = "unmanned systems"
        source.max_results = 100
        source.base_url = "https://api.science.gov/search/v2/records"
        return source

    def test_dns_failure_returns_empty(self):
        source = self._make_enabled_source()

        class _FailingSession:
            def get(self, *args, **kwargs):
                raise requests.exceptions.ConnectionError(
                    "[Errno -2] Name or service not known")

        source.session = _FailingSession()
        result = source.fetch_new_papers()

        assert result == []

    def test_request_exception_returns_empty(self):
        source = self._make_enabled_source()

        class _FailingSession:
            def get(self, *args, **kwargs):
                raise requests.exceptions.RequestException("generic failure")

        source.session = _FailingSession()
        result = source.fetch_new_papers()

        assert result == []

    def test_dns_failure_classifier(self):
        assert ScienceGovSource._is_dns_failure(
            Exception("getaddrinfo failed")) is True
        assert ScienceGovSource._is_dns_failure(
            Exception("[Errno -2] Name or service not known")) is True
        assert ScienceGovSource._is_dns_failure(
            Exception("Connection refused")) is False
