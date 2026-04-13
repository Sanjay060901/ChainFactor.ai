"""Seller auto-approve rule model."""

import uuid

from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin
from app.models.compat import GUID, JSONType


class Rule(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "rules"

    user_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("users.id"), nullable=False, index=True
    )

    # Conditions stored as JSON list:
    # [{"field": "invoice_amount", "operator": "less_than", "value": 500000}, ...]
    conditions: Mapped[list] = mapped_column(JSONType(), nullable=False)

    # Action: "auto_approve", "flag_for_review", "reject"
    action: Mapped[str] = mapped_column(
        String(32), nullable=False, default="auto_approve"
    )

    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Relationship
    user: Mapped["User"] = relationship(back_populates="rules")  # noqa: F821
