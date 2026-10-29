"""The three-seat administrator console and developer access gate."""

from __future__ import annotations

import hmac
import time
from typing import Optional

from fastapi import APIRouter, Depends, Form, Query, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import case, func
from sqlalchemy.orm import Session, joinedload
from starlette import status

from admin_service import (
    AdminActionError,
    AdminLimitReached,
    AdminPolicyError,
    admin_count,
    admin_seats,
    available_admin_slots,
    delete_todo_as_admin,
    delete_user_account,
    demote_from_admin,
    promote_to_admin,
    set_user_active,
)
from config import ADMIN_ACCESS_KEY, DEVELOPER_EMAIL
from database import get_db
from dependencies import AdminUser, CurrentUser, require_admin
from models import AdminAudit, Todo, User, utcnow
from templating import templates
from web_utils import redirect_url


router = APIRouter(prefix="/admin", tags=["admin"])

# Small in-process guard against brute-forcing the developer key.
_KEY_ATTEMPTS: dict[int, list[float]] = {}
_KEY_WINDOW_SECONDS = 300
_KEY_MAX_ATTEMPTS = 5


def _rate_limited(user_id: int) -> bool:
    now = time.time()
    attempts = [stamp for stamp in _KEY_ATTEMPTS.get(user_id, []) if now - stamp < _KEY_WINDOW_SECONDS]
    _KEY_ATTEMPTS[user_id] = attempts
    return len(attempts) >= _KEY_MAX_ATTEMPTS


def _record_attempt(user_id: int) -> None:
    _KEY_ATTEMPTS.setdefault(user_id, []).append(time.time())


def _render_access(
    request: Request,
    user: User,
    *,
    error: Optional[str] = None,
    status_code: int = status.HTTP_200_OK,
):
    response = templates.TemplateResponse(
        request,
        "admin_access.html",
        {
            "request": request,
            "user": user,
            "error": error,
            "developer_email": DEVELOPER_EMAIL,
            "has_key": bool(ADMIN_ACCESS_KEY),
        },
        status_code=status_code,
    )
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Robots-Tag"] = "noindex, nofollow"
    return response


@router.get("")
def admin_dashboard(
    request: Request,
    user: AdminUser,
    db: Session = Depends(get_db),
    message: Optional[str] = Query(default=None),
    kind: str = Query(default="success"),
    welcome: bool = Query(default=False),
):
    users = (
        db.query(User)
        .order_by(case((User.role == "admin", 0), else_=1), User.created_at.desc())
        .all()
    )
    task_counts = dict(
        db.query(Todo.owner_id, func.count(Todo.id))
        .group_by(Todo.owner_id)
        .all()
    )
    completed_counts = dict(
        db.query(Todo.owner_id, func.count(Todo.id))
        .filter(Todo.complete.is_(True))
        .group_by(Todo.owner_id)
        .all()
    )

    total_todos = int(db.query(func.count(Todo.id)).scalar() or 0)
    completed_todos = int(
        db.query(func.count(Todo.id)).filter(Todo.complete.is_(True)).scalar() or 0
    )
    overdue_todos = int(
        db.query(func.count(Todo.id))
        .filter(
            Todo.complete.is_(False),
            Todo.deadline.isnot(None),
            Todo.deadline < utcnow(),
        )
        .scalar()
        or 0
    )
    active_users = int(
        db.query(func.count(User.id)).filter(User.is_active.is_(True)).scalar() or 0
    )

    recent_todos = (
        db.query(Todo)
        .options(joinedload(Todo.owner))
        .order_by(Todo.created_at.desc())
        .limit(8)
        .all()
    )
    audit_entries = (
        db.query(AdminAudit)
        .options(joinedload(AdminAudit.actor))
        .order_by(AdminAudit.created_at.desc())
        .limit(10)
        .all()
    )

    response = templates.TemplateResponse(
        request,
        "admin.html",
        {
            "request": request,
            "user": user,
            "users": users,
            "task_counts": task_counts,
            "completed_counts": completed_counts,
            "total_todos": total_todos,
            "completed_todos": completed_todos,
            "overdue_todos": overdue_todos,
            "active_users": active_users,
            "admin_count": admin_count(db),
            "admin_seats": admin_seats(db),
            "free_slots": available_admin_slots(db),
            "recent_todos": recent_todos,
            "audit_entries": audit_entries,
            "message": message,
            "message_kind": kind,
            "welcome": welcome,
        },
    )
    response.headers["Cache-Control"] = "no-store"
    return response


