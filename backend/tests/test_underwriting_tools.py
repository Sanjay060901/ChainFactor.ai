"""TDD tests for Feature 4.11: Underwriting Agent tools.

Tests all 7 underwriting tools independently in both demo and real modes:
  1. cross_validate_outputs -- consistency checks across pipeline outputs
  2. get_seller_rules -- seller-defined auto-approval thresholds
  3. get_invoice_data -- mock invoice retrieval
  4. approve_invoice -- approval decision record
  5. reject_invoice -- rejection decision record
  6. flag_for_review -- flag-for-review decision record
  7. log_decision -- audit log with UUID trace_id
"""

import uuid
from datetime import datetime

from app.agents.tools.approve_invoice import approve_invoice
from app.agents.tools.cross_validate_outputs import cross_validate_outputs
from app.agents.tools.flag_for_review import flag_for_review
from app.agents.tools.get_invoice_data import get_invoice_data
from app.agents.tools.get_seller_rules import get_seller_rules
from app.agents.tools.log_decision import log_decision
from app.agents.tools.reject_invoice import reject_invoice


# ---------------------------------------------------------------------------
# Helpers: consistent pipeline data for cross_validate tests
# ---------------------------------------------------------------------------


def _make_consistent_data() -> dict:
    """Return a set of pipeline outputs that are internally consistent."""
    return {
        "extracted_data": {
            "total_amount": 501500.00,
            "tax_rate": 18.0,
        },
        "validation_result": {
            "total_amount": 501500.00,
            "valid": True,
        },
        "fraud_result": {
            "overall_result": "pass",
            "flags": [],
        },
        "gst_compliance": {
            "compliant": True,
        },
        "gstn_verification": {
            "active": True,
        },
        "buyer_intel": {
            "payment_history": "reliable",
            "avg_days": 28,
        },
        "credit_score": {
            "cibil_score": 750,
        },
        "company_info": {
            "status": "active",
        },
        "risk_assessment": {
            "risk_score": 75,
        },
    }


def _make_inconsistent_data() -> dict:
    """Return pipeline outputs with multiple discrepancies."""
    return {
        "extracted_data": {
            "total_amount": 501500.00,
            "tax_rate": 18.0,
        },
        "validation_result": {
            "total_amount": 400000.00,  # Mismatch with extracted
            "valid": True,
        },
        "fraud_result": {
            "overall_result": "fail",  # Fraud failed
            "flags": ["duplicate_invoice"],
        },
        "gst_compliance": {
            "compliant": True,
        },
        "gstn_verification": {
            "active": True,
        },
        "buyer_intel": {
            "payment_history": "slow_payer",  # Slow payer
            "avg_days": 65,
        },
        "credit_score": {
            "cibil_score": 850,  # Inconsistent: slow payer but excellent CIBIL
        },
        "company_info": {
            "status": "inactive",  # Inconsistent: GSTIN active but company inactive
        },
        "risk_assessment": {
            "risk_score": 80,  # Inconsistent: fraud failed but high risk score
        },
    }


# ===========================================================================
# cross_validate_outputs
# ===========================================================================


class TestCrossValidateOutputs:
    """Test cross-validation consistency checks."""

    def test_consistent_data_returns_consistent_true(self):
        """All consistent data should yield consistent=true with no discrepancies."""
        data = _make_consistent_data()
        result = cross_validate_outputs(**data)
        assert result["consistent"] is True
        assert result["discrepancies"] == []
        assert result["confidence"] > 0.9

    def test_inconsistent_data_catches_discrepancies(self):
        """Inconsistent data should yield consistent=false with discrepancies listed."""
        data = _make_inconsistent_data()
        result = cross_validate_outputs(**data)
        assert result["consistent"] is False
        assert len(result["discrepancies"]) >= 2
        assert result["confidence"] < 0.9

    def test_amount_mismatch_detected(self):
        """Should detect when extracted and validated amounts differ."""
        data = _make_consistent_data()
        data["validation_result"]["total_amount"] = 999999.99
        result = cross_validate_outputs(**data)
        assert result["consistent"] is False
        assert any("Amount mismatch" in d for d in result["discrepancies"])

    def test_gstin_company_status_mismatch(self):
        """Should detect GSTIN active but company inactive."""
        data = _make_consistent_data()
        data["company_info"]["status"] = "cancelled"
        result = cross_validate_outputs(**data)
        assert result["consistent"] is False
        assert any("company status" in d for d in result["discrepancies"])

    def test_fraud_risk_mismatch(self):
        """Should detect fraud fail with high risk score."""
        data = _make_consistent_data()
        data["fraud_result"]["overall_result"] = "fail"
        data["risk_assessment"]["risk_score"] = 80
        result = cross_validate_outputs(**data)
        assert result["consistent"] is False
        assert any("Fraud" in d for d in result["discrepancies"])

    def test_buyer_credit_mismatch(self):
        """Should detect slow payer with excellent CIBIL."""
        data = _make_consistent_data()
        data["buyer_intel"]["payment_history"] = "slow_payer"
        data["credit_score"]["cibil_score"] = 850
        result = cross_validate_outputs(**data)
        assert result["consistent"] is False
        assert any("CIBIL" in d for d in result["discrepancies"])

    def test_return_shape(self):
        """Return dict must have exactly consistent, discrepancies, confidence."""
        data = _make_consistent_data()
        result = cross_validate_outputs(**data)
        assert set(result.keys()) == {"consistent", "discrepancies", "confidence"}
        assert isinstance(result["consistent"], bool)
        assert isinstance(result["discrepancies"], list)
        assert isinstance(result["confidence"], float)


