"""TDD tests for Feature 4.5b: validate_gst_compliance tool.

Tests GST compliance validation:
- HSN/SAC code format and range validation (6-8 digits)
- Tax rate matches HSN code slab (0%, 5%, 12%, 18%, 28%)
- IGST vs CGST+SGST based on state codes
- E-invoice requirement threshold (5 crore turnover)
- DEMO_MODE returns pre-computed compliant result
"""

import pytest


# ---------------------------------------------------------------------------
# Helpers: sample extracted data
# ---------------------------------------------------------------------------


def _valid_extracted_data_interstate() -> dict:
    """Return valid extracted data for inter-state transaction (IGST).

    Seller: 27* (Maharashtra), Buyer: 29* (Karnataka) -> different states -> IGST.
    """
    return {
        "seller": {
            "name": "Acme Technologies Pvt Ltd",
            "gstin": "27AABCT1234R1ZM",
            "address": "Mumbai, Maharashtra",
        },
        "buyer": {
            "name": "TechBuild Solutions",
            "gstin": "29AABCW5678R1ZX",
            "address": "Bangalore, Karnataka",
        },
        "invoice_number": "INV-2026-001",
        "invoice_date": "2026-03-15",
        "due_date": "2026-04-15",
        "subtotal": 10000.0,
        "tax_amount": 1800.0,
        "tax_rate": 18.0,
        "tax_type": "IGST",
        "total_amount": 11800.0,
        "line_items": [
            {
                "description": "IT Consulting Services",
                "hsn_code": "998311",
                "quantity": 10,
                "rate": 500.0,
                "amount": 5000.0,
            },
            {
                "description": "Software Development",
                "hsn_code": "998312",
                "quantity": 5,
                "rate": 1000.0,
                "amount": 5000.0,
            },
        ],
    }


def _valid_extracted_data_intrastate() -> dict:
    """Return valid extracted data for intra-state transaction (CGST+SGST).

    Seller: 27* (Maharashtra), Buyer: 27* (Maharashtra) -> same state -> CGST+SGST.
    """
    data = _valid_extracted_data_interstate()
    data["buyer"]["gstin"] = "27AABCW5678R1ZX"  # Same state as seller (27)
    data["tax_type"] = "CGST+SGST"
    return data


# ---------------------------------------------------------------------------
# Tests: HSN/SAC code validation
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_valid_hsn_codes():
    """Valid 6-digit HSN/SAC codes should pass validation."""
    from app.agents.tools.validate_gst_compliance import validate_gst_compliance

    result = validate_gst_compliance(_valid_extracted_data_interstate())

    assert result["details"]["hsn_valid"] is True


@pytest.mark.asyncio
async def test_invalid_hsn_code_too_short():
    """HSN code with fewer than 4 digits should fail."""
    from app.agents.tools.validate_gst_compliance import validate_gst_compliance

    data = _valid_extracted_data_interstate()
    data["line_items"][0]["hsn_code"] = "99"  # Too short
    result = validate_gst_compliance(data)

    assert result["details"]["hsn_valid"] is False


@pytest.mark.asyncio
async def test_invalid_hsn_code_non_numeric():
    """HSN code with non-numeric chars should fail."""
    from app.agents.tools.validate_gst_compliance import validate_gst_compliance

    data = _valid_extracted_data_interstate()
    data["line_items"][0]["hsn_code"] = "99AB11"  # Non-numeric
    result = validate_gst_compliance(data)

    assert result["details"]["hsn_valid"] is False


# ---------------------------------------------------------------------------
# Tests: Tax rate matches HSN slab
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_it_services_18_percent():
    """IT services (998311-998319) should have 18% tax rate."""
    from app.agents.tools.validate_gst_compliance import validate_gst_compliance

    data = _valid_extracted_data_interstate()
    data["tax_rate"] = 18.0
    result = validate_gst_compliance(data)

    assert result["details"]["rate_match"] is True


@pytest.mark.asyncio
async def test_computers_18_percent():
    """Computers (8471) should have 18% tax rate."""
    from app.agents.tools.validate_gst_compliance import validate_gst_compliance

    data = _valid_extracted_data_interstate()
    data["line_items"] = [
        {
            "description": "Laptop",
            "hsn_code": "84713010",
            "quantity": 1,
            "rate": 10000.0,
            "amount": 10000.0,
        }
    ]
    data["subtotal"] = 10000.0
    data["tax_rate"] = 18.0
    data["tax_amount"] = 1800.0
    data["total_amount"] = 11800.0
    result = validate_gst_compliance(data)

    assert result["details"]["rate_match"] is True


@pytest.mark.asyncio
async def test_rice_5_percent():
    """Rice (1006) should have 5% tax rate."""
    from app.agents.tools.validate_gst_compliance import validate_gst_compliance

    data = _valid_extracted_data_interstate()
    data["line_items"] = [
        {
            "description": "Basmati Rice",
            "hsn_code": "100630",
            "quantity": 100,
            "rate": 50.0,
            "amount": 5000.0,
        }
    ]
    data["subtotal"] = 5000.0
    data["tax_rate"] = 5.0
    data["tax_amount"] = 250.0
    data["total_amount"] = 5250.0
    result = validate_gst_compliance(data)

    assert result["details"]["rate_match"] is True


