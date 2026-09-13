"""Repository acquisition services (M2)."""

from app.services.repository.cloner import CloneResult, cleanup_workspace, clone_repository
from app.services.repository.file_tree import FileRecord, build_file_tree
from app.services.repository.language_detector import detect_language
from app.services.repository.validator import (
    GitHubRepoRef,
    ValidationError,
    ValidationResult,
    parse_github_url,
    validate_public_repository,
)

__all__ = [
    "CloneResult",
    "FileRecord",
    "GitHubRepoRef",
    "ValidationError",
    "ValidationResult",
    "build_file_tree",
    "cleanup_workspace",
    "clone_repository",
    "detect_language",
    "parse_github_url",
    "validate_public_repository",
]
