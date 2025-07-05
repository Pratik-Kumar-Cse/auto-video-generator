"""
Rate limiting middleware for FastAPI application
"""

import time
import logging
from typing import Callable
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings
from app.core.redis_client import redis_service

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware using Redis"""
    
    def __init__(
        self,
        app,
        requests_per_minute: int = None,
        burst_limit: int = None
    ):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute or settings.RATE_LIMIT_PER_MINUTE
        self.burst_limit = burst_limit or settings.RATE_LIMIT_BURST
        self.window_size = 60  # 1 minute window
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Apply rate limiting based on client IP"""
        
        # Skip rate limiting for health checks and docs
        if request.url.path in ["/health", "/docs", "/redoc", "/openapi.json"]:
            return await call_next(request)
        
        # Get client IP
        client_ip = self._get_client_ip(request)
        
        # Check rate limit
        is_allowed, remaining, reset_time = await self._check_rate_limit(client_ip)
        
        if not is_allowed:
            return JSONResponse(
                status_code=429,
                content={
                    "message": "Rate limit exceeded",
                    "code": 429,
                    "retry_after": reset_time
                },
                headers={
                    "X-RateLimit-Limit": str(self.requests_per_minute),
                    "X-RateLimit-Remaining": str(remaining),
                    "X-RateLimit-Reset": str(reset_time),
                    "Retry-After": str(reset_time)
                }
            )
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(reset_time)
        
        return response
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address"""
        # Check for forwarded headers first
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Fallback to client host
        return request.client.host if request.client else "unknown"
    
    async def _check_rate_limit(self, client_ip: str) -> tuple[bool, int, int]:
        """Check if client is within rate limits"""
        current_time = int(time.time())
        window_start = current_time - self.window_size
        
        # Redis keys
        requests_key = f"rate_limit:requests:{client_ip}"
        burst_key = f"rate_limit:burst:{client_ip}"
        
        try:
            # Get current request count in the window
            request_count = await self._get_request_count(
                requests_key, 
                window_start, 
                current_time
            )
            
            # Check burst limit
            burst_count = await redis_service.get(burst_key) or 0
            if isinstance(burst_count, str):
                burst_count = int(burst_count)
            
            # Calculate remaining requests
            remaining_requests = max(0, self.requests_per_minute - request_count)
            remaining_burst = max(0, self.burst_limit - burst_count)
            
            # Check if request is allowed
            if request_count >= self.requests_per_minute or burst_count >= self.burst_limit:
                reset_time = window_start + self.window_size
                return False, min(remaining_requests, remaining_burst), reset_time
            
            # Record the request
            await self._record_request(requests_key, current_time)
            await self._record_burst(burst_key)
            
            reset_time = window_start + self.window_size
            return True, min(remaining_requests - 1, remaining_burst - 1), reset_time
            
        except Exception as e:
            logger.error(f"Error checking rate limit for {client_ip}: {e}")
            # Allow request if Redis is down
            return True, self.requests_per_minute, current_time + self.window_size
    
    async def _get_request_count(
        self, 
        key: str, 
        window_start: int, 
        current_time: int
    ) -> int:
        """Get request count in the current window"""
        try:
            # Use Redis sorted set to track requests with timestamps
            client = await redis_service.get_client()
            
            # Remove old entries
            await client.zremrangebyscore(key, 0, window_start)
            
            # Count current entries
            count = await client.zcard(key)
            
            return count
            
        except Exception as e:
            logger.error(f"Error getting request count: {e}")
            return 0
    
    async def _record_request(self, key: str, timestamp: int) -> None:
        """Record a request with timestamp"""
        try:
            client = await redis_service.get_client()
            
            # Add request with timestamp as score and value
            await client.zadd(key, {str(timestamp): timestamp})
            
            # Set expiration for cleanup
            await client.expire(key, self.window_size * 2)
            
        except Exception as e:
            logger.error(f"Error recording request: {e}")
    
    async def _record_burst(self, key: str) -> None:
        """Record burst request"""
        try:
            # Increment burst counter
            current_count = await redis_service.get(key) or 0
            if isinstance(current_count, str):
                current_count = int(current_count)
            
            await redis_service.set(key, current_count + 1, expire=10)  # 10 second burst window
            
        except Exception as e:
            logger.error(f"Error recording burst: {e}")


class UserRateLimitMiddleware(BaseHTTPMiddleware):
    """User-specific rate limiting middleware"""
    
    def __init__(
        self,
        app,
        authenticated_limit: int = 1000,  # Higher limit for authenticated users
        anonymous_limit: int = 100        # Lower limit for anonymous users
    ):
        super().__init__(app)
        self.authenticated_limit = authenticated_limit
        self.anonymous_limit = anonymous_limit
        self.window_size = 3600  # 1 hour window
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Apply user-specific rate limiting"""
        
        # Skip for health checks and docs
        if request.url.path in ["/health", "/docs", "/redoc", "/openapi.json"]:
            return await call_next(request)
        
        # Get user ID from request (if authenticated)
        user_id = await self._get_user_id(request)
        
        # Determine rate limit based on authentication
        if user_id:
            limit = self.authenticated_limit
            key = f"user_rate_limit:{user_id}"
        else:
            limit = self.anonymous_limit
            client_ip = self._get_client_ip(request)
            key = f"anon_rate_limit:{client_ip}"
        
        # Check rate limit
        is_allowed, remaining, reset_time = await self._check_user_rate_limit(
            key, 
            limit
        )
        
        if not is_allowed:
            return JSONResponse(
                status_code=429,
                content={
                    "message": "User rate limit exceeded",
                    "code": 429,
                    "retry_after": reset_time
                },
                headers={
                    "X-User-RateLimit-Limit": str(limit),
                    "X-User-RateLimit-Remaining": str(remaining),
                    "X-User-RateLimit-Reset": str(reset_time),
                    "Retry-After": str(reset_time)
                }
            )
        
        # Process request
        response = await call_next(request)
        
        # Add user rate limit headers
        response.headers["X-User-RateLimit-Limit"] = str(limit)
        response.headers["X-User-RateLimit-Remaining"] = str(remaining)
        response.headers["X-User-RateLimit-Reset"] = str(reset_time)
        
        return response
    
    async def _get_user_id(self, request: Request) -> str:
        """Extract user ID from request (implement based on auth system)"""
        # This would be implemented based on your authentication system
        # For now, return None (anonymous user)
        return None
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address"""
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        return request.client.host if request.client else "unknown"
    
    async def _check_user_rate_limit(
        self, 
        key: str, 
        limit: int
    ) -> tuple[bool, int, int]:
        """Check user-specific rate limit"""
        current_time = int(time.time())
        window_start = current_time - self.window_size
        
        try:
            # Get current count
            count = await redis_service.get(key) or 0
            if isinstance(count, str):
                count = int(count)
            
            remaining = max(0, limit - count)
            reset_time = window_start + self.window_size
            
            if count >= limit:
                return False, remaining, reset_time
            
            # Increment counter
            await redis_service.set(key, count + 1, expire=self.window_size)
            
            return True, remaining - 1, reset_time
            
        except Exception as e:
            logger.error(f"Error checking user rate limit: {e}")
            return True, limit, current_time + self.window_size