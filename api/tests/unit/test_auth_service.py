"""AuthService and admin services, against fakes."""

from urllib.parse import parse_qs, urlsplit
from uuid import UUID

import pytest

from taskboard.domain.enums import Role
from taskboard.domain.errors import (
    AuthenticationRequiredError,
    ConflictError,
    InvalidCredentialsError,
    NotFoundError,
    PermissionDeniedError,
    RateLimitedError,
    ValidationFailedError,
)
from taskboard.services.security import hash_token
from tests.unit.conftest import World

PASSWORD = "correct-horse-battery"


def _register(world: World, email: str = "ada@example.test") -> None:
    world.auth.register(email, "Ada", PASSWORD, "10.0.0.1")


def test_register_normalises_email_and_creates_member(world: World) -> None:
    user = world.auth.register("  Ada@Example.TEST ", " Ada ", PASSWORD, "10.0.0.1")
    assert user.email == "ada@example.test"
    assert user.display_name == "Ada"
    assert user.role is Role.MEMBER
    assert world.store.hashes[user.id] != PASSWORD


def test_register_rejects_duplicates_and_short_passwords(world: World) -> None:
    _register(world)
    with pytest.raises(ConflictError):
        _register(world)
    with pytest.raises(ValidationFailedError):
        world.auth.register("b@example.test", "B", "short", "10.0.0.1")
    with pytest.raises(ValidationFailedError):
        world.auth.register("c@example.test", "C", "x" * 129, "10.0.0.1")


def test_register_is_rate_limited_per_ip(world: World) -> None:
    for i in range(5):
        world.auth.register(f"u{i}@example.test", "U", PASSWORD, "10.0.0.9")
    with pytest.raises(RateLimitedError):
        world.auth.register("u9@example.test", "U", PASSWORD, "10.0.0.9")


def test_login_issues_fresh_session_tokens(world: World) -> None:
    _register(world)
    first = world.auth.login("ADA@example.test", PASSWORD, "10.0.0.1")
    second = world.auth.login("ada@example.test", PASSWORD, "10.0.0.1")
    assert first.token != second.token
    assert hash_token(first.token) in world.store.sessions
    assert first.token not in world.store.sessions
    assert world.auth.authenticate(first.token).email == "ada@example.test"


def test_login_failures_look_the_same(world: World) -> None:
    _register(world)
    with pytest.raises(InvalidCredentialsError) as wrong:
        world.auth.login("ada@example.test", "wrong-password-123", "10.0.0.1")
    with pytest.raises(InvalidCredentialsError) as unknown:
        world.auth.login("nobody@example.test", "wrong-password-123", "10.0.0.1")
    assert wrong.value.message == unknown.value.message
    assert world.hasher.burned == 1


def test_login_locks_after_repeated_failures(world: World) -> None:
    _register(world)
    for _ in range(3):
        with pytest.raises(InvalidCredentialsError):
            world.auth.login("ada@example.test", "wrong-password-123", "10.0.0.1")
    with pytest.raises(RateLimitedError):
        world.auth.login("ada@example.test", PASSWORD, "10.0.0.1")


def test_login_is_limited_per_ip(world: World) -> None:
    _register(world)
    for _ in range(10):
        world.auth.login("ada@example.test", PASSWORD, "10.0.0.2")
    with pytest.raises(RateLimitedError):
        world.auth.login("ada@example.test", PASSWORD, "10.0.0.2")


def test_deactivated_user_cannot_log_in_and_loses_sessions(world: World) -> None:
    admin = world.user("root", Role.ADMIN)
    _register(world)
    session = world.auth.login("ada@example.test", PASSWORD, "10.0.0.1")
    world.admin.update_user(admin, session.user.id, role=None, is_active=False)
    with pytest.raises(AuthenticationRequiredError):
        world.auth.authenticate(session.token)
    with pytest.raises(InvalidCredentialsError):
        world.auth.login("ada@example.test", PASSWORD, "10.0.0.1")


def test_sessions_expire_and_logout_ends_them(world: World) -> None:
    _register(world)
    session = world.auth.login("ada@example.test", PASSWORD, "10.0.0.1")
    world.auth.logout(session.token)
    with pytest.raises(AuthenticationRequiredError):
        world.auth.authenticate(session.token)
    other = world.auth.login("ada@example.test", PASSWORD, "10.0.0.1")
    world.clock.advance(3601)
    with pytest.raises(AuthenticationRequiredError):
        world.auth.authenticate(other.token)


