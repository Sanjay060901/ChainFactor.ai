"""validate_gst_compliance tool: Validates GST compliance for extracted invoice data.

Checks:
  - HSN/SAC code format (4-8 digits, all numeric)
  - Tax rate matches the GST slab for the given HSN prefix
  - Tax type correctness (IGST for inter-state, CGST+SGST for intra-state)
  - E-invoice applicability threshold (seller turnover >= 5 crore)

Demo mode: Returns pre-computed compliant result with no computation.

Dependencies:
    - strands (@tool decorator)
    - app.config.settings (DEMO_MODE)
"""

import logging
from typing import Optional

from strands import tool

from app.config import settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# E-invoice mandatory turnover threshold: 5 crore (INR)
EINVOICE_THRESHOLD = 5_00_00_000

# HSN prefix -> applicable GST rate (%).
# Longer prefixes take priority over shorter ones (matched in order of length desc).
_HSN_RATE_MAP: list[tuple[str, float]] = [
    ("9983", 18.0),  # IT services (998311-998319)
    ("8471", 18.0),  # Computers and peripherals
    ("1006", 5.0),  # Rice
    ("0201", 0.0),  # Meat (exempt)
]

# Pre-computed demo result
_DEMO_RESULT: dict = {
    "is_compliant": True,
    "details": {
        "hsn_valid": True,
        "rate_match": True,
        "tax_type_correct": True,
    },
}


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _validate_hsn_codes(line_items: list[dict]) -> bool:
    """Return True if every line item has a valid HSN/SAC code.

    Valid: all-numeric string with 4-8 characters.

    Args:
        line_items: List of line item dicts, each expected to have 'hsn_code'.

    Returns:
        True if all HSN codes are valid; False if any is invalid or missing.
    """
    if not line_items:
        return False

    for item in line_items:
        code = str(item.get("hsn_code", "")).strip()
        if not code:
            logger.debug("HSN code missing on line item: %s", item)
            return False
        if not code.isdigit():
            logger.debug("HSN code non-numeric: %r", code)
            return False
        if not (4 <= len(code) <= 8):
            logger.debug(
                "HSN code length out of range [4,8]: %r (len=%d)", code, len(code)
            )
            return False

    return True


def _expected_rate_for_hsn(hsn_code: str) -> Optional[float]:
    """Return the expected GST rate for a given HSN code, or None if not mapped.

    Matches against known HSN prefix patterns (longest match first).

    Args:
        hsn_code: Numeric HSN/SAC code string.

    Returns:
        Expected GST rate as a float, or None if HSN prefix is not in the map.
    """
    for prefix, rate in _HSN_RATE_MAP:
        if hsn_code.startswith(prefix):
            return rate
    return None


def _validate_rate_match(line_items: list[dict], tax_rate: Optional[float]) -> bool:
    """Return True if the invoice tax rate matches the expected rate for the HSN codes.

    Uses the first line item with a known HSN prefix to determine the expected rate.
    If no HSN prefix is mapped, the check passes (unknown HSN -> cannot validate).

    Args:
        line_items: List of line item dicts.
        tax_rate: The tax rate declared on the invoice (e.g. 18.0).

    Returns:
        True if rate matches or HSN is unmapped; False if rate mismatches.
    """
    for item in line_items:
        code = str(item.get("hsn_code", "")).strip()
        expected = _expected_rate_for_hsn(code)
        if expected is not None:
            match = (tax_rate is not None) and (float(tax_rate) == expected)
            if not match:
                logger.debug(
                    "Rate mismatch: HSN %r expects %.1f%%, got %s%%",
                    code,
                    expected,
                    tax_rate,
                )
            return match

    # No mapped HSN found in line items -- cannot determine expected rate, treat as pass
    return True


def _extract_state_code(gstin: str) -> str:
    """Return the 2-character state code from a GSTIN string.

    Args:
        gstin: 15-character GSTIN string.

    Returns:
        First two characters (state code), or empty string if GSTIN is too short.
    """
    return gstin[:2] if len(gstin) >= 2 else ""


