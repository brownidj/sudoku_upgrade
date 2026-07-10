import pytest

from offer_codes.application.offer_code_service import OfferCodeService
from offer_codes.domain.errors import DuplicateU3ANumberError, NoAvailableOfferCodeError
from offer_codes.domain.models import OfferCodeRecord


class FixedDateProvider:
    def today_iso(self) -> str:
        return "2026-07-09"


class MemoryRepository:
    def __init__(self, records: list[OfferCodeRecord]) -> None:
        self.records = records

    def load_all(self) -> list[OfferCodeRecord]:
        return list(self.records)

    def save_all(self, records: list[OfferCodeRecord]) -> None:
        self.records = list(records)


def test_next_available_returns_first_unissued_record() -> None:
    repository = MemoryRepository(
        [
            OfferCodeRecord("123", "used@example.com", "USED", "2026-07-08"),
            OfferCodeRecord("", "", "NEXT", ""),
        ]
    )
    service = OfferCodeService(repository, FixedDateProvider())

    record = service.next_available()

    assert record.offer_number == "NEXT"


def test_assign_current_sets_data_and_current_date() -> None:
    repository = MemoryRepository([OfferCodeRecord("", "", "NEXT", "")])
    service = OfferCodeService(repository, FixedDateProvider())

    saved = service.assign_current("NEXT", "  U3A-001  ", "  Ada  ", "  Lovelace  ", "  person@example.com  ")

    assert saved == OfferCodeRecord("U3A-001", "person@example.com", "NEXT", "2026-07-09", "Ada", "Lovelace")
    assert repository.records == [saved]


def test_assign_current_normalizes_names_and_email_before_saving() -> None:
    repository = MemoryRepository([OfferCodeRecord("", "", "NEXT", "")])
    service = OfferCodeService(repository, FixedDateProvider())

    saved = service.assign_current("NEXT", "U3A-001", "aDA", "LOVELACE", "PERSON@Example.COM")

    assert saved == OfferCodeRecord("U3A-001", "person@example.com", "NEXT", "2026-07-09", "Ada", "Lovelace")


def test_next_available_raises_when_all_records_are_issued() -> None:
    repository = MemoryRepository([OfferCodeRecord("123", "used@example.com", "USED", "2026-07-08")])
    service = OfferCodeService(repository, FixedDateProvider())

    with pytest.raises(NoAvailableOfferCodeError):
        service.next_available()


def test_assign_current_rejects_duplicate_U3A_number_from_saved_record() -> None:
    existing = OfferCodeRecord("U3A-001", "used@example.com", "USED", "2026-07-08")
    next_record = OfferCodeRecord("", "", "NEXT", "")
    repository = MemoryRepository([existing, next_record])
    service = OfferCodeService(repository, FixedDateProvider())

    with pytest.raises(DuplicateU3ANumberError):
        service.assign_current("NEXT", " U3A-001 ", "Ada", "Lovelace", "person@example.com")

    assert repository.records == [existing, next_record]


def test_assign_current_allows_duplicate_U3A_number_when_existing_record_is_not_issued() -> None:
    existing = OfferCodeRecord("U3A-001", "used@example.com", "USED", "")
    repository = MemoryRepository([existing, OfferCodeRecord("", "", "NEXT", "")])
    service = OfferCodeService(repository, FixedDateProvider())

    saved = service.assign_current("NEXT", "U3A-001", "Ada", "Lovelace", "person@example.com")

    assert saved == OfferCodeRecord("U3A-001", "person@example.com", "NEXT", "2026-07-09", "Ada", "Lovelace")
