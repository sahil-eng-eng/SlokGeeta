"""Granular entity-permission routes (ABAC).

GET    /permissions/mine                                   — list all permissions I have granted to others
GET    /permissions/{entity_type}/{entity_id}             — list all user permissions for an entity
POST   /permissions/{entity_type}/{entity_id}             — set (upsert) permissions for a user
DELETE /permissions/{entity_type}/{entity_id}/{user_id}   — revoke a user's permissions
GET    /permissions/{entity_type}/{entity_id}/check       — check if caller can perform an action
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.services.entity_permissions import EntityPermissionService
from app.schemas.entity_permissions import SetEntityPermissionRequest
from app.core.responses import ApiResponse
from app.constants.messages import PERMISSION_MESSAGES
from app.constants.enums import EntityType

router = APIRouter(prefix="/permissions", tags=["permissions"])


def _get_service(db: AsyncSession = Depends(get_db)) -> EntityPermissionService:
    return EntityPermissionService(db)


@router.get("/mine", response_model=None)
async def list_my_granted_permissions(
    current_user: User = Depends(get_current_user),
    service: EntityPermissionService = Depends(_get_service),
):
    """List all permissions I have granted to other users."""
    results = await service.list_granted_by_me(current_user.id)
    return ApiResponse(
        status_code=200,
        data=[r.model_dump() for r in results],
        message=PERMISSION_MESSAGES["RETRIEVED"],
    )


@router.get("/{entity_type}/{entity_id}", response_model=None)
async def list_permissions(
    entity_type: EntityType,
    entity_id: str,
    current_user: User = Depends(get_current_user),
    service: EntityPermissionService = Depends(_get_service),
):
    results = await service.list_permissions(entity_type, entity_id, current_user.id)
    return ApiResponse(
        status_code=200,
        data=[r.model_dump() for r in results],
        message=PERMISSION_MESSAGES["RETRIEVED"],
    )


@router.post("/{entity_type}/{entity_id}", status_code=200, response_model=None)
async def set_permissions(
    entity_type: EntityType,
    entity_id: str,
    body: SetEntityPermissionRequest,
    current_user: User = Depends(get_current_user),
    service: EntityPermissionService = Depends(_get_service),
):
    result = await service.set_permissions(entity_type, entity_id, current_user.id, body)
    return ApiResponse(
        status_code=200, data=result.model_dump(), message=PERMISSION_MESSAGES["UPDATED"]
    )


@router.delete("/{entity_type}/{entity_id}/{target_user_id}", status_code=204)
async def revoke_permissions(
    entity_type: EntityType,
    entity_id: str,
    target_user_id: str,
    current_user: User = Depends(get_current_user),
    service: EntityPermissionService = Depends(_get_service),
):
    await service.revoke(entity_type, entity_id, target_user_id, current_user.id)


@router.get("/{entity_type}/{entity_id}/check", response_model=None)
async def check_action(
    entity_type: EntityType,
    entity_id: str,
    action: str = Query(..., description="Action to check: view | request_edit | direct_edit"),
    current_user: User = Depends(get_current_user),
    service: EntityPermissionService = Depends(_get_service),
):
    allowed = await service.check_action(current_user.id, entity_type, entity_id, action)
    return ApiResponse(
        status_code=200,
        data={"allowed": allowed},
        message=PERMISSION_MESSAGES["RETRIEVED"],
    )
