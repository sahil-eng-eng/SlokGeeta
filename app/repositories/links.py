"""Shared link repository."""

from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.shared_link import SharedLink


class SharedLinkRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, link: SharedLink) -> SharedLink:
        self.db.add(link)
        await self.db.flush()
        await self.db.refresh(link)
        return link

    async def get_by_code(self, short_code: str) -> Optional[SharedLink]:
        result = await self.db.execute(
            select(SharedLink).where(SharedLink.short_code == short_code)
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, link_id: str) -> Optional[SharedLink]:
        result = await self.db.execute(
            select(SharedLink).where(SharedLink.id == link_id)
        )
        return result.scalar_one_or_none()

    async def list_by_creator(self, creator_id: str) -> list[SharedLink]:
        result = await self.db.execute(
            select(SharedLink)
            .where(SharedLink.creator_id == creator_id, SharedLink.is_active.is_(True))
            .order_by(SharedLink.created_at.desc())
        )
        return list(result.scalars().all())
