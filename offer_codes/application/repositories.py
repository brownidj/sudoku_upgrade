"""Repository interfaces for offer code records."""

from typing import Protocol

from offer_codes.domain.models import AndroidTesterRecord, OfferCodeRecord


class OfferCodeRepository(Protocol):
    def load_all(self) -> list[OfferCodeRecord]:
        ...

    def save_all(self, records: list[OfferCodeRecord]) -> None:
        ...


class AndroidTesterRepository(Protocol):
    def load_all(self) -> list[AndroidTesterRecord]:
        ...

    def save_all(self, records: list[AndroidTesterRecord]) -> None:
        ...
