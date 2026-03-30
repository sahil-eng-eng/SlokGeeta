"""Pydantic schemas for Kirtan Library."""

from typing import Optional
from pydantic import BaseModel
from app.constants.enums import KirtanCategory


class CreateKirtanTrackRequest(BaseModel):
    title: str
    artist: Optional[str] = None
    album: Optional[str] = None
    duration_seconds: Optional[int] = None
    category: KirtanCategory = KirtanCategory.KIRTAN
    audio_url: Optional[str] = None
    external_link: Optional[str] = None
    cover_url: Optional[str] = None


class UpdateKirtanTrackRequest(BaseModel):
    title: Optional[str] = None
    artist: Optional[str] = None
    album: Optional[str] = None
    duration_seconds: Optional[int] = None
    category: Optional[KirtanCategory] = None
    audio_url: Optional[str] = None
    external_link: Optional[str] = None
    cover_url: Optional[str] = None


class KirtanTrackResponse(BaseModel):
    id: str
    owner_id: str
    title: str
    artist: Optional[str]
    album: Optional[str]
    duration_seconds: Optional[int]
    category: str
    audio_url: Optional[str]
    external_link: Optional[str]
    cover_url: Optional[str]
    is_favorite: bool

    model_config = {"from_attributes": True}
