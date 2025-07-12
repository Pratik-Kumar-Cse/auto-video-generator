"""
Test configuration and fixtures for FastAPI Video Generator
"""

import asyncio
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from motor.motor_asyncio import AsyncIOMotorClient
from typing import AsyncGenerator, Generator

from main import app
from app.core.database import get_database
from app.core.redis_client import RedisService
from app.core.config import settings


# Test database configuration
TEST_DATABASE_URL = "mongodb://localhost:27017/test_video_generator"
TEST_REDIS_URL = "redis://localhost:6379/1"


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def test_db():
    """Create test database connection."""
    client = AsyncIOMotorClient(TEST_DATABASE_URL)
    db = client.get_default_database()
    
    # Clean up any existing test data
    await db.scripts.delete_many({})
    await db.videos.delete_many({})
    await db.users.delete_many({})
    
    yield db
    
    # Cleanup after tests
    await db.scripts.delete_many({})
    await db.videos.delete_many({})
    await db.users.delete_many({})
    client.close()


@pytest.fixture
def mock_redis():
    """Mock Redis service for testing."""
    mock_redis = MagicMock(spec=RedisService)
    mock_redis.get = AsyncMock(return_value=None)
    mock_redis.set = AsyncMock(return_value=True)
    mock_redis.delete = AsyncMock(return_value=True)
    mock_redis.lpush = AsyncMock(return_value=1)
    mock_redis.lpop = AsyncMock(return_value=None)
    mock_redis.publish = AsyncMock(return_value=1)
    mock_redis.subscribe = AsyncMock()
    mock_redis.increment = AsyncMock(return_value=1)
    mock_redis.expire = AsyncMock(return_value=True)
    mock_redis.exists = AsyncMock(return_value=False)
    return mock_redis


@pytest.fixture
def client(test_db, mock_redis):
    """Create test client with mocked dependencies."""
    
    def override_get_database():
        return test_db
    
    app.dependency_overrides[get_database] = override_get_database
    
    with patch('app.core.redis_client.redis_service', mock_redis):
        with TestClient(app) as test_client:
            yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture
def mock_llm_service():
    """Mock LLM service for testing."""
    mock_service = MagicMock()
    mock_service.generate_script = AsyncMock(return_value={
        "title": "Test Script",
        "content": "This is a test script content.",
        "metadata": {"duration": "60 seconds"}
    })
    mock_service.validate_link = AsyncMock(return_value=True)
    return mock_service


@pytest.fixture
def mock_autogen_workflow():
    """Mock AutoGen workflow for testing."""
    mock_workflow = MagicMock()
    mock_workflow.generate_script = AsyncMock(return_value={
        "script": "Test script content",
        "title": "Test Title",
        "metadata": {}
    })
    return mock_workflow


@pytest.fixture
def sample_script_data():
    """Sample script data for testing."""
    return {
        "_id": "test_script_id",
        "user_id": "test_user",
        "title": "Test Script",
        "content": "This is a test script content.",
        "topic": "Test Topic",
        "video_type": "shorts",
        "keywords": {"tone": "casual", "audience": "general"},
        "input_type": "TOPIC",
        "status": "completed",
        "metadata": {},
        "created_at": "2024-01-01T00:00:00",
        "updated_at": "2024-01-01T00:00:00"
    }


@pytest.fixture
def sample_video_data():
    """Sample video data for testing."""
    return {
        "_id": "test_video_id",
        "user_id": "test_user",
        "script_id": "test_script_id",
        "status": "PENDING",
        "voice_id": "test_voice",
        "avatar_id": "test_avatar",
        "template_id": "test_template",
        "view_type": "PORTRAIT",
        "metadata": {},
        "created_at": "2024-01-01T00:00:00",
        "updated_at": "2024-01-01T00:00:00"
    }


@pytest.fixture
def sample_user_data():
    """Sample user data for testing."""
    return {
        "_id": "test_user",
        "email": "test@example.com",
        "username": "testuser",
        "is_active": True,
        "subscription": {
            "plan": "premium",
            "credits": 100,
            "expires_at": "2024-12-31T23:59:59"
        },
        "created_at": "2024-01-01T00:00:00",
        "updated_at": "2024-01-01T00:00:00"
    }


@pytest.fixture
def mock_media_utils():
    """Mock media utilities for testing."""
    with patch('app.utils.media_utils.MediaUtils') as mock:
        mock.generate_thumbnail.return_value = True
        mock.create_image_thumbnail.return_value = "/path/to/thumbnail.jpg"
        mock.download_video.return_value = True
        mock.get_file_metadata.return_value = {
            "filename": "test.mp4",
            "size": 1024,
            "mime_type": "video/mp4"
        }
        mock.validate_media_file.return_value = True
        yield mock


@pytest.fixture
def mock_rate_limiter():
    """Mock rate limiter for testing."""
    mock_limiter = MagicMock()
    mock_limiter.is_allowed = AsyncMock(return_value=True)
    mock_limiter.get_remaining = AsyncMock(return_value=100)
    mock_limiter.get_reset_time = AsyncMock(return_value=3600)
    return mock_limiter


@pytest.fixture
def mock_external_apis():
    """Mock external API calls."""
    with patch('requests.get') as mock_get, \
         patch('requests.post') as mock_post:
        
        # Mock successful responses
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": True}
        mock_response.text = "Success"
        
        mock_get.return_value = mock_response
        mock_post.return_value = mock_response
        
        yield {
            "get": mock_get,
            "post": mock_post,
            "response": mock_response
        }


@pytest.fixture
def mock_file_operations():
    """Mock file system operations."""
    with patch('os.path.exists', return_value=True), \
         patch('os.makedirs'), \
         patch('os.remove'), \
         patch('builtins.open', create=True) as mock_open:
        
        mock_open.return_value.__enter__.return_value.read.return_value = "test content"
        yield mock_open


# Async test helpers
class AsyncContextManager:
    """Helper for async context managers in tests."""
    
    def __init__(self, async_func):
        self.async_func = async_func
    
    async def __aenter__(self):
        return await self.async_func()
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


@pytest.fixture
def async_context_manager():
    """Fixture for creating async context managers in tests."""
    return AsyncContextManager


# Test data generators
def generate_test_script(**kwargs):
    """Generate test script data with optional overrides."""
    default_data = {
        "topic": "Test Topic",
        "video_type": "shorts",
        "keywords": {"tone": "casual"},
        "input_type": "TOPIC",
        "video_link": None
    }
    default_data.update(kwargs)
    return default_data


def generate_test_video(**kwargs):
    """Generate test video data with optional overrides."""
    default_data = {
        "script_id": "test_script_id",
        "voice_id": "test_voice",
        "avatar_id": "test_avatar",
        "template_id": "test_template",
        "view_type": "PORTRAIT",
        "caption": None
    }
    default_data.update(kwargs)
    return default_data


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "unit: mark test as unit test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "redis: mark test as requiring Redis"
    )
    config.addinivalue_line(
        "markers", "mongodb: mark test as requiring MongoDB"
    )