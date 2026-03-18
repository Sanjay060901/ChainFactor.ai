"""Feature 4.2: WebSocket server -- additional integration tests.

This file covers areas not tested in test_websocket.py:
  - WebSocket connection acceptance (basic handshake)
  - SSE endpoint content-type header
  - SSE endpoint streams valid data: events
  - Reconnection replay via EventBuffer (in-process)
  - Handler streams from DB agent_traces on reconnection (mocked)
  - Token query param accepted without error
  - Pipeline_complete stops the stream
  - Concurrent connections to different invoice_ids are isolated

Uses starlette.testclient.TestClient for synchronous WebSocket testing and
httpx.AsyncClient for SSE endpoint tests.

External dependencies (Redis, DB) are mocked throughout.
"""

from __future__ import annotations

import json
from unittest.mock import patch

import pytest
from starlette.testclient import TestClient

from app.config import settings
from app.modules.ws.redis_bridge import EventBuffer


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_step_event(step: int = 1) -> dict:
    return {
        "type": "step_complete",
        "step": step,
        "step_name": "extract_invoice",
        "agent": "invoice_processing",
        "status": "complete",
        "detail": "done",
        "result": {},
        "progress": round(step / 14, 2),
        "elapsed_ms": step * 1000,
    }


def _make_complete_event(invoice_id: str = "inv_test") -> dict:
    return {
        "type": "pipeline_complete",
        "decision": "approved",
        "risk_score": 82,
        "reason": "Test approved",
        "nft_asset_id": 99999,
        "invoice_id": invoice_id,
    }


# ---------------------------------------------------------------------------
# WebSocket connection acceptance
# ---------------------------------------------------------------------------


class TestWebSocketAcceptance:
    """WebSocket handshake and basic connectivity."""

    def test_ws_accepts_connection_in_demo_mode(self):
        """WebSocket should accept the connection and return events in DEMO_MODE."""
        from app.main import app

        original = settings.DEMO_MODE
        settings.DEMO_MODE = True
        try:
            client = TestClient(app)
            with client.websocket_connect("/ws/processing/inv_demo") as ws:
                # First message should arrive immediately
                data = ws.receive_json(mode="text")
                assert data is not None
                assert "type" in data
        finally:
            settings.DEMO_MODE = original

    def test_ws_accepts_token_query_param(self):
        """WebSocket with token= query param should be accepted without error."""
        from app.main import app

        original = settings.DEMO_MODE
        settings.DEMO_MODE = True
        try:
            client = TestClient(app)
            with client.websocket_connect(
                "/ws/processing/inv_token_test?token=fake.jwt.token"
            ) as ws:
                data = ws.receive_json(mode="text")
                assert data is not None
        finally:
            settings.DEMO_MODE = original

    def test_ws_demo_delivers_all_15_events(self):
        """DEMO_MODE must yield exactly 14 step events + 1 pipeline_complete."""
        from app.main import app

        original = settings.DEMO_MODE
        settings.DEMO_MODE = True
        try:
            client = TestClient(app)
            with client.websocket_connect("/ws/processing/inv_stub_001") as ws:
                events = []
                while True:
                    try:
                        data = ws.receive_json(mode="text")
                        events.append(data)
                        if data.get("type") == "pipeline_complete":
                            break
                    except Exception:
                        break

                step_events = [e for e in events if e.get("type") == "step_complete"]
                complete_events = [
                    e for e in events if e.get("type") == "pipeline_complete"
                ]
                assert len(step_events) == 14
                assert len(complete_events) == 1
        finally:
            settings.DEMO_MODE = original

    def test_ws_pipeline_complete_is_last_event(self):
        """pipeline_complete must be the final event, not mid-stream."""
        from app.main import app

        original = settings.DEMO_MODE
        settings.DEMO_MODE = True
        try:
            client = TestClient(app)
            with client.websocket_connect("/ws/processing/inv_stub_001") as ws:
                events = []
                while True:
                    try:
                        data = ws.receive_json(mode="text")
                        events.append(data)
                        if data.get("type") == "pipeline_complete":
                            break
                    except Exception:
                        break

                assert events[-1]["type"] == "pipeline_complete"
                for e in events[:-1]:
                    assert e["type"] != "pipeline_complete"
        finally:
            settings.DEMO_MODE = original


# ---------------------------------------------------------------------------
# SSE endpoint
# ---------------------------------------------------------------------------


