"""calculate_risk tool: Multi-signal weighted risk scoring for invoice financing.

Combines outputs from all upstream tools into a single risk score (0-100,
lower is better) with a level label and a one-sentence explanation.

Scoring formula (component -> penalty -> weight):
    fraud_result.overall:
        pass=0, warning=15, fail=40              weight=30%
    validation_result.is_valid:
        True=0, False=25                         weight=15%
    gst_compliance.is_compliant:
        True=0, False=20                         weight=15%
    credit_score.score (CIBIL):
        >= 900  -> penalty=0
        >= 750  -> penalty=10
        >= 650  -> penalty=20
        >= 580  -> penalty=35
        >= 450  -> penalty=50
        < 450   -> penalty=60                    weight=20%
    buyer_intel.payment_history:
        reliable=0, new_buyer=10, slow_payer=20  weight=10%
    company_info.status:
        active=0, dormant=25                     weight=10%

final_score = sum(component_penalty * weight), clamped to [0, 100], rounded to int.
Level:  0-25=low, 26-50=medium, 51-75=high, 76-100=critical

Demo mode: N/A (removed).

Dependencies:
    - strands (@tool decorator)
"""

import logging

from strands import tool

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Credit score breakpoints: (minimum_score, penalty)
_CREDIT_BREAKPOINTS: list[tuple[int, int]] = [
    (900, 0),
    (750, 10),
    (650, 20),
    (580, 35),
    (450, 50),
    (0, 60),
]


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _fraud_penalty(fraud_result: dict) -> float:
    """Map fraud overall result to a raw penalty value."""
    overall = str(fraud_result.get("overall", "pass")).lower()
    mapping = {"pass": 0.0, "warning": 15.0, "fail": 40.0}
    return mapping.get(overall, 0.0)


def _validation_penalty(validation_result: dict) -> float:
    """Map validation is_valid flag to a raw penalty value."""
    is_valid = validation_result.get("is_valid", True)
    return 0.0 if is_valid else 25.0


def _gst_penalty(gst_compliance: dict) -> float:
    """Map GST compliance is_compliant flag to a raw penalty value."""
    is_compliant = gst_compliance.get("is_compliant", True)
    return 0.0 if is_compliant else 20.0


def _credit_penalty(credit_score: dict) -> float:
    """Map CIBIL score integer to a raw penalty value using breakpoints."""
    score = int(credit_score.get("score", 650))
    for minimum, penalty in _CREDIT_BREAKPOINTS:
        if score >= minimum:
            return float(penalty)
    return 60.0  # fallback for scores below all breakpoints


def _buyer_intel_penalty(buyer_intel: dict) -> float:
    """Map payment_history label to a raw penalty value."""
    history = str(buyer_intel.get("payment_history", "reliable")).lower()
    mapping = {"reliable": 0.0, "new_buyer": 10.0, "slow_payer": 20.0}
    return mapping.get(history, 10.0)  # unknown defaults to new_buyer penalty


def _company_penalty(company_info: dict) -> float:
    """Map company status to a raw penalty value."""
    status = str(company_info.get("status", "active")).lower()
    return 0.0 if status == "active" else 25.0


def _score_to_level(score: int) -> str:
    """Convert a numeric risk score to a level label."""
    if score <= 25:
        return "low"
    if score <= 50:
        return "medium"
    if score <= 75:
        return "high"
    return "critical"


def _build_explanation(
    fraud_result: dict,
    validation_result: dict,
    gst_compliance: dict,
    buyer_intel: dict,
    credit_score: dict,
    company_info: dict,
    level: str,
) -> str:
    """Build a one-sentence explanation summarising the dominant risk factors."""
    issues = []

    overall = str(fraud_result.get("overall", "pass")).lower()
    if overall == "fail":
        issues.append("fraud detection failed")
    elif overall == "warning":
        issues.append("fraud warning detected")

    if not validation_result.get("is_valid", True):
        issues.append("invoice fields invalid")

    if not gst_compliance.get("is_compliant", True):
        issues.append("GST non-compliance")

    history = str(buyer_intel.get("payment_history", "reliable")).lower()
    if history == "slow_payer":
        issues.append("buyer is a slow payer")
    elif history == "new_buyer":
        issues.append("buyer has no payment history")

    credit = int(credit_score.get("score", 650))
    if credit < 580:
        issues.append(f"poor credit score ({credit})")
    elif credit < 650:
        issues.append(f"fair credit score ({credit})")

    status = str(company_info.get("status", "active")).lower()
    if status != "active":
        issues.append("company is dormant")

    if not issues:
        return "Low risk: all signals pass. Invoice approved for financing."

    factors = ", ".join(issues)
    return f"Risk level {level}: {factors}."


