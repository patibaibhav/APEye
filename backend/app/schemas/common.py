"""Common schemas, enums, error envelopes, and pagination models."""

from enum import Enum
from typing import Any, Generic, List, Optional, TypeVar
from pydantic import BaseModel, ConfigDict, Field


class ThreatCategory(str, Enum):
    BRUTE_FORCE = "BRUTE_FORCE"
    EXCESSIVE_REQUESTS = "EXCESSIVE_REQUESTS"
    RECONNAISSANCE = "RECONNAISSANCE"
    UNAUTHORIZED_ACCESS = "UNAUTHORIZED_ACCESS"


class Severity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class AlertStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INVESTIGATING = "INVESTIGATING"
    RESOLVED = "RESOLVED"


class AuthOutcome(str, Enum):
    NONE = "NONE"
    AUTHENTICATED = "AUTHENTICATED"
    LOGIN_SUCCESS = "LOGIN_SUCCESS"
    LOGIN_FAILED = "LOGIN_FAILED"
    TOKEN_INVALID = "TOKEN_INVALID"
    TOKEN_EXPIRED = "TOKEN_EXPIRED"
    FORBIDDEN = "FORBIDDEN"


class ErrorCode(str, Enum):
    UNAUTHENTICATED = "UNAUTHENTICATED"
    TOKEN_EXPIRED = "TOKEN_EXPIRED"
    TOKEN_INVALID = "TOKEN_INVALID"
    INVALID_CREDENTIALS = "INVALID_CREDENTIALS"
    FORBIDDEN = "FORBIDDEN"
    NOT_FOUND = "NOT_FOUND"
    ALERT_NOT_FOUND = "ALERT_NOT_FOUND"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    INVALID_TRANSITION = "INVALID_TRANSITION"
    USERNAME_TAKEN = "USERNAME_TAKEN"
    EXPORT_TOO_LARGE = "EXPORT_TOO_LARGE"
    STORAGE_DISABLED = "STORAGE_DISABLED"
    STORAGE_UNAVAILABLE = "STORAGE_UNAVAILABLE"
    INTERNAL_ERROR = "INTERNAL_ERROR"


class ErrorDetail(BaseModel):
    model_config = ConfigDict(extra="forbid")
    code: str
    message: str
    details: Optional[Any] = None
    request_id: str


class ErrorEnvelope(BaseModel):
    model_config = ConfigDict(extra="forbid")
    error: ErrorDetail


T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    page: int = Field(..., ge=1, description="1-based page number")
    page_size: int = Field(..., ge=1, le=100, description="Items per page")
    total_items: int = Field(..., ge=0, description="Total count of items across all pages")
    total_pages: int = Field(..., ge=0, description="Total pages count")
