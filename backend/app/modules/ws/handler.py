"""WebSocket handler for real-time agent trace streaming.

Endpoint: ``/ws/processing/{invoice_id}``

Behaviour:
  DEMO_MODE=True  -- streams pre-computed demo events directly (no Redis)
  DEMO_MODE=False -- subscribes to Redis pub/sub and forwards events

The handler is intentionally kept simple:
  1. Accept the WebSocket connection.
  2. Replay any buffered events the client may have missed (reconnection support).
  3. Stream live events until pipeline_complete is received or client disconnects.

JWT auth is optional for now (full auth in Epic 5).  Pass ``token=<jwt>`` as a
query parameter if you want to identify the caller; the handler logs it but does
not enforce it yet.
"""

from __future__ import annotations

import asyncio
import logging

from fastapi import WebSocket, WebSocketDisconnect
from starlette.websockets import WebSocketState

from app.config import settings
from app.modules.ws.demo_events import build_demo_events
from app.modules.ws.redis_bridge import EventBuffer, subscribe_events

logger = logging.getLogger(__name__)

# Shared in-process event buffer (supports reconnection within the same process)
_event_buffer = EventBuffer(max_events=100)


async def websocket_invoice_handler(
    websocket: WebSocket,
    invoice_id: str,
    token: str | None = None,
) -> None:
    """Accept a WebSocket connection and stream processing events.

    Args:
        websocket: The FastAPI WebSocket instance.
        invoice_id: Invoice being tracked.
        token:      Optional JWT for future auth enforcement.
    """
    await websocket.accept()
    logger.info(
        "WS connected: invoice_id=%s token_provided=%s", invoice_id, bool(token)
    )

    try:
        if settings.DEMO_MODE:
            await _stream_demo(websocket, invoice_id)
        else:
            await _stream_live(websocket, invoice_id)
    except WebSocketDisconnect:
        logger.info("WS disconnected: invoice_id=%s", invoice_id)
    except Exception as exc:
        logger.exception("WS error: invoice_id=%s error=%s", invoice_id, exc)
        if websocket.client_state == WebSocketState.CONNECTED:
            await websocket.send_json(
                {"type": "error", "message": str(exc), "invoice_id": invoice_id}
            )
    finally:
        if websocket.client_state == WebSocketState.CONNECTED:
            await websocket.close()


# ---------------------------------------------------------------------------
# DEMO_MODE stream
# ---------------------------------------------------------------------------

# Small delay between demo events so the frontend animation is visible.
_DEMO_EVENT_DELAY_SECONDS = 0.0  # 0 for tests; override in production via env


async def _stream_demo(websocket: WebSocket, invoice_id: str) -> None:
    """Stream 14 step_complete events + pipeline_complete for DEMO_MODE."""
    events = build_demo_events(invoice_id)
    for event in events:
        await websocket.send_json(event)
        if _DEMO_EVENT_DELAY_SECONDS > 0:
            await asyncio.sleep(_DEMO_EVENT_DELAY_SECONDS)


# ---------------------------------------------------------------------------
# Live stream (Redis pub/sub)
# ---------------------------------------------------------------------------


async def _stream_live(websocket: WebSocket, invoice_id: str) -> None:
    """Forward events from Redis pub/sub to the WebSocket client.

    Also replays any events already in the in-process EventBuffer so
    reconnecting clients catch up instantly.
    """
    # Replay buffered events for reconnection
    buffered = _event_buffer.get(invoice_id)
    for event in buffered:
        await websocket.send_json(event)
        if event.get("type") == "pipeline_complete":
            return  # Pipeline already finished; nothing more to stream

    # Live subscription
    async for event in subscribe_events(invoice_id):
        _event_buffer.add(invoice_id, event)
        await websocket.send_json(event)
        if event.get("type") == "pipeline_complete":
            break
