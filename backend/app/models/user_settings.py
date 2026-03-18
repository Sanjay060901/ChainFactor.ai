"""User settings model -- per-user preferences like default underwriting action."""

import uuid

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDMixin


class UserSettings(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "user_settings"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=False
    )

    # Default action when no rules match: "flag_for_review", "reject", "always_approve"
    default_action: Mapped[str] = mapped_column(
        String(32), nullable=False, default="flag_for_review"
    )
