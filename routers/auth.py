"""Registration, login and logout pages."""

from __future__ import annotations

import re
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from starlette import status

from config import COOKIE_SECURE
from database import get_db
from dependencies import TOKEN_COOKIE, get_optional_user
from models import User, utcnow
from security import cookie_max_age, create_access_token, hash_password, verify_password
from templating import templates
from web_utils import redirect_url, safe_next


router = APIRouter(prefix="/auth", tags=["auth"])

USERNAME_RE = re.compile(r"^[a-z0-9_]{3,30}$")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

# Verifying a dummy hash for unknown usernames reduces username-timing leaks.
_DUMMY_HASH = hash_password("not-a-real-daymark-password")


def _render_login(
    request: Request,
    *,
    error: str | None = None,
    username: str = "",
    next_url: str = "/todos",
    status_code: int = status.HTTP_200_OK,
):
    return templates.TemplateResponse(
        request,
        "login.html",
        {
            "request": request,
            "error": error,
            "username": username,
            "next_url": safe_next(next_url),
            "registered": request.query_params.get("registered") == "1",
            "logged_out": request.query_params.get("logged_out") == "1",
        },
        status_code=status_code,
    )


def _render_register(
    request: Request,
    *,
    error: str | None = None,
    form: dict | None = None,
    status_code: int = status.HTTP_200_OK,
):
    return templates.TemplateResponse(
        request,
        "register.html",
        {
            "request": request,
            "error": error,
            "form": form or {},
        },
        status_code=status_code,
    )


@router.get("/login-page")
def login_page(
    request: Request,
    next: str = "/todos",
    user=Depends(get_optional_user),
):
    if user is not None:
        return RedirectResponse(
            url=safe_next(next), status_code=status.HTTP_303_SEE_OTHER
        )
    return _render_login(request, next_url=next)


@router.post("/login-page")
def login_user(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    next: str = Form("/todos"),
    db: Session = Depends(get_db),
):
    username_normalized = username.strip().lower()
    user: Optional[User] = (
        db.query(User).filter(func.lower(User.username) == username_normalized).first()
    )

    password_ok = verify_password(password, user.hashed_password if user else _DUMMY_HASH)
    if user is None or not password_ok:
        return _render_login(
            request,
            error="That username and password combination is not correct.",
            username=username,
            next_url=next,
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    if not user.is_active:
        return _render_login(
            request,
            error="This account is deactivated. Contact an administrator.",
            username=username,
            next_url=next,
            status_code=status.HTTP_403_FORBIDDEN,
        )

    user.last_login_at = utcnow()
    db.commit()

    token = create_access_token(user_id=user.id, username=user.username)
    destination = safe_next(next)
    response = RedirectResponse(url=destination, status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(
        key=TOKEN_COOKIE,
        value=token,
        max_age=cookie_max_age(),
        httponly=True,
        samesite="lax",
        secure=COOKIE_SECURE,
        path="/",
    )
    return response


@router.get("/register-page")
def register_page(request: Request, user=Depends(get_optional_user)):
    if user is not None:
        return RedirectResponse(url="/todos", status_code=status.HTTP_303_SEE_OTHER)
    return _render_register(request)


@router.post("/register-page")
def register_user(
    request: Request,
    first_name: str = Form(...),
    last_name: str = Form(...),
    email: str = Form(...),
    username: str = Form(...),
    phone_number: str = Form(""),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    form = {
        "first_name": first_name.strip(),
        "last_name": last_name.strip(),
        "email": email.strip().lower(),
        "username": username.strip().lower(),
        "phone_number": phone_number.strip(),
    }

    if not form["first_name"] or len(form["first_name"]) > 60:
        return _render_register(request, error="Enter your first name.", form=form)
    if not form["last_name"] or len(form["last_name"]) > 60:
        return _render_register(request, error="Enter your last name.", form=form)
    if not EMAIL_RE.match(form["email"]) or len(form["email"]) > 254:
        return _render_register(request, error="Enter a valid email address.", form=form)
    if not USERNAME_RE.match(form["username"]):
        return _render_register(
            request,
            error="Username must be 3–30 characters using lowercase letters, numbers or underscores.",
            form=form,
        )
    if len(password) < 8:
        return _render_register(
            request, error="Password must be at least 8 characters.", form=form
        )
    if len(password.encode("utf-8")) > 72:
        return _render_register(
            request, error="Password must be 72 bytes or fewer.", form=form
        )
    if form["phone_number"] and len(form["phone_number"]) > 25:
        return _render_register(request, error="Phone number is too long.", form=form)

    duplicate = (
        db.query(User)
        .filter(
            (func.lower(User.email) == form["email"])
            | (func.lower(User.username) == form["username"])
        )
        .first()
    )
    if duplicate is not None:
        return _render_register(
            request, error="That username or email is already registered.", form=form
        )

    user = User(
        email=form["email"],
        username=form["username"],
        first_name=form["first_name"],
        last_name=form["last_name"],
        hashed_password=hash_password(password),
        phone_number=form["phone_number"] or None,
        role="user",
        admin_slot=None,
        is_active=True,
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        return _render_register(
            request, error="That username or email is already registered.", form=form
        )

    return RedirectResponse(
        url=redirect_url("/auth/login-page", "Account created. Sign in to begin."),
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.post("/token")
def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Session = Depends(get_db),
):
    """JSON token endpoint for API clients. Browser sessions use the cookie."""

    username_normalized = form_data.username.strip().lower()
    user = (
        db.query(User)
        .filter(func.lower(User.username) == username_normalized)
        .first()
    )
    password_ok = verify_password(
        form_data.password, user.hashed_password if user else _DUMMY_HASH
    )
    if user is None or not password_ok or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user.last_login_at = utcnow()
    db.commit()
    return {
        "access_token": create_access_token(user_id=user.id, username=user.username),
        "token_type": "bearer",
        "expires_in": cookie_max_age(),
    }


@router.post("/logout")
def logout_user():
    response = RedirectResponse(
        url="/auth/login-page?logged_out=1",
        status_code=status.HTTP_303_SEE_OTHER,
    )
    response.delete_cookie(TOKEN_COOKIE, path="/")
    return response
