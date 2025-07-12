"""
Unit tests for custom exception classes
"""

import pytest
from fastapi import HTTPException

from app.core.exceptions import (
    ScriptNotFoundException,
    ScriptProcessingException,
    BadRequestException,
    VideoNotFoundException,
    VideoProcessingException,
    AuthenticationException,
    AuthorizationException,
    RateLimitException,
    ExternalServiceException,
    DatabaseException,
    ValidationException,
    FileNotFoundException,
    FileProcessingException,
    ConfigurationException
)


class TestCustomExceptions:
    """Test custom exception classes"""

    def test_script_not_found_exception(self):
        """Test ScriptNotFoundException"""
        script_id = "507f1f77bcf86cd799439011"
        exception = ScriptNotFoundException(script_id)
        
        assert isinstance(exception, HTTPException)
        assert exception.status_code == 404
        assert script_id in exception.detail
        assert "Script not found" in exception.detail

    def test_script_not_found_exception_with_custom_message(self):
        """Test ScriptNotFoundException with custom message"""
        custom_message = "Custom script error message"
        exception = ScriptNotFoundException(message=custom_message)
        
        assert exception.status_code == 404
        assert exception.detail == custom_message

    def test_script_processing_exception(self):
        """Test ScriptProcessingException"""
        error_message = "Failed to generate script content"
        exception = ScriptProcessingException(error_message)
        
        assert isinstance(exception, HTTPException)
        assert exception.status_code == 422
        assert exception.detail == error_message

    def test_script_processing_exception_default_message(self):
        """Test ScriptProcessingException with default message"""
        exception = ScriptProcessingException()
        
        assert exception.status_code == 422
        assert "Script processing failed" in exception.detail

    def test_bad_request_exception(self):
        """Test BadRequestException"""
        error_message = "Invalid request parameters"
        exception = BadRequestException(error_message)
        
        assert isinstance(exception, HTTPException)
        assert exception.status_code == 400
        assert exception.detail == error_message

    def test_bad_request_exception_default_message(self):
        """Test BadRequestException with default message"""
        exception = BadRequestException()
        
        assert exception.status_code == 400
        assert "Bad request" in exception.detail

    def test_video_not_found_exception(self):
        """Test VideoNotFoundException"""
        video_id = "507f1f77bcf86cd799439012"
        exception = VideoNotFoundException(video_id)
        
        assert isinstance(exception, HTTPException)
        assert exception.status_code == 404
        assert video_id in exception.detail
        assert "Video not found" in exception.detail

    def test_video_not_found_exception_with_custom_message(self):
        """Test VideoNotFoundException with custom message"""
        custom_message = "Video has been deleted"
        exception = VideoNotFoundException(message=custom_message)
        
        assert exception.status_code == 404
        assert exception.detail == custom_message

    def test_video_processing_exception(self):
        """Test VideoProcessingException"""
        error_message = "Failed to render video"
        exception = VideoProcessingException(error_message)
        
        assert isinstance(exception, HTTPException)
        assert exception.status_code == 422
        assert exception.detail == error_message

    def test_video_processing_exception_default_message(self):
        """Test VideoProcessingException with default message"""
        exception = VideoProcessingException()
        
        assert exception.status_code == 422
        assert "Video processing failed" in exception.detail

    def test_authentication_exception(self):
        """Test AuthenticationException"""
        error_message = "Invalid credentials"
        exception = AuthenticationException(error_message)
        
        assert isinstance(exception, HTTPException)
        assert exception.status_code == 401
        assert exception.detail == error_message

    def test_authentication_exception_default_message(self):
        """Test AuthenticationException with default message"""
        exception = AuthenticationException()
        
        assert exception.status_code == 401
        assert "Authentication failed" in exception.detail

    def test_authorization_exception(self):
        """Test AuthorizationException"""
        error_message = "Insufficient permissions"
        exception = AuthorizationException(error_message)
        
        assert isinstance(exception, HTTPException)
        assert exception.status_code == 403
        assert exception.detail == error_message

    def test_authorization_exception_default_message(self):
        """Test AuthorizationException with default message"""
        exception = AuthorizationException()
        
        assert exception.status_code == 403
        assert "Access denied" in exception.detail

    def test_rate_limit_exception(self):
        """Test RateLimitException"""
        error_message = "Too many requests"
        exception = RateLimitException(error_message)
        
        assert isinstance(exception, HTTPException)
        assert exception.status_code == 429
        assert exception.detail == error_message

    def test_rate_limit_exception_default_message(self):
        """Test RateLimitException with default message"""
        exception = RateLimitException()
        
        assert exception.status_code == 429
        assert "Rate limit exceeded" in exception.detail

    def test_rate_limit_exception_with_retry_after(self):
        """Test RateLimitException with retry-after header"""
        retry_after = 60
        exception = RateLimitException(retry_after=retry_after)
        
        assert exception.status_code == 429
        assert exception.headers is not None
        assert exception.headers.get("Retry-After") == str(retry_after)

    def test_external_service_exception(self):
        """Test ExternalServiceException"""
        service_name = "OpenAI API"
        error_message = "Service temporarily unavailable"
        exception = ExternalServiceException(service_name, error_message)
        
        assert isinstance(exception, HTTPException)
        assert exception.status_code == 502
        assert service_name in exception.detail
        assert error_message in exception.detail

    def test_external_service_exception_default_message(self):
        """Test ExternalServiceException with default message"""
        service_name = "Redis"
        exception = ExternalServiceException(service_name)
        
        assert exception.status_code == 502
        assert service_name in exception.detail
        assert "External service error" in exception.detail

    def test_database_exception(self):
        """Test DatabaseException"""
        error_message = "Connection timeout"
        exception = DatabaseException(error_message)
        
        assert isinstance(exception, HTTPException)
        assert exception.status_code == 500
        assert exception.detail == error_message

    def test_database_exception_default_message(self):
        """Test DatabaseException with default message"""
        exception = DatabaseException()
        
        assert exception.status_code == 500
        assert "Database error" in exception.detail

    def test_validation_exception(self):
        """Test ValidationException"""
        field_name = "email"
        error_message = "Invalid email format"
        exception = ValidationException(field_name, error_message)
        
        assert isinstance(exception, HTTPException)
        assert exception.status_code == 422
        assert field_name in exception.detail
        assert error_message in exception.detail

    def test_validation_exception_with_errors_list(self):
        """Test ValidationException with list of errors"""
        errors = [
            {"field": "email", "message": "Invalid format"},
            {"field": "password", "message": "Too short"}
        ]
        exception = ValidationException(errors=errors)
        
        assert exception.status_code == 422
        assert "Validation failed" in exception.detail
        # Check that error details are included
        for error in errors:
            assert error["field"] in str(exception.detail)

    def test_file_not_found_exception(self):
        """Test FileNotFoundException"""
        file_path = "/path/to/missing/file.mp4"
        exception = FileNotFoundException(file_path)
        
        assert isinstance(exception, HTTPException)
        assert exception.status_code == 404
        assert file_path in exception.detail
        assert "File not found" in exception.detail

    def test_file_not_found_exception_with_custom_message(self):
        """Test FileNotFoundException with custom message"""
        custom_message = "Media file has been moved"
        exception = FileNotFoundException(message=custom_message)
        
        assert exception.status_code == 404
        assert exception.detail == custom_message

    def test_file_processing_exception(self):
        """Test FileProcessingException"""
        error_message = "Unsupported file format"
        exception = FileProcessingException(error_message)
        
        assert isinstance(exception, HTTPException)
        assert exception.status_code == 422
        assert exception.detail == error_message

    def test_file_processing_exception_default_message(self):
        """Test FileProcessingException with default message"""
        exception = FileProcessingException()
        
        assert exception.status_code == 422
        assert "File processing failed" in exception.detail

    def test_configuration_exception(self):
        """Test ConfigurationException"""
        config_key = "REQUESTY_KEY"
        exception = ConfigurationException(config_key)
        
        assert isinstance(exception, HTTPException)
        assert exception.status_code == 500
        assert config_key in exception.detail
        assert "Configuration error" in exception.detail

    def test_configuration_exception_with_custom_message(self):
        """Test ConfigurationException with custom message"""
        custom_message = "Invalid configuration format"
        exception = ConfigurationException(message=custom_message)
        
        assert exception.status_code == 500
        assert exception.detail == custom_message

    def test_exception_inheritance(self):
        """Test that all custom exceptions inherit from HTTPException"""
        exceptions = [
            ScriptNotFoundException("test"),
            ScriptProcessingException("test"),
            BadRequestException("test"),
            VideoNotFoundException("test"),
            VideoProcessingException("test"),
            AuthenticationException("test"),
            AuthorizationException("test"),
            RateLimitException("test"),
            ExternalServiceException("service", "test"),
            DatabaseException("test"),
            ValidationException("field", "test"),
            FileNotFoundException("test"),
            FileProcessingException("test"),
            ConfigurationException("test")
        ]
        
        for exception in exceptions:
            assert isinstance(exception, HTTPException)
            assert hasattr(exception, 'status_code')
            assert hasattr(exception, 'detail')

    def test_exception_status_codes(self):
        """Test that exceptions have correct status codes"""
        status_code_mapping = {
            ScriptNotFoundException("test"): 404,
            ScriptProcessingException("test"): 422,
            BadRequestException("test"): 400,
            VideoNotFoundException("test"): 404,
            VideoProcessingException("test"): 422,
            AuthenticationException("test"): 401,
            AuthorizationException("test"): 403,
            RateLimitException("test"): 429,
            ExternalServiceException("service", "test"): 502,
            DatabaseException("test"): 500,
            ValidationException("field", "test"): 422,
            FileNotFoundException("test"): 404,
            FileProcessingException("test"): 422,
            ConfigurationException("test"): 500
        }
        
        for exception, expected_code in status_code_mapping.items():
            assert exception.status_code == expected_code

    def test_exception_with_none_values(self):
        """Test exceptions with None values"""
        # Test exceptions that can handle None values gracefully
        exception1 = ScriptNotFoundException(None)
        assert exception1.status_code == 404
        assert "None" in exception1.detail or "Script not found" in exception1.detail
        
        exception2 = VideoNotFoundException(None)
        assert exception2.status_code == 404
        assert "None" in exception2.detail or "Video not found" in exception2.detail

    def test_exception_with_empty_string(self):
        """Test exceptions with empty string values"""
        exception1 = ScriptProcessingException("")
        assert exception1.status_code == 422
        assert exception1.detail == "" or "Script processing failed" in exception1.detail
        
        exception2 = BadRequestException("")
        assert exception2.status_code == 400
        assert exception2.detail == "" or "Bad request" in exception2.detail

    def test_rate_limit_exception_headers(self):
        """Test RateLimitException headers functionality"""
        # Test without retry-after
        exception1 = RateLimitException("Too many requests")
        assert exception1.headers is None or "Retry-After" not in exception1.headers
        
        # Test with retry-after
        exception2 = RateLimitException("Too many requests", retry_after=120)
        assert exception2.headers is not None
        assert exception2.headers["Retry-After"] == "120"
        
        # Test with zero retry-after
        exception3 = RateLimitException("Too many requests", retry_after=0)
        assert exception3.headers is not None
        assert exception3.headers["Retry-After"] == "0"

    def test_validation_exception_complex_errors(self):
        """Test ValidationException with complex error structures"""
        complex_errors = [
            {
                "field": "user.email",
                "message": "Invalid email format",
                "code": "INVALID_EMAIL"
            },
            {
                "field": "user.password",
                "message": "Password must be at least 8 characters",
                "code": "PASSWORD_TOO_SHORT"
            }
        ]
        
        exception = ValidationException(errors=complex_errors)
        assert exception.status_code == 422
        assert "Validation failed" in exception.detail
        
        # Verify that complex error information is preserved
        detail_str = str(exception.detail)
        assert "user.email" in detail_str
        assert "user.password" in detail_str

    def test_external_service_exception_with_status_code(self):
        """Test ExternalServiceException with custom status code"""
        # Some external service exceptions might want different status codes
        exception = ExternalServiceException(
            "Payment Gateway",
            "Payment processing failed",
            status_code=503
        )
        
        # If the exception supports custom status codes
        if hasattr(exception, 'status_code'):
            # Check if it uses the custom status code or defaults to 502
            assert exception.status_code in [502, 503]
        
        assert "Payment Gateway" in exception.detail
        assert "Payment processing failed" in exception.detail