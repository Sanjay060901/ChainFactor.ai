"""Agent trace model -- persists full reasoning chain for audit trail."""

import uuid

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin
from app.models.compat import GUID, JSONType


class AgentTrace(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "agent_traces"

    invoice_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("invoices.id"), nullable=False, index=True
    )

    # Which agent produced this trace
    agent_name: Mapped[str] = mapped_column(String(64), nullable=False)
    model: Mapped[str] = mapped_column(String(64), nullable=False)

    # Timing
    duration_ms: Mapped[int] = mapped_column(Integer, nullable=False)

    # Steps stored as JSONB list:
    # [{"step_number": 1, "tool_name": "extract_invoice", "duration_ms": 3200,
    #   "input_summary": "...", "output_summary": "...", "result": {...}, "status": "complete"}, ...]
    steps: Mapped[list] = mapped_column(JSONType(), nullable=False)

    # Handoff context (what was passed to the next agent, if any)
    handoff_context: Mapped[dict | None] = mapped_column(JSONType(), nullable=True)

    # Relationship
    invoice: Mapped["Invoice"] = relationship(  # noqa: F821
        back_populates="agent_traces"
    )
