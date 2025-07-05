"""
Script API endpoints for FastAPI Video Generation Service
Enhanced with comprehensive functionality
"""

import json
import logging
from typing import Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse

from app.core.database import get_database
from app.core.exceptions import (
    BadRequestException,
    ScriptNotFoundException,
    ScriptProcessingException,
)
from app.models.common import PaginationParams, SuccessResponse
from app.models.script import (
    GenerateScriptRequest,
    RegenerateScriptRequest,
    ScriptCreate,
    ScriptListResponse,
    ScriptResponse,
    ScriptUpdate,
)
from app.services.script_service import ScriptService

logger = logging.getLogger(__name__)

router = APIRouter()


class ScriptGenerationManager:
    @classmethod
    async def initiate_script_generation(
        cls, user_id: str, input_data: dict, db
    ) -> str:
        """
        Initiate async script generation and return a task ID
        """
        script_service = ScriptService(db)

        # Use the enhanced async generation method
        task_id = await script_service.generate_script_async(
            user_id=user_id,
            topic=input_data["topic"],
            video_type=input_data["video_type"],
            keywords=input_data.get("keywords", {}),
            input_type=input_data["input_type"],
            add_brand=input_data.get("add_brand", False),
            music_media_id=input_data.get("music_media_id"),
            link=input_data.get("link"),
            video_link=input_data.get("video_link"),
            client_id=input_data.get("client_id"),
        )

        return task_id


@router.post("/generate", response_model=dict)
async def generate_script(
    request: GenerateScriptRequest,
    db=Depends(get_database),
):
    """
    Initiate script generation task
    Returns a task ID for tracking progress
    """
    try:
        # Validate input
        if request.input_type in ["VIDEO", "BLOG"] and not request.link:
            raise BadRequestException(
                "Link is required for video and blog input types"
            )

        # Use async method to initiate script generation
        # Use a default user_id since auth is removed
        task_id = await ScriptGenerationManager.initiate_script_generation(
            "default_user", request.dict(), db
        )

        return {"task_id": task_id}

    except Exception as e:
        logger.error(f"Error generating script: {e}")
        raise ScriptProcessingException(str(e))


