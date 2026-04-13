"""Invoice model -- core entity with JSONB columns for AI pipeline results."""

import uuid

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin
from app.models.compat import GUID, JSONType


class Invoice(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "invoices"

    user_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("users.id"), nullable=False, index=True
    )

    # Invoice identifiers
    invoice_number: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="uploaded", index=True
    )
    # Statuses: uploaded, processing, extracting, validating, analyzing,
    #           underwriting, minting, approved, rejected, flagged, failed

    # File storage (S3)
    file_key: Mapped[str] = mapped_column(String(512), nullable=False)
    file_name: Mapped[str] = mapped_column(String(256), nullable=False)

    # AI pipeline results (JSON -- flexible, matches Pydantic schemas)
    extracted_data: Mapped[dict | None] = mapped_column(JSONType(), nullable=True)
    validation_result: Mapped[dict | None] = mapped_column(JSONType(), nullable=True)
    gst_compliance: Mapped[dict | None] = mapped_column(JSONType(), nullable=True)
    fraud_detection: Mapped[dict | None] = mapped_column(JSONType(), nullable=True)
    gstin_verification: Mapped[dict | None] = mapped_column(JSONType(), nullable=True)
    buyer_intel: Mapped[dict | None] = mapped_column(JSONType(), nullable=True)
    credit_score: Mapped[dict | None] = mapped_column(JSONType(), nullable=True)
    company_info: Mapped[dict | None] = mapped_column(JSONType(), nullable=True)
    risk_assessment: Mapped[dict | None] = mapped_column(JSONType(), nullable=True)
    underwriting: Mapped[dict | None] = mapped_column(JSONType(), nullable=True)

    # Risk score (denormalized for fast queries/sorting)
    risk_score: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Processing timestamps
    processing_started_at: Mapped[str | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    processing_completed_at: Mapped[str | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    processing_duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # AI explanation (denormalized for fast display)
    ai_explanation: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="invoices")  # noqa: F821
    nft_record: Mapped["NFTRecord | None"] = relationship(  # noqa: F821
        back_populates="invoice", uselist=False, lazy="selectin"
    )
    agent_traces: Mapped[list["AgentTrace"]] = relationship(  # noqa: F821
        back_populates="invoice", lazy="selectin"
    )
