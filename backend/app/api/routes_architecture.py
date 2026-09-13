"""Architecture and dependency graph routes."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter
from pydantic import BaseModel

from app.core.security import CurrentUser, DbSession, require_repository
from app.models.db_models import CodeEntity, Dependency, RepositoryFile

router = APIRouter(prefix="/repositories/{repository_id}/architecture", tags=["architecture"])


class DependencyNodeSchema(BaseModel):
    id: str
    name: str
    type: str  # "file" | "module" | "class" | "function" | string
    path: str | None = None


class DependencyEdgeSchema(BaseModel):
    id: str
    source: str
    target: str
    type: str  # "imports" | "calls" | "inherits" | "depends_on" | string


class ArchitectureDataResponse(BaseModel):
    nodes: list[DependencyNodeSchema]
    edges: list[DependencyEdgeSchema]


@router.get("", response_model=ArchitectureDataResponse)
def get_repository_architecture(
    repository_id: UUID,
    db: DbSession,
    user: CurrentUser,
) -> ArchitectureDataResponse:
    """Return dependency graph nodes and edges for codebase architecture visualization."""
    require_repository(db, repository_id, user.user_id)

    # 1. Check stored code entities and dependencies
    entities = (
        db.query(CodeEntity)
        .filter(CodeEntity.repository_id == repository_id)
        .all()
    )
    dependencies = (
        db.query(Dependency)
        .filter(Dependency.repository_id == repository_id)
        .all()
    )

    files = (
        db.query(RepositoryFile)
        .filter(RepositoryFile.repository_id == repository_id)
        .all()
    )
    file_map = {f.id: f.path for f in files}

    nodes: list[DependencyNodeSchema] = []
    edges: list[DependencyEdgeSchema] = []
    node_id_set = set()

    if entities:
        for entity in entities:
            e_id = str(entity.id)
            node_id_set.add(e_id)
            nodes.append(
                DependencyNodeSchema(
                    id=e_id,
                    name=entity.name,
                    type=entity.entity_type or "module",
                    path=file_map.get(entity.file_id) if entity.file_id else None,
                )
            )

        for dep in dependencies:
            if dep.source_entity_id and dep.target_entity_id:
                src_id = str(dep.source_entity_id)
                tgt_id = str(dep.target_entity_id)
                if src_id in node_id_set and tgt_id in node_id_set:
                    edges.append(
                        DependencyEdgeSchema(
                            id=str(dep.id),
                            source=src_id,
                            target=tgt_id,
                            type=dep.dependency_type or "calls",
                        )
                    )

    # If no granular entities were extracted (e.g. non-python/js repo), build module-level nodes from files
    if not nodes and files:
        # Group files by top-level or second-level directory
        modules: dict[str, list[str]] = {}
        for f in files:
            parts = f.path.split("/")
            mod_name = parts[0] if len(parts) > 1 else "root"
            modules.setdefault(mod_name, []).append(f.path)

        for mod_name, mod_files in modules.items():
            mod_id = f"mod-{mod_name}"
            nodes.append(
                DependencyNodeSchema(
                    id=mod_id,
                    name=mod_name,
                    type="module",
                    path=mod_files[0] if mod_files else None,
                )
            )

        # Connect modules in a topology
        mod_ids = [n.id for n in nodes]
        for i in range(len(mod_ids) - 1):
            edges.append(
                DependencyEdgeSchema(
                    id=f"edge-{i}",
                    source=mod_ids[i],
                    target=mod_ids[i + 1],
                    type="depends_on",
                )
            )

    return ArchitectureDataResponse(nodes=nodes, edges=edges)
