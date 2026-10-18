"""Accounts: registration, login, sessions, password change and reset."""

import logging
from dataclasses import dataclass
from datetime import timedelta
from urllib.parse import urlencode

from taskboard.domain.entities import IssuedSession, User
from taskboard.domain.enums import Role
from taskboard.domain.errors import (
    AuthenticationRequiredError,
    ConflictError,
    InvalidCredentialsError,
    RateLimitedError,
    ValidationFailedError,
)
from taskboard.infra.mailer import Mailer
from taskboard.infra.rate_limit import RateLimiter, limiter_key
from taskboard.repositories.interfaces import (
    ResetTokenRepository,
    SessionRepository,
    UnitOfWork,
    UserRepository,
)
from taskboard.services.security import (
    Clock,
    PasswordHasher,
    check_password_policy,
    hash_token,
    new_token,
)

logger = logging.getLogger("taskboard.auth")


@dataclass(frozen=True, slots=True)
class AuthPolicy:
    session_ttl_seconds: int
    reset_token_ttl_seconds: int
    public_base_url: str
    login_max_failures: int
    login_max_account_failures: int
    login_max_attempts_per_ip: int
    forgot_max_per_ip: int
    register_max_per_ip: int
    rate_limit_window_seconds: int


def normalize_email(email: str) -> str:
    return email.strip().lower()


class AuthService:
    def __init__(
        self,
        *,
        users: UserRepository,
        sessions: SessionRepository,
        reset_tokens: ResetTokenRepository,
        mailer: Mailer,
        hasher: PasswordHasher,
        limiter: RateLimiter,
        clock: Clock,
        uow: UnitOfWork,
        policy: AuthPolicy,
    ) -> None:
        self._users = users
        self._sessions = sessions
        self._reset_tokens = reset_tokens
        self._mailer = mailer
        self._hasher = hasher
        self._limiter = limiter
        self._clock = clock
        self._uow = uow
        self._policy = policy

    def _throttle(self, scope: str, value: str, limit: int) -> None:
        key = limiter_key(scope, value)
        if self._limiter.hit(key, self._policy.rate_limit_window_seconds) > limit:
            logger.warning("rate limit exceeded", extra={"scope": scope})
            raise RateLimitedError()

    def register(self, email: str, display_name: str, password: str, client_ip: str) -> User:
        self._throttle("register-ip", client_ip, self._policy.register_max_per_ip)
        email = normalize_email(email)
        check_password_policy(password)
        if self._users.get_by_email(email) is not None:
            raise ConflictError("An account with this email already exists.")
        user = self._users.add(
            email, display_name.strip(), self._hasher.hash(password), Role.MEMBER
        )
        self._uow.commit()
        logger.info("user registered", extra={"user_id": str(user.id)})
        return user

    def login(self, email: str, password: str, client_ip: str) -> IssuedSession:
        email = normalize_email(email)
        self._throttle("login-ip", client_ip, self._policy.login_max_attempts_per_ip)
        # Lock per (email, client) so a third party cannot lock the owner out, and keep a much
        # higher per-account ceiling that still slows guessing spread across many clients.
        failure_key = limiter_key("login-fail", f"{email}|{client_ip}")
        account_key = limiter_key("login-fail-account", email)
        if (
            self._limiter.count(failure_key) >= self._policy.login_max_failures
            or self._limiter.count(account_key) >= self._policy.login_max_account_failures
        ):
            logger.warning("login blocked after repeated failures")
            raise RateLimitedError()
        credentials = self._users.get_credentials(email)
        if credentials is None:
            self._hasher.burn(password)
        valid = (
            credentials is not None
            and credentials.user.is_active
            and self._hasher.verify(credentials.password_hash, password)
        )
        if credentials is None or not valid:
            self._limiter.hit(failure_key, self._policy.rate_limit_window_seconds)
            self._limiter.hit(account_key, self._policy.rate_limit_window_seconds)
            logger.info("login failed", extra={"client_ip": client_ip})
            raise InvalidCredentialsError()
        self._limiter.reset(failure_key)
        issued = self._issue_session(credentials.user)
        self._uow.commit()
        logger.info("login succeeded", extra={"user_id": str(credentials.user.id)})
        return issued

    def _issue_session(self, user: User) -> IssuedSession:
        now = self._clock.now()
        self._sessions.delete_expired_for_user(user.id, now)
        token = new_token()
        expires_at = now + timedelta(seconds=self._policy.session_ttl_seconds)
        self._sessions.add(user.id, hash_token(token), expires_at)
        return IssuedSession(token=token, expires_at=expires_at, user=user)

    def authenticate(self, token: str) -> User:
        user = self._sessions.find_user(hash_token(token), self._clock.now())
        if user is None:
            raise AuthenticationRequiredError()
        return user

    def logout(self, token: str) -> None:
        self._sessions.delete(hash_token(token))
        self._uow.commit()

    def change_password(self, actor: User, current: str, new: str) -> IssuedSession:
        """Change the password, end every session, and return a fresh one for the caller."""
        # A stolen session must not become a way to guess the account password.
        failure_key = limiter_key("password-change-fail", str(actor.id))
        if self._limiter.count(failure_key) >= self._policy.login_max_failures:
            raise RateLimitedError()
        stored = self._users.get_password_hash(actor.id)
        if stored is None or not self._hasher.verify(stored, current):
            self._limiter.hit(failure_key, self._policy.rate_limit_window_seconds)
            raise ValidationFailedError("Current password is incorrect.")
        self._limiter.reset(failure_key)
        check_password_policy(new)
        self._users.set_password_hash(actor.id, self._hasher.hash(new))
        self._sessions.delete_for_user(actor.id)
        self._reset_tokens.invalidate_for_user(actor.id, self._clock.now())
        issued = self._issue_session(actor)
        self._uow.commit()
        logger.info("password changed", extra={"user_id": str(actor.id)})
        return issued

    def forgot_password(self, email: str, client_ip: str) -> None:
        """Always succeeds from the caller's point of view, so it reveals nothing about accounts."""
        email = normalize_email(email)
        self._throttle("forgot-ip", client_ip, self._policy.forgot_max_per_ip)
        self._throttle("forgot-email", email, self._policy.forgot_max_per_ip)
        user = self._users.get_by_email(email)
        if user is None or not user.is_active:
            return
        now = self._clock.now()
        self._reset_tokens.invalidate_for_user(user.id, now)
        token = new_token()
        expires = now + timedelta(seconds=self._policy.reset_token_ttl_seconds)
        self._reset_tokens.add(user.id, hash_token(token), expires)
        base = self._policy.public_base_url.rstrip("/")
        link = f"{base}/reset-password?{urlencode({'token': token})}"
        minutes = self._policy.reset_token_ttl_seconds // 60
        self._mailer.send(
            user.email,
            "Reset your Taskboard password",
            f"Hello {user.display_name},\n\nUse this link within {minutes} minutes to set a new "
            f"password:\n\n{link}\n\nIf you did not ask for this, you can ignore this email.\n",
        )
        self._uow.commit()
        logger.info("password reset requested", extra={"user_id": str(user.id)})

    def reset_password(self, token: str, new: str) -> None:
        check_password_policy(new)
        user_id = self._reset_tokens.consume(hash_token(token), self._clock.now())
        if user_id is None:
            raise ValidationFailedError("This reset link is invalid or has expired.")
        self._users.set_password_hash(user_id, self._hasher.hash(new))
        self._sessions.delete_for_user(user_id)
        self._uow.commit()
        logger.info("password reset completed", extra={"user_id": str(user_id)})
