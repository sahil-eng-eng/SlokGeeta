"""Schedule service — business logic."""

from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.schedule import ScheduleRepository
from app.models.schedule import ScheduleVersion
from app.schemas.schedule import (
    CreateScheduleVersionRequest,
    UpdateScheduleVersionRequest,
    ScheduleVersionResponse,
    CreateCheckInRequest,
    CheckInResponse,
    ScheduleItemSchema,
    CheckInItemSchema,
)


class VersionNotFoundException(Exception):
    pass


class VersionForbiddenException(Exception):
    pass


class CheckInNotFoundException(Exception):
    pass


class CheckInForbiddenException(Exception):
    pass


class ScheduleService:
    def __init__(self, db: AsyncSession) -> None:
        self.repo = ScheduleRepository(db)

    # ── Helpers ──────────────────────────────────────────────────────────────

    def _version_to_response(self, v: ScheduleVersion) -> ScheduleVersionResponse:
        return ScheduleVersionResponse(
            id=v.id,
            items=[ScheduleItemSchema(**i) for i in v.items],
            applies_to=v.applies_to,
            reward=v.reward,
            reward_days=v.reward_days,
            is_active=v.is_active,
            created_at=v.created_at.isoformat(),
        )

    def _checkin_to_response(self, c) -> CheckInResponse:
        return CheckInResponse(
            id=c.id,
            version_id=c.version_id,
            check_in_date=c.check_in_date.isoformat(),
            items=[CheckInItemSchema(**i) for i in c.items],
            alignment=c.alignment,
            created_at=c.created_at.isoformat(),
        )

    # ── Versions ─────────────────────────────────────────────────────────────

    async def list_versions(self, owner_id: str) -> list[ScheduleVersionResponse]:
        versions = await self.repo.get_versions(owner_id)
        return [self._version_to_response(v) for v in versions]

    async def get_active_version(self, owner_id: str) -> ScheduleVersionResponse | None:
        v = await self.repo.get_active_version(owner_id)
        return self._version_to_response(v) if v else None

    async def create_version(
        self, owner_id: str, data: CreateScheduleVersionRequest
    ) -> ScheduleVersionResponse:
        # Deactivate existing versions
        await self.repo.deactivate_all(owner_id)
        version = ScheduleVersion(
            owner_id=owner_id,
            items=[i.model_dump() for i in data.items],
            applies_to=data.applies_to,
            reward=data.reward,
            reward_days=data.reward_days,
            is_active=True,
        )
        created = await self.repo.create_version(version)
        return self._version_to_response(created)

    async def activate_version(self, owner_id: str, version_id: str) -> ScheduleVersionResponse:
        version = await self.repo.get_version_by_id(version_id)
        if not version:
            raise VersionNotFoundException()
        if version.owner_id != owner_id:
            raise VersionForbiddenException()
        updated = await self.repo.activate_version(version)
        return self._version_to_response(updated)

    async def update_version(
        self, owner_id: str, version_id: str, data: UpdateScheduleVersionRequest
    ) -> ScheduleVersionResponse:
        version = await self.repo.get_version_by_id(version_id)
        if not version:
            raise VersionNotFoundException()
        if version.owner_id != owner_id:
            raise VersionForbiddenException()
        updated = await self.repo.update_version(
            version,
            items=[i.model_dump(exclude_none=True) for i in data.items],
            applies_to=data.applies_to,
            reward=data.reward,
            reward_days=data.reward_days,
        )
        return self._version_to_response(updated)

    # ── Check-ins ────────────────────────────────────────────────────────────

    async def submit_checkin(
        self, owner_id: str, data: CreateCheckInRequest
    ) -> CheckInResponse:
        today = date.today()
        items_raw = [i.model_dump() for i in data.items]
        total = len(items_raw)
        done = sum(1 for i in items_raw if i["done"])
        alignment = round((done / total) * 100) if total > 0 else 0
        checkin = await self.repo.upsert_checkin(
            owner_id=owner_id,
            version_id=data.version_id,
            check_in_date=today,
            items=items_raw,
            alignment=alignment,
        )
        return self._checkin_to_response(checkin)

    async def get_checkins(self, owner_id: str, limit: int = 30) -> list[CheckInResponse]:
        checkins = await self.repo.get_checkins(owner_id, limit)
        return [self._checkin_to_response(c) for c in checkins]

    async def get_today_checkin(self, owner_id: str) -> CheckInResponse | None:
        c = await self.repo.get_checkin_for_date(owner_id, date.today())
        return self._checkin_to_response(c) if c else None

    async def update_checkin(
        self, owner_id: str, checkin_id: str, data: "CreateCheckInRequest"
    ) -> CheckInResponse:
        checkin = await self.repo.get_checkin_by_id(checkin_id)
        if not checkin:
            raise CheckInNotFoundException()
        if checkin.owner_id != owner_id:
            raise CheckInForbiddenException()
        items_raw = [i.model_dump() for i in data.items]
        total = len(items_raw)
        done = sum(1 for i in items_raw if i["done"])
        alignment = round((done / total) * 100) if total > 0 else 0
        updated = await self.repo.update_checkin(checkin, items_raw, alignment)
        return self._checkin_to_response(updated)
