"""Offboarding session API routes."""

from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from app.core.security import CurrentUser, DbSession, require_repository
from app.models.db_models import (
    Contributor,
    KnowledgeItem,
    OffboardingQuestion,
    OffboardingSession,
    utcnow,
)
from app.schemas.knowledge import (
    OffboardingAnswerRequest,
    OffboardingAnswerResponse,
    OffboardingCreateRequest,
    OffboardingCreateResponse,
    OffboardingQuestionResponse,
    OffboardingReportResponse,
    OffboardingSessionResponse,
)
from app.services.integration.pipeline import run_create_offboarding_session

router = APIRouter(prefix="/repositories/{repository_id}/offboarding", tags=["offboarding"])


@router.post("", response_model=OffboardingCreateResponse, status_code=status.HTTP_201_CREATED)
def create_offboarding_session(
    repository_id: UUID,
    payload: OffboardingCreateRequest,
    db: DbSession,
    user: CurrentUser,
) -> OffboardingCreateResponse:
    require_repository(db, repository_id, user.user_id)
    return run_create_offboarding_session(
        repository_id=repository_id,
        contributor_identifier=payload.contributor,
        db=db,
    )


@router.get("/{session_id}", response_model=OffboardingSessionResponse)
def get_offboarding_session(
    repository_id: UUID,
    session_id: UUID,
    db: DbSession,
    user: CurrentUser,
) -> OffboardingSessionResponse:
    require_repository(db, repository_id, user.user_id)
    offboarding_session = (
        db.query(OffboardingSession)
        .filter(
            OffboardingSession.id == session_id,
            OffboardingSession.repository_id == repository_id,
        )
        .first()
    )
    if offboarding_session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "OFFBOARDING_SESSION_NOT_FOUND",
                    "message": "Offboarding session was not found.",
                }
            },
        )

    questions = (
        db.query(OffboardingQuestion)
        .filter(OffboardingQuestion.session_id == session_id)
        .all()
    )

    contributor_name: str | None = None
    if offboarding_session.contributor_id:
        contrib = db.query(Contributor).filter(Contributor.id == offboarding_session.contributor_id).first()
        if contrib:
            contributor_name = contrib.name or contrib.external_id

    return OffboardingSessionResponse(
        session_id=offboarding_session.id,
        repository_id=offboarding_session.repository_id,
        contributor=contributor_name,
        status=offboarding_session.status,
        questions=[
            OffboardingQuestionResponse(
                question_id=q.id,
                question=q.question,
                priority=q.priority,
                answer=q.answer,
                status=q.status,
            )
            for q in questions
        ],
        risk_areas=[],
        knowledge_transfer_results=[],
        created_at=offboarding_session.created_at,
        completed_at=offboarding_session.completed_at,
    )


@router.post("/{session_id}/answer", response_model=OffboardingAnswerResponse)
def answer_offboarding_question(
    repository_id: UUID,
    session_id: UUID,
    payload: OffboardingAnswerRequest,
    db: DbSession,
    user: CurrentUser,
) -> OffboardingAnswerResponse:
    require_repository(db, repository_id, user.user_id)
    question = (
        db.query(OffboardingQuestion)
        .filter(
            OffboardingQuestion.id == payload.question_id,
            OffboardingQuestion.session_id == session_id,
        )
        .first()
    )
    if question is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "QUESTION_NOT_FOUND",
                    "message": "Offboarding question was not found.",
                }
            },
        )

    question.answer = payload.answer
    question.status = "answered"

    # Preserve answer into permanent knowledge store
    db.add(
        KnowledgeItem(
            repository_id=repository_id,
            user_id=user.user_id,
            title=f"Offboarding Answer: {question.question[:60]}",
            content=payload.answer,
            source="offboarding",
        )
    )

    # Check if all questions in session are answered
    session = db.query(OffboardingSession).filter(OffboardingSession.id == session_id).first()
    if session:
        all_questions = db.query(OffboardingQuestion).filter(OffboardingQuestion.session_id == session_id).all()
        if all(q.status == "answered" for q in all_questions):
            session.status = "completed"
            session.completed_at = utcnow()

    db.commit()

    return OffboardingAnswerResponse(
        question_id=payload.question_id,
        status="answered",
    )


@router.get("/{session_id}/report", response_model=OffboardingReportResponse)
def get_offboarding_report(
    repository_id: UUID,
    session_id: UUID,
    db: DbSession,
    user: CurrentUser,
) -> OffboardingReportResponse:
    require_repository(db, repository_id, user.user_id)
    session = (
        db.query(OffboardingSession)
        .filter(
            OffboardingSession.id == session_id,
            OffboardingSession.repository_id == repository_id,
        )
        .first()
    )
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "OFFBOARDING_SESSION_NOT_FOUND",
                    "message": "Offboarding session was not found.",
                }
            },
        )

    questions = db.query(OffboardingQuestion).filter(OffboardingQuestion.session_id == session_id).all()
    answered = [q for q in questions if q.status == "answered" and q.answer]
    pending = [q for q in questions if q.status != "answered" or not q.answer]

    contributor_name: str | None = None
    if session.contributor_id:
        contrib = db.query(Contributor).filter(Contributor.id == session.contributor_id).first()
        if contrib:
            contributor_name = contrib.name or contrib.external_id

    summary = (
        f"Offboarding knowledge handover for {contributor_name or 'contributor'}. "
        f"Captured {len(answered)} critical architecture decisions and identified {len(pending)} open gap(s)."
    )

    key_decisions = [
        f"{q.question}: {q.answer}" for q in answered
    ] or ["No answered architecture questions recorded yet."]

    undocumented_areas = [
        q.question for q in pending
    ]

    knowledge_items = [
        {"title": q.question, "content": q.answer, "priority": q.priority}
        for q in answered
    ]

    return OffboardingReportResponse(
        session_id=session.id,
        repository_id=session.repository_id,
        contributor=contributor_name,
        summary=summary,
        key_decisions=key_decisions,
        undocumented_areas=undocumented_areas,
        knowledge_items=knowledge_items,
        generated_at=utcnow(),
    )
