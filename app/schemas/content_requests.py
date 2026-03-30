"""Schemas for Content Requests (change-request / approval workflow)."""

from datetime import datetime
from typing import Any
from pydantic import BaseModel
from app.constants.enums import EntityType, ContentAction, ContentRequestStatus


class CreateContentRequestRequest(BaseModel):
    entity_type: EntityType
    entity_id: str
    action: ContentAction
    proposed_content: dict[str, Any] | None = None


class ReviewContentRequestRequest(BaseModel):
    status: ContentRequestStatus  # approved | rejected
    reviewer_note: str | None = None


class ContentRequestResponse(BaseModel):
    id: str
    requester_id: str
    requester_username: str
    entity_type: EntityType
    entity_id: str
    action: ContentAction
    proposed_content: dict[str, Any] | None
    status: ContentRequestStatus
    reviewer_id: str | None
    reviewer_note: str | None
    created_at: datetime
    # Context fields — populated on listing to help the reviewer understand what's being changed
    context_breadcrumb: list[str] | None = None   # e.g. ["Book: Bhagavad Gita", "Shlok: ...", "Meaning: ..."]
    current_content: str | None = None            # Current content of the entity being edited

    model_config = {"from_attributes": True}


class ContentRequestListResponse(BaseModel):
    items: list[ContentRequestResponse]
    total: int
