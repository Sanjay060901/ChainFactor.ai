"""TDD tests for Feature 4.8b: get_credit_score tool (Mock CIBIL).

Tests the mock credit score lookup based on GSTIN state code prefix.
All data is deterministic (mock API) -- no external mocking needed.

Mock rules:
- 27* (Maharashtra): score=750, rating="good"
- 29* (Karnataka): score=820, rating="excellent"
- 09* (UP): score=580, rating="fair"
- 07* (Delhi): score=450, rating="poor"
- Others: score=650, rating="average"
- DEMO_MODE: returns 750/good
"""


from app.agents.tools.get_credit_score import get_credit_score


# ---------------------------------------------------------------------------
# Tests: GSTIN prefix-based mock logic
# ---------------------------------------------------------------------------


class TestCreditScoreMockRules:
    """Verify deterministic mock rules based on GSTIN state code prefix."""

    def test_maharashtra_27_returns_good(self):
        """27* (Maharashtra) -> score=750, rating=good."""
        result = get_credit_score(buyer_gstin="27AABCT1234R1ZM", _demo=False)
        assert result["score"] == 750
        assert result["rating"] == "good"

    def test_karnataka_29_returns_excellent(self):
        """29* (Karnataka) -> score=820, rating=excellent."""
        result = get_credit_score(buyer_gstin="29AABCW5678R1ZX", _demo=False)
        assert result["score"] == 820
        assert result["rating"] == "excellent"

    def test_up_09_returns_fair(self):
        """09* (Uttar Pradesh) -> score=580, rating=fair."""
        result = get_credit_score(buyer_gstin="09AAACR5678R1ZQ", _demo=False)
        assert result["score"] == 580
        assert result["rating"] == "fair"

    def test_delhi_07_returns_poor(self):
        """07* (Delhi) -> score=450, rating=poor."""
        result = get_credit_score(buyer_gstin="07AABCD1234R1ZP", _demo=False)
        assert result["score"] == 450
        assert result["rating"] == "poor"

    def test_unknown_prefix_returns_average(self):
        """Unknown state code -> score=650, rating=average."""
        result = get_credit_score(buyer_gstin="33AABCT9999R1ZZ", _demo=False)
        assert result["score"] == 650
        assert result["rating"] == "average"

    def test_another_unknown_prefix(self):
        """06* (Haryana) -> average (not in known list)."""
        result = get_credit_score(buyer_gstin="06XYZAB1234R1ZZ", _demo=False)
        assert result["score"] == 650
        assert result["rating"] == "average"


# ---------------------------------------------------------------------------
# Tests: Return shape
# ---------------------------------------------------------------------------


class TestCreditScoreReturnShape:
    """Verify the return dict has exactly the expected keys."""

    def test_return_keys(self):
        result = get_credit_score(buyer_gstin="27AABCT1234R1ZM", _demo=False)
        assert set(result.keys()) == {"score", "rating"}

    def test_return_types(self):
        result = get_credit_score(buyer_gstin="29AABCW5678R1ZX", _demo=False)
        assert isinstance(result["score"], int)
        assert isinstance(result["rating"], str)


# ---------------------------------------------------------------------------
# Tests: DEMO_MODE
# ---------------------------------------------------------------------------


class TestCreditScoreDemoMode:
    """DEMO_MODE always returns 750/good regardless of GSTIN."""

    def test_demo_mode_returns_good(self):
        """Demo mode returns 750/good even for unknown GSTIN prefix."""
        result = get_credit_score(buyer_gstin="33AABCT9999R1ZZ", _demo=True)
        assert result["score"] == 750
        assert result["rating"] == "good"

    def test_demo_mode_overrides_poor(self):
        """Demo mode overrides poor rating with good."""
        result = get_credit_score(buyer_gstin="07AABCD1234R1ZP", _demo=True)
        assert result["score"] == 750
        assert result["rating"] == "good"


# ---------------------------------------------------------------------------
# Tests: Edge cases
# ---------------------------------------------------------------------------


class TestCreditScoreEdgeCases:
    """Edge case handling."""

    def test_empty_gstin_returns_average(self):
        """Empty GSTIN string should fallback to average."""
        result = get_credit_score(buyer_gstin="", _demo=False)
        assert result["score"] == 650
        assert result["rating"] == "average"

    def test_short_gstin_returns_average(self):
        """Single-char GSTIN should fallback to average."""
        result = get_credit_score(buyer_gstin="2", _demo=False)
        assert result["score"] == 650
        assert result["rating"] == "average"
