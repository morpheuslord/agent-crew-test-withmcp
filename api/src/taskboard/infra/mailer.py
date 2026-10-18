"""Mailer interface and the development implementation that writes to the log and outbox."""

import logging
from typing import Protocol

from taskboard.domain.errors import ValidationFailedError
from taskboard.repositories.interfaces import OutboxRepository

logger = logging.getLogger("taskboard.mail")


class Mailer(Protocol):
    def send(self, to_email: str, subject: str, body: str) -> None: ...


def _check_header(value: str, name: str) -> None:
    """Reject CR/LF so a value can never add headers or recipients in a real mailer."""
    if "\r" in value or "\n" in value:
        raise ValidationFailedError(f"Invalid characters in email {name}.")


class LogOutboxMailer:
    """There is no real email provider: emails go to the API log and the ``outbox`` table.

    The brief requires the log copy so emails can be read in development. A production mailer would
    implement the same interface and must not log message bodies.
    """

    def __init__(self, outbox: OutboxRepository) -> None:
        self._outbox = outbox

    def send(self, to_email: str, subject: str, body: str) -> None:
        _check_header(to_email, "recipient")
        _check_header(subject, "subject")
        message = self._outbox.add(to_email, subject, body)
        logger.info(
            "outgoing email",
            extra={"mail_id": str(message.id), "to": to_email, "subject": subject, "body": body},
        )
