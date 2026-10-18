"""Schemas for teams, projects, tasks, comments, attachments and activity."""

from datetime import date, datetime
from typing import Annotated, Any, Final, Self
from uuid import UUID

from pydantic import Field, StringConstraints, field_validator, model_validator

from taskboard.api.schemas.common import (
    Email,
    Name,
    PageMeta,
    PageParams,
    RequestModel,
    ResponseModel,
)
from taskboard.domain.entities import TaskChanges, TaskDraft, TaskFilter
from taskboard.domain.enums import ActivityType, SortField, SortOrder, TaskPriority, TaskStatus

_CLEARABLE: Final = frozenset({"assignee_id", "due_date"})

Title = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]
Markdown = Annotated[str, Field(max_length=20_000)]
Label = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=50)]
WebhookUrl = Annotated[str, Field(min_length=1, max_length=2048)]


def _dedupe(labels: list[str]) -> list[str]:
    seen: dict[str, None] = {}
    for label in labels:
        seen.setdefault(label, None)
    return list(seen)


class TeamCreate(RequestModel):
    name: Name


class TeamOut(ResponseModel):
    id: UUID
    name: str
    owner_id: UUID
    created_at: datetime


class MemberAdd(RequestModel):
    email: Email


class MemberOut(ResponseModel):
    user_id: UUID
    email: str
    display_name: str
    added_at: datetime


class ProjectCreate(RequestModel):
    name: Name
    webhook_url: WebhookUrl | None = None


class ProjectUpdate(RequestModel):
    name: Name | None = None
    webhook_url: WebhookUrl | None = None
    clear_webhook: bool = False


class ProjectOut(ResponseModel):
    id: UUID
    team_id: UUID
    name: str
    webhook_url: str | None
    archived_at: datetime | None
    is_archived: bool
    created_at: datetime
    updated_at: datetime


class TeamDetailOut(ResponseModel):
    team: TeamOut
    members: list[MemberOut]
    projects: list[ProjectOut]


class TaskCreate(RequestModel):
    title: Title
    description: Markdown = ""
    status: TaskStatus = TaskStatus.TODO
    priority: TaskPriority = TaskPriority.MEDIUM
    assignee_id: UUID | None = None
    due_date: date | None = None
    labels: list[Label] = Field(default_factory=list, max_length=20)

    @field_validator("labels")
    @classmethod
    def _dedupe_labels(cls, value: list[str]) -> list[str]:
        return _dedupe(value)

    def to_draft(self) -> TaskDraft:
        return TaskDraft(
            title=self.title,
            description=self.description,
            status=self.status,
            priority=self.priority,
            assignee_id=self.assignee_id,
            due_date=self.due_date,
            labels=tuple(self.labels),
        )


class TaskUpdate(RequestModel):
    """Only the fields present in the body change. ``null`` clears assignee or due date."""

    title: Title | None = None
    description: Markdown | None = None
    status: TaskStatus | None = None
    priority: TaskPriority | None = None
    assignee_id: UUID | None = None
    due_date: date | None = None
    labels: list[Label] | None = Field(default=None, max_length=20)

    @field_validator("labels")
    @classmethod
    def _dedupe_labels(cls, value: list[str] | None) -> list[str] | None:
        return _dedupe(value) if value is not None else None

    @model_validator(mode="after")
    def _only_clearable_nulls(self) -> Self:
        for name in self.model_fields_set - _CLEARABLE:
            if getattr(self, name) is None:
                raise ValueError(f"{name} cannot be null")
        return self

    def to_changes(self) -> TaskChanges:
        return TaskChanges(
            title=self.title,
            description=self.description,
            status=self.status,
            priority=self.priority,
            assignee_id=self.assignee_id,
            due_date=self.due_date,
            labels=tuple(self.labels) if self.labels is not None else None,
            clear=frozenset(
                name for name in _CLEARABLE & self.model_fields_set if getattr(self, name) is None
            ),
        )


class TaskOut(ResponseModel):
    id: UUID
    project_id: UUID
    title: str
    description: str
    status: TaskStatus
    priority: TaskPriority
    assignee_id: UUID | None
    due_date: date | None
    labels: list[str]
    created_by: UUID
    created_at: datetime
    updated_at: datetime


class TaskPage(PageMeta):
    items: list[TaskOut]


class TaskQuery(PageParams):
    q: str | None = Field(default=None, max_length=200)
    status: TaskStatus | None = None
    assignee_id: UUID | None = None
    label: str | None = Field(default=None, max_length=50)
    due_before: date | None = None
    sort: SortField = SortField.CREATED_AT
    order: SortOrder = SortOrder.DESC

    def to_filter(self) -> TaskFilter:
        return TaskFilter(
            text=self.q.strip() if self.q and self.q.strip() else None,
            status=self.status,
            assignee_id=self.assignee_id,
            label=self.label.strip() if self.label and self.label.strip() else None,
            due_before=self.due_before,
            sort=self.sort,
            order=self.order,
            page=self.page,
            page_size=self.page_size,
        )


class CommentCreate(RequestModel):
    body: Annotated[str, Field(min_length=1, max_length=10_000)]


class CommentOut(ResponseModel):
    id: UUID
    task_id: UUID
    author_id: UUID
    author_name: str
    body: str
    created_at: datetime
    updated_at: datetime


class AttachmentOut(ResponseModel):
    id: UUID
    task_id: UUID
    uploader_id: UUID
    filename: str
    content_type: str
    size_bytes: int
    created_at: datetime


class ActivityOut(ResponseModel):
    id: UUID
    team_id: UUID
    project_id: UUID | None
    task_id: UUID | None
    actor_id: UUID
    actor_name: str
    event_type: ActivityType
    details: dict[str, Any]
    created_at: datetime


class ActivityPage(PageMeta):
    items: list[ActivityOut]
