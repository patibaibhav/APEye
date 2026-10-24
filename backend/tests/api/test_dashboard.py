"""Tests for Dashboard aggregate routes and bucket zero-filling (Owner: Anvi)."""

import asyncio
import json

import pytest

from app.auth.security import create_access_token
from app.db.models.user import User
from app.db.session import SessionLocal
from app.main import create_app


@pytest.fixture
def dash_fixtures():
    session = SessionLocal()
    user = User(
        username="dash_test_user",
        password_hash="hash",
        role="ANALYST",
        is_active=True,
    )
    session.add(user)
    session.commit()

    token, _ = create_access_token(user.id, user.username, user.role)
    user_id = user.id
    session.close()

    yield {"token": token, "user_id": user_id}

    cleanup = SessionLocal()
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


def test_dashboard_summary(dash_fixtures):
    test_app = create_app()

    async def run():
        status, data = await asgi_request(
            test_app,
            "GET",
            "/api/dashboard/summary",
            headers=[(b"authorization", f"Bearer {dash_fixtures['token']}".encode("ascii"))],
        )
        assert status == 200
        assert "window" in data
        assert "from" in data["window"]
        assert "to" in data["window"]
        assert "total_requests" in data
        assert "successful_requests" in data
        assert "failed_requests" in data
        assert "total_alerts" in data
        assert "distinct_suspicious_ips" in data

    asyncio.run(run())


def test_dashboard_traffic_zero_filled(dash_fixtures):
    test_app = create_app()

    async def run():
        status, data = await asgi_request(
            test_app,
            "GET",
            "/api/dashboard/traffic?interval=1h",
            headers=[(b"authorization", f"Bearer {dash_fixtures['token']}".encode("ascii"))],
        )
        assert status == 200
        assert data["interval"] == "1h"
        points = data["points"]
        # Default 24h window with 1h interval should have 24 zero-filled points
        assert len(points) == 24
        for p in points:
            assert "bucket_start" in p
            assert "total" in p
            assert "successful" in p
            assert "failed" in p
            assert p["total"] >= 0

    asyncio.run(run())


def test_dashboard_status_distribution(dash_fixtures):
    test_app = create_app()

    async def run():
        status, data = await asgi_request(
            test_app,
            "GET",
            "/api/dashboard/status-distribution",
            headers=[(b"authorization", f"Bearer {dash_fixtures['token']}".encode("ascii"))],
        )
        assert status == 200
        assert "classes" in data
        assert "codes" in data
        assert isinstance(data["classes"], list)
        assert isinstance(data["codes"], list)

    asyncio.run(run())


def test_dashboard_top_endpoints(dash_fixtures):
    test_app = create_app()

    async def run():
        status, data = await asgi_request(
            test_app,
            "GET",
            "/api/dashboard/top-endpoints?limit=5",
            headers=[(b"authorization", f"Bearer {dash_fixtures['token']}".encode("ascii"))],
        )
        assert status == 200
        assert "items" in data
        assert len(data["items"]) <= 5
        for item in data["items"]:
            assert "endpoint" in item
            assert "request_count" in item
            assert "error_count" in item

    asyncio.run(run())


def test_dashboard_response_times(dash_fixtures):
    test_app = create_app()

    async def run():
        status, data = await asgi_request(
            test_app,
            "GET",
            "/api/dashboard/response-times?interval=1h",
            headers=[(b"authorization", f"Bearer {dash_fixtures['token']}".encode("ascii"))],
        )
        assert status == 200
        assert "points" in data
        assert len(data["points"]) == 24
        for p in data["points"]:
            assert "avg_ms" in p
            assert "p95_ms" in p
            assert "max_ms" in p

    asyncio.run(run())


def test_dashboard_alert_severity_guaranteed_severities(dash_fixtures):
    test_app = create_app()

    async def run():
        status, data = await asgi_request(
            test_app,
            "GET",
            "/api/dashboard/alert-severity",
            headers=[(b"authorization", f"Bearer {dash_fixtures['token']}".encode("ascii"))],
        )
        assert status == 200
        severities = {item["severity"]: item["count"] for item in data["items"]}
        # Always includes LOW, MEDIUM, and HIGH per API contract!
        assert "LOW" in severities
        assert "MEDIUM" in severities
        assert "HIGH" in severities

    asyncio.run(run())
