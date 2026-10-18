"""Structured JSON logging with a per-request id carried in a context variable."""

import json
import logging
import re
import uuid
from contextvars import ContextVar
from datetime import UTC, datetime
from typing import Any, Final

request_id_var: ContextVar[str] = ContextVar("request_id", default="-")

_REQUEST_ID_PATTERN: Final = re.compile(r"^[A-Za-z0-9-]{8,64}$")
_RESERVED: Final = frozenset(logging.LogRecord("", 0, "", 0, "", None, None).__dict__) | {
    "message",
    "asctime",
}


def accept_request_id(candidate: str | None) -> str:
    """Return the caller's request id if it is well formed, otherwise a fresh UUID."""
    if candidate and _REQUEST_ID_PATTERN.fullmatch(candidate):
        return candidate
    return str(uuid.uuid4())


class JsonFormatter(logging.Formatter):
    """Render each record as one JSON object, including any ``extra`` fields."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "ts": datetime.fromtimestamp(record.created, tz=UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
            "request_id": request_id_var.get(),
            "service": "api",
        }
        for key, value in record.__dict__.items():
            if key not in _RESERVED and not key.startswith("_"):
                payload[key] = value
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)


def configure_logging(level: str) -> None:
    """Install the JSON formatter on the root logger and align uvicorn's loggers with it."""
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers[:] = [handler]
    root.setLevel(level)
    for name in ("uvicorn", "uvicorn.error"):
        logger = logging.getLogger(name)
        logger.handlers[:] = []
        logger.propagate = True
    # The request middleware writes its own access line, with the request id.
    logging.getLogger("uvicorn.access").disabled = True
