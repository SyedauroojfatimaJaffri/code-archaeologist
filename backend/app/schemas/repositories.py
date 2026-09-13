"""Repository API schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, HttpUrl


class RepositoryCreateRequest(BaseModel):
    github_url: HttpUrl | str = Field(..., examples=["https://github.com/example/repo"])


class RepositoryCreateResponse(BaseModel):
    repository_id: UUID
    github_url: str
    status: str


class RepositorySummary(BaseModel):
    repository_id: UUID
    github_url: str
    name: str
    owner: str
    default_branch: str | None
    status: str
    created_at: datetime
    updated_at: datetime


class RepositoryDetailResponse(BaseModel):
    repository_id: UUID
    github_url: str
    name: str
    owner: str
    default_branch: str | None
    status: str
    latest_analysis_status: str | None = None
    created_at: datetime
    updated_at: datetime
