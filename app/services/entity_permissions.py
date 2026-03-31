"""Entity permission service — ABAC management at book / shlok / meaning level.

Permission resolution order (most specific wins):
  meaning-level explicit > shlok-level explicit > book-level explicit

Permission levels:
  VIEW         — read-only access (can see content)
  REQUEST_EDIT — propose changes that go through approval workflow
  DIRECT_EDIT  — apply changes immediately without approval

Structural access:
  When a child entity (shlok / meaning) is shared, the system auto-creates
  structural (navigation-only) access rows on ancestor entities so the user
  can navigate to the content without seeing full content of sibling entities.
"""

from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.entity_permissions import EntityPermissionRepository
from app.repositories.books import BookRepository
from app.repositories.shloks import ShlokRepository
from app.models.entity_permission import EntityPermission
from app.models.user import User
from app.schemas.entity_permissions import (
    SetEntityPermissionRequest,
    EntityPermissionResponse,
)
from app.constants.enums import EntityType, PermissionLevel, Visibility
from app.exceptions.books import BookNotFoundException, BookForbiddenException
from app.exceptions.shloks import ShlokNotFoundException, ShlokForbiddenException
from app.exceptions.meanings import MeaningNotFoundException, MeaningForbiddenException


class EntityPermissionService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = EntityPermissionRepository(db)
        self.book_repo = BookRepository(db)
        self.shlok_repo = ShlokRepository(db)

    async def _get_username(self, user_id: str) -> str:
        result = await self.db.execute(
            select(User.username).where(User.id == user_id)
        )
        return result.scalar_one_or_none() or "Unknown"

    async def _assert_entity_owner(
        self, entity_type: EntityType, entity_id: str, caller_id: str
    ) -> None:
        if entity_type == EntityType.BOOK:
            book = await self.book_repo.get_by_id(entity_id)
            if not book:
                raise BookNotFoundException()
            if book.owner_id != caller_id:
                raise BookForbiddenException()
        elif entity_type == EntityType.SHLOK:
            shlok = await self.shlok_repo.get_by_id(entity_id)
            if not shlok:
                raise ShlokNotFoundException()
            if shlok.owner_id != caller_id:
                raise ShlokForbiddenException()
        elif entity_type == EntityType.MEANING:
            from app.models.meaning import Meaning
            result = await self.db.execute(
                select(Meaning).where(Meaning.id == entity_id)
            )
            meaning = result.scalar_one_or_none()
            if not meaning:
                raise MeaningNotFoundException()
            if meaning.author_id != caller_id:
                raise MeaningForbiddenException()

    def _to_response(
        self, perm: EntityPermission, username: str
    ) -> EntityPermissionResponse:
        return EntityPermissionResponse(
            id=perm.id,
            user_id=perm.user_id,
            username=username,
            entity_type=EntityType(perm.entity_type),
            entity_id=perm.entity_id,
            permission_level=perm.permission_level,
            is_structural=perm.is_structural,
            is_hidden=perm.is_hidden,
        )

    # ── Set permissions ───────────────────────────────────────────────────────

    async def set_permissions(
        self,
        entity_type: EntityType,
        entity_id: str,
        caller_id: str,
        data: SetEntityPermissionRequest,
    ) -> EntityPermissionResponse:
        await self._assert_entity_owner(entity_type, entity_id, caller_id)

        perm = EntityPermission(
            user_id=data.user_id,
            entity_type=entity_type.value,
            entity_id=entity_id,
            granted_by=caller_id,
            permission_level=data.permission_level.value,
            allowed_actions=[],  # legacy field maintained for schema compat
            is_structural=False,
            is_hidden=data.is_hidden,
        )
        saved = await self.repo.upsert(perm)

        # Auto-propagate view access to ancestor entities (updates visibility if private)
        await self._propagate_parent_access(data.user_id, entity_type, entity_id, caller_id)

        username = await self._get_username(data.user_id)
        return self._to_response(saved, username)

    async def _propagate_parent_access(
        self,
        user_id: str,
        entity_type: EntityType,
        entity_id: str,
        granted_by: str,
    ) -> None:
        """Walk up the hierarchy; ensure explicit view + update visibility if private on ancestors.

        For meanings this includes walking the meaning parent chain (parent_id)
        all the way to the root, then continuing to the shlok and book.
        """
        if entity_type == EntityType.MEANING:
            from app.models.meaning import Meaning

            # Walk meaning parent chain upward
            current_id = entity_id
            while True:
                result = await self.db.execute(
                    select(Meaning.parent_id, Meaning.shlok_id).where(Meaning.id == current_id)
                )
                row = result.one_or_none()
                if not row:
                    break
                parent_id, shlok_id = row.parent_id, row.shlok_id
                if parent_id:
                    await self._ensure_parent_meaning_access(
                        user_id, parent_id, granted_by
                    )
                    current_id = parent_id
                else:
                    break  # reached root meaning

            # Now propagate to shlok and book
            result2 = await self.db.execute(
                select(Meaning.shlok_id).where(Meaning.id == entity_id)
            )
            shlok_id = result2.scalar_one_or_none()
            if shlok_id:
                await self._ensure_parent_access(user_id, EntityType.SHLOK, shlok_id, granted_by)
                shlok = await self.shlok_repo.get_by_id(shlok_id)
                if shlok:
                    await self._ensure_parent_access(user_id, EntityType.BOOK, shlok.book_id, granted_by)

        elif entity_type == EntityType.SHLOK:
            shlok = await self.shlok_repo.get_by_id(entity_id)
            if shlok:
                await self._ensure_parent_access(user_id, EntityType.BOOK, shlok.book_id, granted_by)

    async def _ensure_parent_access(
        self,
        user_id: str,
        entity_type: EntityType,
        entity_id: str,
        granted_by: str,
    ) -> None:
        """On a parent entity: upgrade visibility from private→specific_users and ensure at least view.

        Rules:
        - If the parent entity is private, change it to specific_users.
        - If the user has no perm or only a structural perm, add an explicit view perm.
        - If the user already has request_edit or direct_edit, NEVER downgrade.
        """
        HIGHER = {PermissionLevel.REQUEST_EDIT.value, PermissionLevel.DIRECT_EDIT.value}
        existing = await self.repo.get(user_id, entity_type.value, entity_id)

        # 1. Update parent entity visibility from private → specific_users
        if entity_type == EntityType.BOOK:
            book = await self.book_repo.get_by_id(entity_id)
            if book and book.visibility == Visibility.PRIVATE:
                await self.book_repo.update(entity_id, visibility=Visibility.SPECIFIC_USERS.value)
        elif entity_type == EntityType.SHLOK:
            shlok = await self.shlok_repo.get_by_id(entity_id)
            if shlok and shlok.visibility == Visibility.PRIVATE:
                await self.shlok_repo.update(entity_id, visibility=Visibility.SPECIFIC_USERS.value)

        # 2. Don't downgrade existing explicit request_edit / direct_edit
        if existing and not existing.is_structural and existing.permission_level in HIGHER:
            return

        # 3. If no perm or only structural: add explicit view
        if not existing or existing.is_structural:
            perm = EntityPermission(
                user_id=user_id,
                entity_type=entity_type.value,
                entity_id=entity_id,
                granted_by=granted_by,
                permission_level=PermissionLevel.VIEW.value,
                allowed_actions=[],
                is_structural=False,
                is_hidden=False,
            )
            await self.repo.upsert(perm)

    async def _ensure_parent_meaning_access(
        self,
        user_id: str,
        meaning_id: str,
        granted_by: str,
    ) -> None:
        """Ensure user has at least view permission on a parent meaning.

        Same never-downgrade rule: if user already has request_edit or direct_edit, keep it.
        Also upgrades parent meaning visibility from private → specific_users.
        """
        from app.repositories.meanings import MeaningRepository

        HIGHER = {PermissionLevel.REQUEST_EDIT.value, PermissionLevel.DIRECT_EDIT.value}
        existing = await self.repo.get(user_id, EntityType.MEANING.value, meaning_id)

        # 1. Upgrade parent meaning visibility from private → specific_users
        meaning_repo = MeaningRepository(self.db)
        parent_meaning = await meaning_repo.get_by_id(meaning_id)
        if parent_meaning and getattr(parent_meaning, "visibility", "private") == Visibility.PRIVATE.value:
            await meaning_repo.update(meaning_id, visibility=Visibility.SPECIFIC_USERS.value)

        # 2. Don't downgrade existing explicit request_edit / direct_edit
        if existing and not existing.is_structural and existing.permission_level in HIGHER:
            return

        # 3. If no perm or only structural: add explicit view
        if not existing or existing.is_structural:
            perm = EntityPermission(
                user_id=user_id,
                entity_type=EntityType.MEANING.value,
                entity_id=meaning_id,
                granted_by=granted_by,
                permission_level=PermissionLevel.VIEW.value,
                allowed_actions=[],
                is_structural=False,
                is_hidden=False,
            )
            await self.repo.upsert(perm)

    # ── Get permissions ───────────────────────────────────────────────────────

    async def list_permissions(
        self,
        entity_type: EntityType,
        entity_id: str,
        caller_id: str,
    ) -> list[EntityPermissionResponse]:
        await self._assert_entity_owner(entity_type, entity_id, caller_id)
        perms = await self.repo.list_for_entity(entity_type, entity_id)
        result = []
        for p in perms:
            username = await self._get_username(p.user_id)
            result.append(self._to_response(p, username))
        return result

    # ── List what I have granted ──────────────────────────────────────────────

    async def list_granted_by_me(
        self, caller_id: str
    ) -> list[EntityPermissionResponse]:
        """Return all explicit permissions the caller has granted to other users."""
        perms = await self.repo.list_granted_by(caller_id)
        result = []
        for p in perms:
            username = await self._get_username(p.user_id)
            result.append(self._to_response(p, username))
        return result

    # ── Revoke ────────────────────────────────────────────────────────────────

    async def revoke(
        self,
        entity_type: EntityType,
        entity_id: str,
        target_user_id: str,
        caller_id: str,
    ) -> None:
        await self._assert_entity_owner(entity_type, entity_id, caller_id)
        await self.repo.delete_for_user(target_user_id, entity_type.value, entity_id)
        # Clean up orphaned structural access on ancestor entities
        await self._cleanup_structural_access(target_user_id, entity_type, entity_id)

    async def _cleanup_structural_access(
        self,
        user_id: str,
        revoked_type: EntityType,
        revoked_entity_id: str,
    ) -> None:
        """After revoking an explicit perm, remove orphaned structural ancestors."""
        if revoked_type == EntityType.MEANING:
            from app.models.meaning import Meaning
            result = await self.db.execute(
                select(Meaning.shlok_id).where(Meaning.id == revoked_entity_id)
            )
            shlok_id = result.scalar_one_or_none()
            if shlok_id:
                # Check if user still has any explicit meaning perms on this shlok
                all_perms = await self.repo.list_non_structural_for_user(user_id, EntityType.MEANING)
                from app.models.meaning import Meaning as MeaningModel
                still_has_shlok = False
                for p in all_perms:
                    r2 = await self.db.execute(
                        select(MeaningModel.shlok_id).where(MeaningModel.id == p.entity_id)
                    )
                    if r2.scalar_one_or_none() == shlok_id:
                        still_has_shlok = True
                        break
                if not still_has_shlok:
                    # Remove structural shlok access
                    shlok_perm = await self.repo.get(user_id, "shlok", shlok_id)
                    if shlok_perm and shlok_perm.is_structural:
                        await self.repo.delete_for_user(user_id, "shlok", shlok_id)
                    # Also check book
                    shlok = await self.shlok_repo.get_by_id(shlok_id)
                    if shlok:
                        await self._maybe_remove_structural_book(user_id, shlok.book_id)

        elif revoked_type == EntityType.SHLOK:
            shlok = await self.shlok_repo.get_by_id(revoked_entity_id)
            if shlok:
                await self._maybe_remove_structural_book(user_id, shlok.book_id)

    async def _maybe_remove_structural_book(self, user_id: str, book_id: str) -> None:
        """Remove structural book access if user has no remaining shlok/meaning perms on it."""
        # Check shlok-level explicit perms on this book
        shlok_perms = await self.repo.list_non_structural_for_user(user_id, EntityType.SHLOK)
        for sp in shlok_perms:
            s = await self.shlok_repo.get_by_id(sp.entity_id)
            if s and s.book_id == book_id:
                return  # still has access via shlok
        # Check meaning-level explicit perms on this book's shloks
        meaning_perms = await self.repo.list_non_structural_for_user(user_id, EntityType.MEANING)
        from app.models.meaning import Meaning
        for mp in meaning_perms:
            r = await self.db.execute(select(Meaning.shlok_id).where(Meaning.id == mp.entity_id))
            shlok_id = r.scalar_one_or_none()
            if shlok_id:
                s = await self.shlok_repo.get_by_id(shlok_id)
                if s and s.book_id == book_id:
                    return  # still has access via meaning→shlok→book
        # Safe to remove structural book access
        book_perm = await self.repo.get(user_id, "book", book_id)
        if book_perm and book_perm.is_structural:
            await self.repo.delete_for_user(user_id, "book", book_id)

    # ── Check permission ──────────────────────────────────────────────────────

    async def check_action(
        self,
        user_id: str,
        entity_type: EntityType,
        entity_id: str,
        action: str,
    ) -> bool:
        """Return True if the user has the given action allowed on the entity.

        Resolution order (most specific wins):
          1. Explicit meaning-level perm
          2. Explicit shlok-level perm
          3. Explicit book-level perm
          4. Default: deny

        Structural access only permits navigation (treated as view-level for the
        parent container, but callers should check the concrete entity level for
        editing actions).
        """
        perm = await self.repo.get(user_id, entity_type.value, entity_id)
        if perm:
            if perm.is_hidden:
                return False
            return self._action_allowed(perm.permission_level, perm.is_structural, action)

        # Walk up hierarchy to find inherited permission
        if entity_type == EntityType.MEANING:
            from app.models.meaning import Meaning
            result = await self.db.execute(
                select(Meaning.shlok_id).where(Meaning.id == entity_id)
            )
            shlok_id = result.scalar_one_or_none()
            if shlok_id:
                return await self.check_action(user_id, EntityType.SHLOK, shlok_id, action)

        if entity_type == EntityType.SHLOK:
            shlok = await self.shlok_repo.get_by_id(entity_id)
            if shlok:
                return await self.check_action(user_id, EntityType.BOOK, shlok.book_id, action)

        return False

    @staticmethod
    def _action_allowed(level: str, is_structural: bool, action: str) -> bool:
        """Determine if an action is permitted for a given permission level."""
        if is_structural:
            # Structural grants only navigation / title viewing
            return action == "view"
        if level == PermissionLevel.VIEW.value:
            return action == "view"
        if level == PermissionLevel.REQUEST_EDIT.value:
            return action in ("view", "request_edit")
        if level == PermissionLevel.DIRECT_EDIT.value:
            return action in ("view", "direct_edit", "add_shlok", "add_meaning", "edit")
        return False

