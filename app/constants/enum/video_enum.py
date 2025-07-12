from enum import Enum


class VideoTypeByCategory(Enum):
    # By Purpose
    PROMOTIONAL = "Promotional Video"
    EDUCATIONAL = "Educational Video"
    CORPORATE = "Corporate Video"
    ENTERTAINMENT = "Entertainment Video"
    EXPLAINER = "Explainer Video"
    TESTIMONIAL = "Testimonial Video"
    EVENT = "Event Video"
    VLOG = "Vlog"

    # By Format
    LIVE_ACTION = "Live-Action Video"
    ANIMATION = "Animation Video"
    SCREEN_RECORDING = "Screen Recording Video"
    STOP_MOTION = "Stop Motion Video"
    TIME_LAPSE = "Time-Lapse Video"
    AI_GENERATED = "AI-Generated Video"

    # By Style
    DOCUMENTARY = "Documentary Style Video"
    CINEMATIC = "Cinematic Style Video"
    SOCIAL_MEDIA = "Social Media Video"
    INTERACTIVE = "Interactive Video"
    VR_360 = "VR/360° Video"

    # By Content
    STORYTELLING = "Storytelling Video"
    PRODUCT_DEMO = "Product Demo Video"
    INTERVIEW = "Interview Video"
    BEHIND_THE_SCENES = "Behind-the-Scenes Video"
    COMPILATION = "Compilation Video"

    # By Production Techniques
    SINGLE_CAMERA = "Single-Camera Video"
    MULTI_CAMERA = "Multi-Camera Video"
    GREEN_SCREEN = "Green Screen Video"
    DRONE = "Drone Video"


class VideoType(str, Enum):
    SHORT = "SHORT"
    LONG = "LONG"


class VideoTypes(str, Enum):
    AI_VIDEO = "ai_video"
    NORMAL = "normal"
    STORY = "story"


class VideoViewType(str, Enum):
    LANDSCAPE = "LANDSCAPE"
    PORTRAIT = "PORTRAIT"
    SQUARE = "SQUARE"


class VideoStatus(str, Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    FAILED = "FAILED"
    COMPLETED = "COMPLETED"
    TIMED_OUT = "TIMED_OUT"


class ScheduleVideoStatus(str, Enum):
    SCHEDULED = "SCHEDULED"
    UPLOADED = "UPLOADED"
    FAILED = "FAILED"
    COMPLETED = "COMPLETED"
    GENERATED = "GENERATED"


class ScheduleType(str, Enum):
    GENERATE = "GENERATE"
    UPLOAD = "UPLOAD"
    AUTO_UPLOAD = "AUTO_UPLOAD"


class VideoQuality(str, Enum):
    Q480p = "480p"
    Q720p = "720p"
    Q1080p = "1080p"
    Q4k = "4k"


class UploadDomain(str, Enum):
    YOUTUBE = "youtube"
    LINKEDIN = "linkedin"  #
    INSTAGRAM = "instagram"


class VideoProcessingTypes(Enum):
    GENERATE_VIDEO = "generate_video"
    UPLOAD_VIDEO = "upload_video"
    AUTO_UPLOAD = "auto_upload"


class VideoPublishModes(Enum):
    MANUAL = "manual"
    SCHEDULE = "schedule"
    REQUIRED_APPROVAL = "require_approval"


class SocialMediaTypes(Enum):
    GOOGLE = "google"
    TIKTOK = "tiktok"
    LINKEDIN = "linkedin"
