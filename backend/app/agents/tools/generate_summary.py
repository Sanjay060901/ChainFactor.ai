"""generate_summary tool: Deterministic summary generation for processed invoices.

Produces a human-readable summary, a list of notable highlights, and a
recommendation based on the risk level.

Logic:
- summary: "Invoice {invoice_number} from {seller.name} to {buyer.name}
            for Rs{total_amount}. Risk: {risk.level} ({risk.score}/100)."
- highlights: notable findings (fraud warnings, GST issues, credit concerns, etc.)
- recommendation: "approve" (low/medium), "review" (high), "reject" (critical)

Dependencies:
    - strands (@tool decorator)
"""

import logging

from strands import tool

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _build_summary(extracted_data: dict, risk_assessment: dict) -> str:
    """Build the one-line summary string."""
    seller_name = (extracted_data.get("seller") or {}).get("name", "Unknown Seller")
    buyer_name = (extracted_data.get("buyer") or {}).get("name", "Unknown Buyer")
    invoice_number = extracted_data.get("invoice_number", "N/A")
    total_amount = extracted_data.get("total_amount", 0.0)
    risk_level = risk_assessment.get("level", "unknown")
    risk_score = risk_assessment.get("score", 0)

    return (
        f"Invoice {invoice_number} from {seller_name} to {buyer_name} "
        f"for Rs{total_amount}. Risk: {risk_level} ({risk_score}/100)."
    )


def _build_highlights(
    validation_result: dict,
    fraud_result: dict,
    gst_compliance: dict,
    buyer_intel: dict,
    credit_score: dict,
    company_info: dict,
) -> list[str]:
    """Build a list of notable highlights from upstream tool outputs."""
    highlights: list[str] = []

    # Validation issues
    if not validation_result.get("is_valid", True):
        errors = validation_result.get("errors", [])
        highlights.append(
            f"Validation errors: {', '.join(errors)}"
            if errors
            else "Field validation failed"
        )

    # Fraud detection
    fraud_overall = str(fraud_result.get("overall", "pass")).lower()
    if fraud_overall == "fail":
        flags = fraud_result.get("flags", [])
        highlights.append(
            f"Fraud detection failed: {', '.join(flags)}"
            if flags
            else "Fraud detection failed"
        )
    elif fraud_overall == "warning":
        flags = fraud_result.get("flags", [])
        highlights.append(
            f"Fraud warning: {', '.join(flags)}" if flags else "Fraud warning detected"
        )

    # GST compliance
    if not gst_compliance.get("is_compliant", True):
        highlights.append("GST non-compliance detected")

    # Buyer intel
    payment_history = str(buyer_intel.get("payment_history", "reliable")).lower()
    if payment_history == "slow_payer":
        avg_days = buyer_intel.get("avg_days", "N/A")
        highlights.append(f"Buyer is a slow payer (avg {avg_days} days)")
    elif payment_history == "new_buyer":
        highlights.append("Buyer has no payment history (new buyer)")

    # Credit score
    score = int(credit_score.get("score", 650))
    if score < 580:
        highlights.append(f"Poor credit score ({score})")
    elif score < 650:
        highlights.append(f"Fair credit score ({score})")

    # Company info
    status = str(company_info.get("status", "active")).lower()
    if status != "active":
        highlights.append(f"Company status: {status}")

    return highlights


def _risk_to_recommendation(risk_level: str) -> str:
    """Map risk level to recommendation."""
    level = risk_level.lower()
    if level in ("low", "medium"):
        return "approve"
    if level == "high":
        return "review"
    return "reject"


def _resolve_summary(
    extracted_data: dict,
    validation_result: dict,
    fraud_result: dict,
    gst_compliance: dict,
    gstin_verification: dict,
    buyer_intel: dict,
    credit_score: dict,
    company_info: dict,
    risk_assessment: dict,
) -> dict:
    """Core summary generation logic, separated from the Strands decorator."""
    invoice_number = (extracted_data or {}).get("invoice_number", "<unknown>")
    logger.info("Generating summary for invoice %s", invoice_number)

    summary = _build_summary(extracted_data, risk_assessment)
    highlights = _build_highlights(
        validation_result,
        fraud_result,
        gst_compliance,
        buyer_intel,
        credit_score,
        company_info,
    )
    risk_level = risk_assessment.get("level", "low")
    recommendation = _risk_to_recommendation(risk_level)

    logger.info(
        "Summary generated: invoice=%s recommendation=%s highlights=%d",
        invoice_number,
        recommendation,
        len(highlights),
    )

    return {
        "summary": summary,
        "highlights": highlights,
        "recommendation": recommendation,
    }


# ---------------------------------------------------------------------------
# Strands @tool  (registered with the agent; no leading-underscore params)
# ---------------------------------------------------------------------------


@tool
def _generate_summary_tool(
    extracted_data: dict,
    validation_result: dict,
    fraud_result: dict,
    gst_compliance: dict,
    gstin_verification: dict,
    buyer_intel: dict,
    credit_score: dict,
    company_info: dict,
    risk_assessment: dict,
) -> dict:
    """Generate a human-readable summary of the invoice processing results.

    Produces a summary string, notable highlights, and a recommendation
    (approve/review/reject) based on the risk level and upstream tool outputs.

    Args:
        extracted_data: Structured invoice dict from extract_invoice tool.
        validation_result: Validation dict from validate_fields tool.
        fraud_result: Fraud detection dict from check_fraud tool.
        gst_compliance: GST compliance dict from validate_gst_compliance tool.
        gstin_verification: GSTIN verification dict from verify_gstn tool.
        buyer_intel: Buyer intelligence dict from get_buyer_intel tool.
        credit_score: Credit score dict from get_credit_score tool.
        company_info: Company information dict from get_company_info tool.
        risk_assessment: Risk assessment dict from calculate_risk tool.
    """
    return _resolve_summary(
        extracted_data,
        validation_result,
        fraud_result,
        gst_compliance,
        gstin_verification,
        buyer_intel,
        credit_score,
        company_info,
        risk_assessment,
    )


# ---------------------------------------------------------------------------
# Public callable (used by tests and by agent tool list)
# ---------------------------------------------------------------------------


def generate_summary(
    extracted_data: dict,
    validation_result: dict,
    fraud_result: dict,
    gst_compliance: dict,
    gstin_verification: dict,
    buyer_intel: dict,
    credit_score: dict,
    company_info: dict,
    risk_assessment: dict,
) -> dict:
    """Generate a human-readable summary of the invoice processing results.

    Args:
        extracted_data: Structured invoice dict from extract_invoice tool.
        validation_result: Validation dict from validate_fields tool.
        fraud_result: Fraud detection dict from check_fraud tool.
        gst_compliance: GST compliance dict from validate_gst_compliance tool.
        gstin_verification: GSTIN verification dict from verify_gstn tool.
        buyer_intel: Buyer intelligence dict from get_buyer_intel tool.
        credit_score: Credit score dict from get_credit_score tool.
        company_info: Company information dict from get_company_info tool.
        risk_assessment: Risk assessment dict from calculate_risk tool.

    Returns:
        Dict with keys: summary (str), highlights (list[str]), recommendation (str).
    """
    return _resolve_summary(
        extracted_data,
        validation_result,
        fraud_result,
        gst_compliance,
        gstin_verification,
        buyer_intel,
        credit_score,
        company_info,
        risk_assessment,
    )
