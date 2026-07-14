import threading

from offer_codes.application.email_sender import EmailSendError
from offer_codes.application.android_tester_service import AndroidTesterService
from offer_codes.application.offer_code_service import OfferCodeService
from offer_codes.domain.models import AndroidTesterRecord, OfferCodeRecord
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


class MemoryAndroidTesterRepository:
    def __init__(self, records: list[AndroidTesterRecord] | None = None) -> None:
        self.records = records or [AndroidTesterRecord("", "", "", "", "Android", "")]
        self.save_calls = 0

    def load_all(self) -> list[AndroidTesterRecord]:
        return list(self.records)

    def save_all(self, records: list[AndroidTesterRecord]) -> None:
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
        self.sent_offer_codes: list[tuple[str, str]] = []
        self.sent_android_closed_test_emails: list[str] = []
        self.cancel_calls = 0

    def send_offer_code(self, to_email: str, offer_number: str, cancel_event: threading.Event | None = None) -> None:
        if self.should_fail:
            raise EmailSendError("send failed")
        self.sent_offer_codes.append((to_email, offer_number))

    def send_android_closed_test_email(self, to_email: str, cancel_event: threading.Event | None = None) -> None:
        if self.should_fail:
            raise EmailSendError("send failed")
        self.sent_android_closed_test_emails.append(to_email)

    def cancel_active_send(self) -> None:
        self.cancel_calls += 1


def make_controller(
    service: OfferCodeService,
    email_service: FakeEmailService | None = None,
    effects: StubEffects | None = None,
    android_repository: MemoryAndroidTesterRepository | None = None,
) -> tuple[OfferCodeController, MemoryAndroidTesterRepository, FakeEmailService, StubEffects]:
    android_repository = android_repository or MemoryAndroidTesterRepository()
    email_service = email_service or FakeEmailService()
    effects = effects or StubEffects()
    controller = OfferCodeController(
        service,
        AndroidTesterService(android_repository, FixedDateProvider()),
        email_service,
        effects,
    )
    return controller, android_repository, email_service, effects


def test_save_is_temporary_dry_run_and_advances_session() -> None:
    repository = MemoryRepository(
        [
            OfferCodeRecord("", "", "FIRST", ""),
            OfferCodeRecord("", "", "SECOND", ""),
        ]
    )
    service = OfferCodeService(repository, FixedDateProvider())
    controller, android_repository, email_service, _effects = make_controller(service)

    assert controller.load_next().offer_number == "FIRST"
    assert controller.remaining_count() == 2

    outcome = controller.save("U3A-001", "Ada", "Lovelace", "PERSON@Example.COM", "iPhone", "2026-07-09", dry_run=True)

    assert outcome.succeeded
    assert outcome.dry_run
    assert outcome.simulated
    assert outcome.record.offer_number == "FIRST"
    assert email_service.sent_offer_codes == []
    assert email_service.sent_android_closed_test_emails == []
    assert android_repository.save_calls == 0
    assert repository.save_calls == 0
    assert repository.records[0] == OfferCodeRecord("", "", "FIRST", "")
    assert controller.load_next().offer_number == "SECOND"
    assert controller.remaining_count() == 1


def test_controller_exposes_default_issued_date() -> None:
    repository = MemoryRepository([OfferCodeRecord("", "", "FIRST", "")])
    service = OfferCodeService(repository, FixedDateProvider())
    controller, _android_repository, _email_service, _effects = make_controller(service)

    assert controller.default_issued_date() == "2026-07-09"


def test_cancelled_dry_run_does_not_advance_or_send() -> None:
    repository = MemoryRepository([OfferCodeRecord("", "", "FIRST", ""), OfferCodeRecord("", "", "SECOND", "")])
    service = OfferCodeService(repository, FixedDateProvider())
    controller, android_repository, email_service, _effects = make_controller(service)
    cancel_event = threading.Event()

    assert controller.load_next().offer_number == "FIRST"
    cancel_event.set()
    outcome = controller.save("U3A-001", "Ada", "Lovelace", "person@example.com", "iPhone", "2026-07-09", dry_run=True, cancel_event=cancel_event)

    assert not outcome.succeeded
    assert email_service.sent_offer_codes == []
    assert email_service.sent_android_closed_test_emails == []
    assert android_repository.save_calls == 0
    assert repository.save_calls == 0
    assert controller.load_next().offer_number == "FIRST"


def test_failed_email_does_not_save_real_issue() -> None:
    repository = MemoryRepository([OfferCodeRecord("", "", "FIRST", "")])
    service = OfferCodeService(repository, FixedDateProvider())
    effects = StubEffects()
    controller, _android_repository, _email_service, _effects = make_controller(
        service, email_service=FakeEmailService(should_fail=True), effects=effects
    )

    assert controller.load_next().offer_number == "FIRST"

    outcome = controller.save("U3A-001", "Ada", "Lovelace", "person@example.com", "iPhone", "2026-07-09", dry_run=False)

    assert not outcome.succeeded
    assert repository.save_calls == 0
    assert controller.load_next().offer_number == "FIRST"
    controller.show_save_error(outcome)
    assert effects.errors == [("Email failed", "send failed")]


