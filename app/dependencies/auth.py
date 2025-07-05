"""
Authentication dependencies for FastAPI
"""

from typing import Dict, Any
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.database import get_database
from app.services.auth_service import AuthService
from app.core.exceptions import (
    AuthenticationError,
    AuthorizationError,
    UserNotFoundError
)

# Security scheme
security = HTTPBearer()


async def get_auth_service(
    db: AsyncIOMotorDatabase = Depends(get_database)
) -> AuthService:
    """Get authentication service instance"""
    return AuthService(db)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_service: AuthService = Depends(get_auth_service)
) -> Dict[str, Any]:
    """
    Get current authenticated user from JWT token
    """
    try:
        token = credentials.credentials
        
        # Check if token is blacklisted
        if await auth_service.is_token_blacklisted(token):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has been revoked",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Get user from token
        user = await auth_service.get_current_user(token)
        return user
        
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )
    except UserNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication service error",
        )


async def get_current_active_user(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get current active user (must be active)
    """
    if not current_user.get("is_active", False):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user


async def get_admin_user(
    current_user: Dict[str, Any] = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Get current user if they are admin
    """
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


def require_permission(permission: str):
    """
    Dependency factory for permission-based access control
    """
    async def permission_checker(
        current_user: Dict[str, Any] = Depends(get_current_active_user),
        auth_service: AuthService = Depends(get_auth_service)
    ) -> Dict[str, Any]:
        try:
            user_id = current_user["_id"]
            has_permission = await auth_service.check_user_permissions(
                user_id, permission
            )
            
            if not has_permission:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission '{permission}' required"
                )
            
            return current_user
            
        except AuthorizationError as e:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=str(e)
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Permission check failed"
            )
    
    return permission_checker


async def get_optional_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_service: AuthService = Depends(get_auth_service)
) -> Dict[str, Any] | None:
    """
    Get current user if token is provided, otherwise return None
    Used for endpoints that work for both authenticated and anonymous users
    """
    if not credentials:
        return None
    
    try:
        token = credentials.credentials
        
        # Check if token is blacklisted
        if await auth_service.is_token_blacklisted(token):
            return None
        
        # Get user from token
        user = await auth_service.get_current_user(token)
        return user
        
    except (AuthenticationError, UserNotFoundError):
        return None
    except Exception:
        return None


# Dependency for extracting user ID from current user
async def get_current_user_id(
    current_user: Dict[str, Any] = Depends(get_current_active_user)
) -> str:
    """Extract user ID from current user"""
    return current_user["_id"]


# Dependency for checking if user owns a resource
def require_resource_owner(resource_user_id_field: str = "user_id"):
    """
    Dependency factory for checking resource ownership
    """
    async def ownership_checker(
        resource_data: Dict[str, Any],
        current_user: Dict[str, Any] = Depends(get_current_active_user)
    ) -> Dict[str, Any]:
        resource_user_id = resource_data.get(resource_user_id_field)
        current_user_id = current_user["_id"]
        
        # Admin can access any resource
        if current_user.get("role") == "admin":
            return current_user
        
        # Check ownership
        if resource_user_id != current_user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: You don't own this resource"
            )
        
        return current_user
    
    return ownership_checker