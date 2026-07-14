"""Controller connecting the form to the application service."""

from dataclasses import dataclass
import threading

from offer_codes.application.android_tester_service import AndroidTesterService
from offer_codes.application.email_sender import EmailCancelledError, EmailSendError
from offer_codes.application.offer_code_email_service import OfferCodeEmailService
from offer_codes.application.offer_code_service import OfferCodeService
from offer_codes.domain.errors import DuplicateU3ANumberError, InvalidDeviceTypeError, NoAvailableOfferCodeError
from offer_codes.domain.models import AndroidTesterRecord, OfferCodeRecord
from offer_codes.domain.rules import OfferCodeRules
from offer_codes.ui.message_effects import MessageEffects


@dataclass(frozen=True)
class SaveOutcome:
    record: OfferCodeRecord | AndroidTesterRecord | None
    error_title: str = ""
    error_message: str = ""
    dry_run: bool = True
    android_tester: bool = False
    simulated: bool = False

    @property
    def succeeded(self) -> bool:
        return self.record is not None or self.simulated


class OfferCodeController:
    def __init__(
        self,
        service: OfferCodeService,
        android_service: AndroidTesterService,
        email_service: OfferCodeEmailService,
        effects: MessageEffects,
    ) -> None:
        self._service = service
        self._android_service = android_service
        self._email_service = email_service
        self._effects = effects
        self._current: OfferCodeRecord | None = None
        self._previewed_offer_numbers: set[str] = set()

    def load_next(self) -> OfferCodeRecord | None:
        records = self._remaining_preview_records()
        if records:
            self._current = records[0]
            return self._current
        self._current = None
        self._effects.show_info("No offer codes", "No unissued offer codes are available.")
        return None

    def remaining_count(self) -> int:
        return len(self._remaining_preview_records())

    def can_save(self, U3A_number: str, first_name: str, last_name: str, email: str, device_type: str) -> bool:
        return self._service.can_save(U3A_number, first_name, last_name, email, device_type)

    def device_types(self) -> tuple[str, ...]:
        return self._service.device_types()

    def default_issued_date(self) -> str:
        return self._service.default_issued_date()

    def save(
        self,
        U3A_number: str,
        first_name: str,
        last_name: str,
        email: str,
        device_type: str,
        issued: str,
        dry_run: bool,
        cancel_event: threading.Event | None = None,
    ) -> SaveOutcome:
        device_error = self._validate_device_type(device_type)
        if device_error is not None:
            return device_error
        if self._is_android(device_type):
            if dry_run:
                return self._send_android_closed_test_email(email, cancel_event)
            if self._is_cancelled(cancel_event):
                return SaveOutcome(record=None)
            return self._send_android_email_and_register_tester(
                U3A_number, first_name, last_name, email, issued, cancel_event
            )
        if self._current is None:
            return SaveOutcome(record=None, error_title="Save failed", error_message="No offer code is loaded.")
        if not dry_run:
            validation_error = self._validate_real_issue(self._current.offer_number, U3A_number, device_type)
            if validation_error is not None:
                return validation_error
        if dry_run:
            if self._is_cancelled(cancel_event):
                return SaveOutcome(record=None)
            self._previewed_offer_numbers.add(self._current.offer_number)
            return SaveOutcome(record=self._current, dry_run=True, simulated=True)
        try:
            self._email_service.send_offer_code(
                self._service.normalized_email(email), self._current.offer_number, cancel_event
            )
            if self._is_cancelled(cancel_event):
                return SaveOutcome(record=None)
        except EmailCancelledError:
            return SaveOutcome(record=None)
        except EmailSendError as exc:
            return SaveOutcome(record=None, error_title="Email failed", error_message=str(exc))
        return self._issue_current_offer_code(U3A_number, first_name, last_name, email, device_type, issued, cancel_event)

    def _validate_device_type(self, device_type: str) -> SaveOutcome | None:
        try:
            self._service.validate_device_type(device_type)
            return None
        except InvalidDeviceTypeError as exc:
            return SaveOutcome(record=None, error_title="Invalid device type", error_message=str(exc))

    def _validate_real_issue(self, offer_number: str, U3A_number: str, device_type: str) -> SaveOutcome | None:
        try:
            self._service.validate_assignment(offer_number, U3A_number, device_type)
            return None
        except DuplicateU3ANumberError as exc:
            return SaveOutcome(record=None, error_title="Duplicate U3A number", error_message=str(exc))
        except InvalidDeviceTypeError as exc:
            return SaveOutcome(record=None, error_title="Invalid device type", error_message=str(exc))
        except NoAvailableOfferCodeError as exc:
            return SaveOutcome(record=None, error_title="Save failed", error_message=str(exc))

    def _issue_current_offer_code(
        self,
        U3A_number: str,
        first_name: str,
        last_name: str,
        email: str,
        device_type: str,
        issued: str,
        cancel_event: threading.Event | None,
    ) -> SaveOutcome:
        if self._is_cancelled(cancel_event):
            return SaveOutcome(record=None)
        try:
            self._current = self._service.assign_current(
                self._current.offer_number, U3A_number, first_name, last_name, email, device_type, issued
            )
        except DuplicateU3ANumberError as exc:
            return SaveOutcome(record=None, error_title="Duplicate U3A number", error_message=str(exc))
        except InvalidDeviceTypeError as exc:
            return SaveOutcome(record=None, error_title="Invalid device type", error_message=str(exc))
        except NoAvailableOfferCodeError as exc:
            return SaveOutcome(record=None, error_title="Save failed", error_message=str(exc))
        return SaveOutcome(record=self._current, dry_run=False)

    def _register_android_tester(
        self,
        U3A_number: str,
        first_name: str,
        last_name: str,
        email: str,
        issued: str,
        cancel_event: threading.Event | None,
    ) -> SaveOutcome:
        if self._is_cancelled(cancel_event):
            return SaveOutcome(record=None)
        try:
            record = self._android_service.register(U3A_number, first_name, last_name, email, issued)
        except InvalidDeviceTypeError as exc:
            return SaveOutcome(record=None, error_title="Invalid device type", error_message=str(exc))
        return SaveOutcome(record=record, dry_run=False, android_tester=True)

    def _send_android_email_and_register_tester(
        self,
        U3A_number: str,
        first_name: str,
        last_name: str,
        email: str,
        issued: str,
        cancel_event: threading.Event | None,
    ) -> SaveOutcome:
        try:
            self._email_service.send_android_closed_test_email(self._service.normalized_email(email), cancel_event)
            if self._is_cancelled(cancel_event):
                return SaveOutcome(record=None)
        except EmailCancelledError:
            return SaveOutcome(record=None)
        except EmailSendError as exc:
            return SaveOutcome(record=None, error_title="Email failed", error_message=str(exc))
        return self._register_android_tester(U3A_number, first_name, last_name, email, issued, cancel_event)

    def _send_android_closed_test_email(self, email: str, cancel_event: threading.Event | None) -> SaveOutcome:
        try:
            self._email_service.send_android_closed_test_email(self._service.normalized_email(email), cancel_event)
            if self._is_cancelled(cancel_event):
                return SaveOutcome(record=None)
        except EmailCancelledError:
            return SaveOutcome(record=None)
        except EmailSendError as exc:
            return SaveOutcome(record=None, error_title="Email failed", error_message=str(exc))
        return SaveOutcome(record=None, dry_run=True, android_tester=True, simulated=True)

    def show_save_error(self, outcome: SaveOutcome) -> None:
        self._effects.show_error(outcome.error_title, outcome.error_message)

    def cancel_active_save(self) -> None:
        self._email_service.cancel_active_send()

    def _remaining_preview_records(self) -> list[OfferCodeRecord]:
        return [
            record
            for record in self._service.available_records()
            if record.offer_number not in self._previewed_offer_numbers
        ]

    def _is_android(self, device_type: str) -> bool:
        return OfferCodeRules.normalize_device_type(device_type) == "Android"

    def _is_cancelled(self, cancel_event: threading.Event | None) -> bool:
        return cancel_event is not None and cancel_event.is_set()
