"""Email sender interface used by application services."""

from dataclasses import dataclass
from typing import Protocol


class EmailSendError(Exception):
    """Raised when an email could not be sent."""


@dataclass(frozen=True)
class EmailRequest:
    to_email: str
    subject: str
    body: str


class EmailSender(Protocol):
    def send(self, request: EmailRequest) -> None:
        ...
