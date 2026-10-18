"""Admin user management and first-admin provisioning."""

import logging
from uuid import UUID

from taskboard.domain.entities import Page, User
from taskboard.domain.enums import Role
from taskboard.domain.errors import NotFoundError, ValidationFailedError
from taskboard.repositories.interfaces import SessionRepository, UnitOfWork, UserRepository
from taskboard.services.access import AccessPolicy
from taskboard.services.auth import normalize_email
from taskboard.services.caching import CacheAside
from taskboard.services.security import PasswordHasher, check_password_policy

logger = logging.getLogger("taskboard.admin")


class UserAdminService:
    def __init__(
        self,
        *,
        users: UserRepository,
        sessions: SessionRepository,
        access: AccessPolicy,
        uow: UnitOfWork,
        cache: CacheAside,
    ) -> None:
        self._users = users
        self._sessions = sessions
        self._access = access
        self._uow = uow
        self._cache = cache

    def list_users(self, actor: User, page: int, page_size: int) -> Page[User]:
        self._access.require_admin(actor)
        return self._users.list(page, page_size)

    def update_user(
        self, actor: User, user_id: UUID, *, role: Role | None, is_active: bool | None
    ) -> User:
        self._access.require_admin(actor)
        if user_id == actor.id and (role is Role.MEMBER or is_active is False):
            raise ValidationFailedError("Admins cannot demote or deactivate themselves.")
        updated = self._users.update(user_id, role=role, is_active=is_active)
        if updated is None:
            raise NotFoundError("User")
        if is_active is False:
            self._sessions.delete_for_user(user_id)
        self._uow.commit()
        self._cache.forget_user(user_id)
        logger.info(
            "admin updated user",
            extra={
                "actor_id": str(actor.id),
                "user_id": str(user_id),
                "role": role.value if role else None,
                "is_active": is_active,
            },
        )
        return updated

    def cache_stats(self, actor: User) -> dict[str, object]:
        self._access.require_admin(actor)
        return {"backend": self._cache.backend, "families": self._cache.stats()}


class AdminProvisioner:
    """Creates or promotes the first admin from operator-supplied credentials."""

    def __init__(
        self, users: UserRepository, hasher: PasswordHasher, uow: UnitOfWork, cache: CacheAside
    ) -> None:
        self._users = users
        self._hasher = hasher
        self._uow = uow
        self._cache = cache

    def ensure_admin(self, email: str, password: str, display_name: str = "Administrator") -> User:
        email = normalize_email(email)
        if "@" not in email:
            raise ValidationFailedError("ADMIN_EMAIL must be an email address.")
        check_password_policy(password)
        existing = self._users.get_by_email(email)
        if existing is None:
            user = self._users.add(email, display_name, self._hasher.hash(password), Role.ADMIN)
        else:
            self._users.set_password_hash(existing.id, self._hasher.hash(password))
            promoted = self._users.update(existing.id, role=Role.ADMIN, is_active=True)
            if promoted is None:
                raise NotFoundError("User")
            user = promoted
        self._uow.commit()
        self._cache.forget_user(user.id)
        return user
