# -*- coding: utf-8 -*-
"""
Module: synapse_client.py
Project: TALOS v5.9.15
Description:
    EventEmitter class for the SYNAPSE Event-Driven Protocol. This module
    provides a thread-safe, non-blocking client that pushes JSON-structured
    events from TALOS to the SYNAPSE event bus at http://localhost:8000/api/v1/events.

    Event types emitted: paper_discovered, paper_evaluated, search_completed,
    gwo_optimized, agent_step, agent_episode_end.

    Each event carries mandatory fields: event_id (UUID4), timestamp (ISO 8601),
    event_type (string enum), source ("talos"), payload (dict).

    Key design decisions:
    - Uses requests.Session with a connection pool for efficiency.
    - Non-blocking emission via threading.Thread with optional callback.
    - Graceful degradation: failed emissions log warnings but never raise.
    - Configurable timeout and retry logic for resilience.
    - Designed for future ALEXANDRIA ecosystem integration where TALOS is one
      of many microservices in a distributed research intelligence mesh.

Dependencies:
    - uuid: Generate unique event identifiers (UUID4).
    - json: Serialize event payloads.
    - logging: Structured logging of emission success/failure.
    - threading: Non-blocking event dispatch.
    - typing: Type hints for maintainability.
    - datetime: ISO 8601 timestamp generation.
    - requests: HTTP POST to the SYNAPSE bus (optional, with fallback).
"""

import uuid
import json
import logging
import threading
from datetime import datetime, timezone
from typing import Optional, Callable, Dict, Any

logger = logging.getLogger("talos.synapse")

# -- Optional requests import with graceful fallback --
try:
    import requests
    _REQUESTS_AVAILABLE = True
except ImportError:
    _REQUESTS_AVAILABLE = False
    logger.warning(
        "requests library not available. EventEmitter will log events "
        "locally instead of pushing to the SYNAPSE bus."
    )


