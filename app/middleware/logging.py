"""
Logging middleware for FastAPI application
"""

import time
import json
import logging
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for request/response logging"""
    
    def __init__(self, app):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Log request and response details"""
        
        start_time = time.time()
        
        # Log request
        await self._log_request(request)
        
        # Process request
        response = await call_next(request)
        
        # Calculate processing time
        process_time = time.time() - start_time
        
        # Log response
        await self._log_response(request, response, process_time)
        
        return response
    
    async def _log_request(self, request: Request) -> None:
        """Log incoming request details"""
        try:
            # Get client info
            client_ip = self._get_client_ip(request)
            user_agent = request.headers.get("user-agent", "")
            
            # Get request details
            method = request.method
            url = str(request.url)
            headers = dict(request.headers)
            
            # Remove sensitive headers
            sensitive_headers = ["authorization", "cookie", "x-api-key"]
            for header in sensitive_headers:
                if header in headers:
                    headers[header] = "[REDACTED]"
            
            # Log request
            log_data = {
                "type": "request",
                "method": method,
                "url": url,
                "client_ip": client_ip,
                "user_agent": user_agent,
                "headers": headers,
                "timestamp": time.time()
            }
            
            # Log request body for POST/PUT/PATCH (be careful with sensitive data)
            if method in ["POST", "PUT", "PATCH"]:
                content_type = request.headers.get("content-type", "")
                if "application/json" in content_type:
                    try:
                        body = await request.body()
                        if body:
                            # Parse JSON and redact sensitive fields
                            body_data = json.loads(body)
                            redacted_body = self._redact_sensitive_data(body_data)
                            log_data["body"] = redacted_body
                    except Exception as e:
                        log_data["body_error"] = str(e)
            
            logger.info(f"Request: {json.dumps(log_data)}")
            
        except Exception as e:
            logger.error(f"Error logging request: {e}")
    
    async def _log_response(
        self, 
        request: Request, 
        response: Response, 
        process_time: float
    ) -> None:
        """Log response details"""
        try:
            # Get response details
            status_code = response.status_code
            headers = dict(response.headers)
            
            # Log response
            log_data = {
                "type": "response",
                "method": request.method,
                "url": str(request.url),
                "status_code": status_code,
                "process_time": round(process_time, 4),
                "headers": headers,
                "timestamp": time.time()
            }
            
            # Determine log level based on status code
            if status_code >= 500:
                logger.error(f"Response: {json.dumps(log_data)}")
            elif status_code >= 400:
                logger.warning(f"Response: {json.dumps(log_data)}")
            else:
                logger.info(f"Response: {json.dumps(log_data)}")
                
        except Exception as e:
            logger.error(f"Error logging response: {e}")
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address"""
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        return request.client.host if request.client else "unknown"
    
    def _redact_sensitive_data(self, data: dict) -> dict:
        """Redact sensitive data from request body"""
        if not isinstance(data, dict):
            return data
        
        sensitive_fields = [
            "password",
            "token",
            "secret",
            "key",
            "api_key",
            "access_token",
            "refresh_token",
            "authorization",
            "credit_card",
            "ssn",
            "social_security",
            "phone",
            "email"  # Optional: you might want to keep email for debugging
        ]
        
        redacted_data = {}
        for key, value in data.items():
            key_lower = key.lower()
            
            # Check if field is sensitive
            is_sensitive = any(sensitive in key_lower for sensitive in sensitive_fields)
            
            if is_sensitive:
                redacted_data[key] = "[REDACTED]"
            elif isinstance(value, dict):
                redacted_data[key] = self._redact_sensitive_data(value)
            elif isinstance(value, list):
                redacted_data[key] = [
                    self._redact_sensitive_data(item) if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                redacted_data[key] = value
        
        return redacted_data


class PerformanceLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for performance monitoring and logging"""
    
    def __init__(self, app, slow_request_threshold: float = 1.0):
        super().__init__(app)
        self.slow_request_threshold = slow_request_threshold
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Monitor and log performance metrics"""
        
        start_time = time.time()
        
        # Process request
        response = await call_next(request)
        
        # Calculate metrics
        process_time = time.time() - start_time
        
        # Log performance metrics
        await self._log_performance(request, response, process_time)
        
        return response
    
    async def _log_performance(
        self, 
        request: Request, 
        response: Response, 
        process_time: float
    ) -> None:
        """Log performance metrics"""
        try:
            method = request.method
            url = str(request.url)
            status_code = response.status_code
            
            # Performance data
            perf_data = {
                "type": "performance",
                "method": method,
                "url": url,
                "status_code": status_code,
                "process_time": round(process_time, 4),
                "timestamp": time.time()
            }
            
            # Log slow requests
            if process_time > self.slow_request_threshold:
                perf_data["slow_request"] = True
                logger.warning(f"Slow request detected: {json.dumps(perf_data)}")
            else:
                logger.info(f"Performance: {json.dumps(perf_data)}")
                
        except Exception as e:
            logger.error(f"Error logging performance: {e}")


class ErrorLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for error logging and tracking"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Log errors and exceptions"""
        
        try:
            response = await call_next(request)
            return response
            
        except Exception as e:
            # Log the error
            await self._log_error(request, e)
            
            # Re-raise the exception
            raise
    
    async def _log_error(self, request: Request, error: Exception) -> None:
        """Log error details"""
        try:
            error_data = {
                "type": "error",
                "method": request.method,
                "url": str(request.url),
                "error_type": type(error).__name__,
                "error_message": str(error),
                "client_ip": self._get_client_ip(request),
                "user_agent": request.headers.get("user-agent", ""),
                "timestamp": time.time()
            }
            
            logger.error(f"Request error: {json.dumps(error_data)}", exc_info=True)
            
        except Exception as log_error:
            logger.error(f"Error logging error: {log_error}")
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address"""
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        return request.client.host if request.client else "unknown"