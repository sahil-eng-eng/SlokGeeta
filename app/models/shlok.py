"""Shlok and ShlokCrossReference models."""

from datetime import datetime
from sqlalchemy import String, Text, Integer, Enum as SAEnum, ARRAY, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import BaseModel
from app.constants.enums import Visibility


class Shlok(BaseModel):
    __tablename__ = "shloks"

    book_id: Mapped[str] = mapped_column(
        String, ForeignKey("books.id", ondelete="CASCADE"), nullable=False, index=True
    )
    owner_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    chapter_number: Mapped[int] = mapped_column(Integer, nullable=True)
    verse_number: Mapped[int] = mapped_column(Integer, nullable=True)
    tags: Mapped[list] = mapped_column(ARRAY(String), default=list, server_default="{}")
    audio_url: Mapped[str] = mapped_column(Text, nullable=True)
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
    scheduled_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    view_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0")


class ShlokCrossReference(BaseModel):
    __tablename__ = "shlok_cross_references"

    source_shlok_id: Mapped[str] = mapped_column(
        String, ForeignKey("shloks.id", ondelete="CASCADE"), nullable=False, index=True
    )
    target_shlok_id: Mapped[str] = mapped_column(
        String, ForeignKey("shloks.id", ondelete="CASCADE"), nullable=False, index=True
    )
    note: Mapped[str] = mapped_column(Text, nullable=True)
