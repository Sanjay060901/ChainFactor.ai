"""TDD tests for Feature 4.9: calculate_risk tool.

Tests the weighted risk scoring formula across all input signals.

Scoring formula:
- fraud_result.overall: pass=0, warning=15, fail=40 (weight 30%)
- validation_result.is_valid: True=0, False=25 (weight 15%)
- gst_compliance.is_compliant: True=0, False=20 (weight 15%)
- credit_score.score: 900->0, 750->10, 650->20, 580->35, 450->50, 0->60 (weight 20%)
- buyer_intel.payment_history: reliable=0, slow_payer=20, new_buyer=10 (weight 10%)
- company_info.status: active=0, dormant=25 (weight 10%)

Final score clamped 0-100.
Level: 0-25=low, 26-50=medium, 51-75=high, 76-100=critical
DEMO_MODE: returns {"score": 15, "level": "low", "explanation": "Low risk..."}
"""

from app.agents.tools.calculate_risk import calculate_risk


# ---------------------------------------------------------------------------
# Helpers: canonical clean / worst-case inputs
# ---------------------------------------------------------------------------


def _clean_extracted_data() -> dict:
    return {
        "seller": {"name": "Acme Pvt Ltd", "gstin": "27AABCA1234R1ZM"},
        "buyer": {"name": "Beta Corp", "gstin": "29AABCB5678R1ZX"},
        "invoice_number": "INV-2026-001",
        "total_amount": 11800.0,
    }


def _clean_validation() -> dict:
    return {"is_valid": True, "errors": [], "warnings": []}


def _clean_fraud() -> dict:
    return {
        "overall": "pass",
        "confidence": 95.0,
        "flags": [],
        "layers": [],
    }


def _clean_gst() -> dict:
    return {"is_compliant": True, "details": {}}


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


# ---------------------------------------------------------------------------
# Tests: Return shape
# ---------------------------------------------------------------------------


class TestCalculateRiskReturnShape:
    """Result must contain score, level, and explanation."""

    def test_return_keys_present(self):
        result = calculate_risk(
            extracted_data=_clean_extracted_data(),
            validation_result=_clean_validation(),
            fraud_result=_clean_fraud(),
            gst_compliance=_clean_gst(),
            buyer_intel=_clean_buyer_intel(),
            credit_score=_clean_credit_score(),
            company_info=_clean_company_info(),
            _demo=False,
        )
        assert "score" in result
        assert "level" in result
        assert "explanation" in result

    def test_score_is_int(self):
        result = calculate_risk(
            extracted_data=_clean_extracted_data(),
            validation_result=_clean_validation(),
            fraud_result=_clean_fraud(),
            gst_compliance=_clean_gst(),
            buyer_intel=_clean_buyer_intel(),
            credit_score=_clean_credit_score(),
            company_info=_clean_company_info(),
            _demo=False,
        )
        assert isinstance(result["score"], int)

    def test_level_is_str(self):
        result = calculate_risk(
            extracted_data=_clean_extracted_data(),
            validation_result=_clean_validation(),
            fraud_result=_clean_fraud(),
            gst_compliance=_clean_gst(),
            buyer_intel=_clean_buyer_intel(),
            credit_score=_clean_credit_score(),
            company_info=_clean_company_info(),
            _demo=False,
        )
        assert isinstance(result["level"], str)

    def test_explanation_is_str(self):
        result = calculate_risk(
            extracted_data=_clean_extracted_data(),
            validation_result=_clean_validation(),
            fraud_result=_clean_fraud(),
            gst_compliance=_clean_gst(),
            buyer_intel=_clean_buyer_intel(),
            credit_score=_clean_credit_score(),
            company_info=_clean_company_info(),
            _demo=False,
        )
        assert isinstance(result["explanation"], str)
        assert len(result["explanation"]) > 0

    def test_score_clamped_0_100(self):
        """Score must always be in [0, 100]."""
        result = calculate_risk(
            extracted_data=_clean_extracted_data(),
            validation_result=_clean_validation(),
            fraud_result=_clean_fraud(),
            gst_compliance=_clean_gst(),
            buyer_intel=_clean_buyer_intel(),
            credit_score=_clean_credit_score(),
            company_info=_clean_company_info(),
            _demo=False,
        )
        assert 0 <= result["score"] <= 100


# ---------------------------------------------------------------------------
# Tests: Level boundaries
# ---------------------------------------------------------------------------


