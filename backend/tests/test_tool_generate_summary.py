"""TDD tests for Feature 4.10: generate_summary tool.

Tests the deterministic summary generation (no LLM calls).

Logic:
- summary: "Invoice {invoice_number} from {seller.name} to {buyer.name}
            for Rs{total_amount}. Risk: {risk.level} ({risk.score}/100)."
- highlights: notable findings (fraud warnings, GST issues, credit concerns, etc.)
- recommendation: "approve" (low/medium), "review" (high), "reject" (critical)
- DEMO_MODE: returns pre-computed summary
"""

from app.agents.tools.generate_summary import generate_summary


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _clean_extracted() -> dict:
    return {
        "seller": {"name": "Acme Pvt Ltd", "gstin": "27AABCA1234R1ZM"},
        "buyer": {"name": "Beta Corp", "gstin": "29AABCB5678R1ZX"},
        "invoice_number": "INV-2026-001",
        "invoice_date": "2026-03-15",
        "due_date": "2026-04-15",
        "total_amount": 11800.0,
        "subtotal": 10000.0,
        "tax_amount": 1800.0,
        "tax_rate": 18.0,
        "line_items": [],
    }


def _clean_validation() -> dict:
    return {"is_valid": True, "errors": [], "warnings": []}


def _clean_fraud() -> dict:
    return {"overall": "pass", "confidence": 95.0, "flags": [], "layers": []}


def _clean_gst() -> dict:
    return {"is_compliant": True, "details": {}}


def _clean_gstin() -> dict:
    return {
        "verified": True,
        "status": "active",
        "details": {
            "seller_gstin_active": True,
            "buyer_gstin_active": True,
            "seller_on_blocklist": False,
            "buyer_on_blocklist": False,
        },
    }


def _clean_buyer_intel() -> dict:
    return {"payment_history": "reliable", "avg_days": 28, "previous_count": 8}


def _clean_credit_score() -> dict:
    return {"score": 750, "rating": "good"}


def _clean_company_info() -> dict:
    return {
        "status": "active",
        "incorporated": "2010-01-01",
        "paid_up_capital": 1000000.0,
    }


def _low_risk() -> dict:
    return {"score": 15, "level": "low", "explanation": "Low risk invoice."}


def _high_risk() -> dict:
    return {"score": 60, "level": "high", "explanation": "High risk due to fraud flag."}


def _critical_risk() -> dict:
    return {
        "score": 85,
        "level": "critical",
        "explanation": "Critical: multiple failures.",
    }


# ---------------------------------------------------------------------------
# Tests: Return shape
# ---------------------------------------------------------------------------


class TestGenerateSummaryReturnShape:
    """Result must contain summary, highlights, and recommendation."""

    def test_return_keys_present(self):
        result = generate_summary(
            extracted_data=_clean_extracted(),
            validation_result=_clean_validation(),
            fraud_result=_clean_fraud(),
            gst_compliance=_clean_gst(),
            gstin_verification=_clean_gstin(),
            buyer_intel=_clean_buyer_intel(),
            credit_score=_clean_credit_score(),
            company_info=_clean_company_info(),
            risk_assessment=_low_risk(),
            _demo=False,
        )
        assert "summary" in result
        assert "highlights" in result
        assert "recommendation" in result

    def test_summary_is_str(self):
        result = generate_summary(
            extracted_data=_clean_extracted(),
            validation_result=_clean_validation(),
            fraud_result=_clean_fraud(),
            gst_compliance=_clean_gst(),
            gstin_verification=_clean_gstin(),
            buyer_intel=_clean_buyer_intel(),
            credit_score=_clean_credit_score(),
            company_info=_clean_company_info(),
            risk_assessment=_low_risk(),
            _demo=False,
        )
        assert isinstance(result["summary"], str)
        assert len(result["summary"]) > 0

    def test_highlights_is_list(self):
        result = generate_summary(
            extracted_data=_clean_extracted(),
            validation_result=_clean_validation(),
            fraud_result=_clean_fraud(),
            gst_compliance=_clean_gst(),
            gstin_verification=_clean_gstin(),
            buyer_intel=_clean_buyer_intel(),
            credit_score=_clean_credit_score(),
            company_info=_clean_company_info(),
            risk_assessment=_low_risk(),
            _demo=False,
        )
        assert isinstance(result["highlights"], list)

    def test_recommendation_is_str(self):
        result = generate_summary(
            extracted_data=_clean_extracted(),
            validation_result=_clean_validation(),
            fraud_result=_clean_fraud(),
            gst_compliance=_clean_gst(),
            gstin_verification=_clean_gstin(),
            buyer_intel=_clean_buyer_intel(),
            credit_score=_clean_credit_score(),
            company_info=_clean_company_info(),
            risk_assessment=_low_risk(),
            _demo=False,
        )
        assert isinstance(result["recommendation"], str)


