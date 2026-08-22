# -*- coding: utf-8 -*-
"""
Module: optica_client.py
Project: TALOS v5.10.7
Description:
    REST client for Project OPTICA, the sister microservice that offloads heavy
    visualization workloads (cnsplots/PyVis graphics) to port 8002. TALOS acts
    as an API client: it sends the active profile database path plus a plot
    specification to OPTICA and receives back the generated artifact path.

    Key design decisions:
    - Uses the requests library with a short connection timeout so the TUI
      never hangs when OPTICA is offline.
    - Resolves the active profile database path dynamically via
      src.core.database_manager.get_active_profile_db_path() so every plot is
      rendered from the exact database the user is currently working on.
    - Graceful degradation: every failure mode (connection refused, timeout,
      HTTP error, unexpected exception) returns a structured error dict instead
      of raising, keeping the TALOS TUI resilient.

Dependencies:
    - os: Absolute path normalization of the resolved database path.
    - requests: HTTP POST to the OPTICA plot generation endpoint.
    - config.settings: OPTICA_API_BASE endpoint configuration.
    - src.core.database_manager: get_active_profile_db_path() path resolver.
"""

import os

import requests

from config.settings import OPTICA_API_BASE


class OpticaClient:
    """
    Lightweight REST client for the OPTICA visualization microservice.

    Attributes:
        base_url (str): Base URL of the OPTICA API (default port 8002).
        timeout (float): HTTP request timeout in seconds.
    """

    # -- Plot types supported by OPTICA (kept in sync with the TUI prompt) --
    PLOT_TYPES = ("opex_dashboard", "semantic_topology")

    # -- Journal templates supported by OPTICA --
    JOURNAL_TEMPLATES = ("nature", "science", "cell")

    def __init__(self, base_url=None, timeout=10.0):
        """Initialize the client with an optional base URL override.

        Args:
            base_url (str, optional): Override for the OPTICA API base URL.
                Defaults to config.settings.OPTICA_API_BASE.
            timeout (float, optional): HTTP request timeout in seconds.
        """
        self.base_url = (base_url or OPTICA_API_BASE).rstrip("/")
        self.timeout = timeout

    @property
    def plot_generate_url(self):
        """Return the full URL of the plot generation endpoint."""
        return f"{self.base_url}/plot/generate"

    def request_plot(self, plot_type, journal_template):
        """Request a plot from OPTICA and return a structured result dict.

        Args:
            plot_type (str): One of opex_dashboard or semantic_topology.
            journal_template (str): One of nature, science, or cell.

        Returns:
            dict: On success, the parsed JSON response from OPTICA augmented
                with an ok=True flag. On any failure, a graceful dict of the
                form {"ok": False, "error": str, "output_path": None}.
        """
        # -- Resolve the active profile database path dynamically --
        try:
            from src.core.database_manager import get_active_profile_db_path
            db_path = os.path.abspath(get_active_profile_db_path())
        except Exception as exc:  # pragma: no cover - defensive
            return self._error("Could not resolve the active database path", exc)

        # -- Build the OPTICA request payload --
        payload = {
            "data_source": db_path,
            "plot_type": plot_type,
            "journal_template": journal_template,
            "override_params": {},
        }

        # -- POST to OPTICA with graceful connection handling --
        try:
            response = requests.post(
                self.plot_generate_url,
                json=payload,
                timeout=self.timeout,
            )
            response.raise_for_status()
            data = response.json()
            if isinstance(data, dict):
                data["ok"] = True
            else:
                data = {"ok": True, "result": data}
            return data
        except requests.exceptions.ConnectionError as exc:
            return self._error(
                "OPTICA is unreachable (is it running on port 8002?)", exc
            )
        except requests.exceptions.Timeout as exc:
            return self._error(
                f"OPTICA request timed out after {self.timeout}s", exc
            )
        except requests.exceptions.HTTPError as exc:
            return self._error(f"OPTICA returned an HTTP error: {exc}", exc)
        except requests.exceptions.RequestException as exc:
            return self._error("OPTICA request failed", exc)
        except Exception as exc:  # pragma: no cover - defensive
            return self._error("Unexpected error during OPTICA request", exc)

    @staticmethod
    def _error(message, exc=None):
        """Build a graceful error dictionary for the TUI to render.

        Args:
            message (str): Human-readable error message.
            exc (Exception, optional): Underlying exception, if any.

        Returns:
            dict: Structured error result with ok=False.
        """
        detail = str(exc) if exc is not None else ""
        return {
            "ok": False,
            "error": message if not detail else f"{message}: {detail}",
            "output_path": None,
        }


# -- Module-level convenience instance (mirrors synapse_emitter) --
optica_client = OpticaClient()
