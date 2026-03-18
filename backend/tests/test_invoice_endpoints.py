"""Integration tests for invoice API stub endpoints (DEMO_MODE)."""

import io

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_invoices(client: AsyncClient):
    """GET /api/v1/invoices returns list with total count."""
    response = await client.get("/api/v1/invoices")

    assert response.status_code == 200
    data = response.json()
    assert "invoices" in data
    assert isinstance(data["invoices"], list)
    assert len(data["invoices"]) > 0
    assert "total" in data
    assert data["total"] > 0
    assert "page" in data
    assert "limit" in data


@pytest.mark.asyncio
async def test_get_invoice_detail(client: AsyncClient):
    """GET /api/v1/invoices/inv_stub_001 returns invoice with extracted_data."""
    response = await client.get("/api/v1/invoices/inv_stub_001")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "inv_stub_001"
    assert "extracted_data" in data
    assert data["extracted_data"]["invoice_number"] == "INV-2026-001"
    assert "seller" in data["extracted_data"]
    assert "buyer" in data["extracted_data"]
    assert "validation" in data
    assert "fraud_detection" in data
    assert "risk_assessment" in data
    assert "underwriting" in data


@pytest.mark.asyncio
async def test_upload_invoice(client: AsyncClient):
    """POST /api/v1/invoices/upload with multipart file returns invoice_id."""
    files = {"file": ("test.pdf", io.BytesIO(b"%PDF-1.4 test"), "application/pdf")}

    response = await client.post("/api/v1/invoices/upload", files=files)

    assert response.status_code == 200
    data = response.json()
    assert "invoice_id" in data
    assert data["invoice_id"]  # non-empty
    assert "status" in data
    assert data["status"] == "processing"
    assert "ws_url" in data


@pytest.mark.asyncio
async def test_invoice_stream_sse(client: AsyncClient):
    """GET /api/v1/invoices/inv_stub_001/stream returns SSE content type."""
    response = await client.get("/api/v1/invoices/inv_stub_001/stream")

    assert response.status_code == 200
    assert "text/event-stream" in response.headers["content-type"]
    # Verify the body contains SSE data lines
    body = response.text
    assert "data:" in body


@pytest.mark.asyncio
async def test_audit_trail(client: AsyncClient):
    """GET /api/v1/invoices/inv_stub_001/audit-trail returns agent traces."""
    response = await client.get("/api/v1/invoices/inv_stub_001/audit-trail")

    assert response.status_code == 200
    data = response.json()
    assert "invoice_id" in data
    assert data["invoice_id"] == "inv_stub_001"
    assert "agents" in data
    assert isinstance(data["agents"], list)
    assert len(data["agents"]) > 0
    assert "total_duration_ms" in data
    assert "handoffs" in data
