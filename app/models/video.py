"""
Pydantic models for video-related operations
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, validator
from enum import Enum


class VideoStatus(str, Enum):
    """Video processing status"""
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    TIMED_OUT = "TIMED_OUT"


class VideoViewType(str, Enum):
    """Video view type"""
    LANDSCAPE = "LANDSCAPE"
    PORTRAIT = "PORTRAIT"
    SQUARE = "SQUARE"


class UploadDomain(str, Enum):
    """Upload domain options"""
    YOUTUBE = "youtube"
    LINKEDIN = "linkedin"
    INSTAGRAM = "instagram"


class ScriptType(str, Enum):
    """Script generation type"""
    TOPIC = "TOPIC"
    VIDEO = "VIDEO"
    BLOG = "BLOG"
    CUSTOM = "CUSTOM"


class VideoType(str, Enum):
    """Video type"""
    SHORTS = "shorts"
    YOUTUBE = "youtube"
    SOCIAL = "social"


# Caption model
class Caption(BaseModel):
    """Caption configuration"""
    font_path: str = Field(..., description="Subtitle font path")
    color_code: str = Field(..., description="Subtitle color code")


# Keywords model for video generation
class Keywords(BaseModel):
    """Keywords and metadata for video generation"""
    time: Optional[str] = Field(None, description="Time-related information")
    objective: Optional[str] = Field(None, description="Objective of the video")
    audience: Optional[str] = Field(None, description="Target audience")
    gender: Optional[str] = Field(None, description="Gender focus")
    tone: Optional[str] = Field(None, description="Tone of the video content")
    speakers: Optional[str] = Field(None, description="Speaker information")


# Video metadata model
class VideoMetadata(BaseModel):
    """Video metadata"""
    title: Optional[str] = Field(None, description="Video title")
    description: Optional[str] = Field(None, description="Video description")
    keywords: Optional[List[str]] = Field(None, description="Video keywords")
    caption: Optional[str] = Field(None, description="Video caption")
    tags: Optional[List[str]] = Field(None, description="Video tags")
    category_id: Optional[str] = Field(None, description="Video category ID")
    privacy_status: Optional[str] = Field(
        "public", 
        description="Privacy status"
    )


# Request models
class GenerateVideoRequest(BaseModel):
    """Request model for generating video"""
    script_id: str = Field(..., description="The script ID for the video")
    avatar_id: Optional[str] = Field(None, description="Avatar ID (optional)")
    voice_id: Optional[str] = Field(None, description="Voice ID")
    template_id: Optional[str] = Field(None, description="Template ID")
    caption: Optional[Caption] = Field(None, description="Caption configuration")
    view_type: VideoViewType = Field(
        VideoViewType.PORTRAIT, 
        description="Type of view for the video"
    )


class GenerateVideoByIdRequest(BaseModel):
    """Request model for generating video by ID"""
    video_id: str = Field(..., description="The video ID to generate")


class GenerateWorkflowVideoRequest(BaseModel):
    """Request model for workflow video generation"""
    topic: str = Field(..., description="Topic of the video")
    video_type: VideoType = Field(..., description="Type of video")
    link: Optional[str] = Field(None, description="Link of video or article")
    script_type: ScriptType = Field(..., description="Type of input for script")
    add_brand: Optional[bool] = Field(False, description="Add brand to video")
    music_media_id: Optional[str] = Field(None, description="Music media ID")
    keywords: Keywords = Field(..., description="Additional keywords")
    avatar_id: Optional[str] = Field(None, description="Avatar ID")
    voice_id: Optional[str] = Field(None, description="Voice ID")
    template_id: Optional[str] = Field(None, description="Template ID")
    caption: Optional[Caption] = Field(None, description="Caption configuration")
    view_type: VideoViewType = Field(
        VideoViewType.PORTRAIT,
        description="Type of view for the video"
    )
    approval: Optional[bool] = Field(False, description="Require approval")

    @validator("link")
    def validate_link_required(cls, v, values):
        """Validate that link is required for VIDEO and BLOG script types"""
        script_type = values.get("script_type")
        if script_type in [ScriptType.VIDEO, ScriptType.BLOG] and not v:
            raise ValueError("Link is required for VIDEO and BLOG script types")
        return v


class GenerateWorkflowVideoByIdRequest(BaseModel):
    """Request model for workflow video generation by ID"""
    video_id: str = Field(..., description="The video ID to generate")
    approval: Optional[bool] = Field(False, description="Require approval")


class UploadVideoRequest(BaseModel):
    """Request model for uploading video"""
    video_id: str = Field(..., description="The video ID to upload")
    upload_domain: UploadDomain = Field(..., description="Upload domain")


class UpdateMetadataRequest(BaseModel):
    """Request model for updating video metadata"""
    metadata: VideoMetadata = Field(..., description="Video metadata")


class VideoUpdate(BaseModel):
    """Request model for updating video"""
    is_community_video: Optional[bool] = Field(
        None, 
        description="Community video flag"
    )
    thumbnail_link: Optional[str] = Field(
        None, 
        description="Video thumbnail link"
    )
    title: Optional[str] = Field(None, description="Video title")
    metadata: Optional[VideoMetadata] = Field(None, description="Video metadata")


class VideoCreate(BaseModel):
    """Request model for creating video"""
    user_id: str = Field(..., description="User ID")
    script_id: str = Field(..., description="Script ID")
    voice_id: Optional[str] = Field(None, description="Voice ID")
    avatar_id: Optional[str] = Field(None, description="Avatar ID")
    template_id: Optional[str] = Field(None, description="Template ID")
    view_type: VideoViewType = Field(
        VideoViewType.PORTRAIT,
        description="Video view type"
    )
    caption: Optional[Caption] = Field(None, description="Caption configuration")


class VideoQualityRequest(BaseModel):
    """Request model for video quality"""
    quality: str = Field(..., pattern="^(720p|1080p)$", description="Video quality")


# Response models
class VideoData(BaseModel):
    """Video data model"""
    video_id: str = Field(..., description="Video ID")
    task_id: Optional[str] = Field(None, description="Task ID")
    view_type: Optional[VideoViewType] = Field(None, description="View type")
    queue_position: Optional[int] = Field(0, description="Queue position")


class VideoResponseModel(BaseModel):
    """Video response model"""
    id: str = Field(..., alias="_id", description="Unique identifier for the video")
    user_id: str = Field(..., description="ID of the user")
    voice_id: Optional[str] = Field(None, description="ID of the voice")
    avatar_id: Optional[str] = Field(None, description="ID of the avatar")
    script_id: str = Field(..., description="ID of the script")
    status: VideoStatus = Field(..., description="Current status of the video")
    link: Optional[str] = Field(None, description="Link to the video")
    title: Optional[str] = Field(None, description="Title of the video")
    avatar_video_ids: Optional[List[str]] = Field(
        None, 
        description="List of avatar video IDs"
    )
    avatar_video_urls: Optional[List[str]] = Field(
        None,
        description="List of avatar video URLs"
    )
    created_at: Optional[datetime] = Field(
        None,
        description="Timestamp of video creation"
    )
    updated_at: Optional[datetime] = Field(
        None,
        description="Timestamp of last update"
    )
    template_id: Optional[str] = Field(
        None,
        description="ID of the template"
    )
    status_message: Optional[str] = Field(
        None,
        description="Additional status information"
    )
    view_type: Optional[VideoViewType] = Field(
        None,
        description="Type of view for the video"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional metadata"
    )
    link_1080p: Optional[str] = Field(
        None,
        description="Link to the 1080p version"
    )
    thumbnail_link: Optional[str] = Field(
        None,
        description="Link to the video thumbnail"
    )
    is_community_video: Optional[bool] = Field(
        False,
        description="Community video flag"
    )
    task_id: Optional[str] = Field(None, description="Celery task ID")


class VideoStatusData(BaseModel):
    """Video status data"""
    status: VideoStatus = Field(..., description="Status of the video")


class PaginationInfo(BaseModel):
    """Pagination information"""
    page: int = Field(..., description="Current page number")
    per_page: int = Field(..., description="Items per page")
    total_count: int = Field(..., description="Total number of items")
    total_pages: int = Field(..., description="Total number of pages")


# API Response models
class VideoResponse(BaseModel):
    """Video API response"""
    message: str = Field(..., description="Response message")
    data: VideoData = Field(..., description="Video data")
    code: int = Field(..., description="Response code")


class VideoDetailResponse(BaseModel):
    """Video detail API response"""
    message: str = Field(..., description="Response message")
    data: VideoResponseModel = Field(..., description="Video details")
    code: int = Field(..., description="Response code")


class VideoListResponse(BaseModel):
    """Video list API response"""
    message: str = Field(..., description="Response message")
    data: List[VideoResponseModel] = Field(..., description="List of videos")
    pagination: PaginationInfo = Field(..., description="Pagination info")
    code: int = Field(..., description="Response code")


class VideoStatusResponse(BaseModel):
    """Video status API response"""
    message: str = Field(..., description="Response message")
    data: VideoStatusData = Field(..., description="Video status data")
    code: int = Field(..., description="Response code")


class UploadResponse(BaseModel):
    """Upload response"""
    message: str = Field(..., description="Response message")
    video_id: str = Field(..., description="Uploaded video ID")
    code: int = Field(..., description="Response code")


class DownloadResponse(BaseModel):
    """Download response"""
    message: str = Field(..., description="Response message")
    download_url: str = Field(..., description="Download URL")
    code: int = Field(..., description="Response code")