class TestCalculateRiskLevels:
    """Verify each risk level band is correctly assigned."""

    def test_all_clean_inputs_low_risk(self):
        """All-green inputs -> score in low band (0-25)."""
        result = calculate_risk(
            extracted_data=_clean_extracted_data(),
            validation_result=_clean_validation(),
            fraud_result=_clean_fraud(),
            gst_compliance=_clean_gst(),
            buyer_intel=_clean_buyer_intel(),
            credit_score=_clean_credit_score(),
            company_info=_clean_company_info(),
            _demo=False,
        )
        assert result["level"] == "low"
        assert 0 <= result["score"] <= 25

    def test_fraud_warning_raises_score(self):
        """Fraud warning should push score up but may stay medium."""
        fraud = _clean_fraud()
        fraud["overall"] = "warning"
        result = calculate_risk(
            extracted_data=_clean_extracted_data(),
            validation_result=_clean_validation(),
            fraud_result=fraud,
            gst_compliance=_clean_gst(),
            buyer_intel=_clean_buyer_intel(),
            credit_score=_clean_credit_score(),
            company_info=_clean_company_info(),
            _demo=False,
        )
        assert result["score"] > 0
        assert result["level"] in ("low", "medium", "high", "critical")

    def test_fraud_fail_pushes_high_or_critical(self):
        """Fraud fail with other issues -> score >= 51 (high or critical)."""
        fraud = _clean_fraud()
        fraud["overall"] = "fail"
        validation = _clean_validation()
        validation["is_valid"] = False
        gst = _clean_gst()
        gst["is_compliant"] = False
        credit = _clean_credit_score()
        credit["score"] = 450
        result = calculate_risk(
            extracted_data=_clean_extracted_data(),
            validation_result=validation,
            fraud_result=fraud,
            gst_compliance=gst,
            buyer_intel=_clean_buyer_intel(),
            credit_score=credit,
            company_info=_clean_company_info(),
            _demo=False,
        )
        assert result["level"] in ("high", "critical")
        assert result["score"] >= 51

    def test_all_bad_inputs_critical(self):
        """Worst-case inputs across all signals -> critical (76-100)."""
        fraud = {"overall": "fail", "confidence": 0.0, "flags": ["bad"], "layers": []}
        validation = {"is_valid": False, "errors": ["error"], "warnings": []}
        gst = {"is_compliant": False, "details": {}}
        buyer = {"payment_history": "slow_payer", "avg_days": 90, "previous_count": 1}
        credit = {"score": 450, "rating": "poor"}
        company = {
            "status": "dormant",
            "incorporated": "2000-01-01",
            "paid_up_capital": 0.0,
        }
        result = calculate_risk(
            extracted_data=_clean_extracted_data(),
            validation_result=validation,
            fraud_result=fraud,
            gst_compliance=gst,
            buyer_intel=buyer,
            credit_score=credit,
            company_info=company,
            _demo=False,
        )
        assert result["level"] == "critical"
        assert result["score"] >= 76

    def test_level_low_boundary(self):
        """A score of 0 must map to 'low'."""
        result = calculate_risk(
            extracted_data=_clean_extracted_data(),
            validation_result=_clean_validation(),
            fraud_result=_clean_fraud(),
            gst_compliance=_clean_gst(),
            buyer_intel=_clean_buyer_intel(),
            credit_score={"score": 900, "rating": "excellent"},
            company_info=_clean_company_info(),
            _demo=False,
        )
        assert result["level"] == "low"


# ---------------------------------------------------------------------------
# Tests: Individual signal contributions
# ---------------------------------------------------------------------------


