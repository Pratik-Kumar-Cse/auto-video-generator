import json
import logging
import os
from bson import ObjectId
import uuid
from app.exceptions.subscription_exceptions import SubscriptionInactiveError
from ...agent.ai_image.workflow import (
    generate_image_prompts,
    read_prompt_generate_image,
)
from ..audio import AudioService
from ...providers.tavus import TavusService
from ...repositories.avatar_repository import AvatarRepository
from ...repositories.video_repository import VideoRepository
from ...repositories.script_repository import ScriptRepository
from ...repositories.user_repository import AuthRepository
from app.repositories.audio_repository import AudioRepository
from app.repositories.voice_repository import VoiceRepository

from termcolor import colored

from app.factory.event_data_factory import EventDataFactory
from app.constant.enum.notification_enum import NotificationType
from app.constant.enum.video_enum import (
    VideoViewType,
    VideoStatus,
    VideoQuality,
    VideoProcessingTypes,
)
from app.agent.video_clip.workflow import generate_sub_clips
from app.agent.image.workflow import generate_images
from app.agent.ai_video.workflow import (
    generate_video_prompts,
    read_prompt_generate_video,
)
from app.agent.search_terms.workflow import generate_search_terms
from app.constant.enum.script_enum import ScriptType
from app.constant.enum.user_enum import EmailType
from app.loggers.monitoring import sentry_client
from app.constant.constant import VIDEO_STATES
from ..youtube import download_youtube_video
from werkzeug.exceptions import NotFound, InternalServerError
from ..llm.multi_model_call import get_video_clips_details, check_video_match
from ..llm.llm_call import get_title, get_script_text
from .stock_video import (
    search_for_stock_videos_on_story_block,
    search_for_stock_videos,
    search_stock_videos,
    call_shutterstock_api,
)
from ..utils import save_video, remove_file, markdown_to_json

from app.constant.enum.event_enum import EventProcessType
from app.service.usage import UsageService
from app.helper.mailer import EmailService
from app.helper.redis import RedisService
from ..notification import NotificationService
from app.helper.sqs_queue import SQSHandler

from ..workflow import WorkflowService

from .video_edit import upscale_video

from app.helper.s3_manager import S3Uploader

