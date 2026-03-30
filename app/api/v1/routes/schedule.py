"""Schedule routes.

GET    /schedule/versions          — list all versions for user
POST   /schedule/versions          — create new (auto-activates)
GET    /schedule/versions/active   — get active version
PATCH  /schedule/versions/{id}/activate — switch active version
POST   /schedule/checkins          — submit today's check-in
GET    /schedule/checkins          — get check-in history
GET    /schedule/checkins/today    — get today's check-in
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.responses import ApiResponse
from app.models.user import User
from app.schemas.schedule import CreateScheduleVersionRequest, CreateCheckInRequest, UpdateScheduleVersionRequest
from app.services.schedule import ScheduleService, VersionNotFoundException, VersionForbiddenException, CheckInNotFoundException, CheckInForbiddenException

router = APIRouter(prefix="/schedule", tags=["schedule"])


def _get_service(db: AsyncSession = Depends(get_db)) -> ScheduleService:
    return ScheduleService(db)


@router.get("/versions", response_model=None)
async def list_versions(
    current_user: User = Depends(get_current_user),
    service: ScheduleService = Depends(_get_service),
):
    versions = await service.list_versions(current_user.id)
    return ApiResponse(
        status_code=200,
        data=[v.model_dump() for v in versions],
        message="Versions retrieved",
    )


@router.get("/versions/active", response_model=None)
async def get_active_version(
    current_user: User = Depends(get_current_user),
    service: ScheduleService = Depends(_get_service),
):
    version = await service.get_active_version(current_user.id)
    return ApiResponse(
        status_code=200,
        data=version.model_dump() if version else None,
        message="Active version retrieved",
    )


@router.post("/versions", response_model=None)
async def create_version(
    body: CreateScheduleVersionRequest,
    current_user: User = Depends(get_current_user),
    service: ScheduleService = Depends(_get_service),
):
    version = await service.create_version(current_user.id, body)
    return ApiResponse(status_code=201, data=version.model_dump(), message="Version created")


@router.patch("/versions/{version_id}/activate", response_model=None)
async def activate_version(
    version_id: str,
    current_user: User = Depends(get_current_user),
    service: ScheduleService = Depends(_get_service),
):
    try:
        version = await service.activate_version(current_user.id, version_id)
    except VersionNotFoundException:
        raise HTTPException(status_code=404, detail="Version not found")
    except VersionForbiddenException:
        raise HTTPException(status_code=403, detail="Forbidden")
    return ApiResponse(status_code=200, data=version.model_dump(), message="Version activated")


@router.patch("/versions/{version_id}", response_model=None)
async def update_version(
    version_id: str,
    body: UpdateScheduleVersionRequest,
    current_user: User = Depends(get_current_user),
    service: ScheduleService = Depends(_get_service),
):
    try:
        version = await service.update_version(current_user.id, version_id, body)
    except VersionNotFoundException:
        raise HTTPException(status_code=404, detail="Version not found")
    except VersionForbiddenException:
        raise HTTPException(status_code=403, detail="Forbidden")
    return ApiResponse(status_code=200, data=version.model_dump(), message="Version updated")


@router.get("/checkins/today", response_model=None)
async def get_today_checkin(
    current_user: User = Depends(get_current_user),
    service: ScheduleService = Depends(_get_service),
):
    checkin = await service.get_today_checkin(current_user.id)
    return ApiResponse(
        status_code=200,
        data=checkin.model_dump() if checkin else None,
        message="Today's check-in retrieved",
    )


@router.get("/checkins", response_model=None)
async def list_checkins(
    limit: int = Query(default=30, le=90),
    current_user: User = Depends(get_current_user),
    service: ScheduleService = Depends(_get_service),
):
    checkins = await service.get_checkins(current_user.id, limit)
    return ApiResponse(
        status_code=200,
        data=[c.model_dump() for c in checkins],
        message="Check-ins retrieved",
    )


@router.post("/checkins", response_model=None)
async def submit_checkin(
    body: CreateCheckInRequest,
    current_user: User = Depends(get_current_user),
    service: ScheduleService = Depends(_get_service),
):
    checkin = await service.submit_checkin(current_user.id, body)
    return ApiResponse(status_code=201, data=checkin.model_dump(), message="Check-in saved")


@router.patch("/checkins/{checkin_id}", response_model=None)
async def update_checkin(
    checkin_id: str,
    body: CreateCheckInRequest,
    current_user: User = Depends(get_current_user),
    service: ScheduleService = Depends(_get_service),
):
    try:
        checkin = await service.update_checkin(current_user.id, checkin_id, body)
    except CheckInNotFoundException:
        raise HTTPException(status_code=404, detail="Check-in not found")
    except CheckInForbiddenException:
        raise HTTPException(status_code=403, detail="Forbidden")
    return ApiResponse(status_code=200, data=checkin.model_dump(), message="Check-in updated")
