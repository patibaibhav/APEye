"""Tests for CSV Exports and export limit enforcement (Owner: Anvi)."""

import asyncio

import pytest

from app.auth.security import create_access_token
from app.db.models.user import User
from app.db.session import SessionLocal
from app.main import create_app
from app.services.export_service import sanitize_csv_value


@pytest.fixture
def export_user():
    session = SessionLocal()
    user = User(
        username="export_test_user",
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
        return {"type": "http.request", "body": b"", "more_body": False}

    async def mock_send(msg):
        messages.append(msg)

    await app(scope, mock_receive, mock_send)

    start_msg = next((m for m in messages if m["type"] == "http.response.start"), None)
    body_msgs = [m for m in messages if m["type"] == "http.response.body"]
    assert start_msg is not None

    headers_dict = dict(start_msg["headers"])
    raw_body = b"".join(m.get("body", b"") for m in body_msgs)
    return start_msg["status"], headers_dict, raw_body.decode("utf-8")


def test_formula_injection_sanitization():
    # Dangerous spreadsheet prefixes
    assert sanitize_csv_value("=1+1") == "'=1+1"
    assert sanitize_csv_value("+cmd|' /C calc'!A0") == "'+cmd|' /C calc'!A0"
    assert sanitize_csv_value("-5+5") == "'-5+5"
    assert sanitize_csv_value("@SUM(A1:A10)") == "'@SUM(A1:A10)"
    assert sanitize_csv_value("\tmalicious") == "'\tmalicious"

    # Normal values remain untouched
    assert sanitize_csv_value(42) == 42
    assert sanitize_csv_value(3.14) == 3.14
    assert sanitize_csv_value(True) is True
    assert sanitize_csv_value("/api/logs") == "/api/logs"
    assert sanitize_csv_value("") == ""
    assert sanitize_csv_value(None) == ""


def test_export_logs_csv_success(export_user):
    test_app = create_app()

    async def run():
        status, headers, content = await asgi_request(
            test_app,
            "GET",
            "/api/exports/logs.csv",
            headers=[(b"authorization", f"Bearer {export_user['token']}".encode("ascii"))],
        )
        assert status == 200
        assert b"text/csv" in headers.get(b"content-type", b"")
        assert 'attachment; filename="logs.csv"' in headers.get(b"content-disposition", b"").decode(
            "ascii"
        )

        lines = content.strip().split("\n")
        assert len(lines) >= 1
        header_row = lines[0].split(",")
        assert "request_id" in header_row
        assert "occurred_at" in header_row
        assert "source_ip" in header_row
        assert "status_code" in header_row

    asyncio.run(run())


def test_export_alerts_csv_success(export_user):
    test_app = create_app()

    async def run():
        status, headers, content = await asgi_request(
            test_app,
            "GET",
            "/api/exports/alerts.csv",
            headers=[(b"authorization", f"Bearer {export_user['token']}".encode("ascii"))],
        )
        assert status == 200
        assert b"text/csv" in headers.get(b"content-type", b"")
        lines = content.strip().split("\n")
        assert len(lines) >= 1
        header_row = lines[0].split(",")
        assert "category" in header_row
        assert "severity" in header_row
        assert "source_ip" in header_row

    asyncio.run(run())


def test_export_limit_cap_returns_413(export_user, monkeypatch):
    test_app = create_app()
    # Set max rows to 0 to simulate export cap violation
    monkeypatch.setenv("EXPORT_MAX_ROWS", "0")

    async def run():
        status, headers, content = await asgi_request(
            test_app,
            "GET",
            "/api/exports/logs.csv",
            headers=[(b"authorization", f"Bearer {export_user['token']}".encode("ascii"))],
        )
        assert status == 413
        assert "EXPORT_TOO_LARGE" in content

    asyncio.run(run())
