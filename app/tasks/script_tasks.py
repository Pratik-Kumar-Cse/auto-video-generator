"""
Script generation Celery tasks
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, Any

from app.core.celery_app import celery_app
from app.core.config import settings
from app.core.database import get_database
from app.core.redis_client import RedisService
from app.services.script_service import ScriptService
from app.constant.enum.script_enum import ScriptStatus, ScriptType
from app.core.exceptions import ScriptProcessingException
from app.loggers.logger import get_logger

logger = get_logger(__name__)


async def update_task_progress(
    task_id: str, 
    progress: int, 
    message: str,
    redis_service: RedisService
):
    """Update task progress in Redis"""
    try:
        progress_data = {
            "progress": progress,
            "message": message,
            "updated_at": datetime.utcnow().isoformat()
        }
        await redis_service.set(
            f"task_progress:{task_id}",
            json.dumps(progress_data),
            expire=3600
        )
    except Exception as e:
        logger.error(f"Failed to update task progress: {e}", exc_info=True)


async def generate_script_content(
    script_type: ScriptType,
    request_data: Dict[str, Any]
) -> Dict[str, Any]:
    """Generate script content based on type and request data"""
    
    # Simulate AI script generation
    # In a real implementation, this would call OpenAI, Claude, or other AI services
    
    if script_type == ScriptType.TOPIC:
        topic = request_data.get("topic", "Unknown Topic")
        duration = request_data.get("duration", 60)
        
        # Generate topic-based script
        content = {
            "title": f"Script about {topic}",
            "description": f"A comprehensive script covering {topic}",
            "segments": [
                {
                    "type": "introduction",
                    "content": f"Welcome to our discussion about {topic}.",
                    "duration": 10,
                    "order": 1
                },
                {
                    "type": "main_content",
                    "content": f"Let's dive deep into {topic} and explore its key aspects.",
                    "duration": duration - 20,
                    "order": 2
                },
                {
                    "type": "conclusion",
                    "content": f"Thank you for learning about {topic} with us.",
                    "duration": 10,
                    "order": 3
                }
            ],
            "word_count": len(f"Welcome to our discussion about {topic}. Let's dive deep into {topic} and explore its key aspects. Thank you for learning about {topic} with us.".split()),
            "estimated_duration": duration
        }
        
    elif script_type == ScriptType.VIDEO:
        video_url = request_data.get("video_url", "")
        
        # Generate video-based script
        content = {
            "title": "Script from Video Analysis",
            "description": f"Script generated from video: {video_url}",
            "segments": [
                {
                    "type": "introduction",
                    "content": "This script is based on video content analysis.",
                    "duration": 15,
                    "order": 1
                },
                {
                    "type": "main_content",
                    "content": "Here's the main content extracted from the video.",
                    "duration": 120,
                    "order": 2
                },
                {
                    "type": "conclusion",
                    "content": "That concludes our video-based script.",
                    "duration": 15,
                    "order": 3
                }
            ],
            "word_count": 50,
            "estimated_duration": 150
        }
        
    elif script_type == ScriptType.BLOG:
        blog_url = request_data.get("blog_url", "")
        
        # Generate blog-based script
        content = {
            "title": "Script from Blog Content",
            "description": f"Script generated from blog: {blog_url}",
            "segments": [
                {
                    "type": "introduction",
                    "content": "This script is based on blog content.",
                    "duration": 10,
                    "order": 1
                },
                {
                    "type": "main_content",
                    "content": "Here's the main content from the blog post.",
                    "duration": 90,
                    "order": 2
                },
                {
                    "type": "conclusion",
                    "content": "That's our blog-based script summary.",
                    "duration": 10,
                    "order": 3
                }
            ],
            "word_count": 40,
            "estimated_duration": 110
        }
        
    else:  # CUSTOM
        custom_content = request_data.get("custom_content", "")
        
        # Generate custom script
        content = {
            "title": "Custom Script",
            "description": "Script from custom content",
            "segments": [
                {
                    "type": "main_content",
                    "content": custom_content or "Custom script content",
                    "duration": 60,
                    "order": 1
                }
            ],
            "word_count": len((custom_content or "Custom script content").split()),
            "estimated_duration": 60
        }
    
    return content


@celery_app.task(bind=True, name="generate_script")
def generate_script_task(
    self, 
    script_id: str, 
    user_id: str, 
    request_data: Dict[str, Any]
):
    """Generate script content task"""
    
    async def _generate_script():
        # Initialize services
        db = await get_database()
        script_service = ScriptService(db)
        redis_service = RedisService()
        
        try:
            task_id = self.request.id
            logger.info(
                f"Starting script generation task: {task_id} "
                f"for script {script_id}"
            )
            
            # Update progress: Starting
            await update_task_progress(
                task_id, 0, "Starting script generation", redis_service
            )
            
            # Update script status
            await script_service.update_script_status(
                script_id, ScriptStatus.PROCESSING, "Generating content"
            )
            
            # Update progress: Analyzing request
            await update_task_progress(
                task_id, 20, "Analyzing request parameters", redis_service
            )
            
            # Get script type
            script_type = ScriptType(request_data.get("type"))
            
            # Update progress: Generating content
            await update_task_progress(
                task_id, 40, "Generating script content", redis_service
            )
            
            # Generate script content
            content = await generate_script_content(script_type, request_data)
            
            # Update progress: Processing content
            await update_task_progress(
                task_id, 70, "Processing generated content", redis_service
            )
            
            # Update script with generated content
            update_data = {
                "content": content,
                "status": ScriptStatus.COMPLETED.value,
                "completed_at": datetime.utcnow(),
                "processing_time": (datetime.utcnow() - datetime.fromisoformat(
                    request_data.get("created_at", datetime.utcnow().isoformat())
                )).total_seconds()
            }
            
            await script_service.update_script(script_id, update_data)
            
            # Update progress: Completed
            await update_task_progress(
                task_id, 100, "Script generation completed", redis_service
            )
            
            logger.info(
                f"Script generation completed successfully: {script_id}"
            )
            return {
                "status": "success",
                "script_id": script_id,
                "message": "Script generated successfully"
            }
            
        except Exception as e:
            logger.error(
                f"Script generation failed for {script_id}: {e}", exc_info=True
            )
            # Update script status to failed
            await script_service.update_script_status(
                script_id,
                ScriptStatus.FAILED,
                f"Generation failed: {str(e)}"
            )
            
            # Update progress: Failed
            await update_task_progress(
                self.request.id, 0, f"Generation failed: {str(e)}",
                redis_service
            )
            
            raise ScriptProcessingException(
                f"Script generation failed: {str(e)}"
            )
        
        finally:
            # Database connection is managed globally, no need to close here
            pass
            await redis_service.close()
    
    # Run async function
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(_generate_script())
    finally:
        loop.close()


@celery_app.task(bind=True, name="regenerate_script")
def regenerate_script_task(
    self, 
    script_id: str, 
    user_id: str, 
    request_data: Dict[str, Any]
):
    """Regenerate script content task"""
    
    async def _regenerate_script():
        # Initialize services
        db = await get_database()
        script_service = ScriptService(db)
        redis_service = RedisService()
        
        try:
            task_id = self.request.id
            
            # Get existing script
            script = await script_service.get_script_by_id(script_id)
            
            # Update progress: Starting
            await update_task_progress(
                task_id, 0, "Starting script regeneration", redis_service
            )
            
            # Update script status
            await script_service.update_script_status(
                script_id, ScriptStatus.PROCESSING, "Regenerating content"
            )
            
            # Merge request data with existing script data
            generation_data = {
                "type": script["type"],
                **script.get("generation_params", {}),
                **request_data
            }
            
            # Update progress: Generating new content
            await update_task_progress(
                task_id, 50, "Generating new script content", redis_service
            )
            
            # Generate new content
            script_type = ScriptType(generation_data.get("type"))
            new_content = await generate_script_content(script_type, generation_data)
            
            # Update script with new content
            update_data = {
                "content": new_content,
                "status": ScriptStatus.COMPLETED.value,
                "regenerated_at": datetime.utcnow(),
                "regeneration_count": script.get("regeneration_count", 0) + 1
            }
            
            await script_service.update_script(script_id, update_data)
            
            # Update progress: Completed
            await update_task_progress(
                task_id, 100, "Script regeneration completed", redis_service
            )
            
            return {
                "status": "success",
                "script_id": script_id,
                "message": "Script regenerated successfully"
            }
            
        except Exception as e:
            # Update script status to failed
            await script_service.update_script_status(
                script_id, 
                ScriptStatus.FAILED, 
                f"Regeneration failed: {str(e)}"
            )
            
            # Update progress: Failed
            await update_task_progress(
                self.request.id, 0, f"Regeneration failed: {str(e)}", redis_service
            )
            
            raise ScriptProcessingException(f"Script regeneration failed: {str(e)}")
        
        finally:
            # Database connection is managed globally, no need to close here
            pass
            await redis_service.close()
    
    # Run async function
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(_regenerate_script())
    finally:
        loop.close()


@celery_app.task(bind=True, name="cleanup_failed_scripts")
def cleanup_failed_scripts_task(self, max_age_hours: int = 24):
    """Clean up failed scripts older than specified hours"""
    
    async def _cleanup_failed_scripts():
        db = await get_database()
        script_service = ScriptService(db)
        
        try:
            # Calculate cutoff time
            cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)
            
            # Find and delete failed scripts
            deleted_count = await script_service.cleanup_failed_scripts(cutoff_time)
            
            return {
                "status": "success",
                "deleted_count": deleted_count,
                "message": f"Cleaned up {deleted_count} failed scripts"
            }
            
        except Exception as e:
            raise Exception(f"Cleanup failed: {str(e)}")
        
        finally:
            # Database connection is managed globally, no need to close here
            pass
    
    # Run async function
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(_cleanup_failed_scripts())
    finally:
        loop.close()