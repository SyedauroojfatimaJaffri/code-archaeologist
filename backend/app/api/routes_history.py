"""Repository history and timeline routes."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter
from pydantic import BaseModel

from app.core.security import CurrentUser, DbSession, require_repository
from app.models.db_models import Commit, Contributor, Issue, PullRequest
from app.services.history.commits import CommitRecord
from app.services.history.issues import IssueRecord
from app.services.history.pull_requests import PullRequestRecord
from app.services.history.timeline import build_timeline

router = APIRouter(prefix="/repositories/{repository_id}/history", tags=["history"])


class TimelineEventSchema(BaseModel):
    event_type: str
    identifier: str
    title: str
    author: str
    timestamp: str
    summary: str | None = None
    state: str | None = None


class HistoryResponse(BaseModel):
    repository_id: UUID
    events: list[TimelineEventSchema]


@router.get("", response_model=HistoryResponse)
def get_repository_history(
    repository_id: UUID,
    db: DbSession,
    user: CurrentUser,
) -> HistoryResponse:
    """Return chronological excavation of commits, pull requests, and issues."""
    require_repository(db, repository_id, user.user_id)

    db_commits = (
        db.query(Commit)
        .filter(Commit.repository_id == repository_id)
        .order_by(Commit.timestamp.desc())
        .limit(100)
        .all()
    )
    db_prs = (
        db.query(PullRequest)
        .filter(PullRequest.repository_id == repository_id)
        .order_by(PullRequest.created_at.desc())
        .limit(50)
        .all()
    )
    db_issues = (
        db.query(Issue)
        .filter(Issue.repository_id == repository_id)
        .order_by(Issue.created_at.desc())
        .limit(50)
        .all()
    )

    commit_records = [
        CommitRecord(
            commit_hash=c.commit_hash,
            author=c.author or "Unknown",
            message=c.message or "",
            timestamp=c.timestamp or c.created_at if hasattr(c, "created_at") else c.timestamp,
            diff=c.diff,
        )
        for c in db_commits
        if c.timestamp is not None
    ]
    pr_records = [
        PullRequestRecord(
            external_id=pr.external_id,
            title=pr.title,
            author=pr.author or "Unknown",
            created_at=pr.created_at,
            body=pr.body,
            state=pr.state or "open",
        )
        for pr in db_prs
        if pr.created_at is not None
    ]
    issue_records = [
        IssueRecord(
            external_id=issue.external_id,
            title=issue.title,
            author=issue.author or "Unknown",
            created_at=issue.created_at,
            body=issue.body,
            state=issue.state or "open",
        )
        for issue in db_issues
        if issue.created_at is not None
    ]

    timeline = build_timeline(commit_records, pr_records, issue_records)

    return HistoryResponse(
        repository_id=repository_id,
        events=[
            TimelineEventSchema(
                event_type=evt.event_type.value if hasattr(evt.event_type, "value") else str(evt.event_type),
                identifier=evt.event_id,
                title=evt.title,
                author=evt.author,
                timestamp=evt.timestamp.isoformat() if evt.timestamp else "",
                summary=evt.summary,
                state=evt.state,
            )
            for evt in timeline
        ],
    )
