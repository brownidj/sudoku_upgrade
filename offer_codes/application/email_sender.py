"""Email sender interface used by application services."""

from dataclasses import dataclass
import threading
from typing import Protocol


class EmailSendError(Exception):
    """Raised when an email could not be sent."""


class EmailCancelledError(EmailSendError):
    """Raised when an email send is cancelled."""


@dataclass(frozen=True)
class EmailRequest:
    to_email: str
    subject: str
    body: str


class EmailSender(Protocol):
    def send(self, request: EmailRequest, cancel_event: threading.Event | None = None) -> None:
        ...
