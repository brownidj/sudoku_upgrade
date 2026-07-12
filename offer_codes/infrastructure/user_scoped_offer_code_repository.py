"""User-scoped view of the shared offer-code YAML repository."""

from offer_codes.application.repositories import OfferCodeRepository
from offer_codes.domain.models import OfferCodeRecord


class UserOfferCodeScopeError(Exception):
    """Raised when offer codes cannot be scoped for a user."""


class UserScopedOfferCodeRepository:
    SLICE_SIZE = 50
    USER_OFFSETS = {
        "david": 0,
        "mihoko": 50,
        "teruko": 100,
    }

    def __init__(self, repository: OfferCodeRepository, user: str) -> None:
        self._repository = repository
        self._user = user

    def load_all(self) -> list[OfferCodeRecord]:
        records = self._repository.load_all()
        start = self._start_index()
        end = start + self.SLICE_SIZE
        scoped_records = records[start:end]
        issued_external_records = [
            record
            for index, record in enumerate(records)
            if not start <= index < end and record.U3A_number.strip() and record.issued.strip()
        ]
        return scoped_records + issued_external_records

    def save_all(self, records: list[OfferCodeRecord]) -> None:
        all_records = self._repository.load_all()
        start = self._start_index()
        end = start + self.SLICE_SIZE
        if len(all_records) < end:
            raise UserOfferCodeScopeError(f"Not enough offer-code records for {self._user}.")
        scoped_offer_numbers = {record.offer_number for record in all_records[start:end]}
        scoped_records = [record for record in records if record.offer_number in scoped_offer_numbers]
        if len(scoped_records) != self.SLICE_SIZE:
            raise UserOfferCodeScopeError(f"Expected {self.SLICE_SIZE} scoped offer-code records.")
        all_records[start:end] = scoped_records
        self._repository.save_all(all_records)

    def _start_index(self) -> int:
        user_key = self._user.strip().casefold()
        if user_key not in self.USER_OFFSETS:
            raise UserOfferCodeScopeError(f"No offer-code allocation is configured for {self._user}.")
        return self.USER_OFFSETS[user_key]
