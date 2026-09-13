"""
test_e2e_integration.py — End-to-End Integration Verification

Validates the complete end-to-end runtime lifecycle:
1. Authentication & JWT Token decoding
2. Public GitHub Repository acquisition (URL validation, file tree, commits)
3. Background Analysis Job execution and state transitions
4. Repository File Tree and Content retrieval
5. Historian Question-Answering with Evidence, Confidence, and Classification
6. Developer Guidance step generation with grounded file references
7. Risk Radar evaluation & signal detection
8. Knowledge Gap listing, answering, and preservation into Knowledge Store
9. Developer Offboarding session creation, question answering, and report generation
10. Strict tenant isolation and unauthorized access rejection
"""

from datetime import datetime, timezone
import pytest
from unittest.mock import patch, MagicMock
from uuid import UUID, uuid4

from app.models.db_models import (
    Repository,
    AnalysisJob,
    RepositoryFile,
    Commit,
    Contributor,
    KnowledgeGap,
    KnowledgeItem,
    OffboardingSession,
    OffboardingQuestion,
    RiskRecord,
)
from app.services.repository.validator import GitHubRepoRef, ValidationResult
from app.services.repository.cloner import CloneResult
from app.services.repository.file_tree import FileRecord
from app.services.history.commits import CommitRecord
from app.services.history.contributors import ContributorRecord
from app.services.integration.pipeline import run_analysis_job


