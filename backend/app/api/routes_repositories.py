"""Repository management routes."""

from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from app.core.security import CurrentUser, DbSession, require_repository
from app.models.db_models import AnalysisJob, Repository
from app.schemas.repositories import (
    RepositoryCreateRequest,
    RepositoryCreateResponse,
    RepositoryDetailResponse,
    RepositorySummary,
)
from app.services.repository import ValidationError, validate_public_repository

router = APIRouter(prefix="/repositories", tags=["repositories"])


def _latest_analysis_status(db, repository_id: UUID) -> str | None:
    job = (
        db.query(AnalysisJob)
        .filter(AnalysisJob.repository_id == repository_id)
        .order_by(AnalysisJob.created_at.desc())
        .first()
    )
    return job.status if job else None


@router.post("", response_model=RepositoryCreateResponse, status_code=status.HTTP_201_CREATED)
def create_repository(
    payload: RepositoryCreateRequest,
    db: DbSession,
    user: CurrentUser,
) -> RepositoryCreateResponse:
    from app.core.config import get_settings

    settings = get_settings()
    github_url = str(payload.github_url)

    try:
        validation = validate_public_repository(
            github_url,
            github_token=settings.github_token,
        )
    except ValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": {"code": "INVALID_REPOSITORY", "message": str(exc)}},
        ) from exc

    existing = (
        db.query(Repository)
        .filter(Repository.user_id == user.user_id, Repository.github_url == validation.repo.github_url)
        .first()
    )
    if existing:
        return RepositoryCreateResponse(
            repository_id=existing.id,
            github_url=existing.github_url,
            status=existing.status,
        )

    repository = Repository(
        user_id=user.user_id,
        github_url=validation.repo.github_url,
        name=validation.repo.name,
        owner=validation.repo.owner,
        default_branch=validation.repo.default_branch,
        status="created",
    )
    db.add(repository)
    db.commit()
    db.refresh(repository)

    return RepositoryCreateResponse(
        repository_id=repository.id,
        github_url=repository.github_url,
        status=repository.status,
    )


@router.get("", response_model=list[RepositorySummary])
def list_repositories(db: DbSession, user: CurrentUser) -> list[RepositorySummary]:
    repositories = (
        db.query(Repository)
        .filter(Repository.user_id == user.user_id)
        .order_by(Repository.created_at.desc())
        .all()
    )
    return [
        RepositorySummary(
            repository_id=repo.id,
            github_url=repo.github_url,
            name=repo.name,
            owner=repo.owner,
            default_branch=repo.default_branch,
            status=repo.status,
            created_at=repo.created_at,
            updated_at=repo.updated_at,
        )
        for repo in repositories
    ]


@router.get("/{repository_id}", response_model=RepositoryDetailResponse)
def get_repository(
    repository_id: UUID,
    db: DbSession,
    user: CurrentUser,
) -> RepositoryDetailResponse:
    repository = require_repository(db, repository_id, user.user_id)
    return RepositoryDetailResponse(
        repository_id=repository.id,
        github_url=repository.github_url,
        name=repository.name,
        owner=repository.owner,
        default_branch=repository.default_branch,
        status=repository.status,
        latest_analysis_status=_latest_analysis_status(db, repository.id),
        created_at=repository.created_at,
        updated_at=repository.updated_at,
    )
