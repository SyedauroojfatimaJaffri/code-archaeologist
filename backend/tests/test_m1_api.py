"""Unit tests for M1 API endpoints and locked contracts."""

import pytest
from unittest.mock import patch, MagicMock
from uuid import uuid4

from app.models.db_models import Repository, AnalysisJob, KnowledgeGap, OffboardingSession
from app.services.repository.validator import GitHubRepoRef, ValidationResult


def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@patch("app.api.routes_repositories.validate_public_repository")
def test_create_repository(mock_validate, client):
    mock_validate.return_value = ValidationResult(
        repo=GitHubRepoRef(
            owner="example",
            name="repo",
            github_url="https://github.com/example/repo",
            default_branch="main",
            is_public=True,
        ),
        metadata={},
    )

    payload = {"github_url": "https://github.com/example/repo"}
    response = client.post("/repositories", json=payload)

    assert response.status_code == 201
    data = response.json()
    assert "repository_id" in data
    assert data["github_url"] == "https://github.com/example/repo"
    assert data["status"] == "created"


def test_list_repositories(client, db_session):
    repo = Repository(
        user_id="usr_test_123456",
        github_url="https://github.com/example/repo1",
        name="repo1",
        owner="example",
        default_branch="main",
        status="created",
    )
    db_session.add(repo)
    db_session.commit()

    response = client.get("/repositories")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert data[0]["name"] == "repo1"


