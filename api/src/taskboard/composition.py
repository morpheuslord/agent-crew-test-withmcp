"""Composition root: the only place that chooses concrete implementations."""

import logging
from dataclasses import dataclass, field
from functools import cached_property

import boto3
import redis
from sqlalchemy import Engine, create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from taskboard.config import Settings, StorageBackend
from taskboard.infra.mailer import LogOutboxMailer
from taskboard.infra.rate_limit import InMemoryRateLimiter, RateLimiter, RedisRateLimiter
from taskboard.infra.storage.base import AttachmentStorage
from taskboard.infra.storage.local import LocalFileStorage
from taskboard.infra.storage.s3 import S3Storage
from taskboard.infra.webhooks.notifier import HttpWebhookNotifier, WebhookNotifier
from taskboard.infra.webhooks.url_policy import WebhookUrlPolicy
from taskboard.repositories.sqlalchemy.accounts import (
    SqlOutboxRepository,
    SqlResetTokenRepository,
    SqlSessionRepository,
    SqlUserRepository,
)
from taskboard.repositories.sqlalchemy.content import (
    SqlActivityRepository,
    SqlAttachmentRepository,
    SqlCommentRepository,
    SqlUnitOfWork,
)
from taskboard.repositories.sqlalchemy.tasks import SqlTaskRepository
from taskboard.repositories.sqlalchemy.teams import SqlProjectRepository, SqlTeamRepository
from taskboard.services.access import AccessPolicy
from taskboard.services.activity import ActivityService
from taskboard.services.attachments import AttachmentService
from taskboard.services.auth import AuthPolicy, AuthService
from taskboard.services.comments import CommentService
from taskboard.services.export import CsvExporter
from taskboard.services.projects import ProjectService
from taskboard.services.security import Argon2PasswordHasher, Clock, PasswordHasher, SystemClock
from taskboard.services.tasks import TaskService
from taskboard.services.teams import TeamService
from taskboard.services.users import AdminProvisioner, UserAdminService

logger = logging.getLogger("taskboard.composition")


@dataclass
class Infrastructure:
    """Process-wide singletons: connection pools, clients and stateless helpers."""

    settings: Settings
    engine: Engine
    session_factory: sessionmaker[Session]
    storage: AttachmentStorage
    notifier: WebhookNotifier
    url_policy: WebhookUrlPolicy
    limiter: RateLimiter
    hasher: PasswordHasher
    clock: Clock
    redis_client: redis.Redis | None = None
    extras: dict[str, object] = field(default_factory=dict)

    def check_database(self) -> None:
        with self.engine.connect() as conn:
            conn.execute(text("SELECT 1"))

    def check_redis(self) -> bool:
        if self.redis_client is None:
            return False
        try:
            return bool(self.redis_client.ping())
        except redis.RedisError:
            return False

    def close(self) -> None:
        if isinstance(self.notifier, HttpWebhookNotifier):
            self.notifier.shutdown()
        if self.redis_client is not None:
            self.redis_client.close()
        self.engine.dispose()


def build_storage(settings: Settings) -> AttachmentStorage:
    if settings.storage_backend is StorageBackend.S3:
        client = boto3.client("s3", region_name=settings.aws_region)
        return S3Storage(client, settings.s3_bucket or "")
    return LocalFileStorage(settings.storage_local_path)


def build_redis(settings: Settings) -> redis.Redis | None:
    if settings.redis_url is None:
        return None
    return redis.Redis.from_url(
        settings.redis_url.get_secret_value(),
        socket_timeout=0.5,
        socket_connect_timeout=0.5,
        health_check_interval=30,
        decode_responses=True,
    )


def build_infrastructure(settings: Settings) -> Infrastructure:
    engine = create_engine(
        settings.database_url.get_secret_value(),
        pool_pre_ping=True,
        pool_size=settings.db_pool_size,
    )
    redis_client = build_redis(settings)
    fallback = InMemoryRateLimiter()
    limiter: RateLimiter = (
        RedisRateLimiter(redis_client, fallback) if redis_client is not None else fallback
    )
    url_policy = WebhookUrlPolicy(
        allow_http=settings.webhook_allow_http,
        allow_private=settings.webhook_allow_private_targets,
    )
    notifier = HttpWebhookNotifier(
        policy=url_policy,
        signing_secret=settings.webhook_signing_secret.get_secret_value().encode(),
        timeout_seconds=settings.webhook_timeout_seconds,
        max_attempts=settings.webhook_max_attempts,
    )
    return Infrastructure(
        settings=settings,
        engine=engine,
        session_factory=sessionmaker(engine, expire_on_commit=False),
        storage=build_storage(settings),
        notifier=notifier,
        url_policy=url_policy,
        limiter=limiter,
        hasher=Argon2PasswordHasher(),
        clock=SystemClock(),
        redis_client=redis_client,
    )


