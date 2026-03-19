"""ARC-69 metadata builder for invoice NFTs.

ARC-69 spec: metadata is a JSON object stored in the note field of the
most recent asset config (acfg) transaction for an ASA.

Reference: https://arc.algorand.foundation/ARCs/arc-0069
"""

import json
from datetime import datetime, timezone


# Required top-level keys per ARC-69
ARC69_STANDARD_KEY = "standard"
ARC69_STANDARD_VALUE = "arc69"

# Required properties for ChainFactor invoice NFTs
REQUIRED_PROPERTIES = frozenset(
    {
        "invoice_id",
        "seller",
        "buyer",
        "amount_inr",
        "risk_score",
        "risk_level",
        "decision",
        "invoice_date",
        "due_date",
        "verified_at",
        "platform",
        "network",
    }
)


def build_arc69_metadata(
    invoice_id: str,
    seller_name: str,
    buyer_name: str,
    amount: float,
    risk_score: int,
    risk_level: str,
    decision: str,
    invoice_date: str,
    due_date: str,
) -> str:
    """Build ARC-69 compliant JSON metadata for an invoice NFT.

    ARC-69 spec: metadata is a JSON object in the note field of the
    most recent asset config transaction.

    Args:
        invoice_id: UUID of the invoice.
        seller_name: Name of the selling company.
        buyer_name: Name of the buying company.
        amount: Invoice amount in INR.
        risk_score: Computed risk score (0-100).
        risk_level: Risk level label (low/medium/high/critical).
        decision: Underwriting decision (approved/rejected/review).
        invoice_date: Invoice issue date (ISO format string).
        due_date: Invoice due date (ISO format string).

    Returns:
        Compact JSON string (no whitespace) suitable for the note field.
    """
    metadata = {
        "standard": ARC69_STANDARD_VALUE,
        "description": f"ChainFactor AI verified invoice #{invoice_id}",
        "mime_type": "application/json",
        "properties": {
            "invoice_id": invoice_id,
            "seller": seller_name,
            "buyer": buyer_name,
            "amount_inr": amount,
            "risk_score": risk_score,
            "risk_level": risk_level,
            "decision": decision,
            "invoice_date": invoice_date,
            "due_date": due_date,
            "verified_at": datetime.now(timezone.utc).isoformat(),
            "platform": "ChainFactor AI",
            "network": "algorand-testnet",
        },
    }
    return json.dumps(metadata, separators=(",", ":"))
