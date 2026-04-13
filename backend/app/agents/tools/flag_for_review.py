"""flag_for_review tool: Records a flag-for-review decision on an invoice.

Logs that an invoice needs manual review, with reason, discrepancies, and
risk score. In production, this would update the invoice status in PostgreSQL,
persist to the underwriting_decisions table, and notify the review queue.

Dependencies:
    - strands (@tool decorator)
"""

import logging
from datetime import datetime, timezone

from strands import tool

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Strands @tool
# ---------------------------------------------------------------------------


@tool
def flag_for_review(
    invoice_id: str,
    reason: str,
    discrepancies: list,
    risk_score: int,
) -> dict:
    """Flag an invoice for manual review.

    Creates a decision record indicating the invoice requires human review
    due to borderline signals, minor discrepancies, or seller rule conflicts.

    Args:
        invoice_id: Unique identifier for the invoice being flagged.
        reason: Human-readable explanation for why review is needed.
        discrepancies: List of specific discrepancies or concerns found.
        risk_score: Calculated risk score (0-100, higher = safer).
    """
    timestamp = datetime.now(timezone.utc).isoformat()

    decision_record = {
        "decision": "flagged_for_review",
        "invoice_id": invoice_id,
        "reason": reason,
        "discrepancies": list(discrepancies),
        "risk_score": risk_score,
        "timestamp": timestamp,
    }

    logger.info(
        "Invoice %s FLAGGED FOR REVIEW: risk_score=%d, discrepancies=%s, reason=%s",
        invoice_id,
        risk_score,
        discrepancies,
        reason,
    )

    return decision_record
