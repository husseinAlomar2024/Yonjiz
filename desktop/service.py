"""Direct SQLite service for the desktop app.

No HTTP, no localhost server, no network calls.  The UI talks to this object
inside the same process.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import case, func
from sqlalchemy.orm import Session, joinedload

from admin_service import (
    AdminActionError,
    AdminLimitReached,
    admin_count,
    admin_seats,
    available_admin_slots,
    delete_todo_as_admin,
    delete_user_account,
    demote_from_admin,
    log_action,
    primary_admin,
    promote_to_admin,
    set_user_active,
)
from database import SessionLocal
from models import AdminAudit, Todo, User, utcnow
from security import hash_password, verify_password


class DesktopError(Exception):
    pass


def _iso(value: Optional[datetime]) -> Optional[str]:
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _deadline_from_iso(value: Any) -> Optional[datetime]:
    if not value:
        return None
    if isinstance(value, datetime):
        parsed = value
    else:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc).replace(tzinfo=None)


def _user_dict(user: User) -> dict:
    return {
        "id": user.id,
        "email": user.email,
        "username": user.username,
        "full_name": user.full_name,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "initials": user.initials,
        "role": user.role,
        "admin_slot": user.admin_slot,
        "is_primary_admin": bool(user.is_primary_admin),
        "is_active": bool(user.is_active),
        "created_at": _iso(user.created_at),
    }


def _todo_dict(todo: Todo) -> dict:
    return {
        "id": todo.id,
        "title": todo.title,
        "description": todo.description or "",
        "priority": todo.priority,
        "complete": bool(todo.complete),
        "created_at": _iso(todo.created_at),
        "updated_at": _iso(todo.updated_at),
        "deadline": _iso(todo.deadline),
        "completed_at": _iso(todo.completed_at),
    }


class DesktopService:
    def __init__(self) -> None:
        self.current_user_id: Optional[int] = None

    # ------------------------------------------------------------------
    # Session and task data
    # ------------------------------------------------------------------
    def _current_user(self, db: Session) -> User:
        if self.current_user_id is None:
            raise DesktopError("Please sign in again.")
        user = db.get(User, self.current_user_id)
        if user is None or not user.is_active:
            self.current_user_id = None
            raise DesktopError("This account is no longer active.")
        return user

    def login(self, username: str, password: str) -> dict:
        username = (username or "").strip().lower()
        db = SessionLocal()
        try:
            user = (
                db.query(User)
                .filter(func.lower(User.username) == username)
                .first()
            )
            if user is None or not verify_password(password, user.hashed_password):
                raise DesktopError("That username and password combination is not correct.")
            if not user.is_active:
                raise DesktopError("This account is deactivated.")
            user.last_login_at = utcnow()
            db.commit()
            self.current_user_id = user.id
            return self.snapshot()
        finally:
            db.close()

    def logout(self) -> None:
        self.current_user_id = None

    def snapshot(self) -> dict:
        db = SessionLocal()
        try:
            user = self._current_user(db)
            tasks = (
                db.query(Todo)
                .filter(Todo.owner_id == user.id)
                .order_by(
                    Todo.complete.asc(),
                    Todo.deadline.is_(None).asc(),
                    Todo.deadline.asc(),
                    Todo.created_at.desc(),
                )
                .all()
            )
            return {
                "user": _user_dict(user),
                "tasks": [_todo_dict(todo) for todo in tasks],
            }
        finally:
            db.close()

    def create_task(self, payload: dict) -> dict:
        db = SessionLocal()
        try:
            user = self._current_user(db)
            title = (payload.get("title") or "").strip()
            if not title:
                raise DesktopError("Give the task a title.")
            if len(title) > 120:
                raise DesktopError("Task title is too long.")
            description = (payload.get("description") or "").strip()
            if len(description) > 1000:
                raise DesktopError("Task note is too long.")
            priority = int(payload.get("priority") or 3)
            if not 1 <= priority <= 5:
                raise DesktopError("Choose a valid priority.")
            now = utcnow()
            todo = Todo(
                title=title,
                description=description,
                priority=priority,
                complete=False,
                owner_id=user.id,
                created_at=now,
                updated_at=now,
                deadline=_deadline_from_iso(payload.get("deadline")),
            )
            db.add(todo)
            db.commit()
            return self.snapshot()
        finally:
            db.close()

    def update_task(self, todo_id: int, payload: dict) -> dict:
        db = SessionLocal()
        try:
            user = self._current_user(db)
            todo = (
                db.query(Todo)
                .filter(Todo.id == todo_id, Todo.owner_id == user.id)
                .first()
            )
            if todo is None:
                raise DesktopError("Task not found.")
            title = (payload.get("title") or "").strip()
            if not title:
                raise DesktopError("Give the task a title.")
            description = (payload.get("description") or "").strip()
            priority = int(payload.get("priority") or 3)
            if not 1 <= priority <= 5:
                raise DesktopError("Choose a valid priority.")
            todo.title = title[:120]
            todo.description = description[:1000]
            todo.priority = priority
            todo.deadline = _deadline_from_iso(payload.get("deadline"))
            todo.updated_at = utcnow()
            db.commit()
            return self.snapshot()
        finally:
            db.close()

    def toggle_task(self, todo_id: int) -> dict:
        db = SessionLocal()
        try:
            user = self._current_user(db)
            todo = (
                db.query(Todo)
                .filter(Todo.id == todo_id, Todo.owner_id == user.id)
                .first()
            )
            if todo is None:
                raise DesktopError("Task not found.")
            todo.complete = not todo.complete
            todo.completed_at = utcnow() if todo.complete else None
            todo.updated_at = utcnow()
            db.commit()
            return self.snapshot()
        finally:
            db.close()

    def delete_task(self, todo_id: int) -> dict:
        db = SessionLocal()
        try:
            user = self._current_user(db)
            todo = (
                db.query(Todo)
                .filter(Todo.id == todo_id, Todo.owner_id == user.id)
                .first()
            )
            if todo is None:
                raise DesktopError("Task not found.")
            db.delete(todo)
            db.commit()
            return self.snapshot()
        finally:
            db.close()

    # ------------------------------------------------------------------
    # Admin console data and actions
    # ------------------------------------------------------------------
    def _require_admin(self, db: Session) -> User:
        user = self._current_user(db)
        if user.role != "admin" or user.admin_slot is None:
            raise DesktopError("Administrator access is required.")
        return user

    def admin_snapshot(self) -> dict:
        db = SessionLocal()
        try:
            user = self._require_admin(db)
            users = (
                db.query(User)
                .order_by(
                    case((User.role == "admin", 0), else_=1),
                    User.created_at.desc(),
                )
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
                db.query(func.count(Todo.id))
                .filter(Todo.complete.is_(True))
                .scalar()
                or 0
            )
            overdue = int(
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
                db.query(func.count(User.id))
                .filter(User.is_active.is_(True))
                .scalar()
                or 0
            )
            recent_todos = (
                db.query(Todo)
                .options(joinedload(Todo.owner))
                .order_by(Todo.created_at.desc())
                .limit(8)
                .all()
            )
            audit = (
                db.query(AdminAudit)
                .options(joinedload(AdminAudit.actor))
                .order_by(AdminAudit.created_at.desc())
                .limit(10)
                .all()
            )
            return {
                "users": [
                    {
                        **_user_dict(person),
                        "task_count": task_counts.get(person.id, 0),
                        "completed_count": completed_counts.get(person.id, 0),
                    }
                    for person in users
                ],
                "seats": [
                    {
                        **seat,
                        "user": _user_dict(seat["user"]) if seat.get("user") else None,
                    }
                    for seat in admin_seats(db)
                ],
                "admin_count": admin_count(db),
                "admin_limit": 3,
                "free_slots": available_admin_slots(db),
                "total_todos": total_todos,
                "completed_todos": completed_todos,
                "overdue_todos": overdue,
                "active_users": active_users,
                "recent_tasks": [
                    {
                        **_todo_dict(todo),
                        "owner": todo.owner.username if todo.owner else "unknown",
                    }
                    for todo in recent_todos
                ],
                "audit": [
                    {
                        "id": entry.id,
                        "action": entry.action,
                        "target_label": entry.target_label,
                        "actor": entry.actor.username if entry.actor else "System",
                        "created_at": _iso(entry.created_at),
                    }
                    for entry in audit
                ],
                "main_admin": (
                    _user_dict(primary_admin(db)) if primary_admin(db) else None
                ),
            }
        finally:
            db.close()

    def change_role(self, user_id: int, action: str) -> dict:
        db = SessionLocal()
        try:
            actor = self._require_admin(db)
            target = db.get(User, user_id)
            if target is None:
                raise DesktopError("That account no longer exists.")
            if action == "promote":
                promote_to_admin(db, target, actor=actor)
            elif action == "demote":
                demote_from_admin(db, target, actor=actor)
            else:
                raise DesktopError("Unknown role action.")
            return self.admin_snapshot()
        except (AdminActionError, AdminLimitReached) as exc:
            raise DesktopError(str(exc)) from exc
        finally:
            db.close()

    def change_status(self, user_id: int, active: bool) -> dict:
        db = SessionLocal()
        try:
            actor = self._require_admin(db)
            target = db.get(User, user_id)
            if target is None:
                raise DesktopError("That account no longer exists.")
            set_user_active(db, target, actor=actor, active=active)
            return self.admin_snapshot()
        except AdminActionError as exc:
            raise DesktopError(str(exc)) from exc
        finally:
            db.close()

    def delete_user(self, user_id: int) -> dict:
        db = SessionLocal()
        try:
            actor = self._require_admin(db)
            target = db.get(User, user_id)
            if target is None:
                raise DesktopError("That account no longer exists.")
            delete_user_account(db, target, actor=actor)
            return self.admin_snapshot()
        except AdminActionError as exc:
            raise DesktopError(str(exc)) from exc
        finally:
            db.close()

    def delete_admin_todo(self, todo_id: int) -> dict:
        db = SessionLocal()
        try:
            actor = self._require_admin(db)
            todo = db.get(Todo, todo_id)
            if todo is None:
                raise DesktopError("That task no longer exists.")
            delete_todo_as_admin(db, todo, actor=actor)
            return self.admin_snapshot()
        except AdminActionError as exc:
            raise DesktopError(str(exc)) from exc
        finally:
            db.close()

    # ------------------------------------------------------------------
    # Account creation (local, regular users only)
    # ------------------------------------------------------------------
    def create_account(
        self,
        username: str,
        password: str,
        full_name: str,
        email: str,
    ) -> dict:
        import re

        username = (username or "").strip().lower()
        full_name = (full_name or "").strip()
        email = (email or "").strip().lower()
        if not re.fullmatch(r"[a-z0-9_]{3,30}", username):
            raise DesktopError("Username must be 3–30 lowercase letters, numbers or underscores.")
        if not full_name:
            raise DesktopError("Enter your name.")
        if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
            raise DesktopError("Enter a valid email.")
        if len(password) < 8:
            raise DesktopError("Password must be at least 8 characters.")
        if len(password.encode("utf-8")) > 72:
            raise DesktopError("Password is too long.")
        parts = full_name.split(maxsplit=1)
        first = parts[0][:60]
        last = (parts[1] if len(parts) > 1 else "Member")[:60]
        db = SessionLocal()
        try:
            duplicate = (
                db.query(User)
                .filter(
                    (func.lower(User.email) == email)
                    | (func.lower(User.username) == username)
                )
                .first()
            )
            if duplicate:
                raise DesktopError("That username or email is already registered.")
            user = User(
                email=email,
                username=username,
                first_name=first,
                last_name=last,
                hashed_password=hash_password(password),
                role="user",
                is_active=True,
            )
            db.add(user)
            db.commit()
            self.current_user_id = user.id
            return self.snapshot()
        finally:
            db.close()
