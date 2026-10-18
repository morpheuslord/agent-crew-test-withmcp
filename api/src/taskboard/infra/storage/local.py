"""Attachment storage on a local filesystem volume (development)."""

import os
import shutil
import tempfile
from collections.abc import Iterator
from pathlib import Path
from typing import IO

from taskboard.infra.storage.base import CHUNK_SIZE, BlobNotFoundError, check_key


class LocalFileStorage:
    def __init__(self, root: str) -> None:
        self._root = Path(root).resolve()
        self._root.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        path = (self._root / check_key(key)).resolve()
        # Defence in depth: the key pattern already forbids traversal.
        if not path.is_relative_to(self._root):
            raise ValueError("storage key escapes the storage root")
        return path

    def save(self, key: str, data: IO[bytes], size: int) -> None:
        path = self._path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp_name = tempfile.mkstemp(dir=path.parent, prefix=".upload-")
        try:
            with os.fdopen(fd, "wb") as out:
                shutil.copyfileobj(data, out, CHUNK_SIZE)
            os.replace(tmp_name, path)
        except BaseException:
            Path(tmp_name).unlink(missing_ok=True)
            raise

    def open(self, key: str) -> Iterator[bytes]:
        path = self._path(key)
        try:
            handle = path.open("rb")
        except FileNotFoundError as exc:
            raise BlobNotFoundError(key) from exc

        def _chunks() -> Iterator[bytes]:
            with handle:
                while chunk := handle.read(CHUNK_SIZE):
                    yield chunk

        return _chunks()

    def delete(self, key: str) -> None:
        self._path(key).unlink(missing_ok=True)

    def check(self) -> None:
        if not os.access(self._root, os.W_OK):
            raise OSError("attachment storage is not writable")
