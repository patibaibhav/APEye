"""Tests for Users Management API and role authorization (Owner: Anvi)."""

import asyncio
import json

import pytest

from app.auth.security import create_access_token, hash_password
from app.db.models.user import User
from app.db.session import SessionLocal
from app.main import create_app


@pytest.fixture
def user_fixtures():
    session = SessionLocal()
    admin = User(
        username="admin_test_user_mgmt",
        password_hash=hash_password("AdminSecurePassword123"),
        role="ADMIN",
        is_active=True,
    )
    analyst = User(
        username="analyst_test_user_mgmt",
        password_hash=hash_password("AnalystSecurePassword123"),
        role="ANALYST",
        is_active=True,
    )
    session.add_all([admin, analyst])
    session.commit()

    admin_id = admin.id
    analyst_id = analyst.id
    session.close()

    yield {"admin_id": admin_id, "analyst_id": analyst_id}

    cleanup = SessionLocal()
    for uid in (admin_id, analyst_id):
        u = cleanup.get(User, uid)
        if u:
            cleanup.delete(u)
    cleanup.commit()
    cleanup.close()


async def asgi_request(app, method, path, body=None, headers=None):
    req_headers = [(b"host", b"testserver")]
    if headers:
        req_headers.extend(headers)

    body_bytes = json.dumps(body).encode("utf-8") if body is not None else b""
    if body is not None:
        req_headers.append((b"content-type", b"application/json"))

    scope = {
        "type": "http",
        "method": method,
        "path": path,
        "query_string": b"",
        "headers": req_headers,
        "client": ("127.0.0.1", 12345),
        "state": {},
    }
    messages = []

    async def mock_receive():
        return {"type": "http.request", "body": body_bytes, "more_body": False}

    async def mock_send(msg):
        messages.append(msg)

    await app(scope, mock_receive, mock_send)

    start_msg = next((m for m in messages if m["type"] == "http.response.start"), None)
    body_msgs = [m for m in messages if m["type"] == "http.response.body"]
    assert start_msg is not None

    raw_body = b"".join(m.get("body", b"") for m in body_msgs)
    data = json.loads(raw_body.decode("utf-8")) if raw_body else {}
    return start_msg["status"], data


def test_list_users_forbidden_for_analyst(user_fixtures):
    test_app = create_app()
    token, _ = create_access_token(user_fixtures["analyst_id"], "analyst_test_user_mgmt", "ANALYST")

    async def run():
        status, data = await asgi_request(
            test_app,
            "GET",
            "/api/users",
            headers=[(b"authorization", f"Bearer {token}".encode("ascii"))],
        )
        assert status == 403
        assert data["error"]["code"] == "FORBIDDEN"

    asyncio.run(run())


def test_list_users_authorized_for_admin(user_fixtures):
    test_app = create_app()
    token, _ = create_access_token(user_fixtures["admin_id"], "admin_test_user_mgmt", "ADMIN")

    async def run():
        status, data = await asgi_request(
            test_app,
            "GET",
            "/api/users",
            headers=[(b"authorization", f"Bearer {token}".encode("ascii"))],
        )
        assert status == 200
        assert "items" in data
        assert "total_items" in data
        assert data["total_items"] >= 2

    asyncio.run(run())


def test_create_user_short_password_rejected(user_fixtures):
    test_app = create_app()
    token, _ = create_access_token(user_fixtures["admin_id"], "admin_test_user_mgmt", "ADMIN")

    async def run():
        # Password is only 8 chars (< 12 required)
        status, data = await asgi_request(
            test_app,
            "POST",
            "/api/users",
            body={
                "username": "short_pwd_user",
                "password": "short_12",  # 8 characters
                "role": "ANALYST",
            },
            headers=[(b"authorization", f"Bearer {token}".encode("ascii"))],
        )
        assert status == 422
        assert data["error"]["code"] == "VALIDATION_ERROR"

    asyncio.run(run())


def test_create_user_duplicate_username_conflict(user_fixtures):
    test_app = create_app()
    token, _ = create_access_token(user_fixtures["admin_id"], "admin_test_user_mgmt", "ADMIN")

    async def run():
        status, data = await asgi_request(
            test_app,
            "POST",
            "/api/users",
            body={
                "username": "admin_test_user_mgmt",  # Existing username
                "password": "LongSecurePassword123",
                "role": "ANALYST",
            },
            headers=[(b"authorization", f"Bearer {token}".encode("ascii"))],
        )
        assert status == 409
        assert data["error"]["code"] == "USERNAME_TAKEN"

    asyncio.run(run())


def test_admin_self_deactivation_forbidden(user_fixtures):
    test_app = create_app()
    token, _ = create_access_token(user_fixtures["admin_id"], "admin_test_user_mgmt", "ADMIN")

    async def run():
        # Admin attempts to deactivate themselves
        status, data = await asgi_request(
            test_app,
            "PATCH",
            f"/api/users/{user_fixtures['admin_id']}",
            body={"is_active": False},
            headers=[(b"authorization", f"Bearer {token}".encode("ascii"))],
        )
        assert status == 403
        assert data["error"]["code"] == "FORBIDDEN"
        assert "cannot deactivate themselves" in data["error"]["message"].lower()

    asyncio.run(run())


def test_admin_can_update_other_user(user_fixtures):
    test_app = create_app()
    token, _ = create_access_token(user_fixtures["admin_id"], "admin_test_user_mgmt", "ADMIN")

    async def run():
        # Admin deactivates analyst user
        status, data = await asgi_request(
            test_app,
            "PATCH",
            f"/api/users/{user_fixtures['analyst_id']}",
            body={"is_active": False},
            headers=[(b"authorization", f"Bearer {token}".encode("ascii"))],
        )
        assert status == 200
        assert data["id"] == user_fixtures["analyst_id"]
        assert data["is_active"] is False

    asyncio.run(run())
