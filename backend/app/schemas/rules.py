"""Seller rules request/response schemas."""

from datetime import datetime

from pydantic import BaseModel


class RuleCondition(BaseModel):
    field: str
    operator: str
    value: float | int | str


class RuleResponse(BaseModel):
    id: str
    conditions: list[RuleCondition]
    action: str
    is_active: bool
    created_at: datetime


class RuleCreateRequest(BaseModel):
    conditions: list[RuleCondition]
    action: str


class RuleUpdateRequest(BaseModel):
    conditions: list[RuleCondition] | None = None
    action: str | None = None
    is_active: bool | None = None


class RulesListResponse(BaseModel):
    rules: list[RuleResponse]
    default_action: str


class DefaultActionRequest(BaseModel):
    default_action: str


class DefaultActionResponse(BaseModel):
    default_action: str
