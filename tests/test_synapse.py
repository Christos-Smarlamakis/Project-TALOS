# -*- coding: utf-8 -*-
"""
Module: test_synapse.py
Project: TALOS v5.9.17
Description:
    Unit tests for the SYNAPSE Event-Driven Protocol components: EventEmitter
    (synapse_client.py) and Synapse webhook routes (synapse_routes.py).
    Tests cover event envelope construction, event type validation, webhook
    command validation, and handler registration.

    Key design decisions:
    - EventEmitter tests use local logging fallback (no live SYNAPSE bus needed).
    - Webhook route tests use FastAPI TestClient for full request/response simulation.
    - All tests are hermetic -- no external dependencies required.

Dependencies:
    - pytest: Test framework for fixture-based testing.
    - fastapi.testclient.TestClient: Simulated HTTP requests for route testing.
"""
import json
import uuid
import pytest
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock

# Test EventEmitter directly (no external dependencies needed for core logic).
from src.integration.synapse_client import EventEmitter


# ------------------------------------------------------------------
# -- EventEmitter Tests --
# ------------------------------------------------------------------

class TestEventEmitter:
    """Tests for the SYNAPSE EventEmitter class."""

    def test_build_event_structure(self):
        """Verify that _build_event produces a compliant SYNAPSE envelope."""
        emitter = EventEmitter()
        event = emitter._build_event("paper_discovered", {"doi": "10.1234/test"})

        # Mandatory fields.
        assert "event_id" in event
        assert "timestamp" in event
        assert "event_type" in event
        assert "source" in event
        assert "payload" in event

        # Value checks.
        assert event["event_type"] == "paper_discovered"
        assert event["source"] == "talos"
        assert event["payload"]["doi"] == "10.1234/test"

        # event_id should be a valid hex UUID (32 chars, no dashes).
        assert len(event["event_id"]) == 32
        int(event["event_id"], 16)  # Should not raise ValueError.

        # timestamp should be ISO 8601.
        datetime.fromisoformat(event["timestamp"])

    def test_emit_valid_event_types(self):
        """Verify that all valid event types are accepted by emit()."""
        emitter = EventEmitter()
        for event_type in emitter.VALID_EVENT_TYPES:
            # Should not raise ValueError.
            emitter.emit(event_type, {"test": True}, blocking=True)

    def test_emit_invalid_event_type(self):
        """Verify that invalid event types raise ValueError."""
        emitter = EventEmitter()
        with pytest.raises(ValueError, match="Invalid event_type"):
            emitter.emit("invalid_event_type", {}, blocking=True)

    def test_emit_local_logging_fallback(self):
        """Verify that emit works when requests is unavailable (local logging)."""
        emitter = EventEmitter()
        # With blocking=True and no requests available (or unreachable bus),
        # the emitter should log locally without raising.
        # This test verifies the non-blocking path doesn't crash.
        thread = emitter.emit("agent_step", {"step": 1}, blocking=False)
        if thread is not None:
            thread.join(timeout=2.0)

    def test_emit_with_callback(self):
        """Verify that the callback is invoked after emission."""
        emitter = EventEmitter()
        callback_results = {}

        def test_callback(success, error_msg):
            callback_results["success"] = success
            callback_results["error"] = error_msg

        # Mock the session post to return HTTP 200, simulating the SYNAPSE bus.
        if emitter._session is not None:
            mock_response = MagicMock()
            mock_response.status_code = 200
            with patch.object(emitter._session, 'post', return_value=mock_response):
                emitter.emit(
                    "search_completed",
                    {"results": 42},
                    callback=test_callback,
                    blocking=True,
                )
        else:
            # If no requests library, _do_emit uses local logging fallback
            # which always calls callback with success=True.
            emitter.emit(
                "search_completed",
                {"results": 42},
                callback=test_callback,
                blocking=True,
            )

        # Callback should have been called.
        assert "success" in callback_results
        assert callback_results["success"] is True

    def test_event_id_uniqueness(self):
        """Verify that each event gets a unique event_id."""
        emitter = EventEmitter()
        ids = set()
        for _ in range(100):
            event = emitter._build_event("paper_evaluated", {"score": 0.95})
            ids.add(event["event_id"])
        assert len(ids) == 100  # All should be unique.

    def test_emitter_close(self):
        """Verify that close() cleans up without errors."""
        emitter = EventEmitter()
        emitter.close()
        # Double close should not raise.
        emitter.close()

    def test_emitter_destructor(self):
        """Verify that __del__ does not raise."""
        emitter = EventEmitter()
        # Simulate deletion.
        emitter.__del__()

    def test_custom_bus_url(self):
        """Verify that a custom bus_url is stored correctly."""
        emitter = EventEmitter(bus_url="http://custom:9999/events")
        assert emitter.bus_url == "http://custom:9999/events"


