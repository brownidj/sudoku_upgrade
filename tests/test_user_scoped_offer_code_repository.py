from offer_codes.domain.models import OfferCodeRecord
from offer_codes.infrastructure.user_scoped_offer_code_repository import UserScopedOfferCodeRepository


class MemoryOfferCodeRepository:
    def __init__(self, records: list[OfferCodeRecord]) -> None:
        self.records = records

    def load_all(self) -> list[OfferCodeRecord]:
        return list(self.records)

    def save_all(self, records: list[OfferCodeRecord]) -> None:
        self.records = list(records)


def _records(count: int = 150) -> list[OfferCodeRecord]:
    return [OfferCodeRecord("", "", f"CODE-{index:03}", "") for index in range(count)]


def test_user_scoped_repository_returns_david_first_50_records() -> None:
    repository = UserScopedOfferCodeRepository(MemoryOfferCodeRepository(_records()), "David")

    records = repository.load_all()

    assert len(records) == 50
    assert records[0].offer_number == "CODE-000"
    assert records[-1].offer_number == "CODE-049"


def test_user_scoped_repository_returns_mihoko_next_50_records() -> None:
    repository = UserScopedOfferCodeRepository(MemoryOfferCodeRepository(_records()), "Mihoko")

    records = repository.load_all()

    assert len(records) == 50
    assert records[0].offer_number == "CODE-050"
    assert records[-1].offer_number == "CODE-099"


def test_user_scoped_repository_returns_teruko_third_50_records() -> None:
    repository = UserScopedOfferCodeRepository(MemoryOfferCodeRepository(_records()), "Teruko")

    records = repository.load_all()

    assert len(records) == 50
    assert records[0].offer_number == "CODE-100"
    assert records[-1].offer_number == "CODE-149"


def test_user_scoped_repository_includes_external_issued_records_for_duplicate_checks() -> None:
    records = _records()
    records[5] = OfferCodeRecord("U3A-001", "used@example.com", "CODE-005", "2026-07-10")
    repository = UserScopedOfferCodeRepository(MemoryOfferCodeRepository(records), "Mihoko")

    loaded_records = repository.load_all()

    assert loaded_records[:50][0].offer_number == "CODE-050"
    assert loaded_records[-1].offer_number == "CODE-005"
