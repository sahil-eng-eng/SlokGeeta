"""NaamJap models — NaamTarget and JapEntry for daily chanting tracker."""

from datetime import date as date_type
from sqlalchemy import String, Text, Integer, Date, ForeignKey
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
