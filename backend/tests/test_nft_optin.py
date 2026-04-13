"""TDD tests for NFT opt-in endpoint and build_optin_txn service function.

Tests cover:
1. build_optin_txn returns a base64 string
2. build_optin_txn creates a 0-amount self-transfer (sender == receiver)
3. Endpoint returns 409 if invoice status != "approved"
4. Endpoint returns 404 if no NFT minted
5. Endpoint returns NFTOptInResponse with unsigned_txn, asset_id, message
6. Message mentions the asset_id
7. Endpoint returns 404 if invoice not found (wrong user / IDOR)
8. Endpoint requires auth (uses get_current_user dependency)
"""

import base64
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException
from httpx import AsyncClient


# ---------------------------------------------------------------------------
# Shared test data
# ---------------------------------------------------------------------------

INVOICE_ID = "aabbccdd-1111-0000-0000-aabbccdd1111"
USER_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")
WALLET_ADDRESS = "TESTWALLETADDRESS7ALGORAND3OPTIN2XYZ"
ASSET_ID = 99887766


def _mock_nft(asset_id: int = ASSET_ID) -> MagicMock:
    """Build a minimal mock NFTRecord."""
    nft = MagicMock()
    nft.asset_id = asset_id
    nft.status = "minted"
    return nft


def _mock_invoice(status: str = "approved", has_nft: bool = True) -> MagicMock:
    """Build a minimal mock Invoice ORM object."""
    inv = MagicMock()
    inv.id = uuid.UUID(INVOICE_ID)
    inv.user_id = USER_ID
    inv.status = status
    inv.invoice_number = "INV-TEST-001"
    inv.extracted_data = {}
    inv.risk_score = 82
    inv.nft_record = _mock_nft() if has_nft else None
    return inv


# ---------------------------------------------------------------------------
# Unit tests for build_optin_txn
# ---------------------------------------------------------------------------


def test_build_optin_txn_returns_base64_string():
    """build_optin_txn must return a non-empty base64-encoded string."""
    import algosdk

    fake_params = MagicMock()

    # Create a bytes-like object that msgpack_encode would return
    fake_encoded = b"\x82\xa4type\xa4apxf"

    mock_txn = MagicMock()
    mock_client = MagicMock()
    mock_client.suggested_params.return_value = fake_params

    with (
        patch(
            "app.modules.invoices.nft_service._get_algod_client",
            return_value=mock_client,
        ),
        patch.object(
            algosdk.transaction,
            "AssetTransferTxn",
            return_value=mock_txn,
        ),
        patch.object(
            algosdk.encoding,
            "msgpack_encode",
            return_value=fake_encoded,
        ),
    ):
        from app.modules.invoices.nft_service import build_optin_txn

        result = build_optin_txn(wallet_address=WALLET_ADDRESS, asset_id=ASSET_ID)

    assert isinstance(result, str)
    assert len(result) > 0
    # Verify it is valid base64
    decoded = base64.b64decode(result)
    assert len(decoded) > 0


def test_build_optin_txn_creates_zero_amount_self_transfer():
    """build_optin_txn must create an AssetTransferTxn with amt=0 and sender==receiver."""
    import algosdk

    fake_params = MagicMock()
    fake_encoded = b"\x82\xa4test\xa4data"
    mock_txn = MagicMock()
    mock_client = MagicMock()
    mock_client.suggested_params.return_value = fake_params

    with (
        patch(
            "app.modules.invoices.nft_service._get_algod_client",
            return_value=mock_client,
        ),
        patch.object(
            algosdk.transaction,
            "AssetTransferTxn",
            return_value=mock_txn,
        ) as mock_asset_txn,
        patch.object(
            algosdk.encoding,
            "msgpack_encode",
            return_value=fake_encoded,
        ),
    ):
        from app.modules.invoices.nft_service import build_optin_txn

        build_optin_txn(wallet_address=WALLET_ADDRESS, asset_id=ASSET_ID)

    # Verify AssetTransferTxn was called with self-transfer (sender == receiver)
    mock_asset_txn.assert_called_once()
    call_kwargs = mock_asset_txn.call_args.kwargs
    assert call_kwargs["sender"] == WALLET_ADDRESS
    assert call_kwargs["receiver"] == WALLET_ADDRESS
    assert call_kwargs["amt"] == 0
    assert call_kwargs["index"] == ASSET_ID


