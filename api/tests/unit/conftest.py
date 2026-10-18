"""Builds every service on top of in-memory fakes."""

from dataclasses import dataclass

import pytest

from taskboard.domain.entities import User
from taskboard.domain.enums import Role
from taskboard.infra.rate_limit import InMemoryRateLimiter
from taskboard.infra.webhooks.url_policy import WebhookUrlPolicy
from taskboard.services.access import AccessPolicy
from taskboard.services.activity import ActivityService
from taskboard.services.attachments import AttachmentService
from taskboard.services.auth import AuthPolicy, AuthService
from taskboard.services.comments import CommentService
from taskboard.services.export import CsvExporter
from taskboard.services.projects import ProjectService
from taskboard.services.tasks import TaskService
from taskboard.services.teams import TeamService
from taskboard.services.users import AdminProvisioner, UserAdminService
from tests.fakes import (
    FakeActivity,
    FakeAttachments,
    FakeClock,
    FakeComments,
    FakeHasher,
    FakeMailer,
    FakeProjects,
    FakeResetTokens,
    FakeSessions,
    FakeStorage,
    FakeTasks,
    FakeTeams,
    FakeUow,
    FakeUsers,
    RecordingNotifier,
    Store,
)

POLICY = AuthPolicy(
    session_ttl_seconds=3600,
    reset_token_ttl_seconds=1800,
    public_base_url="https://taskboard.example.test",
    login_max_failures=3,
    login_max_account_failures=6,
    login_max_attempts_per_ip=10,
    forgot_max_per_ip=3,
    register_max_per_ip=5,
    rate_limit_window_seconds=900,
)


def public_resolver(host: str, port: int) -> list[str]:
    return ["93.184.215.14"]


@dataclass
class World:
    store: Store
    clock: FakeClock
    uow: FakeUow
    mailer: FakeMailer
    notifier: RecordingNotifier
    storage: FakeStorage
    hasher: FakeHasher
    limiter: InMemoryRateLimiter
    users: FakeUsers
    auth: AuthService
    admin: UserAdminService
    provisioner: AdminProvisioner
    teams: TeamService
    projects: ProjectService
    tasks: TaskService
    comments: CommentService
    attachments: AttachmentService
    activity: ActivityService
    exporter: CsvExporter

    def user(self, name: str, role: Role = Role.MEMBER) -> User:
        return self.users.add(f"{name}@example.test", name.title(), "hashed:pw", role)


@pytest.fixture
def world() -> World:
    store = Store()
    clock = FakeClock()
    uow = FakeUow()
    mailer = FakeMailer()
    notifier = RecordingNotifier()
    storage = FakeStorage()
    hasher = FakeHasher()
    limiter = InMemoryRateLimiter()
    users = FakeUsers(store)
    sessions = FakeSessions(store)
    teams_repo = FakeTeams(store)
    projects_repo = FakeProjects(store)
    tasks_repo = FakeTasks(store)
    attachments_repo = FakeAttachments(store)
    access = AccessPolicy(teams_repo, projects_repo, tasks_repo)
    activity = ActivityService(FakeActivity(store), access)
    policy = WebhookUrlPolicy(allow_http=False, allow_private=False, resolver=public_resolver)
    return World(
        store=store,
        clock=clock,
        uow=uow,
        mailer=mailer,
        notifier=notifier,
        storage=storage,
        hasher=hasher,
        limiter=limiter,
        users=users,
        auth=AuthService(
            users=users,
            sessions=sessions,
            reset_tokens=FakeResetTokens(store),
            mailer=mailer,
            hasher=hasher,
            limiter=limiter,
            clock=clock,
            uow=uow,
            policy=POLICY,
        ),
        admin=UserAdminService(users=users, sessions=sessions, access=access, uow=uow),
        provisioner=AdminProvisioner(users, hasher, uow),
        teams=TeamService(
            teams=teams_repo,
            projects=projects_repo,
            users=users,
            access=access,
            activity=activity,
            uow=uow,
        ),
        projects=ProjectService(
            projects=projects_repo,
            teams=teams_repo,
            access=access,
            url_policy=policy,
            signing_keys=lambda project_id: f"key-{project_id}",
            clock=clock,
            uow=uow,
        ),
        tasks=TaskService(
            tasks=tasks_repo,
            teams=teams_repo,
            attachments=attachments_repo,
            storage=storage,
            access=access,
            activity=activity,
            notifier=notifier,
            clock=clock,
            uow=uow,
        ),
        comments=CommentService(
            comments=FakeComments(store), access=access, activity=activity, uow=uow
        ),
        attachments=AttachmentService(
            attachments=attachments_repo,
            storage=storage,
            access=access,
            activity=activity,
            uow=uow,
            max_bytes=1024,
        ),
        activity=activity,
        exporter=CsvExporter(tasks=tasks_repo, teams=teams_repo, access=access),
    )
