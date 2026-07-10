"""SMTP configuration loaded from environment variables."""

import os
from dataclasses import dataclass


class SmtpConfigError(Exception):
    """Raised when SMTP configuration is missing or invalid."""


@dataclass(frozen=True)
class SmtpConfig:
    host: str
    port: int
    username: str
    password: str
    from_email: str

    @classmethod
    def from_env(cls) -> "SmtpConfig":
        values = {
            "host": os.environ.get("OFFER_CODES_SMTP_HOST", "").strip(),
            "port": os.environ.get("OFFER_CODES_SMTP_PORT", "").strip(),
            "username": os.environ.get("OFFER_CODES_SMTP_USERNAME", "").strip(),
            "password": os.environ.get("OFFER_CODES_SMTP_PASSWORD", "").strip(),
            "from_email": os.environ.get("OFFER_CODES_FROM_EMAIL", "").strip(),
        }
        missing = [name for name, value in values.items() if not value]
        if missing:
            raise SmtpConfigError(f"Missing SMTP setting(s): {', '.join(missing)}.")
        try:
            port = int(values["port"])
        except ValueError as exc:
            raise SmtpConfigError("OFFER_CODES_SMTP_PORT must be a number.") from exc
        return cls(
            host=values["host"],
            port=port,
            username=values["username"],
            password=values["password"],
            from_email=values["from_email"],
        )
