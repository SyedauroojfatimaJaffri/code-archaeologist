"""Build a repository file tree from a cloned workspace."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

from app.services.repository.language_detector import detect_language

DEFAULT_IGNORED_DIRS = frozenset(
    {
        ".git",
        ".hg",
        ".svn",
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        "node_modules",
        "venv",
        ".venv",
        "env",
        "dist",
        "build",
        ".next",
        ".nuxt",
        "target",
        ".idea",
        ".vscode",
    }
)

DEFAULT_MAX_FILE_BYTES = 1_048_576  # 1 MiB


@dataclass(frozen=True)
class FileRecord:
    path: str
    language: str
    content: str | None
    size: int
    hash: str
    is_binary: bool


def _is_probably_binary(sample: bytes) -> bool:
    if not sample:
        return False
    if b"\x00" in sample:
        return True
    text_like = sum(32 <= byte <= 126 or byte in (9, 10, 13) for byte in sample)
    return text_like / len(sample) < 0.85


def _file_hash(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def build_file_tree(
    root_path: Path,
    *,
    max_file_bytes: int = DEFAULT_MAX_FILE_BYTES,
    ignored_dirs: frozenset[str] | None = None,
    include_content: bool = True,
) -> list[FileRecord]:
    """
    Walk a cloned repository and collect file metadata for static analysis.

    Skips ignored directories and oversized or binary files. Never executes
    repository code.
    """
    if not root_path.exists() or not root_path.is_dir():
        raise ValueError(f"Repository workspace not found: {root_path}")

    ignored = ignored_dirs or DEFAULT_IGNORED_DIRS
    records: list[FileRecord] = []

    for file_path in sorted(root_path.rglob("*")):
        if not file_path.is_file():
            continue

        relative_parts = file_path.relative_to(root_path).parts
        if any(part in ignored for part in relative_parts):
            continue

        relative_path = file_path.relative_to(root_path).as_posix()
        size = file_path.stat().st_size
        raw_content = file_path.read_bytes()
        is_binary = _is_probably_binary(raw_content[:4096])
        content: str | None = None

        if include_content and not is_binary and size <= max_file_bytes:
            try:
                content = raw_content.decode("utf-8")
            except UnicodeDecodeError:
                is_binary = True

        language = detect_language(relative_path, content)
        records.append(
            FileRecord(
                path=relative_path,
                language=language,
                content=content,
                size=size,
                hash=_file_hash(raw_content),
                is_binary=is_binary,
            )
        )

    return records
