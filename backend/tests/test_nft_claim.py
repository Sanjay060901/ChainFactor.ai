"""TDD tests for NFT claim endpoint and nft_service functions.

Tests cover:
1. transfer_nft returns dict with txn_id and asset_id
2. transfer_nft uses amount=1 (NFT = single indivisible unit)
3. transfer_nft uses app wallet mnemonic for signing
4. submit_signed_txn decodes base64 and submits raw bytes
5. submit_signed_txn returns transaction ID string
6. Endpoint returns 409 if NFT status is not "minted"
7. Endpoint returns NFTClaimResponse with correct fields on success
8. Endpoint updates nft_record status to "claimed"
9. Endpoint returns 404 if invoice not found (IDOR prevention)
10. Endpoint returns 409 if invoice has no nft_record
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

INVOICE_ID = "ccddee11-2222-0000-0000-ccddee112222"
USER_ID = uuid.UUID("33333333-3333-3333-3333-333333333333")
WALLET_ADDRESS = "TESTWALLETCLAIM7ALGORAND3RECV2XYZ99"
ASSET_ID = 55443322
OPTIN_TXN_ID = "OPTIN_TXN_ID_ABCDEF1234567890"
TRANSFER_TXN_ID = "TRANSFER_TXN_ID_XYZ0987654321"
SIGNED_OPTIN_B64 = base64.b64encode(b"fake_signed_optin_txn_bytes").decode()


def _mock_nft(asset_id: int = ASSET_ID, status: str = "minted") -> MagicMock:
    """Build a minimal mock NFTRecord."""
    nft = MagicMock()
    nft.asset_id = asset_id
    nft.status = status
    nft.mint_txn_id = "REAL_MINT_TXN_ABC123"  # Non-DEMO prefix to test real path
    nft.opt_in_txn_id = None
    nft.transfer_txn_id = None
    nft.claimed_by_wallet = None
    return nft


def _mock_invoice(
    status: str = "approved",
    has_nft: bool = True,
    nft_status: str = "minted",
) -> MagicMock:
    """Build a minimal mock Invoice ORM object."""
    inv = MagicMock()
    inv.id = uuid.UUID(INVOICE_ID)
    inv.user_id = USER_ID
    inv.status = status
    inv.nft_record = _mock_nft(status=nft_status) if has_nft else None
    return inv


# ---------------------------------------------------------------------------
# Unit tests: transfer_nft
# ---------------------------------------------------------------------------


def test_transfer_nft_returns_dict_with_txn_id_and_asset_id():
    """transfer_nft must return a dict containing txn_id and asset_id."""
    import algosdk

    mock_client = MagicMock()
    mock_client.suggested_params.return_value = MagicMock()
    mock_client.send_transaction.return_value = TRANSFER_TXN_ID
    mock_client.wait_for_confirmation = MagicMock()

    mock_txn = MagicMock()
    mock_txn.sign.return_value = MagicMock()
    mock_private_key = "fake_private_key"
    mock_sender = "APPSENDERWALLET"

    with (
        patch(
            "app.modules.invoices.nft_service._get_algod_client",
            return_value=mock_client,
        ),
        patch.object(algosdk.mnemonic, "to_private_key", return_value=mock_private_key),
        patch.object(
            algosdk.account, "address_from_private_key", return_value=mock_sender
        ),
        patch.object(algosdk.transaction, "AssetTransferTxn", return_value=mock_txn),
        patch.object(
            algosdk.transaction,
            "wait_for_confirmation",
            return_value={"confirmed-round": 42},
        ),
    ):
        from app.modules.invoices.nft_service import transfer_nft

        result = transfer_nft(asset_id=ASSET_ID, receiver_address=WALLET_ADDRESS)

    assert isinstance(result, dict)
    assert "txn_id" in result
    assert "asset_id" in result
    assert result["txn_id"] == TRANSFER_TXN_ID
    assert result["asset_id"] == ASSET_ID


def test_transfer_nft_uses_amount_of_1():
    """transfer_nft must send exactly 1 unit (NFT is an indivisible single unit)."""
    import algosdk

    mock_client = MagicMock()
    mock_client.suggested_params.return_value = MagicMock()
    mock_client.send_transaction.return_value = TRANSFER_TXN_ID

    mock_txn = MagicMock()
    mock_txn.sign.return_value = MagicMock()

    with (
        patch(
            "app.modules.invoices.nft_service._get_algod_client",
            return_value=mock_client,
        ),
        patch.object(algosdk.mnemonic, "to_private_key", return_value="fake_key"),
        patch.object(
            algosdk.account, "address_from_private_key", return_value="APP_WALLET"
        ),
        patch.object(
            algosdk.transaction, "AssetTransferTxn", return_value=mock_txn
        ) as mock_asset_txn,
        patch.object(
            algosdk.transaction,
            "wait_for_confirmation",
            return_value={"confirmed-round": 10},
        ),
    ):
        from app.modules.invoices.nft_service import transfer_nft

        transfer_nft(asset_id=ASSET_ID, receiver_address=WALLET_ADDRESS)

    call_kwargs = mock_asset_txn.call_args.kwargs
    assert call_kwargs["amt"] == 1


def test_transfer_nft_uses_app_wallet_mnemonic():
    """transfer_nft must derive the signing key from settings.ALGORAND_APP_WALLET_MNEMONIC."""
    import algosdk

    mock_client = MagicMock()
    mock_client.suggested_params.return_value = MagicMock()
    mock_client.send_transaction.return_value = TRANSFER_TXN_ID

    mock_txn = MagicMock()
    mock_txn.sign.return_value = MagicMock()

    with (
        patch(
            "app.modules.invoices.nft_service._get_algod_client",
            return_value=mock_client,
        ),
        patch.object(
            algosdk.mnemonic, "to_private_key", return_value="fake_key"
        ) as mock_to_private_key,
        patch.object(
            algosdk.account, "address_from_private_key", return_value="APP_WALLET"
        ),
        patch.object(algosdk.transaction, "AssetTransferTxn", return_value=mock_txn),
        patch.object(
            algosdk.transaction,
            "wait_for_confirmation",
            return_value={"confirmed-round": 5},
        ),
    ):
        from app.config import settings
        from app.modules.invoices.nft_service import transfer_nft

        transfer_nft(asset_id=ASSET_ID, receiver_address=WALLET_ADDRESS)

    # Must have called to_private_key with the app wallet mnemonic
    mock_to_private_key.assert_called_once_with(settings.ALGORAND_APP_WALLET_MNEMONIC)


# ---------------------------------------------------------------------------
# Unit tests: submit_signed_txn
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_submit_signed_txn_decodes_base64_and_submits_raw_bytes():
    """submit_signed_txn must base64-decode the input and pass raw bytes to send_raw_transaction."""
    import algosdk

    raw_bytes = b"fake_signed_txn_raw_bytes"
    b64_input = base64.b64encode(raw_bytes).decode()

    mock_client = MagicMock()
    mock_client.send_raw_transaction.return_value = OPTIN_TXN_ID

    with (
        patch(
            "app.modules.invoices.nft_service._get_algod_client",
            return_value=mock_client,
        ),
        patch.object(
            algosdk.transaction,
            "wait_for_confirmation",
            return_value={"confirmed-round": 7},
        ),
    ):
        from app.modules.invoices.nft_service import submit_signed_txn

        result = await submit_signed_txn(b64_input)

    mock_client.send_raw_transaction.assert_called_once_with(raw_bytes)
    assert result == OPTIN_TXN_ID


@pytest.mark.asyncio
async def test_submit_signed_txn_returns_transaction_id_string():
    """submit_signed_txn must return the transaction ID as a string."""
    import algosdk

    b64_input = base64.b64encode(b"some_txn_bytes").decode()
    expected_txid = "EXPECTED_TXID_12345ABCDE"

    mock_client = MagicMock()
    mock_client.send_raw_transaction.return_value = expected_txid

    with (
        patch(
            "app.modules.invoices.nft_service._get_algod_client",
            return_value=mock_client,
        ),
        patch.object(
            algosdk.transaction,
            "wait_for_confirmation",
            return_value={"confirmed-round": 99},
        ),
    ):
        from app.modules.invoices.nft_service import submit_signed_txn

        result = await submit_signed_txn(b64_input)

    assert isinstance(result, str)
    assert result == expected_txid


# ---------------------------------------------------------------------------
# Endpoint integration tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_claim_endpoint_returns_409_if_nft_not_minted(client: AsyncClient):
    """POST /{invoice_id}/nft/claim returns 409 if NFT status is not 'minted'."""
    mock_inv = _mock_invoice(nft_status="opt_in_pending")

    with patch(
        "app.modules.invoices.router._get_invoice_for_user",
        new=AsyncMock(return_value=mock_inv),
    ):
        response = await client.post(
            f"/api/v1/invoices/{INVOICE_ID}/nft/claim",
            json={
                "wallet_address": WALLET_ADDRESS,
                "signed_optin_txn": SIGNED_OPTIN_B64,
            },
        )

    assert response.status_code == 409
    assert "not available" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_claim_endpoint_returns_409_if_no_nft_record(client: AsyncClient):
    """POST /{invoice_id}/nft/claim returns 409 if invoice has no nft_record."""
    mock_inv = _mock_invoice(has_nft=False)

    with patch(
        "app.modules.invoices.router._get_invoice_for_user",
        new=AsyncMock(return_value=mock_inv),
    ):
        response = await client.post(
            f"/api/v1/invoices/{INVOICE_ID}/nft/claim",
            json={
                "wallet_address": WALLET_ADDRESS,
                "signed_optin_txn": SIGNED_OPTIN_B64,
            },
        )

    assert response.status_code == 409


@pytest.mark.asyncio
async def test_claim_endpoint_returns_correct_response_shape(client: AsyncClient):
    """POST /{invoice_id}/nft/claim returns NFTClaimResponse with all required fields."""
    mock_inv = _mock_invoice()

    with (
        patch(
            "app.modules.invoices.router._get_invoice_for_user",
            new=AsyncMock(return_value=mock_inv),
        ),
        patch(
            "app.modules.invoices.nft_service.submit_signed_txn",
            new=AsyncMock(return_value=OPTIN_TXN_ID),
        ),
        patch(
            "app.modules.invoices.nft_service.transfer_nft",
            return_value={
                "txn_id": TRANSFER_TXN_ID,
                "asset_id": ASSET_ID,
                "confirmed_round": 42,
            },
        ),
    ):
        response = await client.post(
            f"/api/v1/invoices/{INVOICE_ID}/nft/claim",
            json={
                "wallet_address": WALLET_ADDRESS,
                "signed_optin_txn": SIGNED_OPTIN_B64,
            },
        )

    assert response.status_code == 200
    data = response.json()
    assert "asset_id" in data
    assert "optin_txn_id" in data
    assert "transfer_txn_id" in data
    assert "status" in data
    assert "explorer_url" in data


@pytest.mark.asyncio
async def test_claim_endpoint_response_values_are_correct(client: AsyncClient):
    """The claim response must contain the correct txn IDs, asset_id, and status."""
    mock_inv = _mock_invoice()

    with (
        patch(
            "app.modules.invoices.router._get_invoice_for_user",
            new=AsyncMock(return_value=mock_inv),
        ),
        patch(
            "app.modules.invoices.nft_service.submit_signed_txn",
            new=AsyncMock(return_value=OPTIN_TXN_ID),
        ),
        patch(
            "app.modules.invoices.nft_service.transfer_nft",
            return_value={
                "txn_id": TRANSFER_TXN_ID,
                "asset_id": ASSET_ID,
                "confirmed_round": 42,
            },
        ),
    ):
        response = await client.post(
            f"/api/v1/invoices/{INVOICE_ID}/nft/claim",
            json={
                "wallet_address": WALLET_ADDRESS,
                "signed_optin_txn": SIGNED_OPTIN_B64,
            },
        )

    data = response.json()
    assert data["asset_id"] == ASSET_ID
    assert data["optin_txn_id"] == OPTIN_TXN_ID
    assert data["transfer_txn_id"] == TRANSFER_TXN_ID
    assert data["status"] == "claimed"
    assert str(ASSET_ID) in data["explorer_url"]


@pytest.mark.asyncio
async def test_claim_endpoint_updates_nft_status_to_claimed(client: AsyncClient):
    """The claim endpoint must update nft_record.status to 'claimed'."""
    mock_inv = _mock_invoice()
    mock_nft = mock_inv.nft_record

    with (
        patch(
            "app.modules.invoices.router._get_invoice_for_user",
            new=AsyncMock(return_value=mock_inv),
        ),
        patch(
            "app.modules.invoices.nft_service.submit_signed_txn",
            new=AsyncMock(return_value=OPTIN_TXN_ID),
        ),
        patch(
            "app.modules.invoices.nft_service.transfer_nft",
            return_value={
                "txn_id": TRANSFER_TXN_ID,
                "asset_id": ASSET_ID,
                "confirmed_round": 42,
            },
        ),
    ):
        await client.post(
            f"/api/v1/invoices/{INVOICE_ID}/nft/claim",
            json={
                "wallet_address": WALLET_ADDRESS,
                "signed_optin_txn": SIGNED_OPTIN_B64,
            },
        )

    assert mock_nft.status == "claimed"
    assert mock_nft.transfer_txn_id == TRANSFER_TXN_ID
    assert mock_nft.claimed_by_wallet == WALLET_ADDRESS


@pytest.mark.asyncio
async def test_claim_endpoint_returns_404_if_invoice_not_found(client: AsyncClient):
    """POST /{invoice_id}/nft/claim returns 404 when invoice not found (IDOR prevention)."""
    with patch(
        "app.modules.invoices.router._get_invoice_for_user",
        new=AsyncMock(
            side_effect=HTTPException(status_code=404, detail="Invoice not found")
        ),
    ):
        response = await client.post(
            f"/api/v1/invoices/{INVOICE_ID}/nft/claim",
            json={
                "wallet_address": WALLET_ADDRESS,
                "signed_optin_txn": SIGNED_OPTIN_B64,
            },
        )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_claim_endpoint_explorer_url_contains_asset_id(client: AsyncClient):
    """The explorer_url in the response must reference the asset_id."""
    mock_inv = _mock_invoice()

    with (
        patch(
            "app.modules.invoices.router._get_invoice_for_user",
            new=AsyncMock(return_value=mock_inv),
        ),
        patch(
            "app.modules.invoices.nft_service.submit_signed_txn",
            new=AsyncMock(return_value=OPTIN_TXN_ID),
        ),
        patch(
            "app.modules.invoices.nft_service.transfer_nft",
            return_value={
                "txn_id": TRANSFER_TXN_ID,
                "asset_id": ASSET_ID,
                "confirmed_round": 42,
            },
        ),
    ):
        response = await client.post(
            f"/api/v1/invoices/{INVOICE_ID}/nft/claim",
            json={
                "wallet_address": WALLET_ADDRESS,
                "signed_optin_txn": SIGNED_OPTIN_B64,
            },
        )

    data = response.json()
    assert f"/asset/{ASSET_ID}/" in data["explorer_url"]
    assert "perawallet" in data["explorer_url"]
