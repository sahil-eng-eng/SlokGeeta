"""Repository for Granth CRUD operations."""

from datetime import datetime
from sqlalchemy import select, desc, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.models.granth import Granth, GranthPage, UserGranthProgress


class GranthRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ── Granth ────────────────────────────────────────────────────────────────

    async def create(self, granth: Granth) -> Granth:
        self.db.add(granth)
        await self.db.commit()
        await self.db.refresh(granth)
        return granth

    async def get_by_id(self, granth_id: str) -> Granth | None:
        result = await self.db.execute(
            select(Granth).where(Granth.id == granth_id)
        )
        return result.scalar_one_or_none()

    async def list_all(self, published_only: bool = False) -> list[Granth]:
        stmt = select(Granth).order_by(desc(Granth.created_at))
        if published_only:
            stmt = stmt.where(Granth.is_published == True)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def update(self, granth: Granth) -> Granth:
        await self.db.commit()
        await self.db.refresh(granth)
        return granth

    async def delete(self, granth: Granth) -> None:
        await self.db.delete(granth)
        await self.db.commit()

    # ── GranthPage ────────────────────────────────────────────────────────────

    async def create_page(self, page: GranthPage) -> GranthPage:
        self.db.add(page)
        await self.db.commit()
        await self.db.refresh(page)
        return page

    async def get_page(self, granth_id: str, page_number: int) -> GranthPage | None:
        result = await self.db.execute(
            select(GranthPage)
            .where(GranthPage.granth_id == granth_id, GranthPage.page_number == page_number)
        )
        return result.scalar_one_or_none()

    async def get_pages(self, granth_id: str) -> list[GranthPage]:
        result = await self.db.execute(
            select(GranthPage)
            .where(GranthPage.granth_id == granth_id)
            .order_by(GranthPage.page_number)
        )
        return list(result.scalars().all())

    async def update_page(self, page: GranthPage) -> GranthPage:
        await self.db.commit()
        await self.db.refresh(page)
        return page

    async def delete_page(self, page: GranthPage) -> None:
        await self.db.delete(page)
        await self.db.commit()

    async def count_pages(self, granth_id: str) -> int:
        result = await self.db.execute(
            select(func.count()).select_from(GranthPage).where(GranthPage.granth_id == granth_id)
        )
        return result.scalar() or 0

    # ── Progress ──────────────────────────────────────────────────────────────

    async def get_progress(self, user_id: str, granth_id: str) -> UserGranthProgress | None:
        result = await self.db.execute(
            select(UserGranthProgress)
            .where(
                UserGranthProgress.user_id == user_id,
                UserGranthProgress.granth_id == granth_id,
            )
        )
        return result.scalar_one_or_none()

    async def upsert_progress(
        self, user_id: str, granth_id: str, current_page: int
    ) -> UserGranthProgress:
        existing = await self.get_progress(user_id, granth_id)
        if existing:
            existing.current_page = current_page
            existing.last_read_at = datetime.utcnow()
            await self.db.commit()
            await self.db.refresh(existing)
            return existing
        progress = UserGranthProgress(
            user_id=user_id,
            granth_id=granth_id,
            current_page=current_page,
            last_read_at=datetime.utcnow(),
        )
        self.db.add(progress)
        await self.db.commit()
        await self.db.refresh(progress)
        return progress
