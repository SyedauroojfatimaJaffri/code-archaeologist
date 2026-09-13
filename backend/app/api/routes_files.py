"""Repository file explorer routes."""

from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from app.core.security import CurrentUser, DbSession, require_repository
from app.models.db_models import RepositoryFile
from app.schemas.files import FileDetailResponse, FileTreeItem, FileTreeResponse

router = APIRouter(prefix="/repositories/{repository_id}/files", tags=["files"])


@router.get("", response_model=FileTreeResponse)
def list_repository_files(
    repository_id: UUID,
    db: DbSession,
    user: CurrentUser,
) -> FileTreeResponse:
    require_repository(db, repository_id, user.user_id)
    files = (
        db.query(RepositoryFile)
        .filter(RepositoryFile.repository_id == repository_id)
        .order_by(RepositoryFile.path.asc())
        .all()
    )
    return FileTreeResponse(
        repository_id=repository_id,
        files=[
            FileTreeItem(
                file_id=file.id,
                path=file.path,
                language=file.language,
                size=file.size,
            )
            for file in files
        ],
    )


@router.get("/{path:path}", response_model=FileDetailResponse)
def get_repository_file(
    repository_id: UUID,
    path: str,
    db: DbSession,
    user: CurrentUser,
) -> FileDetailResponse:
    require_repository(db, repository_id, user.user_id)
    file_record = (
        db.query(RepositoryFile)
        .filter(
            RepositoryFile.repository_id == repository_id,
            RepositoryFile.path == path,
        )
        .first()
    )
    if file_record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "FILE_NOT_FOUND",
                    "message": "File was not found in this repository.",
                }
            },
        )

    return FileDetailResponse(
        file_id=file_record.id,
        repository_id=file_record.repository_id,
        path=file_record.path,
        language=file_record.language,
        size=file_record.size,
        hash=file_record.hash,
        content=file_record.content,
        created_at=file_record.created_at,
    )
