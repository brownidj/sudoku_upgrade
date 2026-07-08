"""Controller connecting the form to the application service."""

from offer_codes.application.offer_code_service import OfferCodeService
from offer_codes.domain.errors import NoAvailableOfferCodeError
from offer_codes.domain.models import OfferCodeRecord
from offer_codes.ui.message_effects import MessageEffects


class OfferCodeController:
    def __init__(self, service: OfferCodeService, effects: MessageEffects) -> None:
        self._service = service
        self._effects = effects
        self._current: OfferCodeRecord | None = None

    def load_next(self) -> OfferCodeRecord | None:
        try:
            self._current = self._service.next_available()
            return self._current
        except NoAvailableOfferCodeError as exc:
            self._current = None
            self._effects.show_info("No offer codes", str(exc))
            return None

    def can_save(self, U3A_number: str, email: str) -> bool:
        return self._service.can_save(U3A_number, email)

    def save(self, U3A_number: str, email: str) -> OfferCodeRecord | None:
        if self._current is None:
            self._effects.show_error("Save failed", "No offer code is loaded.")
            return None
        try:
            completed = self._service.assign_current(self._current.offer_number, U3A_number, email)
            self._current = completed
            return completed
        except NoAvailableOfferCodeError as exc:
            self._effects.show_error("Save failed", str(exc))
            return None
