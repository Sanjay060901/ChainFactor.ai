"""TDD tests for Feature 4.5: validate_fields tool.

Tests field-level validation of extracted invoice data:
- Required fields presence check
- Math validation (line items sum, subtotal + tax = total)
- GSTIN format validation (15 chars, state code + PAN + entity + Z + check)
- Date validation (not future, due_date after invoice_date)
- DEMO_MODE returns pre-computed success
"""

import pytest
from unittest.mock import patch


# ---------------------------------------------------------------------------
# Helpers: sample extracted data
# ---------------------------------------------------------------------------


def _valid_extracted_data() -> dict:
    """Return a fully valid extracted invoice data dict."""
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


# ---------------------------------------------------------------------------
# Tests: DEMO_MODE
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_demo_mode_returns_valid():
    """In DEMO_MODE, validate_fields returns is_valid=True with no errors."""
    with patch("app.agents.tools.validate_fields.settings") as mock_settings:
        mock_settings.DEMO_MODE = True
        from app.agents.tools.validate_fields import validate_fields

        result = validate_fields(_valid_extracted_data())

    assert result["is_valid"] is True
    assert result["errors"] == []
    assert result["warnings"] == []


# ---------------------------------------------------------------------------
# Tests: Required fields
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_missing_invoice_number():
    """Missing invoice_number should produce an error."""
    with patch("app.agents.tools.validate_fields.settings") as mock_settings:
        mock_settings.DEMO_MODE = False
        from app.agents.tools.validate_fields import validate_fields

        data = _valid_extracted_data()
        del data["invoice_number"]
        result = validate_fields(data)

    assert result["is_valid"] is False
    assert any("invoice_number" in e.lower() for e in result["errors"])


@pytest.mark.asyncio
async def test_missing_seller_gstin():
    """Missing seller GSTIN should produce an error."""
    with patch("app.agents.tools.validate_fields.settings") as mock_settings:
        mock_settings.DEMO_MODE = False
        from app.agents.tools.validate_fields import validate_fields

        data = _valid_extracted_data()
        del data["seller"]["gstin"]
        result = validate_fields(data)

    assert result["is_valid"] is False
    assert any("seller" in e.lower() and "gstin" in e.lower() for e in result["errors"])


@pytest.mark.asyncio
async def test_missing_buyer_gstin():
    """Missing buyer GSTIN should produce an error."""
    with patch("app.agents.tools.validate_fields.settings") as mock_settings:
        mock_settings.DEMO_MODE = False
        from app.agents.tools.validate_fields import validate_fields

        data = _valid_extracted_data()
        del data["buyer"]["gstin"]
        result = validate_fields(data)

    assert result["is_valid"] is False
    assert any("buyer" in e.lower() and "gstin" in e.lower() for e in result["errors"])


@pytest.mark.asyncio
async def test_missing_line_items():
    """Missing line_items should produce an error."""
    with patch("app.agents.tools.validate_fields.settings") as mock_settings:
        mock_settings.DEMO_MODE = False
        from app.agents.tools.validate_fields import validate_fields

        data = _valid_extracted_data()
        del data["line_items"]
        result = validate_fields(data)

    assert result["is_valid"] is False
    assert any("line_items" in e.lower() for e in result["errors"])


@pytest.mark.asyncio
async def test_empty_line_items():
    """Empty line_items list should produce an error."""
    with patch("app.agents.tools.validate_fields.settings") as mock_settings:
        mock_settings.DEMO_MODE = False
        from app.agents.tools.validate_fields import validate_fields

        data = _valid_extracted_data()
        data["line_items"] = []
        result = validate_fields(data)

    assert result["is_valid"] is False
    assert any("line_items" in e.lower() for e in result["errors"])


@pytest.mark.asyncio
async def test_missing_date():
    """Missing invoice_date should produce an error."""
    with patch("app.agents.tools.validate_fields.settings") as mock_settings:
        mock_settings.DEMO_MODE = False
        from app.agents.tools.validate_fields import validate_fields

        data = _valid_extracted_data()
        del data["invoice_date"]
        result = validate_fields(data)

    assert result["is_valid"] is False
    assert any("invoice_date" in e.lower() for e in result["errors"])


@pytest.mark.asyncio
async def test_missing_amount():
    """Missing total_amount should produce an error."""
    with patch("app.agents.tools.validate_fields.settings") as mock_settings:
        mock_settings.DEMO_MODE = False
        from app.agents.tools.validate_fields import validate_fields

        data = _valid_extracted_data()
        del data["total_amount"]
        result = validate_fields(data)

    assert result["is_valid"] is False
    assert any("total_amount" in e.lower() for e in result["errors"])


# ---------------------------------------------------------------------------
# Tests: Math validation
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_valid_math():
    """Valid extracted data should pass math checks."""
    with patch("app.agents.tools.validate_fields.settings") as mock_settings:
        mock_settings.DEMO_MODE = False
        from app.agents.tools.validate_fields import validate_fields

        result = validate_fields(_valid_extracted_data())

    assert result["is_valid"] is True
    assert result["errors"] == []