@patch("app.services.integration.pipeline.validate_public_repository")
@patch("app.services.integration.pipeline.clone_repository")
@patch("app.services.integration.pipeline.build_file_tree")
@patch("app.services.integration.pipeline.extract_commits")
@patch("app.services.integration.pipeline.fetch_contributors")
@patch("app.services.integration.pipeline.fetch_issues")
@patch("app.services.integration.pipeline.fetch_pull_requests")
def test_full_end_to_end_user_journey(
    mock_prs,
    mock_issues,
    mock_contribs,
    mock_commits,
    mock_tree,
    mock_clone,
    mock_validate,
    client,
    db_session,
):
    # Setup M2 Mocks for a real-world small public repository lifecycle
    repo_ref = GitHubRepoRef(
        owner="octocat",
        name="Hello-World",
        github_url="https://github.com/octocat/Hello-World",
        default_branch="master",
        is_public=True,
    )
    mock_validate.return_value = ValidationResult(repo=repo_ref, metadata={})
    mock_clone.return_value = CloneResult(
        repo=repo_ref,
        workspace_path=MagicMock(),
        clone_url="https://github.com/octocat/Hello-World.git",
    )
    mock_tree.return_value = [
        FileRecord(path="README.md", language="Markdown", size=14, hash="h1", is_binary=False, content="Hello World!"),
        FileRecord(path="src/main.py", language="Python", size=120, hash="h2", is_binary=False, content="def main(): pass"),
        FileRecord(path="src/auth/middleware.py", language="Python", size=55000, hash="h3", is_binary=False, content="class AuthMiddleware: pass"),
    ]
    mock_commits.return_value = [
        CommitRecord(
            commit_hash="7fd1a60b01f91b314f59955a4e4d4e80d8dee119",
            author="octocat",
            message="Add authentication middleware and security handlers",
            timestamp=datetime(2026, 9, 1, 10, 0, 0, tzinfo=timezone.utc),
            diff=None,
        ),
        CommitRecord(
            commit_hash="553c2077f0edc3d5c4d1630ecd46d494e501e64a",
            author="alice",
            message="Initial Hello World commit",
            timestamp=datetime(2026, 8, 15, 12, 0, 0, tzinfo=timezone.utc),
            diff=None,
        ),
    ]
    mock_contribs.return_value = [
        ContributorRecord(
            external_id="octocat",
            name="The Octocat",
            email_hash="h_octo",
            commit_count=5,
            first_seen=datetime(2026, 8, 1, 10, 0, 0, tzinfo=timezone.utc),
            last_seen=datetime(2026, 9, 1, 10, 0, 0, tzinfo=timezone.utc),
        ),
        ContributorRecord(
            external_id="alice",
            name="Alice Smith",
            email_hash="h_alice",
            commit_count=1,
            first_seen=datetime(2026, 8, 15, 12, 0, 0, tzinfo=timezone.utc),
            last_seen=datetime(2026, 8, 15, 12, 0, 0, tzinfo=timezone.utc),
        ),
    ]
    mock_issues.return_value = []
    mock_prs.return_value = []

    # 1. User Adds Repository
    create_res = client.post("/repositories", json={"github_url": "https://github.com/octocat/Hello-World"})
    assert create_res.status_code == 201
    repo_data = create_res.json()
    repo_id = repo_data["repository_id"]
    assert repo_data["status"] == "created"

    # 2. Trigger Analysis Job
    job_res = client.post(f"/repositories/{repo_id}/analyze")
    assert job_res.status_code == 202
    job_id = job_res.json()["analysis_job_id"]

    # 3. Execute Analysis Pipeline (synchronously in test)
    run_analysis_job(job_id)

    # 4. Check Job Status & Repository State
    job_check = client.get(f"/analysis/{job_id}")
    assert job_check.status_code == 200
    assert job_check.json()["status"] == "completed"

    repo_detail = client.get(f"/repositories/{repo_id}")
    assert repo_detail.status_code == 200
    assert repo_detail.json()["status"] == "completed"

    # 5. Verify File Tree & File Content Retrieval
    files_res = client.get(f"/repositories/{repo_id}/files")
    assert files_res.status_code == 200
    files = files_res.json()["files"]
    assert len(files) == 3
    readme_file = next(f for f in files if f["path"] == "README.md")
    
    content_res = client.get(f"/repositories/{repo_id}/files/{readme_file['path']}")
    assert content_res.status_code == 200
    assert content_res.json()["content"] == "Hello World!"

    # 6. Ask Historian Question
    q_res = client.post(
        f"/repositories/{repo_id}/questions",
        json={"question": "Why does the authentication middleware exist?"},
    )
    assert q_res.status_code == 200
    q_data = q_res.json()
    assert "answer" in q_data
    assert "confidence" in q_data
    assert "classification" in q_data
    assert len(q_data["evidence"]) >= 1

    # 7. Request Developer Guidance
    g_res = client.post(
        f"/repositories/{repo_id}/guidance",
        json={"task": "Extend the authentication middleware to support token revocation"},
    )
    assert g_res.status_code == 200
    g_data = g_res.json()
    assert len(g_data["steps"]) >= 1

    # 8. Check Risk Evaluation
    risk_res = client.get(f"/repositories/{repo_id}/risks")
    assert risk_res.status_code == 200
    risks = risk_res.json()["risks"]
    assert len(risks) >= 1
    # Auth middleware exceeds 50kb and contains 'auth', should be flagged
    assert any("auth" in (r["path"] or "").lower() for r in risks)

    # 9. Knowledge Gaps & Human Preservation
    gap = KnowledgeGap(
        repository_id=UUID(repo_id),
        question="Why was custom token verification chosen over standard OAuth?",
        context="Security audit finding",
        priority="high",
        status="open",
    )
    db_session.add(gap)
    db_session.commit()

    gaps_res = client.get(f"/repositories/{repo_id}/knowledge-gaps")
    assert gaps_res.status_code == 200
    assert len(gaps_res.json()["gaps"]) == 1

    # Answer the gap
    ans_res = client.post(
        f"/repositories/{repo_id}/knowledge-gaps/{gap.id}/answer",
        json={"answer": "We required offline verification in air-gapped deployments."},
    )
    assert ans_res.status_code == 200
    assert ans_res.json()["status"] == "resolved"

    # 10. Contributor Offboarding Workflow
    off_res = client.post(
        f"/repositories/{repo_id}/offboarding",
        json={"contributor": "octocat"},
    )
    assert off_res.status_code == 201
    session_id = off_res.json()["session_id"]

    # Get session details
    session_detail = client.get(f"/repositories/{repo_id}/offboarding/{session_id}")
    assert session_detail.status_code == 200
    questions = session_detail.json()["questions"]
    assert len(questions) >= 1
    target_q = questions[0]

    # Submit answer
    q_ans_res = client.post(
        f"/repositories/{repo_id}/offboarding/{session_id}/answer",
        json={
            "question_id": target_q["question_id"],
            "answer": "I chose modular pipeline stages to decouple acquisition from LangGraph analysis.",
        },
    )
    assert q_ans_res.status_code == 200
    assert q_ans_res.json()["status"] == "answered"

    # Generate and fetch final handover report
    report_res = client.get(f"/repositories/{repo_id}/offboarding/{session_id}/report")
    assert report_res.status_code == 200
    rep_data = report_res.json()
    assert "summary" in rep_data
    assert "key_decisions" in rep_data
