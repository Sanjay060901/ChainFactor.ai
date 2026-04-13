"""mint_nft tool: ARC-69 NFT minting on Algorand testnet.

Creates an Algorand Standard Asset (ASA) with ARC-69 metadata representing
a verified invoice. Uses _create_asa() to interact with the Algorand testnet.

Return shape:
    {"asset_id": int, "txn_id": str, "explorer_url": str, "metadata": dict}

ARC-69 metadata shape:
    {"standard": "arc69", "description": str,
     "properties": {invoice_number, seller, buyer, amount, risk_score, risk_level, date}}

Dependencies:
    - strands (@tool decorator)
    - app.config.settings (PERA_EXPLORER_BASE_URL, ALGORAND_*)
    - algosdk (py-algorand-sdk v2.11.1)
"""

import json
import logging

from strands import tool

from app.config import settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_PERA_EXPLORER_ASSET_URL = "https://testnet.explorer.perawallet.app/asset/{asset_id}/"


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _build_arc69_metadata(extracted_data: dict, risk_assessment: dict) -> dict:
    """Build ARC-69 compliant metadata for the NFT.

    Args:
        extracted_data: Structured invoice data from extract_invoice tool.
        risk_assessment: Risk assessment from calculate_risk tool.

    Returns:
        Dict following ARC-69 metadata standard.
    """
    seller_name = (extracted_data.get("seller") or {}).get("name", "Unknown Seller")
    buyer_name = (extracted_data.get("buyer") or {}).get("name", "Unknown Buyer")
    invoice_number = extracted_data.get("invoice_number", "N/A")
    invoice_date = extracted_data.get("invoice_date", "N/A")
    total_amount = extracted_data.get("total_amount", 0.0)
    risk_score = risk_assessment.get("score", 0)
    risk_level = risk_assessment.get("level", "unknown")

    return {
        "standard": "arc69",
        "description": (
            f"ChainFactor AI verified invoice {invoice_number} "
            f"from {seller_name} to {buyer_name}."
        ),
        "properties": {
            "invoice_number": invoice_number,
            "seller": seller_name,
            "buyer": buyer_name,
            "amount": total_amount,
            "risk_score": risk_score,
            "risk_level": risk_level,
            "date": invoice_date,
        },
    }


def _explorer_url(asset_id: int) -> str:
    """Build the Pera Explorer URL for a testnet ASA."""
    return _PERA_EXPLORER_ASSET_URL.format(asset_id=asset_id)


