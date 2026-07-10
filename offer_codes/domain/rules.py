"""Business rules for offer code assignment."""

from offer_codes.domain.models import OfferCodeRecord


class OfferCodeRules:
    @staticmethod
    def can_issue(U3A_number: str, first_name: str, last_name: str, email: str) -> bool:
        return all(
            (
                U3A_number.strip(),
                first_name.strip(),
                last_name.strip(),
                email.strip(),
            )
        )

    @staticmethod
    def is_available(record: OfferCodeRecord) -> bool:
        return not record.U3A_number.strip() and not record.email.strip() and not record.issued.strip()

    @staticmethod
    def complete(
        record: OfferCodeRecord, U3A_number: str, first_name: str, last_name: str, email: str, issued: str
    ) -> OfferCodeRecord:
        return OfferCodeRecord(
            U3A_number=U3A_number.strip(),
            email=OfferCodeRules.normalize_email(email),
            offer_number=record.offer_number,
            issued=issued,
            first_name=OfferCodeRules.normalize_name(first_name),
            last_name=OfferCodeRules.normalize_name(last_name),
        )

    @staticmethod
    def normalize_name(name: str) -> str:
        return " ".join(part.capitalize() for part in name.strip().split())

    @staticmethod
    def normalize_email(email: str) -> str:
        return email.strip().casefold()
