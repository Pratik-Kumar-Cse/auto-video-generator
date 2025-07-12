import json
import logging
import os
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

from app.agent.image.workflow import generate_images
from app.agent.search_terms.workflow import generate_search_terms
from app.agent.video_clip.workflow import generate_sub_clips
from app.constant.constant import MESSAGES, VIDEO_PROCESSING_TYPES, VIDEO_TEMPLATES
from app.constant.notification_enums import NotificationType
from app.constant.script_enums import ScriptType
from app.constant.user_enums import EmailType
from app.constant.video_enums import VideoStatus, VideoViewType
from app.exceptions.video_exceptions import VideoCreationFailed
from app.factory.event_data_factory import EventDataFactory
from app.helper.mailer import EmailService
from app.helper.redis import RedisClient
from app.helper.s3_manager import S3Uploader
from app.helper.utils import read_folder_and_upload
from app.loggers.monitoring import sentry_client
from app.providers.assembly_ai import create_subtitle_file
from app.providers.tavus import TavusService
from app.repositories.audio_repository import AudioRepository
from app.services.usage import UsageService
from bson import ObjectId
from config import config
from moviepy.editor import (  # type: ignore
    AudioFileClip,
    VideoFileClip,
    concatenate_videoclips,
)
from termcolor import colored
from werkzeug.exceptions import BadRequest, InternalServerError, NotFound

from ...repositories.avatar_repository import AvatarRepository
from ...repositories.brand_repository import BrandRepository
from ...repositories.script_repository import ScriptRepository
from ...repositories.user_repository import AuthRepository
from ...repositories.video_repository import VideoRepository
from ..audio import AudioService
from ..llm.llm_call import get_intro_placement_time, get_script_text, get_title
from ..llm.multi_model_call import get_video_clips_details
from ..notification import NotificationService
from ..utils import (
    check_url_expiration,
    clean_dir,
    create_dir,
    download_image,
    format_duration,
    save_video,
    str_replace,
    unlink_folder,
)
from ..youtube import download_youtube_video
from .reel_template import create_reel_video, create_reel_video1
from .stock_video import search_for_stock_videos, search_for_stock_videos_on_story_block
from .utils import stop_ffmpeg_processes
from .video_edit import create_thumbnail
from .video_resolution_converter import convert_video
from .video_template import long_video1, test_long_video
from .video_template_processor import VideoTemplateProcessor

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


