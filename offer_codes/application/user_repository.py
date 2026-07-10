"""Repository interface for login users."""

from typing import Protocol

from offer_codes.domain.user import UserCredential


class UserRepository(Protocol):
    def load_all(self) -> list[UserCredential]:
        ...
