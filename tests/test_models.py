"""
Unit tests for Pydantic models
"""

import pytest
from datetime import datetime
from pydantic import ValidationError

from app.models.script import (
    ScriptCreate,
    ScriptUpdate,
    GenerateScriptRequest,
    RegenerateScriptRequest,
    ValidateLinkRequest,
    Script,
    ScriptResponse,
    ScriptListData,
    ScriptListResponse
)
from app.models.video import (
    VideoStatus,
    VideoViewType,
    UploadDomain,
    ScriptType,
    VideoType,
    Caption,
    Keywords,
    VideoMetadata,
    GenerateVideoRequest,
    GenerateVideoByIdRequest,
    GenerateWorkflowVideoRequest,
    GenerateWorkflowVideoByIdRequest,
    UploadVideoRequest,
    UpdateMetadataRequest,
    VideoUpdate,
    VideoCreate,
    VideoQualityRequest,
    VideoData,
    VideoResponseModel,
    VideoStatusData,
    PaginationInfo,
    VideoResponse,
    VideoDetailResponse,
    VideoListResponse,
    VideoStatusResponse,
    UploadResponse,
    DownloadResponse
)


class TestScriptModels:
    """Test script-related models"""

    def test_script_create_valid(self):
        """Test valid ScriptCreate model"""
        data = {
            "topic": "Test Topic",
            "video_type": "shorts",
            "keywords": {"tone": "casual"},
            "input_type": "TOPIC",
            "add_brand": True,
            "music_media_id": "music123",
            "link": "https://example.com",
            "video_link": "https://video.example.com"
        }
        script = ScriptCreate(**data)
        assert script.topic == "Test Topic"
        assert script.video_type == "shorts"
        assert script.keywords == {"tone": "casual"}
        assert script.input_type == "TOPIC"
        assert script.add_brand is True
        assert script.music_media_id == "music123"

    def test_script_create_minimal(self):
        """Test ScriptCreate with minimal required fields"""
        data = {
            "topic": "Test Topic",
            "video_type": "shorts",
            "input_type": "TOPIC"
        }
        script = ScriptCreate(**data)
        assert script.topic == "Test Topic"
        assert script.keywords == {}
        assert script.add_brand is False
        assert script.music_media_id is None

    def test_script_create_missing_required(self):
        """Test ScriptCreate with missing required fields"""
        with pytest.raises(ValidationError):
            ScriptCreate(topic="Test")

    def test_script_update_partial(self):
        """Test ScriptUpdate with partial data"""
        data = {"title": "Updated Title", "content": "Updated content"}
        script_update = ScriptUpdate(**data)
        assert script_update.title == "Updated Title"
        assert script_update.content == "Updated content"
        assert script_update.topic is None

    def test_generate_script_request_valid(self):
        """Test valid GenerateScriptRequest"""
        data = {
            "topic": "AI Technology",
            "video_type": "youtube",
            "keywords": {"audience": "developers"},
            "input_type": "TOPIC"
        }
        request = GenerateScriptRequest(**data)
        assert request.topic == "AI Technology"
        assert request.video_type == "youtube"
        assert request.input_type == "TOPIC"

    def test_regenerate_script_request_valid(self):
        """Test valid RegenerateScriptRequest"""
        data = {
            "topic": "Updated Topic",
            "video_type": "shorts",
            "link": "https://example.com",
            "keywords": {"tone": "professional"}
        }
        request = RegenerateScriptRequest(**data)
        assert request.topic == "Updated Topic"
        assert request.link == "https://example.com"

    def test_validate_link_request_valid(self):
        """Test valid ValidateLinkRequest"""
        data = {
            "link": "https://youtube.com/watch?v=123",
            "link_type": "youtube"
        }
        request = ValidateLinkRequest(**data)
        assert request.link == "https://youtube.com/watch?v=123"
        assert request.link_type == "youtube"

    def test_script_model_with_alias(self):
        """Test Script model with _id alias"""
        data = {
            "_id": "script123",
            "user_id": "user123",
            "title": "Test Script",
            "content": "Script content",
            "topic": "Test Topic",
            "video_type": "shorts",
            "input_type": "TOPIC",
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        script = Script(**data)
        assert script.id == "script123"
        assert script.user_id == "user123"

    def test_script_response_valid(self):
        """Test ScriptResponse model"""
        script_data = {
            "_id": "script123",
            "user_id": "user123",
            "title": "Test Script",
            "content": "Script content",
            "topic": "Test Topic",
            "video_type": "shorts",
            "input_type": "TOPIC",
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        script = Script(**script_data)
        
        response_data = {
            "message": "Success",
            "data": script,
            "code": 200
        }
        response = ScriptResponse(**response_data)
        assert response.message == "Success"
        assert response.code == 200
        assert response.data.id == "script123"

    def test_script_list_response_valid(self):
        """Test ScriptListResponse model"""
        script_data = {
            "_id": "script123",
            "user_id": "user123",
            "title": "Test Script",
            "content": "Script content",
            "topic": "Test Topic",
            "video_type": "shorts",
            "input_type": "TOPIC",
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        script = Script(**script_data)
        
        list_data = {
            "scripts": [script],
            "page": 1,
            "limit": 10,
            "total_count": 1,
            "total_pages": 1
        }
        script_list_data = ScriptListData(**list_data)
        
        response_data = {
            "message": "Success",
            "data": script_list_data,
            "code": 200
        }
        response = ScriptListResponse(**response_data)
        assert response.message == "Success"
        assert len(response.data.scripts) == 1


class TestVideoModels:
    """Test video-related models"""

    def test_video_status_enum(self):
        """Test VideoStatus enum values"""
        assert VideoStatus.PENDING == "PENDING"
        assert VideoStatus.PROCESSING == "PROCESSING"
        assert VideoStatus.COMPLETED == "COMPLETED"
        assert VideoStatus.FAILED == "FAILED"
        assert VideoStatus.TIMED_OUT == "TIMED_OUT"

    def test_video_view_type_enum(self):
        """Test VideoViewType enum values"""
        assert VideoViewType.LANDSCAPE == "LANDSCAPE"
        assert VideoViewType.PORTRAIT == "PORTRAIT"
        assert VideoViewType.SQUARE == "SQUARE"

    def test_caption_model_valid(self):
        """Test Caption model"""
        data = {
            "font_path": "/fonts/arial.ttf",
            "color_code": "#FFFFFF"
        }
        caption = Caption(**data)
        assert caption.font_path == "/fonts/arial.ttf"
        assert caption.color_code == "#FFFFFF"

    def test_keywords_model_valid(self):
        """Test Keywords model"""
        data = {
            "time": "morning",
            "objective": "educate",
            "audience": "students",
            "gender": "mixed",
            "tone": "friendly",
            "speakers": "single"
        }
        keywords = Keywords(**data)
        assert keywords.time == "morning"
        assert keywords.objective == "educate"
        assert keywords.audience == "students"

    def test_keywords_model_optional_fields(self):
        """Test Keywords model with optional fields"""
        keywords = Keywords()
        assert keywords.time is None
        assert keywords.objective is None
        assert keywords.audience is None

    def test_video_metadata_valid(self):
        """Test VideoMetadata model"""
        data = {
            "title": "Test Video",
            "description": "Test Description",
            "keywords": ["test", "video"],
            "caption": "Test Caption",
            "tags": ["tag1", "tag2"],
            "category_id": "22",
            "privacy_status": "public"
        }
        metadata = VideoMetadata(**data)
        assert metadata.title == "Test Video"
        assert metadata.keywords == ["test", "video"]
        assert metadata.privacy_status == "public"

    def test_generate_video_request_valid(self):
        """Test GenerateVideoRequest model"""
        caption_data = {
            "font_path": "/fonts/arial.ttf",
            "color_code": "#FFFFFF"
        }
        caption = Caption(**caption_data)
        
        data = {
            "script_id": "script123",
            "avatar_id": "avatar123",
            "voice_id": "voice123",
            "template_id": "template123",
            "caption": caption,
            "view_type": VideoViewType.PORTRAIT
        }
        request = GenerateVideoRequest(**data)
        assert request.script_id == "script123"
        assert request.view_type == VideoViewType.PORTRAIT
        assert request.caption.font_path == "/fonts/arial.ttf"

    def test_generate_workflow_video_request_valid(self):
        """Test GenerateWorkflowVideoRequest model"""
        keywords_data = {
            "tone": "casual",
            "audience": "general"
        }
        keywords = Keywords(**keywords_data)
        
        data = {
            "topic": "AI Technology",
            "video_type": VideoType.SHORTS,
            "script_type": ScriptType.TOPIC,
            "keywords": keywords,
            "view_type": VideoViewType.PORTRAIT
        }
        request = GenerateWorkflowVideoRequest(**data)
        assert request.topic == "AI Technology"
        assert request.video_type == VideoType.SHORTS
        assert request.script_type == ScriptType.TOPIC

    def test_generate_workflow_video_request_link_validation(self):
        """Test link validation in GenerateWorkflowVideoRequest"""
        keywords = Keywords()
        
        # Should raise error for VIDEO type without link
        with pytest.raises(ValidationError) as exc_info:
            GenerateWorkflowVideoRequest(
                topic="Test",
                video_type=VideoType.SHORTS,
                script_type=ScriptType.VIDEO,
                keywords=keywords
            )
        assert "Link is required" in str(exc_info.value)

    def test_video_quality_request_valid(self):
        """Test VideoQualityRequest model"""
        data = {"quality": "1080p"}
        request = VideoQualityRequest(**data)
        assert request.quality == "1080p"

    def test_video_quality_request_invalid(self):
        """Test VideoQualityRequest with invalid quality"""
        with pytest.raises(ValidationError):
            VideoQualityRequest(quality="4K")

    def test_video_response_model_valid(self):
        """Test VideoResponseModel"""
        data = {
            "_id": "video123",
            "user_id": "user123",
            "script_id": "script123",
            "status": VideoStatus.PENDING,
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        video = VideoResponseModel(**data)
        assert video.id == "video123"
        assert video.status == VideoStatus.PENDING

    def test_pagination_info_valid(self):
        """Test PaginationInfo model"""
        data = {
            "page": 1,
            "per_page": 10,
            "total_count": 100,
            "total_pages": 10
        }
        pagination = PaginationInfo(**data)
        assert pagination.page == 1
        assert pagination.total_pages == 10

    def test_video_list_response_valid(self):
        """Test VideoListResponse model"""
        video_data = {
            "_id": "video123",
            "user_id": "user123",
            "script_id": "script123",
            "status": VideoStatus.COMPLETED,
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        video = VideoResponseModel(**video_data)
        
        pagination_data = {
            "page": 1,
            "per_page": 10,
            "total_count": 1,
            "total_pages": 1
        }
        pagination = PaginationInfo(**pagination_data)
        
        response_data = {
            "message": "Success",
            "data": [video],
            "pagination": pagination,
            "code": 200
        }
        response = VideoListResponse(**response_data)
        assert response.message == "Success"
        assert len(response.data) == 1
        assert response.pagination.total_count == 1

    def test_upload_response_valid(self):
        """Test UploadResponse model"""
        data = {
            "message": "Upload successful",
            "video_id": "video123",
            "code": 200
        }
        response = UploadResponse(**data)
        assert response.message == "Upload successful"
        assert response.video_id == "video123"

    def test_download_response_valid(self):
        """Test DownloadResponse model"""
        data = {
            "message": "Download ready",
            "download_url": "https://example.com/download/video123",
            "code": 200
        }
        response = DownloadResponse(**data)
        assert response.message == "Download ready"
        assert response.download_url == "https://example.com/download/video123"


class TestModelEdgeCases:
    """Test edge cases and error conditions"""

    def test_script_with_empty_keywords(self):
        """Test script creation with empty keywords"""
        data = {
            "topic": "Test Topic",
            "video_type": "shorts",
            "keywords": {},
            "input_type": "TOPIC"
        }
        script = ScriptCreate(**data)
        assert script.keywords == {}

    def test_video_with_none_optional_fields(self):
        """Test video creation with None optional fields"""
        data = {
            "script_id": "script123",
            "view_type": VideoViewType.PORTRAIT
        }
        request = GenerateVideoRequest(**data)
        assert request.avatar_id is None
        assert request.voice_id is None
        assert request.caption is None

    def test_invalid_enum_values(self):
        """Test invalid enum values"""
        with pytest.raises(ValidationError):
            VideoResponseModel(
                _id="video123",
                user_id="user123",
                script_id="script123",
                status="INVALID_STATUS",
                created_at=datetime.now(),
                updated_at=datetime.now()
            )

    def test_datetime_serialization(self):
        """Test datetime serialization in models"""
        now = datetime.now()
        data = {
            "_id": "script123",
            "user_id": "user123",
            "title": "Test Script",
            "content": "Script content",
            "topic": "Test Topic",
            "video_type": "shorts",
            "input_type": "TOPIC",
            "created_at": now,
            "updated_at": now
        }
        script = Script(**data)
        
        # Test JSON serialization
        json_data = script.model_dump()
        assert isinstance(json_data["created_at"], datetime)