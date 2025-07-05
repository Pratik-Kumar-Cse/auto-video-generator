"""
Celery tasks for video processing
"""

import asyncio
from typing import Dict, Any, Optional
from celery import current_task
from celery.exceptions import Retry

from app.core.celery_app import celery_app
from app.core.database import get_database
from app.core.redis_client import get_redis_service
from app.services.video_service import VideoService
from app.models.video import VideoStatus
from app.core.exceptions import VideoProcessingException


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def generate_video_task(self, video_id: str, user_id: str) -> Dict[str, Any]:
    """
    Celery task for video generation
    """
    try:
        # Update task status
        current_task.update_state(
            state='PROGRESS',
            meta={'current': 0, 'total': 100, 'status': 'Starting video generation'}
        )

        # Run async video generation
        result = asyncio.run(_generate_video_async(video_id, user_id, self))
        
        return {
            'status': 'SUCCESS',
            'video_id': video_id,
            'result': result
        }

    except Exception as exc:
        # Update video status to failed
        asyncio.run(_update_video_status_async(video_id, VideoStatus.FAILED, str(exc)))
        
        # Retry logic
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))
        
        return {
            'status': 'FAILURE',
            'video_id': video_id,
            'error': str(exc)
        }


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def generate_workflow_video_task(
    self, 
    video_id: str, 
    user_id: str, 
    workflow_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Celery task for workflow video generation
    """
    try:
        # Update task status
        current_task.update_state(
            state='PROGRESS',
            meta={'current': 0, 'total': 100, 'status': 'Starting workflow video generation'}
        )

        # Run async workflow video generation
        result = asyncio.run(_generate_workflow_video_async(
            video_id, user_id, workflow_data, self
        ))
        
        return {
            'status': 'SUCCESS',
            'video_id': video_id,
            'result': result
        }

    except Exception as exc:
        # Update video status to failed
        asyncio.run(_update_video_status_async(video_id, VideoStatus.FAILED, str(exc)))
        
        # Retry logic
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))
        
        return {
            'status': 'FAILURE',
            'video_id': video_id,
            'error': str(exc)
        }


@celery_app.task(bind=True)
def upload_video_task(
    self, 
    video_id: str, 
    upload_domain: str, 
    user_id: str
) -> Dict[str, Any]:
    """
    Celery task for video upload
    """
    try:
        # Update task status
        current_task.update_state(
            state='PROGRESS',
            meta={'current': 0, 'total': 100, 'status': f'Uploading to {upload_domain}'}
        )

        # Run async video upload
        result = asyncio.run(_upload_video_async(
            video_id, upload_domain, user_id, self
        ))
        
        return {
            'status': 'SUCCESS',
            'video_id': video_id,
            'upload_domain': upload_domain,
            'result': result
        }

    except Exception as exc:
        return {
            'status': 'FAILURE',
            'video_id': video_id,
            'upload_domain': upload_domain,
            'error': str(exc)
        }


@celery_app.task
def cleanup_expired_videos() -> Dict[str, Any]:
    """
    Periodic task to cleanup expired videos
    """
    try:
        result = asyncio.run(_cleanup_expired_videos_async())
        return {
            'status': 'SUCCESS',
            'cleaned_count': result
        }
    except Exception as exc:
        return {
            'status': 'FAILURE',
            'error': str(exc)
        }


# Async helper functions

async def _generate_video_async(
    video_id: str, 
    user_id: str, 
    task_instance
) -> Dict[str, Any]:
    """
    Async video generation logic
    """
    db = await get_database()
    redis_service = await get_redis_service()
    video_service = VideoService(db)

    try:
        # Update video status to processing
        await video_service.update_video_status(
            video_id, 
            VideoStatus.PROCESSING,
            "Video generation started"
        )

        # Get video data
        video_data = await video_service.get_video_by_id(video_id)
        
        # Update progress
        task_instance.update_state(
            state='PROGRESS',
            meta={'current': 10, 'total': 100, 'status': 'Preparing video data'}
        )

        # Simulate video generation steps
        steps = [
            (20, "Generating script audio"),
            (40, "Creating avatar video"),
            (60, "Combining audio and video"),
            (80, "Adding effects and transitions"),
            (90, "Rendering final video"),
            (100, "Video generation completed")
        ]

        for progress, status in steps:
            # Simulate processing time
            await asyncio.sleep(2)
            
            task_instance.update_state(
                state='PROGRESS',
                meta={'current': progress, 'total': 100, 'status': status}
            )

        # Simulate video file generation
        video_url = f"https://storage.example.com/videos/{video_id}.mp4"
        video_url_1080p = f"https://storage.example.com/videos/{video_id}_1080p.mp4"
        thumbnail_url = f"https://storage.example.com/thumbnails/{video_id}.jpg"

        # Update video with generated URLs
        await video_service.set_video_link(video_id, video_url, video_url_1080p)
        await video_service.set_video_thumbnail(video_id, thumbnail_url)
        
        # Update status to completed
        await video_service.update_video_status(
            video_id, 
            VideoStatus.COMPLETED,
            "Video generation completed successfully"
        )

        # Cache video data
        await redis_service.set(
            f"video:{video_id}", 
            video_url, 
            expire=3600
        )

        return {
            'video_url': video_url,
            'video_url_1080p': video_url_1080p,
            'thumbnail_url': thumbnail_url
        }

    except Exception as e:
        await video_service.update_video_status(
            video_id, 
            VideoStatus.FAILED,
            f"Video generation failed: {str(e)}"
        )
        raise VideoProcessingException(f"Video generation failed: {str(e)}")


async def _generate_workflow_video_async(
    video_id: str, 
    user_id: str, 
    workflow_data: Dict[str, Any],
    task_instance
) -> Dict[str, Any]:
    """
    Async workflow video generation logic
    """
    db = await get_database()
    video_service = VideoService(db)

    try:
        # Update video status to processing
        await video_service.update_video_status(
            video_id, 
            VideoStatus.PROCESSING,
            "Workflow video generation started"
        )

        # Extract workflow parameters
        topic = workflow_data.get('topic')
        video_type = workflow_data.get('video_type')
        script_type = workflow_data.get('script_type')
        
        # Update progress
        task_instance.update_state(
            state='PROGRESS',
            meta={'current': 10, 'total': 100, 'status': 'Processing workflow data'}
        )

        # Workflow-specific steps
        steps = [
            (20, f"Generating script for topic: {topic}"),
            (35, f"Creating {video_type} video structure"),
            (50, "Processing script content"),
            (65, "Generating avatar video"),
            (80, "Combining elements"),
            (95, "Finalizing workflow video"),
            (100, "Workflow video generation completed")
        ]

        for progress, status in steps:
            await asyncio.sleep(3)  # Longer processing for workflow
            
            task_instance.update_state(
                state='PROGRESS',
                meta={'current': progress, 'total': 100, 'status': status}
            )

        # Generate video URLs
        video_url = f"https://storage.example.com/workflow-videos/{video_id}.mp4"
        video_url_1080p = f"https://storage.example.com/workflow-videos/{video_id}_1080p.mp4"
        thumbnail_url = f"https://storage.example.com/workflow-thumbnails/{video_id}.jpg"

        # Update video with generated URLs
        await video_service.set_video_link(video_id, video_url, video_url_1080p)
        await video_service.set_video_thumbnail(video_id, thumbnail_url)
        
        # Update status to completed
        await video_service.update_video_status(
            video_id, 
            VideoStatus.COMPLETED,
            "Workflow video generation completed successfully"
        )

        return {
            'video_url': video_url,
            'video_url_1080p': video_url_1080p,
            'thumbnail_url': thumbnail_url,
            'workflow_type': video_type
        }

    except Exception as e:
        await video_service.update_video_status(
            video_id, 
            VideoStatus.FAILED,
            f"Workflow video generation failed: {str(e)}"
        )
        raise VideoProcessingException(f"Workflow video generation failed: {str(e)}")


async def _upload_video_async(
    video_id: str, 
    upload_domain: str, 
    user_id: str,
    task_instance
) -> Dict[str, Any]:
    """
    Async video upload logic
    """
    db = await get_database()
    video_service = VideoService(db)

    try:
        # Get video data
        video_data = await video_service.get_video_by_id(video_id)
        video_url = video_data.get('link')
        
        if not video_url:
            raise VideoProcessingException("Video URL not found")

        # Update progress
        task_instance.update_state(
            state='PROGRESS',
            meta={'current': 20, 'total': 100, 'status': f'Preparing upload to {upload_domain}'}
        )

        # Simulate upload steps
        steps = [
            (40, f"Connecting to {upload_domain} API"),
            (60, f"Uploading video to {upload_domain}"),
            (80, f"Processing upload on {upload_domain}"),
            (100, f"Upload to {upload_domain} completed")
        ]

        for progress, status in steps:
            await asyncio.sleep(2)
            
            task_instance.update_state(
                state='PROGRESS',
                meta={'current': progress, 'total': 100, 'status': status}
            )

        # Simulate successful upload
        upload_id = f"{upload_domain}_{video_id}_{user_id}"
        upload_url = f"https://{upload_domain}.com/watch?v={upload_id}"

        return {
            'upload_id': upload_id,
            'upload_url': upload_url,
            'platform': upload_domain
        }

    except Exception as e:
        raise VideoProcessingException(f"Video upload failed: {str(e)}")


async def _update_video_status_async(
    video_id: str, 
    status: VideoStatus, 
    message: Optional[str] = None
) -> None:
    """
    Helper to update video status
    """
    try:
        db = await get_database()
        video_service = VideoService(db)
        await video_service.update_video_status(video_id, status, message)
    except Exception:
        # Log error but don't raise to avoid masking original error
        pass


async def _cleanup_expired_videos_async() -> int:
    """
    Cleanup expired videos
    """
    db = await get_database()
    video_service = VideoService(db)
    
    # This would implement actual cleanup logic
    # For now, return 0 as placeholder
    return 0