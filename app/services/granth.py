"""Granth service — business logic for granth operations."""

from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.granth import GranthRepository
from app.models.granth import Granth, GranthPage
from app.schemas.granth import (
    CreateGranthRequest,
    UpdateGranthRequest,
    GranthResponse,
    GranthPageResponse,
    UpdateGranthPageRequest,
    UpdateProgressRequest,
    ProgressResponse,
)
from app.exceptions.base import NotFoundException


class GranthService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = GranthRepository(db)

    def _to_response(self, g: Granth) -> GranthResponse:
        return GranthResponse.model_validate(g)

    def _page_to_response(self, p: GranthPage) -> GranthPageResponse:
        return GranthPageResponse.model_validate(p)

    async def create_granth(
        self, uploaded_by: str, data: CreateGranthRequest
    ) -> GranthResponse:
        granth = Granth(
            title=data.title,
            description=data.description,
            author=data.author,
            language=data.language,
            uploaded_by=uploaded_by,
        )
        created = await self.repo.create(granth)
        return self._to_response(created)

    async def get_granth(self, granth_id: str) -> GranthResponse:
        granth = await self.repo.get_by_id(granth_id)
        if not granth:
            raise NotFoundException("Granth not found")
        return self._to_response(granth)

    async def list_granths(self, published_only: bool = False) -> list[GranthResponse]:
        granths = await self.repo.list_all(published_only)
        return [self._to_response(g) for g in granths]

    async def update_granth(
        self, granth_id: str, data: UpdateGranthRequest
    ) -> GranthResponse:
        granth = await self.repo.get_by_id(granth_id)
        if not granth:
            raise NotFoundException("Granth not found")
        if data.title is not None:
            granth.title = data.title
        if data.description is not None:
            granth.description = data.description
        if data.author is not None:
            granth.author = data.author
        if data.language is not None:
            granth.language = data.language
        if data.is_published is not None:
            granth.is_published = data.is_published
        updated = await self.repo.update(granth)
        return self._to_response(updated)

    async def delete_granth(self, granth_id: str) -> None:
        granth = await self.repo.get_by_id(granth_id)
        if not granth:
            raise NotFoundException("Granth not found")
        await self.repo.delete(granth)

    # ── Pages ─────────────────────────────────────────────────────────────────

    async def add_page(
        self, granth_id: str, page_number: int, content: str, image_url: str | None = None
    ) -> GranthPageResponse:
        granth = await self.repo.get_by_id(granth_id)
        if not granth:
            raise NotFoundException("Granth not found")
        page = GranthPage(
            granth_id=granth_id,
            page_number=page_number,
            content=content,
            image_url=image_url,
        )
        created = await self.repo.create_page(page)

        # Update total pages count
        count = await self.repo.count_pages(granth_id)
        granth.total_pages = count
        await self.repo.update(granth)

        return self._page_to_response(created)

    async def get_page(self, granth_id: str, page_number: int) -> GranthPageResponse:
        page = await self.repo.get_page(granth_id, page_number)
        if not page:
            raise NotFoundException("Page not found")
        return self._page_to_response(page)

    async def get_pages(self, granth_id: str) -> list[GranthPageResponse]:
        pages = await self.repo.get_pages(granth_id)
        return [self._page_to_response(p) for p in pages]

    async def update_page(
        self, granth_id: str, page_number: int, data: UpdateGranthPageRequest
    ) -> GranthPageResponse:
        page = await self.repo.get_page(granth_id, page_number)
        if not page:
            raise NotFoundException("Page not found")
        if data.content is not None:
            page.content = data.content
        updated = await self.repo.update_page(page)
        return self._page_to_response(updated)

    async def delete_page(self, granth_id: str, page_number: int) -> None:
        page = await self.repo.get_page(granth_id, page_number)
        if not page:
            raise NotFoundException("Page not found")
        await self.repo.delete_page(page)
        # Update total_pages count
        granth = await self.repo.get_by_id(granth_id)
        if granth:
            count = await self.repo.count_pages(granth_id)
            granth.total_pages = count
            await self.repo.update(granth)

    # ── Progress ──────────────────────────────────────────────────────────────

    async def get_progress(self, user_id: str, granth_id: str) -> ProgressResponse | None:
        progress = await self.repo.get_progress(user_id, granth_id)
        return ProgressResponse.model_validate(progress) if progress else None

    async def update_progress(
        self, user_id: str, granth_id: str, data: UpdateProgressRequest
    ) -> ProgressResponse:
        progress = await self.repo.upsert_progress(user_id, granth_id, data.current_page)
        return ProgressResponse.model_validate(progress)
