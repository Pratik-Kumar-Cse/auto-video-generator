"""
Server-Sent Events (SSE) API endpoints for FastAPI Video Generation Service
Enhanced with comprehensive functionality from python-backend
"""

import json
import logging
import queue
import time
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import StreamingResponse

from app.core.exceptions import AuthenticationException, BadRequestException
from app.helper.sse_manager import sse_manager
from app.models.common import SuccessResponse
from app.models.sse import (
    BroadcastEventRequest,
    BroadcastEventResponse,
    EventTypes,
    SSEStatusResponse,
    TriggerEventRequest,
    TriggerEventResponse,
)
from app.utils.auth_utils import decode_auth_token

logger = logging.getLogger(__name__)

router = APIRouter()


async def get_current_user_from_token(token: str) -> tuple:
    """
    Extract user information from authentication token

    Args:
        token: Authentication token

    Returns:
        Tuple containing (user_id, ip_address, user_agent, role)

    Raises:
        AuthenticationException: If token is invalid
    """
    try:
        return decode_auth_token(token)
    except Exception as e:
        logger.error(f"Token validation error: {e}")
        raise AuthenticationException("Invalid authentication token")


@router.get("/events")
async def server_sent_events(
    request: Request,
    token: str = Query(..., description="Authentication token"),
):
    """
    Server-Sent Events endpoint with client-specific event handling

    Args:
        request: FastAPI request object
        token: Authentication token for user identification

    Returns:
        StreamingResponse with SSE events
    """
    try:
        # Validate authentication token
        if not token:
            raise AuthenticationException("Authentication token is missing")

        user_info = await get_current_user_from_token(token)
        user_id, ip_address, user_agent, role = user_info
        client_id = user_id
        client_queue = queue.Queue()

        logger.info(f"SSE connection established for client: {client_id}")

        def event_stream():
            try:
                # Register client with SSE manager
                sse_manager.add_client(client_id, client_queue)

                while not sse_manager.is_shutting_down:
                    try:
                        # Get event from client queue with timeout
                        event = client_queue.get(timeout=10)

                        # Only process events for this client or broadcasts
                        if (
                            event.get("client_id") is None
                            or event.get("client_id") == client_id
                        ):
                            event_data = {
                                "event": event["event"],
                                "data": event["data"],
                                "type": event["type"],
                                "id": str(event["timestamp"]),
                            }

                            yield f"event: {event_data['event']}\n"
                            yield f"data: {json.dumps(event_data['data'])}\n"
                            yield f"type: {event_data['type']}\n"
                            yield f"id: {event_data['id']}\n\n"

                    except queue.Empty:
                        # Send keep-alive message
                        yield f"event: {EventTypes.KEEP_ALIVE}\n"
                        yield f"data: {EventTypes.KEEP_ALIVE}\n\n"

            except GeneratorExit:
                logger.info(f"Client {client_id} connection closed")
            except Exception as e:
                logger.error(f"SSE stream error for client {client_id}: {e}")
                yield f"event: {EventTypes.ERROR}\n"
                yield f"data: {json.dumps({'error': str(e)})}\n\n"
            finally:
                # Clean up client connection
                sse_manager.remove_client(client_id)

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

    except AuthenticationException as e:
        logger.error(f"Authentication error in SSE: {e}")
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        logger.error(f"SSE endpoint error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/trigger/{target_client_id}", response_model=TriggerEventResponse)
async def trigger_event_for_client(
    target_client_id: str,
    request: TriggerEventRequest,
):
    """
    Trigger a specific SSE event for a target client

    Args:
        target_client_id: ID of the target client
        request: Event trigger request data

    Returns:
        Response indicating the event was triggered
    """
    try:
        # Validate client exists
        if not sse_manager.is_client_connected(target_client_id):
            raise BadRequestException(f"Client {target_client_id} is not connected")

        # Send event to specific client
        sse_manager.send_update(
            event_name=request.event_type,
            data={
                "message": (
                    request.message or f"Event triggered for client {target_client_id}"
                ),
                "data": request.data,
                "timestamp": time.time(),
            },
            client_id=target_client_id,
        )

        logger.info(f"Event triggered for client: {target_client_id}")

        return TriggerEventResponse(
            status="success",
            message=f"Event triggered for client {target_client_id}",
            client_id=target_client_id,
        )

    except BadRequestException as e:
        logger.error(f"Bad request in trigger event: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error triggering event for client {target_client_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to trigger event")


