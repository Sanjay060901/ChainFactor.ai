"""Public verification endpoint - no auth required.

Allows anyone to verify an invoice NFT by asset ID using on-chain data.
This is a key transparency feature for the hackathon demo.
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends

from app.config import settings
from app.database import get_db

router = APIRouter(prefix="/verify", tags=["verify"])


class VerifyResponse(BaseModel):
    """Public verification response - no sensitive data exposed."""
    verified: bool
    asset_id: int
    invoice_number: str | None = None
    seller_name: str | None = None
    buyer_name: str | None = None
    amount: float | None = None
    risk_score: int | None = None
    risk_level: str | None = None
    decision: str | None = None
    minted_at: str | None = None
    claimed: bool = False
    explorer_url: str
    arc69_metadata: dict | None = None


@router.get("/nft/{asset_id}", response_model=VerifyResponse)
async def verify_nft(
    asset_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Verify an invoice NFT by Algorand asset ID. No authentication required.

    This endpoint allows anyone (lenders, auditors, regulators) to verify
    that an invoice was processed and approved by ChainFactor AI. It returns
    public invoice data without exposing sensitive user information.
    """
    from sqlalchemy import select
    from app.models.nft_record import NFTRecord

    result = await db.execute(
        select(NFTRecord).where(NFTRecord.asset_id == asset_id)
    )
    nft = result.scalars().first()

    if not nft:
        raise HTTPException(
            status_code=404,
            detail=f"No invoice NFT found for asset ID {asset_id}",
        )

    # Load associated invoice for public-safe data
    from app.models.invoice import Invoice

    inv_result = await db.execute(
        select(Invoice).where(Invoice.id == nft.invoice_id)
    )
    invoice = inv_result.scalar_one_or_none()

    metadata = nft.arc69_metadata or {}
    props = metadata.get("properties", {})

    explorer_url = f"{settings.PERA_EXPLORER_BASE_URL}/asset/{asset_id}/"

    # Extract public data from invoice (if exists)
    extracted = (invoice.extracted_data or {}) if invoice else {}
    risk = (invoice.risk_assessment or {}) if invoice else {}

    return VerifyResponse(
        verified=True,
        asset_id=asset_id,
        invoice_number=props.get("invoice_number") or (invoice.invoice_number if invoice else None),
        seller_name=props.get("seller") or extracted.get("seller", {}).get("name"),
        buyer_name=props.get("buyer") or extracted.get("buyer", {}).get("name"),
        amount=props.get("amount") or extracted.get("total_amount"),
        risk_score=props.get("risk_score") or (invoice.risk_score if invoice else None),
        risk_level=risk.get("level") or (
            "low" if (invoice and invoice.risk_score and invoice.risk_score >= 70)
            else "medium" if (invoice and invoice.risk_score and invoice.risk_score >= 40)
            else "high" if (invoice and invoice.risk_score)
            else None
        ),
        decision=invoice.status if invoice else None,
        minted_at=nft.created_at.isoformat() if hasattr(nft, "created_at") and nft.created_at else None,
        claimed=nft.status == "claimed",
        explorer_url=explorer_url,
        arc69_metadata=metadata,
    )


@router.get("/search")
async def search_nft(
    invoice_number: str = Query(..., min_length=1, max_length=50),
    db: AsyncSession = Depends(get_db),
):
    """Search for an NFT by invoice number. No authentication required.

    Returns basic verification data for the matching invoice.
    """
    from sqlalchemy import select
    from app.models.invoice import Invoice
    from app.models.nft_record import NFTRecord

    result = await db.execute(
        select(Invoice).where(Invoice.invoice_number == invoice_number)
    )
    invoice = result.scalar_one_or_none()

    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    nft_result = await db.execute(
        select(NFTRecord).where(NFTRecord.invoice_id == invoice.id)
    )
    nft = nft_result.scalars().first()

    if not nft or not nft.asset_id:
        raise HTTPException(status_code=404, detail="No NFT minted for this invoice")

    return {
        "asset_id": nft.asset_id,
        "invoice_number": invoice.invoice_number,
        "status": nft.status,
        "explorer_url": f"{settings.PERA_EXPLORER_BASE_URL}/asset/{nft.asset_id}/",
    }
