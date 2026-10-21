"""Tests for GET /api/health endpoint."""

import asyncio
import json
from typing import List

from app.api.routes.health import check_database_connectivity
from app.main import create_app
from app.schemas.detection import RequestEvent


async def asgi_get(app, path: str):
    scope = {
        "type": "http",
        "method": "GET",
        "path": path,
        "query_string": b"",
        "headers": [(b"host", b"testserver")],
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
    status_code = start_msg["status"]
    headers = dict(start_msg["headers"])
    body = b"".join(m.get("body", b"") for m in body_msgs)
    data = json.loads(body.decode("utf-8")) if body else {}

    return status_code, headers, data


def test_health_ok_when_database_connected():
    captured_events: List[RequestEvent] = []
    test_app = create_app(ingest_callable=captured_events.append)
    test_app.dependency_overrides[check_database_connectivity] = lambda: True

    async def run():
        status_code, headers, data = await asgi_get(test_app, "/api/health")
        assert status_code == 200
        assert data["status"] == "ok"
        assert data["database"] == "ok"
        assert "version" in data
        assert "time" in data
        assert data["time"].endswith("Z")
        # Ensure /api/health is in ignored_paths and no request log is created
        assert len(captured_events) == 0

    asyncio.run(run())


def test_health_503_when_database_fails():
    test_app = create_app(ingest_callable=lambda e: None)
    test_app.dependency_overrides[check_database_connectivity] = lambda: False

    async def run():
        status_code, headers, data = await asgi_get(test_app, "/api/health")
        # 503 Service Unavailable when DB is down
        assert status_code == 503
        assert data["status"] == "ok"
        assert data["database"] == "error"
        assert "version" in data
        assert "time" in data

    asyncio.run(run())
