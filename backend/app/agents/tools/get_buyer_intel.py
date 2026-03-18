"""get_buyer_intel tool: Retrieves payment history and reliability data for a buyer.

Mock implementation: deterministic results based on the GSTIN state code prefix
(first 2 characters). No external API calls are made.

Mock rules (by GSTIN prefix):
    "27" (Maharashtra): reliable, avg_days=28, previous_count=8
    "29" (Karnataka):   reliable, avg_days=35, previous_count=12
    "09" (Uttar Pradesh): slow_payer, avg_days=65, previous_count=3
    Others / empty / short: new_buyer, avg_days=0, previous_count=0

Demo mode: always returns reliable buyer (payment_history="reliable", avg_days=28,
previous_count=8) regardless of GSTIN.

Dependencies:
    - strands (@tool decorator)
    - app.config.settings (DEMO_MODE)
"""

import logging

from strands import tool

from app.config import settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Pre-computed demo result shown when DEMO_MODE is active
_DEMO_RESULT: dict = {
    "payment_history": "reliable",
    "avg_days": 28,
    "previous_count": 8,
}

# Lookup table keyed by 2-character GSTIN state code
_GSTIN_PREFIX_MAP: dict[str, dict] = {
    "27": {"payment_history": "reliable", "avg_days": 28, "previous_count": 8},
    "29": {"payment_history": "reliable", "avg_days": 35, "previous_count": 12},
    "09": {"payment_history": "slow_payer", "avg_days": 65, "previous_count": 3},
}

# Default result for unknown, empty, or malformed GSTINs
_NEW_BUYER_RESULT: dict = {
    "payment_history": "new_buyer",
    "avg_days": 0,
    "previous_count": 0,
}


# ---------------------------------------------------------------------------
# Internal implementation (pure logic, no Strands dependency)
# ---------------------------------------------------------------------------


def _resolve_buyer_intel(buyer_gstin: str, use_demo: bool) -> dict:
    """Core buyer intel logic, separated from the Strands decorator.

    Args:
        buyer_gstin: The 15-character GST Identification Number of the buyer.
        use_demo: Whether to return the demo (pre-computed) result.

    Returns:
        Dict with payment_history (str), avg_days (int), previous_count (int).
    """
    if use_demo:
        logger.info(
            "DEMO_MODE: returning pre-computed buyer intel for GSTIN %s", buyer_gstin
        )
        return dict(_DEMO_RESULT)

    # Need at least 2 chars to extract the state code prefix
    if len(buyer_gstin) < 2:
        logger.info(
            "GSTIN '%s' is too short to extract state code; returning new_buyer",
            buyer_gstin,
        )
        return dict(_NEW_BUYER_RESULT)

    state_code = buyer_gstin[:2]
    result = _GSTIN_PREFIX_MAP.get(state_code, _NEW_BUYER_RESULT)

    logger.info(
        "Buyer intel for GSTIN %s (prefix=%s): payment_history=%s, avg_days=%d",
        buyer_gstin,
        state_code,
        result["payment_history"],
        result["avg_days"],
    )

    return dict(result)


# ---------------------------------------------------------------------------
# Strands @tool  (registered with the agent; no leading-underscore params)
# ---------------------------------------------------------------------------


@tool
def _get_buyer_intel_tool(buyer_gstin: str) -> dict:
    """Retrieve payment history and buyer reliability data for a given GSTIN.

    Uses a deterministic mock lookup keyed on the first 2 characters (state code)
    of the GSTIN. In DEMO_MODE, always returns a reliable buyer profile.

    Args:
        buyer_gstin: The 15-character GST Identification Number of the buyer.
    """
    return _resolve_buyer_intel(buyer_gstin, use_demo=settings.DEMO_MODE)


# ---------------------------------------------------------------------------
# Public callable (used by tests and by agent tool list)
# Accepts an optional _demo override so tests can force real/demo paths
# without changing global settings.
# ---------------------------------------------------------------------------


def get_buyer_intel(buyer_gstin: str, _demo: bool = None) -> dict:
    """Retrieve payment history and buyer reliability data for a given GSTIN.

    Wraps _get_buyer_intel_tool with a _demo override for testability.

    Args:
        buyer_gstin: The 15-character GST Identification Number of the buyer.
        _demo: Override for DEMO_MODE. True forces demo path, False forces real
               logic, None defers to settings.DEMO_MODE.

    Returns:
        Dict with keys: payment_history (str), avg_days (int), previous_count (int).
    """
    use_demo = settings.DEMO_MODE if _demo is None else _demo
    return _resolve_buyer_intel(buyer_gstin, use_demo=use_demo)
