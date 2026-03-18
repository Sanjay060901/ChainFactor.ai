"""TDD tests for Feature 4.7: check_fraud tool -- 5-layer fraud detection.

Tests cover:
- Demo mode returns pre-computed all-pass result
- Clean invoice passes all 5 layers
- Invalid math fails Financial Consistency layer
- "DUP" in invoice number fails Cross-Reference layer
- Amount > 50L triggers Pattern Analysis warning
- Round-number amounts (ending in 000) trigger Pattern Analysis warning
- Overall result correctly computed from layer results
- Negative amounts fail Financial Consistency
- Tax rate > 100% fails Financial Consistency
- Inactive GSTIN fails Entity Verification layer
- Each layer function is independently testable
"""


from app.config import settings


# ---------------------------------------------------------------------------
# Helpers: build minimal extracted_data and gstin_verification dicts
# ---------------------------------------------------------------------------


def _clean_extracted_data() -> dict:
    """A valid, clean invoice extracted data dict."""
    return {
        "seller": {
            "name": "Acme Pvt Ltd",
            "gstin": "27AABCA1234R1ZM",
            "address": "Mumbai, MH",
        },
        "buyer": {
            "name": "Beta Corp",
            "gstin": "29AABCB5678R1ZX",
            "address": "Bangalore, KA",
        },
        "invoice_number": "INV-2026-001",
        "invoice_date": "2026-03-15",
        "due_date": "2026-04-15",
        "subtotal": 10000.0,
        "tax_amount": 1800.0,
        "tax_rate": 18.0,
        "total_amount": 11800.0,
        "line_items": [
            {
                "description": "Widget A",
                "hsn_code": "8471",
                "quantity": 10,
                "rate": 1000.0,
                "amount": 10000.0,
            }
        ],
    }


def _clean_gstin_verification() -> dict:
    """A passing GSTIN verification result."""
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


# ---------------------------------------------------------------------------
# Tests: Demo mode
# ---------------------------------------------------------------------------


class TestDemoMode:
    """Demo mode returns pre-computed all-pass result with no real logic."""

    def test_demo_mode_returns_pass(self):
        original = settings.DEMO_MODE
        settings.DEMO_MODE = True
        try:
            from app.agents.tools.check_fraud import check_fraud

            result = check_fraud(
                extracted_data=_clean_extracted_data(),
                gstin_verification=_clean_gstin_verification(),
            )
            assert result["overall"] == "pass"
            assert result["confidence"] == 97.0
            assert result["flags"] == []
            assert len(result["layers"]) == 5
            for layer in result["layers"]:
                assert layer["result"] == "pass"
        finally:
            settings.DEMO_MODE = original

    def test_demo_mode_ignores_bad_data(self):
        """Even with bad data, demo mode returns a fixed pass."""
        original = settings.DEMO_MODE
        settings.DEMO_MODE = True
        try:
            from app.agents.tools.check_fraud import check_fraud

            bad_data = _clean_extracted_data()
            bad_data["total_amount"] = -999.0  # would normally fail
            result = check_fraud(
                extracted_data=bad_data,
                gstin_verification=_clean_gstin_verification(),
            )
            assert result["overall"] == "pass"
        finally:
            settings.DEMO_MODE = original


# ---------------------------------------------------------------------------
# Tests: Individual layers (non-demo)
# ---------------------------------------------------------------------------


class TestDocumentIntegrityLayer:
    """Layer 1: Document Integrity -- rule-based checks on data consistency."""

    def test_clean_data_passes(self):
        from app.agents.tools.check_fraud import _check_document_integrity

        layer = _check_document_integrity(_clean_extracted_data())
        assert layer["result"] == "pass"
        assert layer["confidence"] >= 90.0

    def test_missing_seller_name_warns(self):
        from app.agents.tools.check_fraud import _check_document_integrity

        data = _clean_extracted_data()
        data["seller"]["name"] = ""
        layer = _check_document_integrity(data)
        assert layer["result"] in ("warning", "fail")

    def test_missing_invoice_number_warns(self):
        from app.agents.tools.check_fraud import _check_document_integrity

        data = _clean_extracted_data()
        data["invoice_number"] = ""
        layer = _check_document_integrity(data)
        assert layer["result"] in ("warning", "fail")


