"""Pytest fixtures for M1 API and backend testing."""

import os
from typing import Generator
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from sqlalchemy.pool import StaticPool

# Set dummy environment variables before importing app
os.environ["SUPABASE_JWT_SECRET"] = "test-jwt-secret-key-1234567890"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["AUTO_CREATE_TABLES"] = "false"

from app.core.security import AuthenticatedUser, get_current_user
from app.main import app
from app.models.db_models import Base, get_db

TEST_USER_ID = "usr_test_123456"
TEST_USER = AuthenticatedUser(user_id=TEST_USER_ID, email="test@example.com")


@pytest.fixture(scope="session")
def engine():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    
    # Mock pgvector column for sqlite compatibility during test table creation if needed
    from pgvector.sqlalchemy import Vector
    from sqlalchemy.dialects.postgresql import JSONB, UUID
    from sqlalchemy.ext.compiler import compiles

    @compiles(Vector, "sqlite")
    def compile_vector_sqlite(element, compiler, **kw):
        return "TEXT"

    @compiles(JSONB, "sqlite")
    def compile_jsonb_sqlite(element, compiler, **kw):
        return "JSON"

    @compiles(UUID, "sqlite")
    def compile_uuid_sqlite(element, compiler, **kw):
        return "CHAR(32)"

    from app.models import db_models
    db_models.engine = engine
    db_models.SessionLocal.configure(bind=engine)
    Base.metadata.create_all(bind=engine)
    return engine


@pytest.fixture
def db_session(engine) -> Generator[Session, None, None]:
    connection = engine.connect()
    transaction = connection.begin()
    SessionTest = sessionmaker(bind=connection, autoflush=False, autocommit=False)
    session = SessionTest()

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db_session: Session) -> Generator[TestClient, None, None]:
    def _get_test_db():
        try:
            yield db_session
        finally:
            pass

    def _get_test_user():
        return TEST_USER

    app.dependency_overrides[get_db] = _get_test_db
    app.dependency_overrides[get_current_user] = _get_test_user

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


TEST_USER_2_ID = "usr_test_789012"
TEST_USER_2 = AuthenticatedUser(user_id=TEST_USER_2_ID, email="user2@example.com")


@pytest.fixture
def client_user2(db_session: Session) -> Generator[TestClient, None, None]:
    def _get_test_db():
        try:
            yield db_session
        finally:
            pass

    def _get_test_user():
        return TEST_USER_2

    app.dependency_overrides[get_db] = _get_test_db
    app.dependency_overrides[get_current_user] = _get_test_user

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def unauthenticated_client(db_session: Session) -> Generator[TestClient, None, None]:
    def _get_test_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = _get_test_db
    # Do not override get_current_user so default bearer scheme runs

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()

