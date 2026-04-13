"""TDD tests for Feature 4.4: extract_invoice tool.

Tests the Strands @tool that extracts structured data from PDF invoices:
- Textract extraction with mocked boto3 client
- Fallback to Claude vision when Textract fails
- Output matches ExtractedData schema shape
"""

from unittest.mock import MagicMock, patch

import pytest

from app.schemas.invoice import ExtractedData


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _validate_extracted_data_shape(data: dict) -> None:
    """Assert that data dict matches ExtractedData schema structure."""
    model = ExtractedData(**data)
    assert model.seller.name
    assert model.seller.gstin
    assert model.buyer.name
    assert model.buyer.gstin
    assert model.invoice_number
    assert model.invoice_date
    assert model.due_date
    assert model.total_amount > 0
    assert model.tax_amount >= 0
    assert model.tax_rate >= 0
    assert model.subtotal > 0
    assert len(model.line_items) > 0
    for item in model.line_items:
        assert item.description
        assert item.amount > 0


# ---------------------------------------------------------------------------
# Test: Textract extraction (mocked)
# ---------------------------------------------------------------------------

# Minimal Textract AnalyzeDocument response for a simple invoice
MOCK_TEXTRACT_RESPONSE = {
    "Blocks": [
        {
            "BlockType": "LINE",
            "Text": "Invoice Number: INV-2026-001",
            "Confidence": 99.5,
            "Geometry": {
                "BoundingBox": {"Left": 0.1, "Top": 0.1, "Width": 0.3, "Height": 0.02}
            },
        },
        {
            "BlockType": "LINE",
            "Text": "Invoice Date: 2026-03-15",
            "Confidence": 99.1,
        },
        {
            "BlockType": "LINE",
            "Text": "Due Date: 2026-04-15",
            "Confidence": 98.8,
        },
        {
            "BlockType": "LINE",
            "Text": "Seller: Acme Exports Pvt Ltd",
            "Confidence": 98.0,
        },
        {
            "BlockType": "LINE",
            "Text": "Seller GSTIN: 27AABCA1234R1ZM",
            "Confidence": 97.5,
        },
        {
            "BlockType": "LINE",
            "Text": "Buyer: Global Imports Ltd",
            "Confidence": 98.0,
        },
        {
            "BlockType": "LINE",
            "Text": "Buyer GSTIN: 07AABCG5678R1ZN",
            "Confidence": 97.5,
        },
        {
            "BlockType": "LINE",
            "Text": "Subtotal: 50000.00",
            "Confidence": 99.0,
        },
        {
            "BlockType": "LINE",
            "Text": "IGST @18%: 9000.00",
            "Confidence": 98.5,
        },
        {
            "BlockType": "LINE",
            "Text": "Total: 59000.00",
            "Confidence": 99.2,
        },
        {
            "BlockType": "LINE",
            "Text": "Steel Rods HSN:7214 Qty:100 Rate:500 Amount:50000.00",
            "Confidence": 96.0,
        },
    ]
}


