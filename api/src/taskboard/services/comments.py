"""Comments on tasks."""

from collections.abc import Sequence
from uuid import UUID

from taskboard.domain.entities import Comment, User
from taskboard.domain.enums import ActivityType
from taskboard.domain.errors import NotFoundError, PermissionDeniedError, ProjectArchivedError
from taskboard.repositories.interfaces import CommentRepository, UnitOfWork
from taskboard.services.access import AccessPolicy
from taskboard.services.activity import ActivityService


class CommentService:
    def __init__(
        self,
        *,
        comments: CommentRepository,
        access: AccessPolicy,
        activity: ActivityService,
        uow: UnitOfWork,
    ) -> None:
        self._comments = comments
        self._access = access
        self._activity = activity
        self._uow = uow

    def list(self, actor: User, task_id: UUID) -> Sequence[Comment]:
        task, _ = self._access.task_for_member(actor, task_id)
        return self._comments.list_for_task(task.id)

    def add(self, actor: User, task_id: UUID, body: str) -> Comment:
        task, project = self._access.task_for_writer(actor, task_id)
        comment = self._comments.add(task.id, actor.id, body)
        self._activity.record(
            actor=actor,
            event_type=ActivityType.COMMENT_ADDED,
            team_id=project.team_id,
            project_id=project.id,
            task_id=task.id,
            details={"title": task.title, "comment_id": str(comment.id)},
        )
        self._uow.commit()
        return comment

    def _own_comment(self, actor: User, comment_id: UUID) -> Comment:
        comment = self._comments.get(comment_id)
        if comment is None:
            raise NotFoundError("Comment")
        try:
            _, project = self._access.task_for_member(actor, comment.task_id)
        except NotFoundError:
            raise NotFoundError("Comment") from None
        if comment.author_id != actor.id:
            raise PermissionDeniedError("Only the author can change this comment.")
        if project.is_archived:
            raise ProjectArchivedError()
        return comment

    def edit(self, actor: User, comment_id: UUID, body: str) -> Comment:
        comment = self._own_comment(actor, comment_id)
        updated = self._comments.update(comment.id, body)
        self._uow.commit()
        return updated

    def delete(self, actor: User, comment_id: UUID) -> None:
        comment = self._own_comment(actor, comment_id)
        self._comments.delete(comment.id)
        self._uow.commit()
