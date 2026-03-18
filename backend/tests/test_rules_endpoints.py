"""Integration tests for seller rules API stub endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_rules(client: AsyncClient):
    """GET /api/v1/rules returns rules list."""
    response = await client.get("/api/v1/rules")

    assert response.status_code == 200
    data = response.json()
    assert "rules" in data
    assert isinstance(data["rules"], list)
    assert len(data["rules"]) > 0
    assert "default_action" in data

    # Verify rule structure
    rule = data["rules"][0]
    assert "id" in rule
    assert "conditions" in rule
    assert "action" in rule
    assert "is_active" in rule


@pytest.mark.asyncio
async def test_create_rule(client: AsyncClient):
    """POST /api/v1/rules with conditions creates a new rule."""
    body = {
        "conditions": [
            {"field": "invoice_amount", "operator": "less_than", "value": 500000}
        ],
        "action": "auto_approve",
    }

    response = await client.post("/api/v1/rules", json=body)

    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert data["action"] == "auto_approve"
    assert "conditions" in data
    assert len(data["conditions"]) == 1
    assert data["is_active"] is True


@pytest.mark.asyncio
async def test_update_rule(client: AsyncClient):
    """PUT /api/v1/rules/rule_stub_001 updates an existing rule."""
    body = {"is_active": False}

    response = await client.put("/api/v1/rules/rule_stub_001", json=body)

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "rule_stub_001"
    assert data["is_active"] is False


@pytest.mark.asyncio
async def test_delete_rule(client: AsyncClient):
    """DELETE /api/v1/rules/rule_stub_001 deletes the rule."""
    response = await client.delete("/api/v1/rules/rule_stub_001")

    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "rule_stub_001" in data["message"]


@pytest.mark.asyncio
async def test_update_default_action(client: AsyncClient):
    """PUT /api/v1/rules/default-action updates the default action."""
    body = {"default_action": "reject"}

    response = await client.put("/api/v1/rules/default-action", json=body)

    assert response.status_code == 200
    data = response.json()
    assert data["default_action"] == "reject"
