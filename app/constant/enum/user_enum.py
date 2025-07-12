from enum import Enum


class UserRole(str, Enum):
    ADMIN = "admin"
    USER = "user"


class WaitlistStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class AccountStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class EmailType(Enum):
    VIDEO_GENERATED = 1
    FORGOT_PASSWORD = 2
    NEW_PASSWORD = 3
    SIGNUP = 4
    VIDEO_GENERATION_FAILED = 5
    VIDEO_UPLOADED = 6
    WELCOME = 7
    DEACTIVATE = 8
    WAITLIST = 9
    WAITLIST_VERIFIED = 10