@router.get("/stream/{task_id}")
async def stream_script_generation(
    task_id: str,
    db=Depends(get_database),
):
    """
    Server-Sent Events endpoint for script generation progress
    """
    try:
        script_service = ScriptService(db)

        def event_stream():
            try:
                # Check if script is already completed
                script_data = script_service.get_script_using_task_id(task_id)
                if script_data:
                    chunk = {
                        "data": {
                            "index": None,
                            "content": None,
                            "script": script_data,
                            "status": "completed",
                        },
                    }
                    yield f"data: {json.dumps(chunk)}\n\n"
                    return

                # Stream progress updates
                from app.core.redis_client import redis_service

                queue_key = f"script_queue:{task_id}"

                while True:
                    try:
                        # Get message from queue
                        message = redis_service.lpop(queue_key)
                        if message == "[DONE]":
                            chunk = {"data": message}
                            yield f"data: {json.dumps(chunk)}\n\n"
                            yield "data: [DONE]\n\n"
                            break
                        elif message:
                            chunk = {"data": message}
                            yield f"data: {json.dumps(chunk)}\n\n"
                        else:
                            # Send keepalive
                            yield ": keepalive\n\n"
                            import time

                            time.sleep(1)
                    except Exception as e:
                        logger.error(f"Streaming error: {e}")
                        break

            except Exception as e:
                logger.error(f"Stream error: {e}", exc_info=True)
                yield f"data: {json.dumps({'error': str(e)})}\n\n"

        return StreamingResponse(
            event_stream(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    except Exception as e:
        logger.error(f"Error streaming script: {e}")
        raise ScriptProcessingException(str(e))


@router.put("/regenerate/{script_id}", response_model=ScriptResponse)
async def regenerate_script(
    script_id: str,
    request: RegenerateScriptRequest,
    db=Depends(get_database),
):
    """
    Regenerate a script using new parameters
    """
    try:
        user_id = "default_user"  # Use default since auth is removed
        script_service = ScriptService(db)

        script_data = await script_service.get_script_of_user(
            user_id, script_id
        )
        if not script_data:
            raise ScriptNotFoundException(script_id)

        script = await script_service.regenerate_script(
            user_id,
            script_data,
            request.topic,
            request.video_type,
            request.link,
            request.keywords,
        )

        if not script:
            raise BadRequestException("Script regeneration failed")

        return {
            "message": "Script regenerated successfully",
            "data": script,
            "code": 200,
        }

    except Exception as e:
        logger.error(f"Error regenerating script: {e}")
        raise ScriptProcessingException(str(e))


@router.get("/{script_id}", response_model=ScriptResponse)
async def get_script(
    script_id: str,
    db=Depends(get_database),
):
    """
    Get script by ID
    """
    try:
        user_id = "default_user"  # Use default since auth is removed
        script_service = ScriptService(db)

        if not script_id:
            raise BadRequestException("Script ID is required")

        script_data = await script_service.get_script_of_user(
            user_id, script_id
        )
        if not script_data:
            raise ScriptNotFoundException(script_id)

        return {
            "message": "Script fetched successfully",
            "data": script_data,
            "code": 200,
        }

    except Exception as e:
        logger.error(f"Error getting script: {e}")
        raise ScriptProcessingException(str(e))


@router.put("/{script_id}", response_model=ScriptResponse)
async def update_script(
    script_id: str,
    request: ScriptUpdate,
    db=Depends(get_database),
):
    """
    Update script content
    """
    try:
        user_id = "default_user"  # Use default since auth is removed
        script_service = ScriptService(db)

        if not script_id:
            raise BadRequestException("Script ID is required")

        updated_script = await script_service.update_script(
            user_id, script_id, request.dict(exclude_unset=True)
        )

        if not updated_script:
            raise ScriptNotFoundException(script_id)

        return {
            "message": "Script updated successfully",
            "data": updated_script,
            "code": 200,
        }

    except Exception as e:
        logger.error(f"Error updating script: {e}")
        raise ScriptProcessingException(str(e))


@router.delete("/{script_id}", response_model=SuccessResponse)
async def delete_script(
    script_id: str,
    db=Depends(get_database),
):
    """
    Delete script by ID
    """
    try:
        user_id = "default_user"  # Use default since auth is removed
        script_service = ScriptService(db)

        if not script_id:
            raise BadRequestException("Script ID is required")

        success = await script_service.delete_script(user_id, script_id)
        if not success:
            raise ScriptNotFoundException(script_id)

        return {"message": "Script deleted successfully", "code": 200}

    except Exception as e:
        logger.error(f"Error deleting script: {e}")
        raise ScriptProcessingException(str(e))


@router.get("/", response_model=ScriptListResponse)
async def get_all_scripts(
    pagination: PaginationParams = Depends(),
    filter_name: Optional[str] = Query(None, alias="filter"),
    video_type: Optional[str] = Query(None),
    input_type: Optional[str] = Query(None),
    sort_by: str = Query("created_at"),
    sort_order: int = Query(-1),
    db=Depends(get_database),
):
    """
    Get all scripts for user with enhanced filtering and sorting
    """
    try:
        user_id = "default_user"  # Use default since auth is removed
        script_service = ScriptService(db)

        scripts, total_count = await script_service.get_all_scripts_by_user(
            user_id=user_id,
            page=pagination.page,
            per_page=pagination.per_page,
            filter_name=filter_name,
            video_type=video_type,
            input_type=input_type,
            sort_by=sort_by,
            sort_order=sort_order,
        )

        if scripts is None:
            raise ScriptProcessingException("Error retrieving scripts")

        response_data = {
            "scripts": scripts,
            "page": pagination.page,
            "limit": pagination.per_page,
            "total_count": total_count,
            "total_pages": -(-total_count // pagination.per_page),
        }

        return {
            "message": "Scripts fetched successfully",
            "data": response_data,
            "code": 200,
        }

    except Exception as e:
        logger.error(f"Error getting all scripts: {e}")
        raise ScriptProcessingException(str(e))


@router.get("/trending-topics", response_model=SuccessResponse)
async def get_trending_topics(
    limit: int = Query(10, ge=1, le=50),
    db=Depends(get_database),
):
    """
    Get trending topics for script generation
    """
    try:
        script_service = ScriptService(db)
        topics = await script_service.get_trending_topics(limit)

        return {
            "message": "Trending topics fetched successfully",
            "data": {"topics": topics},
            "code": 200,
        }

    except Exception as e:
        logger.error(f"Error getting trending topics: {e}")
        raise ScriptProcessingException(str(e))


@router.post("/create", response_model=ScriptResponse)
async def create_script(
    request: ScriptCreate,
    db=Depends(get_database),
):
    """
    Create a new script manually
    """
    try:
        user_id = "default_user"  # Use default since auth is removed
        script_service = ScriptService(db)

        script_data = await script_service.create_script(
            user_id=user_id,
            title=request.topic,
            content="",  # Will be filled by user
            topic=request.topic,
            video_type=request.video_type,
            keywords=request.keywords,
            input_type=request.input_type,
            metadata={
                "add_brand": request.add_brand,
                "music_media_id": request.music_media_id,
                "link": request.link,
                "video_link": request.video_link,
            },
        )

        return {
            "message": "Script created successfully",
            "data": script_data,
            "code": 201,
        }

    except Exception as e:
        logger.error(f"Error creating script: {e}")
        raise ScriptProcessingException(str(e))
