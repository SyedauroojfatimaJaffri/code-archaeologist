"""Clone public GitHub repositories into an isolated temporary workspace."""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

from app.services.repository.validator import GitHubRepoRef, RepositoryServiceError


@dataclass(frozen=True)
class CloneResult:
    repo: GitHubRepoRef
    workspace_path: Path
    clone_url: str


def _build_clone_url(repo: GitHubRepoRef, github_token: str | None) -> str:
    if github_token:
        return (
            f"https://x-access-token:{github_token}@github.com/"
            f"{repo.owner}/{repo.name}.git"
        )
    return f"https://github.com/{repo.owner}/{repo.name}.git"


def clone_repository(
    repo: GitHubRepoRef,
    *,
    github_token: str | None = None,
    workspace_root: Path | None = None,
    depth: int | None = None,
) -> CloneResult:
    """
    Clone a public repository into a dedicated temporary directory.

    Performs a read-only git clone. Does not install dependencies or execute
    any code from the cloned repository.
    """
    if workspace_root is None:
        workspace_root = Path(tempfile.mkdtemp(prefix="code-archaeologist-"))
    else:
        workspace_root.mkdir(parents=True, exist_ok=True)

    destination = workspace_root / f"{repo.owner}-{repo.name}"
    if destination.exists():
        raise RepositoryServiceError(
            f"Workspace already exists at {destination}. Clean it up before recloning."
        )

    clone_url = _build_clone_url(repo, github_token)
    command = ["git", "clone", clone_url, str(destination)]
    if depth is not None and depth > 0:
        command[2:2] = ["--depth", str(depth)]
    if repo.default_branch:
        command[2:2] = ["--branch", repo.default_branch]

    try:
        subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError as exc:
        cleanup_workspace(destination)
        raise RepositoryServiceError(
            "Git is not installed or not available on PATH."
        ) from exc
    except subprocess.CalledProcessError as exc:
        cleanup_workspace(destination)
        stderr = (exc.stderr or "").strip()
        message = stderr or "Git clone failed."
        raise RepositoryServiceError(message) from exc

    return CloneResult(
        repo=repo,
        workspace_path=destination,
        clone_url=f"https://github.com/{repo.owner}/{repo.name}.git",
    )


def cleanup_workspace(path: Path) -> None:
    """Remove a cloned repository workspace directory."""
    if not path.exists():
        return
    import os
    import stat

    def _unlink_readonly(action, target, exc):
        try:
            os.chmod(target, stat.S_IWRITE)
            action(target)
        except Exception:
            pass

    try:
        shutil.rmtree(path, onexc=_unlink_readonly)
    except TypeError:
        shutil.rmtree(path, onerror=_unlink_readonly)
    except Exception:
        shutil.rmtree(path, ignore_errors=True)
