"""Integration tests for wallet API endpoints (requires auth)."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_link_wallet(client: AsyncClient):
    """POST /api/v1/wallet/link with valid address returns linked=True."""
    # Algorand addresses are exactly 58 characters
    wallet_addr = "ALGO7TEST2ADDRESS3FOR4UNIT5TESTING6WALLET7X4F2ABCDEFGHIJKL"
    body = {
        "wallet_address": wallet_addr,
        "signed_message": "signed_proof",
    }

    response = await client.post("/api/v1/wallet/link", json=body)

    assert response.status_code == 200
    data = response.json()
    assert data["linked"] is True
    assert data["wallet_address"] == wallet_addr


@pytest.mark.asyncio
async def test_link_wallet_invalid_address(client: AsyncClient):
    """POST /api/v1/wallet/link with short address returns 400."""
    body = {
        "wallet_address": "TOOSHORT",
        "signed_message": "signed_proof",
    }

    response = await client.post("/api/v1/wallet/link", json=body)

    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert "58 characters" in data["detail"]


@pytest.mark.asyncio
async def test_wallet_status_no_wallet(client: AsyncClient):
    """GET /api/v1/wallet/status for user without wallet returns linked=False."""
    response = await client.get("/api/v1/wallet/status")

    assert response.status_code == 200
    data = response.json()
    assert data["linked"] is False
    assert data["wallet_address"] is None


@pytest.mark.asyncio
async def test_unlink_wallet_no_wallet(client: AsyncClient):
    """DELETE /api/v1/wallet/link when no wallet linked returns 400."""
    response = await client.delete("/api/v1/wallet/link")

    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert "No wallet linked" in data["detail"]
