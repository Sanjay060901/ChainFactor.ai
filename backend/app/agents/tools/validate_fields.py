"""validate_fields tool: Validates extracted invoice data for completeness and correctness.

Performs four categories of validation:
1. Required fields presence (invoice_number, seller/buyer GSTIN, line_items, date, amount)
2. Math validation (line items sum vs subtotal, subtotal + tax vs total)
3. GSTIN format (15 chars, state code 01-37, full PAN + entity + Z + check pattern)
4. Date format (YYYY-MM-DD) and logical consistency (not future, due >= invoice)

Math tolerance: differences >= 1.0 are errors; 0 < diff < 1.0 are warnings (is_valid stays True).
GSTIN state code must be in range 01-37 (India's valid state codes).
Demo mode: returns pre-computed success with no validation.

Dependencies:
    - strands (@tool decorator)
"""

import logging
import re
from datetime import date, datetime

from strands import tool

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Required top-level fields and nested GSTIN locations
_REQUIRED_TOP_LEVEL = ("invoice_number", "invoice_date", "total_amount")
_GSTIN_LOCATIONS = (
    ("seller", "gstin"),
    ("buyer", "gstin"),
)

# GSTIN regex: 2 digits (state) + 5 uppercase letters (PAN entity name) +
#              4 alphanumeric (PAN number) + 1 alphanumeric (PAN check) +
#              1 alphanumeric (entity number) + Z (always) + 1 alphanumeric (check)
# Breakdown: positions 1-2 = state code, 3-7 = PAN letters, 8-11 = PAN digits,
#            12 = PAN alpha, 13 = entity num, 14 = 'Z', 15 = checksum
_GSTIN_REGEX = re.compile(
    r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[0-9A-Z]{1}[Z]{1}[0-9A-Z]{1}$"
)

# Valid Indian state codes: 01 (J&K) through 37 (Andaman & Nicobar)
_VALID_STATE_CODES = set(f"{i:02d}" for i in range(1, 38))

# Tolerance threshold: diff >= this value triggers an error; below it triggers a warning
_MATH_ERROR_THRESHOLD = 1.0

# Expected date format for invoice_date and due_date
_DATE_FORMAT = "%Y-%m-%d"


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _check_required_fields(data: dict, errors: list[str]) -> None:
    """Check that all required top-level fields are present and non-empty.

    Args:
        data: The extracted invoice data dict.
        errors: Mutable list; errors are appended in-place.
    """
    for field in _REQUIRED_TOP_LEVEL:
        if field not in data or data[field] is None or data[field] == "":
            errors.append(f"Missing required field: {field}")

    # Check nested GSTIN fields
    for parent, child in _GSTIN_LOCATIONS:
        parent_obj = data.get(parent, {}) or {}
        if child not in parent_obj or not parent_obj[child]:
            errors.append(f"Missing required field: {parent}.{child}")

    # line_items must exist and be non-empty
    if "line_items" not in data or data["line_items"] is None:
        errors.append("Missing required field: line_items")
    elif len(data["line_items"]) == 0:
        errors.append("Missing required field: line_items must not be empty")


def _check_gstin_format(gstin: str, label: str, errors: list[str]) -> None:
    """Validate a single GSTIN string against format and state code rules.

    A valid GSTIN is exactly 15 characters matching:
        ^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[0-9A-Z]{1}Z[0-9A-Z]$
    The first two digits must be a valid Indian state code (01-37).

    Args:
        gstin: The GSTIN string to validate.
        label: Human-readable label used in error messages (e.g. "seller GSTIN").
        errors: Mutable list; errors are appended in-place.
    """
    if len(gstin) != 15:
        errors.append(
            f"Invalid {label}: must be exactly 15 characters (got {len(gstin)})"
        )
        return

    if not _GSTIN_REGEX.match(gstin):
        errors.append(f"Invalid {label}: does not match GSTIN format pattern")
        return

    state_code = gstin[:2]
    if state_code not in _VALID_STATE_CODES:
        errors.append(
            f"Invalid {label}: state code '{state_code}' is not a valid Indian state code (01-37)"
        )


def _check_all_gstins(data: dict, errors: list[str]) -> None:
    """Validate GSTIN format for seller and buyer if present.

    Skips validation when the GSTIN field is already missing (covered by
    required-field checks).

    Args:
        data: The extracted invoice data dict.
        errors: Mutable list; errors are appended in-place.
    """
    seller = data.get("seller") or {}
    seller_gstin = seller.get("gstin")
    if seller_gstin:
        _check_gstin_format(seller_gstin, "seller GSTIN", errors)

    buyer = data.get("buyer") or {}
    buyer_gstin = buyer.get("gstin")
    if buyer_gstin:
        _check_gstin_format(buyer_gstin, "buyer GSTIN", errors)


