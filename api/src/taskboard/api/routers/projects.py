"""Project endpoints, including the project's task list, CSV export and activity feed."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query, Response, status

from taskboard.api.deps import CurrentUser, Services
from taskboard.api.schemas.common import PageParams
from taskboard.api.schemas.work import (
    ActivityOut,
    ActivityPage,
    ProjectOut,
    ProjectUpdate,
    TaskCreate,
    TaskOut,
    TaskPage,
    TaskQuery,
)

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("")
def my_projects(services: Services, user: CurrentUser) -> list[ProjectOut]:
    return [ProjectOut.model_validate(p) for p in services.projects.list_my_projects(user)]


@router.get("/{project_id}")
def get_project(project_id: UUID, services: Services, user: CurrentUser) -> ProjectOut:
    return ProjectOut.model_validate(services.projects.get(user, project_id))


@router.patch("/{project_id}")
def update_project(
    project_id: UUID, body: ProjectUpdate, services: Services, user: CurrentUser
) -> ProjectOut:
    project = services.projects.update(
        user,
        project_id,
        name=body.name,
        webhook_url=body.webhook_url,
        clear_webhook=body.clear_webhook,
    )
    return ProjectOut.model_validate(project)


@router.post("/{project_id}/archive")
def archive_project(project_id: UUID, services: Services, user: CurrentUser) -> ProjectOut:
    return ProjectOut.model_validate(services.projects.archive(user, project_id))


@router.get("/{project_id}/tasks")
def list_tasks(
    project_id: UUID,
    query: Annotated[TaskQuery, Query()],
    services: Services,
    user: CurrentUser,
) -> TaskPage:
    page = services.tasks.list_project_tasks(user, project_id, query.to_filter())
    return TaskPage(
        items=[TaskOut.model_validate(t) for t in page.items],
        total=page.total,
        page=page.page,
        page_size=page.page_size,
    )


@router.post("/{project_id}/tasks", status_code=status.HTTP_201_CREATED)
def create_task(
    project_id: UUID, body: TaskCreate, services: Services, user: CurrentUser
) -> TaskOut:
    return TaskOut.model_validate(services.tasks.create(user, project_id, body.to_draft()))


@router.get("/{project_id}/export.csv", response_class=Response)
def export_csv(project_id: UUID, services: Services, user: CurrentUser) -> Response:
    project, content = services.exporter.export(user, project_id)
    return Response(
        content=content.encode("utf-8"),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="project-{project.id}.csv"'},
    )


@router.get("/{project_id}/activity")
def project_activity(
    project_id: UUID,
    paging: Annotated[PageParams, Query()],
    services: Services,
    user: CurrentUser,
) -> ActivityPage:
    page = services.activity.project_feed(user, project_id, paging.page, paging.page_size)
    return ActivityPage(
        items=[ActivityOut.model_validate(e) for e in page.items],
        total=page.total,
        page=page.page,
        page_size=page.page_size,
    )
