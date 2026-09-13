"""Risk analysis API schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class RiskSignal(BaseModel):
    name: str
    value: float | int | str | None = None


class RiskRecordResponse(BaseModel):
    file_id: UUID | None
    path: str | None = None
    score: float
    signals: list[RiskSignal] = Field(default_factory=list)
    explanation: str | None = None
    created_at: datetime | None = None


class RiskListResponse(BaseModel):
    repository_id: UUID
    risks: list[RiskRecordResponse]
