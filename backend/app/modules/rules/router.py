"""Seller rules API endpoints. DEMO_MODE returns stubs; real mode uses DB."""

import uuid as _uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.user import User
from app.modules.auth.dependencies import get_current_user
from app.schemas.common import MessageResponse
from app.schemas.rules import (
    DefaultActionRequest,
    DefaultActionResponse,
    RuleCondition,
    RuleCreateRequest,
    RuleResponse,
    RuleUpdateRequest,
    RulesListResponse,
)

router = APIRouter(prefix="/rules", tags=["rules"])

STUB_NOW = datetime(2026, 3, 18, 10, 0, 0, tzinfo=timezone.utc)

STUB_RULES = [
    RuleResponse(
        id="rule_stub_001",
        conditions=[
            RuleCondition(field="amount", operator="lt", value=500000),
            RuleCondition(field="risk_score", operator="gt", value=60),
            RuleCondition(field="fraud_flags", operator="eq", value=0),
        ],
        action="auto_approve",
        is_active=True,
        created_at=STUB_NOW,
    ),
    RuleResponse(
        id="rule_stub_002",
        conditions=[
            RuleCondition(field="amount", operator="lt", value=1000000),
            RuleCondition(field="risk_score", operator="gt", value=80),
            RuleCondition(field="cibil_score", operator="gt", value=700),
        ],
        action="auto_approve",
        is_active=True,
        created_at=STUB_NOW,
    ),
]


@router.get("", response_model=RulesListResponse)
async def list_rules(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if settings.DEMO_MODE:
        return RulesListResponse(rules=STUB_RULES, default_action="flag_for_review")

    from sqlalchemy import select

    from app.models.rule import Rule
    from app.models.user_settings import UserSettings

    # Get rules for current user
    result = await db.execute(select(Rule).where(Rule.user_id == current_user.id))
    rules = result.scalars().all()

    # Get default action
    us_result = await db.execute(
        select(UserSettings).where(UserSettings.user_id == current_user.id)
    )
    user_settings = us_result.scalar_one_or_none()
    default_action = (
        user_settings.default_action if user_settings else "flag_for_review"
    )

    items = [
        RuleResponse(
            id=str(rule.id),
            conditions=[RuleCondition(**c) for c in (rule.conditions or [])],
            action=rule.action,
            is_active=rule.is_active,
            created_at=rule.created_at,
        )
        for rule in rules
    ]

    return RulesListResponse(rules=items, default_action=default_action)


@router.post("", response_model=RuleResponse)
async def create_rule(
    body: RuleCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if settings.DEMO_MODE:
        return RuleResponse(
            id="rule_stub_new",
            conditions=body.conditions,
            action=body.action,
            is_active=True,
            created_at=STUB_NOW,
        )

    from app.models.rule import Rule

    rule = Rule(
        id=_uuid.uuid4(),
        user_id=current_user.id,
        conditions=[c.model_dump() for c in body.conditions],
        action=body.action,
        is_active=True,
    )
    db.add(rule)
    await db.flush()

    return RuleResponse(
        id=str(rule.id),
        conditions=body.conditions,
        action=rule.action,
        is_active=rule.is_active,
        created_at=rule.created_at,
    )


@router.put("/default-action", response_model=DefaultActionResponse)
async def set_default_action(
    body: DefaultActionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if settings.DEMO_MODE:
        return DefaultActionResponse(default_action=body.default_action)

    from sqlalchemy import select

    from app.models.user_settings import UserSettings

    result = await db.execute(
        select(UserSettings).where(UserSettings.user_id == current_user.id)
    )
    user_settings = result.scalar_one_or_none()

    if user_settings:
        user_settings.default_action = body.default_action
    else:
        user_settings = UserSettings(
            id=_uuid.uuid4(),
            user_id=current_user.id,
            default_action=body.default_action,
        )
        db.add(user_settings)

    await db.flush()
    return DefaultActionResponse(default_action=body.default_action)


@router.put("/{rule_id}", response_model=RuleResponse)
async def update_rule(
    rule_id: str,
    body: RuleUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if settings.DEMO_MODE:
        existing = STUB_RULES[0]
        return RuleResponse(
            id=rule_id,
            conditions=body.conditions or existing.conditions,
            action=body.action or existing.action,
            is_active=body.is_active
            if body.is_active is not None
            else existing.is_active,
            created_at=existing.created_at,
        )

    from sqlalchemy import select

    from app.models.rule import Rule

    result = await db.execute(select(Rule).where(Rule.id == _uuid.UUID(rule_id)))
    rule = result.scalar_one_or_none()

    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")

    if rule.user_id != current_user.id:
        raise HTTPException(
            status_code=403, detail="Not authorized to update this rule"
        )

    if body.conditions is not None:
        rule.conditions = [c.model_dump() for c in body.conditions]
    if body.action is not None:
        rule.action = body.action
    if body.is_active is not None:
        rule.is_active = body.is_active

    await db.flush()

    return RuleResponse(
        id=str(rule.id),
        conditions=[RuleCondition(**c) for c in (rule.conditions or [])],
        action=rule.action,
        is_active=rule.is_active,
        created_at=rule.created_at,
    )


@router.delete("/{rule_id}", response_model=MessageResponse)
async def delete_rule(
    rule_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if settings.DEMO_MODE:
        return MessageResponse(message=f"Rule {rule_id} deleted")

    from sqlalchemy import select

    from app.models.rule import Rule

    result = await db.execute(select(Rule).where(Rule.id == _uuid.UUID(rule_id)))
    rule = result.scalar_one_or_none()

    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")

    if rule.user_id != current_user.id:
        raise HTTPException(
            status_code=403, detail="Not authorized to delete this rule"
        )

    await db.delete(rule)
    await db.flush()

    return MessageResponse(message=f"Rule {rule_id} deleted")
