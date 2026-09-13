"""Knowledge and Knowledge Gap API routes."""

from uuid import UUID

from fastapi import APIRouter

from app.core.security import CurrentUser, DbSession, require_repository
from app.models.db_models import KnowledgeGap, KnowledgeItem
from app.schemas.knowledge import (
    KnowledgeGapAnswerRequest,
    KnowledgeGapAnswerResponse,
    KnowledgeGapListResponse,
    KnowledgeGapResponse,
    KnowledgeItemResponse,
    KnowledgeListResponse,
)
from app.services.integration.pipeline import run_knowledge_gap_answer

router = APIRouter(prefix="/repositories/{repository_id}", tags=["knowledge"])


@router.get("/knowledge-gaps", response_model=KnowledgeGapListResponse)
def list_knowledge_gaps(
    repository_id: UUID,
    db: DbSession,
    user: CurrentUser,
) -> KnowledgeGapListResponse:
    require_repository(db, repository_id, user.user_id)
    gaps = (
        db.query(KnowledgeGap)
        .filter(KnowledgeGap.repository_id == repository_id)
        .order_by(KnowledgeGap.created_at.desc())
        .all()
    )

    return KnowledgeGapListResponse(
        repository_id=repository_id,
        gaps=[
            KnowledgeGapResponse(
                gap_id=gap.id,
                question=gap.question,
                context=gap.context,
                priority=gap.priority,
                status=gap.status,
                created_at=gap.created_at,
            )
            for gap in gaps
        ],
    )


@router.post("/knowledge-gaps/{gap_id}/answer", response_model=KnowledgeGapAnswerResponse)
def answer_knowledge_gap(
    repository_id: UUID,
    gap_id: UUID,
    payload: KnowledgeGapAnswerRequest,
    db: DbSession,
    user: CurrentUser,
) -> KnowledgeGapAnswerResponse:
    require_repository(db, repository_id, user.user_id)
    return run_knowledge_gap_answer(
        repository_id=repository_id,
        gap_id=gap_id,
        answer=payload.answer,
        user_id=user.user_id,
        db=db,
    )


@router.get("/knowledge", response_model=KnowledgeListResponse)
def list_knowledge_items(
    repository_id: UUID,
    db: DbSession,
    user: CurrentUser,
) -> KnowledgeListResponse:
    require_repository(db, repository_id, user.user_id)
    items = (
        db.query(KnowledgeItem)
        .filter(KnowledgeItem.repository_id == repository_id)
        .order_by(KnowledgeItem.created_at.desc())
        .all()
    )

    return KnowledgeListResponse(
        repository_id=repository_id,
        items=[
            KnowledgeItemResponse(
                knowledge_item_id=item.id,
                title=item.title,
                content=item.content,
                source=item.source,
                created_at=item.created_at,
                updated_at=item.updated_at,
            )
            for item in items
        ],
    )
