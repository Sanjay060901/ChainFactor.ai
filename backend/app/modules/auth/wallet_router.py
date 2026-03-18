"""Wallet API stub endpoints."""

from fastapi import APIRouter

from app.schemas.wallet import (
    WalletLinkRequest,
    WalletLinkResponse,
    WalletStatusResponse,
    WalletUnlinkResponse,
)

router = APIRouter(prefix="/wallet", tags=["wallet"])


@router.post("/link", response_model=WalletLinkResponse)
async def link_wallet(body: WalletLinkRequest):
    return WalletLinkResponse(linked=True, wallet_address=body.wallet_address)


@router.get("/status", response_model=WalletStatusResponse)
async def wallet_status():
    return WalletStatusResponse(
        linked=True,
        wallet_address="ALGO7STUB2ADDRESS3FOR4DEMO5TESTING6WALLET7X4F2",
        algo_balance=10.5,
    )


@router.delete("/link", response_model=WalletUnlinkResponse)
async def unlink_wallet():
    return WalletUnlinkResponse(linked=False)
