"""Tests for auth dependencies -- IDOR prevention."""

import uuid

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.modules.auth.dependencies import (
    require_owner,
)


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
