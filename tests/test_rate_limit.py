"""
Unit tests for rate limiting middleware
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import Request, Response
from fastapi.responses import JSONResponse
import time

from app.middleware.rate_limit import (
    RateLimitMiddleware,
    IPRateLimiter,
    UserRateLimiter,
    RateLimitExceeded
)
from app.core.exceptions import TooManyRequestsException


class TestIPRateLimiter:
    """Test IP-based rate limiter"""

    @pytest.fixture
    def mock_redis(self):
        """Mock Redis service"""
        mock_redis = MagicMock()
        mock_redis.get = AsyncMock()
        mock_redis.incr = AsyncMock()
        mock_redis.expire = AsyncMock()
        mock_redis.ttl = AsyncMock()
        return mock_redis

    @pytest.fixture
    def ip_limiter(self, mock_redis):
        """Create IP rate limiter with mocked Redis"""
        return IPRateLimiter(
            redis_service=mock_redis,
            requests_per_minute=60,
            requests_per_hour=1000
        )

    @pytest.mark.asyncio
    async def test_ip_limiter_first_request(self, ip_limiter, mock_redis):
        """Test first request from IP"""
        mock_redis.get.return_value = None
        mock_redis.incr.return_value = 1
        
        result = await ip_limiter.is_allowed("192.168.1.1")
        
        assert result is True
        mock_redis.incr.assert_called()
        mock_redis.expire.assert_called()

    @pytest.mark.asyncio
    async def test_ip_limiter_within_limit(self, ip_limiter, mock_redis):
        """Test request within rate limit"""
        mock_redis.get.side_effect = [b"30", b"500"]  # minute, hour counts
        mock_redis.incr.return_value = 31
        
        result = await ip_limiter.is_allowed("192.168.1.1")
        
        assert result is True

    @pytest.mark.asyncio
    async def test_ip_limiter_minute_limit_exceeded(self, ip_limiter, mock_redis):
        """Test minute rate limit exceeded"""
        mock_redis.get.side_effect = [b"60", b"500"]  # at minute limit
        
        result = await ip_limiter.is_allowed("192.168.1.1")
        
        assert result is False

    @pytest.mark.asyncio
    async def test_ip_limiter_hour_limit_exceeded(self, ip_limiter, mock_redis):
        """Test hour rate limit exceeded"""
        mock_redis.get.side_effect = [b"30", b"1000"]  # at hour limit
        
        result = await ip_limiter.is_allowed("192.168.1.1")
        
        assert result is False

    @pytest.mark.asyncio
    async def test_ip_limiter_get_info(self, ip_limiter, mock_redis):
        """Test getting rate limit info"""
        mock_redis.get.side_effect = [b"30", b"500"]
        mock_redis.ttl.side_effect = [45, 2700]  # TTL for minute and hour
        
        info = await ip_limiter.get_rate_limit_info("192.168.1.1")
        
        assert info["minute_requests"] == 30
        assert info["hour_requests"] == 500
        assert info["minute_remaining"] == 30
        assert info["hour_remaining"] == 500
        assert info["minute_reset"] == 45
        assert info["hour_reset"] == 2700

    @pytest.mark.asyncio
    async def test_ip_limiter_redis_error(self, ip_limiter, mock_redis):
        """Test Redis error handling"""
        mock_redis.get.side_effect = Exception("Redis connection failed")
        
        # Should allow request on Redis error
        result = await ip_limiter.is_allowed("192.168.1.1")
        
        assert result is True


class TestUserRateLimiter:
    """Test user-based rate limiter"""

    @pytest.fixture
    def mock_redis(self):
        """Mock Redis service"""
        mock_redis = MagicMock()
        mock_redis.get = AsyncMock()
        mock_redis.incr = AsyncMock()
        mock_redis.expire = AsyncMock()
        mock_redis.ttl = AsyncMock()
        return mock_redis

    @pytest.fixture
    def user_limiter(self, mock_redis):
        """Create user rate limiter with mocked Redis"""
        return UserRateLimiter(
            redis_service=mock_redis,
            requests_per_minute=100,
            requests_per_hour=5000
        )

    @pytest.mark.asyncio
    async def test_user_limiter_first_request(self, user_limiter, mock_redis):
        """Test first request from user"""
        mock_redis.get.return_value = None
        mock_redis.incr.return_value = 1
        
        result = await user_limiter.is_allowed("user123")
        
        assert result is True
        mock_redis.incr.assert_called()
        mock_redis.expire.assert_called()

    @pytest.mark.asyncio
    async def test_user_limiter_within_limit(self, user_limiter, mock_redis):
        """Test request within rate limit"""
        mock_redis.get.side_effect = [b"50", b"2000"]  # minute, hour counts
        mock_redis.incr.return_value = 51
        
        result = await user_limiter.is_allowed("user123")
        
        assert result is True

    @pytest.mark.asyncio
    async def test_user_limiter_exceeded(self, user_limiter, mock_redis):
        """Test user rate limit exceeded"""
        mock_redis.get.side_effect = [b"100", b"2000"]  # at minute limit
        
        result = await user_limiter.is_allowed("user123")
        
        assert result is False

    @pytest.mark.asyncio
    async def test_user_limiter_get_info(self, user_limiter, mock_redis):
        """Test getting user rate limit info"""
        mock_redis.get.side_effect = [b"75", b"3000"]
        mock_redis.ttl.side_effect = [30, 1800]
        
        info = await user_limiter.get_rate_limit_info("user123")
        
        assert info["minute_requests"] == 75
        assert info["hour_requests"] == 3000
        assert info["minute_remaining"] == 25
        assert info["hour_remaining"] == 2000


class TestRateLimitMiddleware:
    """Test rate limit middleware"""

    @pytest.fixture
    def mock_redis(self):
        """Mock Redis service"""
        mock_redis = MagicMock()
        mock_redis.get = AsyncMock()
        mock_redis.incr = AsyncMock()
        mock_redis.expire = AsyncMock()
        mock_redis.ttl = AsyncMock()
        return mock_redis

    @pytest.fixture
    def middleware(self, mock_redis):
        """Create rate limit middleware with mocked Redis"""
        return RateLimitMiddleware(
            app=MagicMock(),
            redis_service=mock_redis,
            ip_requests_per_minute=60,
            ip_requests_per_hour=1000,
            user_requests_per_minute=100,
            user_requests_per_hour=5000
        )

    @pytest.fixture
    def mock_request(self):
        """Create mock request"""
        request = MagicMock(spec=Request)
        request.client.host = "192.168.1.1"
        request.url.path = "/api/v1/scripts/generate"
        request.method = "POST"
        request.headers = {}
        return request

    @pytest.mark.asyncio
    async def test_middleware_allowed_request(self, middleware, mock_request, mock_redis):
        """Test allowed request through middleware"""
        # Mock rate limiters to allow request
        mock_redis.get.side_effect = [b"30", b"500", b"50", b"2000"]
        mock_redis.incr.return_value = 31
        
        # Mock call_next
        async def mock_call_next(request):
            return Response("OK", status_code=200)
        
        response = await middleware.dispatch(mock_request, mock_call_next)
        
        assert response.status_code == 200
        assert "X-RateLimit-Limit-IP-Minute" in response.headers
        assert "X-RateLimit-Remaining-IP-Minute" in response.headers

    @pytest.mark.asyncio
    async def test_middleware_ip_rate_limited(self, middleware, mock_request, mock_redis):
        """Test IP rate limited request"""
        # Mock IP limiter to exceed limit
        mock_redis.get.side_effect = [b"60", b"500"]  # IP at minute limit
        
        async def mock_call_next(request):
            return Response("OK", status_code=200)
        
        response = await middleware.dispatch(mock_request, mock_call_next)
        
        assert response.status_code == 429
        assert "Rate limit exceeded" in response.body.decode()

    @pytest.mark.asyncio
    async def test_middleware_user_rate_limited(self, middleware, mock_request, mock_redis):
        """Test user rate limited request"""
        # Mock IP limiter to allow, user limiter to exceed
        mock_redis.get.side_effect = [b"30", b"500", b"100", b"2000"]
        
        # Add user ID to request
        mock_request.headers = {"X-User-ID": "user123"}
        
        async def mock_call_next(request):
            return Response("OK", status_code=200)
        
        response = await middleware.dispatch(mock_request, mock_call_next)
        
        assert response.status_code == 429

    @pytest.mark.asyncio
    async def test_middleware_excluded_path(self, middleware, mock_request, mock_redis):
        """Test excluded path bypasses rate limiting"""
        mock_request.url.path = "/health"
        
        async def mock_call_next(request):
            return Response("OK", status_code=200)
        
        response = await middleware.dispatch(mock_request, mock_call_next)
        
        assert response.status_code == 200
        # Redis should not be called for excluded paths
        mock_redis.get.assert_not_called()

    @pytest.mark.asyncio
    async def test_middleware_get_client_ip_forwarded(self, middleware, mock_request):
        """Test getting client IP from X-Forwarded-For header"""
        mock_request.headers = {"X-Forwarded-For": "203.0.113.1, 192.168.1.1"}
        
        ip = middleware._get_client_ip(mock_request)
        
        assert ip == "203.0.113.1"

    @pytest.mark.asyncio
    async def test_middleware_get_client_ip_real_ip(self, middleware, mock_request):
        """Test getting client IP from X-Real-IP header"""
        mock_request.headers = {"X-Real-IP": "203.0.113.1"}
        
        ip = middleware._get_client_ip(mock_request)
        
        assert ip == "203.0.113.1"

    @pytest.mark.asyncio
    async def test_middleware_get_client_ip_fallback(self, middleware, mock_request):
        """Test fallback to request.client.host"""
        ip = middleware._get_client_ip(mock_request)
        
        assert ip == "192.168.1.1"

    @pytest.mark.asyncio
    async def test_middleware_extract_user_id_header(self, middleware, mock_request):
        """Test extracting user ID from header"""
        mock_request.headers = {"X-User-ID": "user123"}
        
        user_id = middleware._extract_user_id(mock_request)
        
        assert user_id == "user123"

    @pytest.mark.asyncio
    async def test_middleware_extract_user_id_auth_header(self, middleware, mock_request):
        """Test extracting user ID from Authorization header"""
        # Mock JWT token decoding
        with patch('jwt.decode') as mock_decode:
            mock_decode.return_value = {"sub": "user456"}
            mock_request.headers = {"Authorization": "Bearer valid.jwt.token"}
            
            user_id = middleware._extract_user_id(mock_request)
            
            assert user_id == "user456"

    @pytest.mark.asyncio
    async def test_middleware_extract_user_id_invalid_jwt(self, middleware, mock_request):
        """Test handling invalid JWT token"""
        with patch('jwt.decode') as mock_decode:
            mock_decode.side_effect = Exception("Invalid token")
            mock_request.headers = {"Authorization": "Bearer invalid.jwt.token"}
            
            user_id = middleware._extract_user_id(mock_request)
            
            assert user_id is None

    @pytest.mark.asyncio
    async def test_middleware_add_rate_limit_headers(self, middleware, mock_redis):
        """Test adding rate limit headers to response"""
        response = Response("OK", status_code=200)
        
        # Mock rate limit info
        ip_info = {
            "minute_requests": 30,
            "minute_remaining": 30,
            "minute_reset": 45,
            "hour_requests": 500,
            "hour_remaining": 500,
            "hour_reset": 2700
        }
        
        user_info = {
            "minute_requests": 50,
            "minute_remaining": 50,
            "minute_reset": 30,
            "hour_requests": 2000,
            "hour_remaining": 3000,
            "hour_reset": 1800
        }
        
        middleware._add_rate_limit_headers(response, ip_info, user_info)
        
        assert response.headers["X-RateLimit-Limit-IP-Minute"] == "60"
        assert response.headers["X-RateLimit-Remaining-IP-Minute"] == "30"
        assert response.headers["X-RateLimit-Reset-IP-Minute"] == "45"
        assert response.headers["X-RateLimit-Limit-User-Minute"] == "100"
        assert response.headers["X-RateLimit-Remaining-User-Minute"] == "50"

    @pytest.mark.asyncio
    async def test_middleware_redis_error_handling(self, middleware, mock_request, mock_redis):
        """Test middleware behavior when Redis fails"""
        mock_redis.get.side_effect = Exception("Redis connection failed")
        
        async def mock_call_next(request):
            return Response("OK", status_code=200)
        
        # Should allow request when Redis fails
        response = await middleware.dispatch(mock_request, mock_call_next)
        
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_rate_limit_exceeded_exception(self):
        """Test RateLimitExceeded exception"""
        exception = RateLimitExceeded(
            limit_type="IP",
            limit=60,
            window="minute",
            retry_after=45
        )
        
        assert exception.limit_type == "IP"
        assert exception.limit == 60
        assert exception.window == "minute"
        assert exception.retry_after == 45

    @pytest.mark.asyncio
    async def test_middleware_performance_monitoring(self, middleware, mock_request, mock_redis):
        """Test performance monitoring in middleware"""
        mock_redis.get.side_effect = [b"30", b"500", b"50", b"2000"]
        mock_redis.incr.return_value = 31
        
        start_time = time.time()
        
        async def mock_call_next(request):
            # Simulate some processing time
            await asyncio.sleep(0.01)
            return Response("OK", status_code=200)
        
        response = await middleware.dispatch(mock_request, mock_call_next)
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        assert response.status_code == 200
        assert processing_time > 0.01  # Should include processing time

    @pytest.mark.asyncio
    async def test_middleware_concurrent_requests(self, middleware, mock_redis):
        """Test middleware handling concurrent requests"""
        import asyncio
        
        mock_redis.get.side_effect = lambda key: b"30" if "minute" in key else b"500"
        mock_redis.incr.return_value = 31
        
        async def mock_call_next(request):
            return Response("OK", status_code=200)
        
        # Create multiple concurrent requests
        requests = []
        for i in range(5):
            request = MagicMock(spec=Request)
            request.client.host = f"192.168.1.{i}"
            request.url.path = "/api/v1/test"
            request.method = "GET"
            request.headers = {}
            requests.append(request)
        
        # Process requests concurrently
        tasks = [
            middleware.dispatch(req, mock_call_next) 
            for req in requests
        ]
        responses = await asyncio.gather(*tasks)
        
        # All requests should succeed
        assert all(resp.status_code == 200 for resp in responses)