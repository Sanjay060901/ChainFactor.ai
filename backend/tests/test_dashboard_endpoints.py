"""Integration tests for dashboard API stub endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_dashboard_summary(client: AsyncClient):
    """GET /api/v1/dashboard/summary returns stats with total_invoices fields."""
    response = await client.get("/api/v1/dashboard/summary")

    assert response.status_code == 200
    data = response.json()
    assert "active_invoices" in data
    assert "pending_invoices" in data
    assert "total_value" in data
    assert data["total_value"] > 0
    assert "avg_risk_score" in data
    assert "approval_rate" in data
    assert "risk_distribution" in data
    assert "monthly_volume" in data
    assert isinstance(data["monthly_volume"], list)
    assert len(data["monthly_volume"]) > 0


@pytest.mark.asyncio
async def test_nl_query(client: AsyncClient):
    """POST /api/v1/dashboard/nl-query returns an answer for the query."""
    body = {"query": "how many invoices"}

    response = await client.post("/api/v1/dashboard/nl-query", json=body)

    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert data["answer"]  # non-empty
    assert "how many invoices" in data["answer"]
    assert "data" in data
