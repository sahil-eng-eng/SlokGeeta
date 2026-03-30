"""Schedule models — ScheduleVersion and ScheduleCheckIn."""

from datetime import date as date_type
from sqlalchemy import String, Integer, Boolean, Date, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import BaseModel


class ScheduleVersion(BaseModel):
    """A user's timetable version with optional self-reward."""

    __tablename__ = "schedule_versions"

    owner_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    # list of {id, time, activity}
    items: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    # list of day name strings e.g. ["Mon", "Tue"]
    applies_to: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    reward: Mapped[str | None] = mapped_column(String(300), nullable=True)
    reward_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


class ScheduleCheckIn(BaseModel):
    """A daily check-in against a schedule version."""

    __tablename__ = "schedule_checkins"

    owner_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    version_id: Mapped[str] = mapped_column(
        String, ForeignKey("schedule_versions.id", ondelete="SET NULL"), nullable=True
    )
    check_in_date: Mapped[date_type] = mapped_column(Date, nullable=False, index=True)
    # list of {id, activity, done}
    items: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    alignment: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
