"""ChatMessage model — individual messages between two users."""

from datetime import datetime
from typing import Optional
from sqlalchemy import String, Text, Enum as SAEnum, ForeignKey, Index, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import BaseModel
from app.constants.enums import MessageStatus


class ChatMessage(BaseModel):
    __tablename__ = "chat_messages"
    __table_args__ = (
        # Efficient pagination for a conversation ordered by time
        Index("ix_chat_conversation", "sender_id", "receiver_id", "created_at"),
        Index("ix_chat_receiver_status", "receiver_id", "status"),
    )

    sender_id: Mapped[str] = mapped_column(
        String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    receiver_id: Mapped[str] = mapped_column(
        String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        SAEnum(
            MessageStatus,
            name="message_status_enum",
            create_constraint=True,
            values_callable=lambda obj: [e.value for e in obj],
        ),
        nullable=False,
        default=MessageStatus.SENT,
        server_default=MessageStatus.SENT.value,
    )
    is_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    edited_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
