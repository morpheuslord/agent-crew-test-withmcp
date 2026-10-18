"""Repositories for comments, attachments and activity events, plus the unit of work."""

from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import Select, delete, func, or_, select
from sqlalchemy.orm import Session

from taskboard.domain.entities import ActivityEvent, Attachment, Comment, NewActivity, Page
from taskboard.domain.enums import ActivityType
from taskboard.domain.errors import NotFoundError
from taskboard.models.tables import ActivityEventRow, AttachmentRow, CommentRow, UserRow
from taskboard.repositories.sqlalchemy.mappers import to_attachment


class SqlUnitOfWork:
    def __init__(self, session: Session) -> None:
        self._s = session

    def commit(self) -> None:
        self._s.commit()

    def rollback(self) -> None:
        self._s.rollback()


class SqlCommentRepository:
    def __init__(self, session: Session) -> None:
        self._s = session

    def _select(self) -> Select[CommentRow, str]:
        return select(CommentRow, UserRow.display_name).join(
            UserRow, UserRow.id == CommentRow.author_id
        )

    @staticmethod
    def _to_comment(row: CommentRow, author_name: str) -> Comment:
        return Comment(
            id=row.id,
            task_id=row.task_id,
            author_id=row.author_id,
            author_name=author_name,
            body=row.body,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    def _hydrate(self, row: CommentRow) -> Comment:
        self._s.flush()
        self._s.refresh(row)
        name = self._s.scalar(select(UserRow.display_name).where(UserRow.id == row.author_id))
        return self._to_comment(row, name or "")

    def add(self, task_id: UUID, author_id: UUID, body: str) -> Comment:
        row = CommentRow(task_id=task_id, author_id=author_id, body=body)
        self._s.add(row)
        return self._hydrate(row)

    def get(self, comment_id: UUID) -> Comment | None:
        result = self._s.execute(self._select().where(CommentRow.id == comment_id)).first()
        if result is None:
            return None
        return self._to_comment(result[0], result[1])

    def list_for_task(self, task_id: UUID) -> Sequence[Comment]:
        rows = self._s.execute(
            self._select()
            .where(CommentRow.task_id == task_id)
            .order_by(CommentRow.created_at, CommentRow.id)
        )
        return [self._to_comment(r[0], r[1]) for r in rows]

    def update(self, comment_id: UUID, body: str) -> Comment:
        row = self._s.get(CommentRow, comment_id)
        if row is None:
            raise NotFoundError("Comment")
        row.body = body
        return self._hydrate(row)

    def delete(self, comment_id: UUID) -> None:
        self._s.execute(delete(CommentRow).where(CommentRow.id == comment_id))


class SqlAttachmentRepository:
    def __init__(self, session: Session) -> None:
        self._s = session

    def add(
        self,
        *,
        task_id: UUID,
        uploader_id: UUID,
        filename: str,
        content_type: str,
        size_bytes: int,
        storage_key: str,
    ) -> Attachment:
        row = AttachmentRow(
            task_id=task_id,
            uploader_id=uploader_id,
            filename=filename,
            content_type=content_type,
            size_bytes=size_bytes,
            storage_key=storage_key,
        )
        self._s.add(row)
        self._s.flush()
        self._s.refresh(row)
        return to_attachment(row)

    def get(self, attachment_id: UUID) -> Attachment | None:
        row = self._s.get(AttachmentRow, attachment_id)
        return to_attachment(row) if row else None

    def list_for_task(self, task_id: UUID) -> Sequence[Attachment]:
        rows = self._s.scalars(
            select(AttachmentRow)
            .where(AttachmentRow.task_id == task_id)
            .order_by(AttachmentRow.created_at, AttachmentRow.id)
        )
        return [to_attachment(r) for r in rows]


class SqlActivityRepository:
    def __init__(self, session: Session) -> None:
        self._s = session

    def add(self, event: NewActivity) -> None:
        self._s.add(
            ActivityEventRow(
                team_id=event.team_id,
                project_id=event.project_id,
                task_id=event.task_id,
                actor_id=event.actor_id,
                event_type=event.event_type.value,
                details=event.details,
            )
        )
        self._s.flush()

    def _page(
        self, stmt: Select[ActivityEventRow, str], page: int, page_size: int
    ) -> Page[ActivityEvent]:
        total = self._s.scalar(select(func.count()).select_from(stmt.subquery())) or 0
        rows = self._s.execute(
            stmt.order_by(ActivityEventRow.created_at.desc(), ActivityEventRow.id)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        items = tuple(
            ActivityEvent(
                id=r[0].id,
                team_id=r[0].team_id,
                project_id=r[0].project_id,
                task_id=r[0].task_id,
                actor_id=r[0].actor_id,
                actor_name=r[1],
                event_type=ActivityType(r[0].event_type),
                details=dict(r[0].details),
                created_at=r[0].created_at,
            )
            for r in rows
        )
        return Page(items, total, page, page_size)

    def _base(self) -> Select[ActivityEventRow, str]:
        return select(ActivityEventRow, UserRow.display_name).join(
            UserRow, UserRow.id == ActivityEventRow.actor_id
        )

    def list_for_project(
        self, project_id: UUID, team_id: UUID, page: int, page_size: int
    ) -> Page[ActivityEvent]:
        # A project's feed also shows its team's membership events, which have no project.
        stmt = self._base().where(
            or_(
                ActivityEventRow.project_id == project_id,
                (ActivityEventRow.team_id == team_id) & ActivityEventRow.project_id.is_(None),
            )
        )
        return self._page(stmt, page, page_size)

    def list_all(self, page: int, page_size: int) -> Page[ActivityEvent]:
        return self._page(self._base(), page, page_size)
