"""
Custom exceptions for the FastAPI Video Generation Service
"""

from typing import Any, Dict, Optional
from fastapi import HTTPException, status


class CustomHTTPException(HTTPException):
    """Base custom HTTP exception"""
    
    def __init__(
        self,
        status_code: int,
        detail: str,
        headers: Optional[Dict[str, Any]] = None
    ):
        super().__init__(status_code=status_code, detail=detail, headers=headers)


class ValidationException(Exception):
    """Exception for validation errors"""
    
    def __init__(self, detail: str):
        self.detail = detail
        super().__init__(detail)


class DatabaseException(Exception):
    """Exception for database errors"""
    
    def __init__(self, detail: str):
        self.detail = detail
        super().__init__(detail)


class AuthenticationException(CustomHTTPException):
    """Exception for authentication errors"""
    
    def __init__(self, detail: str = "Authentication failed"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"}
        )


class AuthorizationException(CustomHTTPException):
    """Exception for authorization errors"""
    
    def __init__(self, detail: str = "Not authorized to access this resource"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail
        )


class NotFoundException(CustomHTTPException):
    """Exception for resource not found errors"""
    
    def __init__(self, detail: str = "Resource not found"):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail
        )


class ConflictException(CustomHTTPException):
    """Exception for conflict errors"""
    
    def __init__(self, detail: str = "Resource conflict"):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail
        )


class BadRequestException(CustomHTTPException):
    """Exception for bad request errors"""
    
    def __init__(self, detail: str = "Bad request"):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail
        )


class UnprocessableEntityException(CustomHTTPException):
    """Exception for unprocessable entity errors"""
    
    def __init__(self, detail: str = "Unprocessable entity"):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=detail
        )


class TooManyRequestsException(CustomHTTPException):
    """Exception for rate limiting errors"""
    
    def __init__(self, detail: str = "Too many requests"):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=detail
        )


class InternalServerErrorException(CustomHTTPException):
    """Exception for internal server errors"""
    
    def __init__(self, detail: str = "Internal server error"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail
        )


class ServiceUnavailableException(CustomHTTPException):
    """Exception for service unavailable errors"""
    
    def __init__(self, detail: str = "Service temporarily unavailable"):
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=detail
        )


# Video-specific exceptions
class VideoNotFoundException(NotFoundException):
    """Exception for video not found"""
    
    def __init__(self, video_id: str):
        super().__init__(detail=f"Video with ID {video_id} not found")


class VideoProcessingException(InternalServerErrorException):
    """Exception for video processing errors"""
    
    def __init__(self, detail: str = "Video processing failed"):
        super().__init__(detail=detail)


class VideoGenerationException(InternalServerErrorException):
    """Exception for video generation errors"""
    
    def __init__(self, detail: str = "Video generation failed"):
        super().__init__(detail=detail)


class VideoUploadException(InternalServerErrorException):
    """Exception for video upload errors"""
    
    def __init__(self, detail: str = "Video upload failed"):
        super().__init__(detail=detail)


# User-specific exceptions
class UserNotFoundException(NotFoundException):
    """Exception for user not found"""
    
    def __init__(self, user_id: str):
        super().__init__(detail=f"User with ID {user_id} not found")


class UserAlreadyExistsException(ConflictException):
    """Exception for user already exists"""
    
    def __init__(self, email: str):
        super().__init__(detail=f"User with email {email} already exists")


class InvalidCredentialsException(AuthenticationException):
    """Exception for invalid credentials"""
    
    def __init__(self):
        super().__init__(detail="Invalid email or password")


class InactiveUserException(AuthenticationException):
    """Exception for inactive user"""
    
    def __init__(self):
        super().__init__(detail="User account is inactive")


# Subscription-specific exceptions
class SubscriptionNotFoundException(NotFoundException):
    """Exception for subscription not found"""
    
    def __init__(self, user_id: str):
        super().__init__(detail=f"Subscription for user {user_id} not found")


class SubscriptionInactiveException(AuthorizationException):
    """Exception for inactive subscription"""
    
    def __init__(self):
        super().__init__(detail="User subscription is inactive")


