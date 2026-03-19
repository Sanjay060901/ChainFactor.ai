"""TDD tests for POST /{invoice_id}/process endpoint.

Tests cover:
1. Returns 202 with ProcessInvoiceResponse shape (invoice_id, status, ws_url)
2. Returns 409 if invoice status is not "uploaded" (e.g., "processing")
3. Returns 404 if invoice not found (wrong user / missing)
4. ws_url contains the invoice_id
5. status is "processing" in response
6. asyncio.create_task is called to launch background pipeline
7. IDOR prevention: helper rejects invoice owned by another user
"""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException
from httpx import AsyncClient


# ---------------------------------------------------------------------------
# Shared test data
# ---------------------------------------------------------------------------

INVOICE_ID = "aabbccdd-0000-0000-0000-aabbccdd0000"
USER_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")


def _mock_invoice(status: str = "uploaded") -> MagicMock:
    """Build a minimal mock Invoice ORM object."""
    inv = MagicMock()
    inv.id = uuid.UUID(INVOICE_ID)
    inv.user_id = USER_ID
    inv.status = status
    inv.file_key = f"invoices/{USER_ID}/{INVOICE_ID}/invoice.pdf"
    return inv


# ---------------------------------------------------------------------------
# Fixture: client with mocked auth (uses conftest client fixture)
# ---------------------------------------------------------------------------
# The conftest `client` fixture already overrides get_current_user to return
# test_user and get_db to return db_session.  We rely on that for most tests.
#
# For tests that need to control the invoice lookup directly, we patch
# _get_invoice_for_user at the router level.
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Test 1: Happy path -- 202 with correct shape
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_process_returns_202_with_correct_shape(client: AsyncClient):
    """POST /invoices/{id}/process returns 202 and ProcessInvoiceResponse shape."""
    mock_inv = _mock_invoice("uploaded")

    with (
        patch(
            "app.modules.invoices.router._get_invoice_for_user",
            new=AsyncMock(return_value=mock_inv),
        ),
        patch("app.modules.agents.pipeline.run_invoice_pipeline", new=AsyncMock()),
        patch("asyncio.create_task") as mock_task,
    ):
        response = await client.post(f"/api/v1/invoices/{INVOICE_ID}/process")

    assert response.status_code == 202
    data = response.json()
    assert "invoice_id" in data
    assert "status" in data
    assert "ws_url" in data
    assert mock_task.called


# ---------------------------------------------------------------------------
# Test 2: status field is "processing"
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_process_response_status_is_processing(client: AsyncClient):
    """Response body status must be 'processing'."""
    mock_inv = _mock_invoice("uploaded")

    with (
        patch(
            "app.modules.invoices.router._get_invoice_for_user",
            new=AsyncMock(return_value=mock_inv),
        ),
        patch("app.modules.agents.pipeline.run_invoice_pipeline", new=AsyncMock()),
        patch("asyncio.create_task"),
    ):
        response = await client.post(f"/api/v1/invoices/{INVOICE_ID}/process")

    assert response.status_code == 202
    assert response.json()["status"] == "processing"


# ---------------------------------------------------------------------------
# Test 3: ws_url contains the invoice_id
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_process_ws_url_contains_invoice_id(client: AsyncClient):
    """ws_url in the response must include the invoice_id."""
    mock_inv = _mock_invoice("uploaded")

    with (
        patch(
            "app.modules.invoices.router._get_invoice_for_user",
            new=AsyncMock(return_value=mock_inv),
        ),
        patch("app.modules.agents.pipeline.run_invoice_pipeline", new=AsyncMock()),
        patch("asyncio.create_task"),
    ):
        response = await client.post(f"/api/v1/invoices/{INVOICE_ID}/process")

    data = response.json()
    assert INVOICE_ID in data["ws_url"]


