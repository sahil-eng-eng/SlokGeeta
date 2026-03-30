"""Repository for Schedule CRUD operations."""

from datetime import date
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.schedule import ScheduleVersion, ScheduleCheckIn


class ScheduleRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ── ScheduleVersion ──────────────────────────────────────────────────────

    async def get_versions(self, owner_id: str) -> list[ScheduleVersion]:
        result = await self.db.execute(
            select(ScheduleVersion)
            .where(ScheduleVersion.owner_id == owner_id)
            .order_by(ScheduleVersion.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_active_version(self, owner_id: str) -> ScheduleVersion | None:
        result = await self.db.execute(
            select(ScheduleVersion)
            .where(ScheduleVersion.owner_id == owner_id, ScheduleVersion.is_active == True)  # noqa: E712
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_version_by_id(self, version_id: str) -> ScheduleVersion | None:
        result = await self.db.execute(
            select(ScheduleVersion).where(ScheduleVersion.id == version_id)
        )
        return result.scalar_one_or_none()

    async def create_version(self, version: ScheduleVersion) -> ScheduleVersion:
        self.db.add(version)
        await self.db.commit()
        await self.db.refresh(version)
        return version

    async def deactivate_all(self, owner_id: str) -> None:
        await self.db.execute(
            update(ScheduleVersion)
            .where(ScheduleVersion.owner_id == owner_id)
            .values(is_active=False)
        )
        await self.db.commit()

    async def activate_version(self, version: ScheduleVersion) -> ScheduleVersion:
        await self.deactivate_all(version.owner_id)
        version.is_active = True
        await self.db.commit()
        await self.db.refresh(version)
        return version

    async def update_version(
        self,
        version: ScheduleVersion,
        items: list[dict],
        applies_to: list[str],
        reward: str | None,
        reward_days: int | None,
    ) -> ScheduleVersion:
        version.items = items
        version.applies_to = applies_to
        version.reward = reward
        version.reward_days = reward_days
        await self.db.commit()
        await self.db.refresh(version)
        return version

    # ── ScheduleCheckIn ──────────────────────────────────────────────────────

    async def get_checkins(self, owner_id: str, limit: int = 30) -> list[ScheduleCheckIn]:
        result = await self.db.execute(
            select(ScheduleCheckIn)
            .where(ScheduleCheckIn.owner_id == owner_id)
            .order_by(ScheduleCheckIn.check_in_date.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_checkin_for_date(self, owner_id: str, check_in_date: date) -> ScheduleCheckIn | None:
        result = await self.db.execute(
            select(ScheduleCheckIn)
            .where(
                ScheduleCheckIn.owner_id == owner_id,
                ScheduleCheckIn.check_in_date == check_in_date,
            )
        )
        return result.scalar_one_or_none()

    async def get_checkin_by_id(self, checkin_id: str) -> ScheduleCheckIn | None:
        result = await self.db.execute(
            select(ScheduleCheckIn).where(ScheduleCheckIn.id == checkin_id)
        )
        return result.scalar_one_or_none()

    async def update_checkin(
        self, checkin: ScheduleCheckIn, items: list[dict], alignment: int
    ) -> ScheduleCheckIn:
        checkin.items = items
        checkin.alignment = alignment
        await self.db.commit()
        await self.db.refresh(checkin)
        return checkin

    async def upsert_checkin(
        self, owner_id: str, version_id: str, check_in_date: date,
        items: list[dict], alignment: int
    ) -> ScheduleCheckIn:
        existing = await self.get_checkin_for_date(owner_id, check_in_date)
        if existing:
            existing.version_id = version_id
            existing.items = items
            existing.alignment = alignment
            await self.db.commit()
            await self.db.refresh(existing)
            return existing
        checkin = ScheduleCheckIn(
            owner_id=owner_id,
            version_id=version_id,
            check_in_date=check_in_date,
            items=items,
            alignment=alignment,
        )
        self.db.add(checkin)
        await self.db.commit()
        await self.db.refresh(checkin)
        return checkin
