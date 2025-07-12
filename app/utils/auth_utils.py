"""
Authentication utilities for FastAPI Video Generation Service
Handles JWT token encoding/decoding and encryption
"""

import base64
import secrets
import string
from datetime import datetime, timedelta
from typing import Optional, Tuple

import jwt
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from app.core.config import settings
from app.core.exceptions import AuthenticationException


def encrypt_data(data: str) -> str:
    """
    Encrypts the provided data using Fernet symmetric encryption.

    Args:
        data: The plaintext data to encrypt.

    Returns:
        The encrypted data as a base64 encoded string.
    """
    fernet = Fernet(settings.SECRET_KEY.encode())
    encrypted = fernet.encrypt(data.encode())
    return encrypted.decode()


def decrypt_data(encrypted_data: str) -> str:
    """
    Decrypts the provided data using Fernet symmetric encryption.

    Args:
        encrypted_data: The encrypted data as a base64 encoded string to
                       decrypt.

    Returns:
        The decrypted data in plaintext.
    """
    fernet = Fernet(settings.SECRET_KEY.encode())
    decrypted = fernet.decrypt(encrypted_data.encode())
    return decrypted.decode()


def encode_auth_token(
    user_id: str, user_agent: str, ip_address: str, role: str
) -> str:
    """
    Generates an encrypted authentication token for a user.

    Args:
        user_id: The user's unique identifier.
        user_agent: The user agent string of the user's device.
        ip_address: The IP address of the user's device.
        role: Specifies whether the user is a normal user or an admin.

    Returns:
        The encrypted authentication token.

    Raises:
        AuthenticationException: If there's an error during token generation.
    """
    try:
        encrypted_user_id = encrypt_data(user_id)

        payload = {
            "exp": datetime.utcnow()
            + timedelta(hours=int(settings.TOKEN_EXPIRY_IN_HOUR), seconds=5),
            "iat": datetime.utcnow(),
            "sub": encrypted_user_id,
            "ip": ip_address,
            "ua": user_agent,
            "role": role,
        }

        auth_token = jwt.encode(
            payload, settings.SECRET_KEY, algorithm="HS256"
        )
        encrypted_auth_token = encrypt_data(auth_token)

        return encrypted_auth_token

    except Exception as e:
        raise AuthenticationException(f"Failed to encode auth token: {str(e)}")


def decode_auth_token(auth_token: str) -> Tuple[str, str, str, str]:
    """
    Decodes an encrypted authentication token to retrieve user information.

    Args:
        auth_token: The encrypted authentication token to decode.

    Returns:
        Tuple containing (user_id, ip_address, user_agent, role)

    Raises:
        AuthenticationException: If the token is invalid or expired.
    """
    try:
        decrypted_auth_token = decrypt_data(auth_token)
        payload = jwt.decode(
            decrypted_auth_token, settings.SECRET_KEY, algorithms=["HS256"]
        )
        encrypted_user_id = payload["sub"]

        user_id = decrypt_data(encrypted_data=encrypted_user_id)
        ip_address: str = payload["ip"]
        user_agent: str = payload["ua"]
        role: str = payload["role"]

        return user_id, ip_address, user_agent, role

    except jwt.ExpiredSignatureError:
        raise AuthenticationException("Token has expired")
    except jwt.InvalidTokenError:
        raise AuthenticationException("Invalid token")
    except Exception as e:
        raise AuthenticationException(f"Failed to decode auth token: {str(e)}")


def encode_refresh_token(
    user_id: str, exp: Optional[datetime] = None
) -> str:
    """
    Generates an encrypted refresh token for a user.

    Args:
        user_id: The user's unique identifier.
        exp: The expiration time for the refresh token. If not provided,
             it defaults to 30 days from the current time.

    Returns:
        The encrypted refresh token.

    Raises:
        AuthenticationException: If there's an error during token generation.
    """
    try:
        encrypted_user_id = encrypt_data(user_id)
        
        if exp is None:
            exp = datetime.utcnow() + timedelta(days=30)
            
        payload = {
            "exp": exp,
            "iat": datetime.utcnow(),
            "sub": encrypted_user_id,
            "is_refresh_token": True,
        }
        
        refresh_token = jwt.encode(
            payload, settings.SECRET_KEY, algorithm="HS256"
        )
        encrypted_refresh_token = encrypt_data(refresh_token)
        
        return encrypted_refresh_token
        
    except Exception as e:
        raise AuthenticationException(
            f"Failed to encode refresh token: {str(e)}"
        )


def decode_refresh_token(refresh_token: str) -> Tuple[str, bool]:
    """
    Decodes an encrypted refresh token to retrieve the user ID.

    Args:
        refresh_token: The encrypted refresh token to decode.

    Returns:
        Tuple containing (user_id, is_refresh_token)

    Raises:
        AuthenticationException: If the token is invalid or has expired.
    """
    try:
        decrypted_refresh_token = decrypt_data(refresh_token)
        payload = jwt.decode(
            decrypted_refresh_token, settings.SECRET_KEY, algorithms=["HS256"]
        )
        encrypted_user_id = payload["sub"]
        user_id = decrypt_data(encrypted_data=encrypted_user_id)
        is_refresh_token = payload.get("is_refresh_token", False)
        
        return user_id, is_refresh_token

    except jwt.ExpiredSignatureError:
        raise AuthenticationException("Refresh token has expired")
    except jwt.InvalidTokenError:
        raise AuthenticationException("Invalid refresh token")
    except Exception as e:
        raise AuthenticationException(f"Invalid refresh token: {str(e)}")


def generate_password(length: int = 16) -> str:
    """
    Generates a strong password.

    Args:
        length: The length of the password. Default is 16 characters.

    Returns:
        The generated password.
    """
    alphabet = string.ascii_letters + string.digits + string.punctuation
    password = "".join(secrets.choice(alphabet) for i in range(length))
    
    # Ensure password complexity
    while not is_password_complex(password):
        password = "".join(secrets.choice(alphabet) for i in range(length))
    
    return password


def is_password_complex(password: str) -> bool:
    """
    Verifies if the provided password meets complexity requirements.

    Args:
        password: The password to be validated.

    Returns:
        True if the password is complex, False otherwise.
    """
    import re
    
    min_length = 8
    if len(password) < min_length:
        return False

    if not re.search(r"[A-Z]", password):
        return False

    if not re.search(r"[a-z]", password):
        return False

    if not re.search(r"\d", password):
        return False

    if not re.search(r"[!@#$%^&*]", password):
        return False

    return True


def create_secret_key() -> str:
    """
    Creates a secret key using PBKDF2HMAC.
    
    Returns:
        Base64 encoded secret key
    """
    password = "video_generator_secret"
    key_length = 32
    salt = b"video_generator_salt"
    iterations = 100000

    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=key_length,
        salt=salt,
        iterations=iterations,
    )

    key = kdf.derive(password.encode())
    base64_key = base64.b64encode(key).decode()
    
    return base64_key


def get_token_from_header(authorization: Optional[str]) -> Optional[str]:
    """
    Extract token from Authorization header.
    
    Args:
        authorization: Authorization header value
        
    Returns:
        Token string if found, None otherwise
    """
    if authorization and authorization.startswith("Bearer "):
        return authorization.split(" ")[1]
    return None