# ---------------------------------------------------------------------------
# Tests: Summary content
# ---------------------------------------------------------------------------


class TestGenerateSummaryContent:
    """Verify the summary string contains expected invoice identifiers."""

    def test_summary_contains_invoice_number(self):
        result = generate_summary(
            extracted_data=_clean_extracted(),
            validation_result=_clean_validation(),
            fraud_result=_clean_fraud(),
            gst_compliance=_clean_gst(),
            gstin_verification=_clean_gstin(),
            buyer_intel=_clean_buyer_intel(),
            credit_score=_clean_credit_score(),
            company_info=_clean_company_info(),
            risk_assessment=_low_risk(),
            _demo=False,
        )
        assert "INV-2026-001" in result["summary"]

    def test_summary_contains_seller_name(self):
        result = generate_summary(
            extracted_data=_clean_extracted(),
            validation_result=_clean_validation(),
            fraud_result=_clean_fraud(),
            gst_compliance=_clean_gst(),
            gstin_verification=_clean_gstin(),
            buyer_intel=_clean_buyer_intel(),
            credit_score=_clean_credit_score(),
            company_info=_clean_company_info(),
            risk_assessment=_low_risk(),
            _demo=False,
        )
        assert "Acme Pvt Ltd" in result["summary"]

    def test_summary_contains_buyer_name(self):
        result = generate_summary(
            extracted_data=_clean_extracted(),
            validation_result=_clean_validation(),
            fraud_result=_clean_fraud(),
            gst_compliance=_clean_gst(),
            gstin_verification=_clean_gstin(),
            buyer_intel=_clean_buyer_intel(),
            credit_score=_clean_credit_score(),
            company_info=_clean_company_info(),
            risk_assessment=_low_risk(),
            _demo=False,
        )
        assert "Beta Corp" in result["summary"]

    def test_summary_contains_risk_level(self):
        result = generate_summary(
            extracted_data=_clean_extracted(),
            validation_result=_clean_validation(),
            fraud_result=_clean_fraud(),
            gst_compliance=_clean_gst(),
            gstin_verification=_clean_gstin(),
            buyer_intel=_clean_buyer_intel(),
            credit_score=_clean_credit_score(),
            company_info=_clean_company_info(),
            risk_assessment=_low_risk(),
            _demo=False,
        )
        assert "low" in result["summary"].lower()

    def test_summary_contains_risk_score(self):
        result = generate_summary(
            extracted_data=_clean_extracted(),
            validation_result=_clean_validation(),
            fraud_result=_clean_fraud(),
            gst_compliance=_clean_gst(),
            gstin_verification=_clean_gstin(),
            buyer_intel=_clean_buyer_intel(),
            credit_score=_clean_credit_score(),
            company_info=_clean_company_info(),
            risk_assessment=_low_risk(),
            _demo=False,
        )
        # "15/100" or "15" must appear in summary
        assert "15" in result["summary"]


# ---------------------------------------------------------------------------
# Tests: Recommendation logic
# ---------------------------------------------------------------------------


