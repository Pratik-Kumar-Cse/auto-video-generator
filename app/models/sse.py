"""
SSE (Server-Sent Events) models and schemas for FastAPI Video Generation
Service
"""

from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class SSEEventRequest(BaseModel):
    """Request model for SSE connection"""
    token: str = Field(..., description="Authentication token")


class SSEEventResponse(BaseModel):
    """Response model for SSE events"""
    event: str = Field(..., description="Event type")
    data: Any = Field(..., description="Event data")
    type: str = Field(..., description="Event category")
    timestamp: float = Field(..., description="Event timestamp")
    client_id: Optional[str] = Field(None, description="Target client ID")


class TriggerEventRequest(BaseModel):
    """Request model for triggering events"""
    event_type: str = Field(..., description="Type of event to trigger")
    data: Dict[str, Any] = Field(..., description="Event data")
    message: Optional[str] = Field(None, description="Optional message")


class TriggerEventResponse(BaseModel):
    """Response model for event triggering"""
    status: str = Field(..., description="Status of the event trigger")
    message: str = Field(..., description="Response message")
    client_id: Optional[str] = Field(None, description="Target client ID")


class BroadcastEventRequest(BaseModel):
    """Request model for broadcasting events"""
    event_type: str = Field(..., description="Type of event to broadcast")
    data: Dict[str, Any] = Field(..., description="Event data")
    message: Optional[str] = Field(None, description="Optional message")


class BroadcastEventResponse(BaseModel):
    """Response model for broadcast events"""
    status: str = Field(..., description="Status of the broadcast")
    message: str = Field(..., description="Response message")
    clients_count: int = Field(..., description="Number of clients reached")


class SSEStatusResponse(BaseModel):
    """Response model for SSE status"""
    connected_clients: int = Field(
        ..., description="Number of connected clients"
    )
    client_ids: list = Field(..., description="List of connected client IDs")
    is_active: bool = Field(..., description="Whether SSE service is active")


class ErrorResponse(BaseModel):
    """Error response model"""
    message: str = Field(..., description="Error message")
    code: int = Field(..., description="Error status code")
    error_type: Optional[str] = Field(None, description="Type of error")


# Event type constants
class EventTypes:
    """Constants for different event types"""
    VIDEO_STREAM = "video_stream"
    SCRIPT_GENERATION = "script_generation"
    PROCESSING_UPDATE = "processing_update"
    NOTIFICATION = "notification"
    SYSTEM_MESSAGE = "system_message"
    KEEP_ALIVE = "keep-alive"
    ERROR = "error"
    COMPLETED = "completed"
    PROGRESS = "progress"


# Event data templates
class VideoStreamEventData(BaseModel):
    """Data model for video stream events"""
    video_id: Optional[str] = Field(None, description="Video ID")
    status: str = Field(..., description="Processing status")
    progress: Optional[float] = Field(None, description="Progress percentage")
    message: str = Field(..., description="Status message")
    metadata: Optional[Dict[str, Any]] = Field(
        None, description="Additional metadata"
    )


class ScriptGenerationEventData(BaseModel):
    """Data model for script generation events"""
    script_id: Optional[str] = Field(None, description="Script ID")
    task_id: Optional[str] = Field(None, description="Task ID")
    status: str = Field(..., description="Generation status")
    progress: Optional[float] = Field(None, description="Progress percentage")
    content: Optional[str] = Field(None, description="Generated content")
    message: str = Field(..., description="Status message")


class ProcessingUpdateEventData(BaseModel):
    """Data model for processing update events"""
    task_id: str = Field(..., description="Task ID")
    task_type: str = Field(..., description="Type of task")
    status: str = Field(..., description="Processing status")
    progress: Optional[float] = Field(None, description="Progress percentage")
    current_step: Optional[str] = Field(
        None, description="Current processing step"
    )
    total_steps: Optional[int] = Field(
        None, description="Total number of steps"
    )
    message: str = Field(..., description="Status message")
    error: Optional[str] = Field(None, description="Error message if any")


class NotificationEventData(BaseModel):
    """Data model for notification events"""
    title: str = Field(..., description="Notification title")
    message: str = Field(..., description="Notification message")
    type: str = Field(
        ..., description="Notification type (info, warning, error, success)"
    )
    action_url: Optional[str] = Field(None, description="Optional action URL")
    metadata: Optional[Dict[str, Any]] = Field(
        None, description="Additional metadata"
    )


class SystemMessageEventData(BaseModel):
    """Data model for system message events"""
    message: str = Field(..., description="System message")
    level: str = Field(..., description="Message level (info, warning, error)")
    component: Optional[str] = Field(None, description="System component")
    timestamp: Optional[float] = Field(None, description="Message timestamp")