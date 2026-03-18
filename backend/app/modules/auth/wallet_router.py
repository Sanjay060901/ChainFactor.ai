"""Wallet API endpoints -- link/unlink Algorand wallet to user account."""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.modules.auth.dependencies import get_current_user
from app.schemas.wallet import (
    WalletLinkRequest,
    WalletLinkResponse,
    WalletStatusResponse,
    WalletUnlinkResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/wallet", tags=["wallet"])


@router.post("/link", response_model=WalletLinkResponse)
async def link_wallet(
    body: WalletLinkRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Link an Algorand wallet address to the authenticated user.

    The frontend signs a message with the wallet to prove ownership.
    TODO: Verify signed_message against wallet_address on-chain.
    """
    # Validate Algorand address format (58 chars, alphanumeric)
    if len(body.wallet_address) != 58:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid Algorand address (must be 58 characters)",
        )

    # TODO: Verify signature proves wallet ownership
    # For hackathon, we trust the frontend (Pera/Defly wallet signs the message)

    current_user.wallet_address = body.wallet_address
    db.add(current_user)
    await db.flush()

    logger.info("Wallet linked for user %s: %s", current_user.id, body.wallet_address)

    return WalletLinkResponse(
        linked=True,
        wallet_address=body.wallet_address,
    )


@router.get("/status", response_model=WalletStatusResponse)
async def wallet_status(
    current_user: User = Depends(get_current_user),
):
    """Get wallet link status for the authenticated user."""
    return WalletStatusResponse(
        linked=current_user.wallet_address is not None,
        wallet_address=current_user.wallet_address,
        algo_balance=None,  # TODO: Query Algorand indexer for balance
    )


@router.delete("/link", response_model=WalletUnlinkResponse)
async def unlink_wallet(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Unlink the Algorand wallet from the authenticated user."""
    if not current_user.wallet_address:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No wallet linked",
        )

    logger.info(
        "Wallet unlinked for user %s: %s", current_user.id, current_user.wallet_address
    )
    current_user.wallet_address = None
    db.add(current_user)
    await db.flush()

    return WalletUnlinkResponse(linked=False)
