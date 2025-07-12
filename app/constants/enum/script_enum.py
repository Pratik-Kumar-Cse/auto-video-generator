from enum import Enum


class ScriptType(str, Enum):
    VIDEO = "VIDEO"
    TOPIC = "TOPIC"
    SCRIPT = "SCRIPT"
    BLOG = "BLOG"
    AI = "AI"


class ScriptStatus(str, Enum):
    DRAFT = "draft"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
