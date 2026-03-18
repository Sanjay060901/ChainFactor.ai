"""Seller rules API stub endpoints."""

from datetime import datetime, timezone

from fastapi import APIRouter

from app.schemas.rules import (
    DefaultActionRequest,
    DefaultActionResponse,
    RuleCondition,
    RuleCreateRequest,
    RuleResponse,
    RuleUpdateRequest,
    RulesListResponse,
)
from app.schemas.common import MessageResponse

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
async def list_rules():
    return RulesListResponse(rules=STUB_RULES, default_action="flag_for_review")


@router.post("", response_model=RuleResponse)
async def create_rule(body: RuleCreateRequest):
    return RuleResponse(
        id="rule_stub_new",
        conditions=body.conditions,
        action=body.action,
        is_active=True,
        created_at=STUB_NOW,
    )


@router.put("/default-action", response_model=DefaultActionResponse)
async def set_default_action(body: DefaultActionRequest):
    return DefaultActionResponse(default_action=body.default_action)


@router.put("/{rule_id}", response_model=RuleResponse)
async def update_rule(rule_id: str, body: RuleUpdateRequest):
    existing = STUB_RULES[0]
    return RuleResponse(
        id=rule_id,
        conditions=body.conditions or existing.conditions,
        action=body.action or existing.action,
        is_active=body.is_active if body.is_active is not None else existing.is_active,
        created_at=existing.created_at,
    )


@router.delete("/{rule_id}", response_model=MessageResponse)
async def delete_rule(rule_id: str):
    return MessageResponse(message=f"Rule {rule_id} deleted")
