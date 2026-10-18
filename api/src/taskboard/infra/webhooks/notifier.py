"""Asynchronous, best-effort webhook delivery."""

import hashlib
import hmac
import json
import logging
import threading
import time
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from typing import Final, Protocol
from uuid import UUID

import httpx

from taskboard.domain.entities import StatusChangedEvent
from taskboard.domain.errors import ValidationFailedError
from taskboard.infra.webhooks.url_policy import WebhookUrlPolicy
from taskboard.logging_setup import request_id_var

logger = logging.getLogger("taskboard.webhooks")

MAX_RESPONSE_BYTES: Final = 64 * 1024


def project_signing_key(secret: bytes, project_id: UUID) -> str:
    """Per-project key derived from the deployment secret.

    Each receiver gets a key that verifies only its own project's events, so it cannot forge events
    for other projects, and the deployment secret itself is never handed out.
    """
    return hmac.new(secret, f"project:{project_id}".encode(), hashlib.sha256).hexdigest()


class WebhookNotifier(Protocol):
    def notify(self, url: str, event: StatusChangedEvent) -> None:
        """Queue delivery and return immediately."""
        ...


class NullWebhookNotifier:
    def notify(self, url: str, event: StatusChangedEvent) -> None:
        return None


class HttpWebhookNotifier:
    """Delivers on a bounded thread pool, with bounded retries and SSRF checks on every attempt."""

    def __init__(
        self,
        *,
        policy: WebhookUrlPolicy,
        signing_secret: bytes,
        timeout_seconds: float,
        max_attempts: int,
        client_factory: Callable[[], httpx.Client] | None = None,
        executor: ThreadPoolExecutor | None = None,
        backoff_seconds: float = 0.5,
        max_pending: int = 500,
    ) -> None:
        self._policy = policy
        self._secret = signing_secret
        self._timeout = timeout_seconds
        self._max_attempts = max_attempts
        self._backoff = backoff_seconds
        self._executor = executor or ThreadPoolExecutor(max_workers=4, thread_name_prefix="webhook")
        self._client_factory = client_factory or self._default_client
        # The executor's queue is unbounded; this caps queued plus running deliveries.
        self._pending = threading.BoundedSemaphore(max_pending)

    def _default_client(self) -> httpx.Client:
        # verify=True (default), no redirects, short timeouts, no proxies from the environment.
        return httpx.Client(
            timeout=httpx.Timeout(self._timeout),
            follow_redirects=False,
            trust_env=False,
        )

    def notify(self, url: str, event: StatusChangedEvent) -> None:
        if not self._pending.acquire(blocking=False):
            logger.warning(
                "webhook backlog full, event dropped", extra={"task_id": str(event.task_id)}
            )
            return
        request_id = request_id_var.get()
        future = self._executor.submit(self._deliver, url, event, request_id)
        future.add_done_callback(lambda _: self._pending.release())

    def shutdown(self) -> None:
        self._executor.shutdown(wait=False, cancel_futures=True)

    def signing_key_for(self, project_id: UUID) -> str:
        return project_signing_key(self._secret, project_id)

    @staticmethod
    def sign(body: bytes, key: str) -> str:
        return "sha256=" + hmac.new(key.encode(), body, hashlib.sha256).hexdigest()

    def _deliver(self, url: str, event: StatusChangedEvent, request_id: str) -> None:
        token = request_id_var.set(request_id)
        try:
            body = json.dumps(event.to_payload(), separators=(",", ":")).encode()
            key = self.signing_key_for(event.project_id)
            for attempt in range(1, self._max_attempts + 1):
                if self._attempt(url, body, key, attempt):
                    return
                if attempt < self._max_attempts:
                    time.sleep(self._backoff * 2 ** (attempt - 1))
            logger.warning("webhook delivery gave up", extra={"task_id": str(event.task_id)})
        finally:
            request_id_var.reset(token)

    def _attempt(self, url: str, body: bytes, key: str, attempt: int) -> bool:
        try:
            target = self._policy.resolve(url)
        except ValidationFailedError as exc:
            logger.warning("webhook target rejected", extra={"reason": exc.message})
            return True  # Not retryable: the destination is not allowed.
        headers = {
            "Host": target.host_header,
            "Content-Type": "application/json",
            "User-Agent": "Taskboard-Webhook/1.0",
            "X-Taskboard-Signature": self.sign(body, key),
        }
        extensions = {"sni_hostname": target.host} if target.scheme == "https" else {}
        try:
            with (
                self._client_factory() as client,
                client.stream(
                    "POST",
                    target.connect_url,
                    content=body,
                    headers=headers,
                    extensions=extensions,
                ) as response,
            ):
                # Per-read timeouts alone let a slow-drip receiver hold a worker indefinitely.
                deadline = time.monotonic() + 2 * self._timeout
                received = 0
                for chunk in response.iter_bytes():
                    received += len(chunk)
                    if received > MAX_RESPONSE_BYTES:
                        break
                    if time.monotonic() > deadline:
                        logger.info("webhook attempt timed out", extra={"attempt": attempt})
                        return False
                ok = 200 <= response.status_code < 300
                logger.info(
                    "webhook delivered" if ok else "webhook rejected by receiver",
                    extra={"status": response.status_code, "attempt": attempt},
                )
                return ok
        except httpx.HTTPError as exc:
            logger.info(
                "webhook attempt failed", extra={"error": type(exc).__name__, "attempt": attempt}
            )
            return False
