"""Repository for NaamJap CRUD operations."""

from datetime import date
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.naam_jap import NaamTarget, JapEntry


class NaamJapRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ── NaamTarget ────────────────────────────────────────────────────────────

    async def get_target(self, owner_id: str) -> NaamTarget | None:
        result = await self.db.execute(
            select(NaamTarget)
            .where(NaamTarget.owner_id == owner_id)
            .order_by(desc(NaamTarget.created_at))
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def upsert_target(self, owner_id: str, start_date: date, end_date: date, total_goal: int) -> NaamTarget:
        existing = await self.get_target(owner_id)
        if existing:
            existing.start_date = start_date
            existing.end_date = end_date
            existing.total_goal = total_goal
            await self.db.commit()
            await self.db.refresh(existing)
            return existing
        target = NaamTarget(
            owner_id=owner_id,
            start_date=start_date,
            end_date=end_date,
            total_goal=total_goal,
        )
        self.db.add(target)
        await self.db.commit()
        await self.db.refresh(target)
        return target

    # ── JapEntry ──────────────────────────────────────────────────────────────

    async def create_entry(self, entry: JapEntry) -> JapEntry:
        self.db.add(entry)
        await self.db.commit()
        await self.db.refresh(entry)
        return entry

    async def get_entry_by_id(self, entry_id: str) -> JapEntry | None:
        result = await self.db.execute(
            select(JapEntry).where(JapEntry.id == entry_id)
        )
        return result.scalar_one_or_none()

    async def get_entries_for_date(self, owner_id: str, entry_date: date) -> list[JapEntry]:
        result = await self.db.execute(
            select(JapEntry)
            .where(JapEntry.owner_id == owner_id, JapEntry.entry_date == entry_date)
            .order_by(JapEntry.created_at)
        )
        return list(result.scalars().all())

    async def get_history(
        self,
        owner_id: str,
        limit: int = 7,
        from_date: date | None = None,
        to_date: date | None = None,
    ) -> list[JapEntry]:
        stmt = (
            select(JapEntry)
            .where(JapEntry.owner_id == owner_id)
        )
        if from_date:
            stmt = stmt.where(JapEntry.entry_date >= from_date)
        if to_date:
            stmt = stmt.where(JapEntry.entry_date <= to_date)
        stmt = stmt.order_by(desc(JapEntry.entry_date), JapEntry.created_at).limit(limit * 20)  # enough entries
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def delete_entry(self, entry: JapEntry) -> None:
        await self.db.delete(entry)
        await self.db.commit()