class InsufficientCreditsException(AuthorizationException):
    """Exception for insufficient credits"""
    
    def __init__(self):
        super().__init__(detail="Insufficient credits to perform this action")


# Script-specific exceptions
class ScriptNotFoundException(NotFoundException):
    """Exception for script not found"""
    
    def __init__(self, script_id: str):
        super().__init__(detail=f"Script with ID {script_id} not found")


class ScriptGenerationException(InternalServerErrorException):
    """Exception for script generation errors"""
    
    def __init__(self, detail: str = "Script generation failed"):
        super().__init__(detail=detail)


class ScriptProcessingException(InternalServerErrorException):
    """Exception for script processing errors"""
    
    def __init__(self, detail: str = "Script processing failed"):
        super().__init__(detail=detail)


# Memory Bank-specific exceptions
class MemoryBankException(InternalServerErrorException):
    """Exception for memory bank errors"""
    
    def __init__(self, detail: str = "Memory bank operation failed"):
        super().__init__(detail=detail)


# Template-specific exceptions
class TemplateNotFoundException(NotFoundException):
    """Exception for template not found"""
    
    def __init__(self, template_id: str):
        super().__init__(detail=f"Template with ID {template_id} not found")


# Avatar-specific exceptions
class AvatarNotFoundException(NotFoundException):
    """Exception for avatar not found"""
    
    def __init__(self, avatar_id: str):
        super().__init__(detail=f"Avatar with ID {avatar_id} not found")


class AvatarGenerationException(InternalServerErrorException):
    """Exception for avatar generation errors"""
    
    def __init__(self, detail: str = "Avatar generation failed"):
        super().__init__(detail=detail)


# Voice-specific exceptions
class VoiceNotFoundException(NotFoundException):
    """Exception for voice not found"""
    
    def __init__(self, voice_id: str):
        super().__init__(detail=f"Voice with ID {voice_id} not found")


class VoiceGenerationException(InternalServerErrorException):
    """Exception for voice generation errors"""
    
    def __init__(self, detail: str = "Voice generation failed"):
        super().__init__(detail=detail)


# Media-specific exceptions
class MediaNotFoundException(NotFoundException):
    """Exception for media not found"""
    
    def __init__(self, media_id: str):
        super().__init__(detail=f"Media with ID {media_id} not found")


class MediaProcessingException(InternalServerErrorException):
    """Exception for media processing errors"""
    
    def __init__(self, detail: str = "Media processing failed"):
        super().__init__(detail=detail)


# File-specific exceptions
class FileTooLargeException(BadRequestException):
    """Exception for file too large"""
    
    def __init__(self, max_size: str):
        super().__init__(detail=f"File size exceeds maximum allowed size of {max_size}")


class UnsupportedFileTypeException(BadRequestException):
    """Exception for unsupported file type"""
    
    def __init__(self, file_type: str, supported_types: list):
        super().__init__(
            detail=f"File type '{file_type}' is not supported. "
                   f"Supported types: {', '.join(supported_types)}"
        )


# External service exceptions
class ExternalServiceException(InternalServerErrorException):
    """Exception for external service errors"""
    
    def __init__(self, service_name: str, detail: str = None):
        if detail:
            message = f"External service '{service_name}' error: {detail}"
        else:
            message = f"External service '{service_name}' is unavailable"
        super().__init__(detail=message)


class APIKeyException(AuthenticationException):
    """Exception for API key errors"""
    
    def __init__(self, service_name: str):
        super().__init__(detail=f"Invalid or missing API key for {service_name}")


# Task-specific exceptions
class TaskNotFoundException(NotFoundException):
    """Exception for task not found"""
    
    def __init__(self, task_id: str):
        super().__init__(detail=f"Task with ID {task_id} not found")


class TaskFailedException(InternalServerErrorException):
    """Exception for task failure"""
    
    def __init__(self, task_id: str, detail: str = None):
        if detail:
            message = f"Task {task_id} failed: {detail}"
        else:
            message = f"Task {task_id} failed"
        super().__init__(detail=message)