"""CSV export of a project's tasks."""

import csv
import io
from collections.abc import Sequence
from typing import Final
from uuid import UUID

from taskboard.domain.entities import Project, Task, User
from taskboard.repositories.interfaces import TaskRepository, TeamRepository
from taskboard.services.access import AccessPolicy

# Spreadsheet apps treat cells starting with these as formulas.
_FORMULA_PREFIXES: Final = ("=", "+", "-", "@", "\t", "\r")

HEADER: Final = (
    "id",
    "title",
    "status",
    "priority",
    "assignee",
    "due_date",
    "labels",
    "created_at",
    "updated_at",
    "description",
)


def neutralise_cell(value: str) -> str:
    """Prefix formula-like values with a quote so they are shown as text (CSV injection)."""
    if value.startswith(_FORMULA_PREFIXES):
        return "'" + value
    return value


class CsvExporter:
    def __init__(
        self, *, tasks: TaskRepository, teams: TeamRepository, access: AccessPolicy
    ) -> None:
        self._tasks = tasks
        self._teams = teams
        self._access = access

    def export(self, actor: User, project_id: UUID) -> tuple[Project, str]:
        project = self._access.project_for_member(actor, project_id)
        tasks = self._tasks.list_for_project(project.id)
        names = {m.user_id: m.display_name for m in self._teams.list_members(project.team_id)}
        return project, self._render(tasks, names)

    @staticmethod
    def _render(tasks: Sequence[Task], names: dict[UUID, str]) -> str:
        out = io.StringIO()
        writer = csv.writer(out, quoting=csv.QUOTE_MINIMAL, lineterminator="\r\n")
        writer.writerow(HEADER)
        for t in tasks:
            assignee = names.get(t.assignee_id, "") if t.assignee_id else ""
            row = [
                str(t.id),
                t.title,
                t.status.value,
                t.priority.value,
                assignee,
                t.due_date.isoformat() if t.due_date else "",
                ";".join(t.labels),
                t.created_at.isoformat(),
                t.updated_at.isoformat(),
                t.description,
            ]
            writer.writerow([neutralise_cell(cell) for cell in row])
        return out.getvalue()
