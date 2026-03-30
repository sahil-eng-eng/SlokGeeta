"""EntityPermission model — fine-grained ABAC at book / shlok / meaning level.

Each row says "user X has [permission_level] on entity Y of type T".
The is_hidden flag means the entity should not be shown to this user at all.
The is_structural flag indicates auto-granted navigation access when a child
entity was shared — the user can see the parent exists for navigation but
cannot access full content without an explicit non-structural permission.
Lower-level explicit permissions (meaning > shlok > book) take precedence.
"""

from sqlalchemy import String, Boolean, Enum as SAEnum, UniqueConstraint, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import BaseModel
from app.constants.enums import EntityType, PermissionLevel


class EntityPermission(BaseModel):
    __tablename__ = "entity_permissions"
    __table_args__ = (
        UniqueConstraint(
            "user_id", "entity_type", "entity_id",
            name="uq_entity_permission",
        ),
    )

    user_id: Mapped[str] = mapped_column(
        String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    entity_type: Mapped[str] = mapped_column(
        SAEnum(
            EntityType,
            name="entity_type_enum",
            create_constraint=False,           # enum already exists
            values_callable=lambda obj: [e.value for e in obj],
        ),
        nullable=False,
    )
    entity_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    granted_by: Mapped[str] = mapped_column(
        String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    # Single permission level — what the recipient can do with this entity
    permission_level: Mapped[str] = mapped_column(
        SAEnum(
            PermissionLevel,
            name="permission_level_enum",
            create_constraint=True,
            values_callable=lambda obj: [e.value for e in obj],
        ),
        nullable=False,
        default=PermissionLevel.VIEW,
        server_default=PermissionLevel.VIEW.value,
    )

    # Legacy JSONB field kept for backward-compat; new code uses permission_level
    allowed_actions: Mapped[list] = mapped_column(
        JSONB, nullable=False, default=list, server_default="[]"
    )

    # True = auto-granted structural (navigation) access when a child was shared.
    is_structural: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )

    # If true the entity is hidden from this user (overrides everything)
    is_hidden: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
