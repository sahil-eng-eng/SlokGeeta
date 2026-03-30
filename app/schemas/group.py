"""Group chat schemas — request and response shapes."""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field


class CreateGroupRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    description: Optional[str] = Field(default=None, max_length=300)
    member_ids: list[str] = Field(default_factory=list)


class UpdateGroupRequest(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=120)
    description: Optional[str] = Field(default=None, max_length=300)
    avatar_url: Optional[str] = Field(default=None)


class GroupMemberResponse(BaseModel):
    user_id: str
    username: str
    display_name: Optional[str]
    avatar_url: Optional[str]
    role: str  # owner | co_admin | member
    is_admin: bool  # True if role is owner or co_admin
    is_online: bool = False
    last_seen_at: Optional[str] = None

    model_config = {"from_attributes": True}


class GroupResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    creator_id: str
    avatar_url: Optional[str] = None
    member_count: int
    members: list[GroupMemberResponse] = Field(default_factory=list)
    created_at: str

    model_config = {"from_attributes": True}


class GroupMessageResponse(BaseModel):
    id: str
    group_id: str
    sender_id: str
    sender_username: str
    sender_display_name: Optional[str]
    content: str
    is_deleted: bool = False
    edited_at: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class SendGroupMessageRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=4000)


class EditGroupMessageRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=4000)


class AddGroupMembersRequest(BaseModel):
    user_ids: list[str] = Field(..., min_length=1)


class UpdateMemberRoleRequest(BaseModel):
    role: str = Field(..., pattern="^(co_admin|member)$")
