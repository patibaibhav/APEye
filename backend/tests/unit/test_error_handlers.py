"""Unit tests for error hierarchy and standardized error envelope formatting."""

import pytest
from pydantic import BaseModel, ValidationError as PydanticValidationError

from app.core.errors import (
    AlertNotFoundError,
    AppError,
    ForbiddenError,
    InvalidTransitionError,
    NotFoundError,
    TokenExpiredError,
    UnauthenticatedError,
    build_error_response,
)
from app.schemas.common import ErrorCode, ErrorEnvelope


def test_build_error_response_envelope():
    response = build_error_response(
        status_code=404,
        code="ALERT_NOT_FOUND",
        message="Alert not found",
        request_id="8f8f7b32-9009-4dcb-b214-01b6f3397629",
        details=None,
    )
    assert response.status_code == 404
    import json
    data = json.loads(response.body.decode("utf-8"))
    
    # Must validate against ErrorEnvelope schema
    envelope = ErrorEnvelope.model_validate(data)
    assert envelope.error.code == "ALERT_NOT_FOUND"
    assert envelope.error.message == "Alert not found"
    assert envelope.error.request_id == "8f8f7b32-9009-4dcb-b214-01b6f3397629"
    assert envelope.error.details is None


def test_app_error_hierarchy():
    err1 = AlertNotFoundError("Specific alert missing")
    assert err1.status_code == 404
    assert err1.code == ErrorCode.ALERT_NOT_FOUND.value

    err2 = UnauthenticatedError()
    assert err2.status_code == 401
    assert err2.code == ErrorCode.UNAUTHENTICATED.value

    err3 = TokenExpiredError()
    assert err3.status_code == 401
    assert err3.code == ErrorCode.TOKEN_EXPIRED.value

    err4 = ForbiddenError()
    assert err4.status_code == 403
    assert err4.code == ErrorCode.FORBIDDEN.value

    err5 = InvalidTransitionError("Cannot move to ACTIVE")
    assert err5.status_code == 409
    assert err5.code == ErrorCode.INVALID_TRANSITION.value


def test_error_envelope_rejects_extra_fields():
    class Dummy(BaseModel):
        pass

    with pytest.raises(PydanticValidationError):
        ErrorEnvelope.model_validate({
            "error": {
                "code": "TEST",
                "message": "msg",
                "request_id": "123",
                "stack_trace": "should_be_forbidden",
            }
        })
