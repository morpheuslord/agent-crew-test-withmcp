"""Team, membership and team-project endpoints."""

from uuid import UUID

from fastapi import APIRouter, status

from taskboard.api.deps import CurrentUser, Services
from taskboard.api.schemas.work import (
    MemberAdd,
    MemberOut,
    ProjectCreate,
    ProjectOut,
    TeamCreate,
    TeamDetailOut,
    TeamOut,
)

router = APIRouter(prefix="/teams", tags=["teams"])


@router.get("")
def list_teams(services: Services, user: CurrentUser) -> list[TeamOut]:
    return [TeamOut.model_validate(t) for t in services.teams.list_my_teams(user)]


@router.post("", status_code=status.HTTP_201_CREATED)
def create_team(body: TeamCreate, services: Services, user: CurrentUser) -> TeamOut:
    return TeamOut.model_validate(services.teams.create_team(user, body.name))


@router.get("/{team_id}")
def get_team(team_id: UUID, services: Services, user: CurrentUser) -> TeamDetailOut:
    return TeamDetailOut.model_validate(services.teams.get_team(user, team_id))


@router.post("/{team_id}/members", status_code=status.HTTP_201_CREATED)
def add_member(team_id: UUID, body: MemberAdd, services: Services, user: CurrentUser) -> MemberOut:
    return MemberOut.model_validate(services.teams.add_member(user, team_id, body.email))


@router.delete("/{team_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_member(team_id: UUID, user_id: UUID, services: Services, user: CurrentUser) -> None:
    services.teams.remove_member(user, team_id, user_id)


@router.get("/{team_id}/projects")
def list_projects(team_id: UUID, services: Services, user: CurrentUser) -> list[ProjectOut]:
    return [
        ProjectOut.model_validate(p) for p in services.projects.list_team_projects(user, team_id)
    ]


@router.post("/{team_id}/projects", status_code=status.HTTP_201_CREATED)
def create_project(
    team_id: UUID, body: ProjectCreate, services: Services, user: CurrentUser
) -> ProjectOut:
    project = services.projects.create(user, team_id, body.name, body.webhook_url)
    return ProjectOut.model_validate(project)
