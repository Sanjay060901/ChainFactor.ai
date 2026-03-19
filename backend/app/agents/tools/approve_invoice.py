"""approve_invoice tool: Records an invoice approval decision.

Logs the approval decision with reason, risk score, and confidence.
In production, this would update the invoice status in PostgreSQL and
persist to the underwriting_decisions table.

Dependencies:
    - strands (@tool decorator)
    - app.config.settings (DEMO_MODE)
"""

import logging
from datetime import datetime, timezone

from strands import tool

from app.config import settings

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Strands @tool
# ---------------------------------------------------------------------------


@tool
def approve_invoice(
    invoice_id: str,
    reason: str,
    risk_score: int,
    confidence: float,
) -> dict:
    """Record an invoice approval decision.

    Creates a decision record with the approval reason, risk score, and
    confidence level. In production, this updates the invoice status in the
    database.

    Args:
        invoice_id: Unique identifier for the invoice being approved.
        reason: Human-readable explanation for the approval decision.
        risk_score: Calculated risk score (0-100, higher = safer).
        confidence: Confidence in the decision (0.0 to 1.0).
    """
    timestamp = datetime.now(timezone.utc).isoformat()

    decision_record = {
        "decision": "approved",
        "invoice_id": invoice_id,
        "reason": reason,
        "risk_score": risk_score,
        "confidence": confidence,
        "timestamp": timestamp,
    }

    if settings.DEMO_MODE:
        logger.info("DEMO_MODE: approve_invoice for %s", invoice_id)
    else:
        logger.info(
            "Invoice %s APPROVED: risk_score=%d, confidence=%.2f, reason=%s",
            invoice_id,
            risk_score,
            confidence,
            reason,
        )

    return decision_record