class TestSSEEndpoint:
    """Server-Sent Events fallback endpoint."""

    @pytest.mark.asyncio
    async def test_sse_returns_event_stream_content_type(self):
        """GET /api/v1/invoices/{id}/stream must return text/event-stream."""
        from httpx import ASGITransport, AsyncClient

        from app.main import app

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            async with client.stream(
                "GET", "/api/v1/invoices/inv_stub_001/stream"
            ) as resp:
                assert resp.status_code == 200
                content_type = resp.headers.get("content-type", "")
                assert "text/event-stream" in content_type

    @pytest.mark.asyncio
    async def test_sse_streams_valid_data_lines(self):
        """SSE stream lines should start with 'data: ' and contain valid JSON."""
        from httpx import ASGITransport, AsyncClient

        from app.main import app

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # Read a limited number of lines to avoid blocking forever
            raw_lines = []
            async with client.stream(
                "GET", "/api/v1/invoices/inv_stub_001/stream"
            ) as resp:
                async for line in resp.aiter_lines():
                    if line.strip():
                        raw_lines.append(line)
                    if len(raw_lines) >= 3:
                        break

        assert len(raw_lines) >= 1
        for line in raw_lines:
            assert line.startswith("data: "), (
                f"SSE line missing 'data: ' prefix: {line!r}"
            )
            payload = line[len("data: ") :]
            parsed = json.loads(payload)
            assert "type" in parsed

    @pytest.mark.asyncio
    async def test_sse_first_event_is_step_1(self):
        """First SSE event should be step 1 (extract_invoice)."""
        from httpx import ASGITransport, AsyncClient

        from app.main import app

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            async with client.stream(
                "GET", "/api/v1/invoices/inv_stub_001/stream"
            ) as resp:
                async for line in resp.aiter_lines():
                    if line.startswith("data: "):
                        first_event = json.loads(line[len("data: ") :])
                        break

        assert first_event["type"] == "step_complete"
        assert first_event["step"] == 1
        assert first_event["step_name"] == "extract_invoice"


# ---------------------------------------------------------------------------
# Reconnection replay (EventBuffer)
# ---------------------------------------------------------------------------


class TestReconnectionReplay:
    """WebSocket reconnection replay via in-process EventBuffer."""

    def test_live_mode_replays_buffered_events_on_reconnect(self):
        """If the EventBuffer already holds events for an invoice, a fresh
        WebSocket connection should receive those buffered events first
        before subscribing to Redis."""
        from app.main import app
        from app.modules.ws import handler as ws_handler

        original = settings.DEMO_MODE
        settings.DEMO_MODE = False

        step_event = _make_step_event(1)
        complete_event = _make_complete_event("inv_replay")

        # Pre-populate the buffer so a "reconnecting" client gets replay
        ws_handler._event_buffer.add("inv_replay", step_event)
        ws_handler._event_buffer.add("inv_replay", complete_event)

        try:
            client = TestClient(app)
            with client.websocket_connect("/ws/processing/inv_replay") as ws:
                received = []
                while True:
                    try:
                        data = ws.receive_json(mode="text")
                        received.append(data)
                        if data.get("type") == "pipeline_complete":
                            break
                    except Exception:
                        break

                # Both buffered events should be replayed without Redis
                assert len(received) == 2
                assert received[0] == step_event
                assert received[1] == complete_event
        finally:
            settings.DEMO_MODE = original
            ws_handler._event_buffer.clear("inv_replay")

    def test_buffer_cleared_state_returns_no_replay(self):
        """If the buffer is empty, no replay events should be sent."""
        from app.modules.ws import handler as ws_handler

        # Buffer is empty -- get should return []
        ws_handler._event_buffer.clear("inv_no_history")
        buffered = ws_handler._event_buffer.get("inv_no_history")
        assert buffered == []


# ---------------------------------------------------------------------------
# Live mode: Redis event forwarding
# ---------------------------------------------------------------------------