def _resolve_risk(
    extracted_data: dict,
    validation_result: dict,
    fraud_result: dict,
    gst_compliance: dict,
    buyer_intel: dict,
    credit_score: dict,
    company_info: dict,
) -> dict:
    """Core risk calculation logic, separated from the Strands decorator."""
    invoice_number = (extracted_data or {}).get("invoice_number", "<unknown>")
    logger.info("Calculating risk score for invoice %s", invoice_number)

    # Weighted sum: each component's penalty is scaled so its maximum equals its
    # weight (percentage of 100).  Scale factors:
    #   fraud:      max_penalty=40  -> scale=30/40=0.750
    #   validation: max_penalty=25  -> scale=15/25=0.600
    #   gst:        max_penalty=20  -> scale=15/20=0.750
    #   credit:     max_penalty=60  -> scale=20/60=0.333
    #   buyer_intel:max_penalty=20  -> scale=10/20=0.500
    #   company:    max_penalty=25  -> scale=10/25=0.400
    #
    # This ensures max possible score = 30+15+15+20+10+10 = 100 (critical)
    raw_score = (
        _fraud_penalty(fraud_result) * (30 / 40)
        + _validation_penalty(validation_result) * (15 / 25)
        + _gst_penalty(gst_compliance) * (15 / 20)
        + _credit_penalty(credit_score) * (20 / 60)
        + _buyer_intel_penalty(buyer_intel) * (10 / 20)
        + _company_penalty(company_info) * (10 / 25)
    )

    # Clamp to [0, 100] and convert to int
    score = max(0, min(100, round(raw_score)))

    level = _score_to_level(score)
    explanation = _build_explanation(
        fraud_result,
        validation_result,
        gst_compliance,
        buyer_intel,
        credit_score,
        company_info,
        level,
    )

    logger.info(
        "Risk calculation complete: invoice=%s score=%d level=%s",
        invoice_number,
        score,
        level,
    )

    return {"score": score, "level": level, "explanation": explanation}


# ---------------------------------------------------------------------------
# Strands @tool  (registered with the agent; no leading-underscore params)
# ---------------------------------------------------------------------------


@tool
def _calculate_risk_tool(
    extracted_data: dict,
    validation_result: dict,
    fraud_result: dict,
    gst_compliance: dict,
    buyer_intel: dict,
    credit_score: dict,
    company_info: dict,
) -> dict:
    """Calculate a weighted risk score from all upstream tool outputs.

    Combines fraud detection, field validation, GST compliance, CIBIL credit
    score, buyer payment history, and company status into a single risk score
    (0-100, lower is better).

    Args:
        extracted_data: Structured invoice dict from extract_invoice tool.
        validation_result: Validation dict from validate_fields tool.
        fraud_result: Fraud detection dict from check_fraud tool.
        gst_compliance: GST compliance dict from validate_gst_compliance tool.
        buyer_intel: Buyer intelligence dict from get_buyer_intel tool.
        credit_score: Credit score dict from get_credit_score tool.
        company_info: Company information dict from get_company_info tool.
    """
    return _resolve_risk(
        extracted_data,
        validation_result,
        fraud_result,
        gst_compliance,
        buyer_intel,
        credit_score,
        company_info,
    )


# ---------------------------------------------------------------------------
# Public callable (used by tests and by agent tool list)
# Accepts an optional _demo override so tests can force real/demo paths
# without changing global settings.
# ---------------------------------------------------------------------------


def calculate_risk(
    extracted_data: dict,
    validation_result: dict,
    fraud_result: dict,
    gst_compliance: dict,
    buyer_intel: dict,
    credit_score: dict,
    company_info: dict,
) -> dict:
    """Calculate a weighted risk score from all upstream tool outputs.

    Args:
        extracted_data: Structured invoice dict from extract_invoice tool.
        validation_result: Validation dict from validate_fields tool.
        fraud_result: Fraud detection dict from check_fraud tool.
        gst_compliance: GST compliance dict from validate_gst_compliance tool.
        buyer_intel: Buyer intelligence dict from get_buyer_intel tool.
        credit_score: Credit score dict from get_credit_score tool.
        company_info: Company information dict from get_company_info tool.

    Returns:
        Dict with keys: score (int), level (str), explanation (str).
    """
    return _resolve_risk(
        extracted_data,
        validation_result,
        fraud_result,
        gst_compliance,
        buyer_intel,
        credit_score,
        company_info,
    )
