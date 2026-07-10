"""Simple authentication service."""

from offer_codes.application.user_repository import UserRepository


class AuthService:
    def __init__(self, repository: UserRepository) -> None:
        self._repository = repository

    def authenticate(self, user: str, password: str) -> bool:
        requested_user = user.strip().casefold()
        requested_password = password.strip().casefold()
        for credential in self._repository.load_all():
            stored_user = credential.user.strip().casefold()
            stored_password = credential.password.strip().casefold()
            if stored_user == requested_user and stored_password == requested_password:
                return True
        return False
