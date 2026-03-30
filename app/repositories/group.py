"""Group chat repository — CRUD operations for groups, members, messages."""

from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.group import GroupConversation, GroupMember, GroupMessage


class GroupRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ── Groups ───────────────────────────────────────────────────────────────

    async def create_group(self, group: GroupConversation) -> GroupConversation:
        self.db.add(group)
        await self.db.flush()  # get id before adding members
        return group

    async def get_group(self, group_id: str) -> Optional[GroupConversation]:
        result = await self.db.execute(
            select(GroupConversation).where(GroupConversation.id == group_id)
        )
        return result.scalar_one_or_none()

    async def get_user_groups(self, user_id: str) -> list[GroupConversation]:
        result = await self.db.execute(
            select(GroupConversation)
            .join(GroupMember, GroupMember.group_id == GroupConversation.id)
            .where(GroupMember.user_id == user_id)
            .order_by(GroupConversation.created_at.desc())
        )
        return list(result.scalars().all())

    # ── Members ──────────────────────────────────────────────────────────────

    async def update_group(
        self,
        group: GroupConversation,
        name: str | None = None,
        description: str | None = None,
        avatar_url: str | None = None,
    ) -> GroupConversation:
        if name is not None:
            group.name = name
        if description is not None:
            group.description = description
        if avatar_url is not None:
            group.avatar_url = avatar_url
        return group

    async def add_member(
        self, group_id: str, user_id: str, is_admin: bool = False, role: str = "member"
    ) -> GroupMember:
        member = GroupMember(group_id=group_id, user_id=user_id, is_admin=is_admin, role=role)
        self.db.add(member)
        return member

    async def update_member_role(self, group_id: str, user_id: str, role: str) -> Optional[GroupMember]:
        member = await self.get_member(group_id, user_id)
        if not member:
            return None
        member.role = role
        member.is_admin = role in ("owner", "co_admin")
        return member

    async def remove_member(self, group_id: str, user_id: str) -> None:
        await self.db.execute(
            delete(GroupMember).where(
                GroupMember.group_id == group_id,
                GroupMember.user_id == user_id,
            )
        )

    async def get_members(self, group_id: str) -> list[GroupMember]:
        result = await self.db.execute(
            select(GroupMember).where(GroupMember.group_id == group_id)
        )
        return list(result.scalars().all())

    async def get_member(self, group_id: str, user_id: str) -> Optional[GroupMember]:
        result = await self.db.execute(
            select(GroupMember).where(
                GroupMember.group_id == group_id,
                GroupMember.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def count_members(self, group_id: str) -> int:
        members = await self.get_members(group_id)
        return len(members)

    # ── Messages ─────────────────────────────────────────────────────────────

    async def create_message(self, message: GroupMessage) -> GroupMessage:
        self.db.add(message)
        await self.db.commit()
        await self.db.refresh(message)
        return message

    async def get_messages(
        self,
        group_id: str,
        limit: int = 50,
        before_id: Optional[str] = None,
    ) -> list[GroupMessage]:
        query = (
            select(GroupMessage)
            .where(GroupMessage.group_id == group_id)
            .order_by(GroupMessage.created_at.desc())
            .limit(limit)
        )
        if before_id:
            pivot = await self.db.execute(
                select(GroupMessage).where(GroupMessage.id == before_id)
            )
            pivot_msg = pivot.scalar_one_or_none()
            if pivot_msg:
                query = query.where(GroupMessage.created_at < pivot_msg.created_at)
        result = await self.db.execute(query)
        return list(reversed(result.scalars().all()))

    async def get_message(self, message_id: str) -> Optional[GroupMessage]:
        result = await self.db.execute(
            select(GroupMessage).where(GroupMessage.id == message_id)
        )
        return result.scalar_one_or_none()

    async def soft_delete_message(self, message_id: str) -> Optional[GroupMessage]:
        msg = await self.get_message(message_id)
        if not msg:
            return None
        msg.is_deleted = True
        msg.content = ""
        await self.db.commit()
        await self.db.refresh(msg)
        return msg

    async def edit_message(self, message_id: str, new_content: str) -> Optional[GroupMessage]:
        msg = await self.get_message(message_id)
        if not msg:
            return None
        msg.content = new_content
        msg.edited_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(msg)
        return msg

    async def commit(self) -> None:
        await self.db.commit()
