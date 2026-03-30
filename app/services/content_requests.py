"""Content request service — change-request / approval workflow."""

from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.content_requests import ContentRequestRepository
from app.repositories.books import BookRepository
from app.repositories.shloks import ShlokRepository
from app.repositories.meanings import MeaningRepository
from app.models.content_request import ContentRequest
from app.models.user import User
from app.schemas.content_requests import (
    CreateContentRequestRequest,
    ReviewContentRequestRequest,
    ContentRequestResponse,
    ContentRequestListResponse,
)
from app.constants.enums import EntityType, ContentRequestStatus
from app.exceptions.content_requests import (
    ContentRequestNotFoundException,
    ContentRequestForbiddenException,
)
from app.exceptions.books import BookNotFoundException
from app.exceptions.shloks import ShlokNotFoundException
from app.exceptions.meanings import MeaningNotFoundException


class ContentRequestService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = ContentRequestRepository(db)
        self.book_repo = BookRepository(db)
        self.shlok_repo = ShlokRepository(db)
        self.meaning_repo = MeaningRepository(db)

    async def _get_username(self, user_id: str) -> str:
        result = await self.db.execute(
            select(User.username).where(User.id == user_id)
        )
        return result.scalar_one_or_none() or "Unknown"

    async def _resolve_owner(self, entity_type: EntityType, entity_id: str) -> str:
        """Return the owner_id of the given entity."""
        if entity_type == EntityType.BOOK:
            entity = await self.book_repo.get_by_id(entity_id)
            if not entity:
                raise BookNotFoundException()
            return entity.owner_id
        if entity_type == EntityType.SHLOK:
            entity = await self.shlok_repo.get_by_id(entity_id)
            if not entity:
                raise ShlokNotFoundException()
            return entity.owner_id
        if entity_type == EntityType.MEANING:
            entity = await self.meaning_repo.get_by_id(entity_id)
            if not entity:
                raise MeaningNotFoundException()
            return entity.author_id
        raise ValueError(f"Unknown entity type: {entity_type}")

    def _to_response(
        self,
        req: ContentRequest,
        requester_username: str,
        context_breadcrumb: list[str] | None = None,
        current_content: str | None = None,
    ) -> ContentRequestResponse:
        return ContentRequestResponse(
            id=req.id,
            requester_id=req.requester_id,
            requester_username=requester_username,
            entity_type=EntityType(req.entity_type),
            entity_id=req.entity_id,
            action=req.action,
            proposed_content=req.proposed_content,
            status=ContentRequestStatus(req.status),
            reviewer_id=req.reviewer_id,
            reviewer_note=req.reviewer_note,
            created_at=req.created_at,
            context_breadcrumb=context_breadcrumb,
            current_content=current_content,
        )

    async def _build_context(
        self, req: ContentRequest
    ) -> tuple[list[str] | None, str | None]:
        """Build a context breadcrumb and current content snippet for a request."""
        entity_type = EntityType(req.entity_type)
        breadcrumb: list[str] = []
        current_content: str | None = None
        try:
            if entity_type == EntityType.MEANING:
                meaning = await self.meaning_repo.get_by_id(req.entity_id)
                if meaning:
                    snippet = (meaning.content or "")[:80]
                    if len(meaning.content or "") > 80:
                        snippet += "…"
                    current_content = meaning.content
                    breadcrumb.append(f"Meaning: {snippet}")
                    shlok = await self.shlok_repo.get_by_id(meaning.shlok_id)
                    if shlok:
                        s_snip = (shlok.content or "")[:60]
                        if len(shlok.content or "") > 60:
                            s_snip += "…"
                        breadcrumb.insert(0, f"Shlok: {s_snip}")
                        book = await self.book_repo.get_by_id(shlok.book_id)
                        if book:
                            breadcrumb.insert(0, f"Book: {book.title}")
            elif entity_type == EntityType.SHLOK:
                shlok = await self.shlok_repo.get_by_id(req.entity_id)
                if shlok:
                    s_snip = (shlok.content or "")[:80]
                    if len(shlok.content or "") > 80:
                        s_snip += "…"
                    current_content = shlok.content
                    breadcrumb.append(f"Shlok: {s_snip}")
                    book = await self.book_repo.get_by_id(shlok.book_id)
                    if book:
                        breadcrumb.insert(0, f"Book: {book.title}")
            elif entity_type == EntityType.BOOK:
                book = await self.book_repo.get_by_id(req.entity_id)
                if book:
                    current_content = book.title
                    breadcrumb.append(f"Book: {book.title}")
        except Exception:
            pass
        return breadcrumb or None, current_content

    # ── Create ────────────────────────────────────────────────────────────────

    async def create(
        self, requester_id: str, data: CreateContentRequestRequest
    ) -> ContentRequestResponse:
        owner_id = await self._resolve_owner(data.entity_type, data.entity_id)

        req = ContentRequest(
            requester_id=requester_id,
            entity_type=data.entity_type.value,
            entity_id=data.entity_id,
            action=data.action.value,
            entity_owner_id=owner_id,
            proposed_content=data.proposed_content,
        )
        created = await self.repo.create(req)
        username = await self._get_username(requester_id)
        return self._to_response(created, username)

    # ── List ──────────────────────────────────────────────────────────────────

    async def list_incoming(
        self,
        owner_id: str,
        status: Optional[ContentRequestStatus] = None,
    ) -> ContentRequestListResponse:
        requests = await self.repo.list_incoming(owner_id, status)
        items = []
        for r in requests:
            username = await self._get_username(r.requester_id)
            breadcrumb, current_content = await self._build_context(r)
            items.append(self._to_response(r, username, breadcrumb, current_content))
        return ContentRequestListResponse(items=items, total=len(items))

    async def list_outgoing(
        self,
        requester_id: str,
        status: Optional[ContentRequestStatus] = None,
    ) -> ContentRequestListResponse:
        requests = await self.repo.list_outgoing(requester_id, status)
        items = []
        for r in requests:
            username = await self._get_username(r.requester_id)
            breadcrumb, current_content = await self._build_context(r)
            items.append(self._to_response(r, username, breadcrumb, current_content))
        return ContentRequestListResponse(items=items, total=len(items))

    # ── Review ────────────────────────────────────────────────────────────────

    async def review(
        self,
        req_id: str,
        reviewer_id: str,
        data: ReviewContentRequestRequest,
    ) -> ContentRequestResponse:
        req = await self.repo.get_by_id(req_id)
        if not req:
            raise ContentRequestNotFoundException()
        if req.entity_owner_id != reviewer_id:
            raise ContentRequestForbiddenException()

        updated = await self.repo.review(
            req_id, reviewer_id, data.status, data.reviewer_note
        )
        username = await self._get_username(updated.requester_id)  # type: ignore
        return self._to_response(updated, username)  # type: ignore

    async def count_pending(self, owner_id: str) -> int:
        return await self.repo.count_incoming_pending(owner_id)
