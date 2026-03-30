"""Chat message repository — scalable cursor-based pagination."""

from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import select, and_, or_, update, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.chat_message import ChatMessage
from app.constants.enums import MessageStatus


class ChatRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, message: ChatMessage) -> ChatMessage:
        self.db.add(message)
        await self.db.flush()
        await self.db.refresh(message)
        return message

    async def get_by_id(self, msg_id: str) -> Optional[ChatMessage]:
        result = await self.db.execute(
            select(ChatMessage).where(ChatMessage.id == msg_id)
        )
        return result.scalar_one_or_none()

    async def get_conversation(
        self,
        user_a: str,
        user_b: str,
        limit: int = 50,
        before_id: Optional[str] = None,
    ) -> list[ChatMessage]:
        """Cursor-based: load `limit` messages before `before_id` (newest first)."""
        conversation_filter = or_(
            and_(
                ChatMessage.sender_id == user_a,
                ChatMessage.receiver_id == user_b,
            ),
            and_(
                ChatMessage.sender_id == user_b,
                ChatMessage.receiver_id == user_a,
            ),
        )

        query = select(ChatMessage).where(conversation_filter)

        if before_id:
            # Get the created_at of the cursor message
            cursor_result = await self.db.execute(
                select(ChatMessage.created_at).where(ChatMessage.id == before_id)
            )
            cursor_ts = cursor_result.scalar_one_or_none()
            if cursor_ts:
                query = query.where(ChatMessage.created_at < cursor_ts)

        query = query.order_by(ChatMessage.created_at.desc()).limit(limit + 1)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_recent_conversations(self, user_id: str) -> list[ChatMessage]:
        """Return the latest message in each conversation for this user."""
        # Subquery: for each (user_a, user_b) pair, max(created_at)
        # Simplified: get latest message per partner using a correlated subquery
        subq = (
            select(
                func.greatest(ChatMessage.sender_id, ChatMessage.receiver_id).label("user_max"),
                func.least(ChatMessage.sender_id, ChatMessage.receiver_id).label("user_min"),
                func.max(ChatMessage.created_at).label("max_ts"),
            )
            .where(
                or_(
                    ChatMessage.sender_id == user_id,
                    ChatMessage.receiver_id == user_id,
                )
            )
            .group_by("user_max", "user_min")
            .subquery()
        )
        result = await self.db.execute(
            select(ChatMessage)
            .join(
                subq,
                and_(
                    func.greatest(ChatMessage.sender_id, ChatMessage.receiver_id)
                    == subq.c.user_max,
                    func.least(ChatMessage.sender_id, ChatMessage.receiver_id)
                    == subq.c.user_min,
                    ChatMessage.created_at == subq.c.max_ts,
                ),
            )
            .order_by(ChatMessage.created_at.desc())
        )
        return list(result.scalars().all())

    async def count_unread(self, receiver_id: str, sender_id: str) -> int:
        result = await self.db.execute(
            select(func.count()).where(
                ChatMessage.receiver_id == receiver_id,
                ChatMessage.sender_id == sender_id,
                ChatMessage.status != MessageStatus.SEEN,
            )
        )
        return result.scalar_one()

    async def mark_seen(self, receiver_id: str, sender_id: str) -> list[str]:
        """Mark all unread messages from `sender_id` to `receiver_id` as seen.
        Returns list of updated message IDs."""
        result = await self.db.execute(
            select(ChatMessage.id).where(
                ChatMessage.receiver_id == receiver_id,
                ChatMessage.sender_id == sender_id,
                ChatMessage.status != MessageStatus.SEEN,
            )
        )
        ids = [row for row in result.scalars().all()]
        if ids:
            await self.db.execute(
                update(ChatMessage)
                .where(ChatMessage.id.in_(ids))
                .values(status=MessageStatus.SEEN)
            )
            await self.db.flush()
        return ids

    async def mark_delivered(self, message_ids: list[str]) -> None:
        if not message_ids:
            return
        await self.db.execute(
            update(ChatMessage)
            .where(
                ChatMessage.id.in_(message_ids),
                ChatMessage.status == MessageStatus.SENT,
            )
            .values(status=MessageStatus.DELIVERED)
        )
        await self.db.flush()

    async def soft_delete(self, msg_id: str) -> Optional[ChatMessage]:
        """Soft-delete a message by clearing its content."""
        result = await self.db.execute(
            select(ChatMessage).where(ChatMessage.id == msg_id)
        )
        msg = result.scalar_one_or_none()
        if not msg:
            return None
        msg.is_deleted = True
        msg.content = ""
        await self.db.flush()
        await self.db.refresh(msg)
        return msg

    async def edit_message(self, msg_id: str, new_content: str) -> Optional[ChatMessage]:
        result = await self.db.execute(
            select(ChatMessage).where(ChatMessage.id == msg_id)
        )
        msg = result.scalar_one_or_none()
        if not msg:
            return None
        msg.content = new_content
        msg.edited_at = datetime.now(timezone.utc)
        await self.db.flush()
        await self.db.refresh(msg)
        return msg
