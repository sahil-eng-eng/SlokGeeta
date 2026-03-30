"""SharedLink model — short-code links to books, shloks, or meanings."""

import random
import string
from sqlalchemy import String, Boolean, DateTime, Enum as SAEnum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import BaseModel
from app.constants.enums import LinkTargetType


def _generate_code() -> str:
    """Generate a random 8-character alphanumeric code."""
    chars = string.ascii_letters + string.digits
    return "".join(random.choices(chars, k=8))


class SharedLink(BaseModel):
    __tablename__ = "shared_links"

    short_code: Mapped[str] = mapped_column(
        String(16), unique=True, nullable=False, default=_generate_code
    )
    target_type: Mapped[str] = mapped_column(
        SAEnum(
            LinkTargetType,
            name="link_target_type_enum",
            create_constraint=True,
            values_callable=lambda obj: [e.value for e in obj],
        ),
        nullable=False,
    )
    target_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    creator_id: Mapped[str] = mapped_column(
        String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    expires_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
