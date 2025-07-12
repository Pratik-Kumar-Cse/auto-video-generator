"""
Unit tests for Script service
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from bson import ObjectId

from app.services.script_service import ScriptService
from app.core.exceptions import (
    ScriptNotFoundException,
    ScriptProcessingException,
    ValidationException
)


class TestScriptService:
    """Test Script service functionality"""

    @pytest.fixture
    def mock_db(self):
        """Mock database connection"""
        mock_db = MagicMock()
        mock_db.scripts = MagicMock()
        mock_db.scripts.find_one = AsyncMock()
        mock_db.scripts.find = MagicMock()
        mock_db.scripts.insert_one = AsyncMock()
        mock_db.scripts.update_one = AsyncMock()
        mock_db.scripts.delete_one = AsyncMock()
        mock_db.scripts.count_documents = AsyncMock()
        mock_db.scripts.aggregate = MagicMock()
        return mock_db

    @pytest.fixture
    def mock_redis(self):
        """Mock Redis service"""
        mock_redis = MagicMock()
        mock_redis.get = AsyncMock()
        mock_redis.set = AsyncMock()
        mock_redis.lpush = AsyncMock()
        mock_redis.publish = AsyncMock()
        mock_redis.cache_with_ttl = AsyncMock()
        return mock_redis

    @pytest.fixture
    def mock_llm_service(self):
        """Mock LLM service"""
        mock_llm = MagicMock()
        mock_llm.generate_script = AsyncMock()
        mock_llm.validate_link = AsyncMock()
        return mock_llm

    @pytest.fixture
    def mock_autogen_workflow(self):
        """Mock AutoGen workflow"""
        mock_workflow = MagicMock()
        mock_workflow.generate_script = AsyncMock()
        return mock_workflow

    @pytest.fixture
    def script_service(self, mock_db, mock_redis, mock_llm_service, mock_autogen_workflow):
        """Create ScriptService with mocked dependencies"""
        with patch('app.services.script_service.redis_service', mock_redis), \
             patch('app.services.script_service.LLMService', return_value=mock_llm_service), \
             patch('app.services.script_service.AutoGenWorkflow', return_value=mock_autogen_workflow):
            return ScriptService(mock_db)

    @pytest.fixture
    def sample_script_data(self):
        """Sample script data for testing"""
        return {
            "_id": ObjectId(),
            "user_id": "test_user",
            "title": "Test Script",
            "content": "This is a test script content.",
            "topic": "Test Topic",
            "video_type": "shorts",
            "keywords": {"tone": "casual", "audience": "general"},
            "input_type": "TOPIC",
            "status": "completed",
            "metadata": {},
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }

    @pytest.mark.asyncio
    async def test_create_script_success(self, script_service, mock_db):
        """Test successful script creation"""
        mock_db.scripts.insert_one.return_value.inserted_id = ObjectId()
        mock_db.scripts.find_one.return_value = {
            "_id": ObjectId(),
            "user_id": "test_user",
            "title": "Test Script",
            "content": "Test content",
            "topic": "Test Topic",
            "video_type": "shorts",
            "keywords": {},
            "input_type": "TOPIC",
            "status": "draft",
            "metadata": {},
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }

        result = await script_service.create_script(
            user_id="test_user",
            title="Test Script",
            content="Test content",
            topic="Test Topic",
            video_type="shorts",
            keywords={},
            input_type="TOPIC"
        )

        assert result is not None
        assert result["title"] == "Test Script"
        mock_db.scripts.insert_one.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_script_of_user_success(self, script_service, mock_db, sample_script_data):
        """Test successful script retrieval"""
        mock_db.scripts.find_one.return_value = sample_script_data

        result = await script_service.get_script_of_user(
            "test_user", str(sample_script_data["_id"])
        )

        assert result is not None
        assert result["title"] == "Test Script"
        mock_db.scripts.find_one.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_script_of_user_not_found(self, script_service, mock_db):
        """Test script not found"""
        mock_db.scripts.find_one.return_value = None

        result = await script_service.get_script_of_user("test_user", "nonexistent_id")

        assert result is None

    @pytest.mark.asyncio
    async def test_update_script_success(self, script_service, mock_db, sample_script_data):
        """Test successful script update"""
        updated_data = sample_script_data.copy()
        updated_data["title"] = "Updated Title"
        updated_data["content"] = "Updated content"

        mock_db.scripts.find_one.return_value = sample_script_data
        mock_db.scripts.update_one.return_value.modified_count = 1
        mock_db.scripts.find_one.side_effect = [sample_script_data, updated_data]

        result = await script_service.update_script(
            "test_user",
            str(sample_script_data["_id"]),
            {"title": "Updated Title", "content": "Updated content"}
        )

        assert result is not None
        assert result["title"] == "Updated Title"
        mock_db.scripts.update_one.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_script_success(self, script_service, mock_db, sample_script_data):
        """Test successful script deletion"""
        mock_db.scripts.find_one.return_value = sample_script_data
        mock_db.scripts.delete_one.return_value.deleted_count = 1

        result = await script_service.delete_script(
            "test_user", str(sample_script_data["_id"])
        )

        assert result is True
        mock_db.scripts.delete_one.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_script_not_found(self, script_service, mock_db):
        """Test deleting non-existent script"""
        mock_db.scripts.find_one.return_value = None

        result = await script_service.delete_script("test_user", "nonexistent_id")

        assert result is False

    @pytest.mark.asyncio
    async def test_get_all_scripts_by_user(self, script_service, mock_db, sample_script_data):
        """Test getting all scripts for a user"""
        mock_cursor = MagicMock()
        mock_cursor.skip.return_value = mock_cursor
        mock_cursor.limit.return_value = mock_cursor
        mock_cursor.sort.return_value = mock_cursor
        mock_cursor.to_list.return_value = [sample_script_data]

        mock_db.scripts.find.return_value = mock_cursor
        mock_db.scripts.count_documents.return_value = 1

        scripts, total_count = await script_service.get_all_scripts_by_user(
            user_id="test_user",
            page=1,
            per_page=10
        )

        assert len(scripts) == 1
        assert total_count == 1
        assert scripts[0]["title"] == "Test Script"

    @pytest.mark.asyncio
    async def test_get_all_scripts_with_filters(self, script_service, mock_db, sample_script_data):
        """Test getting scripts with filters"""
        mock_cursor = MagicMock()
        mock_cursor.skip.return_value = mock_cursor
        mock_cursor.limit.return_value = mock_cursor
        mock_cursor.sort.return_value = mock_cursor
        mock_cursor.to_list.return_value = [sample_script_data]

        mock_db.scripts.find.return_value = mock_cursor
        mock_db.scripts.count_documents.return_value = 1

        scripts, total_count = await script_service.get_all_scripts_by_user(
            user_id="test_user",
            page=1,
            per_page=10,
            filter_name="Test",
            video_type="shorts",
            input_type="TOPIC"
        )

        assert len(scripts) == 1
        mock_db.scripts.find.assert_called_once()
        # Verify filter was applied
        call_args = mock_db.scripts.find.call_args[0][0]
        assert "user_id" in call_args
        assert "$or" in call_args  # Filter by name

    @pytest.mark.asyncio
    async def test_generate_script_async_success(self, script_service, mock_llm_service, mock_redis):
        """Test successful async script generation"""
        mock_llm_service.generate_script.return_value = {
            "title": "Generated Script",
            "content": "Generated content",
            "metadata": {}
        }

        task_id = await script_service.generate_script_async(
            topic="AI Technology",
            video_type="shorts",
            keywords={"tone": "casual"},
            input_type="TOPIC"
        )

        assert task_id is not None
        assert isinstance(task_id, str)
        mock_redis.lpush.assert_called()

    @pytest.mark.asyncio
    async def test_generate_script_with_autogen(self, script_service, mock_autogen_workflow):
        """Test script generation using AutoGen workflow"""
        mock_autogen_workflow.generate_script.return_value = {
            "script": "Generated script content",
            "title": "Generated Title",
            "metadata": {}
        }

        result = await script_service.generate_script_with_autogen(
            topic="AI Technology",
            video_type="shorts",
            keywords={"tone": "casual"},
            input_type="TOPIC"
        )

        assert result is not None
        assert "script" in result
        mock_autogen_workflow.generate_script.assert_called_once()

    @pytest.mark.asyncio
    async def test_regenerate_script_success(self, script_service, mock_llm_service, sample_script_data):
        """Test successful script regeneration"""
        mock_llm_service.generate_script.return_value = {
            "title": "Regenerated Script",
            "content": "Regenerated content",
            "metadata": {}
        }

        result = await script_service.regenerate_script(
            user_id="test_user",
            script_data=sample_script_data,
            topic="Updated Topic",
            video_type="youtube",
            link=None,
            keywords={"tone": "professional"}
        )

        assert result is not None
        assert result["title"] == "Regenerated Script"
        mock_llm_service.generate_script.assert_called_once()

    @pytest.mark.asyncio
    async def test_validate_script_input_valid(self, script_service):
        """Test valid script input validation"""
        is_valid = await script_service.validate_script_input(
            topic="AI Technology",
            video_type="shorts",
            input_type="TOPIC"
        )

        assert is_valid is True

    @pytest.mark.asyncio
    async def test_validate_script_input_invalid_topic(self, script_service):
        """Test invalid topic validation"""
        with pytest.raises(ValidationException):
            await script_service.validate_script_input(
                topic="",  # Empty topic
                video_type="shorts",
                input_type="TOPIC"
            )

    @pytest.mark.asyncio
    async def test_validate_script_input_invalid_video_type(self, script_service):
        """Test invalid video type validation"""
        with pytest.raises(ValidationException):
            await script_service.validate_script_input(
                topic="AI Technology",
                video_type="invalid_type",
                input_type="TOPIC"
            )

    @pytest.mark.asyncio
    async def test_validate_link_success(self, script_service, mock_llm_service):
        """Test successful link validation"""
        mock_llm_service.validate_link.return_value = True

        result = await script_service.validate_link(
            "https://youtube.com/watch?v=123",
            "youtube"
        )

        assert result is True
        mock_llm_service.validate_link.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_trending_topics(self, script_service, mock_db):
        """Test getting trending topics"""
        mock_cursor = MagicMock()
        mock_cursor.to_list.return_value = [
            {"_id": "AI Technology", "count": 10},
            {"_id": "Machine Learning", "count": 8},
            {"_id": "Data Science", "count": 6}
        ]

        mock_db.scripts.aggregate.return_value = mock_cursor

        topics = await script_service.get_trending_topics(limit=5)

        assert len(topics) == 3
        assert topics[0]["topic"] == "AI Technology"
        assert topics[0]["count"] == 10

    @pytest.mark.asyncio
    async def test_get_script_analytics(self, script_service, mock_db):
        """Test getting script analytics"""
        mock_cursor = MagicMock()
        mock_cursor.to_list.return_value = [
            {
                "_id": {"video_type": "shorts", "status": "completed"},
                "count": 15,
                "avg_length": 250
            },
            {
                "_id": {"video_type": "youtube", "status": "completed"},
                "count": 8,
                "avg_length": 500
            }
        ]

        mock_db.scripts.aggregate.return_value = mock_cursor

        analytics = await script_service.get_script_analytics("test_user")

        assert len(analytics) == 2
        assert analytics[0]["count"] == 15

    @pytest.mark.asyncio
    async def test_search_scripts(self, script_service, mock_db, sample_script_data):
        """Test script search functionality"""
        mock_cursor = MagicMock()
        mock_cursor.skip.return_value = mock_cursor
        mock_cursor.limit.return_value = mock_cursor
        mock_cursor.to_list.return_value = [sample_script_data]

        mock_db.scripts.find.return_value = mock_cursor
        mock_db.scripts.count_documents.return_value = 1

        results, total = await script_service.search_scripts(
            user_id="test_user",
            query="Test",
            page=1,
            per_page=10
        )

        assert len(results) == 1
        assert total == 1
        mock_db.scripts.find.assert_called_once()

    @pytest.mark.asyncio
    async def test_duplicate_script(self, script_service, mock_db, sample_script_data):
        """Test script duplication"""
        mock_db.scripts.find_one.return_value = sample_script_data
        mock_db.scripts.insert_one.return_value.inserted_id = ObjectId()

        new_script_data = sample_script_data.copy()
        new_script_data["title"] = "Test Script (Copy)"
        mock_db.scripts.find_one.side_effect = [sample_script_data, new_script_data]

        result = await script_service.duplicate_script(
            "test_user", str(sample_script_data["_id"])
        )

        assert result is not None
        assert "(Copy)" in result["title"]
        mock_db.scripts.insert_one.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_script_using_task_id(self, script_service, mock_redis, sample_script_data):
        """Test getting script using task ID"""
        import json
        mock_redis.get.return_value = json.dumps(sample_script_data, default=str).encode()

        result = script_service.get_script_using_task_id("test_task_id")

        assert result is not None
        mock_redis.get.assert_called_once_with("script_result:test_task_id")

    @pytest.mark.asyncio
    async def test_cache_script_result(self, script_service, mock_redis):
        """Test caching script result"""
        script_data = {
            "title": "Test Script",
            "content": "Test content",
            "metadata": {}
        }

        await script_service.cache_script_result("test_task_id", script_data)

        mock_redis.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_media_content(self, script_service):
        """Test processing media content from URLs"""
        with patch('app.utils.media_utils.MediaUtils') as mock_media:
            mock_media.download_video.return_value = True
            mock_media.generate_thumbnail.return_value = True
            mock_media.get_file_metadata.return_value = {
                "duration": 120,
                "format": "mp4"
            }

            result = await script_service.process_media_content(
                "https://example.com/video.mp4",
                "video"
            )

            assert result is not None
            assert "metadata" in result

    @pytest.mark.asyncio
    async def test_extract_keywords_from_content(self, script_service):
        """Test keyword extraction from content"""
        content = "This is a test content about artificial intelligence and machine learning."

        keywords = await script_service.extract_keywords_from_content(content)

        assert isinstance(keywords, list)
        assert len(keywords) > 0

    @pytest.mark.asyncio
    async def test_generate_script_variations(self, script_service, mock_llm_service):
        """Test generating script variations"""
        mock_llm_service.generate_script.side_effect = [
            {"title": "Variation 1", "content": "Content 1", "metadata": {}},
            {"title": "Variation 2", "content": "Content 2", "metadata": {}},
            {"title": "Variation 3", "content": "Content 3", "metadata": {}}
        ]

        variations = await script_service.generate_script_variations(
            topic="AI Technology",
            video_type="shorts",
            count=3
        )

        assert len(variations) == 3
        assert variations[0]["title"] == "Variation 1"
        assert mock_llm_service.generate_script.call_count == 3

    @pytest.mark.asyncio
    async def test_error_handling_database_error(self, script_service, mock_db):
        """Test error handling for database errors"""
        mock_db.scripts.find_one.side_effect = Exception("Database connection failed")

        with pytest.raises(ScriptProcessingException):
            await script_service.get_script_of_user("test_user", "script_id")

    @pytest.mark.asyncio
    async def test_error_handling_llm_service_error(self, script_service, mock_llm_service):
        """Test error handling for LLM service errors"""
        mock_llm_service.generate_script.side_effect = Exception("LLM service failed")

        with pytest.raises(ScriptProcessingException):
            await script_service.generate_script_async(
                topic="AI Technology",
                video_type="shorts",
                keywords={},
                input_type="TOPIC"
            )

    @pytest.mark.asyncio
    async def test_concurrent_script_generation(self, script_service, mock_llm_service):
        """Test concurrent script generation"""
        import asyncio

        mock_llm_service.generate_script.return_value = {
            "title": "Generated Script",
            "content": "Generated content",
            "metadata": {}
        }

        # Generate multiple scripts concurrently
        tasks = []
        for i in range(3):
            task = script_service.generate_script_async(
                topic=f"Topic {i}",
                video_type="shorts",
                keywords={},
                input_type="TOPIC"
            )
            tasks.append(task)

        task_ids = await asyncio.gather(*tasks)

        assert len(task_ids) == 3
        assert all(isinstance(task_id, str) for task_id in task_ids)

    @pytest.mark.asyncio
    async def test_script_content_validation(self, script_service):
        """Test script content validation"""
        # Valid content
        valid_content = "This is a valid script content with proper structure."
        is_valid = await script_service.validate_script_content(valid_content)
        assert is_valid is True

        # Invalid content (too short)
        invalid_content = "Too short"
        is_valid = await script_service.validate_script_content(invalid_content)
        assert is_valid is False

        # Invalid content (empty)
        empty_content = ""
        is_valid = await script_service.validate_script_content(empty_content)
        assert is_valid is False