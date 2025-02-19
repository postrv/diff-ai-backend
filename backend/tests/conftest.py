# backend/tests/conftest.py
import pytest
import os
import asyncio
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.models.document import Base
from backend.app.config import settings
from backend.app.database import get_db
from backend.app.services.ai_service import AIService


# Set up pytest-asyncio
@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# Test database connection
@pytest.fixture(scope="session")
def engine():
    """Create a test database engine."""
    # Convert PostgresDsn to string for SQLAlchemy
    database_url = str(settings.database_url)
    engine = create_engine(database_url, echo=True)
    yield engine


@pytest.fixture(scope="session")
def create_tables(engine):
    """Create all tables in the test database."""
    Base.metadata.create_all(bind=engine)
    yield
    # Optionally, drop tables after tests
    # Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session(engine, create_tables):
    """Create a fresh database session for each test."""
    connection = engine.connect()
    transaction = connection.begin()
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=connection)
    session = SessionLocal()

    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture
def client(db_session):
    """Create a test client with a DB session dependency override."""

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    del app.dependency_overrides[get_db]


@pytest.fixture
def upload_dir():
    """Ensure upload directory exists for tests."""
    upload_dir = "uploads"
    os.makedirs(upload_dir, exist_ok=True)
    yield upload_dir


@pytest.fixture
def test_db_connection():
    """Test database connection."""
    try:
        # Convert PostgresDsn to string for SQLAlchemy
        database_url = str(settings.database_url)
        engine = create_engine(database_url)
        connection = engine.connect()
        connection.close()
        return True
    except Exception as e:
        pytest.fail(f"Database connection failed: {str(e)}")


# Mock AI service for testing
@pytest.fixture(autouse=True)
def mock_ai_service(monkeypatch):
    """
    Mock the AI service for testing to avoid actual API calls.
    This automatically applies to all tests.
    """

    async def mock_analyze_diff(self, doc_a, doc_b, diff_data):
        return "This is a mock AI summary for testing purposes."

    async def mock_smart_merge(self, request):
        return {
            "merged_content": request.doc_b if request.conflict_resolution == "latest" else request.doc_a,
            "report": {
                "conflicts_resolved": 2,
                "strategy_applied": request.conflict_resolution,
                "summary": "Mock merge completed using the specified strategy."
            }
        }

    # Apply the mocks
    monkeypatch.setattr(AIService, "analyze_diff", mock_analyze_diff)
    monkeypatch.setattr(AIService, "smart_merge", mock_smart_merge)