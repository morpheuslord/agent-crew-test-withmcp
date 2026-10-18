"""Password hashing, token generation and the clock, behind small interfaces."""

import hashlib
import secrets
from datetime import UTC, datetime
from typing import Protocol

from argon2 import PasswordHasher as _Argon2
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError

from taskboard.domain.errors import ValidationFailedError

MIN_PASSWORD_LENGTH = 12
MAX_PASSWORD_LENGTH = 128


class PasswordHasher(Protocol):
    def hash(self, password: str) -> str: ...

    def verify(self, password_hash: str, password: str) -> bool: ...

    def burn(self, password: str) -> None:
        """Spend the time of one verification without a real hash (unknown accounts)."""
        ...


class Argon2PasswordHasher:
    """Argon2id with argon2-cffi's recommended parameters."""

    def __init__(self) -> None:
        self._hasher = _Argon2()
        # Verifying against a real hash for unknown accounts keeps login timing uniform.
        self._dummy_hash = self._hasher.hash(secrets.token_urlsafe(16))

    def hash(self, password: str) -> str:
        return self._hasher.hash(password)

    def verify(self, password_hash: str, password: str) -> bool:
        try:
            return self._hasher.verify(password_hash, password)
        except (VerifyMismatchError, VerificationError, InvalidHashError):
            return False

    def burn(self, password: str) -> None:
        """Spend the same time as a real verification, for accounts that do not exist."""
        self.verify(self._dummy_hash, password)


class Clock(Protocol):
    def now(self) -> datetime: ...


class SystemClock:
    def now(self) -> datetime:
        return datetime.now(UTC)


def new_token() -> str:
    """256 bits from the OS CSPRNG, URL-safe."""
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    """Tokens are stored only as SHA-256 digests; they are high-entropy, so no salt is needed."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def check_password_policy(password: str) -> None:
    """Length-based policy: 12 to 128 characters, any characters allowed."""
    if len(password) < MIN_PASSWORD_LENGTH:
        raise ValidationFailedError(f"Password must be at least {MIN_PASSWORD_LENGTH} characters.")
    if len(password) > MAX_PASSWORD_LENGTH:
        raise ValidationFailedError(f"Password must be at most {MAX_PASSWORD_LENGTH} characters.")
