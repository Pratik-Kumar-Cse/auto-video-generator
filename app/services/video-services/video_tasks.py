import logging

from app.helper.redis import RedisService

import json

from .video import VideoService

from app.repositories.video_repository import VideoRepository

from ..utils import create_dir, clean_dir


from app.repositories.user_repository import AuthRepository

from config import settings


from celery import Celery, Task

from ...constant.enum.video_enum import VideoStatus

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


celery = Celery(
    "video_task",
    broker=settings.RABBITMQ_BROKER_URL,
    backend=settings.CELERY_BACKEND_URL,
)

# Configure Celery to limit memory usage and tasks per worker
celery.conf.update(
    # Worker Settings
    worker_concurrency=3,  # Limit to 2 concurrent tasks
    worker_prefetch_multiplier=1,  # Prevent prefetching multiple tasks
    worker_max_tasks_per_child=1,  # Restart worker after each task
    worker_max_memory_per_child=1000000,  # 1GB memory limit
    # Task Settings
    task_acks_late=True,  # Only acknowledge after task completion
    task_reject_on_worker_lost=True,  # Reject tasks if worker dies
    # Time Limits
    task_time_limit=3600,  # Hard limit: 1 hour
    task_soft_time_limit=3000,  # Soft limit: 50 minutes
    # # Rate Limiting
    # task_annotations={
    #     "video_processing_task.*": {"rate_limit": "2/m"}  # Max 2 tasks per minute
    # },
)


video_service = VideoService()

video_repo = VideoRepository()
auth_repository = AuthRepository()


class LogErrorsTask(Task):
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        logger.error(f"Task {task_id} failed: {exc}")
        super(LogErrorsTask, self).on_failure(exc, task_id, args, kwargs, einfo)


@celery.task(
    bind=True,
    base=LogErrorsTask,
    name="video_processing_task.generate_video",
    max_retries=2,
    retry_backoff=True,
)
def generate_video_task(self, video_data):
    video_id = str(video_data["_id"])
    user_id = str(video_data["user_id"])
    logger.info(f"Starting video generation task for video_id: {video_id}")
    try:
        create_dir("./temp")
        create_dir(f"./temp/{video_id}")
        self.update_state(
            state="PROGRESS",
            meta={"progress": 0, "status": "video_generation_initiated"},
        )
        # Update status to PROCESSING
        video_repo.update_video(
            video_id,
            {
                "status": VideoStatus.PROCESSING,
                "status_message": None,
                "task_id": self.request.id,
            },
        )
        # Generate video
        res = video_service.generate_video(self, video_data)

        clean_dir(f"./temp/{video_id}")

        logger.info(f"Video generation task completed for video_id: {video_id}")

        if res:
            SequentialVideoTask().on_success(user_id)
            return {
                "progress": 100,
                "status": "video generation task start successfully!",
            }
        else:
            SequentialVideoTask().on_failure(user_id)
            return {"progress": 0, "status": "video generation failed!"}

    except celery.exceptions.SoftTimeLimitExceeded as e:
        logger.error(f"Soft time limit exceeded for video_id: {video_id} : str({e})")
        video_repo.update_video(
            video_data["_id"],
            {"status": VideoStatus.TIMED_OUT, "status_message": f"Error:{str(e)}"},
        )
    except Exception as e:
        print("Error generating video", str(e))
        SequentialVideoTask().on_failure(user_id)
        logger.exception(f"Error generating video for video_id: {video_id}")
        # If an error occurs, update the status to FAILED
        video_repo.update_video(
            video_id,
            {"status": VideoStatus.FAILED, "status_message": f"Error:{str(e)}"},
        )


def generate_video(video_data):
    logger.info(f"Starting video generation task for video_id: {video_data['_id']}")
    try:

        video_id = video_data["_id"]

        create_dir(f"./temp/{video_id}")

        # Update status to PROCESSING
        video_repo.update_video(video_id, {"status": VideoStatus.PROCESSING})

        logger.info(f"Video data: {video_data}")

        # Generate video
        result = video_service.generate_video(video_data)

        clean_dir(f"./temp/{video_id}")

        # Update video entry with the result and change status to COMPLETED
        video_repo.update_video_status(video_id, VideoStatus.COMPLETED)

        logger.info(f"Video generation completed for video_id: {video_id}")
        return result

    except celery.exceptions.SoftTimeLimitExceeded as e:
        logger.error(
            f"Soft time limit exceeded for video_id: {video_data['_id']} : str({e})"
        )
        video_repo.update_video(video_data["_id"], {"status": VideoStatus.TIMED_OUT})
        raise

    except Exception as e:
        print("Error generating video", str(e))
        logger.exception(f"Error generating video for video_id: {video_data['_id']}")
        # If an error occurs, update the status to FAILED
        video_repo.update_video_status(video_data["_id"], VideoStatus.FAILED)
        raise


