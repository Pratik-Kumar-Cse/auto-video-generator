from enum import Enum


class Status(str, Enum):
    ACTIVE = "active"
    INACTIVATE = "inactive"


class UserProfileActions(Enum):
    GET = "GET"
    UPDATE = "UPDATE"


class AvatarType(Enum):
    PHOTO = "PHOTO"
    VIDEO = "VIDEO"


class AccessTokenType(Enum):
    ACCESS_TOKEN = "access_token"
    VERIFY_OTP = "verify_otp"
    CHANGE_PASSWORD = "change_password"


class FileType(Enum):
    # Image formats
    JPG = "jpg"
    JPEG = "jpeg"
    PNG = "png"
    GIF = "gif"
    BMP = "bmp"
    TIFF = "tiff"
    WEBP = "webp"
    SVG = "svg"

    # Video formats
    MP4 = "mp4"
    AVI = "avi"
    MOV = "mov"
    MKV = "mkv"
    WMV = "wmv"
    FLV = "flv"
    WEBM = "webm"


class AwsFolderNames(Enum):
    PROFILE = "profile"
    BRAND_LOGO = "brand/logo"
    BRAND_INTRO = "brand/intro_videos"
    BRAND_OUTRO = "brand/outro_videos"


class DeleteTypes(Enum):
    INTRO = "intro"
    OUTRO = "outro"
    UNSAVED = "unsaved"


class IntroOutroTypeKeys(Enum):
    INTRO = DeleteTypes.INTRO.value
    OUTRO = DeleteTypes.OUTRO.value


class VideoGenerationTypes(Enum):
    ARTICLE = "article"
    NEWS = "news"


class VideoType(Enum):
    LONG = "long"
    SHORT = "short"


class VideoPublicMode(Enum):
    MANUAL = "manual"
    SCHEDULE = "schedule"
    REQUIRED_APPROVAL = "require_approval"


class VideoDuration(Enum):
    ONE = 1
    TWO = 2
    THREE = 3
    FIVE = 5
    TEN = 10
    FIFTEEN = 15
    TWENTY = 20
    THIRTY = 30


class PlayHtWebhookProcessStatus(Enum):
    QUEUED = "QUEUED"
    COMPLETE = "complete"
    ERROR = "error"


class TavusWebhookProcessStatus(Enum):
    READY = "ready"
    ERROR = "error"


class UpdateVideoStatus(Enum):
    COMPLETED = "completed"
    FAILED = "failed"
    UPLOADED = "uploaded"
    UPLOAD_FAILED = "upload_failed"


class VideoLogsType(Enum):
    VIDEO_GENERATION = "video_generation"
    VIDEO_UPLOAD = "video_upload"


class SortByForVideo(Enum):
    CREATED = "created"
    DURATION = "duration"
    SCHEDULE_TIME = "scheduleTime"
    PUBLISH_TIME = "publishingTime"


class SortOrder(Enum):
    ASC = "asc"
    DESC = "desc"


class ExternalAuthType(Enum):
    GOOGLE = "google"
    TIKTOK = "tiktok"
    LINKEDIN = "linkedin"


class UploadDomains(Enum):
    YOUTUBE = "youtube"
    TIKTOK = "tiktok"
    LINKEDIN = "linkedin"


class CalenderView(Enum):
    DAY = "day"
    MONTH = "month"
    WEEK = "week"


class VideoSize(Enum):
    PORTRAIT = "portrait"
    LANDSCAPE = "landscape"
    SQUARE = "square"


class AvatarPlatform(Enum):
    TAVUS = "tavus"
    HEYGEN = "heygen"


class HttpMethods(str, Enum):
    POST = "Post"
    PATCH = "Patch"
    DELETE = "Delete"
    GET = "Get"
    PUT = "Put"
