"""Granth models — digital book collection with page-level content and reading progress."""

from datetime import datetime
from typing import Optional
from sqlalchemy import String, Text, Integer, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import BaseModel


class Granth(BaseModel):
    """A sacred text (granth) managed by admins."""

    __tablename__ = "granths"

    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    author: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    language: Mapped[str] = mapped_column(String(50), nullable=False, server_default="punjabi")
    total_pages: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    cover_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    uploaded_by: Mapped[str] = mapped_column(String, nullable=False)

    pages: Mapped[list["GranthPage"]] = relationship(
        "GranthPage", back_populates="granth", cascade="all, delete-orphan",
        order_by="GranthPage.page_number",
    )


class GranthPage(BaseModel):
    """A single page of a granth — stores extracted/AI-processed text."""

    __tablename__ = "granth_pages"

    granth_id: Mapped[str] = mapped_column(
        String, ForeignKey("granths.id", ondelete="CASCADE"), nullable=False, index=True
    )
    page_number: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False, default="")
    image_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    granth: Mapped["Granth"] = relationship("Granth", back_populates="pages")


class UserGranthProgress(BaseModel):
    """Tracks a user's reading progress within a granth."""

    __tablename__ = "user_granth_progress"

    user_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    granth_id: Mapped[str] = mapped_column(
        String, ForeignKey("granths.id", ondelete="CASCADE"), nullable=False, index=True
    )
    current_page: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    last_read_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