@pytest.mark.asyncio
async def test_textract_extraction_success():
    """Textract path: mocked client returns blocks, tool parses into ExtractedData."""
    import json

    mock_s3_client = MagicMock()
    mock_s3_client.get_object.return_value = {
        "Body": MagicMock(read=MagicMock(return_value=b"%PDF-fake-content"))
    }

    mock_textract_client = MagicMock()
    mock_textract_client.analyze_document.return_value = MOCK_TEXTRACT_RESPONSE

    mock_bedrock_client = MagicMock()

    parsed_json = json.dumps(
        {
            "seller": {
                "name": "Acme Exports Pvt Ltd",
                "gstin": "27AABCA1234R1ZM",
                "address": "Mumbai, MH",
            },
            "buyer": {
                "name": "Global Imports Ltd",
                "gstin": "07AABCG5678R1ZN",
                "address": "Delhi, DL",
            },
            "invoice_number": "INV-2026-001",
            "invoice_date": "2026-03-15",
            "due_date": "2026-04-15",
            "subtotal": 50000.00,
            "tax_amount": 9000.00,
            "tax_rate": 18.0,
            "total_amount": 59000.00,
            "line_items": [
                {
                    "description": "Steel Rods",
                    "hsn_code": "7214",
                    "quantity": 100,
                    "rate": 500.0,
                    "amount": 50000.00,
                }
            ],
        }
    )
    mock_bedrock_response = {
        "body": MagicMock(
            read=MagicMock(
                return_value=json.dumps(
                    {"content": [{"type": "text", "text": parsed_json}]}
                ).encode()
            )
        )
    }
    mock_bedrock_client.invoke_model.return_value = mock_bedrock_response

    with patch("boto3.client") as mock_boto:

        def _boto_client_factory(service, **kwargs):
            if service == "s3":
                return mock_s3_client
            if service == "textract":
                return mock_textract_client
            if service == "bedrock-runtime":
                return mock_bedrock_client
            raise ValueError(f"Unexpected service: {service}")

        mock_boto.side_effect = _boto_client_factory

        import importlib
        import app.agents.tools.extract_invoice as mod

        importlib.reload(mod)

        result = mod.extract_invoice(
            s3_file_key="invoices/test-invoice.pdf",
            bucket_name="test-bucket",
        )

        assert isinstance(result, dict)
        _validate_extracted_data_shape(result)
        mock_textract_client.analyze_document.assert_called_once()


# ---------------------------------------------------------------------------
# Test: Fallback to Claude vision when Textract fails
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_fallback_to_claude_on_textract_failure():
    """When Textract raises an exception, tool falls back to Claude vision via Bedrock."""
    import json

    mock_s3_client = MagicMock()
    mock_s3_client.get_object.return_value = {
        "Body": MagicMock(read=MagicMock(return_value=b"%PDF-fake-content"))
    }

    mock_textract_client = MagicMock()
    mock_textract_client.analyze_document.side_effect = Exception(
        "Textract unavailable"
    )

    fallback_json = json.dumps(
        {
            "seller": {
                "name": "Fallback Seller",
                "gstin": "27AABCF9999R1ZP",
                "address": "Pune, MH",
            },
            "buyer": {
                "name": "Fallback Buyer",
                "gstin": "07AABCB8888R1ZQ",
                "address": "Delhi, DL",
            },
            "invoice_number": "INV-FALLBACK-001",
            "invoice_date": "2026-03-10",
            "due_date": "2026-04-10",
            "subtotal": 30000.00,
            "tax_amount": 5400.00,
            "tax_rate": 18.0,
            "total_amount": 35400.00,
            "line_items": [
                {
                    "description": "Copper Wire",
                    "hsn_code": "7408",
                    "quantity": 50,
                    "rate": 600.0,
                    "amount": 30000.00,
                }
            ],
        }
    )

    mock_bedrock_client = MagicMock()
    mock_bedrock_response = {
        "body": MagicMock(
            read=MagicMock(
                return_value=json.dumps(
                    {"content": [{"type": "text", "text": fallback_json}]}
                ).encode()
            )
        )
    }
    mock_bedrock_client.invoke_model.return_value = mock_bedrock_response

    with patch("boto3.client") as mock_boto:

        def _boto_client_factory(service, **kwargs):
            if service == "s3":
                return mock_s3_client
            if service == "textract":
                return mock_textract_client
            if service == "bedrock-runtime":
                return mock_bedrock_client
            raise ValueError(f"Unexpected service: {service}")

        mock_boto.side_effect = _boto_client_factory

        import importlib
        import app.agents.tools.extract_invoice as mod

        importlib.reload(mod)

        result = mod.extract_invoice(
            s3_file_key="invoices/test-fallback.pdf",
            bucket_name="test-bucket",
        )

        assert isinstance(result, dict)
        _validate_extracted_data_shape(result)
        mock_textract_client.analyze_document.assert_called_once()
        mock_bedrock_client.invoke_model.assert_called_once()


# ---------------------------------------------------------------------------
# Test: Tool decorator
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_extract_invoice_is_callable():
    """extract_invoice decorated with @tool should be directly callable."""
    from app.agents.tools.extract_invoice import extract_invoice

    assert callable(extract_invoice)
