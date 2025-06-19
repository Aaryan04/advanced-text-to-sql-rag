import pytest
import asyncio
import os
import tempfile
from pathlib import Path
import sys

# Add backend to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from database.connection import Base, DatabaseManager
from simple_main import app

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def test_db_file():
    """Create a temporary database file for testing."""
    db_fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(db_fd)
    yield db_path
    os.unlink(db_path)

@pytest.fixture
async def test_db_manager(test_db_file):
    """Create a test database manager with isolated database."""
    db_manager = DatabaseManager()
    db_manager.database_url = f"sqlite+aiosqlite:///{test_db_file}"
    await db_manager.initialize()
    yield db_manager
    await db_manager.close()

@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    with TestClient(app) as test_client:
        yield test_client

@pytest.fixture
def sample_query_request():
    """Sample query request for testing."""
    return {
        "question": "Show all employees in engineering",
        "include_explanation": True,
        "max_results": 100
    }

@pytest.fixture
def sample_analytics_query():
    """Sample analytics query for testing."""
    return {
        "question": "What is the average salary by department?",
        "include_explanation": True,
        "max_results": 100
    }

@pytest.fixture
def sample_complex_query():
    """Sample complex query for testing."""
    return {
        "question": "Find top 5 highest paid employees with their departments",
        "include_explanation": True,
        "max_results": 5
    }