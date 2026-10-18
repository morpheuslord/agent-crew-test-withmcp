"""Enumerations used across the domain."""

from enum import StrEnum


class Role(StrEnum):
    ADMIN = "admin"
    MEMBER = "member"


class TaskStatus(StrEnum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"


class TaskPriority(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class SortField(StrEnum):
    """Task fields a client may sort by. Mapped to columns in the repository, never to raw SQL."""

    TITLE = "title"
    STATUS = "status"
    PRIORITY = "priority"
    DUE_DATE = "due_date"
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"
    ASSIGNEE = "assignee"


class SortOrder(StrEnum):
    ASC = "asc"
    DESC = "desc"


class ActivityType(StrEnum):
    TASK_CREATED = "task_created"
    TASK_UPDATED = "task_updated"
    STATUS_CHANGED = "status_changed"
    COMMENT_ADDED = "comment_added"
    ATTACHMENT_ADDED = "attachment_added"
    MEMBER_ADDED = "member_added"
    MEMBER_REMOVED = "member_removed"
