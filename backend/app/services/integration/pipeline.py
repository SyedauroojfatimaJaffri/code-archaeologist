"""M1 Integration Pipeline Orchestrator.

Coordinates M2 (repository/history intelligence) and M3 (AI/parsing/knowledge/risk/offboarding)
services through service interfaces to execute background analysis jobs, answer historian questions,
provide developer guidance, answer knowledge gaps, and create offboarding sessions.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.db_models import (
    AnalysisJob,
    CodeEntity,
    Commit,
    Contributor,
    Dependency,
    Evidence,
    Issue,
    KnowledgeGap,
    KnowledgeItem,
    OffboardingQuestion,
    OffboardingSession,
    PullRequest,
    Repository,
    RepositoryFile,
    RiskRecord,
    SessionLocal,
)
from app.schemas.guidance import GuidanceResponse, GuidanceStep
from app.schemas.historian import EvidenceItem, HistorianQuestionResponse
from app.schemas.knowledge import KnowledgeGapAnswerResponse, OffboardingCreateResponse
from app.services.history import (
    fetch_contributors,
    fetch_issues,
    fetch_pull_requests,
)
from app.services.history.commits import extract_commits
from app.services.repository import (
    GitHubRepoRef,
    build_file_tree,
    cleanup_workspace,
    clone_repository,
    validate_public_repository,
)

logger = logging.getLogger("code_archaeologist.pipeline")


def run_analysis_job(job_id: UUID | str) -> None:
    """
    Execute background analysis pipeline for a queued analysis job.

    1. Updates job status to 'running'
    2. Uses M2 services to acquire repository files, git log, contributors, issues, and PRs
    3. Persists records to PostgreSQL database
    4. Triggers M3 static analysis & risk evaluation if available
    5. Updates job status to 'completed' (or 'failed' on error)
    """
    if isinstance(job_id, str):
        job_id = uuid.UUID(job_id)

    db: Session = SessionLocal()
    workspace_path: Path | None = None
    try:
        job = db.query(AnalysisJob).filter(AnalysisJob.id == job_id).first()
        if not job:
            logger.error("Analysis job %s not found", job_id)
            return

        job.status = "running"
        job.started_at = datetime.now(timezone.utc)
        db.commit()

        repository = db.query(Repository).filter(Repository.id == job.repository_id).first()
        if not repository:
            job.status = "failed"
            job.error_message = "Associated repository not found."
            job.completed_at = datetime.now(timezone.utc)
            db.commit()
            return

        repository.status = "running"
        db.commit()

        settings = get_settings()

        # Phase 1: M2 Repository Validation & Cloning
        validation = validate_public_repository(
            repository.github_url,
            github_token=settings.github_token,
        )
        repo_ref = validation.repo

        clone_result = clone_repository(
            repo_ref,
            github_token=settings.github_token,
        )
        workspace_path = clone_result.workspace_path

        # Phase 2: File Tree Extraction & DB Persistence
        file_records = build_file_tree(workspace_path)
        
        # Clear existing repository files for clean re-analysis
        db.query(RepositoryFile).filter(RepositoryFile.repository_id == repository.id).delete()
        
        db_files: list[RepositoryFile] = []
        for file_rec in file_records:
            file_model = RepositoryFile(
                repository_id=repository.id,
                path=file_rec.path,
                language=file_rec.language,
                content=file_rec.content,
                size=file_rec.size,
                hash=file_rec.hash,
            )
            db_files.append(file_model)
            db.add(file_model)
        db.commit()

        # Phase 3: M2 Git History Intelligence Extraction
        commits = extract_commits(workspace_path, limit=200, include_diff=False)
        db.query(Commit).filter(Commit.repository_id == repository.id).delete()
        for c in commits:
            db.add(
                Commit(
                    repository_id=repository.id,
                    commit_hash=c.commit_hash,
                    author=c.author,
                    message=c.message,
                    timestamp=c.timestamp,
                    diff=c.diff,
                )
            )

        contributors = fetch_contributors(
            repo_ref, repo_path=workspace_path, github_token=settings.github_token
        )
        db.query(Contributor).filter(Contributor.repository_id == repository.id).delete()
        for contrib in contributors:
            db.add(
                Contributor(
                    repository_id=repository.id,
                    external_id=contrib.external_id,
                    name=contrib.name,
                    email_hash=contrib.email_hash,
                    commit_count=contrib.commit_count,
                    first_seen=contrib.first_seen,
                    last_seen=contrib.last_seen,
                )
            )

        issues = fetch_issues(repo_ref, github_token=settings.github_token, max_items=100)
        db.query(Issue).filter(Issue.repository_id == repository.id).delete()
        for issue_rec in issues:
            db.add(
                Issue(
                    repository_id=repository.id,
                    external_id=issue_rec.external_id,
                    title=issue_rec.title,
                    body=issue_rec.body,
                    author=issue_rec.author,
                    state=issue_rec.state,
                    created_at=issue_rec.created_at,
                )
            )

        prs = fetch_pull_requests(repo_ref, github_token=settings.github_token, max_items=100)
        db.query(PullRequest).filter(PullRequest.repository_id == repository.id).delete()
        for pr_rec in prs:
            db.add(
                PullRequest(
                    repository_id=repository.id,
                    external_id=pr_rec.external_id,
                    title=pr_rec.title,
                    body=pr_rec.body,
                    author=pr_rec.author,
                    state=pr_rec.state,
                    created_at=pr_rec.created_at,
                    merged_at=pr_rec.merged_at,
                )
            )

        db.commit()

        # Phase 4: M3 Integration Hook (Static Parsing, AI Risk & Knowledge Gaps)
        _run_m3_analysis_hooks(db, repository, db_files)

        # Complete job
        job.status = "completed"
        job.completed_at = datetime.now(timezone.utc)
        repository.status = "completed"
        db.commit()

    except Exception as exc:
        logger.exception("Analysis job %s failed: %s", job_id, exc)
        try:
            job = db.query(AnalysisJob).filter(AnalysisJob.id == job_id).first()
            if job:
                job.status = "failed"
                job.error_message = str(exc)
                job.completed_at = datetime.now(timezone.utc)
            repo = db.query(Repository).filter(Repository.id == job.repository_id).first() if job else None
            if repo:
                repo.status = "failed"
            db.commit()
        except Exception:
            logger.exception("Failed to update status to failed for job %s", job_id)
    finally:
        if workspace_path:
            cleanup_workspace(workspace_path)
        db.close()


def _run_m3_analysis_hooks(db: Session, repository: Repository, files: list[RepositoryFile]) -> None:
    """Execute static parsing, dependency extraction, risk scoring, and semantic embeddings."""
    # Clear existing derived records
    db.query(Dependency).filter(Dependency.repository_id == repository.id).delete()
    db.query(CodeEntity).filter(CodeEntity.repository_id == repository.id).delete()
    db.query(RiskRecord).filter(RiskRecord.repository_id == repository.id).delete()
    db.query(KnowledgeGap).filter(KnowledgeGap.repository_id == repository.id).delete()

    from app.services.parsing.python_parser import parse_python_file
    from app.services.parsing.javascript_parser import parse_javascript_file
    from app.services.parsing.dependency_mapper import map_dependencies
    from app.services.risk.risk_scorer import RiskInputs, score_files
    from app.services.retrieval.embeddings import embed_batch
    from app.models.db_models import KnowledgeEmbedding

    all_file_entities = []
    file_entity_map: dict[str, set[str]] = {}
    raw_dependencies = []

    for file_rec in files:
        if not file_rec.content:
            continue
        ext = file_rec.path.rsplit(".", 1)[-1].lower() if "." in file_rec.path else ""
        extracted_entities = []
        if ext in ("py", "pyw"):
            extracted_entities, _ = parse_python_file(
                file_rec.content, file_id=str(file_rec.id), repository_id=str(repository.id)
            )
        elif ext in ("js", "jsx", "ts", "tsx", "mjs", "cjs"):
            extracted_entities, _ = parse_javascript_file(
                file_rec.content, file_id=str(file_rec.id), repository_id=str(repository.id)
            )

        if extracted_entities:
            file_deps = map_dependencies(extracted_entities, repository_id=str(repository.id))
            raw_dependencies.extend(file_deps)
            all_file_entities.extend(extracted_entities)
            file_entity_map[str(file_rec.id)] = {e.local_id for e in extracted_entities}

    # Persist CodeEntity rows
    local_to_db_id: dict[str, UUID] = {}
    for entity in all_file_entities:
        db_entity = CodeEntity(
            repository_id=repository.id,
            file_id=uuid.UUID(entity.file_id) if entity.file_id else None,
            entity_type=entity.entity_type.value if hasattr(entity.entity_type, "value") else str(entity.entity_type),
            name=entity.name,
            start_line=entity.start_line,
            end_line=entity.end_line,
            signature=entity.signature,
        )
        db.add(db_entity)
        db.flush()
        local_to_db_id[entity.local_id] = db_entity.id

    # Persist Dependency rows
    for dep in raw_dependencies:
        src_local = dep.get("source_entity_id")
        tgt_local = dep.get("target_entity_id")
        db.add(
            Dependency(
                repository_id=repository.id,
                source_entity_id=local_to_db_id.get(src_local),
                target_entity_id=local_to_db_id.get(tgt_local),
                dependency_type=dep.get("dependency_type", "calls"),
            )
        )
    db.commit()

    # Risk Scoring with deterministic signals
    commits = db.query(Commit).filter(Commit.repository_id == repository.id).all()
    contributors = db.query(Contributor).filter(Contributor.repository_id == repository.id).all()

    commit_dicts = [
        {"hash": c.commit_hash, "author": c.author, "timestamp": c.timestamp, "message": c.message}
        for c in commits
    ]
    contrib_dicts = [
        {"name": c.name, "commit_count": c.commit_count, "first_seen": c.first_seen, "last_seen": c.last_seen}
        for c in contributors
    ]

    risk_inputs_list = []
    for file_rec in files:
        risk_inputs_list.append(
            RiskInputs(
                file_id=str(file_rec.id),
                repository_id=str(repository.id),
                commits=commit_dicts,
                contributors=contrib_dicts,
                entity_local_ids=file_entity_map.get(str(file_rec.id), set()),
                dependencies=raw_dependencies,
                knowledge_gaps=[],
            )
        )

    if risk_inputs_list:
        try:
            scored_records = score_files(risk_inputs_list)
            for scored in scored_records:
                db.add(
                    RiskRecord(
                        repository_id=repository.id,
                        file_id=uuid.UUID(scored["file_id"]) if scored["file_id"] else None,
                        score=scored["score"],
                        signals=scored["signals"],
                        explanation=scored["explanation"],
                    )
                )
        except Exception as exc:
            logger.warning("Deterministic risk scoring error: %s", exc)

    # Knowledge Gap check
    has_readme = any("readme" in f.path.lower() for f in files)
    if not has_readme:
        db.add(
            KnowledgeGap(
                repository_id=repository.id,
                question="Why is there no README documentation explaining the repository architecture?",
                context="Automatic analysis detected missing top-level README file.",
                priority="high",
                status="open",
            )
        )

    # Embeddings generation
    try:
        embed_texts = []
        for file_rec in files[:20]:
            if file_rec.content:
                snippet = f"File: {file_rec.path}\n{file_rec.content[:500]}"
                embed_texts.append(snippet)
        if embed_texts:
            embeddings = embed_batch(embed_texts)
            for snip, vec in zip(embed_texts, embeddings):
                db.add(
                    KnowledgeEmbedding(
                        repository_id=repository.id,
                        content=snip,
                        embedding=vec,
                    )
                )
    except Exception as exc:
        logger.warning("Embeddings generation skipped or failed: %s", exc)

    db.commit()


def run_historian_question(
    repository_id: UUID,
    question: str,
    db: Session | None = None,
) -> HistorianQuestionResponse:
    """Execute Historian Q&A query using M3 AI service or database evidence retrieval fallback."""
    close_db = False
    if db is None:
        db = SessionLocal()
        close_db = True
    try:
        try:
            from app.agents.historian import ask_historian  # type: ignore
            return ask_historian(db, repository_id, question)
        except ImportError:
            try:
                from app.services.m3 import ask_historian  # type: ignore
                return ask_historian(db, repository_id, question)
            except ImportError:
                pass

        # Database evidence retrieval fallback
        query_words = [w.lower() for w in question.split() if len(w) > 3]
        evidence_items: list[EvidenceItem] = []

        # Check commit messages
        commits = db.query(Commit).filter(Commit.repository_id == repository_id).all()
        matching_commits = []
        for c in commits:
            if c.message and any(w in c.message.lower() for w in query_words):
                matching_commits.append(c)

        for mc in matching_commits[:3]:
            evidence_items.append(
                EvidenceItem(
                    source_type="commit",
                    source_id=mc.commit_hash[:8],
                    excerpt=mc.message[:200] if mc.message else None,
                )
            )

        # Check matching files
        files = db.query(RepositoryFile).filter(RepositoryFile.repository_id == repository_id).all()
        matching_files = []
        for f in files:
            if any(w in f.path.lower() for w in query_words):
                matching_files.append(f)

        for mf in matching_files[:3]:
            evidence_items.append(
                EvidenceItem(
                    source_type="file",
                    source_id=str(mf.id),
                    excerpt=f.path,
                )
            )

        # Check human knowledge items
        k_items = db.query(KnowledgeItem).filter(KnowledgeItem.repository_id == repository_id).all()
        for k in k_items:
            if any(w in k.title.lower() or w in k.content.lower() for w in query_words):
                evidence_items.append(
                    EvidenceItem(
                        source_type="knowledge_item",
                        source_id=str(k.id),
                        excerpt=f"{k.title}: {k.content[:150]}",
                    )
                )

        classification = "human_knowledge" if any(e.source_type == "knowledge_item" for e in evidence_items) else "inferred"
        confidence = "medium" if evidence_items else "low"
        
        answer = (
            f"Based on historical commit records and codebase structure for '{question}', "
            f"found {len(evidence_items)} relevant evidence entries across commits and files."
        ) if evidence_items else f"No conclusive evidence found in repository history for: '{question}'."

        return HistorianQuestionResponse(
            answer=answer,
            evidence=evidence_items,
            confidence=confidence,
            classification=classification,
        )
    finally:
        if close_db:
            db.close()


def run_developer_guidance(
    repository_id: UUID,
    task: str,
    db: Session | None = None,
) -> GuidanceResponse:
    """Generate developer implementation guidance steps for a task."""
    close_db = False
    if db is None:
        db = SessionLocal()
        close_db = True
    try:
        try:
            from app.agents.guidance_agent import generate_guidance  # type: ignore
            raw = generate_guidance(db, repository_id, task)
            if isinstance(raw, dict):
                return GuidanceResponse(
                    task=raw.get("task", task),
                    steps=[
                        GuidanceStep(
                            title=s.get("title", f"Step {idx + 1}"),
                            files=s.get("files", []),
                            reasoning=s.get("reasoning", ""),
                        )
                        for idx, s in enumerate(raw.get("steps", []))
                    ],
                )
            if isinstance(raw, GuidanceResponse):
                return raw
        except ImportError:
            try:
                from app.services.m3 import generate_guidance  # type: ignore
                raw = generate_guidance(db, repository_id, task)
                if isinstance(raw, dict):
                    return GuidanceResponse(
                        task=raw.get("task", task),
                        steps=[
                            GuidanceStep(
                                title=s.get("title", f"Step {idx + 1}"),
                                files=s.get("files", []),
                                reasoning=s.get("reasoning", ""),
                            )
                            for idx, s in enumerate(raw.get("steps", []))
                        ],
                    )
                if isinstance(raw, GuidanceResponse):
                    return raw
            except ImportError:
                pass

        # Heuristic task breakdown using analyzed file tree
        files = db.query(RepositoryFile).filter(RepositoryFile.repository_id == repository_id).all()
        relevant_paths = [f.path for f in files if any(w in f.path.lower() for w in task.lower().split() if len(w) > 3)]
        if not relevant_paths:
            relevant_paths = [f.path for f in files[:3]]

        steps = [
            GuidanceStep(
                title="Inspect existing component context",
                files=relevant_paths[:2],
                reasoning=f"Review existing code structures and conventions for task: '{task}'.",
            ),
            GuidanceStep(
                title="Implement changes and maintain architectural invariants",
                files=relevant_paths[2:4] if len(relevant_paths) > 2 else relevant_paths,
                reasoning="Extend target modules and add unit tests following established repository design.",
            ),
        ]

        return GuidanceResponse(task=task, steps=steps)
    finally:
        if close_db:
            db.close()


def run_knowledge_gap_answer(
    repository_id: UUID,
    gap_id: UUID,
    answer: str,
    user_id: str,
    db: Session,
) -> KnowledgeGapAnswerResponse:
    """Process human answer to a knowledge gap and store in Knowledge Store."""
    gap = (
        db.query(KnowledgeGap)
        .filter(KnowledgeGap.id == gap_id, KnowledgeGap.repository_id == repository_id)
        .first()
    )
    if not gap:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "KNOWLEDGE_GAP_NOT_FOUND",
                    "message": "Knowledge gap was not found.",
                }
            },
        )

    # Create knowledge item
    item = KnowledgeItem(
        repository_id=repository_id,
        user_id=user_id,
        title=f"Answer: {gap.question[:100]}",
        content=answer,
        source="human",
    )
    db.add(item)
    db.flush()

    # Update gap status
    gap.status = "resolved"
    gap.resolved_knowledge_item_id = item.id
    gap.resolved_at = datetime.now(timezone.utc)
    db.commit()

    return KnowledgeGapAnswerResponse(
        gap_id=gap.id,
        knowledge_item_id=item.id,
        status="resolved",
    )


def run_create_offboarding_session(
    repository_id: UUID,
    contributor_identifier: str,
    db: Session,
) -> OffboardingCreateResponse:
    """Create an offboarding knowledge preservation session for a departing contributor."""
    # Find matching contributor record if any
    contributor = (
        db.query(Contributor)
        .filter(
            Contributor.repository_id == repository_id,
            (Contributor.external_id == contributor_identifier) | (Contributor.name == contributor_identifier),
        )
        .first()
    )

    session = OffboardingSession(
        repository_id=repository_id,
        contributor_id=contributor.id if contributor else None,
        status="created",
    )
    db.add(session)
    db.flush()

    # Generate initial offboarding questions based on contributor history & high-risk components
    questions = [
        OffboardingQuestion(
            session_id=session.id,
            question=f"What key architectural decisions did {contributor_identifier} make in this repository?",
            priority="high",
            status="pending",
        ),
        OffboardingQuestion(
            session_id=session.id,
            question=f"Are there any undocumented dependencies or deployment steps known by {contributor_identifier}?",
            priority="medium",
            status="pending",
        ),
    ]
    for q in questions:
        db.add(q)

    db.commit()

    return OffboardingCreateResponse(session_id=session.id, status="created")
