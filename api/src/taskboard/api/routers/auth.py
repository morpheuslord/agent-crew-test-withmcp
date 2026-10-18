"""Authentication and profile endpoints."""

from fastapi import APIRouter, status

from taskboard.api.deps import BearerToken, ClientIp, CurrentUser, Services
from taskboard.api.schemas.accounts import (
    ChangePasswordRequest,
    ForgotPasswordRequest,
    LoginRequest,
    LoginResponse,
    MessageOut,
    RegisterRequest,
    ResetPasswordRequest,
    UserOut,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(body: RegisterRequest, services: Services, ip: ClientIp) -> UserOut:
    user = services.auth.register(body.email, body.display_name, body.password, ip)
    return UserOut.model_validate(user)


@router.post("/login")
def login(body: LoginRequest, services: Services, ip: ClientIp) -> LoginResponse:
    return LoginResponse.model_validate(services.auth.login(body.email, body.password, ip))


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(services: Services, token: BearerToken) -> None:
    services.auth.logout(token)


@router.get("/me")
def me(user: CurrentUser) -> UserOut:
    return UserOut.model_validate(user)


@router.post("/password/change")
def change_password(
    body: ChangePasswordRequest, services: Services, user: CurrentUser
) -> LoginResponse:
    issued = services.auth.change_password(user, body.current_password, body.new_password)
    return LoginResponse.model_validate(issued)


@router.post("/password/forgot", status_code=status.HTTP_202_ACCEPTED)
def forgot_password(body: ForgotPasswordRequest, services: Services, ip: ClientIp) -> MessageOut:
    services.auth.forgot_password(body.email, ip)
    return MessageOut(message="If an account exists for that email, a reset link has been sent.")


@router.post("/password/reset")
def reset_password(body: ResetPasswordRequest, services: Services) -> MessageOut:
    services.auth.reset_password(body.token, body.new_password)
    return MessageOut(message="Your password has been reset. You can now log in.")
