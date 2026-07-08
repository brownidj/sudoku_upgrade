"""Repository interfaces for offer code records."""

from typing import Protocol

from offer_codes.domain.models import OfferCodeRecord


class OfferCodeRepository(Protocol):
    def load_all(self) -> list[OfferCodeRecord]:
        ...

    def save_all(self, records: list[OfferCodeRecord]) -> None:
        ...
