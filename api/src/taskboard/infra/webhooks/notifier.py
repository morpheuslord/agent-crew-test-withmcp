"""Asynchronous, best-effort webhook delivery."""

import hashlib
import hmac
import json
import logging
import time
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from typing import Final, Protocol

import httpx

from taskboard.domain.entities import StatusChangedEvent
from taskboard.domain.errors import ValidationFailedError
from taskboard.infra.webhooks.url_policy import WebhookUrlPolicy
from taskboard.logging_setup import request_id_var

logger = logging.getLogger("taskboard.webhooks")

MAX_RESPONSE_BYTES: Final = 64 * 1024


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
    ) -> None:
        self._policy = policy
        self._secret = signing_secret
        self._timeout = timeout_seconds
        self._max_attempts = max_attempts
        self._backoff = backoff_seconds
        self._executor = executor or ThreadPoolExecutor(max_workers=4, thread_name_prefix="webhook")
        self._client_factory = client_factory or self._default_client

    def _default_client(self) -> httpx.Client:
        # verify=True (default), no redirects, short timeouts, no proxies from the environment.
        return httpx.Client(
            timeout=httpx.Timeout(self._timeout),
            follow_redirects=False,
            trust_env=False,
        )

    def notify(self, url: str, event: StatusChangedEvent) -> None:
        request_id = request_id_var.get()
        self._executor.submit(self._deliver, url, event, request_id)

    def shutdown(self) -> None:
        self._executor.shutdown(wait=False, cancel_futures=True)

    def sign(self, body: bytes) -> str:
        return "sha256=" + hmac.new(self._secret, body, hashlib.sha256).hexdigest()

    def _deliver(self, url: str, event: StatusChangedEvent, request_id: str) -> None:
        token = request_id_var.set(request_id)
        try:
            body = json.dumps(event.to_payload(), separators=(",", ":")).encode()
            for attempt in range(1, self._max_attempts + 1):
                if self._attempt(url, body, attempt):
                    return
                if attempt < self._max_attempts:
                    time.sleep(self._backoff * 2 ** (attempt - 1))
            logger.warning("webhook delivery gave up", extra={"task_id": str(event.task_id)})
        finally:
            request_id_var.reset(token)

    def _attempt(self, url: str, body: bytes, attempt: int) -> bool:
        try:
            target = self._policy.resolve(url)
        except ValidationFailedError as exc:
            logger.warning("webhook target rejected", extra={"reason": exc.message})
            return True  # Not retryable: the destination is not allowed.
        headers = {
            "Host": target.host_header,
            "Content-Type": "application/json",
            "User-Agent": "Taskboard-Webhook/1.0",
            "X-Taskboard-Signature": self.sign(body),
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
                received = 0
                for chunk in response.iter_bytes():
                    received += len(chunk)
                    if received > MAX_RESPONSE_BYTES:
                        break
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
