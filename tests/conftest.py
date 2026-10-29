"""Test configuration. Environment must be set before importing the app."""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


TEST_DB = Path(__file__).resolve().parent / "test_daymark.db"
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB.as_posix()}"
os.environ["SECRET_KEY"] = "test-secret-key-not-for-production"
os.environ["ADMIN_ACCESS_KEY"] = "test-developer-key"
os.environ["COOKIE_SECURE"] = "false"

from database import Base, SessionLocal, engine  # noqa: E402
from main import app  # noqa: E402
from models import User  # noqa: E402
from security import hash_password  # noqa: E402


@pytest.fixture()
def client():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture()
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def create_user(
    username: str,
    *,
    password: str = "Password123!",
    email: str | None = None,
    role: str = "user",
    admin_slot: int | None = None,
    active: bool = True,
) -> User:
    session = SessionLocal()
    try:
        user = User(
            email=email or f"{username}@example.test",
            username=username,
            first_name=username.title(),
            last_name="Tester",
            hashed_password=hash_password(password),
            role=role,
            admin_slot=admin_slot,
            is_active=active,
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        return user
    finally:
        session.close()


def register(client: TestClient, username: str, password: str = "Password123!"):
    return client.post(
        "/auth/register-page",
        data={
            "first_name": username.title(),
            "last_name": "Tester",
            "email": f"{username}@example.test",
            "username": username,
            "phone_number": "",
            "password": password,
        },
        follow_redirects=False,
    )


def login(client: TestClient, username: str, password: str = "Password123!"):
    return client.post(
        "/auth/login-page",
        data={"username": username, "password": password, "next": "/todos"},
        follow_redirects=False,
    )
