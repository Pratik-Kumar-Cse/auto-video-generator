import httplib2  # type: ignore
import http.client

DEFAULT_PROFILE = "https://ciny-dev.s3.amazonaws.com/ciny-dev/profile/default.png"


LINKEDIN_URL_PREFIX = "https://www.linkedin.com/feed/update/urn:li:ugcPost"


# Constants can be imported or defined here
class SSE_EVENT_NAME:
    SCRIPT_STREAM = "script_stream"
    VIDEO_STREAM = "video_stream"
    WORKFLOW_STREAM = "workflow_stream"


class AVATAR_GENERATION_STATUS:
    INPROGRESS = "inprogress"
    COMPLETED = "completed"
    FAILED = "failed"


# Authentication prefix
AUTH_PREFIX = "AUTH_"

# Redis auth expiration
REDIS_AUTH_EXPIRATION = 86400

# Redis keys
REDIS_KEYS = {"UPLOAD_VIDEO_IDS": "UPLOAD_VIDEO_IDS"}


# OTP Configuration
OTP_CONFIG = {
    "otpLength": 6,
    "otpExpiresTimes": 5 * 60 * 1000,  # 5 minutes
    "otpRegex": r"^(?:[1-9]\d*|0)$",  # not starting with 0 but contains 0
    "resendOtpTime": 60 * 1000,  # 60 seconds
}


# Time Constants
ONE_MIN_IN_SECONDS = 60
ONE_HOUR_IN_SECONDS = 3600

# Stats Field Names
STATS_FIELD_NAMES = {
    "TOTAL_VIDEOS": "totalVideos",
    "TOTAL_SHORTS": "totalShorts",
    "TOTAL_VIDEOS_GENERATED": "totalVideosGenerated",
    "TOTAL_SHORTS_GENERATED": "totalShortsGenerated",
    "TOTAL_VIDEOS_UPLOADED": "totalVideosUploaded",
    "TOTAL_SHORTS_UPLOADED": "totalShortsUploaded",
    "TOTAL_VIDEOS_BY_CEO": "totalVideosByCEO",
    "TOTAL_VIDEOS_BY_CTO": "totalVideosByCTO",
    "TOTAL_VIDEOS_UPLOADED_TO_YT": "totalVideosUploadedToYT",
    "TOTAL_VIDEOS_UPLOADED_TO_LINKEDIN": "totalVideosUploadedToLinkedIn",
    "TOTAL_VIDEOS_UPLOADED_TO_TIKTOK": "totalVideosUploadedToTikTok",
    "TOTAL_SCHEDULE_VIDEOS": "totalScheduledVideos",
}


# Video Logs Main States
VIDEO_LOGS_MAINSTATES = {
    "VOICE_GENERATION": "voice_generation",
    "AVATAR_GENERATION": "avatar_generation",
    "VIDEO_GENERATION": "video_generation",
}


# N/A String
NA_STRING = "N/A"
REFERRAL_CREDITS = 3

# YOUTUBE CONSTS
VALID_PRIVACY_STATUSES = ("public", "private", "unlisted")
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"
RETRYABLE_STATUS_CODES = [500, 502, 503, 504]
MAX_RETRIES = 10


RETRYABLE_EXCEPTIONS = (
    httplib2.HttpLib2Error,
    IOError,
    http.client.NotConnected,
    http.client.IncompleteRead,
    http.client.ImproperConnectionState,
    http.client.CannotSendRequest,
    http.client.CannotSendHeader,
    http.client.ResponseNotReady,
    http.client.BadStatusLine,
)


class RESPONSE_MESSAGE:
    INVALID_VIDEO_ID = "Invalid video ID"
    VIDEO_ID_DOES_NOT_EXIST = "Video ID does not exist"
    AUDIO_DOES_NOT_EXIST = "Audio does not exist"
    AUDIO_ALREADY_GENERATED = "Audio already generated"
    VOICE_GENERATED = "Voice generated successfully"
    VOICE_SYNCED = "Voice synced successfully"
    WEBHOOK_RECEIVED = "Webhook received"
    UNKNOWN_WEBHOOK_STATUS = "Unknown webhook status"
    VOICE_ALREADY_SAVED_WITH_ROLE = "Voice already saved with this role"
    VOICE_DOES_NOT_EXIST = "Voice does not exist"
    DATA_SAVED_SUCCESS = "SAVE DATA SUCCESSFUL"


# VIDEO STATES
VIDEO_STATES = {
    "STARTED": "Video Creation Process Initiated",
    "DATA_RETRIEVAL_STARTED": "Started fetching video data",
    "DATA_RETRIEVED": "Video Data Successfully Retrieved",
    "START_URL_EXTRACTION": "Started extracting intro, outro and avatar video urls",
    "URLS_EXTRACTED": "Extracted Required URLs",
    "START_DOWNLOADING": "Downloading of Video Assets Started",
    "END_DOWNLOAD": "All Video Assets Downloaded",
    "START_UPLOADING": "Uploading Process Started",
    "UPLOADED": "Videos Combined and Uploaded",
    "DELETE_FILES": "Temporary Files Being Deleted",
    "UPDATE_VIDEO": "Video Status Being Updated",
    "VIDEO_CREATED": "Video Creation Process Completed",
    "SCRIPT_STARTED": "Script generation started",
    "SCRIPT_GENERATED": "Script generated successfully.",
    "SCRIPT_GENERATION_FAILED": "Script generation failed.",
    "VIDEO_GENERATION_FAILED": "Video generation failed.",
    "VIDEO_GENERATION_TASK_CREATED": "Video generation task created",
    "METADATA_GENERATION": "Metadata generation started",
    "METADATA_GENERATED": "Metadata generated",
    "AUDIO_GENERATION_STARTED": "Audio generation started",
    "AUDIO_GENERATED": "Audio generated successfully",
    "SUBTITLE_GENERATED": "Subtitle generated",
    "VIDEO_TITLE_GENERATED": "Video title generated",
    "STOCK_VIDEO_GENERATED": "Stock video generated",
    "IMAGE_VIDEO_GENERATED": "image video generated",
    "AVATAR_VIDEO_GENERATION": "Avatar video generation started",
    "STOCK_VIDEO_GENERATION": "Stock video generation started",
    "AVATAR_VIDEO_GENERATED": "Avatar video generated",
    "VIDEO_UPLOADING": "Video upload in progress",
    "VIDEO_UPLOAD_FAILED": "Video upload failed",
    "STARTED_UPDATING_VIDEO_THUMBNAIL": "Started updating video thumbnail",
    "END_UPDATING_VIDEO_THUMBNAIL": "Ended updating video thumbnail",
}


# Folder paths const
THUMBNAIL_FOLDER = "./thumbnails"


API_PREFIX = "/api/v1"

CINY_WORKFLOW_ID = "456173c8-9547-4800-b171-5527df3f6f89"


WORKFLOW_WEBHOOK_ENDPOINT = "/api/v1/workflow/webhook"
