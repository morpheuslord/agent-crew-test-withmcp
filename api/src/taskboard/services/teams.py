"""Teams and team membership."""

from collections.abc import Sequence
from dataclasses import replace
from uuid import UUID

from taskboard.domain.entities import Team, TeamDetail, TeamMember, User
from taskboard.domain.enums import ActivityType
from taskboard.domain.errors import ConflictError, NotFoundError, ValidationFailedError
from taskboard.repositories.interfaces import (
    ProjectRepository,
    TeamRepository,
    UnitOfWork,
    UserRepository,
)
from taskboard.services.access import AccessPolicy
from taskboard.services.activity import ActivityService
from taskboard.services.auth import normalize_email
from taskboard.services.caching import TEAM_LIST_ADAPTER, CacheAside, CacheKeys


class TeamService:
    def __init__(
        self,
        *,
        teams: TeamRepository,
        projects: ProjectRepository,
        users: UserRepository,
        access: AccessPolicy,
        activity: ActivityService,
        uow: UnitOfWork,
        cache: CacheAside,
    ) -> None:
        self._teams = teams
        self._projects = projects
        self._users = users
        self._access = access
        self._activity = activity
        self._uow = uow
        self._cache = cache

    def list_my_teams(self, actor: User) -> Sequence[Team]:
        return self._cache.get_or_load(
            "user_teams",
            CacheKeys.user_teams(actor.id),
            TEAM_LIST_ADAPTER,
            lambda: list(self._teams.list_for_user(actor.id)),
        )

    def create_team(self, actor: User, name: str) -> Team:
        team = self._teams.add(name.strip(), actor.id)
        self._uow.commit()
        self._cache.forget_user_teams([actor.id])
        return team

    def get_team(self, actor: User, team_id: UUID) -> TeamDetail:
        team = self._access.team_for_member(actor, team_id)
        projects = self._projects.list_for_team(team.id)
        if not (actor.is_admin or team.owner_id == actor.id):
            # Webhook URLs often embed secrets; only owners and admins see them.
            projects = [replace(p, webhook_url=None) for p in projects]
        return TeamDetail(
            team=team,
            members=tuple(self._teams.list_members(team.id)),
            projects=tuple(projects),
        )

    def member_ids(self, team_id: UUID) -> set[UUID]:
        return self._teams.member_ids(team_id)

    def add_member(self, actor: User, team_id: UUID, email: str) -> TeamMember:
        team = self._access.team_for_manager(actor, team_id)
        user = self._users.get_by_email(normalize_email(email))
        if user is None or not user.is_active:
            raise NotFoundError("User")
        if self._teams.is_member(team.id, user.id):
            raise ConflictError("That user is already a member of this team.")
        self._teams.add_member(team.id, user.id)
        self._activity.record(
            actor=actor,
            event_type=ActivityType.MEMBER_ADDED,
            team_id=team.id,
            details={"user_id": str(user.id), "display_name": user.display_name},
        )
        member = next(m for m in self._teams.list_members(team.id) if m.user_id == user.id)
        self._uow.commit()
        self._forget_membership(user.id)
        return member

    def remove_member(self, actor: User, team_id: UUID, user_id: UUID) -> None:
        team = self._access.team_for_manager(actor, team_id)
        if user_id == team.owner_id:
            raise ValidationFailedError("The team owner cannot be removed.")
        user = self._users.get(user_id)
        if user is None or not self._teams.remove_member(team.id, user_id):
            raise NotFoundError("Member")
        self._activity.record(
            actor=actor,
            event_type=ActivityType.MEMBER_REMOVED,
            team_id=team.id,
            details={"user_id": str(user_id), "display_name": user.display_name},
        )
        self._uow.commit()
        self._forget_membership(user_id)

    def _forget_membership(self, user_id: UUID) -> None:
        self._cache.forget_user_teams([user_id])
        self._cache.forget_user_projects([user_id])
