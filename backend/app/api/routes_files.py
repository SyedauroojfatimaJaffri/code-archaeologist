"""Repository file explorer routes."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.core.security import CurrentUser, DbSession, require_repository
from app.models.db_models import RepositoryFile

router = APIRouter(prefix="/repositories/{repository_id}/files", tags=["files"])


class RepositoryFileNodeSchema(BaseModel):
    path: str
    name: str
    type: str  # "file" | "directory"
    children: list[RepositoryFileNodeSchema] | None = None


class RepositoryFileContentSchema(BaseModel):
    path: str
    content: str
    language: str | None = None
    size_bytes: int | None = None
    truncated: bool = False


def _build_hierarchical_tree(files: list[RepositoryFile]) -> list[dict[str, Any]]:
    root: dict[str, Any] = {}
    for f in files:
        parts = f.path.split("/")
        curr = root
        for i, part in enumerate(parts):
            if i == len(parts) - 1:
                curr[part] = {
                    "path": f.path,
                    "name": part,
                    "type": "file",
                }
            else:
                if part not in curr:
                    curr[part] = {
                        "path": "/".join(parts[: i + 1]),
                        "name": part,
                        "type": "directory",
                        "_children": {},
                    }
                curr = curr[part]["_children"]

    def to_nodes(d: dict[str, Any]) -> list[dict[str, Any]]:
        nodes: list[dict[str, Any]] = []
        for _, v in sorted(
            d.items(),
            key=lambda item: (0 if item[1]["type"] == "directory" else 1, item[0].lower()),
        ):
            if v["type"] == "directory":
                children = to_nodes(v.pop("_children", {}))
                nodes.append({
                    "path": v["path"],
                    "name": v["name"],
                    "type": "directory",
                    "children": children,
                })
            else:
                nodes.append({
                    "path": v["path"],
                    "name": v["name"],
                    "type": "file",
                })
        return nodes

    return to_nodes(root)


@router.get("", response_model=list[RepositoryFileNodeSchema])
def get_repository_file_tree(
    repository_id: UUID,
    db: DbSession,
    user: CurrentUser,
) -> list[dict[str, Any]]:
    """Return nested file tree for CodeViewer and FileTree navigation."""
    require_repository(db, repository_id, user.user_id)
    files = (
        db.query(RepositoryFile)
        .filter(RepositoryFile.repository_id == repository_id)
        .order_by(RepositoryFile.path.asc())
        .all()
    )
    return _build_hierarchical_tree(files)


@router.get("/{path:path}", response_model=RepositoryFileContentSchema)
def get_repository_file_content(
    repository_id: UUID,
    path: str,
    db: DbSession,
    user: CurrentUser,
) -> RepositoryFileContentSchema:
    """Return single file content and language metadata."""
    require_repository(db, repository_id, user.user_id)
    file_record = (
        db.query(RepositoryFile)
        .filter(
            RepositoryFile.repository_id == repository_id,
            RepositoryFile.path == path,
        )
        .first()
    )
    if file_record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "FILE_NOT_FOUND",
                    "message": f"File '{path}' was not found in repository.",
                }
            },
        )

    # Detect language from extension if not set
    language = file_record.language
    if not language:
        ext = path.rsplit(".", 1)[-1].lower() if "." in path else ""
        ext_map = {
            "py": "python",
            "js": "javascript",
            "jsx": "javascript",
            "ts": "typescript",
            "tsx": "typescript",
            "json": "json",
            "md": "markdown",
            "html": "html",
            "css": "css",
            "yml": "yaml",
            "yaml": "yaml",
            "sql": "sql",
        }
        language = ext_map.get(ext, "plaintext")

    return RepositoryFileContentSchema(
        path=file_record.path,
        content=file_record.content or "",
        language=language,
        size_bytes=file_record.size,
        truncated=False,
    )
