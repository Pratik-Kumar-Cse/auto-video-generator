"""
Common models for FastAPI Video Generation Service
"""

from typing import Optional, Any, Dict
from pydantic import BaseModel, Field


class PaginationParams(BaseModel):
    """Pagination parameters"""
    page: int = Field(1, ge=1, description="Page number")
    per_page: int = Field(10, ge=1, le=100, description="Items per page")


class SuccessResponse(BaseModel):
    """Generic success response"""
    message: str = Field(..., description="Response message")
    data: Optional[Dict[str, Any]] = Field(None, description="Response data")
    code: int = Field(..., description="Response code")


class ErrorResponse(BaseModel):
    """Generic error response"""
    message: str = Field(..., description="Error message")
    error: Optional[str] = Field(None, description="Error details")
    code: int = Field(..., description="Error code")


class TaskResponse(BaseModel):
    """Task response model"""
    task_id: str = Field(..., description="Task ID")
    status: str = Field(..., description="Task status")
    message: str = Field(..., description="Task message")


class HealthResponse(BaseModel):
    """Health check response"""
    status: str = Field(..., description="Service status")
    service: str = Field(..., description="Service name")
    version: str = Field(..., description="Service version")
    timestamp: Optional[str] = Field(None, description="Response timestamp")


class MetricsResponse(BaseModel):
    """Metrics response"""
    total_requests: int = Field(..., description="Total requests")
    active_tasks: int = Field(..., description="Active tasks")
    queue_size: int = Field(..., description="Queue size")
    uptime: str = Field(..., description="Service uptime")


class FilterParams(BaseModel):
    """Common filter parameters"""
    search: Optional[str] = Field(None, description="Search term")
    status: Optional[str] = Field(None, description="Status filter")
    created_from: Optional[str] = Field(None, description="Created from date")
    created_to: Optional[str] = Field(None, description="Created to date")
    sort_by: Optional[str] = Field("created_at", description="Sort field")
    sort_order: Optional[str] = Field("desc", pattern="^(asc|desc)$", description="Sort order")