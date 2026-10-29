"""Reusable authentication and authorization dependencies."""

from __future__ import annotations

from typing import Annotated, Optional

from fastapi import Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from starlette import status

from database import get_db
from models import User
from security import InvalidTokenError, decode_access_token


TOKEN_COOKIE = "daymark_session"
oauth2_bearer = OAuth2PasswordBearer(tokenUrl="/auth/token", auto_error=False)

DbSession = Annotated[Session, Depends(get_db)]


def _token_from_request(request: Request, bearer_token: Optional[str]) -> Optional[str]:
    return request.cookies.get(TOKEN_COOKIE) or bearer_token


def resolve_session_token(token: Optional[str], db: Session) -> Optional[User]:
    """Resolve a JWT to a live, active user. Used by dependencies and errors."""

    if not token:
        return None

    try:
        payload = decode_access_token(token)
    except InvalidTokenError:
        return None

    user = db.get(User, payload["user_id"])
    if user is None or not user.is_active:
        return None
    return user


def user_from_cookie(request: Request, db: Session) -> Optional[User]:
    """Convenience helper for exception handlers outside the dependency graph."""

    return resolve_session_token(request.cookies.get(TOKEN_COOKIE), db)


def get_optional_user(
    request: Request,
    db: DbSession,
    bearer_token: Annotated[Optional[str], Depends(oauth2_bearer)] = None,
) -> Optional[User]:
    """Return the signed-in user, or None. Never raises for anonymous visitors."""

    return resolve_session_token(_token_from_request(request, bearer_token), db)


def get_current_user(
    request: Request,
    user: Annotated[Optional[User], Depends(get_optional_user)],
) -> User:
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Please sign in to continue.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
OptionalUser = Annotated[Optional[User], Depends(get_optional_user)]


def require_admin(user: CurrentUser) -> User:
    if user.role != "admin" or user.admin_slot is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator access is required.",
        )
    return user


AdminUser = Annotated[User, Depends(require_admin)]
