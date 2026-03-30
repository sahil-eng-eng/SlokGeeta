"""Meanings routes — CRUD for shlok interpretations and voting."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.dependencies import get_current_user, get_optional_user
from app.core.responses import ApiResponse
from app.services.meanings import MeaningService
from app.schemas.meanings import (
    CreateMeaningRequest,
    UpdateMeaningRequest,
    VoteMeaningRequest,
    MeaningResponse,
    MeaningListResponse,
)
from app.constants.messages import MEANING_MESSAGES

router = APIRouter(tags=["Meanings"])


@router.post(
    "/shloks/{shlok_id}/meanings",
    response_model=ApiResponse[MeaningResponse],
)
async def create_meaning(
    shlok_id: str,
    data: CreateMeaningRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    service = MeaningService(db)
    result = await service.create_meaning(shlok_id, current_user.id, data)
    return ApiResponse(
        status_code=201,
        message=MEANING_MESSAGES["CREATED"],
        data=result,
    )


@router.get(
    "/shloks/{shlok_id}/meanings",
    response_model=ApiResponse[MeaningListResponse],
)
async def get_meanings(
    shlok_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_optional_user),
):
    service = MeaningService(db)
    viewer_id = current_user.id if current_user else None
    print(viewer_id,' viewer id in get meanings')
    result = await service.get_meanings_tree(shlok_id, viewer_id)
    return ApiResponse(
        status_code=200,
        message=MEANING_MESSAGES["RETRIEVED"],
        data=result,
    )


@router.patch(
    "/meanings/{meaning_id}",
    response_model=ApiResponse[MeaningResponse],
)
async def update_meaning(
    meaning_id: str,
    data: UpdateMeaningRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    service = MeaningService(db)
    result = await service.update_meaning(meaning_id, current_user.id, data)
    return ApiResponse(
        status_code=200,
        message=MEANING_MESSAGES["UPDATED"],
        data=result,
    )


@router.delete("/meanings/{meaning_id}", response_model=ApiResponse)
async def delete_meaning(
    meaning_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    service = MeaningService(db)
    await service.delete_meaning(meaning_id, current_user.id)
    return ApiResponse(
        status_code=200,
        message=MEANING_MESSAGES["DELETED"],
        data=None,
    )


@router.post(
    "/meanings/{meaning_id}/vote",
    response_model=ApiResponse[MeaningResponse],
)
async def vote_meaning(
    meaning_id: str,
    data: VoteMeaningRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    service = MeaningService(db)
    result = await service.vote_meaning(meaning_id, current_user.id, data.direction)
    return ApiResponse(
        status_code=200,
        message=MEANING_MESSAGES["VOTED"],
        data=result,
    )