class TestGenerateSummaryRecommendation:
    """recommendation maps from risk level."""

    def test_low_risk_approves(self):
        result = generate_summary(
            extracted_data=_clean_extracted(),
            validation_result=_clean_validation(),
            fraud_result=_clean_fraud(),
            gst_compliance=_clean_gst(),
            gstin_verification=_clean_gstin(),
            buyer_intel=_clean_buyer_intel(),
            credit_score=_clean_credit_score(),
            company_info=_clean_company_info(),
            risk_assessment=_low_risk(),
            _demo=False,
        )
        assert result["recommendation"] == "approve"

    def test_medium_risk_approves(self):
        medium_risk = {"score": 35, "level": "medium", "explanation": "Medium risk."}
        result = generate_summary(
            extracted_data=_clean_extracted(),
            validation_result=_clean_validation(),
            fraud_result=_clean_fraud(),
            gst_compliance=_clean_gst(),
            gstin_verification=_clean_gstin(),
            buyer_intel=_clean_buyer_intel(),
            credit_score=_clean_credit_score(),
            company_info=_clean_company_info(),
            risk_assessment=medium_risk,
            _demo=False,
        )
        assert result["recommendation"] == "approve"

    def test_high_risk_review(self):
        result = generate_summary(
            extracted_data=_clean_extracted(),
            validation_result=_clean_validation(),
            fraud_result=_clean_fraud(),
            gst_compliance=_clean_gst(),
            gstin_verification=_clean_gstin(),
            buyer_intel=_clean_buyer_intel(),
            credit_score=_clean_credit_score(),
            company_info=_clean_company_info(),
            risk_assessment=_high_risk(),
            _demo=False,
        )
        assert result["recommendation"] == "review"

    def test_critical_risk_reject(self):
        result = generate_summary(
            extracted_data=_clean_extracted(),
            validation_result=_clean_validation(),
            fraud_result=_clean_fraud(),
            gst_compliance=_clean_gst(),
            gstin_verification=_clean_gstin(),
            buyer_intel=_clean_buyer_intel(),
            credit_score=_clean_credit_score(),
            company_info=_clean_company_info(),
            risk_assessment=_critical_risk(),
            _demo=False,
        )
        assert result["recommendation"] == "reject"


# ---------------------------------------------------------------------------
# Tests: Highlights population
# ---------------------------------------------------------------------------