def test_real_issue_sends_email_and_saves_record() -> None:
    repository = MemoryRepository([OfferCodeRecord("", "", "FIRST", "")])
    service = OfferCodeService(repository, FixedDateProvider())
    controller, _android_repository, email_service, _effects = make_controller(service)

    assert controller.load_next().offer_number == "FIRST"

    outcome = controller.save("U3A-001", "aDA", "LOVELACE", "PERSON@Example.COM", "iPhone", "2026-07-10", dry_run=False)

    assert outcome.succeeded
    assert not outcome.dry_run
    assert email_service.sent_offer_codes == [("person@example.com", "FIRST")]
    assert email_service.sent_android_closed_test_emails == []
    assert repository.save_calls == 1
    assert repository.records == [
        OfferCodeRecord("U3A-001", "person@example.com", "FIRST", "2026-07-10", "Ada", "Lovelace", "iPhone")
    ]


def test_real_issue_duplicate_U3A_number_does_not_send_email() -> None:
    repository = MemoryRepository(
        [
            OfferCodeRecord("U3A-001", "used@example.com", "USED", "2026-07-09"),
            OfferCodeRecord("", "", "FIRST", ""),
        ]
    )
    service = OfferCodeService(repository, FixedDateProvider())
    controller, _android_repository, email_service, _effects = make_controller(service)

    assert controller.load_next().offer_number == "FIRST"

    outcome = controller.save("U3A-001", "Ada", "Lovelace", "person@example.com", "iPhone", "2026-07-10", dry_run=False)

    assert not outcome.succeeded
    assert outcome.error_title == "Duplicate U3A number"
    assert email_service.sent_offer_codes == []
    assert email_service.sent_android_closed_test_emails == []
    assert repository.save_calls == 0


def test_invalid_device_type_does_not_send_email() -> None:
    repository = MemoryRepository([OfferCodeRecord("", "", "FIRST", "")])
    service = OfferCodeService(repository, FixedDateProvider())
    controller, _android_repository, email_service, _effects = make_controller(service)

    assert controller.load_next().offer_number == "FIRST"

    outcome = controller.save("U3A-001", "Ada", "Lovelace", "person@example.com", "Windows", "2026-07-10", dry_run=True)

    assert not outcome.succeeded
    assert outcome.error_title == "Invalid device type"
    assert email_service.sent_offer_codes == []
    assert email_service.sent_android_closed_test_emails == []
    assert repository.save_calls == 0


def test_android_dry_run_sends_email_without_saving_data() -> None:
    repository = MemoryRepository([OfferCodeRecord("", "", "FIRST", "")])
    service = OfferCodeService(repository, FixedDateProvider())
    controller, android_repository, email_service, _effects = make_controller(service)

    assert controller.load_next().offer_number == "FIRST"

    outcome = controller.save("U3A-001", "aDA", "LOVELACE", "PERSON@Example.COM", "Android", "2026-07-10", dry_run=True)

    assert outcome.succeeded
    assert outcome.android_tester
    assert outcome.dry_run
    assert outcome.record is None
    assert email_service.sent_offer_codes == []
    assert email_service.sent_android_closed_test_emails == ["person@example.com"]
    assert repository.save_calls == 0
    assert repository.records == [OfferCodeRecord("", "", "FIRST", "")]
    assert android_repository.save_calls == 0
    assert android_repository.records == [AndroidTesterRecord("", "", "", "", "Android", "")]


def test_android_send_email_records_tester_without_offer_code_assignment() -> None:
    repository = MemoryRepository([OfferCodeRecord("", "", "FIRST", "")])
    service = OfferCodeService(repository, FixedDateProvider())
    controller, android_repository, email_service, _effects = make_controller(service)

    assert controller.load_next().offer_number == "FIRST"

    outcome = controller.save("U3A-001", "aDA", "LOVELACE", "PERSON@Example.COM", "Android", "2026-07-10", dry_run=False)

    assert outcome.succeeded
    assert outcome.android_tester
    assert not outcome.dry_run
    assert email_service.sent_offer_codes == []
    assert email_service.sent_android_closed_test_emails == []
    assert repository.save_calls == 0
    assert repository.records == [OfferCodeRecord("", "", "FIRST", "")]
    assert android_repository.records == [
        AndroidTesterRecord("U3A-001", "person@example.com", "Ada", "Lovelace", "Android", "2026-07-10")
    ]


def test_android_save_does_not_require_loaded_offer_code() -> None:
    repository = MemoryRepository([])
    service = OfferCodeService(repository, FixedDateProvider())
    controller, android_repository, email_service, _effects = make_controller(service)

    outcome = controller.save("U3A-001", "Ada", "Lovelace", "person@example.com", "Android", "2026-07-10", dry_run=False)

    assert outcome.succeeded
    assert outcome.android_tester
    assert email_service.sent_offer_codes == []
    assert email_service.sent_android_closed_test_emails == []
    assert android_repository.records == [
        AndroidTesterRecord("U3A-001", "person@example.com", "Ada", "Lovelace", "Android", "2026-07-10")
    ]


def test_cancel_active_save_delegates_to_email_service() -> None:
    repository = MemoryRepository([OfferCodeRecord("", "", "FIRST", "")])
    service = OfferCodeService(repository, FixedDateProvider())
    controller, _android_repository, email_service, _effects = make_controller(service)

    controller.cancel_active_save()

    assert email_service.cancel_calls == 1
