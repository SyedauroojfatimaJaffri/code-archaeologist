"""Historian agent routes."""

from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from app.core.security import CurrentUser, DbSession, require_repository
from app.schemas.historian import HistorianQuestionRequest, HistorianQuestionResponse
from app.services.integration.pipeline import run_historian_question

router = APIRouter(prefix="/repositories/{repository_id}/questions", tags=["historian"])


@router.post("", response_model=HistorianQuestionResponse)
def ask_historian_question(
    repository_id: UUID,
    payload: HistorianQuestionRequest,
    db: DbSession,
    user: CurrentUser,
) -> HistorianQuestionResponse:
    require_repository(db, repository_id, user.user_id)
    try:
        return run_historian_question(repository_id, payload.question)
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
