"""Tests for Feature 7.1: Seller Rules CRUD -- real DB operations.

Tests cover:
- create, list, update, delete rules + default action
- IDOR prevention on update/delete
"""

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.rule import Rule
from app.models.user import User
from app.models.user_settings import UserSettings


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _create_rule(
    db: AsyncSession,
    user: User,
    *,
    conditions: list | None = None,
    action: str = "auto_approve",
    is_active: bool = True,
) -> Rule:
    """Insert a rule row for a given user."""
    rule = Rule(
        id=uuid.uuid4(),
        user_id=user.id,
        conditions=conditions or [
            {"field": "amount", "operator": "lt", "value": 500000},
        ],
        action=action,
        is_active=is_active,
    )
    db.add(rule)
    await db.flush()
    return rule


# ---------------------------------------------------------------------------
# Tests: real DB CRUD
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_list_rules_real_empty(
    client: AsyncClient, db_session: AsyncSession, test_user: User
):
    """Non-DEMO with no rules returns empty list and default action."""
    response = await client.get("/api/v1/rules")

    assert response.status_code == 200
    data = response.json()
    assert data["rules"] == []
    assert data["default_action"] == "flag_for_review"


@pytest.mark.asyncio
async def test_create_rule_real(
    client: AsyncClient, db_session: AsyncSession, test_user: User
):
    """Non-DEMO creates a real rule in DB."""
    body = {
        "conditions": [{"field": "amount", "operator": "lt", "value": 750000}],
        "action": "auto_approve",
    }

    response = await client.post("/api/v1/rules", json=body)

    assert response.status_code == 200
    data = response.json()
    assert data["action"] == "auto_approve"
    assert len(data["conditions"]) == 1
    assert data["is_active"] is True
    assert data["id"]  # Non-empty UUID string


@pytest.mark.asyncio
async def test_list_rules_real_returns_user_rules(
    client: AsyncClient, db_session: AsyncSession, test_user: User
):
    """Non-DEMO returns only rules belonging to the authenticated user."""
    await _create_rule(db_session, test_user, action="auto_approve")
    await _create_rule(db_session, test_user, action="reject")

    response = await client.get("/api/v1/rules")

    data = response.json()
    assert len(data["rules"]) == 2


@pytest.mark.asyncio
async def test_list_rules_idor_prevention(
    client: AsyncClient, db_session: AsyncSession, test_user: User
):
    """User cannot see rules belonging to another user."""
    other_user = User(
        id=uuid.UUID("77777777-7777-7777-7777-777777777777"),
        cognito_sub="other-rules-sub",
        name="Other",
        email="other-rules@test.com",
        phone="+910000000002",
        company_name="Other Corp",
        gstin="29AABCO5678R1ZX",
    )
    db_session.add(other_user)
    await db_session.flush()

    await _create_rule(db_session, test_user, action="auto_approve")
    await _create_rule(db_session, other_user, action="reject")

    response = await client.get("/api/v1/rules")

    data = response.json()
    assert len(data["rules"]) == 1
    assert data["rules"][0]["action"] == "auto_approve"


@pytest.mark.asyncio
async def test_update_rule_real(
    client: AsyncClient, db_session: AsyncSession, test_user: User
):
    """Non-DEMO updates an existing rule."""
    rule = await _create_rule(db_session, test_user, action="auto_approve")

    body = {"action": "reject", "is_active": False}

    response = await client.put(f"/api/v1/rules/{rule.id}", json=body)

    assert response.status_code == 200
    data = response.json()
    assert data["action"] == "reject"
    assert data["is_active"] is False


@pytest.mark.asyncio
async def test_update_rule_not_found(
    client: AsyncClient, db_session: AsyncSession, test_user: User
):
    """Non-DEMO update on non-existent rule returns 404."""
    fake_id = uuid.uuid4()
    body = {"action": "reject"}

    response = await client.put(f"/api/v1/rules/{fake_id}", json=body)

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_rule_idor(
    client: AsyncClient, db_session: AsyncSession, test_user: User
):
    """Cannot update a rule belonging to another user."""
    other_user = User(
        id=uuid.UUID("66666666-6666-6666-6666-666666666666"),
        cognito_sub="idor-update-sub",
        name="Other",
        email="idor-update@test.com",
        phone="+910000000003",
        company_name="Other Corp",
        gstin="29AABCI1234R1ZX",
    )
    db_session.add(other_user)
    await db_session.flush()

    rule = await _create_rule(db_session, other_user, action="auto_approve")

    body = {"action": "reject"}
    response = await client.put(f"/api/v1/rules/{rule.id}", json=body)

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_delete_rule_real(
    client: AsyncClient, db_session: AsyncSession, test_user: User
):
    """Non-DEMO deletes a rule from DB."""
    rule = await _create_rule(db_session, test_user)

    response = await client.delete(f"/api/v1/rules/{rule.id}")

    assert response.status_code == 200
    data = response.json()
    assert "deleted" in data["message"].lower()


@pytest.mark.asyncio
async def test_delete_rule_not_found(
    client: AsyncClient, db_session: AsyncSession, test_user: User
):
    """Non-DEMO delete on non-existent rule returns 404."""
    fake_id = uuid.uuid4()

    response = await client.delete(f"/api/v1/rules/{fake_id}")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_rule_idor(
    client: AsyncClient, db_session: AsyncSession, test_user: User
):
    """Cannot delete a rule belonging to another user."""
    other_user = User(
        id=uuid.UUID("55555555-5555-5555-5555-555555555555"),
        cognito_sub="idor-delete-sub",
        name="Other",
        email="idor-delete@test.com",
        phone="+910000000004",
        company_name="Other Corp",
        gstin="29AABCD1234R1ZX",
    )
    db_session.add(other_user)
    await db_session.flush()

    rule = await _create_rule(db_session, other_user)

    response = await client.delete(f"/api/v1/rules/{rule.id}")

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_set_default_action_real(
    client: AsyncClient, db_session: AsyncSession, test_user: User
):
    """Non-DEMO creates/updates UserSettings.default_action."""
    body = {"default_action": "reject"}

    response = await client.put("/api/v1/rules/default-action", json=body)

    assert response.status_code == 200
    data = response.json()
    assert data["default_action"] == "reject"


@pytest.mark.asyncio
async def test_set_default_action_real_update_existing(
    client: AsyncClient, db_session: AsyncSession, test_user: User
):
    """Non-DEMO updates an existing UserSettings record."""
    # Create initial settings
    us = UserSettings(
        id=uuid.uuid4(),
        user_id=test_user.id,
        default_action="flag_for_review",
    )
    db_session.add(us)
    await db_session.flush()

    body = {"default_action": "always_approve"}
    response = await client.put("/api/v1/rules/default-action", json=body)

    assert response.status_code == 200
    data = response.json()
    assert data["default_action"] == "always_approve"
