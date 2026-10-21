"""Unit tests for client IP resolution and anti-spoofing."""

from app.middleware.client_ip import resolve_client_ip


def test_client_ip_trusted_proxy_count_zero():
    # When N=0, XFF header is completely ignored; socket peer is always returned
    peer = "203.0.113.195"
    spoofed_xff = "10.0.0.1, 192.168.1.1"
    assert resolve_client_ip(peer, spoofed_xff, trusted_proxy_count=0) == peer


def test_client_ip_single_trusted_proxy_ignores_spoofed_leftmost():
    # Behind 1 trusted proxy (e.g., NGINX/ALB): entries[-1] is the client IP from proxy
    peer = "172.31.0.10"  # Nginx private IP
    # Attacker sent: X-Forwarded-For: 1.1.1.1, 2.2.2.2; Nginx appended 203.0.113.50
    xff = "1.1.1.1, 2.2.2.2, 203.0.113.50"
    assert resolve_client_ip(peer, xff, trusted_proxy_count=1) == "203.0.113.50"


def test_client_ip_multiple_trusted_proxies():
    peer = "172.31.0.10"
    xff = "203.0.113.50, 10.0.0.5, 10.0.0.6"
    assert resolve_client_ip(peer, xff, trusted_proxy_count=2) == "10.0.0.5"


def test_client_ip_too_few_entries_falls_back_to_peer():
    peer = "172.31.0.10"
    xff = "203.0.113.50"  # Only 1 entry, but N=2
    assert resolve_client_ip(peer, xff, trusted_proxy_count=2) == peer


def test_client_ip_malformed_header_falls_back_to_peer():
    peer = "172.31.0.10"
    xff = "not_an_ip, definitely_invalid"
    assert resolve_client_ip(peer, xff, trusted_proxy_count=1) == peer


def test_client_ip_ipv6_support():
    peer = "fe80::1"
    xff = "2001:db8:85a3::8a2e:370:7334"
    assert resolve_client_ip(peer, xff, trusted_proxy_count=1) == "2001:db8:85a3::8a2e:370:7334"
    assert resolve_client_ip(peer, xff, trusted_proxy_count=0) == peer


def test_client_ip_missing_peer():
    # None peer returns 'unknown' when no proxy or invalid
    assert resolve_client_ip(None, None, trusted_proxy_count=0) == "unknown"
    assert resolve_client_ip("", "invalid", trusted_proxy_count=1) == "unknown"
    assert resolve_client_ip(None, "203.0.113.50", trusted_proxy_count=1) == "203.0.113.50"
