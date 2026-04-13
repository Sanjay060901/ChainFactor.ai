"""Dashboard API endpoints. Aggregates data from DB."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

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


def _compute_monthly_volume(invoices) -> list:
    """Aggregate invoices into monthly buckets for the last 6 months."""
    from collections import defaultdict
    from datetime import datetime, timezone

    now = datetime.now(timezone.utc)
    buckets: dict[str, dict] = defaultdict(lambda: {"count": 0, "value": 0.0})

    for inv in invoices:
        ts = inv.created_at or now
        key = ts.strftime("%b")  # e.g. "Apr"
        buckets[key]["count"] += 1
        buckets[key]["value"] += (inv.extracted_data or {}).get("total_amount", 0.0)

    # Build ordered list for the last 6 months
    import calendar

    months = []
    for offset in range(5, -1, -1):
        month_num = ((now.month - 1 - offset) % 12) + 1
        label = calendar.month_abbr[month_num]
        b = buckets.get(label, {"count": 0, "value": 0.0})
        months.append(MonthlyVolume(month=label, count=b["count"], value=b["value"]))

    return months

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
        monthly_volume=_compute_monthly_volume(invoices),
    )


@router.post("/nl-query", response_model=NLQueryResponse)
async def nl_query(
    body: NLQueryRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Natural language query endpoint for portfolio analysis.

    Parses the user's query, runs a safe DB lookup, and returns a
    human-readable answer with supporting data.
    """
    from app.modules.dashboard.nl_engine import execute_nl_query

    result = await execute_nl_query(
        query=body.query,
        user_id=current_user.id,
        db=db,
    )
    return NLQueryResponse(
        answer=result["answer"],
        data=result.get("data"),
    )
