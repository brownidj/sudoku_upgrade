from offer_codes.application.email_sender import EmailSendError
from offer_codes.application.offer_code_service import OfferCodeService
from offer_codes.domain.models import OfferCodeRecord
from offer_codes.ui.offer_code_controller import OfferCodeController


class FixedDateProvider:
    def today_iso(self) -> str:
        return "2026-07-09"


class MemoryRepository:
    def __init__(self, records: list[OfferCodeRecord]) -> None:
        self.records = records
        self.save_calls = 0

    def load_all(self) -> list[OfferCodeRecord]:
        return list(self.records)

    def save_all(self, records: list[OfferCodeRecord]) -> None:
        self.save_calls += 1
        self.records = list(records)


class StubEffects:
    def __init__(self) -> None:
        self.errors: list[tuple[str, str]] = []
        self.infos: list[tuple[str, str]] = []

    def show_error(self, title: str, message: str) -> None:
        self.errors.append((title, message))

    def show_info(self, title: str, message: str) -> None:
        self.infos.append((title, message))


class FakeEmailService:
    def __init__(self, should_fail: bool = False) -> None:
        self.should_fail = should_fail
        self.sent: list[tuple[str, str]] = []

    def send_offer_code(self, to_email: str, offer_number: str) -> None:
        if self.should_fail:
            raise EmailSendError("send failed")
        self.sent.append((to_email, offer_number))


def test_save_is_temporary_dry_run_and_advances_session() -> None:
    repository = MemoryRepository(
        [
            OfferCodeRecord("", "", "FIRST", ""),
            OfferCodeRecord("", "", "SECOND", ""),
        ]
    )
    service = OfferCodeService(repository, FixedDateProvider())
    email_service = FakeEmailService()
    controller = OfferCodeController(service, email_service, StubEffects())

    assert controller.load_next().offer_number == "FIRST"
    assert controller.remaining_count() == 2

    outcome = controller.save("U3A-001", "Ada", "Lovelace", "PERSON@Example.COM", "2026-07-09", dry_run=True)

    assert outcome.succeeded
    assert outcome.dry_run
    assert outcome.record.offer_number == "FIRST"
    assert email_service.sent == [("person@example.com", "FIRST")]
    assert repository.save_calls == 0
    assert repository.records[0] == OfferCodeRecord("", "", "FIRST", "")
    assert controller.load_next().offer_number == "SECOND"
    assert controller.remaining_count() == 1


def test_controller_exposes_default_issued_date() -> None:
    repository = MemoryRepository([OfferCodeRecord("", "", "FIRST", "")])
    service = OfferCodeService(repository, FixedDateProvider())
    controller = OfferCodeController(service, FakeEmailService(), StubEffects())

    assert controller.default_issued_date() == "2026-07-09"


def test_failed_email_does_not_advance_dry_run_session() -> None:
    repository = MemoryRepository([OfferCodeRecord("", "", "FIRST", "")])
    service = OfferCodeService(repository, FixedDateProvider())
    effects = StubEffects()
    controller = OfferCodeController(service, FakeEmailService(should_fail=True), effects)

    assert controller.load_next().offer_number == "FIRST"

    outcome = controller.save("U3A-001", "Ada", "Lovelace", "person@example.com", "2026-07-09", dry_run=True)

    assert not outcome.succeeded
    assert repository.save_calls == 0
    assert controller.load_next().offer_number == "FIRST"
    controller.show_save_error(outcome)
    assert effects.errors == [("Email failed", "send failed")]


def test_real_issue_sends_email_and_saves_record() -> None:
    repository = MemoryRepository([OfferCodeRecord("", "", "FIRST", "")])
    service = OfferCodeService(repository, FixedDateProvider())
    email_service = FakeEmailService()
    controller = OfferCodeController(service, email_service, StubEffects())

    assert controller.load_next().offer_number == "FIRST"

    outcome = controller.save("U3A-001", "aDA", "LOVELACE", "PERSON@Example.COM", "2026-07-10", dry_run=False)

    assert outcome.succeeded
    assert not outcome.dry_run
    assert email_service.sent == [("person@example.com", "FIRST")]
    assert repository.save_calls == 1
    assert repository.records == [
        OfferCodeRecord("U3A-001", "person@example.com", "FIRST", "2026-07-10", "Ada", "Lovelace")
    ]


def test_real_issue_duplicate_U3A_number_does_not_send_email() -> None:
    repository = MemoryRepository(
        [
            OfferCodeRecord("U3A-001", "used@example.com", "USED", "2026-07-09"),
            OfferCodeRecord("", "", "FIRST", ""),
        ]
    )
    service = OfferCodeService(repository, FixedDateProvider())
    email_service = FakeEmailService()
    controller = OfferCodeController(service, email_service, StubEffects())

    assert controller.load_next().offer_number == "FIRST"

    outcome = controller.save("U3A-001", "Ada", "Lovelace", "person@example.com", "2026-07-10", dry_run=False)

    assert not outcome.succeeded
    assert outcome.error_title == "Duplicate U3A number"
    assert email_service.sent == []
    assert repository.save_calls == 0
