from offer_codes.application.auth_service import AuthService
from offer_codes.domain.user import UserCredential


class MemoryUserRepository:
    def __init__(self, users: list[UserCredential]) -> None:
        self.users = users

    def load_all(self) -> list[UserCredential]:
        return list(self.users)


def test_auth_service_accepts_matching_user_and_password() -> None:
    service = AuthService(MemoryUserRepository([UserCredential("David", "david-sample")]))

    assert service.authenticate("David", "david-sample")


def test_auth_service_accepts_user_and_password_in_any_case() -> None:
    service = AuthService(MemoryUserRepository([UserCredential("David", "david-sample")]))

    assert service.authenticate("dAVid", "DAVID-SAMPLE")


def test_auth_service_returns_canonical_user_name() -> None:
    service = AuthService(MemoryUserRepository([UserCredential("David", "david-sample")]))

    assert service.authenticated_user("dAVid", "DAVID-SAMPLE") == "David"


def test_auth_service_rejects_wrong_password() -> None:
    service = AuthService(MemoryUserRepository([UserCredential("David", "david-sample")]))

    assert not service.authenticate("David", "wrong")
