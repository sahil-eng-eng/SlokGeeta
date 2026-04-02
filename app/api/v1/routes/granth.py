"""Granth routes — admin management and user reading endpoints.

Admin endpoints (require admin/superadmin):
POST   /granths                           — create granth
PUT    /granths/{id}                      — update granth
DELETE /granths/{id}                      — delete granth
POST   /granths/{id}/pages               — add page
PUT    /granths/{id}/pages/{page_number}  — update page

Public endpoints (require auth):
GET    /granths                           — list published granths
GET    /granths/{id}                      — get granth details
GET    /granths/{id}/pages/{page_number}  — get a specific page
GET    /granths/{id}/pages               — get all pages
GET    /granths/{id}/progress            — get reading progress
PUT    /granths/{id}/progress            — update reading progress
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.dependencies import get_current_user, get_admin_user
from app.core.responses import ApiResponse
from app.models.user import User
from app.schemas.granth import (
    CreateGranthRequest,
    UpdateGranthRequest,
    CreateGranthPageRequest,
    UpdateGranthPageRequest,
    UpdateProgressRequest,
)
from app.services.granth import GranthService

router = APIRouter(prefix="/granths", tags=["granths"])


def _get_service(db: AsyncSession = Depends(get_db)) -> GranthService:
    return GranthService(db)


# ── Admin endpoints ───────────────────────────────────────────────────────────

@router.post("", status_code=201, response_model=None)
async def create_granth(
    body: CreateGranthRequest,
    admin: User = Depends(get_admin_user),
    service: GranthService = Depends(_get_service),
):
    granth = await service.create_granth(admin.id, body)
    return ApiResponse(status_code=201, data=granth.model_dump(), message="Granth created")


@router.put("/{granth_id}", response_model=None)
async def update_granth(
    granth_id: str,
    body: UpdateGranthRequest,
    admin: User = Depends(get_admin_user),
    service: GranthService = Depends(_get_service),
):
    granth = await service.update_granth(granth_id, body)
    return ApiResponse(status_code=200, data=granth.model_dump(), message="Granth updated")


@router.delete("/{granth_id}", status_code=204)
async def delete_granth(
    granth_id: str,
    admin: User = Depends(get_admin_user),
    service: GranthService = Depends(_get_service),
):
    await service.delete_granth(granth_id)


@router.post("/{granth_id}/pages", status_code=201, response_model=None)
async def add_page(
    granth_id: str,
    body: CreateGranthPageRequest,
    admin: User = Depends(get_admin_user),
    service: GranthService = Depends(_get_service),
):
    page = await service.add_page(granth_id, body.page_number, body.content, body.image_url)
    return ApiResponse(status_code=201, data=page.model_dump(), message="Page added")


@router.delete("/{granth_id}/pages/{page_number}", status_code=204)
async def delete_page(
    granth_id: str,
    page_number: int,
    admin: User = Depends(get_admin_user),
    service: GranthService = Depends(_get_service),
):
    await service.delete_page(granth_id, page_number)


@router.put("/{granth_id}/pages/{page_number}", response_model=None)
async def update_page(
    granth_id: str,
    page_number: int,
    body: UpdateGranthPageRequest,
    admin: User = Depends(get_admin_user),
    service: GranthService = Depends(_get_service),
):
    page = await service.update_page(granth_id, page_number, body)
    return ApiResponse(status_code=200, data=page.model_dump(), message="Page updated")


# ── Public (authenticated) endpoints ─────────────────────────────────────────

@router.get("", response_model=None)
async def list_granths(
    current_user: User = Depends(get_current_user),
    service: GranthService = Depends(_get_service),
):
    is_admin = current_user.role in ("admin", "superadmin")
    granths = await service.list_granths(published_only=not is_admin)
    return ApiResponse(status_code=200, data=[g.model_dump() for g in granths], message="Granths retrieved")


@router.get("/{granth_id}", response_model=None)
async def get_granth(
    granth_id: str,
    current_user: User = Depends(get_current_user),
    service: GranthService = Depends(_get_service),
):
    granth = await service.get_granth(granth_id)
    return ApiResponse(status_code=200, data=granth.model_dump(), message="Granth retrieved")


@router.get("/{granth_id}/pages", response_model=None)
async def get_pages(
    granth_id: str,
    current_user: User = Depends(get_current_user),
    service: GranthService = Depends(_get_service),
):
    pages = await service.get_pages(granth_id)
    return ApiResponse(status_code=200, data=[p.model_dump() for p in pages], message="Pages retrieved")


@router.get("/{granth_id}/pages/{page_number}", response_model=None)
async def get_page(
    granth_id: str,
    page_number: int,
    current_user: User = Depends(get_current_user),
    service: GranthService = Depends(_get_service),
):
    page = await service.get_page(granth_id, page_number)
    return ApiResponse(status_code=200, data=page.model_dump(), message="Page retrieved")


@router.get("/{granth_id}/progress", response_model=None)
async def get_progress(
    granth_id: str,
    current_user: User = Depends(get_current_user),
    service: GranthService = Depends(_get_service),
):
    progress = await service.get_progress(current_user.id, granth_id)
    return ApiResponse(
        status_code=200,
        data=progress.model_dump() if progress else None,
        message="Progress retrieved",
    )


@router.put("/{granth_id}/progress", response_model=None)
async def update_progress(
    granth_id: str,
    body: UpdateProgressRequest,
    current_user: User = Depends(get_current_user),
    service: GranthService = Depends(_get_service),
):
    progress = await service.update_progress(current_user.id, granth_id, body)
    return ApiResponse(status_code=200, data=progress.model_dump(), message="Progress updated")
