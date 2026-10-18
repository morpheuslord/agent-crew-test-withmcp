"""Typed domain errors. The HTTP layer maps each one to a status code in one place."""


class DomainError(Exception):
    """Base class. ``code`` is a stable machine-readable identifier."""

    code = "error"

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class ValidationFailedError(DomainError):
    code = "validation_failed"


class AuthenticationRequiredError(DomainError):
    code = "authentication_required"

    def __init__(self, message: str = "Authentication required.") -> None:
        super().__init__(message)


class InvalidCredentialsError(DomainError):
    code = "invalid_credentials"

    def __init__(self, message: str = "Invalid email or password.") -> None:
        super().__init__(message)


class PermissionDeniedError(DomainError):
    code = "permission_denied"

    def __init__(self, message: str = "You are not allowed to do that.") -> None:
        super().__init__(message)


class NotFoundError(DomainError):
    code = "not_found"

    def __init__(self, what: str = "Resource") -> None:
        super().__init__(f"{what} not found.")


class ConflictError(DomainError):
    code = "conflict"


class ProjectArchivedError(DomainError):
    code = "project_archived"

    def __init__(self) -> None:
        super().__init__("The project is archived and read-only.")


class PayloadTooLargeError(DomainError):
    code = "payload_too_large"


class RateLimitedError(DomainError):
    code = "rate_limited"

    def __init__(self) -> None:
        super().__init__("Too many attempts. Try again later.")