@celery.task(bind=True, base=LogErrorsTask, soft_time_limit=1800, time_limit=1860)
def generate_script_task(self, video_data):
    video_id = video_data["_id"]
    update_progress(self, video_id, 20, "Generating script")
    script_data = video_service.generate_script(video_data)
    video_repo.update_video(video_id, {"script_data": script_data})
    return video_id


@celery.task(bind=True, base=LogErrorsTask, soft_time_limit=1800, time_limit=1860)
def generate_audio_task(self, video_id):
    video_data = video_repo.get_video(video_id)
    update_progress(self, video_id, 40, "Generating audio")
    audio_data = video_service.generate_audio(video_data["script_data"])
    video_repo.update_video(video_id, {"audio_data": audio_data})
    return video_id


@celery.task(bind=True, base=LogErrorsTask, soft_time_limit=3600, time_limit=3660)
def generate_avatar_video_task(self, video_id):
    video_data = video_repo.get_video(video_id)
    update_progress(self, video_id, 60, "Generating video")
    video_data = video_service.generate_video_from_audio(video_data["audio_data"])
    video_repo.update_video(video_id, {"video_data": video_data})
    return video_id


@celery.task(bind=True, base=LogErrorsTask, soft_time_limit=1800, time_limit=1860)
def finalize_video_task(self, video_id):
    video_data = video_repo.get_video(video_id)
    update_progress(self, video_id, 80, "Finalizing video")
    result = video_service.finalize_video(video_data["video_data"])
    update_progress(self, video_id, 100, "Completed")
    video_repo.update_video_status(video_id, "COMPLETED")
    return result


def update_progress(task, video_id, progress, message):
    task.update_state(state="PROGRESS", meta={"progress": progress, "message": message})
    video_repo.update_video(video_id, {"progress": progress, "status_message": message})


@celery.task(bind=True, base=LogErrorsTask)
def start_video_generation(self, video_data):
    video_id = video_data["_id"]
    create_dir(f"./temp/{video_id}")
    update_progress(self, video_id, 0, "Starting video generation")
    video_repo.update_video(
        video_id, {"status": "PROCESSING", "task_id": self.request.id}
    )

    workflow = chain(
        generate_script_task.s(video_data),
        generate_audio_task.s(),
        generate_avatar_video_task.s(),
        finalize_video_task.s(),
    )
    return workflow.apply_async()


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_user_lock_key(user_id):
    return f"user:{user_id}:processing_lock"


def get_user_queue_key(user_id):
    return f"user:{user_id}:video_queue"


class SequentialVideoTask:

    def __init__(
        self,
    ):
        self.redis_service = RedisService()
        self.video_repository = VideoRepository()

    def after_task_completion(self, user_id):
        """Process next task after current task completes"""
        lock_key = get_user_lock_key(user_id)
        queue_key = get_user_queue_key(user_id)

        # Release the processing lock
        self.redis_service.delete_data_with_key(lock_key)

        # Check for next task in queue
        next_task_data = self.redis_service.get_queue_data(queue_key)

        print("next_task_data ==>>", next_task_data)

        if next_task_data:
            # If next_task_data is a string, parse it as JSON
            if isinstance(next_task_data, str):
                next_task_data = json.loads(next_task_data)

            if isinstance(next_task_data, str):
                next_task_data = json.loads(next_task_data)

            # Start the next task
            video_id = next_task_data["video_id"]
            video_data = self.video_repository.get_video_by_id(video_id)
            if video_data:
                generate_video_task.delay(self.video_repository.to_dict(video_data))
                logger.info(
                    f"Started next queued task for user {user_id}, video {video_id}"
                )

    def on_success(self, user_id):
        """Handle successful task completion"""
        logger.info(f"Task completed successfully for user {user_id}")
        self.after_task_completion(user_id)

    def on_failure(self, user_id):
        """Handle task failure"""
        logger.error(f"Task failed for user {user_id}")
        self.after_task_completion(user_id)


# video_data = SequentialVideoTask().video_repository.get_video_by_id(
#     "67ca8198f8536cd2f151ffc9"
# )
# print("video_data", video_data)
# generate_video_task.delay(SequentialVideoTask().video_repository.to_dict(video_data))
