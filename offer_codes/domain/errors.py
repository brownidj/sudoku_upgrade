"""Domain-level exceptions."""


class OfferCodeError(Exception):
    """Base exception for offer code workflows."""


class NoAvailableOfferCodeError(OfferCodeError):
    """Raised when no unissued offer code record is available."""


class DuplicateU3ANumberError(OfferCodeError):
    """Raised when a U3A number already has an issued offer code."""