def _validate_tax_type(
    seller_gstin: str,
    buyer_gstin: str,
    tax_type: Optional[str],
) -> bool:
    """Return True if the tax type is appropriate for the transaction.

    Inter-state (different state codes) -> expected IGST.
    Intra-state (same state codes) -> expected CGST+SGST.
    If tax_type is None/missing, returns True (cannot validate -- do not crash).

    Args:
        seller_gstin: GSTIN of the seller.
        buyer_gstin: GSTIN of the buyer.
        tax_type: Declared tax type on the invoice (e.g. "IGST", "CGST+SGST").

    Returns:
        True if tax type is consistent with state codes or if type is unknown.
    """
    if tax_type is None:
        # Missing tax_type -- cannot validate, return True to avoid false negatives
        return True

    seller_state = _extract_state_code(seller_gstin)
    buyer_state = _extract_state_code(buyer_gstin)

    if not seller_state or not buyer_state:
        # Cannot determine state codes -- skip check
        return True

    is_interstate = seller_state != buyer_state

    if is_interstate:
        correct = tax_type.upper() == "IGST"
    else:
        correct = tax_type.upper() == "CGST+SGST"

    if not correct:
        logger.debug(
            "Tax type mismatch: seller_state=%r, buyer_state=%r, "
            "inter_state=%s, declared=%r",
            seller_state,
            buyer_state,
            is_interstate,
            tax_type,
        )

    return correct


# ---------------------------------------------------------------------------
# Strands @tool
# ---------------------------------------------------------------------------


@tool
def validate_gst_compliance(extracted_data: dict) -> dict:
    """Validate GST compliance for extracted invoice data.

    Performs four checks:
      1. HSN/SAC code format: 4-8 digits, all numeric.
      2. Tax rate matches the GST slab associated with the HSN prefix.
      3. Tax type (IGST vs CGST+SGST) is correct for the transaction type.
      4. E-invoice requirement based on seller annual turnover (>= 5 crore).

    In DEMO_MODE, skips all computation and returns a pre-computed compliant result.

    Args:
        extracted_data: Structured invoice data dict produced by extract_invoice tool.
            Expected keys: seller (with gstin), buyer (with gstin), line_items,
            tax_rate, tax_type (optional), seller_turnover (optional).
    """
    if settings.DEMO_MODE:
        logger.info("DEMO_MODE: returning pre-computed GST compliance result")
        return dict(_DEMO_RESULT)

    logger.info(
        "Validating GST compliance for invoice: %s",
        extracted_data.get("invoice_number"),
    )

    line_items: list[dict] = extracted_data.get("line_items", [])
    tax_rate: Optional[float] = extracted_data.get("tax_rate")
    tax_type: Optional[str] = extracted_data.get("tax_type")

    seller_gstin: str = extracted_data.get("seller", {}).get("gstin", "")
    buyer_gstin: str = extracted_data.get("buyer", {}).get("gstin", "")

    # --- Check 1: HSN code validity ---
    hsn_valid = _validate_hsn_codes(line_items)

    # --- Check 2: Tax rate matches HSN slab ---
    rate_match = _validate_rate_match(line_items, tax_rate)

    # --- Check 3: Tax type matches transaction type ---
    tax_type_correct = _validate_tax_type(seller_gstin, buyer_gstin, tax_type)

    # --- Overall compliance ---
    is_compliant = hsn_valid and rate_match and tax_type_correct

    details: dict = {
        "hsn_valid": hsn_valid,
        "rate_match": rate_match,
        "tax_type_correct": tax_type_correct,
    }

    # --- Check 4: E-invoice requirement (conditional on seller_turnover presence) ---
    if "seller_turnover" in extracted_data:
        seller_turnover = extracted_data["seller_turnover"]
        details["einvoice_required"] = seller_turnover >= EINVOICE_THRESHOLD

    logger.info(
        "GST compliance result: is_compliant=%s, details=%s",
        is_compliant,
        details,
    )

    return {"is_compliant": is_compliant, "details": details}
