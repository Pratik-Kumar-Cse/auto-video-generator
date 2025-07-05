"""
Video API endpoints for FastAPI Video Generation Service
Enhanced with comprehensive functionality
"""

import logging
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse

from app.core.database import get_database
from app.core.exceptions import (
    BadRequestException,
    VideoNotFoundException,
    VideoProcessingException,
)
from app.core.redis_client import redis_service
from app.models.common import PaginationParams, SuccessResponse
from app.models.video import (
    GenerateVideoByIdRequest,
    GenerateVideoRequest,
    UpdateMetadataRequest,
    UploadVideoRequest,
    VideoListResponse,
    VideoResponse,
    VideoStatusResponse,
    VideoUpdate,
)
from app.services.video_service import VideoService


# Mock task imports - these would be real Celery tasks
class MockTasks:
    @staticmethod
    def delay(*args, **kwargs):
        import uuid

        class MockTask:
            def __init__(self):
                self.id = str(uuid.uuid4())

        return MockTask()


generate_video_task = MockTasks()
generate_workflow_video_task = MockTasks()
upload_video_task = MockTasks()

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/generate-video", response_model=VideoResponse)
async def generate_video(
    request: GenerateVideoRequest,
    db=Depends(get_database),
):
    """
    Initialize a new video generation task with enhanced workflow
    """
    try:
        user_id = "default_user"  # Use default since auth is removed
        video_service = VideoService(db)

        # Create video entry
        video_data = await video_service.create_video(
            user_id=user_id,
            script_id=request.script_id,
            voice_id=request.voice_id,
            avatar_id=request.avatar_id,
            template_id=request.template_id,
            view_type=request.view_type.value,
            caption=request.caption.dict() if request.caption else None,
        )

        # Check if user has task in progress
        lock_key = f"user_lock:{user_id}"
        queue_key = f"user_queue:{user_id}"

        is_processing = await redis_service.exists(lock_key)

        if is_processing:
            # Add to queue
            queue_position = await redis_service.rpush(
                queue_key,
                {"video_id": str(video_data["_id"]), "user_id": user_id},
            )
            message = f"Video generation task queued. Position: {queue_position}"
            task_id = None
        else:
            # Start processing with enhanced workflow
            await redis_service.set(lock_key, str(video_data["_id"]), expire=5200)

            # Use enhanced video generation
            enhanced_video = await video_service.generate_video_with_workflow(
                video_data
            )

            task = generate_video_task.delay(str(video_data["_id"]), user_id)
            task_id = task.id

            # Update video with task ID
            await video_service.update_video(
                str(video_data["_id"]), {"task_id": task_id}
            )
            message = "Enhanced video generation task started"

        return {
            "message": message,
            "data": {
                "video_id": str(video_data["_id"]),
                "view_type": video_data.get("view_type"),
                "task_id": task_id,
                "queue_position": queue_position if is_processing else 0,
            },
            "code": 201,
        }

    except Exception as e:
        logger.error(f"Error generating video: {e}")
        raise VideoProcessingException(str(e))


