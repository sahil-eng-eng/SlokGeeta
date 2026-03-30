"""Generic API response wrapper."""

from typing import Optional, Generic, TypeVar
from pydantic import BaseModel

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    status_code: int
    message: str
    data: Optional[T] = None


class PaginatedData(BaseModel, Generic[T]):
    items: list
    next_cursor: Optional[str] = None
    has_more: bool = False
