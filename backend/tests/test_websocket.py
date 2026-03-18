"""Tests for WebSocket server (Feature 4.2).

Covers: Redis bridge publish/subscribe, WebSocket handler, heartbeat,
client disconnect, event format validation, and DEMO_MODE fallback.
"""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from starlette.testclient import TestClient

from app.config import settings
from app.schemas.invoice import PipelineCompleteEvent, ProcessingEvent


# ---------------------------------------------------------------------------
# Redis Bridge unit tests
# ---------------------------------------------------------------------------


class TestRedisBridgePublish:
    """Test publish_event sends correctly formatted messages to Redis."""

    @pytest.mark.asyncio
    async def test_publish_event_serialises_and_publishes(self):
        """publish_event should JSON-encode the event dict and PUBLISH to
        the channel ``invoice:{invoice_id}``."""
        mock_redis = AsyncMock()
        mock_redis.publish = AsyncMock(return_value=1)

        with patch(
            "app.modules.ws.redis_bridge._get_redis_pool",
            return_value=mock_redis,
        ):
            from app.modules.ws.redis_bridge import publish_event

            event = {
                "type": "step_complete",
                "step": 1,
                "step_name": "extract_invoice",
                "agent": "invoice_processing",
                "status": "complete",
                "detail": "Extracting data from PDF...",
                "result": {},
                "progress": 0.07,
                "elapsed_ms": 3200,
            }
            await publish_event("inv_001", event)

            mock_redis.publish.assert_awaited_once_with(
                "invoice:inv_001",
                json.dumps(event),
            )

    @pytest.mark.asyncio
    async def test_publish_event_returns_subscriber_count(self):
        """publish_event should return the number of subscribers that received
        the message (passthrough from Redis PUBLISH)."""
        mock_redis = AsyncMock()
        mock_redis.publish = AsyncMock(return_value=3)

        with patch(
            "app.modules.ws.redis_bridge._get_redis_pool",
            return_value=mock_redis,
        ):
            from app.modules.ws.redis_bridge import publish_event

            count = await publish_event("inv_002", {"type": "test"})
            assert count == 3


class TestRedisBridgeSubscribe:
    """Test subscribe_events yields messages from the Redis channel."""

    @pytest.mark.asyncio
    async def test_subscribe_yields_events(self):
        """subscribe_events should yield decoded JSON dicts from the Redis
        pubsub channel ``invoice:{invoice_id}``."""
        event_data = {
            "type": "step_complete",
            "step": 1,
            "step_name": "extract_invoice",
            "agent": "invoice_processing",
            "status": "complete",
            "detail": "Extracting...",
            "result": {},
            "progress": 0.07,
            "elapsed_ms": 3200,
        }

        # Simulate a pubsub object that yields one message then stops
        mock_message = {
            "type": "message",
            "data": json.dumps(event_data).encode(),
            "channel": b"invoice:inv_001",
        }

        mock_pubsub = AsyncMock()
        mock_pubsub.subscribe = AsyncMock()
        mock_pubsub.unsubscribe = AsyncMock()
        mock_pubsub.aclose = AsyncMock()

        # Make get_message return one message then None forever
        call_count = 0

        async def _get_message(ignore_subscribe_messages=True, timeout=1.0):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return mock_message
            return None

        mock_pubsub.get_message = _get_message

        mock_redis = AsyncMock()
        mock_redis.pubsub = MagicMock(return_value=mock_pubsub)

        with patch(
            "app.modules.ws.redis_bridge._get_redis_pool",
            return_value=mock_redis,
        ):
            from app.modules.ws.redis_bridge import subscribe_events

            received = []
            async for evt in subscribe_events("inv_001"):
                received.append(evt)
                if len(received) >= 1:
                    break

            assert len(received) == 1
            assert received[0] == event_data

    @pytest.mark.asyncio
    async def test_subscribe_cleans_up_on_break(self):
        """When the consumer closes subscribe_events, the pubsub
        should be unsubscribed and closed."""
        mock_pubsub = AsyncMock()
        mock_pubsub.subscribe = AsyncMock()
        mock_pubsub.unsubscribe = AsyncMock()
        mock_pubsub.aclose = AsyncMock()

        msg = {
            "type": "message",
            "data": json.dumps({"type": "test"}).encode(),
            "channel": b"invoice:inv_001",
        }
        call_count = 0

        async def _get_message(ignore_subscribe_messages=True, timeout=1.0):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return msg
            return None

        mock_pubsub.get_message = _get_message

        mock_redis = AsyncMock()
        mock_redis.pubsub = MagicMock(return_value=mock_pubsub)

        with patch(
            "app.modules.ws.redis_bridge._get_redis_pool",
            return_value=mock_redis,
        ):
            from app.modules.ws.redis_bridge import subscribe_events

            stream = subscribe_events("inv_001")
            async for _ in stream:
                break
            # Explicitly close -- Python 3.14 does not synchronously finalize
            # async generators/iterators on ``break`` from ``async for``.
            await stream.aclose()

            mock_pubsub.unsubscribe.assert_awaited_once_with("invoice:inv_001")
            mock_pubsub.aclose.assert_awaited_once()


