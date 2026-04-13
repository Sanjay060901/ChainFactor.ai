"""get_credit_score tool: Mock CIBIL credit score lookup by buyer GSTIN.

Determines a credit score and rating from the buyer's GSTIN state code prefix
using deterministic mock rules (real CIBIL/MCA APIs require government registration).

Mock rules (by first 2 chars of GSTIN):
    "27" (Maharashtra) -> score=750, rating="good"
    "29" (Karnataka)   -> score=820, rating="excellent"
    "09" (Uttar Pradesh) -> score=580, rating="fair"
    "07" (Delhi)       -> score=450, rating="poor"
    Others / short / empty -> score=650, rating="average"

Demo mode: Always returns score=750, rating="good" regardless of GSTIN.

Dependencies:
    - strands (@tool decorator)
"""

import logging

from strands import tool

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Mapping of GSTIN 2-char state code prefix -> (score, rating)
_PREFIX_MAP: dict[str, tuple[int, str]] = {
    "27": (750, "good"),  # Maharashtra
    "29": (820, "excellent"),  # Karnataka
    "09": (580, "fair"),  # Uttar Pradesh
    "07": (450, "poor"),  # Delhi
}

# Default result when prefix is not recognised or GSTIN is too short
_DEFAULT_RESULT: dict = {"score": 650, "rating": "average"}


# ---------------------------------------------------------------------------
# Internal implementation (accepts _demo override, no @tool restriction)
# ---------------------------------------------------------------------------


def _get_credit_score_impl(buyer_gstin: str) -> dict:
    """Core logic for credit score lookup."""
    # Guard: GSTIN must be at least 2 chars for a valid state code prefix
    if len(buyer_gstin) < 2:
        logger.info(
            "buyer_gstin %r is too short for prefix lookup, returning default",
            buyer_gstin,
        )
        return dict(_DEFAULT_RESULT)

    prefix = buyer_gstin[:2]
    if prefix in _PREFIX_MAP:
        score, rating = _PREFIX_MAP[prefix]
        logger.info(
            "Credit score for GSTIN prefix %s: score=%d, rating=%s",
            prefix,
            score,
            rating,
        )
        return {"score": score, "rating": rating}

    logger.info("Unknown GSTIN prefix %s, returning default average score", prefix)
    return dict(_DEFAULT_RESULT)


# ---------------------------------------------------------------------------
# Strands @tool  (Pydantic-safe signature -- no leading-underscore params)
# ---------------------------------------------------------------------------


@tool
def _get_credit_score_tool(buyer_gstin: str) -> dict:
    """Look up the mock CIBIL credit score for a buyer identified by their GSTIN.

    Returns a score and rating derived from the GSTIN state code prefix.

    Args:
        buyer_gstin: 15-character GSTIN of the invoice buyer.
    """
    return _get_credit_score_impl(buyer_gstin)


# ---------------------------------------------------------------------------
# Public export: callable both as a plain function (with _demo) and as a
# Strands tool (via _get_credit_score_tool).  Tests and direct Python callers
# use this name; agent dispatch uses the tool object stored below.
# ---------------------------------------------------------------------------


class _CreditScoreTool:
    """Thin wrapper that exposes _demo override for tests while delegating
    Strands tool protocol to the decorated tool object.

    Attributes on the wrapped Strands tool (tool_name, tool_spec, __call__
    with tool-use dict, etc.) are forwarded so agent registration works
    transparently.
    """

    def __call__(self, buyer_gstin: str) -> dict:
        return _get_credit_score_impl(buyer_gstin)

    # Forward Strands tool protocol attributes to the decorated tool
    def __getattr__(self, item):
        return getattr(_get_credit_score_tool, item)


get_credit_score = _CreditScoreTool()
