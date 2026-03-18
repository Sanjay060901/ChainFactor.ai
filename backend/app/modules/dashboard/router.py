"""Dashboard API stub endpoints."""

from fastapi import APIRouter

from app.schemas.dashboard import (
    DashboardSummaryResponse,
    MonthlyVolume,
    NLQueryRequest,
    NLQueryResponse,
    RiskDistribution,
)

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary", response_model=DashboardSummaryResponse)
async def dashboard_summary():
    return DashboardSummaryResponse(
        total_value=4520000,
        active_invoices=12,
        pending_invoices=3,
        avg_risk_score=72.0,
        approval_rate=85.0,
        risk_distribution=RiskDistribution(low=60, medium=25, high=15),
        monthly_volume=[
            MonthlyVolume(month="Jan", count=8, value=2400000),
            MonthlyVolume(month="Feb", count=11, value=3100000),
            MonthlyVolume(month="Mar", count=15, value=4520000),
        ],
    )


@router.post("/nl-query", response_model=NLQueryResponse)
async def nl_query(body: NLQueryRequest):
    return NLQueryResponse(
        answer=f'You asked: "{body.query}". You have 3 high-risk invoices this week: INV-2026-002 (₹3.1L, risk 45), INV-2026-004 (₹2.1L, risk 12). Consider reviewing the flagged invoices before proceeding.',
        data=[
            {"invoice_id": "inv_stub_002", "risk_score": 45, "amount": 310000},
            {"invoice_id": "inv_stub_004", "risk_score": 12, "amount": 210000},
        ],
    )