@router.get("/")
def admin_dashboard_slash():
    return RedirectResponse(url="/admin", status_code=status.HTTP_308_PERMANENT_REDIRECT)


@router.get("/access")
def developer_access_page(request: Request, user: CurrentUser):
    if user.role == "admin":
        return RedirectResponse(
            url=redirect_url("/admin", "You already have administrator access."),
            status_code=status.HTTP_303_SEE_OTHER,
        )
    return _render_access(request, user)


@router.post("/access")
def developer_access_submit(
    request: Request,
    user: CurrentUser,
    access_key: str = Form(...),
    db: Session = Depends(get_db),
):
    if user.role == "admin":
        return RedirectResponse(url="/admin", status_code=status.HTTP_303_SEE_OTHER)

    if _rate_limited(user.id):
        return _render_access(
            request,
            user,
            error="Too many attempts. Wait five minutes and try again.",
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        )

    if DEVELOPER_EMAIL and user.email.lower() != DEVELOPER_EMAIL:
        _record_attempt(user.id)
        return _render_access(
            request,
            user,
            error="Developer access is restricted to a different account.",
            status_code=status.HTTP_403_FORBIDDEN,
        )

    if not hmac.compare_digest(
        access_key.strip().encode("utf-8"), ADMIN_ACCESS_KEY.encode("utf-8")
    ):
        _record_attempt(user.id)
        return _render_access(
            request,
            user,
            error="That developer key is not valid.",
            status_code=status.HTTP_403_FORBIDDEN,
        )

    try:
        slot = promote_to_admin(
            db, user, actor=user, action="admin.developer_access"
        )
    except AdminLimitReached as exc:
        return _render_access(
            request,
            user,
            error=str(exc),
            status_code=status.HTTP_409_CONFLICT,
        )
    except AdminActionError as exc:
        return _render_access(
            request,
            user,
            error=str(exc),
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    _KEY_ATTEMPTS.pop(user.id, None)
    return RedirectResponse(
        url=redirect_url(
            "/admin",
            f"Developer key accepted. You are admin in seat {slot} of 3.",
        ),
        status_code=status.HTTP_303_SEE_OTHER,
    )


def _back(message: str, kind: str = "success") -> RedirectResponse:
    return RedirectResponse(
        url=redirect_url("/admin", message, kind),
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.post("/users/{user_id}/role")
def change_role(
    user_id: int,
    action: str = Form(...),
    user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    target = db.get(User, user_id)
    if target is None:
        return _back("That account no longer exists.", "error")

    try:
        if action == "promote":
            slot = promote_to_admin(db, target, actor=user)
            return _back(f"@{target.username} now has admin seat {slot}.")
        if action == "demote":
            demote_from_admin(db, target, actor=user)
            return _back(f"@{target.username} is now a regular user.")
        return _back("Unknown role action.", "error")
    except AdminLimitReached as exc:
        return _back(str(exc), "error")
    except AdminPolicyError as exc:
        return _back(str(exc), "error")
    except AdminActionError as exc:
        return _back(str(exc), "error")


@router.post("/users/{user_id}/status")
def change_status(
    user_id: int,
    action: str = Form(...),
    user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    target = db.get(User, user_id)
    if target is None:
        return _back("That account no longer exists.", "error")

    try:
        set_user_active(db, target, actor=user, active=(action == "activate"))
    except AdminActionError as exc:
        return _back(str(exc), "error")
    return _back(
        f"@{target.username} is now {'active' if action == 'activate' else 'deactivated'}."
    )


@router.post("/users/{user_id}/delete")
def delete_user(
    user_id: int,
    user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    target = db.get(User, user_id)
    if target is None:
        return _back("That account no longer exists.", "error")

    try:
        label = delete_user_account(db, target, actor=user)
    except AdminActionError as exc:
        return _back(str(exc), "error")
    return _back(f"Deleted {label}.")


@router.post("/todos/{todo_id}/delete")
def delete_todo(
    todo_id: int,
    user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    todo = db.get(Todo, todo_id)
    if todo is None:
        return _back("That task no longer exists.", "error")
    try:
        label = delete_todo_as_admin(db, todo, actor=user)
    except AdminActionError as exc:
        return _back(str(exc), "error")
    return _back(f"Deleted task {label}.")
