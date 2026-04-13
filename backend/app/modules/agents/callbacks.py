"""Agent callback handler: bridges Strands agent events to WebSocket via Redis.

Strands Agents SDK fires events during agent execution. This module provides
a callback handler that captures BeforeToolCallEvent and AfterToolCallEvent
and publishes them to Redis pub/sub so the WebSocket handler can stream
them to connected clients.

Usage:
    from app.modules.agents.callbacks import create_agent_callback_handler

    handler = create_agent_callback_handler(invoice_id="inv_123")
    agent = Agent(model=model, ..., callback_handler=handler)
"""

from __future__ import annotations

import json
import logging
import time
from typing import Any

from app.modules.agents.config import (
    EVENT_AGENT_THINKING,
    EVENT_HANDOFF,
    EVENT_PIPELINE_ERROR,
    EVENT_TOOL_COMPLETE,
    EVENT_TOOL_START,
    WS_CHANNEL_PREFIX,
)

logger = logging.getLogger(__name__)


def _build_tool_start_event(
    *, tool_name: str, agent_name: str, step: int
) -> dict[str, Any]:
    """Build a tool_start event for WebSocket streaming."""
    return {
        "type": EVENT_TOOL_START,
        "tool_name": tool_name,
        "agent": agent_name,
        "step": step,
        "timestamp": time.time(),
    }


def _build_tool_complete_event(
    *,
    tool_name: str,
    agent_name: str,
    step: int,
    result: Any,
    elapsed_ms: int,
    status: str = "success",
) -> dict[str, Any]:
    """Build a tool_complete event for WebSocket streaming."""
    return {
        "type": EVENT_TOOL_COMPLETE,
        "tool_name": tool_name,
        "agent": agent_name,
        "step": step,
        "status": status,
        "elapsed_ms": elapsed_ms,
        "timestamp": time.time(),
    }


def _build_thinking_event(*, agent_name: str, content: str) -> dict[str, Any]:
    """Build an agent_thinking event (reasoning trace fragment)."""
    return {
        "type": EVENT_AGENT_THINKING,
        "agent": agent_name,
        "content": content[:500],  # Truncate to avoid huge payloads
        "timestamp": time.time(),
    }


def _build_handoff_event(
    *, from_agent: str, to_agent: str, context_keys: list[str]
) -> dict[str, Any]:
    """Build an agent_handoff event."""
    return {
        "type": EVENT_HANDOFF,
        "from_agent": from_agent,
        "to_agent": to_agent,
        "context_keys": context_keys,
        "timestamp": time.time(),
    }


def _build_error_event(
    *, agent_name: str, tool_name: str | None, error: str
) -> dict[str, Any]:
    """Build a pipeline_error event."""
    return {
        "type": EVENT_PIPELINE_ERROR,
        "agent": agent_name,
        "tool_name": tool_name,
        "error": error[:1000],  # Truncate error messages
        "timestamp": time.time(),
    }


class AgentCallbackHandler:
    """Captures Strands agent events and publishes to Redis for WebSocket streaming.

    Tracks tool execution timing and step counts per-agent so the frontend
    can display accurate progress.

    This handler is designed to be passed to a Strands Agent's
    ``callback_handler`` parameter. Strands fires ``__call__`` with event
    dicts containing a ``"type"`` key.
    """

    def __init__(self, invoice_id: str) -> None:
        self.invoice_id = invoice_id
        self.channel = f"{WS_CHANNEL_PREFIX}:{invoice_id}"
        self._step_counter: int = 0
        self._tool_start_times: dict[str, float] = {}
        self._events: list[dict[str, Any]] = []

    @property
    def step_counter(self) -> int:
        """Current step number (read-only)."""
        return self._step_counter

    @property
    def events(self) -> list[dict[str, Any]]:
        """All collected events (read-only, for testing/tracing)."""
        return list(self._events)

    async def on_tool_start(self, tool_name: str, agent_name: str) -> None:
        """Called before a tool executes."""
        self._step_counter += 1
        self._tool_start_times[tool_name] = time.time()

        event = _build_tool_start_event(
            tool_name=tool_name,
            agent_name=agent_name,
            step=self._step_counter,
        )
        self._events.append(event)
        await self._publish(event)

    async def on_tool_complete(
        self, tool_name: str, agent_name: str, result: Any = None
    ) -> None:
        """Called after a tool completes successfully."""
        start_time = self._tool_start_times.pop(tool_name, time.time())
        elapsed_ms = int((time.time() - start_time) * 1000)

        event = _build_tool_complete_event(
            tool_name=tool_name,
            agent_name=agent_name,
            step=self._step_counter,
            result=result,
            elapsed_ms=elapsed_ms,
        )
        self._events.append(event)
        await self._publish(event)

    async def on_tool_error(
        self, tool_name: str, agent_name: str, error: str
    ) -> None:
        """Called when a tool fails."""
        start_time = self._tool_start_times.pop(tool_name, time.time())
        elapsed_ms = int((time.time() - start_time) * 1000)

        event = _build_tool_complete_event(
            tool_name=tool_name,
            agent_name=agent_name,
            step=self._step_counter,
            result=None,
            elapsed_ms=elapsed_ms,
            status="error",
        )
        self._events.append(event)
        await self._publish(event)

        error_event = _build_error_event(
            agent_name=agent_name, tool_name=tool_name, error=error
        )
        self._events.append(error_event)
        await self._publish(error_event)

    async def on_thinking(self, agent_name: str, content: str) -> None:
        """Called when agent produces reasoning text."""
        event = _build_thinking_event(agent_name=agent_name, content=content)
        self._events.append(event)
        await self._publish(event)

    async def on_handoff(
        self,
        from_agent: str,
        to_agent: str,
        context_keys: list[str] | None = None,
    ) -> None:
        """Called when one agent hands off to another."""
        event = _build_handoff_event(
            from_agent=from_agent,
            to_agent=to_agent,
            context_keys=context_keys or [],
        )
        self._events.append(event)
        await self._publish(event)

    async def _publish(self, event: dict[str, Any]) -> None:
        """Publish event to Redis pub/sub channel.

        Fails silently if Redis is unavailable (logged as warning).
        """
        try:
            from app.modules.ws.redis_bridge import publish_event

            await publish_event(self.invoice_id, event)
        except Exception:
            logger.warning(
                "Failed to publish agent event to Redis: invoice=%s type=%s",
                self.invoice_id,
                event.get("type"),
                exc_info=True,
            )


def create_agent_callback_handler(invoice_id: str) -> AgentCallbackHandler:
    """Create a callback handler bound to a specific invoice's Redis channel."""
    return AgentCallbackHandler(invoice_id=invoice_id)
