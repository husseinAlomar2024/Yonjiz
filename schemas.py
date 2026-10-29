"""Pydantic request/response schemas."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator


class TodoPayload(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    description: str = Field(default="", max_length=1000)
    priority: int = Field(default=3, ge=1, le=5)
    complete: bool = False
    deadline: Optional[datetime] = None

    @field_validator("title")
    @classmethod
    def clean_title(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Give the task a title.")
        return value

    @field_validator("description")
    @classmethod
    def clean_description(cls, value: str) -> str:
        return value.strip()

    @field_validator("deadline")
    @classmethod
    def normalize_deadline(cls, value: Optional[datetime]) -> Optional[datetime]:
        if value is None:
            return None
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)


class TodoCompletePayload(BaseModel):
    complete: bool


class TodoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str
    priority: int
    complete: bool
    owner_id: int
    created_at: datetime
    updated_at: datetime
    deadline: Optional[datetime]
    completed_at: Optional[datetime]

    @field_serializer("created_at", "updated_at", "deadline", "completed_at")
    def serialize_datetime(self, value: Optional[datetime]) -> Optional[str]:
        if value is None:
            return None
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