class EventEmitter:
    """
    Thread-safe, non-blocking emitter for the SYNAPSE Event-Driven Protocol.

    Pushes JSON events to the SYNAPSE bus at a configurable endpoint.
    If the requests library is unavailable or the bus is unreachable,
    events are logged locally without raising exceptions.

    Attributes:
        bus_url (str): Full URL of the SYNAPSE events endpoint.
        source (str): Identifier for this microservice (default "talos").
        timeout (float): HTTP request timeout in seconds.
        max_retries (int): Maximum retry attempts on transient failures.
        _session (requests.Session or None): Reusable HTTP session.
    """

    # -- Valid event types as defined by the SYNAPSE protocol --
    VALID_EVENT_TYPES = frozenset({
        "paper_discovered",
        "paper_evaluated",
        "search_completed",
        "gwo_optimized",
        "agent_step",
        "agent_episode_end",
    })

    def __init__(
        self,
        bus_url: str = "http://localhost:8000/api/v1/events",
        source: str = "talos",
        timeout: float = 5.0,
        max_retries: int = 1,
    ):
        """
        Initialize the EventEmitter with connection parameters.

        Args:
            bus_url: Full URL of the SYNAPSE events ingestion endpoint.
            source: Identifier for this microservice in the ecosystem.
            timeout: HTTP request timeout in seconds.
            max_retries: Maximum retry attempts for transient HTTP errors.
                         Default is 1 (one initial attempt, no retries on
                         connection-refused errors) to keep the TUI clean.
        """
        self.bus_url = bus_url
        self.source = source
        self.timeout = timeout
        # -- Cap retries at 1 for connection-refused scenarios (v5.9.5) --
        self.max_retries = min(max_retries, 1)

        # -- Initialize HTTP session if requests is available --
        self._session = None
        if _REQUESTS_AVAILABLE:
            self._session = requests.Session()
            self._session.headers.update({
                "Content-Type": "application/json",
                "User-Agent": f"TALOS-SynapseClient/5.7.0",
            })

        logger.info(
            "EventEmitter initialized: bus=%s, source=%s, requests_available=%s",
            self.bus_url,
            self.source,
            _REQUESTS_AVAILABLE,
        )

    # ------------------------------------------------------------------
    # -- Public API --
    # ------------------------------------------------------------------

    def emit(
        self,
        event_type: str,
        payload: Dict[str, Any],
        callback: Optional[Callable[[bool, Optional[str]], None]] = None,
        blocking: bool = False,
    ) -> Optional[threading.Thread]:
        """
        Emit an event to the SYNAPSE bus.

        Args:
            event_type: One of the VALID_EVENT_TYPES (e.g., "paper_discovered").
            payload: Arbitrary dict with event-specific data.
            callback: Optional callable(bool, str|None) invoked after emission.
                      Receives (success: bool, error_message: str or None).
            blocking: If True, emit synchronously in the calling thread.
                      If False (default), dispatch in a daemon thread.

        Returns:
            The threading.Thread if non-blocking, None if blocking.

        Raises:
            ValueError: If event_type is not in VALID_EVENT_TYPES.
        """
        if event_type not in self.VALID_EVENT_TYPES:
            raise ValueError(
                f"Invalid event_type '{event_type}'. Must be one of: "
                f"{sorted(self.VALID_EVENT_TYPES)}"
            )

        event = self._build_event(event_type, payload)

        if blocking:
            self._do_emit(event, callback)
            return None
        else:
            thread = threading.Thread(
                target=self._do_emit,
                args=(event, callback),
                daemon=True,
                name=f"synapse-emit-{event_type}",
            )
            thread.start()
            return thread

    # ------------------------------------------------------------------
    # -- Internal helpers --
    # ------------------------------------------------------------------

    def _build_event(self, event_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Construct a SYNAPSE-compliant event envelope.

        Args:
            event_type: Validated event type string.
            payload: Event-specific data dict.

        Returns:
            Complete event dict with mandatory SYNAPSE fields.
        """
        return {
            "event_id": uuid.uuid4().hex,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": event_type,
            "source": self.source,
            "payload": payload,
        }

    def _do_emit(
        self,
        event: Dict[str, Any],
        callback: Optional[Callable[[bool, Optional[str]], None]] = None,
    ):
        """
        Perform the actual HTTP POST to the SYNAPSE bus with retry logic.

        If requests is unavailable, logs the event locally and calls the
        callback with success=True (local logging is always available).

        Args:
            event: Fully constructed event envelope.
            callback: Optional post-emission callback.
        """
        if not _REQUESTS_AVAILABLE or self._session is None:
            # -- Local logging fallback --
            logger.info(
                "SYNAPSE event (local log): type=%s, id=%s, payload_keys=%s",
                event["event_type"],
                event["event_id"],
                list(event["payload"].keys()) if event.get("payload") else [],
            )
            logger.debug("SYNAPSE event payload: %s", json.dumps(event, indent=2))
            if callback:
                callback(True, None)
            return

        last_error = None
        for attempt in range(1, self.max_retries + 2):  # 1 initial + N retries
            try:
                response = self._session.post(
                    self.bus_url,
                    json=event,
                    timeout=self.timeout,
                )
                response.raise_for_status()
                logger.debug(
                    "SYNAPSE event emitted: type=%s, id=%s, status=%d",
                    event["event_type"],
                    event["event_id"],
                    response.status_code,
                )
                if callback:
                    callback(True, None)
                return
            except requests.exceptions.ConnectionError:
                # -- Silent fallback (v5.9.5): single warning, no stack trace --
                logger.warning(
                    "SYNAPSE bus unreachable (port 8000 offline). Event logged locally."
                )
                last_error = "Connection refused: Synapse bus offline"
                break  # Do not retry on connection-refused
            except requests.exceptions.Timeout as e:
                last_error = f"Request timed out after {self.timeout}s: {e}"
                logger.warning(
                    "SYNAPSE emission attempt %d/%d failed (timeout): %s",
                    attempt,
                    self.max_retries + 1,
                    e,
                )
            except requests.exceptions.HTTPError as e:
                last_error = f"HTTP error: {e}"
                logger.warning(
                    "SYNAPSE emission attempt %d/%d failed (HTTP): %s",
                    attempt,
                    self.max_retries + 1,
                    e,
                )
                # Do not retry on 4xx client errors (except 429)
                if (
                    e.response is not None
                    and 400 <= e.response.status_code < 500
                    and e.response.status_code != 429
                ):
                    break
            except Exception as e:
                last_error = f"Unexpected error: {e}"
                logger.warning(
                    "SYNAPSE emission attempt %d/%d failed (unexpected): %s",
                    attempt,
                    self.max_retries + 1,
                    e,
                )

        # -- All attempts exhausted (v5.9.5: downgraded from error to warning) --
        if last_error:
            logger.warning(
                "SYNAPSE emission skipped: type=%s, id=%s, reason=%s",
                event["event_type"],
                event["event_id"],
                last_error,
            )
        if callback:
            callback(False, last_error)

    def close(self):
        """
        Clean up the HTTP session and release resources.

        Should be called during application shutdown to ensure
        proper connection pool cleanup.
        """
        if self._session is not None:
            self._session.close()
            self._session = None
            logger.info("EventEmitter session closed.")

    def __del__(self):
        """Destructor: ensure session is cleaned up."""
        self.close()


# ------------------------------------------------------------------
# -- Module-level convenience singleton --
# ------------------------------------------------------------------

# Default emitter instance for quick import and use across TALOS modules.
# Import as: from src.integration.synapse_client import synapse_emitter
synapse_emitter = EventEmitter()