"""Seller auto-approve rule model."""

import uuid

from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class Rule(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "rules"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )

    # Conditions stored as JSONB list:
    # [{"field": "invoice_amount", "operator": "less_than", "value": 500000}, ...]
    conditions: Mapped[list] = mapped_column(JSONB, nullable=False)

    # Action: "auto_approve", "flag_for_review", "reject"
    action: Mapped[str] = mapped_column(
        String(32), nullable=False, default="auto_approve"
    )

    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Relationship
    user: Mapped["User"] = relationship(back_populates="rules")  # noqa: F821
