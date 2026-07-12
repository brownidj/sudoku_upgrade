"""Business rules for offer code assignment."""

from offer_codes.domain.models import OfferCodeRecord


class OfferCodeRules:
    ALLOWED_DEVICE_TYPES = ("Android", "iPhone")

    @staticmethod
    def can_issue(U3A_number: str, first_name: str, last_name: str, email: str, device_type: str) -> bool:
        return all(
            (
                U3A_number.strip(),
                first_name.strip(),
                last_name.strip(),
                email.strip(),
                OfferCodeRules.is_valid_device_type(device_type),
            )
        )

    @staticmethod
    def is_available(record: OfferCodeRecord) -> bool:
        return not record.U3A_number.strip() and not record.email.strip() and not record.issued.strip()

    @staticmethod
    def complete(
        record: OfferCodeRecord,
        U3A_number: str,
        first_name: str,
        last_name: str,
        email: str,
        device_type: str,
        issued: str,
    ) -> OfferCodeRecord:
        return OfferCodeRecord(
            U3A_number=U3A_number.strip(),
            email=OfferCodeRules.normalize_email(email),
            offer_number=record.offer_number,
            issued=issued,
            first_name=OfferCodeRules.normalize_name(first_name),
            last_name=OfferCodeRules.normalize_name(last_name),
            device_type=OfferCodeRules.normalize_device_type(device_type),
        )

    @staticmethod
    def normalize_name(name: str) -> str:
        return " ".join(part.capitalize() for part in name.strip().split())

    @staticmethod
    def normalize_email(email: str) -> str:
        return email.strip().casefold()

    @staticmethod
    def normalize_device_type(device_type: str) -> str:
        requested_device_type = device_type.strip().casefold()
        for allowed_device_type in OfferCodeRules.ALLOWED_DEVICE_TYPES:
            if requested_device_type == allowed_device_type.casefold():
                return allowed_device_type
        return device_type.strip()

    @staticmethod
    def is_valid_device_type(device_type: str) -> bool:
        return OfferCodeRules.normalize_device_type(device_type) in OfferCodeRules.ALLOWED_DEVICE_TYPES
