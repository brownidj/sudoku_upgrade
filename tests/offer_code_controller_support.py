import threading

from offer_codes.application.android_tester_service import AndroidTesterService
from offer_codes.application.email_sender import EmailSendError
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
