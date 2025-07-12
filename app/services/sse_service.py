"""
SSE Service for FastAPI Video Generation Service
Integrates SSE functionality with existing services
"""

import logging
import time
from typing import Any, Dict, Optional

from app.helper.sse_manager import sse_manager
from app.models.sse import EventTypes

logger = logging.getLogger(__name__)


class SSEService:
    """
    Service class for managing SSE events and integrations
    """

    def __init__(self):
        self.sse_manager = sse_manager

    def send_script_generation_update(
        self,
        client_id: str,
        task_id: str,
        status: str,
        progress: Optional[float] = None,
        content: Optional[str] = None,
        message: str = "",
        script_data: Optional[Dict[str, Any]] = None,
    ):
        """
        Send script generation progress update to client

        Args:
            client_id: Target client ID
            task_id: Script generation task ID
            status: Current status (processing, completed, error)
            progress: Progress percentage (0-100)
            content: Generated content (if any)
            message: Status message
            script_data: Complete script data when completed
        """
        try:
            event_data = {
                "task_id": task_id,
                "status": status,
                "progress": progress,
                "content": content,
                "message": message,
                "timestamp": time.time(),
            }

            if script_data:
                event_data["script"] = script_data

            self.sse_manager.send_update(
                event_name=EventTypes.SCRIPT_GENERATION,
                data=event_data,
                client_id=client_id,
            )

            logger.info(f"Script generation update sent to client {client_id}")

        except Exception as e:
            logger.error(f"Error sending script generation update: {e}")

    def send_video_processing_update(
        self,
        client_id: str,
        video_id: str,
        status: str,
        progress: Optional[float] = None,
        message: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        Send video processing update to client

        Args:
            client_id: Target client ID
            video_id: Video processing ID
            status: Current status
            progress: Progress percentage
            message: Status message
            metadata: Additional metadata
        """
        try:
            event_data = {
                "video_id": video_id,
                "status": status,
                "progress": progress,
                "message": message,
                "metadata": metadata or {},
                "timestamp": time.time(),
            }

            self.sse_manager.send_update(
                event_name=EventTypes.VIDEO_STREAM,
                data=event_data,
                client_id=client_id,
            )

            logger.info(f"Video processing update sent to client {client_id}")

        except Exception as e:
            logger.error(f"Error sending video processing update: {e}")

    def send_processing_update(
        self,
        client_id: str,
        task_id: str,
        task_type: str,
        status: str,
        progress: Optional[float] = None,
        current_step: Optional[str] = None,
        total_steps: Optional[int] = None,
        message: str = "",
        error: Optional[str] = None,
    ):
        """
        Send general processing update to client

        Args:
            client_id: Target client ID
            task_id: Task identifier
            task_type: Type of task being processed
            status: Current status
            progress: Progress percentage
            current_step: Current processing step
            total_steps: Total number of steps
            message: Status message
            error: Error message if any
        """
        try:
            event_data = {
                "task_id": task_id,
                "task_type": task_type,
                "status": status,
                "progress": progress,
                "current_step": current_step,
                "total_steps": total_steps,
                "message": message,
                "error": error,
                "timestamp": time.time(),
            }

            self.sse_manager.send_update(
                event_name=EventTypes.PROCESSING_UPDATE,
                data=event_data,
                client_id=client_id,
            )

            logger.info(f"Processing update sent to client {client_id}")

        except Exception as e:
            logger.error(f"Error sending processing update: {e}")

    def send_notification(
        self,
        client_id: str,
        title: str,
        message: str,
        notification_type: str = "info",
        action_url: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        Send notification to client

        Args:
            client_id: Target client ID
            title: Notification title
            message: Notification message
            notification_type: Type (info, warning, error, success)
            action_url: Optional action URL
            metadata: Additional metadata
        """
        try:
            event_data = {
                "title": title,
                "message": message,
                "type": notification_type,
                "action_url": action_url,
                "metadata": metadata or {},
                "timestamp": time.time(),
            }

            self.sse_manager.send_update(
                event_name=EventTypes.NOTIFICATION,
                data=event_data,
                client_id=client_id,
            )

            logger.info(f"Notification sent to client {client_id}")

        except Exception as e:
            logger.error(f"Error sending notification: {e}")

    def send_system_message(
        self,
        message: str,
        level: str = "info",
        component: Optional[str] = None,
        client_id: Optional[str] = None,
    ):
        """
        Send system message to client(s)

        Args:
            message: System message
            level: Message level (info, warning, error)
            component: System component
            client_id: Target client ID (None for broadcast)
        """
        try:
            event_data = {
                "message": message,
                "level": level,
                "component": component,
                "timestamp": time.time(),
            }

            self.sse_manager.send_update(
                event_name=EventTypes.SYSTEM_MESSAGE,
                data=event_data,
                client_id=client_id,
            )

            if client_id:
                logger.info(f"System message sent to client {client_id}")
            else:
                logger.info("System message broadcasted to all clients")

        except Exception as e:
            logger.error(f"Error sending system message: {e}")

    def send_completion_event(
        self,
        client_id: str,
        task_id: str,
        task_type: str,
        result: Dict[str, Any],
        message: str = "Task completed successfully",
    ):
        """
        Send task completion event to client

        Args:
            client_id: Target client ID
            task_id: Task identifier
            task_type: Type of completed task
            result: Task result data
            message: Completion message
        """
        try:
            event_data = {
                "task_id": task_id,
                "task_type": task_type,
                "result": result,
                "message": message,
                "timestamp": time.time(),
            }

            self.sse_manager.send_update(
                event_name=EventTypes.COMPLETED,
                data=event_data,
                client_id=client_id,
            )

            logger.info(f"Completion event sent to client {client_id}")

        except Exception as e:
            logger.error(f"Error sending completion event: {e}")

    def send_error_event(
        self,
        client_id: str,
        task_id: str,
        error_message: str,
        error_type: Optional[str] = None,
        task_type: Optional[str] = None,
    ):
        """
        Send error event to client

        Args:
            client_id: Target client ID
            task_id: Task identifier
            error_message: Error message
            error_type: Type of error
            task_type: Type of task that failed
        """
        try:
            event_data = {
                "task_id": task_id,
                "task_type": task_type,
                "error": error_message,
                "error_type": error_type,
                "timestamp": time.time(),
            }

            self.sse_manager.send_update(
                event_name=EventTypes.ERROR,
                data=event_data,
                client_id=client_id,
            )

            logger.info(f"Error event sent to client {client_id}")

        except Exception as e:
            logger.error(f"Error sending error event: {e}")

    def is_client_connected(self, client_id: str) -> bool:
        """
        Check if a client is connected

        Args:
            client_id: Client ID to check

        Returns:
            True if client is connected, False otherwise
        """
        return self.sse_manager.is_client_connected(client_id)

    def get_connected_clients_count(self) -> int:
        """
        Get number of connected clients

        Returns:
            Number of connected clients
        """
        return self.sse_manager.get_connected_clients_count()

    def broadcast_maintenance_message(self, message: str, scheduled_time: str):
        """
        Broadcast maintenance message to all clients

        Args:
            message: Maintenance message
            scheduled_time: Scheduled maintenance time
        """
        try:
            event_data = {
                "message": message,
                "scheduled_time": scheduled_time,
                "type": "maintenance",
                "timestamp": time.time(),
            }

            self.sse_manager.send_update(
                event_name=EventTypes.SYSTEM_MESSAGE,
                data=event_data,
                client_id=None,  # Broadcast to all
            )

            logger.info("Maintenance message broadcasted to all clients")

        except Exception as e:
            logger.error(f"Error broadcasting maintenance message: {e}")


# Create a singleton instance
sse_service = SSEService()
