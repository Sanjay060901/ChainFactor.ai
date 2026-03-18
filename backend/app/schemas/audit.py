"""Audit trail response schemas."""

from pydantic import BaseModel


class AuditStep(BaseModel):
    step_number: int
    tool_name: str
    started_at: str
    duration_ms: int
    input_summary: str
    output_summary: str
    result: dict
    status: str


class AgentTrace(BaseModel):
    name: str
    model: str
    started_at: str
    duration_ms: int
    steps: list[AuditStep]


class Handoff(BaseModel):
    from_agent: str
    to_agent: str
    context_keys: list[str]


class AuditTrailResponse(BaseModel):
    invoice_id: str
    total_duration_ms: int
    agents: list[AgentTrace]
    handoffs: list[Handoff]
