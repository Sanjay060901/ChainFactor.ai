"""TDD tests for Feature 4.6: verify_gstn tool.

Tests the mock GSTIN verification based on state code prefix (first 2 chars).
All data is deterministic (mock API) -- no external API calls.

Mock rules:
- "27" (Maharashtra): active, not blocklisted
- "29" (Karnataka): active, not blocklisted
- "09" (Uttar Pradesh): active, not blocklisted
- "07" (Delhi): INACTIVE, not blocklisted
- Others: active, not blocklisted
- verified = True if BOTH seller and buyer are active and neither blocklisted
- DEMO_MODE: returns all-active, verified=True
"""

from app.agents.tools.verify_gstn import verify_gstn


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _active_gstin(prefix: str) -> str:
    """Build a plausible 15-char GSTIN with the given 2-char state prefix."""
    return f"{prefix}AABCT1234R1ZM"


# ---------------------------------------------------------------------------
# Tests: Return shape
# ---------------------------------------------------------------------------


class TestVerifyGstnReturnShape:
    """Verify the return dict has the expected structure and types."""

    def test_return_keys_present(self):
        """Result must contain verified, status, and details."""
        result = verify_gstn(
            seller_gstin=_active_gstin("27"),
            buyer_gstin=_active_gstin("29"),
            _demo=False,
        )
        assert "verified" in result
        assert "status" in result
        assert "details" in result

    def test_details_keys_present(self):
        """Details sub-dict must contain four boolean fields."""
        result = verify_gstn(
            seller_gstin=_active_gstin("27"),
            buyer_gstin=_active_gstin("29"),
            _demo=False,
        )
        details = result["details"]
        assert "seller_gstin_active" in details
        assert "buyer_gstin_active" in details
        assert "seller_on_blocklist" in details
        assert "buyer_on_blocklist" in details

    def test_return_types(self):
        """verified is bool, status is str, all details values are bool."""
        result = verify_gstn(
            seller_gstin=_active_gstin("27"),
            buyer_gstin=_active_gstin("29"),
            _demo=False,
        )
        assert isinstance(result["verified"], bool)
        assert isinstance(result["status"], str)
        for key, val in result["details"].items():
            assert isinstance(val, bool), f"details['{key}'] is not bool"


# ---------------------------------------------------------------------------
# Tests: Mock rules -- each state prefix
# ---------------------------------------------------------------------------


class TestVerifyGstnMockRules:
    """Verify deterministic behaviour for each defined GSTIN state prefix."""

    def test_maharashtra_27_active(self):
        """27* (Maharashtra) -> active, not blocklisted."""
        result = verify_gstn(
            seller_gstin=_active_gstin("27"),
            buyer_gstin=_active_gstin("27"),
            _demo=False,
        )
        assert result["details"]["seller_gstin_active"] is True
        assert result["details"]["buyer_gstin_active"] is True
        assert result["details"]["seller_on_blocklist"] is False
        assert result["details"]["buyer_on_blocklist"] is False

    def test_karnataka_29_active(self):
        """29* (Karnataka) -> active, not blocklisted."""
        result = verify_gstn(
            seller_gstin=_active_gstin("29"),
            buyer_gstin=_active_gstin("29"),
            _demo=False,
        )
        assert result["details"]["seller_gstin_active"] is True
        assert result["details"]["buyer_gstin_active"] is True

    def test_up_09_active(self):
        """09* (Uttar Pradesh) -> active (slow payer is buyer_intel's concern)."""
        result = verify_gstn(
            seller_gstin=_active_gstin("09"),
            buyer_gstin=_active_gstin("09"),
            _demo=False,
        )
        assert result["details"]["seller_gstin_active"] is True
        assert result["details"]["buyer_gstin_active"] is True

    def test_delhi_07_inactive(self):
        """07* (Delhi) -> INACTIVE GSTIN."""
        result = verify_gstn(
            seller_gstin=_active_gstin("07"),
            buyer_gstin=_active_gstin("07"),
            _demo=False,
        )
        assert result["details"]["seller_gstin_active"] is False
        assert result["details"]["buyer_gstin_active"] is False

    def test_unknown_prefix_defaults_active(self):
        """Unknown state code (e.g. 33* Tamil Nadu) -> active, not blocklisted."""
        result = verify_gstn(
            seller_gstin=_active_gstin("33"),
            buyer_gstin=_active_gstin("33"),
            _demo=False,
        )
        assert result["details"]["seller_gstin_active"] is True
        assert result["details"]["buyer_gstin_active"] is True
        assert result["details"]["seller_on_blocklist"] is False
        assert result["details"]["buyer_on_blocklist"] is False


# ---------------------------------------------------------------------------
# Tests: verified flag and status
# ---------------------------------------------------------------------------