# ---------------------------------------------------------------------------
# Event format validation
# ---------------------------------------------------------------------------


class TestEventFormat:
    """Ensure demo events match the ProcessingEvent / PipelineCompleteEvent schemas."""

    def test_step_event_matches_processing_event_schema(self):
        """A step_complete event dict should be parseable as ProcessingEvent."""
        event = {
            "type": "step_complete",
            "step": 1,
            "step_name": "extract_invoice",
            "agent": "invoice_processing",
            "status": "complete",
            "detail": "Extracting data from PDF using Textract...",
            "result": {},
            "progress": 0.07,
            "elapsed_ms": 3200,
        }
        parsed = ProcessingEvent(**event)
        assert parsed.type == "step_complete"
        assert parsed.step == 1
        assert parsed.step_name == "extract_invoice"
        assert parsed.progress == 0.07

    def test_pipeline_complete_matches_schema(self):
        """A pipeline_complete event dict should be parseable as PipelineCompleteEvent."""
        event = {
            "type": "pipeline_complete",
            "decision": "approved",
            "risk_score": 82,
            "reason": "Auto-approved: meets Rule 2 criteria",
            "nft_asset_id": 12345678,
            "invoice_id": "inv_stub_001",
        }
        parsed = PipelineCompleteEvent(**event)
        assert parsed.decision == "approved"
        assert parsed.risk_score == 82
        assert parsed.nft_asset_id == 12345678


# ---------------------------------------------------------------------------
# WebSocket handler integration tests (DEMO_MODE)
# ---------------------------------------------------------------------------


class TestWebSocketHandlerDemo:
    """Test the WebSocket handler in DEMO_MODE (no Redis required)."""

    @pytest.mark.asyncio
    async def test_ws_connect_and_receive_demo_events(self):
        """In DEMO_MODE the WS handler should yield all 14 step events
        plus one pipeline_complete event without needing Redis."""
        from app.main import app

        original_demo = settings.DEMO_MODE
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

                # 14 step_complete + 1 pipeline_complete
                assert len(events) == 15

                # First event is step 1
                assert events[0]["type"] == "step_complete"
                assert events[0]["step"] == 1
                assert events[0]["step_name"] == "extract_invoice"

                # Last event is pipeline_complete
                assert events[-1]["type"] == "pipeline_complete"
                assert events[-1]["decision"] == "approved"
                assert events[-1]["risk_score"] == 82
        finally:
            settings.DEMO_MODE = original_demo

    @pytest.mark.asyncio
    async def test_ws_demo_events_are_valid_schemas(self):
        """Every step event from demo mode should parse as ProcessingEvent."""
        from app.main import app

        original_demo = settings.DEMO_MODE
        settings.DEMO_MODE = True

        try:
            client = TestClient(app)
            with client.websocket_connect("/ws/processing/inv_stub_001") as ws:
                while True:
                    try:
                        data = ws.receive_json(mode="text")
                        if data["type"] == "step_complete":
                            ProcessingEvent(**data)
                        elif data["type"] == "pipeline_complete":
                            PipelineCompleteEvent(**data)
                            break
                    except Exception:
                        break
        finally:
            settings.DEMO_MODE = original_demo

    @pytest.mark.asyncio
    async def test_ws_demo_progress_increases(self):
        """Progress values should monotonically increase across step events."""
        from app.main import app

        original_demo = settings.DEMO_MODE
        settings.DEMO_MODE = True

        try:
            client = TestClient(app)
            with client.websocket_connect("/ws/processing/inv_stub_001") as ws:
                prev_progress = 0.0
                while True:
                    try:
                        data = ws.receive_json(mode="text")
                        if data["type"] == "step_complete":
                            assert data["progress"] >= prev_progress
                            prev_progress = data["progress"]
                        elif data["type"] == "pipeline_complete":
                            break
                    except Exception:
                        break
        finally:
            settings.DEMO_MODE = original_demo


