"""Developer guidance API schemas."""

from pydantic import BaseModel, Field


class GuidanceRequest(BaseModel):
    task: str = Field(..., min_length=3)


class GuidanceStep(BaseModel):
    title: str
    files: list[str]
    reasoning: str


class GuidanceResponse(BaseModel):
    task: str
    steps: list[GuidanceStep]
