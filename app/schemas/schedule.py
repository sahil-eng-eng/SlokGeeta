"""Schedule schemas — request and response shapes."""

from datetime import date
from typing import Optional
from pydantic import BaseModel, Field


class ScheduleItemSchema(BaseModel):
    id: str
    # Legacy: single 'time' string. New: start_time + end_time pair.
    time: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    activity: str


class CreateScheduleVersionRequest(BaseModel):
    items: list[ScheduleItemSchema] = Field(..., min_length=1)
    applies_to: list[str] = Field(..., min_length=1)
    reward: str | None = None
    reward_days: int | None = Field(default=None, ge=1)


class UpdateScheduleVersionRequest(BaseModel):
    items: list[ScheduleItemSchema] = Field(..., min_length=1)
    applies_to: list[str] = Field(..., min_length=1)
    reward: str | None = None
    reward_days: int | None = Field(default=None, ge=1)


class ScheduleVersionResponse(BaseModel):
    id: str
    items: list[ScheduleItemSchema]
    applies_to: list[str]
    reward: str | None
    reward_days: int | None
    is_active: bool
    created_at: str

    model_config = {"from_attributes": True}


class CheckInItemSchema(BaseModel):
    id: str
    activity: str
    done: bool


class CreateCheckInRequest(BaseModel):
    version_id: str
    items: list[CheckInItemSchema] = Field(..., min_length=1)


class CheckInResponse(BaseModel):
    id: str
    version_id: str | None
    check_in_date: str
    items: list[CheckInItemSchema]
    alignment: int
    created_at: str

    model_config = {"from_attributes": True}
