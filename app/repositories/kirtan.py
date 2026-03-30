"""Repository for KirtanTrack CRUD operations."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.kirtan_track import KirtanTrack


class KirtanRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(self, track: KirtanTrack) -> KirtanTrack:
        self.db.add(track)
        await self.db.commit()
        await self.db.refresh(track)
        return track

    async def get_by_id(self, track_id: str) -> KirtanTrack | None:
        result = await self.db.execute(
            select(KirtanTrack).where(KirtanTrack.id == track_id)
        )
        return result.scalar_one_or_none()

    async def list_by_owner(self, owner_id: str) -> list[KirtanTrack]:
        result = await self.db.execute(
            select(KirtanTrack)
            .where(KirtanTrack.owner_id == owner_id)
            .order_by(KirtanTrack.created_at.desc())
        )
        return list(result.scalars().all())

    async def delete(self, track: KirtanTrack) -> None:
        await self.db.delete(track)
        await self.db.commit()

    async def save(self, track: KirtanTrack) -> KirtanTrack:
        await self.db.commit()
        await self.db.refresh(track)
        return track
