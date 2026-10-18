"""Row-to-entity mapping. Repositories never hand ORM objects to services."""

from taskboard.domain.entities import Attachment, Project, Task, Team, User
from taskboard.domain.enums import Role, TaskPriority, TaskStatus
from taskboard.models.tables import AttachmentRow, ProjectRow, TaskRow, TeamRow, UserRow


def to_user(row: UserRow) -> User:
    return User(
        id=row.id,
        email=row.email,
        display_name=row.display_name,
        role=Role(row.role),
        is_active=row.is_active,
        created_at=row.created_at,
    )


def to_team(row: TeamRow) -> Team:
    return Team(id=row.id, name=row.name, owner_id=row.owner_id, created_at=row.created_at)


def to_project(row: ProjectRow) -> Project:
    return Project(
        id=row.id,
        team_id=row.team_id,
        name=row.name,
        webhook_url=row.webhook_url,
        archived_at=row.archived_at,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def to_task(row: TaskRow) -> Task:
    return Task(
        id=row.id,
        project_id=row.project_id,
        title=row.title,
        description=row.description,
        status=TaskStatus(row.status),
        priority=TaskPriority(row.priority),
        assignee_id=row.assignee_id,
        due_date=row.due_date,
        labels=tuple(row.labels),
        created_by=row.created_by,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def to_attachment(row: AttachmentRow) -> Attachment:
    return Attachment(
        id=row.id,
        task_id=row.task_id,
        uploader_id=row.uploader_id,
        filename=row.filename,
        content_type=row.content_type,
        size_bytes=row.size_bytes,
        storage_key=row.storage_key,
        created_at=row.created_at,
    )
