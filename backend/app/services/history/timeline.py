"""Build a unified repository history timeline."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from app.services.history.commits import CommitRecord
from app.services.history.issues import IssueRecord
from app.services.history.pull_requests import PullRequestRecord


class TimelineEventType(str, Enum):
    COMMIT = "commit"
    PULL_REQUEST = "pull_request"
    ISSUE = "issue"


@dataclass(frozen=True)
class TimelineEvent:
    event_type: TimelineEventType
    event_id: str
    title: str
    author: str
    timestamp: datetime
    summary: str | None = None
    state: str | None = None


def build_timeline(
    commits: list[CommitRecord],
    pull_requests: list[PullRequestRecord],
    issues: list[IssueRecord],
) -> list[TimelineEvent]:
    """Merge commits, pull requests, and issues into a single chronological feed."""
    events: list[TimelineEvent] = []

    for commit in commits:
        events.append(
            TimelineEvent(
                event_type=TimelineEventType.COMMIT,
                event_id=commit.commit_hash,
                title=commit.message.splitlines()[0] if commit.message else commit.commit_hash,
                author=commit.author,
                timestamp=commit.timestamp,
                summary=commit.message,
            )
        )

    for pull_request in pull_requests:
        events.append(
            TimelineEvent(
                event_type=TimelineEventType.PULL_REQUEST,
                event_id=pull_request.external_id,
                title=pull_request.title,
                author=pull_request.author,
                timestamp=pull_request.created_at,
                summary=pull_request.body,
                state=pull_request.state,
            )
        )

    for issue in issues:
        events.append(
            TimelineEvent(
                event_type=TimelineEventType.ISSUE,
                event_id=issue.external_id,
                title=issue.title,
                author=issue.author,
                timestamp=issue.created_at,
                summary=issue.body,
                state=issue.state,
            )
        )

    return sorted(events, key=lambda event: event.timestamp, reverse=True)