class TestGenerateSummaryHighlights:
    """Highlights list should surface notable issues."""

    def test_clean_invoice_highlights_empty_or_positive(self):
        """A fully clean invoice may have empty or positive-only highlights."""
        result = generate_summary(
            extracted_data=_clean_extracted(),
            validation_result=_clean_validation(),
            fraud_result=_clean_fraud(),
            gst_compliance=_clean_gst(),
            gstin_verification=_clean_gstin(),
            buyer_intel=_clean_buyer_intel(),
            credit_score=_clean_credit_score(),
            company_info=_clean_company_info(),
            risk_assessment=_low_risk(),
            _demo=False,
        )
        # highlights is a list (may be empty for clean invoices)
        assert isinstance(result["highlights"], list)

    def test_fraud_warning_appears_in_highlights(self):
        """Fraud warning or fail should appear in highlights."""
        fraud = {
            "overall": "warning",
            "confidence": 70.0,
            "flags": ["Suspicious pattern"],
            "layers": [],
        }
        result = generate_summary(
            extracted_data=_clean_extracted(),
            validation_result=_clean_validation(),
            fraud_result=fraud,
            gst_compliance=_clean_gst(),
            gstin_verification=_clean_gstin(),
            buyer_intel=_clean_buyer_intel(),
            credit_score=_clean_credit_score(),
            company_info=_clean_company_info(),
            risk_assessment=_high_risk(),
            _demo=False,
        )
        highlights_text = " ".join(result["highlights"]).lower()
        assert len(result["highlights"]) > 0
        assert any(
            "fraud" in h.lower() or "suspicious" in h.lower() or "warning" in h.lower()
            for h in result["highlights"]
        )

    def test_gst_non_compliance_appears_in_highlights(self):
        """GST non-compliance should surface in highlights."""
        gst = {"is_compliant": False, "details": {}}
        result = generate_summary(
            extracted_data=_clean_extracted(),
            validation_result=_clean_validation(),
            fraud_result=_clean_fraud(),
            gst_compliance=gst,
            gstin_verification=_clean_gstin(),
            buyer_intel=_clean_buyer_intel(),
            credit_score=_clean_credit_score(),
            company_info=_clean_company_info(),
            risk_assessment=_high_risk(),
            _demo=False,
        )
        assert any(
            "gst" in h.lower() or "complian" in h.lower() for h in result["highlights"]
        )

    def test_slow_payer_appears_in_highlights(self):
        """Slow payer buyer_intel should appear in highlights."""
        buyer = {"payment_history": "slow_payer", "avg_days": 90, "previous_count": 2}
        result = generate_summary(
            extracted_data=_clean_extracted(),
            validation_result=_clean_validation(),
            fraud_result=_clean_fraud(),
            gst_compliance=_clean_gst(),
            gstin_verification=_clean_gstin(),
            buyer_intel=buyer,
            credit_score=_clean_credit_score(),
            company_info=_clean_company_info(),
            risk_assessment=_high_risk(),
            _demo=False,
        )
        assert any(
            "slow" in h.lower() or "payment" in h.lower() or "payer" in h.lower()
            for h in result["highlights"]
        )

    def test_validation_error_appears_in_highlights(self):
        """Validation failure should surface in highlights."""
        validation = {"is_valid": False, "errors": ["GSTIN missing"], "warnings": []}
        result = generate_summary(
            extracted_data=_clean_extracted(),
            validation_result=validation,
            fraud_result=_clean_fraud(),
            gst_compliance=_clean_gst(),
            gstin_verification=_clean_gstin(),
            buyer_intel=_clean_buyer_intel(),
            credit_score=_clean_credit_score(),
            company_info=_clean_company_info(),
            risk_assessment=_high_risk(),
            _demo=False,
        )
        assert any(
            "valid" in h.lower() or "error" in h.lower() or "field" in h.lower()
            for h in result["highlights"]
        )


# ---------------------------------------------------------------------------
# Tests: DEMO_MODE
# ---------------------------------------------------------------------------


class TestGenerateSummaryDemoMode:
    """DEMO_MODE returns a pre-computed summary."""

    def test_demo_returns_full_shape(self):
        result = generate_summary(
            extracted_data=_clean_extracted(),
            validation_result=_clean_validation(),
            fraud_result=_clean_fraud(),
            gst_compliance=_clean_gst(),
            gstin_verification=_clean_gstin(),
            buyer_intel=_clean_buyer_intel(),
            credit_score=_clean_credit_score(),
            company_info=_clean_company_info(),
            risk_assessment=_low_risk(),
            _demo=True,
        )
        assert "summary" in result
        assert "highlights" in result
        assert "recommendation" in result

    def test_demo_recommendation_approve(self):
        """Pre-computed demo invoice is low risk -> approve."""
        result = generate_summary(
            extracted_data=_clean_extracted(),
            validation_result=_clean_validation(),
            fraud_result=_clean_fraud(),
            gst_compliance=_clean_gst(),
            gstin_verification=_clean_gstin(),
            buyer_intel=_clean_buyer_intel(),
            credit_score=_clean_credit_score(),
            company_info=_clean_company_info(),
            risk_assessment=_low_risk(),
            _demo=True,
        )
        assert result["recommendation"] == "approve"

    def test_demo_ignores_critical_risk_input(self):
        """Demo mode returns pre-computed result, ignores critical risk_assessment."""
        result = generate_summary(
            extracted_data=_clean_extracted(),
            validation_result=_clean_validation(),
            fraud_result=_clean_fraud(),
            gst_compliance=_clean_gst(),
            gstin_verification=_clean_gstin(),
            buyer_intel=_clean_buyer_intel(),
            credit_score=_clean_credit_score(),
            company_info=_clean_company_info(),
            risk_assessment=_critical_risk(),
            _demo=True,
        )
        # Demo always returns approve pre-computed; must NOT be "reject"
        assert result["recommendation"] == "approve"
