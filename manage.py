"""Small operator CLI for local setup.

Examples:
    python manage.py create-main-admin
    python manage.py create-admin
    python manage.py list-admins
    python manage.py show-key
    python manage.py seed-demo
"""

from __future__ import annotations

import argparse
import getpass
import sys
from datetime import timedelta

from sqlalchemy import func

from admin_service import (
    AdminActionError,
    AdminLimitReached,
    admin_seats,
    available_admin_slots,
    log_action,
    primary_admin,
    promote_to_admin,
)
from config import ADMIN_ACCESS_KEY, ADMIN_LIMIT
from database import SessionLocal, init_db
from models import Todo, User, utcnow
from security import hash_password


def _prompt(label: str, default: str | None = None) -> str:
    suffix = f" [{default}]" if default else ""
    value = input(f"{label}{suffix}: ").strip()
    if not value and default:
        return default
    return value


def _password() -> str:
    value = getpass.getpass("Password (8–72 characters): ")
    if len(value) < 8:
        raise SystemExit("Password must be at least 8 characters.")
    if len(value.encode("utf-8")) > 72:
        raise SystemExit("Password must be 72 UTF-8 bytes or fewer.")
    confirmation = getpass.getpass("Confirm password: ")
    if value != confirmation:
        raise SystemExit("Passwords did not match.")
    return value


def command_create_admin(args: argparse.Namespace) -> int:
    init_db()
    db = SessionLocal()
    try:
        username = (args.username or _prompt("Username")).strip().lower()
        if not username:
            raise SystemExit("A username is required.")

        existing = db.query(User).filter(func.lower(User.username) == username).first()
        if existing:
            if existing.role == "admin":
                print(f"@{existing.username} is already admin in seat {existing.admin_slot}.")
                return 0
            try:
                slot = promote_to_admin(db, existing, actor=None, action="admin.cli")
            except (AdminActionError, AdminLimitReached) as exc:
                print(f"Could not promote: {exc}", file=sys.stderr)
                return 1
            print(f"Promoted existing user @{existing.username} to admin seat {slot}.")
            return 0

        email = (args.email or _prompt("Email")).strip().lower()
        first_name = (args.first_name or _prompt("First name")).strip()
        last_name = (args.last_name or _prompt("Last name")).strip()
        password = args.password or _password()

        if not email or "@" not in email:
            raise SystemExit("A valid email is required.")
        if not first_name or not last_name:
            raise SystemExit("First and last name are required.")
        if len(password) < 8 or len(password.encode("utf-8")) > 72:
            raise SystemExit("Password must be 8–72 characters.")

        free_slots = available_admin_slots(db)
        if not free_slots:
            print(
                f"All {ADMIN_LIMIT} admin seats are occupied. Demote an admin first.",
                file=sys.stderr,
            )
            return 1

        user = User(
            email=email,
            username=username,
            first_name=first_name,
            last_name=last_name,
            hashed_password=hash_password(password),
            role="admin",
            admin_slot=free_slots[0],
            is_active=True,
        )
        db.add(user)
        db.flush()
        log_action(
            db,
            actor_id=None,
            action="admin.cli",
            target_label=f"@{username} • admin seat {free_slots[0]}",
        )
        db.commit()
        print(f"Created admin @{username} in seat {free_slots[0]}. Use /auth/login-page.")
        return 0
    finally:
        db.close()


def command_create_main_admin(args: argparse.Namespace) -> int:
    """Create the single protected main admin in seat 1."""

    init_db()
    db = SessionLocal()
    try:
        current = primary_admin(db)
        if current is not None:
            print(
                f"A main admin already exists: @{current.username}. "
                "Only one main admin is allowed.",
                file=sys.stderr,
            )
            return 1

        username = (args.username or _prompt("Username")).strip().lower()
        if not username:
            raise SystemExit("A username is required.")

        existing = db.query(User).filter(func.lower(User.username) == username).first()
        seat_one = (
            db.query(User)
            .filter(User.role == "admin", User.admin_slot == 1)
            .first()
        )
        if seat_one is not None and (existing is None or seat_one.id != existing.id):
            print(
                f"Seat 1 is already occupied by @{seat_one.username}. "
                "Demote that admin before creating the main admin.",
                file=sys.stderr,
            )
            return 1

        if existing:
            existing.role = "admin"
            existing.admin_slot = 1
            existing.is_primary_admin = True
            existing.is_active = True
            log_action(
                db,
                actor_id=None,
                action="admin.primary_created",
                target_label=f"@{existing.username} • protected main admin",
            )
            db.commit()
            print(f"@{existing.username} is now the protected main admin in seat 1.")
            return 0

        email = (args.email or _prompt("Email")).strip().lower()
        first_name = (args.first_name or _prompt("First name")).strip()
        last_name = (args.last_name or _prompt("Last name")).strip()
        password = args.password or _password()

        if not email or "@" not in email:
            raise SystemExit("A valid email is required.")
        if not first_name or not last_name:
            raise SystemExit("First and last name are required.")
        if len(password) < 8 or len(password.encode("utf-8")) > 72:
            raise SystemExit("Password must be 8–72 characters.")

        user = User(
            email=email,
            username=username,
            first_name=first_name,
            last_name=last_name,
            hashed_password=hash_password(password),
            role="admin",
            admin_slot=1,
            is_primary_admin=True,
            is_active=True,
        )
        db.add(user)
        db.flush()
        log_action(
            db,
            actor_id=None,
            action="admin.primary_created",
            target_label=f"@{username} • protected main admin",
        )
        db.commit()
        print(f"Created protected main admin @{username} in seat 1.")
        print("Use /auth/login-page to sign in.")
        return 0
    finally:
        db.close()


