# -*- coding: utf-8 -*-
"""
Module: synapse_routes.py
Project: TALOS v5.9.18
Description:
    FastAPI APIRouter exposing the SYNAPSE webhook endpoint for inbound
    commands from external microservices in the ALEXANDRIA ecosystem.
    This module implements the receiver side of the SYNAPSE Event-Driven
    Protocol -- TALOS listens on POST /api/v1/synapse/webhook for commands
    such as trigger_search, trigger_evaluation, get_status, and shutdown.

    Key design decisions:
    - Pydantic v2 models for strict command validation.
    - All command handling is stateless -- the router validates and logs
      commands, then delegates to background task mechanisms in main_api.py.
    - Port 8001 (TALOS FastAPI) receives SYNAPSE commands; port 8000 is the
      SYNAPSE bus for outbound events.
    - Future extensions can add command-specific handlers by registering
      callables via the COMMAND_HANDLERS registry dict.

Dependencies:
    - fastapi.APIRouter: Route definition and inclusion into main app.
    - fastapi.HTTPException: Error responses for invalid commands.
    - pydantic.BaseModel: Strict command schema validation (v2).
    - typing.Dict, typing.Optional, typing.Any: Type hints.
    - logging: Structured logging of received commands.
    - datetime: Timestamp for acknowledgment responses.
"""

from datetime import datetime, timezone
from typing import Optional, Dict, Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

import logging

logger = logging.getLogger("talos.synapse_routes")

# ------------------------------------------------------------------
# -- FastAPI Router --
# ------------------------------------------------------------------

router = APIRouter(
    prefix="/api/v1/synapse",
    tags=["Synapse Protocol"],
    responses={
        400: {"description": "Invalid command payload"},
        422: {"description": "Unprocessable entity -- schema validation failed"},
        501: {"description": "Command recognized but not yet implemented"},
    },
)

# ------------------------------------------------------------------
# -- Pydantic v2 Models for Inbound Commands --
# ------------------------------------------------------------------

class SynapseWebhookRequest(BaseModel):
    """
    Inbound SYNAPSE command envelope.

    The command field identifies the action to perform. The params dict
    carries optional parameters specific to each command type.
    """
    command: str = Field(
        ...,
        min_length=1,
        description="Command identifier: trigger_search, trigger_evaluation, get_status, shutdown",
    )
    params: Dict[str, Any] = Field(
        default_factory=dict,
        description="Optional parameters for the command",
    )
    request_id: Optional[str] = Field(
        default=None,
        description="Optional correlation ID for tracing across microservices",
    )


class SynapseWebhookResponse(BaseModel):
    """
    Acknowledgment response for a received SYNAPSE command.

    Includes the received command, a status indicator, an optional
    message with details, and the server timestamp.
    """
    command: str
    status: str  # "acknowledged", "rejected", "not_implemented"
    message: str = ""
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


# ------------------------------------------------------------------
# -- Supported Commands Registry --
# ------------------------------------------------------------------

# Valid commands that this webhook endpoint recognizes.
_SUPPORTED_COMMANDS = frozenset({
    "trigger_search",
    "trigger_evaluation",
    "get_status",
    "shutdown",
})

# Command handler registry: mapping of command string -> callable.
# Handlers receive (params: dict) and return (status: str, message: str).
# External modules can register handlers via register_handler().
COMMAND_HANDLERS: Dict[str, Any] = {}


def register_handler(command: str, handler: Any):
    """
    Register a handler callable for a specific SYNAPSE command.

    Args:
        command: The command string (must be in _SUPPORTED_COMMANDS).
        handler: A callable that accepts (params: dict) and returns
                 (status: str, message: str).

    Raises:
        ValueError: If the command is not in the supported commands set.
    """
    if command not in _SUPPORTED_COMMANDS:
        raise ValueError(
            f"Command '{command}' is not supported. Valid commands: "
            f"{sorted(_SUPPORTED_COMMANDS)}"
        )
    COMMAND_HANDLERS[command] = handler
    logger.info("Registered SYNAPSE command handler: %s", command)


# ------------------------------------------------------------------
# -- Core Command Handlers (Default Implementations) --
# ------------------------------------------------------------------

def _handle_get_status(params: Dict[str, Any]) -> tuple:
    """Return basic TALOS status information."""
    return ("acknowledged", "TALOS v5.7.0 is running. Synapse webhook operational.")


def _handle_shutdown(params: Dict[str, Any]) -> tuple:
    """Acknowledge shutdown command (actual shutdown is controlled externally)."""
    logger.warning("SYNAPSE shutdown command received (params=%s). Manual shutdown required.", params)
    return ("acknowledged", "Shutdown command logged. TALOS must be stopped manually.")


# Register default handlers
register_handler("get_status", _handle_get_status)
register_handler("shutdown", _handle_shutdown)


# ------------------------------------------------------------------
# -- Webhook Endpoint --
# ------------------------------------------------------------------

@router.post("/webhook", response_model=SynapseWebhookResponse)
def synapse_webhook(request: SynapseWebhookRequest):
    """
    Receive inbound commands via the SYNAPSE Event-Driven Protocol.

    This endpoint is the single entry point for external microservices to
    send commands to TALOS. Commands are validated against the supported
    set, dispatched to registered handlers, and acknowledged with a
    structured response.

    Supported commands:
        - trigger_search: Launch a new literature search pipeline.
        - trigger_evaluation: Run AI evaluation on stored papers.
        - get_status: Query TALOS health and operational status.
        - shutdown: Request graceful shutdown of the TALOS service.

    Args:
        request: Validated SynapseWebhookRequest with command and params.

    Returns:
        SynapseWebhookResponse with acknowledgment status and details.

    Raises:
        HTTPException 400: If the command is not in the supported set.
        HTTPException 501: If the command has no registered handler.
    """
    command = request.command.strip().lower()

    # -- Validate command --
    if command not in _SUPPORTED_COMMANDS:
        logger.warning(
            "SYNAPSE webhook rejected: unknown command '%s' (request_id=%s)",
            command,
            request.request_id,
        )
        raise HTTPException(
            status_code=400,
            detail=f"Unknown command '{command}'. Supported: {sorted(_SUPPORTED_COMMANDS)}",
        )

    logger.info(
        "SYNAPSE webhook received: command=%s, params=%s, request_id=%s",
        command,
        request.params,
        request.request_id,
    )

    # -- Dispatch to registered handler --
    handler = COMMAND_HANDLERS.get(command)
    if handler is None:
        logger.warning(
            "SYNAPSE command '%s' has no registered handler (request_id=%s)",
            command,
            request.request_id,
        )
        raise HTTPException(
            status_code=501,
            detail=f"Command '{command}' recognized but no handler is registered.",
        )

    try:
        status, message = handler(request.params)
    except Exception as e:
        logger.error(
            "SYNAPSE handler for '%s' raised exception: %s",
            command,
            e,
            exc_info=True,
        )
        return SynapseWebhookResponse(
            command=command,
            status="rejected",
            message=f"Handler error: {str(e)}",
        )

    return SynapseWebhookResponse(
        command=command,
        status=status,
        message=message,
    )