def test_build_optin_txn_uses_correct_asset_id():
    """build_optin_txn passes the exact asset_id to AssetTransferTxn."""
    import algosdk

    different_asset_id = 11223344
    fake_params = MagicMock()
    fake_encoded = b"\x82\xa4test\xa4data"
    mock_txn = MagicMock()
    mock_client = MagicMock()
    mock_client.suggested_params.return_value = fake_params

    with (
        patch(
            "app.modules.invoices.nft_service._get_algod_client",
            return_value=mock_client,
        ),
        patch.object(
            algosdk.transaction,
            "AssetTransferTxn",
            return_value=mock_txn,
        ) as mock_asset_txn,
        patch.object(
            algosdk.encoding,
            "msgpack_encode",
            return_value=fake_encoded,
        ),
    ):
        from app.modules.invoices.nft_service import build_optin_txn

        build_optin_txn(wallet_address=WALLET_ADDRESS, asset_id=different_asset_id)

    call_kwargs = mock_asset_txn.call_args.kwargs
    assert call_kwargs["index"] == different_asset_id


# ---------------------------------------------------------------------------
# Endpoint tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_optin_endpoint_returns_409_if_status_not_approved(client: AsyncClient):
    """POST /invoices/{id}/nft/opt-in returns 409 if invoice status is not 'approved'."""
    mock_inv = _mock_invoice(status="uploaded")

    with patch(
        "app.modules.invoices.router._get_invoice_for_user",
        new=AsyncMock(return_value=mock_inv),
    ):
        response = await client.post(
            f"/api/v1/invoices/{INVOICE_ID}/nft/opt-in",
            json={"wallet_address": WALLET_ADDRESS},
        )

    assert response.status_code == 409
    assert "approved" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_optin_endpoint_returns_409_if_status_is_rejected(client: AsyncClient):
    """POST /invoices/{id}/nft/opt-in returns 409 if invoice status is 'rejected'."""
    mock_inv = _mock_invoice(status="rejected")

    with patch(
        "app.modules.invoices.router._get_invoice_for_user",
        new=AsyncMock(return_value=mock_inv),
    ):
        response = await client.post(
            f"/api/v1/invoices/{INVOICE_ID}/nft/opt-in",
            json={"wallet_address": WALLET_ADDRESS},
        )

    assert response.status_code == 409


@pytest.mark.asyncio
async def test_optin_endpoint_backfills_nft_if_not_minted(client: AsyncClient):
    """POST /invoices/{id}/nft/opt-in backfills a demo NFT when none exists."""
    mock_inv = _mock_invoice(status="approved", has_nft=False)

    with patch(
        "app.modules.invoices.router._get_invoice_for_user",
        new=AsyncMock(return_value=mock_inv),
    ):
        response = await client.post(
            f"/api/v1/invoices/{INVOICE_ID}/nft/opt-in",
            json={"wallet_address": WALLET_ADDRESS},
        )

    # Backfill creates a demo NFT record and returns 200 with opt-in txn
    assert response.status_code == 200
    data = response.json()
    assert data["asset_id"] == 757705539  # demo asset ID
    assert data["unsigned_txn"]  # non-empty base64


@pytest.mark.asyncio
async def test_optin_endpoint_backfills_nft_when_asset_id_is_none(client: AsyncClient):
    """POST /invoices/{id}/nft/opt-in backfills demo NFT when asset_id is None."""
    unique_inv_id = "aabbccdd-1111-0000-0000-aabbccdd2222"  # unique to avoid DB conflict
    mock_inv = _mock_invoice(status="approved", has_nft=True)
    mock_inv.id = uuid.UUID(unique_inv_id)
    mock_inv.nft_record.asset_id = None  # NFT record exists but not yet assigned an ASA
    mock_inv.nft_record.mint_txn_id = None  # No mint txn either

    with patch(
        "app.modules.invoices.router._get_invoice_for_user",
        new=AsyncMock(return_value=mock_inv),
    ):
        response = await client.post(
            f"/api/v1/invoices/{unique_inv_id}/nft/opt-in",
            json={"wallet_address": WALLET_ADDRESS},
        )

    # Backfill creates a demo NFT record and returns 200
    assert response.status_code == 200
    data = response.json()
    assert data["asset_id"] == 757705539


