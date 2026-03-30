"""ContentRequest model — change requests that need owner approval."""

from sqlalchemy import String, Text, Enum as SAEnum, ForeignKey, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import BaseModel
from app.constants.enums import EntityType, ContentAction, ContentRequestStatus


class ContentRequest(BaseModel):
    __tablename__ = "content_requests"
    __table_args__ = (
        Index("ix_content_request_entity", "entity_type", "entity_id"),
        Index("ix_content_request_requester", "requester_id", "status"),
    )

    requester_id: Mapped[str] = mapped_column(
        String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    entity_type: Mapped[str] = mapped_column(
        SAEnum(
            EntityType,
            name="entity_type_enum",
            create_constraint=False,          # enum already defined by Permission model
            values_callable=lambda obj: [e.value for e in obj],
        ),
        nullable=False,
    )
    entity_id: Mapped[str] = mapped_column(String, nullable=False)
    action: Mapped[str] = mapped_column(
        SAEnum(
            ContentAction,
            name="content_action_enum",
            create_constraint=True,
            values_callable=lambda obj: [e.value for e in obj],
        ),
        nullable=False,
    )
    # Owner of the entity — pre-computed so owners can quickly list incoming requests
    entity_owner_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    proposed_content: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    status: Mapped[str] = mapped_column(
        SAEnum(
            ContentRequestStatus,
            name="content_request_status_enum",
            create_constraint=True,
            values_callable=lambda obj: [e.value for e in obj],
        ),
        nullable=False,
        default=ContentRequestStatus.PENDING,
        server_default=ContentRequestStatus.PENDING.value,
    )
    reviewer_id: Mapped[str | None] = mapped_column(
        String, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    reviewer_note: Mapped[str | None] = mapped_column(Text, nullable=True)
