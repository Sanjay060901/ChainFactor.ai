"""User settings model -- per-user preferences like default underwriting action."""

import uuid

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDMixin
from app.models.compat import GUID, JSONType

# Default AI settings for new users
DEFAULT_AI_SETTINGS: dict = {
    "pipeline_timeout": 120,
    "auto_process": True,
    "enable_ws_streaming": True,
    "risk_threshold_low": 70,
    "risk_threshold_high": 40,
    "enable_nft_auto_mint": True,
}


class UserSettings(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "user_settings"

    user_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("users.id"), unique=True, nullable=False
    )

    # Default action when no rules match: "flag_for_review", "reject", "always_approve"
    default_action: Mapped[str] = mapped_column(
        String(32), nullable=False, default="flag_for_review"
    )

    # User-configurable AI settings (JSONB)
    ai_settings: Mapped[dict] = mapped_column(
        JSONType(), nullable=False, default=DEFAULT_AI_SETTINGS
    )
