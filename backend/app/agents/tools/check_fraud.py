"""check_fraud tool: 5-layer fraud detection for Indian GST invoices.

Layers (all rule-based / mock -- no external API calls required):
    1. Document Integrity   -- missing or empty required fields
    2. Financial Consistency -- negative amounts, tax rate sanity, math cross-check
    3. Pattern Analysis      -- high-value threshold, suspicious round numbers
    4. Entity Verification   -- uses upstream GSTIN verification result
    5. Cross-Reference       -- mock duplicate-invoice detection

Each layer returns a dict:
    {"name": str, "result": "pass"|"warning"|"fail", "confidence": float, "detail": str}

Overall result is the worst across all layers. Confidence is the average of all
five layer confidences, rounded to 1 decimal. Non-pass layer details are surfaced
in the top-level ``flags`` list.

Dependencies:
    - strands (@tool decorator)
"""

import logging

from strands import tool

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# High-value threshold: invoices above this amount trigger a pattern warning
HIGH_VALUE_THRESHOLD = 5_000_000.0  # 50 lakh INR

# Round-number modulus: total_amount ending in three zeros is suspicious
ROUND_NUMBER_MODULUS = 1000

# Tolerance for floating-point math comparisons (0.5 INR)
_MATH_TOLERANCE = 0.5

_LAYER_NAMES = [
    "Document Integrity",
    "Financial Consistency",
    "Pattern Analysis",
    "Entity Verification",
    "Cross-Reference",
]


# ---------------------------------------------------------------------------
# Layer 1: Document Integrity
# ---------------------------------------------------------------------------


def _check_document_integrity(extracted_data: dict) -> dict:
    """Check that required document fields are present and non-empty.

    Args:
        extracted_data: Structured invoice data produced by extract_invoice.

    Returns:
        Layer result dict with name, result, confidence, and detail.
    """
    issues = []

    seller_name = (extracted_data.get("seller") or {}).get("name", "")
    if not seller_name or not str(seller_name).strip():
        issues.append("Seller name is missing")

    buyer_name = (extracted_data.get("buyer") or {}).get("name", "")
    if not buyer_name or not str(buyer_name).strip():
        issues.append("Buyer name is missing")

    invoice_number = extracted_data.get("invoice_number", "")
    if not invoice_number or not str(invoice_number).strip():
        issues.append("Invoice number is missing")

    if not issues:
        return {
            "name": "Document Integrity",
            "result": "pass",
            "confidence": 95.0,
            "detail": "All required document fields present",
        }

    return {
        "name": "Document Integrity",
        "result": "warning",
        "confidence": 50.0,
        "detail": "; ".join(issues),
    }


# ---------------------------------------------------------------------------
# Layer 2: Financial Consistency
# ---------------------------------------------------------------------------


def _check_financial_consistency(extracted_data: dict) -> dict:
    """Verify that amounts are non-negative and internal math is consistent.

    Checks:
    - subtotal >= 0
    - total_amount >= 0
    - tax_rate in [0, 100]
    - sum(line_item amounts) ≈ subtotal
    - subtotal + tax_amount ≈ total_amount

    Args:
        extracted_data: Structured invoice data produced by extract_invoice.

    Returns:
        Layer result dict with name, result, confidence, and detail.
    """
    issues = []

    subtotal = float(extracted_data.get("subtotal") or 0.0)
    tax_amount = float(extracted_data.get("tax_amount") or 0.0)
    tax_rate = float(extracted_data.get("tax_rate") or 0.0)
    total_amount = float(extracted_data.get("total_amount") or 0.0)
    line_items = extracted_data.get("line_items") or []

    if subtotal < 0:
        issues.append(f"Negative subtotal: {subtotal}")

    if total_amount < 0:
        issues.append(f"Negative total_amount: {total_amount}")

    if tax_rate > 100.0:
        issues.append(f"Tax rate exceeds 100%: {tax_rate}")

    # Line items sum vs subtotal (only if line_items are present)
    if line_items:
        line_sum = sum(float(item.get("amount") or 0.0) for item in line_items)
        if abs(line_sum - subtotal) > _MATH_TOLERANCE:
            issues.append(
                f"Line items sum ({line_sum}) does not match subtotal ({subtotal})"
            )

    # subtotal + tax ≈ total (skip when amounts are already flagged negative)
    if subtotal >= 0 and total_amount >= 0:
        expected_total = subtotal + tax_amount
        if abs(expected_total - total_amount) > _MATH_TOLERANCE:
            issues.append(
                f"subtotal + tax ({expected_total}) does not match total ({total_amount})"
            )

    if not issues:
        return {
            "name": "Financial Consistency",
            "result": "pass",
            "confidence": 95.0,
            "detail": "All financial checks passed",
        }

    return {
        "name": "Financial Consistency",
        "result": "fail",
        "confidence": 10.0,
        "detail": "; ".join(issues),
    }


# ---------------------------------------------------------------------------
# Layer 3: Pattern Analysis
# ---------------------------------------------------------------------------


