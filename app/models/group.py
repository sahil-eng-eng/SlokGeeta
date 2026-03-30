"""Group chat models — GroupConversation, GroupMember, GroupMessage."""

from datetime import datetime
from typing import Optional
from sqlalchemy import String, Text, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import BaseModel

# Role constants for group members
GROUP_ROLE_OWNER = "owner"
GROUP_ROLE_CO_ADMIN = "co_admin"
GROUP_ROLE_MEMBER = "member"


class GroupConversation(BaseModel):
    """A named group chat conversation."""

    __tablename__ = "group_conversations"

    name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    creator_id: Mapped[str] = mapped_column(
        String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    avatar_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class GroupMember(BaseModel):
    """Membership record linking a user to a group."""

    __tablename__ = "group_members"
    __table_args__ = (
        Index("ix_group_members_group_user", "group_id", "user_id", unique=True),
    )

    group_id: Mapped[str] = mapped_column(
        String, ForeignKey("group_conversations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[str] = mapped_column(
        String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # Role: owner | co_admin | member
    role: Mapped[str] = mapped_column(String(20), nullable=False, default=GROUP_ROLE_MEMBER, server_default=GROUP_ROLE_MEMBER)
    # Keep is_admin for backward compat; derived from role
    is_admin: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


class GroupMessage(BaseModel):
    """A message sent in a group conversation."""

    __tablename__ = "group_messages"
    __table_args__ = (
        Index("ix_group_messages_group_created", "group_id", "created_at"),
    )

    group_id: Mapped[str] = mapped_column(
        String, ForeignKey("group_conversations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    sender_id: Mapped[str] = mapped_column(
        String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    is_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    edited_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
