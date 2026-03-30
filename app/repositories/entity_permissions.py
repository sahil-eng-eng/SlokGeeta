"""Entity permission repository — ABAC data access."""

from typing import Optional
from sqlalchemy import select, update, delete, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.entity_permission import EntityPermission
from app.constants.enums import EntityType, PermissionLevel


class EntityPermissionRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def upsert(self, perm: EntityPermission) -> EntityPermission:
        """Create or replace permissions for a user on an entity.

        If a structural row exists and the new perm is non-structural, the
        structural row is promoted to the explicit level (never demote explicit
        to structural via upsert).
        """
        existing = await self.get(perm.user_id, perm.entity_type, perm.entity_id)
        if existing:
            # Never overwrite an explicit perm with a structural placeholder
            if perm.is_structural and not existing.is_structural:
                return existing
            await self.db.execute(
                update(EntityPermission)
                .where(EntityPermission.id == existing.id)
                .values(
                    permission_level=perm.permission_level,
                    allowed_actions=perm.allowed_actions,
                    is_structural=perm.is_structural,
                    is_hidden=perm.is_hidden,
                    granted_by=perm.granted_by,
                )
            )
            await self.db.flush()
            return await self.get(perm.user_id, perm.entity_type, perm.entity_id)  # type: ignore
        self.db.add(perm)
        await self.db.flush()
        await self.db.refresh(perm)
        return perm

    async def ensure_structural_access(
        self,
        user_id: str,
        entity_type: EntityType,
        entity_id: str,
        granted_by: str,
    ) -> None:
        """Create a structural (navigation-only) access row if none exists.
        Skipped if the user already has an explicit non-structural permission."""
        existing = await self.get(user_id, entity_type.value, entity_id)
        if existing:
            return  # explicit perm already covers this; do not downgrade
        perm = EntityPermission(
            user_id=user_id,
            entity_type=entity_type.value,
            entity_id=entity_id,
            granted_by=granted_by,
            permission_level=PermissionLevel.VIEW.value,
            allowed_actions=[],
            is_structural=True,
            is_hidden=False,
        )
        self.db.add(perm)
        await self.db.flush()

    async def get(
        self, user_id: str, entity_type: str, entity_id: str
    ) -> Optional[EntityPermission]:
        result = await self.db.execute(
            select(EntityPermission).where(
                EntityPermission.user_id == user_id,
                EntityPermission.entity_type == entity_type,
                EntityPermission.entity_id == entity_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_for_entity(
        self, entity_type: EntityType, entity_id: str
    ) -> list[EntityPermission]:
        """Return only explicit (non-structural) permissions for an entity."""
        result = await self.db.execute(
            select(EntityPermission).where(
                EntityPermission.entity_type == entity_type.value,
                EntityPermission.entity_id == entity_id,
                EntityPermission.is_structural == False,  # noqa: E712
            )
        )
        return list(result.scalars().all())

    async def list_granted_by(self, granter_id: str) -> list[EntityPermission]:
        """Return all explicit permissions granted by a specific user."""
        result = await self.db.execute(
            select(EntityPermission).where(
                EntityPermission.granted_by == granter_id,
                EntityPermission.is_structural == False,  # noqa: E712
            )
        )
        return list(result.scalars().all())

    async def delete_for_user(
        self, user_id: str, entity_type: str, entity_id: str
    ) -> None:
        await self.db.execute(
            delete(EntityPermission).where(
                EntityPermission.user_id == user_id,
                EntityPermission.entity_type == entity_type,
                EntityPermission.entity_id == entity_id,
            )
        )
        await self.db.flush()

    async def list_non_structural_for_user(
        self, user_id: str, entity_type: EntityType
    ) -> list[EntityPermission]:
        """Return all explicit (non-structural) permissions for a user's entity type."""
        result = await self.db.execute(
            select(EntityPermission).where(
                EntityPermission.user_id == user_id,
                EntityPermission.entity_type == entity_type.value,
                EntityPermission.is_structural == False,  # noqa: E712
            )
        )
        return list(result.scalars().all())

    async def list_entity_ids_for_user(
        self, user_id: str, entity_type: EntityType
    ) -> list[str]:
        """Return entity_ids where the user has an explicit non-structural permission."""
        result = await self.db.execute(
            select(EntityPermission.entity_id).where(
                EntityPermission.user_id == user_id,
                EntityPermission.entity_type == entity_type.value,
                EntityPermission.is_structural == False,  # noqa: E712
                EntityPermission.is_hidden == False,  # noqa: E712
            )
        )
        return list(result.scalars().all())

    async def list_visible_shlok_ids_in_book(
        self, user_id: str, book_id: str
    ) -> tuple[list[str], list[str]]:
        """Return (explicit_ids, structural_ids) for a user's shlok access within a book.

        explicit_ids  – shloks the user was explicitly granted non-structural access to.
                        Only counted when shlok.visibility == 'specific_users'.
        structural_ids – shloks the user has structural (navigation-only) access to
                         because a child meaning was shared with them.  These are shown
                         even if shlok.visibility == 'private' so the user can navigate.
        """
        from app.models.shlok import Shlok
        book_shlok_ids_sq = (
            select(Shlok.id).where(Shlok.book_id == book_id)
        ).scalar_subquery()

        result_explicit = await self.db.execute(
            select(EntityPermission.entity_id).where(
                EntityPermission.user_id == user_id,
                EntityPermission.entity_type == "shlok",
                EntityPermission.is_hidden == False,  # noqa: E712
                EntityPermission.is_structural == False,  # noqa: E712
                EntityPermission.entity_id.in_(book_shlok_ids_sq),
            )
        )
        explicit_ids = list(result_explicit.scalars().all())

        result_structural = await self.db.execute(
            select(EntityPermission.entity_id).where(
                EntityPermission.user_id == user_id,
                EntityPermission.entity_type == "shlok",
                EntityPermission.is_hidden == False,  # noqa: E712
                EntityPermission.is_structural == True,  # noqa: E712
                EntityPermission.entity_id.in_(book_shlok_ids_sq),
            )
        )
        structural_ids = list(result_structural.scalars().all())
        return explicit_ids, structural_ids

    async def has_active_permissions_for_any(
        self, entity_type: str, entity_ids: list[str]
    ) -> bool:
        """Return True if any entity in entity_ids has at least one active
        (non-structural, non-hidden) permission row."""
        if not entity_ids:
            return False
        result = await self.db.execute(
            select(EntityPermission.id).where(
                EntityPermission.entity_type == entity_type,
                EntityPermission.entity_id.in_(entity_ids),
                EntityPermission.is_structural == False,  # noqa: E712
                EntityPermission.is_hidden == False,  # noqa: E712
            ).limit(1)
        )
        return result.scalar_one_or_none() is not None
