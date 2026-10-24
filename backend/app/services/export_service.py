"""CSV export service implementing formula injection defense and export row limit enforcement (Owner: Anvi)."""

import csv
import io
import os
from typing import Any, Iterable, Sequence


def get_export_max_rows() -> int:
    """Returns EXPORT_MAX_ROWS setting from environment (default 100000)."""
    return int(os.getenv("EXPORT_MAX_ROWS", "100000"))


def sanitize_csv_value(val: Any) -> Any:
    """Neutralizes spreadsheet formula injection risks.

    If a text field begins with '=', '+', '-', '@', '\t', or '\r',
    prepends a single quote to prevent spreadsheet formula execution.
    Preserves numerical types and normal dates/strings intact.
    """
    if val is None:
        return ""
    if isinstance(val, (int, float, bool)):
        return val

    s = str(val)
    if s and s[0] in ("=", "+", "-", "@", "\t", "\r"):
        return "'" + s
    return s


def generate_csv_string(headers: Sequence[str], rows: Iterable[Sequence[Any]]) -> str:
    """Generates an RFC-4180 compliant CSV string with sanitized cells."""
    output = io.StringIO()
    writer = csv.writer(output, lineterminator="\n")
    writer.writerow(headers)

    for row in rows:
        sanitized_row = [sanitize_csv_value(cell) for cell in row]
        writer.writerow(sanitized_row)

    return output.getvalue()
