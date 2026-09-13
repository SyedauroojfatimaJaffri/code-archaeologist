"""Repository management and ingestion routes."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, HTTPException, status

from app.core.security import CurrentUser, DbSession, require_repository
from app.models.db_models import AnalysisJob, Repository
from app.schemas.repositories import (
    RepositoryCreateRequest,
    RepositoryCreateResponse,
    RepositoryDeleteResponse,
    RepositoryDetailResponse,
    RepositoryStatusResponse,
    RepositorySummary,
)
from app.services.integration.pipeline import run_analysis_job
from app.services.repository import ValidationError, validate_public_repository

router = APIRouter(prefix="/repositories", tags=["repositories"])


def _latest_job(db: DbSession, repository_id: UUID) -> AnalysisJob | None:
    return (
        db.query(AnalysisJob)
        .filter(AnalysisJob.repository_id == repository_id)
        .order_by(AnalysisJob.created_at.desc())
        .first()
    )


@router.post("", response_model=RepositoryCreateResponse, status_code=status.HTTP_201_CREATED)
def create_and_ingest_repository(
    payload: RepositoryCreateRequest,
    background_tasks: BackgroundTasks,
    db: DbSession,
    user: CurrentUser,
) -> RepositoryCreateResponse:
    """
    Validate public repository, create repository record, and kick off background ingestion.
    Returns immediately with status 'processing'.
    """
    from app.core.config import get_settings

    settings = get_settings()
    github_url = str(payload.github_url or payload.url)

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
        # If existing repository is already analyzed or running, return its current status
        job = _latest_job(db, existing.id)
        if not job or job.status in ["failed"]:
            # Start new analysis job
            new_job = AnalysisJob(repository_id=existing.id, status="queued")
            existing.status = "processing"
            db.add(new_job)
            db.commit()
            db.refresh(new_job)
            background_tasks.add_task(run_analysis_job, new_job.id)
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
        status="processing",
    )
    db.add(repository)
    db.commit()
    db.refresh(repository)

    # Create initial analysis job and launch background ingestion
    job = AnalysisJob(repository_id=repository.id, status="queued")
    db.add(job)
    db.commit()
    db.refresh(job)

    background_tasks.add_task(run_analysis_job, job.id)

    return RepositoryCreateResponse(
        repository_id=repository.id,
        github_url=repository.github_url,
        status="processing",
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
    latest_job = _latest_job(db, repository.id)
    return RepositoryDetailResponse(
        repository_id=repository.id,
        github_url=repository.github_url,
        name=repository.name,
        owner=repository.owner,
        default_branch=repository.default_branch,
        status=repository.status,
        latest_analysis_status=latest_job.status if latest_job else None,
        created_at=repository.created_at,
        updated_at=repository.updated_at,
    )


@router.get("/{repository_id}/status", response_model=RepositoryStatusResponse)
def get_repository_status(
    repository_id: UUID,
    db: DbSession,
    user: CurrentUser,
) -> RepositoryStatusResponse:
    """Polling endpoint for analysis progress tracking."""
    repository = require_repository(db, repository_id, user.user_id)
    latest_job = _latest_job(db, repository.id)

    # Determine status string
    overall_status = repository.status
    error_msg = None
    if latest_job:
        if latest_job.status == "failed":
            overall_status = "failed"
            error_msg = latest_job.error_message
        elif latest_job.status == "completed":
            overall_status = "completed"
        elif overall_status not in ["failed", "completed"]:
            overall_status = latest_job.status

    return RepositoryStatusResponse(
        repository_id=repository.id,
        status=overall_status,
        error_message=error_msg,
        latest_analysis_status=latest_job.status if latest_job else None,
    )


@router.delete("/{repository_id}", response_model=RepositoryDeleteResponse)
def delete_repository(
    repository_id: UUID,
    db: DbSession,
    user: CurrentUser,
) -> RepositoryDeleteResponse:
    repository = require_repository(db, repository_id, user.user_id)
    db.delete(repository)
    db.commit()
    return RepositoryDeleteResponse(repository_id=repository_id, status="deleted")
