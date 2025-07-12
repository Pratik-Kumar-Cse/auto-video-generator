"""
Celery configuration for async task processing
"""

import logging
from celery import Celery
from celery.signals import worker_ready, worker_shutting_down

from app.core.config import settings

logger = logging.getLogger(__name__)

# Create Celery instance
celery_app = Celery(
    "video_generator",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.tasks.video_tasks",
        "app.tasks.script_tasks",
        # Only include existing task modules
        # "app.tasks.media_tasks",      # Not found
        # "app.tasks.notification_tasks", # Not found
        # "app.tasks.upload_tasks",     # Not found
    ],
)

# Celery configuration
celery_app.conf.update(
    # Task serialization
    task_serializer=settings.CELERY_TASK_SERIALIZER,
    result_serializer=settings.CELERY_RESULT_SERIALIZER,
    accept_content=settings.CELERY_ACCEPT_CONTENT,
    # Timezone settings
    timezone=settings.CELERY_TIMEZONE,
    enable_utc=settings.CELERY_ENABLE_UTC,
    # Task routing
    task_routes={
        "app.tasks.video_tasks.*": {"queue": "video_processing"},
        "app.tasks.script_tasks.*": {"queue": "script_generation"},
        # Only include routes for existing task modules
        # "app.tasks.media_tasks.*": {"queue": "media_processing"},
        # "app.tasks.notification_tasks.*": {"queue": "notifications"},
        # "app.tasks.upload_tasks.*": {"queue": "uploads"},
    },
    # Worker configuration
    worker_max_tasks_per_child=1000,  # Prevent memory leaks
    worker_disable_rate_limits=False,
    worker_prefetch_multiplier=1,  # One task at a time per worker
    # Task execution settings
    task_acks_late=True,  # Acknowledge tasks after completion
    task_reject_on_worker_lost=True,  # Reject tasks if worker dies
    task_track_started=True,  # Track when tasks start
    task_time_limit=3600,  # 1 hour hard limit
    task_soft_time_limit=3300,  # 55 minutes soft limit
    # Result backend settings
    result_expires=3600,  # Results expire after 1 hour
    result_persistent=True,  # Persist results
    # Broker settings
    broker_connection_retry_on_startup=True,
    broker_connection_retry=True,
    broker_connection_max_retries=10,
    # Task retry settings
    task_default_retry_delay=60,  # 1 minute
    task_max_retries=3,
    # Monitoring
    worker_send_task_events=True,
    task_send_sent_event=True,
    # Security
    worker_hijack_root_logger=False,
    worker_log_color=False,
)

# Task priority levels
PRIORITY_HIGH = 9
PRIORITY_NORMAL = 5
PRIORITY_LOW = 1

# Queue configurations
QUEUE_CONFIGS = {
    "video_processing": {
        "routing_key": "video_processing",
        "priority": PRIORITY_HIGH,
        "max_retries": 2,
    },
    "script_generation": {
        "routing_key": "script_generation",
        "priority": PRIORITY_NORMAL,
        "max_retries": 3,
    },
    "media_processing": {
        "routing_key": "media_processing",
        "priority": PRIORITY_NORMAL,
        "max_retries": 2,
    },
    "notifications": {
        "routing_key": "notifications",
        "priority": PRIORITY_LOW,
        "max_retries": 5,
    },
    "uploads": {
        "routing_key": "uploads",
        "priority": PRIORITY_NORMAL,
        "max_retries": 3,
    },
}


@worker_ready.connect
def worker_ready_handler(sender=None, **kwargs):
    """Handler for when worker is ready"""
    logger.info(f"Celery worker {sender} is ready")


@worker_shutting_down.connect
def worker_shutting_down_handler(sender=None, **kwargs):
    """Handler for when worker is shutting down"""
    logger.info(f"Celery worker {sender} is shutting down")


# Task base class with common functionality
class BaseTask(celery_app.Task):
    """Base task class with common functionality"""

    def on_success(self, retval, task_id, args, kwargs):
        """Called when task succeeds"""
        logger.info(f"Task {task_id} succeeded with result: {retval}")

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Called when task fails"""
        logger.error(f"Task {task_id} failed with exception: {exc}")
        logger.error(f"Exception info: {einfo}")

    def on_retry(self, exc, task_id, args, kwargs, einfo):
        """Called when task is retried"""
        logger.warning(f"Task {task_id} is being retried due to: {exc}")


# Set the base task class
celery_app.Task = BaseTask


def get_task_info(task_id: str) -> dict:
    """Get information about a task"""
    try:
        result = celery_app.AsyncResult(task_id)
        return {
            "task_id": task_id,
            "status": result.status,
            "result": result.result,
            "traceback": result.traceback,
            "info": result.info,
        }
    except Exception as e:
        logger.error(f"Error getting task info for {task_id}: {e}")
        return {"task_id": task_id, "status": "UNKNOWN", "error": str(e)}


def revoke_task(task_id: str, terminate: bool = False) -> bool:
    """Revoke a task"""
    try:
        celery_app.control.revoke(task_id, terminate=terminate)
        logger.info(f"Task {task_id} revoked (terminate={terminate})")
        return True
    except Exception as e:
        logger.error(f"Error revoking task {task_id}: {e}")
        return False


def get_active_tasks() -> list:
    """Get list of active tasks"""
    try:
        inspect = celery_app.control.inspect()
        active_tasks = inspect.active()
        return active_tasks or []
    except Exception as e:
        logger.error(f"Error getting active tasks: {e}")
        return []


def get_worker_stats() -> dict:
    """Get worker statistics"""
    try:
        inspect = celery_app.control.inspect()
        stats = inspect.stats()
        return stats or {}
    except Exception as e:
        logger.error(f"Error getting worker stats: {e}")
        return {}


# Health check for Celery
def check_celery_health() -> bool:
    """Check if Celery is healthy"""
    try:
        inspect = celery_app.control.inspect()
        stats = inspect.stats()
        return bool(stats)
    except Exception as e:
        logger.error(f"Celery health check failed: {e}")
        return False
