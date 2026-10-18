"""Immutable domain entities returned by repositories and services."""

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any
from uuid import UUID

from taskboard.domain.enums import (
    ActivityType,
    Role,
    SortField,
    SortOrder,
    TaskPriority,
    TaskStatus,
)


@dataclass(frozen=True, slots=True)
class User:
    id: UUID
    email: str
    display_name: str
    role: Role
    is_active: bool
    created_at: datetime

    @property
    def is_admin(self) -> bool:
        return self.role is Role.ADMIN


@dataclass(frozen=True, slots=True)
class UserCredentials:
    """A user together with their password hash. Never leaves the service layer."""

    user: User
    password_hash: str


@dataclass(frozen=True, slots=True)
class IssuedSession:
    """A freshly created session. ``token`` is the only copy of the raw secret."""

    token: str
    expires_at: datetime
    user: User


@dataclass(frozen=True, slots=True)
class Team:
    id: UUID
    name: str
    owner_id: UUID
    created_at: datetime


@dataclass(frozen=True, slots=True)
class TeamMember:
    user_id: UUID
    email: str
    display_name: str
    added_at: datetime


@dataclass(frozen=True, slots=True)
class Project:
    id: UUID
    team_id: UUID
    name: str
    webhook_url: str | None
    archived_at: datetime | None
    created_at: datetime
    updated_at: datetime

    @property
    def is_archived(self) -> bool:
        return self.archived_at is not None


@dataclass(frozen=True, slots=True)
class TeamDetail:
    team: Team
    members: tuple[TeamMember, ...]
    projects: tuple[Project, ...]


@dataclass(frozen=True, slots=True)
class Task:
    id: UUID
    project_id: UUID
    title: str
    description: str
    status: TaskStatus
    priority: TaskPriority
    assignee_id: UUID | None
    due_date: date | None
    labels: tuple[str, ...]
    created_by: UUID
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True, slots=True)
class TaskDraft:
    """Client-supplied fields for a new task."""

    title: str
    description: str = ""
    status: TaskStatus = TaskStatus.TODO
    priority: TaskPriority = TaskPriority.MEDIUM
    assignee_id: UUID | None = None
    due_date: date | None = None
    labels: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class NewTask:
    project_id: UUID
    title: str
    description: str
    status: TaskStatus
    priority: TaskPriority
    assignee_id: UUID | None
    due_date: date | None
    labels: tuple[str, ...]
    created_by: UUID


@dataclass(frozen=True, slots=True)
class TaskChanges:
    """Fields to change on a task. ``None`` means "leave unchanged" unless listed in ``clear``."""

    title: str | None = None
    description: str | None = None
    status: TaskStatus | None = None
    priority: TaskPriority | None = None
    assignee_id: UUID | None = None
    due_date: date | None = None
    labels: tuple[str, ...] | None = None
    clear: frozenset[str] = field(default_factory=frozenset)

    def changed_fields(self) -> list[str]:
        names = [
            "title",
            "description",
            "status",
            "priority",
            "assignee_id",
            "due_date",
            "labels",
        ]
        return [n for n in names if getattr(self, n) is not None or n in self.clear]


@dataclass(frozen=True, slots=True)
class TaskFilter:
    text: str | None = None
    status: TaskStatus | None = None
    assignee_id: UUID | None = None
    label: str | None = None
    due_before: date | None = None
    sort: SortField = SortField.CREATED_AT
    order: SortOrder = SortOrder.DESC
    page: int = 1
    page_size: int = 50


@dataclass(frozen=True, slots=True)
class Page[T]:
    items: tuple[T, ...]
    total: int
    page: int
    page_size: int


@dataclass(frozen=True, slots=True)
class Comment:
    id: UUID
    task_id: UUID
    author_id: UUID
    author_name: str
    body: str
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True, slots=True)
class Attachment:
    id: UUID
    task_id: UUID
    uploader_id: UUID
    filename: str
    content_type: str
    size_bytes: int
    storage_key: str
    created_at: datetime


@dataclass(frozen=True, slots=True)
class ActivityEvent:
    id: UUID
    team_id: UUID
    project_id: UUID | None
    task_id: UUID | None
    actor_id: UUID
    actor_name: str
    event_type: ActivityType
    details: dict[str, Any]
    created_at: datetime


@dataclass(frozen=True, slots=True)
class NewActivity:
    team_id: UUID
    project_id: UUID | None
    task_id: UUID | None
    actor_id: UUID
    event_type: ActivityType
    details: dict[str, Any]


@dataclass(frozen=True, slots=True)
class OutboxMessage:
    id: UUID
    to_email: str
    subject: str
    body: str
    created_at: datetime


@dataclass(frozen=True, slots=True)
class StatusChangedEvent:
    """Payload for the ``task.status_changed`` webhook."""

    task_id: UUID
    project_id: UUID
    old_status: TaskStatus
    new_status: TaskStatus
    actor_id: UUID
    timestamp: datetime

    def to_payload(self) -> dict[str, str]:
        return {
            "event": "task.status_changed",
            "task_id": str(self.task_id),
            "project_id": str(self.project_id),
            "old_status": self.old_status.value,
            "new_status": self.new_status.value,
            "actor_id": str(self.actor_id),
            "timestamp": self.timestamp.isoformat(),
        }
