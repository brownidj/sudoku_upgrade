"""Domain models for offer code assignment."""

from dataclasses import dataclass


@dataclass(frozen=True)
class OfferCodeRecord:
    U3A_number: str
    email: str
    offer_number: str
    issued: str
    first_name: str = ""
    last_name: str = ""
    device_type: str = ""

    @classmethod
    def blank(cls, offer_number: str) -> "OfferCodeRecord":
        return cls(U3A_number="", email="", offer_number=offer_number, issued="")


@dataclass(frozen=True)
class AndroidTesterRecord:
    U3A_number: str
    email: str
    first_name: str
    last_name: str
    device_type: str
    registered: str
