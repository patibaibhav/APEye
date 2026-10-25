"""Custom exception hierarchy and standardized error envelope handlers.

Follows the API Contract:
All non-2xx responses conform to:
{ "error": { "code": str, "message": str, "details": Any, "request_id": str } }
Never exposes internal stack traces or secrets to clients.
"""

import uuid
from typing import Any, Optional

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.logging_config import get_ops_logger
from app.schemas.common import ErrorCode, ErrorDetail, ErrorEnvelope


class AppError(Exception):
    """Base class for all application-level errors."""

    def __init__(
        self,
        message: str,
        code: ErrorCode | str = ErrorCode.INTERNAL_ERROR,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[Any] = None,
    ):
        super().__init__(message)
        self.message = message
        self.code = code.value if isinstance(code, ErrorCode) else str(code)
        self.status_code = status_code
        self.details = details


class UnauthenticatedError(AppError):
    def __init__(self, message: str = "Authentication required", details: Optional[Any] = None):
        super().__init__(
            message=message,
            code=ErrorCode.UNAUTHENTICATED,
            status_code=status.HTTP_401_UNAUTHORIZED,
            details=details,
        )


class TokenExpiredError(AppError):
    def __init__(self, message: str = "Token has expired", details: Optional[Any] = None):
        super().__init__(
            message=message,
            code=ErrorCode.TOKEN_EXPIRED,
            status_code=status.HTTP_401_UNAUTHORIZED,
            details=details,
        )


class TokenInvalidError(AppError):
    def __init__(self, message: str = "Invalid token", details: Optional[Any] = None):
        super().__init__(
            message=message,
            code=ErrorCode.TOKEN_INVALID,
            status_code=status.HTTP_401_UNAUTHORIZED,
            details=details,
        )


class InvalidCredentialsError(AppError):
    def __init__(self, message: str = "Invalid credentials", details: Optional[Any] = None):
        super().__init__(
            message=message,
            code=ErrorCode.INVALID_CREDENTIALS,
            status_code=status.HTTP_401_UNAUTHORIZED,
            details=details,
        )


class ForbiddenError(AppError):
    def __init__(self, message: str = "Forbidden", details: Optional[Any] = None):
        super().__init__(
            message=message,
            code=ErrorCode.FORBIDDEN,
            status_code=status.HTTP_403_FORBIDDEN,
            details=details,
        )


class NotFoundError(AppError):
    def __init__(self, message: str = "Resource not found", details: Optional[Any] = None):
        super().__init__(
            message=message,
            code=ErrorCode.NOT_FOUND,
            status_code=status.HTTP_404_NOT_FOUND,
            details=details,
        )


class AlertNotFoundError(AppError):
    def __init__(self, message: str = "Alert not found", details: Optional[Any] = None):
        super().__init__(
            message=message,
            code=ErrorCode.ALERT_NOT_FOUND,
            status_code=status.HTTP_404_NOT_FOUND,
            details=details,
        )


class ValidationError(AppError):
    def __init__(self, message: str = "Validation error", details: Optional[Any] = None):
        super().__init__(
            message=message,
            code=ErrorCode.VALIDATION_ERROR,
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            details=details,
        )


class InvalidTransitionError(AppError):
    def __init__(self, message: str = "Invalid status transition", details: Optional[Any] = None):
        super().__init__(
            message=message,
            code=ErrorCode.INVALID_TRANSITION,
            status_code=status.HTTP_409_CONFLICT,
            details=details,
        )


class UsernameTakenError(AppError):
    def __init__(self, message: str = "Username already exists", details: Optional[Any] = None):
        super().__init__(
            message=message,
            code=ErrorCode.USERNAME_TAKEN,
            status_code=status.HTTP_409_CONFLICT,
            details=details,
        )


class ExportTooLargeError(AppError):
    def __init__(self, message: str = "Export size limit exceeded", details: Optional[Any] = None):
        super().__init__(
            message=message,
            code=ErrorCode.EXPORT_TOO_LARGE,
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            details=details,
        )


