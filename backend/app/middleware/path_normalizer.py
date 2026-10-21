"""Path normalization utility.

Follows the blueprint specification:
- Strip trailing slash (except for '/').
- Replace purely numeric segments, UUIDs, and 16+ character hex segments with '{id}'.
- Truncate result to 512 characters.
"""

import re

_UUID_RE = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
)
_HEX_16_RE = re.compile(r"^[0-9a-fA-F]{16,}$")
_NUMERIC_RE = re.compile(r"^\d+$")


def normalize_path(path: str) -> str:
    """Normalizes path by stripping trailing slashes and replacing identifiers with '{id}'."""
    if not path:
        return "/"

    # Strip trailing slash (except '/')
    if len(path) > 1 and path.endswith("/"):
        path = path.rstrip("/")

    segments = path.split("/")
    normalized = []

    for seg in segments:
        if not seg:
            normalized.append(seg)
            continue

        if _NUMERIC_RE.match(seg) or _UUID_RE.match(seg) or _HEX_16_RE.match(seg):
            normalized.append("{id}")
        else:
            normalized.append(seg)

    result = "/".join(normalized)
    return result[:512]
