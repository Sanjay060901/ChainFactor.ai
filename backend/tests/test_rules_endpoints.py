"""Integration tests for seller rules API endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_rules_empty(client: AsyncClient):
    """GET /api/v1/rules returns empty rules list when none exist."""
    response = await client.get("/api/v1/rules")

    assert response.status_code == 200
    data = response.json()
    assert "rules" in data
    assert isinstance(data["rules"], list)
    assert "default_action" in data


@pytest.mark.asyncio
async def test_create_and_list_rule(client: AsyncClient):
    """Create a rule then verify it appears in the list."""
    body = {
        "conditions": [
            {"field": "invoice_amount", "operator": "less_than", "value": 500000}
        ],
        "action": "auto_approve",
    }

    # Create
    response = await client.post("/api/v1/rules", json=body)
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert data["action"] == "auto_approve"
    assert "conditions" in data
    assert len(data["conditions"]) == 1
    assert data["is_active"] is True
    rule_id = data["id"]

    # List
    list_resp = await client.get("/api/v1/rules")
    assert list_resp.status_code == 200
    rules = list_resp.json()["rules"]
    assert any(r["id"] == rule_id for r in rules)


@pytest.mark.asyncio
async def test_create_update_delete_rule(client: AsyncClient):
    """Full CRUD lifecycle for a rule."""
    # Create
    body = {
        "conditions": [
            {"field": "risk_score", "operator": "greater_than", "value": 80}
        ],
        "action": "flag_for_review",
    }
    create_resp = await client.post("/api/v1/rules", json=body)
    assert create_resp.status_code == 200
    rule_id = create_resp.json()["id"]

    # Update
    update_body = {"is_active": False}
    update_resp = await client.put(f"/api/v1/rules/{rule_id}", json=update_body)
    assert update_resp.status_code == 200
    assert update_resp.json()["is_active"] is False

    # Delete
    delete_resp = await client.delete(f"/api/v1/rules/{rule_id}")
    assert delete_resp.status_code == 200
    assert "message" in delete_resp.json()


@pytest.mark.asyncio
async def test_update_default_action(client: AsyncClient):
    """PUT /api/v1/rules/default-action updates the default action."""
    body = {"default_action": "reject"}

    response = await client.put("/api/v1/rules/default-action", json=body)

    assert response.status_code == 200
    data = response.json()
    assert data["default_action"] == "reject"