def _check_math(data: dict, errors: list[str], warnings: list[str]) -> None:
    """Validate numeric consistency between line items, subtotal, tax, and total.

    Rules:
    - sum(line_items[].amount) vs subtotal: diff >= 1.0 = error, 0 < diff < 1.0 = warning
    - subtotal + tax_amount vs total_amount: same thresholds

    Missing numeric fields are silently skipped (covered by required-field checks).

    Args:
        data: The extracted invoice data dict.
        errors: Mutable list; errors are appended in-place.
        warnings: Mutable list; warnings are appended in-place.
    """
    line_items = data.get("line_items") or []
    subtotal = data.get("subtotal")
    tax_amount = data.get("tax_amount", 0.0) or 0.0
    total_amount = data.get("total_amount")

    # Line items sum vs subtotal
    if line_items and subtotal is not None:
        line_sum = sum(float(item.get("amount", 0)) for item in line_items)
        diff = abs(line_sum - float(subtotal))
        if diff >= _MATH_ERROR_THRESHOLD:
            errors.append(
                f"Math error: line items sum ({line_sum:.2f}) does not match "
                f"subtotal ({subtotal:.2f}), difference {diff:.2f}"
            )
        elif diff > 0:
            warnings.append(
                f"Math warning: line items sum ({line_sum:.2f}) differs from "
                f"subtotal ({subtotal:.2f}) by {diff:.2f} (rounding)"
            )

    # Subtotal + tax vs total
    if subtotal is not None and total_amount is not None:
        expected_total = float(subtotal) + float(tax_amount)
        diff = abs(expected_total - float(total_amount))
        if diff >= _MATH_ERROR_THRESHOLD:
            errors.append(
                f"Math error: subtotal ({subtotal}) + tax ({tax_amount}) = {expected_total:.2f} "
                f"does not match total_amount ({total_amount}), difference {diff:.2f}"
            )
        elif diff > 0:
            warnings.append(
                f"Math warning: subtotal + tax ({expected_total:.2f}) differs from "
                f"total_amount ({total_amount}) by {diff:.2f} (rounding)"
            )


def _parse_date(date_str: str, field_name: str, errors: list[str]) -> date | None:
    """Parse a date string in YYYY-MM-DD format.

    Args:
        date_str: The raw date string from extracted data.
        field_name: Field name for error messages.
        errors: Mutable list; errors are appended in-place if unparseable.

    Returns:
        Parsed date object, or None if parsing failed.
    """
    try:
        return datetime.strptime(date_str, _DATE_FORMAT).date()
    except (ValueError, TypeError):
        errors.append(
            f"Invalid date format for {field_name}: '{date_str}' (expected YYYY-MM-DD)"
        )
        return None


def _check_dates(data: dict, errors: list[str], warnings: list[str]) -> None:
    """Validate date fields for format and logical consistency.

    Rules:
    - invoice_date must parse as YYYY-MM-DD (error if not)
    - invoice_date in the future = warning (not error)
    - due_date before invoice_date = warning (not error)

    Args:
        data: The extracted invoice data dict.
        errors: Mutable list; errors are appended in-place.
        warnings: Mutable list; warnings are appended in-place.
    """
    raw_invoice_date = data.get("invoice_date")
    if not raw_invoice_date:
        # Already caught by required-field checks; skip here to avoid duplicate error
        return

    invoice_date = _parse_date(str(raw_invoice_date), "invoice_date", errors)
    if invoice_date is None:
        # Parsing failed; error already appended
        return

    today = date.today()
    if invoice_date > today:
        warnings.append(
            f"Invoice date {invoice_date} is in the future (today is {today})"
        )

    raw_due_date = data.get("due_date")
    if raw_due_date:
        # due_date format errors are warnings, not blocking errors
        try:
            due_date = datetime.strptime(str(raw_due_date), _DATE_FORMAT).date()
            if due_date < invoice_date:
                warnings.append(
                    f"due_date ({due_date}) is before invoice_date ({invoice_date})"
                )
        except (ValueError, TypeError):
            warnings.append(
                f"due_date '{raw_due_date}' could not be parsed as YYYY-MM-DD"
            )


# ---------------------------------------------------------------------------
# Strands @tool
# ---------------------------------------------------------------------------


@tool
def validate_fields(extracted_data: dict) -> dict:
    """Validate the completeness and correctness of extracted invoice fields.

    Checks required fields, math consistency, GSTIN format, and date validity.

    Args:
        extracted_data: Structured invoice dict produced by extract_invoice tool.
    """
    logger.info("Validating extracted invoice fields")

    errors: list[str] = []
    warnings: list[str] = []

    # Run all validation categories (each mutates errors/warnings in-place)
    _check_required_fields(extracted_data, errors)
    _check_all_gstins(extracted_data, errors)
    _check_math(extracted_data, errors, warnings)
    _check_dates(extracted_data, errors, warnings)

    is_valid = len(errors) == 0

    logger.info(
        "Field validation complete: is_valid=%s, errors=%d, warnings=%d",
        is_valid,
        len(errors),
        len(warnings),
    )

    return {
        "is_valid": is_valid,
        "errors": errors,
        "warnings": warnings,
    }
