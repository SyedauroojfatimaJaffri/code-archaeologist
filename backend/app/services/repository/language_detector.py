"""Detect programming language from file paths and optional content."""

from __future__ import annotations

from pathlib import PurePosixPath

EXTENSION_LANGUAGE_MAP: dict[str, str] = {
    ".py": "python",
    ".pyw": "python",
    ".js": "javascript",
    ".jsx": "javascript",
    ".mjs": "javascript",
    ".cjs": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".java": "java",
    ".cpp": "cpp",
    ".cc": "cpp",
    ".cxx": "cpp",
    ".hpp": "cpp",
    ".h": "cpp",
    ".go": "go",
    ".md": "markdown",
    ".json": "json",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".toml": "toml",
    ".sql": "sql",
    ".html": "html",
    ".css": "css",
    ".scss": "scss",
    ".sh": "shell",
    ".bash": "shell",
    ".zsh": "shell",
    ".ps1": "powershell",
    ".rs": "rust",
    ".rb": "ruby",
    ".php": "php",
    ".swift": "swift",
    ".kt": "kotlin",
    ".cs": "csharp",
}

SHEBANG_LANGUAGE_MAP: tuple[tuple[str, str], ...] = (
    ("python", "python"),
    ("node", "javascript"),
    ("bash", "shell"),
    ("sh", "shell"),
    ("zsh", "shell"),
)


def detect_language(path: str, content: str | None = None) -> str:
    """
    Infer a language label for a repository file.

    Returns a supported launch language when recognized, otherwise a best-effort
    label or ``unknown`` for graceful degradation.
    """
    extension = PurePosixPath(path).suffix.lower()
    if extension in EXTENSION_LANGUAGE_MAP:
        return EXTENSION_LANGUAGE_MAP[extension]

    if content:
        first_line = content.splitlines()[0] if content.splitlines() else ""
        if first_line.startswith("#!"):
            shebang = first_line.lower()
            for needle, language in SHEBANG_LANGUAGE_MAP:
                if needle in shebang:
                    return language

    if extension:
        return extension.lstrip(".")
    return "unknown"
