"""Schemas for shareable link generation and resolution."""

from datetime import datetime
from typing import Any
from pydantic import BaseModel
from app.constants.enums import LinkTargetType


class GenerateLinkRequest(BaseModel):
    target_type: LinkTargetType
    target_id: str
    expires_at: datetime | None = None


class SharedLinkResponse(BaseModel):
    id: str
    short_code: str
    target_type: LinkTargetType
    target_id: str
    creator_id: str
    expires_at: datetime | None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class ResolvedLinkResponse(BaseModel):
    link: SharedLinkResponse
    # The actual resource data (book / shlok / meaning dict) 
    data: dict[str, Any]
