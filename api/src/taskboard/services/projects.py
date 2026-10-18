"""Projects: creation, renaming, webhook configuration and archiving."""

from collections.abc import Callable, Sequence
from dataclasses import replace
from uuid import UUID

from taskboard.domain.entities import Project, User
from taskboard.domain.errors import ProjectArchivedError
from taskboard.infra.webhooks.url_policy import WebhookUrlPolicy
from taskboard.repositories.interfaces import ProjectRepository, TeamRepository, UnitOfWork
from taskboard.services.access import AccessPolicy
from taskboard.services.caching import PROJECT_LIST_ADAPTER, CacheAside, CacheKeys
from taskboard.services.security import Clock


class ProjectService:
    def __init__(
        self,
        *,
        projects: ProjectRepository,
        teams: TeamRepository,
        access: AccessPolicy,
        url_policy: WebhookUrlPolicy,
        signing_keys: Callable[[UUID], str],
        clock: Clock,
        uow: UnitOfWork,
        cache: CacheAside,
    ) -> None:
        self._projects = projects
        self._teams = teams
        self._access = access
        self._url_policy = url_policy
        self._signing_keys = signing_keys
        self._clock = clock
        self._uow = uow
        self._cache = cache

    def redact(self, actor: User, projects: Sequence[Project]) -> list[Project]:
        """Show webhook URLs (which often embed secrets) and signing keys only to managers."""
        managers: dict[UUID, bool] = {}
        result = []
        for project in projects:
            if project.team_id not in managers:
                team = self._teams.get(project.team_id)
                managers[project.team_id] = actor.is_admin or (
                    team is not None and team.owner_id == actor.id
                )
            if not managers[project.team_id]:
                result.append(replace(project, webhook_url=None, webhook_signing_key=None))
            elif project.webhook_url:
                result.append(replace(project, webhook_signing_key=self._signing_keys(project.id)))
            else:
                result.append(project)
        return result

    def list_my_projects(self, actor: User) -> Sequence[Project]:
        projects = self._cache.get_or_load(
            "user_projects",
            CacheKeys.user_projects(actor.id),
            PROJECT_LIST_ADAPTER,
            lambda: list(self._projects.list_for_teams(self._teams.team_ids_for_user(actor.id))),
        )
        return self.redact(actor, projects)

    def _forget_team_lists(self, team_id: UUID) -> None:
        self._cache.forget_user_projects(self._teams.member_ids(team_id))

    def list_team_projects(self, actor: User, team_id: UUID) -> Sequence[Project]:
        team = self._access.team_for_member(actor, team_id)
        return self.redact(actor, self._projects.list_for_team(team.id))

    def create(self, actor: User, team_id: UUID, name: str, webhook_url: str | None) -> Project:
        team = self._access.team_for_manager(actor, team_id)
        url = self._url_policy.validate(webhook_url) if webhook_url else None
        project = self._projects.add(team.id, name.strip(), url)
        self._uow.commit()
        self._forget_team_lists(team.id)
        return self.redact(actor, [project])[0]

    def get(self, actor: User, project_id: UUID) -> Project:
        return self.redact(actor, [self._access.project_for_member(actor, project_id)])[0]

    def update(
        self,
        actor: User,
        project_id: UUID,
        *,
        name: str | None,
        webhook_url: str | None,
        clear_webhook: bool,
    ) -> Project:
        project = self._access.project_for_manager(actor, project_id)
        if project.is_archived:
            raise ProjectArchivedError()
        url = self._url_policy.validate(webhook_url) if webhook_url else None
        updated = self._projects.update(
            project.id,
            name=name.strip() if name is not None else None,
            webhook_url=url,
            clear_webhook=clear_webhook,
        )
        self._uow.commit()
        self._forget_team_lists(updated.team_id)
        return self.redact(actor, [updated])[0]

    def archive(self, actor: User, project_id: UUID) -> Project:
        project = self._access.project_for_manager(actor, project_id)
        archived = self._projects.archive(project.id, self._clock.now())
        self._uow.commit()
        self._forget_team_lists(archived.team_id)
        return self.redact(actor, [archived])[0]