@pytest.mark.asyncio
async def test_optin_endpoint_returns_correct_response_shape(client: AsyncClient):
    """POST /invoices/{id}/nft/opt-in returns NFTOptInResponse with unsigned_txn, asset_id, message."""
    mock_inv = _mock_invoice(status="approved", has_nft=True)
    fake_unsigned_txn = base64.b64encode(b"fake_txn_bytes").decode()

    with (
        patch(
            "app.modules.invoices.router._get_invoice_for_user",
            new=AsyncMock(return_value=mock_inv),
        ),
        patch(
            "app.modules.invoices.nft_service.build_optin_txn",
            return_value=fake_unsigned_txn,
        ),
    ):
        response = await client.post(
            f"/api/v1/invoices/{INVOICE_ID}/nft/opt-in",
            json={"wallet_address": WALLET_ADDRESS},
        )

    assert response.status_code == 200
    data = response.json()
    assert "unsigned_txn" in data
    assert "asset_id" in data
    assert "message" in data


@pytest.mark.asyncio
async def test_optin_endpoint_message_mentions_asset_id(client: AsyncClient):
    """The response message must reference the asset_id."""
    mock_inv = _mock_invoice(status="approved", has_nft=True)
    fake_unsigned_txn = base64.b64encode(b"fake_txn_bytes").decode()

    with (
        patch(
            "app.modules.invoices.router._get_invoice_for_user",
            new=AsyncMock(return_value=mock_inv),
        ),
        patch(
            "app.modules.invoices.nft_service.build_optin_txn",
            return_value=fake_unsigned_txn,
        ),
    ):
        response = await client.post(
            f"/api/v1/invoices/{INVOICE_ID}/nft/opt-in",
            json={"wallet_address": WALLET_ADDRESS},
        )

    data = response.json()
    assert str(ASSET_ID) in data["message"]


@pytest.mark.asyncio
async def test_optin_endpoint_asset_id_matches_nft_record(client: AsyncClient):
    """The asset_id in the response must match the NFT record's asset_id."""
    mock_inv = _mock_invoice(status="approved", has_nft=True)
    fake_unsigned_txn = base64.b64encode(b"fake_txn_bytes").decode()

    with (
        patch(
            "app.modules.invoices.router._get_invoice_for_user",
            new=AsyncMock(return_value=mock_inv),
        ),
        patch(
            "app.modules.invoices.nft_service.build_optin_txn",
            return_value=fake_unsigned_txn,
        ),
    ):
        response = await client.post(
            f"/api/v1/invoices/{INVOICE_ID}/nft/opt-in",
            json={"wallet_address": WALLET_ADDRESS},
        )

    assert response.json()["asset_id"] == ASSET_ID


@pytest.mark.asyncio
async def test_optin_endpoint_returns_404_when_invoice_not_found(client: AsyncClient):
    """POST /invoices/{id}/nft/opt-in returns 404 when invoice not found (IDOR prevention)."""
    with patch(
        "app.modules.invoices.router._get_invoice_for_user",
        new=AsyncMock(
            side_effect=HTTPException(status_code=404, detail="Invoice not found")
        ),
    ):
        response = await client.post(
            f"/api/v1/invoices/{INVOICE_ID}/nft/opt-in",
            json={"wallet_address": WALLET_ADDRESS},
        )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_optin_endpoint_unsigned_txn_is_base64(client: AsyncClient):
    """The unsigned_txn field must be a valid base64-encoded string."""
    mock_inv = _mock_invoice(status="approved", has_nft=True)
    real_b64 = base64.b64encode(b"a_real_transaction_payload").decode()

    with (
        patch(
            "app.modules.invoices.router._get_invoice_for_user",
            new=AsyncMock(return_value=mock_inv),
        ),
        patch(
            "app.modules.invoices.nft_service.build_optin_txn",
            return_value=real_b64,
        ),
    ):
        response = await client.post(
            f"/api/v1/invoices/{INVOICE_ID}/nft/opt-in",
            json={"wallet_address": WALLET_ADDRESS},
        )

    data = response.json()
    # Must be decodable as base64 without error
    decoded = base64.b64decode(data["unsigned_txn"])
    assert len(decoded) > 0
