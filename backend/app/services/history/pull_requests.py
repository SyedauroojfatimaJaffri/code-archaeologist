"""Fetch pull request history from the GitHub REST API."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

import httpx

from app.services.repository.validator import GitHubRepoRef, RepositoryServiceError, github_headers


@dataclass(frozen=True)
class PullRequestRecord:
    external_id: str
    title: str
    body: str | None
    author: str
    state: str
    created_at: datetime
    merged_at: datetime | None


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _paginate_github(
    url: str,
    *,
    github_token: str | None,
    timeout: float,
    params: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    page = 1
    query = dict(params or {})
    query.setdefault("per_page", 100)
    query.setdefault("state", "all")

    try:
        with httpx.Client(timeout=timeout) as client:
            while True:
                query["page"] = page
                response = client.get(
                    url,
                    headers=github_headers(github_token),
                    params=query,
                )
                if response.status_code == 404:
                    raise RepositoryServiceError("Repository pull requests were not found.")
                if response.status_code == 403:
                    raise RepositoryServiceError(
                        "GitHub API rate limit reached while fetching pull requests. "
                        "Provide a GITHUB_TOKEN for higher limits."
                    )
                if response.status_code >= 400:
                    raise RepositoryServiceError(
                        f"GitHub API returned status {response.status_code} for pull requests."
                    )
                batch = response.json()
                if not batch:
                    break
                items.extend(batch)
                if len(batch) < query["per_page"]:
                    break
                page += 1
    except httpx.HTTPError as exc:
        raise RepositoryServiceError(
            f"Unable to fetch pull requests from GitHub: {exc}"
        ) from exc

    return items


def fetch_pull_requests(
    repo: GitHubRepoRef,
    *,
    github_token: str | None = None,
    timeout: float = 30.0,
    max_items: int = 200,
) -> list[PullRequestRecord]:
    """Fetch pull requests for a public repository via the GitHub REST API."""
    url = f"https://api.github.com/repos/{repo.owner}/{repo.name}/pulls"
    payloads = _paginate_github(url, github_token=github_token, timeout=timeout)[:max_items]

    records: list[PullRequestRecord] = []
    for item in payloads:
        created_at = _parse_datetime(item.get("created_at")) or datetime.now(timezone.utc)
        merged_at = _parse_datetime(item.get("merged_at"))
        user = item.get("user") or {}
        records.append(
            PullRequestRecord(
                external_id=str(item.get("number")),
                title=item.get("title") or "",
                body=item.get("body"),
                author=user.get("login") or "unknown",
                state=item.get("state") or "unknown",
                created_at=created_at,
                merged_at=merged_at,
            )
        )
    return records