class RequestServices:
    """Builds repositories and services around one database session (one per request)."""

    def __init__(self, infra: Infrastructure, session: Session) -> None:
        self._infra = infra
        self._session = session
        self.uow = SqlUnitOfWork(session)
        self.users = SqlUserRepository(session)
        self.sessions = SqlSessionRepository(session)
        self.teams_repo = SqlTeamRepository(session)
        self.projects_repo = SqlProjectRepository(session)
        self.tasks_repo = SqlTaskRepository(session)

    @cached_property
    def access(self) -> AccessPolicy:
        return AccessPolicy(self.teams_repo, self.projects_repo, self.tasks_repo)

    @cached_property
    def activity(self) -> ActivityService:
        return ActivityService(SqlActivityRepository(self._session), self.access)

    @cached_property
    def auth(self) -> AuthService:
        s = self._infra.settings
        return AuthService(
            users=self.users,
            sessions=self.sessions,
            reset_tokens=SqlResetTokenRepository(self._session),
            mailer=LogOutboxMailer(SqlOutboxRepository(self._session)),
            hasher=self._infra.hasher,
            limiter=self._infra.limiter,
            clock=self._infra.clock,
            uow=self.uow,
            policy=AuthPolicy(
                session_ttl_seconds=s.session_ttl_seconds,
                reset_token_ttl_seconds=s.reset_token_ttl_seconds,
                public_base_url=str(s.public_base_url),
                login_max_failures=s.login_max_failures,
                login_max_attempts_per_ip=s.login_max_attempts_per_ip,
                forgot_max_per_ip=s.forgot_max_per_ip,
                register_max_per_ip=s.register_max_per_ip,
                rate_limit_window_seconds=s.rate_limit_window_seconds,
            ),
        )

    @cached_property
    def user_admin(self) -> UserAdminService:
        return UserAdminService(
            users=self.users, sessions=self.sessions, access=self.access, uow=self.uow
        )

    @cached_property
    def provisioner(self) -> AdminProvisioner:
        return AdminProvisioner(self.users, self._infra.hasher, self.uow)

    @cached_property
    def teams(self) -> TeamService:
        return TeamService(
            teams=self.teams_repo,
            projects=self.projects_repo,
            users=self.users,
            access=self.access,
            activity=self.activity,
            uow=self.uow,
        )

    @cached_property
    def projects(self) -> ProjectService:
        return ProjectService(
            projects=self.projects_repo,
            teams=self.teams_repo,
            access=self.access,
            url_policy=self._infra.url_policy,
            clock=self._infra.clock,
            uow=self.uow,
        )

    @cached_property
    def tasks(self) -> TaskService:
        return TaskService(
            tasks=self.tasks_repo,
            teams=self.teams_repo,
            attachments=SqlAttachmentRepository(self._session),
            storage=self._infra.storage,
            access=self.access,
            activity=self.activity,
            notifier=self._infra.notifier,
            clock=self._infra.clock,
            uow=self.uow,
        )

    @cached_property
    def comments(self) -> CommentService:
        return CommentService(
            comments=SqlCommentRepository(self._session),
            access=self.access,
            activity=self.activity,
            uow=self.uow,
        )

    @cached_property
    def attachments(self) -> AttachmentService:
        return AttachmentService(
            attachments=SqlAttachmentRepository(self._session),
            storage=self._infra.storage,
            access=self.access,
            activity=self.activity,
            uow=self.uow,
            max_bytes=self._infra.settings.max_upload_bytes,
        )

    @cached_property
    def exporter(self) -> CsvExporter:
        return CsvExporter(tasks=self.tasks_repo, teams=self.teams_repo, access=self.access)
