"""Admin seat management and audited administrative actions.

Seat allocation lives here so every entry point (web UI, developer access,
CLI helper) follows the same rules.  The database schema is still the final
authority: only three unique non-null admin_slot values can exist.
"""

from __future__ import annotations

from typing import Optional

from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from config import ADMIN_LIMIT
from models import AdminAudit, Todo, User


class AdminActionError(Exception):
    """A user-facing admin operation failure."""


class AdminLimitReached(AdminActionError):
    pass


class AdminPolicyError(AdminActionError):
    pass


def admin_count(db: Session) -> int:
    return int(db.query(func.count(User.id)).filter(User.role == "admin").scalar() or 0)


def primary_admin(db: Session) -> Optional[User]:
    return (
        db.query(User)
        .filter(User.is_primary_admin.is_(True))
        .first()
    )


def available_admin_slots(db: Session) -> list[int]:
    used = {
        slot
        for (slot,) in db.query(User.admin_slot)
        .filter(User.role == "admin", User.admin_slot.isnot(None))
        .all()
    }
    return [slot for slot in range(1, ADMIN_LIMIT + 1) if slot not in used]


def admin_seats(db: Session) -> list[dict]:
    """Return the three seats with their current occupant, if any."""

    admins = (
        db.query(User)
        .filter(User.role == "admin")
        .order_by(User.admin_slot.asc())
        .all()
    )
    by_slot = {admin.admin_slot: admin for admin in admins}
    return [
        {
            "slot": slot,
            "user": by_slot.get(slot),
            "occupied": slot in by_slot,
            "primary": bool(
                slot in by_slot and by_slot[slot].is_primary_admin
            ),
        }
        for slot in range(1, ADMIN_LIMIT + 1)
    ]


def log_action(
    db: Session,
    *,
    actor_id: Optional[int],
    action: str,
    target_label: Optional[str] = None,
) -> AdminAudit:
    entry = AdminAudit(actor_id=actor_id, action=action, target_label=target_label)
    db.add(entry)
    return entry


def promote_to_admin(
    db: Session,
    user: User,
    *,
    actor: Optional[User],
    action: str = "admin.promote",
) -> int:
    if user.role == "admin" and user.admin_slot is not None:
        return user.admin_slot
    if not user.is_active:
        raise AdminPolicyError("Activate this account before granting admin access.")
    if admin_count(db) >= ADMIN_LIMIT:
        raise AdminLimitReached(
            "All three administrator seats are occupied. Demote an admin first."
        )

    free_slots = available_admin_slots(db)
    if not free_slots:
        raise AdminLimitReached("No administrator seats are available.")
    slot = free_slots[0]

    user.role = "admin"
    user.admin_slot = slot
    log_action(
        db,
        actor_id=actor.id if actor else None,
        action=action,
        target_label=f"@{user.username} • admin seat {slot}",
    )
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise AdminLimitReached(
            "That admin seat was just taken. Refresh and try again."
        ) from exc

    db.refresh(user)
    return slot


def demote_from_admin(
    db: Session,
    user: User,
    *,
    actor: User,
) -> None:
    if user.role != "admin":
        raise AdminPolicyError("This account is not an administrator.")
    if user.is_primary_admin:
        raise AdminPolicyError(
            "The main administrator is protected and cannot be demoted."
        )
    if actor.id == user.id:
        raise AdminPolicyError("You cannot remove your own admin access.")
    if admin_count(db) <= 1:
        raise AdminPolicyError("The last administrator cannot be demoted.")

    previous_slot = user.admin_slot
    user.role = "user"
    user.admin_slot = None
    log_action(
        db,
        actor_id=actor.id,
        action="admin.demote",
        target_label=f"@{user.username} • released seat {previous_slot}",
    )
    try:
        db.commit()
    except IntegrityError as exc:  # pragma: no cover - guard for odd databases
        db.rollback()
        raise AdminActionError("Could not update that administrator.") from exc
    db.refresh(user)


def set_user_active(
    db: Session,
    user: User,
    *,
    actor: User,
    active: bool,
) -> None:
    if user.is_primary_admin and not active:
        raise AdminPolicyError(
            "The main administrator is protected and cannot be deactivated."
        )
    if actor.id == user.id and not active:
        raise AdminPolicyError("You cannot deactivate your own account.")
    if user.role == "admin" and not active:
        raise AdminPolicyError("Demote this administrator before deactivating them.")
    if user.is_active == active:
        return

    user.is_active = active
    log_action(
        db,
        actor_id=actor.id,
        action="user.activate" if active else "user.deactivate",
        target_label=f"@{user.username}",
    )
    db.commit()
    db.refresh(user)


def delete_user_account(db: Session, user: User, *, actor: User) -> str:
    if user.is_primary_admin:
        raise AdminPolicyError(
            "The main administrator is protected and cannot be deleted."
        )
    if actor.id == user.id:
        raise AdminPolicyError("You cannot delete your own account.")
    if user.role == "admin" and admin_count(db) <= 1:
        raise AdminPolicyError("The last administrator cannot be deleted.")

    task_count = int(
        db.query(func.count(Todo.id)).filter(Todo.owner_id == user.id).scalar() or 0
    )
    label = f"@{user.username} • {task_count} task{'s' if task_count != 1 else ''}"
    log_action(
        db,
        actor_id=actor.id,
        action="user.delete",
        target_label=label,
    )
    db.delete(user)
    try:
        db.commit()
    except IntegrityError as exc:  # pragma: no cover - protects referential integrity
        db.rollback()
        raise AdminActionError("This account is still referenced by other data.") from exc
    return label


def delete_todo_as_admin(db: Session, todo: Todo, *, actor: User) -> str:
    label = f"“{todo.title}” • @{todo.owner.username if todo.owner else 'unknown'}"
    log_action(
        db,
        actor_id=actor.id,
        action="todo.delete",
        target_label=label,
    )
    db.delete(todo)
    db.commit()
    return label
