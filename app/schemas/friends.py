"""Schemas for the friend / social system."""

from datetime import datetime
from pydantic import BaseModel
from app.constants.enums import FriendRequestStatus


class SendFriendRequestRequest(BaseModel):
    receiver_id: str


class FriendRequestResponse(BaseModel):
    id: str
    sender_id: str
    receiver_id: str
    sender_username: str
    sender_avatar: str | None
    receiver_username: str | None = None
    status: FriendRequestStatus
    created_at: datetime

    model_config = {"from_attributes": True}


class FriendResponse(BaseModel):
    id: str
    username: str
    full_name: str | None
    avatar_url: str | None
    bio: str | None

    model_config = {"from_attributes": True}


class UserSearchResult(BaseModel):
    id: str
    username: str
    full_name: str | None
    avatar_url: str | None
    is_friend: bool
    pending_request_id: str | None  # non-null if a request is pending either way
