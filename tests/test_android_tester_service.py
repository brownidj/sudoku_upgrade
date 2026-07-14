from offer_codes.application.android_tester_service import AndroidTesterService
from offer_codes.domain.models import AndroidTesterRecord


class FixedDateProvider:
    def today_iso(self) -> str:
        return "2026-07-10"


class MemoryAndroidTesterRepository:
    def __init__(self, records: list[AndroidTesterRecord]) -> None:
        self.records = records

    def load_all(self) -> list[AndroidTesterRecord]:
        return list(self.records)

    def save_all(self, records: list[AndroidTesterRecord]) -> None:
        self.records = list(records)


def test_android_tester_service_completes_first_blank_record() -> None:
    repository = MemoryAndroidTesterRepository([AndroidTesterRecord("", "", "", "", "Android", "")])
    service = AndroidTesterService(repository, FixedDateProvider())

    saved = service.register(" U3A-001 ", " aDA ", " LOVELACE ", " PERSON@Example.COM ")

    assert saved == AndroidTesterRecord("U3A-001", "person@example.com", "Ada", "Lovelace", "Android", "2026-07-10")
    assert repository.records == [saved]


def test_android_tester_service_appends_when_no_blank_record_exists() -> None:
    existing = AndroidTesterRecord("U3A-001", "used@example.com", "Used", "Person", "Android", "2026-07-09")
    repository = MemoryAndroidTesterRepository([existing])
    service = AndroidTesterService(repository, FixedDateProvider())

    saved = service.register("U3A-002", "Ada", "Lovelace", "person@example.com", "2026-07-11")

    assert repository.records == [
        existing,
        AndroidTesterRecord("U3A-002", "person@example.com", "Ada", "Lovelace", "Android", "2026-07-11"),
    ]
    assert saved == repository.records[-1]
