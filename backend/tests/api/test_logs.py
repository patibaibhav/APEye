"""Tests for Request Logs API endpoints and filtering (Owner: Anvi)."""

import asyncio
import json
from datetime import datetime, timedelta, timezone

import pytest

from app.auth.security import create_access_token
from app.db.models.log import ApiRequestLog
from app.db.models.user import User
from app.db.session import SessionLocal
from app.main import create_app


@pytest.fixture
def log_fixtures():
    session = SessionLocal()
    now = datetime.now(timezone.utc)

    user = User(
        username="logs_test_user",
        password_hash="hash",
        role="ANALYST",
        is_active=True,
    )
    session.add(user)
    session.commit()

    l1 = ApiRequestLog(
        request_id="req-test-log-1",
        occurred_at=now - timedelta(minutes=10),
        source_ip="192.168.10.5",
        path="/api/users/profile",
        normalized_path="/api/users/profile",
        method="GET",
        status_code=200,
        response_time_ms=25,
        auth_outcome="AUTHENTICATED",
        user_id=user.id,
    )
    l2 = ApiRequestLog(
        request_id="req-test-log-2",
        occurred_at=now - timedelta(minutes=5),
        source_ip="198.51.100.22",
        path="/api/special%path_with_wildcards",
        normalized_path="/api/special%path_with_wildcards",
        method="POST",
        status_code=404,
        response_time_ms=10,
        auth_outcome="NONE",
        user_id=None,
    )
    session.add_all([l1, l2])
    session.commit()

    token, _ = create_access_token(user.id, user.username, user.role)
    user_id = user.id
    l1_id = l1.id
    session.close()

    yield {"token": token, "user_id": user_id, "l1_id": l1_id}

    cleanup = SessionLocal()
    for req_id in ("req-test-log-1", "req-test-log-2"):
        row = cleanup.query(ApiRequestLog).filter_by(request_id=req_id).first()
        if row:
            cleanup.delete(row)
    u = cleanup.get(User, user_id)
    if u:
        cleanup.delete(u)
    cleanup.commit()
    cleanup.close()


async def asgi_request(app, method, path, headers=None):
    req_headers = [(b"host", b"testserver")]
    if headers:
        req_headers.extend(headers)

    if "?" in path:
        clean_path, qs = path.split("?", 1)
        query_bytes = qs.encode("ascii")
    else:
        clean_path = path
        query_bytes = b""

    scope = {
        "type": "http",
        "method": method,
        "path": clean_path,
        "query_string": query_bytes,
        "headers": req_headers,
        "client": ("127.0.0.1", 12345),
        "state": {},
    }
    messages = []

    async def mock_receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    async def mock_send(msg):
        messages.append(msg)

    await app(scope, mock_receive, mock_send)

    start_msg = next((m for m in messages if m["type"] == "http.response.start"), None)
    body_msgs = [m for m in messages if m["type"] == "http.response.body"]
    assert start_msg is not None

    raw_body = b"".join(m.get("body", b"") for m in body_msgs)
    data = json.loads(raw_body.decode("utf-8")) if raw_body else {}
    return start_msg["status"], data


def test_list_logs_pagination_and_sorting(log_fixtures):
    test_app = create_app()

    async def run():
        status, data = await asgi_request(
            test_app,
            "GET",
            "/api/logs?page=1&page_size=10",
            headers=[(b"authorization", f"Bearer {log_fixtures['token']}".encode("ascii"))],
        )
        assert status == 200
        assert "items" in data
        assert "total_items" in data
        assert len(data["items"]) >= 2
        # Check sorting: occurred_at descending
        if len(data["items"]) >= 2:
            assert data["items"][0]["occurred_at"] >= data["items"][1]["occurred_at"]

    asyncio.run(run())


def test_list_logs_filter_exact_source_ip(log_fixtures):
    test_app = create_app()

    async def run():
        status, data = await asgi_request(
            test_app,
            "GET",
            "/api/logs?source_ip=198.51.100.22",
            headers=[(b"authorization", f"Bearer {log_fixtures['token']}".encode("ascii"))],
        )
        assert status == 200
        assert all(item["source_ip"] == "198.51.100.22" for item in data["items"])

    asyncio.run(run())


def test_list_logs_invalid_source_ip_fails_validation(log_fixtures):
    test_app = create_app()

    async def run():
        status, data = await asgi_request(
            test_app,
            "GET",
            "/api/logs?source_ip=not-an-ip-address",
            headers=[(b"authorization", f"Bearer {log_fixtures['token']}".encode("ascii"))],
        )
        assert status == 422
        assert data["error"]["code"] == "VALIDATION_ERROR"

    asyncio.run(run())


def test_list_logs_filter_endpoint_prefix_with_escaped_wildcards(log_fixtures):
    test_app = create_app()

    async def run():
        # Literal endpoint containing '%' and '_' must not act as SQL LIKE wildcards
        status, data = await asgi_request(
            test_app,
            "GET",
            "/api/logs?endpoint=/api/special%path_with_wildcards",
            headers=[(b"authorization", f"Bearer {log_fixtures['token']}".encode("ascii"))],
        )
        assert status == 200
        assert len(data["items"]) == 1
        assert data["items"][0]["path"] == "/api/special%path_with_wildcards"

    asyncio.run(run())


def test_get_single_log_success_and_not_found(log_fixtures):
    test_app = create_app()

    async def run():
        # Success
        status, data = await asgi_request(
            test_app,
            "GET",
            f"/api/logs/{log_fixtures['l1_id']}",
            headers=[(b"authorization", f"Bearer {log_fixtures['token']}".encode("ascii"))],
        )
        assert status == 200
        assert data["id"] == log_fixtures["l1_id"]
        assert data["source_ip"] == "192.168.10.5"

        # Not found
        status, data = await asgi_request(
            test_app,
            "GET",
            "/api/logs/99999999",
            headers=[(b"authorization", f"Bearer {log_fixtures['token']}".encode("ascii"))],
        )
        assert status == 404
        assert data["error"]["code"] == "NOT_FOUND"

    asyncio.run(run())
