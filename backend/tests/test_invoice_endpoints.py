"""Integration tests for invoice API endpoints."""

import io

import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, patch


@pytest.mark.asyncio
async def test_list_invoices_empty(client: AsyncClient):
    """GET /api/v1/invoices returns empty list when no invoices exist."""
    response = await client.get("/api/v1/invoices")

    assert response.status_code == 200
    data = response.json()
    assert "invoices" in data
    assert isinstance(data["invoices"], list)
    assert "total" in data
    assert "page" in data
    assert "limit" in data


@pytest.mark.asyncio
async def test_upload_invoice(client: AsyncClient):
    """POST /api/v1/invoices/upload with multipart file returns invoice_id."""
    files = {"file": ("test.pdf", io.BytesIO(b"%PDF-1.4 test content here"), "application/pdf")}

    with patch(
        "app.modules.invoices.router.upload_to_s3", new_callable=AsyncMock
    ) as mock_s3:
        mock_s3.return_value = "invoices/test-user/key/test.pdf"
        response = await client.post("/api/v1/invoices/upload", files=files)

    assert response.status_code == 200
    data = response.json()
    assert "invoice_id" in data
    assert data["invoice_id"]  # non-empty
    assert "status" in data
    assert data["status"] == "uploaded"
    assert "ws_url" in data
