"""SQLAlchemy models and the database rules behind the three-admin limit.

The admin limit is *not* only an application check.  Every admin gets one of
three numeric seats (1, 2 or 3).  A UNIQUE constraint on ``admin_slot`` makes a
fourth admin impossible at the database layer, and a CHECK constraint keeps
``role`` and ``admin_slot`` consistent.  Seat 1 belongs to the single protected
main admin (``is_primary_admin``), who cannot be demoted, deactivated or deleted
through the app.
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import relationship

from database import Base


def utcnow() -> datetime:
    """Return naive UTC (portable across PostgreSQL and SQLite)."""

    return datetime.now(timezone.utc).replace(tzinfo=None)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(254), nullable=False, unique=True, index=True)
    username = Column(String(30), nullable=False, unique=True, index=True)
    first_name = Column(String(60), nullable=False)
    last_name = Column(String(60), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True, server_default="1")
    role = Column(String(20), nullable=False, default="user", server_default="user")
    admin_slot = Column(Integer, nullable=True)
    is_primary_admin = Column(
        Boolean, nullable=False, default=False, server_default="0"
    )
    phone_number = Column(String(25), nullable=True)
    created_at = Column(DateTime, nullable=False, default=utcnow)
    last_login_at = Column(DateTime, nullable=True)

    todos = relationship(
        "Todo",
        back_populates="owner",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    __table_args__ = (
        CheckConstraint("role IN ('user', 'admin')", name="ck_users_role"),
        CheckConstraint(
            "(role = 'admin' AND admin_slot IS NOT NULL AND admin_slot BETWEEN 1 AND 3) "
            "OR (role = 'user' AND admin_slot IS NULL)",
            name="ck_users_admin_slot",
        ),
        CheckConstraint(
            "NOT is_primary_admin "
            "OR (role = 'admin' AND admin_slot = 1 AND is_active)",
            name="ck_users_primary_admin",
        ),
        UniqueConstraint("admin_slot", name="uq_users_admin_slot"),
        Index("ix_users_role_admin_slot", "role", "admin_slot"),
        Index(
            "uq_users_single_primary_admin",
            "is_primary_admin",
            unique=True,
            sqlite_where=text("is_primary_admin = 1"),
            postgresql_where=text("is_primary_admin"),
        ),
    )

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()

    @property
    def initials(self) -> str:
        letters = [part[0] for part in (self.first_name, self.last_name) if part]
        return "".join(letters).upper()[:2] or self.username[:2].upper()


class Todo(Base):
    __tablename__ = "todos"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(120), nullable=False)
    description = Column(String(1000), nullable=False, default="", server_default="")
    priority = Column(Integer, nullable=False, default=3, server_default="3")
    complete = Column(Boolean, nullable=False, default=False, server_default="0")
    owner_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    created_at = Column(DateTime, nullable=False, default=utcnow)
    updated_at = Column(DateTime, nullable=False, default=utcnow, onupdate=utcnow)
    deadline = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    owner = relationship("User", back_populates="todos")

    __table_args__ = (
        CheckConstraint("priority BETWEEN 1 AND 5", name="ck_todos_priority"),
        Index("ix_todos_owner_complete", "owner_id", "complete"),
        Index("ix_todos_owner_deadline", "owner_id", "deadline"),
    )


class AdminAudit(Base):
    """Small audit trail for sensitive admin/developer actions."""

    __tablename__ = "admin_audit"

    id = Column(Integer, primary_key=True, index=True)
    actor_id = Column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    action = Column(String(60), nullable=False)
    target_label = Column(String(180), nullable=True)
    created_at = Column(DateTime, nullable=False, default=utcnow, index=True)

    actor = relationship("User", foreign_keys=[actor_id])