from config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class VideoService:
    def __init__(self):
        self.audio_service = AudioService()
        self.tavus_service = TavusService()
        self.avatar_repository = AvatarRepository()
        self.video_repository = VideoRepository()
        self.script_repository = ScriptRepository()
        self.s3_service = S3Uploader()
        self.user_repository = AuthRepository()
        self.email_service = EmailService()
        self.notification_service = NotificationService()
        self.usage_service = UsageService()
        self.event_data_factory = EventDataFactory()
        self.handler = SQSHandler()
        self.audio_repository = AudioRepository()
        self.workflow_service = WorkflowService()
        self.voice_repository = VoiceRepository()
        self.redis_service = RedisService()

    def send_script_event(
        self,
        processing_type,
        data,
        message,
        client_id: str = None,
    ):
        try:
            """
            Send a script update to the frontend via Server-Sent Events

            :param audio_id: Unique identifier for the script
            :param audio_data: Data transfer object containing script details
            :param client_id: Optional specific client ID to send the event to
            """

            data["client_id"] = client_id
            # Sending the completed event
            self.event_data_factory.send_video_events(
                processing_type,
                data,
                message,
            )
        except Exception as e:
            print(colored(f"send_script_event occurred: {e}", "red"))

    def send_email(self, user_id, video_id, email_type, metadata=None):

        user_data = self.user_repository.find_user_by_id(user_id)

        link = f"{settings.FRONTEND_ENDPOINT}/dashboard/my-projects/{video_id}?videoId={video_id}"

        self.email_service.send_email_with_template(
            user_data["name"], user_data["email"], link, email_type, metadata
        )

    def _extract_video_data(self, video_data):
        return (
            str(video_data["user_id"]),
            str(video_data["script_id"]),
            video_data.get("voice_id", None),
        )

    def generate_video_clips_details(
        self,
        video_data,
        script_data,
        task,
        percentage=2,
    ):
        try:
            video_id = str(video_data["_id"])
            video_link = script_data.get("video_link")

            video_file_path = video_data.get("video_file_path", None)

            if script_data.get("type") == ScriptType.VIDEO.value:

                task.update_state(
                    state="PROGRESS",
                    meta={"progress": percentage, "status": "fetching clips ..."},
                )

                if video_data.get("video_clips_details") is None:

                    self.send_script_event(
                        EventProcessType.VIDEO_CLIP_CREATION.value,
                        {"video_id": video_id, "percentage": percentage},
                        VIDEO_STATES["STOCK_VIDEO_GENERATION"],
                        client_id=str(video_data["user_id"]),
                    )

                    if video_file_path:
                        if not os.path.exists(video_file_path):
                            if video_link:
                                video_file_path = save_video(
                                    video_link,
                                    video_id="video",
                                    directory=f"./temp/{video_id}",
                                )
                            else:
                                video_file_path = download_youtube_video(
                                    script_data["link"], f"./temp/{video_id}/"
                                )
                    else:
                        if video_link:
                            video_file_path = save_video(
                                video_link,
                                video_id="video",
                                directory=f"./temp/{video_id}",
                            )
                        else:
                            video_file_path = download_youtube_video(
                                script_data["link"], f"./temp/{video_id}/"
                            )

                    if not video_file_path:
                        raise Exception("Unable to download video.")

                    video_clips_details = get_video_clips_details(
                        script_data["script"], video_file_path
                    )

                    if not video_clips_details:
                        raise Exception("Unable to find video clips.")

                    video_data = self.video_repository.update_video(
                        video_id,
                        {
                            "video_clips_details": video_clips_details,
                            "video_file_path": video_file_path,
                        },
                    )
            return video_data
        except Exception as e:
            print(colored(f"[-] Error generate_video_clips_details: {str(e)}", "red"))
            raise

    def download_avatar_video(self, video_id, user_id, avatar_video_ids):
        avatar_video_urls = self.get_avatar_videos(
            video_id, user_id, None, avatar_video_ids
        )
        for index, video_url in enumerate(avatar_video_urls):
            save_video(
                video_url,
                video_id=f"avatar_{index}",
                directory=f"./temp/{video_id}",
            )
        return avatar_video_urls

    def generate_video(self, task, video_data):
        video_id = str(video_data["_id"])
        avatar_id = video_data.get("avatar_id", None)
        title = video_data.get("title", None)
        avatar_video_urls = video_data.get("avatar_video_urls", None)
        avatar_video_ids = video_data.get("avatar_video_ids", None)
        user_id, script_id, voice_id = self._extract_video_data(video_data)
        self.send_script_event(
            EventProcessType.VIDEO_GENERATION.value,
            {"video_id": video_id, "percentage": 1},
            VIDEO_STATES["STARTED"],
            client_id=str(video_data["user_id"]),
        )
        try:
            script_data = self.script_repository.get_script(script_id)
            script = script_data.get("script")
            if not script:
                raise NotFound("Script is not found.")
            if avatar_id and avatar_video_urls is None:
                video_ids = []
                video_links = []
                avatar_data = self.avatar_repository.get_avatar_by_id(avatar_id)
                if avatar_data.get("is_cloned") is False:
                    if video_data.get("avatar_video_ids") is None:

                        script = get_script_text(script_data["script"])

                        print(colored(f"script:{script}", "yellow"))

                        video_res = self.tavus_service.create_video_using_script(
                            script=script,
                            replica_id=avatar_data["avatar_id"],
                        )
                        self.video_repository.update_video(
                            video_id,
                            {"avatar_video_ids": [video_res["video_id"]]},
                        )

                        video_data = self.generate_video_clips_details(
                            video_data, script_data, task
                        )

                        avatar_video_urls = self.get_avatar_videos(
                            video_id, user_id, task, [video_res["video_id"]]
                        )
                    else:

                        video_data = self.generate_video_clips_details(
                            video_data, script_data, task
                        )

                        avatar_video_urls = self.get_avatar_videos(
                            video_id,
                            user_id,
                            task,
                            video_data.get("avatar_video_ids"),
                        )

                    if (
                        avatar_video_urls
                        and len(avatar_video_urls) != 0
                        and avatar_video_urls[0]
                    ):
                        self.video_repository.update_video(
                            video_id,
                            {"avatar_video_urls": avatar_video_urls},
                        )
                else:

                    audio_data = self.audio_service.generate_audio(
                        user_id, voice_id, script_id
                    )

                    video_data = self.generate_video_clips_details(
                        video_data, script_data, task
                    )

                    task.update_state(
                        state="PROGRESS",
                        meta={"progress": 10, "status": "audio generating ..."},
                    )

                    self.send_script_event(
                        EventProcessType.AUDIO_GENERATION.value,
                        {"video_id": video_id, "percentage": 5},
                        VIDEO_STATES["AUDIO_GENERATION_STARTED"],
                        client_id=str(video_data["user_id"]),
                    )

                    audio_data = self.audio_service.get_updated_audio(audio_data)

                    self.send_script_event(
                        EventProcessType.AUDIO_GENERATED.value,
                        {"video_id": video_id, "percentage": 10},
                        VIDEO_STATES["AUDIO_GENERATED"],
                        client_id=str(video_data["user_id"]),
                    )

                    if video_data.get("avatar_video_ids") is None:
                        videos_res = self.tavus_service.generate_videos(
                            audio_urls=audio_data["audio_links"],
                            replica_id=avatar_data["avatar_id"],
                        )

                        for res in videos_res:
                            video_ids.append(res["video_id"])
                            video_links.append(res["video_link"])

                        self.video_repository.update_video(
                            video_id,
                            {"avatar_video_ids": video_ids},
                        )

            if avatar_id and avatar_video_ids:
                self.download_avatar_video(video_id, user_id, avatar_video_ids)

            if avatar_video_urls:
                video_data = self.generate_video_clips_details(
                    video_data, script_data, task, 15
                )
                audio_data = self.audio_service.generate_audio_using_video(
                    video_id, user_id, voice_id, script_id, avatar_video_urls[0], script
                )
            else:
                audio_data = self.audio_service.generate_audio(
                    user_id, voice_id, script_id
                )
                video_data = self.generate_video_clips_details(
                    video_data, script_data, task
                )

                task.update_state(
                    state="PROGRESS",
                    meta={"progress": 10, "status": "audio generating ..."},
                )

                self.send_script_event(
                    EventProcessType.AUDIO_GENERATION.value,
                    {"video_id": video_id, "percentage": 5},
                    VIDEO_STATES["AUDIO_GENERATION_STARTED"],
                    client_id=user_id,
                )
                audio_data = self.audio_service.get_updated_audio(audio_data)

                self.send_script_event(
                    EventProcessType.AUDIO_GENERATED.value,
                    {"video_id": video_id, "percentage": 10},
                    VIDEO_STATES["AUDIO_GENERATED"],
                    client_id=str(video_data["user_id"]),
                )

            task.update_state(
                state="PROGRESS",
                meta={"progress": 20, "status": "subtitle generating ..."},
            )

            if audio_data.get("subtitles") is None:
                audio_data = self.audio_service.generate_subtitles(
                    video_id, str(audio_data["_id"])
                )
                self.send_script_event(
                    EventProcessType.SUBTITLE_GENERATION.value,
                    {"video_id": video_id, "percentage": 20},
                    VIDEO_STATES["SUBTITLE_GENERATED"],
                    client_id=user_id,
                )

            title = video_data.get("title")

            task.update_state(
                state="PROGRESS",
                meta={"progress": 22, "status": "title generating ..."},
            )

            if title is None:

                self.send_script_event(
                    EventProcessType.TITLE_GENERATION.value,
                    {"video_id": video_id, "percentage": 22},
                    VIDEO_STATES["VIDEO_TITLE_GENERATED"],
                    client_id=user_id,
                )
                # Generate a script
                title = get_title(
                    script_data["script"]
                )  # Pass the AI model to the script generation

                video_data = self.video_repository.update_video(
                    video_id,
                    {
                        "title": title,
                    },
                )

                print(colored("title of script: " + title, "yellow"))

            video_data = self.video_repository.to_dict(video_data)

            if script_data.get("type") == ScriptType.AI.value:
                video_data = self.process_ai_script(
                    script_data,
                    video_data,
                    audio_data,
                    video_data.get("video_file_path"),
                    task,
                )
            else:
                video_data = self.process_script(
                    script_data,
                    video_data,
                    audio_data,
                    video_data.get("video_file_path"),
                    task,
                )

            video_data = self.video_repository.to_dict(video_data)

            self.generate_video_queue(str(video_data["_id"]))

            return video_data

        except Exception as e:
            print("Error generating video", str(e))
            task.update_state(
                state="FAILED",
                meta={"progress": 0, "status": "failed ..."},
            )
            self.send_script_event(
                EventProcessType.ERROR_LOGS.value,
                {
                    "video_id": video_id,
                    "error_message": str(e),
                },
                VIDEO_STATES["VIDEO_GENERATION_FAILED"],
                client_id=user_id,
            )

            # If an error occurs, update the status to FAILED
            self.video_repository.update_video(
                video_id,
                {"status": VideoStatus.FAILED, "status_message": f"Error: {str(e)}"},
            )
            self.send_email(
                user_id,
                video_id,
                EmailType.VIDEO_GENERATION_FAILED.value,
                {"failed_reason": f"Error:{str(e)}"},
            )

            self.notification_service.create_notification(
                user_id,
                "Video Update",
                f"Video generation failed, {str(e)}",
                NotificationType.UPDATE.value,
                {
                    "type": "NOTIFICATION",
                    "data": {"video_id": video_id},
                },
            )
            sentry_client.capture_exception(e)
            return None

    def process_script(
        self,
        script_data,
        video_data,
        audio_data,
        video_file_path=None,
        task=None,
    ):
        video_id = str(video_data["_id"])
        user_id = str(video_data["user_id"])
        avatar_id = video_data.get("avatar_id", None)

        if script_data.get("type") == ScriptType.VIDEO.value:
            task.update_state(
                state="PROGRESS",
                meta={"progress": 30, "status": "clips downloading ..."},
            )

            if (
                video_data.get("event_video_clips") is None
                or len(video_data.get("event_video_clips")) == 0
            ):

                self.send_script_event(
                    EventProcessType.STOCK_VIDEO_CREATION.value,
                    {"video_id": video_id, "percentage": 30},
                    VIDEO_STATES["STOCK_VIDEO_GENERATED"],
                    client_id=user_id,
                )
                self.generate_sub_clips_safely(
                    video_id,
                    video_data.get("video_clips_details"),
                    script_data["script"],
                    audio_data["subtitles"],
                    video_file_path,
                )

                with open("./content/clips.json", "r") as file:
                    clips = json.load(file)

                clips = sorted(clips["data"], key=lambda x: x["atTime"])

                video_data = self.video_repository.update_video(
                    video_id, {"event_video_clips": clips}
                )

        task.update_state(
            state="PROGRESS",
            meta={"progress": 35, "status": "stock clip extracting ..."},
        )

        if (
            video_data.get("stock_video_clips") is None
            or len(video_data.get("stock_video_clips")) == 0
        ) and (script_data["type"] != ScriptType.VIDEO.value or not avatar_id):

            self.send_script_event(
                EventProcessType.STOCK_VIDEO_CREATION.value,
                {"video_id": video_id, "percentage": 35},
                VIDEO_STATES["STOCK_VIDEO_GENERATED"],
                client_id=user_id,
            )

            self.generate_search_terms_safely(
                script_data["script"], audio_data["subtitles"]
            )

            with open("./content/search_terms.json", "r") as file:
                search_terms_data = json.load(file)

            search_terms_data, video_urls = self.fetch_stock_videos(
                video_id=video_id,
                search_terms_data=search_terms_data,
            )

            search_terms_data = sorted(search_terms_data, key=lambda x: x["at_time"])

            video_data = self.video_repository.update_video(
                video_id,
                {"stock_video_clips": search_terms_data, "video_urls": video_urls},
            )

        task.update_state(
            state="PROGRESS",
            meta={"progress": 45, "status": "image clip extracting ..."},
        )

        self.send_script_event(
            EventProcessType.STOCK_VIDEO_CREATION.value,
            {"video_id": video_id, "percentage": 40},
            VIDEO_STATES["STOCK_VIDEO_GENERATED"],
            client_id=user_id,
        )

        if video_data.get("images") is None or len(video_data.get("images")) == 0:

            link = None

            if script_data["type"] == ScriptType.BLOG.value:
                link = script_data["link"]

            image_links = self.generate_images_safely(
                video_id,
                script_data["title"],
                script_data["script"],
                audio_data["subtitles"],
                link,
            )

            new_images = []
            if len(image_links) > 0:
                with open("./content/images.json", "r") as file:
                    image_data = json.load(file)

                for key, value in image_data.items():
                    images = json.loads(key)

                images = sorted(images, key=lambda x: x["atTime"])

                for index, image_data in enumerate(images):
                    try:
                        image_data["url"] = image_links[image_data["image"] - 1]
                        new_images.append(image_data)
                    except Exception as e:
                        print("Error loading image", str(e))

            video_data = self.video_repository.update_video(
                video_id, {"images": new_images, "image_links": image_links}
            )

        self.send_script_event(
            EventProcessType.STOCK_VIDEO_DATA_CREATED.value,
            {"video_id": video_id, "percentage": 40},
            VIDEO_STATES["STOCK_VIDEO_GENERATED"],
            client_id=user_id,
        )

        return video_data

    def process_ai_script(
        self,
        script_data,
        video_data,
        audio_data,
        video_file_path=None,
        task=None,
    ):
        video_id = str(video_data["_id"])
        user_id = str(video_data["user_id"])

        task.update_state(
            state="PROGRESS",
            meta={"progress": 25, "status": "image clip extracting ..."},
        )

        self.send_script_event(
            EventProcessType.STOCK_VIDEO_CREATION.value,
            {"video_id": video_id, "percentage": 30},
            VIDEO_STATES["STOCK_VIDEO_GENERATED"],
            client_id=user_id,
        )

        if (
            video_data.get("ai_images_data") is None
            or len(video_data.get("ai_images_data")) == 0
        ):

            images_data = self.generate_image_safely(
                video_id,
                audio_data["subtitles"],
                video_data.get("view_type"),
            )

            video_data = self.video_repository.update_video(
                video_id,
                {
                    "ai_images_data": images_data,
                },
            )

        self.send_script_event(
            EventProcessType.STOCK_VIDEO_CREATION.value,
            {"video_id": video_id, "percentage": 35},
            VIDEO_STATES["STOCK_VIDEO_GENERATED"],
            client_id=user_id,
        )

        # if (
        #     video_data.get("ai_video_data") is None
        #     or len(video_data.get("ai_video_data")) == 0
        # ):

        #     videos_data = self.generate_video_safely(
        #         video_id,
        #         audio_data["subtitles"],
        #         video_data.get("view_type"),
        #     )

        #     video_data = self.video_repository.update_video(
        #         video_id, {"ai_video_data": videos_data}
        #     )

        self.send_script_event(
            EventProcessType.STOCK_VIDEO_DATA_CREATED.value,
            {"video_id": video_id, "percentage": 40},
            VIDEO_STATES["STOCK_VIDEO_GENERATED"],
            client_id=user_id,
        )

        return video_data

    def generate_sub_clips_safely(
        self, video_id, video_clips_details, script, subtitles, video_file_path
    ):
        try:
            generate_sub_clips(
                video_id, video_clips_details, script, subtitles, video_file_path
            )
        except Exception as e:
            print(colored(f"[-] Error generating video clips: {e}", "red"))
            raise

    def generate_images_safely(self, video_id, title, script, subtitles, link):
        try:
            return generate_images(video_id, title, script, subtitles, link)
        except Exception as e:
            print(colored(f"[-] Error generating images: {e}", "red"))
            raise

    def generate_search_terms_safely(self, script, subtitles):
        try:
            return generate_search_terms(script, subtitles)
        except Exception as e:
            print(colored(f"[-] Error generating search term: {e}", "red"))
            raise

    def get_avatar_videos(
        self,
        video_id,
        user_id,
        task,
        video_ids,
        percentage=5,
    ):
        try:
            if task:
                task.update_state(
                    state="PROGRESS",
                    meta={"progress": percentage, "status": "avatar generating ..."},
                )

            self.send_script_event(
                EventProcessType.AVATAR_GENERATION.value,
                {
                    "video_id": str(video_id),
                    "percentage": percentage,
                },
                VIDEO_STATES["AVATAR_VIDEO_GENERATION"],
                client_id=user_id,
            )

            videos_data = self.tavus_service.get_videos(video_ids, task)

            self.send_script_event(
                EventProcessType.AVATAR_VIDEO_GENERATED.value,
                {"video_id": str(video_id), "percentage": 15},
                VIDEO_STATES["AVATAR_VIDEO_GENERATED"],
                client_id=user_id,
            )

            return [
                video["download_url"]
                for video in videos_data
                if "download_url" in video
            ]
        except Exception as e:
            print(f"Error fetching avatar videos: {e}")
            return InternalServerError("Error fetching avatar videos")

    def fetch_stock_videos(
        self,
        video_id,
        search_terms_data,
    ):
        video_urls, new_search_terms_data = self.search_videos(
            search_terms_data,
        )
        return new_search_terms_data, video_urls

    def search_videos(self, search_terms_data, video_provider="all", it=2, min_dur=5):
        search_terms = [
            data["search_terms"] for data in search_terms_data.get("data", [])
        ]
        video_urls = []
        new_search_terms_data = []
        for index, search_term in enumerate(search_terms):
            if video_provider == "storyblocks":
                found_urls = search_for_stock_videos_on_story_block(
                    search_term, it, min_dur
                )
            elif video_provider == "pexels":
                found_urls = search_for_stock_videos(search_term, it, min_dur)
            else:
                found_urls = search_stock_videos(search_term, it, min_dur)

            for url in found_urls:
                if url is not None and url not in video_urls:
                    video_urls.append(url)
                    search_terms_data["data"][index]["url"] = url
                    new_search_terms_data.append(search_terms_data["data"][index])
                    break
        return video_urls, new_search_terms_data

    def download_video_with_quality(self, user_id, video_data, quality):

        video_id = str(video_data["_id"])

        try:

            user_data = self.user_repository.get_populated_user_details(user_id)

            if not user_data.get("subscription"):
                raise SubscriptionInactiveError("subscription is not active")

            if not video_data.get("link"):
                raise Exception("video is not available")

            if quality == VideoQuality.Q720p.value:

                download_link = self.s3_service.generate_presigned_url_for_download(
                    "videos", f"{video_id}.mp4"
                )

            elif quality == VideoQuality.Q1080p.value:

                if not video_data.get("link_1080p"):

                    video_path = f"./temp/{video_id}.mp4"

                    save_video(
                        video_data.get("link"),
                        video_id=video_id,
                    )

                    final_video_path = f"./temp/{video_id}_1080p.mp4"

                    upscale_video(
                        video_path,
                        final_video_path,
                        VideoViewType.LANDSCAPE.value == video_data.get("view_type"),
                    )

                    link = self.s3_service.upload_file(
                        "videos",
                        final_video_path,
                        f"{video_id}_1080.mp4",
                        mimetype="video/mp4",
                    )

                    video_data = self.video_repository.update_video(
                        video_id, {"link_1080p": link}
                    )
                    remove_file(video_path)
                    remove_file(final_video_path)

                download_link = self.s3_service.generate_presigned_url_for_download(
                    "videos",
                    f"{video_id}_1080.mp4",
                )

            else:
                raise Exception("video quality not available")

            return {"download_link": download_link}
        except Exception:
            print(
                colored(
                    f"[-] Could not download_video_with_quality: {video_id}",
                    "red",
                )
            )
            raise

    def generate_video_queue(self, video_id):
        try:
            print("Generating video data...")
            process_type = VideoProcessingTypes.GENERATE_VIDEO.value
            res = self.sent_event(
                {
                    "video_id": video_id,
                    "process_type": process_type,
                }
            )
            self.event_data_factory.log_step(
                video_id,
                VIDEO_STATES["VIDEO_GENERATION_TASK_CREATED"],
                "Video generation initialise",
            )

            return res
        except Exception as e:
            logger.error("Error generating video", str(e))
            sentry_client.capture_exception(e)
            error_message = str(e)
            self.event_data_factory.log_step(
                video_id,
                VIDEO_STATES["VIDEO_GENERATION_TASK_CREATED"],
                f"Video task creation error. Reason:{error_message}",
            )
            raise

    def sent_event(self, message_object):
        # Create or get an existing queue
        queue_name = settings.QUEUE_NAME
        queue = self.handler.get_queue(queue_name)
        if not queue:
            queue = self.handler.create_queue(queue_name)
            if queue:
                print(f"Created queue: {queue.url}")
            else:
                print("Failed to create queue")
                return
        # Serialize the object to JSON
        message_body = json.dumps(message_object)
        # Send the serialized object as a message
        response = self.handler.send_message(queue, message_body)
        if response:
            print(f"Message sent successfully. Message ID: {response['MessageId']}")
            print(f"Sent object: {message_object}")
        else:
            print("Failed to send message")
        return response

    def generate_image_safely(
        self,
        video_id,
        subtitles,
        size=VideoViewType.LANDSCAPE.value,
    ):
        try:
            generate_image_prompts(subtitles)
            image_data = read_prompt_generate_image(size)
            self.event_data_factory.log_step(
                video_id,
                VIDEO_STATES["IMAGE_VIDEO_GENERATED"],
                "Image video generated",
            )
            return image_data
        except Exception as e:
            print(f"[-] Error generating Images data: {str(e)}")
            if hasattr(e, "message"):
                error_message = str(e.message)
            else:
                error_message = str(e)
            reason = f"Image video generation error. Processing Stage: {VIDEO_STATES["IMAGE_VIDEO_GENERATED"]}. Reason: {error_message}"
            self.event_data_factory.push_logs_to_redis(
                video_id,
                "video_generation",
                VIDEO_STATES["IMAGE_VIDEO_GENERATED"],
                "",
                reason,
            )
            return None

    def generate_video_safely(self, video_id, subtitles, size="1:1"):
        try:
            generate_video_prompts(subtitles)
            video_data = read_prompt_generate_video(size)
            self.event_data_factory.log_step(
                video_id,
                VIDEO_STATES["IMAGE_VIDEO_GENERATED"],
                "Ai video video generated",
            )
            return video_data
        except Exception as e:
            print(f"[-] Error generating video data: {str(e)}")
            if hasattr(e, "message"):
                error_message = str(e.message)
            else:
                error_message = str(e)
            reason = f"Ai video generation error. Processing Stage: {VIDEO_STATES["IMAGE_VIDEO_GENERATED"]}. Reason: {error_message}"
            self.event_data_factory.push_logs_to_redis(
                video_id,
                "video_generation",
                VIDEO_STATES["IMAGE_VIDEO_GENERATED"],
                "",
                reason,
            )
            return None

    def search_videos_with_quality_check(
        self,
        search_terms,
        search_terms_data,
        script,
        video_provider="storyblocks",
        it=2,
        min_dur=5,
        max_relevance_retries=2,
    ):
        video_urls = []
        new_search_terms_data = []
        send_event = False
        for index, search_term in enumerate(search_terms):
            relevance_retry_count = 0
            # Specific retries for relevance score
            try:
                # Choose the appropriate search function based on video provider
                search_function = (
                    search_for_stock_videos_on_story_block
                    if video_provider == "storyblocks"
                    else search_for_stock_videos
                )
                found_urls = search_function(search_term, it, min_dur)
                print(f"Found URLs (attempt {relevance_retry_count + 1}):", found_urls)

                for url in found_urls:
                    if url is not None and url not in video_urls:
                        relevance_retry_count = (
                            0  # Reset relevance retry count for each new URL
                        )
                        success = False
                        relevance_score = 0
                        while relevance_retry_count < max_relevance_retries:
                            path = save_video(
                                url, video_id=index, directory="./temp/stock"
                            )
                            try:
                                # Check video quality
                                quality_res = check_video_match(
                                    script, path, search_term
                                )
                                quality_res = markdown_to_json(quality_res)
                                relevance_score = quality_res.get("relevance_score", 5)
                                relevant_segments = quality_res.get(
                                    "relevant_segments", []
                                )
                                print(
                                    f"Quality check response (attempt, relevance retry {relevance_retry_count + 1}):",
                                    f"Score: {relevance_score}",
                                )
                                if relevance_score > 5:
                                    # Video meets quality threshold
                                    success = True

                                    url = self.s3_provider.upload_file(
                                        "stock/videos",
                                        path,
                                        new_file_name=f"{uuid.uuid4()}.mp4",
                                        mimetype="video/mp4",
                                    )
                                    video_urls.append(url)

                                    current_data = search_terms_data["data"][
                                        index
                                    ].copy()  # Create a copy of the data
                                    current_data.update(
                                        {
                                            "url": url,
                                            "score": relevance_score,
                                            "alternative_terms": quality_res.get(
                                                "alternative_search_terms"
                                            ),
                                            "relevant_segments": relevant_segments,
                                        }
                                    )
                                    new_search_terms_data.append(current_data)

                                    remove_file(path)
                                    break  # Break the relevance retry loop
                                # If score is low, try alternative terms
                                if (
                                    relevance_retry_count < max_relevance_retries - 1
                                ):  # Still have retries left
                                    alternative_res = call_shutterstock_api(
                                        quality_res["alternative_search_terms"]
                                    )
                                    print(
                                        f"Trying alternative terms (relevance retry {relevance_retry_count + 1}):",
                                        quality_res["alternative_search_terms"],
                                    )
                                    if len(alternative_res) > 0:
                                        url = alternative_res[0]
                                    else:
                                        # Try StoryBlock as fallback
                                        storyblock_res = (
                                            search_for_stock_videos_on_story_block(
                                                quality_res["alternative_search_terms"][
                                                    0
                                                ],
                                            )
                                        )
                                        if len(storyblock_res) > 0:
                                            url = storyblock_res[0]
                                        else:
                                            if len(found_urls) > 1:
                                                url = found_urls[1]

                                relevance_retry_count += 1
                            except Exception as e:
                                print(
                                    f"Error in video verification relevance retry {relevance_retry_count + 1}): {str(e)}"
                                )

                                relevance_retry_count += 1

                        if not success:
                            send_event = True
                            url = self.s3_provider.upload_file(
                                "stock/videos",
                                path,
                                new_file_name=f"{uuid.uuid4()}.mp4",
                                mimetype="video/mp4",
                            )
                            video_urls.append(url)
                            current_data = search_terms_data["data"][
                                index
                            ].copy()  # Create a copy of the data
                            current_data.update(
                                {
                                    "url": url or None,
                                    "score": relevance_score,
                                    "alternative_terms": quality_res.get(
                                        "alternative_search_terms"
                                    ),
                                    "relevant_segments": relevant_segments,
                                }
                            )
                            new_search_terms_data.append(current_data)
                            remove_file(path)
                        break  # Break the URL loop if we found a good video
                print(
                    f"Warning: Could not find suitable video for '{search_term}' after attempts"
                    f"with {max_relevance_retries} relevance checks each"
                )
            except Exception as e:
                print(f"Error in search attempt: {str(e)}")
        return video_urls, new_search_terms_data, send_event

    def generate_video_using_workflow(self, data):

        user_id = data.get("user_id")

        approval = data.get("approval", False)

        topic = data["topic"]
        video_type = data["video_type"]
        link = data.get("link", None)
        script_type = data.get("script_type", None)
        keywords = data.get("keywords", None)

        view_type = data.get("view_type", None)
        avatar_id = data.get("avatar_id", None)
        voice_id = data.get("voice_id", None)
        template_id = data.get("template_id", None)
        caption = data.get("caption", None)
        add_brand = data.get("add_brand", False)
        music_media_id = data.get("music_media_id")

        clone_avatar_id = None
        clone_voice_id = None

        if avatar_id:
            avatar_data = self.avatar_repository.get_avatar_by_id(avatar_id)
            clone_avatar_id = avatar_data.get("avatar_id")

        if voice_id:
            voice_data = self.voice_repository.get_voice_by_id(voice_id)
            clone_voice_id = voice_data.get("voice_id")

        request_data = {
            "topic": topic,
            "video_type": video_type,
            "script_type": script_type,
            "keywords": keywords,
            "view_type": view_type,
            "avatar_id": clone_avatar_id,
            "voice_id": "TX3LPaxmHKxFdv7VOQHJ",
            "caption": caption,
            "link": link,
            "event_stock_clips": [],
        }

        response = self.workflow_service.start_workflow(request_data, approval)

        script_data = {
            "user_id": user_id,
            "title": topic,
            "script": None,
            "type": script_type,
            "keywords": keywords,
            "video_type": video_type,
            "link": link,
        }

        # Create a new video entry with pending status
        script_id = self.script_repository.create_script(script_data)

        video_data = {
            "user_id": user_id,
            "voice_id": ObjectId(voice_id) if voice_id is not None else None,
            "avatar_id": ObjectId(avatar_id) if avatar_id is not None else None,
            "script_id": ObjectId(script_id),
            "status": VideoStatus.PENDING,
            "template_id": template_id,
            "view_type": view_type,
            "caption": caption,
            "add_brand": add_brand,
            "music_media_id": (
                ObjectId(music_media_id) if music_media_id is not None else None
            ),
            "correlation_id": response.get("correlationId"),
        }

        # Create a new video entry with pending status
        video_data = self.video_repository.create_video(video_data)

        video_data = self.video_repository.to_dict(video_data)

        self.redis_service.set_data_in_redis_with_ttl(
            f"workflow-video:{response.get("correlationId")}", str(user_id), 3600
        )

        return {
            "video_data": video_data,
            "script_data": self.script_repository.to_dict(script_data),
        }

    def generate_video_using_workflow_with_video_id(
        self, video_id, user_id, approval: bool = False
    ):
        # Extract video data using video_id
        video_data = self.video_repository.get_video_data(video_id, user_id)

        if not video_data:
            raise NotFound(f"Video with ID {video_id} not found.")

        script_id = str(video_data["script_id"])
        view_type = video_data.get("view_type", None)
        captions = video_data.get("caption", None)

        # Extract script data using script_id
        script_data = video_data.get("script")

        if not script_data:
            raise NotFound(f"Script with ID {script_id} not found.")

        topic = script_data.get("title", None)
        video_type = script_data.get("video_type", None)
        link = script_data.get("video_link", None)
        script_type = script_data.get("type", None)
        keywords = script_data.get("keywords", None)

        voice_data = video_data.get("voice", None)
        avatar_data = video_data.get("avatar", None)

        voice_id = None
        avatar_id = None

        if voice_data:
            voice_id = voice_data.get("voice_id", None)

        if avatar_data:
            avatar_id = avatar_data.get("avatar_id", None)

        request_data = {
            "topic": topic,
            "video_type": video_type,
            "script_type": script_type,
            "keywords": keywords,
            "view_type": view_type,
            "avatar_id": avatar_id,
            "voice_id": voice_id,
            "captions": captions,
            "link": link,
        }

        # Start workflow
        response = self.workflow_service.start_workflow(request_data, approval)

        # Update video data with correlation ID
        correlation_id = response.get("correlationId")

        self.redis_service.set_data_in_redis_with_ttl(
            f"workflow-video:{response.get("correlationId")}", str(user_id), 3600
        )

        updated_video_data = self.video_repository.update_video(
            video_id, {"correlation_id": correlation_id}
        )

        return {
            "video_data": self.video_repository.to_dict(updated_video_data),
            "script_data": self.script_repository.to_dict(script_data),
        }