# ------------------------------------------------------------------
# -- Synapse Webhook Route Tests --
# ------------------------------------------------------------------

class TestSynapseWebhookRoutes:
    """Tests for the FastAPI Synapse webhook routes."""

    @pytest.fixture
    def client(self):
        """Create a FastAPI TestClient with the synapse router mounted."""
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from src.api.synapse_routes import router

        app = FastAPI()
        app.include_router(router)
        return TestClient(app)

    def test_webhook_get_status(self, client):
        """Verify that the get_status command returns acknowledged."""
        response = client.post(
            "/api/v1/synapse/webhook",
            json={"command": "get_status", "params": {}},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["command"] == "get_status"
        assert data["status"] == "acknowledged"
        assert "message" in data
        assert "timestamp" in data

    def test_webhook_shutdown(self, client):
        """Verify that the shutdown command is acknowledged."""
        response = client.post(
            "/api/v1/synapse/webhook",
            json={"command": "shutdown", "params": {"reason": "maintenance"}},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["command"] == "shutdown"
        assert data["status"] == "acknowledged"

    def test_webhook_unknown_command(self, client):
        """Verify that unknown commands return 400."""
        response = client.post(
            "/api/v1/synapse/webhook",
            json={"command": "execute_skynet", "params": {}},
        )
        assert response.status_code == 400
        assert "Unknown command" in response.json()["detail"]

    def test_webhook_trigger_search_no_handler(self, client):
        """Verify that commands with no handler return 501."""
        # trigger_search is in _SUPPORTED_COMMANDS but has no registered handler.
        response = client.post(
            "/api/v1/synapse/webhook",
            json={"command": "trigger_search", "params": {"query": "AI ethics"}},
        )
        assert response.status_code == 501
        assert "no handler" in response.json()["detail"].lower()

    def test_webhook_response_schema(self, client):
        """Verify that all responses match the SynapseWebhookResponse schema."""
        response = client.post(
            "/api/v1/synapse/webhook",
            json={"command": "get_status", "params": {}},
        )
        data = response.json()
        # Verify all expected fields.
        assert set(data.keys()) == {"command", "status", "message", "timestamp"}
        assert data["status"] in ("acknowledged", "rejected", "not_implemented")

    def test_webhook_with_request_id(self, client):
        """Verify that request_id is accepted in the payload."""
        response = client.post(
            "/api/v1/synapse/webhook",
            json={
                "command": "get_status",
                "params": {},
                "request_id": "correlation-abc-123",
            },
        )
        assert response.status_code == 200

    def test_webhook_missing_command(self, client):
        """Verify that missing command field returns 422."""
        response = client.post(
            "/api/v1/synapse/webhook",
            json={"params": {}},
        )
        assert response.status_code == 422

    def test_webhook_empty_command(self, client):
        """Verify that empty command field returns 422."""
        response = client.post(
            "/api/v1/synapse/webhook",
            json={"command": "", "params": {}},
        )
        assert response.status_code == 422


# ------------------------------------------------------------------
# -- Handler Registration Tests --
# ------------------------------------------------------------------

class TestHandlerRegistration:
    """Tests for the SYNAPSE command handler registry."""

    def test_register_valid_handler(self):
        """Verify that a valid command handler can be registered."""
        from src.api.synapse_routes import register_handler, COMMAND_HANDLERS
        from unittest.mock import MagicMock

        original_handler = COMMAND_HANDLERS.get("trigger_evaluation")
        try:
            mock_handler = MagicMock(return_value=("acknowledged", "ok"))
            register_handler("trigger_evaluation", mock_handler)
            assert COMMAND_HANDLERS["trigger_evaluation"] is mock_handler
        finally:
            # Restore original.
            if original_handler:
                COMMAND_HANDLERS["trigger_evaluation"] = original_handler
            else:
                COMMAND_HANDLERS.pop("trigger_evaluation", None)

    def test_register_invalid_command(self):
        """Verify that registering an invalid command raises ValueError."""
        from src.api.synapse_routes import register_handler
        from unittest.mock import MagicMock

        with pytest.raises(ValueError, match="not supported"):
            register_handler("invalid_cmd", MagicMock())

    def test_get_status_handler_returns_tuple(self):
        """Verify that the default get_status handler returns a tuple."""
        from src.api.synapse_routes import COMMAND_HANDLERS
        handler = COMMAND_HANDLERS.get("get_status")
        assert handler is not None
        status, message = handler({})
        assert status == "acknowledged"
        assert isinstance(message, str)
        assert "TALOS" in message

    def test_shutdown_handler_returns_tuple(self):
        """Verify that the default shutdown handler returns a tuple."""
        from src.api.synapse_routes import COMMAND_HANDLERS
        handler = COMMAND_HANDLERS.get("shutdown")
        assert handler is not None
        status, message = handler({})
        assert status == "acknowledged"