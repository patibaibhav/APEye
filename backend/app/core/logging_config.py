"""Operational JSON logging configuration for APEye.

Follows the Logging Contract: JSON output, UTC ISO-8601 timestamps with 'Z',
no secrets, passwords, tokens, or request bodies.
"""

import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any, Dict

_LOGGER_NAME = "app.ops"


class JsonFormatter(logging.Formatter):
    """Custom JSON formatter outputting one structured JSON line per log record."""

    def format(self, record: logging.LogRecord) -> str:
        # Base log data
        now = datetime.now(timezone.utc)
        ts = now.strftime("%Y-%m-%dT%H:%M:%SZ")

        log_data: Dict[str, Any] = {
            "ts": ts,
            "level": record.levelname,
            "event": getattr(record, "event", record.getMessage()),
        }

        # Optional request_id
        request_id = getattr(record, "request_id", None)
        if request_id:
            log_data["request_id"] = str(request_id)

        # Merge any extra metadata passed via extra={"extra_fields": {...}} or direct attributes
        extra_fields = getattr(record, "extra_fields", None)
        if isinstance(extra_fields, dict):
            # Sanitize and omit sensitive keys
            for k, v in extra_fields.items():
                if k.lower() not in {"password", "token", "secret", "authorization", "cookie"}:
                    log_data[k] = v

        if record.exc_info and not record.exc_text:
            # We record exception type and message, never exposing raw internal trace to output
            exc_type, exc_val, _ = record.exc_info
            if exc_type and exc_val:
                log_data["error"] = f"{exc_type.__name__}: {exc_val}"

        return json.dumps(log_data)


def configure_logging(log_level: str = "INFO") -> None:
    """Configures the root and app.ops logger with standard JSON stream handler."""
    level = getattr(logging, log_level.upper(), logging.INFO)

    ops_logger = logging.getLogger(_LOGGER_NAME)
    ops_logger.setLevel(level)

    # Avoid duplicate handlers if reconfigured
    if not any(isinstance(h, logging.StreamHandler) for h in ops_logger.handlers):
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JsonFormatter())
        ops_logger.addHandler(handler)

    ops_logger.propagate = False


def get_ops_logger() -> logging.Logger:
    """Returns the central operational logger 'app.ops'."""
    logger = logging.getLogger(_LOGGER_NAME)
    if not logger.handlers:
        configure_logging()
    return logger
