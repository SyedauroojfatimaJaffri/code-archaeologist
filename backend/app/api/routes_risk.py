"""Risk analysis routes."""

from uuid import UUID

from fastapi import APIRouter

from app.core.security import CurrentUser, DbSession, require_repository
from app.models.db_models import RepositoryFile, RiskRecord
from app.schemas.risk import RiskListResponse, RiskRecordResponse, RiskSignal

router = APIRouter(prefix="/repositories/{repository_id}/risks", tags=["risk"])


@router.get("", response_model=RiskListResponse)
def list_risks(
    repository_id: UUID,
    db: DbSession,
    user: CurrentUser,
) -> RiskListResponse:
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

    return RiskListResponse(
        repository_id=repository_id,
        risks=[
            RiskRecordResponse(
                file_id=record.file_id,
                path=file_paths.get(record.file_id) if record.file_id else None,
                score=record.score,
                signals=[
                    RiskSignal(name=str(key), value=value)
                    for key, value in (record.signals or {}).items()
                ],
                explanation=record.explanation,
                created_at=record.created_at,
            )
            for record in records
        ],
    )