@router.post("/broadcast", response_model=BroadcastEventResponse)
async def trigger_broadcast_event(
    request: BroadcastEventRequest,
):
    """
    Trigger a broadcast SSE event for all connected clients

    Args:
        request: Broadcast event request data

    Returns:
        Response indicating the broadcast was sent
    """
    try:
        clients_count = sse_manager.get_connected_clients_count()

        if clients_count == 0:
            logger.warning("No clients connected for broadcast")
            return BroadcastEventResponse(
                status="warning",
                message="No clients connected to receive broadcast",
                clients_count=0,
            )

        # Broadcast event to all clients
        sse_manager.send_update(
            event_name=request.event_type,
            data={
                "message": request.message or "Broadcast event triggered",
                "data": request.data,
                "timestamp": time.time(),
            },
            client_id=None,  # None means broadcast to all
        )

        logger.info(f"Broadcast event sent to {clients_count} clients")

        return BroadcastEventResponse(
            status="success",
            message=f"Broadcast event sent to {clients_count} clients",
            clients_count=clients_count,
        )

    except Exception as e:
        logger.error(f"Error broadcasting event: {e}")
        raise HTTPException(status_code=500, detail="Failed to broadcast event")


@router.get("/status", response_model=SSEStatusResponse)
async def get_sse_status():
    """
    Get current SSE service status and connected clients information

    Returns:
        SSE status information
    """
    try:
        connected_clients = sse_manager.get_connected_clients_count()
        client_ids = sse_manager.get_connected_client_ids()
        is_active = not sse_manager.is_shutting_down

        return SSEStatusResponse(
            connected_clients=connected_clients,
            client_ids=client_ids,
            is_active=is_active,
        )

    except Exception as e:
        logger.error(f"Error getting SSE status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get SSE status")


@router.post("/send-notification/{client_id}")
async def send_notification_to_client(
    client_id: str,
    title: str = Query(..., description="Notification title"),
    message: str = Query(..., description="Notification message"),
    notification_type: str = Query("info", description="Notification type"),
):
    """
    Send a notification event to a specific client

    Args:
        client_id: Target client ID
        title: Notification title
        message: Notification message
        notification_type: Type of notification (info, warning, error, success)

    Returns:
        Success response
    """
    try:
        if not sse_manager.is_client_connected(client_id):
            raise BadRequestException(f"Client {client_id} is not connected")

        sse_manager.send_update(
            event_name=EventTypes.NOTIFICATION,
            data={
                "title": title,
                "message": message,
                "type": notification_type,
                "timestamp": time.time(),
            },
            client_id=client_id,
        )

        return SuccessResponse(
            message=f"Notification sent to client {client_id}",
            code=200,
        )

    except BadRequestException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error sending notification to client {client_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to send notification")


@router.post("/send-progress-update/{client_id}")
async def send_progress_update(
    client_id: str,
    task_id: str = Query(..., description="Task ID"),
    progress: float = Query(..., description="Progress percentage (0-100)"),
    message: str = Query(..., description="Progress message"),
    current_step: Optional[str] = Query(None, description="Current step"),
):
    """
    Send a progress update event to a specific client

    Args:
        client_id: Target client ID
        task_id: Task identifier
        progress: Progress percentage (0-100)
        message: Progress message
        current_step: Current processing step

    Returns:
        Success response
    """
    try:
        if not sse_manager.is_client_connected(client_id):
            raise BadRequestException(f"Client {client_id} is not connected")

        sse_manager.send_update(
            event_name=EventTypes.PROGRESS,
            data={
                "task_id": task_id,
                "progress": progress,
                "message": message,
                "current_step": current_step,
                "timestamp": time.time(),
            },
            client_id=client_id,
        )

        return SuccessResponse(
            message=f"Progress update sent to client {client_id}",
            code=200,
        )

    except BadRequestException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error sending progress update to client {client_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to send progress update")


@router.delete("/disconnect/{client_id}")
async def disconnect_client(client_id: str):
    """
    Forcefully disconnect a specific client

    Args:
        client_id: Client ID to disconnect

    Returns:
        Success response
    """
    try:
        if not sse_manager.is_client_connected(client_id):
            raise BadRequestException(f"Client {client_id} is not connected")

        sse_manager.remove_client(client_id)

        return SuccessResponse(
            message=f"Client {client_id} disconnected successfully",
            code=200,
        )

    except BadRequestException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error disconnecting client {client_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to disconnect client")
