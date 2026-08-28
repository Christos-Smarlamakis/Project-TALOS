# -*- coding: utf-8 -*-
"""
Module: http_client.py
Project: TALOS v5.10.16
Description:
    Shared HTTP session factory for the TALOS ingestion and local-inference
    layers. Builds a persistent requests.Session with urllib3 connection pooling
    and HTTP Keep-Alive so multi-source academic scraping reuses TCP/TLS
    connections instead of opening a new socket per request. Zero new external
    dependencies: requests and urllib3 are already project dependencies.

Dependencies:
    - requests: HTTP client (already a project dependency).
    - requests.adapters.HTTPAdapter: Transport adapter for connection pooling.
"""

import requests
from requests.adapters import HTTPAdapter


DEFAULT_USER_AGENT = "TALOS/5.10.16 (autonomous academic literature agent)"


def build_session(pool_connections=10, pool_maxsize=20, timeout=20.0,
                  user_agent=None):
    """Build a persistent requests.Session with connection pooling.

    Args:
        pool_connections (int): Number of host connection pools to cache.
        pool_maxsize (int): Maximum pooled connections per host.
        timeout (float): Default request timeout in seconds.
        user_agent (str | None): User-Agent header override.

    Returns:
        requests.Session: Configured, keep-alive session with polite headers.
    """
    session = requests.Session()
    adapter = HTTPAdapter(
        pool_connections=pool_connections,
        pool_maxsize=pool_maxsize,
    )
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    session.headers.update({
        "User-Agent": user_agent or DEFAULT_USER_AGENT,
        "Accept": "application/json, application/xml, text/xml, */*",
    })
    session.timeout = timeout
    return session
