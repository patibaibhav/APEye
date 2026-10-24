"""Tests for Reports API and Archive Generation (Owner: Anvi)."""

import asyncio
import json

import pytest

from app.auth.security import create_access_token
from app.db.models.user import User
from app.db.session import SessionLocal
from app.main import create_app


@pytest.fixture
def report_users():
    session = SessionLocal()
    admin = User(
        username="report_admin_user",
        password_hash="hash",
        role="ADMIN",
        is_active=True,
    )
    analyst = User(
        username="report_analyst_user",
        password_hash="hash",
        role="ANALYST",
        is_active=True,
    )
    session.add_all([admin, analyst])
    session.commit()

    admin_token, _ = create_access_token(admin.id, admin.username, "ADMIN")
    analyst_token, _ = create_access_token(analyst.id, analyst.username, "ANALYST")
    admin_id = admin.id
    analyst_id = analyst.id
    session.close()

    yield {
        "admin_token": admin_token,
        "analyst_token": analyst_token,
        "admin_id": admin_id,
        "analyst_id": analyst_id,
    }

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
        return {"type": "http.request", "body": body_bytes, "more_body": False}

    async def mock_send(msg):
        messages.append(msg)

    await app(scope, mock_receive, mock_send)

    start_msg = next((m for m in messages if m["type"] == "http.response.start"), None)
    body_msgs = [m for m in messages if m["type"] == "http.response.body"]
    assert start_msg is not None

    raw_body = b"".join(m.get("body", b"") for m in body_msgs)
    try:
        data = json.loads(raw_body.decode("utf-8")) if raw_body else {}
    except Exception:
        data = raw_body.decode("utf-8", errors="replace")
    return start_msg["status"], data


def test_get_report_summary(report_users):
    test_app = create_app()

    async def run():
        status, data = await asgi_request(
            test_app,
            "GET",
            "/api/reports/summary",
            headers=[(b"authorization", f"Bearer {report_users['analyst_token']}".encode("ascii"))],
        )
        assert status == 200
        assert "range" in data
        assert "total_requests" in data
        assert "threat_breakdown" in data
        assert "top_suspicious_ips" in data

    asyncio.run(run())


def test_archive_forbidden_for_analyst(report_users):
    test_app = create_app()

    async def run():
        status, data = await asgi_request(
            test_app,
            "POST",
            "/api/reports/archive",
            body={
                "report_type": "SUMMARY",
                "from": "2026-01-01T00:00:00Z",
                "to": "2026-01-02T00:00:00Z",
            },
            headers=[(b"authorization", f"Bearer {report_users['analyst_token']}".encode("ascii"))],
        )
        assert status == 403
        assert data["error"]["code"] == "FORBIDDEN"

    asyncio.run(run())


def test_archive_creation_and_download_flow(report_users, tmp_path, monkeypatch):
    monkeypatch.setenv("STORAGE_BACKEND", "local")
    monkeypatch.setenv("LOCAL_STORAGE_DIR", str(tmp_path))

    test_app = create_app()

    async def run():
        # 1. Create SUMMARY archive as ADMIN
        status, data = await asgi_request(
            test_app,
            "POST",
            "/api/reports/archive",
            body={
                "report_type": "SUMMARY",
                "from": "2026-01-01T00:00:00Z",
                "to": "2026-01-02T00:00:00Z",
            },
            headers=[(b"authorization", f"Bearer {report_users['admin_token']}".encode("ascii"))],
        )
        assert status == 201
        archive_id = data["id"]
        assert data["report_type"] == "SUMMARY"
        assert data["storage_backend"] == "local"
        assert data["size_bytes"] > 0
        assert "range" in data

        # 2. List archives
        status, list_data = await asgi_request(
            test_app,
            "GET",
            "/api/reports",
            headers=[(b"authorization", f"Bearer {report_users['analyst_token']}".encode("ascii"))],
        )
        assert status == 200
        assert list_data["total_items"] >= 1

        # 3. Request download URL
        status, dl_data = await asgi_request(
            test_app,
            "GET",
            f"/api/reports/{archive_id}/download",
            headers=[(b"authorization", f"Bearer {report_users['analyst_token']}".encode("ascii"))],
        )
        assert status == 200
        assert "url" in dl_data
        assert "expires_at" in dl_data
        assert "/api/reports/file" in dl_data["url"]

        # 4. Download file contents via file streaming endpoint
        status, file_content = await asgi_request(
            test_app,
            "GET",
            dl_data["url"],
            headers=[(b"authorization", f"Bearer {report_users['analyst_token']}".encode("ascii"))],
        )
        assert status == 200

    asyncio.run(run())
