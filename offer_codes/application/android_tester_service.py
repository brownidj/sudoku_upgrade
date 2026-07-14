"""Application service for Android tester registration."""

from offer_codes.application.clock import DateProvider
from offer_codes.application.repositories import AndroidTesterRepository
from offer_codes.domain.errors import InvalidDeviceTypeError
from offer_codes.domain.models import AndroidTesterRecord
from offer_codes.domain.rules import OfferCodeRules


class AndroidTesterService:
    def __init__(self, repository: AndroidTesterRepository, date_provider: DateProvider) -> None:
        self._repository = repository
        self._date_provider = date_provider

    def register(
        self, U3A_number: str, first_name: str, last_name: str, email: str, registered: str | None = None
    ) -> AndroidTesterRecord:
        records = self._repository.load_all()
        completed = AndroidTesterRecord(
            U3A_number=U3A_number.strip(),
            email=OfferCodeRules.normalize_email(email),
            first_name=OfferCodeRules.normalize_name(first_name),
            last_name=OfferCodeRules.normalize_name(last_name),
            device_type="Android",
            registered=registered or self._date_provider.today_iso(),
        )
        for index, record in enumerate(records):
            if self._is_available(record):
                records[index] = completed
                self._repository.save_all(records)
                return completed
        records.append(completed)
        self._repository.save_all(records)
        return completed

    def validate_device_type(self, device_type: str) -> None:
        if OfferCodeRules.normalize_device_type(device_type) != "Android":
            raise InvalidDeviceTypeError("Device type must be Android.")

    def _is_available(self, record: AndroidTesterRecord) -> bool:
        return not record.U3A_number.strip() and not record.email.strip() and not record.registered.strip()
