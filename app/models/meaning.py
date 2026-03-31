"""Meaning model — nested interpretations of shloks."""

from sqlalchemy import String, Text, Integer, Enum as SAEnum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import BaseModel
from app.constants.enums import ApprovalStatus, Visibility


class Meaning(BaseModel):
    __tablename__ = "meanings"

    shlok_id: Mapped[str] = mapped_column(
        String, ForeignKey("shloks.id", ondelete="CASCADE"), nullable=False, index=True
    )
    parent_id: Mapped[str | None] = mapped_column(
        String,
        ForeignKey("meanings.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    author_id: Mapped[str] = mapped_column(
        String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    status: Mapped[str] = mapped_column(
        SAEnum(
            ApprovalStatus,
            name="approval_status_enum",
            create_constraint=True,
            create_type=False,
            values_callable=lambda obj: [e.value for e in obj],
        ),
        default=ApprovalStatus.APPROVED,
        server_default=ApprovalStatus.APPROVED.value,
    )
    vote_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    visibility: Mapped[str] = mapped_column(
        SAEnum(
            Visibility,
            name="visibility_enum",
            create_constraint=True,
            create_type=False,
            values_callable=lambda obj: [e.value for e in obj],
        ),
        default=Visibility.PRIVATE,
        server_default=Visibility.PRIVATE.value,
    )

    # Self-referential relationship for nested reply tree
    children: Mapped[list["Meaning"]] = relationship(
        "Meaning",
        foreign_keys=[parent_id],
        back_populates="parent",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    parent: Mapped["Meaning | None"] = relationship(
        "Meaning",
        foreign_keys=[parent_id],
        back_populates="children",
        remote_side="Meaning.id",
    )
