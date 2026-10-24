"""Tests for Sandbox endpoints: access control, role gating, and ENABLE_SANDBOX toggle."""

import asyncio
import json
from typing import List, Optional

from app.api.routes.sandbox import get_admin_user, get_current_user
from app.core.config import CoreSettings, Settings
from app.main import create_app
from app.schemas.detection import RequestEvent


async def asgi_request(
    app,
    path: str,
    method: str = "GET",
    headers: Optional[list] = None,
):
    req_headers = [(b"host", b"testserver")]
    if headers:
        req_headers.extend(headers)

    scope = {
        "type": "http",
        "method": method,
        "path": path,
        "query_string": b"",
        "headers": req_headers,
        "client": ("198.51.100.1", 54321),
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
    status_code = start_msg["status"]
    body = b"".join(m.get("body", b"") for m in body_msgs)
    data = json.loads(body.decode("utf-8")) if body else {}

    return status_code, data


def test_sandbox_ping_public():
    captured_events: List[RequestEvent] = []
    test_app = create_app(ingest_callable=captured_events.append)

    async def run():
        status_code, data = await asgi_request(test_app, "/api/sandbox/ping")
        assert status_code == 200
        assert data == {"ok": True}
        # Ingestion captures sandbox traffic for simulator testing!
        assert len(captured_events) == 1
        assert captured_events[0].path == "/api/sandbox/ping"

    asyncio.run(run())


def test_sandbox_disabled_returns_404():
    # Configure ENABLE_SANDBOX=false
    disabled_settings = Settings(core=CoreSettings(enable_sandbox=False))
    test_app = create_app(settings=disabled_settings, ingest_callable=lambda e: None)

    async def run():
        # Ping returns 404 when sandbox is disabled
        status_code, data = await asgi_request(test_app, "/api/sandbox/ping")
        assert status_code == 404
        assert data["error"]["code"] == "NOT_FOUND"

        # Protected returns 404 when disabled
        status_code, data = await asgi_request(test_app, "/api/sandbox/protected")
        assert status_code == 404

        # Admin-only returns 404 when disabled
        status_code, data = await asgi_request(test_app, "/api/sandbox/admin-only")
        assert status_code == 404

    asyncio.run(run())


def test_sandbox_protected_unauthenticated():
    test_app = create_app(ingest_callable=lambda e: None)

    async def run():
        # No Authorization header provided
        status_code, data = await asgi_request(test_app, "/api/sandbox/protected")
        assert status_code == 401
        assert data["error"]["code"] == "UNAUTHENTICATED"

    asyncio.run(run())


def test_sandbox_protected_authorized():
    test_app = create_app(ingest_callable=lambda e: None)
    # Simulate valid authenticated user (ANALYST role)
    test_app.dependency_overrides[get_current_user] = lambda: {
        "id": 10,
        "username": "analyst1",
        "role": "ANALYST",
    }

    async def run():
        status_code, data = await asgi_request(
            test_app,
            "/api/sandbox/protected",
            headers=[(b"authorization", b"Bearer dummy-valid-token")],
        )
        assert status_code == 200
        assert data == {"ok": True}

    asyncio.run(run())


def test_sandbox_admin_only_forbidden_for_analyst():
    test_app = create_app(ingest_callable=lambda e: None)
    # User is authenticated but only has ANALYST role
    test_app.dependency_overrides[get_current_user] = lambda: {
        "id": 10,
        "username": "analyst1",
        "role": "ANALYST",
    }

    async def run():
        status_code, data = await asgi_request(
            test_app,
            "/api/sandbox/admin-only",
            headers=[(b"authorization", b"Bearer dummy-analyst-token")],
        )
        # Must return 403 Forbidden with standard error envelope
        assert status_code == 403
        assert data["error"]["code"] == "FORBIDDEN"

    asyncio.run(run())


def test_sandbox_admin_only_authorized_for_admin():
    test_app = create_app(ingest_callable=lambda e: None)
    # User is authenticated with ADMIN role
    admin_user = {"id": 1, "username": "admin", "role": "ADMIN"}
    test_app.dependency_overrides[get_current_user] = lambda: admin_user
    test_app.dependency_overrides[get_admin_user] = lambda: admin_user

    async def run():
        status_code, data = await asgi_request(
            test_app,
            "/api/sandbox/admin-only",
            headers=[(b"authorization", b"Bearer dummy-admin-token")],
        )
        assert status_code == 200
        assert data == {"ok": True}

    asyncio.run(run())
