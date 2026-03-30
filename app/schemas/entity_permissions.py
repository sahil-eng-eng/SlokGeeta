"""Schemas for fine-grained entity permissions (ABAC)."""

from pydantic import BaseModel
from app.constants.enums import EntityType, PermissionLevel


class SetEntityPermissionRequest(BaseModel):
    user_id: str
    permission_level: PermissionLevel
    is_hidden: bool = False


class EntityPermissionResponse(BaseModel):
    id: str
    user_id: str
    username: str
    entity_type: EntityType
    entity_id: str
    permission_level: str
    is_structural: bool
    is_hidden: bool

    model_config = {"from_attributes": True}
