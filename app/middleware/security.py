"""
Security middleware for FastAPI application
"""

import time
import logging
from typing import Callable
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class SecurityMiddleware(BaseHTTPMiddleware):
    """Security middleware to add security headers and validate requests"""
    
    def __init__(self, app, max_request_size: int = 10 * 1024 * 1024):
        super().__init__(app)
        self.max_request_size = max_request_size
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and add security headers"""
        
        # Check request size
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > self.max_request_size:
            return JSONResponse(
                status_code=413,
                content={
                    "message": "Request entity too large",
                    "code": 413
                }
            )
        
        # Validate request method
        if request.method not in ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"]:
            return JSONResponse(
                status_code=405,
                content={
                    "message": "Method not allowed",
                    "code": 405
                }
            )
        
        # Process request
        start_time = time.time()
        
        try:
            response = await call_next(request)
        except Exception as e:
            logger.error(f"Unhandled exception in security middleware: {e}")
            return JSONResponse(
                status_code=500,
                content={
                    "message": "Internal server error",
                    "code": 500
                }
            )
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["X-Permitted-Cross-Domain-Policies"] = "none"
        response.headers["Cross-Origin-Embedder-Policy"] = "require-corp"
        response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
        response.headers["Cross-Origin-Resource-Policy"] = "cross-origin"
        
        # Add timing header for monitoring
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        
        # Add server header
        response.headers["Server"] = "FastAPI-VideoGen/1.0"
        
        return response


def validate_input_data(data: dict, max_depth: int = 5) -> bool:
    """Validate input data for security threats"""
    if not isinstance(data, dict):
        return True
    
    max_keys = 100
    max_value_length = 10000
    
    if len(data) > max_keys:
        return False
    
    def _validate_recursive(obj, depth):
        if depth <= 0:
            return False
        
        if isinstance(obj, dict):
            if len(obj) > max_keys:
                return False
            for key, value in obj.items():
                if not _validate_recursive(value, depth - 1):
                    return False
        elif isinstance(obj, list):
            if len(obj) > max_keys:
                return False
            for item in obj:
                if not _validate_recursive(item, depth - 1):
                    return False
        else:
            str_value = str(obj)
            if len(str_value) > max_value_length:
                return False
            
            # Check for potentially dangerous patterns
            dangerous_patterns = [
                "<script",
                "javascript:",
                "vbscript:",
                "onload=",
                "onerror=",
                "eval(",
                "exec(",
                "system(",
                "shell_exec(",
                "passthru(",
                "file_get_contents(",
                "file_put_contents(",
                "fopen(",
                "fwrite(",
                "include(",
                "require(",
                "../../",
                "../",
                "\\x",
                "\\u",
                "%3C",
                "%3E",
                "%22",
                "%27"
            ]
            
            str_lower = str_value.lower()
            for pattern in dangerous_patterns:
                if pattern in str_lower:
                    return False
        
        return True
    
    return _validate_recursive(data, max_depth)


class InputValidationMiddleware(BaseHTTPMiddleware):
    """Middleware to validate input data"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Validate request input data"""
        
        # Only validate POST, PUT, PATCH requests with JSON content
        if request.method in ["POST", "PUT", "PATCH"]:
            content_type = request.headers.get("content-type", "")
            
            if "application/json" in content_type:
                try:
                    # Read request body
                    body = await request.body()
                    if body:
                        import json
                        data = json.loads(body)
                        
                        # Validate input data
                        if not validate_input_data(data):
                            return JSONResponse(
                                status_code=400,
                                content={
                                    "message": "Invalid input data detected",
                                    "code": 400
                                }
                            )
                        
                        # Recreate request with validated body
                        async def receive():
                            return {
                                "type": "http.request",
                                "body": body,
                                "more_body": False
                            }
                        
                        request._receive = receive
                        
                except (json.JSONDecodeError, ValueError):
                    return JSONResponse(
                        status_code=400,
                        content={
                            "message": "Invalid JSON format",
                            "code": 400
                        }
                    )
                except Exception as e:
                    logger.error(f"Error validating input data: {e}")
                    return JSONResponse(
                        status_code=400,
                        content={
                            "message": "Request validation failed",
                            "code": 400
                        }
                    )
        
        response = await call_next(request)
        return response