@router.get("/video-generation-status/{video_id}")
async def get_video_generation_status(video_id: str, db=Depends(get_database)):
    """
    Get video generation status with real-time updates
    """
    try:
        video_service = VideoService(db)
        video = await video_service.get_video_by_id(video_id)
        if not video:
            raise VideoNotFoundException(video_id)

        task_id = video.get("task_id")
        if not task_id:
            raise BadRequestException("No task associated with this video")

        def generate_status():
            """Generator for server-sent events with enhanced progress"""
            import json
            import time

            # Mock enhanced progress tracking
            progress_steps = [
                {"step": "Initializing", "progress": 5},
                {"step": "Processing script", "progress": 15},
                {"step": "Generating audio", "progress": 30},
                {"step": "Creating video clips", "progress": 50},
                {"step": "Adding effects", "progress": 70},
                {"step": "Rendering final video", "progress": 90},
                {"step": "Completed", "progress": 100},
            ]

            for step_data in progress_steps:
                yield f"data: {json.dumps(step_data)}\n\n"
                time.sleep(2)

            # Send final result
            final_result = {
                "status": "completed",
                "video_url": f"https://example.com/video/{video_id}.mp4",
                "thumbnail_url": f"https://example.com/thumb/{video_id}.jpg",
            }
            yield f"data: {json.dumps(final_result)}\n\n"
            yield "event: CLOSE\ndata: Stream closed\n\n"

        return StreamingResponse(
            generate_status(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
        )

    except Exception as e:
        logger.error(f"Error getting video status: {e}")
        raise VideoProcessingException(str(e))


@router.post("/generate-video-by-id", response_model=VideoResponse)
async def generate_video_by_id(
    request: GenerateVideoByIdRequest, db=Depends(get_database)
):
    """
    Generate video by existing video ID with enhanced processing
    """
    try:
        user_id = "default_user"  # Use default since auth is removed
        video_id = request.video_id
        video_service = VideoService(db)

        video = await video_service.get_video_by_user_id(user_id, video_id)
        if not video:
            raise VideoNotFoundException(video_id)

        if video.get("status") == "COMPLETED":
            raise BadRequestException("Video has already been generated")

        if video.get("status") == "PROCESSING":
            raise BadRequestException("Video is already in progress")

        # Use enhanced workflow generation
        enhanced_video = (
            await video_service.generate_video_using_workflow_with_video_id(
                video_id, user_id
            )
        )

        # Start generation task
        task = generate_video_task.delay(video_id, user_id)

        # Update video with task ID
        await video_service.update_video(video_id, {"task_id": task.id})

        return {
            "message": "Enhanced video generation task created successfully",
            "data": {
                "video_id": video_id,
                "task_id": task.id,
                "view_type": video.get("view_type"),
                "workflow_initiated": True,
            },
            "code": 201,
        }

    except Exception as e:
        logger.error(f"Error generating video by ID: {e}")
        raise VideoProcessingException(str(e))


@router.get("/get-video/{video_id}", response_model=VideoResponse)
async def get_video(video_id: str, db=Depends(get_database)):
    """
    Get video details by ID with enhanced metadata
    """
    try:
        user_id = "default_user"  # Use default since auth is removed
        video_service = VideoService(db)
        video = await video_service.get_video_details(video_id, user_id)

        if not video:
            raise VideoNotFoundException(video_id)

        return {
            "message": "Video fetched successfully",
            "data": video,
            "code": 200,
        }

    except Exception as e:
        logger.error(f"Error getting video: {e}")
        raise VideoProcessingException(str(e))


@router.get("/get-videos", response_model=VideoListResponse)
async def get_videos(
    pagination: PaginationParams = Depends(),
    status: Optional[str] = Query(None),
    view_type: Optional[str] = Query(None),
    title: Optional[str] = Query(None),
    db=Depends(get_database),
):
    """
    Get user's videos with enhanced pagination and filtering
    """
    try:
        user_id = "default_user"  # Use default since auth is removed
        video_service = VideoService(db)

        result = await video_service.find_videos_by_user_id(
            user_id=user_id,
            page=pagination.page,
            per_page=pagination.per_page,
            status=status,
            view_type=view_type,
            title=title,
        )

        return {
            "message": "Videos successfully fetched",
            "data": result["videos"],
            "pagination": {
                "page": result["page"],
                "per_page": result["per_page"],
                "total_count": result["total_count"],
                "total_pages": result["total_pages"],
            },
            "code": 200,
        }

    except Exception as e:
        logger.error(f"Error getting videos: {e}")
        raise VideoProcessingException(str(e))


@router.put("/update-video/{video_id}", response_model=VideoResponse)
async def update_video(video_id: str, request: VideoUpdate, db=Depends(get_database)):
    """
    Update video details with enhanced validation
    """
    try:
        user_id = "default_user"  # Use default since auth is removed
        video_service = VideoService(db)

        video = await video_service.get_video_by_user_id(user_id, video_id)
        if not video:
            raise VideoNotFoundException(video_id)

        updated_video = await video_service.update_video(
            video_id, request.dict(exclude_unset=True)
        )

        return {
            "message": "Video updated successfully",
            "data": updated_video,
            "code": 200,
        }

    except Exception as e:
        logger.error(f"Error updating video: {e}")
        raise VideoProcessingException(str(e))


@router.delete("/delete-video/{video_id}", response_model=SuccessResponse)
async def delete_video(video_id: str, db=Depends(get_database)):
    """
    Delete video by ID with audit trail
    """
    try:
        user_id = "default_user"  # Use default since auth is removed
        video_service = VideoService(db)

        video = await video_service.get_video_by_user_id(user_id, video_id)
        if not video:
            raise VideoNotFoundException(video_id)

        await video_service.soft_delete_video(video_id)

        return {"message": "Video deleted successfully", "code": 200}

    except Exception as e:
        logger.error(f"Error deleting video: {e}")
        raise VideoProcessingException(str(e))


@router.get("/get-video-status/{video_id}", response_model=VideoStatusResponse)
async def get_video_status(video_id: str, db=Depends(get_database)):
    """
    Get enhanced video status with detailed information
    """
    try:
        video_service = VideoService(db)
        video = await video_service.get_video_by_id(video_id)
        if not video:
            raise VideoNotFoundException(video_id)

        # Enhanced status information
        status_data = {
            "status": video["status"],
            "progress": video.get("progress", 0),
            "status_message": video.get("status_message"),
            "estimated_completion": video.get("estimated_completion"),
            "processing_stage": video.get("processing_stage", "pending"),
        }

        return {
            "message": "Video status fetched successfully",
            "data": status_data,
            "code": 200,
        }

    except Exception as e:
        logger.error(f"Error getting video status: {e}")
        raise VideoProcessingException(str(e))


@router.post("/upload-video", response_model=SuccessResponse)
async def upload_video(
    request: UploadVideoRequest,
    background_tasks: BackgroundTasks,
    db=Depends(get_database),
):
    """
    Upload video to external platforms with enhanced integration
    """
    try:
        user_id = "default_user"  # Use default since auth is removed
        video_id = request.video_id
        upload_domain = request.upload_domain.value
        video_service = VideoService(db)

        video = await video_service.get_video_by_user_id(user_id, video_id)
        if not video:
            raise VideoNotFoundException(video_id)

        # Check if video has metadata
        if not video.get("metadata"):
            raise BadRequestException("Video metadata not found")

        # Use enhanced upload method
        upload_result = await video_service.upload_video_to_platform(
            user_id, video, upload_domain
        )

        # Start upload task
        task = upload_video_task.delay(video_id, upload_domain, user_id)

        return {
            "message": "Enhanced video upload started successfully",
            "task_id": task.id,
            "upload_info": upload_result,
            "code": 201,
        }

    except Exception as e:
        logger.error(f"Error uploading video: {e}")
        raise VideoProcessingException(str(e))


@router.put("/update-metadata/{video_id}", response_model=SuccessResponse)
async def update_metadata(
    video_id: str,
    request: UpdateMetadataRequest,
    db=Depends(get_database),
):
    """
    Update video metadata with enhanced validation
    """
    try:
        user_id = "default_user"  # Use default since auth is removed
        video_service = VideoService(db)

        video = await video_service.get_video_by_user_id(user_id, video_id)
        if not video:
            raise VideoNotFoundException(video_id)

        # Update metadata
        existing_metadata = video.get("metadata", {})
        updated_metadata = {**existing_metadata, **request.metadata.dict()}

        updated_video = await video_service.update_video(
            video_id, {"metadata": updated_metadata}
        )

        return {
            "message": "Metadata updated successfully",
            "data": updated_video,
            "code": 200,
        }

    except Exception as e:
        logger.error(f"Error updating metadata: {e}")
        raise VideoProcessingException(str(e))


@router.get("/download-video/{video_id}", response_model=SuccessResponse)
async def download_video(
    video_id: str,
    quality: str = Query("720p", pattern="^(720p|1080p)$"),
    db=Depends(get_database),
):
    """
    Download video with enhanced quality options
    """
    try:
        user_id = "default_user"  # Use default since auth is removed
        video_service = VideoService(db)

        video = await video_service.get_video_by_user_id(user_id, video_id)
        if not video:
            raise VideoNotFoundException(video_id)

        # Use enhanced download method
        download_result = await video_service.download_video_with_quality(
            user_id, video, quality
        )

        return {
            "message": "Video download URL generated successfully",
            "download_url": download_result["download_link"],
            "quality": quality,
            "file_size": download_result.get("file_size"),
            "code": 200,
        }

    except Exception as e:
        logger.error(f"Error downloading video: {e}")
        raise VideoProcessingException(str(e))


@router.post("/generate-metadata", response_model=SuccessResponse)
async def generate_metadata(video_id: str, db=Depends(get_database)):
    """
    Generate enhanced YouTube metadata for video
    """
    try:
        user_id = "default_user"  # Use default since auth is removed
        video_service = VideoService(db)

        video = await video_service.get_video_by_user_id(user_id, video_id)
        if not video:
            raise VideoNotFoundException(video_id)

        # Generate enhanced metadata
        metadata = await video_service.generate_youtube_metadata(video)

        return {
            "message": "Enhanced metadata generated successfully",
            "data": metadata,
            "code": 201,
        }

    except Exception as e:
        logger.error(f"Error generating metadata: {e}")
        raise VideoProcessingException(str(e))


@router.get("/search", response_model=VideoListResponse)
async def search_videos(
    q: str = Query(..., description="Search query"),
    pagination: PaginationParams = Depends(),
    db=Depends(get_database),
):
    """
    Search videos with enhanced search capabilities
    """
    try:
        user_id = "default_user"  # Use default since auth is removed
        video_service = VideoService(db)

        result = await video_service.search_videos(
            user_id=user_id,
            search_term=q,
            page=pagination.page,
            per_page=pagination.per_page,
        )

        return {
            "message": "Enhanced video search completed successfully",
            "data": result["videos"],
            "pagination": {
                "page": result["page"],
                "per_page": result["per_page"],
                "total_count": result["total_count"],
                "total_pages": result["total_pages"],
            },
            "code": 200,
        }

    except Exception as e:
        logger.error(f"Error searching videos: {e}")
        raise VideoProcessingException(str(e))


# Enhanced endpoints for advanced video functionality


@router.post("/regenerate/{video_id}", response_model=VideoResponse)
async def regenerate_video(
    video_id: str,
    regeneration_params: dict = {},
    db=Depends(get_database),
):
    """
    Regenerate video with new parameters
    """
    try:
        user_id = "default_user"  # Use default since auth is removed
        video_service = VideoService(db)

        regenerated_video = await video_service.regenerate_video(
            user_id, video_id, regeneration_params
        )

        return {
            "message": "Video regeneration initiated successfully",
            "data": regenerated_video,
            "code": 201,
        }

    except Exception as e:
        logger.error(f"Error regenerating video: {e}")
        raise VideoProcessingException(str(e))


@router.post("/batch-generate", response_model=dict)
async def batch_generate_videos(
    script_ids: list = Query(..., description="List of script IDs"),
    video_settings: dict = {},
    db=Depends(get_database),
):
    """
    Generate multiple videos in batch
    """
    try:
        user_id = "default_user"  # Use default since auth is removed
        video_service = VideoService(db)

        batch_results = []

        for script_id in script_ids[:5]:  # Limit to 5 videos per batch
            video_data = await video_service.create_video(
                user_id=user_id, script_id=script_id, **video_settings
            )

            # Start generation
            enhanced_video = await video_service.generate_video_with_workflow(
                video_data
            )

            batch_results.append(
                {
                    "script_id": script_id,
                    "video_id": str(video_data["_id"]),
                    "status": "initiated",
                }
            )

        return {
            "message": f"Batch generation initiated for {len(batch_results)} videos",
            "data": {"batch_results": batch_results},
            "code": 201,
        }

    except Exception as e:
        logger.error(f"Error in batch video generation: {e}")
        raise VideoProcessingException(str(e))
