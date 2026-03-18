"""Wallet request/response schemas."""

from pydantic import BaseModel


class WalletLinkRequest(BaseModel):
    wallet_address: str
    signed_message: str


class WalletLinkResponse(BaseModel):
    linked: bool
    wallet_address: str


class WalletStatusResponse(BaseModel):
    linked: bool
    wallet_address: str | None = None
    algo_balance: float | None = None


class WalletUnlinkResponse(BaseModel):
    linked: bool
