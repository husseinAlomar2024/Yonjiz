from __future__ import annotations

import pytest
from sqlalchemy.exc import IntegrityError

from database import SessionLocal
from models import AdminAudit, Todo, User, utcnow
from tests.conftest import create_user, login, register


def test_public_pages_and_security_headers(client):
    for path in ("/", "/auth/login-page", "/auth/register-page", "/healthy"):
        response = client.get(path)
        assert response.status_code == 200, path

    response = client.get("/")
    assert "YONJIZ" in response.text
    assert "ينجز" in response.text
    assert response.headers["x-content-type-options"] == "nosniff"
    assert "frame-ancestors 'none'" in response.headers["content-security-policy"]


def test_anonymous_workspace_redirects_to_login(client):
    response = client.get("/todos", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"].startswith("/auth/login-page?next=")

    api_response = client.post(
        "/api/todos",
        json={"title": "Nope", "priority": 3, "complete": False},
    )
    assert api_response.status_code == 401


def test_registration_login_and_password_is_hashed(client):
    response = register(client, "alice")
    assert response.status_code == 303
    assert "login-page" in response.headers["location"]

    session = SessionLocal()
    try:
        user = session.query(User).filter(User.username == "alice").one()
        assert user.role == "user"
        assert user.admin_slot is None
        assert user.hashed_password != "Password123!"
        assert user.hashed_password.startswith("$2")
    finally:
        session.close()

    response = login(client, "alice")
    assert response.status_code == 303
    assert response.headers["location"] == "/todos"
    assert "daymark_session" in response.cookies

    page = client.get("/todos")
    assert page.status_code == 200
    assert "alice" in page.text.lower()

    token_response = client.post(
        "/auth/token",
        data={"username": "alice", "password": "Password123!"},
    )
    assert token_response.status_code == 200
    assert token_response.json()["token_type"] == "bearer"
    assert token_response.json()["access_token"]

    bad_token = client.post(
        "/auth/token",
        data={"username": "alice", "password": "wrong"},
    )
    assert bad_token.status_code == 401
    assert bad_token.headers["content-type"].startswith("application/json")


def test_registration_rejects_duplicates_and_invalid_values(client):
    assert register(client, "bob").status_code == 303
    duplicate = client.post(
        "/auth/register-page",
        data={
            "first_name": "Bob",
            "last_name": "Again",
            "email": "bob@example.test",
            "username": "bob",
            "phone_number": "",
            "password": "Password123!",
        },
    )
    assert duplicate.status_code == 200
    assert "already registered" in duplicate.text

    bad_username = client.post(
        "/auth/register-page",
        data={
            "first_name": "Bad",
            "last_name": "Name",
            "email": "bad@example.test",
            "username": "No Spaces",
            "phone_number": "",
            "password": "Password123!",
        },
    )
    assert bad_username.status_code == 200
    assert "Username must" in bad_username.text

    short_password = client.post(
        "/auth/register-page",
        data={
            "first_name": "Short",
            "last_name": "Pass",
            "email": "short@example.test",
            "username": "shortpass",
            "phone_number": "",
            "password": "short",
        },
    )
    assert short_password.status_code == 200
    assert "at least 8" in short_password.text


def test_login_failure_and_inactive_account(client):
    create_user("inactive", active=False)
    response = client.post(
        "/auth/login-page",
        data={"username": "inactive", "password": "Password123!", "next": "/todos"},
    )
    assert response.status_code == 403
    assert "deactivated" in response.text

    response = client.post(
        "/auth/login-page",
        data={"username": "inactive", "password": "wrong", "next": "/todos"},
    )
    assert response.status_code == 401
    assert "not correct" in response.text


def test_todo_api_optional_deadline_and_scoping(client):
    register(client, "owner")
    login(client, "owner")

    no_deadline = client.post(
        "/api/todos",
        json={
            "title": "Open-ended task",
            "description": "No date attached",
            "priority": 3,
            "complete": False,
            "deadline": None,
        },
    )
    assert no_deadline.status_code == 201
    payload = no_deadline.json()
    assert payload["deadline"] is None
    assert payload["created_at"].endswith("Z")
    todo_id = payload["id"]

    with_deadline = client.post(
        "/api/todos",
        json={
            "title": "Dated task",
            "priority": 5,
            "complete": False,
            "deadline": "2026-11-01T17:30:00Z",
        },
    )
    assert with_deadline.status_code == 201
    assert with_deadline.json()["deadline"] == "2026-11-01T17:30:00Z"

    listed = client.get("/api/todos")
    assert listed.status_code == 200
    assert {item["id"] for item in listed.json()} == {
        todo_id,
        with_deadline.json()["id"],
    }

    updated = client.put(
        f"/api/todos/{todo_id}",
        json={
            "title": "Open-ended task",
            "description": "Now with a date",
            "priority": 4,
            "complete": False,
            "deadline": "2026-11-03T09:00:00Z",
        },
    )
    assert updated.status_code == 200
    assert updated.json()["deadline"] == "2026-11-03T09:00:00Z"

    completed = client.patch(
        f"/api/todos/{todo_id}/complete", json={"complete": True}
    )
    assert completed.status_code == 200
    assert completed.json()["complete"] is True
    assert completed.json()["completed_at"].endswith("Z")

    page = client.get("/todos")
    assert "Open-ended task" in page.text
    assert "Nov 03" in page.text

    # A second account cannot read or mutate the first account's tasks.
    client.post("/auth/logout")
    register(client, "intruder")
    login(client, "intruder")
    assert client.put(
        f"/api/todos/{todo_id}",
        json={"title": "stolen", "priority": 3, "complete": False},
    ).status_code == 404
    assert client.delete(f"/api/todos/{todo_id}").status_code == 404
    assert "Open-ended task" not in client.get("/todos").text


def test_admin_access_requires_role_and_developer_key(client):
    register(client, "normal")
    login(client, "normal")

    assert client.get("/admin").status_code == 403

    wrong = client.post("/admin/access", data={"access_key": "wrong"})
    assert wrong.status_code == 403
    assert "not valid" in wrong.text

    accepted = client.post(
        "/admin/access", data={"access_key": "test-developer-key"}, follow_redirects=False
    )
    assert accepted.status_code == 303
    assert accepted.headers["location"].startswith("/admin")

    page = client.get("/admin")
    assert page.status_code == 200
    assert "The people and" in page.text

    session = SessionLocal()
    try:
        user = session.query(User).filter(User.username == "normal").one()
        assert user.role == "admin"
        assert user.admin_slot == 1
        entry = session.query(AdminAudit).order_by(AdminAudit.id.desc()).first()
        assert entry.action == "admin.developer_access"
    finally:
        session.close()


def test_three_admin_limit_is_enforced_by_app_and_database(client):
    create_user("rootadmin", role="admin", admin_slot=1)
    for name in ("second", "third", "fourth"):
        create_user(name)
    login(client, "rootadmin", password="Password123!")

    for name in ("second", "third"):
        response = client.post(
            f"/admin/users/{_user_id(name)}/role",
            data={"action": "promote"},
            follow_redirects=False,
        )
        assert response.status_code == 303
        assert "message=" in response.headers["location"]

    session = SessionLocal()
    try:
        admins = session.query(User).filter(User.role == "admin").all()
        assert len(admins) == 3
        assert sorted(admin.admin_slot for admin in admins) == [1, 2, 3]
    finally:
        session.close()

    blocked = client.post(
        f"/admin/users/{_user_id('fourth')}/role",
        data={"action": "promote"},
        follow_redirects=True,
    )
    assert blocked.status_code == 200
    assert "All three administrator seats are occupied" in blocked.text

    session = SessionLocal()
    try:
        fourth = session.query(User).filter(User.username == "fourth").one()
        assert fourth.role == "user"
        assert fourth.admin_slot is None
        assert session.query(User).filter(User.role == "admin").count() == 3
    finally:
        session.close()

    # Even direct SQLAlchemy inserts cannot make a fourth admin.
    session = SessionLocal()
    try:
        session.add(
            User(
                email="rogue@example.test",
                username="rogue",
                first_name="Rogue",
                last_name="Admin",
                hashed_password="x",
                role="admin",
                admin_slot=None,
            )
        )
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()

        session.add(
            User(
                email="rogue2@example.test",
                username="rogue2",
                first_name="Rogue",
                last_name="Admin",
                hashed_password="x",
                role="admin",
                admin_slot=2,
            )
        )
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()

        session.add(
            User(
                email="rogue3@example.test",
                username="rogue3",
                first_name="Rogue",
                last_name="Admin",
                hashed_password="x",
                role="admin",
                admin_slot=4,
            )
        )
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()
        assert session.query(User).filter(User.role == "admin").count() == 3
    finally:
        session.close()


def test_admin_self_protection_and_audit_trail(client):
    root = create_user("rootadmin", role="admin", admin_slot=1)
    register(client, "member")
    login(client, "rootadmin")

    self_demote = client.post(
        f"/admin/users/{root.id}/role",
        data={"action": "demote"},
        follow_redirects=True,
    )
    assert "cannot remove your own admin access" in self_demote.text

    self_delete = client.post(
        f"/admin/users/{root.id}/delete", follow_redirects=True
    )
    assert "cannot delete your own account" in self_delete.text

    session = SessionLocal()
    try:
        assert session.get(User, root.id).role == "admin"
        assert session.query(User).filter(User.role == "admin").count() == 1
    finally:
        session.close()


def test_admin_deletes_account_and_tasks(client):
    create_user("rootadmin", role="admin", admin_slot=1)
    target = create_user("target")
    session = SessionLocal()
    try:
        session.add(
            Todo(
                title="Target task",
                description="",
                priority=2,
                complete=False,
                owner_id=target.id,
                created_at=utcnow(),
                updated_at=utcnow(),
            )
        )
        session.commit()
    finally:
        session.close()

    login(client, "rootadmin")
    response = client.post(
        f"/admin/users/{target.id}/delete", follow_redirects=True
    )
    assert response.status_code == 200
    assert "Deleted" in response.text

    session = SessionLocal()
    try:
        assert session.get(User, target.id) is None
        assert session.query(Todo).filter(Todo.owner_id == target.id).count() == 0
        assert session.query(AdminAudit).filter(AdminAudit.action == "user.delete").count() == 1
    finally:
        session.close()


def test_registration_never_grants_admin(client):
    response = client.post(
        "/auth/register-page",
        data={
            "first_name": "Sneaky",
            "last_name": "User",
            "email": "sneaky@example.test",
            "username": "sneaky",
            "phone_number": "",
            "password": "Password123!",
            "role": "admin",
        },
        follow_redirects=False,
    )
    assert response.status_code == 303
    session = SessionLocal()
    try:
        user = session.query(User).filter(User.username == "sneaky").one()
        assert user.role == "user"
        assert user.admin_slot is None
    finally:
        session.close()


def test_primary_admin_is_protected_and_can_hire_and_kick(client):
    primary = create_user(
        "hussein_alomar", role="admin", admin_slot=1, primary=True
    )
    secondary = create_user("second_admin", role="admin", admin_slot=2)
    candidate = create_user("candidate")

    # A normal admin can see the main admin but cannot remove them.
    login(client, "second_admin")
    admin_page = client.get("/admin")
    assert admin_page.status_code == 200
    assert "Main admin" in admin_page.text
    assert "Untouchable" in admin_page.text

    for path, payload, expected in [
        (
            f"/admin/users/{primary.id}/role",
            {"action": "demote"},
            "main administrator is protected",
        ),
        (
            f"/admin/users/{primary.id}/status",
            {"action": "deactivate"},
            "main administrator is protected",
        ),
        (
            f"/admin/users/{primary.id}/delete",
            {},
            "main administrator is protected",
        ),
    ]:
        response = client.post(path, data=payload, follow_redirects=True)
        assert response.status_code == 200
        assert expected in response.text

    session = SessionLocal()
    try:
        protected = session.get(User, primary.id)
        assert protected.role == "admin"
        assert protected.admin_slot == 1
        assert protected.is_primary_admin is True
        assert protected.is_active is True
    finally:
        session.close()

    # The main admin can kick another admin and hire a new one.
    client.post("/auth/logout")
    login(client, "hussein_alomar")

    kicked = client.post(
        f"/admin/users/{secondary.id}/role",
        data={"action": "demote"},
        follow_redirects=True,
    )
    assert "is now a regular user" in kicked.text

    hired = client.post(
        f"/admin/users/{candidate.id}/role",
        data={"action": "promote"},
        follow_redirects=True,
    )
    assert "now has admin seat" in hired.text

    session = SessionLocal()
    try:
        assert session.get(User, secondary.id).role == "user"
        assert session.get(User, candidate.id).role == "admin"
        assert session.query(User).filter(User.is_primary_admin.is_(True)).count() == 1
    finally:
        session.close()


def test_only_one_primary_admin_and_seat_one_are_enforced(client):
    create_user("main_one", role="admin", admin_slot=1, primary=True)

    session = SessionLocal()
    try:
        session.add(
            User(
                email="second-primary@example.test",
                username="second_primary",
                first_name="Second",
                last_name="Primary",
                hashed_password="x",
                role="admin",
                admin_slot=2,
                is_primary_admin=True,
                is_active=True,
            )
        )
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()
        assert session.query(User).filter(User.is_primary_admin.is_(True)).count() == 1
    finally:
        session.close()


def _user_id(username: str) -> int:
    session = SessionLocal()
    try:
        return session.query(User).filter(User.username == username).one().id
    finally:
        session.close()
