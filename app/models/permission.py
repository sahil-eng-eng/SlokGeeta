"""Permission model for entity-level access control."""

from sqlalchemy import String, Enum as SAEnum, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import BaseModel
from app.constants.enums import PermissionRole, EntityType


class Permission(BaseModel):
    __tablename__ = "permissions"
    __table_args__ = (
        UniqueConstraint(
            "user_id", "entity_type", "entity_id",
            name="uq_user_entity_permission",
        ),
    )

    user_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    entity_type: Mapped[str] = mapped_column(
        SAEnum(
            EntityType,
            name="entity_type_enum",
            create_constraint=True,
            values_callable=lambda obj: [e.value for e in obj],
        ),
        nullable=False,
    )
    entity_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    role: Mapped[str] = mapped_column(
        SAEnum(
            PermissionRole,
            name="permission_role_enum",
            create_constraint=True,
            values_callable=lambda obj: [e.value for e in obj],
        ),
        nullable=False,
    )
    granted_by: Mapped[str] = mapped_column(String, nullable=False)
