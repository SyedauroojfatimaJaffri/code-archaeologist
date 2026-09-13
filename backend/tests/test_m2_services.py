"""Unit tests for M2 Repository Acquisition and Git History Intelligence services."""

from __future__ import annotations

import os
import stat
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import httpx
import pytest

from app.services.history.commits import CommitRecord, extract_commits
from app.services.history.contributors import ContributorRecord, fetch_contributors
from app.services.history.issues import IssueRecord, fetch_issues
from app.services.history.pull_requests import PullRequestRecord, fetch_pull_requests
from app.services.history.timeline import TimelineEvent, TimelineEventType, build_timeline
from app.services.repository.cloner import CloneResult, cleanup_workspace, clone_repository
from app.services.repository.file_tree import FileRecord, build_file_tree
from app.services.repository.language_detector import detect_language
from app.services.repository.validator import (
    GitHubRepoRef,
    RepositoryServiceError,
    ValidationError,
    ValidationResult,
    parse_github_url,
    validate_public_repository,
)


# =========================================================================
# 1. GitHub URL Parsing Tests
# =========================================================================

def test_parse_valid_github_urls():
    ref = parse_github_url("https://github.com/psf/requests")
    assert ref.owner == "psf"
    assert ref.name == "requests"
    assert ref.github_url == "https://github.com/psf/requests"

    # With .git suffix
    ref2 = parse_github_url("https://github.com/pallets/flask.git")
    assert ref2.owner == "pallets"
    assert ref2.name == "flask"

    # With trailing slash
    ref3 = parse_github_url("https://github.com/fastapi/fastapi/")
    assert ref3.owner == "fastapi"
    assert ref3.name == "fastapi"

    # With www prefix
    ref4 = parse_github_url("https://www.github.com/django/django")
    assert ref4.owner == "django"
    assert ref4.name == "django"


def test_parse_invalid_urls_rejected():
    with pytest.raises(ValidationError):
        parse_github_url("https://gitlab.com/owner/repo")

    with pytest.raises(ValidationError):
        parse_github_url("https://bitbucket.org/owner/repo")

    with pytest.raises(ValidationError):
        parse_github_url("not-a-url")

    with pytest.raises(ValidationError):
        parse_github_url("")


# =========================================================================
# 2. Public Repository Validation Tests
# =========================================================================

@patch("httpx.Client.get")
def test_validate_public_repository_success(mock_get):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "full_name": "psf/requests",
        "description": "A simple HTTP library",
        "default_branch": "main",
        "size": 12345,
        "language": "Python",
        "private": False,
    }
    mock_get.return_value = mock_resp

    result = validate_public_repository("https://github.com/psf/requests")
    assert isinstance(result, ValidationResult)
    assert result.repo.owner == "psf"
    assert result.repo.name == "requests"
    assert result.repo.is_public is True
    assert result.repo.default_branch == "main"
    assert result.metadata["language"] == "Python"


@patch("httpx.Client.get")
def test_validate_repository_private_rejected(mock_get):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "full_name": "secret/private-repo",
        "private": True,
    }
    mock_get.return_value = mock_resp

    with pytest.raises(ValidationError, match="Only public GitHub repositories are supported"):
        validate_public_repository("https://github.com/secret/private-repo")


@patch("httpx.Client.get")
def test_validate_repository_not_found(mock_get):
    mock_resp = MagicMock()
    mock_resp.status_code = 404
    mock_get.return_value = mock_resp

    with pytest.raises(ValidationError, match="Repository was not found"):
        validate_public_repository("https://github.com/nonexistent/repo")


@patch("httpx.Client.get")
def test_validate_repository_rate_limit(mock_get):
    mock_resp = MagicMock()
    mock_resp.status_code = 403
    mock_get.return_value = mock_resp

    with pytest.raises(ValidationError, match="GitHub API access was denied"):
        validate_public_repository("https://github.com/owner/repo")


# =========================================================================
# 3. Language Detection Tests
# =========================================================================

def test_detect_launch_languages():
    # Python
    assert detect_language("app/main.py") == "python"
    assert detect_language("scripts/run.pyw") == "python"
    assert detect_language("bin/script", "#!/usr/bin/env python3\nprint(1)") == "python"

    # JavaScript
    assert detect_language("src/index.js") == "javascript"
    assert detect_language("src/component.jsx") == "javascript"
    assert detect_language("scripts/cli", "#!/usr/bin/env node\nconsole.log(1)") == "javascript"

    # TypeScript
    assert detect_language("src/app.ts") == "typescript"
    assert detect_language("src/App.tsx") == "typescript"

    # Java
    assert detect_language("src/Main.java") == "java"

    # C++
    assert detect_language("src/engine.cpp") == "cpp"
    assert detect_language("include/engine.hpp") == "cpp"
    assert detect_language("src/core.cc") == "cpp"
    assert detect_language("include/common.h") == "cpp"

    # Go
    assert detect_language("cmd/server/main.go") == "go"


