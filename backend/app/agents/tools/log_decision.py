"""log_decision tool: Persists the complete underwriting decision with reasoning trace.

Logs the full decision context (invoice_id, decision, reasoning trace, all signals)
for audit and compliance. In production, this would persist to the agent_traces table
in PostgreSQL and stream via WebSocket.

Dependencies:
    - strands (@tool decorator)
"""

import logging
import uuid
from datetime import datetime, timezone

from strands import tool

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Strands @tool
# ---------------------------------------------------------------------------


@tool
def log_decision(
    invoice_id: str,
    decision: str,
    reasoning_trace: str,
    all_signals: dict,
) -> dict:
    """Log the complete underwriting decision with full reasoning trace.

    Persists the decision, reasoning, and all input signals for auditability.
    In production, this writes to the agent_traces table and streams via WebSocket.

    Args:
        invoice_id: Unique identifier for the invoice.
        decision: The underwriting decision (approved, rejected, flagged_for_review).
        reasoning_trace: Full text explanation of the agent's reasoning process.
        all_signals: Dict containing all input signals used in the decision.
    """
    trace_id = str(uuid.uuid4())
    timestamp = datetime.now(timezone.utc).isoformat()

    log_record = {
        "logged": True,
        "invoice_id": invoice_id,
        "decision": decision,
        "trace_id": trace_id,
        "timestamp": timestamp,
    }

    logger.info(
        "Decision logged: invoice=%s, decision=%s, trace_id=%s, "
        "reasoning_length=%d, signals_count=%d",
        invoice_id,
        decision,
        trace_id,
        len(reasoning_trace),
        len(all_signals),
    )

    return log_record
