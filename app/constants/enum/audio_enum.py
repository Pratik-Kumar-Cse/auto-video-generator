from enum import Enum


class Status(str, Enum):
    PENDING = "PENDING"
    FAILED = "FAILED"
    COMPLETED = "COMPLETED"


# Enums for status and types
class AudioStatus(str, Enum):
    COMPLETED = "completed"


class PlayHtWebhookProcessStatus(str, Enum):
    QUEUED = "queued"
    COMPLETE = "complete"
    ERROR = "error"
