"""mint_nft tool: ARC-69 NFT minting on Algorand testnet.

Creates an Algorand Standard Asset (ASA) with ARC-69 metadata representing
a verified invoice. In DEMO_MODE, returns a mock result without any algosdk
calls. In real mode, uses _create_asa() to interact with the Algorand testnet.

Return shape:
    {"asset_id": int, "txn_id": str, "explorer_url": str, "metadata": dict}

ARC-69 metadata shape:
    {"standard": "arc69", "description": str,
     "properties": {invoice_number, seller, buyer, amount, risk_score, risk_level, date}}

Dependencies:
    - strands (@tool decorator)
    - app.config.settings (DEMO_MODE, PERA_EXPLORER_BASE_URL, ALGORAND_*)
    - algosdk (py-algorand-sdk v2.11.1) -- only in real mode
"""

import json
import logging

from strands import tool

from app.config import settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_DEMO_ASSET_ID = 123456789
_DEMO_TXN_ID = "DEMO_TXN_MINT_001"
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

    This function makes real algosdk calls. It is patched in tests.

    Args:
        metadata: ARC-69 metadata dict to embed in the ASA note field.
        invoice_id: Invoice identifier for logging.

    Returns:
        Tuple of (asset_id, txn_id).
    """
    from algosdk import transaction
    import algosdk
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

    # Get suggested params
    params = algod_client.suggested_params()

    # Build ASA creation transaction
    note = json.dumps(metadata).encode("utf-8")
    txn = transaction.AssetConfigTxn(
        sender=sender,
        sp=params,
        total=1,
        decimals=0,
        default_frozen=False,
        unit_name="CFINV",
        asset_name=f"ChainFactor-{metadata.get('properties', {}).get('invoice_number', 'INV')}",
        url=f"https://chainfactor.ai/invoice/{invoice_id}",
        note=note,
        manager=sender,
        reserve=sender,
        freeze=sender,
        clawback=sender,
    )

    # Sign and send
    signed_txn = txn.sign(private_key)
    txn_id = algod_client.send_transaction(signed_txn)

    # Wait for confirmation
    confirmed = transaction.wait_for_confirmation(algod_client, txn_id, 4)
    asset_id = confirmed["asset-index"]

    logger.info(
        "ASA created: asset_id=%d txn_id=%s invoice=%s",
        asset_id,
        txn_id,
        invoice_id,
    )

    return asset_id, txn_id


def _resolve_mint(
    invoice_id: str,
    extracted_data: dict,
    risk_assessment: dict,
    use_demo: bool,
) -> dict:
    """Core minting logic, separated from the Strands decorator.

    Args:
        invoice_id: Invoice identifier.
        extracted_data: Structured invoice data from extract_invoice tool.
        risk_assessment: Risk assessment from calculate_risk tool.
        use_demo: Whether to return the demo (mock) result.

    Returns:
        Dict with keys: asset_id (int), txn_id (str), explorer_url (str), metadata (dict).
    """
    metadata = _build_arc69_metadata(extracted_data, risk_assessment)

    if use_demo:
        logger.info("DEMO_MODE: returning mock NFT minting result")
        return {
            "asset_id": _DEMO_ASSET_ID,
            "txn_id": _DEMO_TXN_ID,
            "explorer_url": _explorer_url(_DEMO_ASSET_ID),
            "metadata": metadata,
        }

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
    an ARC-69 note. In DEMO_MODE, returns a mock result.

    Args:
        invoice_id: The invoice identifier.
        extracted_data: Structured invoice dict from extract_invoice tool.
        risk_assessment: Risk assessment dict from calculate_risk tool.
    """
    return _resolve_mint(
        invoice_id,
        extracted_data,
        risk_assessment,
        use_demo=settings.DEMO_MODE,
    )


# ---------------------------------------------------------------------------
# Public callable (used by tests and by agent tool list)
# Accepts an optional _demo override so tests can force real/demo paths
# without changing global settings.
# ---------------------------------------------------------------------------


def mint_nft(
    invoice_id: str,
    extracted_data: dict,
    risk_assessment: dict,
    _demo: bool = None,
) -> dict:
    """Mint an ARC-69 NFT on Algorand testnet for a verified invoice.

    Wraps _mint_nft_tool with a _demo override for testability.

    Args:
        invoice_id: The invoice identifier.
        extracted_data: Structured invoice dict from extract_invoice tool.
        risk_assessment: Risk assessment dict from calculate_risk tool.
        _demo: Override for DEMO_MODE. True forces demo path, False forces real
               logic, None defers to settings.DEMO_MODE.

    Returns:
        Dict with keys: asset_id (int), txn_id (str), explorer_url (str), metadata (dict).
    """
    use_demo = settings.DEMO_MODE if _demo is None else _demo
    return _resolve_mint(
        invoice_id,
        extracted_data,
        risk_assessment,
        use_demo=use_demo,
    )
