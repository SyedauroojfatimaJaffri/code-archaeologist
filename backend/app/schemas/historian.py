"""Historian question API schemas."""

from pydantic import BaseModel, Field


class HistorianQuestionRequest(BaseModel):
    question: str = Field(..., min_length=3)


class EvidenceItem(BaseModel):
    source_type: str
    source_id: str | None = None
    excerpt: str | None = None


class HistorianQuestionResponse(BaseModel):
    answer: str
    evidence: list[EvidenceItem]
    confidence: str
    classification: str
