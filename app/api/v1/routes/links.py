"""Shareable link routes.

POST /links          — generate a shareable link
GET  /links          — list my generated links
GET  /links/{code}   — resolve a link (public)
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.services.links import SharedLinkService
from app.schemas.links import GenerateLinkRequest
from app.core.responses import ApiResponse
from app.constants.messages import LINK_MESSAGES

router = APIRouter(prefix="/links", tags=["links"])


def _get_service(db: AsyncSession = Depends(get_db)) -> SharedLinkService:
    return SharedLinkService(db)


@router.post("", status_code=201, response_model=None)
async def generate_link(
    body: GenerateLinkRequest,
    current_user: User = Depends(get_current_user),
    service: SharedLinkService = Depends(_get_service),
):
    result = await service.generate(current_user.id, body)
    return ApiResponse(status_code=201, data=result.model_dump(), message=LINK_MESSAGES["LINK_CREATED"])


@router.get("", response_model=None)
async def list_my_links(
    current_user: User = Depends(get_current_user),
    service: SharedLinkService = Depends(_get_service),
):
    results = await service.list_my_links(current_user.id)
    return ApiResponse(
        status_code=200,
        data=[r.model_dump() for r in results],
        message=LINK_MESSAGES["LINKS_RETRIEVED"],
    )


@router.get("/{code}", response_model=None)
async def resolve_link(
    code: str,
    service: SharedLinkService = Depends(_get_service),
):
    result = await service.resolve(code)
    return ApiResponse(status_code=200, data=result.model_dump(), message=LINK_MESSAGES["LINK_RESOLVED"])