class TestFinancialConsistencyLayer:
    """Layer 2: Financial Consistency -- math verification."""

    def test_correct_math_passes(self):
        from app.agents.tools.check_fraud import _check_financial_consistency

        layer = _check_financial_consistency(_clean_extracted_data())
        assert layer["result"] == "pass"
        assert layer["confidence"] >= 90.0

    def test_wrong_total_fails(self):
        from app.agents.tools.check_fraud import _check_financial_consistency

        data = _clean_extracted_data()
        data["total_amount"] = 99999.0  # subtotal + tax != 99999
        layer = _check_financial_consistency(data)
        assert layer["result"] == "fail"

    def test_negative_amount_fails(self):
        from app.agents.tools.check_fraud import _check_financial_consistency

        data = _clean_extracted_data()
        data["subtotal"] = -5000.0
        layer = _check_financial_consistency(data)
        assert layer["result"] == "fail"

    def test_negative_total_fails(self):
        from app.agents.tools.check_fraud import _check_financial_consistency

        data = _clean_extracted_data()
        data["total_amount"] = -100.0
        layer = _check_financial_consistency(data)
        assert layer["result"] == "fail"

    def test_tax_rate_over_100_fails(self):
        from app.agents.tools.check_fraud import _check_financial_consistency

        data = _clean_extracted_data()
        data["tax_rate"] = 150.0
        layer = _check_financial_consistency(data)
        assert layer["result"] == "fail"

    def test_zero_tax_rate_passes(self):
        """Zero tax rate is valid (exempt goods)."""
        from app.agents.tools.check_fraud import _check_financial_consistency

        data = _clean_extracted_data()
        data["tax_rate"] = 0.0
        data["tax_amount"] = 0.0
        data["total_amount"] = 10000.0
        layer = _check_financial_consistency(data)
        assert layer["result"] == "pass"

    def test_line_items_mismatch_fails(self):
        """Sum of line item amounts must equal subtotal."""
        from app.agents.tools.check_fraud import _check_financial_consistency

        data = _clean_extracted_data()
        data["line_items"][0]["amount"] = 5000.0  # subtotal is 10000
        layer = _check_financial_consistency(data)
        assert layer["result"] == "fail"


class TestPatternAnalysisLayer:
    """Layer 3: Pattern Analysis -- flag suspicious patterns (mock rules)."""

    def test_normal_amount_passes(self):
        from app.agents.tools.check_fraud import _check_pattern_analysis

        layer = _check_pattern_analysis(_clean_extracted_data())
        assert layer["result"] == "pass"

    def test_amount_over_50_lakh_warns(self):
        from app.agents.tools.check_fraud import _check_pattern_analysis

        data = _clean_extracted_data()
        data["total_amount"] = 5_100_000.0  # > 50,00,000
        data["subtotal"] = 4_322_034.0
        data["tax_amount"] = 777_966.0
        layer = _check_pattern_analysis(data)
        assert layer["result"] == "warning"
        assert "high" in layer["detail"].lower() or "amount" in layer["detail"].lower()

    def test_round_number_ending_000_warns(self):
        from app.agents.tools.check_fraud import _check_pattern_analysis

        data = _clean_extracted_data()
        data["total_amount"] = 100_000.0
        data["subtotal"] = 84_746.0
        data["tax_amount"] = 15_254.0
        layer = _check_pattern_analysis(data)
        assert layer["result"] == "warning"
        assert "round" in layer["detail"].lower()

    def test_exact_1000_warns(self):
        """1000 ends in 000 -- should warn."""
        from app.agents.tools.check_fraud import _check_pattern_analysis

        data = _clean_extracted_data()
        data["total_amount"] = 1_000.0
        data["subtotal"] = 847.0
        data["tax_amount"] = 153.0
        layer = _check_pattern_analysis(data)
        assert layer["result"] == "warning"


class TestEntityVerificationLayer:
    """Layer 4: Entity Verification -- uses GSTIN verification results."""

    def test_active_gstin_passes(self):
        from app.agents.tools.check_fraud import _check_entity_verification

        layer = _check_entity_verification(
            _clean_extracted_data(), _clean_gstin_verification()
        )
        assert layer["result"] == "pass"

    def test_inactive_gstin_fails(self):
        from app.agents.tools.check_fraud import _check_entity_verification

        gstin = _clean_gstin_verification()
        gstin["details"]["seller_gstin_active"] = False
        layer = _check_entity_verification(_clean_extracted_data(), gstin)
        assert layer["result"] == "fail"

    def test_blocklisted_entity_fails(self):
        from app.agents.tools.check_fraud import _check_entity_verification

        gstin = _clean_gstin_verification()
        gstin["details"]["buyer_on_blocklist"] = True
        layer = _check_entity_verification(_clean_extracted_data(), gstin)
        assert layer["result"] == "fail"

    def test_unverified_gstin_fails(self):
        from app.agents.tools.check_fraud import _check_entity_verification

        gstin = _clean_gstin_verification()
        gstin["verified"] = False
        layer = _check_entity_verification(_clean_extracted_data(), gstin)
        assert layer["result"] == "fail"


