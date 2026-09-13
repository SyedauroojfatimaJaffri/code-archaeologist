"""Knowledge, knowledge gaps, and offboarding API schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class KnowledgeGapResponse(BaseModel):
    gap_id: UUID
    question: str
    context: str | None = None
    priority: str | None = None
    status: str
    created_at: datetime


class KnowledgeGapListResponse(BaseModel):
    repository_id: UUID
    gaps: list[KnowledgeGapResponse]


class KnowledgeGapAnswerRequest(BaseModel):
    answer: str = Field(..., min_length=3)


class KnowledgeGapAnswerResponse(BaseModel):
    gap_id: UUID
    knowledge_item_id: UUID
    status: str


class KnowledgeItemResponse(BaseModel):
    knowledge_item_id: UUID
    title: str
    content: str
    source: str
    created_at: datetime
    updated_at: datetime


class KnowledgeListResponse(BaseModel):
    repository_id: UUID
    items: list[KnowledgeItemResponse]


class OffboardingCreateRequest(BaseModel):
    contributor: str = Field(..., min_length=1)


class OffboardingCreateResponse(BaseModel):
    session_id: UUID
    status: str


class OffboardingQuestionResponse(BaseModel):
    question_id: UUID
    question: str
    priority: str | None = None
    answer: str | None = None
    status: str


class OffboardingSessionResponse(BaseModel):
    session_id: UUID
    repository_id: UUID
    contributor: str | None = None
    status: str
    questions: list[OffboardingQuestionResponse] = Field(default_factory=list)
    risk_areas: list[str] = Field(default_factory=list)
    knowledge_transfer_results: list[str] = Field(default_factory=list)
    created_at: datetime
    completed_at: datetime | None = None
