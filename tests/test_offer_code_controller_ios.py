import threading

from offer_codes.application.offer_code_service import OfferCodeService
from offer_codes.domain.models import OfferCodeRecord
from tests.offer_code_controller_support import (
    FakeEmailService,
    FixedDateProvider,
    MemoryRepository,
    StubEffects,
    make_controller,
)


def test_save_is_temporary_dry_run_and_advances_session() -> None:
    repository = MemoryRepository(
        [OfferCodeRecord("", "", "FIRST", ""), OfferCodeRecord("", "", "SECOND", "")]
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
    outcome = controller.save(
        "U3A-001", "Ada", "Lovelace", "person@example.com", "iPhone", "2026-07-09", dry_run=True, cancel_event=cancel_event
    )

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
        [OfferCodeRecord("U3A-001", "used@example.com", "USED", "2026-07-09"), OfferCodeRecord("", "", "FIRST", "")]
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
