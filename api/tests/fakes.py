"""In-memory fakes of the repository and infrastructure interfaces, for service unit tests."""

import uuid
from collections.abc import Collection, Iterator, Sequence
from dataclasses import dataclass, field, replace
from datetime import UTC, datetime, timedelta
from typing import IO
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
    StatusChangedEvent,
    Task,
    TaskChanges,
    TaskFilter,
    Team,
    TeamMember,
    User,
    UserCredentials,
)
from taskboard.domain.enums import Role
from taskboard.domain.errors import NotFoundError
from taskboard.infra.storage.base import BlobNotFoundError


class FakeClock:
    def __init__(self) -> None:
        self.current = datetime(2026, 10, 18, 9, 0, tzinfo=UTC)

    def now(self) -> datetime:
        return self.current

    def advance(self, seconds: int) -> None:
        self.current += timedelta(seconds=seconds)


class FakeHasher:
    """Reversible stand-in; the real Argon2 hasher has its own tests."""

    def __init__(self) -> None:
        self.burned = 0

    def hash(self, password: str) -> str:
        return f"hashed:{password}"

    def verify(self, password_hash: str, password: str) -> bool:
        return password_hash == f"hashed:{password}"

    def burn(self, password: str) -> None:
        self.burned += 1


class FakeUow:
    def __init__(self) -> None:
        self.commits = 0
        self.rollbacks = 0

    def commit(self) -> None:
        self.commits += 1

    def rollback(self) -> None:
        self.rollbacks += 1


@dataclass
class Store:
    """Shared state, so repositories can see each other's rows like a database would."""

    users: dict[UUID, User] = field(default_factory=dict)
    hashes: dict[UUID, str] = field(default_factory=dict)
    sessions: dict[str, tuple[UUID, datetime]] = field(default_factory=dict)
    resets: dict[str, tuple[UUID, datetime, bool]] = field(default_factory=dict)
    outbox: list[OutboxMessage] = field(default_factory=list)
    teams: dict[UUID, Team] = field(default_factory=dict)
    members: dict[tuple[UUID, UUID], datetime] = field(default_factory=dict)
    projects: dict[UUID, Project] = field(default_factory=dict)
    tasks: dict[UUID, Task] = field(default_factory=dict)
    comments: dict[UUID, Comment] = field(default_factory=dict)
    attachments: dict[UUID, Attachment] = field(default_factory=dict)
    activity: list[ActivityEvent] = field(default_factory=list)


NOW = datetime(2026, 10, 18, 9, 0, tzinfo=UTC)


class FakeUsers:
    def __init__(self, store: Store) -> None:
        self.s = store

    def add(self, email: str, display_name: str, password_hash: str, role: Role) -> User:
        user = User(uuid.uuid4(), email, display_name, role, True, NOW)
        self.s.users[user.id] = user
        self.s.hashes[user.id] = password_hash
        return user

    def get(self, user_id: UUID) -> User | None:
        return self.s.users.get(user_id)

    def get_by_email(self, email: str) -> User | None:
        return next((u for u in self.s.users.values() if u.email == email), None)

    def get_credentials(self, email: str) -> UserCredentials | None:
        user = self.get_by_email(email)
        return UserCredentials(user, self.s.hashes[user.id]) if user else None

    def get_password_hash(self, user_id: UUID) -> str | None:
        return self.s.hashes.get(user_id)

    def set_password_hash(self, user_id: UUID, password_hash: str) -> None:
        self.s.hashes[user_id] = password_hash

    def update(
        self, user_id: UUID, *, role: Role | None = None, is_active: bool | None = None
    ) -> User | None:
        user = self.s.users.get(user_id)
        if user is None:
            return None
        if role is not None:
            user = replace(user, role=role)
        if is_active is not None:
            user = replace(user, is_active=is_active)
        self.s.users[user_id] = user
        return user

    def list(self, page: int, page_size: int) -> Page[User]:
        items = list(self.s.users.values())
        start = (page - 1) * page_size
        return Page(tuple(items[start : start + page_size]), len(items), page, page_size)


class FakeSessions:
    def __init__(self, store: Store) -> None:
        self.s = store

    def add(self, user_id: UUID, token_hash: str, expires_at: datetime) -> None:
        self.s.sessions[token_hash] = (user_id, expires_at)

    def find_user_id(self, token_hash: str, now: datetime) -> UUID | None:
        entry = self.s.sessions.get(token_hash)
        if entry is None or entry[1] <= now:
            return None
        return entry[0]

    def delete(self, token_hash: str) -> None:
        self.s.sessions.pop(token_hash, None)

    def delete_for_user(self, user_id: UUID) -> None:
        for key in [k for k, v in self.s.sessions.items() if v[0] == user_id]:
            del self.s.sessions[key]

    def delete_expired_for_user(self, user_id: UUID, now: datetime) -> None:
        for key in [k for k, v in self.s.sessions.items() if v[0] == user_id and v[1] <= now]:
            del self.s.sessions[key]


