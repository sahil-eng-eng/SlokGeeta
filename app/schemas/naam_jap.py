"""Pydantic schemas for NaamJap."""

from datetime import date
from typing import Optional
from pydantic import BaseModel


class SetNaamTargetRequest(BaseModel):
    start_date: date
    end_date: date
    total_goal: int


class NaamTargetResponse(BaseModel):
    id: str
    owner_id: str
    start_date: date
    end_date: date
    total_goal: int

    model_config = {"from_attributes": True}


class CreateJapEntryRequest(BaseModel):
    entry_date: date
    time_slot: str
    count: int


class JapEntryResponse(BaseModel):
    id: str
    owner_id: str
    entry_date: date
    time_slot: str
    count: int

    model_config = {"from_attributes": True}


class DayLogResponse(BaseModel):
    date: str
    entries: list[JapEntryResponse]
    total: int


# ── Instant Jap ───────────────────────────────────────────────────────────────

class SaveInstantJapRequest(BaseModel):
    count: int
    target: int = 108
    duration_seconds: int
    completed: bool = False


class InstantJapSessionResponse(BaseModel):
    id: str
    owner_id: str
    count: int
    target: int
    duration_seconds: int
    completed: bool
    session_date: date
    created_at: str

    model_config = {"from_attributes": True}
