"""Projects: creation, renaming, webhook configuration and archiving."""

from collections.abc import Sequence
from dataclasses import replace
from uuid import UUID

from taskboard.domain.entities import Project, User
from taskboard.domain.errors import ProjectArchivedError
from taskboard.infra.webhooks.url_policy import WebhookUrlPolicy
from taskboard.repositories.interfaces import ProjectRepository, TeamRepository, UnitOfWork
from taskboard.services.access import AccessPolicy
from taskboard.services.security import Clock


class ProjectService:
    def __init__(
        self,
        *,
        projects: ProjectRepository,
        teams: TeamRepository,
        access: AccessPolicy,
        url_policy: WebhookUrlPolicy,
        clock: Clock,
        uow: UnitOfWork,
    ) -> None:
        self._projects = projects
        self._teams = teams
        self._access = access
        self._url_policy = url_policy
        self._clock = clock
        self._uow = uow

    def redact(self, actor: User, projects: Sequence[Project]) -> list[Project]:
        """Hide webhook URLs (which often embed secrets) from anyone but owners and admins."""
        if actor.is_admin:
            return list(projects)
        owners: dict[UUID, bool] = {}
        result = []
        for project in projects:
            if project.team_id not in owners:
                team = self._teams.get(project.team_id)
                owners[project.team_id] = team is not None and team.owner_id == actor.id
            visible = owners[project.team_id]
            result.append(project if visible else replace(project, webhook_url=None))
        return result

    def list_my_projects(self, actor: User) -> Sequence[Project]:
        return self.redact(
            actor, self._projects.list_for_teams(self._teams.team_ids_for_user(actor.id))
        )

    def list_team_projects(self, actor: User, team_id: UUID) -> Sequence[Project]:
        team = self._access.team_for_member(actor, team_id)
        return self.redact(actor, self._projects.list_for_team(team.id))

    def create(self, actor: User, team_id: UUID, name: str, webhook_url: str | None) -> Project:
        team = self._access.team_for_manager(actor, team_id)
        url = self._url_policy.validate(webhook_url) if webhook_url else None
        project = self._projects.add(team.id, name.strip(), url)
        self._uow.commit()
        return project

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
        return updated

    def archive(self, actor: User, project_id: UUID) -> Project:
        project = self._access.project_for_manager(actor, project_id)
        archived = self._projects.archive(project.id, self._clock.now())
        self._uow.commit()
        return archived
