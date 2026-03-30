"""Kirtan Library routes.

GET    /kirtan/tracks            — list my tracks
POST   /kirtan/tracks            — add a track
PATCH  /kirtan/tracks/{id}/favorite — toggle favorite
DELETE /kirtan/tracks/{id}       — delete a track
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.responses import ApiResponse
from app.models.user import User
from app.schemas.kirtan import CreateKirtanTrackRequest, KirtanTrackResponse
from app.services.kirtan import (
    KirtanService,
    KirtanNotFoundException,
    KirtanForbiddenException,
    KirtanInvalidFileException,
)

router = APIRouter(prefix="/kirtan", tags=["kirtan"])


def _get_service(db: AsyncSession = Depends(get_db)) -> KirtanService:
    return KirtanService(db)


@router.get("/tracks", response_model=None)
async def list_tracks(
    current_user: User = Depends(get_current_user),
    service: KirtanService = Depends(_get_service),
):
    tracks = await service.list_tracks(current_user.id)
    return ApiResponse(
        status_code=200,
        data=[t.model_dump() for t in tracks],
        message="Tracks retrieved",
    )


@router.post("/tracks", status_code=201, response_model=None)
async def create_track(
    body: CreateKirtanTrackRequest,
    current_user: User = Depends(get_current_user),
    service: KirtanService = Depends(_get_service),
):
    track = await service.create_track(current_user.id, body)
    return ApiResponse(status_code=201, data=track.model_dump(), message="Track added")


@router.patch("/tracks/{track_id}/favorite", response_model=None)
async def toggle_favorite(
    track_id: str,
    current_user: User = Depends(get_current_user),
    service: KirtanService = Depends(_get_service),
):
    try:
        track = await service.toggle_favorite(track_id, current_user.id)
    except KirtanNotFoundException:
        raise HTTPException(status_code=404, detail="Track not found")
    except KirtanForbiddenException:
        raise HTTPException(status_code=403, detail="Forbidden")
    return ApiResponse(status_code=200, data=track.model_dump(), message="Favorite updated")


@router.delete("/tracks/{track_id}", status_code=204)
async def delete_track(
    track_id: str,
    current_user: User = Depends(get_current_user),
    service: KirtanService = Depends(_get_service),
):
    try:
        await service.delete_track(track_id, current_user.id)
    except KirtanNotFoundException:
        raise HTTPException(status_code=404, detail="Track not found")
    except KirtanForbiddenException:
        raise HTTPException(status_code=403, detail="Forbidden")


@router.post("/tracks/{track_id}/audio", response_model=None)
async def upload_audio(
    track_id: str,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    service: KirtanService = Depends(_get_service),
):
    try:
        track = await service.upload_audio(track_id, current_user.id, file)
    except KirtanNotFoundException:
        raise HTTPException(status_code=404, detail="Track not found")
    except KirtanForbiddenException:
        raise HTTPException(status_code=403, detail="Forbidden")
    except KirtanInvalidFileException as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    return ApiResponse(status_code=200, data=track.model_dump(), message="Audio uploaded")