@pytest.mark.asyncio
async def test_meat_exempt():
    """Meat (0201) is exempt (0% tax)."""
    from app.agents.tools.validate_gst_compliance import validate_gst_compliance

    data = _valid_extracted_data_interstate()
    data["line_items"] = [
        {
            "description": "Fresh Beef",
            "hsn_code": "020100",
            "quantity": 10,
            "rate": 500.0,
            "amount": 5000.0,
        }
    ]
    data["subtotal"] = 5000.0
    data["tax_rate"] = 0.0
    data["tax_amount"] = 0.0
    data["total_amount"] = 5000.0
    result = validate_gst_compliance(data)

    assert result["details"]["rate_match"] is True


@pytest.mark.asyncio
async def test_rate_mismatch():
    """Wrong tax rate for HSN code should fail rate_match."""
    from app.agents.tools.validate_gst_compliance import validate_gst_compliance

    data = _valid_extracted_data_interstate()
    # IT services should be 18%, set to 5%
    data["tax_rate"] = 5.0
    result = validate_gst_compliance(data)

    assert result["details"]["rate_match"] is False
    assert result["is_compliant"] is False


# ---------------------------------------------------------------------------
# Tests: IGST vs CGST+SGST (state code check)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_interstate_igst_correct():
    """Different state codes (27 vs 29) with IGST should be correct."""
    from app.agents.tools.validate_gst_compliance import validate_gst_compliance

    data = _valid_extracted_data_interstate()
    data["tax_type"] = "IGST"
    result = validate_gst_compliance(data)

    assert result["details"]["tax_type_correct"] is True


@pytest.mark.asyncio
async def test_intrastate_cgst_sgst_correct():
    """Same state codes (27 vs 27) with CGST+SGST should be correct."""
    from app.agents.tools.validate_gst_compliance import validate_gst_compliance

    data = _valid_extracted_data_intrastate()
    result = validate_gst_compliance(data)

    assert result["details"]["tax_type_correct"] is True


@pytest.mark.asyncio
async def test_interstate_cgst_sgst_wrong():
    """Different state codes with CGST+SGST (should be IGST) is incorrect."""
    from app.agents.tools.validate_gst_compliance import validate_gst_compliance

    data = _valid_extracted_data_interstate()
    data["tax_type"] = "CGST+SGST"  # Wrong for inter-state
    result = validate_gst_compliance(data)

    assert result["details"]["tax_type_correct"] is False


@pytest.mark.asyncio
async def test_intrastate_igst_wrong():
    """Same state codes with IGST (should be CGST+SGST) is incorrect."""

    from app.agents.tools.validate_gst_compliance import validate_gst_compliance

    data = _valid_extracted_data_intrastate()
    data["tax_type"] = "IGST"  # Wrong for intra-state
    result = validate_gst_compliance(data)

    assert result["details"]["tax_type_correct"] is False


# ---------------------------------------------------------------------------
# Tests: E-invoice requirement
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_einvoice_not_required_below_threshold():
    """Turnover below 5 crore should not require e-invoice."""
    from app.agents.tools.validate_gst_compliance import validate_gst_compliance

    data = _valid_extracted_data_interstate()
    data["seller_turnover"] = 4_00_00_000  # 4 crore (below 5 crore threshold)
    result = validate_gst_compliance(data)

    assert result["details"].get("einvoice_required") is False


@pytest.mark.asyncio
async def test_einvoice_required_above_threshold():
    """Turnover above 5 crore should require e-invoice."""
    from app.agents.tools.validate_gst_compliance import validate_gst_compliance

    data = _valid_extracted_data_interstate()
    data["seller_turnover"] = 6_00_00_000  # 6 crore (above threshold)
    result = validate_gst_compliance(data)

    assert result["details"].get("einvoice_required") is True


# ---------------------------------------------------------------------------
# Tests: Return shape
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_return_shape():
    """Result must have is_compliant and details keys with expected sub-keys."""
    from app.agents.tools.validate_gst_compliance import validate_gst_compliance

    result = validate_gst_compliance(_valid_extracted_data_interstate())

    assert "is_compliant" in result
    assert "details" in result
    assert isinstance(result["is_compliant"], bool)
    details = result["details"]
    assert "hsn_valid" in details
    assert "rate_match" in details
    assert "tax_type_correct" in details


@pytest.mark.asyncio
async def test_missing_tax_type_defaults_gracefully():
    """If tax_type is missing, tool should still return a result without crashing."""
    from app.agents.tools.validate_gst_compliance import validate_gst_compliance

    data = _valid_extracted_data_interstate()
    data.pop("tax_type", None)
    result = validate_gst_compliance(data)

    assert "is_compliant" in result
    assert "details" in result
