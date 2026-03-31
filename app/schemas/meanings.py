"""Meaning request / response schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from app.constants.enums import ApprovalStatus


class CreateMeaningRequest(BaseModel):
    content: str = Field(min_length=1)
    parent_id: Optional[str] = None


class InsertMeaningAboveRequest(BaseModel):
    """Insert a new meaning directly above an existing sibling."""
    content: str = Field(min_length=1)
    target_meaning_id: str = Field(..., description="The meaning above which to insert")


class UpdateMeaningRequest(BaseModel):
    content: Optional[str] = Field(default=None, min_length=1)
    visibility: Optional[str] = None  # 'public' | 'private' | 'specific_users'


class VoteMeaningRequest(BaseModel):
    direction: int = Field(..., ge=-1, le=1)


class MeaningResponse(BaseModel):
    id: str
    shlok_id: str
    parent_id: Optional[str] = None
    author_id: str
    # Frontend expects "text" not "content" and "author" not "author_id"
    text: str
    author: str
    author_reputation: Optional[int] = None
    votes: int
    created_at: datetime
    status: str
    is_owner: bool = False
    visibility: str = "private"
    # Viewer's permission level on this meaning (null for author or public access)
    my_permission: Optional[str] = None
    # Placeholder arrays — full implementation can be added later
    reactions: list = []
    versions: list = []
    children: list[MeaningResponse] = []

    model_config = {"from_attributes": True}


# Required for recursive self-reference in Pydantic v2
MeaningResponse.model_rebuild()


class MeaningListResponse(BaseModel):
    items: list[MeaningResponse]
