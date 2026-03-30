"""Schemas for the real-time chat system."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from app.constants.enums import MessageStatus


class SendMessageRequest(BaseModel):
    receiver_id: str
    content: str


class MessageBody(BaseModel):
    content: str


class EditMessageBody(BaseModel):
    content: str


class MessageResponse(BaseModel):
    id: str
    sender_id: str
    receiver_id: str
    content: str
    status: MessageStatus
    created_at: datetime
    is_deleted: bool = False
    edited_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class MessageListResponse(BaseModel):
    items: list[MessageResponse]
    has_more: bool
    # cursor to pass as `before_id` in the next request
    next_cursor: str | None


class ConversationPreview(BaseModel):
    """Summary of the most recent message with a given user."""
    friend_id: str
    friend_username: str
    friend_avatar: str | None
    last_message: str
    last_message_at: datetime
    unread_count: int


# ── WebSocket event payloads ───────────────────────────────────────────────────

class WsNewMessage(BaseModel):
    type: str = "new_message"
    message: MessageResponse


class WsTypingEvent(BaseModel):
    type: str = "typing"
    sender_id: str
    receiver_id: str
    is_typing: bool


class WsStatusUpdate(BaseModel):
    type: str = "status_update"
    message_id: str
    status: MessageStatus


class WsDeliveredAck(BaseModel):
    type: str = "delivered"
    message_ids: list[str]
