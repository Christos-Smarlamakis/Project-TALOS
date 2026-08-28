# -*- coding: utf-8 -*-
"""
Module: visualizer_bridge.py
Project: TALOS v5.10.13
Description:
    Centralized, fire-and-forget HTTP bridge that pushes evaluation telemetry
    to the 3D Knowledge Constellation Visualizer. Every search pipeline
    (DRL live agent, 24/7 daemon, daily search, historic search) calls
    push_visualizer_event() after scoring a paper so the visualizer receives
    an active push instead of relying solely on its passive AJAX DB poller.

    The bridge posts a flat JSON envelope to the FastAPI endpoint
    POST /api/v1/visualizer/events on port 8001, which classifies the event
    into the 4-state bi-directional beam model (query_out, data_in,
    evaluation, error) and appends it to the recent-beam queue consumed by
    GET /api/v1/visualizer/state.

Dependencies:
    - requests: synchronous HTTP POST to the visualizer events endpoint.
    - threading: daemon-thread dispatch so a slow or offline API never blocks
      the ingestion or evaluation pipeline.
"""
import requests
import threading


def push_visualizer_event(event_type: str, source: str, score=None, title=None, **extra):
    """Fires a non-blocking telemetry event to the 3D Visualizer.

    The optional ``extra`` keyword arguments are merged into the payload so
    callers can attach additional fields (for example ``error_msg``) without
    changing the bridge signature.
    """
    def _send():
        try:
            payload = {
                "event_type": event_type,
                "source": source,
                "score": float(score) if score is not None else 0.0,
                "title": title or "",
            }
            payload.update(extra)
            requests.post("http://127.0.0.1:8001/api/v1/visualizer/events", json=payload, timeout=0.5)
        except Exception:
            pass
    threading.Thread(target=_send, daemon=True).start()
