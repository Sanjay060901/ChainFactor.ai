"""Dialect-agnostic column types for PostgreSQL and SQLite compatibility.

When DATABASE_URL starts with 'sqlite', uses plain String/Text columns.
Otherwise, uses native PostgreSQL UUID and JSONB types.
"""

import json
import uuid

from sqlalchemy import String, Text, TypeDecorator
from sqlalchemy.types import TypeEngine


class GUID(TypeDecorator):
    """Platform-independent UUID type.

    Uses PostgreSQL UUID when available, otherwise stores as CHAR(36).
    """

    impl = String(36)
    cache_ok = True

    def load_dialect_impl(self, dialect) -> TypeEngine:
        if dialect.name == "postgresql":
            from sqlalchemy.dialects.postgresql import UUID as PG_UUID

            return dialect.type_descriptor(PG_UUID(as_uuid=True))
        return dialect.type_descriptor(String(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        if dialect.name == "postgresql":
            return value if isinstance(value, uuid.UUID) else uuid.UUID(value)
        return str(value) if isinstance(value, uuid.UUID) else value

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        if isinstance(value, uuid.UUID):
            return value
        return uuid.UUID(value)


class JSONType(TypeDecorator):
    """Platform-independent JSON type.

    Uses PostgreSQL JSONB when available, otherwise stores as Text with
    JSON serialization/deserialization.
    """

    impl = Text
    cache_ok = True

    def load_dialect_impl(self, dialect) -> TypeEngine:
        if dialect.name == "postgresql":
            from sqlalchemy.dialects.postgresql import JSONB

            return dialect.type_descriptor(JSONB())
        return dialect.type_descriptor(Text())

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        if dialect.name == "postgresql":
            return value  # JSONB handles native Python dicts/lists
        return json.dumps(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        if isinstance(value, (dict, list)):
            return value  # Already deserialized (PostgreSQL JSONB)
        return json.loads(value)