# ---------------------------------------------------------------------------
# Test 4: invoice_id in response matches path parameter
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_process_response_invoice_id_matches_path(client: AsyncClient):
    """invoice_id in response must match the path parameter."""
    mock_inv = _mock_invoice("uploaded")

    with (
        patch(
            "app.modules.invoices.router._get_invoice_for_user",
            new=AsyncMock(return_value=mock_inv),
        ),
        patch("app.modules.agents.pipeline.run_invoice_pipeline", new=AsyncMock()),
        patch("asyncio.create_task"),
    ):
        response = await client.post(f"/api/v1/invoices/{INVOICE_ID}/process")

    assert response.json()["invoice_id"] == INVOICE_ID


# ---------------------------------------------------------------------------
# Test 5: Returns 409 if invoice is already processing
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_process_returns_409_when_status_is_processing(client: AsyncClient):
    """POST /process returns 409 if invoice status is 'processing'."""
    mock_inv = _mock_invoice("processing")

    with patch(
        "app.modules.invoices.router._get_invoice_for_user",
        new=AsyncMock(return_value=mock_inv),
    ):
        response = await client.post(f"/api/v1/invoices/{INVOICE_ID}/process")

    assert response.status_code == 409
    assert "processing" in response.json()["detail"].lower()


# ---------------------------------------------------------------------------
# Test 6: Returns 409 if invoice is approved (any non-uploaded status)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_process_returns_409_when_status_is_approved(client: AsyncClient):
    """POST /process returns 409 for any status that is not 'uploaded'."""
    mock_inv = _mock_invoice("approved")

    with patch(
        "app.modules.invoices.router._get_invoice_for_user",
        new=AsyncMock(return_value=mock_inv),
    ):
        response = await client.post(f"/api/v1/invoices/{INVOICE_ID}/process")

    assert response.status_code == 409


# ---------------------------------------------------------------------------
# Test 7: Returns 404 if invoice not found / wrong user
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_process_returns_404_when_invoice_not_found(client: AsyncClient):
    """POST /process returns 404 when invoice doesn't exist or belongs to another user."""
    with patch(
        "app.modules.invoices.router._get_invoice_for_user",
        new=AsyncMock(
            side_effect=HTTPException(status_code=404, detail="Invoice not found")
        ),
    ):
        response = await client.post(f"/api/v1/invoices/{INVOICE_ID}/process")

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


# ---------------------------------------------------------------------------
# Test 8: asyncio.create_task is called (pipeline launched)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_process_creates_background_task(client: AsyncClient):
    """asyncio.create_task must be called once to launch the pipeline."""
    mock_inv = _mock_invoice("uploaded")

    with (
        patch(
            "app.modules.invoices.router._get_invoice_for_user",
            new=AsyncMock(return_value=mock_inv),
        ),
        patch("app.modules.agents.pipeline.run_invoice_pipeline", new=AsyncMock()),
        patch("asyncio.create_task") as mock_task,
    ):
        await client.post(f"/api/v1/invoices/{INVOICE_ID}/process")

    mock_task.assert_called_once()


# ---------------------------------------------------------------------------
# Test 9: IDOR unit test for _get_invoice_for_user helper
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_invoice_for_user_raises_404_for_wrong_user():
    """_get_invoice_for_user raises 404 when invoice belongs to a different user."""
    from app.modules.invoices.router import _get_invoice_for_user

    wrong_user_id = uuid.UUID("99999999-9999-9999-9999-999999999999")

    # Mock DB that returns None (no match for this user_id)
    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db.execute = AsyncMock(return_value=mock_result)

    with pytest.raises(HTTPException) as exc_info:
        await _get_invoice_for_user(mock_db, INVOICE_ID, wrong_user_id)

    assert exc_info.value.status_code == 404


# ---------------------------------------------------------------------------
# Test 10: _get_invoice_for_user returns invoice for correct user
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_invoice_for_user_returns_invoice_for_correct_user():
    """_get_invoice_for_user returns the invoice when user_id matches."""
    from app.modules.invoices.router import _get_invoice_for_user

    expected_invoice = _mock_invoice("uploaded")

    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = expected_invoice
    mock_db.execute = AsyncMock(return_value=mock_result)

    invoice = await _get_invoice_for_user(mock_db, INVOICE_ID, USER_ID)

    assert invoice is expected_invoice
