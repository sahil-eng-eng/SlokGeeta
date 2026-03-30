"""Group chat service — business logic."""

from datetime import datetime, timezone, timedelta
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.group import GroupRepository
from app.models.group import (
    GroupConversation,
    GroupMember,
    GroupMessage,
    GROUP_ROLE_OWNER,
    GROUP_ROLE_CO_ADMIN,
    GROUP_ROLE_MEMBER,
)
from app.models.user import User
from app.schemas.group import (
    CreateGroupRequest,
    UpdateGroupRequest,
    GroupMemberResponse,
    GroupResponse,
    GroupMessageResponse,
    SendGroupMessageRequest,
    EditGroupMessageRequest,
    AddGroupMembersRequest,
    UpdateMemberRoleRequest,
)
from app.core.ws_manager import ws_manager

# Users active in the last 5 minutes are considered "online"
_ONLINE_THRESHOLD = timedelta(minutes=5)


class GroupNotFoundException(Exception):
    pass


class GroupForbiddenException(Exception):
    pass


class GroupMessageNotFoundException(Exception):
    pass


class GroupMessageForbiddenException(Exception):
    pass


class GroupService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = GroupRepository(db)

    # ── Helpers ──────────────────────────────────────────────────────────────

    async def _get_user(self, user_id: str) -> Optional[User]:
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def _get_users_by_ids(self, user_ids: list[str]) -> dict[str, User]:
        result = await self.db.execute(select(User).where(User.id.in_(user_ids)))
        return {u.id: u for u in result.scalars().all()}

    def _is_online(self, user: User) -> bool:
        if not getattr(user, "last_seen_at", None):
            return False
        now = datetime.now(timezone.utc)
        last = user.last_seen_at
        if last.tzinfo is None:
            last = last.replace(tzinfo=timezone.utc)
        return (now - last) < _ONLINE_THRESHOLD

    def _member_to_response(self, member: GroupMember, user: Optional[User]) -> GroupMemberResponse:
        role = getattr(member, "role", GROUP_ROLE_MEMBER)
        last_seen = None
        if user and getattr(user, "last_seen_at", None):
            last_seen = user.last_seen_at.isoformat() if hasattr(user.last_seen_at, "isoformat") else str(user.last_seen_at)
        return GroupMemberResponse(
            user_id=member.user_id,
            username=user.username if user else member.user_id,
            display_name=user.full_name if user else None,
            avatar_url=getattr(user, "avatar_url", None) if user else None,
            role=role,
            is_admin=role in (GROUP_ROLE_OWNER, GROUP_ROLE_CO_ADMIN),
            is_online=self._is_online(user) if user else False,
            last_seen_at=last_seen,
        )

    async def _build_group_response(
        self, group: GroupConversation, caller_id: Optional[str] = None
    ) -> GroupResponse:
        raw_members = await self.repo.get_members(group.id)
        user_ids = [m.user_id for m in raw_members]
        users = await self._get_users_by_ids(user_ids)
        member_responses = [
            self._member_to_response(m, users.get(m.user_id)) for m in raw_members
        ]
        my_role: Optional[str] = None
        if caller_id:
            my = next((m for m in raw_members if m.user_id == caller_id), None)
            if my:
                my_role = getattr(my, "role", GROUP_ROLE_MEMBER)
        return GroupResponse(
            id=group.id,
            name=group.name,
            description=group.description,
            creator_id=group.creator_id,
            avatar_url=getattr(group, "avatar_url", None),
            member_count=len(raw_members),
            members=member_responses,
            created_at=group.created_at.isoformat(),
        )

    def _message_to_response(
        self, msg: GroupMessage, sender: Optional[User]
    ) -> GroupMessageResponse:
        return GroupMessageResponse(
            id=msg.id,
            group_id=msg.group_id,
            sender_id=msg.sender_id,
            sender_username=sender.username if sender else msg.sender_id,
            sender_display_name=sender.full_name if sender else None,
            content=msg.content,
            is_deleted=msg.is_deleted,
            edited_at=msg.edited_at,
            created_at=msg.created_at,
        )

    async def _assert_member(self, group_id: str, user_id: str) -> None:
        member = await self.repo.get_member(group_id, user_id)
        if not member:
            raise GroupForbiddenException()

    async def _assert_admin(self, group_id: str, user_id: str) -> None:
        member = await self.repo.get_member(group_id, user_id)
        if not member:
            raise GroupForbiddenException()
        role = getattr(member, "role", GROUP_ROLE_MEMBER)
        if role not in (GROUP_ROLE_OWNER, GROUP_ROLE_CO_ADMIN):
            raise GroupForbiddenException()

    # ── Groups ───────────────────────────────────────────────────────────────

    async def create_group(
        self, creator_id: str, data: CreateGroupRequest
    ) -> GroupResponse:
        group = GroupConversation(
            name=data.name,
            description=data.description,
            creator_id=creator_id,
        )
        group = await self.repo.create_group(group)

        # Creator is always the owner
        await self.repo.add_member(group.id, creator_id, is_admin=True, role=GROUP_ROLE_OWNER)

        # Add requested members
        existing_users = await self._get_users_by_ids(data.member_ids)
        for uid in data.member_ids:
            if uid != creator_id and uid in existing_users:
                await self.repo.add_member(group.id, uid, is_admin=False, role=GROUP_ROLE_MEMBER)

        await self.repo.commit()
        return await self._build_group_response(group, caller_id=creator_id)

    async def list_user_groups(self, user_id: str) -> list[GroupResponse]:
        groups = await self.repo.get_user_groups(user_id)
        result = []
        for g in groups:
            result.append(await self._build_group_response(g, caller_id=user_id))
        return result

    async def get_group(self, group_id: str, user_id: str) -> GroupResponse:
        group = await self.repo.get_group(group_id)
        if not group:
            raise GroupNotFoundException()
        await self._assert_member(group_id, user_id)
        return await self._build_group_response(group, caller_id=user_id)

    async def edit_group(
        self, group_id: str, caller_id: str, data: UpdateGroupRequest
    ) -> GroupResponse:
        group = await self.repo.get_group(group_id)
        if not group:
            raise GroupNotFoundException()
        await self._assert_admin(group_id, caller_id)
        await self.repo.update_group(
            group,
            name=data.name,
            description=data.description,
            avatar_url=data.avatar_url,
        )
        await self.repo.commit()
        response = await self._build_group_response(group, caller_id=caller_id)
        # Notify all members
        members = await self.repo.get_members(group_id)
        for m in members:
            await ws_manager.send_to_user(
                m.user_id,
                {"type": "group_updated", "group": response.model_dump(mode="json")},
            )
        return response

    async def add_members(
        self, group_id: str, requester_id: str, data: AddGroupMembersRequest
    ) -> GroupResponse:
        group = await self.repo.get_group(group_id)
        if not group:
            raise GroupNotFoundException()
        await self._assert_admin(group_id, requester_id)

        users = await self._get_users_by_ids(data.user_ids)
        added_ids: list[str] = []
        for uid in data.user_ids:
            if uid in users:
                existing = await self.repo.get_member(group_id, uid)
                if not existing:
                    await self.repo.add_member(group_id, uid, is_admin=False, role=GROUP_ROLE_MEMBER)
                    added_ids.append(uid)

        await self.repo.commit()
        response = await self._build_group_response(group, caller_id=requester_id)
        # Notify newly added members
        for uid in added_ids:
            await ws_manager.send_to_user(
                uid,
                {"type": "group_added", "group": response.model_dump(mode="json")},
            )
        return response

    async def update_member_role(
        self, group_id: str, caller_id: str, target_user_id: str, new_role: str
    ) -> GroupResponse:
        group = await self.repo.get_group(group_id)
        if not group:
            raise GroupNotFoundException()
        # Only owner can change roles
        caller = await self.repo.get_member(group_id, caller_id)
        if not caller or getattr(caller, "role", "") != GROUP_ROLE_OWNER:
            raise GroupForbiddenException()
        # Cannot change owner role
        if target_user_id == group.creator_id:
            raise GroupForbiddenException()
        await self.repo.update_member_role(group_id, target_user_id, new_role)
        await self.repo.commit()
        return await self._build_group_response(group, caller_id=caller_id)

    async def leave_group(self, group_id: str, user_id: str) -> None:
        group = await self.repo.get_group(group_id)
        if not group:
            raise GroupNotFoundException()
        await self._assert_member(group_id, user_id)
        await self.repo.remove_member(group_id, user_id)
        await self.repo.commit()
        # Broadcast to remaining members
        remaining = await self.repo.get_members(group_id)
        for m in remaining:
            await ws_manager.send_to_user(
                m.user_id,
                {"type": "group_left", "group_id": group_id, "user_id": user_id},
            )

    # ── Messages ─────────────────────────────────────────────────────────────

    async def send_message(
        self, group_id: str, sender_id: str, data: SendGroupMessageRequest
    ) -> GroupMessageResponse:
        group = await self.repo.get_group(group_id)
        if not group:
            raise GroupNotFoundException()
        await self._assert_member(group_id, sender_id)

        msg = GroupMessage(
            group_id=group_id,
            sender_id=sender_id,
            content=data.content,
        )
        created = await self.repo.create_message(msg)
        sender = await self._get_user(sender_id)
        response = self._message_to_response(created, sender)

        # Push to all other members in this group
        members = await self.repo.get_members(group_id)
        for member in members:
            if member.user_id != sender_id:
                await ws_manager.send_to_user(
                    member.user_id,
                    {"type": "group_message", "message": response.model_dump(mode="json")},
                )

        return response

    async def get_messages(
        self,
        group_id: str,
        user_id: str,
        limit: int = 50,
        before_id: Optional[str] = None,
    ) -> list[GroupMessageResponse]:
        group = await self.repo.get_group(group_id)
        if not group:
            raise GroupNotFoundException()
        await self._assert_member(group_id, user_id)

        messages = await self.repo.get_messages(group_id, limit, before_id)
        sender_ids = list({m.sender_id for m in messages})
        users = await self._get_users_by_ids(sender_ids)
        return [self._message_to_response(m, users.get(m.sender_id)) for m in messages]

    async def delete_message(
        self, group_id: str, message_id: str, caller_id: str
    ) -> GroupMessageResponse:
        group = await self.repo.get_group(group_id)
        if not group:
            raise GroupNotFoundException()
        await self._assert_member(group_id, caller_id)

        msg = await self.repo.get_message(message_id)
        if not msg or msg.group_id != group_id:
            raise GroupMessageNotFoundException()
        if msg.sender_id != caller_id:
            raise GroupMessageForbiddenException()

        updated = await self.repo.soft_delete_message(message_id)
        sender = await self._get_user(caller_id)
        response = self._message_to_response(updated, sender)

        members = await self.repo.get_members(group_id)
        for member in members:
            if member.user_id != caller_id:
                await ws_manager.send_to_user(
                    member.user_id,
                    {"type": "group_message_deleted", "message": response.model_dump(mode="json")},
                )

        return response

    async def edit_message(
        self, group_id: str, message_id: str, caller_id: str, data: EditGroupMessageRequest
    ) -> GroupMessageResponse:
        group = await self.repo.get_group(group_id)
        if not group:
            raise GroupNotFoundException()
        await self._assert_member(group_id, caller_id)

        msg = await self.repo.get_message(message_id)
        if not msg or msg.group_id != group_id:
            raise GroupMessageNotFoundException()
        if msg.sender_id != caller_id:
            raise GroupMessageForbiddenException()

        updated = await self.repo.edit_message(message_id, data.content)
        sender = await self._get_user(caller_id)
        response = self._message_to_response(updated, sender)

        members = await self.repo.get_members(group_id)
        for member in members:
            if member.user_id != caller_id:
                await ws_manager.send_to_user(
                    member.user_id,
                    {"type": "group_message_edited", "message": response.model_dump(mode="json")},
                )

        return response
