"""Dashboard API endpoints. DEMO_MODE returns stubs; real mode aggregates from DB."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.user import User
from app.modules.auth.dependencies import get_current_user
from app.schemas.dashboard import (
    DashboardSummaryResponse,
    MonthlyVolume,
    NLQueryRequest,
    NLQueryResponse,
    RiskDistribution,
)

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

_ACTIVE_STATUSES = {"approved", "minted"}
_PENDING_STATUSES = {
    "uploaded",
    "processing",
    "extracting",
    "validating",
    "analyzing",
    "underwriting",
    "minting",
}


@router.get("/summary", response_model=DashboardSummaryResponse)
async def dashboard_summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if settings.DEMO_MODE:
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

    # Real DB aggregation
    from sqlalchemy import select

    from app.models.invoice import Invoice

    # Fetch all invoices for the current user
    result = await db.execute(select(Invoice).where(Invoice.user_id == current_user.id))
    invoices = result.scalars().all()

    if not invoices:
        return DashboardSummaryResponse(
            total_value=0,
            active_invoices=0,
            pending_invoices=0,
            avg_risk_score=0.0,
            approval_rate=0.0,
            risk_distribution=RiskDistribution(low=0, medium=0, high=0),
            monthly_volume=[],
        )

    total = len(invoices)
    active = sum(1 for inv in invoices if inv.status in _ACTIVE_STATUSES)
    pending = sum(1 for inv in invoices if inv.status in _PENDING_STATUSES)

    # Total value from extracted_data.total_amount
    total_value = sum(
        (inv.extracted_data or {}).get("total_amount", 0.0) for inv in invoices
    )

    # Average risk score
    risk_scores = [inv.risk_score for inv in invoices if inv.risk_score is not None]
    avg_risk = sum(risk_scores) / len(risk_scores) if risk_scores else 0.0

    # Approval rate
    approval_rate = (active / total * 100) if total > 0 else 0.0

    # Risk distribution (based on risk_score: >=70 = low, 40-69 = medium, <40 = high)
    low_count = sum(1 for s in risk_scores if s >= 70)
    medium_count = sum(1 for s in risk_scores if 40 <= s < 70)
    high_count = sum(1 for s in risk_scores if s < 40)
    scored_total = len(risk_scores) if risk_scores else 1  # avoid division by zero

    return DashboardSummaryResponse(
        total_value=total_value,
        active_invoices=active,
        pending_invoices=pending,
        avg_risk_score=avg_risk,
        approval_rate=approval_rate,
        risk_distribution=RiskDistribution(
            low=round(low_count / scored_total * 100, 1),
            medium=round(medium_count / scored_total * 100, 1),
            high=round(high_count / scored_total * 100, 1),
        ),
        monthly_volume=[],
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
