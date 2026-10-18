"""Central authorization rules. Every service asks this class before touching data."""

import logging
from uuid import UUID

from taskboard.domain.entities import Project, Task, Team, User
from taskboard.domain.errors import NotFoundError, PermissionDeniedError, ProjectArchivedError
from taskboard.repositories.interfaces import ProjectRepository, TaskRepository, TeamRepository

logger = logging.getLogger("taskboard.access")


class AccessPolicy:
    """Resolves objects to their team and checks the caller's relationship to that team.

    Callers who cannot see an object get ``NotFoundError``, so object ids from other teams are never
    confirmed. Callers who can see it but may not change it get ``PermissionDeniedError``.
    """

    def __init__(
        self, teams: TeamRepository, projects: ProjectRepository, tasks: TaskRepository
    ) -> None:
        self._teams = teams
        self._projects = projects
        self._tasks = tasks

    def visible_team_ids(self, actor: User) -> set[UUID] | None:
        """Teams whose data the actor may read; ``None`` means every team (admins)."""
        if actor.is_admin:
            return None
        return self._teams.team_ids_for_user(actor.id)

    def require_admin(self, actor: User) -> None:
        if not actor.is_admin:
            self._deny(actor, "admin")
            raise PermissionDeniedError()

    def team_for_member(self, actor: User, team_id: UUID) -> Team:
        team = self._teams.get(team_id)
        if team is None or not (actor.is_admin or self._teams.is_member(team_id, actor.id)):
            self._deny(actor, "team", team_id)
            raise NotFoundError("Team")
        return team

    def team_for_manager(self, actor: User, team_id: UUID) -> Team:
        team = self.team_for_member(actor, team_id)
        if not (actor.is_admin or team.owner_id == actor.id):
            self._deny(actor, "team-manage", team_id)
            raise PermissionDeniedError("Only the team owner or an admin can do that.")
        return team

    def project_for_member(self, actor: User, project_id: UUID) -> Project:
        project = self._projects.get(project_id)
        if project is None:
            raise NotFoundError("Project")
        try:
            self.team_for_member(actor, project.team_id)
        except NotFoundError:
            raise NotFoundError("Project") from None
        return project

    def project_for_manager(self, actor: User, project_id: UUID) -> Project:
        project = self.project_for_member(actor, project_id)
        self.team_for_manager(actor, project.team_id)
        return project

    def project_for_writer(self, actor: User, project_id: UUID) -> Project:
        """Members may write only to active projects."""
        project = self.project_for_member(actor, project_id)
        if project.is_archived:
            raise ProjectArchivedError()
        return project

    def task_for_member(self, actor: User, task_id: UUID) -> tuple[Task, Project]:
        task = self._tasks.get(task_id)
        if task is None:
            raise NotFoundError("Task")
        try:
            project = self.project_for_member(actor, task.project_id)
        except NotFoundError:
            raise NotFoundError("Task") from None
        return task, project

    def task_for_writer(self, actor: User, task_id: UUID) -> tuple[Task, Project]:
        task, project = self.task_for_member(actor, task_id)
        if project.is_archived:
            raise ProjectArchivedError()
        return task, project

    @staticmethod
    def _deny(actor: User, scope: str, object_id: UUID | None = None) -> None:
        logger.info(
            "access denied",
            extra={
                "actor_id": str(actor.id),
                "scope": scope,
                "object_id": str(object_id) if object_id else None,
            },
        )
