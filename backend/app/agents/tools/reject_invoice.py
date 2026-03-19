"""reject_invoice tool: Records an invoice rejection decision.

Logs the rejection decision with reason, risk score, and fraud flags.
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
def reject_invoice(
    invoice_id: str,
    reason: str,
    risk_score: int,
    fraud_flags: list,
) -> dict:
    """Record an invoice rejection decision.

    Creates a decision record with the rejection reason, risk score, and
    list of fraud flags that contributed to the rejection.

    Args:
        invoice_id: Unique identifier for the invoice being rejected.
        reason: Human-readable explanation for the rejection decision.
        risk_score: Calculated risk score (0-100, higher = safer).
        fraud_flags: List of fraud flags that triggered the rejection.
    """
    timestamp = datetime.now(timezone.utc).isoformat()

    decision_record = {
        "decision": "rejected",
        "invoice_id": invoice_id,
        "reason": reason,
        "risk_score": risk_score,
        "fraud_flags": list(fraud_flags),
        "timestamp": timestamp,
    }

    if settings.DEMO_MODE:
        logger.info("DEMO_MODE: reject_invoice for %s", invoice_id)
    else:
        logger.info(
            "Invoice %s REJECTED: risk_score=%d, fraud_flags=%s, reason=%s",
            invoice_id,
            risk_score,
            fraud_flags,
            reason,
        )

    return decision_record
