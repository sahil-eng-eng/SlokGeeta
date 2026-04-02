"""Pydantic schemas for Granth module."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


# ── Granth ──────────────────────────────────────────────────────────────────

class CreateGranthRequest(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    description: Optional[str] = None
    author: Optional[str] = None
    language: str = "punjabi"


class UpdateGranthRequest(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    description: Optional[str] = None
    author: Optional[str] = None
    language: Optional[str] = None
    is_published: Optional[bool] = None


class GranthResponse(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    author: Optional[str] = None
    language: str
    total_pages: int
    cover_url: Optional[str] = None
    is_published: bool
    uploaded_by: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ── GranthPage ──────────────────────────────────────────────────────────────

class GranthPageResponse(BaseModel):
    id: str
    granth_id: str
    page_number: int
    content: str
    image_url: Optional[str] = None

    model_config = {"from_attributes": True}


class CreateGranthPageRequest(BaseModel):
    page_number: int
    content: str = ""
    image_url: Optional[str] = None


class UpdateGranthPageRequest(BaseModel):
    content: Optional[str] = None


# ── Progress ────────────────────────────────────────────────────────────────

class UpdateProgressRequest(BaseModel):
    current_page: int


class ProgressResponse(BaseModel):
    id: str
    user_id: str
    granth_id: str
    current_page: int
    last_read_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
