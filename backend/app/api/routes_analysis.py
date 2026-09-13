"""Analysis job routes."""

from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, HTTPException, status

from app.core.security import CurrentUser, DbSession, require_repository
from app.models.db_models import AnalysisJob
from app.schemas.analysis import AnalysisJobResponse, AnalysisStartResponse
from app.services.integration.pipeline import run_analysis_job

router = APIRouter(tags=["analysis"])


@router.post(
    "/repositories/{repository_id}/analyze",
    response_model=AnalysisStartResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def start_analysis(
    repository_id: UUID,
    background_tasks: BackgroundTasks,
    db: DbSession,
    user: CurrentUser,
) -> AnalysisStartResponse:
    repository = require_repository(db, repository_id, user.user_id)

    active_job = (
        db.query(AnalysisJob)
        .filter(
            AnalysisJob.repository_id == repository.id,
            AnalysisJob.status.in_(["queued", "running"]),
        )
        .first()
    )
    if active_job:
        return AnalysisStartResponse(
            analysis_job_id=active_job.id,
            status=active_job.status,
        )

    job = AnalysisJob(repository_id=repository.id, status="queued")
    repository.status = "queued"
    db.add(job)
    db.commit()
    db.refresh(job)

    background_tasks.add_task(run_analysis_job, job.id)

    return AnalysisStartResponse(analysis_job_id=job.id, status=job.status)


@router.get("/analysis/{analysis_job_id}", response_model=AnalysisJobResponse)
def get_analysis_job(
    analysis_job_id: UUID,
    db: DbSession,
    user: CurrentUser,
) -> AnalysisJobResponse:
    job = db.query(AnalysisJob).filter(AnalysisJob.id == analysis_job_id).first()
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "ANALYSIS_JOB_NOT_FOUND",
                    "message": "Analysis job was not found.",
                }
            },
        )

    require_repository(db, job.repository_id, user.user_id)

    return AnalysisJobResponse(
        analysis_job_id=job.id,
        repository_id=job.repository_id,
        status=job.status,
        error_message=job.error_message,
        started_at=job.started_at,
        completed_at=job.completed_at,
        created_at=job.created_at,
    )
