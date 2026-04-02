"""NaamJap routes.

GET    /naam-jap/target          — get my active target
POST   /naam-jap/target          — set / update target
GET    /naam-jap/today           — get today's jap entries
POST   /naam-jap/entries         — add a new entry
DELETE /naam-jap/entries/{id}    — remove an entry
GET    /naam-jap/history         — get history (grouped by day)
"""

from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.responses import ApiResponse
from app.models.user import User
from app.schemas.naam_jap import SetNaamTargetRequest, CreateJapEntryRequest, SaveInstantJapRequest
from app.services.naam_jap import NaamJapService, EntryNotFoundException, EntryForbiddenException

router = APIRouter(prefix="/naam-jap", tags=["naam-jap"])


def _get_service(db: AsyncSession = Depends(get_db)) -> NaamJapService:
    return NaamJapService(db)


@router.get("/target", response_model=None)
async def get_target(
    current_user: User = Depends(get_current_user),
    service: NaamJapService = Depends(_get_service),
):
    target = await service.get_target(current_user.id)
    return ApiResponse(
        status_code=200,
        data=target.model_dump() if target else None,
        message="Target retrieved",
    )


@router.post("/target", response_model=None)
async def set_target(
    body: SetNaamTargetRequest,
    current_user: User = Depends(get_current_user),
    service: NaamJapService = Depends(_get_service),
):
    target = await service.set_target(current_user.id, body)
    return ApiResponse(status_code=200, data=target.model_dump(), message="Target saved")


@router.get("/today", response_model=None)
async def get_today(
    current_user: User = Depends(get_current_user),
    service: NaamJapService = Depends(_get_service),
):
    entries = await service.get_today_entries(current_user.id, date.today())
    return ApiResponse(
        status_code=200,
        data=[e.model_dump() for e in entries],
        message="Today's entries retrieved",
    )


@router.post("/entries", status_code=201, response_model=None)
async def add_entry(
    body: CreateJapEntryRequest,
    current_user: User = Depends(get_current_user),
    service: NaamJapService = Depends(_get_service),
):
    entry = await service.add_entry(current_user.id, body)
    return ApiResponse(status_code=201, data=entry.model_dump(), message="Entry added")


@router.delete("/entries/{entry_id}", status_code=204)
async def delete_entry(
    entry_id: str,
    current_user: User = Depends(get_current_user),
    service: NaamJapService = Depends(_get_service),
):
    try:
        await service.delete_entry(entry_id, current_user.id)
    except EntryNotFoundException:
        raise HTTPException(status_code=404, detail="Entry not found")
    except EntryForbiddenException:
        raise HTTPException(status_code=403, detail="Forbidden")


@router.get("/history", response_model=None)
async def get_history(
    limit: int = Query(default=7, le=90),
    from_date: date | None = Query(default=None),
    to_date: date | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    service: NaamJapService = Depends(_get_service),
):
    history = await service.get_history(current_user.id, limit, from_date, to_date)
    return ApiResponse(
        status_code=200,
        data=[h.model_dump() for h in history],
        message="History retrieved",
    )


# ── Instant Jap ───────────────────────────────────────────────────────────────

@router.post("/instant-sessions", status_code=201, response_model=None)
async def save_instant_session(
    body: SaveInstantJapRequest,
    current_user: User = Depends(get_current_user),
    service: NaamJapService = Depends(_get_service),
):
    session = await service.save_instant_session(current_user.id, body)
    return ApiResponse(status_code=201, data=session.model_dump(), message="Session saved")


@router.get("/instant-sessions", response_model=None)
async def get_instant_sessions(
    limit: int = Query(default=20, le=100),
    current_user: User = Depends(get_current_user),
    service: NaamJapService = Depends(_get_service),
):
    sessions = await service.get_instant_sessions(current_user.id, limit)
    return ApiResponse(
        status_code=200,
        data=[s.model_dump() for s in sessions],
        message="Sessions retrieved",
    )
