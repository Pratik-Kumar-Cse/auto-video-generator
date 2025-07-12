from enum import Enum


class NotificationType(str, Enum):
    NEWS = "news"
    ALERT = "alert"
    UPDATE = "update"
    REMINDER = "reminder"
