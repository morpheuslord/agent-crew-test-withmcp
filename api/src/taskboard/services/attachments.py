"""Task attachments: upload with a size cap, listing and download."""

import logging
import tempfile
import unicodedata
import uuid
from collections.abc import Iterator, Sequence
from pathlib import PurePosixPath, PureWindowsPath
from typing import BinaryIO, Final
from uuid import UUID

from taskboard.domain.entities import Attachment, User
from taskboard.domain.enums import ActivityType
from taskboard.domain.errors import NotFoundError, PayloadTooLargeError
from taskboard.infra.storage.base import CHUNK_SIZE, AttachmentStorage, BlobNotFoundError
from taskboard.repositories.interfaces import AttachmentRepository, UnitOfWork
from taskboard.services.access import AccessPolicy
from taskboard.services.activity import ActivityService

logger = logging.getLogger("taskboard.attachments")

MAX_FILENAME_LENGTH: Final = 200
MAX_CONTENT_TYPE_LENGTH: Final = 100


def clean_filename(raw: str | None) -> str:
    """Keep only a safe display name: the base name, no control characters, bounded length."""
    name = raw or ""
    name = PureWindowsPath(PurePosixPath(name).name).name
    name = "".join(ch for ch in name if unicodedata.category(ch)[0] != "C")
    name = name.strip().strip(".")
    if len(name) > MAX_FILENAME_LENGTH:
        stem, dot, ext = name.rpartition(".")
        if dot and len(ext) <= 16:
            name = stem[: MAX_FILENAME_LENGTH - len(ext) - 1] + "." + ext
        else:
            name = name[:MAX_FILENAME_LENGTH]
    return name or "attachment"


def clean_content_type(raw: str | None) -> str:
    """Recorded for information only; downloads are always served as octet-stream."""
    value = (raw or "").split(";")[0].strip().lower()
    if not value or len(value) > MAX_CONTENT_TYPE_LENGTH or not value.isascii() or "/" not in value:
        return "application/octet-stream"
    return value


class AttachmentService:
    def __init__(
        self,
        *,
        attachments: AttachmentRepository,
        storage: AttachmentStorage,
        access: AccessPolicy,
        activity: ActivityService,
        uow: UnitOfWork,
        max_bytes: int,
    ) -> None:
        self._attachments = attachments
        self._storage = storage
        self._access = access
        self._activity = activity
        self._uow = uow
        self._max_bytes = max_bytes

    def list(self, actor: User, task_id: UUID) -> Sequence[Attachment]:
        task, _ = self._access.task_for_member(actor, task_id)
        return self._attachments.list_for_task(task.id)

    def upload(
        self,
        actor: User,
        task_id: UUID,
        *,
        filename: str | None,
        content_type: str | None,
        data: BinaryIO,
    ) -> Attachment:
        task, project = self._access.task_for_writer(actor, task_id)
        key = f"attachments/{uuid.uuid4().hex}"
        with tempfile.SpooledTemporaryFile(max_size=1024 * 1024) as buffer:
            size = 0
            while chunk := data.read(CHUNK_SIZE):
                size += len(chunk)
                if size > self._max_bytes:
                    raise PayloadTooLargeError(
                        f"Attachments are limited to {self._max_bytes // (1024 * 1024)} MB."
                    )
                buffer.write(chunk)
            buffer.seek(0)
            self._storage.save(key, buffer, size)
        try:
            attachment = self._attachments.add(
                task_id=task.id,
                uploader_id=actor.id,
                filename=clean_filename(filename),
                content_type=clean_content_type(content_type),
                size_bytes=size,
                storage_key=key,
            )
            self._activity.record(
                actor=actor,
                event_type=ActivityType.ATTACHMENT_ADDED,
                team_id=project.team_id,
                project_id=project.id,
                task_id=task.id,
                details={"title": task.title, "filename": attachment.filename},
            )
            self._uow.commit()
        except Exception:
            self._uow.rollback()
            self._storage.delete(key)
            raise
        return attachment

    def open(self, actor: User, attachment_id: UUID) -> tuple[Attachment, Iterator[bytes]]:
        attachment = self._attachments.get(attachment_id)
        if attachment is None:
            raise NotFoundError("Attachment")
        try:
            self._access.task_for_member(actor, attachment.task_id)
        except NotFoundError:
            raise NotFoundError("Attachment") from None
        try:
            stream = self._storage.open(attachment.storage_key)
        except BlobNotFoundError:
            logger.error("attachment blob missing", extra={"attachment_id": str(attachment.id)})
            raise NotFoundError("Attachment") from None
        return attachment, stream