class StorageDisabledError(AppError):
    def __init__(self, message: str = "Storage backend disabled", details: Optional[Any] = None):
        super().__init__(
            message=message,
            code=ErrorCode.STORAGE_DISABLED,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            details=details,
        )


class StorageUnavailableError(AppError):
    def __init__(self, message: str = "Storage service unavailable", details: Optional[Any] = None):
        super().__init__(
            message=message,
            code=ErrorCode.STORAGE_UNAVAILABLE,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            details=details,
        )


class InternalError(AppError):
    def __init__(self, message: str = "Internal server error", details: Optional[Any] = None):
        super().__init__(
            message=message,
            code=ErrorCode.INTERNAL_ERROR,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details,
        )


def _get_request_id(request: Request) -> str:
    """Extracts request_id from state or header or generates fallback."""
    if hasattr(request, "state") and getattr(request.state, "request_id", None):
        return str(request.state.request_id)
    header_id = request.headers.get("X-Request-ID")
    if header_id:
        return header_id
    return str(uuid.uuid4())


def build_error_response(
    status_code: int,
    code: str,
    message: str,
    request_id: str,
    details: Optional[Any] = None,
) -> JSONResponse:
    """Builds a compliant ErrorEnvelope JSONResponse."""
    envelope = ErrorEnvelope(
        error=ErrorDetail(
            code=code,
            message=message,
            details=details,
            request_id=request_id,
        )
    )
    return JSONResponse(status_code=status_code, content=envelope.model_dump())


def register_error_handlers(app: FastAPI) -> None:
    """Registers standard exception handlers mapping all non-2xx cases to the error envelope."""

    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
        req_id = _get_request_id(request)
        return build_error_response(
            status_code=exc.status_code,
            code=exc.code,
            message=exc.message,
            request_id=req_id,
            details=exc.details,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        req_id = _get_request_id(request)
        # Format field problems cleanly without leaking internal structures
        formatted_details = []
        for error in exc.errors():
            loc = " -> ".join(str(part) for part in error.get("loc", []))
            formatted_details.append({"loc": loc, "msg": error.get("msg"), "type": error.get("type")})

        return build_error_response(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            code=ErrorCode.VALIDATION_ERROR.value,
            message="Request validation failed",
            request_id=req_id,
            details=formatted_details,
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        req_id = _get_request_id(request)
        # Map common HTTP status codes to frozen error codes
        code = ErrorCode.INTERNAL_ERROR.value
        if exc.status_code == status.HTTP_401_UNAUTHORIZED:
            code = ErrorCode.UNAUTHENTICATED.value
        elif exc.status_code == status.HTTP_403_FORBIDDEN:
            code = ErrorCode.FORBIDDEN.value
        elif exc.status_code == status.HTTP_404_NOT_FOUND:
            code = ErrorCode.NOT_FOUND.value
        elif exc.status_code == status.HTTP_409_CONFLICT:
            code = ErrorCode.INVALID_TRANSITION.value
        elif exc.status_code == status.HTTP_413_REQUEST_ENTITY_TOO_LARGE:
            code = ErrorCode.EXPORT_TOO_LARGE.value
        elif exc.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT:
            code = ErrorCode.VALIDATION_ERROR.value
        elif exc.status_code == status.HTTP_503_SERVICE_UNAVAILABLE:
            code = ErrorCode.STORAGE_UNAVAILABLE.value

        message = str(exc.detail) if exc.detail else "HTTP Exception"
        return build_error_response(
            status_code=exc.status_code,
            code=code,
            message=message,
            request_id=req_id,
            details=None,
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        req_id = _get_request_id(request)
        ops_logger = get_ops_logger()
        # Log sanitized error message internally to ops logger; NEVER expose to client
        ops_logger.error(
            "unhandled_server_error",
            extra={
                "extra_fields": {
                    "request_id": req_id,
                    "error_type": type(exc).__name__,
                    "error_msg": str(exc),
                }
            },
        )
        return build_error_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            code=ErrorCode.INTERNAL_ERROR.value,
            message="Internal server error",
            request_id=req_id,
            details=None,
        )
