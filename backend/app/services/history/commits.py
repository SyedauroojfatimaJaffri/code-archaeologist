"""Extract commit history from a cloned repository."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from app.services.repository.validator import RepositoryServiceError

_COMMIT_MARKER = "===COMMIT==="


@dataclass(frozen=True)
class CommitRecord:
    commit_hash: str
    author: str
    message: str
    timestamp: datetime
    diff: str | None


def _parse_timestamp(value: str) -> datetime:
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return datetime.now(timezone.utc)


def _parse_commit_block(block: str, *, include_diff: bool) -> CommitRecord | None:
    block = block.strip()
    if not block:
        return None

    lines = block.splitlines()
    header = lines[0]
    parts = header.split("===", 4)
    if len(parts) < 4:
        return None

    commit_hash, author, timestamp_raw, subject = parts[0], parts[1], parts[2], parts[3]
    initial_body = parts[4] if len(parts) > 4 else ""
    body_lines: list[str] = [initial_body.strip()] if initial_body.strip() else []
    diff_lines: list[str] = []
    mode = "body"

    for line in lines[1:]:
        if include_diff and line.startswith("diff --git"):
            mode = "diff"
        if mode == "body":
            body_lines.append(line)
        else:
            diff_lines.append(line)

    message = subject.strip()
    body = "\n".join(body_lines).strip()
    if body:
        message = f"{message}\n{body}".strip()

    return CommitRecord(
        commit_hash=commit_hash,
        author=author,
        message=message,
        timestamp=_parse_timestamp(timestamp_raw),
        diff="\n".join(diff_lines) if diff_lines else None,
    )


def extract_commits(
    repo_path: Path,
    *,
    limit: int = 500,
    include_diff: bool = True,
) -> list[CommitRecord]:
    """
    Read commit history from a local git clone.

    Uses read-only git commands against the workspace; never executes repository code.
    """
    if not repo_path.exists():
        raise RepositoryServiceError(f"Repository workspace not found: {repo_path}")

    pretty_format = f"{_COMMIT_MARKER}%H===%an===%aI===%s===%b"
    command = [
        "git",
        "-C",
        str(repo_path),
        "log",
        f"-{limit}",
        f"--pretty=format:{pretty_format}",
    ]
    if include_diff:
        command.append("-p")

    try:
        result = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError as exc:
        raise RepositoryServiceError(
            "Git is not installed or not available on PATH."
        ) from exc
    except subprocess.CalledProcessError as exc:
        stderr_text = (exc.stderr or "").strip()
        stderr_lower = stderr_text.lower()
        if (
            "does not have any commits yet" in stderr_lower
            or "unknown revision" in stderr_lower
            or "bad default revision 'head'" in stderr_lower
            or "fatal: your current branch" in stderr_lower
        ):
            return []
        raise RepositoryServiceError(stderr_text or "Failed to read commit history.") from exc

    commits: list[CommitRecord] = []
    for raw_block in result.stdout.split(_COMMIT_MARKER):
        record = _parse_commit_block(raw_block, include_diff=include_diff)
        if record:
            commits.append(record)
    return commits
