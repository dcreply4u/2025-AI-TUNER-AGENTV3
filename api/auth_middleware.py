"""
Authentication Middleware for API Endpoints
Provides JWT-based authentication and authorization.
"""

from __future__ import annotations

import logging
import os
import time
from functools import wraps
from typing import Any, Callable, Optional

from fastapi import HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

try:
    from fastapi_jwt_auth import AuthJWT
    JWT_AVAILABLE = True
except ImportError:
    JWT_AVAILABLE = False
    AuthJWT = None  # type: ignore

LOGGER = logging.getLogger(__name__)

# Security scheme
security = HTTPBearer()


class AuthenticationError(HTTPException):
    """Authentication error."""
    def __init__(self, detail: str = "Authentication required"):
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)


class AuthorizationError(HTTPException):
    """Authorization error."""
    def __init__(self, detail: str = "Insufficient permissions"):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


def get_auth_jwt() -> Optional[AuthJWT]:
    """Get AuthJWT instance."""
    if not JWT_AVAILABLE:
        return None
    
    try:
        auth_jwt = AuthJWT()
        return auth_jwt
    except Exception as e:
        LOGGER.warning("Failed to initialize AuthJWT: %s", e)
        return None


async def verify_token(credentials: HTTPAuthorizationCredentials) -> dict[str, Any]:
    """
    Verify JWT token and return user info.
    
    Args:
        credentials: HTTP authorization credentials
    
    Returns:
        User information dictionary
    
    Raises:
        AuthenticationError: If token is invalid
    """
    if not JWT_AVAILABLE:
        # In development, allow if no JWT library
        if os.getenv("DEBUG_MODE", "false").lower() in {"1", "true", "yes"}:
            return {"user_id": "dev_user", "role": "user"}
        raise AuthenticationError("JWT authentication not available")
    
    auth_jwt = get_auth_jwt()
    if not auth_jwt:
        raise AuthenticationError("Authentication service unavailable")
    
    try:
        # Verify token
        auth_jwt.jwt_required()
        current_user = auth_jwt.get_jwt_subject()
        jwt_data = auth_jwt.get_raw_jwt()
        
        return {
            "user_id": current_user,
            "role": jwt_data.get("role", "user"),
            "email": jwt_data.get("email"),
            "permissions": jwt_data.get("permissions", []),
        }
    except Exception as e:
        LOGGER.warning("Token verification failed: %s", e)
        raise AuthenticationError("Invalid or expired token")


def require_auth(func: Callable) -> Callable:
    """
    Decorator to require authentication.
    
    Usage:
        @require_auth
        async def my_endpoint(request: Request):
            user = request.state.user
            ...
    """
    @wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        request = None
        for arg in args:
            if isinstance(arg, Request):
                request = arg
                break
        
        if not request:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Request object not found"
            )
        
        # Get credentials
        credentials = await security(request)
        if not credentials:
            raise AuthenticationError()
        
        # Verify token
        user_info = await verify_token(credentials)
        request.state.user = user_info
        
        return await func(*args, **kwargs)
    
    return wrapper


def require_role(role: str):
    """
    Decorator to require specific role.
    
    Usage:
        @require_role("admin")
        async def admin_endpoint(request: Request):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            
            if not request:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Request object not found"
                )
            
            # Check if authenticated
            if not hasattr(request.state, "user"):
                # Try to authenticate
                credentials = await security(request)
                if credentials:
                    user_info = await verify_token(credentials)
                    request.state.user = user_info
                else:
                    raise AuthenticationError()
            
            user = request.state.user
            user_role = user.get("role", "user")
            
            # Check role
            if user_role != role and user_role != "admin":
                raise AuthorizationError(f"Requires {role} role")
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def require_permission(permission: str):
    """
    Decorator to require specific permission.
    
    Usage:
        @require_permission("tuning:write")
        async def tuning_endpoint(request: Request):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            
            if not request:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Request object not found"
                )
            
            # Check if authenticated
            if not hasattr(request.state, "user"):
                credentials = await security(request)
                if credentials:
                    user_info = await verify_token(credentials)
                    request.state.user = user_info
                else:
                    raise AuthenticationError()
            
            user = request.state.user
            permissions = user.get("permissions", [])
            
            # Admin has all permissions
            if user.get("role") == "admin":
                return await func(*args, **kwargs)
            
            # Check permission
            if permission not in permissions:
                raise AuthorizationError(f"Requires {permission} permission")
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


