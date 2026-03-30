"""Content request routes (request/approval workflow).

POST  /requests                  — create a content request
GET   /requests/incoming         — list requests directed at me (as owner)
GET   /requests/outgoing         — list requests I sent
GET   /requests/pending-count    — count pending incoming requests (sidebar badge)
PATCH /requests/{id}/review      — approve or reject a request
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.services.content_requests import ContentRequestService
from app.schemas.content_requests import (
    CreateContentRequestRequest,
    ReviewContentRequestRequest,
)
from app.core.responses import ApiResponse
from app.constants.messages import CONTENT_REQUEST_MESSAGES
from app.constants.enums import ContentRequestStatus

router = APIRouter(prefix="/requests", tags=["content-requests"])


def _get_service(db: AsyncSession = Depends(get_db)) -> ContentRequestService:
    return ContentRequestService(db)


@router.post("", status_code=201, response_model=None)
async def create_request(
    body: CreateContentRequestRequest,
    current_user: User = Depends(get_current_user),
    service: ContentRequestService = Depends(_get_service),
):
    result = await service.create(current_user.id, body)
    return ApiResponse(
        status_code=201, data=result.model_dump(), message=CONTENT_REQUEST_MESSAGES["REQUEST_CREATED"]
    )


@router.get("/incoming", response_model=None)
async def list_incoming(
    status: ContentRequestStatus | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    service: ContentRequestService = Depends(_get_service),
):
    results = await service.list_incoming(current_user.id, status)
    return ApiResponse(
        status_code=200,
        data=[r.model_dump() for r in results.items],
        message=CONTENT_REQUEST_MESSAGES["REQUESTS_RETRIEVED"],
    )


@router.get("/outgoing", response_model=None)
async def list_outgoing(
    status: ContentRequestStatus | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    service: ContentRequestService = Depends(_get_service),
):
    results = await service.list_outgoing(current_user.id, status)
    return ApiResponse(
        status_code=200,
        data=[r.model_dump() for r in results.items],
        message=CONTENT_REQUEST_MESSAGES["REQUESTS_RETRIEVED"],
    )


@router.get("/pending-count", response_model=None)
async def pending_count(
    current_user: User = Depends(get_current_user),
    service: ContentRequestService = Depends(_get_service),
):
    count = await service.count_pending(current_user.id)
    return ApiResponse(
        status_code=200,
        data={"count": count}, message=CONTENT_REQUEST_MESSAGES["REQUESTS_RETRIEVED"]
    )


@router.patch("/{request_id}/review", response_model=None)
async def review_request(
    request_id: str,
    body: ReviewContentRequestRequest,
    current_user: User = Depends(get_current_user),
    service: ContentRequestService = Depends(_get_service),
):
    result = await service.review(request_id, current_user.id, body)
    return ApiResponse(
        status_code=200, data=result.model_dump(), message=CONTENT_REQUEST_MESSAGES["REQUEST_REVIEWED"]
    )
