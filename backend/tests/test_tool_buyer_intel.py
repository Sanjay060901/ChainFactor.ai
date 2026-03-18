"""TDD tests for Feature 4.8: get_buyer_intel tool.

Tests the mock buyer intelligence lookup based on GSTIN state code prefix.
All data is deterministic (mock API) -- no external mocking needed.

Mock rules:
- 27* (Maharashtra): reliable, avg_days=28, previous_count=8
- 29* (Karnataka): reliable, avg_days=35, previous_count=12
- 09* (UP): slow_payer, avg_days=65, previous_count=3
- Others: new_buyer, avg_days=0, previous_count=0
- DEMO_MODE: always returns reliable buyer
"""


from app.agents.tools.get_buyer_intel import get_buyer_intel


# ---------------------------------------------------------------------------
# Tests: GSTIN prefix-based mock logic
# ---------------------------------------------------------------------------


class TestBuyerIntelMockRules:
    """Verify deterministic mock rules based on GSTIN state code prefix."""

    def test_maharashtra_27_returns_reliable(self):
        """27* (Maharashtra) -> reliable buyer with 28 avg days."""
        result = get_buyer_intel(buyer_gstin="27AABCT1234R1ZM", _demo=False)
        assert result["payment_history"] == "reliable"
        assert result["avg_days"] == 28
        assert result["previous_count"] == 8

    def test_karnataka_29_returns_reliable(self):
        """29* (Karnataka) -> reliable buyer with 35 avg days."""
        result = get_buyer_intel(buyer_gstin="29AABCW5678R1ZX", _demo=False)
        assert result["payment_history"] == "reliable"
        assert result["avg_days"] == 35
        assert result["previous_count"] == 12

    def test_up_09_returns_slow_payer(self):
        """09* (Uttar Pradesh) -> slow_payer with 65 avg days."""
        result = get_buyer_intel(buyer_gstin="09AAACR5678R1ZQ", _demo=False)
        assert result["payment_history"] == "slow_payer"
        assert result["avg_days"] == 65
        assert result["previous_count"] == 3

    def test_unknown_prefix_returns_new_buyer(self):
        """Unknown state code -> new_buyer with 0 history."""
        result = get_buyer_intel(buyer_gstin="33AABCT9999R1ZZ", _demo=False)
        assert result["payment_history"] == "new_buyer"
        assert result["avg_days"] == 0
        assert result["previous_count"] == 0

    def test_another_unknown_prefix(self):
        """06* (Haryana) -> new_buyer (not in known list)."""
        result = get_buyer_intel(buyer_gstin="06XYZAB1234R1ZZ", _demo=False)
        assert result["payment_history"] == "new_buyer"
        assert result["avg_days"] == 0
        assert result["previous_count"] == 0


# ---------------------------------------------------------------------------
# Tests: Return shape
# ---------------------------------------------------------------------------


class TestBuyerIntelReturnShape:
    """Verify the return dict has exactly the expected keys."""

    def test_return_keys(self):
        result = get_buyer_intel(buyer_gstin="27AABCT1234R1ZM", _demo=False)
        assert set(result.keys()) == {"payment_history", "avg_days", "previous_count"}

    def test_return_types(self):
        result = get_buyer_intel(buyer_gstin="29AABCW5678R1ZX", _demo=False)
        assert isinstance(result["payment_history"], str)
        assert isinstance(result["avg_days"], int)
        assert isinstance(result["previous_count"], int)


# ---------------------------------------------------------------------------
# Tests: DEMO_MODE
# ---------------------------------------------------------------------------


class TestBuyerIntelDemoMode:
    """DEMO_MODE always returns a reliable buyer regardless of GSTIN."""

    def test_demo_mode_returns_reliable(self):
        """Demo mode returns reliable buyer even for unknown GSTIN prefix."""
        result = get_buyer_intel(buyer_gstin="33AABCT9999R1ZZ", _demo=True)
        assert result["payment_history"] == "reliable"
        assert result["avg_days"] == 28
        assert result["previous_count"] == 8

    def test_demo_mode_ignores_slow_payer_prefix(self):
        """Demo mode overrides slow_payer prefix with reliable."""
        result = get_buyer_intel(buyer_gstin="09AAACR5678R1ZQ", _demo=True)
        assert result["payment_history"] == "reliable"


# ---------------------------------------------------------------------------
# Tests: Edge cases
# ---------------------------------------------------------------------------


class TestBuyerIntelEdgeCases:
    """Edge case handling."""

    def test_empty_gstin_returns_new_buyer(self):
        """Empty GSTIN string should fallback to new_buyer."""
        result = get_buyer_intel(buyer_gstin="", _demo=False)
        assert result["payment_history"] == "new_buyer"

    def test_short_gstin_returns_new_buyer(self):
        """Single-char GSTIN should fallback to new_buyer."""
        result = get_buyer_intel(buyer_gstin="2", _demo=False)
        assert result["payment_history"] == "new_buyer"
