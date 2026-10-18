"""Attachment storage in Amazon S3 (AWS). Credentials come from the instance role."""

from collections.abc import Iterator
from typing import IO, TYPE_CHECKING

from taskboard.infra.storage.base import CHUNK_SIZE, BlobNotFoundError, check_key

if TYPE_CHECKING:
    from mypy_boto3_s3 import S3Client


class S3Storage:
    def __init__(self, client: "S3Client", bucket: str) -> None:
        self._client = client
        self._bucket = bucket

    def save(self, key: str, data: IO[bytes], size: int) -> None:
        self._client.put_object(
            Bucket=self._bucket,
            Key=check_key(key),
            Body=data,
            ContentLength=size,
            ContentType="application/octet-stream",
            ServerSideEncryption="aws:kms",
        )

    def open(self, key: str) -> Iterator[bytes]:
        try:
            response = self._client.get_object(Bucket=self._bucket, Key=check_key(key))
        except self._client.exceptions.NoSuchKey as exc:
            raise BlobNotFoundError(key) from exc
        body = response["Body"]

        def _chunks() -> Iterator[bytes]:
            try:
                yield from body.iter_chunks(CHUNK_SIZE)
            finally:
                body.close()

        return _chunks()

    def delete(self, key: str) -> None:
        self._client.delete_object(Bucket=self._bucket, Key=check_key(key))

    def check(self) -> None:
        self._client.head_bucket(Bucket=self._bucket)
