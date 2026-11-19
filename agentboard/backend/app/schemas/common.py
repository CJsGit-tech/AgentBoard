from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class Record(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    revision: int
    created_at: datetime
    updated_at: datetime


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=256)
    purpose: str = ""

    @field_validator("name")
    @classmethod
    def nonblank_name(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Name must contain a non-whitespace character")
        return value.strip()


class ProjectChanges(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=256)
    purpose: str | None = None


class ProjectUpdate(BaseModel):
    expected_revision: int = Field(ge=1)
    changes: ProjectChanges


class ProjectDelete(BaseModel):
    expected_revision: int = Field(ge=1)
    confirm: Literal[True]


class ProjectRecord(Record):
    name: str
    purpose: str


class RoleCreate(BaseModel):
    name: str = Field(min_length=1, max_length=256)
    responsibilities: str = Field(min_length=1, max_length=256)

    @field_validator("name", "responsibilities")
    @classmethod
    def nonblank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Value must contain a non-whitespace character")
        return value.strip()


class RoleChanges(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=256)
    responsibilities: str | None = Field(default=None, min_length=1, max_length=256)


class RoleUpdate(BaseModel):
    expected_revision: int = Field(ge=1)
    changes: RoleChanges


class RoleRecord(Record):
    project_id: UUID
    name: str
    responsibilities: str


class Page(BaseModel):
    items: list
    next_cursor: str | None = None


class ActivityCreate(BaseModel):
    ticket_id: UUID | None
    agent_name: str = Field(min_length=1, max_length=256)
    action: str = Field(min_length=1, max_length=256)
    event_type: Literal["dispatch", "tool_call", "ticket_update", "work"]
    outcome: Literal["started", "success", "failed", "pending", "rejected", "cancelled"]
    summary: str = Field(default="", max_length=2048)
    labels: list[str] = Field(default_factory=list, max_length=16)
    occurred_at: datetime

    @field_validator("agent_name", "action")
    @classmethod
    def nonblank_activity(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Value must contain a non-whitespace character")
        return value.strip()

    @field_validator("labels")
    @classmethod
    def bounded_labels(cls, values: list[str]) -> list[str]:
        if len(set(values)) != len(values) or any(not value or len(value) > 64 for value in values):
            raise ValueError("Labels must be unique and contain 1 to 64 characters")
        return values

    @field_validator("occurred_at")
    @classmethod
    def utc_time(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None or value.utcoffset().total_seconds() != 0:
            raise ValueError("Timestamp must include UTC timezone")
        return value
