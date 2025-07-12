"""
Event Routes for Script Generation and Video Generation
Dedicated SSE endpoints for real-time event monitoring
"""

import json
import time
from typing import Optional, Dict, Any

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse

from app.core.exceptions import BadRequestException
from app.helper.sse_manager import sse_manager
from app.services.sse_service import sse_service
from app.models.sse import EventTypes
from app.models.common import SuccessResponse
from app.loggers.logger import get_logger

logger = get_logger(__name__)

router = APIRouter()


@router.get("/script-generation/{task_id}")
async def listen_script_generation_events(
    task_id: str,
    client_id: str = Query(..., description="Client ID for SSE connection"),
    timeout: int = Query(300, description="Connection timeout in seconds"),
):
    """
    Listen to script generation events for a specific task

    Args:
        task_id: Script generation task ID
        client_id: Client identifier for SSE connection
        timeout: Connection timeout in seconds

    Returns:
        StreamingResponse with script generation events
    """
    try:
        logger.info(
            f"Script generation event listener started: "
            f"task_id={task_id}, client_id={client_id}"
        )

        def event_stream():
            start_time = time.time()

            try:
                while True:
                    # Check timeout
                    if time.time() - start_time > timeout:
                        logger.info(
                            f"Script generation event stream timeout for "
                            f"task {task_id}"
                        )
                        yield "event: timeout\n"
                        timeout_data = json.dumps({"message": "Connection timeout"})
                        yield f"data: {timeout_data}\n\n"
                        break

                    # Check if client is still connected
                    if not sse_manager.is_client_connected(client_id):
                        logger.warning(
                            f"Client {client_id} disconnected during script "
                            f"generation monitoring"
                        )
                        break

                    # Send keep-alive every 30 seconds
                    yield f"event: {EventTypes.KEEP_ALIVE}\n"
                    keepalive_data = json.dumps(
                        {"task_id": task_id, "timestamp": time.time()}
                    )
                    yield f"data: {keepalive_data}\n\n"

                    time.sleep(30)

            except Exception as e:
                logger.error(
                    f"Error in script generation event stream: {e}", exc_info=True
                )
                yield f"event: {EventTypes.ERROR}\n"
                error_data = json.dumps({"error": str(e), "task_id": task_id})
                yield f"data: {error_data}\n\n"

        return StreamingResponse(
            event_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",
                "Connection": "keep-alive",
                "Content-Type": "text/event-stream",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Cache-Control",
            },
        )

    except Exception as e:
        logger.error(
            f"Error setting up script generation event listener: {e}", exc_info=True
        )
        raise HTTPException(
            status_code=500, detail="Failed to setup script generation event listener"
        )


@router.get("/video-generation/{video_id}")
async def listen_video_generation_events(
    video_id: str,
    client_id: str = Query(..., description="Client ID for SSE connection"),
    timeout: int = Query(600, description="Connection timeout in seconds"),
):
    """
    Listen to video generation events for a specific video

    Args:
        video_id: Video generation ID
        client_id: Client identifier for SSE connection
        timeout: Connection timeout in seconds

    Returns:
        StreamingResponse with video generation events
    """
    try:
        logger.info(
            f"Video generation event listener started: "
            f"video_id={video_id}, client_id={client_id}"
        )

        def event_stream():
            start_time = time.time()

            try:
                while True:
                    # Check timeout
                    if time.time() - start_time > timeout:
                        logger.info(
                            f"Video generation event stream timeout for "
                            f"video {video_id}"
                        )
                        yield "event: timeout\n"
                        timeout_data = json.dumps({"message": "Connection timeout"})
                        yield f"data: {timeout_data}\n\n"
                        break

                    # Check if client is still connected
                    if not sse_manager.is_client_connected(client_id):
                        logger.warning(
                            f"Client {client_id} disconnected during video "
                            f"generation monitoring"
                        )
                        break

                    # Send keep-alive every 30 seconds
                    yield f"event: {EventTypes.KEEP_ALIVE}\n"
                    keepalive_data = json.dumps(
                        {"video_id": video_id, "timestamp": time.time()}
                    )
                    yield f"data: {keepalive_data}\n\n"

                    time.sleep(30)

            except Exception as e:
                logger.error(
                    f"Error in video generation event stream: {e}", exc_info=True
                )
                yield f"event: {EventTypes.ERROR}\n"
                error_data = json.dumps({"error": str(e), "video_id": video_id})
                yield f"data: {error_data}\n\n"

        return StreamingResponse(
            event_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",
                "Connection": "keep-alive",
                "Content-Type": "text/event-stream",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Cache-Control",
            },
        )

    except Exception as e:
        logger.error(
            f"Error setting up video generation event listener: {e}", exc_info=True
        )
        raise HTTPException(
            status_code=500, detail="Failed to setup video generation event listener"
        )


@router.post("/script-generation/{task_id}/update")
async def send_script_generation_update(
    task_id: str,
    client_id: str = Query(..., description="Target client ID"),
    status: str = Query(..., description="Current status"),
    progress: Optional[float] = Query(None, description="Progress percentage"),
    message: str = Query("", description="Status message"),
    content: Optional[str] = Query(None, description="Generated content"),
):
    """
    Send script generation update to listening clients

    Args:
        task_id: Script generation task ID
        client_id: Target client ID
        status: Current generation status
        progress: Progress percentage (0-100)
        message: Status message
        content: Generated content (if any)

    Returns:
        Success response
    """
    try:
        logger.info(
            f"Sending script generation update: task_id={task_id}, "
            f"status={status}, progress={progress}"
        )

        # Validate client connection
        if not sse_manager.is_client_connected(client_id):
            raise BadRequestException(f"Client {client_id} is not connected")

        # Send update via SSE service
        sse_service.send_script_generation_update(
            client_id=client_id,
            task_id=task_id,
            status=status,
            progress=progress,
            content=content,
            message=message,
        )

        logger.info(f"Script generation update sent successfully: task_id={task_id}")

        return SuccessResponse(
            message=f"Script generation update sent for task {task_id}",
            code=200,
        )

    except BadRequestException as e:
        logger.error(f"Bad request in script generation update: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error sending script generation update: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail="Failed to send script generation update"
        )


