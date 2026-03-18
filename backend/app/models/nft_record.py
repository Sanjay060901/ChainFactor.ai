"""NFT record model -- tracks Algorand ASA minting and claim status."""

import uuid

from sqlalchemy import BigInteger, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class NFTRecord(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "nft_records"

    invoice_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("invoices.id"), unique=True, nullable=False
    )

    # Algorand ASA details
    asset_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    mint_txn_id: Mapped[str | None] = mapped_column(String(64), nullable=True)

    # Claim flow: user opts-in then receives transfer
    opt_in_txn_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    transfer_txn_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    claimed_by_wallet: Mapped[str | None] = mapped_column(String(58), nullable=True)

    # ARC-69 metadata snapshot ("metadata" is reserved by SQLAlchemy DeclarativeBase)
    arc69_metadata: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Status: minted, opt_in_pending, claimed, failed
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="minted")

    # Relationship
    invoice: Mapped["Invoice"] = relationship(  # noqa: F821
        back_populates="nft_record"
    )
