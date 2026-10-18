"""Repository interfaces. Services depend only on these Protocols."""

from collections.abc import Collection, Sequence
from datetime import datetime
from typing import Protocol
from uuid import UUID

from taskboard.domain.entities import (
    ActivityEvent,
    Attachment,
    Comment,
    NewActivity,
    NewTask,
    OutboxMessage,
    Page,
    Project,
    SessionPrincipal,
    Task,
    TaskChanges,
    TaskFilter,
    Team,
    TeamMember,
    User,
    UserCredentials,
)
from taskboard.domain.enums import Role


class UnitOfWork(Protocol):
    def commit(self) -> None: ...

    def rollback(self) -> None: ...


class UserRepository(Protocol):
    def add(self, email: str, display_name: str, password_hash: str, role: Role) -> User: ...

    def get(self, user_id: UUID) -> User | None: ...

    def get_by_email(self, email: str) -> User | None: ...

    def get_credentials(self, email: str) -> UserCredentials | None: ...

    def get_password_hash(self, user_id: UUID) -> str | None: ...

    def set_password_hash(self, user_id: UUID, password_hash: str) -> None: ...

    def update(
        self, user_id: UUID, *, role: Role | None = None, is_active: bool | None = None
    ) -> User | None: ...

    def list(self, page: int, page_size: int) -> Page[User]: ...


class SessionRepository(Protocol):
    def add(self, user_id: UUID, token_hash: str, expires_at: datetime) -> None: ...

    def find_principal(self, token_hash: str, now: datetime) -> SessionPrincipal | None:
        """Return the owner of an unexpired session with their current role and status."""
        ...

    def delete(self, token_hash: str) -> None: ...

    def delete_for_user(self, user_id: UUID) -> None: ...

    def delete_expired_for_user(self, user_id: UUID, now: datetime) -> None: ...


class ResetTokenRepository(Protocol):
    def add(self, user_id: UUID, token_hash: str, expires_at: datetime) -> None: ...

    def consume(self, token_hash: str, now: datetime) -> UUID | None:
        """Atomically mark an unused, unexpired token as used and return its user id."""
        ...

    def invalidate_for_user(self, user_id: UUID, now: datetime) -> None: ...


class OutboxRepository(Protocol):
    def add(self, to_email: str, subject: str, body: str) -> OutboxMessage: ...

    def list_for(self, to_email: str) -> Sequence[OutboxMessage]: ...


class TeamRepository(Protocol):
    def add(self, name: str, owner_id: UUID) -> Team:
        """Create a team and make its owner the first member."""
        ...

    def get(self, team_id: UUID) -> Team | None: ...

    def list_for_user(self, user_id: UUID) -> Sequence[Team]: ...

    def team_ids_for_user(self, user_id: UUID) -> set[UUID]: ...

    def is_member(self, team_id: UUID, user_id: UUID) -> bool: ...

    def add_member(self, team_id: UUID, user_id: UUID) -> None: ...

    def remove_member(self, team_id: UUID, user_id: UUID) -> bool: ...

    def list_members(self, team_id: UUID) -> Sequence[TeamMember]: ...

    def member_ids(self, team_id: UUID) -> set[UUID]: ...


class ProjectRepository(Protocol):
    def add(self, team_id: UUID, name: str, webhook_url: str | None) -> Project: ...

    def get(self, project_id: UUID) -> Project | None: ...

    def list_for_team(self, team_id: UUID) -> Sequence[Project]: ...

    def list_for_teams(self, team_ids: Collection[UUID]) -> Sequence[Project]: ...

    def update(
        self, project_id: UUID, *, name: str | None, webhook_url: str | None, clear_webhook: bool
    ) -> Project: ...

    def archive(self, project_id: UUID, now: datetime) -> Project: ...


class TaskRepository(Protocol):
    def add(self, task: NewTask) -> Task: ...

    def get(self, task_id: UUID) -> Task | None: ...

    def update(self, task_id: UUID, changes: TaskChanges) -> Task: ...

    def delete(self, task_id: UUID) -> None: ...

    def search(
        self,
        flt: TaskFilter,
        *,
        team_ids: Collection[UUID] | None,
        project_id: UUID | None = None,
    ) -> Page[Task]:
        """Search tasks. ``team_ids=None`` means no team restriction (admins only)."""
        ...

    def list_for_project(self, project_id: UUID) -> Sequence[Task]: ...


class CommentRepository(Protocol):
    def add(self, task_id: UUID, author_id: UUID, body: str) -> Comment: ...

    def get(self, comment_id: UUID) -> Comment | None: ...

    def list_for_task(self, task_id: UUID) -> Sequence[Comment]: ...

    def update(self, comment_id: UUID, body: str) -> Comment: ...

    def delete(self, comment_id: UUID) -> None: ...


class AttachmentRepository(Protocol):
    def add(
        self,
        *,
        task_id: UUID,
        uploader_id: UUID,
        filename: str,
        content_type: str,
        size_bytes: int,
        storage_key: str,
    ) -> Attachment: ...

    def get(self, attachment_id: UUID) -> Attachment | None: ...

    def list_for_task(self, task_id: UUID) -> Sequence[Attachment]: ...


class ActivityRepository(Protocol):
    def add(self, event: NewActivity) -> None: ...

    def list_for_project(
        self, project_id: UUID, team_id: UUID, page: int, page_size: int
    ) -> Page[ActivityEvent]: ...

    def list_all(self, page: int, page_size: int) -> Page[ActivityEvent]: ...
