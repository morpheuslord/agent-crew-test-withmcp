"""Schemas for authentication, profiles and admin user management."""

from datetime import datetime
from uuid import UUID

from pydantic import Field

from taskboard.api.schemas.common import (
    Email,
    Name,
    PageMeta,
    Password,
    RequestModel,
    ResponseModel,
)
from taskboard.domain.enums import Role


class RegisterRequest(RequestModel):
    email: Email
    display_name: Name
    password: Password


class LoginRequest(RequestModel):
    email: Email
    password: Password


class ChangePasswordRequest(RequestModel):
    current_password: Password
    new_password: Password


class ForgotPasswordRequest(RequestModel):
    email: Email


class ResetPasswordRequest(RequestModel):
    token: str = Field(min_length=20, max_length=200, pattern=r"^[A-Za-z0-9_-]+$")
    new_password: Password


class UserOut(ResponseModel):
    id: UUID
    email: str
    display_name: str
    role: Role
    is_active: bool
    created_at: datetime


class LoginResponse(ResponseModel):
    token: str
    expires_at: datetime
    user: UserOut


class MessageOut(ResponseModel):
    message: str


class UserPage(PageMeta):
    items: list[UserOut]


class AdminUserUpdate(RequestModel):
    role: Role | None = None
    is_active: bool | None = None