class FakeResetTokens:
    def __init__(self, store: Store) -> None:
        self.s = store

    def add(self, user_id: UUID, token_hash: str, expires_at: datetime) -> None:
        self.s.resets[token_hash] = (user_id, expires_at, False)

    def consume(self, token_hash: str, now: datetime) -> UUID | None:
        entry = self.s.resets.get(token_hash)
        if entry is None or entry[2] or entry[1] <= now:
            return None
        self.s.resets[token_hash] = (entry[0], entry[1], True)
        return entry[0]

    def invalidate_for_user(self, user_id: UUID, now: datetime) -> None:
        for key, (uid, exp, _) in list(self.s.resets.items()):
            if uid == user_id:
                self.s.resets[key] = (uid, exp, True)


class FakeOutbox:
    def __init__(self, store: Store) -> None:
        self.s = store

    def add(self, to_email: str, subject: str, body: str) -> OutboxMessage:
        message = OutboxMessage(uuid.uuid4(), to_email, subject, body, NOW)
        self.s.outbox.append(message)
        return message

    def list_for(self, to_email: str) -> Sequence[OutboxMessage]:
        return [m for m in self.s.outbox if m.to_email == to_email]


class FakeTeams:
    def __init__(self, store: Store) -> None:
        self.s = store

    def add(self, name: str, owner_id: UUID) -> Team:
        team = Team(uuid.uuid4(), name, owner_id, NOW)
        self.s.teams[team.id] = team
        self.s.members[(team.id, owner_id)] = NOW
        return team

    def get(self, team_id: UUID) -> Team | None:
        return self.s.teams.get(team_id)

    def list_for_user(self, user_id: UUID) -> Sequence[Team]:
        return [t for t in self.s.teams.values() if (t.id, user_id) in self.s.members]

    def team_ids_for_user(self, user_id: UUID) -> set[UUID]:
        return {tid for (tid, uid) in self.s.members if uid == user_id}

    def is_member(self, team_id: UUID, user_id: UUID) -> bool:
        return (team_id, user_id) in self.s.members

    def add_member(self, team_id: UUID, user_id: UUID) -> None:
        self.s.members[(team_id, user_id)] = NOW

    def remove_member(self, team_id: UUID, user_id: UUID) -> bool:
        return self.s.members.pop((team_id, user_id), None) is not None

    def list_members(self, team_id: UUID) -> Sequence[TeamMember]:
        return [
            TeamMember(uid, self.s.users[uid].email, self.s.users[uid].display_name, added)
            for (tid, uid), added in self.s.members.items()
            if tid == team_id
        ]

    def member_ids(self, team_id: UUID) -> set[UUID]:
        return {uid for (tid, uid) in self.s.members if tid == team_id}


class FakeProjects:
    def __init__(self, store: Store) -> None:
        self.s = store

    def add(self, team_id: UUID, name: str, webhook_url: str | None) -> Project:
        project = Project(uuid.uuid4(), team_id, name, webhook_url, None, NOW, NOW)
        self.s.projects[project.id] = project
        return project

    def get(self, project_id: UUID) -> Project | None:
        return self.s.projects.get(project_id)

    def list_for_team(self, team_id: UUID) -> Sequence[Project]:
        return [p for p in self.s.projects.values() if p.team_id == team_id]

    def list_for_teams(self, team_ids: Collection[UUID]) -> Sequence[Project]:
        return [p for p in self.s.projects.values() if p.team_id in team_ids]

    def update(
        self, project_id: UUID, *, name: str | None, webhook_url: str | None, clear_webhook: bool
    ) -> Project:
        project = self.s.projects[project_id]
        if name is not None:
            project = replace(project, name=name)
        if clear_webhook:
            project = replace(project, webhook_url=None)
        elif webhook_url is not None:
            project = replace(project, webhook_url=webhook_url)
        self.s.projects[project_id] = project
        return project

    def archive(self, project_id: UUID, now: datetime) -> Project:
        project = replace(self.s.projects[project_id], archived_at=now)
        self.s.projects[project_id] = project
        return project