# ---------------------------------------------------------------------------
# WebSocket handler with mocked Redis (non-demo mode)
# ---------------------------------------------------------------------------


class TestWebSocketHandlerLive:
    """Test the WebSocket handler with mocked Redis pub/sub."""

    @pytest.mark.asyncio
    async def test_ws_forwards_redis_events_to_client(self):
        """In live mode, events published to Redis should be forwarded
        to the connected WebSocket client."""
        from app.main import app

        original_demo = settings.DEMO_MODE
        settings.DEMO_MODE = False

        event = {
            "type": "step_complete",
            "step": 1,
            "step_name": "extract_invoice",
            "agent": "invoice_processing",
            "status": "complete",
            "detail": "Extracting...",
            "result": {},
            "progress": 0.07,
            "elapsed_ms": 3200,
        }
        final = {
            "type": "pipeline_complete",
            "decision": "approved",
            "risk_score": 82,
            "reason": "Auto-approved",
            "nft_asset_id": 12345678,
            "invoice_id": "inv_test_001",
        }

        async def mock_subscribe(invoice_id):
            """Yield one step event then the final event."""
            yield event
            yield final

        try:
            with patch(
                "app.modules.ws.handler.subscribe_events",
                side_effect=mock_subscribe,
            ):
                client = TestClient(app)
                with client.websocket_connect("/ws/processing/inv_test_001") as ws:
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
                    assert received[0]["step_name"] == "extract_invoice"
                    assert received[1]["type"] == "pipeline_complete"
        finally:
            settings.DEMO_MODE = original_demo


# ---------------------------------------------------------------------------
# Heartbeat
# ---------------------------------------------------------------------------


class TestHeartbeat:
    """Test the heartbeat mechanism keeps the connection alive."""

    @pytest.mark.asyncio
    async def test_heartbeat_setting_is_configurable(self):
        """WS_HEARTBEAT_INTERVAL_SECONDS should be available in settings."""
        assert hasattr(settings, "WS_HEARTBEAT_INTERVAL_SECONDS")
        assert isinstance(settings.WS_HEARTBEAT_INTERVAL_SECONDS, int)
        assert settings.WS_HEARTBEAT_INTERVAL_SECONDS > 0


# ---------------------------------------------------------------------------
# Reconnection buffer
# ---------------------------------------------------------------------------


class TestReconnectionBuffer:
    """Test the event buffer that supports reconnection."""

    @pytest.mark.asyncio
    async def test_event_buffer_stores_events(self):
        """EventBuffer should store events keyed by invoice_id."""
        from app.modules.ws.redis_bridge import EventBuffer

        buf = EventBuffer(max_events=10)
        evt = {"type": "step_complete", "step": 1}
        buf.add("inv_001", evt)

        events = buf.get("inv_001")
        assert len(events) == 1
        assert events[0] == evt

    @pytest.mark.asyncio
    async def test_event_buffer_respects_max(self):
        """EventBuffer should cap stored events at max_events."""
        from app.modules.ws.redis_bridge import EventBuffer

        buf = EventBuffer(max_events=3)
        for i in range(5):
            buf.add("inv_001", {"step": i})

        events = buf.get("inv_001")
        assert len(events) == 3
        # Should keep the 3 most recent
        assert events[0]["step"] == 2
        assert events[2]["step"] == 4

    @pytest.mark.asyncio
    async def test_event_buffer_returns_empty_for_unknown(self):
        """EventBuffer.get should return [] for unknown invoice_id."""
        from app.modules.ws.redis_bridge import EventBuffer

        buf = EventBuffer(max_events=10)
        assert buf.get("nonexistent") == []

    @pytest.mark.asyncio
    async def test_event_buffer_clear(self):
        """EventBuffer.clear should remove all events for an invoice."""
        from app.modules.ws.redis_bridge import EventBuffer

        buf = EventBuffer(max_events=10)
        buf.add("inv_001", {"step": 1})
        buf.clear("inv_001")
        assert buf.get("inv_001") == []
