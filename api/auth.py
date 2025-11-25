from __future__ import annotations

from typing import Any, Dict, Optional

import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi_jwt_auth import AuthJWT
from fastapi_jwt_auth.exceptions import AuthJWTException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, constr

from config import settings
from .users_db import create_user, get_user, has_users


class UserRegister(BaseModel):
    username: constr(strip_whitespace=True, min_length=3, max_length=64)  # type: ignore
    password: constr(min_length=6, max_length=128)  # type: ignore
    role: constr(strip_whitespace=True, min_length=3, max_length=32) = "viewer"  # type: ignore


class UserLogin(BaseModel):
    username: constr(strip_whitespace=True, min_length=3, max_length=64)  # type: ignore
    password: constr(min_length=6, max_length=128)  # type: ignore


@AuthJWT.load_config
def get_config() -> Any:
    return settings


def authenticate_user(username: str, password: str) -> Optional[Dict[str, str]]:
    user = get_user(username)
    if not user:
        return None
    if not bcrypt.checkpw(password.encode(), user["password_hash"].encode()):
        return None
    return user


def require_role(required_role: str):
    def wrapper(authorize: AuthJWT = Depends()):
        authorize.jwt_required()
        claims = authorize.get_raw_jwt()
        user_role = claims.get("role")
        if user_role not in {"admin", required_role}:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient privileges"
            )
        return claims

    return wrapper


def jwt_exception_handler(request, exc: AuthJWTException):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})


__all__ = [
    "UserRegister",
    "UserLogin",
    "authenticate_user",
    "require_role",
    "jwt_exception_handler",
    "create_user",
    "has_users",
]

