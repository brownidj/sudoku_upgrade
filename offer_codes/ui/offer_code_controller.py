"""Controller connecting the form to the application service."""

from dataclasses import dataclass

from offer_codes.application.email_sender import EmailSendError
from offer_codes.application.offer_code_email_service import OfferCodeEmailService
from offer_codes.application.offer_code_service import OfferCodeService
from offer_codes.domain.errors import DuplicateU3ANumberError, NoAvailableOfferCodeError
from offer_codes.domain.models import OfferCodeRecord
from offer_codes.ui.message_effects import MessageEffects


@dataclass(frozen=True)
class SaveOutcome:
    record: OfferCodeRecord | None
    error_title: str = ""
    error_message: str = ""
    dry_run: bool = True

    @property
    def succeeded(self) -> bool:
        return self.record is not None


class OfferCodeController:
    def __init__(
        self, service: OfferCodeService, email_service: OfferCodeEmailService, effects: MessageEffects
    ) -> None:
        self._service = service
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

    def can_save(self, U3A_number: str, first_name: str, last_name: str, email: str) -> bool:
        return self._service.can_save(U3A_number, first_name, last_name, email)

    def default_issued_date(self) -> str:
        return self._service.default_issued_date()

    def save(
        self, U3A_number: str, first_name: str, last_name: str, email: str, issued: str, dry_run: bool
    ) -> SaveOutcome:
        if self._current is None:
            return SaveOutcome(record=None, error_title="Save failed", error_message="No offer code is loaded.")
        if not dry_run:
            validation_error = self._validate_real_issue(self._current.offer_number, U3A_number)
            if validation_error is not None:
                return validation_error
        try:
            self._email_service.send_offer_code(self._service.normalized_email(email), self._current.offer_number)
        except EmailSendError as exc:
            return SaveOutcome(record=None, error_title="Email failed", error_message=str(exc))
        if dry_run:
            self._previewed_offer_numbers.add(self._current.offer_number)
            return SaveOutcome(record=self._current, dry_run=True)
        return self._issue_current_offer_code(U3A_number, first_name, last_name, email, issued)

    def _validate_real_issue(self, offer_number: str, U3A_number: str) -> SaveOutcome | None:
        try:
            self._service.validate_assignment(offer_number, U3A_number)
            return None
        except DuplicateU3ANumberError as exc:
            return SaveOutcome(record=None, error_title="Duplicate U3A number", error_message=str(exc))
        except NoAvailableOfferCodeError as exc:
            return SaveOutcome(record=None, error_title="Save failed", error_message=str(exc))

    def _issue_current_offer_code(
        self, U3A_number: str, first_name: str, last_name: str, email: str, issued: str
    ) -> SaveOutcome:
        try:
            self._current = self._service.assign_current(
                self._current.offer_number, U3A_number, first_name, last_name, email, issued
            )
        except DuplicateU3ANumberError as exc:
            return SaveOutcome(record=None, error_title="Duplicate U3A number", error_message=str(exc))
        except NoAvailableOfferCodeError as exc:
            return SaveOutcome(record=None, error_title="Save failed", error_message=str(exc))
        return SaveOutcome(record=self._current, dry_run=False)

    def show_save_error(self, outcome: SaveOutcome) -> None:
        self._effects.show_error(outcome.error_title, outcome.error_message)

    def _remaining_preview_records(self) -> list[OfferCodeRecord]:
        return [
            record
            for record in self._service.available_records()
            if record.offer_number not in self._previewed_offer_numbers
        ]
