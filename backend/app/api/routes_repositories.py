"""Repository management routes alias for backwards compatibility."""

from app.api.routes_repository import (
    create_and_ingest_repository,
    delete_repository,
    get_repository,
    get_repository_status,
    list_repositories,
    router,
)

__all__ = [
    "router",
    "create_and_ingest_repository",
    "list_repositories",
    "get_repository",
    "get_repository_status",
    "delete_repository",
]
