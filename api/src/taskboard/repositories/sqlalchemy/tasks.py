"""Task repository, including search with client-chosen sorting."""

from collections.abc import Collection, Sequence
from typing import Any
from uuid import UUID

from sqlalchemy import ColumnElement, Select, case, delete, func, or_, select
from sqlalchemy.orm import InstrumentedAttribute, Session, aliased

from taskboard.domain.entities import NewTask, Page, Task, TaskChanges, TaskFilter
from taskboard.domain.enums import SortField, SortOrder
from taskboard.domain.errors import NotFoundError
from taskboard.models.tables import ProjectRow, TaskRow, UserRow
from taskboard.repositories.sqlalchemy.mappers import to_task

_Assignee = aliased(UserRow)

_STATUS_RANK = case({"todo": 1, "in_progress": 2, "done": 3}, value=TaskRow.status)
_PRIORITY_RANK = case({"low": 1, "medium": 2, "high": 3}, value=TaskRow.priority)

# The only way a client value reaches ORDER BY: an enum member mapped to a column expression.
_SORT_COLUMNS: dict[SortField, ColumnElement[Any] | InstrumentedAttribute[Any]] = {
    SortField.TITLE: func.lower(TaskRow.title),
    SortField.STATUS: _STATUS_RANK,
    SortField.PRIORITY: _PRIORITY_RANK,
    SortField.DUE_DATE: TaskRow.due_date,
    SortField.CREATED_AT: TaskRow.created_at,
    SortField.UPDATED_AT: TaskRow.updated_at,
    SortField.ASSIGNEE: func.lower(_Assignee.display_name),
}


def escape_like(term: str) -> str:
    """Escape LIKE wildcards so user text matches literally."""
    return term.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


class SqlTaskRepository:
    def __init__(self, session: Session) -> None:
        self._s = session

    def add(self, task: NewTask) -> Task:
        row = TaskRow(
            project_id=task.project_id,
            title=task.title,
            description=task.description,
            status=task.status.value,
            priority=task.priority.value,
            assignee_id=task.assignee_id,
            due_date=task.due_date,
            labels=list(task.labels),
            created_by=task.created_by,
        )
        self._s.add(row)
        self._s.flush()
        self._s.refresh(row)
        return to_task(row)

    def get(self, task_id: UUID) -> Task | None:
        row = self._s.get(TaskRow, task_id)
        return to_task(row) if row else None

    def update(self, task_id: UUID, changes: TaskChanges) -> Task:
        row = self._s.get(TaskRow, task_id)
        if row is None:
            raise NotFoundError("Task")
        if changes.title is not None:
            row.title = changes.title
        if changes.description is not None:
            row.description = changes.description
        if changes.status is not None:
            row.status = changes.status.value
        if changes.priority is not None:
            row.priority = changes.priority.value
        if changes.labels is not None:
            row.labels = list(changes.labels)
        if "assignee_id" in changes.clear:
            row.assignee_id = None
        elif changes.assignee_id is not None:
            row.assignee_id = changes.assignee_id
        if "due_date" in changes.clear:
            row.due_date = None
        elif changes.due_date is not None:
            row.due_date = changes.due_date
        self._s.flush()
        self._s.refresh(row)
        return to_task(row)

    def delete(self, task_id: UUID) -> None:
        self._s.execute(delete(TaskRow).where(TaskRow.id == task_id))

    def search(
        self,
        flt: TaskFilter,
        *,
        team_ids: Collection[UUID] | None,
        project_id: UUID | None = None,
    ) -> Page[Task]:
        stmt = self._filtered(flt, team_ids=team_ids, project_id=project_id)
        total = self._s.scalar(select(func.count()).select_from(stmt.subquery())) or 0
        column = _SORT_COLUMNS[flt.sort]
        ordered = column.asc() if flt.order is SortOrder.ASC else column.desc()
        rows = self._s.scalars(
            stmt.order_by(ordered.nulls_last(), TaskRow.id)
            .offset((flt.page - 1) * flt.page_size)
            .limit(flt.page_size)
        )
        return Page(tuple(to_task(r) for r in rows), total, flt.page, flt.page_size)

    def _filtered(
        self,
        flt: TaskFilter,
        *,
        team_ids: Collection[UUID] | None,
        project_id: UUID | None,
    ) -> Select[TaskRow]:
        stmt = (
            select(TaskRow)
            .join(ProjectRow, ProjectRow.id == TaskRow.project_id)
            .outerjoin(_Assignee, _Assignee.id == TaskRow.assignee_id)
        )
        if team_ids is not None:
            stmt = stmt.where(ProjectRow.team_id.in_(list(team_ids) or [None]))
        if project_id is not None:
            stmt = stmt.where(TaskRow.project_id == project_id)
        if flt.text:
            pattern = f"%{escape_like(flt.text)}%"
            stmt = stmt.where(
                or_(
                    TaskRow.title.ilike(pattern, escape="\\"),
                    TaskRow.description.ilike(pattern, escape="\\"),
                )
            )
        if flt.status is not None:
            stmt = stmt.where(TaskRow.status == flt.status.value)
        if flt.assignee_id is not None:
            stmt = stmt.where(TaskRow.assignee_id == flt.assignee_id)
        if flt.label:
            stmt = stmt.where(TaskRow.labels.contains([flt.label]))
        if flt.due_before is not None:
            stmt = stmt.where(TaskRow.due_date < flt.due_before)
        return stmt

    def list_for_project(self, project_id: UUID) -> Sequence[Task]:
        rows = self._s.scalars(
            select(TaskRow)
            .where(TaskRow.project_id == project_id)
            .order_by(TaskRow.created_at, TaskRow.id)
        )
        return [to_task(r) for r in rows]
