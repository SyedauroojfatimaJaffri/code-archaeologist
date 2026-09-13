"""Risk analysis routes."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter
from pydantic import BaseModel

from app.core.security import CurrentUser, DbSession, require_repository
from app.models.db_models import RepositoryFile, RiskRecord

router = APIRouter(tags=["risk"])


class RiskItemSchema(BaseModel):
    file_id: str
    file_path: str | None = None
    path: str | None = None
    score: float
    signals: dict[str, Any] = {}
    explanation: str | None = None


class RiskResponseSchema(BaseModel):
    repository_id: UUID | None = None
    risks: list[RiskItemSchema]


def _get_risks_for_repo(repository_id: UUID, db: DbSession, user: CurrentUser) -> RiskResponseSchema:
    require_repository(db, repository_id, user.user_id)
    records = (
        db.query(RiskRecord)
        .filter(RiskRecord.repository_id == repository_id)
        .order_by(RiskRecord.score.desc())
        .all()
    )

    file_paths: dict[UUID, str] = {}
    file_ids = [record.file_id for record in records if record.file_id]
    if file_ids:
        files = db.query(RepositoryFile).filter(RepositoryFile.id.in_(file_ids)).all()
        file_paths = {file.id: file.path for file in files}

    return RiskResponseSchema(
        repository_id=repository_id,
        risks=[
            RiskItemSchema(
                file_id=str(record.file_id) if record.file_id else str(record.id),
                file_path=file_paths.get(record.file_id) if record.file_id else None,
                path=file_paths.get(record.file_id) if record.file_id else None,
                score=round(record.score, 4),
                signals=record.signals or {},
                explanation=record.explanation,
            )
            for record in records
        ],
    )


@router.get("/repositories/{repository_id}/risks", response_model=RiskResponseSchema)
def list_risks_plural(
    repository_id: UUID,
    db: DbSession,
    user: CurrentUser,
) -> RiskResponseSchema:
    return _get_risks_for_repo(repository_id, db, user)


@router.get("/repositories/{repository_id}/risk", response_model=RiskResponseSchema)
def list_risks_singular(
    repository_id: UUID,
    db: DbSession,
    user: CurrentUser,
) -> RiskResponseSchema:
    return _get_risks_for_repo(repository_id, db, user)