def test_get_repository_detail(client, db_session):
    repo = Repository(
        user_id="usr_test_123456",
        github_url="https://github.com/example/repo2",
        name="repo2",
        owner="example",
        default_branch="main",
        status="created",
    )
    db_session.add(repo)
    db_session.commit()

    response = client.get(f"/repositories/{repo.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["repository_id"] == str(repo.id)
    assert data["name"] == "repo2"


def test_get_repository_not_found_locked_error(client):
    fake_id = uuid4()
    response = client.get(f"/repositories/{fake_id}")
    assert response.status_code == 404
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "REPOSITORY_NOT_FOUND"


@patch("app.api.routes_analysis.run_analysis_job")
def test_start_analysis_and_get_job(mock_run_job, client, db_session):
    repo = Repository(
        user_id="usr_test_123456",
        github_url="https://github.com/example/repo3",
        name="repo3",
        owner="example",
        default_branch="main",
        status="created",
    )
    db_session.add(repo)
    db_session.commit()

    response = client.post(f"/repositories/{repo.id}/analyze")
    assert response.status_code == 202
    data = response.json()
    assert "analysis_job_id" in data
    assert data["status"] == "queued"

    job_id = data["analysis_job_id"]
    job_response = client.get(f"/analysis/{job_id}")
    assert job_response.status_code == 200
    job_data = job_response.json()
    assert job_data["analysis_job_id"] == job_id
    assert job_data["status"] == "queued"


def test_historian_question(client, db_session):
    repo = Repository(
        user_id="usr_test_123456",
        github_url="https://github.com/example/repo4",
        name="repo4",
        owner="example",
        default_branch="main",
        status="created",
    )
    db_session.add(repo)
    db_session.commit()

    payload = {"question": "Why does this authentication middleware exist?"}
    response = client.post(f"/repositories/{repo.id}/questions", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert "evidence" in data
    assert "confidence" in data
    assert "classification" in data


def test_developer_guidance(client, db_session):
    repo = Repository(
        user_id="usr_test_123456",
        github_url="https://github.com/example/repo5",
        name="repo5",
        owner="example",
        default_branch="main",
        status="created",
    )
    db_session.add(repo)
    db_session.commit()

    payload = {"task": "Add a new authentication endpoint"}
    response = client.post(f"/repositories/{repo.id}/guidance", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["task"] == payload["task"]
    assert "steps" in data


def test_knowledge_gaps_and_answer(client, db_session):
    repo = Repository(
        user_id="usr_test_123456",
        github_url="https://github.com/example/repo6",
        name="repo6",
        owner="example",
        default_branch="main",
        status="created",
    )
    db_session.add(repo)
    db_session.commit()

    gap = KnowledgeGap(
        repository_id=repo.id,
        question="Why was JWT secret chosen?",
        context="Security analysis",
        priority="high",
        status="open",
    )
    db_session.add(gap)
    db_session.commit()

    # List gaps
    list_res = client.get(f"/repositories/{repo.id}/knowledge-gaps")
    assert list_res.status_code == 200
    gaps_data = list_res.json()["gaps"]
    assert len(gaps_data) == 1
    assert gaps_data[0]["gap_id"] == str(gap.id)

    # Answer gap
    ans_res = client.post(
        f"/repositories/{repo.id}/knowledge-gaps/{gap.id}/answer",
        json={"answer": "Human-provided explanation of JWT secret choice."},
    )
    assert ans_res.status_code == 200
    ans_data = ans_res.json()
    assert ans_data["status"] == "resolved"
    assert "knowledge_item_id" in ans_data


def test_offboarding_create_and_get(client, db_session):
    repo = Repository(
        user_id="usr_test_123456",
        github_url="https://github.com/example/repo7",
        name="repo7",
        owner="example",
        default_branch="main",
        status="created",
    )
    db_session.add(repo)
    db_session.commit()

    # Create session
    create_res = client.post(
        f"/repositories/{repo.id}/offboarding",
        json={"contributor": "alice"},
    )
    assert create_res.status_code == 201
    session_id = create_res.json()["session_id"]

    # Get session
    get_res = client.get(f"/repositories/{repo.id}/offboarding/{session_id}")
    assert get_res.status_code == 200
    session_data = get_res.json()
    assert session_data["session_id"] == session_id
    assert session_data["status"] == "created"
    assert len(session_data["questions"]) >= 1


def test_user_isolation_cannot_access_other_users_repo(client_user2, db_session):
    """User 2 should NOT be able to view, query or analyze User 1's repository."""
    repo = Repository(
        user_id="usr_test_123456",  # Owned by User 1
        github_url="https://github.com/example/user1-repo",
        name="user1-repo",
        owner="example",
        default_branch="main",
        status="created",
    )
    db_session.add(repo)
    db_session.commit()

    # User 2 attempts to get repo detail
    res = client_user2.get(f"/repositories/{repo.id}")
    assert res.status_code == 404
    assert res.json()["error"]["code"] == "REPOSITORY_NOT_FOUND"

    # User 2 attempts to list files
    files_res = client_user2.get(f"/repositories/{repo.id}/files")
    assert files_res.status_code == 404
    assert files_res.json()["error"]["code"] == "REPOSITORY_NOT_FOUND"

    # User 2 attempts to analyze repo
    analyze_res = client_user2.post(f"/repositories/{repo.id}/analyze")
    assert analyze_res.status_code == 404
    assert analyze_res.json()["error"]["code"] == "REPOSITORY_NOT_FOUND"

    # User 2 attempts to ask historian question
    question_res = client_user2.post(
        f"/repositories/{repo.id}/questions",
        json={"question": "Why does this exist?"},
    )
    assert question_res.status_code == 404
    assert question_res.json()["error"]["code"] == "REPOSITORY_NOT_FOUND"


def test_user_isolation_list_repositories_only_own_user1(client, db_session):
    """User 1 only sees User 1's repos, not User 2's repos."""
    repo1 = Repository(
        user_id="usr_test_123456",
        github_url="https://github.com/example/u1-repo",
        name="u1-repo",
        owner="example",
        default_branch="main",
        status="created",
    )
    repo2 = Repository(
        user_id="usr_test_789012",
        github_url="https://github.com/example/u2-repo",
        name="u2-repo",
        owner="example",
        default_branch="main",
        status="created",
    )
    db_session.add_all([repo1, repo2])
    db_session.commit()

    res1 = client.get("/repositories")
    assert res1.status_code == 200
    ids_1 = [r["repository_id"] for r in res1.json()]
    assert str(repo1.id) in ids_1
    assert str(repo2.id) not in ids_1


def test_user_isolation_list_repositories_only_own_user2(client_user2, db_session):
    """User 2 only sees User 2's repos, not User 1's repos."""
    repo1 = Repository(
        user_id="usr_test_123456",
        github_url="https://github.com/example/u1-repo-b",
        name="u1-repo-b",
        owner="example",
        default_branch="main",
        status="created",
    )
    repo2 = Repository(
        user_id="usr_test_789012",
        github_url="https://github.com/example/u2-repo-b",
        name="u2-repo-b",
        owner="example",
        default_branch="main",
        status="created",
    )
    db_session.add_all([repo1, repo2])
    db_session.commit()

    res2 = client_user2.get("/repositories")
    assert res2.status_code == 200
    ids_2 = [r["repository_id"] for r in res2.json()]
    assert str(repo2.id) in ids_2
    assert str(repo1.id) not in ids_2


def test_unauthenticated_request_rejected(unauthenticated_client):
    """Requests without a valid Supabase token must return 401 with locked error format."""
    res = unauthenticated_client.get("/repositories")
    assert res.status_code == 401
    data = res.json()
    assert "error" in data
    assert data["error"]["code"] == "UNAUTHORIZED"


def test_repository_files_and_content(client, db_session):
    """GET /repositories/{id}/files and GET /repositories/{id}/files/{path}."""
    repo = Repository(
        user_id="usr_test_123456",
        github_url="https://github.com/example/repo-files",
        name="repo-files",
        owner="example",
        default_branch="main",
        status="created",
    )
    db_session.add(repo)
    db_session.commit()

    from app.models.db_models import RepositoryFile
    file_record = RepositoryFile(
        repository_id=repo.id,
        path="src/index.ts",
        language="typescript",
        content="console.log('hello');",
        size=21,
        hash="abcdef123456",
    )
    db_session.add(file_record)
    db_session.commit()

    # List files
    tree_res = client.get(f"/repositories/{repo.id}/files")
    assert tree_res.status_code == 200
    tree_data = tree_res.json()
    assert tree_data["repository_id"] == str(repo.id)
    assert len(tree_data["files"]) == 1
    assert tree_data["files"][0]["path"] == "src/index.ts"

    # Get file detail
    detail_res = client.get(f"/repositories/{repo.id}/files/src/index.ts")
    assert detail_res.status_code == 200
    detail_data = detail_res.json()
    assert detail_data["path"] == "src/index.ts"
    assert detail_data["content"] == "console.log('hello');"
    assert detail_data["language"] == "typescript"

    # Not found file
    nf_res = client.get(f"/repositories/{repo.id}/files/nonexistent.py")
    assert nf_res.status_code == 404
    assert nf_res.json()["error"]["code"] == "FILE_NOT_FOUND"


def test_repository_risks_and_knowledge(client, db_session):
    """GET /repositories/{id}/risks and GET /repositories/{id}/knowledge."""
    repo = Repository(
        user_id="usr_test_123456",
        github_url="https://github.com/example/repo-risk-know",
        name="repo-risk-know",
        owner="example",
        default_branch="main",
        status="created",
    )
    db_session.add(repo)
    db_session.commit()

    from app.models.db_models import RiskRecord, KnowledgeItem
    risk = RiskRecord(
        repository_id=repo.id,
        score=0.85,
        signals={"high_churn": 42, "critical_path": True},
        explanation="High change velocity in core authentication.",
    )
    k_item = KnowledgeItem(
        repository_id=repo.id,
        user_id="usr_test_123456",
        title="Auth Design Rationale",
        content="JWT is used with RS256 for microservice SSO verification.",
        source="human",
    )
    db_session.add_all([risk, k_item])
    db_session.commit()

    # Get risks
    risk_res = client.get(f"/repositories/{repo.id}/risks")
    assert risk_res.status_code == 200
    risk_data = risk_res.json()
    assert len(risk_data["risks"]) == 1
    assert risk_data["risks"][0]["score"] == 0.85
    assert len(risk_data["risks"][0]["signals"]) == 2

    # Get knowledge
    know_res = client.get(f"/repositories/{repo.id}/knowledge")
    assert know_res.status_code == 200
    know_data = know_res.json()
    assert len(know_data["items"]) == 1
    assert know_data["items"][0]["title"] == "Auth Design Rationale"


def test_validation_error_format(client):
    """Ensure malformed JSON returns 400 with locked error structure."""
    res = client.post("/repositories", content="invalid-json", headers={"Content-Type": "application/json"})
    assert res.status_code == 400
    data = res.json()
    assert "error" in data
    assert data["error"]["code"] == "INVALID_REQUEST"

