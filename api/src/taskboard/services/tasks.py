"""Tasks: CRUD, status changes with webhooks, listing and cross-project search."""

import logging
from uuid import UUID

from taskboard.domain.entities import (
    NewTask,
    Page,
    Project,
    StatusChangedEvent,
    Task,
    TaskChanges,
    TaskDraft,
    TaskFilter,
    User,
)
from taskboard.domain.enums import ActivityType
from taskboard.domain.errors import NotFoundError, ValidationFailedError
from taskboard.infra.storage.base import AttachmentStorage
from taskboard.infra.webhooks.notifier import WebhookNotifier
from taskboard.repositories.interfaces import (
    AttachmentRepository,
    TaskRepository,
    TeamRepository,
    UnitOfWork,
)
from taskboard.services.access import AccessPolicy
from taskboard.services.activity import ActivityService
from taskboard.services.caching import TASK_ADAPTER, TASK_PAGE_ADAPTER, CacheAside, CacheKeys
from taskboard.services.security import Clock

logger = logging.getLogger("taskboard.tasks")


class TaskService:
    def __init__(
        self,
        *,
        tasks: TaskRepository,
        teams: TeamRepository,
        attachments: AttachmentRepository,
        storage: AttachmentStorage,
        access: AccessPolicy,
        activity: ActivityService,
        notifier: WebhookNotifier,
        clock: Clock,
        uow: UnitOfWork,
        cache: CacheAside,
    ) -> None:
        self._tasks = tasks
        self._teams = teams
        self._attachments = attachments
        self._storage = storage
        self._access = access
        self._activity = activity
        self._notifier = notifier
        self._clock = clock
        self._uow = uow
        self._cache = cache

    def _check_assignee(self, project: Project, assignee_id: UUID | None) -> None:
        if assignee_id is not None and not self._teams.is_member(project.team_id, assignee_id):
            raise ValidationFailedError("The assignee must be a member of the project's team.")

    def list_project_tasks(self, actor: User, project_id: UUID, flt: TaskFilter) -> Page[Task]:
        project = self._access.project_for_member(actor, project_id)
        version = self._cache.task_list_version(project.id)
        return self._cache.get_or_load(
            "task_list",
            CacheKeys.task_list(project.id, version, flt),
            TASK_PAGE_ADAPTER,
            lambda: self._tasks.search(flt, team_ids=None, project_id=project.id),
        )

    def search(self, actor: User, flt: TaskFilter) -> Page[Task]:
        return self._tasks.search(flt, team_ids=self._access.visible_team_ids(actor))

    def create(self, actor: User, project_id: UUID, draft: TaskDraft) -> Task:
        project = self._access.project_for_writer(actor, project_id)
        self._check_assignee(project, draft.assignee_id)
        task = self._tasks.add(
            NewTask(
                project_id=project.id,
                title=draft.title.strip(),
                description=draft.description,
                status=draft.status,
                priority=draft.priority,
                assignee_id=draft.assignee_id,
                due_date=draft.due_date,
                labels=draft.labels,
                created_by=actor.id,
            )
        )
        self._activity.record(
            actor=actor,
            event_type=ActivityType.TASK_CREATED,
            team_id=project.team_id,
            project_id=project.id,
            task_id=task.id,
            details={"title": task.title},
        )
        self._uow.commit()
        self._cache.forget_task_lists(project.id)
        return task

    def get(self, actor: User, task_id: UUID) -> Task:
        task = self._cache.get_or_load(
            "task", CacheKeys.task(task_id), TASK_ADAPTER, lambda: self._tasks.get(task_id)
        )
        if task is None:
            raise NotFoundError("Task")
        # A task never moves between projects, so the cached project id is safe to authorize
        # with; membership itself is always checked against the database.
        try:
            self._access.project_for_member(actor, task.project_id)
        except NotFoundError:
            raise NotFoundError("Task") from None
        return task

    def update(self, actor: User, task_id: UUID, changes: TaskChanges) -> Task:
        task, project = self._access.task_for_writer(actor, task_id)
        if changes.assignee_id is not None:
            self._check_assignee(project, changes.assignee_id)
        updated = self._tasks.update(task.id, changes)
        status_changed = changes.status is not None and changes.status is not task.status
        other_fields = [f for f in changes.changed_fields() if f != "status"]
        if other_fields:
            self._activity.record(
                actor=actor,
                event_type=ActivityType.TASK_UPDATED,
                team_id=project.team_id,
                project_id=project.id,
                task_id=task.id,
                details={"title": updated.title, "fields": other_fields},
            )
        if status_changed:
            self._activity.record(
                actor=actor,
                event_type=ActivityType.STATUS_CHANGED,
                team_id=project.team_id,
                project_id=project.id,
                task_id=task.id,
                details={
                    "title": updated.title,
                    "old_status": task.status.value,
                    "new_status": updated.status.value,
                },
            )
        self._uow.commit()
        self._cache.forget_task(task.id)
        self._cache.forget_task_lists(project.id)
        if status_changed and project.webhook_url:
            self._notifier.notify(
                project.webhook_url,
                StatusChangedEvent(
                    task_id=task.id,
                    project_id=project.id,
                    old_status=task.status,
                    new_status=updated.status,
                    actor_id=actor.id,
                    timestamp=self._clock.now(),
                ),
            )
        return updated

    def delete(self, actor: User, task_id: UUID) -> Task:
        task, project = self._access.task_for_writer(actor, task_id)
        keys = [a.storage_key for a in self._attachments.list_for_task(task.id)]
        self._tasks.delete(task.id)
        self._uow.commit()
        self._cache.forget_task(task.id)
        self._cache.forget_task_lists(project.id)
        for key in keys:
            try:
                self._storage.delete(key)
            except Exception:
                logger.warning("attachment blob not deleted", extra={"task_id": str(task.id)})
        return task