def _create_asa(
    metadata: dict,
    invoice_id: str,
) -> tuple[int, str]:
    """Create an ASA on Algorand testnet with ARC-69 metadata.

    When ALGORAND_APP_ID > 0: calls the deployed InvoiceNFT ARC4 contract's
    create_nft() method via AtomicTransactionComposer. The contract creates
    the ASA as an inner transaction and returns the asset ID.

    When ALGORAND_APP_ID == 0: falls back to direct AssetConfigTxn creation
    (no contract needed -- same ARC-69 metadata in note field).

    This function makes real algosdk calls. It is patched in tests.

    Args:
        metadata: ARC-69 metadata dict to embed in the ASA note field.
        invoice_id: Invoice identifier for logging.

    Returns:
        Tuple of (asset_id, txn_id).
    """
    import algosdk
    from algosdk import transaction
    from algosdk.v2client import algod

    logger.info("Creating ASA on testnet for invoice %s", invoice_id)

    # Connect to Algorand testnet via Algonode (free, no token)
    algod_client = algod.AlgodClient(
        algod_token="",
        algod_address=settings.ALGORAND_ALGOD_URL,
        headers={"User-Agent": "ChainFactor-AI"},
    )

    # Recover the application wallet from mnemonic
    private_key = algosdk.mnemonic.to_private_key(settings.ALGORAND_APP_WALLET_MNEMONIC)
    sender = algosdk.account.address_from_private_key(private_key)
    params = algod_client.suggested_params()
    metadata_json_str = json.dumps(metadata)
    note = metadata_json_str.encode("utf-8")

    # --- Path 1: Call deployed ARC4 contract (preferred) ---
    if settings.ALGORAND_APP_ID > 0:
        logger.info(
            "Calling ARC4 contract app_id=%d for invoice %s",
            settings.ALGORAND_APP_ID,
            invoice_id,
        )
        try:
            from algosdk.atomic_transaction_composer import (
                AccountTransactionSigner,
                AtomicTransactionComposer,
            )
            from algosdk.abi import Method

            # ABI method signature for InvoiceNFT.create_nft
            method = Method.from_signature(
                "create_nft(string,uint64,string,string)uint64"
            )

            props = metadata.get("properties", {})
            risk_score = int(props.get("risk_score", 0))
            decision = str(props.get("risk_level", "unknown"))
            invoice_id_arg = str(invoice_id)

            signer = AccountTransactionSigner(private_key)
            atc = AtomicTransactionComposer()
            atc.add_method_call(
                app_id=settings.ALGORAND_APP_ID,
                method=method,
                sender=sender,
                sp=params,
                signer=signer,
                method_args=[invoice_id_arg, risk_score, decision, metadata_json_str],
                note=note,
            )
            result = atc.execute(algod_client, wait_rounds=4)
            txn_id = result.tx_ids[0]
            asset_id = int(result.abi_results[0].return_value)

            logger.info(
                "ARC4 contract minted ASA: asset_id=%d txn_id=%s invoice=%s",
                asset_id, txn_id, invoice_id,
            )
            return asset_id, txn_id

        except Exception as exc:
            logger.warning(
                "ARC4 contract call failed (%s), falling back to direct ASA creation",
                exc,
            )

    # --- Path 2: Direct ASA creation (fallback / no contract configured) ---
    logger.info("Direct ASA creation for invoice %s", invoice_id)
    invoice_number = metadata.get("properties", {}).get("invoice_number", "INV")
    asset_name = f"CF-{invoice_number}"[:32]
    txn = transaction.AssetConfigTxn(
        sender=sender,
        sp=params,
        total=1,
        decimals=0,
        default_frozen=False,
        unit_name="CFINV",
        asset_name=asset_name,
        url=f"https://chainfactor.ai/invoice/{invoice_id}",
        note=note,
        manager=sender,
        reserve=sender,
        freeze=sender,
        clawback=sender,
    )
    signed_txn = txn.sign(private_key)
    txn_id = algod_client.send_transaction(signed_txn)
    confirmed = transaction.wait_for_confirmation(algod_client, txn_id, 4)
    asset_id = confirmed["asset-index"]

    logger.info(
        "Direct ASA created: asset_id=%d txn_id=%s invoice=%s",
        asset_id, txn_id, invoice_id,
    )
    return asset_id, txn_id


def _resolve_mint(
    invoice_id: str,
    extracted_data: dict,
    risk_assessment: dict,
) -> dict:
    """Core minting logic, separated from the Strands decorator."""
    metadata = _build_arc69_metadata(extracted_data, risk_assessment)

    logger.info("Minting ARC-69 NFT for invoice %s", invoice_id)

    asset_id, txn_id = _create_asa(metadata, invoice_id)

    return {
        "asset_id": asset_id,
        "txn_id": txn_id,
        "explorer_url": _explorer_url(asset_id),
        "metadata": metadata,
    }


# ---------------------------------------------------------------------------
# Strands @tool  (registered with the agent; no leading-underscore params)
# ---------------------------------------------------------------------------


@tool
def _mint_nft_tool(
    invoice_id: str,
    extracted_data: dict,
    risk_assessment: dict,
) -> dict:
    """Mint an ARC-69 NFT on Algorand testnet for a verified invoice.

    Creates an Algorand Standard Asset with invoice metadata embedded as
    an ARC-69 note.

    Args:
        invoice_id: The invoice identifier.
        extracted_data: Structured invoice dict from extract_invoice tool.
        risk_assessment: Risk assessment dict from calculate_risk tool.
    """
    return _resolve_mint(
        invoice_id,
        extracted_data,
        risk_assessment,
    )


# ---------------------------------------------------------------------------
# Public callable (used by tests and by agent tool list)
# ---------------------------------------------------------------------------


def mint_nft(
    invoice_id: str,
    extracted_data: dict,
    risk_assessment: dict,
) -> dict:
    """Mint an ARC-69 NFT on Algorand testnet for a verified invoice.

    Args:
        invoice_id: The invoice identifier.
        extracted_data: Structured invoice dict from extract_invoice tool.
        risk_assessment: Risk assessment dict from calculate_risk tool.

    Returns:
        Dict with keys: asset_id (int), txn_id (str), explorer_url (str), metadata (dict).
    """
    return _resolve_mint(
        invoice_id,
        extracted_data,
        risk_assessment,
    )
