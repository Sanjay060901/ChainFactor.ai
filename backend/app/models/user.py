"""User model -- linked to Cognito identity + optional Algorand wallet."""

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class User(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "users"

    cognito_sub: Mapped[str] = mapped_column(
        String(128), unique=True, nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    email: Mapped[str] = mapped_column(String(320), unique=True, nullable=False)
    phone: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    company_name: Mapped[str] = mapped_column(String(512), nullable=False)
    gstin: Mapped[str] = mapped_column(String(15), nullable=False, index=True)
    password_hash: Mapped[str | None] = mapped_column(String(256), nullable=True)

    # Algorand wallet (optional, linked after registration)
    wallet_address: Mapped[str | None] = mapped_column(String(58), nullable=True)

    # Relationships
    invoices: Mapped[list["Invoice"]] = relationship(  # noqa: F821
        back_populates="user", lazy="selectin"
    )
    rules: Mapped[list["Rule"]] = relationship(  # noqa: F821
        back_populates="user", lazy="selectin"
    )
