"""Extract contributor statistics from GitHub and local git history."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Any

import httpx

from app.services.repository.validator import GitHubRepoRef, RepositoryServiceError, github_headers


@dataclass(frozen=True)
class ContributorRecord:
    external_id: str
    name: str
    email_hash: str | None
    commit_count: int
    first_seen: datetime | None
    last_seen: datetime | None


def _hash_email(email: str) -> str:
    return sha256(email.strip().lower().encode("utf-8")).hexdigest()


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _fetch_github_contributors(
    repo: GitHubRepoRef,
    *,
    github_token: str | None,
    timeout: float,
) -> list[dict[str, Any]]:
    url = f"https://api.github.com/repos/{repo.owner}/{repo.name}/contributors"
    try:
        with httpx.Client(timeout=timeout) as client:
            response = client.get(
                url,
                headers=github_headers(github_token),
                params={"per_page": 100, "anon": "true"},
            )
    except httpx.HTTPError as exc:
        raise RepositoryServiceError(
            f"Unable to fetch contributors from GitHub: {exc}"
        ) from exc

    if response.status_code >= 400:
        return []
    return response.json()


def _extract_git_contributors(repo_path: Path) -> dict[str, ContributorRecord]:
    command = [
        "git",
        "-C",
        str(repo_path),
        "shortlog",
        "-sne",
        "--all",
    ]
    try:
        result = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
            input="",
        )
    except FileNotFoundError as exc:
        raise RepositoryServiceError(
            "Git is not installed or not available on PATH."
        ) from exc
    except subprocess.CalledProcessError as exc:
        stderr = (exc.stderr or "").strip()
        raise RepositoryServiceError(stderr or "Failed to read git contributors.") from exc

    contributors: dict[str, ContributorRecord] = {}
    for line in result.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split("\t", 1)
        if len(parts) != 2:
            continue
        count_part, identity = parts
        try:
            commit_count = int(count_part.strip())
        except ValueError:
            continue

        name = identity
        email: str | None = None
        if "<" in identity and identity.endswith(">"):
            name = identity[: identity.rindex("<")].strip()
            email = identity[identity.index("<") + 1 : -1].strip()

        external_id = email or name
        email_hash = _hash_email(email) if email else None
        contributors[external_id] = ContributorRecord(
            external_id=external_id,
            name=name or external_id,
            email_hash=email_hash,
            commit_count=commit_count,
            first_seen=None,
            last_seen=None,
        )
    return contributors


def _first_last_seen(repo_path: Path) -> dict[str, tuple[datetime | None, datetime | None]]:
    command = [
        "git",
        "-C",
        str(repo_path),
        "log",
        "--format=%ae|%aI",
    ]
    try:
        result = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError:
        return {}

    seen: dict[str, list[datetime]] = {}
    for line in result.stdout.splitlines():
        if "|" not in line:
            continue
        email, timestamp_raw = line.split("|", 1)
        timestamp = _parse_datetime(timestamp_raw)
        if timestamp is None:
            continue
        seen.setdefault(email.strip().lower(), []).append(timestamp)

    bounds: dict[str, tuple[datetime | None, datetime | None]] = {}
    for email, timestamps in seen.items():
        bounds[email] = (min(timestamps), max(timestamps))
    return bounds


def fetch_contributors(
    repo: GitHubRepoRef,
    *,
    repo_path: Path | None = None,
    github_token: str | None = None,
    timeout: float = 30.0,
) -> list[ContributorRecord]:
    """
    Combine GitHub contributor metadata with local git shortlog statistics.

    When ``repo_path`` is provided, commit counts and first/last seen timestamps
    are derived from the cloned workspace.
    """
    github_payload = _fetch_github_contributors(
        repo, github_token=github_token, timeout=timeout
    )
    git_contributors = _extract_git_contributors(repo_path) if repo_path else {}
    first_last = _first_last_seen(repo_path) if repo_path else {}

    records: dict[str, ContributorRecord] = {}

    for item in github_payload:
        login = item.get("login") or item.get("name") or "unknown"
        commit_count = int(item.get("contributions") or 0)
        records[login] = ContributorRecord(
            external_id=login,
            name=login,
            email_hash=None,
            commit_count=commit_count,
            first_seen=None,
            last_seen=None,
        )

    for external_id, git_record in git_contributors.items():
        email_key = external_id.strip().lower() if "@" in external_id else None
        first_seen, last_seen = (
            first_last.get(email_key, (None, None)) if email_key else (None, None)
        )
        existing = records.get(external_id)
        commit_count = max(existing.commit_count if existing else 0, git_record.commit_count)
        records[external_id] = ContributorRecord(
            external_id=external_id,
            name=git_record.name,
            email_hash=git_record.email_hash,
            commit_count=commit_count,
            first_seen=first_seen,
            last_seen=last_seen,
        )

    return sorted(records.values(), key=lambda item: item.commit_count, reverse=True)
