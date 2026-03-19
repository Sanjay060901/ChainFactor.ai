"""NFT service -- builds Algorand transactions for opt-in and claim flows."""

from __future__ import annotations

import base64
import logging

import algosdk
from algosdk.v2client.algod import AlgodClient

from app.config import settings

logger = logging.getLogger(__name__)


def _get_algod_client() -> AlgodClient:
    """Return an AlgodClient pointed at the configured Algorand node.

    Uses an empty token string because Algonode public endpoints do not
    require authentication.

    Returns:
        AlgodClient: Configured client for the Algorand node.
    """
    return AlgodClient("", settings.ALGORAND_ALGOD_URL)


def build_optin_txn(*, wallet_address: str, asset_id: int) -> str:
    """Build an unsigned ASA opt-in transaction encoded as a base64 string.

    Opt-in = 0-amount AssetTransferTxn where sender == receiver.
    The caller must sign this transaction client-side and submit it to
    the Algorand network before the NFT transfer can proceed.

    Args:
        wallet_address: Algorand address of the user who wants to opt-in.
        asset_id:       The Algorand Standard Asset (ASA) ID to opt-in to.

    Returns:
        Base64-encoded msgpack of the unsigned AssetTransferTxn.
    """
    client = _get_algod_client()
    params = client.suggested_params()

    txn = algosdk.transaction.AssetTransferTxn(
        sender=wallet_address,
        receiver=wallet_address,
        amt=0,
        index=asset_id,
        sp=params,
    )

    encoded = algosdk.encoding.msgpack_encode(txn)
    # msgpack_encode returns bytes on newer versions; guard for either
    raw: bytes = encoded if isinstance(encoded, bytes) else encoded.encode()
    return base64.b64encode(raw).decode()


async def submit_signed_txn(signed_txn_b64: str) -> str:
    """Submit a base64-encoded signed transaction to Algorand testnet.

    Decodes the base64 string to raw bytes, submits via send_raw_transaction,
    then waits up to 4 rounds for confirmation before returning the txn ID.

    Args:
        signed_txn_b64: Base64-encoded signed transaction (from user's wallet).

    Returns:
        Transaction ID string of the confirmed transaction.
    """
    client = _get_algod_client()
    raw = base64.b64decode(signed_txn_b64)
    txid = client.send_raw_transaction(raw)
    algosdk.transaction.wait_for_confirmation(client, txid, 4)
    return txid


def transfer_nft(*, asset_id: int, receiver_address: str) -> dict:
    """Transfer ASA from application wallet to user wallet.

    The app wallet must already be the creator (or clawback address) of the ASA.
    Sends exactly 1 unit -- NFTs are indivisible single-unit assets.

    Args:
        asset_id:         Algorand Standard Asset ID to transfer.
        receiver_address: Algorand address of the recipient (user wallet).

    Returns:
        Dict with keys: txn_id (str), asset_id (int), confirmed_round (int).
    """
    client = _get_algod_client()
    params = client.suggested_params()

    private_key = algosdk.mnemonic.to_private_key(settings.ALGORAND_APP_WALLET_MNEMONIC)
    sender = algosdk.account.address_from_private_key(private_key)

    txn = algosdk.transaction.AssetTransferTxn(
        sender=sender,
        receiver=receiver_address,
        amt=1,
        index=asset_id,
        sp=params,
    )

    signed_txn = txn.sign(private_key)
    txid = client.send_transaction(signed_txn)
    result = algosdk.transaction.wait_for_confirmation(client, txid, 4)

    return {
        "txn_id": txid,
        "asset_id": asset_id,
        "confirmed_round": result.get("confirmed-round", 0),
    }
