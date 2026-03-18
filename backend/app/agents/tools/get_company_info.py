"""get_company_info tool: Mock MCA company info lookup by GSTIN state code.

Simulates Ministry of Corporate Affairs (MCA) API responses using deterministic
rules keyed on the GSTIN state code prefix (first 2 characters).

Mock rules (deterministic by state code prefix):
- "27" (Maharashtra): status="active", incorporated="2015", paid_up_capital=100_000_000.0
- "29" (Karnataka):   status="active", incorporated="2018", paid_up_capital=50_000_000.0
- "09" (Uttar Pradesh): status="active", incorporated="2020", paid_up_capital=10_000_000.0
- "07" (Delhi):       status="dormant", incorporated="2010", paid_up_capital=5_000_000.0
- Others/empty/short: status="active", incorporated="2019", paid_up_capital=25_000_000.0

DEMO_MODE: Always returns the Maharashtra active company profile.

Design note:
    The Strands @tool decorator builds a Pydantic model from the function
    signature, and Pydantic rejects field names that start with an underscore.
    To allow the test-visible _demo override parameter without exposing it to
    the Strands tool schema, the implementation is split into:
      - _lookup_company_info(): pure logic function (no decorator) that accepts
        company_gstin + _demo and is callable in unit tests.
      - get_company_info_tool: the @tool-decorated function that accepts only
        company_gstin (what Strands/Pydantic sees) and always uses settings.DEMO_MODE.
      - get_company_info: the public alias used by tests and agents; delegates
        to _lookup_company_info with the _demo override intact.

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

# Demo / DEMO_MODE fixed response -- Maharashtra active company profile
_DEMO_PROFILE: dict = {
    "status": "active",
    "incorporated": "2015",
    "paid_up_capital": 100_000_000.0,
}

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


def _lookup_company_info(company_gstin: str, _demo: bool = None) -> dict:
    """Look up mock company info for a given GSTIN.

    Args:
        company_gstin: GSTIN of the company (15 chars expected).
        _demo: Override for DEMO_MODE. None = use settings.DEMO_MODE,
               True = force demo, False = force real (mock) logic.

    Returns:
        dict with keys: status (str), incorporated (str), paid_up_capital (float).
    """
    use_demo = settings.DEMO_MODE if _demo is None else _demo

    if use_demo:
        logger.info(
            "DEMO_MODE: returning pre-computed company info for GSTIN %s", company_gstin
        )
        return dict(_DEMO_PROFILE)

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

    In DEMO_MODE, always returns the active Maharashtra company profile regardless
    of the provided GSTIN.

    Args:
        company_gstin: 15-character GSTIN of the company to look up.
    """
    return _lookup_company_info(company_gstin)


# ---------------------------------------------------------------------------
# Public alias -- preserves the _demo override for tests while delegating
# to the same core logic as the Strands tool
# ---------------------------------------------------------------------------


def get_company_info(company_gstin: str, _demo: bool = None) -> dict:
    """Public entry point for company info lookup.

    Delegates to _lookup_company_info, preserving the _demo override used in
    unit tests. Agents should register get_company_info_tool with the Strands
    Swarm; tests and internal callers use this function directly.

    Args:
        company_gstin: 15-character GSTIN of the company to look up.
        _demo: Override for DEMO_MODE. None = use settings.DEMO_MODE,
               True = force demo, False = force real (mock) logic.

    Returns:
        dict with keys: status (str), incorporated (str), paid_up_capital (float).
    """
    return _lookup_company_info(company_gstin, _demo=_demo)
