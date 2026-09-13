"""Validate and parse public GitHub repository URLs."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

import httpx

GITHUB_URL_PATTERN = re.compile(
    r"^https?://(?:www\.)?github\.com/(?P<owner>[\w.-]+)/(?P<name>[\w.-]+?)(?:\.git)?/?(?:#.*)?(?:\?.*)?$",
    re.IGNORECASE,
)


class RepositoryServiceError(Exception):
    """Base error for repository acquisition services."""


class ValidationError(RepositoryServiceError):
    """Raised when a repository URL fails validation."""


@dataclass(frozen=True)
class GitHubRepoRef:
    owner: str
    name: str
    github_url: str
    default_branch: str | None = None
    is_public: bool = False


@dataclass(frozen=True)
class ValidationResult:
    repo: GitHubRepoRef
    metadata: dict[str, Any]


def parse_github_url(url: str) -> GitHubRepoRef:
    """Parse a GitHub repository URL into owner/name components."""
    normalized = url.strip()
    if not normalized:
        raise ValidationError("GitHub URL is required.")

    match = GITHUB_URL_PATTERN.match(normalized)
    if not match:
        raise ValidationError(
            "URL must be a public GitHub repository link, e.g. "
            "https://github.com/owner/repo"
        )

    owner = match.group("owner")
    name = match.group("name").removesuffix(".git")
    canonical_url = f"https://github.com/{owner}/{name}"
    return GitHubRepoRef(owner=owner, name=name, github_url=canonical_url)


def github_headers(token: str | None) -> dict[str, str]:
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "CodeArchaeologist/1.0",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def validate_public_repository(
    url: str,
    *,
    github_token: str | None = None,
    timeout: float = 30.0,
) -> ValidationResult:
    """
    Validate that the URL points to an existing public GitHub repository.

    Uses the GitHub REST API read-only; never clones or executes repository code.
    """
    repo_ref = parse_github_url(url)
    api_url = f"https://api.github.com/repos/{repo_ref.owner}/{repo_ref.name}"

    try:
        with httpx.Client(timeout=timeout) as client:
            response = client.get(api_url, headers=github_headers(github_token))
    except httpx.HTTPError as exc:
        raise RepositoryServiceError(
            f"Unable to reach GitHub API for {repo_ref.github_url}: {exc}"
        ) from exc

    if response.status_code == 404:
        raise ValidationError(
            "Repository was not found or is not publicly accessible."
        )
    if response.status_code == 403:
        raise ValidationError(
            "GitHub API access was denied. Check the token or rate limits."
        )
    if response.status_code >= 400:
        raise ValidationError(
            f"GitHub API returned an unexpected status ({response.status_code})."
        )

    payload = response.json()
    if payload.get("private"):
        raise ValidationError("Only public GitHub repositories are supported.")

    repo = GitHubRepoRef(
        owner=repo_ref.owner,
        name=repo_ref.name,
        github_url=repo_ref.github_url,
        default_branch=payload.get("default_branch"),
        is_public=True,
    )
    metadata = {
        "full_name": payload.get("full_name"),
        "description": payload.get("description"),
        "default_branch": payload.get("default_branch"),
        "size": payload.get("size"),
        "language": payload.get("language"),
    }
    return ValidationResult(repo=repo, metadata=metadata)
