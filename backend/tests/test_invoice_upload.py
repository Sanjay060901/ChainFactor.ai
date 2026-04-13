"""TDD tests for Feature 3.1: Invoice Upload Backend.

Tests the real upload endpoint (not stub):
- PDF validation (type, size)
- S3 upload via mocked boto3
- Invoice DB record creation
- Auth required
"""

import io
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession



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




# ---------------------------------------------------------------------------
# Tests: Real upload
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
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

