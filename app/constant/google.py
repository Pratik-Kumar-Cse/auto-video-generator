from enum import Enum


class Google(Enum):

    # Define login scope as a combination of 'profile', 'email', and SCOPES
    LOGIN_SCOPE = [
        "https://www.googleapis.com/auth/userinfo.profile",
        "https://www.googleapis.com/auth/userinfo.email",
        "openid",
    ]

    # Set GOOGLE_LOGIN constant as a string value
    GOOGLE_LOGIN = "google.login"

    NOT_REPEAT = "No Repeat"