def test_detect_language_graceful_degradation():
    assert detect_language("notes.md") == "markdown"
    assert detect_language("config.yaml") == "yaml"
    assert detect_language("schema.sql") == "sql"
    assert detect_language("custom.xyz") == "xyz"
    assert detect_language("Dockerfile_unknown") == "unknown"


# =========================================================================
# 4. File Tree & 5. Binary/Oversized File Handling Tests
# =========================================================================

def test_build_file_tree_with_filtering_and_binary(tmp_path):
    # Setup test workspace structure
    (tmp_path / "src").mkdir()
    (tmp_path / ".git").mkdir()
    (tmp_path / "node_modules").mkdir()

    # Normal text file
    py_file = tmp_path / "src" / "main.py"
    py_file.write_text("print('hello world')", encoding="utf-8")

    # Binary file (contains null byte)
    bin_file = tmp_path / "src" / "image.png"
    bin_file.write_bytes(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR")

    # Ignored files in .git and node_modules
    (tmp_path / ".git" / "config").write_text("git-config")
    (tmp_path / "node_modules" / "pkg.js").write_text("package-code")

    records = build_file_tree(tmp_path)
    paths = [r.path for r in records]

    # .git and node_modules must be excluded
    assert ".git/config" not in paths
    assert "node_modules/pkg.js" not in paths

    # src/main.py must be detected and text content included
    main_rec = next(r for r in records if r.path == "src/main.py")
    assert main_rec.language == "python"
    assert main_rec.content == "print('hello world')"
    assert main_rec.is_binary is False
    assert len(main_rec.hash) == 64

    # src/image.png must be marked binary with content=None
    img_rec = next(r for r in records if r.path == "src/image.png")
    assert img_rec.is_binary is True
    assert img_rec.content is None
    assert len(img_rec.hash) == 64


def test_build_file_tree_oversized_file(tmp_path):
    big_file = tmp_path / "large.txt"
    # Write 100 bytes but set max_file_bytes to 50
    big_file.write_text("A" * 100, encoding="utf-8")

    records = build_file_tree(tmp_path, max_file_bytes=50)
    assert len(records) == 1
    assert records[0].size == 100
    assert records[0].content is None  # Content omitted because file exceeds max size


def test_build_file_tree_nonexistent_raises():
    with pytest.raises(ValueError):
        build_file_tree(Path("nonexistent-dir-123456"))


# =========================================================================
# 6. Commit Extraction Tests
# =========================================================================

@patch("subprocess.run")
def test_extract_commits_parsing(mock_run):
    sample_git_log = (
        "===COMMIT===abc1234===Alice===2026-01-15T10:00:00+00:00===Add auth middleware===\n"
        "Detailed commit message body.\n"
        "diff --git a/auth.py b/auth.py\n"
        "--- a/auth.py\n"
        "+++ b/auth.py\n"
        "+def verify(): pass\n"
        "===COMMIT===def5678===Bob===2026-01-14T09:30:00+00:00===Initial project skeleton===\n"
    )
    mock_run.return_value = MagicMock(stdout=sample_git_log)

    commits = extract_commits(Path("."), limit=10, include_diff=True)
    assert len(commits) == 2

    assert commits[0].commit_hash == "abc1234"
    assert commits[0].author == "Alice"
    assert "Add auth middleware" in commits[0].message
    assert "Detailed commit message body." in commits[0].message
    assert "diff --git" in (commits[0].diff or "")

    assert commits[1].commit_hash == "def5678"
    assert commits[1].author == "Bob"


@patch("subprocess.run")
def test_extract_commits_empty_repository(mock_run):
    import subprocess
    mock_run.side_effect = subprocess.CalledProcessError(
        returncode=128,
        cmd=["git", "log"],
        stderr="fatal: your current branch 'main' does not have any commits yet",
    )

    commits = extract_commits(Path("."))
    assert commits == []


# =========================================================================
# 7. Contributor Extraction Tests
# =========================================================================

@patch("httpx.Client.get")
def test_fetch_contributors_github_only(mock_get):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = [
        {"login": "charlie", "contributions": 45},
        {"login": "dave", "contributions": 12},
    ]
    mock_get.return_value = mock_resp

    repo_ref = GitHubRepoRef(owner="org", name="repo", github_url="https://github.com/org/repo")
    contributors = fetch_contributors(repo_ref, repo_path=None)

    assert len(contributors) == 2
    assert contributors[0].name == "charlie"
    assert contributors[0].commit_count == 45
    assert contributors[1].name == "dave"
    assert contributors[1].commit_count == 12


# =========================================================================
# 8. Pull Request & 9. Issue Extraction Tests
# =========================================================================

@patch("httpx.Client.get")
def test_fetch_pull_requests(mock_get):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = [
        {
            "number": 101,
            "title": "Fix memory leak",
            "body": "Resolves issue #50",
            "user": {"login": "eve"},
            "state": "closed",
            "created_at": "2026-02-01T12:00:00Z",
            "merged_at": "2026-02-01T14:30:00Z",
        }
    ]
    mock_get.return_value = mock_resp

    repo_ref = GitHubRepoRef(owner="org", name="repo", github_url="https://github.com/org/repo")
    prs = fetch_pull_requests(repo_ref)

    assert len(prs) == 1
    assert prs[0].external_id == "101"
    assert prs[0].title == "Fix memory leak"
    assert prs[0].author == "eve"
    assert prs[0].merged_at is not None


@patch("httpx.Client.get")
def test_fetch_issues_filters_out_prs(mock_get):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = [
        {
            "number": 50,
            "title": "Memory leak on heavy load",
            "body": "System OOMs after 2 hours",
            "user": {"login": "frank"},
            "state": "open",
            "created_at": "2026-01-20T08:00:00Z",
        },
        {
            "number": 51,
            "title": "PR #51 title",
            "pull_request": {"url": "https://api.github.com/repos/org/repo/pulls/51"},
            "user": {"login": "frank"},
            "state": "open",
            "created_at": "2026-01-21T08:00:00Z",
        },
    ]
    mock_get.return_value = mock_resp

    repo_ref = GitHubRepoRef(owner="org", name="repo", github_url="https://github.com/org/repo")
    issues = fetch_issues(repo_ref)

    assert len(issues) == 1
    assert issues[0].external_id == "50"
    assert issues[0].title == "Memory leak on heavy load"
    assert issues[0].author == "frank"


# =========================================================================
# 10. Timeline Generation & Sorting Tests
# =========================================================================

def test_build_timeline_chronological_descending():
    t1 = datetime(2026, 1, 10, 12, 0, tzinfo=timezone.utc)
    t2 = datetime(2026, 1, 15, 12, 0, tzinfo=timezone.utc)
    t3 = datetime(2026, 1, 20, 12, 0, tzinfo=timezone.utc)

    commits = [
        CommitRecord(
            commit_hash="c111",
            author="Alice",
            message="Commit at t2",
            timestamp=t2,
            diff=None,
        )
    ]
    prs = [
        PullRequestRecord(
            external_id="pr1",
            title="PR at t3",
            body="PR body",
            author="Bob",
            state="merged",
            created_at=t3,
            merged_at=t3,
        )
    ]
    issues = [
        IssueRecord(
            external_id="iss1",
            title="Issue at t1",
            body="Issue body",
            author="Charlie",
            state="closed",
            created_at=t1,
        )
    ]

    timeline = build_timeline(commits, prs, issues)
    assert len(timeline) == 3

    # Must be sorted descending by timestamp: t3 -> t2 -> t1
    assert timeline[0].event_type == TimelineEventType.PULL_REQUEST
    assert timeline[0].event_id == "pr1"
    assert timeline[0].timestamp == t3

    assert timeline[1].event_type == TimelineEventType.COMMIT
    assert timeline[1].event_id == "c111"
    assert timeline[1].timestamp == t2

    assert timeline[2].event_type == TimelineEventType.ISSUE
    assert timeline[2].event_id == "iss1"
    assert timeline[2].timestamp == t1


# =========================================================================
# 11. Workspace Cleanup Tests
# =========================================================================

def test_cleanup_workspace(tmp_path):
    target_dir = tmp_path / "test-workspace"
    target_dir.mkdir()
    read_only_file = target_dir / "readonly.txt"
    read_only_file.write_text("cannot delete easily")
    # Make read-only
    os.chmod(read_only_file, stat.S_IREAD)

    assert target_dir.exists()
    cleanup_workspace(target_dir)
    assert not target_dir.exists()


def test_cleanup_workspace_nonexistent_handled_safely():
    # Should not raise
    cleanup_workspace(Path("completely-nonexistent-path-98765"))
