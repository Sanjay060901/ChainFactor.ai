"""TDD tests for Feature 4.8c: get_company_info tool (Mock MCA).

Tests the mock company info lookup based on GSTIN state code prefix.
All data is deterministic (mock API) -- no external mocking needed.

Mock rules:
- 27* (Maharashtra): status="active", incorporated="2015", paid_up_capital=100_000_000.0
- 29* (Karnataka): status="active", incorporated="2018", paid_up_capital=50_000_000.0
- 09* (UP): status="active", incorporated="2020", paid_up_capital=10_000_000.0
- 07* (Delhi): status="dormant", incorporated="2010", paid_up_capital=5_000_000.0
- Others: status="active", incorporated="2019", paid_up_capital=25_000_000.0
- DEMO_MODE: returns active company (Maharashtra profile)
"""


from app.agents.tools.get_company_info import get_company_info


# ---------------------------------------------------------------------------
# Tests: GSTIN prefix-based mock logic
# ---------------------------------------------------------------------------


class TestCompanyInfoMockRules:
    """Verify deterministic mock rules based on GSTIN state code prefix."""

    def test_maharashtra_27_returns_active_2015(self):
        """27* (Maharashtra) -> active, 2015, 10Cr capital."""
        result = get_company_info(company_gstin="27AABCT1234R1ZM")
        assert result["status"] == "active"
        assert result["incorporated"] == "2015"
        assert result["paid_up_capital"] == 100_000_000.0

    def test_karnataka_29_returns_active_2018(self):
        """29* (Karnataka) -> active, 2018, 5Cr capital."""
        result = get_company_info(company_gstin="29AABCW5678R1ZX")
        assert result["status"] == "active"
        assert result["incorporated"] == "2018"
        assert result["paid_up_capital"] == 50_000_000.0

    def test_up_09_returns_active_2020(self):
        """09* (Uttar Pradesh) -> active, 2020, 1Cr capital."""
        result = get_company_info(company_gstin="09AAACR5678R1ZQ")
        assert result["status"] == "active"
        assert result["incorporated"] == "2020"
        assert result["paid_up_capital"] == 10_000_000.0

    def test_delhi_07_returns_dormant(self):
        """07* (Delhi) -> dormant, 2010, 50L capital."""
        result = get_company_info(company_gstin="07AABCD1234R1ZP")
        assert result["status"] == "dormant"
        assert result["incorporated"] == "2010"
        assert result["paid_up_capital"] == 5_000_000.0

    def test_unknown_prefix_returns_default(self):
        """Unknown state code -> active, 2019, 2.5Cr capital."""
        result = get_company_info(company_gstin="33AABCT9999R1ZZ")
        assert result["status"] == "active"
        assert result["incorporated"] == "2019"
        assert result["paid_up_capital"] == 25_000_000.0

    def test_another_unknown_prefix(self):
        """06* (Haryana) -> default profile."""
        result = get_company_info(company_gstin="06XYZAB1234R1ZZ")
        assert result["status"] == "active"
        assert result["incorporated"] == "2019"
        assert result["paid_up_capital"] == 25_000_000.0


# ---------------------------------------------------------------------------
# Tests: Return shape
# ---------------------------------------------------------------------------


class TestCompanyInfoReturnShape:
    """Verify the return dict has exactly the expected keys."""

    def test_return_keys(self):
        result = get_company_info(company_gstin="27AABCT1234R1ZM")
        assert set(result.keys()) == {"status", "incorporated", "paid_up_capital"}

    def test_return_types(self):
        result = get_company_info(company_gstin="29AABCW5678R1ZX")
        assert isinstance(result["status"], str)
        assert isinstance(result["incorporated"], str)
        assert isinstance(result["paid_up_capital"], float)


# ---------------------------------------------------------------------------
# Tests: DEMO_MODE
# ---------------------------------------------------------------------------



class TestCompanyInfoEdgeCases:
    """Edge case handling."""

    def test_empty_gstin_returns_default(self):
        """Empty GSTIN string should fallback to default profile."""
        result = get_company_info(company_gstin="")
        assert result["status"] == "active"
        assert result["incorporated"] == "2019"

    def test_short_gstin_returns_default(self):
        """Single-char GSTIN should fallback to default profile."""
        result = get_company_info(company_gstin="2")
        assert result["status"] == "active"
