"""Analysis job API schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class AnalysisStartResponse(BaseModel):
    analysis_job_id: UUID
    status: str


class AnalysisJobResponse(BaseModel):
    analysis_job_id: UUID
    repository_id: UUID
    status: str
    error_message: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime
