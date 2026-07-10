"""User credentials for simple local login."""

from dataclasses import dataclass


@dataclass(frozen=True)
class UserCredential:
    user: str
    password: str
