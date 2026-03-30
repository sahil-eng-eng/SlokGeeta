"""Shlok request / response schemas."""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from app.constants.enums import Visibility


class CreateShlokRequest(BaseModel):
    book_id: str
    content: str = Field(min_length=1)
    chapter_number: Optional[int] = None
    verse_number: Optional[int] = None
    tags: list[str] = []
    visibility: Visibility = Visibility.PRIVATE
    scheduled_at: Optional[datetime] = None


class UpdateShlokRequest(BaseModel):
    content: Optional[str] = Field(None, min_length=1)
    chapter_number: Optional[int] = None
    verse_number: Optional[int] = None
    tags: Optional[list[str]] = None
    visibility: Optional[Visibility] = None
    scheduled_at: Optional[datetime] = None


class ShlokResponse(BaseModel):
    id: str
    book_id: str
    owner_id: str
    content: str
    chapter_number: Optional[int] = None
    verse_number: Optional[int] = None
    tags: list[str] = []
    audio_url: Optional[str] = None
    visibility: str
    scheduled_at: Optional[datetime] = None
    view_count: int = 0
    created_at: datetime
    updated_at: datetime
    # Viewer's permission level on this shlok (null for owner or public access)
    my_permission: Optional[str] = None

    model_config = {"from_attributes": True}


class ShlokListResponse(BaseModel):
    items: list[ShlokResponse]
    next_cursor: Optional[str] = None
    has_more: bool = False


class CrossReferenceRequest(BaseModel):
    target_shlok_id: str
    note: Optional[str] = None


class CrossReferenceResponse(BaseModel):
    id: str
    source_shlok_id: str
    target_shlok_id: str
    note: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}
