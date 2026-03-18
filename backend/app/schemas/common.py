"""Common response schemas used across modules."""

from pydantic import BaseModel


class MessageResponse(BaseModel):
    message: str


class PaginatedParams(BaseModel):
    page: int = 1
    limit: int = 10
    sort: str = "-created_at"
    search: str | None = None
