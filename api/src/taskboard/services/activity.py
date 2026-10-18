"""Activity feed: recording events and reading per-project and global feeds."""

from typing import Any
from uuid import UUID

from taskboard.domain.entities import ActivityEvent, NewActivity, Page, User
from taskboard.domain.enums import ActivityType
from taskboard.repositories.interfaces import ActivityRepository
from taskboard.services.access import AccessPolicy


class ActivityService:
    def __init__(self, activity: ActivityRepository, access: AccessPolicy) -> None:
        self._activity = activity
        self._access = access

    def record(
        self,
        *,
        actor: User,
        event_type: ActivityType,
        team_id: UUID,
        project_id: UUID | None = None,
        task_id: UUID | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Add an event in the caller's transaction; it commits with the change it describes."""
        self._activity.add(
            NewActivity(
                team_id=team_id,
                project_id=project_id,
                task_id=task_id,
                actor_id=actor.id,
                event_type=event_type,
                details=details or {},
            )
        )

    def project_feed(
        self, actor: User, project_id: UUID, page: int, page_size: int
    ) -> Page[ActivityEvent]:
        project = self._access.project_for_member(actor, project_id)
        return self._activity.list_for_project(project.id, project.team_id, page, page_size)

    def global_feed(self, actor: User, page: int, page_size: int) -> Page[ActivityEvent]:
        self._access.require_admin(actor)
        return self._activity.list_all(page, page_size)
