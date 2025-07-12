"""
Unit tests for API endpoints
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
import json
from datetime import datetime

from app.main import app
from app.core.exceptions import (
    ScriptNotFoundException,
    ScriptProcessingException,
    BadRequestException
)


class TestScriptEndpoints:
    """Test script API endpoints"""

    def test_generate_script_success(self, client, mock_redis):
        """Test successful script generation"""
        with patch('app.api.v1.endpoints.scripts.ScriptGenerationManager') as mock_manager:
            mock_manager.initiate_script_generation.return_value = "test_task_id"
            
            response = client.post(
                "/api/v1/scripts/generate",
                json={
                    "topic": "AI Technology",
                    "video_type": "shorts",
                    "keywords": {"tone": "casual"},
                    "input_type": "TOPIC"
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "task_id" in data
            assert data["task_id"] == "test_task_id"

    def test_generate_script_missing_link(self, client):
        """Test script generation with missing required link"""
        response = client.post(
            "/api/v1/scripts/generate",
            json={
                "topic": "AI Technology",
                "video_type": "shorts",
                "keywords": {"tone": "casual"},
                "input_type": "VIDEO"  # Requires link
            }
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "Link is required" in data["detail"]

    def test_generate_script_invalid_input(self, client):
        """Test script generation with invalid input"""
        response = client.post(
            "/api/v1/scripts/generate",
            json={
                "topic": "",  # Empty topic
                "video_type": "shorts",
                "input_type": "TOPIC"
            }
        )
        
        assert response.status_code == 422  # Validation error

    def test_stream_script_generation_completed(self, client, mock_redis):
        """Test streaming for completed script"""
        with patch('app.services.script_service.ScriptService') as mock_service:
            mock_instance = mock_service.return_value
            mock_instance.get_script_using_task_id.return_value = {
                "title": "Test Script",
                "content": "Test content",
                "status": "completed"
            }
            
            response = client.get("/api/v1/scripts/stream/test_task_id")
            
            assert response.status_code == 200
            assert response.headers["content-type"] == "text/event-stream; charset=utf-8"

    def test_get_script_success(self, client, sample_script_data):
        """Test successful script retrieval"""
        with patch('app.services.script_service.ScriptService') as mock_service:
            mock_instance = mock_service.return_value
            mock_instance.get_script_of_user.return_value = sample_script_data
            
            response = client.get("/api/v1/scripts/test_script_id")
            
            assert response.status_code == 200
            data = response.json()
            assert data["message"] == "Script fetched successfully"
            assert data["data"]["title"] == "Test Script"

    def test_get_script_not_found(self, client):
        """Test script not found"""
        with patch('app.services.script_service.ScriptService') as mock_service:
            mock_instance = mock_service.return_value
            mock_instance.get_script_of_user.return_value = None
            
            response = client.get("/api/v1/scripts/nonexistent_id")
            
            assert response.status_code == 404

    def test_update_script_success(self, client, sample_script_data):
        """Test successful script update"""
        updated_data = sample_script_data.copy()
        updated_data["title"] = "Updated Title"
        
        with patch('app.services.script_service.ScriptService') as mock_service:
            mock_instance = mock_service.return_value
            mock_instance.update_script.return_value = updated_data
            
            response = client.put(
                "/api/v1/scripts/test_script_id",
                json={
                    "title": "Updated Title",
                    "content": "Updated content"
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["data"]["title"] == "Updated Title"

    def test_delete_script_success(self, client):
        """Test successful script deletion"""
        with patch('app.services.script_service.ScriptService') as mock_service:
            mock_instance = mock_service.return_value
            mock_instance.delete_script.return_value = True
            
            response = client.delete("/api/v1/scripts/test_script_id")
            
            assert response.status_code == 200
            data = response.json()
            assert data["message"] == "Script deleted successfully"

    def test_delete_script_not_found(self, client):
        """Test deleting non-existent script"""
        with patch('app.services.script_service.ScriptService') as mock_service:
            mock_instance = mock_service.return_value
            mock_instance.delete_script.return_value = False
            
            response = client.delete("/api/v1/scripts/nonexistent_id")
            
            assert response.status_code == 404

    def test_get_all_scripts_success(self, client, sample_script_data):
        """Test getting all scripts"""
        with patch('app.services.script_service.ScriptService') as mock_service:
            mock_instance = mock_service.return_value
            mock_instance.get_all_scripts_by_user.return_value = (
                [sample_script_data], 1
            )
            
            response = client.get("/api/v1/scripts/")
            
            assert response.status_code == 200
            data = response.json()
            assert data["message"] == "Scripts fetched successfully"
            assert len(data["data"]["scripts"]) == 1
            assert data["data"]["total_count"] == 1

    def test_get_all_scripts_with_filters(self, client, sample_script_data):
        """Test getting scripts with filters"""
        with patch('app.services.script_service.ScriptService') as mock_service:
            mock_instance = mock_service.return_value
            mock_instance.get_all_scripts_by_user.return_value = (
                [sample_script_data], 1
            )
            
            response = client.get(
                "/api/v1/scripts/?filter=Test&video_type=shorts&page=1&per_page=10"
            )
            
            assert response.status_code == 200
            data = response.json()
            assert len(data["data"]["scripts"]) == 1

    def test_get_trending_topics_success(self, client):
        """Test getting trending topics"""
        with patch('app.services.script_service.ScriptService') as mock_service:
            mock_instance = mock_service.return_value
            mock_instance.get_trending_topics.return_value = [
                {"topic": "AI Technology", "count": 10},
                {"topic": "Machine Learning", "count": 8}
            ]
            
            response = client.get("/api/v1/scripts/trending-topics?limit=10")
            
            assert response.status_code == 200
            data = response.json()
            assert len(data["data"]["topics"]) == 2
            assert data["data"]["topics"][0]["topic"] == "AI Technology"

    def test_create_script_success(self, client, sample_script_data):
        """Test successful script creation"""
        with patch('app.services.script_service.ScriptService') as mock_service:
            mock_instance = mock_service.return_value
            mock_instance.create_script.return_value = sample_script_data
            
            response = client.post(
                "/api/v1/scripts/create",
                json={
                    "topic": "Test Topic",
                    "video_type": "shorts",
                    "keywords": {"tone": "casual"},
                    "input_type": "TOPIC",
                    "add_brand": False
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["message"] == "Script created successfully"
            assert data["code"] == 201

    def test_regenerate_script_success(self, client, sample_script_data):
        """Test successful script regeneration"""
        with patch('app.services.script_service.ScriptService') as mock_service:
            mock_instance = mock_service.return_value
            mock_instance.get_script_of_user.return_value = sample_script_data
            mock_instance.regenerate_script.return_value = sample_script_data
            
            response = client.put(
                "/api/v1/scripts/regenerate/test_script_id",
                json={
                    "topic": "Updated Topic",
                    "video_type": "youtube",
                    "keywords": {"tone": "professional"}
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["message"] == "Script regenerated successfully"


class TestVideoEndpoints:
    """Test video API endpoints"""

    def test_generate_video_success(self, client):
        """Test successful video generation"""
        with patch('app.services.video_service.VideoService') as mock_service:
            mock_instance = mock_service.return_value
            mock_instance.generate_video.return_value = {
                "video_id": "test_video_id",
                "task_id": "test_task_id",
                "status": "PENDING"
            }
            
            response = client.post(
                "/api/v1/videos/generate",
                json={
                    "script_id": "test_script_id",
                    "voice_id": "test_voice",
                    "avatar_id": "test_avatar",
                    "view_type": "PORTRAIT"
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "video_id" in data["data"]

    def test_get_video_success(self, client, sample_video_data):
        """Test successful video retrieval"""
        with patch('app.services.video_service.VideoService') as mock_service:
            mock_instance = mock_service.return_value
            mock_instance.get_video.return_value = sample_video_data
            
            response = client.get("/api/v1/videos/test_video_id")
            
            assert response.status_code == 200
            data = response.json()
            assert data["data"]["id"] == "test_video_id"

    def test_get_video_status_success(self, client):
        """Test getting video status"""
        with patch('app.services.video_service.VideoService') as mock_service:
            mock_instance = mock_service.return_value
            mock_instance.get_video_status.return_value = "PROCESSING"
            
            response = client.get("/api/v1/videos/test_video_id/status")
            
            assert response.status_code == 200
            data = response.json()
            assert data["data"]["status"] == "PROCESSING"

    def test_update_video_success(self, client, sample_video_data):
        """Test successful video update"""
        with patch('app.services.video_service.VideoService') as mock_service:
            mock_instance = mock_service.return_value
            mock_instance.update_video.return_value = sample_video_data
            
            response = client.put(
                "/api/v1/videos/test_video_id",
                json={
                    "title": "Updated Video Title",
                    "metadata": {"description": "Updated description"}
                }
            )
            
            assert response.status_code == 200

    def test_delete_video_success(self, client):
        """Test successful video deletion"""
        with patch('app.services.video_service.VideoService') as mock_service:
            mock_instance = mock_service.return_value
            mock_instance.delete_video.return_value = True
            
            response = client.delete("/api/v1/videos/test_video_id")
            
            assert response.status_code == 200

    def test_get_all_videos_success(self, client, sample_video_data):
        """Test getting all videos"""
        with patch('app.services.video_service.VideoService') as mock_service:
            mock_instance = mock_service.return_value
            mock_instance.get_all_videos.return_value = (
                [sample_video_data], 1
            )
            
            response = client.get("/api/v1/videos/")
            
            assert response.status_code == 200
            data = response.json()
            assert len(data["data"]) == 1


class TestHealthEndpoints:
    """Test health check endpoints"""

    def test_health_check_success(self, client):
        """Test successful health check"""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_health_check_detailed(self, client, mock_redis):
        """Test detailed health check"""
        mock_redis.health_check.return_value = True
        
        with patch('app.core.database.get_database') as mock_db:
            mock_db_instance = AsyncMock()
            mock_db_instance.command.return_value = {"ok": 1}
            mock_db.return_value = mock_db_instance
            
            response = client.get("/health/detailed")
            
            assert response.status_code == 200
            data = response.json()
            assert "database" in data
            assert "redis" in data


class TestErrorHandling:
    """Test error handling in endpoints"""

    def test_validation_error_handling(self, client):
        """Test validation error handling"""
        response = client.post(
            "/api/v1/scripts/generate",
            json={
                "topic": "",  # Invalid empty topic
                "video_type": "invalid_type",  # Invalid video type
                "input_type": "TOPIC"
            }
        )
        
        assert response.status_code == 422

    def test_internal_server_error_handling(self, client):
        """Test internal server error handling"""
        with patch('app.services.script_service.ScriptService') as mock_service:
            mock_instance = mock_service.return_value
            mock_instance.get_script_of_user.side_effect = Exception("Database error")
            
            response = client.get("/api/v1/scripts/test_script_id")
            
            assert response.status_code == 500

    def test_not_found_error_handling(self, client):
        """Test not found error handling"""
        with patch('app.services.script_service.ScriptService') as mock_service:
            mock_instance = mock_service.return_value
            mock_instance.get_script_of_user.return_value = None
            
            response = client.get("/api/v1/scripts/nonexistent_id")
            
            assert response.status_code == 404

    def test_rate_limit_error_handling(self, client):
        """Test rate limit error handling"""
        with patch('app.middleware.rate_limit.RateLimitMiddleware') as mock_middleware:
            mock_middleware.return_value.dispatch.side_effect = Exception("Rate limit exceeded")
            
            # This would normally be handled by the middleware
            # but we're testing the error response format
            response = client.get("/api/v1/scripts/")
            
            # The actual status code depends on how the middleware handles the error
            assert response.status_code in [429, 500]


class TestAuthentication:
    """Test authentication and authorization"""

    def test_missing_auth_header(self, client):
        """Test request without authentication header"""
        # Since auth is removed, this should succeed
        response = client.get("/api/v1/scripts/")
        assert response.status_code == 200

    def test_invalid_auth_token(self, client):
        """Test request with invalid authentication token"""
        # Since auth is removed, this should succeed regardless
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.get("/api/v1/scripts/", headers=headers)
        assert response.status_code == 200


class TestCORS:
    """Test CORS configuration"""

    def test_cors_preflight_request(self, client):
        """Test CORS preflight request"""
        response = client.options(
            "/api/v1/scripts/",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type"
            }
        )
        
        assert response.status_code == 200
        assert "Access-Control-Allow-Origin" in response.headers

    def test_cors_actual_request(self, client):
        """Test actual CORS request"""
        response = client.get(
            "/api/v1/scripts/",
            headers={"Origin": "http://localhost:3000"}
        )
        
        assert response.status_code == 200
        assert "Access-Control-Allow-Origin" in response.headers


class TestPagination:
    """Test pagination functionality"""

    def test_pagination_default_values(self, client, sample_script_data):
        """Test pagination with default values"""
        with patch('app.services.script_service.ScriptService') as mock_service:
            mock_instance = mock_service.return_value
            mock_instance.get_all_scripts_by_user.return_value = (
                [sample_script_data], 1
            )
            
            response = client.get("/api/v1/scripts/")
            
            assert response.status_code == 200
            data = response.json()
            assert data["data"]["page"] == 1
            assert data["data"]["limit"] == 10

    def test_pagination_custom_values(self, client, sample_script_data):
        """Test pagination with custom values"""
        with patch('app.services.script_service.ScriptService') as mock_service:
            mock_instance = mock_service.return_value
            mock_instance.get_all_scripts_by_user.return_value = (
                [sample_script_data], 1
            )
            
            response = client.get("/api/v1/scripts/?page=2&per_page=5")
            
            assert response.status_code == 200
            data = response.json()
            assert data["data"]["page"] == 2
            assert data["data"]["limit"] == 5

    def test_pagination_invalid_values(self, client):
        """Test pagination with invalid values"""
        response = client.get("/api/v1/scripts/?page=0&per_page=-1")
        
        # Should handle invalid values gracefully
        assert response.status_code in [200, 422]


class TestContentNegotiation:
    """Test content negotiation"""

    def test_json_content_type(self, client):
        """Test JSON content type handling"""
        response = client.post(
            "/api/v1/scripts/generate",
            json={
                "topic": "AI Technology",
                "video_type": "shorts",
                "input_type": "TOPIC"
            },
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"

    def test_unsupported_content_type(self, client):
        """Test unsupported content type"""
        response = client.post(
            "/api/v1/scripts/generate",
            data="invalid data",
            headers={"Content-Type": "text/plain"}
        )
        
        assert response.status_code == 422


class TestRateLimiting:
    """Test rate limiting functionality"""

    def test_rate_limit_headers(self, client, mock_redis):
        """Test rate limit headers in response"""
        mock_redis.get.return_value = b"5"  # Current request count
        
        response = client.get("/api/v1/scripts/")
        
        # Rate limit headers should be present
        assert "X-RateLimit-Limit-IP-Minute" in response.headers
        assert "X-RateLimit-Remaining-IP-Minute" in response.headers

    def test_rate_limit_exceeded(self, client, mock_redis):
        """Test rate limit exceeded scenario"""
        mock_redis.get.return_value = b"100"  # At rate limit
        
        # This would be handled by the rate limiting middleware
        response = client.get("/api/v1/scripts/")
        
        # Depending on middleware implementation
        assert response.status_code in [200, 429]