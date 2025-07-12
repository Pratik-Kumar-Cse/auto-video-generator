import requests
from bson import ObjectId
from apiclient.errors import HttpError
import logging
from app.helper.mailer import EmailService
from ..llm.llm_call import generate_metadata, generate_reel_captions
from ..youtube import upload_video

from app.service.uploader.ytuploader import YoutubeUploader
from ..utils import save_video, remove_file
from app.constant.enum.video_enum import (
    VideoViewType,
    ScheduleVideoStatus,
    UploadDomain,
)
from werkzeug.exceptions import NotFound
from app.service.uploader.linkedin_upload import LinkedInUploader
from ..scheduler import scheduler
from app.constant.enum.user_enum import EmailType

from app.repositories.script_repository import ScriptRepository
from app.repositories.video_repository import VideoRepository
from app.repositories.audio_repository import AudioRepository
from app.repositories.schedule_video_repository import ScheduleVideoRepository
from app.repositories.user_repository import AuthRepository
from app.repositories.uploaded_video_repository import UploadedVideoRepository


# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class UploadVideoService:

    def __init__(self):
        self.script_repository = ScriptRepository()
        self.video_repository = VideoRepository()
        self.audio_repository = AudioRepository()
        self.auth_repository = AuthRepository()
        self.schedule_video_repository = ScheduleVideoRepository()
        self.email_service = EmailService()
        self.upload_video_repo = UploadedVideoRepository()

    def send_email(self, user_data, video_id, email_type, metadata=None):

        link = f"https://www.youtube.com/watch?v={video_id}"

        self.email_service.send_email_with_template(
            user_data["name"], user_data["email"], link, email_type, metadata
        )

    def generate_youtube_metadata(self, video_data):

        try:

            script_data = self.script_repository.get_script(video_data.get("script_id"))

            audio_data = self.audio_repository.get_audio_by_script(
                video_data.get("script_id")
            )

            metadata = video_data.get("metadata", None)

            if not metadata:

                video_type = (
                    "Shorts"
                    if video_data.get("view_type") == VideoViewType.PORTRAIT.value
                    else "Video"
                )

                # Define metadata for the video, we will display this to the user, and use it for the YouTube upload
                title, description, keywords = generate_metadata(
                    script_data["title"],
                    audio_data["subtitles"],
                    video_type,
                )

                caption = generate_reel_captions(
                    script_data["title"],
                    script_data["script"],
                )

                metadata = {
                    "title": title,
                    "description": description,
                    "keywords": keywords,
                    "caption": caption,
                }

                self.video_repository.update_video(
                    video_data["_id"],
                    {"metadata": metadata},
                )

            return metadata
        except HttpError as e:
            print(f"An HTTP error {e.resp.status} occurred:\n{e.content}")

    def upload_on_youtube(self, user_data, video_data):

        metadata = video_data.get("metadata")

        # Choose the appropriate category ID for your videos
        video_category_id = "28"  # Science & Technology
        privacyStatus = "public"  # "public", "private", "unlisted"

        video_path = save_video(video_data["link"], video_data["_id"])

        video_metadata = {
            "video_path": video_path,
            "title": metadata["title"],
            "description": metadata["description"],
            "category": video_category_id,
            "keywords": ",".join(metadata.get("keywords")),
            "privacyStatus": privacyStatus,
        }

        # Upload the video to YouTube
        try:
            # Unpack the video_metadata dictionary into individual arguments
            video_response = upload_video(
                email=user_data["email"],
                youtube_credentials=user_data["youtube_credentials"],
                video_path=video_metadata["video_path"],
                title=video_metadata["title"],
                description=video_metadata["description"],
                category=video_metadata["category"],
                keywords=video_metadata["keywords"],
                privacy_status=video_metadata["privacyStatus"],
            )
            print(f"Uploaded video ID: {video_response.get('id')}")
            remove_file(video_path)
            video_data = self.video_repository.update_video(
                str(video_data["_id"]), {"youtube_video_id": video_response.get("id")}
            )

            self.upload_video_repo.create_uploaded_video(
                {
                    "video_id": ObjectId(str(video_data["_id"])),
                    "user_id": ObjectId(str(user_data["_id"])),
                    "upload_video_id": video_response.get("id"),
                    "upload_link": f"https://www.youtube.com/watch?v={video_response.get("id")}",
                    "upload_domain": UploadDomain.YOUTUBE.value,
                }
            )

            self.send_email(
                user_data,
                video_response.get("id"),
                EmailType.VIDEO_UPLOADED.value,
            )
            return {"id": video_response.get("id")}
        except HttpError as e:
            print(f"An HTTP error {e.resp.status} occurred:\n{e.content}")

    def upload_on_instagram(self, user_data, video_data):

        try:

            script_data = self.script_repository.get_script(video_data.get("script_id"))

            caption = generate_reel_captions(
                script_data["title"], script_data["script"]
            )

            instagram_account_id = self.get_instagram_account_id(
                user_data["youtube_token"]
            )

            if not instagram_account_id:
                return {"message": "Failed to get Instagram account ID"}, 400

            result = self.upload_video_to_instagram(
                user_data["youtube_token"],
                instagram_account_id,
                video_data["link"],
                caption,
            )
            return {"result": result}, 200
        except HttpError as e:
            print(f"An HTTP error {e.resp.status} occurred:\n{e.content}")

    def get_instagram_account_id(self, access_token):
        url = f"https://graph.facebook.com/{API_VERSION}/me/accounts"
        params = {"access_token": access_token}
        response = requests.get(url, params=params)
        response.raise_for_status()
        pages = response.json().get("data", [])

        if pages:
            page_id = pages[0]["id"]
            url = f"https://graph.facebook.com/{API_VERSION}/{page_id}?fields=instagram_business_account&access_token={access_token}"
            response = requests.get(url)
            response.raise_for_status()
            return response.json().get("instagram_business_account", {}).get("id")
        return None

    def upload_video_to_instagram(
        self, access_token, instagram_account_id, video_url, caption
    ):
        # Step 1: Create a container
        container_url = (
            f"https://graph.facebook.com/{API_VERSION}/{instagram_account_id}/media"
        )
        params = {
            "access_token": access_token,
            "media_type": "REELS",
            "video_url": video_url,
            "caption": caption,
        }
        response = requests.post(container_url, data=params)
        creation_id = response.json().get("id")

        if not creation_id:
            return "Failed to create media container"

        # Step 2: Publish the container
        publish_url = f"https://graph.facebook.com/{API_VERSION}/{instagram_account_id}/media_publish"
        params = {"access_token": access_token, "creation_id": creation_id}
        response = requests.post(publish_url, data=params)

        if response.status_code == 200:
            return f"Video uploaded successfully. Media ID: {response.json().get('id')}"
        else:
            return f"Failed to publish video. Error: {response.text}"

    def schedule_to_upload(self, user_data, video_data, upload_domain, scheduled_time):

        metadata = video_data.get("metadata")

        # Choose the appropriate category ID for your videos
        video_category_id = "28"  # Science & Technology
        privacyStatus = "public"  # "public", "private", "unlisted"

        schedule_video_data = {
            "user_id": ObjectId(user_data["_id"]),
            "video_id": ObjectId(video_data["_id"]),
            "metadata": {
                "title": metadata.get("title"),
                "description": metadata["description"],
                "caption": metadata.get("caption"),
                "category": video_category_id,
                "keywords": ",".join(metadata.get("keywords")),
                "privacyStatus": privacyStatus,
            },
            "video_link": video_data["link"],
            "thumbnail_link": video_data.get("thumbnail_link"),
            "status": ScheduleVideoStatus.SCHEDULED,
            "scheduled_time": scheduled_time,
            "upload_domain": upload_domain,
        }

        try:

            data = self.schedule_video_repository.create_schedule_video(
                schedule_video_data
            )

            scheduler.create_job_to_upload(
                str(data["_id"]),
                scheduled_time,
            )

            return self.schedule_video_repository.to_dict(data)

        except HttpError as e:
            print(f"An HTTP error {e.resp.status} occurred:\n{e.content}")

    def upload_schedule_video(self, video_data):

        video_data = self.schedule_video_repository.get_schedule_video_by_id(
            video_data["schedule_video_id"]
        )

        print("Uploading video testing", video_data)

        user_data = self.auth_repository.find_user_by_id(str(video_data["user_id"]))

        if video_data.get("upload_domain") == UploadDomain.LINKEDIN.value:

            video_data = self.video_repository.get_video_by_id(
                str(video_data["video_id"])
            )
            credential = user_data.get("linkedin_credentials")
            linkedin_uploader = LinkedInUploader(
                credential.get("access_token"), credential.get("sub")
            )
            response = linkedin_uploader.upload_video(user_data, video_data)
            return response

        # Choose the appropriate category ID for your videos
        video_category_id = "28"  # Science & Technology
        privacyStatus = "public"  # "public", "private", "unlisted"

        video_path = save_video(video_data["video_link"], str(video_data["video_id"]))

        metadata = video_data.get("metadata")

        video_metadata = {
            "video_path": video_path,
            "title": metadata["title"],
            "description": metadata["description"],
            "category": video_category_id,
            "keywords": ",".join(metadata["keywords"]),
            "privacyStatus": privacyStatus,
        }

        # Upload the video to YouTube
        try:
            # Unpack the video_metadata dictionary into individual arguments
            video_response = upload_video(
                email=user_data["email"],
                youtube_credentials=user_data["youtube_credentials"],
                video_path=video_metadata["video_path"],
                title=video_metadata["title"],
                description=video_metadata["description"],
                category=video_metadata["category"],
                keywords=video_metadata["keywords"],
                privacy_status=video_metadata["privacyStatus"],
            )
            print(f"Uploaded video ID: {video_response.get('id')}")

            self.schedule_video_repository.update_schedule_video(
                str(video_data["_id"]),
                {
                    "status": ScheduleVideoStatus.UPLOADED,
                    "youtube_video_id": video_response.get("id"),
                },
            )
            remove_file(video_path)

            self.upload_video_repo.create_uploaded_video(
                {
                    "video_id": ObjectId(str(video_data["_id"])),
                    "user_id": ObjectId(str(user_data["_id"])),
                    "upload_video_id": video_response.get("id"),
                    "upload_link": f"https://www.youtube.com/watch?v={video_response.get("id")}",
                    "upload_domain": UploadDomain.YOUTUBE.value,
                }
            )

            self.send_email(
                user_data,
                video_response.get("id"),
                EmailType.VIDEO_UPLOADED.value,
            )

            return {"id": video_response.get("id")}
        except HttpError as e:
            self.schedule_video_repository.update_schedule_video(
                str(video_data["_id"]),
                {"status": ScheduleVideoStatus.FAILED, "error_message": str(e)},
            )
            remove_file(video_path)
            print(f"An HTTP error {e.resp.status} occurred:\n{e.content}")

    def update_schedule_video(self, user_id, video_id, update_data):

        schedule_video = (
            self.schedule_video_repository.get_schedule_video_by_id_and_user(
                video_id, user_id
            )
        )
        if not schedule_video:
            raise NotFound(f"ScheduleVideo {id} doesn't exist")

        if update_data.get("scheduled_time"):

            scheduler.delete_job(video_id)

            scheduler.create_job_to_upload(
                video_id,
                update_data.get("scheduled_time"),
            )

        video_data = self.schedule_video_repository.update_schedule_video(
            video_id, update_data
        )

        return self.schedule_video_repository.to_dict(video_data)

    def delete_schedule_video(self, user_id, video_id):
        schedule_video = (
            self.schedule_video_repository.get_schedule_video_by_id_and_user(
                video_id, user_id
            )
        )

        if not schedule_video:
            raise NotFound(f"ScheduleVideo {id} doesn't exist")

        scheduler.delete_job(video_id)

        return self.schedule_video_repository.delete_schedule_video(user_id, video_id)

    def schedule_generate_video(
        self,
        user_id,
        video_data,
        upload_domain,
        scheduled_time,
    ):

        schedule_video_data = {
            "user_id": ObjectId(user_id),
            "video_id": ObjectId(video_data["_id"]),
            "metadata": {},
            "type": ScheduleType.GENERATE,
            "video_link": None,
            "thumbnail_link": None,
            "status": ScheduleVideoStatus.SCHEDULED,
            "scheduled_time": scheduled_time,
            "upload_domain": upload_domain,
        }

        try:

            data = self.schedule_video_repository.create_schedule_video(
                schedule_video_data
            )

            return self.schedule_video_repository.to_dict(data)

        except HttpError as e:
            print(f"An HTTP error {e.resp.status} occurred:\n{e.content}")
