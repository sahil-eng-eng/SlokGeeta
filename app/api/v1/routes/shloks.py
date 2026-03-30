"""Shlok routes — CRUD, audio upload, listing, cross-references, related."""

from fastapi import APIRouter, Depends, UploadFile, File, Query
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.dependencies import get_current_user, get_optional_user
from app.core.responses import ApiResponse
from app.services.shloks import ShlokService
from app.schemas.shloks import (
    CreateShlokRequest,
    UpdateShlokRequest,
    ShlokResponse,
    ShlokListResponse,
    CrossReferenceRequest,
    CrossReferenceResponse,
)
from app.constants.messages import SHLOK_MESSAGES

router = APIRouter(prefix="/shloks", tags=["Shloks"])


@router.post("", response_model=ApiResponse[ShlokResponse])
async def create_shlok(
    data: CreateShlokRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    service = ShlokService(db)
    result = await service.create_shlok(current_user.id, data)
    return ApiResponse(
        status_code=201,
        message=SHLOK_MESSAGES["CREATED"],
        data=result,
    )


@router.get(
    "/book/{book_id}", response_model=ApiResponse[ShlokListResponse]
)
async def list_shloks_by_book(
    book_id: str,
    cursor: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_optional_user),
):
    service = ShlokService(db)
    user_id = current_user.id if current_user else None
    result = await service.list_by_book(book_id, user_id, cursor, limit)
    return ApiResponse(
        status_code=200,
        message=SHLOK_MESSAGES["LIST_RETRIEVED"],
        data=result,
    )


@router.get("/{shlok_id}", response_model=ApiResponse[ShlokResponse])
async def get_shlok(
    shlok_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_optional_user),
):
    service = ShlokService(db)
    user_id = current_user.id if current_user else None
    result = await service.get_shlok(shlok_id, user_id)
    return ApiResponse(
        status_code=200,
        message=SHLOK_MESSAGES["RETRIEVED"],
        data=result,
    )


@router.patch(
    "/{shlok_id}", response_model=ApiResponse[ShlokResponse]
)
async def update_shlok(
    shlok_id: str,
    data: UpdateShlokRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    service = ShlokService(db)
    result = await service.update_shlok(
        shlok_id, current_user.id, data
    )
    return ApiResponse(
        status_code=200,
        message=SHLOK_MESSAGES["UPDATED"],
        data=result,
    )


@router.delete("/{shlok_id}", response_model=ApiResponse)
async def delete_shlok(
    shlok_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    service = ShlokService(db)
    await service.delete_shlok(shlok_id, current_user.id)
    return ApiResponse(
        status_code=200,
        message=SHLOK_MESSAGES["DELETED"],
    )


@router.post(
    "/{shlok_id}/audio",
    response_model=ApiResponse[ShlokResponse],
)
async def upload_audio(
    shlok_id: str,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    content = await file.read()
    ext = file.filename.split(".")[-1] if file.filename else "mp3"
    service = ShlokService(db)
    result = await service.upload_audio(
        shlok_id,
        current_user.id,
        content,
        file.content_type or "audio/mpeg",
        ext,
    )
    return ApiResponse(
        status_code=200,
        message=SHLOK_MESSAGES["AUDIO_UPLOADED"],
        data=result,
    )


@router.get(
    "/{shlok_id}/related",
    response_model=ApiResponse[list[ShlokResponse]],
)
async def get_related_shloks(
    shlok_id: str,
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    service = ShlokService(db)
    result = await service.get_related(shlok_id, limit)
    return ApiResponse(
        status_code=200,
        message=SHLOK_MESSAGES["RELATED_RETRIEVED"],
        data=result,
    )


@router.post(
    "/{shlok_id}/cross-references",
    response_model=ApiResponse[CrossReferenceResponse],
)
async def add_cross_reference(
    shlok_id: str,
    data: CrossReferenceRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    service = ShlokService(db)
    result = await service.add_cross_reference(
        shlok_id, current_user.id, data
    )
    return ApiResponse(
        status_code=201,
        message=SHLOK_MESSAGES["CROSS_REF_ADDED"],
        data=result,
    )


@router.get(
    "/{shlok_id}/cross-references",
    response_model=ApiResponse[list[CrossReferenceResponse]],
)
async def get_cross_references(
    shlok_id: str,
    db: AsyncSession = Depends(get_db),
):
    service = ShlokService(db)
    result = await service.get_cross_references(shlok_id)
    return ApiResponse(
        status_code=200,
        message=SHLOK_MESSAGES["CROSS_REFS_RETRIEVED"],
        data=result,
    )
