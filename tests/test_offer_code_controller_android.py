from offer_codes.application.offer_code_service import OfferCodeService
from offer_codes.domain.models import AndroidTesterRecord, OfferCodeRecord
from tests.offer_code_controller_support import (
    FakeEmailService,
    FixedDateProvider,
    MemoryRepository,
    StubEffects,
    make_controller,
)


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
    assert email_service.sent_android_closed_test_emails == ["person@example.com"]
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
    assert email_service.sent_android_closed_test_emails == ["person@example.com"]
    assert android_repository.records == [
        AndroidTesterRecord("U3A-001", "person@example.com", "Ada", "Lovelace", "Android", "2026-07-10")
    ]


def test_failed_android_email_does_not_save_tester() -> None:
    repository = MemoryRepository([OfferCodeRecord("", "", "FIRST", "")])
    service = OfferCodeService(repository, FixedDateProvider())
    effects = StubEffects()
    controller, android_repository, email_service, _effects = make_controller(
        service, email_service=FakeEmailService(should_fail=True), effects=effects
    )

    outcome = controller.save("U3A-001", "Ada", "Lovelace", "person@example.com", "Android", "2026-07-10", dry_run=False)

    assert not outcome.succeeded
    assert outcome.error_title == "Email failed"
    assert email_service.sent_offer_codes == []
    assert email_service.sent_android_closed_test_emails == []
    assert android_repository.save_calls == 0
    assert android_repository.records == [AndroidTesterRecord("", "", "", "", "Android", "")]


def test_cancel_active_save_delegates_to_email_service() -> None:
    repository = MemoryRepository([OfferCodeRecord("", "", "FIRST", "")])
    service = OfferCodeService(repository, FixedDateProvider())
    controller, _android_repository, email_service, _effects = make_controller(service)

    controller.cancel_active_save()

    assert email_service.cancel_calls == 1