class TestVerifyGstnVerifiedFlag:
    """verified=True only when both are active and neither blocklisted."""

    def test_both_active_verified_true(self):
        """Maharashtra seller + Karnataka buyer -> verified=True."""
        result = verify_gstn(
            seller_gstin=_active_gstin("27"),
            buyer_gstin=_active_gstin("29"),
            _demo=False,
        )
        assert result["verified"] is True
        assert result["status"] == "active"

    def test_inactive_seller_verified_false(self):
        """Delhi (07) seller is inactive -> verified=False."""
        result = verify_gstn(
            seller_gstin=_active_gstin("07"),
            buyer_gstin=_active_gstin("27"),
            _demo=False,
        )
        assert result["verified"] is False
        assert result["status"] == "inactive"

    def test_inactive_buyer_verified_false(self):
        """Delhi (07) buyer is inactive -> verified=False."""
        result = verify_gstn(
            seller_gstin=_active_gstin("27"),
            buyer_gstin=_active_gstin("07"),
            _demo=False,
        )
        assert result["verified"] is False
        assert result["status"] == "inactive"

    def test_both_inactive_verified_false(self):
        """Both Delhi (07) parties -> verified=False."""
        result = verify_gstn(
            seller_gstin=_active_gstin("07"),
            buyer_gstin=_active_gstin("07"),
            _demo=False,
        )
        assert result["verified"] is False
        assert result["status"] == "inactive"

    def test_status_active_when_verified(self):
        """status must be 'active' when verified=True."""
        result = verify_gstn(
            seller_gstin=_active_gstin("27"),
            buyer_gstin=_active_gstin("29"),
            _demo=False,
        )
        assert result["status"] == "active"

    def test_status_inactive_when_not_verified(self):
        """status must be 'inactive' when verified=False."""
        result = verify_gstn(
            seller_gstin=_active_gstin("07"),
            buyer_gstin=_active_gstin("27"),
            _demo=False,
        )
        assert result["status"] == "inactive"


# ---------------------------------------------------------------------------
# Tests: DEMO_MODE
# ---------------------------------------------------------------------------


class TestVerifyGstnDemoMode:
    """DEMO_MODE always returns all-active, verified=True regardless of GSTINs."""

    def test_demo_mode_all_active(self):
        """Demo mode returns verified=True even when Delhi (07) prefix is used."""
        result = verify_gstn(
            seller_gstin=_active_gstin("07"),
            buyer_gstin=_active_gstin("07"),
            _demo=True,
        )
        assert result["verified"] is True
        assert result["status"] == "active"
        assert result["details"]["seller_gstin_active"] is True
        assert result["details"]["buyer_gstin_active"] is True
        assert result["details"]["seller_on_blocklist"] is False
        assert result["details"]["buyer_on_blocklist"] is False

    def test_demo_mode_returns_full_shape(self):
        """Demo result has verified, status, and details keys."""
        result = verify_gstn(
            seller_gstin=_active_gstin("27"),
            buyer_gstin=_active_gstin("29"),
            _demo=True,
        )
        assert "verified" in result
        assert "status" in result
        assert "details" in result

    def test_demo_mode_overrides_inactive_prefix(self):
        """Even with an inactive prefix, demo mode returns active."""
        result = verify_gstn(
            seller_gstin=_active_gstin("07"),
            buyer_gstin=_active_gstin("29"),
            _demo=True,
        )
        assert result["verified"] is True


# ---------------------------------------------------------------------------
# Tests: Edge cases
# ---------------------------------------------------------------------------


class TestVerifyGstnEdgeCases:
    """Edge case handling for malformed GSTINs."""

    def test_empty_seller_gstin_falls_back_to_active(self):
        """Empty seller GSTIN -> treated as unknown prefix -> active by default."""
        result = verify_gstn(
            seller_gstin="",
            buyer_gstin=_active_gstin("29"),
            _demo=False,
        )
        # Empty gstin has no prefix -> unknown prefix -> active (per spec)
        assert isinstance(result["verified"], bool)
        assert result["details"]["seller_gstin_active"] is True

    def test_empty_buyer_gstin_falls_back_to_active(self):
        """Empty buyer GSTIN -> treated as unknown prefix -> active by default."""
        result = verify_gstn(
            seller_gstin=_active_gstin("27"),
            buyer_gstin="",
            _demo=False,
        )
        assert result["details"]["buyer_gstin_active"] is True

    def test_short_gstin_treated_as_unknown(self):
        """1-char GSTIN cannot extract a 2-char prefix -> defaults to active."""
        result = verify_gstn(
            seller_gstin="2",
            buyer_gstin="2",
            _demo=False,
        )
        assert result["details"]["seller_gstin_active"] is True

    def test_mixed_prefixes(self):
        """Active seller (27) + inactive buyer (07) -> verified=False."""
        result = verify_gstn(
            seller_gstin=_active_gstin("27"),
            buyer_gstin=_active_gstin("07"),
            _demo=False,
        )
        assert result["details"]["seller_gstin_active"] is True
        assert result["details"]["buyer_gstin_active"] is False
        assert result["verified"] is False
