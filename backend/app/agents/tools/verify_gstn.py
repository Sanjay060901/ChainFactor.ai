"""verify_gstn tool: Mock GSTIN verification for Indian GST registrations.

Mock implementation: deterministic results based on the GSTIN state code prefix
(first 2 characters). No external API calls are made.

Mock rules (by GSTIN prefix):
    "27" (Maharashtra): active, not blocklisted
    "29" (Karnataka):   active, not blocklisted
    "09" (Uttar Pradesh): active, not blocklisted (slow payer is buyer_intel's concern)
    "07" (Delhi): INACTIVE, not blocklisted
    Others / short / empty: active, not blocklisted (safe default)

verified = True if BOTH seller and buyer are active AND neither is blocklisted.
status = "active" if verified, else "inactive".

Demo mode: returns all-active, verified=True regardless of GSTINs.

Dependencies:
    - strands (@tool decorator)
"""

import logging

from strands import tool

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# State code prefixes that are INACTIVE (cannot transact)
_INACTIVE_PREFIXES: frozenset[str] = frozenset({"07"})  # Delhi (mock rule)

# State code prefixes that are on the blocklist
_BLOCKLISTED_PREFIXES: frozenset[str] = frozenset()  # none in current mock


# ---------------------------------------------------------------------------
# Internal implementation (pure logic, no Strands dependency)
# ---------------------------------------------------------------------------


def _gstin_status(gstin: str) -> tuple[bool, bool]:
    """Return (is_active, is_blocklisted) for a single GSTIN.

    Args:
        gstin: The GSTIN string to evaluate (any length).

    Returns:
        Tuple of (is_active, is_blocklisted).
    """
    # Cannot extract a 2-char prefix from a short/empty string -> default active
    if len(gstin) < 2:
        return True, False

    prefix = gstin[:2]
    is_active = prefix not in _INACTIVE_PREFIXES
    is_blocklisted = prefix in _BLOCKLISTED_PREFIXES

    return is_active, is_blocklisted


def _resolve_gstin_verification(
    seller_gstin: str, buyer_gstin: str
) -> dict:
    """Core GSTIN verification logic, separated from the Strands decorator."""
    seller_active, seller_blocklisted = _gstin_status(seller_gstin)
    buyer_active, buyer_blocklisted = _gstin_status(buyer_gstin)

    verified = (
        seller_active
        and buyer_active
        and not seller_blocklisted
        and not buyer_blocklisted
    )
    status = "active" if verified else "inactive"

    logger.info(
        "GSTIN verification: seller=%s(active=%s) buyer=%s(active=%s) verified=%s",
        seller_gstin,
        seller_active,
        buyer_gstin,
        buyer_active,
        verified,
    )

    return {
        "verified": verified,
        "status": status,
        "details": {
            "seller_gstin_active": seller_active,
            "buyer_gstin_active": buyer_active,
            "seller_on_blocklist": seller_blocklisted,
            "buyer_on_blocklist": buyer_blocklisted,
        },
    }


# ---------------------------------------------------------------------------
# Strands @tool  (registered with the agent; no leading-underscore params)
# ---------------------------------------------------------------------------


@tool
def _verify_gstn_tool(seller_gstin: str, buyer_gstin: str) -> dict:
    """Verify GSTIN registration status for both seller and buyer.

    Uses a deterministic mock lookup keyed on the first 2 characters (state code)
    of each GSTIN.

    Args:
        seller_gstin: The 15-character GST Identification Number of the seller.
        buyer_gstin: The 15-character GST Identification Number of the buyer.
    """
    return _resolve_gstin_verification(seller_gstin, buyer_gstin)


# ---------------------------------------------------------------------------
# Public callable (used by tests and by agent tool list)
# ---------------------------------------------------------------------------


def verify_gstn(seller_gstin: str, buyer_gstin: str) -> dict:
    """Verify GSTIN registration status for both seller and buyer.

    Args:
        seller_gstin: The 15-character GST Identification Number of the seller.
        buyer_gstin: The 15-character GST Identification Number of the buyer.

    Returns:
        Dict with keys:
            verified (bool): True if both GSTINs are active and not blocklisted.
            status (str): "active" if verified, else "inactive".
            details (dict): per-GSTIN active and blocklist flags.
    """
    return _resolve_gstin_verification(seller_gstin, buyer_gstin)
