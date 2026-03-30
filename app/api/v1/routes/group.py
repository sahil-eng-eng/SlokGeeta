"""Group chat routes.

POST   /groups                                          — create a group
GET    /groups                                          — list user's groups
GET    /groups/{group_id}                               — get group details
PATCH  /groups/{group_id}                               — edit group (admin)
POST   /groups/{group_id}/members                       — add members (admin only)
PATCH  /groups/{group_id}/members/{user_id}/role        — change role (owner only)
DELETE /groups/{group_id}/leave                         — leave a group
POST   /groups/{group_id}/messages                      — send a message
GET    /groups/{group_id}/messages                      — get message history
DELETE /groups/{group_id}/messages/{message_id}         — delete a message
PATCH  /groups/{group_id}/messages/{message_id}         — edit a message
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.responses import ApiResponse
from app.models.user import User
from app.schemas.group import (
    CreateGroupRequest,
    UpdateGroupRequest,
    UpdateMemberRoleRequest,
    SendGroupMessageRequest,
    EditGroupMessageRequest,
    AddGroupMembersRequest,
)
from app.services.group import (
    GroupService,
    GroupNotFoundException,
    GroupForbiddenException,
    GroupMessageNotFoundException,
    GroupMessageForbiddenException,
)

router = APIRouter(prefix="/groups", tags=["groups"])


def _get_service(db: AsyncSession = Depends(get_db)) -> GroupService:
    return GroupService(db)


@router.post("", response_model=None)
async def create_group(
    body: CreateGroupRequest,
    current_user: User = Depends(get_current_user),
    service: GroupService = Depends(_get_service),
):
    group = await service.create_group(current_user.id, body)
    return ApiResponse(status_code=201, data=group.model_dump(), message="Group created")


@router.get("", response_model=None)
async def list_groups(
    current_user: User = Depends(get_current_user),
    service: GroupService = Depends(_get_service),
):
    groups = await service.list_user_groups(current_user.id)
    return ApiResponse(status_code=200, data=[g.model_dump() for g in groups], message="Groups retrieved")


@router.get("/{group_id}", response_model=None)
async def get_group(
    group_id: str,
    current_user: User = Depends(get_current_user),
    service: GroupService = Depends(_get_service),
):
    try:
        group = await service.get_group(group_id, current_user.id)
    except GroupNotFoundException:
        raise HTTPException(status_code=404, detail="Group not found")
    except GroupForbiddenException:
        raise HTTPException(status_code=403, detail="Not a member of this group")
    return ApiResponse(status_code=200, data=group.model_dump(mode="json"), message="Group retrieved")


@router.patch("/{group_id}", response_model=None)
async def edit_group(
    group_id: str,
    body: UpdateGroupRequest,
    current_user: User = Depends(get_current_user),
    service: GroupService = Depends(_get_service),
):
    try:
        group = await service.edit_group(group_id, current_user.id, body)
    except GroupNotFoundException:
        raise HTTPException(status_code=404, detail="Group not found")
    except GroupForbiddenException:
        raise HTTPException(status_code=403, detail="Admin only")
    return ApiResponse(status_code=200, data=group.model_dump(mode="json"), message="Group updated")


@router.post("/{group_id}/members", response_model=None)
async def add_members(
    group_id: str,
    body: AddGroupMembersRequest,
    current_user: User = Depends(get_current_user),
    service: GroupService = Depends(_get_service),
):
    try:
        group = await service.add_members(group_id, current_user.id, body)
    except GroupNotFoundException:
        raise HTTPException(status_code=404, detail="Group not found")
    except GroupForbiddenException:
        raise HTTPException(status_code=403, detail="Admin only")
    return ApiResponse(status_code=200, data=group.model_dump(mode="json"), message="Members added")


@router.patch("/{group_id}/members/{target_user_id}/role", response_model=None)
async def update_member_role(
    group_id: str,
    target_user_id: str,
    body: UpdateMemberRoleRequest,
    current_user: User = Depends(get_current_user),
    service: GroupService = Depends(_get_service),
):
    try:
        group = await service.update_member_role(group_id, current_user.id, target_user_id, body.role)
    except GroupNotFoundException:
        raise HTTPException(status_code=404, detail="Group not found")
    except GroupForbiddenException:
        raise HTTPException(status_code=403, detail="Owner only")
    return ApiResponse(status_code=200, data=group.model_dump(mode="json"), message="Role updated")


@router.delete("/{group_id}/leave", response_model=None, status_code=204)
async def leave_group(
    group_id: str,
    current_user: User = Depends(get_current_user),
    service: GroupService = Depends(_get_service),
):
    try:
        await service.leave_group(group_id, current_user.id)
    except GroupNotFoundException:
        raise HTTPException(status_code=404, detail="Group not found")
    except GroupForbiddenException:
        raise HTTPException(status_code=403, detail="Not a member")


@router.post("/{group_id}/messages", response_model=None)
async def send_message(
    group_id: str,
    body: SendGroupMessageRequest,
    current_user: User = Depends(get_current_user),
    service: GroupService = Depends(_get_service),
):
    try:
        message = await service.send_message(group_id, current_user.id, body)
    except GroupNotFoundException:
        raise HTTPException(status_code=404, detail="Group not found")
    except GroupForbiddenException:
        raise HTTPException(status_code=403, detail="Not a member")
    return ApiResponse(status_code=201, data=message.model_dump(mode="json"), message="Message sent")


@router.get("/{group_id}/messages", response_model=None)
async def get_messages(
    group_id: str,
    limit: int = Query(default=50, le=100),
    before_id: str | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    service: GroupService = Depends(_get_service),
):
    try:
        messages = await service.get_messages(group_id, current_user.id, limit, before_id)
    except GroupNotFoundException:
        raise HTTPException(status_code=404, detail="Group not found")
    except GroupForbiddenException:
        raise HTTPException(status_code=403, detail="Not a member")
    return ApiResponse(
        status_code=200,
        data=[m.model_dump(mode="json") for m in messages],
        message="Messages retrieved",
    )


@router.delete("/{group_id}/messages/{message_id}", response_model=None)
async def delete_message(
    group_id: str,
    message_id: str,
    current_user: User = Depends(get_current_user),
    service: GroupService = Depends(_get_service),
):
    try:
        message = await service.delete_message(group_id, message_id, current_user.id)
    except GroupNotFoundException:
        raise HTTPException(status_code=404, detail="Group not found")
    except GroupForbiddenException:
        raise HTTPException(status_code=403, detail="Not a member")
    except GroupMessageNotFoundException:
        raise HTTPException(status_code=404, detail="Message not found")
    except GroupMessageForbiddenException:
        raise HTTPException(status_code=403, detail="Cannot delete another user's message")
    return ApiResponse(status_code=200, data=message.model_dump(mode="json"), message="Message deleted")


@router.patch("/{group_id}/messages/{message_id}", response_model=None)
async def edit_message(
    group_id: str,
    message_id: str,
    body: EditGroupMessageRequest,
    current_user: User = Depends(get_current_user),
    service: GroupService = Depends(_get_service),
):
    try:
        message = await service.edit_message(group_id, message_id, current_user.id, body)
    except GroupNotFoundException:
        raise HTTPException(status_code=404, detail="Group not found")
    except GroupForbiddenException:
        raise HTTPException(status_code=403, detail="Not a member")
    except GroupMessageNotFoundException:
        raise HTTPException(status_code=404, detail="Message not found")
    except GroupMessageForbiddenException:
        raise HTTPException(status_code=403, detail="Cannot edit another user's message")
    return ApiResponse(status_code=200, data=message.model_dump(mode="json"), message="Message updated")
