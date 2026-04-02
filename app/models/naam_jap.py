"""NaamJap models — NaamTarget, JapEntry, and InstantJapSession."""

from datetime import date as date_type, datetime
from typing import Optional
from sqlalchemy import String, Text, Integer, Date, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import BaseModel


class NaamTarget(BaseModel):
    """A user's chanting goal for a date range."""

    __tablename__ = "naam_targets"

    owner_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    start_date: Mapped[date_type] = mapped_column(Date, nullable=False)
    end_date: Mapped[date_type] = mapped_column(Date, nullable=False)
    total_goal: Mapped[int] = mapped_column(Integer, nullable=False)


class JapEntry(BaseModel):
    """A single chanting session logged by the user on a specific date."""

    __tablename__ = "jap_entries"

    owner_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    entry_date: Mapped[date_type] = mapped_column(Date, nullable=False, index=True)
    time_slot: Mapped[str] = mapped_column(String(100), nullable=False)
    count: Mapped[int] = mapped_column(Integer, nullable=False)


class InstantJapSession(BaseModel):
    """A quick tap-based jap session — records total taps and duration."""

    __tablename__ = "instant_jap_sessions"

    owner_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    target: Mapped[int] = mapped_column(Integer, nullable=False, default=108)
    duration_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    completed: Mapped[bool] = mapped_column(default=False, server_default="false")
    session_date: Mapped[date_type] = mapped_column(Date, nullable=False, index=True)