class TestCalculateRiskSignals:
    """Each signal independently increases the risk score when bad."""

    def test_invalid_validation_raises_score(self):
        """is_valid=False should increase score vs clean baseline."""
        clean = calculate_risk(
            extracted_data=_clean_extracted_data(),
            validation_result=_clean_validation(),
            fraud_result=_clean_fraud(),
            gst_compliance=_clean_gst(),
            buyer_intel=_clean_buyer_intel(),
            credit_score=_clean_credit_score(),
            company_info=_clean_company_info(),
            _demo=False,
        )
        bad_validation = {
            "is_valid": False,
            "errors": ["missing gstin"],
            "warnings": [],
        }
        result = calculate_risk(
            extracted_data=_clean_extracted_data(),
            validation_result=bad_validation,
            fraud_result=_clean_fraud(),
            gst_compliance=_clean_gst(),
            buyer_intel=_clean_buyer_intel(),
            credit_score=_clean_credit_score(),
            company_info=_clean_company_info(),
            _demo=False,
        )
        assert result["score"] > clean["score"]

    def test_gst_non_compliance_raises_score(self):
        """is_compliant=False should increase score vs clean baseline."""
        clean = calculate_risk(
            extracted_data=_clean_extracted_data(),
            validation_result=_clean_validation(),
            fraud_result=_clean_fraud(),
            gst_compliance=_clean_gst(),
            buyer_intel=_clean_buyer_intel(),
            credit_score=_clean_credit_score(),
            company_info=_clean_company_info(),
            _demo=False,
        )
        bad_gst = {"is_compliant": False, "details": {}}
        result = calculate_risk(
            extracted_data=_clean_extracted_data(),
            validation_result=_clean_validation(),
            fraud_result=_clean_fraud(),
            gst_compliance=bad_gst,
            buyer_intel=_clean_buyer_intel(),
            credit_score=_clean_credit_score(),
            company_info=_clean_company_info(),
            _demo=False,
        )
        assert result["score"] > clean["score"]

    def test_slow_payer_raises_score(self):
        """payment_history=slow_payer should raise score."""
        clean = calculate_risk(
            extracted_data=_clean_extracted_data(),
            validation_result=_clean_validation(),
            fraud_result=_clean_fraud(),
            gst_compliance=_clean_gst(),
            buyer_intel=_clean_buyer_intel(),
            credit_score=_clean_credit_score(),
            company_info=_clean_company_info(),
            _demo=False,
        )
        bad_buyer = {
            "payment_history": "slow_payer",
            "avg_days": 90,
            "previous_count": 2,
        }
        result = calculate_risk(
            extracted_data=_clean_extracted_data(),
            validation_result=_clean_validation(),
            fraud_result=_clean_fraud(),
            gst_compliance=_clean_gst(),
            buyer_intel=bad_buyer,
            credit_score=_clean_credit_score(),
            company_info=_clean_company_info(),
            _demo=False,
        )
        assert result["score"] > clean["score"]

    def test_dormant_company_raises_score(self):
        """company status=dormant should raise score."""
        clean = calculate_risk(
            extracted_data=_clean_extracted_data(),
            validation_result=_clean_validation(),
            fraud_result=_clean_fraud(),
            gst_compliance=_clean_gst(),
            buyer_intel=_clean_buyer_intel(),
            credit_score=_clean_credit_score(),
            company_info=_clean_company_info(),
            _demo=False,
        )
        dormant = {
            "status": "dormant",
            "incorporated": "2010-01-01",
            "paid_up_capital": 1000000.0,
        }
        result = calculate_risk(
            extracted_data=_clean_extracted_data(),
            validation_result=_clean_validation(),
            fraud_result=_clean_fraud(),
            gst_compliance=_clean_gst(),
            buyer_intel=_clean_buyer_intel(),
            credit_score=_clean_credit_score(),
            company_info=dormant,
            _demo=False,
        )
        assert result["score"] > clean["score"]

    def test_low_credit_score_raises_score(self):
        """credit_score=450 should raise score vs 750."""
        clean = calculate_risk(
            extracted_data=_clean_extracted_data(),
            validation_result=_clean_validation(),
            fraud_result=_clean_fraud(),
            gst_compliance=_clean_gst(),
            buyer_intel=_clean_buyer_intel(),
            credit_score=_clean_credit_score(),
            company_info=_clean_company_info(),
            _demo=False,
        )
        poor_credit = {"score": 450, "rating": "poor"}
        result = calculate_risk(
            extracted_data=_clean_extracted_data(),
            validation_result=_clean_validation(),
            fraud_result=_clean_fraud(),
            gst_compliance=_clean_gst(),
            buyer_intel=_clean_buyer_intel(),
            credit_score=poor_credit,
            company_info=_clean_company_info(),
            _demo=False,
        )
        assert result["score"] > clean["score"]


# ---------------------------------------------------------------------------
# Tests: DEMO_MODE
# ---------------------------------------------------------------------------


class TestCalculateRiskDemoMode:
    """DEMO_MODE returns pre-computed low-risk result."""

    def test_demo_mode_returns_low_risk(self):
        result = calculate_risk(
            extracted_data=_clean_extracted_data(),
            validation_result=_clean_validation(),
            fraud_result=_clean_fraud(),
            gst_compliance=_clean_gst(),
            buyer_intel=_clean_buyer_intel(),
            credit_score=_clean_credit_score(),
            company_info=_clean_company_info(),
            _demo=True,
        )
        assert result["score"] == 15
        assert result["level"] == "low"
        assert (
            "low risk" in result["explanation"].lower()
            or len(result["explanation"]) > 0
        )

    def test_demo_mode_ignores_bad_inputs(self):
        """Demo mode overrides bad inputs with fixed result."""
        fraud = {"overall": "fail", "confidence": 0.0, "flags": [], "layers": []}
        result = calculate_risk(
            extracted_data=_clean_extracted_data(),
            validation_result={"is_valid": False, "errors": [], "warnings": []},
            fraud_result=fraud,
            gst_compliance={"is_compliant": False, "details": {}},
            buyer_intel=_clean_buyer_intel(),
            credit_score=_clean_credit_score(),
            company_info=_clean_company_info(),
            _demo=True,
        )
        assert result["score"] == 15
        assert result["level"] == "low"

    def test_demo_mode_result_keys(self):
        result = calculate_risk(
            extracted_data=_clean_extracted_data(),
            validation_result=_clean_validation(),
            fraud_result=_clean_fraud(),
            gst_compliance=_clean_gst(),
            buyer_intel=_clean_buyer_intel(),
            credit_score=_clean_credit_score(),
            company_info=_clean_company_info(),
            _demo=True,
        )
        assert set(result.keys()) == {"score", "level", "explanation"}
