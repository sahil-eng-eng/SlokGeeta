"""Chat service — business logic for real-time messaging."""

from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.chat import ChatRepository
from app.repositories.friends import FriendRequestRepository
from app.models.chat_message import ChatMessage
from app.models.user import User
from app.schemas.chat import (
    MessageResponse,
    MessageListResponse,
    ConversationPreview,
)
from app.constants.enums import MessageStatus
from app.exceptions.chat import NotFriendsException, MessageNotFoundException, MessageForbiddenException
from app.core.ws_manager import ws_manager


class ChatService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = ChatRepository(db)
        self.friend_repo = FriendRequestRepository(db)

    def _to_response(self, msg: ChatMessage) -> MessageResponse:
        return MessageResponse(
            id=msg.id,
            sender_id=msg.sender_id,
            receiver_id=msg.receiver_id,
            content=msg.content,
            status=MessageStatus(msg.status),
            created_at=msg.created_at,
            is_deleted=msg.is_deleted,
            edited_at=msg.edited_at,
        )

    async def _assert_friends(self, user_a: str, user_b: str) -> None:
        if not await self.friend_repo.are_friends(user_a, user_b):
            raise NotFriendsException()

    # ── Send message ─────────────────────────────────────────────────────────

    async def send_message(
        self, sender_id: str, receiver_id: str, content: str
    ) -> MessageResponse:
        await self._assert_friends(sender_id, receiver_id)

        msg = ChatMessage(
            sender_id=sender_id,
            receiver_id=receiver_id,
            content=content,
            status=MessageStatus.SENT,
        )
        created = await self.repo.create(msg)
        response = self._to_response(created)

        # Push real-time delivery to receiver if online
        if ws_manager.is_online(receiver_id):
            await ws_manager.send_to_user(
                receiver_id,
                {"type": "new_message", "message": response.model_dump(mode="json")},
            )
            # Mark as delivered immediately
            await self.repo.mark_delivered([created.id])
            response.status = MessageStatus.DELIVERED

        return response

    # ── Load history ─────────────────────────────────────────────────────────

    async def get_conversation(
        self,
        user_a: str,
        user_b: str,
        limit: int = 50,
        before_id: Optional[str] = None,
    ) -> MessageListResponse:
        await self._assert_friends(user_a, user_b)

        messages = await self.repo.get_conversation(user_a, user_b, limit, before_id)
        has_more = len(messages) > limit
        if has_more:
            messages = messages[:limit]

        # Return in chronological order (oldest first for display)
        messages.reverse()

        next_cursor = messages[0].id if has_more and messages else None
        return MessageListResponse(
            items=[self._to_response(m) for m in messages],
            has_more=has_more,
            next_cursor=next_cursor,
        )

    # ── Conversations list ────────────────────────────────────────────────────

    async def list_conversations(self, user_id: str) -> list[ConversationPreview]:
        latest_msgs = await self.repo.get_recent_conversations(user_id)
        previews: list[ConversationPreview] = []

        for msg in latest_msgs:
            friend_id = msg.receiver_id if msg.sender_id == user_id else msg.sender_id
            user_result = await self.db.execute(
                select(User.username, User.avatar_url).where(User.id == friend_id)
            )
            row = user_result.one_or_none()
            username = row.username if row else "Unknown"
            avatar = row.avatar_url if row else None
            unread = await self.repo.count_unread(user_id, friend_id)

            previews.append(
                ConversationPreview(
                    friend_id=friend_id,
                    friend_username=username,
                    friend_avatar=avatar,
                    last_message=msg.content,
                    last_message_at=msg.created_at,
                    unread_count=unread,
                )
            )
        return previews

    # ── Mark seen ────────────────────────────────────────────────────────────

    async def mark_conversation_seen(
        self, receiver_id: str, sender_id: str
    ) -> None:
        seen_ids = await self.repo.mark_seen(receiver_id, sender_id)
        if seen_ids and ws_manager.is_online(sender_id):
            for msg_id in seen_ids:
                await ws_manager.send_to_user(
                    sender_id,
                    {
                        "type": "status_update",
                        "message_id": msg_id,
                        "status": MessageStatus.SEEN.value,
                    },
                )

    # ── Delete message ────────────────────────────────────────────────────────

    async def delete_message(self, message_id: str, caller_id: str) -> MessageResponse:
        msg = await self.repo.get_by_id(message_id)
        if not msg:
            raise MessageNotFoundException()
        if msg.sender_id != caller_id:
            raise MessageForbiddenException()
        updated = await self.repo.soft_delete(message_id)
        response = self._to_response(updated)  # type: ignore
        partner_id = msg.receiver_id
        if ws_manager.is_online(partner_id):
            await ws_manager.send_to_user(
                partner_id,
                {"type": "message_deleted", "message_id": message_id},
            )
        return response

    # ── Edit message ──────────────────────────────────────────────────────────

    async def edit_message(self, message_id: str, caller_id: str, new_content: str) -> MessageResponse:
        msg = await self.repo.get_by_id(message_id)
        if not msg:
            raise MessageNotFoundException()
        if msg.sender_id != caller_id:
            raise MessageForbiddenException()
        updated = await self.repo.edit_message(message_id, new_content)
        response = self._to_response(updated)  # type: ignore
        partner_id = msg.receiver_id
        if ws_manager.is_online(partner_id):
            await ws_manager.send_to_user(
                partner_id,
                {"type": "message_edited", "message": response.model_dump(mode="json")},
            )
        return response
