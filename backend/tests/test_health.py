"""Integration tests for health check endpoint."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(unauth_client: AsyncClient):
    """GET /health returns healthy status (no auth required)."""
    response = await unauth_client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data