class FakeTasks:
    def __init__(self, store: Store) -> None:
        self.s = store

    def add(self, task: NewTask) -> Task:
        created = Task(
            uuid.uuid4(),
            task.project_id,
            task.title,
            task.description,
            task.status,
            task.priority,
            task.assignee_id,
            task.due_date,
            task.labels,
            task.created_by,
            NOW,
            NOW,
        )
        self.s.tasks[created.id] = created
        return created

    def get(self, task_id: UUID) -> Task | None:
        return self.s.tasks.get(task_id)

    def update(self, task_id: UUID, changes: TaskChanges) -> Task:
        task = self.s.tasks.get(task_id)
        if task is None:
            raise NotFoundError("Task")
        values = {
            name: getattr(changes, name)
            for name in ("title", "description", "status", "priority", "labels")
            if getattr(changes, name) is not None
        }
        for name in ("assignee_id", "due_date"):
            if name in changes.clear:
                values[name] = None
            elif getattr(changes, name) is not None:
                values[name] = getattr(changes, name)
        task = replace(task, **values)
        self.s.tasks[task_id] = task
        return task

    def delete(self, task_id: UUID) -> None:
        self.s.tasks.pop(task_id, None)

    def search(
        self,
        flt: TaskFilter,
        *,
        team_ids: Collection[UUID] | None,
        project_id: UUID | None = None,
    ) -> Page[Task]:
        items = [
            t
            for t in self.s.tasks.values()
            if (team_ids is None or self.s.projects[t.project_id].team_id in team_ids)
            and (project_id is None or t.project_id == project_id)
            and (flt.status is None or t.status is flt.status)
            and (flt.text is None or flt.text.lower() in (t.title + t.description).lower())
        ]
        return Page(tuple(items), len(items), flt.page, flt.page_size)

    def list_for_project(self, project_id: UUID) -> Sequence[Task]:
        return [t for t in self.s.tasks.values() if t.project_id == project_id]


class FakeComments:
    def __init__(self, store: Store) -> None:
        self.s = store

    def add(self, task_id: UUID, author_id: UUID, body: str) -> Comment:
        name = self.s.users[author_id].display_name
        comment = Comment(uuid.uuid4(), task_id, author_id, name, body, NOW, NOW)
        self.s.comments[comment.id] = comment
        return comment

    def get(self, comment_id: UUID) -> Comment | None:
        return self.s.comments.get(comment_id)

    def list_for_task(self, task_id: UUID) -> Sequence[Comment]:
        return [c for c in self.s.comments.values() if c.task_id == task_id]

    def update(self, comment_id: UUID, body: str) -> Comment:
        comment = replace(self.s.comments[comment_id], body=body)
        self.s.comments[comment_id] = comment
        return comment

    def delete(self, comment_id: UUID) -> None:
        self.s.comments.pop(comment_id, None)


class FakeAttachments:
    def __init__(self, store: Store) -> None:
        self.s = store

    def add(
        self,
        *,
        task_id: UUID,
        uploader_id: UUID,
        filename: str,
        content_type: str,
        size_bytes: int,
        storage_key: str,
    ) -> Attachment:
        attachment = Attachment(
            uuid.uuid4(), task_id, uploader_id, filename, content_type, size_bytes, storage_key, NOW
        )
        self.s.attachments[attachment.id] = attachment
        return attachment

    def get(self, attachment_id: UUID) -> Attachment | None:
        return self.s.attachments.get(attachment_id)

    def list_for_task(self, task_id: UUID) -> Sequence[Attachment]:
        return [a for a in self.s.attachments.values() if a.task_id == task_id]


class FakeActivity:
    def __init__(self, store: Store) -> None:
        self.s = store

    def add(self, event: NewActivity) -> None:
        name = self.s.users[event.actor_id].display_name
        self.s.activity.append(
            ActivityEvent(
                uuid.uuid4(),
                event.team_id,
                event.project_id,
                event.task_id,
                event.actor_id,
                name,
                event.event_type,
                event.details,
                NOW,
            )
        )

    def list_for_project(
        self, project_id: UUID, team_id: UUID, page: int, page_size: int
    ) -> Page[ActivityEvent]:
        items = [
            e
            for e in self.s.activity
            if e.project_id == project_id or (e.team_id == team_id and e.project_id is None)
        ]
        return Page(tuple(items), len(items), page, page_size)

    def list_all(self, page: int, page_size: int) -> Page[ActivityEvent]:
        return Page(tuple(self.s.activity), len(self.s.activity), page, page_size)


class FakeStorage:
    def __init__(self) -> None:
        self.blobs: dict[str, bytes] = {}

    def save(self, key: str, data: IO[bytes], size: int) -> None:
        self.blobs[key] = data.read()

    def open(self, key: str) -> Iterator[bytes]:
        if key not in self.blobs:
            raise BlobNotFoundError(key)
        return iter([self.blobs[key]])

    def delete(self, key: str) -> None:
        self.blobs.pop(key, None)

    def check(self) -> None:
        return None


class RecordingNotifier:
    def __init__(self) -> None:
        self.sent: list[tuple[str, StatusChangedEvent]] = []

    def notify(self, url: str, event: StatusChangedEvent) -> None:
        self.sent.append((url, event))


class FakeMailer:
    def __init__(self) -> None:
        self.sent: list[tuple[str, str, str]] = []

    def send(self, to_email: str, subject: str, body: str) -> None:
        self.sent.append((to_email, subject, body))
