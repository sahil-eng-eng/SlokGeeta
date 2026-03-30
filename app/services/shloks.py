"""Shlok service — business logic for CRUD, audio upload, listing, cross-refs."""

from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.shloks import ShlokRepository
from app.models.shlok import Shlok, ShlokCrossReference
from app.schemas.shloks import (
    CreateShlokRequest,
    UpdateShlokRequest,
    ShlokResponse,
    ShlokListResponse,
    CrossReferenceRequest,
    CrossReferenceResponse,
)
from app.exceptions.shloks import ShlokNotFoundException, ShlokForbiddenException, ShlokCannotMakePrivateException
from app.constants.enums import Visibility, PermissionLevel, EntityType
from app.utils.pagination import encode_cursor


class ShlokService:
    def __init__(self, db: AsyncSession):
        self.repo = ShlokRepository(db)
        self.db = db

    async def create_shlok(
        self, owner_id: str, data: CreateShlokRequest
    ) -> ShlokResponse:
        from app.repositories.books import BookRepository

        book_repo = BookRepository(self.db)
        book = await book_repo.get_by_id(data.book_id)
        if not book:
            from app.exceptions.books import BookNotFoundException
            raise BookNotFoundException()
        if book.owner_id != owner_id:
            from app.repositories.entity_permissions import EntityPermissionRepository
            perm_repo = EntityPermissionRepository(self.db)
            perm = await perm_repo.get(owner_id, "book", book.id)
            if not (
                perm
                and not perm.is_hidden
                and not perm.is_structural
                and perm.permission_level == PermissionLevel.DIRECT_EDIT.value
            ):
                raise ShlokForbiddenException()

        shlok = Shlok(owner_id=owner_id, **data.model_dump())
        shlok = await self.repo.create(shlok)
        return ShlokResponse.model_validate(shlok)

    async def get_shlok(
        self, shlok_id: str, user_id: Optional[str] = None
    ) -> ShlokResponse:
        shlok = await self.repo.get_by_id(shlok_id)
        if not shlok:
            raise ShlokNotFoundException()
        await self._check_read_access(shlok, user_id)
        if user_id and shlok.owner_id != user_id:
            await self.repo.increment_view(shlok_id)
        response = ShlokResponse.model_validate(shlok)
        # Bug 2: Include viewer's permission level so the frontend can gate Edit buttons
        if user_id and shlok.owner_id != user_id:
            from app.repositories.entity_permissions import EntityPermissionRepository
            perm_repo = EntityPermissionRepository(self.db)
            perm = await perm_repo.get(user_id, "shlok", shlok_id)
            if perm and not perm.is_hidden and not perm.is_structural:
                response.my_permission = perm.permission_level
        return response

    async def update_shlok(
        self, shlok_id: str, user_id: str, data: UpdateShlokRequest
    ) -> ShlokResponse:
        shlok = await self.repo.get_by_id(shlok_id)
        if not shlok:
            raise ShlokNotFoundException()
        await self._check_write_access(shlok, user_id)
        updates = data.model_dump(exclude_unset=True)
        # Block changing to private when any meanings are still shared
        if updates.get("visibility") == "private":
            from app.repositories.meanings import MeaningRepository
            from app.repositories.entity_permissions import EntityPermissionRepository
            meaning_repo = MeaningRepository(self.db)
            perm_repo = EntityPermissionRepository(self.db)
            meaning_ids = await meaning_repo.get_all_ids_by_shlok(shlok_id)
            if meaning_ids and await perm_repo.has_active_permissions_for_any("meaning", meaning_ids):
                raise ShlokCannotMakePrivateException()
        if updates:
            shlok = await self.repo.update(shlok_id, **updates)
        return ShlokResponse.model_validate(shlok)

    async def delete_shlok(self, shlok_id: str, user_id: str) -> None:
        shlok = await self.repo.get_by_id(shlok_id)
        if not shlok:
            raise ShlokNotFoundException()
        if shlok.owner_id != user_id:
            raise ShlokForbiddenException()
        await self.repo.delete(shlok_id)

    async def upload_audio(
        self,
        shlok_id: str,
        user_id: str,
        file_bytes: bytes,
        content_type: str,
        ext: str,
    ) -> ShlokResponse:
        shlok = await self.repo.get_by_id(shlok_id)
        if not shlok:
            raise ShlokNotFoundException()
        await self._check_write_access(shlok, user_id)
        from app.utils.supabase import upload_file

        path = f"{user_id}/{shlok_id}/audio.{ext}"
        url = await upload_file(
            "shlok-audio", path, file_bytes, content_type
        )
        shlok = await self.repo.update(shlok_id, audio_url=url)
        return ShlokResponse.model_validate(shlok)

    async def list_by_book(
        self,
        book_id: str,
        user_id: Optional[str],
        cursor: Optional[str] = None,
        limit: int = 20,
    ) -> ShlokListResponse:
        from app.services.books import BookService

        book_svc = BookService(self.db)
        book = await book_svc.get_book(book_id, user_id)

        # Non-owners only see public shloks + shloks they have explicit access to.
        # (Structural shlok access — granted when a meaning is shared — also gives
        # visibility so the user can navigate to the specific meaning.)
        if user_id and book.owner_id != user_id:
            from app.repositories.entity_permissions import EntityPermissionRepository
            perm_repo = EntityPermissionRepository(self.db)
            explicit_ids, structural_ids = await perm_repo.list_visible_shlok_ids_in_book(
                user_id, book_id
            )
            shloks = await self.repo.list_by_book_for_nonowner(
                book_id, explicit_ids, structural_ids, cursor, limit
            )
        else:
            shloks = await self.repo.list_by_book(book_id, cursor, limit)
        has_more = len(shloks) > limit
        items = shloks[:limit]
        next_cursor = (
            encode_cursor(items[-1].created_at, items[-1].id)
            if has_more and items
            else None
        )
        return ShlokListResponse(
            items=[ShlokResponse.model_validate(s) for s in items],
            next_cursor=next_cursor,
            has_more=has_more,
        )

    async def get_related(
        self, shlok_id: str, limit: int = 10
    ) -> list[ShlokResponse]:
        shlok = await self.repo.get_by_id(shlok_id)
        if not shlok:
            raise ShlokNotFoundException()
        related = await self.repo.get_related_shloks(shlok, limit)
        return [ShlokResponse.model_validate(s) for s in related]

    async def add_cross_reference(
        self,
        shlok_id: str,
        user_id: str,
        data: CrossReferenceRequest,
    ) -> CrossReferenceResponse:
        shlok = await self.repo.get_by_id(shlok_id)
        if not shlok:
            raise ShlokNotFoundException()
        await self._check_write_access(shlok, user_id)
        ref = ShlokCrossReference(
            source_shlok_id=shlok_id,
            target_shlok_id=data.target_shlok_id,
            note=data.note,
        )
        ref = await self.repo.add_cross_reference(ref)
        return CrossReferenceResponse.model_validate(ref)

    async def get_cross_references(
        self, shlok_id: str
    ) -> list[CrossReferenceResponse]:
        refs = await self.repo.get_cross_references(shlok_id)
        return [CrossReferenceResponse.model_validate(r) for r in refs]

    async def _check_read_access(
        self, shlok: Shlok, user_id: Optional[str]
    ) -> None:
        if shlok.visibility == Visibility.PUBLIC:
            return
        if user_id and shlok.owner_id == user_id:
            return
        if user_id:
            # Bug 1 fix: check entity-permission table, but respect visibility.
            # - structural row: navigation access granted when a child meaning was shared
            #   → allowed regardless of shlok visibility (user navigates to their meaning)
            # - explicit (non-structural) row: only honoured when visibility = 'specific_users'
            #   → if owner changed shlok back to 'private', explicit rows are bypassed
            from app.repositories.entity_permissions import EntityPermissionRepository
            perm_repo = EntityPermissionRepository(self.db)
            perm = await perm_repo.get(user_id, "shlok", shlok.id)
            if perm and not perm.is_hidden:
                if perm.is_structural:
                    # Always allow: user is navigating to a shared child meaning
                    return
                if shlok.visibility == Visibility.SPECIFIC_USERS:
                    # Explicit share + shlok is shared with specific users
                    return
        raise ShlokForbiddenException()

    async def _check_write_access(
        self, shlok: Shlok, user_id: str
    ) -> None:
        if shlok.owner_id == user_id:
            return
        from app.repositories.entity_permissions import EntityPermissionRepository
        perm_repo = EntityPermissionRepository(self.db)
        perm = await perm_repo.get(user_id, "shlok", shlok.id)
        if (
            perm
            and not perm.is_hidden
            and not perm.is_structural
            and perm.permission_level == PermissionLevel.DIRECT_EDIT.value
        ):
            return
        raise ShlokForbiddenException()
