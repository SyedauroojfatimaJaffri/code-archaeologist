"""Repository file API schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class FileTreeItem(BaseModel):
    file_id: UUID
    path: str
    language: str | None
    size: int


class FileTreeResponse(BaseModel):
    repository_id: UUID
    files: list[FileTreeItem]


class FileDetailResponse(BaseModel):
    file_id: UUID
    repository_id: UUID
    path: str
    language: str | None
    size: int
    hash: str | None
    content: str | None
    created_at: datetime