class TestCrossReferenceLayer:
    """Layer 5: Cross-Reference -- mock duplicate detection."""

    def test_normal_invoice_passes(self):
        from app.agents.tools.check_fraud import _check_cross_reference

        layer = _check_cross_reference(_clean_extracted_data())
        assert layer["result"] == "pass"

    def test_dup_in_invoice_number_fails(self):
        from app.agents.tools.check_fraud import _check_cross_reference

        data = _clean_extracted_data()
        data["invoice_number"] = "INV-DUP-001"
        layer = _check_cross_reference(data)
        assert layer["result"] == "fail"
        assert "duplicate" in layer["detail"].lower()

    def test_dup_case_insensitive(self):
        """DUP detection should be case-insensitive."""
        from app.agents.tools.check_fraud import _check_cross_reference

        data = _clean_extracted_data()
        data["invoice_number"] = "inv-dup-002"
        layer = _check_cross_reference(data)
        assert layer["result"] == "fail"


# ---------------------------------------------------------------------------
# Tests: Overall result computation
# ---------------------------------------------------------------------------


class TestOverallResult:
    """End-to-end check_fraud with DEMO_MODE off."""

    def setup_method(self):
        self._original = settings.DEMO_MODE
        settings.DEMO_MODE = False

    def teardown_method(self):
        settings.DEMO_MODE = self._original

    def test_clean_invoice_all_pass(self):
        from app.agents.tools.check_fraud import check_fraud

        result = check_fraud(
            extracted_data=_clean_extracted_data(),
            gstin_verification=_clean_gstin_verification(),
        )
        assert result["overall"] == "pass"
        assert result["confidence"] >= 90.0
        assert result["flags"] == []
        assert len(result["layers"]) == 5
        for layer in result["layers"]:
            assert layer["result"] == "pass"

    def test_any_fail_gives_overall_fail(self):
        from app.agents.tools.check_fraud import check_fraud

        data = _clean_extracted_data()
        data["total_amount"] = 99999.0  # Financial Consistency fail
        result = check_fraud(
            extracted_data=data,
            gstin_verification=_clean_gstin_verification(),
        )
        assert result["overall"] == "fail"
        assert len(result["flags"]) > 0

    def test_warning_no_fail_gives_overall_warning(self):
        from app.agents.tools.check_fraud import check_fraud

        data = _clean_extracted_data()
        # Trigger Pattern Analysis warning (amount > 50L) but everything else passes
        data["total_amount"] = 5_100_000.0
        data["subtotal"] = 4_322_034.0
        data["tax_amount"] = 777_966.0
        data["line_items"][0]["amount"] = 4_322_034.0
        result = check_fraud(
            extracted_data=data,
            gstin_verification=_clean_gstin_verification(),
        )
        assert result["overall"] == "warning"
        assert len(result["flags"]) > 0

    def test_dup_invoice_fails_overall(self):
        from app.agents.tools.check_fraud import check_fraud

        data = _clean_extracted_data()
        data["invoice_number"] = "INV-DUP-999"
        result = check_fraud(
            extracted_data=data,
            gstin_verification=_clean_gstin_verification(),
        )
        assert result["overall"] == "fail"

    def test_confidence_is_average_of_layers(self):
        from app.agents.tools.check_fraud import check_fraud

        result = check_fraud(
            extracted_data=_clean_extracted_data(),
            gstin_verification=_clean_gstin_verification(),
        )
        layer_confidences = [l["confidence"] for l in result["layers"]]
        expected_avg = round(sum(layer_confidences) / len(layer_confidences), 1)
        assert result["confidence"] == expected_avg

    def test_multiple_failures_all_flagged(self):
        """Multiple layer failures should all appear in flags."""
        from app.agents.tools.check_fraud import check_fraud

        data = _clean_extracted_data()
        data["total_amount"] = -100.0  # Financial fail
        data["invoice_number"] = "DUP-BAD"  # Cross-Reference fail
        gstin = _clean_gstin_verification()
        gstin["details"]["seller_gstin_active"] = False  # Entity fail
        result = check_fraud(extracted_data=data, gstin_verification=gstin)
        assert result["overall"] == "fail"
        # At least 3 failures
        fail_layers = [l for l in result["layers"] if l["result"] == "fail"]
        assert len(fail_layers) >= 3
