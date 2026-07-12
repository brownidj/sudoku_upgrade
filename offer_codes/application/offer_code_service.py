"""Application service for assigning offer codes."""

from offer_codes.application.clock import DateProvider
from offer_codes.application.repositories import OfferCodeRepository
from offer_codes.domain.errors import DuplicateU3ANumberError, InvalidDeviceTypeError, NoAvailableOfferCodeError
from offer_codes.domain.models import OfferCodeRecord
from offer_codes.domain.rules import OfferCodeRules


class OfferCodeService:
    def __init__(self, repository: OfferCodeRepository, date_provider: DateProvider) -> None:
        self._repository = repository
        self._date_provider = date_provider

    def next_available(self) -> OfferCodeRecord:
        for record in self.available_records():
            if OfferCodeRules.is_available(record):
                return record
        raise NoAvailableOfferCodeError("No unissued offer codes are available.")

    def available_records(self) -> list[OfferCodeRecord]:
        records = self._repository.load_all()
        return [record for record in records if OfferCodeRules.is_available(record)]

    def can_save(self, U3A_number: str, first_name: str, last_name: str, email: str, device_type: str) -> bool:
        return OfferCodeRules.can_issue(U3A_number, first_name, last_name, email, device_type)

    def default_issued_date(self) -> str:
        return self._date_provider.today_iso()

    def normalized_email(self, email: str) -> str:
        return OfferCodeRules.normalize_email(email)

    def device_types(self) -> tuple[str, ...]:
        return OfferCodeRules.ALLOWED_DEVICE_TYPES

    def validate_device_type(self, device_type: str) -> None:
        self._ensure_device_type_is_valid(device_type)

    def assign_current(
        self,
        offer_number: str,
        U3A_number: str,
        first_name: str,
        last_name: str,
        email: str,
        device_type: str,
        issued: str | None = None,
    ) -> OfferCodeRecord:
        records = self._repository.load_all()
        self.validate_assignment(offer_number, U3A_number, device_type)
        for index, record in enumerate(records):
            if record.offer_number == offer_number:
                completed = OfferCodeRules.complete(
                    record=record,
                    U3A_number=U3A_number,
                    first_name=first_name,
                    last_name=last_name,
                    email=email,
                    device_type=device_type,
                    issued=issued or self.default_issued_date(),
                )
                records[index] = completed
                self._repository.save_all(records)
                return completed
        raise NoAvailableOfferCodeError(f"Offer code {offer_number} was not found.")

    def validate_assignment(self, offer_number: str, U3A_number: str, device_type: str) -> None:
        records = self._repository.load_all()
        self._ensure_offer_code_exists(records, offer_number)
        self.validate_device_type(device_type)
        self._ensure_U3A_number_is_unique(records, offer_number, U3A_number)

    def _ensure_offer_code_exists(self, records: list[OfferCodeRecord], offer_number: str) -> None:
        if not any(record.offer_number == offer_number for record in records):
            raise NoAvailableOfferCodeError(f"Offer code {offer_number} was not found.")

    def _ensure_U3A_number_is_unique(
        self, records: list[OfferCodeRecord], current_offer_number: str, U3A_number: str
    ) -> None:
        requested_U3A_number = U3A_number.strip()
        for record in records:
            if record.offer_number == current_offer_number:
                continue
            if record.U3A_number.strip() == requested_U3A_number and record.issued.strip():
                raise DuplicateU3ANumberError(
                    f"U3A number {requested_U3A_number} already has an issued offer code."
                )

    def _ensure_device_type_is_valid(self, device_type: str) -> None:
        if not OfferCodeRules.is_valid_device_type(device_type):
            allowed_device_types = " or ".join(OfferCodeRules.ALLOWED_DEVICE_TYPES)
            raise InvalidDeviceTypeError(f"Device type must be {allowed_device_types}.")
