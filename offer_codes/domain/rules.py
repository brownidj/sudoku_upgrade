"""Business rules for offer code assignment."""

from offer_codes.domain.models import OfferCodeRecord


class OfferCodeRules:
    @staticmethod
    def can_issue(U3A_number: str, email: str) -> bool:
        return bool(U3A_number.strip()) and bool(email.strip())

    @staticmethod
    def is_available(record: OfferCodeRecord) -> bool:
        return not record.U3A_number.strip() and not record.email.strip() and not record.issued.strip()

    @staticmethod
    def complete(record: OfferCodeRecord, U3A_number: str, email: str, issued: str) -> OfferCodeRecord:
        return OfferCodeRecord(
            U3A_number=U3A_number.strip(),
            email=email.strip(),
            offer_number=record.offer_number,
            issued=issued,
        )
