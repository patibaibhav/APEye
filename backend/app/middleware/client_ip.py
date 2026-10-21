"""Client IP resolution with trusted proxy anti-spoofing support.

Follows the blueprint specification:
- trusted_proxy_count == 0: return peer.
- N > 0: split X-Forwarded-For on commas, strip, take entries[-N].
- Validate with ipaddress; on any problem (too few entries, invalid IP) return peer.
- If peer is None or empty: return 'unknown'.
"""

import ipaddress
from typing import Optional


def resolve_client_ip(
    peer: Optional[str],
    forwarded_for: Optional[str],
    trusted_proxy_count: int = 0,
) -> str:
    """Resolves client IP respecting configured trusted proxy depth."""
    fallback = peer.strip() if (peer and peer.strip()) else "unknown"

    if trusted_proxy_count <= 0 or not forwarded_for:
        return fallback

    entries = [entry.strip() for entry in forwarded_for.split(",") if entry.strip()]

    if len(entries) < trusted_proxy_count:
        return fallback

    candidate = entries[-trusted_proxy_count]

    try:
        ipaddress.ip_address(candidate)
        return candidate
    except ValueError:
        return fallback