def _check_pattern_analysis(extracted_data: dict) -> dict:
    """Flag suspicious amount patterns without failing the invoice outright.

    Patterns checked:
    - total_amount > HIGH_VALUE_THRESHOLD (50 lakh) -- unusual for SME invoices
    - total_amount ends in three zeros (round-number amounts are suspicious)

    Args:
        extracted_data: Structured invoice data produced by extract_invoice.

    Returns:
        Layer result dict with name, result, confidence, and detail.
    """
    warnings = []

    total_amount = float(extracted_data.get("total_amount") or 0.0)

    if total_amount > HIGH_VALUE_THRESHOLD:
        warnings.append(
            f"Unusually high invoice amount: {total_amount:.0f} (threshold {HIGH_VALUE_THRESHOLD:.0f})"
        )

    # Round-number check: total_amount % 1000 == 0 (and total > 0 to avoid zero-invoice noise)
    if total_amount > 0 and int(total_amount) % ROUND_NUMBER_MODULUS == 0:
        warnings.append(
            f"Round-number total amount detected: {total_amount:.0f} (suspicious pattern)"
        )

    if not warnings:
        return {
            "name": "Pattern Analysis",
            "result": "pass",
            "confidence": 90.0,
            "detail": "No suspicious patterns detected",
        }

    return {
        "name": "Pattern Analysis",
        "result": "warning",
        "confidence": 60.0,
        "detail": "; ".join(warnings),
    }


# ---------------------------------------------------------------------------
# Layer 4: Entity Verification
# ---------------------------------------------------------------------------


def _check_entity_verification(extracted_data: dict, gstin_verification: dict) -> dict:
    """Evaluate entity trustworthiness using upstream GSTIN verification data.

    Args:
        extracted_data: Structured invoice data (used for context logging only).
        gstin_verification: Output from the verify_gstn tool / mock GSTIN service.
            Expected keys: verified (bool), details.seller_gstin_active (bool),
            details.buyer_on_blocklist (bool).

    Returns:
        Layer result dict with name, result, confidence, and detail.
    """
    issues = []

    verified = gstin_verification.get("verified", False)
    if not verified:
        issues.append("GSTIN verification failed: overall verification status is False")

    details = gstin_verification.get("details") or {}

    seller_active = details.get("seller_gstin_active", True)
    if not seller_active:
        issues.append("Seller GSTIN is inactive or cancelled")

    buyer_blocklist = details.get("buyer_on_blocklist", False)
    if buyer_blocklist:
        issues.append("Buyer entity is on the fraud/GST blocklist")

    if not issues:
        return {
            "name": "Entity Verification",
            "result": "pass",
            "confidence": 95.0,
            "detail": "All entities verified and active",
        }

    return {
        "name": "Entity Verification",
        "result": "fail",
        "confidence": 5.0,
        "detail": "; ".join(issues),
    }


# ---------------------------------------------------------------------------
# Layer 5: Cross-Reference
# ---------------------------------------------------------------------------


def _check_cross_reference(extracted_data: dict) -> dict:
    """Mock duplicate-invoice detection via invoice number heuristics.

    In production this would query the invoice database. For the hackathon,
    any invoice number containing the substring "DUP" (case-insensitive) is
    treated as a detected duplicate.

    Args:
        extracted_data: Structured invoice data produced by extract_invoice.

    Returns:
        Layer result dict with name, result, confidence, and detail.
    """
    invoice_number = str(extracted_data.get("invoice_number") or "")

    if "dup" in invoice_number.lower():
        return {
            "name": "Cross-Reference",
            "result": "fail",
            "confidence": 5.0,
            "detail": f"Possible duplicate invoice detected: '{invoice_number}' matches existing record",
        }

    return {
        "name": "Cross-Reference",
        "result": "pass",
        "confidence": 90.0,
        "detail": "No duplicate invoice found",
    }


# ---------------------------------------------------------------------------
# Helper: aggregate layer results into overall verdict
# ---------------------------------------------------------------------------


def _aggregate_results(layers: list[dict]) -> tuple[str, float, list[str]]:
    """Compute overall fraud result, average confidence, and flag list.

    Args:
        layers: List of five layer result dicts.

    Returns:
        Tuple of (overall, confidence, flags) where:
            overall   -- "fail" if any layer failed, "warning" if any warned, else "pass"
            confidence -- average of layer confidences rounded to 1 decimal
            flags      -- detail strings from all non-pass layers
    """
    results = [layer["result"] for layer in layers]
    flags = [layer["detail"] for layer in layers if layer["result"] != "pass"]

    if "fail" in results:
        overall = "fail"
    elif "warning" in results:
        overall = "warning"
    else:
        overall = "pass"

    confidences = [layer["confidence"] for layer in layers]
    avg_confidence = round(sum(confidences) / len(confidences), 1)

    return overall, avg_confidence, flags


# ---------------------------------------------------------------------------
# Strands @tool
# ---------------------------------------------------------------------------


@tool
def check_fraud(extracted_data: dict, gstin_verification: dict) -> dict:
    """Run 5-layer fraud detection on an extracted invoice.

    Layers applied in order:
        1. Document Integrity   -- required field presence
        2. Financial Consistency -- negative amounts, tax rate, math cross-check
        3. Pattern Analysis      -- high-value or round-number red flags
        4. Entity Verification   -- GSTIN active status and blocklist check
        5. Cross-Reference       -- mock duplicate-invoice detection

    Args:
        extracted_data: Structured invoice dict from extract_invoice tool.
        gstin_verification: GSTIN verification dict from verify_gstn tool.
    """
    logger.info(
        "Running 5-layer fraud detection on invoice %s",
        extracted_data.get("invoice_number", "<unknown>"),
    )

    layers = [
        _check_document_integrity(extracted_data),
        _check_financial_consistency(extracted_data),
        _check_pattern_analysis(extracted_data),
        _check_entity_verification(extracted_data, gstin_verification),
        _check_cross_reference(extracted_data),
    ]

    overall, confidence, flags = _aggregate_results(layers)

    logger.info(
        "Fraud detection complete: overall=%s confidence=%.1f flags=%d",
        overall,
        confidence,
        len(flags),
    )

    return {
        "overall": overall,
        "confidence": confidence,
        "flags": flags,
        "layers": layers,
    }
