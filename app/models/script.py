"""
Script models for FastAPI Video Generation Service
"""

from typing import Optional, Dict, List, Any
from pydantic import BaseModel, Field
from datetime import datetime


class ScriptCreate(BaseModel):
    """Model for creating a new script"""
    topic: str = Field(..., description="Script topic")
    video_type: str = Field(..., description="Type of video")
    keywords: Optional[Dict[str, Any]] = Field(default={}, description="Keywords")
    input_type: str = Field(..., description="Input type (VIDEO, BLOG, TOPIC)")
    add_brand: Optional[bool] = Field(default=False, description="Add brand info")
    music_media_id: Optional[str] = Field(None, description="Music media ID")
    link: Optional[str] = Field(None, description="Link for video/blog input")
    video_link: Optional[str] = Field(None, description="Video link")


class ScriptUpdate(BaseModel):
    """Model for updating a script"""
    title: Optional[str] = Field(None, description="Script title")
    content: Optional[str] = Field(None, description="Script content")
    topic: Optional[str] = Field(None, description="Script topic")
    video_type: Optional[str] = Field(None, description="Type of video")
    keywords: Optional[Dict[str, Any]] = Field(None, description="Keywords")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Metadata")


class GenerateScriptRequest(BaseModel):
    """Model for script generation request"""
    topic: str = Field(..., description="Script topic")
    video_type: str = Field(..., description="Type of video")
    keywords: Optional[Dict[str, Any]] = Field(default={}, description="Keywords")
    input_type: str = Field(..., description="Input type (VIDEO, BLOG, TOPIC)")
    video_link: Optional[str] = Field(None, description="Video link")


class RegenerateScriptRequest(BaseModel):
    """Model for script regeneration request"""
    topic: str = Field(..., description="Script topic")
    video_type: str = Field(..., description="Type of video")
    link: Optional[str] = Field(None, description="Link for video/blog input")
    keywords: Optional[Dict[str, Any]] = Field(default={}, description="Keywords")


class ValidateLinkRequest(BaseModel):
    """Model for link validation request"""
    link: str = Field(..., description="Link to validate")
    link_type: str = Field(..., description="Type of link")


class Script(BaseModel):
    """Script model"""
    id: str = Field(..., alias="_id", description="Script ID")
    user_id: str = Field(..., description="User ID")
    title: str = Field(..., description="Script title")
    content: str = Field(..., description="Script content")
    topic: str = Field(..., description="Script topic")
    video_type: str = Field(..., description="Type of video")
    keywords: Optional[Dict[str, Any]] = Field(default={}, description="Keywords")
    input_type: str = Field(..., description="Input type")
    status: str = Field(default="draft", description="Script status")
    metadata: Optional[Dict[str, Any]] = Field(default={}, description="Metadata")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Update timestamp")

    model_config = {
        "populate_by_name": True,
        "json_encoders": {
            datetime: lambda v: v.isoformat()
        }
    }


class ScriptResponse(BaseModel):
    """Response model for script operations"""
    message: str = Field(..., description="Response message")
    data: Optional[Script] = Field(None, description="Script data")
    code: int = Field(..., description="Response code")


class ScriptListData(BaseModel):
    """Data model for script list response"""
    scripts: List[Script] = Field(..., description="List of scripts")
    page: int = Field(..., description="Current page")
    limit: int = Field(..., description="Items per page")
    total_count: int = Field(..., description="Total number of scripts")
    total_pages: int = Field(..., description="Total number of pages")


class ScriptListResponse(BaseModel):
    """Response model for script list operations"""
    message: str = Field(..., description="Response message")
    data: ScriptListData = Field(..., description="Script list data")
    code: int = Field(..., description="Response code")