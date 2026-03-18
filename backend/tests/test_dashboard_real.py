"""Tests for Feature 5.1: Dashboard Summary Backend -- real DB aggregations.

Tests cover:
- DEMO_MODE returns stub data (existing behavior preserved)
- Non-DEMO: aggregation queries on Invoice table
"""

import uuid
from unittest.mock import patch

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.invoice import Invoice
from app.models.user import User


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _create_invoice(
    db: AsyncSession,
    user: User,
    *,
    status: str = "approved",
    risk_score: int | None = 82,
    extracted_data: dict | None = None,
) -> Invoice:
    """Insert an invoice row for a given user."""
    inv = Invoice(
        id=uuid.uuid4(),
        user_id=user.id,
        invoice_number=f"INV-DASH-{uuid.uuid4().hex[:6]}",
        status=status,
        file_key=f"invoices/{user.id}/test.pdf",
        file_name="test.pdf",
        risk_score=risk_score,
        extracted_data=extracted_data
        or {
            "seller": {"name": "Test Seller", "gstin": "27AABCU9603R1ZM"},
            "total_amount": 500000.0,
        },
    )
    db.add(inv)
    await db.flush()
    return inv


# ---------------------------------------------------------------------------
# DEMO_MODE tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_dashboard_summary_demo_mode(client: AsyncClient):
    """In DEMO_MODE, dashboard returns pre-built stub data."""
    response = await client.get("/api/v1/dashboard/summary")

    assert response.status_code == 200
    data = response.json()
    assert data["total_value"] == 4520000
    assert data["active_invoices"] == 12


# ---------------------------------------------------------------------------
# Non-DEMO mode tests (real DB aggregation)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_dashboard_summary_real_empty(
    client: AsyncClient, db_session: AsyncSession, test_user: User
):
    """Non-DEMO with no invoices returns zeroed stats."""
    with patch("app.modules.dashboard.router.settings") as mock_settings:
        mock_settings.DEMO_MODE = False
        response = await client.get("/api/v1/dashboard/summary")

    assert response.status_code == 200
    data = response.json()
    assert data["total_value"] == 0
    assert data["active_invoices"] == 0
    assert data["pending_invoices"] == 0
    assert data["avg_risk_score"] == 0.0
    assert data["approval_rate"] == 0.0


@pytest.mark.asyncio
async def test_dashboard_summary_real_counts(
    client: AsyncClient, db_session: AsyncSession, test_user: User
):
    """Non-DEMO aggregates counts from Invoice table."""
    await _create_invoice(db_session, test_user, status="approved", risk_score=80)
    await _create_invoice(db_session, test_user, status="approved", risk_score=60)
    await _create_invoice(db_session, test_user, status="processing", risk_score=50)
    await _create_invoice(db_session, test_user, status="rejected", risk_score=20)

    with patch("app.modules.dashboard.router.settings") as mock_settings:
        mock_settings.DEMO_MODE = False
        response = await client.get("/api/v1/dashboard/summary")

    data = response.json()
    # active = approved + minted
    assert data["active_invoices"] == 2
    # pending = uploaded + processing + extracting + validating + analyzing + underwriting + minting
    assert data["pending_invoices"] == 1
    # avg risk across all 4 invoices: (80+60+50+20)/4 = 52.5
    assert data["avg_risk_score"] == pytest.approx(52.5, rel=0.1)
    # approval_rate = approved / total * 100 = 2/4 * 100 = 50.0
    assert data["approval_rate"] == pytest.approx(50.0, rel=0.1)


@pytest.mark.asyncio
async def test_dashboard_summary_real_idor(
    client: AsyncClient, db_session: AsyncSession, test_user: User
):
    """Dashboard only counts invoices belonging to the current user."""
    other_user = User(
        id=uuid.UUID("88888888-8888-8888-8888-888888888888"),
        cognito_sub="other-dash-sub",
        name="Other",
        email="other-dash@test.com",
        phone="+910000000001",
        company_name="Other Corp",
        gstin="29AABCO1234R1ZX",
    )
    db_session.add(other_user)
    await db_session.flush()

    await _create_invoice(db_session, test_user, status="approved", risk_score=80)
    await _create_invoice(db_session, other_user, status="approved", risk_score=90)

    with patch("app.modules.dashboard.router.settings") as mock_settings:
        mock_settings.DEMO_MODE = False
        response = await client.get("/api/v1/dashboard/summary")

    data = response.json()
    assert data["active_invoices"] == 1  # Only test_user's invoice


@pytest.mark.asyncio
async def test_dashboard_summary_real_risk_distribution(
    client: AsyncClient, db_session: AsyncSession, test_user: User
):
    """Risk distribution percentages are computed correctly."""
    await _create_invoice(db_session, test_user, risk_score=85)  # low
    await _create_invoice(db_session, test_user, risk_score=75)  # low
    await _create_invoice(db_session, test_user, risk_score=50)  # medium
    await _create_invoice(db_session, test_user, risk_score=15)  # high

    with patch("app.modules.dashboard.router.settings") as mock_settings:
        mock_settings.DEMO_MODE = False
        response = await client.get("/api/v1/dashboard/summary")

    data = response.json()
    dist = data["risk_distribution"]
    assert dist["low"] == pytest.approx(50.0, rel=0.1)  # 2/4
    assert dist["medium"] == pytest.approx(25.0, rel=0.1)  # 1/4
    assert dist["high"] == pytest.approx(25.0, rel=0.1)  # 1/4