FRONTEND_ENDPOINT = config.variables["FRONTEND_ENDPOINT"]


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
        self.brand_repository = BrandRepository()
        self.notification_service = NotificationService()
        self.usage_service = UsageService()
        self.event_data_factory = EventDataFactory()
        self.redis_instance = RedisClient()
        self.audio_repository = AudioRepository()
        self.video_state = None

    def send_email(self, user_id, video_id, email_type, metadata=None):
        try:

            user_data = self.user_repository.find_user_by_id(user_id)

            if metadata:
                link = f"{FRONTEND_ENDPOINT}/dashboard/my-projects"
            else:
                link = f"{FRONTEND_ENDPOINT}/dashboard/my-projects/{video_id}"

            self.email_service.send_email_with_template(
                user_data["name"], user_data["email"], link, email_type, metadata
            )
        except Exception as e:
            print("send_email video error", str(e))

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
        percentage=2,
    ):
        try:
            video_id = str(video_data["_id"])
            video_link = script_data.get("video_link")

            video_file_path = video_data.get("video_file_path", None)

            if script_data.get("type") == ScriptType.VIDEO.value:

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

                if video_data.get("video_clips_details") is None:

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

    def generate_video(self, video_id):

        create_dir("./temp")
        create_dir(f"./temp/{video_id}")

        video_data = self.get_video_data(video_id)

        if not video_data:
            raise NotFound(f"Video data is not found: {video_id}")

        if video_data.get("status") == VideoStatus.COMPLETED:
            raise BadRequest("Video has already been generated")

        script_data = video_data.get("script")

        if script_data.get("type") == ScriptType.AI.value:
            return self.process_video(video_data)

        avatar_id = video_data.get("avatar_id", None)
        title = video_data.get("title", None)
        avatar_video_urls = video_data.get("avatar_video_urls", None)

        avatar_video_ids = video_data.get("avatar_video_ids", None)

        user_id, script_id, voice_id = self._extract_video_data(video_data)

        try:

            script_data = self.script_repository.get_script(script_id)
            script_data = self.script_repository.to_dict(script_data)

            script = script_data.get("script")

            if not script:
                raise NotFound("Script is not found.")

            if avatar_id and avatar_video_urls is None:

                video_ids = []
                video_links = []
                avatar_data = self.avatar_repository.get_avatar_by_id(avatar_id)

                if avatar_data.get("is_cloned") is False:

                    if video_data.get("avatar_video_ids") is None:

                        script = get_script_text(script_data["script"], "gpt4")

                        print(colored(f"script:{script}", "yellow"))

                        video_res = self.tavus_service.create_video_using_script(
                            name="testing",
                            script=script,
                            replica_id=avatar_data["avatar_id"],
                        )
                        self.video_repository.update_video(
                            video_id,
                            {"avatar_video_ids": [video_res["video_id"]]},
                        )

                        video_data = self.generate_video_clips_details(
                            video_data, script_data
                        )

                        avatar_video_urls = self.get_avatar_videos(
                            [video_res["video_id"]]
                        )
                    else:

                        video_data = self.generate_video_clips_details(
                            video_data, script_data
                        )

                        avatar_video_urls = self.get_avatar_videos(
                            video_data.get("avatar_video_ids")
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
                        video_data, script_data
                    )

                    audio_data = self.audio_service.get_updated_audio(audio_data)

                    if video_data.get("avatar_video_ids") is None:
                        videos_res = self.tavus_service.generate_videos(
                            name="testing",
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
                self.download_avatar_video(video_id, avatar_video_ids)

            if avatar_video_urls:
                video_data = self.generate_video_clips_details(
                    video_data, script_data, 15
                )
                audio_data = self.audio_service.generate_audio_using_video(
                    video_id, user_id, voice_id, script_id, avatar_video_urls[0], script
                )
            else:
                audio_data = self.audio_service.generate_audio(
                    user_id, voice_id, script_id
                )
                video_data = self.generate_video_clips_details(video_data, script_data)

                audio_data = self.audio_service.get_updated_audio(audio_data)

            audio_data = self.audio_service.generate_subtitles(
                video_id, str(audio_data["_id"])
            )

            title = video_data.get("title")

            if title is None:
                # Generate a script
                title = get_title(
                    script_data["script"], "gpt-3.5-turbo"
                )  # Pass the AI model to the script generation

                video_data = self.video_repository.update_video(
                    video_id,
                    {
                        "title": title,
                    },
                )

                print(colored("title of script: " + title, "yellow"))

            video_data = self.video_repository.to_dict(video_data)

            video_data = self.process_script(
                script_data,
                video_data,
                audio_data,
                video_data.get("video_file_path"),
            )

            video_data = self.video_repository.to_dict(video_data)

            subtitles_path = create_subtitle_file(video_id, audio_data.get("subtitles"))

            final_video_path, duration = self.generate_final_video(
                video_data, script_data, audio_data, subtitles_path
            )

            if final_video_path is None:
                raise VideoCreationFailed("video is generation failed")

            thumbnail_path = f"./temp/{video_id}/thumbnail.jpg"

            create_thumbnail(final_video_path, thumbnail_path)

            link = self.s3_service.upload_file(
                "videos",
                final_video_path,
                f"{video_id}.mp4",
                mimetype="video/mp4",
            )

            thumbnail_link = self.s3_service.upload_file(
                "videos",
                thumbnail_path,
                f"{video_id}.jpg",
                mimetype="image/jpeg",
            )

            video_data = self.video_repository.update_video(
                video_id,
                {
                    "link": link,
                    "thumbnail_link": thumbnail_link,
                    "status": VideoStatus.COMPLETED,
                    "duration": duration,
                },
            )

            self.usage_service.create_usage(
                ObjectId(user_id),
                {"credits_used": 1, "seconds_used": int(duration)},
            )

            # Sending the completed event
            self.event_data_factory.send_video_events(
                VIDEO_PROCESSING_TYPES["VIDEO_CREATED"],
                {
                    "video_id": video_id,
                    "thumbnail": thumbnail_link,
                    "video_link": link,
                    "client_id": user_id,
                },
                MESSAGES["VIDEO_GENERATION_DONE"],
                False,
            )

            self.send_email(user_id, video_id, EmailType.VIDEO_GENERATED.value)

            self.notification_service.create_notification(
                user_id,
                "Video Update",
                f"Video successfully generated, {title}",
                NotificationType.UPDATE.value,
                {
                    "type": "NOTIFICATION",
                    "data": {"video_id": video_id, "title": title},
                },
            )

            # clean_dir(f"./temp/{video_id}")

            return video_data

        except Exception as e:
            print("Error generating video", str(e))

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
            if hasattr(e, "message"):
                error_message = str(e.message)
            else:
                error_message = str(e)
            reason = f"Video generation error. Processing Stage: video generation. Reason: {error_message}"
            self.event_data_factory.send_video_events(
                VIDEO_PROCESSING_TYPES["ERROR_LOGS"],
                {"video_id": video_id, "client_id": user_id, "error_message": str(e)},
                reason,
                False,
            )
            # clean_dir(f"./temp/{video_id}")
            sentry_client.capture_exception(e)
            return None

    def process_script(
        self,
        script_data,
        video_data,
        audio_data,
        video_file_path=None,
    ):
        video_id = str(video_data["_id"])
        avatar_id = video_data.get("avatar_id", None)

        if script_data.get("type") == ScriptType.VIDEO.value:
            if (
                video_data.get("event_video_clips") is None
                or len(video_data.get("event_video_clips")) == 0
            ):
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

        if (
            video_data.get("stock_video_clips") is None
            or len(video_data.get("stock_video_clips")) == 0
        ) and (script_data["type"] != ScriptType.VIDEO.value or not avatar_id):

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

        else:

            if video_data.get("video_urls") and len(video_data.get("video_urls")) != 0:
                self.download_videos(video_id, video_data["video_urls"])

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

            with open("./content/images.json", "r") as file:
                image_data = json.load(file)

            for key, value in image_data.items():
                images = json.loads(key)

            images = sorted(images, key=lambda x: x["atTime"])

            video_data = self.video_repository.update_video(
                video_id, {"images": images, "image_links": image_links}
            )

        else:

            if (
                video_data.get("image_links")
                and len(video_data.get("image_links")) != 0
            ):
                for index, link in enumerate(video_data["image_links"]):
                    save_path = f"./temp/{video_id}/image_{index + 1}.jpg"
                    download_image(link, save_path)

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

    def save_brand_details(
        self,
        video_id,
        user_id,
        view_type,
    ):
        try:
            brand = self.brand_repository.get_brand_details(user_id)

            if brand:
                logo = brand.get("logo")
                if logo.get("url"):
                    save_path = f"./temp/{video_id}/logo.png"
                    download_image(logo["url"], save_path)
                if VideoViewType.LANDSCAPE.value == view_type:
                    intro_landscape = brand.get("intro_landscape")
                    outro_landscape = brand.get("outro_landscape")
                    if intro_landscape:
                        save_video(
                            intro_landscape.get("url"),
                            video_id="intro_video",
                            directory=f"./temp/{video_id}",
                        )
                    if outro_landscape:
                        save_video(
                            outro_landscape.get("url"),
                            video_id="outro_video",
                            directory=f"./temp/{video_id}",
                        )
                if VideoViewType.SQUARE.value == view_type:
                    intro_square = brand.get("intro_square")
                    outro_square = brand.get("outro_square")
                    if intro_square:
                        save_video(
                            intro_square.get("url"),
                            video_id="intro_video",
                            directory=f"./temp/{video_id}",
                        )
                    if outro_square:
                        save_video(
                            outro_square.get("url"),
                            video_id="outro_video",
                            directory=f"./temp/{video_id}",
                        )

                if VideoViewType.PORTRAIT.value == view_type:
                    intro_portrait = brand.get("intro_portrait")
                    outro_portrait = brand.get("outro_portrait")
                    if intro_portrait:
                        save_video(
                            intro_portrait.get("url"),
                            video_id="intro_video",
                            directory=f"./temp/{video_id}",
                        )
                    if outro_portrait:
                        save_video(
                            outro_portrait.get("url"),
                            video_id="outro_video",
                            directory=f"./temp/{video_id}",
                        )

                return logo

            return {"position": "top-right", "size": "medium"}

        except Exception as e:
            logger.error(f"Error generating images: {str(e)}")
            raise

    def download_avatar_video(self, video_id, avatar_video_ids):
        avatar_video_urls = self.get_avatar_videos(avatar_video_ids)
        for index, video_url in enumerate(avatar_video_urls):
            save_video(
                video_url,
                video_id=f"avatar_{index}",
                directory=f"./temp/{video_id}",
            )
        return avatar_video_urls

    def generate_final_video(
        self,
        video_data,
        script_data,
        audio_data,
        subtitles_path,
    ):
        try:
            duration = 0
            video_id = str(video_data["_id"])
            user_id = str(video_data["user_id"])
            view_type = video_data["view_type"]
            template_id = video_data.get("template_id", "template_1")
            caption = video_data.get("caption")
            music_media_id = script_data.get("music_media_id", None)
            add_brand = script_data.get("add_brand", False)
            print(music_media_id, add_brand)
            logo = {"position": "top-right", "size": "medium"}
            if add_brand:
                logo = self.save_brand_details(video_id, user_id, view_type)
            print("logo", logo)
            if video_data.get("avatar_video_urls") or video_data.get(
                "avatar_video_ids"
            ):
                if video_data.get("avatar_video_urls"):
                    video_urls = video_data.get("avatar_video_urls")
                else:
                    video_urls = self.get_avatar_videos(
                        video_data["avatar_video_ids"],
                    )
                    self.video_repository.update_video(
                        video_id,
                        {"avatar_video_urls": video_urls},
                    )
                print("video_urls", video_urls)
                video_paths = []
                for index, video_url in enumerate(video_urls):
                    saved_video_path = save_video(
                        video_url,
                        video_id=f"avatar_{index}",
                        directory=f"./temp/{video_id}",
                    )
                    video_paths.append(saved_video_path)
                if video_data.get("view_type") == VideoViewType.PORTRAIT.value:
                    final_video_path, duration = create_reel_video(
                        video_id,
                        user_id,
                        video_paths,
                        subtitles_path,
                        video_data.get("event_video_clips"),
                        video_data.get("images"),
                        video_data.get("stock_video_clips"),
                        template_id,
                        script_data["type"] == ScriptType.VIDEO.value,
                        video_data.get("video_file_path"),
                        caption,
                        music_media_id,
                        logo,
                    )
                else:
                    if video_data.get("intro_time") is None:
                        try:
                            intro_time = float(
                                get_intro_placement_time(audio_data["subtitles"])
                            )
                        except Exception as e:
                            print("Error in intro time", str(e))
                            intro_time = 7
                        self.video_repository.update_video(
                            video_id,
                            {"intro_time": intro_time},
                        )
                    else:
                        intro_time = video_data.get("intro_time")
                    print("intro_time", intro_time)
                    final_video_path, duration = test_long_video(
                        video_id,
                        user_id,
                        video_paths,
                        video_data.get("title"),
                        video_data.get("event_video_clips"),
                        video_data.get("stock_video_clips"),
                        video_data.get("images"),
                        video_data.get("video_file_path"),
                        intro_time,
                        logo,
                    )
            else:
                audio_path = f"./temp/{video_id}/audio.mp3"
                if video_data.get("view_type") == VideoViewType.PORTRAIT.value:
                    final_video_path, duration = create_reel_video1(
                        video_id,
                        user_id,
                        audio_path,
                        subtitles_path,
                        video_data.get("event_video_clips"),
                        video_data.get("images"),
                        video_data.get("stock_video_clips"),
                        script_data.get("type") == ScriptType.VIDEO.value,
                        video_data.get("video_file_path"),
                        caption,
                        music_media_id,
                        logo,
                    )
                else:
                    final_video_path, duration = long_video1(
                        video_id,
                        user_id,
                        audio_path,
                        video_data.get("event_video_clips"),
                        video_data.get("images"),
                        video_data.get("stock_video_clips"),
                        video_data.get("video_file_path"),
                        logo,
                    )
            stop_ffmpeg_processes()
            return final_video_path, duration
        except Exception as e:
            print(colored(f"[-] Error generating final video: {e}", "red"))
            raise InternalServerError("Video processing failed")

    def get_avatar_videos(self, video_ids):
        try:

            videos_data = self.tavus_service.get_videos(video_ids)
            return [
                video["download_url"]
                for video in videos_data
                if "download_url" in video
            ]
        except Exception as e:
            print(f"Error fetching avatar videos: {e}")
            return []

    def fetch_stock_videos(
        self, video_id, search_terms_data, video_provider="storyblocks", it=2, min_dur=5
    ):
        video_urls, new_search_terms_data = self.search_videos(
            search_terms_data, video_provider, it, min_dur
        )
        self.download_videos(video_id, video_urls)
        return new_search_terms_data, video_urls

    def search_videos(self, search_terms_data, video_provider, it, min_dur):
        search_terms = [
            data["search_terms"] for data in search_terms_data.get("data", [])
        ]
        video_urls = []
        new_search_terms_data = []
        for index, search_term in enumerate(search_terms):
            found_urls = (
                search_for_stock_videos_on_story_block
                if video_provider == "storyblocks"
                else search_for_stock_videos
            )(search_term, it, min_dur)
            for url in found_urls:
                if url is not None and url not in video_urls:
                    video_urls.append(url)
                    new_search_terms_data.append(search_terms_data["data"][index])
                    break
        return video_urls, new_search_terms_data

    def download_videos(self, video_id, video_urls):
        if not video_urls:
            print(colored("[-] No videos found to download.", "red"))
            return []

        print(colored(f"[+] Downloading {len(video_urls)} videos...", "blue"))
        video_paths = []
        for index, video_url in enumerate(video_urls):
            try:
                saved_video_path = save_video(
                    video_url, video_id=index, directory=f"./temp/{video_id}"
                )
                video_paths.append(saved_video_path)
            except Exception:
                print(colored(f"[-] Could not download video: {video_url}", "red"))
        return video_paths

    def process_video(self, video_data):
        """
        Process the video by combining avatar, intro, and outro clips, creating a thumbnail, uploading to S3,
        and updating the video status in the backend.

        :param video_id: The ID of the video to be processed.
        """

        video_id = video_data.get("_id")
        user_id = video_data.get("user_id")

        try:
            # Retrieving the data from DB
            self.video_state = MESSAGES["DATA_RETRIEVAL_STARTED"]

            script_id = video_data.get("script_id")
            video_id = video_data.get("_id")
            title = video_data.get("title")
            view_type = video_data.get("view_type")

            stock_videos = (
                video_data.get("stock_video_clips")
                or video_data.get("ai_videos_data")
                or []
            )
            stock_images = (
                video_data.get("images") or video_data.get("ai_images_data") or []
            )

            video_clips = video_data.get("event_video_clips") or []

            # Video data retrieved
            self.video_state = MESSAGES["DATA_RETRIEVED"]

            self.event_data_factory.log_step(
                video_id, self.video_state, f"Video data retrieved: {video_id}"
            )

            # Checking whether the container is already running or not
            container_status = self.check_container_status(video_id)

            if container_status is not None:
                raise ValueError("Video generation is already started")

            # Video creation started
            self.video_state = MESSAGES["STARTED"]

            self.event_data_factory.log_step(
                video_id,
                self.video_state,
                f"Video creation has been started: {video_id}",
            )

            # Extracting all the required video Urls
            self.video_state = MESSAGES["START_URL_EXTRACTION"]

            self.event_data_factory.log_step(
                video_id,
                self.video_state,
                f"Url extraction started {video_id}",
            )

            avatar_id = video_data.get("avatar_id")
            avatar_video_ids = video_data.get("avatar_video_ids")

            # Download all required videos
            self.video_state = MESSAGES["START_DOWNLOADING"]

            self.event_data_factory.log_step(
                video_id,
                self.video_state,
                "Started downloading avatar, intro, and outro videos",
            )
            video_paths = []
            audio_paths = [f"./temp/{video_id}/audio.mp3"]

            if avatar_id and avatar_video_ids:
                self.download_avatar_video(video_id, avatar_video_ids)
                for index, avatar_id in enumerate(avatar_video_ids):
                    video_paths.append(f"./temp/{video_id}/avatar_{index}.mp4")

            audio_data = self.audio_repository.get_audio_by_script(script_id)

            audio_data = self.audio_service.generate_subtitles(
                video_id, str(audio_data["_id"])
            )

            create_subtitle_file(video_id, audio_data.get("subtitles"))

            self.download_content_videos(
                video_data, stock_videos, stock_images, video_clips
            )

            # All the videos has been downloaded
            self.video_state = MESSAGES["END_DOWNLOAD"]

            self.event_data_factory.log_step(
                video_id,
                self.video_state,
                "Downloading complete for avatar, intro, and outro videos",
            )

            # Combine the videos and upload to S3
            self.video_state = MESSAGES["START_UPLOADING"]

            self.event_data_factory.log_step(
                video_id, self.video_state, "Started uploading videos"
            )

            uploaded_objects, final_video_duration, video_resolution = (
                self.combine_and_upload(
                    video_id,
                    video_paths,
                    audio_paths,
                    view_type,
                    stock_videos,
                    stock_images,
                    video_clips,
                )
            )

            print(uploaded_objects, final_video_duration, video_resolution)

            # Videos are uploaded to s3
            self.video_state = MESSAGES["UPLOADED"]

            self.event_data_factory.log_step(
                video_id,
                self.video_state,
                f"Videos combined and uploaded: {uploaded_objects}",
            )

            # Clean up the local video directory
            self.video_state = MESSAGES["DELETE_FILES"]

            self.event_data_factory.log_step(
                video_id, self.video_state, "Removing downloaded files"
            )

            unlink_folder(f"./temp/{video_id}")

            # Update video status in backend
            self.video_state = MESSAGES["UPDATE_VIDEO"]

            self.event_data_factory.log_step(
                video_id, self.video_state, f"Updating video status: {video_id}"
            )

            thumbnail, video_link = self.update_video_status(
                video_id, uploaded_objects, final_video_duration, video_resolution
            )

            # Sending the completed event
            self.event_data_factory.send_video_events(
                VIDEO_PROCESSING_TYPES["VIDEO_CREATED"],
                {"videoId": video_id, "thumbnail": thumbnail, "videoLink": video_link},
                MESSAGES["VIDEO_GENERATION_DONE"],
                True,
            )

            # Video creation done
            self.video_state = MESSAGES["VIDEO_CREATED"]
            self.event_data_factory.log_step(
                video_id,
                self.video_state,
                f"Video processing completed for video ID: {video_id}",
            )

            self.send_email(user_id, video_id, EmailType.VIDEO_GENERATED.value)

            self.notification_service.create_notification(
                user_id,
                "Video Update",
                f"Video successfully generated, {title}",
                NotificationType.UPDATE.value,
                {
                    "type": "NOTIFICATION",
                    "data": {"video_id": video_id, "title": title},
                },
            )

        except Exception as e:

            # Safely handle different types of exceptions
            print("exceppppption", e)
            if hasattr(e, "message"):
                error_message = str(e.message)
            else:
                error_message = str(e)
            print(f"An error occurred: {error_message}")

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

            reason = f"Video generation error. Processing Stage: {self.video_state}. Reason: {str_replace(error_message, 'Error: ', '')}"
            self.event_data_factory.send_video_events(
                VIDEO_PROCESSING_TYPES["ERROR_LOGS"],
                {"video_id": video_id},
                reason,
                True,
            )
            # Pushing the stepper logs to redis
            self.event_data_factory.push_logs_to_redis(
                video_id, "video_generation", self.video_state, "", reason
            )
            clean_dir(f"./temp/{video_id}")
            sentry_client.capture_exception(e)
        finally:
            # Removing container running flag from redis
            self.delete_container_status_data(video_id)

    def get_video_data(self, video_id):
        """
        Retrieve the video data from the repository using the video ID.

        :param video_id: The ID of the video to retrieve.
        :return: The video data if found, None otherwise.
        """
        video_data = self.video_repository.find_video(video_id, True)
        if not video_data:
            print("Video not found")
            return None
        return self.video_repository.to_dict(video_data)

    def download_content_videos(
        self,
        video_data,
        stock_videos,
        stock_images,
        video_clips,
    ):
        """
        Download avatar, intro, and outro videos.

        :param video_path: The base path to save the avatar videos.
        :param avatar_video: Dictionary containing avatar video information.
        :param intro_video_url: URL for the intro video.
        :param outro_video_url: URL for the outro video.
        """

        video_id = str(video_data["_id"])
        user_id = str(video_data["user_id"])
        view_type = video_data["view_type"]

        if stock_videos and len(stock_videos) != 0:
            stock_video_urls = [
                video["url"] for video in stock_videos if "url" in video
            ]
            self.download_videos(video_id, stock_video_urls)

        if stock_images and len(stock_images) != 0:
            for index, data in enumerate(stock_images):
                save_path = f"./temp/{video_id}/image_{index + 1}.jpg"
                download_image(data["url"], save_path)

        if video_clips and len(video_clips) != 0:
            self.generate_video_clips_details(video_data, video_data["script"])

        self.save_brand_details(video_id, user_id, view_type)

        print("Stock footages downloaded")

    def download_images(self, image_path, image_urls, max_workers=5):
        """
        Download images and save them locally using a thread pool.

        :param image_path: Path to save the images.
        :param image_urls: List of image URLs.
        :param max_workers: Maximum number of threads to use.
        """

        def download_image_task(index, image_url):
            """
            Task to download a single image.
            """
            download_image(image_url, index, image_path)

        # Use ThreadPoolExecutor to parallelize downloads
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Create a dictionary mapping futures to their respective URLs
            future_to_url = {
                executor.submit(download_image_task, index, image_url): image_url
                for index, image_url in enumerate(image_urls)
            }

            # Process the results as they complete
            for future in as_completed(future_to_url):
                image_url = future_to_url[future]
                try:
                    # Attempt to get the result (this will raise any exceptions that occurred)
                    future.result()
                    print(f"[+] Successfully downloaded: {image_url}")
                except Exception as exc:
                    print(f"[-] Could not download image: {image_url}. Error: {exc}")

    def download_stock_videos(self, video_path, stock_video_urls, max_workers=4):

        # Use ThreadPoolExecutor for parallel downloads
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Create a dictionary to map futures to their original URLs
            future_to_url = {
                executor.submit(save_video, video_url, index, video_path): video_url
                for index, video_url in enumerate(stock_video_urls)
                if video_url and video_url.strip()
            }

            # Process the results as they complete
            for future in as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    # Attempt to get the result (this will raise any exceptions that occurred)
                    future.result()
                    print(f"[+] Successfully downloaded: {url}")
                except Exception as exc:
                    print(f"[-] Could not download video: {url}. Error: {exc}")

    def download_avatar_videos(
        self, video_path, avatar_video_ids, avatar_video_urls, max_workers=5
    ):
        """
        Download avatar videos and save them locally using a thread pool.

        :param video_path: Path to save the avatar videos.
        :param avatar_video_ids: List of avatar video IDs.
        :param avatar_video_urls: List of avatar video URLs.
        :param max_workers: Maximum number of threads to use.
        """

        def download_video_task(index, avatar_video_url):
            """
            Task to handle the download logic for each avatar video.
            """
            if not check_url_expiration(avatar_video_url):
                api_url = (
                    f"/avatar/get-avatar-video?video_ids={avatar_video_ids[index]}"
                )
                headers = self.http_service.make_auth_headers()
                response = self.http_service.get_call(
                    api_url, headers=headers, is_node_call=False
                )
                avatar_video_url = response.get("data")[0]["download_url"]
            save_video(avatar_video_url, avatar_video_ids[index], video_path)

        # Use ThreadPoolExecutor to parallelize downloads
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Create a dictionary mapping futures to their respective indices
            future_to_index = {
                executor.submit(download_video_task, index, avatar_video_url): index
                for index, avatar_video_url in enumerate(avatar_video_urls)
            }

            # Process the results as they complete
            for future in as_completed(future_to_index):
                index = future_to_index[future]
                try:
                    # Attempt to get the result (this will raise any exceptions that occurred)
                    future.result()
                    print(
                        f"[+] Successfully downloaded video with ID: {avatar_video_ids[index]}"
                    )
                except Exception as exc:
                    print(
                        f"[-] Could not download video with ID: {avatar_video_ids[index]}. Error: {exc}"
                    )

    def download_intro_outro_videos(self, video_link, video_path, video_type):
        """
        Download intro or outro video.

        :param video_link: URL of the video to download.
        :param video_path: Local path to save the video.
        :param video_type: The type of the video ('intro' or 'outro').
        """
        save_video(video_link, video_type, video_path)

    def download_intro_outro_videos_parallel(
        self,
        intro_video_url,
        intro_video_path,
        outro_video_url,
        outro_video_path,
        max_workers=2,
    ):
        """
        Download intro and outro videos in parallel using a thread pool.

        :param intro_video_url: URL of the intro video.
        :param intro_video_path: Path to save the intro video.
        :param outro_video_url: URL of the outro video.
        :param outro_video_path: Path to save the outro video.
        :param max_workers: Maximum number of threads to use (default is 2 for intro and outro).
        """
        tasks = [
            {"url": intro_video_url, "path": intro_video_path, "type": "intro"},
            {"url": outro_video_url, "path": outro_video_path, "type": "outro"},
        ]

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit tasks to the executor
            futures = {
                executor.submit(
                    self.download_intro_outro_videos,
                    task["url"],
                    task["path"],
                    task["type"],
                ): task["type"]
                for task in tasks
            }

            # Process the results as they complete
            for future in as_completed(futures):
                video_type = futures[future]
                try:
                    future.result()  # This will raise any exceptions that occurred
                    print(f"[+] Successfully downloaded {video_type} video.")
                except Exception as exc:
                    print(f"[-] Could not download {video_type} video. Error: {exc}")

    def combine_and_upload(
        self,
        video_id,
        video_paths,
        audio_paths,
        view_type,
        stock_videos,
        stock_images,
        video_clips,
    ):
        """
        Create thumbnail, Combine intro, avatar, and outro videos into a final video, then upload it to S3.

        :param video_id: The ID of the video being processed.
        :param avatar_video: Information about the avatar videos.
        :param intro_video_path: Path to the intro video.
        :param outro_video_path: Path to the outro video.
        :param video_mode: long video or short video (long or short)
        :param upload_social_domain: Youtube or Tiktok or Linkedin
        """

        final_video_duration = self.combine_videos(
            video_id,
            video_paths,
            audio_paths,
            view_type,
            stock_videos,
            stock_images,
            video_clips,
        )

        final_video_duration = 71.06

        create_thumbnail(
            f"./temp/{video_id}/{video_id}.mp4", f"./temp/{video_id}/thumbnail.jpg"
        )

        # Converting video into different formats
        convert_video(video_id, view_type)

        uploaded_objects = read_folder_and_upload(video_id)

        return uploaded_objects, final_video_duration, view_type

    def combine_videos(
        self,
        video_id,
        video_paths,
        audio_paths,
        view_type,
        stock_videos,
        stock_images,
        video_clips,
    ):
        """
        Combine intro, main, and outro videos into a single output video.

        :param intro_path: Path to the intro video.
        :param main_paths: List of paths to the main content videos.
        :param outro_path: Path to the outro video.
        :param output_path: Path to save the final combined video.
        :param video_id: _id of the video
        :param video_mode: long video or short video (long or short)
        :param upload_domain: Youtube or Tiktok or Linkedin
        """
        payload = {"video_clips": video_clips}

        if view_type == VideoViewType.LANDSCAPE.value:
            # Prepare the payload for generating a video
            template_id = VIDEO_TEMPLATES["LANDSCAPE_TEMPLATE"]

        if view_type == VideoViewType.SQUARE.value:
            template_id = VIDEO_TEMPLATES["SQUARE_TEMPLATE"]

        if view_type == VideoViewType.PORTRAIT.value:
            template_id = VIDEO_TEMPLATES["PORTRAIT_TEMPLATE"]

        if video_paths and len(video_paths) != 0:
            # Load avatar clips and concatenate them
            avatar_clips_list = [VideoFileClip(path) for path in video_paths]

            payload["main_video"] = concatenate_videoclips(
                avatar_clips_list, method="compose"
            )

        if audio_paths and len(audio_paths) != 0:
            # Load avatar clips and concatenate them
            avatar_clips_list = [AudioFileClip(path) for path in audio_paths]

            payload["main_audio"] = avatar_clips_list[0]

        # Create a defaultdict to store the merged data, sorted by 'at_time'
        merged_data = defaultdict(list)

        # Add data1 items to the merged_data dictionary
        for item in stock_images:
            merged_data[item["atTime"]].append({"stock_image": item})

        # Add data2 items to the merged_data dictionary
        for item in stock_videos:
            merged_data[item["atTime"]].append({"stock_video": item})

        # Sort the keys (at_time values) in increasing order
        sorted_keys = sorted(merged_data.keys())

        merged_json = [
            {"atTime": k, **{key: value for d in v for key, value in d.items()}}
            for k, v in zip(sorted_keys, [merged_data[key] for key in sorted_keys])
        ]

        payload["stock"] = merged_json

        # Record the start time
        start_time = datetime.now()

        # Generate video clips from the template processor
        final_duration = VideoTemplateProcessor(template_id).generate_video(
            payload, video_id
        )

        print("final_duration", final_duration)

        # Record the end time
        end_time = datetime.now()
        print(f"Start Time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"End Time: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")

        # Return the duration of the full video
        return format_duration(final_duration)

    def get_video_attributes(self, video_path):
        """
        Extracts and returns the width and height of the video.

        This function loads the video file located at the provided 'video_path' using
        the VideoFileClip function from the moviepy library. It then retrieves the
        video's dimensions (width and height) and returns them as a tuple.

        :param video_path: Path to the video file.
        :return: A tuple (width, height) representing the video's dimensions.
        """
        video_clip = VideoFileClip(video_path)
        width, height = video_clip.size
        return width, height

    def update_video_status(
        self,
        video_id,
        uploaded_objects,
        final_video_duration,
        video_resolution,
    ):
        """
        Update the status of the video to 'COMPLETED' in the backend.

        :param video_id: The ID of the video being processed.
        :param uploaded_objects: Uploaded files url
        :param final_video_duration: Final video duration
        """

        # Extract final video and thumbnail
        thumbnail = uploaded_objects.get("thumbnail", None)
        # Get the first item from the thumbnail array
        video_link = uploaded_objects.get(video_id, None)
        # Get the first item from the final array

        # Process compressed files into a simplified resolution-keyed dictionary
        compressed_files = uploaded_objects.get("compressed", [])

        compressed_videos = {}
        for file_url in compressed_files:
            # Extract the resolution from the file name (e.g., "video_1280x720.mp4")
            file_name = os.path.basename(file_url)

            resolution = file_name.split("_")[-1].split(".")[
                0
            ]  # Extract "1280x720" from "video_1280x720.mp4"

            if video_resolution == VideoViewType.PORTRAIT.value:

                short_resolution = resolution.split("x")[
                    0
                ]  # Extract the height, e.g., "720" from "720X1280"

            else:

                short_resolution = resolution.split("x")[
                    -1
                ]  # Extract the height, e.g., "720" from "1280x720"

            compressed_videos[short_resolution] = file_url

        self.video_repository.update_video(
            video_id,
            {
                "link": video_link,
                "thumbnail_link": thumbnail,
                "status": VideoStatus.COMPLETED,
                "duration": final_video_duration,
                "compressed_videos": compressed_videos,
            },
        )

        return thumbnail, video_link

    def check_container_status(self, video_id):
        """
        This function checks whether a video generation process is already
        running in another container by querying Redis.

        Args:
            video_id (str): The unique identifier for the video.

        Returns:
            str or None: The status of the video container from Redis.
            If no status is found, it sets the status to "1", indicating
            the process has started.
        """
        key = f"CONTAINER_STATUS_{video_id}"
        container_exist = self.redis_instance.get_value(key)
        if not container_exist:
            self.redis_instance.set_value(key, str(1))
        return container_exist

    def delete_container_status_data(self, video_id):
        """
        Function to delete the container data once the process is complete.
        """
        key = f"CONTAINER_STATUS_{video_id}"
        self.redis_instance.remove_value(key)
