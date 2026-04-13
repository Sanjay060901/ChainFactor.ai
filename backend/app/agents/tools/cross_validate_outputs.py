"""cross_validate_outputs tool: Checks consistency across all pipeline outputs.

Validates that outputs from different tools in the Invoice Processing Agent
pipeline are internally consistent. Catches discrepancies like:
  - Amounts in extracted_data not matching validation_result
  - GSTIN active status in gstn_verification not matching company_info status
  - Fraud pass/fail misaligned with risk_score level
  - Buyer intel payment history inconsistent with credit score range

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

# Risk score thresholds for consistency checks
_HIGH_RISK_THRESHOLD = 30  # Below this = high risk
_LOW_RISK_THRESHOLD = 70  # Above this = low risk


# ---------------------------------------------------------------------------
# Internal implementation (pure logic, no Strands dependency)
# ---------------------------------------------------------------------------


def _resolve_cross_validate(
    extracted_data: dict,
    validation_result: dict,
    fraud_result: dict,
    gst_compliance: dict,
    gstn_verification: dict,
    buyer_intel: dict,
    credit_score: dict,
    company_info: dict,
    risk_assessment: dict,
) -> dict:
    """Core cross-validation logic, separated from the Strands decorator."""
    discrepancies: list[str] = []

    # Check 1: Amounts in extracted_data match validation_result
    extracted_amount = extracted_data.get("total_amount")
    validated_amount = validation_result.get("total_amount")
    if (
        extracted_amount is not None
        and validated_amount is not None
        and abs(float(extracted_amount) - float(validated_amount)) > 0.01
    ):
        discrepancies.append(
            f"Amount mismatch: extracted={extracted_amount}, validated={validated_amount}"
        )

    # Check 2: GSTIN active in gstn_verification matches company_info status
    gstn_active = gstn_verification.get("active")
    company_status = company_info.get("status", "").lower()
    if gstn_active is not None:
        if gstn_active and company_status in ("inactive", "cancelled", "suspended"):
            discrepancies.append(
                f"GSTIN shows active but company status is '{company_status}'"
            )
        elif not gstn_active and company_status == "active":
            discrepancies.append("GSTIN shows inactive but company status is 'active'")

    # Check 3: Fraud result aligns with risk score level
    fraud_overall = fraud_result.get("overall_result", "").lower()
    risk_score = risk_assessment.get("risk_score")
    if risk_score is not None:
        risk_score_val = int(risk_score)
        if fraud_overall == "fail" and risk_score_val > _LOW_RISK_THRESHOLD:
            discrepancies.append(
                f"Fraud detection failed but risk score is high ({risk_score_val})"
            )
        elif fraud_overall == "pass" and risk_score_val < _HIGH_RISK_THRESHOLD:
            discrepancies.append(
                f"Fraud detection passed but risk score is very low ({risk_score_val})"
            )

    # Check 4: Buyer intel payment history consistent with credit score
    payment_history = buyer_intel.get("payment_history", "").lower()
    cibil_score = credit_score.get("cibil_score")
    if cibil_score is not None:
        cibil_val = int(cibil_score)
        if payment_history == "reliable" and cibil_val < 500:
            discrepancies.append(
                f"Buyer shows reliable payment history but CIBIL score is very low ({cibil_val})"
            )
        elif payment_history == "slow_payer" and cibil_val > 800:
            discrepancies.append(
                f"Buyer shows slow payment history but CIBIL score is excellent ({cibil_val})"
            )

    # Check 5: GST compliance status vs extracted tax rate
    gst_valid = gst_compliance.get("compliant", gst_compliance.get("valid"))
    tax_rate = extracted_data.get("tax_rate")
    if gst_valid is False and tax_rate is not None and float(tax_rate) > 0:
        discrepancies.append(
            "GST compliance check failed but invoice has non-zero tax rate"
        )

    # Calculate confidence based on number of discrepancies
    consistent = len(discrepancies) == 0
    if consistent:
        confidence = 0.95
    elif len(discrepancies) <= 2:
        confidence = round(0.7 - (len(discrepancies) * 0.1), 2)
    else:
        confidence = round(max(0.2, 0.7 - (len(discrepancies) * 0.15)), 2)

    logger.info(
        "Cross-validation complete: consistent=%s, discrepancies=%d, confidence=%.2f",
        consistent,
        len(discrepancies),
        confidence,
    )

    return {
        "consistent": consistent,
        "discrepancies": discrepancies,
        "confidence": confidence,
    }


# ---------------------------------------------------------------------------
# Strands @tool  (registered with the agent; no leading-underscore params)
# ---------------------------------------------------------------------------


@tool
def _cross_validate_outputs_tool(
    extracted_data: dict,
    validation_result: dict,
    fraud_result: dict,
    gst_compliance: dict,
    gstn_verification: dict,
    buyer_intel: dict,
    credit_score: dict,
    company_info: dict,
    risk_assessment: dict,
) -> dict:
    """Cross-validate all pipeline outputs for consistency.

    Checks that amounts match across tools, GSTIN status is consistent,
    fraud results align with risk scores, and buyer intel matches credit data.

    Args:
        extracted_data: Output from extract_invoice tool.
        validation_result: Output from validate_fields tool.
        fraud_result: Output from check_fraud tool.
        gst_compliance: Output from validate_gst_compliance tool.
        gstn_verification: Output from verify_gstn tool.
        buyer_intel: Output from get_buyer_intel tool.
        credit_score: Output from get_credit_score tool.
        company_info: Output from get_company_info tool.
        risk_assessment: Output from calculate_risk tool.
    """
    return _resolve_cross_validate(
        extracted_data=extracted_data,
        validation_result=validation_result,
        fraud_result=fraud_result,
        gst_compliance=gst_compliance,
        gstn_verification=gstn_verification,
        buyer_intel=buyer_intel,
        credit_score=credit_score,
        company_info=company_info,
        risk_assessment=risk_assessment,
    )


# ---------------------------------------------------------------------------
# Public callable (used by tests and by agent tool list)
# ---------------------------------------------------------------------------


def cross_validate_outputs(
    extracted_data: dict,
    validation_result: dict,
    fraud_result: dict,
    gst_compliance: dict,
    gstn_verification: dict,
    buyer_intel: dict,
    credit_score: dict,
    company_info: dict,
    risk_assessment: dict,
) -> dict:
    """Cross-validate all pipeline outputs for consistency.

    Args:
        extracted_data: Output from extract_invoice tool.
        validation_result: Output from validate_fields tool.
        fraud_result: Output from check_fraud tool.
        gst_compliance: Output from validate_gst_compliance tool.
        gstn_verification: Output from verify_gstn tool.
        buyer_intel: Output from get_buyer_intel tool.
        credit_score: Output from get_credit_score tool.
        company_info: Output from get_company_info tool.
        risk_assessment: Output from calculate_risk tool.

    Returns:
        Dict with consistent (bool), discrepancies (list[str]), confidence (float).
    """
    return _resolve_cross_validate(
        extracted_data=extracted_data,
        validation_result=validation_result,
        fraud_result=fraud_result,
        gst_compliance=gst_compliance,
        gstn_verification=gstn_verification,
        buyer_intel=buyer_intel,
        credit_score=credit_score,
        company_info=company_info,
        risk_assessment=risk_assessment,
    )
