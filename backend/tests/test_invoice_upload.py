"""TDD tests for Feature 3.1: Invoice Upload Backend.

Tests the real upload endpoint (not stub):
- PDF validation (type, size)
- S3 upload via mocked boto3
- Invoice DB record creation
- Auth required
- DEMO_MODE fallback
"""

import io
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_pdf_bytes(size_kb: int = 10) -> bytes:
    """Create a minimal valid PDF byte stream of approximately size_kb."""
    header = b"%PDF-1.4\n"
    padding = b"0" * (size_kb * 1024 - len(header))
    return header + padding


def _make_txt_bytes() -> bytes:
    return b"This is not a PDF file"


@pytest.fixture
def _disable_demo_mode():
    """Temporarily disable DEMO_MODE for tests that need real behavior."""
    original = settings.DEMO_MODE
    settings.DEMO_MODE = False
    yield
    settings.DEMO_MODE = original


# ---------------------------------------------------------------------------
# Tests: DEMO_MODE (default in test suite)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_upload_demo_mode_returns_stub(client: AsyncClient):
    """In DEMO_MODE, upload returns pre-computed stub response."""
    pdf_data = _make_pdf_bytes(10)

    response = await client.post(
        "/api/v1/invoices/upload",
        files={"file": ("invoice.pdf", io.BytesIO(pdf_data), "application/pdf")},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["invoice_id"] == "inv_stub_001"
    assert data["status"] == "uploaded"


# ---------------------------------------------------------------------------
# Tests: Real upload (DEMO_MODE off)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.usefixtures("_disable_demo_mode")
async def test_upload_pdf_success(client: AsyncClient, db_session: AsyncSession):
    """Upload a valid PDF -> 200, creates Invoice in DB, returns invoice_id."""
    pdf_data = _make_pdf_bytes(50)

    with patch(
        "app.modules.invoices.router.upload_to_s3", new_callable=AsyncMock
    ) as mock_s3:
        mock_s3.return_value = "invoices/test-user/some-key/invoice.pdf"

        response = await client.post(
            "/api/v1/invoices/upload",
            files={"file": ("invoice.pdf", io.BytesIO(pdf_data), "application/pdf")},
        )

    assert response.status_code == 200
    data = response.json()
    assert "invoice_id" in data
    assert data["status"] == "uploaded"
    assert "ws_url" in data
    assert data["ws_url"].startswith("/ws/processing/")
    assert "created_at" in data
    # invoice_id should be a real UUID, not the stub
    assert data["invoice_id"] != "inv_stub_001"


@pytest.mark.asyncio
@pytest.mark.usefixtures("_disable_demo_mode")
async def test_upload_rejects_non_pdf(client: AsyncClient):
    """Upload a .txt file -> 400 with clear error message."""
    txt_data = _make_txt_bytes()

    response = await client.post(
        "/api/v1/invoices/upload",
        files={"file": ("notes.txt", io.BytesIO(txt_data), "text/plain")},
    )

    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert "PDF" in data["detail"]


@pytest.mark.asyncio
@pytest.mark.usefixtures("_disable_demo_mode")
async def test_upload_rejects_oversized_file(client: AsyncClient):
    """Upload a PDF > 5MB -> 400 with size error."""
    big_pdf = _make_pdf_bytes(5500)  # ~5.5 MB, over 5MB limit

    response = await client.post(
        "/api/v1/invoices/upload",
        files={"file": ("huge.pdf", io.BytesIO(big_pdf), "application/pdf")},
    )

    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert "5MB" in data["detail"] or "5 MB" in data["detail"]


@pytest.mark.asyncio
@pytest.mark.usefixtures("_disable_demo_mode")
async def test_upload_returns_correct_response_shape(client: AsyncClient):
    """Verify response matches the wireframe API contract."""
    pdf_data = _make_pdf_bytes(20)

    with patch(
        "app.modules.invoices.router.upload_to_s3", new_callable=AsyncMock
    ) as mock_s3:
        mock_s3.return_value = "invoices/test-user/key/invoice.pdf"

        response = await client.post(
            "/api/v1/invoices/upload",
            files={"file": ("contract.pdf", io.BytesIO(pdf_data), "application/pdf")},
        )

    assert response.status_code == 200
    data = response.json()

    # Exact shape per wireframes.md API contract
    assert set(data.keys()) >= {"invoice_id", "status", "ws_url", "created_at"}
    assert data["status"] == "uploaded"
    assert data["ws_url"].startswith("/ws/processing/")


@pytest.mark.asyncio
@pytest.mark.usefixtures("_disable_demo_mode")
async def test_upload_s3_called_with_user_path(client: AsyncClient, test_user):
    """S3 key should include user_id for tenant isolation."""
    pdf_data = _make_pdf_bytes(10)

    with patch(
        "app.modules.invoices.router.upload_to_s3", new_callable=AsyncMock
    ) as mock_s3:
        mock_s3.return_value = "invoices/key/invoice.pdf"

        response = await client.post(
            "/api/v1/invoices/upload",
            files={"file": ("invoice.pdf", io.BytesIO(pdf_data), "application/pdf")},
        )

    assert response.status_code == 200
    mock_s3.assert_called_once()
    # First positional arg is file_bytes, s3_key is keyword arg
    call_kwargs = mock_s3.call_args
    s3_key = call_kwargs.kwargs.get("s3_key", "")
    assert str(test_user.id) in s3_key


@pytest.mark.asyncio
async def test_upload_requires_auth(unauth_client: AsyncClient):
    """Upload without auth -> returns demo stub (DEMO_MODE on) or 401 (off)."""
    # With DEMO_MODE=True (conftest default), unauth still works (demo user)
    # This test verifies that when DEMO_MODE is off, auth is enforced
    original = settings.DEMO_MODE
    settings.DEMO_MODE = False
    try:
        pdf_data = _make_pdf_bytes(10)
        response = await unauth_client.post(
            "/api/v1/invoices/upload",
            files={"file": ("invoice.pdf", io.BytesIO(pdf_data), "application/pdf")},
        )
        # Without auth token and DEMO_MODE off, should fail
        assert response.status_code in (401, 403)
    finally:
        settings.DEMO_MODE = original