def command_list_admins(_args: argparse.Namespace) -> int:
    init_db()
    db = SessionLocal()
    try:
        for seat in admin_seats(db):
            if seat["occupied"]:
                person = seat["user"]
                marker = " [MAIN ADMIN]" if person.is_primary_admin else ""
                print(f"Seat {seat['slot']}: @{person.username} <{person.email}>{marker}")
            else:
                print(f"Seat {seat['slot']}: available")
        return 0
    finally:
        db.close()


def command_show_key(_args: argparse.Namespace) -> int:
    print(ADMIN_ACCESS_KEY)
    print("\nUse this while signed in at /admin/access.", file=sys.stderr)
    return 0


def command_seed_demo(_args: argparse.Namespace) -> int:
    init_db()
    db = SessionLocal()
    try:
        if db.query(User).filter(User.username == "demo").first():
            print("Demo data already exists; nothing changed.")
            return 0

        now = utcnow()
        demo = User(
            email="demo@daymark.local",
            username="demo",
            first_name="Hussein",
            last_name="Saleh",
            hashed_password=hash_password("Demo1234!"),
            role="user",
            is_active=True,
            phone_number="+962 7 9000 0000",
        )
        db.add(demo)
        db.flush()

        tasks = [
            ("Finish the product brief", "Tighten the narrative and send it to the team.", 4, False, now.replace(hour=17, minute=0), now - timedelta(days=1)),
            ("Review the new dashboard", "Check the calendar states and mobile spacing.", 3, False, (now + timedelta(days=1)).replace(hour=10, minute=0), now - timedelta(hours=5)),
            ("Send the studio invoice", "The February retainer is still outstanding.", 5, False, (now - timedelta(days=2)).replace(hour=12, minute=0), now - timedelta(days=5)),
            ("Book the design critique", "Find a room and a time that suits everyone.", 2, False, None, now - timedelta(days=2)),
            ("Morning pages", "Three pages before the inbox opens.", 2, True, None, now - timedelta(days=3)),
            ("Plan next week's priorities", "Protected time to decide what matters.", 5, False, (now + timedelta(days=5)).replace(hour=9, minute=30), now - timedelta(hours=3)),
            ("Read the accessibility notes", "A useful pass before the next release.", 1, False, (now + timedelta(days=9)).replace(hour=15, minute=0), now - timedelta(hours=9)),
            ("Reply to Leen", "Confirm the workshop dates.", 3, False, None, now - timedelta(hours=2)),
        ]

        for title, description, priority, complete, deadline, created in tasks:
            db.add(
                Todo(
                    title=title,
                    description=description,
                    priority=priority,
                    complete=complete,
                    owner_id=demo.id,
                    created_at=created,
                    updated_at=created,
                    deadline=deadline,
                    completed_at=(created + timedelta(hours=2)) if complete else None,
                )
            )

        db.commit()
        print("Demo workspace created.")
        print("  username: demo")
        print("  password: Demo1234!")
        print("Sign in at /auth/login-page. To try the admin console, run:")
        print("  python manage.py create-admin")
        return 0
    finally:
        db.close()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="YONJIZ operator commands")
    subparsers = parser.add_subparsers(dest="command", required=True)

    create = subparsers.add_parser("create-admin", help="Create or promote an administrator")
    create.add_argument("--username")
    create.add_argument("--email")
    create.add_argument("--first-name")
    create.add_argument("--last-name")
    create.add_argument("--password", help="Non-interactive password; avoid in shared shells")
    create.set_defaults(func=command_create_admin)

    primary = subparsers.add_parser(
        "create-main-admin",
        help="Create the one protected main admin in seat 1",
    )
    primary.add_argument("--username")
    primary.add_argument("--email")
    primary.add_argument("--first-name")
    primary.add_argument("--last-name")
    primary.add_argument("--password", help="Non-interactive password; avoid in shared shells")
    primary.set_defaults(func=command_create_main_admin)

    list_cmd = subparsers.add_parser("list-admins", help="Show all three admin seats")
    list_cmd.set_defaults(func=command_list_admins)

    key_cmd = subparsers.add_parser("show-key", help="Print the developer access key")
    key_cmd.set_defaults(func=command_show_key)

    demo = subparsers.add_parser("seed-demo", help="Add an optional demo user and sample tasks")
    demo.set_defaults(func=command_seed_demo)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        return args.func(args)
    except KeyboardInterrupt:
        print("\nCancelled.", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
