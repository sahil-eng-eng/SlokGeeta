"""NaamJap service — business logic."""

from collections import defaultdict
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.naam_jap import NaamJapRepository
from app.models.naam_jap import JapEntry, InstantJapSession
from app.schemas.naam_jap import (
    SetNaamTargetRequest,
    NaamTargetResponse,
    CreateJapEntryRequest,
    JapEntryResponse,
    DayLogResponse,
    SaveInstantJapRequest,
    InstantJapSessionResponse,
)


class EntryNotFoundException(Exception):
    pass


class EntryForbiddenException(Exception):
    pass


class NaamJapService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = NaamJapRepository(db)

    def _target_to_response(self, t) -> NaamTargetResponse:
        return NaamTargetResponse(
            id=t.id,
            owner_id=t.owner_id,
            start_date=t.start_date,
            end_date=t.end_date,
            total_goal=t.total_goal,
        )

    def _entry_to_response(self, e: JapEntry) -> JapEntryResponse:
        return JapEntryResponse(
            id=e.id,
            owner_id=e.owner_id,
            entry_date=e.entry_date,
            time_slot=e.time_slot,
            count=e.count,
        )

    async def get_target(self, owner_id: str) -> NaamTargetResponse | None:
        target = await self.repo.get_target(owner_id)
        return self._target_to_response(target) if target else None

    async def set_target(
        self, owner_id: str, data: SetNaamTargetRequest
    ) -> NaamTargetResponse:
        target = await self.repo.upsert_target(
            owner_id, data.start_date, data.end_date, data.total_goal
        )
        return self._target_to_response(target)

    async def get_today_entries(
        self, owner_id: str, today: date
    ) -> list[JapEntryResponse]:
        entries = await self.repo.get_entries_for_date(owner_id, today)
        return [self._entry_to_response(e) for e in entries]

    async def add_entry(
        self, owner_id: str, data: CreateJapEntryRequest
    ) -> JapEntryResponse:
        entry = JapEntry(
            owner_id=owner_id,
            entry_date=data.entry_date,
            time_slot=data.time_slot,
            count=data.count,
        )
        created = await self.repo.create_entry(entry)
        return self._entry_to_response(created)

    async def delete_entry(self, entry_id: str, owner_id: str) -> None:
        entry = await self.repo.get_entry_by_id(entry_id)
        if not entry:
            raise EntryNotFoundException()
        if entry.owner_id != owner_id:
            raise EntryForbiddenException()
        await self.repo.delete_entry(entry)

    async def get_history(
        self,
        owner_id: str,
        limit: int = 7,
        from_date: date | None = None,
        to_date: date | None = None,
    ) -> list[DayLogResponse]:
        entries = await self.repo.get_history(owner_id, limit, from_date, to_date)
        # Group by date
        grouped: dict[str, list[JapEntryResponse]] = defaultdict(list)
        for e in entries:
            date_str = e.entry_date.isoformat()
            grouped[date_str].append(self._entry_to_response(e))
        return [
            DayLogResponse(
                date=d,
                entries=grouped[d],
                total=sum(en.count for en in grouped[d]),
            )
            for d in sorted(grouped.keys(), reverse=True)
        ]

    # ── Instant Jap ───────────────────────────────────────────────────────────

    async def save_instant_session(
        self, owner_id: str, data: SaveInstantJapRequest
    ) -> InstantJapSessionResponse:
        session = InstantJapSession(
            owner_id=owner_id,
            count=data.count,
            target=data.target,
            duration_seconds=data.duration_seconds,
            completed=data.completed,
            session_date=date.today(),
        )
        created = await self.repo.create_instant_session(session)
        return InstantJapSessionResponse(
            id=created.id,
            owner_id=created.owner_id,
            count=created.count,
            target=created.target,
            duration_seconds=created.duration_seconds,
            completed=created.completed,
            session_date=created.session_date,
            created_at=str(created.created_at),
        )

    async def get_instant_sessions(
        self, owner_id: str, limit: int = 20
    ) -> list[InstantJapSessionResponse]:
        sessions = await self.repo.get_instant_sessions(owner_id, limit)
        return [
            InstantJapSessionResponse(
                id=s.id,
                owner_id=s.owner_id,
                count=s.count,
                target=s.target,
                duration_seconds=s.duration_seconds,
                completed=s.completed,
                session_date=s.session_date,
                created_at=str(s.created_at),
            )
            for s in sessions
        ]
