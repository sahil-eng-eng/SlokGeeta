"""Book request / response schemas."""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from app.constants.enums import Visibility


class CreateBookRequest(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    description: Optional[str] = None
    category: Optional[str] = None
    tags: list[str] = []
    source: Optional[str] = None
    author_name: Optional[str] = None
    visibility: Visibility = Visibility.PRIVATE


class UpdateBookRequest(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    description: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[list[str]] = None
    source: Optional[str] = None
    author_name: Optional[str] = None
    visibility: Optional[Visibility] = None


class BookResponse(BaseModel):
    id: str
    owner_id: str
    title: str
    description: Optional[str] = None
    cover_image_url: Optional[str] = None
    category: Optional[str] = None
    tags: list[str] = []
    source: Optional[str] = None
    author_name: Optional[str] = None
    visibility: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class BookListResponse(BaseModel):
    items: list[BookResponse]
    next_cursor: Optional[str] = None
    has_more: bool = False
