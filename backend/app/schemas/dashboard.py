"""Dashboard request/response schemas."""

from pydantic import BaseModel


class MonthlyVolume(BaseModel):
    month: str
    count: int
    value: float


class RiskDistribution(BaseModel):
    low: float
    medium: float
    high: float


class DashboardSummaryResponse(BaseModel):
    total_value: float
    active_invoices: int
    pending_invoices: int
    avg_risk_score: float
    approval_rate: float
    risk_distribution: RiskDistribution
    monthly_volume: list[MonthlyVolume]


class NLQueryRequest(BaseModel):
    query: str


class NLQueryResponse(BaseModel):
    answer: str
    data: list[dict] | None = None