class TestCrossValidateDemo:
    """Demo mode for cross_validate_outputs."""


class TestGetSellerRules:
    """Test seller rules lookup by seller_id prefix."""

    def test_seller_1_returns_permissive(self):
        """seller_1* prefix should return permissive rules."""
        result = get_seller_rules(seller_id="seller_1_tata")
        assert result["max_amount"] == 1000000.0
        assert result["min_risk_score"] == 30
        assert result["min_cibil_score"] == 600
        assert result["max_fraud_flags"] == 2
        assert result["auto_approve_enabled"] is True

    def test_seller_2_returns_strict(self):
        """seller_2* prefix should return strict rules."""
        result = get_seller_rules(seller_id="seller_2_adani")
        assert result["max_amount"] == 200000.0
        assert result["min_risk_score"] == 20
        assert result["min_cibil_score"] == 750
        assert result["max_fraud_flags"] == 0
        assert result["auto_approve_enabled"] is True

    def test_unknown_seller_returns_moderate(self):
        """Unknown seller_id should return moderate defaults."""
        result = get_seller_rules(seller_id="some_other_seller")
        assert result["max_amount"] == 500000.0
        assert result["min_risk_score"] == 40
        assert result["min_cibil_score"] == 650
        assert result["max_fraud_flags"] == 1
        assert result["auto_approve_enabled"] is True

    def test_return_shape(self):
        result = get_seller_rules(seller_id="seller_1_any")
        expected_keys = {
            "max_amount",
            "min_risk_score",
            "min_cibil_score",
            "max_fraud_flags",
            "auto_approve_enabled",
        }
        assert set(result.keys()) == expected_keys


class TestGetSellerRulesDemo:
    """Demo mode for get_seller_rules."""


class TestGetInvoiceData:
    """Test invoice data retrieval."""

    def test_known_invoice_001(self):
        result = get_invoice_data(invoice_id="demo-invoice-001")
        assert result["invoice_id"] == "demo-invoice-001"
        assert result["amount"] == 501500.00
        assert result["seller_id"] == "seller_1_tata"

    def test_known_invoice_002(self):
        result = get_invoice_data(invoice_id="demo-invoice-002")
        assert result["invoice_id"] == "demo-invoice-002"
        assert result["amount"] == 150000.00

    def test_known_invoice_003(self):
        result = get_invoice_data(invoice_id="demo-invoice-003")
        assert result["invoice_id"] == "demo-invoice-003"
        assert result["amount"] == 7500000.00

    def test_unknown_invoice_returns_generic(self):
        result = get_invoice_data(invoice_id="unknown-123")
        assert result["invoice_id"] == "unknown-123"
        assert result["amount"] == 250000.00
        assert result["seller_id"] == "seller_unknown"

    def test_return_shape(self):
        result = get_invoice_data(invoice_id="demo-invoice-001")
        expected_keys = {
            "invoice_id",
            "status",
            "amount",
            "seller_id",
            "buyer_gstin",
            "created_at",
            "s3_key",
        }
        assert set(result.keys()) == expected_keys


class TestGetInvoiceDataDemo:
    """Demo mode for get_invoice_data."""


class TestApproveInvoice:
    """Test approval decision record."""

    def test_returns_approved_decision(self):
        result = approve_invoice(
            invoice_id="inv-001",
            reason="All checks passed",
            risk_score=85,
            confidence=0.95,
        )
        assert result["decision"] == "approved"
        assert result["invoice_id"] == "inv-001"
        assert result["reason"] == "All checks passed"
        assert result["risk_score"] == 85
        assert result["confidence"] == 0.95

    def test_has_timestamp(self):
        result = approve_invoice(
            invoice_id="inv-001",
            reason="Good",
            risk_score=80,
            confidence=0.9,
        )
        assert "timestamp" in result
        # Should be a valid ISO format timestamp
        datetime.fromisoformat(result["timestamp"])

    def test_return_keys(self):
        result = approve_invoice(
            invoice_id="inv-001",
            reason="OK",
            risk_score=80,
            confidence=0.9,
        )
        expected_keys = {
            "decision",
            "invoice_id",
            "reason",
            "risk_score",
            "confidence",
            "timestamp",
        }
        assert set(result.keys()) == expected_keys


