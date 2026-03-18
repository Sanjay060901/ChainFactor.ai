"""WebSocket module -- real-time agent trace streaming over WebSocket and SSE.

Architecture:
  Agent tools publish events via publish_event() -> Redis pub/sub channel
  WebSocket handler subscribes to the channel and forwards events to the client
  SSE endpoint provides a fallback for environments where WebSocket is blocked

In DEMO_MODE (no Redis, no agents), the handler streams pre-computed events
for 3 stub invoices without any external dependencies.
"""
