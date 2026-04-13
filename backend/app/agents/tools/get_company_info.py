"""get_company_info tool: Mock MCA company info lookup by GSTIN state code.

Simulates Ministry of Corporate Affairs (MCA) API responses using deterministic
rules keyed on the GSTIN state code prefix (first 2 characters).

Mock rules (deterministic by state code prefix):
- "27" (Maharashtra): status="active", incorporated="2015", paid_up_capital=100_000_000.0
- "29" (Karnataka):   status="active", incorporated="2018", paid_up_capital=50_000_000.0
- "09" (Uttar Pradesh): status="active", incorporated="2020", paid_up_capital=10_000_000.0
- "07" (Delhi):       status="dormant", incorporated="2010", paid_up_capital=5_000_000.0
- Others/empty/short: status="active", incorporated="2019", paid_up_capital=25_000_000.0

Dependencies:
    - strands (@tool decorator)
"""

import logging

from strands import tool

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Deterministic mock profiles keyed on GSTIN state code (first 2 chars)
_STATE_PROFILES: dict[str, dict] = {
    "27": {
        "status": "active",
        "incorporated": "2015",
        "paid_up_capital": 100_000_000.0,
    },
    "29": {
        "status": "active",
        "incorporated": "2018",
        "paid_up_capital": 50_000_000.0,
    },
    "09": {
        "status": "active",
        "incorporated": "2020",
        "paid_up_capital": 10_000_000.0,
    },
    "07": {
        "status": "dormant",
        "incorporated": "2010",
        "paid_up_capital": 5_000_000.0,
    },
}

# Default profile for any unrecognised or too-short GSTIN
_DEFAULT_PROFILE: dict = {
    "status": "active",
    "incorporated": "2019",
    "paid_up_capital": 25_000_000.0,
}


# ---------------------------------------------------------------------------
# Core logic (no decorator -- safe for direct calls and unit tests)
# ---------------------------------------------------------------------------


def _lookup_company_info(company_gstin: str) -> dict:
    """Look up mock company info for a given GSTIN."""
    # State code is the first 2 characters of a valid GSTIN
    state_code = company_gstin[:2] if len(company_gstin) >= 2 else ""
    profile = _STATE_PROFILES.get(state_code, _DEFAULT_PROFILE)

    logger.info(
        "Company info lookup: GSTIN=%s state_code=%s status=%s",
        company_gstin,
        state_code,
        profile["status"],
    )

    return dict(profile)


# ---------------------------------------------------------------------------
# Strands @tool (only company_gstin is exposed to the tool schema)
# ---------------------------------------------------------------------------


@tool
def get_company_info_tool(company_gstin: str) -> dict:
    """Retrieve mock company incorporation and financial info from the MCA registry.

    Uses deterministic rules based on the GSTIN state code prefix (first 2 chars)
    to simulate MCA API responses without requiring government-registered API access.

    Args:
        company_gstin: 15-character GSTIN of the company to look up.
    """
    return _lookup_company_info(company_gstin)


# ---------------------------------------------------------------------------
# Public alias
# ---------------------------------------------------------------------------


def get_company_info(company_gstin: str) -> dict:
    """Public entry point for company info lookup.

    Args:
        company_gstin: 15-character GSTIN of the company to look up.

    Returns:
        dict with keys: status (str), incorporated (str), paid_up_capital (float).
    """
    return _lookup_company_info(company_gstin)
