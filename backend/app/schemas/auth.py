"""Authentication and User schemas (Owner: Anvi).

Follows Blueprint Section 5.10 and API Contract Section 8.2:
- POST /api/auth/login
- GET /api/auth/me
- Users CRUD models
"""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class Role(str, Enum):
    ADMIN = "ADMIN"
    ANALYST = "ANALYST"


class UserSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    role: str


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_at: str
    user: UserSummary


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    role: str
    is_active: bool
    created_at: datetime
    last_login_at: Optional[datetime] = None


class UserCreate(BaseModel):
    username: str = Field(..., min_length=1, max_length=50)
    password: str = Field(..., min_length=12)
    role: Role


class UserUpdate(BaseModel):
    is_active: Optional[bool] = None
    role: Optional[Role] = None


class TokenClaims(BaseModel):
    sub: str
    username: str
    role: str
    iat: int
    exp: int
