"""Task, comment, attachment and search endpoints."""

from typing import Annotated, Final
from urllib.parse import quote
from uuid import UUID

from fastapi import APIRouter, File, Query, UploadFile, status
from fastapi.responses import StreamingResponse

from taskboard.api.deps import CurrentUser, Services
from taskboard.api.schemas.work import (
    AttachmentOut,
    CommentCreate,
    CommentOut,
    TaskOut,
    TaskPage,
    TaskQuery,
    TaskUpdate,
)

router = APIRouter(tags=["tasks"])

DOWNLOAD_CSP: Final = "sandbox; default-src 'none'"


def content_disposition(filename: str) -> str:
    """RFC 6266 header with an ASCII fallback and a UTF-8 ``filename*`` parameter."""
    fallback = "".join(
        ch if ch.isascii() and ch.isprintable() and ch not in '"\\;' else "_" for ch in filename
    )
    return f"attachment; filename=\"{fallback}\"; filename*=UTF-8''{quote(filename, safe='')}"


@router.get("/tasks/{task_id}")
def get_task(task_id: UUID, services: Services, user: CurrentUser) -> TaskOut:
    return TaskOut.model_validate(services.tasks.get(user, task_id))


@router.patch("/tasks/{task_id}")
def update_task(task_id: UUID, body: TaskUpdate, services: Services, user: CurrentUser) -> TaskOut:
    return TaskOut.model_validate(services.tasks.update(user, task_id, body.to_changes()))


@router.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: UUID, services: Services, user: CurrentUser) -> None:
    services.tasks.delete(user, task_id)


@router.get("/tasks/{task_id}/comments")
def list_comments(task_id: UUID, services: Services, user: CurrentUser) -> list[CommentOut]:
    return [CommentOut.model_validate(c) for c in services.comments.list(user, task_id)]


@router.post("/tasks/{task_id}/comments", status_code=status.HTTP_201_CREATED)
def add_comment(
    task_id: UUID, body: CommentCreate, services: Services, user: CurrentUser
) -> CommentOut:
    return CommentOut.model_validate(services.comments.add(user, task_id, body.body))


@router.patch("/comments/{comment_id}")
def edit_comment(
    comment_id: UUID, body: CommentCreate, services: Services, user: CurrentUser
) -> CommentOut:
    return CommentOut.model_validate(services.comments.edit(user, comment_id, body.body))


@router.delete("/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_comment(comment_id: UUID, services: Services, user: CurrentUser) -> None:
    services.comments.delete(user, comment_id)


@router.get("/tasks/{task_id}/attachments")
def list_attachments(task_id: UUID, services: Services, user: CurrentUser) -> list[AttachmentOut]:
    return [AttachmentOut.model_validate(a) for a in services.attachments.list(user, task_id)]


@router.post("/tasks/{task_id}/attachments", status_code=status.HTTP_201_CREATED)
def upload_attachment(
    task_id: UUID,
    file: Annotated[UploadFile, File()],
    services: Services,
    user: CurrentUser,
) -> AttachmentOut:
    attachment = services.attachments.upload(
        user,
        task_id,
        filename=file.filename,
        content_type=file.content_type,
        data=file.file,
    )
    return AttachmentOut.model_validate(attachment)


@router.get("/attachments/{attachment_id}/download", response_class=StreamingResponse)
def download_attachment(
    attachment_id: UUID, services: Services, user: CurrentUser
) -> StreamingResponse:
    attachment, stream = services.attachments.open(user, attachment_id)
    return StreamingResponse(
        stream,
        media_type="application/octet-stream",
        headers={
            "Content-Disposition": content_disposition(attachment.filename),
            "Content-Length": str(attachment.size_bytes),
            "Content-Security-Policy": DOWNLOAD_CSP,
            "X-Content-Type-Options": "nosniff",
        },
    )


@router.get("/search/tasks")
def search_tasks(
    query: Annotated[TaskQuery, Query()], services: Services, user: CurrentUser
) -> TaskPage:
    page = services.tasks.search(user, query.to_filter())
    return TaskPage(
        items=[TaskOut.model_validate(t) for t in page.items],
        total=page.total,
        page=page.page,
        page_size=page.page_size,
    )