@router.post("/video-generation/{video_id}/update")
async def send_video_generation_update(
    video_id: str,
    client_id: str = Query(..., description="Target client ID"),
    status: str = Query(..., description="Current status"),
    progress: Optional[float] = Query(None, description="Progress percentage"),
    message: str = Query("", description="Status message"),
    metadata: Optional[Dict[str, Any]] = None,
):
    """
    Send video generation update to listening clients

    Args:
        video_id: Video generation ID
        client_id: Target client ID
        status: Current generation status
        progress: Progress percentage (0-100)
        message: Status message
        metadata: Additional metadata

    Returns:
        Success response
    """
    try:
        logger.info(
            f"Sending video generation update: video_id={video_id}, "
            f"status={status}, progress={progress}"
        )

        # Validate client connection
        if not sse_manager.is_client_connected(client_id):
            raise BadRequestException(f"Client {client_id} is not connected")

        # Send update via SSE service
        sse_service.send_video_processing_update(
            client_id=client_id,
            video_id=video_id,
            status=status,
            progress=progress,
            message=message,
            metadata=metadata or {},
        )

        logger.info(f"Video generation update sent successfully: video_id={video_id}")

        return SuccessResponse(
            message=f"Video generation update sent for video {video_id}",
            code=200,
        )

    except BadRequestException as e:
        logger.error(f"Bad request in video generation update: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error sending video generation update: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail="Failed to send video generation update"
        )


@router.get("/script-generation/{task_id}/status")
async def get_script_generation_status(
    task_id: str,
):
    """
    Get current status of script generation task

    Args:
        task_id: Script generation task ID

    Returns:
        Current task status information
    """
    try:
        logger.debug(f"Getting script generation status for task: {task_id}")

        # This would typically query your database or cache
        # For now, return a mock response
        status_info = {
            "task_id": task_id,
            "status": "processing",
            "progress": 50.0,
            "message": "Generating script content...",
            "created_at": time.time(),
            "updated_at": time.time(),
        }

        return {
            "message": "Script generation status retrieved",
            "data": status_info,
            "code": 200,
        }

    except Exception as e:
        logger.error(f"Error getting script generation status: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail="Failed to get script generation status"
        )


@router.get("/video-generation/{video_id}/status")
async def get_video_generation_status(
    video_id: str,
):
    """
    Get current status of video generation

    Args:
        video_id: Video generation ID

    Returns:
        Current video generation status information
    """
    try:
        logger.debug(f"Getting video generation status for video: {video_id}")

        # This would typically query your database or cache
        # For now, return a mock response
        status_info = {
            "video_id": video_id,
            "status": "processing",
            "progress": 30.0,
            "message": "Processing video content...",
            "created_at": time.time(),
            "updated_at": time.time(),
        }

        return {
            "message": "Video generation status retrieved",
            "data": status_info,
            "code": 200,
        }

    except Exception as e:
        logger.error(f"Error getting video generation status: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail="Failed to get video generation status"
        )


@router.post("/script-generation/{task_id}/complete")
async def complete_script_generation(
    task_id: str,
    script_data: Dict[str, Any],
    client_id: str = Query(..., description="Target client ID"),
    message: str = Query("Script generation completed successfully"),
):
    """
    Mark script generation as completed and send final event

    Args:
        task_id: Script generation task ID
        client_id: Target client ID
        script_data: Complete script data
        message: Completion message

    Returns:
        Success response
    """
    try:
        logger.info(f"Completing script generation: task_id={task_id}")

        # Validate client connection
        if not sse_manager.is_client_connected(client_id):
            raise BadRequestException(f"Client {client_id} is not connected")

        # Send completion event
        sse_service.send_completion_event(
            client_id=client_id,
            task_id=task_id,
            task_type="script_generation",
            result=script_data,
            message=message,
        )

        logger.info(f"Script generation completed successfully: task_id={task_id}")

        return SuccessResponse(
            message=f"Script generation completed for task {task_id}",
            code=200,
        )

    except BadRequestException as e:
        logger.error(f"Bad request in script generation completion: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error completing script generation: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail="Failed to complete script generation"
        )


@router.post("/video-generation/{video_id}/complete")
async def complete_video_generation(
    video_id: str,
    video_data: Dict[str, Any],
    client_id: str = Query(..., description="Target client ID"),
    message: str = Query("Video generation completed successfully"),
):
    """
    Mark video generation as completed and send final event

    Args:
        video_id: Video generation ID
        client_id: Target client ID
        video_data: Complete video data
        message: Completion message

    Returns:
        Success response
    """
    try:
        logger.info(f"Completing video generation: video_id={video_id}")

        # Validate client connection
        if not sse_manager.is_client_connected(client_id):
            raise BadRequestException(f"Client {client_id} is not connected")

        # Send completion event
        sse_service.send_completion_event(
            client_id=client_id,
            task_id=video_id,
            task_type="video_generation",
            result=video_data,
            message=message,
        )

        logger.info(f"Video generation completed successfully: video_id={video_id}")

        return SuccessResponse(
            message=f"Video generation completed for video {video_id}",
            code=200,
        )

    except BadRequestException as e:
        logger.error(f"Bad request in video generation completion: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error completing video generation: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail="Failed to complete video generation"
        )
