"""Unit tests for path normalization."""

from app.middleware.path_normalizer import normalize_path


def test_normalize_numeric_id():
    assert normalize_path("/api/logs/123") == "/api/logs/{id}"
    assert normalize_path("/api/users/99999/status") == "/api/users/{id}/status"


def test_normalize_uuid():
    uuid_str = "8f8f7b32-9009-4dcb-b214-01b6f3397629"
    assert normalize_path(f"/api/alerts/{uuid_str}") == "/api/alerts/{id}"
    assert normalize_path(f"/api/alerts/{uuid_str}/notes") == "/api/alerts/{id}/notes"


def test_normalize_16_plus_hex_segment():
    hex_16 = "0123456789abcdef"
    hex_32 = "a1b2c3d4e5f67890123456789abcdef0"
    assert normalize_path(f"/api/reports/{hex_16}") == "/api/reports/{id}"
    assert normalize_path(f"/api/reports/{hex_32}/download") == "/api/reports/{id}/download"

    # Hex segment with less than 16 characters should not be normalized as hex
    short_hex = "abcdef12"  # 8 chars
    assert normalize_path(f"/api/short/{short_hex}") == f"/api/short/{short_hex}"


def test_normalize_trailing_slash():
    assert normalize_path("/api/logs/") == "/api/logs"
    assert normalize_path("/api/alerts///") == "/api/alerts"
    assert normalize_path("/") == "/"


def test_normalize_truncation():
    # Very long path with over 512 characters
    long_segment = "a" * 600
    path = f"/api/long/{long_segment}"
    normalized = normalize_path(path)
    assert len(normalized) <= 512
