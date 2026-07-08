import pytest

from offer_codes.application.offer_code_service import OfferCodeService
from offer_codes.domain.errors import NoAvailableOfferCodeError
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

    saved = service.assign_current("NEXT", "  U3A-001  ", "  person@example.com  ")

    assert saved == OfferCodeRecord("U3A-001", "person@example.com", "NEXT", "2026-07-09")
    assert repository.records == [saved]


def test_next_available_raises_when_all_records_are_issued() -> None:
    repository = MemoryRepository([OfferCodeRecord("123", "used@example.com", "USED", "2026-07-08")])
    service = OfferCodeService(repository, FixedDateProvider())

    with pytest.raises(NoAvailableOfferCodeError):
        service.next_available()