# ===========================================================================
# reject_invoice
# ===========================================================================


class TestRejectInvoice:
    """Test rejection decision record."""

    def test_returns_rejected_decision(self):
        result = reject_invoice(
            invoice_id="inv-002",
            reason="Critical fraud detected",
            risk_score=15,
            fraud_flags=["duplicate_invoice", "fake_gstin"],
        )
        assert result["decision"] == "rejected"
        assert result["invoice_id"] == "inv-002"
        assert result["reason"] == "Critical fraud detected"
        assert result["risk_score"] == 15
        assert result["fraud_flags"] == ["duplicate_invoice", "fake_gstin"]

    def test_has_timestamp(self):
        result = reject_invoice(
            invoice_id="inv-002",
            reason="Bad",
            risk_score=10,
            fraud_flags=[],
        )
        assert "timestamp" in result
        datetime.fromisoformat(result["timestamp"])

    def test_return_keys(self):
        result = reject_invoice(
            invoice_id="inv-002",
            reason="Bad",
            risk_score=10,
            fraud_flags=["flag1"],
        )
        expected_keys = {
            "decision",
            "invoice_id",
            "reason",
            "risk_score",
            "fraud_flags",
            "timestamp",
        }
        assert set(result.keys()) == expected_keys


# ===========================================================================
# flag_for_review
# ===========================================================================


class TestFlagForReview:
    """Test flag-for-review decision record."""

    def test_returns_flagged_decision(self):
        result = flag_for_review(
            invoice_id="inv-003",
            reason="Borderline risk score",
            discrepancies=["amount mismatch", "GSTIN status conflict"],
            risk_score=45,
        )
        assert result["decision"] == "flagged_for_review"
        assert result["invoice_id"] == "inv-003"
        assert result["reason"] == "Borderline risk score"
        assert result["discrepancies"] == [
            "amount mismatch",
            "GSTIN status conflict",
        ]
        assert result["risk_score"] == 45

    def test_has_timestamp(self):
        result = flag_for_review(
            invoice_id="inv-003",
            reason="Review",
            discrepancies=[],
            risk_score=50,
        )
        assert "timestamp" in result
        datetime.fromisoformat(result["timestamp"])

    def test_return_keys(self):
        result = flag_for_review(
            invoice_id="inv-003",
            reason="Review",
            discrepancies=[],
            risk_score=50,
        )
        expected_keys = {
            "decision",
            "invoice_id",
            "reason",
            "discrepancies",
            "risk_score",
            "timestamp",
        }
        assert set(result.keys()) == expected_keys


# ===========================================================================
# log_decision
# ===========================================================================


class TestLogDecision:
    """Test decision audit logging."""

    def test_returns_logged_true(self):
        result = log_decision(
            invoice_id="inv-001",
            decision="approved",
            reasoning_trace="All signals green. Risk score 85. CIBIL 750.",
            all_signals={"risk_score": 85, "cibil": 750},
        )
        assert result["logged"] is True
        assert result["invoice_id"] == "inv-001"
        assert result["decision"] == "approved"

    def test_returns_uuid_trace_id(self):
        result = log_decision(
            invoice_id="inv-001",
            decision="approved",
            reasoning_trace="Test trace",
            all_signals={},
        )
        assert "trace_id" in result
        # Validate it's a proper UUID
        parsed = uuid.UUID(result["trace_id"])
        assert str(parsed) == result["trace_id"]

    def test_has_timestamp(self):
        result = log_decision(
            invoice_id="inv-001",
            decision="rejected",
            reasoning_trace="Test",
            all_signals={},
        )
        assert "timestamp" in result
        datetime.fromisoformat(result["timestamp"])

    def test_return_keys(self):
        result = log_decision(
            invoice_id="inv-001",
            decision="flagged_for_review",
            reasoning_trace="Test",
            all_signals={},
        )
        expected_keys = {"logged", "invoice_id", "decision", "trace_id", "timestamp"}
        assert set(result.keys()) == expected_keys

    def test_unique_trace_ids(self):
        """Each call should generate a unique trace_id."""
        r1 = log_decision(
            invoice_id="inv-001",
            decision="approved",
            reasoning_trace="A",
            all_signals={},
        )
        r2 = log_decision(
            invoice_id="inv-001",
            decision="approved",
            reasoning_trace="B",
            all_signals={},
        )
        assert r1["trace_id"] != r2["trace_id"]
