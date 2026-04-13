"""get_seller_rules tool: Retrieves seller-defined auto-approval rules.

Mock implementation: deterministic results based on seller_id prefix.

Mock rules (by seller_id prefix):
    "seller_1": permissive (max_amount=1000000, min_risk_score=30, min_cibil=600,
                max_fraud_flags=2, auto_approve=true)
    "seller_2": strict (max_amount=200000, min_risk_score=20, min_cibil=750,
                max_fraud_flags=0, auto_approve=true)
    Others:     moderate defaults (max_amount=500000, min_risk_score=40, min_cibil=650,
                max_fraud_flags=1, auto_approve=true)

Demo mode: returns permissive rules (same as seller_1).

Dependencies:
    - strands (@tool decorator)
"""

import logging

from strands import tool

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_PERMISSIVE_RULES: dict = {
    "max_amount": 1000000.0,
    "min_risk_score": 30,
    "min_cibil_score": 600,
    "max_fraud_flags": 2,
    "auto_approve_enabled": True,
}

_STRICT_RULES: dict = {
    "max_amount": 200000.0,
    "min_risk_score": 20,
    "min_cibil_score": 750,
    "max_fraud_flags": 0,
    "auto_approve_enabled": True,
}

_MODERATE_RULES: dict = {
    "max_amount": 500000.0,
    "min_risk_score": 40,
    "min_cibil_score": 650,
    "max_fraud_flags": 1,
    "auto_approve_enabled": True,
}


# ---------------------------------------------------------------------------
# Internal implementation (pure logic, no Strands dependency)
# ---------------------------------------------------------------------------


def _resolve_seller_rules(seller_id: str) -> dict:
    """Core seller rules lookup logic, separated from the Strands decorator."""
    if seller_id.startswith("seller_1"):
        logger.info("Seller %s matched permissive rules (seller_1*)", seller_id)
        return dict(_PERMISSIVE_RULES)

    if seller_id.startswith("seller_2"):
        logger.info("Seller %s matched strict rules (seller_2*)", seller_id)
        return dict(_STRICT_RULES)

    logger.info("Seller %s using moderate default rules", seller_id)
    return dict(_MODERATE_RULES)


# ---------------------------------------------------------------------------
# Strands @tool  (registered with the agent; no leading-underscore params)
# ---------------------------------------------------------------------------


@tool
def _get_seller_rules_tool(seller_id: str) -> dict:
    """Retrieve seller-defined auto-approval rules for underwriting decisions.

    Returns thresholds for max invoice amount, minimum risk score, minimum
    CIBIL score, maximum fraud flags, and whether auto-approve is enabled.

    Args:
        seller_id: Unique identifier for the seller.
    """
    return _resolve_seller_rules(seller_id)


# ---------------------------------------------------------------------------
# Public callable (used by tests and by agent tool list)
# ---------------------------------------------------------------------------


def get_seller_rules(seller_id: str) -> dict:
    """Retrieve seller-defined auto-approval rules for underwriting decisions.

    Args:
        seller_id: Unique identifier for the seller.

    Returns:
        Dict with max_amount, min_risk_score, min_cibil_score,
        max_fraud_flags, auto_approve_enabled.
    """
    return _resolve_seller_rules(seller_id)
