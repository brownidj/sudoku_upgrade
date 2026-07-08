"""Application service for assigning offer codes."""

from offer_codes.application.clock import DateProvider
from offer_codes.application.repositories import OfferCodeRepository
from offer_codes.domain.errors import NoAvailableOfferCodeError
from offer_codes.domain.models import OfferCodeRecord
from offer_codes.domain.rules import OfferCodeRules


class OfferCodeService:
    def __init__(self, repository: OfferCodeRepository, date_provider: DateProvider) -> None:
        self._repository = repository
        self._date_provider = date_provider

    def next_available(self) -> OfferCodeRecord:
        records = self._repository.load_all()
        for record in records:
            if OfferCodeRules.is_available(record):
                return record
        raise NoAvailableOfferCodeError("No unissued offer codes are available.")

    def can_save(self, U3A_number: str, email: str) -> bool:
        return OfferCodeRules.can_issue(U3A_number, email)

    def assign_current(self, offer_number: str, U3A_number: str, email: str) -> OfferCodeRecord:
        records = self._repository.load_all()
        for index, record in enumerate(records):
            if record.offer_number == offer_number:
                completed = OfferCodeRules.complete(
                    record=record,
                    U3A_number=U3A_number,
                    email=email,
                    issued=self._date_provider.today_iso(),
                )
                records[index] = completed
                self._repository.save_all(records)
                return completed
        raise NoAvailableOfferCodeError(f"Offer code {offer_number} was not found.")
