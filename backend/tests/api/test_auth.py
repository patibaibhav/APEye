"""Tests for Authentication API and JWT handling (Owner: Anvi)."""

import asyncio
import json
from datetime import timedelta

import pytest

from app.auth.security import create_access_token, hash_password, verify_password
from app.db.models.user import User
from app.db.session import SessionLocal
from app.main import create_app


@pytest.fixture
def auth_user():
    session = SessionLocal()
    # Create test user
    pwd_hash = hash_password("ValidPassword123")
    user = User(
        username="auth_test_user",
        password_hash=pwd_hash,
        role="ANALYST",
        is_active=True,
    )
    session.add(user)
    session.commit()
    user_id = user.id
    session.close()

    yield {"id": user_id, "username": "auth_test_user", "password": "ValidPassword123"}

    # Cleanup
    cleanup_session = SessionLocal()
    u = cleanup_session.get(User, user_id)
    if u:
        cleanup_session.delete(u)
        cleanup_session.commit()
    cleanup_session.close()


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


def test_password_hashing_and_verification():
    raw_pwd = "SuperSecretPassword123"
    hashed = hash_password(raw_pwd)
    assert hashed != raw_pwd
    assert verify_password(raw_pwd, hashed) is True
    assert verify_password("WrongPassword123", hashed) is False


def test_login_success(auth_user):
    test_app = create_app()

    async def run():
        status, data = await asgi_request(
            test_app,
            "POST",
            "/api/auth/login",
            body={"username": auth_user["username"], "password": auth_user["password"]},
        )
        assert status == 200
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "expires_at" in data
        assert data["expires_at"].endswith("Z")
        assert data["user"]["username"] == auth_user["username"]
        assert data["user"]["role"] == "ANALYST"

    asyncio.run(run())


def test_login_invalid_password(auth_user):
    test_app = create_app()

    async def run():
        status, data = await asgi_request(
            test_app,
            "POST",
            "/api/auth/login",
            body={"username": auth_user["username"], "password": "WrongPassword999"},
        )
        assert status == 401
        assert data["error"]["code"] == "INVALID_CREDENTIALS"

    asyncio.run(run())


def test_login_unknown_user():
    test_app = create_app()

    async def run():
        status, data = await asgi_request(
            test_app,
            "POST",
            "/api/auth/login",
            body={"username": "non_existent_user_999", "password": "SomePassword123"},
        )
        assert status == 401
        assert data["error"]["code"] == "INVALID_CREDENTIALS"

    asyncio.run(run())


def test_logout():
    test_app = create_app()

    async def run():
        status, data = await asgi_request(test_app, "POST", "/api/auth/logout")
        assert status == 204

    asyncio.run(run())


def test_get_me_authenticated(auth_user):
    test_app = create_app()
    token, _ = create_access_token(auth_user["id"], auth_user["username"], "ANALYST")

    async def run():
        status, data = await asgi_request(
            test_app,
            "GET",
            "/api/auth/me",
            headers=[(b"authorization", f"Bearer {token}".encode("ascii"))],
        )
        assert status == 200
        assert data["id"] == auth_user["id"]
        assert data["username"] == auth_user["username"]
        assert data["role"] == "ANALYST"
        assert "password_hash" not in data

    asyncio.run(run())


def test_get_me_missing_token():
    test_app = create_app()

    async def run():
        status, data = await asgi_request(test_app, "GET", "/api/auth/me")
        assert status == 401
        assert data["error"]["code"] == "UNAUTHENTICATED"

    asyncio.run(run())


def test_get_me_expired_token(auth_user):
    test_app = create_app()
    # Create an expired token (negative delta)
    expired_token, _ = create_access_token(
        auth_user["id"],
        auth_user["username"],
        "ANALYST",
        expires_delta=timedelta(minutes=-5),
    )

    async def run():
        status, data = await asgi_request(
            test_app,
            "GET",
            "/api/auth/me",
            headers=[(b"authorization", f"Bearer {expired_token}".encode("ascii"))],
        )
        assert status == 401
        assert data["error"]["code"] == "TOKEN_EXPIRED"

    asyncio.run(run())


def test_get_me_invalid_token():
    test_app = create_app()

    async def run():
        status, data = await asgi_request(
            test_app,
            "GET",
            "/api/auth/me",
            headers=[(b"authorization", b"Bearer completely-invalid-garbage-token")],
        )
        assert status == 401
        assert data["error"]["code"] == "TOKEN_INVALID"

    asyncio.run(run())
