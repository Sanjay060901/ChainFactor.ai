"""Tests for Feature 3.3: Invoice List Backend -- real DB queries.

Tests cover:
- pagination, filtering, sorting, search, IDOR prevention
"""

import uuid

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
    invoice_number: str = "INV-TEST-001",
    status: str = "approved",
    risk_score: int | None = 82,
    extracted_data: dict | None = None,
) -> Invoice:
    """Insert an invoice row for a given user."""
    inv = Invoice(
        id=uuid.uuid4(),
        user_id=user.id,
        invoice_number=invoice_number,
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
# Tests: real DB queries
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# DB query tests (real DB queries)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_invoices_real_empty(
    client: AsyncClient, db_session: AsyncSession, test_user: User
):
    """Non-DEMO with no invoices returns empty list."""
    response = await client.get("/api/v1/invoices")

    assert response.status_code == 200
    data = response.json()
    assert data["invoices"] == []
    assert data["total"] == 0
    assert data["pages"] == 0


@pytest.mark.asyncio
async def test_list_invoices_real_returns_user_invoices(
    client: AsyncClient, db_session: AsyncSession, test_user: User
):
    """Non-DEMO returns invoices belonging to the authenticated user."""
    await _create_invoice(
        db_session, test_user, invoice_number="INV-001", status="approved"
    )
    await _create_invoice(
        db_session, test_user, invoice_number="INV-002", status="flagged"
    )

    response = await client.get("/api/v1/invoices")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert len(data["invoices"]) == 2


@pytest.mark.asyncio
async def test_list_invoices_idor_prevention(
    client: AsyncClient, db_session: AsyncSession, test_user: User
):
    """User cannot see invoices belonging to another user."""
    # Create another user
    other_user = User(
        id=uuid.UUID("99999999-9999-9999-9999-999999999999"),
        cognito_sub="other-sub-999",
        name="Other User",
        email="other@test.com",
        phone="+910000000000",
        company_name="Other Corp",
        gstin="29AABCO1234R1ZX",
    )
    db_session.add(other_user)
    await db_session.flush()

    await _create_invoice(db_session, other_user, invoice_number="INV-OTHER")
    await _create_invoice(db_session, test_user, invoice_number="INV-MINE")

    response = await client.get("/api/v1/invoices")

    data = response.json()
    assert data["total"] == 1
    assert data["invoices"][0]["invoice_number"] == "INV-MINE"


@pytest.mark.asyncio
async def test_list_invoices_pagination(
    client: AsyncClient, db_session: AsyncSession, test_user: User
):
    """Pagination returns correct page and total pages."""
    for i in range(5):
        await _create_invoice(db_session, test_user, invoice_number=f"INV-PAG-{i:03d}")

    response = await client.get("/api/v1/invoices?page=1&limit=2")

    data = response.json()
    assert data["total"] == 5
    assert len(data["invoices"]) == 2
    assert data["pages"] == 3  # ceil(5/2)
    assert data["page"] == 1
    assert data["limit"] == 2


@pytest.mark.asyncio
async def test_list_invoices_filter_by_status(
    client: AsyncClient, db_session: AsyncSession, test_user: User
):
    """Filter by status returns only matching invoices."""
    await _create_invoice(
        db_session, test_user, invoice_number="INV-A", status="approved"
    )
    await _create_invoice(
        db_session, test_user, invoice_number="INV-F", status="flagged"
    )
    await _create_invoice(
        db_session, test_user, invoice_number="INV-R", status="rejected"
    )

    response = await client.get("/api/v1/invoices?status=flagged")

    data = response.json()
    assert data["total"] == 1
    assert data["invoices"][0]["status"] == "flagged"


@pytest.mark.asyncio
async def test_list_invoices_filter_by_risk_level(
    client: AsyncClient, db_session: AsyncSession, test_user: User
):
    """Filter by risk_level maps to score ranges: low>=70, medium 40-69, high<40."""
    await _create_invoice(db_session, test_user, invoice_number="INV-L", risk_score=85)
    await _create_invoice(db_session, test_user, invoice_number="INV-M", risk_score=55)
    await _create_invoice(db_session, test_user, invoice_number="INV-H", risk_score=20)

    response = await client.get("/api/v1/invoices?risk_level=low")

    data = response.json()
    assert data["total"] == 1
    assert data["invoices"][0]["invoice_number"] == "INV-L"


@pytest.mark.asyncio
async def test_list_invoices_search(
    client: AsyncClient, db_session: AsyncSession, test_user: User
):
    """Search matches on invoice_number (case-insensitive)."""
    await _create_invoice(db_session, test_user, invoice_number="INV-SEARCH-ABC")
    await _create_invoice(db_session, test_user, invoice_number="INV-OTHER-XYZ")

    response = await client.get("/api/v1/invoices?search=search")

    data = response.json()
    assert data["total"] == 1
    assert "SEARCH" in data["invoices"][0]["invoice_number"]


@pytest.mark.asyncio
async def test_list_invoices_sort_ascending(
    client: AsyncClient, db_session: AsyncSession, test_user: User
):
    """Sort by risk_score ascending returns lowest first."""
    await _create_invoice(
        db_session, test_user, invoice_number="INV-HIGH", risk_score=90
    )
    await _create_invoice(
        db_session, test_user, invoice_number="INV-LOW", risk_score=10
    )

    response = await client.get("/api/v1/invoices?sort=risk_score")

    data = response.json()
    assert len(data["invoices"]) == 2
    assert data["invoices"][0]["risk_score"] <= data["invoices"][1]["risk_score"]
