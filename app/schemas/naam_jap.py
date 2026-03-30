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
