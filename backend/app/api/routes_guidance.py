"""Developer guidance routes."""

from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from app.core.security import CurrentUser, DbSession, require_repository
from app.schemas.guidance import GuidanceRequest, GuidanceResponse
from app.services.integration.pipeline import run_developer_guidance

router = APIRouter(prefix="/repositories/{repository_id}/guidance", tags=["guidance"])


@router.post("", response_model=GuidanceResponse)
def create_guidance(
    repository_id: UUID,
    payload: GuidanceRequest,
    db: DbSession,
    user: CurrentUser,
) -> GuidanceResponse:
    require_repository(db, repository_id, user.user_id)
    try:
        return run_developer_guidance(repository_id, payload.task)
    except NotImplementedError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": {
                    "code": "MODULE_NOT_AVAILABLE",
                    "message": str(exc),
                }
            },
        ) from exc