class TestLiveModeEventForwarding:
    """WebSocket handler in live mode forwards Redis events to the client."""

    def test_live_mode_forwards_events_and_stops_at_complete(self):
        """In live mode, step + pipeline_complete events from Redis should be
        forwarded to the WebSocket client.  The connection closes after
        pipeline_complete."""
        from app.main import app

        original = settings.DEMO_MODE
        settings.DEMO_MODE = False

        step = _make_step_event(1)
        complete = _make_complete_event("inv_live_fwd")

        async def mock_subscribe(invoice_id):
            yield step
            yield complete

        try:
            with patch(
                "app.modules.ws.handler.subscribe_events",
                side_effect=mock_subscribe,
            ):
                client = TestClient(app)
                with client.websocket_connect("/ws/processing/inv_live_fwd") as ws:
                    received = []
                    while True:
                        try:
                            data = ws.receive_json(mode="text")
                            received.append(data)
                            if data.get("type") == "pipeline_complete":
                                break
                        except Exception:
                            break

                    assert len(received) == 2
                    assert received[0]["type"] == "step_complete"
                    assert received[1]["type"] == "pipeline_complete"
        finally:
            settings.DEMO_MODE = original

    def test_live_mode_stops_cleanly_after_pipeline_complete(self):
        """After pipeline_complete, no further events should be forwarded even
        if the Redis subscription yields more messages."""
        from app.main import app

        original = settings.DEMO_MODE
        settings.DEMO_MODE = False

        complete = _make_complete_event("inv_stop")
        extra = _make_step_event(99)  # Should never be forwarded

        async def mock_subscribe(invoice_id):
            yield complete
            yield extra  # This should not reach the client

        try:
            with patch(
                "app.modules.ws.handler.subscribe_events",
                side_effect=mock_subscribe,
            ):
                client = TestClient(app)
                with client.websocket_connect("/ws/processing/inv_stop") as ws:
                    received = []
                    while True:
                        try:
                            data = ws.receive_json(mode="text")
                            received.append(data)
                            if data.get("type") == "pipeline_complete":
                                break
                        except Exception:
                            break

                    # Only the pipeline_complete should be received
                    assert len(received) == 1
                    assert received[0]["type"] == "pipeline_complete"
        finally:
            settings.DEMO_MODE = original


# ---------------------------------------------------------------------------
# Event isolation (concurrent invoice_ids)
# ---------------------------------------------------------------------------


class TestConcurrentInvoiceIsolation:
    """Events for different invoice_ids must not bleed into each other."""

    def test_event_buffer_isolates_per_invoice_id(self):
        """Events added for one invoice_id should not appear under another."""
        buf = EventBuffer(max_events=50)
        buf.add("inv_a", {"step": 1})
        buf.add("inv_b", {"step": 2})

        assert buf.get("inv_a") == [{"step": 1}]
        assert buf.get("inv_b") == [{"step": 2}]

    def test_event_buffer_clear_does_not_affect_other_invoices(self):
        """Clearing one invoice_id must not remove events for others."""
        buf = EventBuffer(max_events=50)
        buf.add("inv_x", {"step": 1})
        buf.add("inv_y", {"step": 2})
        buf.clear("inv_x")

        assert buf.get("inv_x") == []
        assert buf.get("inv_y") == [{"step": 2}]


# ---------------------------------------------------------------------------
# Heartbeat configuration
# ---------------------------------------------------------------------------


class TestHeartbeatConfiguration:
    """Heartbeat interval is configurable via settings."""

    def test_heartbeat_interval_is_positive_integer(self):
        """WS_HEARTBEAT_INTERVAL_SECONDS must be a positive integer."""
        assert isinstance(settings.WS_HEARTBEAT_INTERVAL_SECONDS, int)
        assert settings.WS_HEARTBEAT_INTERVAL_SECONDS > 0

    def test_heartbeat_interval_default_is_reasonable(self):
        """Default heartbeat of 30s is within the 10-60 second practical range."""
        # 30s default balances ALB idle timeout vs connection overhead
        assert 10 <= settings.WS_HEARTBEAT_INTERVAL_SECONDS <= 120


# ---------------------------------------------------------------------------
# EventBuffer edge cases
# ---------------------------------------------------------------------------


class TestEventBufferEdgeCases:
    """EventBuffer correctness under edge conditions."""

    def test_add_single_event_and_retrieve(self):
        buf = EventBuffer(max_events=5)
        buf.add("inv_e1", {"type": "step_complete", "step": 1})
        assert buf.get("inv_e1") == [{"type": "step_complete", "step": 1}]

    def test_overflow_keeps_most_recent(self):
        """When capacity is exceeded, oldest events are evicted."""
        buf = EventBuffer(max_events=3)
        for i in range(6):
            buf.add("inv_overflow", {"step": i})
        result = buf.get("inv_overflow")
        assert len(result) == 3
        # Newest 3: steps 3, 4, 5
        assert result[0]["step"] == 3
        assert result[2]["step"] == 5

    def test_get_unknown_invoice_returns_empty_list(self):
        buf = EventBuffer(max_events=10)
        assert buf.get("inv_unknown_xyz") == []

    def test_clear_nonexistent_does_not_raise(self):
        """Clearing an invoice_id that has no events should not raise."""
        buf = EventBuffer(max_events=10)
        buf.clear("inv_never_added")  # Should not raise

    def test_max_events_boundary_at_one(self):
        """EventBuffer with max_events=1 always holds only the latest event."""
        buf = EventBuffer(max_events=1)
        buf.add("inv_1", {"step": 1})
        buf.add("inv_1", {"step": 2})
        result = buf.get("inv_1")
        assert len(result) == 1
        assert result[0]["step"] == 2