def test_change_password_revokes_other_sessions(world: World) -> None:
    _register(world)
    old = world.auth.login("ada@example.test", PASSWORD, "10.0.0.1")
    with pytest.raises(ValidationFailedError):
        world.auth.change_password(old.user, "not-the-password", "new-password-456")
    fresh = world.auth.change_password(old.user, PASSWORD, "new-password-456")
    with pytest.raises(AuthenticationRequiredError):
        world.auth.authenticate(old.token)
    assert world.auth.authenticate(fresh.token).id == old.user.id
    world.auth.login("ada@example.test", "new-password-456", "10.0.0.1")


def _reset_token(world: World) -> str:
    _, _, body = world.mailer.sent[-1]
    link = next(line for line in body.splitlines() if line.startswith("https://"))
    assert link.startswith("https://taskboard.example.test/reset-password?")
    return parse_qs(urlsplit(link).query)["token"][0]


def test_forgot_password_reset_flow_is_single_use(world: World) -> None:
    _register(world)
    session = world.auth.login("ada@example.test", PASSWORD, "10.0.0.1")
    world.auth.forgot_password("ada@example.test", "10.0.0.1")
    token = _reset_token(world)
    world.auth.reset_password(token, "brand-new-password")
    with pytest.raises(AuthenticationRequiredError):
        world.auth.authenticate(session.token)
    with pytest.raises(ValidationFailedError):
        world.auth.reset_password(token, "another-password-1")
    world.auth.login("ada@example.test", "brand-new-password", "10.0.0.1")


def test_reset_tokens_expire_and_are_replaced(world: World) -> None:
    _register(world)
    world.auth.forgot_password("ada@example.test", "10.0.0.1")
    first = _reset_token(world)
    world.auth.forgot_password("ada@example.test", "10.0.0.1")
    second = _reset_token(world)
    with pytest.raises(ValidationFailedError):
        world.auth.reset_password(first, "brand-new-password")
    world.clock.advance(1801)
    with pytest.raises(ValidationFailedError):
        world.auth.reset_password(second, "brand-new-password")


def test_forgot_password_reveals_nothing_for_unknown_email(world: World) -> None:
    world.auth.forgot_password("ghost@example.test", "10.0.0.1")
    assert world.mailer.sent == []


def test_forgot_password_is_rate_limited(world: World) -> None:
    for _ in range(3):
        world.auth.forgot_password("ghost@example.test", "10.0.0.3")
    with pytest.raises(RateLimitedError):
        world.auth.forgot_password("ghost@example.test", "10.0.0.3")


def test_admin_service_requires_admin_and_protects_self(world: World) -> None:
    admin = world.user("root", Role.ADMIN)
    member = world.user("mia")
    with pytest.raises(PermissionDeniedError):
        world.admin.list_users(member, 1, 50)
    with pytest.raises(PermissionDeniedError):
        world.admin.update_user(member, admin.id, role=Role.MEMBER, is_active=None)
    with pytest.raises(ValidationFailedError):
        world.admin.update_user(admin, admin.id, role=Role.MEMBER, is_active=None)
    with pytest.raises(NotFoundError):
        world.admin.update_user(admin, UUID(int=1), role=Role.ADMIN, is_active=None)
    promoted = world.admin.update_user(admin, member.id, role=Role.ADMIN, is_active=None)
    assert promoted.role is Role.ADMIN
    assert world.admin.list_users(admin, 1, 50).total == 2


def test_provisioner_creates_then_promotes(world: World) -> None:
    created = world.provisioner.ensure_admin("Boss@example.test", "admin-password-1")
    assert created.role is Role.ADMIN
    member = world.user("mia")
    promoted = world.provisioner.ensure_admin(member.email, "admin-password-2")
    assert promoted.role is Role.ADMIN
    with pytest.raises(ValidationFailedError):
        world.provisioner.ensure_admin("not-an-email", "admin-password-3")
    with pytest.raises(ValidationFailedError):
        world.provisioner.ensure_admin("x@example.test", "short")
