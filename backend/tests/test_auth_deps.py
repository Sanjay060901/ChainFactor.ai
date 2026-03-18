"""Tests for auth dependencies -- demo mode and IDOR prevention."""

import uuid

import pytest
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.modules.auth.dependencies import (
    DEMO_USER_SUB,
    _get_or_create_demo_user,
    require_owner,
)


# ---------------------------------------------------------------------------
# Demo mode: _get_or_create_demo_user
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_current_user_demo_mode(db_session: AsyncSession):
    """In demo mode, _get_or_create_demo_user creates a demo user in the DB."""
    user = await _get_or_create_demo_user(db_session)

    assert user is not None
    assert user.cognito_sub == DEMO_USER_SUB
    assert user.name == "Demo User"
    assert user.email == "demo@chainfactor.ai"

    # Verify persisted in DB
    result = await db_session.execute(
        select(User).where(User.cognito_sub == DEMO_USER_SUB)
    )
    db_user = result.scalar_one_or_none()
    assert db_user is not None
    assert db_user.id == user.id


@pytest.mark.asyncio
async def test_get_current_user_demo_mode_idempotent(db_session: AsyncSession):
    """Calling _get_or_create_demo_user twice returns the same user (no duplicate)."""
    user_first = await _get_or_create_demo_user(db_session)
    user_second = await _get_or_create_demo_user(db_session)

    assert user_first.id == user_second.id
    assert user_first.cognito_sub == user_second.cognito_sub

    # Verify exactly one demo user in DB
    result = await db_session.execute(
        select(User).where(User.cognito_sub == DEMO_USER_SUB)
    )
    users = result.scalars().all()
    assert len(users) == 1


# ---------------------------------------------------------------------------
# IDOR prevention: require_owner
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_require_owner_success(test_user: User):
    """require_owner does not raise when user_id matches the current user."""
    # Should not raise any exception
    require_owner(invoice_user_id=test_user.id, current_user=test_user)


@pytest.mark.asyncio
async def test_require_owner_forbidden(test_user: User):
    """require_owner raises HTTPException 403 when user_id does not match."""
    other_user_id = uuid.UUID("99999999-9999-9999-9999-999999999999")

    with pytest.raises(HTTPException) as exc_info:
        require_owner(invoice_user_id=other_user_id, current_user=test_user)

    assert exc_info.value.status_code == 403
    assert "do not have access" in exc_info.value.detail.lower()
