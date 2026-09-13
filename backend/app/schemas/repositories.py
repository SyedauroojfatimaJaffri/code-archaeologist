from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, model_validator


class RepositoryCreateRequest(BaseModel):
    github_url: str | None = None
    url: str | None = None

    @model_validator(mode="before")
    @classmethod
    def check_url(cls, data: Any) -> Any:
        if isinstance(data, dict):
            url_val = data.get("url") or data.get("github_url")
            if not url_val:
                raise ValueError("A repository URL ('url' or 'github_url') is required.")
            data["github_url"] = str(url_val)
            data["url"] = str(url_val)
        return data


class RepositoryCreateResponse(BaseModel):
    repository_id: UUID
    github_url: str
    status: str


class RepositorySummary(BaseModel):
    repository_id: UUID
    github_url: str
    name: str
    owner: str
    default_branch: str | None = None
    status: str
    created_at: datetime
    updated_at: datetime


class RepositoryDetailResponse(BaseModel):
    repository_id: UUID
    github_url: str
    name: str
    owner: str
    default_branch: str | None = None
    status: str
    latest_analysis_status: str | None = None
    created_at: datetime
    updated_at: datetime


class RepositoryStatusResponse(BaseModel):
    repository_id: UUID
    status: str
    error_message: str | None = None
    latest_analysis_status: str | None = None


class RepositoryDeleteResponse(BaseModel):
    repository_id: UUID
    status: str
