"""Redis pub/sub bridge for WebSocket event streaming.

Provides:
  publish_event(invoice_id, event_data) -- publish to Redis channel
  subscribe_events(invoice_id)          -- async generator yielding events
  EventBuffer                           -- in-process ring buffer for reconnection replay

Channel naming convention: ``invoice:{invoice_id}``

Redis connection is lazy -- a single aioredis connection pool is created on first
use and reused for subsequent calls.  If Redis is unavailable at startup, the
module fails fast on first use (not at import time), so DEMO_MODE can run without
any Redis dependency.
"""

from __future__ import annotations

import asyncio
import json
import logging
from collections import deque
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Redis connection pool (lazy init)
# ---------------------------------------------------------------------------

_redis_pool: Any = None  # redis.asyncio.Redis instance


async def _get_redis_pool() -> Any:
    """Return a shared Redis connection pool, creating it on first call.

    Separated into its own function so tests can easily patch it.
    """
    global _redis_pool
    if _redis_pool is None:
        import redis.asyncio as aioredis  # type: ignore

        from app.config import settings

        _redis_pool = aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=False,  # We handle decoding ourselves
        )
    return _redis_pool


def _channel(invoice_id: str) -> str:
    """Return the Redis channel name for an invoice."""
    return f"invoice:{invoice_id}"


# ---------------------------------------------------------------------------
# Publish
# ---------------------------------------------------------------------------


async def publish_event(invoice_id: str, event_data: dict) -> int:
    """Publish an event dict to the Redis pub/sub channel for this invoice.

    Args:
        invoice_id: Invoice identifier (used to build the channel name).
        event_data: Arbitrary dict; will be JSON-encoded before publishing.

    Returns:
        Number of subscribers that received the message (from Redis PUBLISH).
    """
    redis = await _get_redis_pool()
    payload = json.dumps(event_data)
    count: int = await redis.publish(_channel(invoice_id), payload)
    return count


# ---------------------------------------------------------------------------
# Subscribe
# ---------------------------------------------------------------------------


class _SubscribeEventsStream:
    """Async iterator that yields decoded event dicts from Redis pub/sub.

    Implements ``__aiter__`` / ``__anext__`` directly (instead of using an async
    generator) so that cleanup (unsubscribe + close) is performed reliably in
    ``aclose()``, which ``async for`` calls automatically when the loop exits
    via ``break`` or exception.

    Unlike async generators, a class-based async iterator's ``aclose()`` is a
    normal coroutine that runs without any ``GeneratorExit`` restrictions.

    Initialization (connecting to Redis, subscribing) is lazy -- it runs on the
    first ``__anext__`` call.
    """

    def __init__(self, invoice_id: str) -> None:
        self._invoice_id = invoice_id
        self._pubsub: Any = None
        self._channel: str = ""
        self._closed = False
        self._initialized = False

    async def _init(self) -> None:
        """Lazy initialization: connect to Redis and subscribe."""
        redis = await _get_redis_pool()
        self._channel = _channel(self._invoice_id)
        self._pubsub = redis.pubsub()
        await self._pubsub.subscribe(self._channel)
        self._initialized = True

    def __aiter__(self):
        return self

    async def __anext__(self) -> dict:
        if not self._initialized:
            await self._init()

        while True:
            if self._closed:
                raise StopAsyncIteration

            message = await self._pubsub.get_message(
                ignore_subscribe_messages=True, timeout=1.0
            )
            if message is not None and message.get("type") == "message":
                raw = message["data"]
                if isinstance(raw, (bytes, bytearray)):
                    raw = raw.decode("utf-8")
                return json.loads(raw)
            else:
                # No message -- yield control to the event loop briefly
                await asyncio.sleep(0.01)

    async def aclose(self) -> None:
        """Unsubscribe and close the pubsub connection."""
        if self._initialized and not self._closed:
            self._closed = True
            await self._pubsub.unsubscribe(self._channel)
            await self._pubsub.aclose()


def subscribe_events(invoice_id: str) -> _SubscribeEventsStream:
    """Create an async iterator that yields decoded event dicts from Redis pub/sub.

    Subscribes to ``invoice:{invoice_id}`` and yields each message as a
    decoded dict.  The iterator runs until the caller breaks out of it,
    at which point it unsubscribes and closes the pubsub connection via
    ``aclose()`` (called automatically by ``async for`` on loop exit).

    Usage::

        async for event in subscribe_events("inv_001"):
            process(event)
            if done:
                break  # triggers aclose() -> unsubscribe + close

    Args:
        invoice_id: Invoice identifier.

    Returns:
        An async iterable/iterator that yields decoded event dicts.
    """
    return _SubscribeEventsStream(invoice_id)


# ---------------------------------------------------------------------------
# EventBuffer -- in-process ring buffer for reconnection replay
# ---------------------------------------------------------------------------


class EventBuffer:
    """In-process FIFO ring buffer that stores the last N events per invoice.

    Used to replay missed events to reconnecting WebSocket clients without
    requiring a Redis LRANGE call.  Each server process maintains its own
    buffer; for multi-process deployments, replay falls back to DB queries
    (see handler.py).

    Args:
        max_events: Maximum number of events stored per invoice_id.
    """

    def __init__(self, max_events: int = 100) -> None:
        self._max_events = max_events
        self._buffers: dict[str, deque] = {}

    def add(self, invoice_id: str, event: dict) -> None:
        """Append an event to the buffer for ``invoice_id``.

        If the buffer is full, the oldest event is discarded (deque maxlen).
        """
        if invoice_id not in self._buffers:
            self._buffers[invoice_id] = deque(maxlen=self._max_events)
        self._buffers[invoice_id].append(event)

    def get(self, invoice_id: str) -> list[dict]:
        """Return all buffered events for ``invoice_id`` in insertion order.

        Returns an empty list if no events have been buffered.
        """
        if invoice_id not in self._buffers:
            return []
        return list(self._buffers[invoice_id])

    def clear(self, invoice_id: str) -> None:
        """Remove all buffered events for ``invoice_id``."""
        self._buffers.pop(invoice_id, None)
