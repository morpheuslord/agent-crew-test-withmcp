"""Repositories for teams, memberships and projects."""

from collections.abc import Collection, Sequence
from datetime import datetime
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from taskboard.domain.entities import Project, Team, TeamMember
from taskboard.domain.errors import NotFoundError
from taskboard.models.tables import ProjectRow, TeamMemberRow, TeamRow, UserRow
from taskboard.repositories.sqlalchemy.mappers import to_project, to_team


class SqlTeamRepository:
    def __init__(self, session: Session) -> None:
        self._s = session

    def add(self, name: str, owner_id: UUID) -> Team:
        row = TeamRow(name=name, owner_id=owner_id)
        self._s.add(row)
        self._s.flush()
        self._s.add(TeamMemberRow(team_id=row.id, user_id=owner_id))
        self._s.flush()
        self._s.refresh(row)
        return to_team(row)

    def get(self, team_id: UUID) -> Team | None:
        row = self._s.get(TeamRow, team_id)
        return to_team(row) if row else None

    def list_for_user(self, user_id: UUID) -> Sequence[Team]:
        rows = self._s.scalars(
            select(TeamRow)
            .join(TeamMemberRow, TeamMemberRow.team_id == TeamRow.id)
            .where(TeamMemberRow.user_id == user_id)
            .order_by(TeamRow.name, TeamRow.id)
        )
        return [to_team(r) for r in rows]

    def team_ids_for_user(self, user_id: UUID) -> set[UUID]:
        return set(
            self._s.scalars(select(TeamMemberRow.team_id).where(TeamMemberRow.user_id == user_id))
        )

    def is_member(self, team_id: UUID, user_id: UUID) -> bool:
        return self._s.get(TeamMemberRow, (team_id, user_id)) is not None

    def add_member(self, team_id: UUID, user_id: UUID) -> None:
        self._s.add(TeamMemberRow(team_id=team_id, user_id=user_id))
        self._s.flush()

    def remove_member(self, team_id: UUID, user_id: UUID) -> bool:
        result = self._s.execute(
            delete(TeamMemberRow).where(
                TeamMemberRow.team_id == team_id, TeamMemberRow.user_id == user_id
            )
        )
        return bool(getattr(result, "rowcount", 0))

    def list_members(self, team_id: UUID) -> Sequence[TeamMember]:
        rows = self._s.execute(
            select(UserRow.id, UserRow.email, UserRow.display_name, TeamMemberRow.added_at)
            .join(TeamMemberRow, TeamMemberRow.user_id == UserRow.id)
            .where(TeamMemberRow.team_id == team_id)
            .order_by(UserRow.display_name, UserRow.id)
        )
        return [TeamMember(r.id, r.email, r.display_name, r.added_at) for r in rows]

    def member_ids(self, team_id: UUID) -> set[UUID]:
        return set(
            self._s.scalars(select(TeamMemberRow.user_id).where(TeamMemberRow.team_id == team_id))
        )


class SqlProjectRepository:
    def __init__(self, session: Session) -> None:
        self._s = session

    def add(self, team_id: UUID, name: str, webhook_url: str | None) -> Project:
        row = ProjectRow(team_id=team_id, name=name, webhook_url=webhook_url)
        self._s.add(row)
        self._s.flush()
        self._s.refresh(row)
        return to_project(row)

    def get(self, project_id: UUID) -> Project | None:
        row = self._s.get(ProjectRow, project_id)
        return to_project(row) if row else None

    def list_for_team(self, team_id: UUID) -> Sequence[Project]:
        rows = self._s.scalars(
            select(ProjectRow)
            .where(ProjectRow.team_id == team_id)
            .order_by(ProjectRow.name, ProjectRow.id)
        )
        return [to_project(r) for r in rows]

    def list_for_teams(self, team_ids: Collection[UUID]) -> Sequence[Project]:
        if not team_ids:
            return []
        rows = self._s.scalars(
            select(ProjectRow)
            .where(ProjectRow.team_id.in_(list(team_ids)))
            .order_by(ProjectRow.name, ProjectRow.id)
        )
        return [to_project(r) for r in rows]

    def _row(self, project_id: UUID) -> ProjectRow:
        row = self._s.get(ProjectRow, project_id)
        if row is None:
            raise NotFoundError("Project")
        return row

    def update(
        self, project_id: UUID, *, name: str | None, webhook_url: str | None, clear_webhook: bool
    ) -> Project:
        row = self._row(project_id)
        if name is not None:
            row.name = name
        if clear_webhook:
            row.webhook_url = None
        elif webhook_url is not None:
            row.webhook_url = webhook_url
        self._s.flush()
        self._s.refresh(row)
        return to_project(row)

    def archive(self, project_id: UUID, now: datetime) -> Project:
        row = self._row(project_id)
        if row.archived_at is None:
            row.archived_at = now
        self._s.flush()
        self._s.refresh(row)
        return to_project(row)