@pytest.mark.asyncio
async def test_line_items_sum_mismatch():
    """Sum of line_items amounts != subtotal should produce an error."""
    with patch("app.agents.tools.validate_fields.settings") as mock_settings:
        mock_settings.DEMO_MODE = False
        from app.agents.tools.validate_fields import validate_fields

        data = _valid_extracted_data()
        data["subtotal"] = 9999.0  # Should be 10000.0
        result = validate_fields(data)

    assert result["is_valid"] is False
    assert any("subtotal" in e.lower() for e in result["errors"])


@pytest.mark.asyncio
async def test_total_mismatch():
    """subtotal + tax_amount != total_amount should produce an error."""
    with patch("app.agents.tools.validate_fields.settings") as mock_settings:
        mock_settings.DEMO_MODE = False
        from app.agents.tools.validate_fields import validate_fields

        data = _valid_extracted_data()
        data["total_amount"] = 12000.0  # Should be 11800.0
        result = validate_fields(data)

    assert result["is_valid"] is False
    assert any("total" in e.lower() for e in result["errors"])


@pytest.mark.asyncio
async def test_math_tolerance_passes():
    """Small rounding differences (< 1.0) should produce warning, not error."""
    with patch("app.agents.tools.validate_fields.settings") as mock_settings:
        mock_settings.DEMO_MODE = False
        from app.agents.tools.validate_fields import validate_fields

        data = _valid_extracted_data()
        data["total_amount"] = 11800.50  # Within tolerance
        result = validate_fields(data)

    # Should pass with warning (within 1.0 tolerance)
    assert result["is_valid"] is True
    assert len(result["warnings"]) > 0


# ---------------------------------------------------------------------------
# Tests: GSTIN format validation
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_valid_gstin_format():
    """Valid GSTIN format should not produce errors."""
    with patch("app.agents.tools.validate_fields.settings") as mock_settings:
        mock_settings.DEMO_MODE = False
        from app.agents.tools.validate_fields import validate_fields

        result = validate_fields(_valid_extracted_data())

    assert result["is_valid"] is True


@pytest.mark.asyncio
async def test_invalid_gstin_length():
    """GSTIN with wrong length should produce an error."""
    with patch("app.agents.tools.validate_fields.settings") as mock_settings:
        mock_settings.DEMO_MODE = False
        from app.agents.tools.validate_fields import validate_fields

        data = _valid_extracted_data()
        data["seller"]["gstin"] = "27AABCT1234"  # Too short
        result = validate_fields(data)

    assert result["is_valid"] is False
    assert any("gstin" in e.lower() for e in result["errors"])


@pytest.mark.asyncio
async def test_invalid_gstin_pattern():
    """GSTIN with invalid pattern should produce an error."""
    with patch("app.agents.tools.validate_fields.settings") as mock_settings:
        mock_settings.DEMO_MODE = False
        from app.agents.tools.validate_fields import validate_fields

        data = _valid_extracted_data()
        data["buyer"]["gstin"] = "99XYZAB1234R1Z1"  # Invalid state code 99
        result = validate_fields(data)

    assert result["is_valid"] is False
    assert any("gstin" in e.lower() for e in result["errors"])


# ---------------------------------------------------------------------------
# Tests: Date validation
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_future_invoice_date():
    """Invoice date in the future should produce a warning."""
    with patch("app.agents.tools.validate_fields.settings") as mock_settings:
        mock_settings.DEMO_MODE = False
        from app.agents.tools.validate_fields import validate_fields

        data = _valid_extracted_data()
        data["invoice_date"] = "2099-01-01"
        result = validate_fields(data)

    assert any("future" in w.lower() for w in result["warnings"])


@pytest.mark.asyncio
async def test_due_date_before_invoice_date():
    """Due date before invoice date should produce a warning."""
    with patch("app.agents.tools.validate_fields.settings") as mock_settings:
        mock_settings.DEMO_MODE = False
        from app.agents.tools.validate_fields import validate_fields

        data = _valid_extracted_data()
        data["invoice_date"] = "2026-03-15"
        data["due_date"] = "2026-03-01"  # Before invoice date
        result = validate_fields(data)

    assert any(
        "due_date" in w.lower() or "due date" in w.lower() for w in result["warnings"]
    )


@pytest.mark.asyncio
async def test_invalid_date_format():
    """Invalid date format should produce an error."""
    with patch("app.agents.tools.validate_fields.settings") as mock_settings:
        mock_settings.DEMO_MODE = False
        from app.agents.tools.validate_fields import validate_fields

        data = _valid_extracted_data()
        data["invoice_date"] = "15/03/2026"  # Wrong format
        result = validate_fields(data)

    assert result["is_valid"] is False
    assert any("date" in e.lower() for e in result["errors"])


# ---------------------------------------------------------------------------
# Tests: Return shape
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_return_shape():
    """Result must have is_valid, errors, and warnings keys."""
    with patch("app.agents.tools.validate_fields.settings") as mock_settings:
        mock_settings.DEMO_MODE = False
        from app.agents.tools.validate_fields import validate_fields

        result = validate_fields(_valid_extracted_data())

    assert "is_valid" in result
    assert "errors" in result
    assert "warnings" in result
    assert isinstance(result["is_valid"], bool)
    assert isinstance(result["errors"], list)
    assert isinstance(result["warnings"], list)
